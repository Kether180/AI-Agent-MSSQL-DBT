package security

import (
	"fmt"

	"github.com/gin-gonic/gin"
)

// SecurityHeadersConfig defines configuration for security headers
type SecurityHeadersConfig struct {
	// Content Security Policy
	CSPEnabled      bool
	CSPDirectives   string
	CSPReportOnly   bool

	// Frame options
	XFrameOptions   string // DENY, SAMEORIGIN, or ALLOW-FROM uri

	// XSS Protection (legacy but still useful)
	XSSProtection   string

	// Content Type Options
	ContentTypeOptions string

	// Referrer Policy
	ReferrerPolicy  string

	// Permissions Policy (formerly Feature-Policy)
	PermissionsPolicy string

	// HSTS (HTTP Strict Transport Security)
	HSTSEnabled     bool
	HSTSMaxAge      int
	HSTSIncludeSub  bool
	HSTSPreload     bool

	// Cache Control for sensitive endpoints
	NoCacheEnabled  bool
}

// DefaultSecurityHeadersConfig returns production-ready defaults
func DefaultSecurityHeadersConfig() SecurityHeadersConfig {
	return SecurityHeadersConfig{
		// CSP - restrictive by default
		CSPEnabled: true,
		CSPDirectives: "default-src 'self'; " +
			"script-src 'self' 'unsafe-inline' 'unsafe-eval'; " +
			"style-src 'self' 'unsafe-inline'; " +
			"img-src 'self' data: https:; " +
			"font-src 'self' data:; " +
			"connect-src 'self' https:; " +
			"frame-ancestors 'none'; " +
			"base-uri 'self'; " +
			"form-action 'self';",
		CSPReportOnly: false,

		// Prevent clickjacking
		XFrameOptions: "DENY",

		// XSS protection
		XSSProtection: "1; mode=block",

		// Prevent MIME type sniffing
		ContentTypeOptions: "nosniff",

		// Referrer policy - don't leak URLs
		ReferrerPolicy: "strict-origin-when-cross-origin",

		// Disable dangerous features
		PermissionsPolicy: "geolocation=(), microphone=(), camera=(), payment=(), usb=()",

		// HSTS - force HTTPS
		HSTSEnabled:    true,
		HSTSMaxAge:     31536000, // 1 year
		HSTSIncludeSub: true,
		HSTSPreload:    false, // Enable after testing

		// No cache for API responses
		NoCacheEnabled: true,
	}
}

// SecurityHeadersMiddleware returns a Gin middleware that adds security headers
func SecurityHeadersMiddleware(config SecurityHeadersConfig) gin.HandlerFunc {
	return func(c *gin.Context) {
		// Content Security Policy
		if config.CSPEnabled && config.CSPDirectives != "" {
			if config.CSPReportOnly {
				c.Header("Content-Security-Policy-Report-Only", config.CSPDirectives)
			} else {
				c.Header("Content-Security-Policy", config.CSPDirectives)
			}
		}

		// X-Frame-Options - prevent clickjacking
		if config.XFrameOptions != "" {
			c.Header("X-Frame-Options", config.XFrameOptions)
		}

		// X-XSS-Protection
		if config.XSSProtection != "" {
			c.Header("X-XSS-Protection", config.XSSProtection)
		}

		// X-Content-Type-Options - prevent MIME sniffing
		if config.ContentTypeOptions != "" {
			c.Header("X-Content-Type-Options", config.ContentTypeOptions)
		}

		// Referrer-Policy
		if config.ReferrerPolicy != "" {
			c.Header("Referrer-Policy", config.ReferrerPolicy)
		}

		// Permissions-Policy
		if config.PermissionsPolicy != "" {
			c.Header("Permissions-Policy", config.PermissionsPolicy)
		}

		// HSTS - only on HTTPS
		if config.HSTSEnabled {
			hstsValue := fmt.Sprintf("max-age=%d", config.HSTSMaxAge)
			if config.HSTSIncludeSub {
				hstsValue += "; includeSubDomains"
			}
			if config.HSTSPreload {
				hstsValue += "; preload"
			}
			// Only set on HTTPS (check X-Forwarded-Proto for reverse proxy)
			if c.Request.TLS != nil || c.GetHeader("X-Forwarded-Proto") == "https" {
				c.Header("Strict-Transport-Security", hstsValue)
			}
		}

		// Cache-Control for API endpoints
		if config.NoCacheEnabled {
			c.Header("Cache-Control", "no-store, no-cache, must-revalidate, private")
			c.Header("Pragma", "no-cache")
			c.Header("Expires", "0")
		}

		// Additional security headers
		c.Header("X-Permitted-Cross-Domain-Policies", "none")
		c.Header("X-Download-Options", "noopen")

		c.Next()
	}
}

// StrictSecurityHeadersMiddleware returns extra-strict headers for sensitive endpoints
func StrictSecurityHeadersMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		// Extra strict CSP for auth endpoints
		c.Header("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none';")
		c.Header("X-Frame-Options", "DENY")
		c.Header("X-Content-Type-Options", "nosniff")
		c.Header("Cache-Control", "no-store")
		c.Header("Pragma", "no-cache")

		c.Next()
	}
}
