package security

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"path/filepath"
	"strings"
)

// FileUploadConfig configures file upload security
type FileUploadConfig struct {
	MaxFileSize        int64    // Maximum file size in bytes
	AllowedExtensions  []string // Allowed file extensions
	AllowedMIMETypes   []string // Allowed MIME types
	ScanForMalware     bool     // Enable malware scanning (placeholder)
	ValidateMagicBytes bool     // Validate file magic bytes
	BlockExecutables   bool     // Block executable files
	SanitizeFilenames  bool     // Sanitize uploaded filenames
}

// DefaultFileUploadConfig returns secure defaults
func DefaultFileUploadConfig() FileUploadConfig {
	return FileUploadConfig{
		MaxFileSize: 10 * 1024 * 1024, // 10MB default
		AllowedExtensions: []string{
			".sql", ".csv", ".json", ".xml", ".yaml", ".yml",
			".txt", ".md", ".pdf", ".xlsx", ".xls",
		},
		AllowedMIMETypes: []string{
			"text/plain",
			"text/csv",
			"application/json",
			"application/xml",
			"text/xml",
			"application/x-yaml",
			"text/yaml",
			"application/pdf",
			"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
			"application/vnd.ms-excel",
			"application/sql",
			"text/x-sql",
		},
		ScanForMalware:     false, // Requires external scanner
		ValidateMagicBytes: true,
		BlockExecutables:   true,
		SanitizeFilenames:  true,
	}
}

// FileUploadValidator validates uploaded files
type FileUploadValidator struct {
	config FileUploadConfig
}

// NewFileUploadValidator creates a new file upload validator
func NewFileUploadValidator(config FileUploadConfig) *FileUploadValidator {
	return &FileUploadValidator{config: config}
}

// FileValidationResult contains the validation result
type FileValidationResult struct {
	Valid           bool     `json:"valid"`
	Filename        string   `json:"filename"`
	SanitizedName   string   `json:"sanitized_name,omitempty"`
	Size            int64    `json:"size"`
	MIMEType        string   `json:"mime_type"`
	Extension       string   `json:"extension"`
	SHA256          string   `json:"sha256,omitempty"`
	Errors          []string `json:"errors,omitempty"`
	Warnings        []string `json:"warnings,omitempty"`
}

// ValidateFile validates an uploaded file
func (v *FileUploadValidator) ValidateFile(file *multipart.FileHeader) (*FileValidationResult, error) {
	result := &FileValidationResult{
		Valid:    true,
		Filename: file.Filename,
		Size:     file.Size,
	}

	// Get extension
	result.Extension = strings.ToLower(filepath.Ext(file.Filename))

	// Sanitize filename
	if v.config.SanitizeFilenames {
		result.SanitizedName = v.sanitizeFilename(file.Filename)
	}

	// Check file size
	if file.Size > v.config.MaxFileSize {
		result.Valid = false
		result.Errors = append(result.Errors,
			fmt.Sprintf("File size (%d bytes) exceeds maximum allowed (%d bytes)",
				file.Size, v.config.MaxFileSize))
	}

	// Check extension
	if !v.isExtensionAllowed(result.Extension) {
		result.Valid = false
		result.Errors = append(result.Errors,
			fmt.Sprintf("File extension '%s' is not allowed", result.Extension))
	}

	// Open file for content inspection
	f, err := file.Open()
	if err != nil {
		return result, fmt.Errorf("failed to open file: %w", err)
	}
	defer f.Close()

	// Read file content for inspection
	content := make([]byte, 512) // Read first 512 bytes for magic number detection
	n, _ := f.Read(content)
	content = content[:n]

	// Detect MIME type from content
	result.MIMEType = http.DetectContentType(content)

	// Check MIME type
	if !v.isMIMETypeAllowed(result.MIMEType) {
		// Allow text/plain as fallback for many text-based formats
		if result.MIMEType != "text/plain" || !v.isTextExtension(result.Extension) {
			result.Valid = false
			result.Errors = append(result.Errors,
				fmt.Sprintf("MIME type '%s' is not allowed", result.MIMEType))
		}
	}

	// Check for executable content
	if v.config.BlockExecutables {
		if v.isExecutableContent(content) {
			result.Valid = false
			result.Errors = append(result.Errors, "File appears to contain executable content")
		}
	}

	// Validate magic bytes
	if v.config.ValidateMagicBytes {
		if !v.validateMagicBytes(content, result.Extension) {
			result.Warnings = append(result.Warnings,
				"File content does not match expected format for extension")
		}
	}

	// Calculate SHA256 hash (reset file position first)
	f.Seek(0, 0)
	hash := sha256.New()
	if _, err := io.Copy(hash, f); err == nil {
		result.SHA256 = hex.EncodeToString(hash.Sum(nil))
	}

	// Check for path traversal in filename
	if strings.Contains(file.Filename, "..") ||
		strings.Contains(file.Filename, "/") ||
		strings.Contains(file.Filename, "\\") {
		result.Valid = false
		result.Errors = append(result.Errors, "Filename contains invalid characters")
	}

	return result, nil
}

