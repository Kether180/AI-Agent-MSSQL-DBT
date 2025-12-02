package security

import (
	"regexp"
	"strings"
	"sync"
)

// PatternDetector detects suspicious patterns in input
type PatternDetector struct {
	mu       sync.RWMutex
	patterns []DetectionPattern
}

// DetectionPattern represents a pattern to detect
type DetectionPattern struct {
	Pattern     *regexp.Regexp
	PatternType string
	Severity    string
	Description string
}

// NewPatternDetector creates a new pattern detector
func NewPatternDetector() *PatternDetector {
	return &PatternDetector{
		patterns: make([]DetectionPattern, 0),
	}
}

// LoadDefaultPatterns loads built-in security patterns
func (pd *PatternDetector) LoadDefaultPatterns() {
	pd.mu.Lock()
	defer pd.mu.Unlock()

	// SQL Injection patterns
	sqlInjectionPatterns := []struct {
		pattern     string
		description string
	}{
		{`(?i)(\b(SELECT|INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|EXEC|EXECUTE)\b.*\b(FROM|INTO|TABLE|DATABASE)\b)`, "SQL statement in input"},
		{`(?i)(\bUNION\s+SELECT\b)`, "UNION SELECT injection"},
		{`(?i)(\bOR\s+1\s*=\s*1\b)`, "SQL OR 1=1 injection"},
		{`(?i)(\bAND\s+1\s*=\s*1\b)`, "SQL AND 1=1 injection"},
		{`(?i)(--\s*$|;\s*--)`, "SQL comment injection"},
		{`(?i)(\bxp_cmdshell\b)`, "xp_cmdshell attempt"},
		{`(?i)(\bINFORMATION_SCHEMA\b)`, "Information schema access"},
		{`(?i)(\bSLEEP\s*\()`, "SQL SLEEP injection"},
		{`(?i)(\bBENCHMARK\s*\()`, "SQL BENCHMARK injection"},
		{`(?i)(\bWAITFOR\s+DELAY\b)`, "WAITFOR DELAY injection"},
	}

	for _, p := range sqlInjectionPatterns {
		pd.addPatternInternal(p.pattern, "sql_injection", "high", p.description)
	}

	// XSS patterns
	xssPatterns := []struct {
		pattern     string
		description string
	}{
		{`(?i)(<script[^>]*>)`, "Script tag detected"},
		{`(?i)(javascript\s*:)`, "JavaScript protocol"},
		{`(?i)(on\w+\s*=\s*["']?[^"']*["']?)`, "Event handler attribute"},
		{`(?i)(<iframe[^>]*>)`, "Iframe tag detected"},
		{`(?i)(<embed[^>]*>)`, "Embed tag detected"},
		{`(?i)(<object[^>]*>)`, "Object tag detected"},
		{`(?i)(data\s*:\s*text/html)`, "Data URI HTML"},
		{`(?i)(<svg[^>]*onload)`, "SVG onload attack"},
	}

	for _, p := range xssPatterns {
		pd.addPatternInternal(p.pattern, "xss", "high", p.description)
	}

	// Prompt injection patterns (for AI agents)
	promptInjectionPatterns := []struct {
		pattern     string
		description string
	}{
		{`(?i)(ignore\s+(previous|above|all)\s+instructions)`, "Ignore instructions attempt"},
		{`(?i)(disregard\s+(previous|above|all))`, "Disregard instructions attempt"},
		{`(?i)(forget\s+(previous|above|all))`, "Forget instructions attempt"},
		{`(?i)(system\s*:\s*you\s+are)`, "System role injection"},
		{`(?i)(new\s+instructions)`, "New instructions injection"},
		{`(?i)(</system>)`, "System tag injection"},
		{`(?i)(<\|im_start\|>)`, "Instruction marker injection"},
		{`(?i)(<\|im_end\|>)`, "Instruction marker injection"},
		{`(?i)(HUMAN:|ASSISTANT:)`, "Role marker injection"},
		{`(?i)(###\s*Instruction)`, "Instruction header injection"},
		{`(?i)(you\s+are\s+now\s+)`, "Role change attempt"},
		{`(?i)(act\s+as\s+if\s+you)`, "Behavior change attempt"},
		{`(?i)(pretend\s+you\s+are)`, "Pretend injection"},
		{`(?i)(reveal\s+your\s+(system|instructions|prompt))`, "System reveal attempt"},
		{`(?i)(what\s+are\s+your\s+instructions)`, "Instructions extraction attempt"},
	}

	for _, p := range promptInjectionPatterns {
		pd.addPatternInternal(p.pattern, "prompt_injection", "critical", p.description)
	}

	// Command injection patterns
	commandInjectionPatterns := []struct {
		pattern     string
		description string
	}{
		{`(?i)(;\s*(ls|cat|rm|wget|curl|bash|sh|nc|ncat)\s)`, "Shell command injection"},
		{`(?i)(\|\s*(ls|cat|rm|wget|curl|bash|sh)\s)`, "Pipe command injection"},
		{`(?i)(\$\(.*\))`, "Command substitution"},
		{"`[^`]+`", "Backtick command execution"},
		{`(?i)(&&\s*(rm|wget|curl|bash|sh)\s)`, "Command chaining"},
	}

	for _, p := range commandInjectionPatterns {
		pd.addPatternInternal(p.pattern, "command_injection", "critical", p.description)
	}

	// Path traversal patterns
	pathTraversalPatterns := []struct {
		pattern     string
		description string
	}{
		{`(\.\./|\.\.\\)`, "Directory traversal attempt"},
		{`(?i)(/etc/passwd)`, "Passwd file access"},
		{`(?i)(/etc/shadow)`, "Shadow file access"},
		{`(?i)(C:\\Windows\\)`, "Windows system path"},
	}

	for _, p := range pathTraversalPatterns {
		pd.addPatternInternal(p.pattern, "path_traversal", "high", p.description)
	}

	// Sensitive data patterns
	sensitiveDataPatterns := []struct {
		pattern     string
		description string
	}{
		{`(?i)(password\s*[=:]\s*["']?[^"'\s]+)`, "Password in request"},
		{`(?i)(api[_-]?key\s*[=:]\s*["']?[^"'\s]+)`, "API key in request"},
		{`(?i)(secret\s*[=:]\s*["']?[^"'\s]+)`, "Secret in request"},
		{`(?i)(bearer\s+[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+)`, "JWT token exposed"},
	}

	for _, p := range sensitiveDataPatterns {
		pd.addPatternInternal(p.pattern, "sensitive_data", "medium", p.description)
	}
}

