package validation

import (
	"fmt"
	"net"
	"regexp"
	"strings"
	"unicode"
)

// ValidationError contains validation error details
type ValidationError struct {
	Field   string `json:"field"`
	Message string `json:"message"`
}

// ValidationResult contains the result of validation
type ValidationResult struct {
	Valid  bool              `json:"valid"`
	Errors []ValidationError `json:"errors,omitempty"`
}

// AddError adds an error to the result
func (v *ValidationResult) AddError(field, message string) {
	v.Valid = false
	v.Errors = append(v.Errors, ValidationError{Field: field, Message: message})
}

// ErrorMessages returns all error messages as a formatted string
func (v *ValidationResult) ErrorMessages() string {
	if len(v.Errors) == 0 {
		return ""
	}

	messages := make([]string, len(v.Errors))
	for i, err := range v.Errors {
		messages[i] = fmt.Sprintf("%s: %s", err.Field, err.Message)
	}
	return strings.Join(messages, "; ")
}

// NewValidationResult creates a new valid result
func NewValidationResult() *ValidationResult {
	return &ValidationResult{Valid: true, Errors: []ValidationError{}}
}

// ConnectionValidator validates database connection parameters
type ConnectionValidator struct{}

// NewConnectionValidator creates a new connection validator
func NewConnectionValidator() *ConnectionValidator {
	return &ConnectionValidator{}
}

// ValidDBTypes contains the allowed database types
var ValidDBTypes = map[string]bool{
	"mssql":      true,
	"postgresql": true,
	"mysql":      true,
	"snowflake":  true,
	"bigquery":   true,
	"databricks": true,
	"redshift":   true,
	"fabric":     true,
	"spark":      true,
}

// Reserved or dangerous names that shouldn't be allowed
var reservedNames = []string{
	"admin", "root", "system", "null", "undefined",
	"drop", "delete", "truncate", "exec", "execute",
}

// Regex patterns for validation
var (
	// Only alphanumeric, spaces, hyphens, underscores for connection names
	connectionNameRegex = regexp.MustCompile(`^[a-zA-Z0-9\s\-_]+$`)

	// Database name: alphanumeric, underscore, hyphen, period
	databaseNameRegex = regexp.MustCompile(`^[a-zA-Z0-9_\-.]+$`)

	// Username: alphanumeric, underscore, hyphen, at, period, backslash (for domain\user)
	usernameRegex = regexp.MustCompile(`^[a-zA-Z0-9_\-@.\\]+$`)

	// Host: valid hostname or IP address patterns
	hostRegex = regexp.MustCompile(`^[a-zA-Z0-9\-_.]+$`)

	// SQL injection patterns to detect
	sqlInjectionPatterns = []*regexp.Regexp{
		regexp.MustCompile(`(?i)(SELECT|INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|EXEC|EXECUTE)\s`),
		regexp.MustCompile(`(?i)UNION\s+SELECT`),
		regexp.MustCompile(`(?i)OR\s+1\s*=\s*1`),
		regexp.MustCompile(`(?i)AND\s+1\s*=\s*1`),
		regexp.MustCompile(`(?i)--\s*$`),
		regexp.MustCompile(`(?i);\s*--`),
		regexp.MustCompile(`(?i)xp_cmdshell`),
		regexp.MustCompile(`(?i)WAITFOR\s+DELAY`),
		regexp.MustCompile(`(?i)BENCHMARK\s*\(`),
		regexp.MustCompile(`(?i)SLEEP\s*\(`),
	}
)

