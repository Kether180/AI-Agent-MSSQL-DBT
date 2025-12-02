package db

import (
	"fmt"
	"log"

	"github.com/datamigrate-ai/backend/internal/config"
	"github.com/jmoiron/sqlx"
	_ "github.com/lib/pq"
)

var DB *sqlx.DB

func Connect(cfg *config.Config) error {
	dsn := cfg.GetDSN()

	var err error
	DB, err = sqlx.Connect("postgres", dsn)
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}

	// Test connection
	if err := DB.Ping(); err != nil {
		return fmt.Errorf("failed to ping database: %w", err)
	}

	log.Println("Connected to PostgreSQL database")
	return nil
}

func Close() {
	if DB != nil {
		DB.Close()
	}
}

// RunMigrations creates all necessary tables
func RunMigrations() error {
	schema := `
	-- Organizations table (companies/teams)
	CREATE TABLE IF NOT EXISTS organizations (
		id SERIAL PRIMARY KEY,
		name VARCHAR(255) NOT NULL,
		slug VARCHAR(255) UNIQUE NOT NULL,
		plan VARCHAR(50) DEFAULT 'free',
		max_users INTEGER DEFAULT 5,
		max_migrations INTEGER DEFAULT 10,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	);

	-- Users table
	CREATE TABLE IF NOT EXISTS users (
		id SERIAL PRIMARY KEY,
		email VARCHAR(255) UNIQUE NOT NULL,
		password VARCHAR(255) NOT NULL,
		first_name VARCHAR(100),
		last_name VARCHAR(100),
		job_title VARCHAR(100),
		phone VARCHAR(50),
		organization_id INTEGER REFERENCES organizations(id) ON DELETE SET NULL,
		role VARCHAR(50) DEFAULT 'member',
		is_admin BOOLEAN DEFAULT FALSE,
		is_active BOOLEAN DEFAULT TRUE,
		last_login_at TIMESTAMP,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	);

	-- Organization invitations table
	CREATE TABLE IF NOT EXISTS organization_invitations (
		id SERIAL PRIMARY KEY,
		organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
		email VARCHAR(255) NOT NULL,
		role VARCHAR(50) DEFAULT 'member',
		token VARCHAR(255) UNIQUE NOT NULL,
		invited_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
		expires_at TIMESTAMP NOT NULL,
		accepted_at TIMESTAMP,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	);

	-- Migrations table (organization_id added via ALTER TABLE for existing tables)
	CREATE TABLE IF NOT EXISTS migrations (
		id SERIAL PRIMARY KEY,
		name VARCHAR(255) NOT NULL,
		status VARCHAR(50) DEFAULT 'pending',
		progress INTEGER DEFAULT 0,
		source_database VARCHAR(255),
		target_project VARCHAR(255),
		tables_count INTEGER DEFAULT 0,
		user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
		error TEXT,
		config JSONB,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		completed_at TIMESTAMP,
		updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	);

	-- Database connections table (organization_id added via ALTER TABLE for existing tables)
	CREATE TABLE IF NOT EXISTS database_connections (
		id SERIAL PRIMARY KEY,
		name VARCHAR(255) NOT NULL,
		db_type VARCHAR(50) NOT NULL,
		host VARCHAR(255) NOT NULL,
		port INTEGER NOT NULL,
		database_name VARCHAR(255) NOT NULL,
		username VARCHAR(255) NOT NULL,
		password VARCHAR(255) NOT NULL,
		is_source BOOLEAN DEFAULT TRUE,
		user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	);

	-- API keys table
	CREATE TABLE IF NOT EXISTS api_keys (
		id SERIAL PRIMARY KEY,
		name VARCHAR(255) NOT NULL,
		key VARCHAR(255) NOT NULL,
		is_active BOOLEAN DEFAULT TRUE,
		rate_limit INTEGER DEFAULT 1000,
		user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
		last_used_at TIMESTAMP,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	);

	-- Migration logs table (for detailed progress tracking)
	CREATE TABLE IF NOT EXISTS migration_logs (
		id SERIAL PRIMARY KEY,
		migration_id INTEGER REFERENCES migrations(id) ON DELETE CASCADE,
		level VARCHAR(20) NOT NULL,
		message TEXT NOT NULL,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	);

	-- Security audit logs table (Guardian Agent)
	CREATE TABLE IF NOT EXISTS security_audit_logs (
		id SERIAL PRIMARY KEY,
		event_type VARCHAR(50) NOT NULL,
		severity VARCHAR(20) NOT NULL,
		user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
		organization_id INTEGER REFERENCES organizations(id) ON DELETE SET NULL,
		ip_address VARCHAR(45),
		user_agent TEXT,
		endpoint VARCHAR(255),
		method VARCHAR(10),
		request_body TEXT,
		response_status INTEGER,
		blocked BOOLEAN DEFAULT FALSE,
		block_reason TEXT,
		metadata JSONB,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	);

	-- Rate limiting table
	CREATE TABLE IF NOT EXISTS rate_limits (
		id SERIAL PRIMARY KEY,
		identifier VARCHAR(255) NOT NULL,
		endpoint VARCHAR(255) NOT NULL,
		request_count INTEGER DEFAULT 1,
		window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		UNIQUE(identifier, endpoint)
	);

	-- Security policies table
	CREATE TABLE IF NOT EXISTS security_policies (
		id SERIAL PRIMARY KEY,
		name VARCHAR(255) NOT NULL,
		description TEXT,
		policy_type VARCHAR(50) NOT NULL,
		rules JSONB NOT NULL,
		is_active BOOLEAN DEFAULT TRUE,
		organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	);

	-- Blocked patterns table (for suspicious input detection)
	CREATE TABLE IF NOT EXISTS blocked_patterns (
		id SERIAL PRIMARY KEY,
		pattern TEXT NOT NULL,
		pattern_type VARCHAR(50) NOT NULL,
		description TEXT,
		severity VARCHAR(20) DEFAULT 'medium',
		is_active BOOLEAN DEFAULT TRUE,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	);

	-- Create indexes (indexes for organization_id columns created after ALTER TABLE)
	CREATE INDEX IF NOT EXISTS idx_organizations_slug ON organizations(slug);
	CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
	CREATE INDEX IF NOT EXISTS idx_organization_invitations_token ON organization_invitations(token);
	CREATE INDEX IF NOT EXISTS idx_organization_invitations_email ON organization_invitations(email);
	CREATE INDEX IF NOT EXISTS idx_migrations_user_id ON migrations(user_id);
	CREATE INDEX IF NOT EXISTS idx_migrations_status ON migrations(status);
	CREATE INDEX IF NOT EXISTS idx_database_connections_user_id ON database_connections(user_id);
	CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
	CREATE INDEX IF NOT EXISTS idx_migration_logs_migration_id ON migration_logs(migration_id);
	CREATE INDEX IF NOT EXISTS idx_security_audit_logs_user_id ON security_audit_logs(user_id);
	CREATE INDEX IF NOT EXISTS idx_security_audit_logs_org_id ON security_audit_logs(organization_id);
	CREATE INDEX IF NOT EXISTS idx_security_audit_logs_event_type ON security_audit_logs(event_type);
	CREATE INDEX IF NOT EXISTS idx_security_audit_logs_created_at ON security_audit_logs(created_at);
	CREATE INDEX IF NOT EXISTS idx_rate_limits_identifier ON rate_limits(identifier);
	CREATE INDEX IF NOT EXISTS idx_blocked_patterns_type ON blocked_patterns(pattern_type);
	`

	_, err := DB.Exec(schema)
	if err != nil {
		return fmt.Errorf("failed to run migrations: %w", err)
	}

	// Run ALTER TABLE migrations for existing tables
	if err := runAlterTableMigrations(); err != nil {
		log.Printf("Warning: Some ALTER TABLE migrations failed (may already exist): %v", err)
	}

	log.Println("Database migrations completed")
	return nil
}

// runAlterTableMigrations adds new columns to existing tables
func runAlterTableMigrations() error {
	alterStatements := []string{
		// Add new columns to users table
		"ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR(100)",
		"ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name VARCHAR(100)",
		"ALTER TABLE users ADD COLUMN IF NOT EXISTS job_title VARCHAR(100)",
		"ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(50)",
		"ALTER TABLE users ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES organizations(id) ON DELETE SET NULL",
		"ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'member'",
		"ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE",
		"ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP",

		// Add organization_id to migrations table
		"ALTER TABLE migrations ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE",

		// Add organization_id to database_connections table
		"ALTER TABLE database_connections ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE",

		// Create indexes for organization_id columns
		"CREATE INDEX IF NOT EXISTS idx_users_organization_id ON users(organization_id)",
		"CREATE INDEX IF NOT EXISTS idx_migrations_organization_id ON migrations(organization_id)",
		"CREATE INDEX IF NOT EXISTS idx_database_connections_organization_id ON database_connections(organization_id)",
	}

	for _, stmt := range alterStatements {
		_, err := DB.Exec(stmt)
		if err != nil {
			// Log but continue - column/index might already exist
			log.Printf("Migration statement warning: %v", err)
		}
	}

	return nil
}
