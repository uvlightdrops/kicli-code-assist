# stack.yaml Varianten für kicli-code-assist

## Kontext

kicli-code-assist hat 2 Teile:
- **Backend:** Flask Web-Server (kicli_code_assist/web/server.py) → Port 8000
- **Frontend:** React/TypeScript (web/frontend/) → Build in kicli_code_assist/web/static/

Abhängig vom Deployment-Szenario brauchen wir unterschiedliche Stacks.

---

## Variante 1: MINIMAL (nur Flask)

**Use-Case:** Production, TUI nur, oder Frontend schon separates Container

```yaml
stack:
  name: kicli-assist
  target: local
  
  services:
    web:
      kind: process
      command: ["{python}", "-m", "kicli_code_assist.web.server"]
      cwd: "{root}"
      host: 127.0.0.1
      port: 8000
      env:
        PYTHONUNBUFFERED: "1"
        KI_STAGE: "production"
      health_path: /api/health
      health_timeout: 10
      health_retries: 5
      health_interval: 2
      stdout_log: "log/web.log"
      stderr_log: "log/web.err.log"
```

**Pros:**
- ✅ Einfach, schnell zu starten
- ✅ Flask serviert auch Static Files aus `web/static/`
- ✅ Für TUI + Basic WebUI ausreichend

**Cons:**
- ❌ Kein HMR (Hot Module Reload)
- ❌ Frontend muss vorher gebaut sein (`npm run build`)

**Wann:** Semi-Prod, Production, TUI-only

---

## Variante 2: DEV (Flask + React HMR)

**Use-Case:** Local Development mit Live Reloading

```yaml
stack:
  name: kicli-assist-dev
  target: local
  
  services:
    # Backend API
    api:
      kind: process
      command: ["{python}", "-m", "kicli_code_assist.web.server"]
      cwd: "{root}"
      host: 127.0.0.1
      port: 8000
      env:
        PYTHONUNBUFFERED: "1"
        KI_STAGE: "development"
      health_path: /api/health
      health_timeout: 10
      health_retries: 5
      health_interval: 2
      stdout_log: "log/api.log"
      stderr_log: "log/api.err.log"
    
    # Frontend Dev Server (Vite HMR)
    frontend:
      kind: process
      command: ["npm", "run", "dev"]
      cwd: "{root}/web/frontend"
      host: 127.0.0.1
      port: 5173  # Vite default
      depends_on: [api]
      env:
        VITE_API_URL: "http://127.0.0.1:8000"
      health_path: /
      health_timeout: 15
      health_retries: 3
      stdout_log: "log/frontend.log"
      stderr_log: "log/frontend.err.log"
```

**Pros:**
- ✅ Hot Module Reload (Frontend-Änderungen live)
- ✅ Source Maps für Debugging
- ✅ Schnelle Dev-Iteration

**Cons:**
- ❌ 2 Prozesse, komplexer zu debuggen
- ❌ Frontend und API auf unterschiedlichen Ports
- ❌ CORS muss konfiguriert sein

**Wann:** Local Development

---

## Variante 3: PRODUCTION (Flask + Pre-Built Frontend)

**Use-Case:** Semi-Prod, Production mit optimiertem Frontend

```yaml
stack:
  name: kicli-assist-prod
  target: local
  
  services:
    web:
      kind: process
      # Flask mit gebautem Frontend (static files)
      command: ["{python}", "-m", "kicli_code_assist.web.server"]
      cwd: "{root}"
      host: 127.0.0.1
      port: 8000
      env:
        PYTHONUNBUFFERED: "1"
        KI_STAGE: "production"
      health_path: /api/health
      health_timeout: 10
      health_retries: 5
      health_interval: 2
      stdout_log: "log/web.log"
      stderr_log: "log/web.err.log"
```

**Pre-Build Step (vor `stackctl start`):**
```bash
cd web/frontend
npm install
npm run build
# Output: ../../kicli_code_assist/web/static/
```

**Pros:**
- ✅ Einziger Prozess (einfach)
- ✅ Frontend optimiert (minified, bundled)
- ✅ Ein Port :8000, Apache reverse proxy einfach
- ✅ Für Semi-Prod ideal

**Cons:**
- ❌ Kein HMR (muss rebuild nach Frontend-Änderung)

**Wann:** Semi-Prod, Production

---

## Variante 4: FULL STACK (mit Optional DB)

**Use-Case:** Zukunft mit persistenter DB (Chat-History, etc.)

```yaml
stack:
  name: kicli-assist-full
  target: local
  
  services:
    # Optional: Database initialization (later)
    db:
      kind: process
      command: ["bash", "-c", "python -c 'import sqlite3; sqlite3.connect(\"var/kicli.db\")'"]
      cwd: "{root}"
      # Non-blocking init, dann exit
      
    # Backend
    web:
      kind: process
      command: ["{python}", "-m", "kicli_code_assist.web.server"]
      cwd: "{root}"
      host: 127.0.0.1
      port: 8000
      depends_on: [db]  # Wait for DB init (if used)
      env:
        PYTHONUNBUFFERED: "1"
        KI_STAGE: "production"
        DB_URL: "sqlite:///var/kicli.db"
      health_path: /api/health
      health_timeout: 10
      health_retries: 5
      health_interval: 2
      stdout_log: "log/web.log"
      stderr_log: "log/web.err.log"
```

**Pros:**
- ✅ Bereit für DB-Features
- ✅ Dependency Management (db → web)
- ✅ Erweiterbar

**Cons:**
- ❌ Komplexer
- ❌ Noch nicht nötig (TUI speichert in Files)

**Wann:** Wenn Chat-History persistent werden soll

---

## Empfehlung für dich

| Szenario | Variante | Grund |
|----------|----------|-------|
| **Jetzt Semi-Prod** | #3 (Production) | Einfach, Frontend vorher `npm run build` |
| **Local Dev** | #2 (Dev) | HMR für schnelle Iteration |
| **TUI nur** | #1 (Minimal) | Keine WebUI nötig |
| **Später mit DB** | #4 (Full Stack) | Chat-History persistent |

---

## Nächste Schritte

1. **Variante #3 verwenden für Semi-Prod:**
   ```bash
   cp deploy/stack-semiprod.yaml deploy/stack.yaml
   ```

2. **Bevor stackctl start:**
   ```bash
   cd web/frontend
   npm install
   npm run build
   ```

3. **Dann:**
   ```bash
   cd /path/to/kicli-code-assist
   stackctl local start --project .
   ```

---

## Questions?

- Welche Variante magst du?
- Brauchst du DB später?
- Nur Flask (TUI) oder auch WebUI?