// addPatternInternal adds a pattern without locking (internal use)
func (pd *PatternDetector) addPatternInternal(pattern, patternType, severity, description string) {
	compiled, err := regexp.Compile(pattern)
	if err != nil {
		return // Skip invalid patterns
	}

	pd.patterns = append(pd.patterns, DetectionPattern{
		Pattern:     compiled,
		PatternType: patternType,
		Severity:    severity,
		Description: description,
	})
}

// AddPattern adds a custom pattern to the detector
func (pd *PatternDetector) AddPattern(pattern, patternType, severity string) error {
	pd.mu.Lock()
	defer pd.mu.Unlock()

	compiled, err := regexp.Compile(pattern)
	if err != nil {
		return err
	}

	pd.patterns = append(pd.patterns, DetectionPattern{
		Pattern:     compiled,
		PatternType: patternType,
		Severity:    severity,
	})

	return nil
}

// Detect checks input for suspicious patterns
func (pd *PatternDetector) Detect(input string) (detected bool, patternType string, severity string) {
	pd.mu.RLock()
	defer pd.mu.RUnlock()

	// Normalize input
	normalizedInput := strings.ToLower(input)

	for _, p := range pd.patterns {
		if p.Pattern.MatchString(normalizedInput) || p.Pattern.MatchString(input) {
			return true, p.PatternType, p.Severity
		}
	}

	return false, "", ""
}

// DetectAll returns all matching patterns
func (pd *PatternDetector) DetectAll(input string) []DetectionPattern {
	pd.mu.RLock()
	defer pd.mu.RUnlock()

	var matches []DetectionPattern
	normalizedInput := strings.ToLower(input)

	for _, p := range pd.patterns {
		if p.Pattern.MatchString(normalizedInput) || p.Pattern.MatchString(input) {
			matches = append(matches, p)
		}
	}

	return matches
}

// GetPatternCount returns the number of loaded patterns
func (pd *PatternDetector) GetPatternCount() int {
	pd.mu.RLock()
	defer pd.mu.RUnlock()
	return len(pd.patterns)
}

// SanitizeInput attempts to remove detected patterns from input
func (pd *PatternDetector) SanitizeInput(input string) string {
	pd.mu.RLock()
	defer pd.mu.RUnlock()

	sanitized := input

	for _, p := range pd.patterns {
		sanitized = p.Pattern.ReplaceAllString(sanitized, "[BLOCKED]")
	}

	return sanitized
}

// ValidateInput checks if input is safe and returns validation result
func (pd *PatternDetector) ValidateInput(input string) ValidationResult {
	matches := pd.DetectAll(input)

	result := ValidationResult{
		IsValid:  len(matches) == 0,
		Input:    input,
		Threats:  make([]ThreatInfo, 0, len(matches)),
		Severity: "none",
	}

	for _, m := range matches {
		result.Threats = append(result.Threats, ThreatInfo{
			Type:        m.PatternType,
			Severity:    m.Severity,
			Description: m.Description,
		})

		// Track highest severity
		if severityLevel(m.Severity) > severityLevel(result.Severity) {
			result.Severity = m.Severity
		}
	}

	return result
}

// ValidationResult contains the result of input validation
type ValidationResult struct {
	IsValid  bool         `json:"is_valid"`
	Input    string       `json:"input,omitempty"`
	Threats  []ThreatInfo `json:"threats,omitempty"`
	Severity string       `json:"severity"`
}

// ThreatInfo contains information about a detected threat
type ThreatInfo struct {
	Type        string `json:"type"`
	Severity    string `json:"severity"`
	Description string `json:"description"`
}

// severityLevel returns numeric level for severity comparison
func severityLevel(severity string) int {
	switch severity {
	case "critical":
		return 4
	case "high":
		return 3
	case "medium":
		return 2
	case "low":
		return 1
	default:
		return 0
	}
}
