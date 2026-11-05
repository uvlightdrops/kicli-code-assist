# Web Frontend für kicli-code-assist

**Status:** Architecture & Design Phase  
**Version:** 1.0  
**Date:** 2026-10-20  
**Scope:** Parallel web-based IDE to complement Textual TUI

---

## Executive Summary

Implement a web-based IDE (React + Flask) running alongside the existing Textual TUI. Both frontends share:
- Unified **ki-core** backend services (config, LLM, validation)
- Same **chat_session.py** message management
- Consistent logging to `~/dev_data/kicli-code-assist/log/`
- Config-driven endpoints and storage paths

**Key Benefit:** Avoid Textual widget limitations while maintaining feature parity.

---

## 1. Architecture Overview

### 1.1 Component Stack

```
┌─────────────────────────────────────────────────┐
│  Web Frontend (React + TypeScript)              │
│  - Chat UI with file loading                    │
│  - Terminal/Logging viewer                      │
│  - Config inspector                             │
│  - Real-time WebSocket updates                  │
└──────────────────┬──────────────────────────────┘
                   │ HTTP/WebSocket (localhost:8000)
┌──────────────────▼──────────────────────────────┐
│  Backend Server (Flask + Python)                │
│  - REST API endpoints (/api/chat, /api/config) │
│  - WebSocket handler for streaming responses   │
│  - File upload/download                        │
│  - Logging aggregation                         │
└──────────────────┬──────────────────────────────┘
                   │ (direct imports)
┌──────────────────▼──────────────────────────────┐
│  Shared Services (Python)                       │
│  - kicli_code_assist.chat_session.ChatSession   │
│  - kicli_code_assist.logging_integration        │
│  - ki_core.config.ConfigManager                │
│  - ki_core.adapters (Ollama, OpenAI)           │
└─────────────────────────────────────────────────┘
```

### 1.2 Deployment Model

- **Single Process:** Flask server runs in same container/machine as TUI
- **Port:** Configurable via `web.port` in ki.yaml (default: 8000)
- **Shared State:** Both TUI and Web can run simultaneously, sharing chat history
- **Logs:** All logs written to `~/dev_data/kicli-code-assist/log/`
- **Config:** Both read from same ki.yaml location

---

## 2. Config System Integration

### 2.1 Schema Extensions (kicli.schema.yaml)

Add new section:

```yaml
web:
  enabled: true                    # Enable/disable web frontend
  host: "127.0.0.1"              # Bind address
  port: 8000                       # HTTP port
  cors_origins: ["http://localhost:3000"]  # dev/prod origins
  max_upload_size_mb: 50          # File upload limit
```

### 2.2 Config Loading in Backend

```python
from ki_core.config import ConfigManager

config = ConfigManager()
app_config = config.load()

web_config = app_config.get('web', {})
FLASK_HOST = web_config.get('host', '127.0.0.1')
FLASK_PORT = web_config.get('port', 8000)
```

---

## 3. Backend API Specification

### 3.1 Core Endpoints

#### POST /api/chat
**Send message to LLM with loaded files**

Request:
```json
{
  "message": "Explain this code",
  "files": [
    {"path": "/path/to/file.py", "content": "..."}
  ]
}
```

Response (immediate):
```json
{
  "request_id": "uuid",
  "status": "processing"
}
```

Then stream via WebSocket `chat.response.{request_id}`

#### GET /api/config
**Fetch current configuration**

Response:
```json
{
  "storage": {"log_dir": "/home/user/dev_data/kicli-code-assist/log"},
  "llm": {"provider": "ollama", "model": "codellama"},
  "web": {"port": 8000}
}
```

#### GET /api/logs
**Fetch recent log entries**

Query params: `?lines=100&level=INFO`

Response:
```json
{
  "logs": [
    {"timestamp": "2026-10-20T01:00:00", "level": "INFO", "message": "Chat started"}
  ]
}
```

#### POST /api/files/upload
**Upload file to context**

Multipart form-data: `file` + `path` (optional)

