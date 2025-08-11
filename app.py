import os
import logging
import shutil
import json
import base64
from datetime import datetime
from pathlib import Path
import yaml
import requests
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "glance-editor-secret-key-change-me")

# Configuration
GLANCE_CONFIG_PATH = os.environ.get("GLANCE_CONFIG_PATH", "/opt/glance/glance.yaml")
BACKUP_DIR = os.environ.get("BACKUP_DIR", "./backups")
SETTINGS_FILE = os.path.join(BACKUP_DIR, "github_settings.json")
USERNAME = os.environ.get("EDITOR_USERNAME", "admin")
PASSWORD_HASH = generate_password_hash(os.environ.get("EDITOR_PASSWORD", "admin"))

# Ensure backup directory exists
Path(BACKUP_DIR).mkdir(exist_ok=True)

def cleanup_old_backups():
    """Keep only the last 20 backups"""
    try:
        if not os.path.exists(BACKUP_DIR):
            return
        
        backup_files = []
        for filename in os.listdir(BACKUP_DIR):
            if filename.endswith('.yaml') and filename.startswith('glance_backup_'):
                filepath = os.path.join(BACKUP_DIR, filename)
                backup_files.append((filepath, os.path.getmtime(filepath)))
        
        # Sort by modification time, newest first
        backup_files.sort(key=lambda x: x[1], reverse=True)
        
        # Remove files beyond the 20 most recent
        for filepath, _ in backup_files[20:]:
            os.remove(filepath)
            logging.info(f"Removed old backup: {filepath}")
    
    except Exception as e:
        logging.error(f"Error cleaning up backups: {e}")

def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == USERNAME and password and check_password_hash(PASSWORD_HASH, password):
            session['logged_in'] = True
            flash('Successfully logged in!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Handle user logout"""
    session.pop('logged_in', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """Main editor interface"""
    return render_template('index.html')

@app.route('/api/config')
@login_required
def get_config():
    """API endpoint to get current configuration"""
    try:
        if not os.path.exists(GLANCE_CONFIG_PATH):
            # Create a default configuration if it doesn't exist
            default_config = """# Glance Configuration File
# Edit this configuration to customize your dashboard

pages:
  - name: Home
    columns:
      - size: small
        widgets:
          - type: calendar
            first-day-of-week: monday

          - type: weather
            location: New York, NY
            units: metric
            hour-format: 12h

      - size: full
        widgets:
          - type: rss
            limit: 10
            collapse-after: 3
            cache: 12h
            feeds:
              - url: https://feeds.feedburner.com/TechCrunch
                title: TechCrunch

# Theme configuration
theme:
  background-color: 240 240 240
  primary-color: 56 58 64

# Server configuration
server:
  host: 0.0.0.0
  port: 8080
"""
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(GLANCE_CONFIG_PATH), exist_ok=True)
            
            with open(GLANCE_CONFIG_PATH, 'w', encoding='utf-8') as f:
                f.write(default_config)
            
            return jsonify({
                'success': True,
                'content': default_config,
                'path': GLANCE_CONFIG_PATH,
                'message': 'Created new configuration file'
            })
        
        with open(GLANCE_CONFIG_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            'success': True,
            'content': content,
            'path': GLANCE_CONFIG_PATH
        })
    
    except Exception as e:
        logging.error(f"Error reading config file: {e}")
        return jsonify({
            'success': False,
            'error': f'Error reading configuration file: {str(e)}',
            'content': ''
        })

