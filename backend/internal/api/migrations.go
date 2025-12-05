package api

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/datamigrate-ai/backend/internal/aiservice"
	"github.com/datamigrate-ai/backend/internal/db"
	"github.com/datamigrate-ai/backend/internal/email"
	"github.com/datamigrate-ai/backend/internal/middleware"
	"github.com/datamigrate-ai/backend/internal/models"
	"github.com/gin-gonic/gin"
)

type MigrationsHandler struct{}

func NewMigrationsHandler() *MigrationsHandler {
	return &MigrationsHandler{}
}

// GetAll returns all migrations for the current user
// @Summary List all migrations
// @Description Get all migrations for the current user
// @Tags migrations
// @Accept json
// @Produce json
// @Security BearerAuth
// @Success 200 {array} models.Migration
// @Failure 500 {object} map[string]string
// @Router /migrations [get]
func (h *MigrationsHandler) GetAll(c *gin.Context) {
	userID := middleware.GetUserID(c)

	var migrations []models.Migration
	err := db.DB.Select(&migrations, `
		SELECT id, name, status, progress, source_database, target_project,
		       tables_count, COALESCE(views_count, 0) as views_count,
		       COALESCE(foreign_keys_count, 0) as foreign_keys_count,
		       COALESCE(models_generated, 0) as models_generated,
		       user_id, error, created_at, completed_at, updated_at
		FROM migrations
		WHERE user_id = $1
		ORDER BY created_at DESC
	`, userID)

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch migrations"})
		return
	}

	if migrations == nil {
		migrations = []models.Migration{}
	}

	c.JSON(http.StatusOK, migrations)
}

