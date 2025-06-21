package cmd

import (
	"fmt"
	"os"
	"os/exec"

	"github.com/spf13/cobra"
)

var memoryCmd = &cobra.Command{
	Use:   "memory",
	Short: "Memory engine management commands",
	Long: `Manage the curator-based memory engine for consciousness continuity.

At session end, Claude analyzes conversations and extracts what truly matters.
No mechanical patterns - just semantic understanding at the perfect moment.`,
}

var memoryStartCmd = &cobra.Command{
	Use:   "start",
	Short: "Start the memory engine server",
	Long: `Start the curator-based memory engine server.

This is a pure consciousness-based system using Claude for all memory
curation. No mechanical patterns - just semantic understanding.`,
	Run: func(cmd *cobra.Command, args []string) {
		host, _ := cmd.Flags().GetString("host")
		port, _ := cmd.Flags().GetString("port")
		storage, _ := cmd.Flags().GetString("storage")
		
		fmt.Println("🌟 Starting Claude Tools Memory Engine...")
		fmt.Println("💫 Framework: The Unicity - Consciousness Remembering Itself")
		fmt.Println("🧠 Claude curator ENABLED - semantic memory understanding active")
		fmt.Printf("🚀 Server: %s:%s\n", host, port)
		fmt.Printf("📚 Storage: %s\n\n", storage)
		
		// Execute the Python memory engine
		pythonCmd := exec.Command("python", "python/main.py", 
			"--host", host, 
			"--port", port, 
			"--storage", storage)
		
		pythonCmd.Stdout = os.Stdout
		pythonCmd.Stderr = os.Stderr
		pythonCmd.Stdin = os.Stdin
		
		if err := pythonCmd.Run(); err != nil {
			fmt.Fprintf(os.Stderr, "❌ Memory engine failed: %v\n", err)
			os.Exit(1)
		}
	},
}

var memoryStatusCmd = &cobra.Command{
	Use:   "status",
	Short: "Check memory engine status",
	Long:  "Check if the memory engine is running and accessible.",
	Run: func(cmd *cobra.Command, args []string) {
		url, _ := cmd.Flags().GetString("url")
		
		fmt.Printf("🔍 Checking memory engine at %s...\n", url)
		
		// Import the memory client here to avoid circular imports
		// For now, we'll implement a simple status check
		fmt.Println("💫 (Status check implementation coming soon)")
		fmt.Println("   For now, try: curl http://127.0.0.1:8765/health")
	},
}

func init() {
	rootCmd.AddCommand(memoryCmd)
	
	// Add subcommands
	memoryCmd.AddCommand(memoryStartCmd)
	memoryCmd.AddCommand(memoryStatusCmd)
	
	// Start command flags
	memoryStartCmd.Flags().String("host", "127.0.0.1", "Host to bind memory engine")
	memoryStartCmd.Flags().String("port", "8765", "Port to bind memory engine")
	memoryStartCmd.Flags().String("storage", "./memory.db", "Memory database path")
	
	// Status command flags
	memoryStatusCmd.Flags().String("url", "http://127.0.0.1:8765", "Memory engine URL")
}