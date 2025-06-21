package memory

import (
	"fmt"
)

// ClaudeIntegration interface to avoid circular imports
type ClaudeIntegration interface {
	SendMessageWithMemory(message, memoryContext string) (*ClaudeResponse, error)
}

// ClaudeResponse represents a response from Claude Code
type ClaudeResponse struct {
	Content      string `json:"content"`
	InputTokens  int    `json:"input_tokens,omitempty"`
	OutputTokens int    `json:"output_tokens,omitempty"`
}

// ConversationFlow handles the complete memory-aware conversation cycle
type ConversationFlow struct {
	sessionManager    *SessionManager
	claudeIntegration ClaudeIntegration
}

// NewConversationFlow creates a new conversation flow manager
func NewConversationFlow(sessionManager *SessionManager, claudeIntegration ClaudeIntegration) *ConversationFlow {
	return &ConversationFlow{
		sessionManager:    sessionManager,
		claudeIntegration: claudeIntegration,
	}
}

// ProcessMessage handles a complete conversation exchange with memory
func (cf *ConversationFlow) ProcessMessage(userMessage string) (*ConversationResponse, error) {
	// 1. Get memory context for the message
	fmt.Print("🔍 Retrieving memory context...")
	context, err := cf.sessionManager.GetContextForMessage(userMessage)
	if err != nil {
		fmt.Print("\r                                    \r") // Clear the line
		return nil, fmt.Errorf("failed to get memory context: %w", err)
	}
	fmt.Print("\r✅ Memory context retrieved         \n")

	// 2. Send to Claude with memory context
	fmt.Print("🤔 Claude is thinking...")
	claudeResponse, err := cf.claudeIntegration.SendMessageWithMemory(userMessage, context.ContextText)
	if err != nil {
		fmt.Print("\r                                    \r") // Clear the line
		return nil, fmt.Errorf("failed to get Claude response: %w", err)
	}
	fmt.Print("\r✅ Claude has responded             \n")

	// 3. Store the exchange in memory
	fmt.Print("💾 Storing in memory...")
	updatedContext, err := cf.sessionManager.ProcessExchange(userMessage, claudeResponse.Content)
	if err != nil {
		fmt.Print("\r                                    \r") // Clear the line
		return nil, fmt.Errorf("failed to store exchange: %w", err)
	}
	fmt.Print("\r✅ Memory updated                   \n")

	return &ConversationResponse{
		ClaudeResponse:   claudeResponse.Content,
		MemoryContext:    context,
		UpdatedContext:   updatedContext,
		TokenUsage:       TokenUsage{Input: claudeResponse.InputTokens, Output: claudeResponse.OutputTokens},
	}, nil
}

// ConversationResponse contains the complete response from a memory-aware exchange
type ConversationResponse struct {
	ClaudeResponse   string                `json:"claude_response"`
	MemoryContext    *ConversationContext  `json:"memory_context"`
	UpdatedContext   *ConversationContext  `json:"updated_context"`
	TokenUsage       TokenUsage            `json:"token_usage"`
}

// TokenUsage tracks Claude API token consumption
type TokenUsage struct {
	Input  int `json:"input_tokens"`
	Output int `json:"output_tokens"`
}