package claude

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"strings"
	"sync"
	"time"

	"claudetools-memory/internal/memory"
	"github.com/tidwall/gjson"
)

// Integration manages Claude Code with proper session handling
type Integration struct {
	execPath       string
	timeout        time.Duration
	activeSessions map[string]*ManagedSession
	mu             sync.RWMutex
}

// ManagedSession represents an active Claude session
type ManagedSession struct {
	SessionID      string
	ClaudeSessionID string  // The actual session ID from Claude
	MessageCount   int
	StartedAt      time.Time
	LastMessageAt  time.Time
}

// ClaudeResponse represents a response from Claude
type ClaudeResponse struct {
	Content      string
	InputTokens  int
	OutputTokens int
}

// NewIntegration creates a new Claude integration
func NewIntegration(execPath string) *Integration {
	if execPath == "" {
		execPath = "claude"
	}
	
	return &Integration{
		execPath:       execPath,
		timeout:        300 * time.Second,
		activeSessions: make(map[string]*ManagedSession),
	}
}

// SendMessageInSession sends a message within a managed session
func (i *Integration) SendMessageInSession(sessionID, message, contextPrefix string) (*ClaudeResponse, error) {
	i.mu.Lock()
	session, exists := i.activeSessions[sessionID]
	if !exists {
		// Create new session placeholder - Claude session ID will be set after first message
		session = &ManagedSession{
			SessionID:       sessionID,
			ClaudeSessionID: "", // Will be populated from first response
			MessageCount:    0,
			StartedAt:       time.Now(),
			LastMessageAt:   time.Now(),
		}
		i.activeSessions[sessionID] = session
	}
	i.mu.Unlock()
	
	// Prepare the full message
	fullMessage := message
	if contextPrefix != "" {
		// Inject context prefix whenever available
		fullMessage = contextPrefix + "\n\n" + message
		fmt.Printf("[DEBUG] Message has context prefix (length: %d)\n", len(contextPrefix))
	}
	fmt.Printf("[DEBUG] Full message being sent (length: %d):\n%s\n", len(fullMessage), fullMessage)
	
	// Execute Claude with session continuation
	var cmd *exec.Cmd
	if session.MessageCount == 0 {
		// First message - start new session
		fmt.Printf("[DEBUG] First message, starting new session\n")
		fmt.Printf("[DEBUG] Command: %s --print --output-format json <message>\n", i.execPath)
		cmd = exec.Command(i.execPath, "--print", "--output-format", "json", fullMessage)
	} else if session.ClaudeSessionID != "" {
		// Resume specific session with session ID
		fmt.Printf("[DEBUG] Resuming session: %s\n", session.ClaudeSessionID)
		cmd = exec.Command(i.execPath, "--print", "--output-format", "json", "--resume", session.ClaudeSessionID, fullMessage)
	} else {
		// This shouldn't happen, but fallback to new session
		fmt.Printf("[DEBUG] Fallback: starting new session (no Claude session ID)\n")
		cmd = exec.Command(i.execPath, "--print", "--output-format", "json", fullMessage)
	}
	
	// Process the JSON response
	response, sessionInfo, err := i.processJSONResponse(cmd)
	if err != nil {
		return nil, fmt.Errorf("failed to process Claude response: %w", err)
	}
	
	// Update session info
	i.mu.Lock()
	session.MessageCount++
	session.LastMessageAt = time.Now()
	if sessionInfo.SessionID != "" {
		session.ClaudeSessionID = sessionInfo.SessionID
	}
	i.mu.Unlock()
	
	return response, nil
}

// ResumeSession resumes a previous Claude session
func (i *Integration) ResumeSession(sessionID, claudeSessionID string) error {
	i.mu.Lock()
	defer i.mu.Unlock()
	
	// Verify the session exists in Claude
	cmd := exec.Command(i.execPath, "--print", "--output-format", "json", "--resume", claudeSessionID, "Session resumed")
	output, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("failed to resume Claude session %s: %w", claudeSessionID, err)
	}
	
	// Parse response to verify session
	if !gjson.ValidBytes(output) {
		return fmt.Errorf("invalid response from Claude")
	}
	
	result := gjson.ParseBytes(output)
	if result.Get("type").String() == "error" {
		return fmt.Errorf("Claude session %s not found", claudeSessionID)
	}
	
	// Store the resumed session
	i.activeSessions[sessionID] = &ManagedSession{
		SessionID:       sessionID,
		ClaudeSessionID: claudeSessionID,
		MessageCount:    1, // We just sent a resume message
		StartedAt:       time.Now(),
		LastMessageAt:   time.Now(),
	}
	
	return nil
}

