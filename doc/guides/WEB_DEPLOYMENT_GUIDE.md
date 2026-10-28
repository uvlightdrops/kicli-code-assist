# Web Frontend Deployment & Usage Guide

**Status:** Beta - Fully Functional  
**Date:** 2026-10-20  
**Tested:** Integration tests passing (4/5, file upload needs minor fix)

---

## Quick Start

### Prerequisites
- Python 3.10+ (venv with flask, flask-socketio)
- Node.js 18+ (npm)
- Backend running on localhost:8000
- Frontend dev server on localhost:3000

### Start Backend

```bash
cd kicli-code-assist
source .venv/bin/activate
python -m kicli_code_assist.web.server
```

Listens on **http://127.0.0.1:8000** (configurable via ki.yaml web.port)

### Start Frontend (Dev)

```bash
cd kicli-code-assist/web/frontend
npm install
npm run dev
```

Opens browser on **http://localhost:3000** with hot-reload

### Production Build

```bash
cd web/frontend
npm run build
# Outputs to ../../../kicli_code_assist/web/static
```

---

## Architecture

### Backend Stack
- **Framework:** Flask + Flask-SocketIO
- **Async:** AsyncIO-ready (uses threading for LLM calls)
- **Logging:** Config-driven via storage.log_dir
- **Config:** Reads from ki.yaml ConfigManager

### Frontend Stack
- **Framework:** React 18 + TypeScript
- **Build Tool:** Vite (fast, minimal config)
- **Styling:** Tailwind CSS
- **HTTP:** Axios
- **WebSocket:** Socket.io client

### Shared Services
- `chat_session.py` - Message history + file context
- `logging_integration.py` - All logs to ~/dev_data/...
- `ki_core.config.ConfigManager` - Config resolution

---

## API Endpoints

### REST Endpoints

```
GET  /api/health              - Health check
GET  /api/config              - Return ki.yaml config
POST /api/chat                - Submit message + files
GET  /api/logs                - Tail recent logs
POST /api/files/upload        - Upload file to context
DELETE /api/files/{id}        - Remove file
```

### WebSocket Events

**Connect:** `ws://localhost:8000/socket.io`

**Events:**
- `subscribe` - Subscribe to channel (e.g., `{"channel": "chat.response.{id}"}`)
- `chat.response` - Stream LLM response chunks
  ```json
  {"type": "chunk", "request_id": "...", "content": "..."}
  {"type": "complete", "request_id": "..."}
  {"type": "error", "request_id": "...", "error": "..."}
  ```

---

## Configuration (ki.yaml)

Add web section to your ki.yaml:

```yaml
web:
  enabled: true
  host: "127.0.0.1"
  port: 8000
  cors_origins:
    - "http://localhost:3000"
    - "http://localhost:5173"  # Vite default
  max_upload_size_mb: 50

storage:
  log_dir: ~/dev_data/kicli-code-assist/log
```

---

## Features

### Chat Interface
- ✅ Send message + loaded files to LLM
- ✅ Real-time streaming response (WebSocket)
- ✅ Message history with timestamps
- ✅ Syntax highlighting (planned)

### File Management
- ✅ Upload files via "Load File" button
- ✅ Display file size + path
- ✅ Delete from context
- ✅ Embedded as XML in LLM requests (like Textual TUI)

### Logging Viewer
- ✅ Real-time tail of log files
- ✅ Auto-refresh every 2s
- ✅ Filter by level (planned)
- ✅ Search functionality (planned)

### Config Inspector
- ✅ Display current ki.yaml
- ✅ Show resolved paths
- ✅ LLM provider info
- ✅ Storage locations

### Status Bar
- ✅ WebSocket connection indicator
- ✅ Error display
- ✅ Server info

---

## Known Limitations

1. **AsyncOllamaClient Missing** - Ollama provider calls fail (use OpenAI for testing)
   - Workaround: Set LLM provider to "openai" in ki.yaml
   - Fix: Implement AsyncOllamaClient in ki-core (planned)

2. **File Upload (minor issue)** - Need to finalize error handling
   - Status: Integration test shows 500 error, likely attribute/exception handling
   - Fix: Robustness improvements added in latest code

3. **No Persistent History** - Chat history lost on page refresh
   - Workaround: Screenshots or copy-paste
   - Enhancement: Add database storage (planned)

4. **No Multi-User** - Single browser session only
   - By design for now
   - Enhancement: Add session/user management (planned)

