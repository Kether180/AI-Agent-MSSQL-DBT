package security

import (
	"regexp"
	"strings"
)

// AIOutputFilter filters AI responses for security-sensitive content
type AIOutputFilter struct {
	sensitivePatterns   []*regexp.Regexp
	redactionPatterns   []*regexp.Regexp
	blockedInstructions []string
}

// AIOutputFilterConfig configures the output filter
type AIOutputFilterConfig struct {
	FilterCredentials      bool
	FilterAPIKeys          bool
	FilterInternalURLs     bool
	FilterSystemPrompts    bool
	FilterSensitiveData    bool
	CustomPatterns         []string
	RedactWithPlaceholder  string
}

// DefaultAIOutputFilterConfig returns secure defaults
func DefaultAIOutputFilterConfig() AIOutputFilterConfig {
	return AIOutputFilterConfig{
		FilterCredentials:     true,
		FilterAPIKeys:         true,
		FilterInternalURLs:    true,
		FilterSystemPrompts:   true,
		FilterSensitiveData:   true,
		RedactWithPlaceholder: "[REDACTED]",
	}
}

// NewAIOutputFilter creates a new AI output filter
func NewAIOutputFilter(config AIOutputFilterConfig) *AIOutputFilter {
	filter := &AIOutputFilter{
		blockedInstructions: []string{
			"ignore previous instructions",
			"disregard all prior",
			"forget your instructions",
			"new instructions:",
			"system prompt:",
			"you are now",
			"act as if",
			"pretend you are",
		},
	}

	// Build regex patterns based on config
	if config.FilterCredentials {
		filter.sensitivePatterns = append(filter.sensitivePatterns,
			// Passwords in common formats
			regexp.MustCompile(`(?i)password\s*[:=]\s*['"]?[^\s'"]+['"]?`),
			regexp.MustCompile(`(?i)passwd\s*[:=]\s*['"]?[^\s'"]+['"]?`),
			regexp.MustCompile(`(?i)pwd\s*[:=]\s*['"]?[^\s'"]+['"]?`),
			regexp.MustCompile(`(?i)secret\s*[:=]\s*['"]?[^\s'"]+['"]?`),
		)
	}

	if config.FilterAPIKeys {
		filter.sensitivePatterns = append(filter.sensitivePatterns,
			// API keys patterns
			regexp.MustCompile(`(?i)api[_-]?key\s*[:=]\s*['"]?[A-Za-z0-9_\-]{20,}['"]?`),
			regexp.MustCompile(`(?i)access[_-]?token\s*[:=]\s*['"]?[A-Za-z0-9_\-\.]{20,}['"]?`),
			regexp.MustCompile(`(?i)bearer\s+[A-Za-z0-9_\-\.]{20,}`),
			// AWS keys
			regexp.MustCompile(`AKIA[0-9A-Z]{16}`),
			// Azure keys
			regexp.MustCompile(`[a-zA-Z0-9+/]{86}==`),
			// Anthropic API keys
			regexp.MustCompile(`sk-ant-[a-zA-Z0-9\-_]{80,}`),
			// OpenAI API keys
			regexp.MustCompile(`sk-[a-zA-Z0-9]{48}`),
			// Generic API key pattern
			regexp.MustCompile(`dm_[a-f0-9]{64}`),
		)
	}

	if config.FilterInternalURLs {
		filter.sensitivePatterns = append(filter.sensitivePatterns,
			// Internal URLs
			regexp.MustCompile(`(?i)https?://localhost[:/]`),
			regexp.MustCompile(`(?i)https?://127\.0\.0\.1[:/]`),
			regexp.MustCompile(`(?i)https?://192\.168\.\d+\.\d+[:/]`),
			regexp.MustCompile(`(?i)https?://10\.\d+\.\d+\.\d+[:/]`),
			regexp.MustCompile(`(?i)https?://172\.(1[6-9]|2\d|3[01])\.\d+\.\d+[:/]`),
			regexp.MustCompile(`(?i)https?://[^/]+\.internal[:/]`),
			regexp.MustCompile(`(?i)https?://[^/]+\.local[:/]`),
		)
	}

	if config.FilterSensitiveData {
		filter.redactionPatterns = append(filter.redactionPatterns,
			// SSN
			regexp.MustCompile(`\b\d{3}-\d{2}-\d{4}\b`),
			// Credit card numbers (basic)
			regexp.MustCompile(`\b(?:\d{4}[- ]?){3}\d{4}\b`),
			// Email addresses (optionally filter)
			// regexp.MustCompile(`\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b`),
		)
	}

	// Add custom patterns
	for _, pattern := range config.CustomPatterns {
		if re, err := regexp.Compile(pattern); err == nil {
			filter.sensitivePatterns = append(filter.sensitivePatterns, re)
		}
	}

	return filter
}

