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
		views_count INTEGER DEFAULT 0,
		foreign_keys_count INTEGER DEFAULT 0,
		models_generated INTEGER DEFAULT 0,
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
		username VARCHAR(255),
		password VARCHAR(255),
		use_windows_auth BOOLEAN DEFAULT FALSE,
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

	-- Warehouse deployments table (for tracking dbt deployments)
	CREATE TABLE IF NOT EXISTS warehouse_deployments (
		id SERIAL PRIMARY KEY,
		migration_id INTEGER REFERENCES migrations(id) ON DELETE CASCADE,
		connection_id INTEGER REFERENCES database_connections(id) ON DELETE CASCADE,
		status VARCHAR(50) DEFAULT 'pending',
		dbt_run_status VARCHAR(50),
		dbt_test_status VARCHAR(50),
		tables_created INTEGER DEFAULT 0,
		tests_passed INTEGER DEFAULT 0,
		tests_failed INTEGER DEFAULT 0,
		dbt_run_output TEXT,
		dbt_test_output TEXT,
		error TEXT,
		user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		completed_at TIMESTAMP
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

	-- Password reset tokens table
	CREATE TABLE IF NOT EXISTS password_reset_tokens (
		id SERIAL PRIMARY KEY,
		user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
		token VARCHAR(255) UNIQUE NOT NULL,
		expires_at TIMESTAMP NOT NULL,
		used_at TIMESTAMP,
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
	CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_token ON password_reset_tokens(token);
	CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user_id ON password_reset_tokens(user_id);
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

		// Add migration metadata columns
		"ALTER TABLE migrations ADD COLUMN IF NOT EXISTS views_count INTEGER DEFAULT 0",
		"ALTER TABLE migrations ADD COLUMN IF NOT EXISTS foreign_keys_count INTEGER DEFAULT 0",
		"ALTER TABLE migrations ADD COLUMN IF NOT EXISTS models_generated INTEGER DEFAULT 0",

		// Add organization_id to database_connections table
		"ALTER TABLE database_connections ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE",

		// Add use_windows_auth column to database_connections table
		"ALTER TABLE database_connections ADD COLUMN IF NOT EXISTS use_windows_auth BOOLEAN DEFAULT FALSE",

		// Make username and password nullable for Windows Auth
		"ALTER TABLE database_connections ALTER COLUMN username DROP NOT NULL",
		"ALTER TABLE database_connections ALTER COLUMN password DROP NOT NULL",

		// Add extra_config for warehouse-specific settings (Snowflake, BigQuery, Databricks)
		"ALTER TABLE database_connections ADD COLUMN IF NOT EXISTS extra_config JSONB",

		// Create indexes for organization_id columns
		"CREATE INDEX IF NOT EXISTS idx_users_organization_id ON users(organization_id)",
		"CREATE INDEX IF NOT EXISTS idx_migrations_organization_id ON migrations(organization_id)",
		"CREATE INDEX IF NOT EXISTS idx_database_connections_organization_id ON database_connections(organization_id)",
		"CREATE INDEX IF NOT EXISTS idx_warehouse_deployments_migration_id ON warehouse_deployments(migration_id)",
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

// RunRAGMigrations sets up pgvector extension and RAG tables
func RunRAGMigrations() error {
	// Enable pgvector extension (requires superuser or extension already installed)
	_, err := DB.Exec("CREATE EXTENSION IF NOT EXISTS vector")
	if err != nil {
		log.Printf("Warning: Could not create vector extension (may need superuser): %v", err)
		log.Println("RAG features will be disabled until pgvector is installed")
		return nil // Don't fail - RAG is optional
	}

	ragSchema := `
	-- Schema pattern embeddings (for learning from migrations)
	CREATE TABLE IF NOT EXISTS schema_embeddings (
		id SERIAL PRIMARY KEY,
		source_type VARCHAR(50) NOT NULL,           -- 'table', 'column', 'relationship', 'procedure'
		source_name VARCHAR(255) NOT NULL,          -- Original name (e.g., 'dbo.Customers')
		source_schema JSONB NOT NULL,               -- Full schema definition
		embedding vector(1536),                     -- OpenAI ada-002 embedding dimension
		metadata JSONB,                             -- Additional context
		migration_id INTEGER REFERENCES migrations(id) ON DELETE SET NULL,
		organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	);

	-- SQL transformation patterns (successful transformations)
	CREATE TABLE IF NOT EXISTS transformation_embeddings (
		id SERIAL PRIMARY KEY,
		source_sql TEXT NOT NULL,                   -- Original MSSQL
		target_sql TEXT NOT NULL,                   -- Generated dbt SQL
		transformation_type VARCHAR(50) NOT NULL,   -- 'table', 'view', 'procedure', 'function'
		embedding vector(1536),                     -- Embedding of source_sql
		quality_score FLOAT DEFAULT 0.0,            -- 0-1 score from validation
		metadata JSONB,                             -- Transformation context
		migration_id INTEGER REFERENCES migrations(id) ON DELETE SET NULL,
		organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	);

	-- dbt best practices knowledge base
	CREATE TABLE IF NOT EXISTS knowledge_embeddings (
		id SERIAL PRIMARY KEY,
		category VARCHAR(100) NOT NULL,             -- 'materialization', 'testing', 'naming', 'performance'
		title VARCHAR(255) NOT NULL,
		content TEXT NOT NULL,                      -- The actual knowledge/best practice
		embedding vector(1536),
		source VARCHAR(255),                        -- 'dbt_docs', 'community', 'internal'
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	);

	-- RAG query cache (for performance)
	CREATE TABLE IF NOT EXISTS rag_query_cache (
		id SERIAL PRIMARY KEY,
		query_hash VARCHAR(64) UNIQUE NOT NULL,     -- SHA-256 of query
		query_text TEXT NOT NULL,
		results JSONB NOT NULL,                     -- Cached results
		hit_count INTEGER DEFAULT 1,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		expires_at TIMESTAMP NOT NULL
	);

	-- Create vector similarity search indexes (IVFFlat for performance)
	CREATE INDEX IF NOT EXISTS idx_schema_embeddings_vector
		ON schema_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

	CREATE INDEX IF NOT EXISTS idx_transformation_embeddings_vector
		ON transformation_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

	CREATE INDEX IF NOT EXISTS idx_knowledge_embeddings_vector
		ON knowledge_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

	-- Regular indexes for filtering
	CREATE INDEX IF NOT EXISTS idx_schema_embeddings_type ON schema_embeddings(source_type);
	CREATE INDEX IF NOT EXISTS idx_schema_embeddings_org ON schema_embeddings(organization_id);
	CREATE INDEX IF NOT EXISTS idx_transformation_embeddings_type ON transformation_embeddings(transformation_type);
	CREATE INDEX IF NOT EXISTS idx_transformation_embeddings_score ON transformation_embeddings(quality_score);
	CREATE INDEX IF NOT EXISTS idx_knowledge_embeddings_category ON knowledge_embeddings(category);
	CREATE INDEX IF NOT EXISTS idx_rag_query_cache_hash ON rag_query_cache(query_hash);
	CREATE INDEX IF NOT EXISTS idx_rag_query_cache_expires ON rag_query_cache(expires_at);
	`

	_, err = DB.Exec(ragSchema)
	if err != nil {
		return fmt.Errorf("failed to create RAG tables: %w", err)
	}

	log.Println("RAG (pgvector) migrations completed")
	return nil
}
