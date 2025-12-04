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
	DBType         string
	Host           string
	Port           int
	Database       string
	Username       string
	Password       string
	UseWindowsAuth bool
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
		if params.UseWindowsAuth {
			// Windows Authentication (Trusted Connection)
			dsn = fmt.Sprintf(
				"server=%s;port=%d;database=%s;trusted_connection=yes;connection timeout=10",
				params.Host, params.Port, params.Database,
			)
		} else {
			// SQL Server Authentication
			dsn = fmt.Sprintf(
				"server=%s;port=%d;database=%s;user id=%s;password=%s;connection timeout=10",
				params.Host, params.Port, params.Database, params.Username, params.Password,
			)
		}
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

// TableInfo holds information about a database table
type TableInfo struct {
	Name     string `json:"name"`
	Schema   string `json:"schema"`
	RowCount int64  `json:"row_count"`
}

// ColumnInfo holds information about a column
type ColumnInfo struct {
	Name       string `json:"name"`
	DataType   string `json:"data_type"`
	IsNullable bool   `json:"is_nullable"`
	MaxLength  int    `json:"max_length,omitempty"`
}

// ViewInfo holds information about a database view
type ViewInfo struct {
	Name   string `json:"name"`
	Schema string `json:"schema"`
}

// MetadataResult holds all extracted metadata from a database
type MetadataResult struct {
	Database string      `json:"database"`
	Tables   []TableInfo `json:"tables"`
	Views    []ViewInfo  `json:"views"`
	Success  bool        `json:"success"`
	Error    string      `json:"error,omitempty"`
}

// ExtractMetadata extracts tables, views, and columns from a database
func ExtractMetadata(params ConnectionParams) MetadataResult {
	result := MetadataResult{
		Database: params.Database,
		Tables:   []TableInfo{},
		Views:    []ViewInfo{},
		Success:  false,
	}

	// Build connection string based on database type
	var dsn string
	var driver string

	switch params.DBType {
	case "mssql", "sqlserver":
		driver = "sqlserver"
		if params.UseWindowsAuth {
			// Windows Authentication (Trusted Connection)
			dsn = fmt.Sprintf(
				"server=%s;port=%d;database=%s;trusted_connection=yes;connection timeout=30",
				params.Host, params.Port, params.Database,
			)
		} else {
			// SQL Server Authentication
			dsn = fmt.Sprintf(
				"server=%s;port=%d;database=%s;user id=%s;password=%s;connection timeout=30",
				params.Host, params.Port, params.Database, params.Username, params.Password,
			)
		}
	case "postgresql", "postgres":
		driver = "postgres"
		dsn = fmt.Sprintf(
			"host=%s port=%d dbname=%s user=%s password=%s sslmode=disable connect_timeout=30",
			params.Host, params.Port, params.Database, params.Username, params.Password,
		)
	default:
		result.Error = fmt.Sprintf("Unsupported database type: %s", params.DBType)
		return result
	}

	// Open connection
	db, err := sql.Open(driver, dsn)
	if err != nil {
		result.Error = fmt.Sprintf("Failed to create connection: %v", err)
		return result
	}
	defer db.Close()

	// Set connection pool settings
	db.SetMaxOpenConns(5)
	db.SetMaxIdleConns(2)
	db.SetConnMaxLifetime(5 * time.Minute)

	// Create context with timeout
	ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel()

	// Ping the database
	if err := db.PingContext(ctx); err != nil {
		result.Error = fmt.Sprintf("Connection failed: %v", err)
		return result
	}

	// Extract tables and views based on database type
	switch params.DBType {
	case "mssql", "sqlserver":
		// Get tables with row counts
		rows, err := db.QueryContext(ctx, `
			SELECT
				t.TABLE_SCHEMA,
				t.TABLE_NAME,
				ISNULL(p.rows, 0) as row_count
			FROM INFORMATION_SCHEMA.TABLES t
			LEFT JOIN sys.tables st ON st.name = t.TABLE_NAME
			LEFT JOIN sys.partitions p ON st.object_id = p.object_id AND p.index_id IN (0, 1)
			WHERE t.TABLE_TYPE = 'BASE TABLE'
			AND t.TABLE_CATALOG = @p1
			ORDER BY t.TABLE_SCHEMA, t.TABLE_NAME
		`, params.Database)
		if err == nil {
			defer rows.Close()
			for rows.Next() {
				var table TableInfo
				if err := rows.Scan(&table.Schema, &table.Name, &table.RowCount); err == nil {
					result.Tables = append(result.Tables, table)
				}
			}
		}

		// Get views
		viewRows, err := db.QueryContext(ctx, `
			SELECT TABLE_SCHEMA, TABLE_NAME
			FROM INFORMATION_SCHEMA.VIEWS
			WHERE TABLE_CATALOG = @p1
			ORDER BY TABLE_SCHEMA, TABLE_NAME
		`, params.Database)
		if err == nil {
			defer viewRows.Close()
			for viewRows.Next() {
				var view ViewInfo
				if err := viewRows.Scan(&view.Schema, &view.Name); err == nil {
					result.Views = append(result.Views, view)
				}
			}
		}

	case "postgresql", "postgres":
		// Get tables with row counts (estimated)
		rows, err := db.QueryContext(ctx, `
			SELECT
				schemaname,
				tablename,
				COALESCE(n_live_tup, 0) as row_count
			FROM pg_stat_user_tables
			ORDER BY schemaname, tablename
		`)
		if err == nil {
			defer rows.Close()
			for rows.Next() {
				var table TableInfo
				if err := rows.Scan(&table.Schema, &table.Name, &table.RowCount); err == nil {
					result.Tables = append(result.Tables, table)
				}
			}
		}

		// Get views
		viewRows, err := db.QueryContext(ctx, `
			SELECT table_schema, table_name
			FROM information_schema.views
			WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
			ORDER BY table_schema, table_name
		`)
		if err == nil {
			defer viewRows.Close()
			for viewRows.Next() {
				var view ViewInfo
				if err := viewRows.Scan(&view.Schema, &view.Name); err == nil {
					result.Views = append(result.Views, view)
				}
			}
		}
	}

	result.Success = true
	return result
}