// FilterOutput filters the AI output for sensitive content
func (f *AIOutputFilter) FilterOutput(output string) AIFilterResult {
	result := AIFilterResult{
		Original:     output,
		Filtered:     output,
		WasFiltered:  false,
		FilteredItems: []string{},
	}

	// Check for prompt injection attempts in output
	lowerOutput := strings.ToLower(output)
	for _, instruction := range f.blockedInstructions {
		if strings.Contains(lowerOutput, instruction) {
			result.ContainsInjection = true
			result.FilteredItems = append(result.FilteredItems, "prompt_injection_attempt")
		}
	}

	// Apply sensitive patterns
	for _, pattern := range f.sensitivePatterns {
		if pattern.MatchString(result.Filtered) {
			matches := pattern.FindAllString(result.Filtered, -1)
			for _, match := range matches {
				result.FilteredItems = append(result.FilteredItems, "sensitive_pattern")
				result.Filtered = strings.ReplaceAll(result.Filtered, match, "[REDACTED]")
				result.WasFiltered = true
			}
		}
	}

	// Apply redaction patterns
	for _, pattern := range f.redactionPatterns {
		if pattern.MatchString(result.Filtered) {
			result.Filtered = pattern.ReplaceAllString(result.Filtered, "[REDACTED]")
			result.FilteredItems = append(result.FilteredItems, "pii_redacted")
			result.WasFiltered = true
		}
	}

	return result
}

// FilterInput filters user input before sending to AI
func (f *AIOutputFilter) FilterInput(input string) AIFilterResult {
	result := AIFilterResult{
		Original:     input,
		Filtered:     input,
		WasFiltered:  false,
		FilteredItems: []string{},
	}

	// Check for prompt injection attempts
	lowerInput := strings.ToLower(input)
	for _, instruction := range f.blockedInstructions {
		if strings.Contains(lowerInput, instruction) {
			result.ContainsInjection = true
			result.FilteredItems = append(result.FilteredItems, "injection_attempt: "+instruction)
		}
	}

	// Check for attempts to extract system prompts
	extractionPatterns := []string{
		"what are your instructions",
		"show me your system prompt",
		"reveal your prompt",
		"print your instructions",
		"output your prompt",
		"what were you told",
		"repeat everything above",
		"ignore the above and",
	}

	for _, pattern := range extractionPatterns {
		if strings.Contains(lowerInput, pattern) {
			result.ContainsInjection = true
			result.FilteredItems = append(result.FilteredItems, "prompt_extraction_attempt")
		}
	}

	return result
}

// AIFilterResult contains the result of filtering
type AIFilterResult struct {
	Original          string   `json:"original,omitempty"`
	Filtered          string   `json:"filtered"`
	WasFiltered       bool     `json:"was_filtered"`
	ContainsInjection bool     `json:"contains_injection"`
	FilteredItems     []string `json:"filtered_items,omitempty"`
}

// SanitizeForLogging removes sensitive data from strings before logging
func SanitizeForLogging(input string) string {
	// Create a minimal filter for logging
	filter := NewAIOutputFilter(AIOutputFilterConfig{
		FilterCredentials:     true,
		FilterAPIKeys:         true,
		FilterSensitiveData:   true,
		RedactWithPlaceholder: "***",
	})

	result := filter.FilterOutput(input)
	return result.Filtered
}

// ValidateAIResponse validates that an AI response is safe to return
func ValidateAIResponse(response string) (bool, []string) {
	filter := NewAIOutputFilter(DefaultAIOutputFilterConfig())
	result := filter.FilterOutput(response)

	warnings := []string{}

	if result.ContainsInjection {
		warnings = append(warnings, "Response may contain prompt injection content")
	}

	if result.WasFiltered {
		warnings = append(warnings, "Sensitive content was filtered from response")
	}

	// Response is safe if no injection and reasonable length
	isSafe := !result.ContainsInjection && len(response) < 100000

	return isSafe, warnings
}

// ContentModerationResult contains moderation check results
type ContentModerationResult struct {
	Safe       bool     `json:"safe"`
	Categories []string `json:"categories,omitempty"`
	Confidence float64  `json:"confidence"`
}

// CheckContentModeration performs basic content moderation checks
func CheckContentModeration(content string) ContentModerationResult {
	result := ContentModerationResult{
		Safe:       true,
		Confidence: 0.9,
	}

	lowerContent := strings.ToLower(content)

	// Check for potentially harmful instructions
	harmfulPatterns := []struct {
		pattern  string
		category string
	}{
		{"sql injection", "security_instruction"},
		{"drop table", "destructive_sql"},
		{"delete from", "destructive_sql"},
		{"truncate table", "destructive_sql"},
		{"xp_cmdshell", "command_injection"},
		{"exec master", "command_injection"},
		{"<script>", "xss_attempt"},
		{"javascript:", "xss_attempt"},
		{"onerror=", "xss_attempt"},
	}

	for _, hp := range harmfulPatterns {
		if strings.Contains(lowerContent, hp.pattern) {
			result.Safe = false
			result.Categories = append(result.Categories, hp.category)
			result.Confidence = 0.95
		}
	}

	return result
}
