from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, session, abort
import toml
import os
from datetime import datetime
import json
import shutil
import argparse
import requests
from functools import wraps
import werkzeug
import secrets
import time
from urllib.parse import urlparse
# SAML imports
from saml2 import BINDING_HTTP_REDIRECT, BINDING_HTTP_POST
from saml2.config import Config as Saml2Config
from saml2.client import Saml2Client
from saml2.metadata import entity_descriptor
from saml2.response import AuthnResponse
from saml2.saml import name_id_from_string
from authlib.integrations.flask_client import OAuth

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(APP_ROOT, 'templates')
app = Flask(__name__, template_folder=TEMPLATE_DIR)
configured_secret_key = os.environ.get('SECRET_KEY')
app.secret_key = configured_secret_key or secrets.token_hex(32)
is_production = os.environ.get('FLASK_ENV', '').lower() == 'production'
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=os.environ.get('COOKIE_SECURE', '1' if is_production else '0') == '1',
    MAX_CONTENT_LENGTH=int(os.environ.get('MAX_CONTENT_LENGTH', 1024 * 1024 * 1024)),
)

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


def init_safe_join(base_dir, *parts):
    candidate = os.path.join(base_dir, *parts)
    base_real = os.path.realpath(base_dir)
    candidate_real = os.path.realpath(candidate)
    if os.path.commonpath([base_real, candidate_real]) != base_real:
        raise RuntimeError(f'Invalid path configuration under {base_dir}')
    return candidate


SERVER_CONFIG_FILE = init_safe_join(SERVER_DIR, 'ServerConfig.toml')
APP_CONFIG_FILE = init_safe_join(CONFIG_DIR, 'app_config.json')
USER_CONFIG_FILE = init_safe_join(CONFIG_DIR, 'user_config.json')

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
        backup_file = safe_join(BACKUP_DIR, f"ServerConfig_backup_{timestamp}.toml")
        if not backup_file:
            raise ValueError('Invalid backup file path')
        
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
                    old_backup_path = safe_join(BACKUP_DIR, old_backup)
                    if old_backup_path and os.path.isfile(old_backup_path):
                        os.remove(old_backup_path)
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


@app.context_processor
def inject_template_security_context():
    return {'csrf_token': get_or_create_csrf_token()}

@app.route('/')
def index():
    """Main page showing the configuration form"""
    config = load_config()
    return render_template('index.html', config=config)

# --- Authentication Mode Configuration ---
AUTH_MODE = os.environ.get('AUTH_MODE', 'BASIC').upper()  # Options: NO_AUTH, BASIC, SAML, OAUTH
if AUTH_MODE not in ('NO_AUTH', 'BASIC', 'SAML', 'OAUTH'):
    print(f"[WARN] Invalid AUTH_MODE '{AUTH_MODE}', defaulting to BASIC.")
    AUTH_MODE = 'BASIC'
if AUTH_MODE == 'NO_AUTH':
    print("[WARNING] Running with NO_AUTH mode: All endpoints are open! This is NOT recommended for production.")

ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')  # Must be set in production
LOGIN_RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get('LOGIN_RATE_LIMIT_WINDOW_SECONDS', '300'))
LOGIN_RATE_LIMIT_MAX_ATTEMPTS = int(os.environ.get('LOGIN_RATE_LIMIT_MAX_ATTEMPTS', '5'))
login_attempts = {}


def get_client_ip():
    forwarded_for = request.headers.get('X-Forwarded-For', '')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.remote_addr or 'unknown'


def prune_login_attempts(now):
    expired_keys = [
        key for key, attempts in login_attempts.items()
        if all(now - attempt_ts > LOGIN_RATE_LIMIT_WINDOW_SECONDS for attempt_ts in attempts)
    ]
    for key in expired_keys:
        login_attempts.pop(key, None)


def is_login_rate_limited(username):
    now = time.time()
    prune_login_attempts(now)
    key = f"{get_client_ip()}:{username or ''}"
    attempts = [
        attempt_ts for attempt_ts in login_attempts.get(key, [])
        if now - attempt_ts <= LOGIN_RATE_LIMIT_WINDOW_SECONDS
    ]
    login_attempts[key] = attempts
    return len(attempts) >= LOGIN_RATE_LIMIT_MAX_ATTEMPTS


