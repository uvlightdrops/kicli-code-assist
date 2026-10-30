# Option 2 Deployment: stackctl + systemd

Robuste Variante für Semi-Prod mit Unterstützung für TUI und WebUI.

## Architektur

### TUI (Terminal User Interface) - Lokal nur
```
systemd [kicli-assist service]
    ↓
stackctl local start
    ↓
Agents (programmieren über CLI/Terminal)
```

### WebUI (Web Interface) - Remote Zugriff
```
Browser (Remote/External)
    ↓
Web Server (Apache2, Nginx, Caddy, etc.) :80/:443
    ↓
systemd [kicli-assist service] :8000 (Reverse Proxy)
    ↓
stackctl local start
    ↓
Agents (programmieren über Web-UI)
```

**Wichtig:** WebUI erfordert einen Web-Server für externen Zugriff. TUI läuft auch ohne.


## Setup auf Semi-Prod Host

### 1. Vorbereitung

```bash
# SSH auf Semi-Prod
ssh user@semi-prod

# Python venv vorbereiten
cd /opt/kicli  # oder ~/kicli
python3 -m venv .venv
source .venv/bin/activate

# Dependencies installieren (mit Proxy falls nötig)
pip install -e /path/to/ki-core
pip install -e /path/to/kicli-code-assist

# Test: stackctl funktioniert?
stackctl repo-status
```

### 2. Systemd Service installieren

```bash
# Von kicli-code-assist root:
cd /path/to/kicli-code-assist

# Script ausführen (mit sudo)
bash scripts/setup_stackctl_systemd.sh install

# Verifyifizieren
sudo systemctl status kicli-assist
```

### 3. Stack Config anpassen

```bash
# Beispiel für Semi-Prod:
cp deploy/stack-semiprod.yaml deploy/stack.yaml

# Pfade und Ports je nach Host anpassen
vi deploy/stack.yaml
```

### 4. Service starten

```bash
# Start
sudo systemctl start kicli-assist

# Status
sudo systemctl status kicli-assist

# Logs (live)
sudo journalctl -u kicli-assist -f

# Stop
sudo systemctl stop kicli-assist
```

## Verfügbare Kommandos

```bash
bash scripts/setup_stackctl_systemd.sh install   # Einmalig: systemd service einrichten
bash scripts/setup_stackctl_systemd.sh start     # Service starten
bash scripts/setup_stackctl_systemd.sh stop      # Service stoppen
bash scripts/setup_stackctl_systemd.sh restart   # Service neu starten
bash scripts/setup_stackctl_systemd.sh status    # Status anzeigen
bash scripts/setup_stackctl_systemd.sh logs      # Logs folgen
bash scripts/setup_stackctl_systemd.sh enable    # Auto-start bei Boot
bash scripts/setup_stackctl_systemd.sh disable   # Auto-start deaktivieren
```

## Mit Web-Server für WebUI (Reverse Proxy)

Falls du die WebUI remote erreichbar brauchst, verwende einen der folgenden:

### Apache2

```apache
<VirtualHost *:80>
    ServerName kicli.example.com
    
    ProxyPreserveHost On
    ProxyRequests Off
    
    # Proxy all traffic to Flask
    <Location />
        ProxyPass http://127.0.0.1:8000/
        ProxyPassReverse http://127.0.0.1:8000/
    </Location>
    
    # WebSocket support
    <Location /socket.io/>
        ProxyPass http://127.0.0.1:8000/socket.io/
        ProxyPassReverse http://127.0.0.1:8000/socket.io/
        ProxyPassReverseCookiePath / /
    </Location>
    
    ErrorLog ${APACHE_LOG_DIR}/kicli-error.log
    CustomLog ${APACHE_LOG_DIR}/kicli-access.log combined
</VirtualHost>
```

**Enable:**
```bash
sudo a2enmod proxy proxy_http proxy_wstunnel
sudo a2ensite kicli-semiprod
sudo systemctl reload apache2
```

### Nginx (Alternative)

```nginx
server {
    listen 80;
    server_name kicli.example.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # WebSocket support
    location /socket.io/ {
        proxy_pass http://127.0.0.1:8000/socket.io/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

**Enable:**
```bash
sudo ln -s /etc/nginx/sites-available/kicli /etc/nginx/sites-enabled/
sudo systemctl reload nginx
```


## Zusammenfassung: TUI vs WebUI

| Aspekt | TUI | WebUI |
|--------|-----|-------|
| **User Interface** | Terminal/CLI | Browser |
| **Access** | Local SSH nur | Remote über HTTP/HTTPS |
| **Required** | systemd + stackctl | systemd + stackctl + Web-Server |
| **Web-Server nötig** | ❌ Nein | ✅ Ja (Apache/Nginx/Caddy/...) |
| **Setup-Zeit** | ~ 5 Min | ~ 10-15 Min |
| **Komplexität** | Einfach | Mittel |

**Wahl treffen:**
- **TUI nur:** Systemd + Stackctl reicht, Skip Web-Server
- **WebUI:** Systemd + Stackctl + Web-Server (deine Wahl: Apache/Nginx/etc.)


### Service startet nicht
```bash
# Logs checken
sudo journalctl -u kicli-assist -n 50

# Manuelle Test: stackctl direkt aufrufen
cd /path/to/kicli-code-assist
stackctl local start --project .
```

### Port 8000 ist belegt
```bash
# Welcher Prozess nutzt Port 8000?
sudo lsof -i :8000

# Stack.yaml anpassen:
vi deploy/stack.yaml
# "port: 8000" ändern auf free port (z.B. 8080)
```

### Health Check schlägt fehl
```bash
# Test manuell:
curl http://127.0.0.1:8000/api/health

# In stack.yaml erhöhen:
health_timeout: 15  # Mehr Zeit für Startup
health_retries: 5   # Mehr Versuche
health_interval: 2  # Längere Pausen
```

### Logs nicht sichtbar
```bash
# Journalctl mit mehr Output
sudo journalctl -u kicli-assist -n 100 --all

# Oder direkt in Files:
tail -f log/web.log
tail -f log/web.err.log
```

## Monitoring

Health Check Status:
```bash
curl -v http://127.0.0.1:8000/api/health
```

Service Restart automatisch bei Crash:
```bash
# Systemd Konfiguration:
Restart=on-failure
RestartSec=10
# → Service startet nach 10 Sekunden neu wenn gekrasht
```

## Firewall

Wenn UFW läuft, nur Port 80/443 freigeben (Apache Proxy):
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
# Port 8000 bleibt geschlossen (nur lokal)
```
