package security

import (
	"sync"
	"time"
)

// AccountLockout manages failed login attempts and account lockouts
type AccountLockout struct {
	mu              sync.RWMutex
	attempts        map[string]*LoginAttempts
	config          LockoutConfig
	cleanupInterval time.Duration
	stopCleanup     chan struct{}
}

// LoginAttempts tracks login attempts for an email/IP combination
type LoginAttempts struct {
	FailedCount  int
	LastAttempt  time.Time
	LockedUntil  *time.Time
	LockCount    int // Number of times account has been locked
	IPAddresses  map[string]int
	LastSuccess  *time.Time
}

// LockoutConfig defines the lockout policy
type LockoutConfig struct {
	MaxAttempts         int           // Max failed attempts before lockout
	LockoutDuration     time.Duration // How long to lock the account
	AttemptWindow       time.Duration // Window to count attempts
	ProgressiveLockout  bool          // Increase lockout duration with each lock
	MaxLockoutDuration  time.Duration // Maximum lockout duration
	NotifyOnLockout     bool          // Send notification on lockout
	TrackByIP           bool          // Also track by IP address
	IPMaxAttempts       int           // Max attempts per IP across all accounts
}

// DefaultLockoutConfig returns sensible defaults
func DefaultLockoutConfig() LockoutConfig {
	return LockoutConfig{
		MaxAttempts:        5,
		LockoutDuration:    15 * time.Minute,
		AttemptWindow:      30 * time.Minute,
		ProgressiveLockout: true,
		MaxLockoutDuration: 24 * time.Hour,
		NotifyOnLockout:    true,
		TrackByIP:          true,
		IPMaxAttempts:      20,
	}
}

var accountLockout *AccountLockout
var accountLockoutOnce sync.Once

// GetAccountLockout returns the singleton AccountLockout instance
func GetAccountLockout() *AccountLockout {
	accountLockoutOnce.Do(func() {
		accountLockout = &AccountLockout{
			attempts:        make(map[string]*LoginAttempts),
			config:          DefaultLockoutConfig(),
			cleanupInterval: 10 * time.Minute,
			stopCleanup:     make(chan struct{}),
		}
		go accountLockout.cleanupLoop()
	})
	return accountLockout
}

// SetConfig updates the lockout configuration
func (al *AccountLockout) SetConfig(config LockoutConfig) {
	al.mu.Lock()
	defer al.mu.Unlock()
	al.config = config
}

// RecordFailedAttempt records a failed login attempt
func (al *AccountLockout) RecordFailedAttempt(email, ipAddress string) LockoutStatus {
	al.mu.Lock()
	defer al.mu.Unlock()

	now := time.Now()

	// Get or create attempt record
	attempts, exists := al.attempts[email]
	if !exists {
		attempts = &LoginAttempts{
			IPAddresses: make(map[string]int),
		}
		al.attempts[email] = attempts
	}

	// Check if already locked
	if attempts.LockedUntil != nil && now.Before(*attempts.LockedUntil) {
		remaining := attempts.LockedUntil.Sub(now)
		return LockoutStatus{
			Locked:          true,
			RemainingTime:   remaining,
			AttemptsLeft:    0,
			Message:         "Account is temporarily locked due to too many failed login attempts",
			LockoutExpiry:   attempts.LockedUntil,
		}
	}

	// Clear old attempts outside the window
	if now.Sub(attempts.LastAttempt) > al.config.AttemptWindow {
		attempts.FailedCount = 0
		attempts.IPAddresses = make(map[string]int)
	}

	// Increment counters
	attempts.FailedCount++
	attempts.LastAttempt = now
	if ipAddress != "" {
		attempts.IPAddresses[ipAddress]++
	}

	// Check if should lock
	if attempts.FailedCount >= al.config.MaxAttempts {
		// Calculate lockout duration (progressive if enabled)
		lockoutDuration := al.config.LockoutDuration
		if al.config.ProgressiveLockout && attempts.LockCount > 0 {
			// Double the lockout for each subsequent lock
			multiplier := 1 << attempts.LockCount // 2^lockCount
			if multiplier > 96 { // Cap at ~96x (about 24 hours for 15-min base)
				multiplier = 96
			}
			lockoutDuration = time.Duration(multiplier) * al.config.LockoutDuration
			if lockoutDuration > al.config.MaxLockoutDuration {
				lockoutDuration = al.config.MaxLockoutDuration
			}
		}

		lockUntil := now.Add(lockoutDuration)
		attempts.LockedUntil = &lockUntil
		attempts.LockCount++
		attempts.FailedCount = 0 // Reset for next window

		return LockoutStatus{
			Locked:         true,
			RemainingTime:  lockoutDuration,
			AttemptsLeft:   0,
			Message:        "Account has been temporarily locked due to too many failed login attempts",
			LockoutExpiry:  &lockUntil,
			JustLocked:     true,
			LockCount:      attempts.LockCount,
		}
	}

	attemptsLeft := al.config.MaxAttempts - attempts.FailedCount
	return LockoutStatus{
		Locked:       false,
		AttemptsLeft: attemptsLeft,
		Message:      "",
	}
}