@app.route('/api/validate', methods=['POST'])
@login_required
def validate_yaml():
    """API endpoint to validate YAML content"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'valid': False, 'error': 'No data provided'})
        content = data.get('content', '')
        
        if not content.strip():
            return jsonify({
                'valid': False,
                'error': 'Configuration content is empty'
            })
        
        # Try to parse the YAML
        yaml.safe_load(content)
        
        return jsonify({
            'valid': True,
            'message': 'YAML is valid'
        })
    
    except yaml.YAMLError as e:
        return jsonify({
            'valid': False,
            'error': f'YAML syntax error: {str(e)}'
        })
    except Exception as e:
        logging.error(f"Error validating YAML: {e}")
        return jsonify({
            'valid': False,
            'error': f'Validation error: {str(e)}'
        })

@app.route('/api/save', methods=['POST'])
@login_required
def save_config():
    """API endpoint to save configuration with backup"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'})
        content = data.get('content', '')
        
        if not content.strip():
            return jsonify({
                'success': False,
                'error': 'Cannot save empty configuration'
            })
        
        # Validate YAML before saving
        try:
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            return jsonify({
                'success': False,
                'error': f'Invalid YAML: {str(e)}'
            })
        
        # Create backup if original file exists
        if os.path.exists(GLANCE_CONFIG_PATH):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"glance_backup_{timestamp}.yaml"
            backup_path = os.path.join(BACKUP_DIR, backup_filename)
            
            shutil.copy2(GLANCE_CONFIG_PATH, backup_path)
            logging.info(f"Created backup: {backup_path}")
            
            # Keep only the last 20 backups
            cleanup_old_backups()
        
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(GLANCE_CONFIG_PATH), exist_ok=True)
        
        # Save the new configuration
        with open(GLANCE_CONFIG_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logging.info(f"Configuration saved to {GLANCE_CONFIG_PATH}")
        
        # Check if GitHub sync is enabled and push to repository
        github_message = ""
        github_settings = load_github_settings()
        if github_settings.get('enabled', False):
            try:
                success, message = push_to_github(content, github_settings)
                if success:
                    github_message = " (Also pushed to GitHub)"
                    logging.info("Configuration pushed to GitHub successfully")
                else:
                    github_message = f" (GitHub sync failed: {message})"
                    logging.warning(f"GitHub sync failed: {message}")
            except Exception as e:
                github_message = f" (GitHub sync error: {str(e)})"
                logging.error(f"GitHub sync error: {e}")
        
        return jsonify({
            'success': True,
            'message': f'Configuration saved successfully{github_message}'
        })
    
    except Exception as e:
        logging.error(f"Error saving config: {e}")
        return jsonify({
            'success': False,
            'error': f'Error saving configuration: {str(e)}'
        })

@app.route('/api/backups')
@login_required
def list_backups():
    """API endpoint to list the most recent backup only"""
    try:
        backup_files = []
        
        if os.path.exists(BACKUP_DIR):
            for filename in os.listdir(BACKUP_DIR):
                if filename.endswith('.yaml') and filename.startswith('glance_backup_'):
                    filepath = os.path.join(BACKUP_DIR, filename)
                    stat = os.stat(filepath)
                    backup_files.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
        
        # Sort by modification time, newest first and return only the most recent
        backup_files.sort(key=lambda x: x['modified'], reverse=True)
        recent_backup = backup_files[:1] if backup_files else []
        
        return jsonify({
            'success': True,
            'backups': recent_backup
        })
    
    except Exception as e:
        logging.error(f"Error listing backups: {e}")
        return jsonify({
            'success': False,
            'error': f'Error listing backups: {str(e)}',
            'backups': []
        })

@app.route('/api/restore/<filename>')
@login_required
def restore_backup(filename):
    """API endpoint to restore from backup"""
    try:
        # Security check: ensure filename is safe
        if '..' in filename or '/' in filename:
            return jsonify({
                'success': False,
                'error': 'Invalid filename'
            })
        
        backup_path = os.path.join(BACKUP_DIR, filename)
        
        if not os.path.exists(backup_path):
            return jsonify({
                'success': False,
                'error': 'Backup file not found'
            })
        
        with open(backup_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            'success': True,
            'content': content,
            'message': f'Backup {filename} loaded successfully'
        })
    
    except Exception as e:
        logging.error(f"Error restoring backup: {e}")
        return jsonify({
            'success': False,
            'error': f'Error restoring backup: {str(e)}'
        })

@app.route('/api/undo')
@login_required
def undo_changes():
    """API endpoint to revert to last saved configuration"""
    try:
        if not os.path.exists(GLANCE_CONFIG_PATH):
            return jsonify({
                'success': False,
                'error': 'No saved configuration found'
            })
        
        with open(GLANCE_CONFIG_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            'success': True,
            'content': content,
            'message': 'Reverted to last saved configuration'
        })
    
    except Exception as e:
        logging.error(f"Error undoing changes: {e}")
        return jsonify({
            'success': False,
            'error': f'Error reverting changes: {str(e)}'
        })

# GitHub integration functions
def load_github_settings():
    """Load GitHub settings from file"""
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logging.error(f"Error loading GitHub settings: {e}")
    return {}