def record_failed_login(username):
    now = time.time()
    prune_login_attempts(now)
    key = f"{get_client_ip()}:{username or ''}"
    login_attempts.setdefault(key, []).append(now)


def clear_login_attempts(username):
    key = f"{get_client_ip()}:{username or ''}"
    login_attempts.pop(key, None)


def get_or_create_csrf_token():
    token = session.get('csrf_token')
    if not token:
        token = secrets.token_urlsafe(32)
        session['csrf_token'] = token
    return token


def validate_csrf():
    expected_token = session.get('csrf_token')
    provided_token = request.headers.get('X-CSRF-Token')
    if not provided_token:
        provided_token = request.form.get('csrf_token')
    if request.is_json:
        data = request.get_json(silent=True) or {}
        provided_token = provided_token or data.get('csrf_token')
    return bool(expected_token and provided_token and secrets.compare_digest(expected_token, provided_token))


def is_safe_redirect_target(target):
    if not target:
        return False
    parsed = urlparse(target)
    if parsed.scheme or parsed.netloc:
        return False
    return target.startswith('/') and not target.startswith('//')


def get_next_redirect_target():
    target = request.args.get('next') or request.form.get('next')
    if is_safe_redirect_target(target):
        return target
    return url_for('index')


def get_post_auth_redirect():
    target = session.pop('post_auth_redirect', None)
    if is_safe_redirect_target(target):
        return target
    return url_for('index')


def sanitize_filename(value):
    filename = os.path.basename((value or '').strip())
    if not filename or filename in {'.', '..'}:
        return None
    return filename


def is_within_directory(base_dir, candidate_path):
    base_real = os.path.realpath(base_dir)
    candidate_real = os.path.realpath(candidate_path)
    return os.path.commonpath([base_real, candidate_real]) == base_real


def safe_join(base_dir, *parts):
    candidate = os.path.join(base_dir, *parts)
    if not is_within_directory(base_dir, candidate):
        return None
    return candidate


def sanitize_log_filename(value):
    filename = sanitize_filename(value)
    if not filename:
        return None
    if filename != value.strip():
        return None
    return filename


def validate_oauth_redirect_uri():
    parsed = urlparse(OAUTH_REDIRECT_URI)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc:
        raise RuntimeError('OAUTH_REDIRECT_URI must be an absolute http or https URL.')


# --- SAML Configuration ---
SAML_IDP_METADATA_URL = os.environ.get('SAML_IDP_METADATA_URL')  # e.g. Authentik or Google Workspace metadata URL
SAML_SP_ENTITY_ID = os.environ.get('SAML_SP_ENTITY_ID', 'http://localhost:5000/saml/metadata')
SAML_SP_ACS_URL = os.environ.get('SAML_SP_ACS_URL', 'http://localhost:5000/saml/acs')
SAML_SP_CERT = os.environ.get('SAML_SP_CERT')  # Optional: path to SP cert (PEM)
SAML_SP_KEY = os.environ.get('SAML_SP_KEY')    # Optional: path to SP key (PEM)

# SAML config loader
def load_saml_config():
    saml_settings = {
        'entityid': SAML_SP_ENTITY_ID,
        'service': {
            'sp': {
                'endpoints': {
                    'assertion_consumer_service': [
                        (SAML_SP_ACS_URL, BINDING_HTTP_POST),
                        (SAML_SP_ACS_URL, BINDING_HTTP_REDIRECT),
                    ],
                },
                'allow_unsolicited': False,
                'authn_requests_signed': False,
                'logout_requests_signed': True,
                'want_assertions_signed': True,
                'want_response_signed': False,
            },
        },
        'metadata': {
            'remote': [
                {'url': SAML_IDP_METADATA_URL},
            ]
        },
        'debug': 1,
    }
    if SAML_SP_CERT and SAML_SP_KEY:
        saml_settings['key_file'] = SAML_SP_KEY
        saml_settings['cert_file'] = SAML_SP_CERT
    saml_config = Saml2Config()
    saml_config.load(saml_settings)
    saml_config.allow_unknown_attributes = True
    return saml_config

