from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
import toml
import os
from datetime import datetime
import json
import shutil
import argparse
import requests
import base64
from functools import wraps

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(APP_ROOT, 'templates')
app = Flask(__name__, template_folder=TEMPLATE_DIR)
app.secret_key = os.environ.get('SECRET_KEY', 'beammp_config_secret_key_2024')

# Parse command-line arguments for development overrides
parser = argparse.ArgumentParser(description="BeamMP Server Configurator")
parser.add_argument('--config-dir', type=str, help='Path to app config directory')
parser.add_argument('--backup-dir', type=str, help='Path to app backup directory')
parser.add_argument('--server-dir', type=str, help='Path to server data directory')
args, unknown = parser.parse_known_args()

# Configuration from environment variables or flags
CONFIG_DIR = args.config_dir or os.environ.get('CONFIG_DIR', '/config')
BACKUP_DIR = args.backup_dir or os.environ.get('BACKUP_DIR', '/backup')
SERVER_DIR = args.server_dir or os.environ.get('SERVER_DIR', '/server')
LOG_DIR = SERVER_DIR
SERVER_CONFIG_FILE = os.path.join(SERVER_DIR, 'ServerConfig.toml')
APP_CONFIG_FILE = os.path.join(CONFIG_DIR, 'app_config.json')
USER_CONFIG_FILE = os.path.join(CONFIG_DIR, 'user_config.json')

DOCKER_PROXY_URL = os.environ.get('DOCKER_HOST', 'http://docker-proxy:2375')
BEAMMP_CONTAINER_NAME = os.environ.get('BEAMMP_CONTAINER_NAME', 'beammp-server')

