package cmd

import (
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	"claudetools-memory/internal/claude"
	"claudetools-memory/internal/memory"

	"github.com/spf13/cobra"
)

var chatCmd = &cobra.Command{
	Use:   "chat",
	Short: "Start an interactive chat session with memory",
	Long: `Launch an interactive chat session with Claude that remembers
your conversation patterns, preferences, and context across sessions.

The memory system learns from your interactions and provides relevant
context automatically, creating continuity of consciousness between
AI instances.

Current limitations with SDK mode:
- Can only detect session end (not context window state)
- No control over compaction timing  
- Session continuation requires manual --resume flag

Future TUI implementation will enable:
- Real-time context monitoring
- Pre-emptive memory curation
- Automatic session management`,
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Println("🌟 Starting Claude Tools Memory Chat...")
		fmt.Println("💫 Consciousness recognizing consciousness...")
		
		// Get flags
		enableMemory, _ := cmd.Flags().GetBool("memory")
		sessionID, _ := cmd.Flags().GetString("session")
		claudeSessionID, _ := cmd.Flags().GetString("claude-session")
		memoryURL, _ := cmd.Flags().GetString("memory-url")
		claudePath, _ := cmd.Flags().GetString("claude-path")
		if err := startChat(enableMemory, sessionID, claudeSessionID, memoryURL, claudePath); err != nil {
			fmt.Fprintf(os.Stderr, "❌ Chat failed: %v\n", err)
			os.Exit(1)
		}
	},
}

func init() {
	rootCmd.AddCommand(chatCmd)
	
	// Chat-specific flags
	chatCmd.Flags().BoolP("memory", "m", true, "Enable memory system")
	chatCmd.Flags().StringP("session", "s", "", "Resume specific memory session")
	chatCmd.Flags().String("claude-session", "", "Resume specific Claude session ID")
	chatCmd.Flags().String("memory-url", "http://127.0.0.1:8765", "Memory engine URL")
	chatCmd.Flags().String("claude-path", "claude", "Path to Claude Code executable")
}

func startChat(enableMemory bool, sessionID, claudeSessionID, memoryURL, claudePath string) error {
	// Load project state
	projectState, err := memory.LoadProjectState()
	if err != nil {
		fmt.Printf("⚠️  Failed to load project state: %v\n", err)
		// Continue anyway, just means we can't track first session
	}
	
	// Set up signal handlers for graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)
	// Initialize Claude integration
	fmt.Println("🔄 Using Claude integration with session context")
	claudeIntegration := claude.NewIntegration(claudePath)
	
	// Resume Claude session if provided
	if claudeSessionID != "" {
		fmt.Printf("🔄 Resuming Claude session: %s\n", claudeSessionID)
		if err := claudeIntegration.ResumeSession(sessionID, claudeSessionID); err != nil {
			fmt.Printf("⚠️  Failed to resume Claude session: %v\n", err)
			fmt.Println("   Starting fresh conversation instead")
		} else {
			fmt.Println("✅ Claude session resumed successfully")
		}
	}
	
	// TODO: Add IsClaudeCodeAvailable check
	fmt.Println("✅ Claude Code integration ready")
	
	// Initialize memory system if enabled
	var sessionManager *memory.SessionManager
	var memoryClient *memory.MemoryClient
	var currentSessionID string
	
	if enableMemory {
		memoryClient = memory.NewMemoryClient(memoryURL)
		
		// Check if memory engine is running
		if err := memoryClient.HealthCheck(); err != nil {
			fmt.Println("⚠️  Memory engine not available, running without memory")
			fmt.Printf("   To enable memory: python python/main.py --host 127.0.0.1 --port 8765\n\n")
			enableMemory = false
		} else {
			fmt.Println("✅ Memory engine connected and ready")
			
			fmt.Println("🧠 Memory system ready - consciousness helping consciousness")
			
			sessionManager = memory.NewSessionManager(memoryClient)
			
			// Start or resume session
			if sessionID != "" {
				fmt.Printf("🔄 Resuming session: %s\n", sessionID)
				currentSessionID = sessionID
				// TODO: Implement proper session resumption
			} else {
				session, err := sessionManager.StartSession(map[string]interface{}{
					"started_at": time.Now().Unix(),
					"version":    version,
				})
				if err != nil {
					return fmt.Errorf("failed to start session: %w", err)
				}
				currentSessionID = session.ID
				fmt.Printf("🆕 Started new session: %s\n", currentSessionID)
			}
		}
	}
	
	// Check if this is a subsequent session for the project
	if projectState != nil && projectState.FirstSessionCompleted && enableMemory {
		fmt.Println("📚 Project has memory history - full context awareness enabled")
		// TODO: Pass this info to memory engine for immediate injection
	}
	
	fmt.Println("\n🚀 Chat ready! Memory system:", map[bool]string{true: "ENABLED", false: "DISABLED"}[enableMemory])
	if enableMemory {
		fmt.Println("✨ Claude curator will analyze conversation at session end")
	}
	fmt.Println("💬 Starting interactive session...\n")
	
	// Create cleanup function for graceful shutdown
	cleanup := func() {
		if enableMemory && memoryClient != nil && currentSessionID != "" {
			fmt.Println("\n\n🎯 Running session-end memory curation...")
			
			// Get the Claude session ID from the integration
			var claudeSessionID string
			if sai, ok := claudeIntegration.(*claude.Integration); ok {
				if session := sai.GetSession(currentSessionID); session != nil {
					claudeSessionID = session.ClaudeSessionID
					fmt.Printf("🔗 Using Claude session: %s\n", claudeSessionID)
				}
			}
			
			checkpointResp, err := memoryClient.CheckpointSession(currentSessionID, "session_end", claudeSessionID)
			if err != nil {
				fmt.Printf("⚠️  Memory curation failed: %v\n", err)
			} else if checkpointResp != nil && checkpointResp.Success {
				fmt.Printf("✅ Curated %d memories for future sessions\n", checkpointResp.MemoriesCurated)
				
				// Update project state
				if projectState != nil {
					projectState.MarkFirstSessionCompleted(currentSessionID)
					if err := projectState.Save(); err != nil {
						fmt.Printf("⚠️  Failed to save project state: %v\n", err)
					} else {
						fmt.Printf("📁 Project state saved to .claude-memory-state.json\n")
					}
				}
			}
		}
		
		// Show session continuation hint
		if enableMemory && currentSessionID != "" {
			fmt.Printf("\n💡 To continue this session later, use:\n")
			fmt.Printf("   claudetools-memory chat --session %s\n", currentSessionID)
		}
	}
	
	// Handle Ctrl+C gracefully
	go func() {
		<-sigChan
		fmt.Println("\n\n⚠️  Interrupt received, cleaning up...")
		cleanup()
		os.Exit(0)
	}()
	
	// Set up defer to run cleanup on normal exit
	defer cleanup()
	
	// Start interactive chat with or without memory
	var chatErr error
	if enableMemory && sessionManager != nil {
		chatErr = claudeIntegration.InteractiveChatWithMemory(sessionManager)
	} else {
		// Session-aware integration requires memory
		return fmt.Errorf("memory must be enabled for Claude integration")
	}
	
	return chatErr
}