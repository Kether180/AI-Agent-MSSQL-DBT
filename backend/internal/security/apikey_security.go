package security

import (
	"crypto/sha256"
	"crypto/subtle"
	"encoding/hex"
	"fmt"
	"log"
	"net"
	"strings"
	"sync"
	"time"
)

// APIKeyConfig holds configuration for API key security
type APIKeyConfig struct {
	DefaultExpirationDays int           // Default expiration in days (0 = no expiration)
	MaxExpirationDays     int           // Maximum allowed expiration
	RequireIPRestriction  bool          // Require IP restrictions for new keys
	HashKeys              bool          // Hash keys in database
	RateLimitWindow       time.Duration // Window for rate limiting
	MaxRequestsPerWindow  int           // Max requests per window
}

// DefaultAPIKeyConfig returns sensible defaults
func DefaultAPIKeyConfig() APIKeyConfig {
	return APIKeyConfig{
		DefaultExpirationDays: 90,  // 90 days default expiration
		MaxExpirationDays:     365, // Max 1 year
		RequireIPRestriction:  false,
		HashKeys:              true,
		RateLimitWindow:       time.Minute,
		MaxRequestsPerWindow:  100,
	}
}

// APIKeyValidator validates API keys with additional security checks
type APIKeyValidator struct {
	mu         sync.RWMutex
	config     APIKeyConfig
	usageStats map[string]*APIKeyUsage
}

// APIKeyUsage tracks usage statistics for an API key
type APIKeyUsage struct {
	KeyHash       string
	RequestCount  int
	WindowStart   time.Time
	LastUsed      time.Time
	TotalRequests int64
	IPAddresses   map[string]int
}

// APIKeyValidationResult contains the result of API key validation
type APIKeyValidationResult struct {
	Valid           bool     `json:"valid"`
	Expired         bool     `json:"expired,omitempty"`
	RateLimited     bool     `json:"rate_limited,omitempty"`
	IPBlocked       bool     `json:"ip_blocked,omitempty"`
	Error           string   `json:"error,omitempty"`
	RemainingQuota  int      `json:"remaining_quota,omitempty"`
	ExpiresAt       *time.Time `json:"expires_at,omitempty"`
}

var apiKeyValidator *APIKeyValidator
var apiKeyValidatorOnce sync.Once

// GetAPIKeyValidator returns the singleton APIKeyValidator instance
func GetAPIKeyValidator() *APIKeyValidator {
	apiKeyValidatorOnce.Do(func() {
		apiKeyValidator = &APIKeyValidator{
			config:     DefaultAPIKeyConfig(),
			usageStats: make(map[string]*APIKeyUsage),
		}
		// Start cleanup goroutine
		go apiKeyValidator.cleanupLoop()
	})
	return apiKeyValidator
}

// SetConfig updates the API key configuration
func (v *APIKeyValidator) SetConfig(config APIKeyConfig) {
	v.mu.Lock()
	defer v.mu.Unlock()
	v.config = config
}

// HashAPIKey creates a SHA-256 hash of an API key
func HashAPIKey(key string) string {
	hash := sha256.Sum256([]byte(key))
	return hex.EncodeToString(hash[:])
}

// ValidateKey performs comprehensive validation of an API key
func (v *APIKeyValidator) ValidateKey(key, clientIP string, allowedIPs []string, expiresAt *time.Time) APIKeyValidationResult {
	result := APIKeyValidationResult{Valid: true}

	// Check expiration
	if expiresAt != nil && time.Now().After(*expiresAt) {
		result.Valid = false
		result.Expired = true
		result.Error = "API key has expired"
		result.ExpiresAt = expiresAt
		return result
	}
	result.ExpiresAt = expiresAt

	// Check IP restrictions
	if len(allowedIPs) > 0 && clientIP != "" {
		if !v.isIPAllowed(clientIP, allowedIPs) {
			result.Valid = false
			result.IPBlocked = true
			result.Error = "IP address not authorized for this API key"
			log.Printf("API key used from unauthorized IP: %s (allowed: %v)", clientIP, allowedIPs)
			return result
		}
	}

	// Check rate limit
	keyHash := HashAPIKey(key)
	if v.isRateLimited(keyHash, clientIP) {
		result.Valid = false
		result.RateLimited = true
		result.Error = "Rate limit exceeded for this API key"
		result.RemainingQuota = 0
		return result
	}

	// Record usage
	remaining := v.recordUsage(keyHash, clientIP)
	result.RemainingQuota = remaining

	return result
}

// isIPAllowed checks if the client IP is in the allowed list
func (v *APIKeyValidator) isIPAllowed(clientIP string, allowedIPs []string) bool {
	clientAddr := net.ParseIP(clientIP)
	if clientAddr == nil {
		return false
	}

	for _, allowed := range allowedIPs {
		allowed = strings.TrimSpace(allowed)
		if allowed == "" {
			continue
		}

		// Check if it's a CIDR notation
		if strings.Contains(allowed, "/") {
			_, ipNet, err := net.ParseCIDR(allowed)
			if err == nil && ipNet.Contains(clientAddr) {
				return true
			}
		} else {
			// Exact IP match
			allowedAddr := net.ParseIP(allowed)
			if allowedAddr != nil && clientAddr.Equal(allowedAddr) {
				return true
			}
		}
	}

	return false
}

