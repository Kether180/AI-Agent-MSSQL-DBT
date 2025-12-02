package api

import (
	"database/sql"
	"encoding/json"
	"log"
	"net/http"
	"strconv"

	"github.com/datamigrate-ai/backend/internal/aiservice"
	"github.com/datamigrate-ai/backend/internal/db"
	"github.com/datamigrate-ai/backend/internal/middleware"
	"github.com/datamigrate-ai/backend/internal/models"
	"github.com/gin-gonic/gin"
)

type MigrationsHandler struct{}

func NewMigrationsHandler() *MigrationsHandler {
	return &MigrationsHandler{}
}

// GetAll returns all migrations for the current user
func (h *MigrationsHandler) GetAll(c *gin.Context) {
	userID := middleware.GetUserID(c)

	var migrations []models.Migration
	err := db.DB.Select(&migrations, `
		SELECT id, name, status, progress, source_database, target_project,
		       tables_count, user_id, error, created_at, completed_at, updated_at
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
		       tables_count, user_id, error, config, created_at, completed_at, updated_at
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
		ID       int64  `db:"id"`
		Name     string `db:"name"`
		DBType   string `db:"db_type"`
		Host     string `db:"host"`
		Port     int    `db:"port"`
		Database string `db:"database_name"`
		Username string `db:"username"`
		Password string `db:"password"`
	}

	err = db.DB.Get(&connection, `
		SELECT id, name, db_type, host, port, database_name, username, password
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
				"type":     connection.DBType,
				"host":     connection.Host,
				"port":     connection.Port,
				"database": connection.Database,
				"username": connection.Username,
				"password": connection.Password,
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

// UpdateStatus updates migration status (internal endpoint for AI service)
func (h *MigrationsHandler) UpdateStatus(c *gin.Context) {
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid migration ID"})
		return
	}

	var req struct {
		Status   string  `json:"status"`
		Progress int     `json:"progress"`
		Error    *string `json:"error,omitempty"`
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

	c.JSON(http.StatusOK, gin.H{"message": "Status updated"})
}