// GetSession returns the managed session information
func (i *Integration) GetSession(sessionID string) *ManagedSession {
	i.mu.RLock()
	defer i.mu.RUnlock()
	
	session, exists := i.activeSessions[sessionID]
	if !exists {
		return nil
	}
	
	// Return a copy to avoid race conditions
	return &ManagedSession{
		SessionID:       session.SessionID,
		ClaudeSessionID: session.ClaudeSessionID,
		MessageCount:    session.MessageCount,
		StartedAt:       session.StartedAt,
		LastMessageAt:   session.LastMessageAt,
	}
}

// processStreamingResponse handles the stream-json output from Claude
func (i *Integration) processStreamingResponse(cmd *exec.Cmd) (*ClaudeResponse, *SessionInfo, error) {
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		return nil, nil, fmt.Errorf("failed to create stdout pipe: %w", err)
	}
	
	if err := cmd.Start(); err != nil {
		return nil, nil, fmt.Errorf("failed to start claude: %w", err)
	}
	
	fmt.Printf("[DEBUG] Claude process started, reading response...\n")
	
	defer cmd.Wait()
	
	// Read streaming JSON responses
	scanner := bufio.NewScanner(stdout)
	var messages []json.RawMessage
	var sessionInfo SessionInfo
	var finalResponse *ClaudeResponse
	
	for scanner.Scan() {
		line := scanner.Text()
		if line == "" {
			continue
		}
		
		// Parse each JSON message
		if !gjson.Valid(line) {
			fmt.Printf("[DEBUG] Invalid JSON line: %s\n", line)
			continue
		}
		
		msg := gjson.Parse(line)
		msgType := msg.Get("type").String()
		fmt.Printf("[DEBUG] Message type: %s\n", msgType)
		
		switch msgType {
		case "system":
			// Extract session info from init message
			if msg.Get("subtype").String() == "init" {
				sessionInfo.SessionID = msg.Get("session_id").String()
				sessionInfo.Model = msg.Get("model").String()
			}
			
		case "assistant":
			// Claude's response
			content := extractStreamContent(msg.Get("message"))
			finalResponse = &ClaudeResponse{
				Content: content,
			}
			
		case "result":
			// Final result with token counts
			if msg.Get("subtype").String() == "success" {
				if finalResponse == nil {
					finalResponse = &ClaudeResponse{}
				}
				finalResponse.Content = msg.Get("result").String()
				finalResponse.InputTokens = int(msg.Get("usage.input_tokens").Int())
				finalResponse.OutputTokens = int(msg.Get("usage.output_tokens").Int())
			}
		}
		
		messages = append(messages, json.RawMessage(line))
	}
	
	if err := scanner.Err(); err != nil {
		return nil, nil, fmt.Errorf("error reading response: %w", err)
	}
	
	if finalResponse == nil {
		return nil, nil, fmt.Errorf("no response received from Claude")
	}
	
	return finalResponse, &sessionInfo, nil
}

// SessionInfo contains Claude session metadata
type SessionInfo struct {
	SessionID string
	Model     string
}

// extractStreamContent extracts text from streaming message format
func extractStreamContent(message gjson.Result) string {
	// Handle different content formats in streaming responses
	content := message.Get("content")
	if content.IsArray() {
		var texts []string
		content.ForEach(func(_, block gjson.Result) bool {
			if text := block.Get("text"); text.Exists() {
				texts = append(texts, text.String())
			}
			return true
		})
		return strings.Join(texts, "\n")
	}
	
	// Fallback to direct content
	return content.String()
}

