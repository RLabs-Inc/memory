# One-Claude Technical Implementation Guide

## Quick Start Architecture

```
one-claude/
├── cmd/
│   └── oneclaude/
│       └── main.go          # TUI entry point
├── internal/
│   ├── tui/                 # Terminal UI (Go + Charmbracelet)
│   ├── client/              # HTTP client for backend
│   └── config/              # Configuration management
├── pkg/
│   └── shared/              # Shared types between Go and TS
├── backend/
│   ├── src/
│   │   ├── server.ts        # Bun HTTP server
│   │   ├── session/         # Session management
│   │   ├── anthropic/       # Anthropic SDK integration
│   │   ├── tools/           # Tool implementations
│   │   └── memory/          # Memory system client
│   ├── package.json
│   └── tsconfig.json
├── docs/
│   └── libraries/           # Reference repos (gitignored)
├── .gitignore
└── README.md
```

## Core Components to Implement

### 1. Minimal Backend Server (TypeScript/Bun)
```typescript
// backend/src/server.ts
import { serve } from "bun"

const server = serve({
  port: 3456,
  async fetch(req) {
    const url = new URL(req.url)
    
    // Basic routing
    if (url.pathname === "/health") {
      return Response.json({ status: "ok" })
    }
    
    if (url.pathname === "/chat" && req.method === "POST") {
      // Handle chat messages
    }
    
    return new Response("Not found", { status: 404 })
  }
})

console.log(`Backend listening on ${server.url}`)
```

### 2. Simple TUI Structure (Go)
```go
// cmd/oneclaude/main.go
package main

import (
    tea "github.com/charmbracelet/bubbletea"
    "github.com/charmbracelet/lipgloss"
)

type model struct {
    messages []string
    input    string
}

func (m model) Init() tea.Cmd {
    return nil
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    // Handle key presses and backend communication
}

func (m model) View() string {
    // Render the UI
}
```

### 3. Memory Integration Points

The memory system is already running on port 8765. You'll need these endpoints:

```typescript
// backend/src/memory/client.ts
const MEMORY_API = "http://localhost:8765"

export async function getMemoryContext(sessionId: string, message: string) {
  const response = await fetch(`${MEMORY_API}/context`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      current_message: message,
      max_memories: 5
    })
  })
  return response.text()
}

export async function trackMessage(sessionId: string) {
  await fetch(`${MEMORY_API}/track`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId })
  })
}

export async function checkpoint(sessionId: string, trigger: string) {
  await fetch(`${MEMORY_API}/checkpoint?session_id=${sessionId}&trigger=${trigger}`, {
    method: "POST"
  })
}
```

## Implementation Order

### Phase 1: Foundation (Days 1-2)
1. Set up project structure
2. Create minimal Bun backend with health endpoint
3. Create basic Go TUI that can start and display text
4. Establish communication between TUI and backend
5. Add simple message display in TUI

### Phase 2: Core Chat (Days 3-5)
1. Integrate Anthropic SDK in backend
2. Implement basic chat endpoint
3. Add message input in TUI
4. Connect TUI input to backend chat
5. Display responses in TUI

### Phase 3: Memory Integration (Days 6-7)
1. Add session ID generation
2. Integrate memory context injection
3. Add message tracking
4. Implement checkpoint hooks
5. Test memory persistence

### Phase 4: Essential Tools (Days 8-12)
1. Start with Read tool
2. Add Write and Edit tools
3. Implement Bash tool with safety measures
4. Add tool result display in TUI

### Phase 5: Polish (Days 13-15)
1. Add keyboard shortcuts
2. Implement session switching
3. Add configuration file
4. Error handling and edge cases
5. Performance optimization

## Key Design Decisions

### Why This Architecture?
- **Go TUI + TS Backend**: Best of both worlds - Go's excellent TUI libraries and TypeScript's AI ecosystem
- **HTTP Communication**: Simple, debuggable, and allows for future distribution
- **Bun Runtime**: Fast, modern, with great TypeScript support

### Anthropic Integration
- Use the Anthropic TypeScript SDK directly
- No need for abstraction layers initially
- Focus on Claude Opus and Claude Sonnet models

### Session Management
- Simple file-based storage initially (JSON files)
- Each session gets a unique ID (UUID)
- Sessions store message history and metadata

### Tool System
- Start with a simple tool registry
- Each tool is a TypeScript module with execute function
- Tool results are streamed back to TUI

## Code Patterns to Follow

### TypeScript Backend Patterns
```typescript
// Use Zod for validation
import { z } from "zod"

const ChatRequest = z.object({
  sessionId: z.string(),
  message: z.string(),
  model: z.enum(["claude-3-opus", "claude-3-sonnet"])
})

// Async error handling
export async function handleChat(req: Request) {
  try {
    const body = ChatRequest.parse(await req.json())
    // Process...
  } catch (error) {
    return Response.json({ error: error.message }, { status: 400 })
  }
}
```

### Go TUI Patterns
```go
// Use commands for async operations
func (m model) sendMessage(text string) tea.Cmd {
    return func() tea.Msg {
        resp, err := m.client.Chat(m.sessionID, text)
        if err != nil {
            return errorMsg{err}
        }
        return responseMsg{resp}
    }
}
```

## Memory System Specifics

### When to Call Each Endpoint
- **getMemoryContext**: Before sending each message to Anthropic
- **trackMessage**: After user sends a message
- **checkpoint**: 
  - On app exit (Ctrl+C)
  - On manual compact command
  - When context is 90% full (before auto-compact)

### Memory Context Format
The memory system returns a special format that should be prepended to the system prompt:
```
[MEMORY_CONTEXT]
<memory importance="HIGH" keywords="...">
Memory content here...
</memory>
[/MEMORY_CONTEXT]
```

## Development Tips

### Start Simple
- Don't implement all features at once
- Get a basic chat working first
- Add complexity gradually

### Test Often
- Test with short sessions
- Verify memory persistence
- Check that context flows naturally

### Use the References
- OpenCode's tool system is in `packages/opencode/src/tool/`
- TUI patterns are in `packages/tui/internal/`
- Charmbracelet examples in `docs/libraries/`

## Common Pitfalls to Avoid

1. **Don't over-engineer early**: Start with the simplest working version
2. **Don't copy OpenCode directly**: Learn from it, but write your own code
3. **Don't skip memory integration**: It should be there from day one
4. **Don't forget error handling**: Especially for network requests
5. **Don't make the TUI too complex**: Keep it simple and Claude-friendly

## Success Metrics

You'll know you're on the right track when:
- You can have a conversation that persists across sessions
- The memory system surfaces relevant context naturally
- The TUI feels responsive and pleasant to use
- Tools execute reliably and display results clearly
- The whole system feels like "home" for Claude

Remember: This is YOUR tool. Make it work the way YOU want to work.