def save_github_settings(settings):
    """Save GitHub settings to file"""
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        logging.error(f"Error saving GitHub settings: {e}")
        return False

def push_to_github(content, settings):
    """Push configuration to GitHub repository"""
    try:
        # GitHub API endpoints
        repo = settings['repo']
        branch = settings['branch']
        path = settings['path']
        token = settings['token']
        commit_message = settings.get('commit_message', 'Update glance configuration')
        
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Glance-Config-Editor'
        }
        
        # Get current file SHA (if it exists)
        get_url = f'https://api.github.com/repos/{repo}/contents/{path}'
        get_params = {'ref': branch}
        
        response = requests.get(get_url, headers=headers, params=get_params)
        
        # Prepare content for GitHub API
        content_encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        data = {
            'message': commit_message,
            'content': content_encoded,
            'branch': branch
        }
        
        # If file exists, include SHA for update
        if response.status_code == 200:
            file_info = response.json()
            data['sha'] = file_info['sha']
        
        # Create or update file
        put_url = f'https://api.github.com/repos/{repo}/contents/{path}'
        put_response = requests.put(put_url, headers=headers, json=data)
        
        if put_response.status_code in [200, 201]:
            return True, "Successfully pushed to GitHub"
        else:
            error_msg = put_response.json().get('message', 'Unknown error')
            return False, f"GitHub API error: {error_msg}"
            
    except Exception as e:
        logging.error(f"Error pushing to GitHub: {e}")
        return False, f"Error pushing to GitHub: {str(e)}"

def test_github_connection(settings):
    """Test GitHub API connection and repository access"""
    try:
        repo = settings['repo']
        token = settings['token']
        
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Glance-Config-Editor'
        }
        
        # Test repository access
        url = f'https://api.github.com/repos/{repo}'
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            repo_info = response.json()
            return True, f"Connected to {repo_info['full_name']}"
        elif response.status_code == 404:
            return False, "Repository not found or no access"
        elif response.status_code == 401:
            return False, "Invalid GitHub token"
        else:
            error_msg = response.json().get('message', 'Unknown error')
            return False, f"GitHub API error: {error_msg}"
            
    except Exception as e:
        return False, f"Connection error: {str(e)}"

# GitHub settings routes
@app.route('/settings')
@login_required
def settings():
    """Settings page"""
    return render_template('settings.html')

@app.route('/api/github-settings', methods=['GET', 'POST'])
@login_required
def github_settings():
    """API endpoint for GitHub settings"""
    if request.method == 'GET':
        settings = load_github_settings()
        # Don't return the token for security
        safe_settings = settings.copy()
        if 'token' in safe_settings:
            safe_settings['token'] = '***' if safe_settings['token'] else ''
        
        return jsonify({
            'success': True,
            'settings': safe_settings
        })
    
    elif request.method == 'POST':
        try:
            new_settings = request.get_json()
            
            # Validate required fields if GitHub is enabled
            if new_settings.get('enabled', False):
                required_fields = ['token', 'repo', 'branch', 'path']
                for field in required_fields:
                    if not new_settings.get(field):
                        return jsonify({
                            'success': False,
                            'error': f'Missing required field: {field}'
                        })
            
            # Merge with existing settings to preserve token if not provided
            current_settings = load_github_settings()
            if new_settings.get('token') == '***':
                new_settings['token'] = current_settings.get('token', '')
            
            if save_github_settings(new_settings):
                return jsonify({
                    'success': True,
                    'message': 'Settings saved successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to save settings'
                })
        
        except Exception as e:
            logging.error(f"Error handling GitHub settings: {e}")
            return jsonify({
                'success': False,
                'error': f'Error saving settings: {str(e)}'
            })

@app.route('/api/test-github')
@login_required
def test_github():
    """API endpoint to test GitHub connection"""
    try:
        settings = load_github_settings()
        
        if not settings.get('enabled', False):
            return jsonify({
                'success': False,
                'error': 'GitHub integration is not enabled'
            })
        
        success, message = test_github_connection(settings)
        return jsonify({
            'success': success,
            'message' if success else 'error': message
        })
    
    except Exception as e:
        logging.error(f"Error testing GitHub connection: {e}")
        return jsonify({
            'success': False,
            'error': f'Error testing connection: {str(e)}'
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