def get_saml_client():
    return Saml2Client(config=load_saml_config())

# --- SAML Endpoints ---
@app.route('/saml/login')
def saml_login():
    session['post_auth_redirect'] = get_next_redirect_target()
    saml_client = get_saml_client()
    reqid, info = saml_client.prepare_for_authenticate()
    for key, value in info['headers']:
        if key == 'Location':
            return redirect(value)
    return 'Unable to redirect to SAML IdP', 500

@app.route('/saml/acs', methods=['POST'])
def saml_acs():
    saml_client = get_saml_client()
    saml_response = request.form.get('SAMLResponse')
    if not saml_response:
        return 'Missing SAMLResponse', 400
    authn_response = saml_client.parse_authn_request_response(
        saml_response,
        BINDING_HTTP_POST
    )
    if not authn_response or not authn_response.ava:
        return 'Invalid SAML response', 400
    # Store user info in session
    session['saml_user'] = {
        'name_id': str(authn_response.name_id),
        'attributes': authn_response.ava
    }
    return redirect(get_post_auth_redirect())

@app.route('/saml/metadata')
def saml_metadata():
    saml_config = load_saml_config()
    ed = entity_descriptor(saml_config)
    resp = app.response_class(ed.to_string(), mimetype='text/xml')
    return resp

@app.route('/saml/logout')
def saml_logout():
    session.pop('saml_user', None)
    return redirect('/')

# --- OAuth2 Configuration ---
OAUTH_CLIENT_ID = os.environ.get('OAUTH_CLIENT_ID')
OAUTH_CLIENT_SECRET = os.environ.get('OAUTH_CLIENT_SECRET')
OAUTH_AUTHORIZE_URL = os.environ.get('OAUTH_AUTHORIZE_URL')
OAUTH_TOKEN_URL = os.environ.get('OAUTH_TOKEN_URL')
OAUTH_USERINFO_URL = os.environ.get('OAUTH_USERINFO_URL')
OAUTH_SCOPE = os.environ.get('OAUTH_SCOPE', 'openid email profile')
OAUTH_REDIRECT_URI = os.environ.get('OAUTH_REDIRECT_URI', 'http://localhost:5000/oauth/callback')
OAUTH_PROVIDER = os.environ.get('OAUTH_PROVIDER', 'authentik')

OIDC_DISCOVERY_URL = os.environ.get('OIDC_DISCOVERY_URL')
OIDC_JWKS_URL = os.environ.get('OIDC_JWKS_URL')

if AUTH_MODE == 'OAUTH':
    validate_oauth_redirect_uri()
    oauth = OAuth(app)

    # Register OAuth client with OIDC discovery if available, else manual config
    if OIDC_DISCOVERY_URL:
        oauth.register(
            name='main',
            server_metadata_url=OIDC_DISCOVERY_URL,
            client_id=OAUTH_CLIENT_ID,
            client_secret=OAUTH_CLIENT_SECRET,
            client_kwargs={'scope': OAUTH_SCOPE},
        )
    elif OAUTH_AUTHORIZE_URL and OAUTH_TOKEN_URL and OAUTH_USERINFO_URL:
        extra_args = {}
        if OIDC_JWKS_URL:
            extra_args['jwks_uri'] = OIDC_JWKS_URL
        oauth.register(
            name='main',
            client_id=OAUTH_CLIENT_ID,
            client_secret=OAUTH_CLIENT_SECRET,
            access_token_url=OAUTH_TOKEN_URL,
            access_token_params=None,
            authorize_url=OAUTH_AUTHORIZE_URL,
            authorize_params=None,
            api_base_url=OAUTH_USERINFO_URL.rsplit('/', 1)[0]+'/',
            client_kwargs={'scope': OAUTH_SCOPE},
            **extra_args
        )
    else:
        raise RuntimeError('No valid OIDC discovery URL or manual OAuth endpoints provided.')

