package security

import (
	"fmt"
	"net"
	"strings"
)

// IPValidator validates IP addresses and hostnames for SSRF protection
type IPValidator struct {
	blockPrivate    bool
	blockLoopback   bool
	blockLinkLocal  bool
	blockMulticast  bool
	allowedCIDRs    []*net.IPNet
	blockedCIDRs    []*net.IPNet
	blockedHosts    map[string]bool
	isProduction    bool
}

// IPValidatorConfig configures the IP validator
type IPValidatorConfig struct {
	BlockPrivateIPs   bool     // Block 10.x, 172.16-31.x, 192.168.x
	BlockLoopback     bool     // Block 127.x, ::1
	BlockLinkLocal    bool     // Block 169.254.x, fe80::
	BlockMulticast    bool     // Block 224.x-239.x
	AllowedCIDRs      []string // Explicit allow list
	BlockedCIDRs      []string // Explicit block list
	BlockedHostnames  []string // Specific hostnames to block
	IsProduction      bool     // Production mode (stricter)
}

// DefaultIPValidatorConfig returns production-safe defaults
func DefaultIPValidatorConfig(isProduction bool) IPValidatorConfig {
	config := IPValidatorConfig{
		BlockPrivateIPs:  isProduction,
		BlockLoopback:    isProduction,
		BlockLinkLocal:   true,
		BlockMulticast:   true,
		IsProduction:     isProduction,
		BlockedHostnames: []string{
			"metadata.google.internal",      // GCP metadata
			"169.254.169.254",               // AWS/GCP metadata
			"metadata.google.com",
			"kubernetes.default",
			"kubernetes.default.svc",
		},
	}

	if isProduction {
		// In production, also block cloud metadata endpoints
		config.BlockedCIDRs = []string{
			"169.254.169.254/32", // Cloud metadata
		}
	}

	return config
}

// NewIPValidator creates a new IP validator
func NewIPValidator(config IPValidatorConfig) (*IPValidator, error) {
	v := &IPValidator{
		blockPrivate:   config.BlockPrivateIPs,
		blockLoopback:  config.BlockLoopback,
		blockLinkLocal: config.BlockLinkLocal,
		blockMulticast: config.BlockMulticast,
		isProduction:   config.IsProduction,
		blockedHosts:   make(map[string]bool),
	}

	// Parse allowed CIDRs
	for _, cidr := range config.AllowedCIDRs {
		_, ipNet, err := net.ParseCIDR(cidr)
		if err != nil {
			return nil, fmt.Errorf("invalid allowed CIDR %s: %w", cidr, err)
		}
		v.allowedCIDRs = append(v.allowedCIDRs, ipNet)
	}

	// Parse blocked CIDRs
	for _, cidr := range config.BlockedCIDRs {
		_, ipNet, err := net.ParseCIDR(cidr)
		if err != nil {
			return nil, fmt.Errorf("invalid blocked CIDR %s: %w", cidr, err)
		}
		v.blockedCIDRs = append(v.blockedCIDRs, ipNet)
	}

	// Add blocked hostnames
	for _, host := range config.BlockedHostnames {
		v.blockedHosts[strings.ToLower(host)] = true
	}

	return v, nil
}

// ValidateHost validates a hostname or IP address
func (v *IPValidator) ValidateHost(host string) error {
	// Check blocked hostnames first
	if v.blockedHosts[strings.ToLower(host)] {
		return fmt.Errorf("hostname '%s' is blocked", host)
	}

	// Check common blocked patterns
	lowerHost := strings.ToLower(host)
	blockedPatterns := []string{
		"metadata",
		"internal",
		".local",
		"localhost",
	}

	if v.isProduction {
		for _, pattern := range blockedPatterns {
			if strings.Contains(lowerHost, pattern) {
				return fmt.Errorf("hostname '%s' contains blocked pattern '%s'", host, pattern)
			}
		}
	}

	// Try to parse as IP
	ip := net.ParseIP(host)
	if ip != nil {
		return v.ValidateIP(ip)
	}

	// It's a hostname - try to resolve it
	ips, err := net.LookupIP(host)
	if err != nil {
		// Can't resolve - might be okay, let connection fail naturally
		return nil
	}

	// Validate all resolved IPs
	for _, resolvedIP := range ips {
		if err := v.ValidateIP(resolvedIP); err != nil {
			return fmt.Errorf("hostname '%s' resolves to blocked IP: %w", host, err)
		}
	}

	return nil
}

