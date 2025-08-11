# Overview

This project is a production-ready web-based configuration editor for Glance dashboard configurations, optimized for deployment on Proxmox LXC containers. The application provides a secure, user-friendly interface for editing YAML configuration files with comprehensive backup protection, GitHub integration, and automated deployment tools.

# User Preferences

- **Communication style**: Simple, everyday language
- **Primary deployment method**: GitHub installation for ease of use
- **Focus areas**: LXC container deployment, backup safety, automated installation

# System Architecture

## Web Framework Architecture
The application is built using Flask, a lightweight Python web framework, following a simple MVC pattern:
- **Routes**: Defined in `app.py` handling authentication, configuration editing, and backup management
- **Templates**: Jinja2 templates in the `templates/` directory for rendering HTML pages
- **Static Assets**: CSS and client-side JavaScript served from the `static/` directory

## Authentication System
Simple session-based authentication implemented using Flask sessions:
- Username and password stored as environment variables
- Password hashing using Werkzeug's security utilities
- Session-based login state management with decorator-based route protection
- No database required - credentials configured via environment variables

## Configuration Management
File-based configuration system for managing Glance YAML files:
- **Primary Config**: Main Glance configuration file path configurable via environment variable
- **Backup System**: Automatic backup creation before modifications with timestamp-based naming (keeps last 20)
- **Original Protection**: Creates initial backup of existing glance.yml during first installation  
- **Recovery Scripts**: One-command restoration to original configuration via restore-original.sh
- **YAML Processing**: Uses PyYAML library for parsing and validation of configuration files

## Frontend Architecture
Modern web interface using Bootstrap and CodeMirror Editor:
- **UI Framework**: Bootstrap 5 with dark theme for consistent styling
- **Code Editor**: CodeMirror with YAML syntax highlighting, dark theme, and line numbers
- **Icons**: Feather Icons for consistent iconography
- **Responsive Design**: Mobile-friendly interface with fullscreen editor capability
- **Keyboard Shortcuts**: Ctrl+S to save, Ctrl+R to reload configuration

## Deployment System
Production-ready deployment optimized for Proxmox LXC containers:
- **Automated Installer**: Single-command GitHub-based installation with install.sh
- **Environment Setup**: Automatic Python virtual environment creation and dependency management
- **Systemd Integration**: Service creation with proper environment variable handling
- **Original Backup**: Automatic protection of existing glance.yml during first install
- **Recovery Tools**: fix-env.sh and restore-original.sh for maintenance and troubleshooting

## File System Integration
Direct file system operations for configuration management:
- Configuration files read/written directly to the file system  
- Backup directory management with automatic creation (limited to 20 most recent)
- Original configuration protection with timestamped backup files
- Path-based configuration using environment variables for flexibility

## GitHub Integration System
Optional GitHub repository synchronization for version control:
- **Settings Management**: Configuration stored locally in JSON format
- **Repository Sync**: Automatic push to GitHub repository on each save
- **Authentication**: GitHub Personal Access Token with repository permissions
- **Error Handling**: Graceful failure with local save completion if GitHub sync fails
- **Test Connection**: Validate GitHub credentials and repository access

# External Dependencies

## Python Libraries
- **Flask**: Web framework for handling HTTP requests and responses
- **PyYAML**: YAML parsing and generation for configuration file handling
- **Werkzeug**: Security utilities for password hashing and validation
- **Requests**: HTTP library for GitHub API integration
- **JSON**: Configuration storage for GitHub settings (built-in)
- **Base64**: Content encoding for GitHub API (built-in)

## Frontend Libraries (CDN-hosted)
- **Bootstrap 5**: UI framework for responsive design and components
- **CodeMirror**: Advanced code editor with YAML syntax highlighting and dark theme
- **Feather Icons**: Lightweight icon library for UI elements

## Environment Configuration
- `SESSION_SECRET`: Flask session encryption key
- `GLANCE_CONFIG_PATH`: Path to the main Glance configuration file (glance.yml)
- `BACKUP_DIR`: Directory for storing configuration backups
- `EDITOR_USERNAME`: Admin username for authentication
- `EDITOR_PASSWORD`: Admin password for authentication

## File System Dependencies
- Read/write access to Glance configuration files (*.yml format)
- Directory creation permissions for backup storage
- YAML file format compatibility with Glance application