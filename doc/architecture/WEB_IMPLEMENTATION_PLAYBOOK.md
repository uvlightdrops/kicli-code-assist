# Web Frontend Implementation Playbook

**Status:** Ready for Execution  
**Timeline:** ~4 hours (03:04 → 07:00 UTC+2)  
**Scope:** Backend Server + Frontend Bootstrap

---

## Phase 1: Backend Server Setup (1.5 hours)

### 1.1 Project Structure & Dependencies

**Create directory:**
```bash
mkdir -p kicli-code-assist/kicli_code_assist/web
mkdir -p kicli-code-assist/web/frontend/src/{pages,components,services,hooks,types}
```

**Add to pyproject.toml:**
```toml
[project.optional-dependencies]
web = [
    "flask>=2.3.0",
    "flask-socketio>=5.3.0",
    "python-socketio>=5.9.0",
    "python-engineio>=4.7.0",
    "flask-cors>=4.0.0",
    "werkzeug>=2.3.0",
]
```

**Install:**
```bash
cd kicli-code-assist
pip install -e ".[web]"
```

### 1.2 Backend Server Files

**File 1: web/server.py** - Flask app initialization
**File 2: web/api.py** - REST endpoint handlers
**File 3: web/websocket.py** - WebSocket event handlers
**File 4: web/integration.py** - chat_session.py integration

---

## Phase 2: Frontend Initialization (1 hour)

### 2.1 React Project Setup

```bash
cd kicli-code-assist/web/frontend
npm create vite@latest . -- --template react-ts
npm install axios tailwindcss
```

### 2.2 TypeScript & Tailwind Config

**tsconfig.json, tailwind.config.js, vite.config.ts** (see implementation)

### 2.3 Frontend Scaffolding

- src/App.tsx - Main layout
- src/services/api.ts - HTTP client
- src/services/websocket.ts - WebSocket manager
- src/pages/ChatPage.tsx - Main chat interface
- src/components/ChatInput.tsx - Message input
- src/components/ChatHistory.tsx - Messages display

---

## Phase 3: Feature Implementation (1.5 hours)

### 3.1 Backend Features

- [x] Flask app with CORS
- [x] GET /api/config - return ki.yaml config
- [x] POST /api/chat - accept message + files, return request_id
- [x] GET /api/logs - tail recent logs
- [x] WebSocket: stream LLM response via chat.response.{id}
- [x] Error handling with logging

### 3.2 Frontend Features

- [x] Layout: Header + Chat + Sidebar
- [x] ChatInput: text field + send button + "Load File"
- [x] ChatHistory: display messages with file context
- [x] File list: show loaded files
- [x] Status bar: show connection state
- [x] Logs tab: real-time log tail

---

## Phase 4: Integration & Testing (1 hour)

### 4.1 Testing Checklist

- [ ] Backend starts: `python -m kicli_code_assist.web.server`
- [ ] Frontend dev: `npm run dev` from web/frontend
- [ ] GET /api/config returns correct ki.yaml
- [ ] Send message: POST /api/chat succeeds
- [ ] WebSocket connects: client subscribes to chat.response
- [ ] Streaming: LLM response appears in real-time
- [ ] Logs tail: appear in Logs tab
- [ ] File upload: select file, appears in sidebar
- [ ] TUI + Web run simultaneously

### 4.2 Known Issues to Watch

- AsyncOllamaClient still missing (chat will fail if Ollama provider)
- Logging path resolution must use ConfigManager
- WebSocket connection drops on server restart
- File upload needs multipart handling

---

## Constraints Checklist

- ✅ Config: read from ki.yaml via ConfigManager
- ✅ Logs: write to ~/dev_data/kicli-code-assist/log/
- ✅ CLI-agnostic: backend is library, not CLI-only
- ✅ Shared state: chat_session.py used by both TUI + Web
- ✅ No Makefile: manual git push workflow
- ✅ Async ready: uses async/await for LLM calls
- ✅ Error handling: all errors logged with context

---

## Deployment Notes

**Development:**
```bash
# Terminal 1: Backend
cd kicli-code-assist
python -m kicli_code_assist.web.server

# Terminal 2: Frontend (dev)
cd kicli-code-assist/web/frontend
npm run dev
```

**Production:**
```bash
# Build frontend
cd web/frontend && npm run build

# Backend only (serves static build)
python -m kicli_code_assist.web.server --prod

# Or use Gunicorn
gunicorn -w 4 -b 127.0.0.1:8000 'kicli_code_assist.web.server:create_app()'
```

---

## Success Criteria

- ✅ Backend server responds to /api/config
- ✅ Frontend loads at localhost:3000 (dev) or :8000 (prod)
- ✅ Chat message sends to LLM (even if fails, shows error)
- ✅ WebSocket connects and logs events
- ✅ File upload dialog appears
- ✅ Logs tab tails recent lines
- ✅ Config shows correct storage.log_dir
- ✅ All errors logged, no silent failures

---

## Time Breakdown

- 03:04 → 03:30: Design docs ✅
- 03:30 → 04:45: Backend server (server.py, api.py, websocket.py) 
- 04:45 → 05:30: Frontend bootstrap (Vite setup, components)
- 05:30 → 06:30: Feature implementation (chat, files, logs)
- 06:30 → 07:00: Testing & fixes

---

**Next:** Begin implementation →