Response:
```json
{
  "file_id": "uuid",
  "path": "/uploaded/filename",
  "size_bytes": 1024
}
```

#### GET /api/files/{file_id}
**Download uploaded file**

#### DELETE /api/files/{file_id}
**Remove file from context**

### 3.2 WebSocket Events

**Connect:** `ws://localhost:8000/ws/chat`

**Client → Server:**
```json
{
  "type": "subscribe",
  "channel": "chat.response.{request_id}"
}
```

**Server → Client (streaming):**
```json
{
  "type": "chunk",
  "request_id": "uuid",
  "content": "partial response text"
}
```

```json
{
  "type": "complete",
  "request_id": "uuid",
  "status": "success"
}
```

```json
{
  "type": "error",
  "request_id": "uuid",
  "error": "LLM connection failed"
}
```

---

## 4. Frontend Architecture

### 4.1 Component Structure

```
src/
  pages/
    ChatPage.tsx          # Main IDE view
    ConfigPage.tsx        # Settings inspector
    LogsPage.tsx          # Log viewer
  components/
    ChatInput.tsx         # Message input + file loader
    ChatHistory.tsx       # Message history display
    FileList.tsx          # Loaded files sidebar
    TerminalLog.tsx       # Real-time log viewer
    StatusBar.tsx         # Connection status
  hooks/
    useChat.ts            # Chat API calls + WS subscription
    useConfig.ts          # Config fetch/cache
    useLogs.ts            # Log streaming
  services/
    api.ts                # HTTP client
    websocket.ts          # WebSocket manager
  types/
    api.ts                # API types
```

### 4.2 Key Features

1. **Chat Interface**
   - Message input with Ctrl+Enter to send
   - "Load File" dialog (keyboard shortcut L)
   - Streaming response display
   - File context shown inline (like Textual)

2. **Sidebar**
   - Loaded files with delete button
   - Quick config view
   - Connection status indicator

3. **Terminal Tab**
   - Real-time log tail (refreshes via WebSocket)
   - Filter by level (DEBUG, INFO, WARN, ERROR)
   - Search functionality

4. **Config Inspector**
   - Read-only display of current config
   - Show which file was loaded from
   - Environment overrides highlighted

---

## 5. Implementation Phases

### Phase 1: Backend Server (Day 1)
- [ ] Flask app structure
- [ ] REST endpoints (/api/chat, /api/config, /api/logs)
- [ ] WebSocket for streaming chat responses
- [ ] Integration with chat_session.py
- [ ] Error handling + logging

### Phase 2: Frontend Structure (Day 1)
- [ ] React project setup (Vite)
- [ ] TypeScript config
- [ ] Component scaffolding
- [ ] API/WebSocket client libraries

### Phase 3: Feature Implementation (Day 2)
- [ ] Chat input + send (via REST)
- [ ] File upload/manage
- [ ] WebSocket response streaming
- [ ] Logging viewer
- [ ] Config inspector

### Phase 4: Integration & Testing (Day 2)
- [ ] Run TUI + Web simultaneously
- [ ] End-to-end chat flow
- [ ] Error handling verification
- [ ] Log aggregation

---

## 6. Tech Stack Rationale

| Layer | Choice | Why |
|-------|--------|-----|
| Backend HTTP | **Flask** | Lightweight, Python, integrates with ki-core |
| Backend WebSocket | **Flask-SocketIO** | Real-time streaming, integrates with Flask |
| Frontend Framework | **React + TypeScript** | Modern, type-safe, large ecosystem |
| Frontend Build | **Vite** | Fast dev server, minimal config |
| Frontend HTTP | **Axios/Fetch** | Simple async calls to Flask |
| Styling | **Tailwind CSS** | Rapid UI development, consistent design |
| Deployment | **Single process** | No Docker/containers initially (per deployment notes) |

---

## 7. Configuration & Startup

### 7.1 Starting Backend

```bash
cd kicli-code-assist
python -m kicli_code_assist.web.server
```

