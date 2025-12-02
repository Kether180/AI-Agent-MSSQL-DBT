package api

import (
	"database/sql"
	"fmt"
	"net/http"
	"regexp"
	"strings"

	"github.com/datamigrate-ai/backend/internal/config"
	"github.com/datamigrate-ai/backend/internal/db"
	"github.com/datamigrate-ai/backend/internal/middleware"
	"github.com/datamigrate-ai/backend/internal/models"
	"github.com/gin-gonic/gin"
	"golang.org/x/crypto/bcrypt"
)

// generateSlug creates a URL-safe slug from organization name
func generateSlug(name string) string {
	// Convert to lowercase
	slug := strings.ToLower(name)
	// Replace spaces with hyphens
	slug = strings.ReplaceAll(slug, " ", "-")
	// Remove non-alphanumeric characters except hyphens
	reg := regexp.MustCompile("[^a-z0-9-]+")
	slug = reg.ReplaceAllString(slug, "")
	// Remove multiple consecutive hyphens
	reg = regexp.MustCompile("-+")
	slug = reg.ReplaceAllString(slug, "-")
	// Trim leading/trailing hyphens
	slug = strings.Trim(slug, "-")
	return slug
}

type AuthHandler struct {
	cfg *config.Config
}

func NewAuthHandler(cfg *config.Config) *AuthHandler {
	return &AuthHandler{cfg: cfg}
}

// Register creates a new user and organization
func (h *AuthHandler) Register(c *gin.Context) {
	var req models.RegisterRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Check if user already exists
	var existingUser models.User
	err := db.DB.Get(&existingUser, "SELECT id FROM users WHERE email = $1", req.Email)
	if err == nil {
		c.JSON(http.StatusConflict, gin.H{"error": "User with this email already exists"})
		return
	}

	// Hash password
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to hash password"})
		return
	}

	// Generate unique slug for organization
	baseSlug := generateSlug(req.OrganizationName)
	slug := baseSlug
	counter := 1

	// Ensure slug is unique
	for {
		var count int
		db.DB.Get(&count, "SELECT COUNT(*) FROM organizations WHERE slug = $1", slug)
		if count == 0 {
			break
		}
		slug = baseSlug + "-" + string(rune('0'+counter))
		counter++
		if counter > 100 {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to generate unique organization slug"})
			return
		}
	}

	// Start transaction
	tx, err := db.DB.Beginx()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to start transaction"})
		return
	}
	defer tx.Rollback()

	// Create organization
	var orgID int64
	err = tx.QueryRow(
		`INSERT INTO organizations (name, slug, plan, max_users, max_migrations)
		 VALUES ($1, $2, 'free', 5, 10) RETURNING id`,
		req.OrganizationName, slug,
	).Scan(&orgID)

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create organization"})
		return
	}

	// Create user with organization and admin role
	var userID int64
	err = tx.QueryRow(
		`INSERT INTO users (email, password, first_name, last_name, job_title, phone, organization_id, role, is_admin, is_active)
		 VALUES ($1, $2, $3, $4, $5, $6, $7, 'admin', false, true) RETURNING id`,
		req.Email, string(hashedPassword), req.FirstName, req.LastName, req.JobTitle, req.Phone, orgID,
	).Scan(&userID)

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create user"})
		return
	}

	// Commit transaction
	if err := tx.Commit(); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to commit transaction"})
		return
	}

	// Generate token
	token, err := middleware.GenerateToken(userID, req.Email, false, h.cfg.JWTExpiration)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to generate token"})
		return
	}

	c.JSON(http.StatusCreated, models.LoginResponse{
		AccessToken: token,
		User: models.User{
			ID:             userID,
			Email:          req.Email,
			FirstName:      &req.FirstName,
			LastName:       &req.LastName,
			JobTitle:       req.JobTitle,
			Phone:          req.Phone,
			OrganizationID: &orgID,
			Role:           "admin",
			IsAdmin:        false,
			IsActive:       true,
			Organization: &models.Organization{
				ID:   orgID,
				Name: req.OrganizationName,
				Slug: slug,
				Plan: "free",
			},
		},
	})
}

// Login authenticates a user
func (h *AuthHandler) Login(c *gin.Context) {
	var req models.LoginRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Find user with all fields
	var user models.User
	err := db.DB.Get(&user, `
		SELECT id, email, password, first_name, last_name, job_title, phone,
		       organization_id, role, is_admin, is_active, last_login_at, created_at, updated_at
		FROM users WHERE email = $1`, req.Email)
	if err != nil {
		if err == sql.ErrNoRows {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid credentials"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Database error"})
		return
	}

	// Check if user is active
	if !user.IsActive {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Account is deactivated"})
		return
	}

	// Check password
	if err := bcrypt.CompareHashAndPassword([]byte(user.Password), []byte(req.Password)); err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid credentials"})
		return
	}

	// Update last login
	db.DB.Exec("UPDATE users SET last_login_at = NOW() WHERE id = $1", user.ID)

	// Get organization if user belongs to one
	if user.OrganizationID != nil {
		var org models.Organization
		err := db.DB.Get(&org, "SELECT id, name, slug, plan, max_users, max_migrations FROM organizations WHERE id = $1", *user.OrganizationID)
		if err == nil {
			user.Organization = &org
		}
	}

	// Generate token
	token, err := middleware.GenerateToken(user.ID, user.Email, user.IsAdmin, h.cfg.JWTExpiration)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to generate token"})
		return
	}

	c.JSON(http.StatusOK, models.LoginResponse{
		AccessToken: token,
		User:        user,
	})
}

