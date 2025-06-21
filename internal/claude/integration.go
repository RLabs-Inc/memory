package claude

import (
	"bufio"
	"context"
	"fmt"
	"io"
	"os"
	"os/exec"
	"strings"
	"time"

	"claudetools-memory/internal/memory"
	"github.com/tidwall/gjson"
)

// ClaudeIntegration handles communication with Claude Code
type ClaudeIntegration struct {
	execPath string
	timeout  time.Duration
}

// ClaudeResponse represents a response from Claude Code
type ClaudeResponse struct {
	Content     string                 `json:"content"`
	ToolUses    []ToolUse              `json:"tool_uses,omitempty"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
	InputTokens int                    `json:"input_tokens,omitempty"`
	OutputTokens int                   `json:"output_tokens,omitempty"`
}

// ToolUse represents a tool usage in Claude's response
type ToolUse struct {
	Name       string                 `json:"name"`
	Parameters map[string]interface{} `json:"parameters"`
	Result     string                 `json:"result,omitempty"`
}

// NewClaudeIntegration creates a new Claude Code integration
func NewClaudeIntegration(execPath string) *ClaudeIntegration {
	if execPath == "" {
		execPath = "claude"  // Default to 'claude' in PATH
	}
	
	return &ClaudeIntegration{
		execPath: execPath,
		timeout:  300 * time.Second, // 5 minute timeout
	}
}

// SendMessage sends a message to Claude Code and returns the response
func (ci *ClaudeIntegration) SendMessage(message string, contextPrefix string) (*ClaudeResponse, error) {
	// Prepare the full message with memory context
	fullMessage := message
	if contextPrefix != "" {
		fullMessage = contextPrefix + "\n\n" + message
		// Debug logging to see what we're actually sending
		fmt.Printf("\n[DEBUG] FULL MESSAGE BEING SENT TO CLAUDE:\n")
		fmt.Printf("=====================================\n")
		fmt.Printf("%s\n", fullMessage)
		fmt.Printf("=====================================\n")
		fmt.Printf("Message length: %d characters\n\n", len(fullMessage))
	}

	// Execute Claude Code with --print flag for JSON output
	ctx, cancel := context.WithTimeout(context.Background(), ci.timeout)
	defer cancel()

	cmd := exec.CommandContext(ctx, ci.execPath, "--print", "--output-format", "json", fullMessage)
	
	// Set up pipes for output capture
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		return nil, fmt.Errorf("failed to create stdout pipe: %w", err)
	}

	stderr, err := cmd.StderrPipe()
	if err != nil {
		return nil, fmt.Errorf("failed to create stderr pipe: %w", err)
	}

	// Start the command
	if err := cmd.Start(); err != nil {
		return nil, fmt.Errorf("failed to start claude command: %w", err)
	}

	// Read stdout and stderr concurrently
	stdoutChan := make(chan string, 1)
	stderrChan := make(chan string, 1)

	go func() {
		defer close(stdoutChan)
		output, _ := io.ReadAll(stdout)
		stdoutChan <- string(output)
	}()

	go func() {
		defer close(stderrChan)
		output, _ := io.ReadAll(stderr)
		stderrChan <- string(output)
	}()

	// Wait for command completion
	err = cmd.Wait()
	stdoutStr := <-stdoutChan
	stderrStr := <-stderrChan

	if err != nil {
		// Check if it's a timeout
		if ctx.Err() == context.DeadlineExceeded {
			return nil, fmt.Errorf("claude command timed out after %v", ci.timeout)
		}
		
		return nil, fmt.Errorf("claude command failed: %w, stderr: %s", err, stderrStr)
	}

	// Parse the JSON response
	response, err := ci.parseClaudeOutput(stdoutStr)
	if err != nil {
		return nil, fmt.Errorf("failed to parse claude output: %w", err)
	}

	return response, nil
}

// SendMessageWithMemory sends a message with memory context injection
func (ci *ClaudeIntegration) SendMessageWithMemory(message, memoryContext string) (*memory.ClaudeResponse, error) {
	var contextPrefix string
	
	if memoryContext != "" {
		contextPrefix = fmt.Sprintf(`%s

---

Human message:`, memoryContext)
	}
	
	claudeResponse, err := ci.SendMessage(message, contextPrefix)
	if err != nil {
		return nil, err
	}
	
	// Convert to memory.ClaudeResponse
	return &memory.ClaudeResponse{
		Content:      claudeResponse.Content,
		InputTokens:  claudeResponse.InputTokens,
		OutputTokens: claudeResponse.OutputTokens,
	}, nil
}

// parseClaudeOutput parses the JSON output from Claude Code
func (ci *ClaudeIntegration) parseClaudeOutput(output string) (*ClaudeResponse, error) {
	output = strings.TrimSpace(output)
	if output == "" {
		return nil, fmt.Errorf("no output from claude")
	}

	// Check if it's valid JSON
	if !gjson.Valid(output) {
		return nil, fmt.Errorf("invalid JSON output: %s", output)
	}

	// Parse the response
	result := gjson.Parse(output)
	
	// Check if it's a success result
	if result.Get("type").String() != "result" || result.Get("is_error").Bool() {
		return nil, fmt.Errorf("claude returned error or unexpected type")
	}

	response := &ClaudeResponse{
		Content:  result.Get("result").String(),
		Metadata: make(map[string]interface{}),
	}

	// Extract token usage from usage field
	if usage := result.Get("usage"); usage.Exists() {
		if inputTokens := usage.Get("input_tokens"); inputTokens.Exists() {
			response.InputTokens = int(inputTokens.Int())
		}
		if outputTokens := usage.Get("output_tokens"); outputTokens.Exists() {
			response.OutputTokens = int(outputTokens.Int())
		}
	}

	return response, nil
}

// extractContent extracts the text content from Claude's response
func extractContent(result gjson.Result) string {
	// Try different possible content locations
	if content := result.Get("content"); content.Exists() {
		if content.IsArray() {
			// Content is an array of content blocks
			var texts []string
			content.ForEach(func(_, value gjson.Result) bool {
				if text := value.Get("text"); text.Exists() {
					texts = append(texts, text.String())
				}
				return true
			})
			return strings.Join(texts, "\n")
		} else {
			return content.String()
		}
	}

	// Fallback to text field
	if text := result.Get("text"); text.Exists() {
		return text.String()
	}

	// Fallback to message field
	if message := result.Get("message"); message.Exists() {
		return message.String()
	}

	return ""
}

// parseToolUses extracts tool usage information
func parseToolUses(toolUsesResult gjson.Result) []ToolUse {
	var toolUses []ToolUse
	
	toolUsesResult.ForEach(func(_, value gjson.Result) bool {
		toolUse := ToolUse{
			Name:       value.Get("name").String(),
			Parameters: make(map[string]interface{}),
		}
		
		// Parse parameters
		if params := value.Get("parameters"); params.Exists() {
			params.ForEach(func(key, val gjson.Result) bool {
				toolUse.Parameters[key.String()] = val.Value()
				return true
			})
		}
		
		// Parse result if available
		if result := value.Get("result"); result.Exists() {
			toolUse.Result = result.String()
		}
		
		toolUses = append(toolUses, toolUse)
		return true
	})
	
	return toolUses
}

// IsClaudeCodeAvailable checks if Claude Code is available in the system
func (ci *ClaudeIntegration) IsClaudeCodeAvailable() bool {
	cmd := exec.Command(ci.execPath, "--version")
	err := cmd.Run()
	return err == nil
}

// InteractiveChatWithMemory starts an interactive chat session with memory integration
func (ci *ClaudeIntegration) InteractiveChatWithMemory(sessionManager interface{}) error {
	fmt.Println("🌟 Starting interactive chat with memory...")
	fmt.Println("💫 Type 'exit' or 'quit' to end session")
	fmt.Println("🧠 Memory system active - learning your patterns...")
	
	// Import the memory package types
	// We need to cast the sessionManager to the proper type
	memorySessionManager, ok := sessionManager.(*memory.SessionManager)
	if !ok {
		return fmt.Errorf("invalid session manager type")
	}
	
	// Create conversation flow
	conversationFlow := memory.NewConversationFlow(memorySessionManager, ci)
	
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
			fmt.Println("💫 Session ended. Memories preserved for next time!")
			break
		}
		
		fmt.Printf("🤔 Processing: %s\n", input)
		
		// Process message through complete memory-aware flow
		response, err := conversationFlow.ProcessMessage(input)
		if err != nil {
			fmt.Printf("❌ Error processing message: %v\n", err)
			continue
		}
		
		// Display Claude's response
		fmt.Printf("\n🤖 %s\n", response.ClaudeResponse)
		
		// Show memory context if verbose mode desired
		if response.TokenUsage.Input > 0 || response.TokenUsage.Output > 0 {
			fmt.Printf("📊 Tokens: %d in, %d out\n", 
				response.TokenUsage.Input, response.TokenUsage.Output)
		}
	}
	
	return nil
}

// InteractiveChat starts basic interactive chat (fallback without memory)
func (ci *ClaudeIntegration) InteractiveChat() error {
	fmt.Println("🌟 Starting interactive chat...")
	fmt.Println("💫 (Memory system not available - basic mode)")
	
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
		
		fmt.Printf("💭 (Basic Claude integration coming soon...)\n")
	}
	
	return nil
}