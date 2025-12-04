package crypto

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"encoding/base64"
	"errors"
	"fmt"
	"io"
	"sync"
)

// EncryptionService provides AES-256-GCM encryption for sensitive data
type EncryptionService struct {
	key    []byte
	mu     sync.RWMutex
	gcm    cipher.AEAD
	keySet bool
}

var (
	// ErrKeyNotSet indicates the encryption key hasn't been set
	ErrKeyNotSet = errors.New("encryption key not set")
	// ErrInvalidKeyLength indicates the key is not 32 bytes (AES-256)
	ErrInvalidKeyLength = errors.New("encryption key must be exactly 32 bytes for AES-256")
	// ErrDecryptionFailed indicates decryption failed (wrong key or corrupted data)
	ErrDecryptionFailed = errors.New("decryption failed: invalid key or corrupted data")
	// ErrInvalidCiphertext indicates the ciphertext is too short or malformed
	ErrInvalidCiphertext = errors.New("invalid ciphertext: too short or malformed")
)

// Global encryption service instance
var globalService *EncryptionService
var once sync.Once

// GetEncryptionService returns the global encryption service singleton
func GetEncryptionService() *EncryptionService {
	once.Do(func() {
		globalService = &EncryptionService{}
	})
	return globalService
}

// NewEncryptionService creates a new encryption service with the given key
func NewEncryptionService(key []byte) (*EncryptionService, error) {
	service := &EncryptionService{}
	if err := service.SetKey(key); err != nil {
		return nil, err
	}
	return service, nil
}

// SetKey sets the encryption key (must be 32 bytes for AES-256)
func (s *EncryptionService) SetKey(key []byte) error {
	if len(key) != 32 {
		return ErrInvalidKeyLength
	}

	s.mu.Lock()
	defer s.mu.Unlock()

	// Create AES cipher block
	block, err := aes.NewCipher(key)
	if err != nil {
		return fmt.Errorf("failed to create cipher: %w", err)
	}

	// Create GCM mode
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return fmt.Errorf("failed to create GCM: %w", err)
	}

	s.key = make([]byte, 32)
	copy(s.key, key)
	s.gcm = gcm
	s.keySet = true

	return nil
}

// SetKeyFromString sets the encryption key from a base64-encoded string
func (s *EncryptionService) SetKeyFromString(keyStr string) error {
	key, err := base64.StdEncoding.DecodeString(keyStr)
	if err != nil {
		// Try using the string directly if it's exactly 32 bytes
		if len(keyStr) == 32 {
			return s.SetKey([]byte(keyStr))
		}
		return fmt.Errorf("invalid base64 key: %w", err)
	}
	return s.SetKey(key)
}

// IsKeySet returns whether an encryption key has been configured
func (s *EncryptionService) IsKeySet() bool {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.keySet
}

// Encrypt encrypts plaintext using AES-256-GCM
// Returns base64-encoded ciphertext (nonce prepended to encrypted data)
func (s *EncryptionService) Encrypt(plaintext string) (string, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	if !s.keySet {
		return "", ErrKeyNotSet
	}

	// Generate random nonce
	nonce := make([]byte, s.gcm.NonceSize())
	if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
		return "", fmt.Errorf("failed to generate nonce: %w", err)
	}

	// Encrypt with authentication
	ciphertext := s.gcm.Seal(nonce, nonce, []byte(plaintext), nil)

	// Return base64-encoded result
	return base64.StdEncoding.EncodeToString(ciphertext), nil
}

// Decrypt decrypts base64-encoded ciphertext using AES-256-GCM
func (s *EncryptionService) Decrypt(ciphertextBase64 string) (string, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	if !s.keySet {
		return "", ErrKeyNotSet
	}

	// Decode base64
	ciphertext, err := base64.StdEncoding.DecodeString(ciphertextBase64)
	if err != nil {
		return "", fmt.Errorf("invalid base64: %w", err)
	}

	// Validate minimum length (nonce + at least 1 byte of ciphertext + auth tag)
	nonceSize := s.gcm.NonceSize()
	if len(ciphertext) < nonceSize+s.gcm.Overhead() {
		return "", ErrInvalidCiphertext
	}

	// Extract nonce and actual ciphertext
	nonce, encryptedData := ciphertext[:nonceSize], ciphertext[nonceSize:]

	// Decrypt and verify authentication
	plaintext, err := s.gcm.Open(nil, nonce, encryptedData, nil)
	if err != nil {
		return "", ErrDecryptionFailed
	}

	return string(plaintext), nil
}

// EncryptBytes encrypts raw bytes
func (s *EncryptionService) EncryptBytes(data []byte) ([]byte, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	if !s.keySet {
		return nil, ErrKeyNotSet
	}

	nonce := make([]byte, s.gcm.NonceSize())
	if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
		return nil, fmt.Errorf("failed to generate nonce: %w", err)
	}

	return s.gcm.Seal(nonce, nonce, data, nil), nil
}

// DecryptBytes decrypts raw bytes
func (s *EncryptionService) DecryptBytes(ciphertext []byte) ([]byte, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	if !s.keySet {
		return nil, ErrKeyNotSet
	}

	nonceSize := s.gcm.NonceSize()
	if len(ciphertext) < nonceSize+s.gcm.Overhead() {
		return nil, ErrInvalidCiphertext
	}

	nonce, encryptedData := ciphertext[:nonceSize], ciphertext[nonceSize:]

	plaintext, err := s.gcm.Open(nil, nonce, encryptedData, nil)
	if err != nil {
		return nil, ErrDecryptionFailed
	}

	return plaintext, nil
}

// GenerateKey generates a cryptographically secure 32-byte key for AES-256
func GenerateKey() ([]byte, error) {
	key := make([]byte, 32)
	if _, err := io.ReadFull(rand.Reader, key); err != nil {
		return nil, fmt.Errorf("failed to generate key: %w", err)
	}
	return key, nil
}

// GenerateKeyString generates a base64-encoded encryption key
func GenerateKeyString() (string, error) {
	key, err := GenerateKey()
	if err != nil {
		return "", err
	}
	return base64.StdEncoding.EncodeToString(key), nil
}

// MaskPassword returns a masked version of a password for logging
func MaskPassword(password string) string {
	if len(password) == 0 {
		return ""
	}
	if len(password) <= 4 {
		return "****"
	}
	return password[:2] + "****" + password[len(password)-2:]
}

// IsEncrypted attempts to detect if a string is encrypted (base64 + minimum length)
func IsEncrypted(value string) bool {
	// Encrypted values are base64-encoded and have nonce + ciphertext + auth tag
	// Minimum length: 12 (nonce) + 16 (auth tag) = 28 bytes = ~38 base64 chars
	if len(value) < 38 {
		return false
	}

	// Try to decode as base64
	decoded, err := base64.StdEncoding.DecodeString(value)
	if err != nil {
		return false
	}

	// Check if decoded length is reasonable for encrypted data
	// GCM nonce (12) + at least 1 byte + auth tag (16) = 29 minimum
	return len(decoded) >= 29
}
