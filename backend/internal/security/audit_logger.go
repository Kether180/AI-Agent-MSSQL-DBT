package security

import (
	"encoding/json"
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/datamigrate-ai/backend/internal/db"
)

// AuditLogger handles security audit logging
type AuditLogger struct {
	mu         sync.Mutex
	buffer     []*SecurityEvent
	bufferSize int
	flushChan  chan struct{}
	stopChan   chan struct{}
}

// NewAuditLogger creates a new audit logger
func NewAuditLogger() *AuditLogger {
	al := &AuditLogger{
		buffer:     make([]*SecurityEvent, 0, 100),
		bufferSize: 100,
		flushChan:  make(chan struct{}, 1),
		stopChan:   make(chan struct{}),
	}

	// Start background flush goroutine
	go al.flushLoop()

	return al
}

// Log adds a security event to the audit log
func (al *AuditLogger) Log(event *SecurityEvent) {
	al.mu.Lock()
	defer al.mu.Unlock()

	// Set timestamp if not set
	if event.Timestamp.IsZero() {
		event.Timestamp = time.Now()
	}

	// Add to buffer
	al.buffer = append(al.buffer, event)

	// Log critical events immediately to console
	if event.Severity == "critical" || event.Blocked {
		log.Printf("[SECURITY] %s: %s - IP: %s, Endpoint: %s, Blocked: %v, Reason: %s",
			event.Severity, event.EventType, event.IPAddress, event.Endpoint, event.Blocked, event.BlockReason)
	}

	// Trigger flush if buffer is full
	if len(al.buffer) >= al.bufferSize {
		select {
		case al.flushChan <- struct{}{}:
		default:
		}
	}
}

// flushLoop periodically flushes the buffer to the database
func (al *AuditLogger) flushLoop() {
	ticker := time.NewTicker(time.Second * 10)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			al.Flush()
		case <-al.flushChan:
			al.Flush()
		case <-al.stopChan:
			al.Flush() // Final flush before stopping
			return
		}
	}
}

// Flush writes buffered events to the database
func (al *AuditLogger) Flush() {
	al.mu.Lock()
	if len(al.buffer) == 0 {
		al.mu.Unlock()
		return
	}

	// Copy buffer and reset
	events := make([]*SecurityEvent, len(al.buffer))
	copy(events, al.buffer)
	al.buffer = al.buffer[:0]
	al.mu.Unlock()

	// Write to database
	for _, event := range events {
		al.writeToDatabase(event)
	}
}

// writeToDatabase persists a security event to the database
func (al *AuditLogger) writeToDatabase(event *SecurityEvent) {
	metadataJSON, _ := json.Marshal(event.Metadata)

	query := `
		INSERT INTO security_audit_logs
		(event_type, severity, user_id, organization_id, ip_address, user_agent,
		 endpoint, method, request_body, response_status, blocked, block_reason, metadata, created_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
	`

	_, err := db.DB.Exec(query,
		event.EventType,
		event.Severity,
		event.UserID,
		event.OrganizationID,
		event.IPAddress,
		event.UserAgent,
		event.Endpoint,
		event.Method,
		event.RequestBody,
		event.ResponseStatus,
		event.Blocked,
		event.BlockReason,
		string(metadataJSON),
		event.Timestamp,
	)

	if err != nil {
		log.Printf("Error writing audit log to database: %v", err)
	}
}