// RecordSuccessfulLogin records a successful login and clears attempts
func (al *AccountLockout) RecordSuccessfulLogin(email, ipAddress string) {
	al.mu.Lock()
	defer al.mu.Unlock()

	now := time.Now()

	if attempts, exists := al.attempts[email]; exists {
		attempts.FailedCount = 0
		attempts.LockedUntil = nil
		attempts.LastSuccess = &now
		attempts.IPAddresses = make(map[string]int)
		// Note: We keep LockCount for progressive lockout on future attempts
	}
}

// IsLocked checks if an account is currently locked
func (al *AccountLockout) IsLocked(email string) LockoutStatus {
	al.mu.RLock()
	defer al.mu.RUnlock()

	attempts, exists := al.attempts[email]
	if !exists {
		return LockoutStatus{
			Locked:       false,
			AttemptsLeft: al.config.MaxAttempts,
		}
	}

	now := time.Now()
	if attempts.LockedUntil != nil && now.Before(*attempts.LockedUntil) {
		remaining := attempts.LockedUntil.Sub(now)
		return LockoutStatus{
			Locked:        true,
			RemainingTime: remaining,
			AttemptsLeft:  0,
			Message:       "Account is temporarily locked",
			LockoutExpiry: attempts.LockedUntil,
		}
	}

	attemptsLeft := al.config.MaxAttempts - attempts.FailedCount
	if attemptsLeft < 0 {
		attemptsLeft = 0
	}

	return LockoutStatus{
		Locked:       false,
		AttemptsLeft: attemptsLeft,
	}
}

// CheckIPBlocked checks if an IP is blocked due to too many attempts
func (al *AccountLockout) CheckIPBlocked(ipAddress string) bool {
	if !al.config.TrackByIP {
		return false
	}

	al.mu.RLock()
	defer al.mu.RUnlock()

	totalAttempts := 0
	for _, attempts := range al.attempts {
		if count, exists := attempts.IPAddresses[ipAddress]; exists {
			totalAttempts += count
		}
	}

	return totalAttempts >= al.config.IPMaxAttempts
}

// UnlockAccount manually unlocks an account (admin action)
func (al *AccountLockout) UnlockAccount(email string) {
	al.mu.Lock()
	defer al.mu.Unlock()

	if attempts, exists := al.attempts[email]; exists {
		attempts.LockedUntil = nil
		attempts.FailedCount = 0
	}
}

// GetAttemptInfo returns information about login attempts for an email
func (al *AccountLockout) GetAttemptInfo(email string) *LoginAttemptInfo {
	al.mu.RLock()
	defer al.mu.RUnlock()

	attempts, exists := al.attempts[email]
	if !exists {
		return nil
	}

	info := &LoginAttemptInfo{
		FailedCount: attempts.FailedCount,
		LastAttempt: attempts.LastAttempt,
		LockCount:   attempts.LockCount,
		IPCount:     len(attempts.IPAddresses),
	}

	if attempts.LockedUntil != nil {
		info.LockedUntil = attempts.LockedUntil
		info.IsLocked = time.Now().Before(*attempts.LockedUntil)
	}

	if attempts.LastSuccess != nil {
		info.LastSuccess = attempts.LastSuccess
	}

	return info
}

// cleanupLoop periodically removes stale entries
func (al *AccountLockout) cleanupLoop() {
	ticker := time.NewTicker(al.cleanupInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			al.cleanup()
		case <-al.stopCleanup:
			return
		}
	}
}

// cleanup removes old attempt records
func (al *AccountLockout) cleanup() {
	al.mu.Lock()
	defer al.mu.Unlock()

	now := time.Now()
	staleThreshold := 24 * time.Hour

	for email, attempts := range al.attempts {
		// Remove if no activity for 24 hours and not locked
		if now.Sub(attempts.LastAttempt) > staleThreshold {
			if attempts.LockedUntil == nil || now.After(*attempts.LockedUntil) {
				delete(al.attempts, email)
			}
		}
	}
}

// Stop stops the cleanup goroutine
func (al *AccountLockout) Stop() {
	close(al.stopCleanup)
}

// LockoutStatus represents the current lockout status
type LockoutStatus struct {
	Locked        bool           `json:"locked"`
	RemainingTime time.Duration  `json:"remaining_time,omitempty"`
	AttemptsLeft  int            `json:"attempts_left"`
	Message       string         `json:"message,omitempty"`
	LockoutExpiry *time.Time     `json:"lockout_expiry,omitempty"`
	JustLocked    bool           `json:"just_locked,omitempty"`
	LockCount     int            `json:"lock_count,omitempty"`
}

// LoginAttemptInfo provides information about login attempts
type LoginAttemptInfo struct {
	FailedCount int        `json:"failed_count"`
	LastAttempt time.Time  `json:"last_attempt"`
	LastSuccess *time.Time `json:"last_success,omitempty"`
	LockedUntil *time.Time `json:"locked_until,omitempty"`
	IsLocked    bool       `json:"is_locked"`
	LockCount   int        `json:"lock_count"`
	IPCount     int        `json:"ip_count"`
}
