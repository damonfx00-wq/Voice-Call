# Conversation Memory System

## Overview
The Voice Call AI Assistant now includes a persistent conversation memory system that allows conversations to continue across multiple calls. Each conversation is stored in a session that persists on disk.

## Features

### 1. **Session-Based Memory**
- Each conversation is assigned a unique session ID
- Sessions are automatically created on first message
- Sessions persist across application restarts

### 2. **Conversation Continuity**
- The AI remembers previous parts of the conversation
- You can end a call and resume the conversation later
- Session ID is maintained across multiple calls

### 3. **Persistent Storage**
- Conversations are saved to disk in JSON format
- Location: `backend/data/conversations/`
- Each session file contains full conversation history with timestamps

## How It Works

### Backend
1. **ConversationMemory Class** (`app/memory/conversation_memory.py`)
   - Manages session creation, retrieval, and deletion
   - Stores conversations as JSON files
   - Provides formatted history for LLM API calls

2. **IntelligentAgent** (`app/agents/agent.py`)
   - Automatically loads conversation history on initialization
   - Saves every message (user and assistant) to memory
   - Supports resuming conversations via session_id

3. **API Endpoints**
   - `POST /api/chat` - Chat with session management
   - `GET /api/sessions` - List all sessions
   - `GET /api/sessions/{session_id}` - Get session details
   - `DELETE /api/sessions/{session_id}` - Delete a session

### Frontend
1. **Session State Management**
   - Session ID is stored in component state
   - Automatically sent with each chat request
   - Persists across multiple calls (until page refresh)

2. **Intro Greeting**
   - AI speaks an intro greeting when mic is first activated
   - Greeting is only spoken once per call session

## API Usage

### Chat with Session Management
```typescript
const response = await apiService.chat({
    message: "Hello!",
    session_id: "existing-session-id" // Optional - omit for new session
});

// Response includes session_id for future requests
console.log(response.session_id);
```

### List All Sessions
```typescript
const sessions = await apiService.listSessions();
// Returns array of session summaries with metadata
```

### Get Session Details
```typescript
const session = await apiService.getSession(sessionId);
// Returns full conversation history
```

### Delete Session
```typescript
await apiService.deleteSession(sessionId);
```

## Session Data Structure

```json
{
  "session_id": "uuid-v4",
  "user_id": "optional-user-id",
  "created_at": "2026-01-05T12:00:00",
  "updated_at": "2026-01-05T12:30:00",
  "conversation_history": [
    {
      "role": "user",
      "content": "Hello!",
      "timestamp": "2026-01-05T12:00:00"
    },
    {
      "role": "assistant",
      "content": "Hi! How can I help you?",
      "timestamp": "2026-01-05T12:00:05"
    }
  ],
  "metadata": {}
}
```

## Benefits

1. **Contextual Conversations**: The AI remembers what you discussed earlier
2. **Multi-Call Sessions**: End a call and resume later without losing context
3. **Conversation History**: Full audit trail of all interactions
4. **Scalable**: Each user can have multiple conversation sessions
5. **Privacy**: Sessions can be deleted when no longer needed

## Future Enhancements

- User authentication for session ownership
- Session search and filtering
- Conversation summaries
- Export conversations
- Session sharing
- Automatic session cleanup (old sessions)
