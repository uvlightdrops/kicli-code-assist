#!/bin/bash
# Semi-prod deployment setup script
#
# Interactive setup for Apache2 vhost + reverse proxy
# Supports both Option 1 (single-port) and Option 2 (dual-port)
#
# Usage: sudo ./scripts/deploy_semi_prod.sh

set -e

if [[ $EUID -ne 0 ]]; then
    echo "❌ This script must be run as root (sudo)"
    exit 1
fi

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEPLOYMENT_DIR="${PROJECT_ROOT}/docs/deployment"

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║     kicli-web Semi-Prod Deployment Setup               ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Select option
echo "Choose deployment option:"
echo ""
echo "  1) Option 1 (RECOMMENDED): Single-port via Flask"
echo "     - One port (8000)"
echo "     - Firewall-friendly ✅"
echo "     - Frontend built to static files"
echo "     - No Node.js on prod"
echo ""
echo "  2) Option 2: Dual-port with Vite dev server"
echo "     - Two ports (8000 + 3000)"
echo "     - More complex, better for dev"
echo "     - Requires Node.js on prod"
echo ""

read -p "Select option (1 or 2): " OPTION

if [[ ! "$OPTION" =~ ^[12]$ ]]; then
    echo "❌ Invalid option. Exiting."
    exit 1
fi

# ============================================================================
# Setup Apache2
# ============================================================================

echo ""
echo "▶ Setting up Apache2..."

# Enable modules
echo "  • Enabling Apache modules..."
a2enmod proxy proxy_http rewrite

if [[ "$OPTION" == "2" ]]; then
    a2enmod proxy_wstunnel
fi

# Copy vhost config
if [[ "$OPTION" == "1" ]]; then
    CONF_FILE="${DEPLOYMENT_DIR}/kicli-web-option1.conf"
    SITE_NAME="kicli-web-option1"
else
    CONF_FILE="${DEPLOYMENT_DIR}/kicli-web-option2.conf"
    SITE_NAME="kicli-web-option2"
fi

if [[ ! -f "$CONF_FILE" ]]; then
    echo "❌ Config file not found: $CONF_FILE"
    exit 1
fi

echo "  • Installing vhost config..."
cp "$CONF_FILE" "/etc/apache2/sites-available/${SITE_NAME}.conf"

# Enable site
echo "  • Enabling site..."
a2ensite "${SITE_NAME}.conf"

# Disable old site if exists
if a2ensite kicli-web-option1.conf 2>/dev/null && [[ "$OPTION" == "2" ]]; then
    a2dissite kicli-web-option1.conf 2>/dev/null || true
fi

if a2ensite kicli-web-option2.conf 2>/dev/null && [[ "$OPTION" == "1" ]]; then
    a2dissite kicli-web-option2.conf 2>/dev/null || true
fi

# Reload Apache
echo "  • Reloading Apache..."
systemctl reload apache2

echo "✅ Apache2 configured: $SITE_NAME"

# ============================================================================
# Setup static files (Option 1 only)
# ============================================================================

if [[ "$OPTION" == "1" ]]; then
    echo ""
    echo "▶ Setting up static files (Option 1)..."
    
    STATIC_DIR="${PROJECT_ROOT}/kicli_code_assist/web/static"
    
    if [[ ! -d "$STATIC_DIR" ]]; then
        echo "  ⚠ Static directory not found: $STATIC_DIR"
        echo "  Run from project root:"
        echo "    npm run build --prefix web/frontend"
        echo "    ./scripts/collect_static.sh"
        echo ""
    else
        FILE_COUNT=$(find "$STATIC_DIR" -type f 2>/dev/null | wc -l)
        echo "  ✅ Static files ready ($FILE_COUNT files)"
    fi
fi

# ============================================================================
# Summary
# ============================================================================

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║ Deployment Complete                                    ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "Option selected: $OPTION"
echo "VHost config: /etc/apache2/sites-available/${SITE_NAME}.conf"
echo "Log location: /var/log/apache2/"
echo ""

if [[ "$OPTION" == "1" ]]; then
    echo "Next steps (Option 1):"
    echo "  1. npm run build --prefix web/frontend"
    echo "  2. ./scripts/collect_static.sh"
    echo "  3. python -m kicli_code_assist.web.server"
    echo ""
    echo "Test:"
    echo "  curl http://localhost/api/health"
    echo ""
else
    echo "Next steps (Option 2):"
    echo "  1. npm install --prefix web/frontend"
    echo "  2. python -m kicli_code_assist.web.server &"
    echo "  3. cd web/frontend && npm run dev &"
    echo ""
    echo "Test:"
    echo "  curl http://localhost/api/health"
    echo "  curl http://localhost/"
    echo ""
fi

echo "Monitor logs:"
echo "  tail -f /var/log/apache2/${SITE_NAME}-error.log"
echo ""
