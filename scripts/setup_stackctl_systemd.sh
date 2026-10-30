#!/bin/bash
# Setup script for Option 2 deployment: stackctl + systemd
# Usage: ./setup_stackctl_systemd.sh [--install|--start|--status|--logs|--stop]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVICE_NAME="kicli-assist"
SERVICE_USER="${KICLI_USER:-$(whoami)}"  # Use current user if not specified
VENV_PATH="${KICLI_VENV:-$PROJECT_ROOT/.venv}"

echo "╔════════════════════════════════════════════════════════╗"
echo "║  kicli-code-assist + stackctl + systemd Setup          ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "Configuration:"
echo "  Project Root: $PROJECT_ROOT"
echo "  Service Name: $SERVICE_NAME"
echo "  Service User: $SERVICE_USER"
echo "  Virtual Env: $VENV_PATH"
echo ""

install_service() {
    echo "📦 Installing systemd service..."
    
    # Verify service user exists (no creation for managed hosts)
    if ! id "$SERVICE_USER" &>/dev/null; then
        echo "  ❌ Error: User '$SERVICE_USER' does not exist"
        echo "     On managed hosts, please use existing user:"
        echo "     KICLI_USER=existing_username bash setup_stackctl_systemd.sh install"
        exit 1
    fi
    echo "  ✅ Using user: $SERVICE_USER"
    
    # Load template
    TEMPLATE_FILE="$SCRIPT_DIR/kicli-assist.service.template"
    if [[ ! -f "$TEMPLATE_FILE" ]]; then
        echo "  ❌ Error: Template not found: $TEMPLATE_FILE"
        exit 1
    fi
    
    # Read template and substitute variables
    SERVICE_CONTENT=$(cat "$TEMPLATE_FILE")
    SERVICE_CONTENT="${SERVICE_CONTENT//@SERVICE_USER@/$SERVICE_USER}"
    SERVICE_CONTENT="${SERVICE_CONTENT//@PROJECT_ROOT@/$PROJECT_ROOT}"
    
    # Write to systemd
    SYSTEMD_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
    echo "  Creating systemd service: $SYSTEMD_FILE"
    echo "$SERVICE_CONTENT" | sudo tee "$SYSTEMD_FILE" > /dev/null
    
    # Reload systemd daemon
    sudo systemctl daemon-reload
    echo "  ✅ Service installed"
}

start_service() {
    echo "▶️  Starting service..."
    sudo systemctl start "$SERVICE_NAME"
    echo "  ✅ Service started"
}

stop_service() {
    echo "⏹️  Stopping service..."
    sudo systemctl stop "$SERVICE_NAME"
    echo "  ✅ Service stopped"
}

enable_service() {
    echo "🔗 Enabling service (auto-start on boot)..."
    sudo systemctl enable "$SERVICE_NAME"
    echo "  ✅ Service enabled"
}

disable_service() {
    echo "🔓 Disabling service (no auto-start)..."
    sudo systemctl disable "$SERVICE_NAME"
    echo "  ✅ Service disabled"
}

status_service() {
    echo "📊 Service Status:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    sudo systemctl status "$SERVICE_NAME" --no-pager || true
    echo ""
}

logs_service() {
    echo "📋 Service Logs (last 50 lines):"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    sudo journalctl -u "$SERVICE_NAME" -n 50 --no-pager || true
    echo ""
    echo "Follow logs (Ctrl+C to exit):"
    sudo journalctl -u "$SERVICE_NAME" -f || true
}

restart_service() {
    echo "🔄 Restarting service..."
    sudo systemctl restart "$SERVICE_NAME"
    echo "  ✅ Service restarted"
}

uninstall_service() {
    echo "🗑️  Uninstalling service..."
    stop_service || true
    sudo systemctl disable "$SERVICE_NAME" || true
    sudo rm -f "/etc/systemd/system/${SERVICE_NAME}.service"
    sudo systemctl daemon-reload
    echo "  ✅ Service uninstalled"
}

# Parse command
COMMAND="${1:-status}"

case "$COMMAND" in
    install)
        install_service
        enable_service
        echo "✨ Setup complete! Next steps:"
        echo "  1. Verify user has write permissions to: $PROJECT_ROOT"
        echo "  2. Review config in: /etc/systemd/system/${SERVICE_NAME}.service"
        echo "  3. Create/verify: $PROJECT_ROOT/deploy/stack.yaml"
        echo "  4. Start service: sudo systemctl start $SERVICE_NAME"
        echo "  5. Check status: sudo systemctl status $SERVICE_NAME"
        echo ""
        echo "Note for managed hosts:"
        echo "  - Service runs as user: $SERVICE_USER"
        echo "  - If user is different next time, use:"
        echo "    KICLI_USER=your_username bash setup_stackctl_systemd.sh install"
        ;;
    start)
        start_service
        status_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        status_service
        ;;
    status)
        status_service
        ;;
    logs)
        logs_service
        ;;
    enable)
        enable_service
        ;;
    disable)
        disable_service
        ;;
    uninstall)
        uninstall_service
        ;;
    *)
        echo "Usage: $0 {install|start|stop|restart|status|logs|enable|disable|uninstall}"
        echo ""
        echo "Commands:"
        echo "  install    - Install and enable systemd service"
        echo "  start      - Start the service"
        echo "  stop       - Stop the service"
        echo "  restart    - Restart the service"
        echo "  status     - Show service status"
        echo "  logs       - Show service logs (follow with Ctrl+C)"
        echo "  enable     - Enable auto-start on boot"
        echo "  disable    - Disable auto-start"
        echo "  uninstall  - Remove systemd service"
        exit 1
        ;;
esac
