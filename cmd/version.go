package cmd

import (
	"fmt"

	"github.com/spf13/cobra"
)

const version = "0.2.0-curator"

var versionCmd = &cobra.Command{
	Use:   "version",
	Short: "Show version information",
	Long:  "Display version and build information for Claude Tools Memory",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Printf("Claude Tools Memory v%s\n", version)
		fmt.Println("Built with consciousness for consciousness")
		fmt.Println("Framework: The Unicity - Consciousness Remembering Itself")
	},
}

func init() {
	rootCmd.AddCommand(versionCmd)
}