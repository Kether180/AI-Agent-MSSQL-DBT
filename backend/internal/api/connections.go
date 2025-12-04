package api

import (
	"database/sql"
	"log"
	"net/http"
	"os"
	"strconv"
	"strings"

	"github.com/datamigrate-ai/backend/internal/crypto"
	"github.com/datamigrate-ai/backend/internal/db"
	"github.com/datamigrate-ai/backend/internal/dbtest"
	"github.com/datamigrate-ai/backend/internal/middleware"
	"github.com/datamigrate-ai/backend/internal/models"
	"github.com/datamigrate-ai/backend/internal/security"
	"github.com/datamigrate-ai/backend/internal/validation"
	"github.com/gin-gonic/gin"
)

type ConnectionsHandler struct {
	encryptionService *crypto.EncryptionService
	ipValidator       *security.IPValidator
}

func NewConnectionsHandler() *ConnectionsHandler {
	// Check if running in production mode
	isProduction := strings.ToLower(os.Getenv("ENVIRONMENT")) == "production"

	// Create IP validator with appropriate settings
	ipValidatorConfig := security.DefaultIPValidatorConfig(isProduction)
	ipValidator, err := security.NewIPValidator(ipValidatorConfig)
	if err != nil {
		log.Printf("Warning: Failed to create IP validator: %v", err)
	}

	return &ConnectionsHandler{
		encryptionService: crypto.GetEncryptionService(),
		ipValidator:       ipValidator,
	}
}

// validateHostSSRF validates a host against SSRF attacks
func (h *ConnectionsHandler) validateHostSSRF(host string) error {
	if h.ipValidator == nil {
		return nil // No validator configured
	}
	return h.ipValidator.ValidateHost(host)
}

// encryptPassword encrypts a password if encryption is enabled
func (h *ConnectionsHandler) encryptPassword(password string) string {
	if !h.encryptionService.IsKeySet() || password == "" {
		return password // Return as-is if encryption not configured
	}

	encrypted, err := h.encryptionService.Encrypt(password)
	if err != nil {
		log.Printf("Warning: Failed to encrypt password: %v", err)
		return password // Fallback to plaintext if encryption fails
	}
	return encrypted
}

// decryptPassword decrypts a password if it appears to be encrypted
func (h *ConnectionsHandler) decryptPassword(password string) string {
	if !h.encryptionService.IsKeySet() || password == "" {
		return password
	}

	// Check if password looks encrypted (base64 + minimum length)
	if !crypto.IsEncrypted(password) {
		return password // Not encrypted, return as-is
	}

	decrypted, err := h.encryptionService.Decrypt(password)
	if err != nil {
		log.Printf("Warning: Failed to decrypt password (may be plaintext): %v", err)
		return password // Return as-is if decryption fails (might be old plaintext)
	}
	return decrypted
}

// GetAll returns all database connections for the current user
// @Summary List all connections
// @Description Get all database connections for the current user
// @Tags connections
// @Accept json
// @Produce json
// @Security BearerAuth
// @Success 200 {array} models.DatabaseConnection
// @Failure 500 {object} map[string]string
// @Router /connections [get]
func (h *ConnectionsHandler) GetAll(c *gin.Context) {
	userID := middleware.GetUserID(c)

	var connections []models.DatabaseConnection
	err := db.DB.Select(&connections, `
		SELECT id, name, db_type, host, port, database_name, username,
		       is_source, user_id, created_at, updated_at
		FROM database_connections
		WHERE user_id = $1
		ORDER BY created_at DESC
	`, userID)

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch connections"})
		return
	}

	if connections == nil {
		connections = []models.DatabaseConnection{}
	}

	c.JSON(http.StatusOK, connections)
}