// GetCurrentUser returns the current authenticated user
func (h *AuthHandler) GetCurrentUser(c *gin.Context) {
	userID := middleware.GetUserID(c)

	var user models.User
	err := db.DB.Get(&user, `
		SELECT id, email, first_name, last_name, job_title, phone,
		       organization_id, role, is_admin, is_active, last_login_at, created_at, updated_at
		FROM users WHERE id = $1`, userID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "User not found"})
		return
	}

	// Get organization if user belongs to one
	if user.OrganizationID != nil {
		var org models.Organization
		err := db.DB.Get(&org, "SELECT id, name, slug, plan, max_users, max_migrations FROM organizations WHERE id = $1", *user.OrganizationID)
		if err == nil {
			user.Organization = &org
		}
	}

	c.JSON(http.StatusOK, user)
}

// Logout (client-side token removal, but we can add token blacklisting later)
func (h *AuthHandler) Logout(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"message": "Logged out successfully"})
}

// UpdateProfile updates the current user's profile
func (h *AuthHandler) UpdateProfile(c *gin.Context) {
	userID := middleware.GetUserID(c)

	var req models.UpdateProfileRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Check if email is being changed and if it's already taken
	if req.Email != nil && *req.Email != "" {
		var existingUser models.User
		err := db.DB.Get(&existingUser, "SELECT id FROM users WHERE email = $1 AND id != $2", *req.Email, userID)
		if err == nil {
			c.JSON(http.StatusConflict, gin.H{"error": "Email is already in use by another account"})
			return
		}
	}

	// Build dynamic update query
	query := "UPDATE users SET updated_at = NOW()"
	args := []interface{}{}
	argCount := 0

	if req.FirstName != nil {
		argCount++
		query += fmt.Sprintf(", first_name = $%d", argCount)
		args = append(args, *req.FirstName)
	}
	if req.LastName != nil {
		argCount++
		query += fmt.Sprintf(", last_name = $%d", argCount)
		args = append(args, *req.LastName)
	}
	if req.Email != nil {
		argCount++
		query += fmt.Sprintf(", email = $%d", argCount)
		args = append(args, *req.Email)
	}
	if req.JobTitle != nil {
		argCount++
		query += fmt.Sprintf(", job_title = $%d", argCount)
		args = append(args, *req.JobTitle)
	}
	if req.Phone != nil {
		argCount++
		query += fmt.Sprintf(", phone = $%d", argCount)
		args = append(args, *req.Phone)
	}

	argCount++
	query += fmt.Sprintf(" WHERE id = $%d", argCount)
	args = append(args, userID)

	_, err := db.DB.Exec(query, args...)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to update profile"})
		return
	}

	// Fetch and return updated user
	var user models.User
	err = db.DB.Get(&user, `
		SELECT id, email, first_name, last_name, job_title, phone,
		       organization_id, role, is_admin, is_active, last_login_at, created_at, updated_at
		FROM users WHERE id = $1`, userID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch updated user"})
		return
	}

	// Get organization if user belongs to one
	if user.OrganizationID != nil {
		var org models.Organization
		err := db.DB.Get(&org, "SELECT id, name, slug, plan, max_users, max_migrations FROM organizations WHERE id = $1", *user.OrganizationID)
		if err == nil {
			user.Organization = &org
		}
	}

	c.JSON(http.StatusOK, user)
}

// ChangePassword changes the current user's password
func (h *AuthHandler) ChangePassword(c *gin.Context) {
	userID := middleware.GetUserID(c)

	var req models.ChangePasswordRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Get current user with password
	var user models.User
	err := db.DB.Get(&user, "SELECT id, password FROM users WHERE id = $1", userID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "User not found"})
		return
	}

	// Verify current password
	if err := bcrypt.CompareHashAndPassword([]byte(user.Password), []byte(req.CurrentPassword)); err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Current password is incorrect"})
		return
	}

	// Hash new password
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(req.NewPassword), bcrypt.DefaultCost)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to hash password"})
		return
	}

	// Update password
	_, err = db.DB.Exec("UPDATE users SET password = $1, updated_at = NOW() WHERE id = $2", string(hashedPassword), userID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to update password"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Password updated successfully"})
}