// ValidateConnectionName validates the connection name
func (v *ConnectionValidator) ValidateConnectionName(name string) *ValidationResult {
	result := NewValidationResult()

	// Check length
	if len(name) < 2 {
		result.AddError("name", "Name must be at least 2 characters long")
	}
	if len(name) > 100 {
		result.AddError("name", "Name must not exceed 100 characters")
	}

	// Check for valid characters
	if !connectionNameRegex.MatchString(name) {
		result.AddError("name", "Name can only contain letters, numbers, spaces, hyphens, and underscores")
	}

	// Check for reserved names
	lowerName := strings.ToLower(strings.TrimSpace(name))
	for _, reserved := range reservedNames {
		if lowerName == reserved {
			result.AddError("name", fmt.Sprintf("'%s' is a reserved name and cannot be used", name))
			break
		}
	}

	// Check for SQL injection
	if v.containsSQLInjection(name) {
		result.AddError("name", "Name contains potentially dangerous content")
	}

	return result
}

// ValidateDBType validates the database type
func (v *ConnectionValidator) ValidateDBType(dbType string) *ValidationResult {
	result := NewValidationResult()

	if dbType == "" {
		result.AddError("db_type", "Database type is required")
		return result
	}

	if !ValidDBTypes[dbType] {
		validTypes := make([]string, 0, len(ValidDBTypes))
		for t := range ValidDBTypes {
			validTypes = append(validTypes, t)
		}
		result.AddError("db_type", fmt.Sprintf("Invalid database type. Must be one of: %s", strings.Join(validTypes, ", ")))
	}

	return result
}

// ValidateHost validates the host address
func (v *ConnectionValidator) ValidateHost(host string) *ValidationResult {
	result := NewValidationResult()

	if host == "" {
		result.AddError("host", "Host is required")
		return result
	}

	// Check length
	if len(host) > 253 {
		result.AddError("host", "Host must not exceed 253 characters")
	}

	// Try parsing as IP address
	if ip := net.ParseIP(host); ip != nil {
		// Valid IP address
		return result
	}

	// Validate as hostname
	if !hostRegex.MatchString(host) {
		result.AddError("host", "Host contains invalid characters")
	}

	// Check for SQL injection
	if v.containsSQLInjection(host) {
		result.AddError("host", "Host contains potentially dangerous content")
	}

	// Check for localhost variants (may want to restrict in production)
	lowerHost := strings.ToLower(host)
	if lowerHost == "localhost" || lowerHost == "127.0.0.1" || lowerHost == "::1" {
		// Allow localhost in development, but flag for logging
	}

	return result
}

// ValidatePort validates the port number
func (v *ConnectionValidator) ValidatePort(port int) *ValidationResult {
	result := NewValidationResult()

	if port <= 0 {
		result.AddError("port", "Port must be a positive number")
		return result
	}

	if port > 65535 {
		result.AddError("port", "Port must not exceed 65535")
	}

	// Common dangerous ports that might indicate misconfiguration
	dangerousPorts := map[int]string{
		22:   "SSH",
		23:   "Telnet",
		25:   "SMTP",
		80:   "HTTP",
		443:  "HTTPS",
		445:  "SMB",
		3389: "RDP",
	}

	if service, isDangerous := dangerousPorts[port]; isDangerous {
		// Log warning but allow (might be intentional)
		_ = service // Could add a warning here
	}

	return result
}

// ValidateDatabaseName validates the database name
func (v *ConnectionValidator) ValidateDatabaseName(dbName string) *ValidationResult {
	result := NewValidationResult()

	if dbName == "" {
		result.AddError("database_name", "Database name is required")
		return result
	}

	// Check length
	if len(dbName) > 128 {
		result.AddError("database_name", "Database name must not exceed 128 characters")
	}

	// Check for valid characters
	if !databaseNameRegex.MatchString(dbName) {
		result.AddError("database_name", "Database name can only contain letters, numbers, underscores, hyphens, and periods")
	}

	// Check for reserved names
	lowerName := strings.ToLower(dbName)
	for _, reserved := range reservedNames {
		if lowerName == reserved {
			result.AddError("database_name", fmt.Sprintf("'%s' is a reserved name", dbName))
			break
		}
	}

	// Check for SQL injection
	if v.containsSQLInjection(dbName) {
		result.AddError("database_name", "Database name contains potentially dangerous content")
	}

	return result
}

