package security

import (
	"bytes"
	"encoding/json"
	"io"
	"log"
	"net/http"
	"regexp"
	"sync"
	"time"

	"github.com/datamigrate-ai/backend/internal/db"
	"github.com/gin-gonic/gin"
)

// GuardianAgent is the central security agent that monitors and protects the system
type GuardianAgent struct {
	mu              sync.RWMutex
	rateLimiter     *RateLimiter
	patternDetector *PatternDetector
	auditLogger     *AuditLogger
	policies        []SecurityPolicy
}

// SecurityEvent represents a security-related event
type SecurityEvent struct {
	EventType      string                 `json:"event_type"`
	Severity       string                 `json:"severity"`
	UserID         *int64                 `json:"user_id,omitempty"`
	OrganizationID *int64                 `json:"organization_id,omitempty"`
	IPAddress      string                 `json:"ip_address"`
	UserAgent      string                 `json:"user_agent"`
	Endpoint       string                 `json:"endpoint"`
	Method         string                 `json:"method"`
	RequestBody    string                 `json:"request_body,omitempty"`
	ResponseStatus int                    `json:"response_status,omitempty"`
	Blocked        bool                   `json:"blocked"`
	BlockReason    string                 `json:"block_reason,omitempty"`
	Metadata       map[string]interface{} `json:"metadata,omitempty"`
	Timestamp      time.Time              `json:"timestamp"`
}

// SecurityPolicy defines security rules
type SecurityPolicy struct {
	ID             int64                  `db:"id" json:"id"`
	Name           string                 `db:"name" json:"name"`
	Description    string                 `db:"description" json:"description"`
	PolicyType     string                 `db:"policy_type" json:"policy_type"`
	Rules          map[string]interface{} `json:"rules"`
	IsActive       bool                   `db:"is_active" json:"is_active"`
	OrganizationID *int64                 `db:"organization_id" json:"organization_id,omitempty"`
}

// BlockedPattern represents a pattern to detect malicious input
type BlockedPattern struct {
	ID          int64  `db:"id" json:"id"`
	Pattern     string `db:"pattern" json:"pattern"`
	PatternType string `db:"pattern_type" json:"pattern_type"`
	Description string `db:"description" json:"description"`
	Severity    string `db:"severity" json:"severity"`
	IsActive    bool   `db:"is_active" json:"is_active"`
	compiled    *regexp.Regexp
}

var guardian *GuardianAgent
var guardianOnce sync.Once

// GetGuardian returns the singleton GuardianAgent instance
func GetGuardian() *GuardianAgent {
	guardianOnce.Do(func() {
		guardian = &GuardianAgent{
			rateLimiter:     NewRateLimiter(),
			patternDetector: NewPatternDetector(),
			auditLogger:     NewAuditLogger(),
		}
		guardian.loadPolicies()
		guardian.loadBlockedPatterns()
		log.Println("Guardian Agent initialized - Security monitoring active")
	})
	return guardian
}

// loadPolicies loads security policies from the database
func (g *GuardianAgent) loadPolicies() {
	g.mu.Lock()
	defer g.mu.Unlock()

	// For now, use default policies. Can be extended to load from DB
	g.policies = []SecurityPolicy{
		{
			Name:       "rate_limit_default",
			PolicyType: "rate_limit",
			Rules: map[string]interface{}{
				"requests_per_minute": 60,
				"requests_per_hour":   1000,
			},
			IsActive: true,
		},
		{
			Name:       "input_validation",
			PolicyType: "input_validation",
			Rules: map[string]interface{}{
				"max_body_size":    1048576, // 1MB
				"max_field_length": 10000,
			},
			IsActive: true,
		},
	}
}

// loadBlockedPatterns loads suspicious patterns from the database
func (g *GuardianAgent) loadBlockedPatterns() {
	g.patternDetector.LoadDefaultPatterns()

	// Also try to load from database
	var patterns []BlockedPattern
	err := db.DB.Select(&patterns, "SELECT id, pattern, pattern_type, description, severity, is_active FROM blocked_patterns WHERE is_active = true")
	if err != nil {
		log.Printf("Warning: Could not load blocked patterns from DB: %v", err)
		return
	}

	for _, p := range patterns {
		g.patternDetector.AddPattern(p.Pattern, p.PatternType, p.Severity)
	}
}