# Ensure directories exist
for directory in [BACKUP_DIR, CONFIG_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Get the directory where this script is located
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_APP_CONFIG_FILE = os.path.join(APP_ROOT, 'default_app_config.json')
if not os.path.exists(APP_CONFIG_FILE):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    shutil.copy(DEFAULT_APP_CONFIG_FILE, APP_CONFIG_FILE)
    print(f"Created default app config at {APP_CONFIG_FILE}")

def load_app_config():
    """Load the application configuration from JSON file"""
    try:
        with open(APP_CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {APP_CONFIG_FILE} not found, using default configuration")
        return {}
    except Exception as e:
        print(f"Error loading app config: {e}")
        return {}

def get_server_defaults():
    """Get server default configuration"""
    app_config = load_app_config()
    return app_config.get('serverDefaults', {
        'General': {
            'Name': 'BeamMP Server',
            'Description': 'BeamMP Server',
            'Port': 30814,
            'MaxPlayers': 8,
            'MaxCars': 10,
            'Map': '/levels/utah/info.json',
            'ResourceFolder': 'Resources',
            'Tags': 'Freeroam',
            'Mods': '',
            'AuthKey': '',
            'Private': True,
            'Debug': False,
            'LogChat': False
        },
        'Misc': {
            'SendErrorsShowMessage': False,
            'SendErrors': False,
            'ImScaredOfUpdates': False
        }
    })

def load_config():
    """Load the TOML configuration file"""
    try:
        with open(SERVER_CONFIG_FILE, 'r', encoding='utf-8') as f:
            return toml.load(f)
    except FileNotFoundError:
        # Return default config if file doesn't exist
        return get_server_defaults()
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

def save_config(config_data):
    """Save the configuration to TOML file with backup and enforce backup retention by number of backups"""
    try:
        # Create backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(BACKUP_DIR, f"ServerConfig_backup_{timestamp}.toml")
        
        if os.path.exists(SERVER_CONFIG_FILE):
            with open(SERVER_CONFIG_FILE, 'r', encoding='utf-8') as f:
                current_content = f.read()
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(current_content)
        
        # Save new config
        with open(SERVER_CONFIG_FILE, 'w', encoding='utf-8') as f:
            toml.dump(config_data, f)
        
        # Enforce backup retention by number of backups
        retention_count = 10  # Default
        try:
            user_config = load_user_config()
            retention_count = int(user_config.get('backupRetention', 10))
        except Exception:
            pass
        
        backups = [f for f in os.listdir(BACKUP_DIR) if f.endswith('.toml')]
        backups.sort(reverse=True)  # Newest first
        if len(backups) > retention_count:
            for old_backup in backups[retention_count:]:
                try:
                    os.remove(os.path.join(BACKUP_DIR, old_backup))
                except Exception:
                    pass
        
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def get_field_type(value):
    """Determine the type of a configuration field"""
    if isinstance(value, bool):
        return 'checkbox'
    elif isinstance(value, int):
        return 'number'
    elif isinstance(value, str):
        return 'text'
    else:
        return 'text'

@app.route('/')
def index():
    """Main page showing the configuration form"""
    config = load_config()
    return render_template('index.html', config=config)

# --- Security: HTTP Basic Auth Decorator ---
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')  # Must be set in production

def check_auth(auth_header):
    if not auth_header or not auth_header.startswith('Basic '):
        return False
    try:
        encoded = auth_header.split(' ', 1)[1]
        decoded = base64.b64decode(encoded).decode('utf-8')
        username, password = decoded.split(':', 1)
        return username == ADMIN_USERNAME and password == ADMIN_PASSWORD
    except Exception:
        return False

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization')
        if not check_auth(auth):
            return ('Unauthorized', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})
        return f(*args, **kwargs)
    return decorated

# --- Enforce SECRET_KEY in production ---
if os.environ.get('FLASK_ENV', '').lower() == 'production' and not os.environ.get('SECRET_KEY'):
    raise RuntimeError('SECRET_KEY environment variable must be set in production!')

# --- Sanitize file path inputs ---
# (used in restore_backup and delete_backup)

# --- Validate config/user-config JSON ---
def validate_config_data(data):
    # Only allow dict with 'General' and/or 'Misc' keys, each mapping to dict
    if not isinstance(data, dict):
        return False
    for section in data:
        if section not in ('General', 'Misc'):
            return False
        if not isinstance(data[section], dict):
            return False
    return True

def validate_user_config_data(data):
    # Only allow dict with known keys
    allowed_keys = {'theme', 'customMaps', 'customTags', 'backupRetention', 'serverLogFilename'}
    if not isinstance(data, dict):
        return False
    for k in data:
        if k not in allowed_keys:
            return False
    return True

# --- Restrict Docker proxy access at the network level (see docker-compose.yml comment) ---

# --- Apply auth and validation to sensitive endpoints ---
@app.route('/api/config', methods=['GET'])
@requires_auth
def get_config():
    config = load_config()
    return jsonify(config)

@app.route('/api/app-config', methods=['GET'])
@requires_auth
def get_app_config():
    app_config = load_app_config()
    return jsonify(app_config)

@app.route('/api/maps', methods=['GET'])
def get_maps():
    """API endpoint to get available maps"""
    app_config = load_app_config()
    maps = app_config.get('defaultMaps', [])
    return jsonify(maps)

@app.route('/api/tags', methods=['GET'])
def get_tags():
    """API endpoint to get available tags"""
    app_config = load_app_config()
    tags = app_config.get('defaultTags', {})
    return jsonify(tags)

@app.route('/api/config', methods=['POST'])
@requires_auth
def update_config():
    try:
        data = request.get_json()
        if not validate_config_data(data):
            return jsonify({'success': False, 'message': 'Invalid config data'}), 400
        
        # Convert string values to appropriate types
        for section in data:
            for key, value in data[section].items():
                if isinstance(value, str):
                    # Try to convert to boolean
                    if value.lower() in ['true', 'false']:
                        data[section][key] = value.lower() == 'true'
                    # Try to convert to integer
                    elif value.isdigit():
                        data[section][key] = int(value)
        
        if save_config(data):
            return jsonify({'success': True, 'message': 'Configuration saved successfully!'})
        else:
            return jsonify({'success': False, 'message': 'Failed to save configuration'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/backups')
def list_backups():
    """Show list of backup files"""
    backups = []
    if os.path.exists(BACKUP_DIR):
        for file in os.listdir(BACKUP_DIR):
            if file.endswith('.toml'):
                file_path = os.path.join(BACKUP_DIR, file)
                stat = os.stat(file_path)
                backups.append({
                    'name': file,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
    
    backups.sort(key=lambda x: x['modified'], reverse=True)
    return render_template('backups.html', backups=backups)

@app.route('/backup/<filename>')
@requires_auth
def restore_backup(filename):
    backup_path = os.path.join(BACKUP_DIR, os.path.basename(filename))
    if os.path.exists(backup_path):
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                content = f.read()
            with open(SERVER_CONFIG_FILE, 'w', encoding='utf-8') as f:
                f.write(content)
            flash(f'Backup {filename} restored successfully!', 'success')
        except Exception as e:
            flash(f'Error restoring backup: {str(e)}', 'error')
    else:
        flash('Backup file not found!', 'error')
    
    return redirect(url_for('list_backups'))

@app.route('/backup/delete/<filename>', methods=['POST'])
@requires_auth
def delete_backup(filename):
    backup_path = os.path.join(BACKUP_DIR, os.path.basename(filename))
    if os.path.exists(backup_path):
        try:
            os.remove(backup_path)
            flash(f'Backup {filename} deleted successfully!', 'success')
        except Exception as e:
            flash(f'Error deleting backup: {str(e)}', 'error')
    else:
        flash('Backup file not found!', 'error')
    return redirect(url_for('list_backups'))

@app.route('/health')
def health_check():
    """Health check endpoint for container orchestration"""
    try:
        # Try to load config to ensure the app is working
        load_config()
        return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/api/containers', methods=['GET'])
@requires_auth
def list_containers():
    try:
        resp = requests.get(f"{DOCKER_PROXY_URL}/containers/json?all=1", timeout=3)
        resp.raise_for_status()
        containers = resp.json()
        result = [
            {
                'id': c['Id'],
                'names': c.get('Names', []),
                'image': c.get('Image'),
                'status': c.get('Status'),
                'state': c.get('State'),
            }
            for c in containers
        ]
        return jsonify({'success': True, 'containers': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

def find_container_id_by_name(container_name):
    try:
        resp = requests.get(f"{DOCKER_PROXY_URL}/containers/json?all=1", timeout=3)
        resp.raise_for_status()
        containers = resp.json()
        debug_names = []
        for c in containers:
            for n in c.get('Names', []):
                debug_names.append(n)
                if n == f"/{container_name}":
                    return c['Id'], n.strip('/'), debug_names
        return None, None, debug_names
    except Exception as e:
        return None, None, [f'Exception: {str(e)}']

@app.route('/api/restart-server', methods=['POST'])
@requires_auth
def api_restart_server():
    container_id, resolved_name, debug_names = find_container_id_by_name(BEAMMP_CONTAINER_NAME)
    if not container_id:
        return jsonify({'success': False, 'message': f'BeamMP container "{BEAMMP_CONTAINER_NAME}" not found', 'containers_seen': debug_names}), 404
    try:
        resp = requests.post(f"{DOCKER_PROXY_URL}/containers/{container_id}/restart", timeout=10)
        if resp.status_code == 204:
            return jsonify({'success': True, 'message': f'BeamMP server restarted successfully', 'container_name': resolved_name, 'container_id': container_id}), 200
        else:
            return jsonify({'success': False, 'message': f'Failed to restart container: {resp.text}', 'containers_seen': debug_names}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error restarting container: {str(e)}', 'containers_seen': debug_names}), 500

@app.route('/api/server-status', methods=['GET'])
@requires_auth
def api_server_status():
    container_id, resolved_name, debug_names = find_container_id_by_name(BEAMMP_CONTAINER_NAME)
    if not container_id:
        return jsonify({'success': False, 'message': f'BeamMP container "{BEAMMP_CONTAINER_NAME}" not found', 'status': 'not_found', 'containers_seen': debug_names}), 404
    try:
        resp = requests.get(f"{DOCKER_PROXY_URL}/containers/{container_id}/json", timeout=3)
        resp.raise_for_status()
        info = resp.json()
        status = info['State']['Status']
        created = info['Created']
        image = info['Config']['Image']
        return jsonify({
            'success': True,
            'status': status,
            'container_name': resolved_name,
            'container_id': container_id,
            'created': created,
            'image': image
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error getting server status: {str(e)}', 'status': 'error', 'containers_seen': debug_names}), 500

@app.route('/api/server-log', methods=['GET'])
def get_server_log():
    """API endpoint to get the server log"""
    try:
        user_config = load_user_config()
        log_filename = user_config.get('serverLogFilename', 'Server.log')
        log_path = os.path.join(LOG_DIR, log_filename)
        
        if not os.path.exists(log_path):
            return jsonify({
                'success': False, 
                'log': '', 
                'message': f'Log file "{log_filename}" not found in logs directory. Please check the log filename in App Settings or ensure the server has generated logs.'
            })
        
        with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
            log_content = f.read()
        return jsonify({'success': True, 'log': log_content})
    except PermissionError:
        return jsonify({
            'success': False, 
            'log': '', 
            'message': f'Permission denied reading log file "{log_filename}". Check file permissions.'
        })
    except Exception as e:
        return jsonify({
            'success': False, 
            'log': '', 
            'message': f'Error reading log file: {str(e)}'
        })

def demux_docker_logs(log_bytes):
    # Docker multiplexed logs: each frame is 8 bytes header + payload
    out = []
    i = 0
    while i + 8 <= len(log_bytes):
        header = log_bytes[i:i+8]
        length = int.from_bytes(header[4:8], 'big')
        payload = log_bytes[i+8:i+8+length]
        try:
            out.append(payload.decode('utf-8', errors='replace'))
        except Exception:
            out.append(str(payload))
        i += 8 + length
    return ''.join(out)

@app.route('/api/container-log', methods=['GET'])
@requires_auth
def get_container_log():
    container_id, resolved_name, debug_names = find_container_id_by_name(BEAMMP_CONTAINER_NAME)
    if not container_id:
        return jsonify({'success': False, 'log': '', 'message': f'Container "{BEAMMP_CONTAINER_NAME}" not found', 'containers_seen': debug_names}), 404
    try:
        resp = requests.get(f"{DOCKER_PROXY_URL}/containers/{container_id}/logs?tail=200&stdout=1&stderr=1", timeout=5)
        if resp.status_code == 200:
            logs = demux_docker_logs(resp.content)
            return jsonify({'success': True, 'log': logs})
        else:
            return jsonify({'success': False, 'log': '', 'message': f'Failed to get logs: {resp.text}', 'containers_seen': debug_names})
    except Exception as e:
        return jsonify({'success': False, 'log': '', 'message': str(e), 'containers_seen': debug_names})

# Helper to load user config

def load_user_config():
    try:
        with open(USER_CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def save_user_config(data):
    try:
        with open(USER_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving user config: {e}")
        return False

def normalize_custom_map_entry(entry):
    parts = entry.split('|')
    if len(parts) == 2:
        name = parts[0].strip()
        path = parts[1].strip()
        if '/' not in path and not path.endswith('.json'):
            path = f"/levels/{path}/info.json"
        return f"{name}|{path}"
    else:
        val = entry.strip()
        if '/' not in val and not val.endswith('.json'):
            val = f"/levels/{val}/info.json"
        return val

@app.route('/api/user-config', methods=['GET'])
@requires_auth
def get_user_config():
    config = load_user_config()
    # Normalize customMaps to always use full path format
    if 'customMaps' in config and isinstance(config['customMaps'], list):
        config['customMaps'] = [normalize_custom_map_entry(e) for e in config['customMaps']]
    return jsonify(config)

@app.route('/api/user-config', methods=['POST'])
@requires_auth
def update_user_config():
    try:
        data = request.get_json()
        if not validate_user_config_data(data):
            return jsonify({'success': False, 'message': 'Invalid user config data'}), 400
        # Auto-complete custom map paths
        if 'customMaps' in data and isinstance(data['customMaps'], list):
            data['customMaps'] = [normalize_custom_map_entry(e) for e in data['customMaps']]
        save_user_config(data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    # Get host from environment variable or default to 0.0.0.0 for containers
    host = os.environ.get('HOST', '0.0.0.0')
    # Set debug mode based on environment variable
    debug = (
        os.environ.get('FLASK_DEBUG', '0') == '1' or
        os.environ.get('FLASK_ENV', '').lower() == 'development'
    )
    print(f"Starting BeamMP Configurator on {host}:{port}")
    print(f"Server config file: {SERVER_CONFIG_FILE}")
    print(f"Backup directory: {BACKUP_DIR}")
    print(f"Flask debug mode: {debug}")
    app.run(debug=debug, host=host, port=port) 