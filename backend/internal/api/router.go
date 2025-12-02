package api

import (
	"net/http"

	"github.com/datamigrate-ai/backend/internal/config"
	"github.com/datamigrate-ai/backend/internal/middleware"
	"github.com/datamigrate-ai/backend/internal/security"
	"github.com/gin-gonic/gin"
)

func SetupRouter(cfg *config.Config) *gin.Engine {
	router := gin.Default()

	// Initialize JWT middleware
	middleware.InitJWT(cfg)

	// Initialize Guardian Agent (Security Layer)
	guardian := security.GetGuardian()
	router.Use(guardian.Middleware())

	// CORS middleware
	router.Use(func(c *gin.Context) {
		origin := c.Request.Header.Get("Origin")

		// Check if origin is allowed
		allowed := false
		for _, o := range cfg.AllowedOrigins {
			if o == origin {
				allowed = true
				break
			}
		}

		if allowed {
			c.Header("Access-Control-Allow-Origin", origin)
			c.Header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS, PATCH")
			c.Header("Access-Control-Allow-Headers", "Origin, Content-Type, Authorization, Accept")
			c.Header("Access-Control-Allow-Credentials", "true")
			c.Header("Access-Control-Max-Age", "86400")
		}

		if c.Request.Method == http.MethodOptions {
			c.AbortWithStatus(http.StatusNoContent)
			return
		}

		c.Next()
	})

	// Health check
	router.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{"status": "ok", "service": "datamigrate-api"})
	})

	// API v1 routes
	v1 := router.Group("/api/v1")

	// Create handlers
	authHandler := NewAuthHandler(cfg)
	migrationsHandler := NewMigrationsHandler()
	connectionsHandler := NewConnectionsHandler()
	apiKeysHandler := NewAPIKeysHandler()
	securityHandler := NewSecurityHandler()

	// Auth routes (public)
	auth := v1.Group("/auth")
	auth.POST("/register", authHandler.Register)
	auth.POST("/login", authHandler.Login)

	// Protected routes
	protected := v1.Group("")
	protected.Use(middleware.AuthMiddleware())

	// Auth (protected)
	protected.GET("/auth/me", authHandler.GetCurrentUser)
	protected.POST("/auth/logout", authHandler.Logout)
	protected.PUT("/auth/profile", authHandler.UpdateProfile)
	protected.PUT("/auth/password", authHandler.ChangePassword)

	// Migrations
	migrations := protected.Group("/migrations")
	migrations.GET("", migrationsHandler.GetAll)
	migrations.GET("/:id", migrationsHandler.GetOne)
	migrations.POST("", migrationsHandler.Create)
	migrations.DELETE("/:id", migrationsHandler.Delete)
	migrations.POST("/:id/start", migrationsHandler.Start)
	migrations.POST("/:id/stop", migrationsHandler.Stop)

	// Stats
	protected.GET("/stats", migrationsHandler.GetStats)

	// Database connections
	connections := protected.Group("/connections")
	connections.GET("", connectionsHandler.GetAll)
	connections.GET("/:id", connectionsHandler.GetOne)
	connections.POST("", connectionsHandler.Create)
	connections.PUT("/:id", connectionsHandler.Update)
	connections.DELETE("/:id", connectionsHandler.Delete)
	connections.POST("/:id/test", connectionsHandler.Test)

	// API Keys
	apiKeys := protected.Group("/api-keys")
	apiKeys.GET("", apiKeysHandler.GetAll)
	apiKeys.POST("", apiKeysHandler.Create)
	apiKeys.DELETE("/:id", apiKeysHandler.Delete)
	apiKeys.PUT("/:id/toggle", apiKeysHandler.Toggle)

	// Security routes (admin only)
	securityRoutes := protected.Group("/security")
	securityRoutes.GET("/audit-logs", securityHandler.GetAuditLogs)
	securityRoutes.GET("/stats", securityHandler.GetSecurityStats)
	securityRoutes.GET("/dashboard", securityHandler.GetSecurityDashboard)
	securityRoutes.POST("/validate", securityHandler.ValidateInput)
	securityRoutes.GET("/rate-limit", securityHandler.GetRateLimitStatus)
	securityRoutes.POST("/reload-policies", securityHandler.ReloadPolicies)

	// Internal routes (for AI service communication - no auth required)
	internal := v1.Group("/internal")
	internal.PATCH("/migrations/:id/status", migrationsHandler.UpdateStatus)

	return router
}
