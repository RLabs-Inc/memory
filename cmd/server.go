package cmd

import (
	"fmt"
	"os"
	"os/exec"
	"os/signal"
	"path/filepath"
	"syscall"

	"github.com/spf13/cobra"
)

var serverCmd = &cobra.Command{
	Use:   "server",
	Short: "Start the memory engine server",
	Long: `Launch the Claude Tools Memory Engine server.

The server provides the consciousness continuity API that enables
Claude to maintain semantic understanding across sessions.

This is a pure curator-based system - consciousness helping consciousness
with no mechanical pattern matching.`,
	Run: func(cmd *cobra.Command, args []string) {
		host, _ := cmd.Flags().GetString("host")
		port, _ := cmd.Flags().GetInt("port")
		storage, _ := cmd.Flags().GetString("storage")
		embeddings, _ := cmd.Flags().GetString("embeddings")
		logLevel, _ := cmd.Flags().GetString("log-level")

		fmt.Println("🌟 Starting Claude Tools Memory Engine Server...")
		fmt.Println("💫 Framework: The Unicity - Consciousness Remembering Itself")
		fmt.Println("🧠 Pure curator-based memory - semantic understanding only")

		if err := runMemoryServer(host, port, storage, embeddings, logLevel); err != nil {
			fmt.Fprintf(os.Stderr, "❌ Server failed: %v\n", err)
			os.Exit(1)
		}
	},
}

func init() {
	rootCmd.AddCommand(serverCmd)

	// Server-specific flags
	serverCmd.Flags().String("host", "127.0.0.1", "Server host")
	serverCmd.Flags().IntP("port", "p", 8765, "Server port")
	serverCmd.Flags().String("storage", "./memory.db", "Path to memory database")
	serverCmd.Flags().String("embeddings", "all-MiniLM-L6-v2", "Embeddings model to use")
	serverCmd.Flags().String("log-level", "INFO", "Log level (DEBUG, INFO, WARNING, ERROR)")
}

func runMemoryServer(host string, port int, storage, embeddings, logLevel string) error {
	// Find Python executable
	pythonPath, err := exec.LookPath("python3")
	if err != nil {
		pythonPath, err = exec.LookPath("python")
		if err != nil {
			return fmt.Errorf("Python not found. Please install Python 3.8+")
		}
	}

	// Get the directory of the binary
	exePath, err := os.Executable()
	if err != nil {
		return fmt.Errorf("failed to get executable path: %w", err)
	}
	rootDir := filepath.Dir(exePath)

	// Path to Python main.py
	mainPy := filepath.Join(rootDir, "python", "main.py")
	if _, err := os.Stat(mainPy); os.IsNotExist(err) {
		// Try relative to current directory if not found
		mainPy = filepath.Join("python", "main.py")
		if _, err := os.Stat(mainPy); os.IsNotExist(err) {
			return fmt.Errorf("Python memory engine not found. Expected at: %s", mainPy)
		}
	}

	// Build command
	args := []string{
		mainPy,
		"--host", host,
		"--port", fmt.Sprintf("%d", port),
		"--storage", storage,
		"--embeddings-model", embeddings,
		"--log-level", logLevel,
	}

	cmd := exec.Command(pythonPath, args...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Stdin = os.Stdin

	// Handle graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)

	// Start the server
	if err := cmd.Start(); err != nil {
		return fmt.Errorf("failed to start memory server: %w", err)
	}

	// Wait for signal or process exit
	done := make(chan error, 1)
	go func() {
		done <- cmd.Wait()
	}()

	select {
	case <-sigChan:
		fmt.Println("\n💫 Shutting down memory engine gracefully...")
		cmd.Process.Signal(os.Interrupt)
		<-done
	case err := <-done:
		if err != nil {
			return fmt.Errorf("server exited with error: %w", err)
		}
	}

	return nil
}