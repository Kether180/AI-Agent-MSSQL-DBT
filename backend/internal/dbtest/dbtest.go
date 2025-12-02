package dbtest

import (
	"context"
	"database/sql"
	"fmt"
	"time"

	_ "github.com/denisenkom/go-mssqldb" // MSSQL driver
	_ "github.com/lib/pq"                // PostgreSQL driver
)

// ConnectionParams holds the parameters for testing a database connection
type ConnectionParams struct {
	DBType   string
	Host     string
	Port     int
	Database string
	Username string
	Password string
}

// TestResult holds the result of a connection test
type TestResult struct {
	Success     bool   `json:"success"`
	Message     string `json:"message"`
	Latency     int64  `json:"latency_ms"`
	ServerInfo  string `json:"server_info,omitempty"`
	TableCount  int    `json:"table_count,omitempty"`
}

// TestConnection tests a database connection and returns detailed results
func TestConnection(params ConnectionParams) TestResult {
	start := time.Now()

	// Build connection string based on database type
	var dsn string
	var driver string

	switch params.DBType {
	case "mssql", "sqlserver":
		driver = "sqlserver"
		dsn = fmt.Sprintf(
			"server=%s;port=%d;database=%s;user id=%s;password=%s;connection timeout=10",
			params.Host, params.Port, params.Database, params.Username, params.Password,
		)
	case "postgresql", "postgres":
		driver = "postgres"
		dsn = fmt.Sprintf(
			"host=%s port=%d dbname=%s user=%s password=%s sslmode=disable connect_timeout=10",
			params.Host, params.Port, params.Database, params.Username, params.Password,
		)
	default:
		return TestResult{
			Success: false,
			Message: fmt.Sprintf("Unsupported database type: %s", params.DBType),
			Latency: time.Since(start).Milliseconds(),
		}
	}

	// Open connection
	db, err := sql.Open(driver, dsn)
	if err != nil {
		return TestResult{
			Success: false,
			Message: fmt.Sprintf("Failed to create connection: %v", err),
			Latency: time.Since(start).Milliseconds(),
		}
	}
	defer db.Close()

	// Set connection pool settings for test
	db.SetMaxOpenConns(1)
	db.SetMaxIdleConns(1)
	db.SetConnMaxLifetime(30 * time.Second)

	// Create context with timeout
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// Ping the database
	if err := db.PingContext(ctx); err != nil {
		return TestResult{
			Success: false,
			Message: fmt.Sprintf("Connection failed: %v", err),
			Latency: time.Since(start).Milliseconds(),
		}
	}

	// Get server version and table count
	var serverInfo string
	var tableCount int

	switch params.DBType {
	case "mssql", "sqlserver":
		// Get SQL Server version
		db.QueryRowContext(ctx, "SELECT @@VERSION").Scan(&serverInfo)
		// Count user tables
		db.QueryRowContext(ctx, `
			SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES
			WHERE TABLE_TYPE = 'BASE TABLE' AND TABLE_CATALOG = @p1
		`, params.Database).Scan(&tableCount)

	case "postgresql", "postgres":
		// Get PostgreSQL version
		db.QueryRowContext(ctx, "SELECT version()").Scan(&serverInfo)
		// Count user tables
		db.QueryRowContext(ctx, `
			SELECT COUNT(*) FROM information_schema.tables
			WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
		`).Scan(&tableCount)
	}

	// Truncate server info if too long
	if len(serverInfo) > 100 {
		serverInfo = serverInfo[:100] + "..."
	}

	return TestResult{
		Success:    true,
		Message:    "Connection successful",
		Latency:    time.Since(start).Milliseconds(),
		ServerInfo: serverInfo,
		TableCount: tableCount,
	}
}
