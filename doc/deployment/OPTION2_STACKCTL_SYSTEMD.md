# Option 2 Deployment: stackctl + systemd

Einfache, robuste Variante für Semi-Prod.

## Architektur

```
systemd [kicli-assist service]
    ↓
stackctl local start
    ↓
    ├─ Orchestration: start/stop/health-check services
    ├─ Dependencies: enforce startup order
    ├─ Health Checks: wait until ready
    └─ Logs: aggregate output
    ↓
[Flask Web App] → 127.0.0.1:8000
    ↓
[Apache2 reverse proxy] → External port 80/443
```

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

## Mit Apache2 Reverse Proxy

### Apache Config

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

## Troubleshooting

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
