package api

import (
	"crypto/rand"
	"encoding/hex"
	"net/http"
	"strconv"

	"github.com/datamigrate-ai/backend/internal/db"
	"github.com/datamigrate-ai/backend/internal/middleware"
	"github.com/datamigrate-ai/backend/internal/models"
	"github.com/gin-gonic/gin"
)

type APIKeysHandler struct{}

func NewAPIKeysHandler() *APIKeysHandler {
	return &APIKeysHandler{}
}

// generateAPIKey generates a random API key
func generateAPIKey() (string, error) {
	bytes := make([]byte, 32)
	if _, err := rand.Read(bytes); err != nil {
		return "", err
	}
	return "dm_" + hex.EncodeToString(bytes), nil
}

// GetAll returns all API keys for the current user
func (h *APIKeysHandler) GetAll(c *gin.Context) {
	userID := middleware.GetUserID(c)

	var keys []models.APIKey
	err := db.DB.Select(&keys, `
		SELECT id, name, key, is_active, rate_limit, user_id, created_at, last_used_at
		FROM api_keys
		WHERE user_id = $1
		ORDER BY created_at DESC
	`, userID)

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch API keys"})
		return
	}

	if keys == nil {
		keys = []models.APIKey{}
	}

	// Mask the keys for security (show only first 8 and last 4 characters)
	for i := range keys {
		if len(keys[i].Key) > 12 {
			keys[i].Key = keys[i].Key[:8] + "..." + keys[i].Key[len(keys[i].Key)-4:]
		}
	}

	c.JSON(http.StatusOK, keys)
}

// Create creates a new API key
func (h *APIKeysHandler) Create(c *gin.Context) {
	userID := middleware.GetUserID(c)

	var req models.CreateAPIKeyRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Generate API key
	key, err := generateAPIKey()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to generate API key"})
		return
	}

	rateLimit := req.RateLimit
	if rateLimit == 0 {
		rateLimit = 1000 // Default rate limit
	}

	var keyID int64
	err = db.DB.QueryRow(`
		INSERT INTO api_keys (name, key, rate_limit, user_id)
		VALUES ($1, $2, $3, $4)
		RETURNING id
	`, req.Name, key, rateLimit, userID).Scan(&keyID)

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create API key"})
		return
	}

	// Return the full key only once during creation
	c.JSON(http.StatusCreated, gin.H{
		"id":         keyID,
		"name":       req.Name,
		"key":        key,
		"rate_limit": rateLimit,
		"message":    "Save this key securely. It won't be shown again.",
	})
}

// Delete deletes an API key
func (h *APIKeysHandler) Delete(c *gin.Context) {
	userID := middleware.GetUserID(c)
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid API key ID"})
		return
	}

	result, err := db.DB.Exec("DELETE FROM api_keys WHERE id = $1 AND user_id = $2", id, userID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to delete API key"})
		return
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		c.JSON(http.StatusNotFound, gin.H{"error": "API key not found"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "API key deleted"})
}

// Toggle toggles an API key's active status
func (h *APIKeysHandler) Toggle(c *gin.Context) {
	userID := middleware.GetUserID(c)
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid API key ID"})
		return
	}

	result, err := db.DB.Exec(`
		UPDATE api_keys SET is_active = NOT is_active
		WHERE id = $1 AND user_id = $2
	`, id, userID)

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to toggle API key"})
		return
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		c.JSON(http.StatusNotFound, gin.H{"error": "API key not found"})
		return
	}

	var key models.APIKey
	db.DB.Get(&key, "SELECT id, name, is_active FROM api_keys WHERE id = $1", id)

	c.JSON(http.StatusOK, gin.H{
		"message":   "API key toggled",
		"is_active": key.IsActive,
	})
}
