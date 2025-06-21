package memory

import (
	"encoding/json"
	"os"
	"path/filepath"
	"time"
)

// ProjectState tracks memory system state for a project directory
type ProjectState struct {
	FirstSessionCompleted bool      `json:"first_session_completed"`
	LastSessionID         string    `json:"last_session_id"`
	LastCurationTime      time.Time `json:"last_curation_time"`
	ProjectName           string    `json:"project_name"`
	MemoryVersion         string    `json:"memory_version"`
	// Future fields can be added here without breaking compatibility
}

const projectStateFile = ".claude-memory-state.json"

// LoadProjectState loads the project state from the current directory
func LoadProjectState() (*ProjectState, error) {
	data, err := os.ReadFile(projectStateFile)
	if err != nil {
		if os.IsNotExist(err) {
			// First time in this project
			cwd, _ := os.Getwd()
			return &ProjectState{
				FirstSessionCompleted: false,
				ProjectName:           filepath.Base(cwd),
				MemoryVersion:         "0.1.0",
			}, nil
		}
		return nil, err
	}

	var state ProjectState
	if err := json.Unmarshal(data, &state); err != nil {
		return nil, err
	}

	return &state, nil
}

// SaveProjectState saves the project state to the current directory
func (ps *ProjectState) Save() error {
	data, err := json.MarshalIndent(ps, "", "  ")
	if err != nil {
		return err
	}

	return os.WriteFile(projectStateFile, data, 0644)
}

// MarkFirstSessionCompleted updates the state after first session
func (ps *ProjectState) MarkFirstSessionCompleted(sessionID string) {
	ps.FirstSessionCompleted = true
	ps.LastSessionID = sessionID
	ps.LastCurationTime = time.Now()
}