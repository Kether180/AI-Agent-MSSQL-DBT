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
	ID             int64      `db:"id" json:"id"`
	Name           string     `db:"name" json:"name"`
	Status         string     `db:"status" json:"status"` // pending, running, completed, failed
	Progress       int        `db:"progress" json:"progress"`
	SourceDatabase string     `db:"source_database" json:"source_database"`
	TargetProject  string     `db:"target_project" json:"target_project"`
	TablesCount    int        `db:"tables_count" json:"tables_count"`
	UserID         int64      `db:"user_id" json:"user_id"`
	Error          *string    `db:"error" json:"error,omitempty"`
	Config         *string    `db:"config" json:"config,omitempty"` // JSON config
	CreatedAt      time.Time  `db:"created_at" json:"created_at"`
	CompletedAt    *time.Time `db:"completed_at" json:"completed_at,omitempty"`
	UpdatedAt      time.Time  `db:"updated_at" json:"updated_at"`
}

// DatabaseConnection represents a saved database connection
type DatabaseConnection struct {
	ID           int64     `db:"id" json:"id"`
	Name         string    `db:"name" json:"name"`
	DBType       string    `db:"db_type" json:"db_type"` // mssql, postgresql, mysql
	Host         string    `db:"host" json:"host"`
	Port         int       `db:"port" json:"port"`
	DatabaseName string    `db:"database_name" json:"database_name"`
	Username     string    `db:"username" json:"username"`
	Password     string    `db:"password" json:"-"` // Encrypted, never expose
	IsSource     bool      `db:"is_source" json:"is_source"`
	UserID       int64     `db:"user_id" json:"user_id"`
	CreatedAt    time.Time `db:"created_at" json:"created_at"`
	UpdatedAt    time.Time `db:"updated_at" json:"updated_at"`
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
	Name         string `json:"name" binding:"required"`
	DBType       string `json:"db_type" binding:"required"`
	Host         string `json:"host" binding:"required"`
	Port         int    `json:"port" binding:"required"`
	DatabaseName string `json:"database_name" binding:"required"`
	Username     string `json:"username" binding:"required"`
	Password     string `json:"password" binding:"required"`
	IsSource     bool   `json:"is_source"`
}

type CreateAPIKeyRequest struct {
	Name      string `json:"name" binding:"required"`
	RateLimit int    `json:"rate_limit"`
}

type DashboardStats struct {
	TotalMigrations     int     `json:"total_migrations"`
	CompletedMigrations int     `json:"completed_migrations"`
	RunningMigrations   int     `json:"running_migrations"`
	FailedMigrations    int     `json:"failed_migrations"`
	SuccessRate         float64 `json:"success_rate"`
}
