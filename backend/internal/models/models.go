package models

import (
	"time"
)

// Organization represents a company or team
type Organization struct {
	ID            int64     `db:"id" json:"id"`
	Name          string    `db:"name" json:"name"`
	Slug          string    `db:"slug" json:"slug"`
	Plan          string    `db:"plan" json:"plan"` // free, starter, professional, enterprise
	MaxUsers      int       `db:"max_users" json:"max_users"`
	MaxMigrations int       `db:"max_migrations" json:"max_migrations"`
	CreatedAt     time.Time `db:"created_at" json:"created_at"`
	UpdatedAt     time.Time `db:"updated_at" json:"updated_at"`
}

// User represents a user in the system
type User struct {
	ID             int64      `db:"id" json:"id"`
	Email          string     `db:"email" json:"email"`
	Password       string     `db:"password" json:"-"` // Never expose password
	FirstName      *string    `db:"first_name" json:"first_name,omitempty"`
	LastName       *string    `db:"last_name" json:"last_name,omitempty"`
	JobTitle       *string    `db:"job_title" json:"job_title,omitempty"`
	Phone          *string    `db:"phone" json:"phone,omitempty"`
	OrganizationID *int64     `db:"organization_id" json:"organization_id,omitempty"`
	Role           string     `db:"role" json:"role"` // admin, member, viewer
	IsAdmin        bool       `db:"is_admin" json:"is_admin"`
	IsActive       bool       `db:"is_active" json:"is_active"`
	LastLoginAt    *time.Time `db:"last_login_at" json:"last_login_at,omitempty"`
	CreatedAt      time.Time  `db:"created_at" json:"created_at"`
	UpdatedAt      time.Time  `db:"updated_at" json:"updated_at"`
	// Virtual field (joined from organization)
	Organization *Organization `db:"-" json:"organization,omitempty"`
}

// OrganizationInvitation represents an invite to join an organization
type OrganizationInvitation struct {
	ID             int64      `db:"id" json:"id"`
	OrganizationID int64      `db:"organization_id" json:"organization_id"`
	Email          string     `db:"email" json:"email"`
	Role           string     `db:"role" json:"role"`
	Token          string     `db:"token" json:"-"` // Never expose token
	InvitedBy      *int64     `db:"invited_by" json:"invited_by,omitempty"`
	ExpiresAt      time.Time  `db:"expires_at" json:"expires_at"`
	AcceptedAt     *time.Time `db:"accepted_at" json:"accepted_at,omitempty"`
	CreatedAt      time.Time  `db:"created_at" json:"created_at"`
}

// Migration represents a database migration job
type Migration struct {
	ID               int64      `db:"id" json:"id"`
	Name             string     `db:"name" json:"name"`
	Status           string     `db:"status" json:"status"` // pending, running, completed, failed
	Progress         int        `db:"progress" json:"progress"`
	SourceDatabase   string     `db:"source_database" json:"source_database"`
	TargetProject    string     `db:"target_project" json:"target_project"`
	TablesCount      int        `db:"tables_count" json:"tables_count"`
	ViewsCount       int        `db:"views_count" json:"views_count"`
	ForeignKeysCount int        `db:"foreign_keys_count" json:"foreign_keys_count"`
	ModelsGenerated  int        `db:"models_generated" json:"models_generated"`
	UserID           int64      `db:"user_id" json:"user_id"`
	Error            *string    `db:"error" json:"error,omitempty"`
	Config           *string    `db:"config" json:"config,omitempty"` // JSON config
	CreatedAt        time.Time  `db:"created_at" json:"created_at"`
	CompletedAt      *time.Time `db:"completed_at" json:"completed_at,omitempty"`
	UpdatedAt        time.Time  `db:"updated_at" json:"updated_at"`
}