// GetLogs retrieves audit logs with optional filtering
func (al *AuditLogger) GetLogs(filters map[string]interface{}, limit, offset int) ([]SecurityEvent, error) {
	query := `
		SELECT event_type, severity, user_id, organization_id, ip_address, user_agent,
		       endpoint, method, request_body, response_status, blocked, block_reason,
		       metadata, created_at
		FROM security_audit_logs
		WHERE 1=1
	`
	args := []interface{}{}
	argCount := 0

	// Apply filters
	if eventType, ok := filters["event_type"].(string); ok && eventType != "" {
		argCount++
		query += fmt.Sprintf(" AND event_type = $%d", argCount)
		args = append(args, eventType)
	}

	if severity, ok := filters["severity"].(string); ok && severity != "" {
		argCount++
		query += fmt.Sprintf(" AND severity = $%d", argCount)
		args = append(args, severity)
	}

	if userID, ok := filters["user_id"].(int64); ok && userID > 0 {
		argCount++
		query += fmt.Sprintf(" AND user_id = $%d", argCount)
		args = append(args, userID)
	}

	if orgID, ok := filters["organization_id"].(int64); ok && orgID > 0 {
		argCount++
		query += fmt.Sprintf(" AND organization_id = $%d", argCount)
		args = append(args, orgID)
	}

	if blocked, ok := filters["blocked"].(bool); ok {
		argCount++
		query += fmt.Sprintf(" AND blocked = $%d", argCount)
		args = append(args, blocked)
	}

	if startDate, ok := filters["start_date"].(time.Time); ok {
		argCount++
		query += fmt.Sprintf(" AND created_at >= $%d", argCount)
		args = append(args, startDate)
	}

	if endDate, ok := filters["end_date"].(time.Time); ok {
		argCount++
		query += fmt.Sprintf(" AND created_at <= $%d", argCount)
		args = append(args, endDate)
	}

	// Order and pagination
	query += " ORDER BY created_at DESC"
	argCount++
	query += fmt.Sprintf(" LIMIT $%d", argCount)
	args = append(args, limit)
	argCount++
	query += fmt.Sprintf(" OFFSET $%d", argCount)
	args = append(args, offset)

	rows, err := db.DB.Query(query, args...)
	if err != nil {
		return nil, fmt.Errorf("failed to query audit logs: %w", err)
	}
	defer rows.Close()

	var events []SecurityEvent
	for rows.Next() {
		var event SecurityEvent
		var metadataJSON string
		var userID, orgID *int64

		err := rows.Scan(
			&event.EventType,
			&event.Severity,
			&userID,
			&orgID,
			&event.IPAddress,
			&event.UserAgent,
			&event.Endpoint,
			&event.Method,
			&event.RequestBody,
			&event.ResponseStatus,
			&event.Blocked,
			&event.BlockReason,
			&metadataJSON,
			&event.Timestamp,
		)
		if err != nil {
			continue
		}

		event.UserID = userID
		event.OrganizationID = orgID

		if metadataJSON != "" {
			json.Unmarshal([]byte(metadataJSON), &event.Metadata)
		}

		events = append(events, event)
	}

	return events, nil
}

