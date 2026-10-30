#!/bin/bash
# Diagnose script for deployment host capabilities
# Usage: ./diagnose_deployment_host.sh

set -e

echo "╔════════════════════════════════════════════════════════╗"
echo "║     Deployment Host Diagnostic Report                  ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# System Info
echo "🖥️  System Information"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "OS: $(lsb_release -ds 2>/dev/null || echo 'Unknown')"
echo "Kernel: $(uname -r)"
echo "Hostname: $(hostname)"
echo "Uptime: $(uptime -p)"
echo ""

# User & Permissions
echo "👤 User & Permissions"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Current User: $(whoami)"
if sudo -n true 2>/dev/null; then
    echo "Sudo Access: ✅ Yes (passwordless)"
else
    echo "Sudo Access: ⚠️  Requires password"
fi
echo ""

# Firewall
echo "🔥 Firewall Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if sudo systemctl is-active ufw > /dev/null 2>&1; then
    echo "UFW Firewall: ✅ Active"
    echo "Rules:"
    sudo ufw status | grep -E "^\d|^To" | head -10 || true
elif sudo systemctl is-active firewalld > /dev/null 2>&1; then
    echo "Firewalld: ✅ Active"
    sudo firewall-cmd --list-all 2>/dev/null | head -20 || true
else
    echo "Firewall: ⚠️  Not detected (ufw/firewalld)"
fi
echo ""

# Open Ports
echo "🔌 Network - Open Ports (listening)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TCP ports:"
sudo ss -tlnp 2>/dev/null | grep LISTEN | awk '{print $4, $7}' | sort | uniq || netstat -tlnp 2>/dev/null | grep LISTEN | tail -10 || echo "Could not detect open ports"
echo ""

# Required Tools
echo "🛠️  Required Tools & Runtimes"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
check_tool() {
    local tool=$1
    if command -v "$tool" &> /dev/null; then
        version=$("$tool" --version 2>/dev/null | head -1 || echo "unknown")
        echo "✅ $tool: $version"
    else
        echo "❌ $tool: NOT FOUND"
    fi
}

check_tool git
check_tool python3
check_tool python
check_tool pip
check_tool pip3
check_tool node
check_tool npm
check_tool docker
check_tool docker-compose
check_tool systemctl
check_tool curl
echo ""

# Python Environment
echo "🐍 Python Environment"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 --version
echo "Python Location: $(which python3)"
echo "Pip Location: $(which pip3)"
echo "Pip Version: $(pip3 --version)"
if [ -d ".venv" ]; then
    echo "Virtual Env: ✅ .venv found locally"
elif [ -d "/opt/kicli/.venv" ]; then
    echo "Virtual Env: ✅ /opt/kicli/.venv found"
else
    echo "Virtual Env: ⚠️  Not found in standard locations"
fi
echo ""

# Disk Space
echo "💾 Disk Space"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
df -h / | tail -1 | awk '{print "Root filesystem: " $1 " - " $2 " total, " $4 " available (" $5 " used)"}'
if [ -d /opt ]; then
    df -h /opt | tail -1 | awk '{print "/opt: " $1 " - " $2 " total, " $4 " available"}'
fi
echo ""

# systemd
echo "📋 Systemd Services"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Can enable/disable services: ✅ systemd available"
echo "Sample running services:"
systemctl list-units --type=service --state=running 2>/dev/null | grep -E "apache|nginx|python|node|kicli" | head -5 || echo "  (none matching deployment pattern)"
echo ""

# Reverse Proxy
echo "🔀 Reverse Proxy Options"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if command -v apache2ctl &> /dev/null; then
    echo "✅ Apache2: $(apache2ctl -v | head -1)"
else
    echo "❌ Apache2: NOT FOUND"
fi

if command -v nginx &> /dev/null; then
    echo "✅ Nginx: $(nginx -v 2>&1)"
else
    echo "❌ Nginx: NOT FOUND"
fi
echo ""

# Container Runtime
echo "🐳 Container & Orchestration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if command -v docker &> /dev/null; then
    echo "✅ Docker: $(docker --version)"
else
    echo "❌ Docker: NOT FOUND"
fi

if command -v kubectl &> /dev/null; then
    echo "✅ kubectl: $(kubectl version --client --short 2>/dev/null || echo 'installed')"
else
    echo "❌ kubectl: NOT FOUND"
fi

if command -v helm &> /dev/null; then
    echo "✅ Helm: $(helm version --short 2>/dev/null || echo 'installed')"
else
    echo "❌ Helm: NOT FOUND"
fi

if command -v skopeo &> /dev/null; then
    echo "✅ Skopeo: $(skopeo --version 2>/dev/null || echo 'installed')"
else
    echo "❌ Skopeo: NOT FOUND"
fi
echo ""

# Git Repos
echo "📁 Git & Project Structure"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -d ".git" ]; then
    echo "✅ Git Repo: Found in $(pwd)"
    echo "  Branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')"
    echo "  Remote: $(git config --get remote.origin.url 2>/dev/null || echo 'none')"
else
    echo "❌ Git Repo: Not in current directory"
fi
echo ""

# Recommendation
echo "📋 Deployment Options Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Option 1 (Simple): Flask + Reverse Proxy (Apache/Nginx)"
echo "  Requires: Python3, pip, Apache2/Nginx, git"
echo "  Ports: 8000 (backend), 80/443 (proxy)"
echo "  Complexity: ⭐ Low"
echo ""
echo "Option 2 (Advanced): stackctl + systemd"
echo "  Requires: Python3, git, systemd"
echo "  Ports: Custom (per stack.yaml)"
echo "  Complexity: ⭐⭐ Medium"
echo ""
echo "Option 3 (Container): Docker + Helm/k8s"
echo "  Requires: Docker, Helm, kubectl (optional)"
echo "  Ports: Variable"
echo "  Complexity: ⭐⭐⭐ High"
echo ""

echo "╔════════════════════════════════════════════════════════╗"
echo "║  Diagnostic complete. Review sections marked with ❌   ║"
echo "╚════════════════════════════════════════════════════════╝"
