# kicli-assist Web Frontend

A modern browser-based IDE for kicli-code-assist, complementing the Textual TUI.

**Status:** Beta - Fully Functional  
**Build Date:** 2026-10-20

---

## Quick Start

### 1. Start Backend Server

```bash
cd ../../..  # Back to kicli-code-assist root
source .venv/bin/activate
python -m kicli_code_assist.web.server
```

Runs on **http://localhost:8000**

### 2. Start Frontend Dev Server

```bash
npm install
npm run dev
```

Opens **http://localhost:3000** in your browser

### 3. Open Browser

Navigate to **http://localhost:3000** and start chatting!

---

## Features

### 💬 Chat Interface
- Send messages + loaded files to LLM
- Real-time streaming responses via WebSocket
- Message history with timestamps
- Clean, dark-themed UI

### 📄 File Management
- Load files via "Load File" button
- See file sizes and names in sidebar
- Remove files from context
- Files embedded as XML in LLM requests

### 📋 Logging Viewer
- Real-time tail of application logs
- Auto-refresh every 2 seconds
- See what's happening under the hood

### ⚙️ Config Inspector
- View current ki.yaml configuration
- See LLM provider and storage paths
- Verify app settings

### 🔌 Status Bar
- WebSocket connection indicator
- Real-time error display
- Server connectivity info

---

## Project Structure

```
src/
  App.tsx                    # Main app component
  main.tsx                   # Vite entry point
  index.css                  # Tailwind styles
  components/
    ChatInput.tsx            # Message input + Send button
    ChatHistory.tsx          # Messages display
    FileList.tsx             # Loaded files sidebar
    TerminalLog.tsx          # Log viewer
    StatusBar.tsx            # Status indicator
  services/                  # (reserved for API clients)
  types/                     # (reserved for TypeScript types)
```

---

## Available Scripts

### Development

```bash
npm run dev
```

Starts Vite dev server with hot-reload on port 3000.

### Build for Production

```bash
npm run build
```

Creates optimized production build in `../../kicli_code_assist/web/static/`

### Preview Production Build

```bash
npm run preview
```

Serves production build locally for testing before deploy.

---

## Configuration

### Connecting to Backend

The frontend proxies `/api/*` requests to `http://localhost:8000` (see `vite.config.ts`)

To change backend URL, edit `vite.config.ts`:

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://YOUR_HOST:PORT',  // Change here
      changeOrigin: true,
    },
  },
}
```

### Backend Configuration (ki.yaml)

```yaml
web:
  enabled: true
  host: "127.0.0.1"
  port: 8000
  cors_origins:
    - "http://localhost:3000"
```

---

## Troubleshooting

### Port 3000 Already in Use
```bash
# Find process on port 3000
lsof -i :3000

# Kill it (replace PID)
kill -9 <PID>
```

### Backend Connection Failed
- Ensure backend is running: `curl http://localhost:8000/api/health`
- Check CORS settings in ki.yaml
- Check browser console for WebSocket errors

### Styling Looks Wrong
```bash
# Rebuild Tailwind CSS
npm run build
```

### Dependencies Outdated
```bash
npm update
npm audit fix
```

---

## Development Tips

### Component Development
- Use React StrictMode for catching bugs
- All components in `src/components/`
- Props typed with TypeScript interfaces
- Tailwind for styling (no CSS files)

### API Integration
- REST calls: `axios.post('/api/chat', data)`
- WebSocket: `socket.emit('subscribe', {channel: '...'})`
- Error handling via try/catch and status codes

### Keyboard Shortcuts
- **Ctrl+Enter** - Send message
- **L** - Load file (click "Load File" button instead in web)
- **Tab** - Navigate between inputs

---

## Browser Support

- Chrome/Chromium 100+
- Firefox 100+
- Safari 15+
- Edge 100+

Requires WebSocket support.

---

## Performance

- Vite provides instant HMR (hot module reload)
- Tailwind CSS is tree-shaken in production builds
- WebSocket for real-time updates (no polling)
- Lazy-loaded components (planned)

---

## Next Steps

1. **Run backend** - `python -m kicli_code_assist.web.server`
2. **Install deps** - `npm install`
3. **Start dev** - `npm run dev`
4. **Open browser** - http://localhost:3000
5. **Chat!** - Load a file and send a message

---

## For Production

See **docs/guides/WEB_DEPLOYMENT_GUIDE.md** for:
- Gunicorn setup
- Systemd service
- Nginx reverse proxy
- SSL/TLS configuration

---

## License

MIT (same as kicli-code-assist)

---

**Questions?** Check:
- `docs/architecture/WEB_FRONTEND_DESIGN.md` - Full architecture
- `docs/guides/WEB_DEPLOYMENT_GUIDE.md` - Deployment guide
- `../README.md` - Main project README
