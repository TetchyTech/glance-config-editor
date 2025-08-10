# Glance Configuration Editor

A lightweight web-based editor for Glance dashboard configuration files, designed for easy deployment on Proxmox LXC containers.

## Features

- **YAML Syntax Highlighting**: CodeMirror editor with dark theme and line numbers
- **Real-time Validation**: Automatic YAML validation as you type
- **Automatic Backups**: Keeps the last 20 configuration backups with timestamps
- **Undo Functionality**: Revert to last saved configuration
- **GitHub Integration**: Optional sync to GitHub repository on save
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Keyboard Shortcuts**: Ctrl+S to save, Ctrl+R to reload

## Quick Install on LXC Container

### One-Command Installation
```bash
# Install git if not present
apt update && apt install git -y

# Clone and install
git clone https://github.com/YOUR-USERNAME/glance-config-editor.git /opt/glance-editor
cd /opt/glance-editor
chmod +x install.sh
sudo ./install.sh
```

### Manual Installation
```bash
# Install dependencies
apt update && apt install python3 python3-pip python3-venv git -y

# Clone repository
git clone https://github.com/YOUR-USERNAME/glance-config-editor.git /opt/glance-editor
cd /opt/glance-editor

# Set up Python environment
python3 -m venv glance-env
source glance-env/bin/activate
pip install flask pyyaml werkzeug gunicorn requests

# Configure environment
cp .env.example .env
nano .env  # Edit your settings

# Start the application
python main.py
```

## Configuration

Edit `/opt/glance-editor/.env`:
```bash
export SESSION_SECRET="your-secure-random-string"
export GLANCE_CONFIG_PATH="/path/to/your/glance.yaml"
export BACKUP_DIR="/opt/glance-editor/backups"
export EDITOR_USERNAME="admin"
export EDITOR_PASSWORD="your-secure-password"
```

## Usage

1. Access the editor at `http://[LXC-IP]:5000`
2. Login with your configured username/password
3. Edit your Glance configuration with syntax highlighting
4. Save changes (automatically creates backup)
5. Optional: Configure GitHub integration in Settings

## GitHub Integration

1. Go to Settings page
2. Enable GitHub sync
3. Add your GitHub Personal Access Token
4. Configure repository details
5. Test connection
6. Every save will now push to GitHub automatically

## Service Management

The installer creates a systemd service:
```bash
sudo systemctl status glance-editor    # Check status
sudo systemctl start glance-editor     # Start service
sudo systemctl stop glance-editor      # Stop service  
sudo systemctl restart glance-editor   # Restart service
journalctl -u glance-editor -f         # View logs
```

## File Structure

```
/opt/glance-editor/
├── app.py              # Main Flask application
├── main.py             # Entry point
├── install.sh          # Automated installer
├── templates/          # HTML templates
│   ├── index.html      # Main editor interface
│   ├── login.html      # Login page
│   └── settings.html   # GitHub settings
├── static/             # CSS and assets
│   └── style.css       # Custom styles
├── backups/            # Configuration backups
└── glance-env/         # Python virtual environment
```

## Requirements

- Debian/Ubuntu-based LXC container
- Python 3.7+
- Network access for CDN resources (Bootstrap, CodeMirror, Feather Icons)
- Optional: GitHub account for repository sync

## Security Notes

- Change default admin password
- Use strong SESSION_SECRET
- Consider HTTPS with reverse proxy
- Restrict network access if needed
- Keep Python dependencies updated

## Troubleshooting

**Port 5000 in use:** Change port in main.py and service file
**Permission denied:** Check file permissions and ownership  
**Can't connect:** Verify firewall settings and bind address
**Service won't start:** Check logs with `journalctl -u glance-editor -n 50`

## License

MIT License - Use freely for personal and commercial projects.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request