// sanitizeFilename removes potentially dangerous characters from filename
func (v *FileUploadValidator) sanitizeFilename(filename string) string {
	// Get base name (remove any path components)
	filename = filepath.Base(filename)

	// Replace dangerous characters
	replacer := strings.NewReplacer(
		"../", "",
		"..\\", "",
		"/", "_",
		"\\", "_",
		"<", "",
		">", "",
		":", "",
		"\"", "",
		"|", "",
		"?", "",
		"*", "",
		"\x00", "",
	)
	filename = replacer.Replace(filename)

	// Limit filename length
	if len(filename) > 255 {
		ext := filepath.Ext(filename)
		name := filename[:255-len(ext)]
		filename = name + ext
	}

	// Ensure not empty
	if filename == "" || filename == "." {
		filename = "unnamed_file"
	}

	return filename
}

// isExtensionAllowed checks if the extension is in the allowed list
func (v *FileUploadValidator) isExtensionAllowed(ext string) bool {
	ext = strings.ToLower(ext)
	for _, allowed := range v.config.AllowedExtensions {
		if strings.ToLower(allowed) == ext {
			return true
		}
	}
	return false
}

// isMIMETypeAllowed checks if the MIME type is in the allowed list
func (v *FileUploadValidator) isMIMETypeAllowed(mimeType string) bool {
	// Get base MIME type (without charset, etc.)
	baseMIME := strings.Split(mimeType, ";")[0]
	baseMIME = strings.TrimSpace(baseMIME)

	for _, allowed := range v.config.AllowedMIMETypes {
		if allowed == baseMIME {
			return true
		}
	}
	return false
}

// isTextExtension checks if the extension is a text-based format
func (v *FileUploadValidator) isTextExtension(ext string) bool {
	textExtensions := []string{".sql", ".csv", ".json", ".xml", ".yaml", ".yml", ".txt", ".md"}
	ext = strings.ToLower(ext)
	for _, te := range textExtensions {
		if te == ext {
			return true
		}
	}
	return false
}

// isExecutableContent checks if content appears to be executable
func (v *FileUploadValidator) isExecutableContent(content []byte) bool {
	if len(content) < 2 {
		return false
	}

	// Check for common executable signatures
	signatures := [][]byte{
		{0x4D, 0x5A},             // MZ (Windows EXE/DLL)
		{0x7F, 0x45, 0x4C, 0x46}, // ELF (Linux executable)
		{0xCA, 0xFE, 0xBA, 0xBE}, // Mach-O (macOS)
		{0x50, 0x4B, 0x03, 0x04}, // ZIP (could be JAR)
		{0x23, 0x21},             // Shebang (#!)
	}

	for _, sig := range signatures {
		if len(content) >= len(sig) && bytes.HasPrefix(content, sig) {
			// Allow ZIP for XLSX files
			if bytes.HasPrefix(content, []byte{0x50, 0x4B, 0x03, 0x04}) {
				return false // XLSX files are ZIP-based
			}
			return true
		}
	}

	return false
}

// validateMagicBytes validates that file content matches expected format
func (v *FileUploadValidator) validateMagicBytes(content []byte, ext string) bool {
	if len(content) < 4 {
		return true // Not enough content to validate
	}

	switch strings.ToLower(ext) {
	case ".pdf":
		return bytes.HasPrefix(content, []byte("%PDF"))
	case ".xlsx":
		return bytes.HasPrefix(content, []byte{0x50, 0x4B, 0x03, 0x04}) // ZIP signature
	case ".xls":
		return bytes.HasPrefix(content, []byte{0xD0, 0xCF, 0x11, 0xE0}) // OLE signature
	case ".json":
		// JSON should start with { or [
		trimmed := bytes.TrimSpace(content)
		return len(trimmed) > 0 && (trimmed[0] == '{' || trimmed[0] == '[')
	case ".xml":
		trimmed := bytes.TrimSpace(content)
		return bytes.HasPrefix(trimmed, []byte("<?xml")) || bytes.HasPrefix(trimmed, []byte("<"))
	case ".sql", ".csv", ".txt", ".md", ".yaml", ".yml":
		// Text files - just ensure no binary content in first bytes
		for _, b := range content[:min(100, len(content))] {
			if b < 0x09 || (b > 0x0D && b < 0x20 && b != 0x1B) {
				if b != 0x00 { // Allow null at end
					return false
				}
			}
		}
		return true
	default:
		return true
	}
}

// GetFileUploadValidator returns a default file upload validator
func GetFileUploadValidator() *FileUploadValidator {
	return NewFileUploadValidator(DefaultFileUploadConfig())
}

// QuarantineFile quarantines a suspicious file (placeholder for actual implementation)
func QuarantineFile(filepath string, reason string) error {
	// In a real implementation, this would move the file to a quarantine directory
	// and log the event for security review
	return nil
}

// min returns the minimum of two integers
func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
