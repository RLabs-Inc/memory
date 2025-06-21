package memory

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/tidwall/gjson"
)

// MemoryClient handles communication with the Python memory engine
type MemoryClient struct {
	baseURL    string
	httpClient *http.Client
}

// ConversationContext represents memory context for a session
type ConversationContext struct {
	SessionID    string             `json:"session_id"`
	MessageCount int                `json:"message_count"`
	ContextText  string             `json:"context_text"`
	HasMemories  bool               `json:"has_memories"`
	Patterns     map[string]float64 `json:"patterns"`
}

// ProcessMessageRequest for sending exchanges to memory engine
type ProcessMessageRequest struct {
	SessionID     string                 `json:"session_id"`
	UserMessage   string                 `json:"user_message"`
	ClaudeResponse string                `json:"claude_response"`
	Metadata      map[string]interface{} `json:"metadata,omitempty"`
}

// GetContextRequest for retrieving context
type GetContextRequest struct {
	SessionID      string `json:"session_id"`
	CurrentMessage string `json:"current_message"`
}

// CheckpointRequest for triggering memory curation
type CheckpointRequest struct {
	SessionID string `json:"session_id"`
	Trigger   string `json:"trigger"`
	ClaudeSessionID string `json:"claude_session_id,omitempty"`
}

// CheckpointResponse from memory curation
type CheckpointResponse struct {
	Success         bool   `json:"success"`
	Trigger         string `json:"trigger"`
	MemoriesCurated int    `json:"memories_curated"`
	Message         string `json:"message"`
}

// StatsResponse from memory engine
type StatsResponse struct {
	CuratorEnabled   bool   `json:"curator_enabled"`
	CuratorAvailable bool   `json:"curator_available"`
	TotalSessions    int    `json:"total_sessions"`
	TotalExchanges   int    `json:"total_exchanges"`
	CuratedMemories  int    `json:"curated_memories"`
	MemorySize       string `json:"memory_size"`
}

// NewMemoryClient creates a new memory client
func NewMemoryClient(baseURL string) *MemoryClient {
	return &MemoryClient{
		baseURL: baseURL,
		httpClient: &http.Client{
			Timeout: 120 * time.Second, // Increased for curator operations
		},
	}
}

// NewDefaultMemoryClient creates a memory client with default settings
func NewDefaultMemoryClient() *MemoryClient {
	return NewMemoryClient("http://127.0.0.1:8765")
}

// HealthCheck verifies the memory engine is running
func (mc *MemoryClient) HealthCheck() error {
	resp, err := mc.httpClient.Get(mc.baseURL + "/health")
	if err != nil {
		return fmt.Errorf("memory engine not reachable: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("memory engine unhealthy: status %d", resp.StatusCode)
	}

	return nil
}

// GetContext retrieves memory context for a new message
func (mc *MemoryClient) GetContext(sessionID, currentMessage string) (*ConversationContext, error) {
	request := GetContextRequest{
		SessionID:      sessionID,
		CurrentMessage: currentMessage,
	}

	respBody, err := mc.makeRequest("POST", "/memory/context", request)
	if err != nil {
		return nil, fmt.Errorf("failed to get context: %w", err)
	}

	var context ConversationContext
	if err := json.Unmarshal(respBody, &context); err != nil {
		return nil, fmt.Errorf("failed to parse context response: %w", err)
	}

	return &context, nil
}

// ProcessMessage sends a conversation exchange to the memory engine
func (mc *MemoryClient) ProcessMessage(sessionID, userMessage, claudeResponse string, metadata map[string]interface{}) (*ConversationContext, error) {
	request := ProcessMessageRequest{
		SessionID:      sessionID,
		UserMessage:    userMessage,
		ClaudeResponse: claudeResponse,
		Metadata:       metadata,
	}

	respBody, err := mc.makeRequest("POST", "/memory/process", request)
	if err != nil {
		return nil, fmt.Errorf("failed to process message: %w", err)
	}

	// Parse the nested response structure
	contextData := gjson.GetBytes(respBody, "context")
	
	var context ConversationContext
	if err := json.Unmarshal([]byte(contextData.String()), &context); err != nil {
		return nil, fmt.Errorf("failed to parse process response: %w", err)
	}

	return &context, nil
}

// CheckpointSession triggers memory curation at key points
func (mc *MemoryClient) CheckpointSession(sessionID, trigger string, claudeSessionID string) (*CheckpointResponse, error) {
	request := CheckpointRequest{
		SessionID: sessionID,
		Trigger:   trigger,
		ClaudeSessionID: claudeSessionID,
	}

	respBody, err := mc.makeRequest("POST", "/memory/checkpoint", request)
	if err != nil {
		return nil, fmt.Errorf("failed to checkpoint session: %w", err)
	}

	var response CheckpointResponse
	if err := json.Unmarshal(respBody, &response); err != nil {
		return nil, fmt.Errorf("failed to parse checkpoint response: %w", err)
	}

	return &response, nil
}

// GetStats retrieves memory engine statistics
func (mc *MemoryClient) GetStats() (*StatsResponse, error) {
	respBody, err := mc.makeRequest("GET", "/memory/stats", nil)
	if err != nil {
		return nil, fmt.Errorf("failed to get stats: %w", err)
	}

	var stats StatsResponse
	if err := json.Unmarshal(respBody, &stats); err != nil {
		return nil, fmt.Errorf("failed to parse stats response: %w", err)
	}

	return &stats, nil
}

// makeRequest makes an HTTP request to the memory engine
func (mc *MemoryClient) makeRequest(method, endpoint string, payload interface{}) ([]byte, error) {
	var reqBody []byte
	var err error

	if payload != nil {
		reqBody, err = json.Marshal(payload)
		if err != nil {
			return nil, fmt.Errorf("failed to marshal request: %w", err)
		}
	}

	req, err := http.NewRequest(method, mc.baseURL+endpoint, bytes.NewBuffer(reqBody))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := mc.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	buf := new(bytes.Buffer)
	_, err = buf.ReadFrom(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("memory engine error: status %d, body: %s", resp.StatusCode, buf.String())
	}

	return buf.Bytes(), nil
}