// GetStats returns security statistics
func (al *AuditLogger) GetStats(orgID *int64, period time.Duration) (map[string]interface{}, error) {
	since := time.Now().Add(-period)

	baseQuery := `
		SELECT
			COUNT(*) as total_events,
			COUNT(*) FILTER (WHERE blocked = true) as blocked_count,
			COUNT(*) FILTER (WHERE severity = 'critical') as critical_count,
			COUNT(*) FILTER (WHERE severity = 'high') as high_count,
			COUNT(*) FILTER (WHERE event_type = 'rate_limit_exceeded') as rate_limit_count,
			COUNT(*) FILTER (WHERE event_type = 'suspicious_pattern') as suspicious_count
		FROM security_audit_logs
		WHERE created_at >= $1
	`

	args := []interface{}{since}
	if orgID != nil {
		baseQuery += " AND organization_id = $2"
		args = append(args, *orgID)
	}

	var totalEvents, blockedCount, criticalCount, highCount, rateLimitCount, suspiciousCount int
	err := db.DB.QueryRow(baseQuery, args...).Scan(
		&totalEvents, &blockedCount, &criticalCount, &highCount, &rateLimitCount, &suspiciousCount,
	)
	if err != nil {
		return nil, fmt.Errorf("failed to get audit stats: %w", err)
	}

	// Get top blocked IPs
	topIPsQuery := `
		SELECT ip_address, COUNT(*) as count
		FROM security_audit_logs
		WHERE created_at >= $1 AND blocked = true
	`
	if orgID != nil {
		topIPsQuery += " AND organization_id = $2"
	}
	topIPsQuery += " GROUP BY ip_address ORDER BY count DESC LIMIT 10"

	topIPs := make([]map[string]interface{}, 0)
	rows, err := db.DB.Query(topIPsQuery, args...)
	if err == nil {
		defer rows.Close()
		for rows.Next() {
			var ip string
			var count int
			if rows.Scan(&ip, &count) == nil {
				topIPs = append(topIPs, map[string]interface{}{
					"ip":    ip,
					"count": count,
				})
			}
		}
	}

	// Get events by type
	eventsByType := make(map[string]int)
	eventTypeQuery := `
		SELECT event_type, COUNT(*) as count
		FROM security_audit_logs
		WHERE created_at >= $1
	`
	if orgID != nil {
		eventTypeQuery += " AND organization_id = $2"
	}
	eventTypeQuery += " GROUP BY event_type"

	rows, err = db.DB.Query(eventTypeQuery, args...)
	if err == nil {
		defer rows.Close()
		for rows.Next() {
			var eventType string
			var count int
			if rows.Scan(&eventType, &count) == nil {
				eventsByType[eventType] = count
			}
		}
	}

	return map[string]interface{}{
		"period":               period.String(),
		"total_events":         totalEvents,
		"blocked_count":        blockedCount,
		"critical_count":       criticalCount,
		"high_severity_count":  highCount,
		"rate_limit_events":    rateLimitCount,
		"suspicious_patterns":  suspiciousCount,
		"top_blocked_ips":      topIPs,
		"events_by_type":       eventsByType,
		"block_rate_percent":   float64(blockedCount) / float64(max(totalEvents, 1)) * 100,
	}, nil
}

// Stop stops the audit logger
func (al *AuditLogger) Stop() {
	close(al.stopChan)
}

// max returns the larger of two integers
func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}

// LogLoginAttempt logs a login attempt
func (al *AuditLogger) LogLoginAttempt(email, ip, userAgent string, success bool, userID *int64) {
	severity := "info"
	eventType := "login_success"
	if !success {
		severity = "warning"
		eventType = "login_failed"
	}

	event := &SecurityEvent{
		EventType: eventType,
		Severity:  severity,
		UserID:    userID,
		IPAddress: ip,
		UserAgent: userAgent,
		Endpoint:  "/api/v1/auth/login",
		Method:    "POST",
		Metadata: map[string]interface{}{
			"email":   email,
			"success": success,
		},
		Timestamp: time.Now(),
	}

	al.Log(event)
}

// LogPasswordChange logs a password change event
func (al *AuditLogger) LogPasswordChange(userID int64, ip, userAgent string, success bool) {
	severity := "info"
	eventType := "password_changed"
	if !success {
		severity = "warning"
		eventType = "password_change_failed"
	}

	event := &SecurityEvent{
		EventType: eventType,
		Severity:  severity,
		UserID:    &userID,
		IPAddress: ip,
		UserAgent: userAgent,
		Endpoint:  "/api/v1/auth/password",
		Method:    "PUT",
		Metadata: map[string]interface{}{
			"success": success,
		},
		Timestamp: time.Now(),
	}

	al.Log(event)
}

// LogDataAccess logs sensitive data access
func (al *AuditLogger) LogDataAccess(userID, orgID *int64, resourceType, resourceID, action, ip string) {
	event := &SecurityEvent{
		EventType:      "data_access",
		Severity:       "info",
		UserID:         userID,
		OrganizationID: orgID,
		IPAddress:      ip,
		Metadata: map[string]interface{}{
			"resource_type": resourceType,
			"resource_id":   resourceID,
			"action":        action,
		},
		Timestamp: time.Now(),
	}

	al.Log(event)
}