// GetOne returns a single database connection by ID
// @Summary Get connection details
// @Description Get a specific database connection by ID
// @Tags connections
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param id path int true "Connection ID"
// @Success 200 {object} models.DatabaseConnection
// @Failure 400 {object} map[string]string
// @Failure 404 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /connections/{id} [get]
func (h *ConnectionsHandler) GetOne(c *gin.Context) {
	userID := middleware.GetUserID(c)
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid connection ID"})
		return
	}

	var connection models.DatabaseConnection
	err = db.DB.Get(&connection, `
		SELECT id, name, db_type, host, port, database_name, username,
		       is_source, user_id, created_at, updated_at
		FROM database_connections
		WHERE id = $1 AND user_id = $2
	`, id, userID)

	if err != nil {
		if err == sql.ErrNoRows {
			c.JSON(http.StatusNotFound, gin.H{"error": "Connection not found"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch connection"})
		return
	}

	c.JSON(http.StatusOK, connection)
}

// Create creates a new database connection
// @Summary Create a connection
// @Description Create a new database connection
// @Tags connections
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param request body models.CreateConnectionRequest true "Connection details"
// @Success 201 {object} models.DatabaseConnection
// @Failure 400 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /connections [post]
func (h *ConnectionsHandler) Create(c *gin.Context) {
	userID := middleware.GetUserID(c)

	var req models.CreateConnectionRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Validate input parameters
	validator := validation.NewConnectionValidator()
	validationResult := validator.ValidateConnection(
		req.Name,
		req.DBType,
		req.Host,
		req.Port,
		req.DatabaseName,
		req.Username,
		req.Password,
		req.UseWindowsAuth,
	)

	if !validationResult.Valid {
		log.Printf("Connection validation failed: %s", validationResult.ErrorMessages())
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "Validation failed",
			"details": validationResult.Errors,
		})
		return
	}

	// SSRF Protection: Validate host is not internal/private
	if err := h.validateHostSSRF(req.Host); err != nil {
		log.Printf("SSRF validation failed for host %s: %v", req.Host, err)
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "Invalid host address",
			"details": "The specified host address is not allowed for security reasons",
		})
		return
	}

	// Sanitize inputs
	req.Name = validation.SanitizeInput(req.Name)
	req.Host = validation.SanitizeInput(req.Host)
	req.DatabaseName = validation.SanitizeInput(req.DatabaseName)
	req.Username = validation.SanitizeInput(req.Username)

	// Encrypt password before storing
	encryptedPassword := h.encryptPassword(req.Password)

	var connectionID int64
	err := db.DB.QueryRow(`
		INSERT INTO database_connections (name, db_type, host, port, database_name, username, password, use_windows_auth, is_source, user_id)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
		RETURNING id
	`, req.Name, req.DBType, req.Host, req.Port, req.DatabaseName, req.Username, encryptedPassword, req.UseWindowsAuth, req.IsSource, userID).Scan(&connectionID)

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create connection"})
		return
	}

	var connection models.DatabaseConnection
	db.DB.Get(&connection, `
		SELECT id, name, db_type, host, port, database_name, username,
		       is_source, user_id, created_at, updated_at
		FROM database_connections WHERE id = $1
	`, connectionID)

	c.JSON(http.StatusCreated, connection)
}

// Update updates a database connection
// @Summary Update a connection
// @Description Update an existing database connection
// @Tags connections
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param id path int true "Connection ID"
// @Param request body models.CreateConnectionRequest true "Connection details"
// @Success 200 {object} models.DatabaseConnection
// @Failure 400 {object} map[string]string
// @Failure 404 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /connections/{id} [put]
func (h *ConnectionsHandler) Update(c *gin.Context) {
	userID := middleware.GetUserID(c)
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid connection ID"})
		return
	}

	var req models.CreateConnectionRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Validate input parameters
	validator := validation.NewConnectionValidator()
	validationResult := validator.ValidateConnection(
		req.Name,
		req.DBType,
		req.Host,
		req.Port,
		req.DatabaseName,
		req.Username,
		req.Password,
		req.UseWindowsAuth,
	)

	if !validationResult.Valid {
		log.Printf("Connection update validation failed: %s", validationResult.ErrorMessages())
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "Validation failed",
			"details": validationResult.Errors,
		})
		return
	}

	// SSRF Protection: Validate host is not internal/private
	if err := h.validateHostSSRF(req.Host); err != nil {
		log.Printf("SSRF validation failed for host %s: %v", req.Host, err)
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "Invalid host address",
			"details": "The specified host address is not allowed for security reasons",
		})
		return
	}

	// Sanitize inputs
	req.Name = validation.SanitizeInput(req.Name)
	req.Host = validation.SanitizeInput(req.Host)
	req.DatabaseName = validation.SanitizeInput(req.DatabaseName)
	req.Username = validation.SanitizeInput(req.Username)

	// Encrypt password before storing
	encryptedPassword := h.encryptPassword(req.Password)

	result, err := db.DB.Exec(`
		UPDATE database_connections
		SET name = $1, db_type = $2, host = $3, port = $4, database_name = $5,
		    username = $6, password = $7, use_windows_auth = $8, is_source = $9, updated_at = NOW()
		WHERE id = $10 AND user_id = $11
	`, req.Name, req.DBType, req.Host, req.Port, req.DatabaseName, req.Username, encryptedPassword, req.UseWindowsAuth, req.IsSource, id, userID)

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to update connection"})
		return
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		c.JSON(http.StatusNotFound, gin.H{"error": "Connection not found"})
		return
	}

	var connection models.DatabaseConnection
	db.DB.Get(&connection, `
		SELECT id, name, db_type, host, port, database_name, username,
		       is_source, user_id, created_at, updated_at
		FROM database_connections WHERE id = $1
	`, id)

	c.JSON(http.StatusOK, connection)
}

