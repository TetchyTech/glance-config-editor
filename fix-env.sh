#!/bin/bash

# Quick fix for environment variable issues
# Run this if the service isn't reading your config file

echo "🔧 Fixing Glance Editor environment configuration..."

cd /opt/glance-editor

# Source the current .env file
if [ -f ".env" ]; then
    source .env
    echo "✅ Loaded environment variables from .env"
else
    echo "❌ .env file not found! Creating a basic one..."
    cat > .env << 'EOF'
export SESSION_SECRET="glance-editor-$(openssl rand -hex 16)"
export GLANCE_CONFIG_PATH="/opt/glance/glance.yml"
export BACKUP_DIR="/opt/glance-editor/backups"
export EDITOR_USERNAME="admin"
export EDITOR_PASSWORD="admin"
EOF
    source .env
fi

# Create initial backup if glance config exists and no backups exist yet
if [ -f "${GLANCE_CONFIG_PATH}" ] && [ ! -f "/opt/glance-editor/backups/glance_original_backup_"* ]; then
    echo "📦 Creating initial backup of existing glance.yml..."
    INITIAL_BACKUP_NAME="glance_original_backup_$(date +%Y%m%d_%H%M%S).yml"
    mkdir -p /opt/glance-editor/backups
    cp "${GLANCE_CONFIG_PATH}" "/opt/glance-editor/backups/$INITIAL_BACKUP_NAME"
    echo "✅ Original configuration backed up as: $INITIAL_BACKUP_NAME"
fi

# Update systemd service with current environment
echo "🔄 Updating systemd service..."
cat > /etc/systemd/system/glance-editor.service << EOF
[Unit]
Description=Glance Configuration Editor
After=network.target

[Service]
Type=exec
User=root
WorkingDirectory=/opt/glance-editor
Environment="SESSION_SECRET=${SESSION_SECRET}"
Environment="GLANCE_CONFIG_PATH=${GLANCE_CONFIG_PATH}"
Environment="BACKUP_DIR=${BACKUP_DIR}"
Environment="EDITOR_USERNAME=${EDITOR_USERNAME}"
Environment="EDITOR_PASSWORD=${EDITOR_PASSWORD}"
ExecStart=/opt/glance-editor/glance-env/bin/gunicorn --bind 0.0.0.0:5000 --workers 1 --timeout 120 main:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Reload and restart service
systemctl daemon-reload
systemctl restart glance-editor

# Check status
sleep 2
if systemctl is-active --quiet glance-editor; then
    echo "✅ Service restarted successfully!"
    echo "📍 Config file: ${GLANCE_CONFIG_PATH}"
    echo "📁 Backup dir: ${BACKUP_DIR}"
    echo "👤 Username: ${EDITOR_USERNAME}"
    
    # Test if config file exists
    if [ -f "${GLANCE_CONFIG_PATH}" ]; then
        echo "✅ Config file found and readable"
    else
        echo "⚠️  Config file not found at ${GLANCE_CONFIG_PATH}"
        echo "   Create it or update GLANCE_CONFIG_PATH in .env"
    fi
else
    echo "❌ Service failed to start. Check logs:"
    echo "   journalctl -u glance-editor -n 20"
fi