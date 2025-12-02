package security

import (
	"sync"
	"time"
)

// RateLimiter implements a sliding window rate limiter
type RateLimiter struct {
	mu       sync.RWMutex
	entries  map[string]*RateLimitEntry
	config   RateLimitConfig
	cleanupC chan struct{}
}

// RateLimitEntry tracks requests for a single identifier
type RateLimitEntry struct {
	Requests    []time.Time
	BlockedAt   *time.Time
	BlockCount  int
	LastRequest time.Time
}

// RateLimitConfig defines rate limiting thresholds
type RateLimitConfig struct {
	RequestsPerMinute int
	RequestsPerHour   int
	BurstLimit        int
	BlockDuration     time.Duration
	CleanupInterval   time.Duration
}

// NewRateLimiter creates a new rate limiter with default settings
func NewRateLimiter() *RateLimiter {
	rl := &RateLimiter{
		entries: make(map[string]*RateLimitEntry),
		config: RateLimitConfig{
			RequestsPerMinute: 60,
			RequestsPerHour:   500,
			BurstLimit:        10,      // Max requests per second
			BlockDuration:     time.Minute * 5,
			CleanupInterval:   time.Minute * 10,
		},
		cleanupC: make(chan struct{}),
	}

	// Start cleanup goroutine
	go rl.cleanupLoop()

	return rl
}

// Check verifies if a request should be allowed
func (rl *RateLimiter) Check(identifier, endpoint string) (blocked bool, reason string) {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	key := identifier + ":" + endpoint
	now := time.Now()

	entry, exists := rl.entries[key]
	if !exists {
		entry = &RateLimitEntry{
			Requests: make([]time.Time, 0, 100),
		}
		rl.entries[key] = entry
	}

	// Check if currently blocked
	if entry.BlockedAt != nil {
		if now.Before(entry.BlockedAt.Add(rl.config.BlockDuration)) {
			return true, "IP temporarily blocked due to rate limit violations"
		}
		// Block expired, reset
		entry.BlockedAt = nil
		entry.Requests = entry.Requests[:0]
	}

	// Clean old requests outside the window
	oneHourAgo := now.Add(-time.Hour)
	validRequests := make([]time.Time, 0, len(entry.Requests))
	for _, t := range entry.Requests {
		if t.After(oneHourAgo) {
			validRequests = append(validRequests, t)
		}
	}
	entry.Requests = validRequests

	// Count requests in different windows
	oneMinuteAgo := now.Add(-time.Minute)
	oneSecondAgo := now.Add(-time.Second)

	var countPerMinute, countPerSecond, countPerHour int
	for _, t := range entry.Requests {
		countPerHour++
		if t.After(oneMinuteAgo) {
			countPerMinute++
		}
		if t.After(oneSecondAgo) {
			countPerSecond++
		}
	}

	// Check burst limit (per second)
	if countPerSecond >= rl.config.BurstLimit {
		entry.BlockCount++
		if entry.BlockCount >= 3 {
			blockTime := now
			entry.BlockedAt = &blockTime
			return true, "Burst limit exceeded, temporarily blocked"
		}
		return true, "Too many requests per second"
	}

	// Check per minute limit
	if countPerMinute >= rl.config.RequestsPerMinute {
		entry.BlockCount++
		if entry.BlockCount >= 5 {
			blockTime := now
			entry.BlockedAt = &blockTime
			return true, "Rate limit exceeded, temporarily blocked"
		}
		return true, "Rate limit exceeded (per minute)"
	}

	// Check per hour limit
	if countPerHour >= rl.config.RequestsPerHour {
		return true, "Rate limit exceeded (per hour)"
	}

	// Allow request
	entry.Requests = append(entry.Requests, now)
	entry.LastRequest = now

	return false, ""
}

// CheckGlobal checks global rate limits (for unauthenticated endpoints)
func (rl *RateLimiter) CheckGlobal(identifier string) (blocked bool, reason string) {
	return rl.Check(identifier, "global")
}

// GetActiveCount returns the number of active rate limit entries
func (rl *RateLimiter) GetActiveCount() int {
	rl.mu.RLock()
	defer rl.mu.RUnlock()
	return len(rl.entries)
}

// cleanupLoop periodically removes stale entries
func (rl *RateLimiter) cleanupLoop() {
	ticker := time.NewTicker(rl.config.CleanupInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			rl.cleanup()
		case <-rl.cleanupC:
			return
		}
	}
}

// cleanup removes stale entries
func (rl *RateLimiter) cleanup() {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	now := time.Now()
	staleThreshold := now.Add(-time.Hour * 2)

	for key, entry := range rl.entries {
		if entry.LastRequest.Before(staleThreshold) {
			delete(rl.entries, key)
		}
	}
}

// Stop stops the rate limiter cleanup goroutine
func (rl *RateLimiter) Stop() {
	close(rl.cleanupC)
}

// SetConfig updates the rate limiter configuration
func (rl *RateLimiter) SetConfig(config RateLimitConfig) {
	rl.mu.Lock()
	defer rl.mu.Unlock()
	rl.config = config
}

// ResetEntry resets the rate limit for a specific identifier
func (rl *RateLimiter) ResetEntry(identifier, endpoint string) {
	rl.mu.Lock()
	defer rl.mu.Unlock()
	key := identifier + ":" + endpoint
	delete(rl.entries, key)
}

// GetStatus returns the rate limit status for an identifier
func (rl *RateLimiter) GetStatus(identifier, endpoint string) map[string]interface{} {
	rl.mu.RLock()
	defer rl.mu.RUnlock()

	key := identifier + ":" + endpoint
	entry, exists := rl.entries[key]
	if !exists {
		return map[string]interface{}{
			"requests_last_minute": 0,
			"requests_last_hour":   0,
			"blocked":              false,
			"remaining_per_minute": rl.config.RequestsPerMinute,
			"remaining_per_hour":   rl.config.RequestsPerHour,
		}
	}

	now := time.Now()
	oneMinuteAgo := now.Add(-time.Minute)
	oneHourAgo := now.Add(-time.Hour)

	var countPerMinute, countPerHour int
	for _, t := range entry.Requests {
		if t.After(oneHourAgo) {
			countPerHour++
		}
		if t.After(oneMinuteAgo) {
			countPerMinute++
		}
	}

	blocked := entry.BlockedAt != nil && now.Before(entry.BlockedAt.Add(rl.config.BlockDuration))

	return map[string]interface{}{
		"requests_last_minute": countPerMinute,
		"requests_last_hour":   countPerHour,
		"blocked":              blocked,
		"remaining_per_minute": rl.config.RequestsPerMinute - countPerMinute,
		"remaining_per_hour":   rl.config.RequestsPerHour - countPerHour,
		"block_count":          entry.BlockCount,
	}
}