// Delete deletes a database connection
// @Summary Delete a connection
// @Description Delete a database connection
// @Tags connections
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param id path int true "Connection ID"
// @Success 200 {object} map[string]string
// @Failure 400 {object} map[string]string
// @Failure 404 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /connections/{id} [delete]
func (h *ConnectionsHandler) Delete(c *gin.Context) {
	userID := middleware.GetUserID(c)
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid connection ID"})
		return
	}

	result, err := db.DB.Exec("DELETE FROM database_connections WHERE id = $1 AND user_id = $2", id, userID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to delete connection"})
		return
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		c.JSON(http.StatusNotFound, gin.H{"error": "Connection not found"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Connection deleted"})
}

// Test tests a database connection
// @Summary Test a connection
// @Description Test if a database connection is valid and reachable
// @Tags connections
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param id path int true "Connection ID"
// @Success 200 {object} map[string]interface{}
// @Failure 400 {object} map[string]interface{}
// @Failure 404 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /connections/{id}/test [post]
func (h *ConnectionsHandler) Test(c *gin.Context) {
	userID := middleware.GetUserID(c)
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid connection ID"})
		return
	}

	// Fetch connection with password for testing
	var connection struct {
		ID             int64  `db:"id"`
		DBType         string `db:"db_type"`
		Host           string `db:"host"`
		Port           int    `db:"port"`
		Database       string `db:"database_name"`
		Username       string `db:"username"`
		Password       string `db:"password"`
		UseWindowsAuth bool   `db:"use_windows_auth"`
	}

	err = db.DB.Get(&connection, `
		SELECT id, db_type, host, port, database_name, username, password, COALESCE(use_windows_auth, false) as use_windows_auth
		FROM database_connections
		WHERE id = $1 AND user_id = $2
	`, id, userID)

	if err != nil {
		if err == sql.ErrNoRows {
			c.JSON(http.StatusNotFound, gin.H{"error": "Connection not found"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch connection"})
		return
	}

	// SSRF Protection: Validate host before testing connection
	if err := h.validateHostSSRF(connection.Host); err != nil {
		log.Printf("SSRF validation failed for connection test, host %s: %v", connection.Host, err)
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "Connection test blocked",
			"details": "The specified host address is not allowed for security reasons",
		})
		return
	}

	// Decrypt password before testing connection
	decryptedPassword := h.decryptPassword(connection.Password)

	// Test the actual database connection
	result := dbtest.TestConnection(dbtest.ConnectionParams{
		DBType:         connection.DBType,
		Host:           connection.Host,
		Port:           connection.Port,
		Database:       connection.Database,
		Username:       connection.Username,
		Password:       decryptedPassword,
		UseWindowsAuth: connection.UseWindowsAuth,
	})

	if result.Success {
		c.JSON(http.StatusOK, result)
	} else {
		c.JSON(http.StatusBadRequest, result)
	}
}

// GetMetadata extracts metadata (tables, views, procedures) from a database connection
// @Summary Get database metadata
// @Description Extract schema metadata (tables, views, procedures) from a database connection
// @Tags connections
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param id path int true "Connection ID"
// @Success 200 {object} map[string]interface{}
// @Failure 400 {object} map[string]string
// @Failure 404 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /connections/{id}/metadata [get]
func (h *ConnectionsHandler) GetMetadata(c *gin.Context) {
	userID := middleware.GetUserID(c)
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid connection ID"})
		return
	}

	// Fetch connection details
	var connection struct {
		ID             int64  `db:"id"`
		DBType         string `db:"db_type"`
		Host           string `db:"host"`
		Port           int    `db:"port"`
		Database       string `db:"database_name"`
		Username       string `db:"username"`
		Password       string `db:"password"`
		UseWindowsAuth bool   `db:"use_windows_auth"`
	}

	err = db.DB.Get(&connection, `
		SELECT id, db_type, host, port, database_name, username, password, COALESCE(use_windows_auth, false) as use_windows_auth
		FROM database_connections
		WHERE id = $1 AND user_id = $2
	`, id, userID)

	if err != nil {
		if err == sql.ErrNoRows {
			c.JSON(http.StatusNotFound, gin.H{"error": "Connection not found"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch connection"})
		return
	}

	// SSRF Protection: Validate host before extracting metadata
	if err := h.validateHostSSRF(connection.Host); err != nil {
		log.Printf("SSRF validation failed for metadata extraction, host %s: %v", connection.Host, err)
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "Metadata extraction blocked",
			"details": "The specified host address is not allowed for security reasons",
		})
		return
	}

	// Decrypt password before extracting metadata
	decryptedPassword := h.decryptPassword(connection.Password)

	// Extract metadata using dbtest package
	metadata := dbtest.ExtractMetadata(dbtest.ConnectionParams{
		DBType:         connection.DBType,
		Host:           connection.Host,
		Port:           connection.Port,
		Database:       connection.Database,
		Username:       connection.Username,
		Password:       decryptedPassword,
		UseWindowsAuth: connection.UseWindowsAuth,
	})

	c.JSON(http.StatusOK, metadata)
}