- Reads config from ~/current_working_dir/ki.yaml (or default)
- Logs to ~/dev_data/kicli-code-assist/log/kicli-web.log
- Listens on 127.0.0.1:8000 (configurable)

### 7.2 Starting Frontend

```bash
cd kicli-code-assist/web/frontend
npm run dev
```

- Dev server on localhost:3000
- Proxies /api to localhost:8000
- Hot-reload on file changes

### 7.3 Parallel Execution

```bash
# Terminal 1: TUI
cd kicli-code-assist && kicli-assist tui

# Terminal 2: Web Backend
cd kicli-code-assist && python -m kicli_code_assist.web.server

# Terminal 3: Web Frontend (dev)
cd kicli-code-assist/web/frontend && npm run dev
```

Both can run simultaneously, sharing chat_session.py state.

---

## 8. Constraints & Decisions

### 8.1 Constraints Honored

✅ Config-driven (ki.yaml respects storage.log_dir)  
✅ Logs always to ~/dev_data/kicli-code-assist/log/  
✅ No hardcoded paths (use ConfigManager)  
✅ No Makefile (manual git push workflow)  
✅ Python-only backend (no JS backend frameworks)  
✅ Shared ki-core services (not duplicated)  
✅ Async LLM support (ready for AsyncOllamaClient)  

### 8.2 Design Decisions

1. **Single Port Binding:** Flask handles both REST + WebSocket (simpler than separate servers)
2. **File Context:** Same embedding format as Textual (XML `<file>...</file>`)
3. **Message History:** Shared chat_session.py means TUI + Web see same messages
4. **Stateless Backend:** Each request is independent; session state in Python objects
5. **Minimal Frontend Dependencies:** Use vanilla JS where possible, React only for complex UI

---

## 9. Error Handling Strategy

### 9.1 Error Propagation

```
Frontend Error → HTTP 4xx/5xx → Client catches → UI shows toast
             → WebSocket error event → UI reconnect logic
             → Log viewer shows error lines
```

### 9.2 Logging Levels

- **DEBUG:** WebSocket messages, API calls, config loading
- **INFO:** Chat started, file uploaded, config changed
- **WARNING:** LLM timeout, connection retried
- **ERROR:** LLM failed, file not found, config invalid

All written to:
- `~/dev_data/kicli-code-assist/log/kicli-web.log` (Flask requests)
- `~/dev_data/kicli-code-assist/log/kicli-llm.log` (LLM calls)

---

## 10. Future Enhancements

- Persistent chat history (database)
- User authentication
- Multiple projects/contexts
- Code syntax highlighting
- Auto-complete from loaded files
- Export chat to markdown
- Collaborative editing (multi-user)

---

## 11. Success Criteria

- [ ] Backend server starts without errors
- [ ] Web frontend loads at localhost:3000
- [ ] Chat submission sends message + files to LLM
- [ ] Streaming response displays in real-time
- [ ] Logs visible in web UI (same as TUI)
- [ ] Config inspector shows correct paths
- [ ] TUI and Web run simultaneously, sharing state
- [ ] All errors logged to ~/dev_data/... 
- [ ] No hardcoded paths anywhere

---

## Appendix A: File Structure

```
kicli-code-assist/
├── kicli_code_assist/
│   ├── web/
│   │   ├── __init__.py
│   │   ├── server.py          # Flask app + routes
│   │   ├── api.py             # Endpoint handlers
│   │   ├── websocket.py       # SocketIO handlers
│   │   └── integration.py     # chat_session integration
│   ├── chat_session.py        # (shared)
│   ├── logging_integration.py # (shared)
│   └── ui/
│       └── app.py             # (Textual, unchanged)
├── web/
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── pages/
│   │   │   ├── components/
│   │   │   ├── services/
│   │   │   ├── types/
│   │   │   └── App.tsx
│   │   ├── package.json
│   │   ├── vite.config.ts
│   │   └── tsconfig.json
│   └── README.md
└── docs/
    └── architecture/
        └── WEB_FRONTEND_DESIGN.md (this file)
```

---

**Next Step:** Begin implementation Phase 1 (Backend Server)
