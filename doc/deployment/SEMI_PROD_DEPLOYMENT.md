# Semi-Prod Deployment Guide

Zwei Optionen für Firewall-Szenarien mit Apache2 reverse proxy.

## Option 1: Single-Port (Empfohlen)

Frontend build zu static files, Flask serviert alles über port 8000.

**Vorteil:** Nur ein Port, Firewall-freundlich  
**Nachteil:** Node.js nicht auf Prod nötig, aber Rebuild vor Deploy

### Apache2 Vhost Config

**File:** `/etc/apache2/sites-available/kicli-web.conf`

```apache
<VirtualHost *:80>
    ServerName kicli.example.com
    ServerAdmin admin@example.com

    # Enable proxy modules
    ProxyPreserveHost On
    ProxyRequests Off

    # Route all traffic to Flask backend
    <Location />
        ProxyPass http://localhost:8000/
        ProxyPassReverse http://localhost:8000/
    </Location>

    # Logging
    ErrorLog ${APACHE_LOG_DIR}/kicli-error.log
    CustomLog ${APACHE_LOG_DIR}/kicli-access.log combined

    # Performance
    TimeOut 300
</VirtualHost>
```

**Enable:**
```bash
sudo a2enmod proxy proxy_http
sudo a2ensite kicli-web.conf
sudo systemctl reload apache2
```

### Deployment Workflow

```bash
# 1. Build frontend
npm run build          # → web/frontend/dist/

# 2. Collect static files
./scripts/collect_static.sh

# 3. Start Flask (serves both API + static files)
python -m kicli_code_assist.web.server
```

---

## Option 2: Dual-Port (Flexible)

Vite dev server + Flask getrennt, je ein reverse proxy.

**Vorteil:** Frontend reload ohne Backend restart  
**Nachteil:** Zwei Ports, Firewall-Komplexität, Node.js auf Prod

### Apache2 Vhost Config

**File:** `/etc/apache2/sites-available/kicli-web.conf`

```apache
<VirtualHost *:80>
    ServerName kicli.example.com
    ServerAdmin admin@example.com

    ProxyPreserveHost On
    ProxyRequests Off

    # API routes to Flask
    <Location /api/>
        ProxyPass http://localhost:8000/api/
        ProxyPassReverse http://localhost:8000/api/
    </Location>

    # WebSocket for chat
    <Location /socket.io/>
        ProxyPass http://localhost:8000/socket.io/
        ProxyPassReverse http://localhost:8000/socket.io/
        ProxyPassReverseCookiePath / /
    </Location>

    # Frontend assets + static to Vite
    <Location />
        ProxyPass http://localhost:3000/
        ProxyPassReverse http://localhost:3000/
    </Location>

    ErrorLog ${APACHE_LOG_DIR}/kicli-error.log
    CustomLog ${APACHE_LOG_DIR}/kicli-access.log combined

    TimeOut 300
</VirtualHost>
```

**Enable:**
```bash
sudo a2enmod proxy proxy_http proxy_wstunnel
sudo a2ensite kicli-web.conf
sudo systemctl reload apache2
```

### Deployment Workflow

```bash
# 1. Install dependencies
npm install --prefix web/frontend

# 2. Start both servers
python -m kicli_code_assist.web.server &
cd web/frontend && npm run dev &
```

---

## Firewall Testing

```bash
# Test port 8000 (Option 1 + Option 2 backend)
curl http://localhost:8000/api/health

# Test port 3000 (Option 2 frontend only)
curl http://localhost:3000

# Test Apache reverse proxy
curl http://localhost/api/health
```

---

## Recommendation

**Start with Option 1:**
- Simpler setup
- No Node.js on prod
- One port = high Firewall success rate
- If Firewall blocks: easy to diagnose

**Fall back to Option 2 if needed:**
- Confirm port 3000 is reachable first
- Use WebSocket tunnel config above
- Monitor proxy logs: `tail -f /var/log/apache2/kicli-error.log`

---

## Static Files Setup (Option 1)

See `scripts/collect_static.sh` for automation.

Manual:
```bash
mkdir -p kicli_code_assist/web/static
cp -r web/frontend/dist/* kicli_code_assist/web/static/
```

Flask serves from: `kicli_code_assist/web/static/`
