package middleware

import (
	"net/http"
	"strings"
	"time"

	"github.com/datamigrate-ai/backend/internal/config"
	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
)

type Claims struct {
	UserID  int64  `json:"user_id"`
	Email   string `json:"email"`
	IsAdmin bool   `json:"is_admin"`
	jwt.RegisteredClaims
}

var jwtSecret []byte

func InitJWT(cfg *config.Config) {
	jwtSecret = []byte(cfg.JWTSecret)
}

// GenerateToken creates a new JWT token for a user
func GenerateToken(userID int64, email string, isAdmin bool, expirationHours int) (string, error) {
	claims := &Claims{
		UserID:  userID,
		Email:   email,
		IsAdmin: isAdmin,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(time.Duration(expirationHours) * time.Hour)),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
			Issuer:    "datamigrate-ai",
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString(jwtSecret)
}

// ValidateToken validates a JWT token and returns the claims
func ValidateToken(tokenString string) (*Claims, error) {
	token, err := jwt.ParseWithClaims(tokenString, &Claims{}, func(token *jwt.Token) (interface{}, error) {
		return jwtSecret, nil
	})

	if err != nil {
		return nil, err
	}

	if claims, ok := token.Claims.(*Claims); ok && token.Valid {
		return claims, nil
	}

	return nil, jwt.ErrSignatureInvalid
}

// AuthMiddleware is a Gin middleware that validates JWT tokens
func AuthMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		authHeader := c.GetHeader("Authorization")
		if authHeader == "" {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Authorization header required"})
			c.Abort()
			return
		}

		// Extract token from "Bearer <token>"
		parts := strings.Split(authHeader, " ")
		if len(parts) != 2 || parts[0] != "Bearer" {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid authorization header format"})
			c.Abort()
			return
		}

		tokenString := parts[1]
		claims, err := ValidateToken(tokenString)
		if err != nil {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid or expired token"})
			c.Abort()
			return
		}

		// Store user info in context
		c.Set("user_id", claims.UserID)
		c.Set("email", claims.Email)
		c.Set("is_admin", claims.IsAdmin)

		c.Next()
	}
}

// AdminMiddleware ensures the user is an admin
func AdminMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		isAdmin, exists := c.Get("is_admin")
		if !exists || !isAdmin.(bool) {
			c.JSON(http.StatusForbidden, gin.H{"error": "Admin access required"})
			c.Abort()
			return
		}
		c.Next()
	}
}

// GetUserID extracts user ID from context
func GetUserID(c *gin.Context) int64 {
	userID, _ := c.Get("user_id")
	return userID.(int64)
}

// IsAdmin checks if the current user is an admin
func IsAdmin(c *gin.Context) bool {
	isAdmin, exists := c.Get("is_admin")
	if !exists {
		return false
	}
	return isAdmin.(bool)
}

// GetOrganizationID extracts organization ID from context
func GetOrganizationID(c *gin.Context) int64 {
	orgID, exists := c.Get("organization_id")
	if !exists {
		return 0
	}
	if id, ok := orgID.(int64); ok {
		return id
	}
	return 0
}