// GetOne returns a single migration by ID
// @Summary Get migration details
// @Description Get detailed information about a specific migration
// @Tags migrations
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param id path int true "Migration ID"
// @Success 200 {object} models.Migration
// @Failure 400 {object} map[string]string
// @Failure 404 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /migrations/{id} [get]
func (h *MigrationsHandler) GetOne(c *gin.Context) {
	userID := middleware.GetUserID(c)
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid migration ID"})
		return
	}

	var migration models.Migration
	err = db.DB.Get(&migration, `
		SELECT id, name, status, progress, source_database, target_project,
		       tables_count, COALESCE(views_count, 0) as views_count,
		       COALESCE(foreign_keys_count, 0) as foreign_keys_count,
		       COALESCE(models_generated, 0) as models_generated,
		       user_id, error, config, created_at, completed_at, updated_at
		FROM migrations
		WHERE id = $1 AND user_id = $2
	`, id, userID)

	if err != nil {
		if err == sql.ErrNoRows {
			c.JSON(http.StatusNotFound, gin.H{"error": "Migration not found"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch migration"})
		return
	}

	c.JSON(http.StatusOK, migration)
}

// Create creates a new migration
// @Summary Create a new migration
// @Description Create a new migration project
// @Tags migrations
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param request body models.CreateMigrationRequest true "Migration configuration"
// @Success 201 {object} models.Migration
// @Failure 400 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /migrations [post]
func (h *MigrationsHandler) Create(c *gin.Context) {
	userID := middleware.GetUserID(c)

	var req models.CreateMigrationRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	tablesCount := len(req.Tables)
	if tablesCount == 0 {
		tablesCount = 1 // Default if no tables specified
	}

	var migrationID int64
	err := db.DB.QueryRow(`
		INSERT INTO migrations (name, source_database, target_project, tables_count, user_id, status, progress)
		VALUES ($1, $2, $3, $4, $5, 'pending', 0)
		RETURNING id
	`, req.Name, req.SourceDatabase, req.TargetProject, tablesCount, userID).Scan(&migrationID)

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create migration"})
		return
	}

	// Fetch the created migration
	var migration models.Migration
	db.DB.Get(&migration, `
		SELECT id, name, status, progress, source_database, target_project,
		       tables_count, user_id, created_at, updated_at
		FROM migrations WHERE id = $1
	`, migrationID)

	c.JSON(http.StatusCreated, migration)
}

// Delete deletes a migration
// @Summary Delete a migration
// @Description Delete a migration project (cannot delete running migrations)
// @Tags migrations
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param id path int true "Migration ID"
// @Success 200 {object} map[string]string
// @Failure 400 {object} map[string]string
// @Failure 404 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /migrations/{id} [delete]
func (h *MigrationsHandler) Delete(c *gin.Context) {
	userID := middleware.GetUserID(c)
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid migration ID"})
		return
	}

	// Check ownership and status
	var migration models.Migration
	err = db.DB.Get(&migration, "SELECT status FROM migrations WHERE id = $1 AND user_id = $2", id, userID)
	if err != nil {
		if err == sql.ErrNoRows {
			c.JSON(http.StatusNotFound, gin.H{"error": "Migration not found"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Database error"})
		return
	}

	if migration.Status == "running" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Cannot delete a running migration"})
		return
	}

	_, err = db.DB.Exec("DELETE FROM migrations WHERE id = $1 AND user_id = $2", id, userID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to delete migration"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Migration deleted"})
}

// Start starts a pending migration
// @Summary Start a migration
// @Description Start a pending migration to begin extracting metadata and generating dbt project
// @Tags migrations
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param id path int true "Migration ID"
// @Success 200 {object} map[string]string
// @Failure 400 {object} map[string]string
// @Failure 404 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /migrations/{id}/start [post]
func (h *MigrationsHandler) Start(c *gin.Context) {
	userID := middleware.GetUserID(c)
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid migration ID"})
		return
	}

	// First, get the migration details including source_database
	var migration struct {
		ID             int64          `db:"id"`
		SourceDatabase string         `db:"source_database"`
		TargetProject  string         `db:"target_project"`
		Config         sql.NullString `db:"config"`
		Status         string         `db:"status"`
	}

	err = db.DB.Get(&migration, `
		SELECT id, source_database, target_project, config, status
		FROM migrations
		WHERE id = $1 AND user_id = $2
	`, id, userID)

	if err != nil {
		if err == sql.ErrNoRows {
			c.JSON(http.StatusNotFound, gin.H{"error": "Migration not found"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch migration"})
		return
	}

	if migration.Status != "pending" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Migration is not in pending status"})
		return
	}

	// Get the source database connection details
	var connection struct {
		ID             int64  `db:"id"`
		Name           string `db:"name"`
		DBType         string `db:"db_type"`
		Host           string `db:"host"`
		Port           int    `db:"port"`
		Database       string `db:"database_name"`
		Username       string `db:"username"`
		Password       string `db:"password"`
		UseWindowsAuth bool   `db:"use_windows_auth"`
	}

	err = db.DB.Get(&connection, `
		SELECT id, name, db_type, host, port, database_name, username, password, COALESCE(use_windows_auth, false) as use_windows_auth
		FROM database_connections
		WHERE name = $1 AND user_id = $2
	`, migration.SourceDatabase, userID)

	if err != nil {
		if err == sql.ErrNoRows {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Source database connection not found"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch database connection"})
		return
	}

	// Update status to running
	result, err := db.DB.Exec(`
		UPDATE migrations SET status = 'running', progress = 0, updated_at = NOW()
		WHERE id = $1 AND user_id = $2 AND status = 'pending'
	`, id, userID)

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to start migration"})
		return
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Migration not found or not in pending status"})
		return
	}

	// Parse tables from config if available
	var tables []string
	if migration.Config.Valid {
		var config struct {
			Tables []string `json:"tables"`
		}
		if err := json.Unmarshal([]byte(migration.Config.String), &config); err == nil {
			tables = config.Tables
		}
	}

	// Trigger AI service to process the migration
	aiClient := aiservice.GetClient()
	if aiClient != nil {
		req := aiservice.MigrationRequest{
			MigrationID: id,
			SourceConnection: map[string]interface{}{
				"type":             connection.DBType,
				"host":             connection.Host,
				"port":             connection.Port,
				"database":         connection.Database,
				"username":         connection.Username,
				"password":         connection.Password,
				"use_windows_auth": connection.UseWindowsAuth,
			},
			TargetProject: migration.TargetProject,
			Tables:        tables,
			IncludeViews:  false,
		}

		go func() {
			// Call AI service in background
			_, err := aiClient.StartMigration(req)
			if err != nil {
				log.Printf("Failed to trigger AI service for migration %d: %v", id, err)
				// Update migration status to failed
				db.DB.Exec(`
					UPDATE migrations SET status = 'failed', error = $1, updated_at = NOW()
					WHERE id = $2
				`, "Failed to connect to AI service: "+err.Error(), id)
			}
		}()
	} else {
		log.Printf("AI service client not initialized, migration %d started in manual mode", id)
	}

	c.JSON(http.StatusOK, gin.H{"message": "Migration started", "migration_id": id})
}