// isRateLimited checks if the API key has exceeded its rate limit
func (v *APIKeyValidator) isRateLimited(keyHash, clientIP string) bool {
	v.mu.RLock()
	defer v.mu.RUnlock()

	usage, exists := v.usageStats[keyHash]
	if !exists {
		return false
	}

	// Check if we're in a new window
	if time.Since(usage.WindowStart) > v.config.RateLimitWindow {
		return false
	}

	return usage.RequestCount >= v.config.MaxRequestsPerWindow
}

// recordUsage records a usage event for an API key
func (v *APIKeyValidator) recordUsage(keyHash, clientIP string) int {
	v.mu.Lock()
	defer v.mu.Unlock()

	usage, exists := v.usageStats[keyHash]
	if !exists {
		usage = &APIKeyUsage{
			KeyHash:     keyHash,
			WindowStart: time.Now(),
			IPAddresses: make(map[string]int),
		}
		v.usageStats[keyHash] = usage
	}

	// Reset window if needed
	if time.Since(usage.WindowStart) > v.config.RateLimitWindow {
		usage.WindowStart = time.Now()
		usage.RequestCount = 0
	}

	usage.RequestCount++
	usage.TotalRequests++
	usage.LastUsed = time.Now()
	if clientIP != "" {
		usage.IPAddresses[clientIP]++
	}

	return v.config.MaxRequestsPerWindow - usage.RequestCount
}

// GetUsageStats returns usage statistics for an API key
func (v *APIKeyValidator) GetUsageStats(keyHash string) *APIKeyUsageStats {
	v.mu.RLock()
	defer v.mu.RUnlock()

	usage, exists := v.usageStats[keyHash]
	if !exists {
		return nil
	}

	return &APIKeyUsageStats{
		TotalRequests:   usage.TotalRequests,
		LastUsed:        usage.LastUsed,
		UniqueIPs:       len(usage.IPAddresses),
		CurrentWindow:   usage.RequestCount,
		WindowRemaining: v.config.MaxRequestsPerWindow - usage.RequestCount,
	}
}

// APIKeyUsageStats contains usage statistics
type APIKeyUsageStats struct {
	TotalRequests   int64     `json:"total_requests"`
	LastUsed        time.Time `json:"last_used"`
	UniqueIPs       int       `json:"unique_ips"`
	CurrentWindow   int       `json:"current_window_requests"`
	WindowRemaining int       `json:"window_remaining"`
}

// SecureCompare performs a constant-time comparison of two API keys
func SecureCompare(a, b string) bool {
	return subtle.ConstantTimeCompare([]byte(a), []byte(b)) == 1
}

// ValidateIPList validates a list of IP addresses or CIDR notations
func ValidateIPList(ips []string) error {
	for _, ip := range ips {
		ip = strings.TrimSpace(ip)
		if ip == "" {
			continue
		}

		// Check CIDR notation
		if strings.Contains(ip, "/") {
			_, _, err := net.ParseCIDR(ip)
			if err != nil {
				return fmt.Errorf("invalid CIDR notation '%s': %w", ip, err)
			}
		} else {
			// Check plain IP
			if net.ParseIP(ip) == nil {
				return fmt.Errorf("invalid IP address '%s'", ip)
			}
		}
	}
	return nil
}

// cleanupLoop periodically cleans up old usage data
func (v *APIKeyValidator) cleanupLoop() {
	ticker := time.NewTicker(10 * time.Minute)
	defer ticker.Stop()

	for range ticker.C {
		v.cleanup()
	}
}

// cleanup removes stale usage records
func (v *APIKeyValidator) cleanup() {
	v.mu.Lock()
	defer v.mu.Unlock()

	staleThreshold := time.Hour * 24 // Remove records not used in 24 hours

	for keyHash, usage := range v.usageStats {
		if time.Since(usage.LastUsed) > staleThreshold {
			delete(v.usageStats, keyHash)
		}
	}
}

// GenerateExpirationDate generates an expiration date based on days
func GenerateExpirationDate(days int) *time.Time {
	if days <= 0 {
		return nil
	}
	expiry := time.Now().AddDate(0, 0, days)
	return &expiry
}

// FormatExpirationWarning returns a warning message if expiration is near
func FormatExpirationWarning(expiresAt *time.Time) string {
	if expiresAt == nil {
		return ""
	}

	daysUntilExpiry := int(time.Until(*expiresAt).Hours() / 24)

	if daysUntilExpiry <= 0 {
		return "API key has expired"
	} else if daysUntilExpiry <= 7 {
		return fmt.Sprintf("API key expires in %d days", daysUntilExpiry)
	} else if daysUntilExpiry <= 30 {
		return fmt.Sprintf("API key expires in %d days", daysUntilExpiry)
	}

	return ""
}
