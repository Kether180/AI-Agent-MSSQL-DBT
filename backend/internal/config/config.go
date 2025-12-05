package config

import (
	"os"
	"strconv"

	"github.com/joho/godotenv"
)

type Config struct {
	// Server
	ServerPort string
	ServerHost string

	// Database
	DBHost     string
	DBPort     string
	DBUser     string
	DBPassword string
	DBName     string
	DBSSLMode  string

	// JWT
	JWTSecret     string
	JWTExpiration int // hours

	// Encryption - for encrypting sensitive data like database passwords
	EncryptionKey string // 32-byte key for AES-256, base64 encoded or raw 32 chars

	// CORS
	AllowedOrigins []string

	// AI Service
	AIServiceURL string

	// Static files (frontend)
	StaticDir string

	// Environment
	Environment string // development, staging, production
}

func Load() (*Config, error) {
	// Load .env file if exists
	godotenv.Load()

	cfg := &Config{
		// Server defaults
		ServerPort: getEnv("SERVER_PORT", "8080"),
		ServerHost: getEnv("SERVER_HOST", "0.0.0.0"),

		// Database defaults
		DBHost:     getEnv("DB_HOST", "localhost"),
		DBPort:     getEnv("DB_PORT", "5432"),
		DBUser:     getEnv("DB_USER", "datamigrate"),
		DBPassword: getEnv("DB_PASSWORD", "datamigrate123"),
		DBName:     getEnv("DB_NAME", "datamigrate"),
		DBSSLMode:  getEnv("DB_SSL_MODE", "disable"),

		// JWT defaults
		JWTSecret:     getEnv("JWT_SECRET", "your-super-secret-jwt-key-change-in-production"),
		JWTExpiration: getEnvInt("JWT_EXPIRATION_HOURS", 24),

		// CORS
		AllowedOrigins: []string{
			"http://localhost:5173",
			"http://localhost:5174",
			"http://localhost:3000",
		},

		// AI Service (Python FastAPI microservice)
		AIServiceURL: getEnv("AI_SERVICE_URL", "http://localhost:8081"),

		// Static files directory (frontend build output)
		StaticDir: getEnv("STATIC_DIR", ""),

		// Encryption key for database credentials (REQUIRED in production)
		// Generate with: openssl rand -base64 32
		EncryptionKey: getEnv("ENCRYPTION_KEY", ""),

		// Environment
		Environment: getEnv("ENVIRONMENT", "development"),
	}

	return cfg, nil
}

// IsProduction returns true if running in production environment
func (c *Config) IsProduction() bool {
	return c.Environment == "production"
}

// IsDevelopment returns true if running in development environment
func (c *Config) IsDevelopment() bool {
	return c.Environment == "development" || c.Environment == ""
}

func (c *Config) GetDSN() string {
	return "host=" + c.DBHost +
		" port=" + c.DBPort +
		" user=" + c.DBUser +
		" password=" + c.DBPassword +
		" dbname=" + c.DBName +
		" sslmode=" + c.DBSSLMode
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getEnvInt(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		if intVal, err := strconv.Atoi(value); err == nil {
			return intVal
		}
	}
	return defaultValue
}
