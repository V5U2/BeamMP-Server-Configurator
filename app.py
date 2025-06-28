from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import toml
import os
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'beammp_config_secret_key_2024')

# Configuration from environment variables
CONFIG_DIR = os.environ.get('CONFIG_DIR', '.')
BACKUP_DIR = os.environ.get('BACKUP_DIR', 'backups')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'ServerConfig.toml')

# Ensure directories exist
for directory in [BACKUP_DIR, CONFIG_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

def load_config():
    """Load the TOML configuration file"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return toml.load(f)
    except FileNotFoundError:
        # Return default config if file doesn't exist
        return {
            'General': {
                'Name': 'BeamMP Server',
                'Description': 'BeamMP Server',
                'Port': 30814,
                'MaxPlayers': 8,
                'MaxCars': 10,
                'Map': '/levels/utah/info.json',
                'ResourceFolder': 'Resources',
                'Tags': 'Freeroam',
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
        }
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

def save_config(config_data):
    """Save the configuration to TOML file with backup"""
    try:
        # Create backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(BACKUP_DIR, f"ServerConfig_backup_{timestamp}.toml")
        
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                current_content = f.read()
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(current_content)
        
        # Save new config
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            toml.dump(config_data, f)
        
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

@app.route('/api/config', methods=['GET'])
def get_config():
    """API endpoint to get current configuration"""
    config = load_config()
    return jsonify(config)

@app.route('/api/config', methods=['POST'])
def update_config():
    """API endpoint to update configuration"""
    try:
        data = request.get_json()
        
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
def restore_backup(filename):
    """Restore a backup file"""
    backup_path = os.path.join(BACKUP_DIR, filename)
    if os.path.exists(backup_path):
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                content = f.read()
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                f.write(content)
            flash(f'Backup {filename} restored successfully!', 'success')
        except Exception as e:
            flash(f'Error restoring backup: {str(e)}', 'error')
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

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Get host from environment variable or default to 0.0.0.0 for containers
    host = os.environ.get('HOST', '0.0.0.0')
    
    # Set debug mode based on environment
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"Starting BeamMP Configurator on {host}:{port}")
    print(f"Config file: {CONFIG_FILE}")
    print(f"Backup directory: {BACKUP_DIR}")
    
    app.run(debug=debug, host=host, port=port) 