// DatabaseConnection represents a saved database connection
type DatabaseConnection struct {
	ID             int64     `db:"id" json:"id"`
	Name           string    `db:"name" json:"name"`
	DBType         string    `db:"db_type" json:"db_type"` // mssql, postgresql, mysql, snowflake, bigquery, databricks
	Host           string    `db:"host" json:"host"`
	Port           int       `db:"port" json:"port"`
	DatabaseName   string    `db:"database_name" json:"database_name"`
	Username       string    `db:"username" json:"username"`
	Password       string    `db:"password" json:"-"` // Encrypted, never expose
	UseWindowsAuth bool      `db:"use_windows_auth" json:"use_windows_auth"`
	IsSource       bool      `db:"is_source" json:"is_source"`
	UserID         int64     `db:"user_id" json:"user_id"`
	// Warehouse-specific fields (JSON stored in extra_config)
	ExtraConfig *string   `db:"extra_config" json:"extra_config,omitempty"` // JSON for warehouse-specific settings
	CreatedAt   time.Time `db:"created_at" json:"created_at"`
	UpdatedAt   time.Time `db:"updated_at" json:"updated_at"`
}

// WarehouseDeployment represents a deployment of dbt project to a warehouse
type WarehouseDeployment struct {
	ID               int64      `db:"id" json:"id"`
	MigrationID      int64      `db:"migration_id" json:"migration_id"`
	ConnectionID     int64      `db:"connection_id" json:"connection_id"`
	Status           string     `db:"status" json:"status"` // pending, running, completed, failed
	DbtRunStatus     *string    `db:"dbt_run_status" json:"dbt_run_status,omitempty"`
	DbtTestStatus    *string    `db:"dbt_test_status" json:"dbt_test_status,omitempty"`
	TablesCreated    int        `db:"tables_created" json:"tables_created"`
	TestsPassed      int        `db:"tests_passed" json:"tests_passed"`
	TestsFailed      int        `db:"tests_failed" json:"tests_failed"`
	DbtRunOutput     *string    `db:"dbt_run_output" json:"dbt_run_output,omitempty"`
	DbtTestOutput    *string    `db:"dbt_test_output" json:"dbt_test_output,omitempty"`
	Error            *string    `db:"error" json:"error,omitempty"`
	UserID           int64      `db:"user_id" json:"user_id"`
	CreatedAt        time.Time  `db:"created_at" json:"created_at"`
	CompletedAt      *time.Time `db:"completed_at" json:"completed_at,omitempty"`
}

// APIKey represents an API key for programmatic access
type APIKey struct {
	ID         int64      `db:"id" json:"id"`
	Name       string     `db:"name" json:"name"`
	Key        string     `db:"key" json:"key"`
	IsActive   bool       `db:"is_active" json:"is_active"`
	RateLimit  int        `db:"rate_limit" json:"rate_limit"`
	UserID     int64      `db:"user_id" json:"user_id"`
	LastUsedAt *time.Time `db:"last_used_at" json:"last_used_at,omitempty"`
	CreatedAt  time.Time  `db:"created_at" json:"created_at"`
}

// Request/Response DTOs

type LoginRequest struct {
	Email    string `json:"email" binding:"required,email"`
	Password string `json:"password" binding:"required,min=6"`
}

type LoginResponse struct {
	AccessToken string `json:"access_token"`
	User        User   `json:"user"`
}

type RegisterRequest struct {
	Email            string  `json:"email" binding:"required,email"`
	Password         string  `json:"password" binding:"required,min=6"`
	FirstName        string  `json:"first_name" binding:"required,min=1"`
	LastName         string  `json:"last_name" binding:"required,min=1"`
	OrganizationName string  `json:"organization_name" binding:"required,min=2"`
	JobTitle         *string `json:"job_title"`
	Phone            *string `json:"phone"`
}

type UpdateProfileRequest struct {
	FirstName *string `json:"first_name"`
	LastName  *string `json:"last_name"`
	Email     *string `json:"email"`
	JobTitle  *string `json:"job_title"`
	Phone     *string `json:"phone"`
}

type ChangePasswordRequest struct {
	CurrentPassword string `json:"current_password" binding:"required,min=6"`
	NewPassword     string `json:"new_password" binding:"required,min=6"`
}