@app.route('/oauth/login')
def oauth_login():
    session['post_auth_redirect'] = get_next_redirect_target()
    redirect_uri = OAUTH_REDIRECT_URI
    return oauth.main.authorize_redirect(redirect_uri)

@app.route('/oauth/callback')
def oauth_callback():
    try:
        token = oauth.main.authorize_access_token()
        if OIDC_DISCOVERY_URL:
            userinfo = oauth.main.userinfo()
        else:
            userinfo = oauth.main.get(OAUTH_USERINFO_URL).json()
        session['oauth_user'] = userinfo
        return redirect(get_post_auth_redirect())
    except Exception as e:
        print("OAuth callback error:", e)
        return "OAuth callback error", 500

@app.route('/oauth/logout')
def oauth_logout():
    session.pop('oauth_user', None)
    return redirect('/')

# --- BASIC Auth Session-based Login Endpoint ---
@app.route('/login', methods=['POST'])
def login():
    if AUTH_MODE != 'BASIC':
        return jsonify({'success': False, 'message': 'Login not allowed in this mode'}), 403
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    if is_login_rate_limited(username):
        return jsonify({'success': False, 'message': 'Too many failed login attempts. Try again later.'}), 429
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['basic_user'] = username
        clear_login_attempts(username)
        session['csrf_token'] = secrets.token_urlsafe(32)
        return jsonify({'success': True, 'user': username, 'csrf_token': session['csrf_token']})
    record_failed_login(username)
    return jsonify({'success': False, 'message': 'Invalid username or password'}), 401

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('csrf_token', None)
    session.pop('basic_user', None)
    session.pop('oauth_user', None)
    session.pop('saml_user', None)
    return jsonify({'success': True})

# --- Update check_auth for BASIC to use session ---
def check_auth(auth_header):
    if AUTH_MODE == 'NO_AUTH':
        return True
    if AUTH_MODE == 'BASIC':
        return 'basic_user' in session
    if AUTH_MODE == 'SAML':
        return 'saml_user' in session
    if AUTH_MODE == 'OAUTH':
        return 'oauth_user' in session
    return False

# --- Update requires_auth for BASIC session logic ---
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        print(f"[AUTH DEBUG] Mode: {AUTH_MODE}, Endpoint: {request.path}")
        next_path = request.full_path[:-1] if request.full_path.endswith('?') else request.full_path
        if AUTH_MODE == 'NO_AUTH':
            print("[AUTH DEBUG] NO_AUTH: allowing access")
            return f(*args, **kwargs)
        if not check_auth(request.headers.get('Authorization')):
            if AUTH_MODE == 'SAML':
                print("[AUTH DEBUG] SAML: redirecting to /saml/login")
                return redirect(url_for('saml_login', next=next_path))
            if AUTH_MODE == 'OAUTH':
                print("[AUTH DEBUG] OAUTH: redirecting to /oauth/login")
                return redirect(url_for('oauth_login', next=next_path))
            if AUTH_MODE == 'BASIC':
                print("[AUTH DEBUG] BASIC: returning 401 JSON for login modal")
                # Always return JSON for API, redirect for UI
                if request.accept_mimetypes.accept_json:
                    resp = jsonify({'success': False, 'message': 'Login required'})
                    resp.status_code = 401
                    # Remove any WWW-Authenticate header
                    resp.headers.pop('WWW-Authenticate', None)
                    return resp
                return redirect(url_for('index'))
            print("[AUTH DEBUG] Fallback: returning generic 401")
            # For any other mode, return JSON and remove WWW-Authenticate
            resp = jsonify({'success': False, 'message': 'Unauthorized'})
            resp.status_code = 401
            resp.headers.pop('WWW-Authenticate', None)
            return resp
        print("[AUTH DEBUG] Authenticated: allowing access")
        return f(*args, **kwargs)
    return decorated

@app.before_request
def enforce_request_security():
    get_or_create_csrf_token()
    if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
        if request.endpoint == 'saml_acs':
            return None
        if not validate_csrf():
            if request.path.startswith('/api/') or request.path in ('/login', '/logout'):
                return jsonify({'success': False, 'message': 'CSRF validation failed'}), 403
            abort(403)
    return None


