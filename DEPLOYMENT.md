# Glance Config Editor - LXC Deployment Guide

This guide will help you deploy the Glance Configuration Editor on your Proxmox LXC container.

## Method 1: Direct File Transfer (Recommended)

### Step 1: Prepare Your LXC Container
```bash
# Update system packages
apt update && apt upgrade -y

# Install Python and required system packages
apt install python3 python3-pip python3-venv git curl wget -y

# Create application directory
mkdir -p /opt/glance-editor
cd /opt/glance-editor
```

### Step 2: Transfer Files
You have several options to get the files into your LXC:

**Option A: Using SCP/SFTP (if SSH is enabled)**
From your local machine:
```bash
scp -r glance-editor-files/* root@[LXC-IP]:/opt/glance-editor/
```

**Option B: Using wget to download from this Replit**
```bash
# If this Replit is deployed, you can download files directly
# Replace [REPLIT-URL] with the actual URL
wget [REPLIT-URL]/download-deployment-package
```

**Option C: Manual file creation**
Create each file manually using nano or vim. The essential files are:
- `app.py` (main application)
- `main.py` (entry point)
- `templates/index.html` (main interface)
- `templates/login.html` (login page)
- `templates/settings.html` (GitHub settings)
- `static/style.css` (custom styles)

### Step 3: Set Up Python Environment
```bash
cd /opt/glance-editor

# Create virtual environment
python3 -m venv glance-env
source glance-env/bin/activate

# Install Python dependencies
pip install flask pyyaml werkzeug gunicorn requests

# Make sure directories exist
mkdir -p templates static backups
```

### Step 4: Configure Environment Variables
```bash
# Create environment file
cat > /opt/glance-editor/.env << 'EOF'
export SESSION_SECRET="glance-editor-$(openssl rand -hex 16)"
export GLANCE_CONFIG_PATH="/opt/glance/glance.yaml"
export BACKUP_DIR="/opt/glance-editor/backups"
export EDITOR_USERNAME="admin"
export EDITOR_PASSWORD="your-secure-password-here"
EOF

# Make it executable
chmod +x /opt/glance-editor/.env

# Load environment variables
source /opt/glance-editor/.env
```

### Step 5: Create Systemd Service (Optional but Recommended)
```bash
# Create systemd service file
cat > /etc/systemd/system/glance-editor.service << 'EOF'
[Unit]
Description=Glance Configuration Editor
After=network.target

[Service]
Type=exec
User=root
WorkingDirectory=/opt/glance-editor
EnvironmentFile=/opt/glance-editor/.env
ExecStartPre=/bin/bash -c 'source /opt/glance-editor/glance-env/bin/activate'
ExecStart=/opt/glance-editor/glance-env/bin/gunicorn --bind 0.0.0.0:5000 --workers 1 --timeout 120 main:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
systemctl daemon-reload
systemctl enable glance-editor
systemctl start glance-editor

# Check status
systemctl status glance-editor
```

### Step 6: Test the Installation
```bash
# Check if service is running
curl http://localhost:5000

# Check from another machine on your network
curl http://[LXC-IP]:5000
```

## Method 2: Quick Manual Setup

If you prefer to create files manually:

### Step 1: Create Directory Structure
```bash
mkdir -p /opt/glance-editor/{templates,static,backups}
cd /opt/glance-editor
```

### Step 2: Create main.py
```bash
cat > main.py << 'EOF'
from app import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
EOF
```

### Step 3: Copy Application Files
You'll need to manually create or transfer:
- `app.py` (the main Flask application - 541 lines)
- `templates/index.html` (main interface)
- `templates/login.html` (login page) 
- `templates/settings.html` (settings page)
- `static/style.css` (custom styles)

## Configuration Options

### Environment Variables
- `SESSION_SECRET`: Flask session encryption key (generate randomly)
- `GLANCE_CONFIG_PATH`: Path to your Glance configuration file
- `BACKUP_DIR`: Directory for configuration backups
- `EDITOR_USERNAME`: Admin username (default: admin)
- `EDITOR_PASSWORD`: Admin password (change this!)

### Network Configuration
The application runs on port 5000 by default. Make sure:
- Port 5000 is not blocked by firewall
- Your LXC container can bind to 0.0.0.0:5000
- The port is accessible from your network

### Integration with Existing Glance
If you already have Glance running:
- Set `GLANCE_CONFIG_PATH` to your existing glance.yaml file
- The editor will read/write to your actual configuration
- Backups are stored separately in the backup directory

## Troubleshooting

### Common Issues:
1. **Port 5000 already in use**: Change the port in main.py
2. **Permission denied**: Make sure files are readable and directories writable
3. **Module not found**: Ensure virtual environment is activated and dependencies installed
4. **Can't connect from network**: Check firewall settings and bind address

### Logs:
```bash
# Check systemd service logs
journalctl -u glance-editor -f

# Check application logs manually
cd /opt/glance-editor
source glance-env/bin/activate
python main.py
```

## Security Notes

- Change the default admin password
- Use a strong SESSION_SECRET
- Consider using HTTPS with a reverse proxy (nginx/apache)
- Restrict network access if needed using iptables
- Regularly update Python dependencies

## Access Your Editor

Once running, access the editor at:
- From LXC: `http://localhost:5000`
- From network: `http://[LXC-IP]:5000`
- Login with username: `admin` and your configured password

The editor provides:
- YAML syntax highlighting and validation
- Automatic backup creation (keeps last 20)
- Undo functionality
- Optional GitHub integration
- Responsive web interface