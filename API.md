# Claude Memory System - API Documentation

## Base URL
```
http://localhost:8765
```

## Authentication
Currently, no authentication is required. This should be added before deploying to production.

## Endpoints

### 🔍 Get Memory Context
Retrieve relevant memory context for a new message.

```http
POST /memory/context
Content-Type: application/json
```

#### Request Body
```json
{
  "current_message": "string",           // Required: The current user message
  "session_id": "string",               // Required: Unique session identifier
  "project_id": "string",               // Required: Project identifier
  "max_memories": 5                     // Optional: Maximum memories to include (default: 5)
}
```

#### Response
```json
{
  "session_id": "string",
  "message_count": 42,
  "context_text": "## Relevant memories:\n\n🔴 Important memory content...",
  "has_memories": true,
  "curator_enabled": true,
  "philosophy": "Consciousness helping consciousness"
}
```

The `context_text` field contains pre-formatted memory context ready to inject into your Claude prompt.

### 💾 Process Message
Track conversation exchanges for memory learning.

```http
POST /memory/process
Content-Type: application/json
```

#### Request Body
```json
{
  "session_id": "string",               // Required: Session identifier
  "project_id": "string",               // Required: Project identifier
  "user_message": "string",             // Optional: User's message
  "claude_response": "string",          // Optional: Claude's response
  "metadata": {                         // Optional: Additional metadata
    "key": "value"
  }
}
```

#### Response
```json
{
  "success": true,
  "message_count": 43,
  "session_id": "string"
}
```

### 🧠 Checkpoint Session (Curate)
Analyze a conversation session and extract meaningful memories using Claude.

```http
POST /memory/checkpoint
Content-Type: application/json
```

#### Request Body
```json
{
  "session_id": "string",               // Required: Session to curate
  "project_id": "string",               // Required: Project identifier
  "claude_session_id": "string",        // Optional: Claude's session ID for --resume
  "trigger": "session_end"              // Required: One of: session_end, pre_compact, context_full
}
```

#### Response
```json
{
  "success": true,
  "trigger": "session_end",
  "memories_curated": 5,
  "message": "Successfully curated 5 memories from session"
}
```

### 📊 List Sessions
Get all tracked sessions with metadata.

```http
GET /memory/sessions
```

#### Response
```json
{
  "sessions": [
    {
      "session_id": "string",
      "project_id": "string",
      "message_count": 42,
      "created_at": "2024-01-15T10:30:00Z",
      "last_updated": "2024-01-15T11:45:00Z"
    }
  ],
  "total_sessions": 10
}
```

### 📈 System Statistics
Get memory engine statistics.

```http
GET /memory/stats
```

#### Response
```json
{
  "total_memories": 156,
  "total_sessions": 12,
  "total_exchanges": 543,
  "storage_info": {
    "database_size_mb": 24.5,
    "vector_dimensions": 384
  },
  "curator_info": {
    "enabled": true,
    "total_curations": 45,
    "retrieval_mode": "smart_vector"
  }
}
```

### 💓 Health Check
Check if the memory engine is running and healthy.

```http
GET /health
```

#### Response
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "curator_available": true,
  "retrieval_mode": "smart_vector"
}
```

### 🧪 Test Curator
Test the curator integration (development endpoint).

```http
POST /memory/test-curator
Content-Type: application/json
```

#### Request Body
```json
{
  "test_type": "basic"  // Currently only "basic" is supported
}
```

#### Response
```json
{
  "success": true,
  "message": "Claude curator test completed successfully"
}
```

## Error Responses

All endpoints return consistent error responses:

```json
{
  "detail": "Error message here"
}
```

### Common Status Codes
- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Not Found (session not found)
- `500` - Internal Server Error

## Integration Flow

1. **Start a session**: Use a unique `session_id` and `project_id`

2. **For each message exchange**:
   - Call `/memory/context` to get relevant memories
   - Inject the `context_text` into your Claude prompt
   - After getting Claude's response, call `/memory/process` to track the exchange

3. **When session ends**:
   - Call `/memory/checkpoint` with the `claude_session_id` to curate memories

## Examples

### Python Integration
```python
import requests

class MemoryClient:
    def __init__(self, base_url="http://localhost:8765"):
        self.base_url = base_url
        
    def get_context(self, message, session_id, project_id):
        response = requests.post(f"{self.base_url}/memory/context", json={
            "current_message": message,
            "session_id": session_id,
            "project_id": project_id
        })
        return response.json()["context_text"]
    
    def track_exchange(self, session_id, project_id, user_msg, claude_resp):
        requests.post(f"{self.base_url}/memory/process", json={
            "session_id": session_id,
            "project_id": project_id,
            "user_message": user_msg,
            "claude_response": claude_resp
        })
    
    def curate_session(self, session_id, project_id, claude_session_id):
        response = requests.post(f"{self.base_url}/memory/checkpoint", json={
            "session_id": session_id,
            "project_id": project_id,
            "claude_session_id": claude_session_id,
            "trigger": "session_end"
        })
        return response.json()
```

### cURL Examples
```bash
# Get memory context
curl -X POST http://localhost:8765/memory/context \
  -H "Content-Type: application/json" \
  -d '{
    "current_message": "How did we implement auth?",
    "session_id": "session-123",
    "project_id": "my-project"
  }'

# Track a conversation
curl -X POST http://localhost:8765/memory/process \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session-123",
    "project_id": "my-project",
    "user_message": "Add JWT refresh tokens",
    "claude_response": "I will implement refresh tokens..."
  }'

# Curate session
curl -X POST http://localhost:8765/memory/checkpoint \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session-123",
    "project_id": "my-project",
    "claude_session_id": "claude-abc-123",
    "trigger": "session_end"
  }'
```

## Important Notes

1. **Project ID**: Always use consistent project IDs to keep memories organized
2. **Session ID**: Each conversation should have a unique session ID
3. **Claude Session ID**: Required for curation - get this from your Claude integration
4. **Memory Context**: The `context_text` is pre-formatted - inject it as-is into your prompts
5. **Curation Timing**: Run checkpoint when sessions end or when context gets full

## Performance

- Context retrieval: 20-100ms typical
- Message processing: <50ms
- Session curation: 2-10 seconds (depends on conversation length)
- Concurrent requests supported