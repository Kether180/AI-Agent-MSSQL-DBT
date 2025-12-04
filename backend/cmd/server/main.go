package main

import (
	"log"

	"github.com/datamigrate-ai/backend/internal/aiservice"
	"github.com/datamigrate-ai/backend/internal/api"
	"github.com/datamigrate-ai/backend/internal/config"
	"github.com/datamigrate-ai/backend/internal/crypto"
	"github.com/datamigrate-ai/backend/internal/db"

	_ "github.com/datamigrate-ai/backend/docs" // swagger docs
)

// @title DataMigrate AI API
// @version 1.0
// @description AI-powered MSSQL to dbt migration service API
// @termsOfService http://swagger.io/terms/

// @contact.name API Support
// @contact.url http://www.datamigrate.ai/support
// @contact.email support@datamigrate.ai

// @license.name Apache 2.0
// @license.url http://www.apache.org/licenses/LICENSE-2.0.html

// @host localhost:8080
// @BasePath /api/v1

// @securityDefinitions.apikey BearerAuth
// @in header
// @name Authorization
// @description Enter your JWT token with the `Bearer ` prefix

func main() {
	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Failed to load config: %v", err)
	}

	// Connect to database
	if err := db.Connect(cfg); err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	defer db.DB.Close()

	// Run database migrations
	if err := db.RunMigrations(); err != nil {
		log.Fatalf("Failed to run migrations: %v", err)
	}

	// Run RAG migrations (pgvector - optional, won't fail if extension not available)
	if err := db.RunRAGMigrations(); err != nil {
		log.Printf("Warning: RAG migrations failed: %v", err)
	}

	// Initialize encryption service for database credential security
	if cfg.EncryptionKey != "" {
		encService := crypto.GetEncryptionService()
		if err := encService.SetKeyFromString(cfg.EncryptionKey); err != nil {
			log.Printf("Warning: Failed to initialize encryption: %v", err)
			log.Printf("Database passwords will be stored in plaintext!")
		} else {
			log.Printf("Encryption service initialized (AES-256-GCM)")
		}
	} else {
		if cfg.IsProduction() {
			log.Printf("WARNING: ENCRYPTION_KEY not set in production! Database passwords will be stored in plaintext!")
		} else {
			log.Printf("Note: ENCRYPTION_KEY not set. Set it for encrypted password storage.")
		}
	}

	// Initialize AI service client
	aiservice.Init(cfg.AIServiceURL)
	log.Printf("AI service client initialized: %s", cfg.AIServiceURL)

	// Setup router
	router := api.SetupRouter(cfg)

	// Start server
	addr := cfg.ServerHost + ":" + cfg.ServerPort
	log.Printf("Starting DataMigrate API server on %s", addr)
	if err := router.Run(addr); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