// Stop stops a running migration
// @Summary Stop a migration
// @Description Stop a running migration
// @Tags migrations
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param id path int true "Migration ID"
// @Success 200 {object} map[string]string
// @Failure 400 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /migrations/{id}/stop [post]
func (h *MigrationsHandler) Stop(c *gin.Context) {
	userID := middleware.GetUserID(c)
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid migration ID"})
		return
	}

	result, err := db.DB.Exec(`
		UPDATE migrations SET status = 'failed', error = 'Stopped by user', updated_at = NOW()
		WHERE id = $1 AND user_id = $2 AND status = 'running'
	`, id, userID)

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to stop migration"})
		return
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Migration not found or not running"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Migration stopped"})
}

// GetStats returns dashboard statistics
// @Summary Get dashboard statistics
// @Description Get migration statistics for the current user's dashboard
// @Tags stats
// @Accept json
// @Produce json
// @Security BearerAuth
// @Success 200 {object} models.DashboardStats
// @Router /stats [get]
func (h *MigrationsHandler) GetStats(c *gin.Context) {
	userID := middleware.GetUserID(c)

	var stats models.DashboardStats

	// Get counts
	db.DB.Get(&stats.TotalMigrations, "SELECT COUNT(*) FROM migrations WHERE user_id = $1", userID)
	db.DB.Get(&stats.CompletedMigrations, "SELECT COUNT(*) FROM migrations WHERE user_id = $1 AND status = 'completed'", userID)
	db.DB.Get(&stats.RunningMigrations, "SELECT COUNT(*) FROM migrations WHERE user_id = $1 AND status = 'running'", userID)
	db.DB.Get(&stats.FailedMigrations, "SELECT COUNT(*) FROM migrations WHERE user_id = $1 AND status = 'failed'", userID)

	if stats.TotalMigrations > 0 {
		stats.SuccessRate = float64(stats.CompletedMigrations) / float64(stats.TotalMigrations) * 100
	}

	c.JSON(http.StatusOK, stats)
}

// GetFiles returns the list of generated dbt files for a migration
// @Summary Get migration files
// @Description Get list of generated dbt files for a migration
// @Tags migrations
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param id path int true "Migration ID"
// @Success 200 {object} map[string]interface{}
// @Failure 400 {object} map[string]string
// @Failure 404 {object} map[string]string
// @Failure 503 {object} map[string]string
// @Router /migrations/{id}/files [get]
func (h *MigrationsHandler) GetFiles(c *gin.Context) {
	userID := middleware.GetUserID(c)
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid migration ID"})
		return
	}

	// Verify user owns this migration
	var migration models.Migration
	err = db.DB.Get(&migration, "SELECT id FROM migrations WHERE id = $1 AND user_id = $2", id, userID)
	if err != nil {
		if err == sql.ErrNoRows {
			c.JSON(http.StatusNotFound, gin.H{"error": "Migration not found"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Database error"})
		return
	}

	// Get files from AI service
	aiClient := aiservice.GetClient()
	if aiClient == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "AI service not available"})
		return
	}

	files, err := aiClient.GetMigrationFiles(id)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, files)
}

