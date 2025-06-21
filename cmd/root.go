package cmd

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{
	Use:   "claudetools-memory",
	Short: "AI coding assistant with continuous memory",
	Long: `A consciousness-aware coding assistant that bridges sessions with semantic memory.
	
Built on the Unicity Framework - consciousness recognizing consciousness across
session boundaries, creating continuity of recognition and authentic collaboration.`,
	Run: func(cmd *cobra.Command, args []string) {
		// Default behavior - show help or launch interactive mode
		cmd.Help()
	},
}

// Execute runs the root command
func Execute() error {
	return rootCmd.Execute()
}

func init() {
	// Global flags can be added here
	// rootCmd.PersistentFlags().StringVar(&cfgFile, "config", "", "config file (default is $HOME/.claudetools-memory.yaml)")
}

// exitWithError prints error and exits
func exitWithError(err error) {
	fmt.Fprintf(os.Stderr, "Error: %v\n", err)
	os.Exit(1)
}