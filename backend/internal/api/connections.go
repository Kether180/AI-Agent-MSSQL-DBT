package api

import (
	"database/sql"
	"net/http"
	"strconv"

	"github.com/datamigrate-ai/backend/internal/db"
	"github.com/datamigrate-ai/backend/internal/dbtest"
	"github.com/datamigrate-ai/backend/internal/middleware"
	"github.com/datamigrate-ai/backend/internal/models"
	"github.com/gin-gonic/gin"
)

type ConnectionsHandler struct{}

func NewConnectionsHandler() *ConnectionsHandler {
	return &ConnectionsHandler{}
}

// GetAll returns all database connections for the current user
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
func (h *ConnectionsHandler) Create(c *gin.Context) {
	userID := middleware.GetUserID(c)

	var req models.CreateConnectionRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	var connectionID int64
	err := db.DB.QueryRow(`
		INSERT INTO database_connections (name, db_type, host, port, database_name, username, password, is_source, user_id)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
		RETURNING id
	`, req.Name, req.DBType, req.Host, req.Port, req.DatabaseName, req.Username, req.Password, req.IsSource, userID).Scan(&connectionID)

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

	result, err := db.DB.Exec(`
		UPDATE database_connections
		SET name = $1, db_type = $2, host = $3, port = $4, database_name = $5,
		    username = $6, password = $7, is_source = $8, updated_at = NOW()
		WHERE id = $9 AND user_id = $10
	`, req.Name, req.DBType, req.Host, req.Port, req.DatabaseName, req.Username, req.Password, req.IsSource, id, userID)

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
func (h *ConnectionsHandler) Test(c *gin.Context) {
	userID := middleware.GetUserID(c)
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid connection ID"})
		return
	}

	// Fetch connection with password for testing
	var connection struct {
		ID       int64  `db:"id"`
		DBType   string `db:"db_type"`
		Host     string `db:"host"`
		Port     int    `db:"port"`
		Database string `db:"database_name"`
		Username string `db:"username"`
		Password string `db:"password"`
	}

	err = db.DB.Get(&connection, `
		SELECT id, db_type, host, port, database_name, username, password
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

	// Test the actual database connection
	result := dbtest.TestConnection(dbtest.ConnectionParams{
		DBType:   connection.DBType,
		Host:     connection.Host,
		Port:     connection.Port,
		Database: connection.Database,
		Username: connection.Username,
		Password: connection.Password,
	})

	if result.Success {
		c.JSON(http.StatusOK, result)
	} else {
		c.JSON(http.StatusBadRequest, result)
	}
}