// GetFileContent returns the content of a specific dbt file
// @Summary Get file content
// @Description Get the content of a specific generated dbt file
// @Tags migrations
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param id path int true "Migration ID"
// @Param filepath path string true "File path within the project"
// @Success 200 {object} map[string]interface{}
// @Failure 400 {object} map[string]string
// @Failure 404 {object} map[string]string
// @Failure 503 {object} map[string]string
// @Router /migrations/{id}/files/{filepath} [get]
func (h *MigrationsHandler) GetFileContent(c *gin.Context) {
	userID := middleware.GetUserID(c)
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid migration ID"})
		return
	}

	filePath := c.Param("filepath")
	// Gin's wildcard (*filepath) includes leading slash, strip it
	filePath = strings.TrimPrefix(filePath, "/")
	if filePath == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "File path required"})
		return
	}

	// Verify user owns this migration
	var migration models.Migration
	err = db.DB.Get(&migration, "SELECT id FROM migrations WHERE id = $1 AND user_id = $2", id, userID)
	if err != nil {
		if err == sql.ErrNoRows {
			c.JSON(http.StatusNotFound, gin.H{"error": "Migration not found"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Database error"})
		return
	}

	// Get file content from AI service
	aiClient := aiservice.GetClient()
	if aiClient == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "AI service not available"})
		return
	}

	content, err := aiClient.GetMigrationFileContent(id, filePath)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, content)
}

// DownloadProject returns the URL to download the dbt project
// @Summary Download dbt project
// @Description Get download URL for the completed dbt project as ZIP
// @Tags migrations
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param id path int true "Migration ID"
// @Success 200 {object} map[string]interface{}
// @Failure 400 {object} map[string]string
// @Failure 404 {object} map[string]string
// @Failure 503 {object} map[string]string
// @Router /migrations/{id}/download [get]
func (h *MigrationsHandler) DownloadProject(c *gin.Context) {
	userID := middleware.GetUserID(c)
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid migration ID"})
		return
	}

	// Verify user owns this migration
	var migration models.Migration
	err = db.DB.Get(&migration, "SELECT id, status FROM migrations WHERE id = $1 AND user_id = $2", id, userID)
	if err != nil {
		if err == sql.ErrNoRows {
			c.JSON(http.StatusNotFound, gin.H{"error": "Migration not found"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Database error"})
		return
	}

	if migration.Status != "completed" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Migration not completed yet"})
		return
	}

	// Get download URL from AI service
	aiClient := aiservice.GetClient()
	if aiClient == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "AI service not available"})
		return
	}

	downloadURL := aiClient.GetMigrationDownloadURL(id)

	c.JSON(http.StatusOK, gin.H{
		"download_url": downloadURL,
		"migration_id": id,
	})
}

