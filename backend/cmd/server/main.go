package main

import (
	"log"

	"github.com/datamigrate-ai/backend/internal/api"
	"github.com/datamigrate-ai/backend/internal/config"
	"github.com/datamigrate-ai/backend/internal/db"
)

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

	// Setup router
	router := api.SetupRouter(cfg)

	// Start server
	addr := cfg.ServerHost + ":" + cfg.ServerPort
	log.Printf("Starting DataMigrate API server on %s", addr)
	if err := router.Run(addr); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
