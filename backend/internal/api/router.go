package api

import (
	"net/http"

	"github.com/datamigrate-ai/backend/internal/config"
	"github.com/datamigrate-ai/backend/internal/metrics"
	"github.com/datamigrate-ai/backend/internal/middleware"
	"github.com/datamigrate-ai/backend/internal/security"
	"github.com/gin-gonic/gin"
	swaggerFiles "github.com/swaggo/files"
	ginSwagger "github.com/swaggo/gin-swagger"
)

func SetupRouter(cfg *config.Config) *gin.Engine {
	router := gin.Default()

	// Initialize JWT middleware
	middleware.InitJWT(cfg)

	// Security Headers middleware (first layer of defense)
	securityHeadersConfig := security.DefaultSecurityHeadersConfig()
	router.Use(security.SecurityHeadersMiddleware(securityHeadersConfig))

	// Prometheus metrics middleware (before other middleware)
	router.Use(metrics.PrometheusMiddleware())

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

	// Prometheus metrics endpoint
	router.GET("/metrics", metrics.Handler())

	// Swagger documentation endpoint
	router.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler))

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
	auth.POST("/forgot-password", authHandler.ForgotPassword)
	auth.POST("/reset-password", authHandler.ResetPassword)

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
	migrations.GET("/:id/files", migrationsHandler.GetFiles)
	migrations.GET("/:id/files/*filepath", migrationsHandler.GetFileContent)
	migrations.GET("/:id/download", migrationsHandler.DownloadProject)

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
	connections.GET("/:id/metadata", connectionsHandler.GetMetadata)

	// API Keys
	apiKeys := protected.Group("/api-keys")
	apiKeys.GET("", apiKeysHandler.GetAll)
	apiKeys.POST("", apiKeysHandler.Create)
	apiKeys.DELETE("/:id", apiKeysHandler.Delete)
	apiKeys.PUT("/:id/toggle", apiKeysHandler.Toggle)

	// AI Chat (proxies to Python AI service)
	chatHandler := NewChatHandler(cfg)
	protected.POST("/chat", chatHandler.Chat)

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