// processJSONResponse handles the json output from Claude
func (i *Integration) processJSONResponse(cmd *exec.Cmd) (*ClaudeResponse, *SessionInfo, error) {
	output, err := cmd.CombinedOutput()
	if err != nil {
		return nil, nil, fmt.Errorf("command failed: %w", err)
	}
	
	outputStr := strings.TrimSpace(string(output))
	fmt.Printf("[DEBUG] Raw JSON output: %s\n", outputStr)
	
	if !gjson.Valid(outputStr) {
		return nil, nil, fmt.Errorf("invalid JSON output")
	}
	
	result := gjson.Parse(outputStr)
	
	// Check for error
	if result.Get("type").String() == "error" {
		return nil, nil, fmt.Errorf("Claude error: %s", result.Get("message").String())
	}
	
	// Extract response content
	content := result.Get("result").String()
	if content == "" {
		return nil, nil, fmt.Errorf("no content in response")
	}
	
	response := &ClaudeResponse{
		Content:      content,
		InputTokens:  int(result.Get("usage.input_tokens").Int()),
		OutputTokens: int(result.Get("usage.output_tokens").Int()),
	}
	
	// Extract session info
	sessionInfo := &SessionInfo{
		SessionID: result.Get("session_id").String(),
		Model:     result.Get("model").String(),
	}
	
	return response, sessionInfo, nil
}

// startNewClaudeSession starts a fresh Claude session
func (i *Integration) startNewClaudeSession() (string, error) {
	// No longer needed - session will be created on first real message
	return "", nil
}

// GetActiveSession returns the active session for a given ID
func (i *Integration) GetActiveSession(sessionID string) (*ManagedSession, bool) {
	i.mu.RLock()
	defer i.mu.RUnlock()
	
	session, exists := i.activeSessions[sessionID]
	return session, exists
}

// CloseSession closes an active session
func (i *Integration) CloseSession(sessionID string) {
	i.mu.Lock()
	defer i.mu.Unlock()
	
	delete(i.activeSessions, sessionID)
}

// InteractiveChatWithMemory runs a session-aware chat with memory
func (i *Integration) InteractiveChatWithMemory(sessionManager *memory.SessionManager) error {
	fmt.Println("🌟 Starting session-aware chat with memory...")
	fmt.Println("💫 Claude will maintain conversation context across messages")
	fmt.Println("🧠 Memory system active - learning your patterns...")
	
	// Get the current session ID from the manager
	sessionID := ""
	if sessionManager != nil && sessionManager.GetCurrentSession() != nil {
		sessionID = sessionManager.GetCurrentSession().ID
	}
	if sessionID == "" {
		sessionID = fmt.Sprintf("session_%d", time.Now().Unix())
	}
	
	conversationFlow := memory.NewConversationFlow(sessionManager, sai)
	scanner := bufio.NewScanner(os.Stdin)
	
	for {
		fmt.Print("\n> ")
		if !scanner.Scan() {
			break
		}
		
		input := strings.TrimSpace(scanner.Text())
		if input == "" {
			continue
		}
		
		if input == "exit" || input == "quit" {
			break
		}
		
		// Process through memory-aware flow
		response, err := conversationFlow.ProcessMessage(input)
		if err != nil {
			fmt.Printf("❌ Error: %v\n", err)
			continue
		}
		
		fmt.Printf("\n🤖 %s\n", response.ClaudeResponse)
		
		// Show session info
		if session, exists := i.GetActiveSession(sessionID); exists {
			fmt.Printf("📊 Session: %s (msg #%d)\n", session.ClaudeSessionID[:8], session.MessageCount)
		}
	}
	
	// Get final session info for continuation
	if session, exists := i.GetActiveSession(sessionID); exists && session.ClaudeSessionID != "" {
		fmt.Printf("\n💡 To continue this exact conversation later:\n")
		fmt.Printf("   claudetools-memory chat --session %s --claude-session %s\n", sessionID, session.ClaudeSessionID)
		fmt.Printf("   or with Claude directly:\n")
		fmt.Printf("   claude --resume %s\n", session.ClaudeSessionID)
	}
	
	return nil
}

// Implement the ClaudeIntegration interface
func (i *Integration) SendMessageWithMemory(message, memoryContext string) (*memory.ClaudeResponse, error) {
	// Use a default session for compatibility
	sessionID := "default"
	
	claudeResp, err := i.SendMessageInSession(sessionID, message, memoryContext)
	if err != nil {
		return nil, err
	}
	
	return &memory.ClaudeResponse{
		Content:      claudeResp.Content,
		InputTokens:  claudeResp.InputTokens,
		OutputTokens: claudeResp.OutputTokens,
	}, nil
}