// ValidateUsername validates the username
func (v *ConnectionValidator) ValidateUsername(username string, useWindowsAuth bool) *ValidationResult {
	result := NewValidationResult()

	// Username can be empty if using Windows Auth
	if username == "" && !useWindowsAuth {
		// Username is optional for some databases
		return result
	}

	if username == "" {
		return result
	}

	// Check length
	if len(username) > 128 {
		result.AddError("username", "Username must not exceed 128 characters")
	}

	// Check for valid characters
	if !usernameRegex.MatchString(username) {
		result.AddError("username", "Username contains invalid characters")
	}

	// Check for SQL injection
	if v.containsSQLInjection(username) {
		result.AddError("username", "Username contains potentially dangerous content")
	}

	return result
}

// ValidatePassword validates the password
func (v *ConnectionValidator) ValidatePassword(password string, useWindowsAuth bool) *ValidationResult {
	result := NewValidationResult()

	// Password can be empty if using Windows Auth
	if password == "" && !useWindowsAuth {
		// Password is optional for some databases
		return result
	}

	if password == "" {
		return result
	}

	// Check length (reasonable max for passwords)
	if len(password) > 256 {
		result.AddError("password", "Password must not exceed 256 characters")
	}

	// Check for control characters (potential injection)
	for _, r := range password {
		if unicode.IsControl(r) && r != '\t' && r != '\n' && r != '\r' {
			result.AddError("password", "Password contains invalid control characters")
			break
		}
	}

	return result
}

// ValidateConnection validates all connection parameters
func (v *ConnectionValidator) ValidateConnection(name, dbType, host string, port int, databaseName, username, password string, useWindowsAuth bool) *ValidationResult {
	result := NewValidationResult()

	// Validate each field
	if nameResult := v.ValidateConnectionName(name); !nameResult.Valid {
		result.Errors = append(result.Errors, nameResult.Errors...)
		result.Valid = false
	}

	if typeResult := v.ValidateDBType(dbType); !typeResult.Valid {
		result.Errors = append(result.Errors, typeResult.Errors...)
		result.Valid = false
	}

	if hostResult := v.ValidateHost(host); !hostResult.Valid {
		result.Errors = append(result.Errors, hostResult.Errors...)
		result.Valid = false
	}

	if portResult := v.ValidatePort(port); !portResult.Valid {
		result.Errors = append(result.Errors, portResult.Errors...)
		result.Valid = false
	}

	if dbResult := v.ValidateDatabaseName(databaseName); !dbResult.Valid {
		result.Errors = append(result.Errors, dbResult.Errors...)
		result.Valid = false
	}

	if userResult := v.ValidateUsername(username, useWindowsAuth); !userResult.Valid {
		result.Errors = append(result.Errors, userResult.Errors...)
		result.Valid = false
	}

	if passResult := v.ValidatePassword(password, useWindowsAuth); !passResult.Valid {
		result.Errors = append(result.Errors, passResult.Errors...)
		result.Valid = false
	}

	return result
}

// containsSQLInjection checks if the input contains SQL injection patterns
func (v *ConnectionValidator) containsSQLInjection(input string) bool {
	for _, pattern := range sqlInjectionPatterns {
		if pattern.MatchString(input) {
			return true
		}
	}
	return false
}

// SanitizeInput removes potentially dangerous characters from input
func SanitizeInput(input string) string {
	// Remove null bytes
	result := strings.ReplaceAll(input, "\x00", "")

	// Remove other control characters except common whitespace
	var sanitized strings.Builder
	for _, r := range result {
		if !unicode.IsControl(r) || r == '\t' || r == '\n' || r == '\r' || r == ' ' {
			sanitized.WriteRune(r)
		}
	}

	return strings.TrimSpace(sanitized.String())
}