@app.after_request
def apply_security_headers(response):
    response.headers.setdefault('Cache-Control', 'no-store')
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'DENY')
    response.headers.setdefault('Referrer-Policy', 'same-origin')
    response.headers.setdefault('Cross-Origin-Opener-Policy', 'same-origin')
    response.headers.setdefault(
        'Content-Security-Policy',
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "font-src 'self' https://cdnjs.cloudflare.com; "
        "img-src 'self' data: https://www.gravatar.com; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    return response


# --- Enforce SECRET_KEY in production ---
if is_production and not configured_secret_key:
    raise RuntimeError('A strong SECRET_KEY environment variable must be set in production!')

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
    allowed_keys = {'theme', 'customMaps', 'customTags', 'backupRetention', 'serverLogFilename', 'logAutoRefresh'}
    if not isinstance(data, dict):
        return False
    for k in data:
        if k not in allowed_keys:
            return False
    if 'theme' in data and data['theme'] not in ('dark', 'light'):
        return False
    if 'backupRetention' in data:
        try:
            retention = int(data['backupRetention'])
        except (TypeError, ValueError):
            return False
        if retention < 1 or retention > 100:
            return False
    if 'logAutoRefresh' in data:
        try:
            refresh = int(data['logAutoRefresh'])
        except (TypeError, ValueError):
            return False
        if refresh < 0 or refresh > 3600:
            return False
    if 'serverLogFilename' in data:
        if sanitize_log_filename(data['serverLogFilename']) is None:
            return False
    if 'customMaps' in data:
        if not isinstance(data['customMaps'], list) or any(not isinstance(item, str) or len(item) > 512 for item in data['customMaps']):
            return False
    if 'customTags' in data:
        if not isinstance(data['customTags'], list) or any(not isinstance(item, str) or len(item) > 128 for item in data['customTags']):
            return False
    return True

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
@requires_auth
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

@app.route('/backup/<filename>', methods=['POST'])
@requires_auth
def restore_backup(filename):
    safe_filename = sanitize_filename(filename)
    if not safe_filename or not safe_filename.endswith('.toml'):
        flash('Invalid backup filename.', 'error')
        return redirect(url_for('list_backups'))
    backup_path = safe_join(BACKUP_DIR, safe_filename)
    if not backup_path:
        flash('Invalid backup filename.', 'error')
        return redirect(url_for('list_backups'))
    if os.path.exists(backup_path):
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                content = f.read()
            with open(SERVER_CONFIG_FILE, 'w', encoding='utf-8') as f:
                f.write(content)
            flash(f'Backup {safe_filename} restored successfully!', 'success')
        except Exception as e:
            flash(f'Error restoring backup: {str(e)}', 'error')
    else:
        flash('Backup file not found!', 'error')
    
    return redirect(url_for('list_backups'))

@app.route('/backup/delete/<filename>', methods=['POST'])
@requires_auth
def delete_backup(filename):
    safe_filename = sanitize_filename(filename)
    if not safe_filename or not safe_filename.endswith('.toml'):
        flash('Invalid backup filename.', 'error')
        return redirect(url_for('list_backups'))
    backup_path = safe_join(BACKUP_DIR, safe_filename)
    if not backup_path:
        flash('Invalid backup filename.', 'error')
        return redirect(url_for('list_backups'))
    if os.path.exists(backup_path):
        try:
            os.remove(backup_path)
            flash(f'Backup {safe_filename} deleted successfully!', 'success')
        except Exception as e:
            flash(f'Error deleting backup: {str(e)}', 'error')
    else:
        flash('Backup file not found!', 'error')
    return redirect(url_for('list_backups'))

# Remove the /health endpoint and its function
def remove_health_check():
    pass

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
@requires_auth
def get_server_log():
    """API endpoint to get the server log"""
    try:
        user_config = load_user_config()
        log_filename = sanitize_log_filename(user_config.get('serverLogFilename', 'Server.log')) or 'Server.log'
        log_path = safe_join(LOG_DIR, log_filename)
        if not log_path:
            return jsonify({
                'success': False,
                'log': '',
                'message': 'Invalid log filename.'
            }), 400
        
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
        user_config_path = safe_join(CONFIG_DIR, os.path.basename(USER_CONFIG_FILE))
        if not user_config_path:
            raise ValueError('Invalid user config path')
        with open(user_config_path, 'w', encoding='utf-8') as f:
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
        if 'serverLogFilename' in data:
            data['serverLogFilename'] = sanitize_log_filename(data['serverLogFilename'])
        # Auto-complete custom map paths
        if 'customMaps' in data and isinstance(data['customMaps'], list):
            data['customMaps'] = [normalize_custom_map_entry(e) for e in data['customMaps']]
        save_user_config(data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

MODS_DIR = os.path.join(SERVER_DIR, 'Resources', 'Client')

@app.route('/api/mods', methods=['GET'])
@requires_auth
def list_mods():
    """List all zip files in the mods directory"""
    try:
        if not os.path.exists(MODS_DIR):
            return jsonify({'success': True, 'mods': []})
        mods = [f for f in os.listdir(MODS_DIR) if f.lower().endswith('.zip')]
        return jsonify({'success': True, 'mods': mods})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/mods', methods=['POST'])
@requires_auth
def upload_mod():
    """Upload a zip file to the mods directory"""
    if 'mod' not in request.files:
        return jsonify({'success': False, 'message': 'No file part in request'}), 400
    file = request.files['mod']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'}), 400
    if not file.filename.lower().endswith('.zip'):
        return jsonify({'success': False, 'message': 'Only .zip files are allowed'}), 400
    filename = werkzeug.utils.secure_filename(file.filename)
    os.makedirs(MODS_DIR, exist_ok=True)
    save_path = safe_join(MODS_DIR, filename)
    if not save_path:
        return jsonify({'success': False, 'message': 'Invalid filename'}), 400
    try:
        file.save(save_path)
        return jsonify({'success': True, 'message': f'File {filename} uploaded successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/mods/<modname>', methods=['DELETE'])
@requires_auth
def delete_mod(modname):
    """Delete a zip file from the mods directory"""
    if not modname.lower().endswith('.zip'):
        return jsonify({'success': False, 'message': 'Only .zip files can be deleted'}), 400
    filename = werkzeug.utils.secure_filename(modname)
    file_path = safe_join(MODS_DIR, filename)
    if not file_path:
        return jsonify({'success': False, 'message': 'Invalid filename'}), 400
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'message': 'File not found'}), 404
    try:
        os.remove(file_path)
        return jsonify({'success': True, 'message': f'File {filename} deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/mods/<modname>/download', methods=['GET'])
@requires_auth
def download_mod(modname):
    """Download a zip file from the mods directory"""
    if not modname.lower().endswith('.zip'):
        return jsonify({'success': False, 'message': 'Only .zip files can be downloaded'}), 400
    filename = werkzeug.utils.secure_filename(modname)
    file_path = safe_join(MODS_DIR, filename)
    if not file_path:
        return jsonify({'success': False, 'message': 'Invalid filename'}), 400
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'message': 'File not found'}), 404
    try:
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# --- Update /api/auth-info for OAUTH ---
@app.route('/api/auth-info', methods=['GET'])
def get_auth_info():
    mode = AUTH_MODE
    user = None
    if mode == 'BASIC':
        if 'basic_user' in session:
            user = session['basic_user']
    elif mode == 'SAML':
        if 'saml_user' in session:
            user = session['saml_user']['attributes'].get('email', ['SAML User'])[0]
        else:
            user = None
    elif mode == 'OAUTH':
        if 'oauth_user' in session:
            user = session['oauth_user'].get('email') or session['oauth_user'].get('preferred_username')
        else:
            user = None
    return jsonify({'mode': mode, 'user': user, 'csrf_token': get_or_create_csrf_token()})

if __name__ == '__main__':
    if AUTH_MODE == 'BASIC' and not ADMIN_PASSWORD:
        print('[WARNING] ADMIN_PASSWORD is not set! You must set this in production.')
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