// ValidateIP validates an IP address
func (v *IPValidator) ValidateIP(ip net.IP) error {
	// Check explicit allow list first
	for _, allowed := range v.allowedCIDRs {
		if allowed.Contains(ip) {
			return nil // Explicitly allowed
		}
	}

	// Check explicit block list
	for _, blocked := range v.blockedCIDRs {
		if blocked.Contains(ip) {
			return fmt.Errorf("IP %s is in blocked range", ip.String())
		}
	}

	// Check loopback (127.x.x.x, ::1)
	if v.blockLoopback && ip.IsLoopback() {
		return fmt.Errorf("loopback addresses are not allowed")
	}

	// Check private IPs
	if v.blockPrivate && ip.IsPrivate() {
		return fmt.Errorf("private IP addresses are not allowed")
	}

	// Check link-local (169.254.x.x, fe80::)
	if v.blockLinkLocal && ip.IsLinkLocalUnicast() {
		return fmt.Errorf("link-local addresses are not allowed")
	}

	// Check multicast
	if v.blockMulticast && ip.IsMulticast() {
		return fmt.Errorf("multicast addresses are not allowed")
	}

	// Check for IPv6 special addresses
	if ip.To4() == nil {
		// IPv6
		if ip.IsLinkLocalMulticast() {
			return fmt.Errorf("link-local multicast addresses are not allowed")
		}
		if ip.IsInterfaceLocalMulticast() {
			return fmt.Errorf("interface-local multicast addresses are not allowed")
		}
	}

	// Check unspecified (0.0.0.0, ::)
	if ip.IsUnspecified() {
		return fmt.Errorf("unspecified addresses are not allowed")
	}

	return nil
}

// IsPrivateIP checks if an IP is private (for logging purposes)
func IsPrivateIP(ip net.IP) bool {
	if ip == nil {
		return false
	}
	return ip.IsPrivate() || ip.IsLoopback() || ip.IsLinkLocalUnicast()
}

// ValidationResult contains the result of IP validation
type IPValidationResult struct {
	Valid       bool   `json:"valid"`
	Host        string `json:"host"`
	ResolvedIPs []string `json:"resolved_ips,omitempty"`
	Error       string `json:"error,omitempty"`
	Warnings    []string `json:"warnings,omitempty"`
}

// ValidateHostDetailed returns detailed validation result
func (v *IPValidator) ValidateHostDetailed(host string) IPValidationResult {
	result := IPValidationResult{
		Host:  host,
		Valid: true,
	}

	// Check blocked hostnames
	if v.blockedHosts[strings.ToLower(host)] {
		result.Valid = false
		result.Error = fmt.Sprintf("hostname '%s' is blocked", host)
		return result
	}

	// Try to parse as IP
	ip := net.ParseIP(host)
	if ip != nil {
		if err := v.ValidateIP(ip); err != nil {
			result.Valid = false
			result.Error = err.Error()
		}
		result.ResolvedIPs = []string{ip.String()}
		return result
	}

	// Resolve hostname
	ips, err := net.LookupIP(host)
	if err != nil {
		result.Warnings = append(result.Warnings, "hostname could not be resolved")
		return result
	}

	for _, resolvedIP := range ips {
		result.ResolvedIPs = append(result.ResolvedIPs, resolvedIP.String())
		if err := v.ValidateIP(resolvedIP); err != nil {
			result.Valid = false
			result.Error = fmt.Sprintf("resolves to blocked IP %s: %s", resolvedIP.String(), err.Error())
			return result
		}
	}

	return result
}

// GetIPType returns the type of IP address for logging
func GetIPType(ip net.IP) string {
	if ip == nil {
		return "invalid"
	}
	if ip.IsLoopback() {
		return "loopback"
	}
	if ip.IsPrivate() {
		return "private"
	}
	if ip.IsLinkLocalUnicast() {
		return "link-local"
	}
	if ip.IsMulticast() {
		return "multicast"
	}
	if ip.IsGlobalUnicast() {
		return "public"
	}
	return "unknown"
}
