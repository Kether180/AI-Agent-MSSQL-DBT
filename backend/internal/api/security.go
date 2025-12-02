package api

import (
	"net/http"
	"strconv"
	"time"

	"github.com/datamigrate-ai/backend/internal/middleware"
	"github.com/datamigrate-ai/backend/internal/security"
	"github.com/gin-gonic/gin"
)

type SecurityHandler struct {
	guardian *security.GuardianAgent
}

func NewSecurityHandler() *SecurityHandler {
	return &SecurityHandler{
		guardian: security.GetGuardian(),
	}
}

// GetAuditLogs retrieves security audit logs
func (h *SecurityHandler) GetAuditLogs(c *gin.Context) {
	// Only admins can view audit logs
	if !middleware.IsAdmin(c) {
		c.JSON(http.StatusForbidden, gin.H{"error": "Admin access required"})
		return
	}

	// Parse query parameters
	filters := make(map[string]interface{})

	if eventType := c.Query("event_type"); eventType != "" {
		filters["event_type"] = eventType
	}
	if severity := c.Query("severity"); severity != "" {
		filters["severity"] = severity
	}
	if blocked := c.Query("blocked"); blocked != "" {
		filters["blocked"] = blocked == "true"
	}

	limit := 50
	if l := c.Query("limit"); l != "" {
		if parsed, err := strconv.Atoi(l); err == nil && parsed > 0 && parsed <= 200 {
			limit = parsed
		}
	}

	offset := 0
	if o := c.Query("offset"); o != "" {
		if parsed, err := strconv.Atoi(o); err == nil && parsed >= 0 {
			offset = parsed
		}
	}

	logs, err := h.guardian.GetAuditLogs(filters, limit, offset)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve audit logs"})
		return
	}

	c.JSON(http.StatusOK, logs)
}

// GetSecurityStats returns security statistics
func (h *SecurityHandler) GetSecurityStats(c *gin.Context) {
	// Only admins can view security stats
	if !middleware.IsAdmin(c) {
		c.JSON(http.StatusForbidden, gin.H{"error": "Admin access required"})
		return
	}

	// Parse period (default 24h)
	period := 24 * time.Hour
	if p := c.Query("period"); p != "" {
		switch p {
		case "1h":
			period = time.Hour
		case "6h":
			period = 6 * time.Hour
		case "24h":
			period = 24 * time.Hour
		case "7d":
			period = 7 * 24 * time.Hour
		case "30d":
			period = 30 * 24 * time.Hour
		}
	}

	// Get organization ID if user is not super admin
	var orgID *int64
	if !middleware.IsAdmin(c) {
		id := middleware.GetOrganizationID(c)
		if id > 0 {
			orgID = &id
		}
	}

	stats := h.guardian.GetSecurityStats()

	// Get audit stats
	auditStats, err := h.guardian.GetAuditLogs(map[string]interface{}{}, 0, 0)
	if err == nil {
		stats["recent_events"] = len(auditStats)
	}

	// Add rate limiter stats
	if orgID != nil {
		stats["organization_id"] = *orgID
	}
	stats["period"] = period.String()

	c.JSON(http.StatusOK, stats)
}

// ValidateInput validates input for security threats
func (h *SecurityHandler) ValidateInput(c *gin.Context) {
	var req struct {
		Input string `json:"input" binding:"required"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Get the guardian's pattern detector
	guardian := security.GetGuardian()
	result := guardian.GetSecurityStats()

	// Check for patterns
	detector := security.NewPatternDetector()
	detector.LoadDefaultPatterns()

	validation := detector.ValidateInput(req.Input)

	c.JSON(http.StatusOK, gin.H{
		"is_valid":        validation.IsValid,
		"severity":        validation.Severity,
		"threats":         validation.Threats,
		"patterns_loaded": result["patterns_loaded"],
	})
}

// GetRateLimitStatus returns rate limit status for the current user
func (h *SecurityHandler) GetRateLimitStatus(c *gin.Context) {
	clientIP := c.ClientIP()
	endpoint := c.Query("endpoint")
	if endpoint == "" {
		endpoint = "global"
	}

	// This is a simplified status - in production you'd want more details
	c.JSON(http.StatusOK, gin.H{
		"ip":       clientIP,
		"endpoint": endpoint,
		"status":   "active",
		"message":  "Rate limiting is active",
	})
}

// ReloadPolicies reloads security policies (admin only)
func (h *SecurityHandler) ReloadPolicies(c *gin.Context) {
	// Only admins can reload policies
	if !middleware.IsAdmin(c) {
		c.JSON(http.StatusForbidden, gin.H{"error": "Admin access required"})
		return
	}

	h.guardian.ReloadPolicies()

	c.JSON(http.StatusOK, gin.H{
		"message": "Security policies reloaded successfully",
		"stats":   h.guardian.GetSecurityStats(),
	})
}

// GetSecurityDashboard returns a comprehensive security dashboard
func (h *SecurityHandler) GetSecurityDashboard(c *gin.Context) {
	// Only admins can view security dashboard
	if !middleware.IsAdmin(c) {
		c.JSON(http.StatusForbidden, gin.H{"error": "Admin access required"})
		return
	}

	stats := h.guardian.GetSecurityStats()

	// Get recent blocked events
	blockedFilters := map[string]interface{}{"blocked": true}
	blockedEvents, _ := h.guardian.GetAuditLogs(blockedFilters, 10, 0)

	// Get recent critical events
	criticalFilters := map[string]interface{}{"severity": "critical"}
	criticalEvents, _ := h.guardian.GetAuditLogs(criticalFilters, 10, 0)

	c.JSON(http.StatusOK, gin.H{
		"stats":                stats,
		"recent_blocked":       blockedEvents,
		"recent_critical":      criticalEvents,
		"guardian_status":      "active",
		"last_updated":         time.Now().Format(time.RFC3339),
	})
}