type CreateMigrationRequest struct {
	Name           string   `json:"name" binding:"required,min=3"`
	SourceDatabase string   `json:"source_database" binding:"required"`
	TargetProject  string   `json:"target_project" binding:"required"`
	Tables         []string `json:"tables"`
	IncludeViews   bool     `json:"include_views"`
}

type CreateConnectionRequest struct {
	Name           string `json:"name" binding:"required"`
	DBType         string `json:"db_type" binding:"required"`
	Host           string `json:"host" binding:"required"`
	Port           int    `json:"port" binding:"required"`
	DatabaseName   string `json:"database_name" binding:"required"`
	Username       string `json:"username"`
	Password       string `json:"password"`
	UseWindowsAuth bool   `json:"use_windows_auth"`
	IsSource       bool   `json:"is_source"`
}

type CreateAPIKeyRequest struct {
	Name      string `json:"name" binding:"required"`
	RateLimit int    `json:"rate_limit"`
}

// ForgotPasswordRequest is used to request a password reset email
type ForgotPasswordRequest struct {
	Email string `json:"email" binding:"required,email"`
}

// ResetPasswordRequest is used to reset password with a token
type ResetPasswordRequest struct {
	Token       string `json:"token" binding:"required"`
	NewPassword string `json:"new_password" binding:"required,min=6"`
}

type DashboardStats struct {
	TotalMigrations     int     `json:"total_migrations"`
	CompletedMigrations int     `json:"completed_migrations"`
	RunningMigrations   int     `json:"running_migrations"`
	FailedMigrations    int     `json:"failed_migrations"`
	SuccessRate         float64 `json:"success_rate"`
}

// CreateWarehouseConnectionRequest for adding warehouse connections
type CreateWarehouseConnectionRequest struct {
	Name         string                 `json:"name" binding:"required"`
	DBType       string                 `json:"db_type" binding:"required"` // snowflake, bigquery, databricks
	Account      string                 `json:"account,omitempty"`          // Snowflake account
	Warehouse    string                 `json:"warehouse,omitempty"`        // Snowflake warehouse
	Database     string                 `json:"database" binding:"required"`
	Schema       string                 `json:"schema,omitempty"`
	Username     string                 `json:"username,omitempty"`
	Password     string                 `json:"password,omitempty"`
	Role         string                 `json:"role,omitempty"`    // Snowflake role
	Project      string                 `json:"project,omitempty"` // BigQuery project
	Dataset      string                 `json:"dataset,omitempty"` // BigQuery dataset
	KeyFile      string                 `json:"key_file,omitempty"`
	Host         string                 `json:"host,omitempty"`         // Databricks host
	HTTPPath     string                 `json:"http_path,omitempty"`    // Databricks HTTP path
	AccessToken  string                 `json:"access_token,omitempty"` // Databricks token
	ExtraOptions map[string]interface{} `json:"extra_options,omitempty"`
}

// DeployToWarehouseRequest for deploying a migration to a warehouse
type DeployToWarehouseRequest struct {
	ConnectionID int64 `json:"connection_id" binding:"required"`
	RunTests     bool  `json:"run_tests"`
	FullRefresh  bool  `json:"full_refresh"`
}

// DeploymentStatusResponse returns the status of a deployment
type DeploymentStatusResponse struct {
	ID            int64      `json:"id"`
	MigrationID   int64      `json:"migration_id"`
	Status        string     `json:"status"`
	DbtRunStatus  *string    `json:"dbt_run_status,omitempty"`
	DbtTestStatus *string    `json:"dbt_test_status,omitempty"`
	TablesCreated int        `json:"tables_created"`
	TestsPassed   int        `json:"tests_passed"`
	TestsFailed   int        `json:"tests_failed"`
	Error         *string    `json:"error,omitempty"`
	CreatedAt     time.Time  `json:"created_at"`
	CompletedAt   *time.Time `json:"completed_at,omitempty"`
}