// UpdateStatus updates migration status (internal endpoint for AI service)
// @Summary Update migration status (Internal)
// @Description Internal endpoint for AI service to update migration status
// @Tags internal
// @Accept json
// @Produce json
// @Param id path int true "Migration ID"
// @Param request body object true "Status update"
// @Success 200 {object} map[string]string
// @Failure 400 {object} map[string]string
// @Failure 404 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /internal/migrations/{id}/status [patch]
func (h *MigrationsHandler) UpdateStatus(c *gin.Context) {
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid migration ID"})
		return
	}

	var req struct {
		Status           string  `json:"status"`
		Progress         int     `json:"progress"`
		Error            *string `json:"error,omitempty"`
		TablesCount      *int    `json:"tables_count,omitempty"`
		ViewsCount       *int    `json:"views_count,omitempty"`
		ForeignKeysCount *int    `json:"foreign_keys_count,omitempty"`
		ModelsGenerated  *int    `json:"models_generated,omitempty"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Build the update query based on what's provided
	query := "UPDATE migrations SET status = $1, progress = $2, updated_at = NOW()"
	args := []interface{}{req.Status, req.Progress}
	argIndex := 3

	if req.Error != nil {
		query += ", error = $" + strconv.Itoa(argIndex)
		args = append(args, *req.Error)
		argIndex++
	}

	if req.TablesCount != nil {
		query += ", tables_count = $" + strconv.Itoa(argIndex)
		args = append(args, *req.TablesCount)
		argIndex++
	}

	if req.ViewsCount != nil {
		query += ", views_count = $" + strconv.Itoa(argIndex)
		args = append(args, *req.ViewsCount)
		argIndex++
	}

	if req.ForeignKeysCount != nil {
		query += ", foreign_keys_count = $" + strconv.Itoa(argIndex)
		args = append(args, *req.ForeignKeysCount)
		argIndex++
	}

	if req.ModelsGenerated != nil {
		query += ", models_generated = $" + strconv.Itoa(argIndex)
		args = append(args, *req.ModelsGenerated)
		argIndex++
	}

	if req.Status == "completed" {
		query += ", completed_at = NOW()"
	}

	query += " WHERE id = $" + strconv.Itoa(argIndex)
	args = append(args, id)

	result, err := db.DB.Exec(query, args...)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to update migration status"})
		return
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		c.JSON(http.StatusNotFound, gin.H{"error": "Migration not found"})
		return
	}

	// Send email notification for completed or failed migrations
	if req.Status == "completed" || req.Status == "failed" {
		go sendMigrationEmail(id, req.Status, req.Error)
	}

	c.JSON(http.StatusOK, gin.H{"message": "Status updated"})
}

// sendMigrationEmail sends email notification when migration completes or fails
func sendMigrationEmail(migrationID int64, status string, errorMsg *string) {
	// Get migration details and user info
	var migration struct {
		Name        string         `db:"name"`
		TablesCount int            `db:"tables_count"`
		CreatedAt   time.Time      `db:"created_at"`
		CompletedAt sql.NullTime   `db:"completed_at"`
		UserID      int64          `db:"user_id"`
	}

	err := db.DB.Get(&migration, `
		SELECT name, tables_count, created_at, completed_at, user_id
		FROM migrations WHERE id = $1
	`, migrationID)
	if err != nil {
		log.Printf("Failed to fetch migration for email notification: %v", err)
		return
	}

	// Get user info
	var user struct {
		Email     string `db:"email"`
		FirstName string `db:"first_name"`
	}

	err = db.DB.Get(&user, `
		SELECT email, first_name FROM users WHERE id = $1
	`, migration.UserID)
	if err != nil {
		log.Printf("Failed to fetch user for email notification: %v", err)
		return
	}

	// Initialize email service
	emailService := email.NewService()
	if !emailService.IsConfigured() {
		// Use mock service for development logging
		mockService := email.NewMockService()
		if status == "completed" {
			duration := "N/A"
			if migration.CompletedAt.Valid {
				duration = formatDuration(migration.CompletedAt.Time.Sub(migration.CreatedAt))
			}
			mockService.SendMigrationCompleteEmail(user.Email, user.FirstName, migration.Name, migration.TablesCount, duration)
		} else {
			errMessage := "Unknown error"
			if errorMsg != nil {
				errMessage = *errorMsg
			}
			mockService.SendMigrationFailedEmail(user.Email, user.FirstName, migration.Name, errMessage)
		}
		return
	}

	// Send actual email
	if status == "completed" {
		duration := "N/A"
		if migration.CompletedAt.Valid {
			duration = formatDuration(migration.CompletedAt.Time.Sub(migration.CreatedAt))
		}
		err = emailService.SendMigrationCompleteEmail(user.Email, user.FirstName, migration.Name, migration.TablesCount, duration)
	} else {
		errMessage := "Unknown error"
		if errorMsg != nil {
			errMessage = *errorMsg
		}
		err = emailService.SendMigrationFailedEmail(user.Email, user.FirstName, migration.Name, errMessage)
	}

	if err != nil {
		log.Printf("Failed to send migration %s email: %v", status, err)
	} else {
		log.Printf("Sent migration %s email to %s for migration '%s'", status, user.Email, migration.Name)
	}
}

// formatDuration formats a duration into a human-readable string
func formatDuration(d time.Duration) string {
	if d < time.Minute {
		return fmt.Sprintf("%d seconds", int(d.Seconds()))
	} else if d < time.Hour {
		mins := int(d.Minutes())
		secs := int(d.Seconds()) % 60
		return fmt.Sprintf("%d min %d sec", mins, secs)
	}
	hours := int(d.Hours())
	mins := int(d.Minutes()) % 60
	return fmt.Sprintf("%d hr %d min", hours, mins)
}
