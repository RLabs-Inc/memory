package cmd

import (
	"database/sql"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/spf13/cobra"
	_ "github.com/mattn/go-sqlite3"
)

var analyzeCmd = &cobra.Command{
	Use:   "analyze",
	Short: "Analyze memory patterns and conversation history",
	Long: `Analyze stored conversations, patterns, and memory effectiveness.
Provides insights into how the memory system is learning and what
patterns are emerging from your interactions.`,
	Run: func(cmd *cobra.Command, args []string) {
		dbPath, _ := cmd.Flags().GetString("db-path")
		sessionID, _ := cmd.Flags().GetString("session")
		
		if err := analyzeMemory(dbPath, sessionID); err != nil {
			fmt.Fprintf(os.Stderr, "❌ Analysis failed: %v\n", err)
			os.Exit(1)
		}
	},
}

func init() {
	rootCmd.AddCommand(analyzeCmd)
	
	// Analysis-specific flags
	homeDir, _ := os.UserHomeDir()
	defaultDB := filepath.Join(homeDir, ".claudetools-memory", "memory.db")
	
	analyzeCmd.Flags().String("db-path", defaultDB, "Path to memory database")
	analyzeCmd.Flags().StringP("session", "s", "", "Analyze specific session (optional)")
}

func analyzeMemory(dbPath string, sessionID string) error {
	// Open SQLite database
	db, err := sql.Open("sqlite3", dbPath)
	if err != nil {
		return fmt.Errorf("failed to open database: %w", err)
	}
	defer db.Close()

	fmt.Println("🧠 Memory System Analysis")
	fmt.Println("========================")
	
	// Overall statistics
	var totalSessions, totalExchanges, totalPatterns int
	db.QueryRow("SELECT COUNT(*) FROM sessions").Scan(&totalSessions)
	db.QueryRow("SELECT COUNT(*) FROM exchanges").Scan(&totalExchanges)
	db.QueryRow("SELECT COUNT(*) FROM patterns").Scan(&totalPatterns)
	
	fmt.Printf("\n📊 Overall Statistics:\n")
	fmt.Printf("   Sessions:  %d\n", totalSessions)
	fmt.Printf("   Exchanges: %d\n", totalExchanges)
	fmt.Printf("   Patterns:  %d\n", totalPatterns)
	
	// Session-specific analysis
	if sessionID != "" {
		fmt.Printf("\n🔍 Session Analysis: %s\n", sessionID)
		
		var exchangeCount int
		err = db.QueryRow("SELECT COUNT(*) FROM exchanges WHERE session_id = ?", sessionID).Scan(&exchangeCount)
		if err != nil {
			return fmt.Errorf("session not found")
		}
		
		fmt.Printf("   Messages exchanged: %d\n", exchangeCount)
		
		// Show patterns learned
		rows, err := db.Query(`
			SELECT pattern_type, pattern_data, confidence 
			FROM patterns 
			WHERE session_id = ? 
			ORDER BY confidence DESC 
			LIMIT 5
		`, sessionID)
		if err == nil {
			defer rows.Close()
			
			fmt.Printf("\n   Top Patterns Detected:\n")
			for rows.Next() {
				var patternType, patternData string
				var confidence float64
				rows.Scan(&patternType, &patternData, &confidence)
				fmt.Printf("   - %s: %.2f%% confidence\n", patternType, confidence*100)
			}
		}
	} else {
		// Recent sessions
		fmt.Printf("\n📅 Recent Sessions:\n")
		rows, err := db.Query(`
			SELECT s.id, s.created_at, COUNT(e.id) as exchange_count
			FROM sessions s
			LEFT JOIN exchanges e ON s.id = e.session_id
			GROUP BY s.id
			ORDER BY s.created_at DESC
			LIMIT 5
		`)
		if err == nil {
			defer rows.Close()
			
			for rows.Next() {
				var sid string
				var createdAt float64
				var count int
				rows.Scan(&sid, &createdAt, &count)
				
				t := time.Unix(int64(createdAt), 0)
				fmt.Printf("   %s - %s (%d messages)\n", 
					sid[:20]+"...", 
					t.Format("2006-01-02 15:04"), 
					count)
			}
		}
	}
	
	// Memory effectiveness metrics
	fmt.Printf("\n🎯 Memory Effectiveness:\n")
	
	// Check if we're past observation threshold
	if totalExchanges < 20 {
		fmt.Printf("   Status: 👁️  Silent Observation Phase (%d/20 messages)\n", totalExchanges)
	} else if totalExchanges < 40 {
		fmt.Printf("   Status: 📚 Gradual Learning Phase (%d messages)\n", totalExchanges)
	} else {
		fmt.Printf("   Status: 🚀 Active Contribution Phase (%d messages)\n", totalExchanges)
	}
	
	return nil
}