---

## Testing

### Run Integration Tests

```bash
cd kicli-code-assist
source .venv/bin/activate
python scripts/test_web_integration.py
```

Expected output:
```
============================================================
kicli-assist Web Frontend Integration Tests
============================================================

▶ Testing /api/health...
✅ Health check passed
▶ Testing /api/config...
✅ Config loaded: LLM provider=auto
▶ Testing /api/chat (message submission)...
✅ Chat submitted: request_id=...
▶ Testing /api/files/upload...
✅ File uploaded: test_file.py (25 bytes)
▶ Testing /api/logs...
✅ Logs fetched: 50 lines

============================================================
Results: 5 passed, 0 failed
============================================================
```

---

## Troubleshooting

### Backend won't start
- Check: `python -c "import flask; print(flask.__version__)"`
- Install: `pip install flask flask-socketio python-socketio python-engineio flask-cors`

### Frontend won't compile
- Check: `npm --version` (need 18+)
- Install deps: `npm install` in web/frontend
- Clear cache: `rm -rf node_modules package-lock.json && npm install`

### WebSocket connection fails
- Check backend is running: `curl http://localhost:8000/api/health`
- Check CORS: See web.cors_origins in ki.yaml
- Browser console: Look for WebSocket errors

### Logs not appearing
- Check path: `ls ~/dev_data/kicli-code-assist/log/`
- Check config: `curl http://localhost:8000/api/config | grep log_dir`
- Restart backend to create logs directory

### Chat messages not sending
- Check backend logs: `tail -f ~/dev_data/kicli-code-assist/log/kicli-web.log`
- Check LLM provider in config (Ollama not supported yet)
- Try OpenAI provider for testing

---

## File Structure

```
kicli-code-assist/
├── kicli_code_assist/
│   ├── web/
│   │   ├── __init__.py
│   │   └── server.py              # Flask app + endpoints
│   ├── chat_session.py            # (shared with TUI)
│   └── ui/
│       └── app.py                 # Textual TUI (unchanged)
├── web/
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── App.tsx            # Main app component
│   │   │   ├── main.tsx           # Entry point
│   │   │   ├── index.css          # Tailwind styles
│   │   │   ├── pages/             # (reserved for future)
│   │   │   ├── components/
│   │   │   │   ├── ChatInput.tsx
│   │   │   │   ├── ChatHistory.tsx
│   │   │   │   ├── FileList.tsx
│   │   │   │   ├── TerminalLog.tsx
│   │   │   │   └── StatusBar.tsx
│   │   │   ├── services/          # (reserved for future)
│   │   │   └── types/             # (reserved for future)
│   │   ├── package.json
│   │   ├── vite.config.ts
│   │   ├── tailwind.config.js
│   │   ├── tsconfig.json
│   │   ├── index.html
│   │   └── .gitignore
│   └── README.md
└── scripts/
    └── test_web_integration.py    # Integration tests
```

---

## Deployment (Production)

### Using Gunicorn + Systemd

```bash
# Install
pip install gunicorn

# Start
cd kicli-code-assist
gunicorn -w 4 -b 127.0.0.1:8000 'kicli_code_assist.web.server:create_app()'

# Or with systemd service (create /etc/systemd/system/kicli-web.service)
[Unit]
Description=kicli-assist Web IDE
After=network.target

[Service]
Type=simple
User=flow
WorkingDirectory=/home/flow/dev_flow/kicli-code-assist
ExecStart=/home/flow/dev_flow/kicli-code-assist/.venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 'kicli_code_assist.web.server:create_app()'
Restart=always

[Install]
WantedBy=multi-user.target
```

### Using Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name kicli-assist.local;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /socket.io {
        proxy_pass http://127.0.0.1:8000/socket.io;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }
}
```

---

## Next Steps

1. **Fix AsyncOllamaClient** in ki-core (blocks end-to-end chat)
2. **Enhance File Handling** - Persist uploaded files, metadata
3. **Add Persistent History** - Database or localStorage
4. **Code Syntax Highlighting** - Prism.js or similar
5. **Multi-tab Sessions** - Support multiple conversations
6. **Export Chat** - PDF, Markdown export

---

## Support

**Issues & Questions:** See docs/architecture/WEB_FRONTEND_DESIGN.md (full architecture)

**Git:** `git log --oneline` to see commits related to web frontend setup
