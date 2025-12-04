package api

import (
	"crypto/rand"
	"database/sql"
	"encoding/hex"
	"fmt"
	"log"
	"net/http"
	"regexp"
	"strings"
	"time"

	"github.com/datamigrate-ai/backend/internal/config"
	"github.com/datamigrate-ai/backend/internal/db"
	"github.com/datamigrate-ai/backend/internal/email"
	"github.com/datamigrate-ai/backend/internal/middleware"
	"github.com/datamigrate-ai/backend/internal/models"
	"github.com/datamigrate-ai/backend/internal/security"
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
// @Summary Register a new user
// @Description Create a new user account with an organization
// @Tags auth
// @Accept json
// @Produce json
// @Param request body models.RegisterRequest true "Registration details"
// @Success 201 {object} models.LoginResponse
// @Failure 400 {object} map[string]string
// @Failure 409 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /auth/register [post]
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
// @Summary Login user
// @Description Authenticate a user and return a JWT token
// @Tags auth
// @Accept json
// @Produce json
// @Param request body models.LoginRequest true "Login credentials"
// @Success 200 {object} models.LoginResponse
// @Failure 400 {object} map[string]string
// @Failure 401 {object} map[string]string
// @Failure 429 {object} map[string]string "Account locked"
// @Failure 500 {object} map[string]string
// @Router /auth/login [post]
func (h *AuthHandler) Login(c *gin.Context) {
	var req models.LoginRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Get client IP for lockout tracking
	clientIP := c.ClientIP()
	accountLockout := security.GetAccountLockout()

	// Check if account is locked
	lockoutStatus := accountLockout.IsLocked(req.Email)
	if lockoutStatus.Locked {
		log.Printf("Login attempt for locked account: %s from IP: %s", req.Email, clientIP)
		c.JSON(http.StatusTooManyRequests, gin.H{
			"error":           lockoutStatus.Message,
			"locked":          true,
			"retry_after_sec": int(lockoutStatus.RemainingTime.Seconds()),
		})
		return
	}

	// Check if IP is blocked (too many failed attempts across accounts)
	if accountLockout.CheckIPBlocked(clientIP) {
		log.Printf("Login attempt from blocked IP: %s for email: %s", clientIP, req.Email)
		c.JSON(http.StatusTooManyRequests, gin.H{
			"error":  "Too many failed login attempts from this IP address. Please try again later.",
			"locked": true,
		})
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
			// Record failed attempt even for non-existent accounts (prevent enumeration)
			status := accountLockout.RecordFailedAttempt(req.Email, clientIP)
			log.Printf("Failed login (user not found): %s from IP: %s, attempts left: %d", req.Email, clientIP, status.AttemptsLeft)
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid credentials"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Database error"})
		return
	}

	// Check if user is active
	if !user.IsActive {
		log.Printf("Login attempt for deactivated account: %s from IP: %s", req.Email, clientIP)
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Account is deactivated"})
		return
	}

	// Check password
	if err := bcrypt.CompareHashAndPassword([]byte(user.Password), []byte(req.Password)); err != nil {
		// Record failed attempt
		status := accountLockout.RecordFailedAttempt(req.Email, clientIP)
		log.Printf("Failed login (wrong password): %s from IP: %s, attempts left: %d", req.Email, clientIP, status.AttemptsLeft)

		if status.JustLocked {
			log.Printf("Account locked: %s after %d lock events", req.Email, status.LockCount)
			c.JSON(http.StatusTooManyRequests, gin.H{
				"error":           status.Message,
				"locked":          true,
				"retry_after_sec": int(status.RemainingTime.Seconds()),
			})
			return
		}

		response := gin.H{"error": "Invalid credentials"}
		if status.AttemptsLeft <= 3 && status.AttemptsLeft > 0 {
			response["warning"] = fmt.Sprintf("%d login attempts remaining before account lockout", status.AttemptsLeft)
		}
		c.JSON(http.StatusUnauthorized, response)
		return
	}

	// Successful login - clear failed attempts
	accountLockout.RecordSuccessfulLogin(req.Email, clientIP)
	log.Printf("Successful login: %s from IP: %s", req.Email, clientIP)

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
// @Summary Get current user
// @Description Get the currently authenticated user's profile
// @Tags auth
// @Accept json
// @Produce json
// @Security BearerAuth
// @Success 200 {object} models.User
// @Failure 404 {object} map[string]string
// @Router /auth/me [get]
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
// @Summary Logout user
// @Description Logout the current user (client-side token removal)
// @Tags auth
// @Accept json
// @Produce json
// @Security BearerAuth
// @Success 200 {object} map[string]string
// @Router /auth/logout [post]
func (h *AuthHandler) Logout(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"message": "Logged out successfully"})
}

// UpdateProfile updates the current user's profile
// @Summary Update user profile
// @Description Update the current user's profile information
// @Tags auth
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param request body models.UpdateProfileRequest true "Profile update data"
// @Success 200 {object} models.User
// @Failure 400 {object} map[string]string
// @Failure 409 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /auth/profile [put]
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
// @Summary Change password
// @Description Change the current user's password
// @Tags auth
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param request body models.ChangePasswordRequest true "Password change data"
// @Success 200 {object} map[string]string
// @Failure 400 {object} map[string]string
// @Failure 401 {object} map[string]string
// @Failure 404 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /auth/password [put]
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

