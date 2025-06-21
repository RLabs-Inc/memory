package memory

import (
	"crypto/rand"
	"fmt"
	"time"
)

// SessionManager handles session lifecycle and memory integration
type SessionManager struct {
	client       *MemoryClient
	currentSession *Session
}

// Session represents an active conversation session
type Session struct {
	ID        string                 `json:"id"`
	CreatedAt time.Time              `json:"created_at"`
	Metadata  map[string]interface{} `json:"metadata"`
}

// NewSessionManager creates a new session manager
func NewSessionManager(client *MemoryClient) *SessionManager {
	return &SessionManager{
		client: client,
	}
}

// StartSession begins a new conversation session
func (sm *SessionManager) StartSession(metadata map[string]interface{}) (*Session, error) {
	sessionID, err := generateSessionID()
	if err != nil {
		return nil, fmt.Errorf("failed to generate session ID: %w", err)
	}

	if metadata == nil {
		metadata = make(map[string]interface{})
	}

	session := &Session{
		ID:        sessionID,
		CreatedAt: time.Now(),
		Metadata:  metadata,
	}

	sm.currentSession = session
	return session, nil
}

// GetCurrentSession returns the current active session
func (sm *SessionManager) GetCurrentSession() *Session {
	return sm.currentSession
}

// ProcessExchange handles a complete conversation exchange with memory
func (sm *SessionManager) ProcessExchange(userMessage, claudeResponse string) (*ConversationContext, error) {
	if sm.currentSession == nil {
		return nil, fmt.Errorf("no active session")
	}

	// Process the exchange through memory engine
	context, err := sm.client.ProcessMessage(
		sm.currentSession.ID,
		userMessage,
		claudeResponse,
		sm.currentSession.Metadata,
	)
	if err != nil {
		return nil, fmt.Errorf("failed to process exchange: %w", err)
	}

	return context, nil
}

// GetContextForMessage retrieves memory context before sending to Claude
func (sm *SessionManager) GetContextForMessage(userMessage string) (*ConversationContext, error) {
	if sm.currentSession == nil {
		// Start a new session if none exists
		session, err := sm.StartSession(nil)
		if err != nil {
			return nil, fmt.Errorf("failed to start session: %w", err)
		}
		sm.currentSession = session
	}

	context, err := sm.client.GetContext(sm.currentSession.ID, userMessage)
	if err != nil {
		return nil, fmt.Errorf("failed to get context: %w", err)
	}

	return context, nil
}

// generateSessionID creates a unique session identifier
func generateSessionID() (string, error) {
	bytes := make([]byte, 16)
	_, err := rand.Read(bytes)
	if err != nil {
		return "", err
	}

	// Format as hex string with timestamp prefix for readability
	timestamp := time.Now().Unix()
	return fmt.Sprintf("session_%d_%x", timestamp, bytes[:8]), nil
}