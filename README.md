# Glance Configuration Editor

A lightweight web-based editor for Glance dashboard configuration files, designed for easy deployment on Proxmox LXC containers.

## Features

- **YAML Syntax Highlighting**: CodeMirror editor with dark theme and line numbers
- **Real-time Validation**: Automatic YAML validation as you type
- **Automatic Backups**: Keeps the last 20 configuration backups with timestamps
- **Original Backup Protection**: Creates initial backup of existing glance.yml on first install
- **Easy Recovery**: One-command restoration to original configuration
- **GitHub Integration**: Optional sync to GitHub repository on save
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Keyboard Shortcuts**: Ctrl+S to save, Ctrl+R to reload

## Installation

### GitHub Installation (Recommended)

**One-Command Install:**
```bash
# Install git and clone repository
apt update && apt install git -y
git clone https://github.com/TetchyTech/glance-config-editor.git /opt/glance-editor
cd /opt/glance-editor
chmod +x install.sh
sudo ./install.sh
```

**What the installer does:**
- Creates Python virtual environment
- Installs all required dependencies
- Backs up your existing glance.yml file safely
- Creates systemd service for automatic startup
- Sets up secure default configuration

### Manual Step-by-Step Installation
```bash
# Install system dependencies
apt update && apt install python3 python3-pip python3-venv git -y

# Clone repository from GitHub
git clone https://github.com/TetchyTech/glance-config-editor.git /opt/glance-editor
cd /opt/glance-editor

# Set up Python environment manually
python3 -m venv glance-env
source glance-env/bin/activate
pip install flask pyyaml werkzeug gunicorn requests

# Configure environment variables
cp .env.example .env
nano .env  # Edit your settings

# Start application manually
python main.py
```

### Legacy Installation (Without GitHub)
If you cannot use GitHub, see [DEPLOYMENT.md](./DEPLOYMENT.md) for manual file transfer methods.

## Configuration

Edit `/opt/glance-editor/.env`:
```bash
export SESSION_SECRET="your-secure-random-string"
export GLANCE_CONFIG_PATH="/path/to/your/glance.yml"
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
├── app.py                   # Main Flask application
├── main.py                  # Entry point
├── install.sh               # Automated installer
├── fix-env.sh               # Environment troubleshooting script
├── restore-original.sh      # Restore to original backup
├── .env.example             # Environment configuration template
├── templates/               # HTML templates
│   ├── index.html           # Main editor interface
│   ├── login.html           # Login page
│   └── settings.html        # GitHub settings
├── static/                  # CSS and assets
│   └── style.css            # Custom styles
├── backups/                 # Configuration backups
│   └── glance_original_backup_*.yml   # Original backup
└── glance-env/              # Python virtual environment
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

## Recovery and Maintenance

### Restore Original Configuration
If you need to revert to your original glance.yml:
```bash
cd /opt/glance-editor
sudo ./restore-original.sh
```

### Fix Environment Issues  
If the service won't start after system changes:
```bash
cd /opt/glance-editor
sudo ./fix-env.sh
```

## Troubleshooting

**Service won't start:** Run `sudo ./fix-env.sh` to fix environment issues  
**Port 5000 in use:** Change port in main.py and service file
**Permission denied:** Check file permissions and ownership  
**Can't connect:** Verify firewall settings and bind address
**Need original config:** Run `sudo ./restore-original.sh`
**Check logs:** Use `journalctl -u glance-editor -f` to view real-time logs

## License

MIT License - Use freely for personal and commercial projects.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request