// ForgotPassword sends a password reset email
// @Summary Forgot password
// @Description Request a password reset email
// @Tags auth
// @Accept json
// @Produce json
// @Param request body models.ForgotPasswordRequest true "Email address"
// @Success 200 {object} map[string]string
// @Failure 400 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /auth/forgot-password [post]
func (h *AuthHandler) ForgotPassword(c *gin.Context) {
	var req models.ForgotPasswordRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Find user by email
	var user struct {
		ID        int64   `db:"id"`
		Email     string  `db:"email"`
		FirstName *string `db:"first_name"`
		IsActive  bool    `db:"is_active"`
	}
	err := db.DB.Get(&user, "SELECT id, email, first_name, is_active FROM users WHERE email = $1", req.Email)
	if err != nil {
		// Don't reveal if email exists or not - always return success
		log.Printf("Password reset requested for unknown email: %s", req.Email)
		c.JSON(http.StatusOK, gin.H{"message": "If an account with that email exists, a password reset link has been sent"})
		return
	}

	// Check if user is active
	if !user.IsActive {
		log.Printf("Password reset requested for deactivated account: %s", req.Email)
		c.JSON(http.StatusOK, gin.H{"message": "If an account with that email exists, a password reset link has been sent"})
		return
	}

	// Generate secure reset token
	tokenBytes := make([]byte, 32)
	if _, err := rand.Read(tokenBytes); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to generate reset token"})
		return
	}
	resetToken := hex.EncodeToString(tokenBytes)

	// Set expiration to 1 hour from now
	expiresAt := time.Now().Add(1 * time.Hour)

	// Delete any existing tokens for this user
	db.DB.Exec("DELETE FROM password_reset_tokens WHERE user_id = $1", user.ID)

	// Store the reset token
	_, err = db.DB.Exec(`
		INSERT INTO password_reset_tokens (user_id, token, expires_at)
		VALUES ($1, $2, $3)
	`, user.ID, resetToken, expiresAt)
	if err != nil {
		log.Printf("Failed to store password reset token: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create password reset request"})
		return
	}

	// Send password reset email
	emailService := email.NewService()
	firstName := "User"
	if user.FirstName != nil && *user.FirstName != "" {
		firstName = *user.FirstName
	}

	if emailService.IsConfigured() {
		err = emailService.SendPasswordResetEmail(user.Email, firstName, resetToken)
		if err != nil {
			log.Printf("Failed to send password reset email: %v", err)
			// Don't reveal email sending failures to the user
		}
	} else {
		// Use mock service in development
		mockService := email.NewMockService()
		mockService.SendPasswordResetEmail(user.Email, firstName, resetToken)
		log.Printf("Email service not configured, using mock. Reset token for %s: %s", user.Email, resetToken)
	}

	c.JSON(http.StatusOK, gin.H{"message": "If an account with that email exists, a password reset link has been sent"})
}

// ResetPassword resets the user's password using a reset token
// @Summary Reset password
// @Description Reset password using a valid reset token
// @Tags auth
// @Accept json
// @Produce json
// @Param request body models.ResetPasswordRequest true "Reset token and new password"
// @Success 200 {object} map[string]string
// @Failure 400 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /auth/reset-password [post]
func (h *AuthHandler) ResetPassword(c *gin.Context) {
	var req models.ResetPasswordRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Find the reset token
	var tokenRecord struct {
		ID        int64      `db:"id"`
		UserID    int64      `db:"user_id"`
		ExpiresAt time.Time  `db:"expires_at"`
		UsedAt    *time.Time `db:"used_at"`
	}
	err := db.DB.Get(&tokenRecord, `
		SELECT id, user_id, expires_at, used_at
		FROM password_reset_tokens
		WHERE token = $1
	`, req.Token)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid or expired reset token"})
		return
	}

	// Check if token has already been used
	if tokenRecord.UsedAt != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "This reset token has already been used"})
		return
	}

	// Check if token has expired
	if time.Now().After(tokenRecord.ExpiresAt) {
		c.JSON(http.StatusBadRequest, gin.H{"error": "This reset token has expired"})
		return
	}

	// Hash the new password
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(req.NewPassword), bcrypt.DefaultCost)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to hash password"})
		return
	}

	// Start transaction
	tx, err := db.DB.Beginx()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to start transaction"})
		return
	}
	defer tx.Rollback()

	// Update the user's password
	_, err = tx.Exec("UPDATE users SET password = $1, updated_at = NOW() WHERE id = $2", string(hashedPassword), tokenRecord.UserID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to update password"})
		return
	}

	// Mark the token as used
	_, err = tx.Exec("UPDATE password_reset_tokens SET used_at = NOW() WHERE id = $1", tokenRecord.ID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to mark token as used"})
		return
	}

	// Commit transaction
	if err := tx.Commit(); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to commit transaction"})
		return
	}

	log.Printf("Password successfully reset for user ID: %d", tokenRecord.UserID)
	c.JSON(http.StatusOK, gin.H{"message": "Password has been reset successfully. You can now log in with your new password."})
}
