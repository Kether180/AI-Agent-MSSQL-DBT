package aiservice

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

// Client handles communication with the AI service
type Client struct {
	baseURL    string
	httpClient *http.Client
}

// MigrationRequest represents the request to start a migration
type MigrationRequest struct {
	MigrationID      int64                  `json:"migration_id"`
	SourceConnection map[string]interface{} `json:"source_connection"`
	TargetProject    string                 `json:"target_project"`
	Tables           []string               `json:"tables,omitempty"`
	IncludeViews     bool                   `json:"include_views"`
}

// MigrationResponse represents the response from starting a migration
type MigrationResponse struct {
	Message     string `json:"message"`
	MigrationID int64  `json:"migration_id"`
}

// MigrationStatus represents the status of a migration
type MigrationStatus struct {
	MigrationID     int64   `json:"migration_id"`
	Status          string  `json:"status"`
	Progress        int     `json:"progress"`
	CurrentPhase    string  `json:"current_phase,omitempty"`
	CurrentModel    string  `json:"current_model,omitempty"`
	Error           string  `json:"error,omitempty"`
	CompletedModels int     `json:"completed_models"`
	TotalModels     int     `json:"total_models"`
}

var client *Client

// Init initializes the AI service client
func Init(baseURL string) {
	client = &Client{
		baseURL: baseURL,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// GetClient returns the initialized client
func GetClient() *Client {
	return client
}

// StartMigration triggers a new migration in the AI service
func (c *Client) StartMigration(req MigrationRequest) (*MigrationResponse, error) {
	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	resp, err := c.httpClient.Post(
		c.baseURL+"/migrations/start",
		"application/json",
		bytes.NewBuffer(body),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to call AI service: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		var errResp struct {
			Detail string `json:"detail"`
		}
		json.NewDecoder(resp.Body).Decode(&errResp)
		return nil, fmt.Errorf("AI service error: %s (status %d)", errResp.Detail, resp.StatusCode)
	}

	var result MigrationResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// GetMigrationStatus gets the current status of a migration
func (c *Client) GetMigrationStatus(migrationID int64) (*MigrationStatus, error) {
	resp, err := c.httpClient.Get(
		fmt.Sprintf("%s/migrations/%d/status", c.baseURL, migrationID),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to call AI service: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return nil, fmt.Errorf("migration not found in AI service")
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("AI service error (status %d)", resp.StatusCode)
	}

	var result MigrationStatus
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// StopMigration stops a running migration
func (c *Client) StopMigration(migrationID int64) error {
	resp, err := c.httpClient.Post(
		fmt.Sprintf("%s/migrations/%d/stop", c.baseURL, migrationID),
		"application/json",
		nil,
	)
	if err != nil {
		return fmt.Errorf("failed to call AI service: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("AI service error (status %d)", resp.StatusCode)
	}

	return nil
}

// HealthCheck checks if the AI service is healthy
func (c *Client) HealthCheck() error {
	resp, err := c.httpClient.Get(c.baseURL + "/health")
	if err != nil {
		return fmt.Errorf("AI service unreachable: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("AI service unhealthy (status %d)", resp.StatusCode)
	}

	return nil
}

// DBTFile represents a file in the generated dbt project
type DBTFile struct {
	Path string `json:"path"`
	Name string `json:"name"`
	Size int64  `json:"size"`
	Type string `json:"type"`
}

// DBTFilesResponse represents the list of files response
type DBTFilesResponse struct {
	MigrationID int64     `json:"migration_id"`
	ProjectPath string    `json:"project_path"`
	Files       []DBTFile `json:"files"`
}

// DBTFileContent represents file content response
type DBTFileContent struct {
	Path    string `json:"path"`
	Content string `json:"content"`
	Size    int    `json:"size"`
}

// GetMigrationFiles gets the list of generated dbt files
func (c *Client) GetMigrationFiles(migrationID int64) (*DBTFilesResponse, error) {
	resp, err := c.httpClient.Get(
		fmt.Sprintf("%s/migrations/%d/files", c.baseURL, migrationID),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to call AI service: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return nil, fmt.Errorf("migration not found in AI service")
	}

	if resp.StatusCode == http.StatusBadRequest {
		var errResp struct {
			Detail string `json:"detail"`
		}
		json.NewDecoder(resp.Body).Decode(&errResp)
		return nil, fmt.Errorf(errResp.Detail)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("AI service error (status %d)", resp.StatusCode)
	}

	var result DBTFilesResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// GetMigrationFileContent gets the content of a specific dbt file
func (c *Client) GetMigrationFileContent(migrationID int64, filePath string) (*DBTFileContent, error) {
	resp, err := c.httpClient.Get(
		fmt.Sprintf("%s/migrations/%d/files/%s", c.baseURL, migrationID, filePath),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to call AI service: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return nil, fmt.Errorf("file not found")
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("AI service error (status %d)", resp.StatusCode)
	}

	var result DBTFileContent
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// GetMigrationDownloadURL returns the URL to download the dbt project
func (c *Client) GetMigrationDownloadURL(migrationID int64) string {
	return fmt.Sprintf("%s/migrations/%d/download", c.baseURL, migrationID)
}
