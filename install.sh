#!/bin/bash

# Glance Configuration Editor - LXC Installation Script
# Run this script on your Debian-based LXC container

set -e

echo "🚀 Installing Glance Configuration Editor..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    print_error "Please run as root (use sudo)"
    exit 1
fi

# Update system
print_status "Updating system packages..."
apt update && apt upgrade -y

# Install required packages
print_status "Installing Python and dependencies..."
apt install python3 python3-pip python3-venv curl wget nano -y

# Create application directory
print_status "Creating application directory..."
mkdir -p /opt/glance-editor/{templates,static,backups}
cd /opt/glance-editor

# Create Python virtual environment
print_status "Setting up Python virtual environment..."
python3 -m venv glance-env
source glance-env/bin/activate

# Install Python packages
print_status "Installing Python dependencies..."
pip install flask pyyaml werkzeug gunicorn requests

# Generate secure session secret
SESSION_SECRET="glance-editor-$(openssl rand -hex 16)"

# Get configuration from user
echo ""
print_status "Configuration Setup"
echo "Please provide the following information:"

read -p "Admin username [admin]: " ADMIN_USER
ADMIN_USER=${ADMIN_USER:-admin}

while true; do
    read -s -p "Admin password: " ADMIN_PASS
    echo
    if [ -n "$ADMIN_PASS" ]; then
        break
    fi
    print_warning "Password cannot be empty"
done

read -p "Path to Glance config file [/opt/glance/glance.yaml]: " GLANCE_PATH
GLANCE_PATH=${GLANCE_PATH:-/opt/glance/glance.yaml}

# Create environment file
print_status "Creating environment configuration..."
cat > .env << EOF
export SESSION_SECRET="$SESSION_SECRET"
export GLANCE_CONFIG_PATH="$GLANCE_PATH"
export BACKUP_DIR="/opt/glance-editor/backups"
export EDITOR_USERNAME="$ADMIN_USER"
export EDITOR_PASSWORD="$ADMIN_PASS"
EOF

chmod 600 .env

# Create main.py if it doesn't exist
if [ ! -f "main.py" ]; then
    print_status "Creating main.py..."
    cat > main.py << 'EOF'
from app import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
EOF
fi

# Check if app.py exists (should be there if cloned from git)
if [ ! -f "app.py" ]; then
    print_error "app.py not found!"
    print_status "Make sure you're running this from the correct directory."
    print_status "If you cloned from git: cd /opt/glance-editor"
    print_status "If manual install: copy all files to this directory first"
    exit 1
fi

# Create initial backup of existing glance.yaml if it exists
if [ -f "$GLANCE_PATH" ]; then
    print_status "Creating initial backup of existing glance.yaml..."
    INITIAL_BACKUP_NAME="glance_original_backup_$(date +%Y%m%d_%H%M%S).yaml"
    cp "$GLANCE_PATH" "/opt/glance-editor/backups/$INITIAL_BACKUP_NAME"
    print_status "Original configuration backed up as: $INITIAL_BACKUP_NAME"
else
    print_warning "Glance config file not found at: $GLANCE_PATH"
    print_status "The editor will create a default configuration when first accessed."
fi

# Create systemd service
print_status "Creating systemd service..."
cat > /etc/systemd/system/glance-editor.service << EOF
[Unit]
Description=Glance Configuration Editor
After=network.target

[Service]
Type=exec
User=root
WorkingDirectory=/opt/glance-editor
Environment="SESSION_SECRET=$SESSION_SECRET"
Environment="GLANCE_CONFIG_PATH=$GLANCE_PATH"
Environment="BACKUP_DIR=/opt/glance-editor/backups"
Environment="EDITOR_USERNAME=$ADMIN_USER"
Environment="EDITOR_PASSWORD=$ADMIN_PASS"
ExecStart=/opt/glance-editor/glance-env/bin/gunicorn --bind 0.0.0.0:5000 --workers 1 --timeout 120 main:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
systemctl daemon-reload
systemctl enable glance-editor

# Start the service
print_status "Starting Glance Editor service..."
systemctl start glance-editor

# Wait a moment for startup
sleep 3

# Check service status
if systemctl is-active --quiet glance-editor; then
    print_status "✅ Glance Configuration Editor is running!"
    echo ""
    echo "Access your editor at:"
    echo "  🌐 http://$(hostname -I | awk '{print $1}'):5000"
    echo "  👤 Username: $ADMIN_USER"
    echo "  🔒 Password: [your configured password]"
    echo ""
    echo "Service management:"
    echo "  📊 Check status: systemctl status glance-editor"
    echo "  🛑 Stop service: systemctl stop glance-editor"
    echo "  ▶️  Start service: systemctl start glance-editor"
    echo "  🔄 Restart service: systemctl restart glance-editor"
    echo "  📝 View logs: journalctl -u glance-editor -f"
else
    print_error "Failed to start service!"
    print_status "Check logs with: journalctl -u glance-editor -n 50"
    exit 1
fi

# Show final instructions
echo ""
print_status "Installation complete!"
print_warning "Important security notes:"
echo "  - Change the admin password if using default"
echo "  - Consider setting up a reverse proxy with HTTPS"
echo "  - Configure firewall if needed"
echo ""
print_status "For troubleshooting, see /opt/glance-editor/DEPLOYMENT.md"