// Middleware returns the Guardian security middleware
func (g *GuardianAgent) Middleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		startTime := time.Now()

		// Get request info
		clientIP := c.ClientIP()
		userAgent := c.Request.UserAgent()
		endpoint := c.Request.URL.Path
		method := c.Request.Method

		// Create security event
		event := &SecurityEvent{
			EventType: "request",
			Severity:  "info",
			IPAddress: clientIP,
			UserAgent: userAgent,
			Endpoint:  endpoint,
			Method:    method,
			Timestamp: startTime,
			Metadata:  make(map[string]interface{}),
		}

		// 1. Rate limiting check
		if blocked, reason := g.rateLimiter.Check(clientIP, endpoint); blocked {
			event.EventType = "rate_limit_exceeded"
			event.Severity = "warning"
			event.Blocked = true
			event.BlockReason = reason
			g.auditLogger.Log(event)

			c.JSON(http.StatusTooManyRequests, gin.H{
				"error":       "Rate limit exceeded",
				"retry_after": 60,
			})
			c.Abort()
			return
		}

		// 2. Read and validate request body
		if c.Request.Body != nil && method != "GET" {
			bodyBytes, err := io.ReadAll(c.Request.Body)
			if err == nil {
				// Check body size
				if len(bodyBytes) > 1048576 { // 1MB limit
					event.EventType = "oversized_request"
					event.Severity = "warning"
					event.Blocked = true
					event.BlockReason = "Request body too large"
					g.auditLogger.Log(event)

					c.JSON(http.StatusRequestEntityTooLarge, gin.H{
						"error": "Request body too large",
					})
					c.Abort()
					return
				}

				// 3. Pattern detection for suspicious content
				bodyString := string(bodyBytes)
				if detected, patternType, severity := g.patternDetector.Detect(bodyString); detected {
					event.EventType = "suspicious_pattern"
					event.Severity = severity
					event.Blocked = true
					event.BlockReason = "Suspicious pattern detected: " + patternType
					event.RequestBody = g.sanitizeForLog(bodyString)
					g.auditLogger.Log(event)

					c.JSON(http.StatusBadRequest, gin.H{
						"error": "Invalid request content",
					})
					c.Abort()
					return
				}

				// Restore body for downstream handlers
				c.Request.Body = io.NopCloser(bytes.NewBuffer(bodyBytes))

				// Store sanitized body for audit
				event.RequestBody = g.sanitizeForLog(bodyString)
			}
		}

		// 4. Check URL parameters for suspicious patterns
		for key, values := range c.Request.URL.Query() {
			for _, value := range values {
				if detected, patternType, severity := g.patternDetector.Detect(value); detected {
					event.EventType = "suspicious_query_param"
					event.Severity = severity
					event.Blocked = true
					event.BlockReason = "Suspicious query parameter: " + key + " (" + patternType + ")"
					g.auditLogger.Log(event)

					c.JSON(http.StatusBadRequest, gin.H{
						"error": "Invalid request parameters",
					})
					c.Abort()
					return
				}
			}
		}

		// Process request
		c.Next()

		// 5. Post-request audit logging
		event.ResponseStatus = c.Writer.Status()

		// Get user ID if authenticated
		if userID, exists := c.Get("user_id"); exists {
			if id, ok := userID.(int64); ok {
				event.UserID = &id
			}
		}

		// Get organization ID if available
		if orgID, exists := c.Get("organization_id"); exists {
			if id, ok := orgID.(int64); ok {
				event.OrganizationID = &id
			}
		}

		// Determine severity based on response status
		if event.ResponseStatus >= 500 {
			event.Severity = "error"
		} else if event.ResponseStatus >= 400 {
			event.Severity = "warning"
		}

		// Add timing metadata
		event.Metadata["duration_ms"] = time.Since(startTime).Milliseconds()

		// Log the event
		g.auditLogger.Log(event)
	}
}

// sanitizeForLog removes sensitive data before logging
func (g *GuardianAgent) sanitizeForLog(body string) string {
	// Parse as JSON and redact sensitive fields
	var data map[string]interface{}
	if err := json.Unmarshal([]byte(body), &data); err != nil {
		// Not JSON, truncate if too long
		if len(body) > 500 {
			return body[:500] + "...[truncated]"
		}
		return body
	}

	// Redact sensitive fields
	sensitiveFields := []string{"password", "current_password", "new_password", "token", "secret", "api_key", "credit_card"}
	for _, field := range sensitiveFields {
		if _, exists := data[field]; exists {
			data[field] = "[REDACTED]"
		}
	}

	sanitized, _ := json.Marshal(data)
	return string(sanitized)
}

// LogSecurityEvent manually logs a security event
func (g *GuardianAgent) LogSecurityEvent(event *SecurityEvent) {
	g.auditLogger.Log(event)
}

// GetAuditLogs retrieves audit logs with filtering
func (g *GuardianAgent) GetAuditLogs(filters map[string]interface{}, limit, offset int) ([]SecurityEvent, error) {
	return g.auditLogger.GetLogs(filters, limit, offset)
}

// ReloadPolicies reloads security policies from the database
func (g *GuardianAgent) ReloadPolicies() {
	g.loadPolicies()
	g.loadBlockedPatterns()
	log.Println("Guardian Agent: Security policies reloaded")
}

// GetSecurityStats returns security statistics
func (g *GuardianAgent) GetSecurityStats() map[string]interface{} {
	return map[string]interface{}{
		"rate_limiter_active_entries": g.rateLimiter.GetActiveCount(),
		"patterns_loaded":             g.patternDetector.GetPatternCount(),
		"policies_active":             len(g.policies),
	}
}
