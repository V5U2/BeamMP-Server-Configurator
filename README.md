# BeamMP Server Configurator

A simple web-based configuration tool for BeamMP servers that allows you to easily modify your `ServerConfig.toml` file through a modern, user-friendly interface.

## Features

- 🎛️ **Easy Configuration**: Modify all BeamMP server settings through a web interface
- 🔄 **Automatic Backups**: Creates backups before saving changes
- 📱 **Responsive Design**: Works on desktop and mobile devices
- 🔒 **Safe Operations**: Confirms before restoring backups
- 🎨 **Modern UI**: Beautiful, intuitive interface with Bootstrap 5
- 🐳 **Container Ready**: Full Docker support for easy deployment
- 🎨 **Theme Customization**: Multiple themes and custom settings
- 🗺️ **Map Selection**: Dropdown with all vanilla BeamMP maps
- 🏷️ **Tag Management**: Comprehensive tag selection system

## Prerequisites

- Python 3.7 or higher (for local development)
- Docker and Docker Compose (for container deployment)
- Your `ServerConfig.toml` file

## Quick Start with Docker (Recommended)

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd beammp_server_tool
```

### 2. Deploy with Docker
```bash
# Make deployment script executable
chmod +x deploy.sh

# Deploy the application
./deploy.sh

# Or deploy with production nginx
./deploy.sh --production
```

### 3. Access the Application
- **Development**: http://localhost:5000
- **Production**: http://localhost (with nginx)

## Manual Docker Deployment

### 1. Build and Run
```bash
# Build the container
docker build -t beammp-configurator .

# Run the container
docker run -d \
  --name beammp-configurator \
  -p 5000:5000 \
  -v $(pwd)/configs:/app/configs:ro \
  -v $(pwd)/backups:/app/backups \
  -v $(pwd)/logs:/app/logs \
  beammp-configurator
```

### 2. Using Docker Compose
```bash
# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

## Local Development Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Configuration
```bash
# Copy the example configuration
cp ServerConfig.example.toml ServerConfig.toml

# Edit the configuration with your settings
# Or use the web interface after starting the app
```

### 3. Run the Application
```bash
python app.py
```

### 4. Access the Web Interface
Open your browser and navigate to: `http://localhost:5000`

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CONFIG_DIR` | `.` | Directory containing ServerConfig.toml |
| `BACKUP_DIR` | `backups` | Directory for backup files |
| `SECRET_KEY` | `beammp_config_secret_key_2024` | Flask secret key |
| `PORT` | `5000` | Port to run the application on |
| `HOST` | `0.0.0.0` | Host to bind to |
| `FLASK_ENV` | `production` | Flask environment |

### Directory Structure
```
beammp_server_tool/
├── app.py                 # Main Flask application
├── ServerConfig.toml      # Your BeamMP server configuration
├── ServerConfig.example.toml # Example configuration file
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose configuration
├── nginx.conf            # Nginx reverse proxy configuration
├── deploy.sh             # Deployment script
├── README.md             # This file
├── LICENSE               # MIT License
├── .gitignore            # Git ignore rules
├── .dockerignore         # Docker ignore rules
├── templates/            # HTML templates
│   ├── index.html        # Main configuration interface
│   └── backups.html      # Backup management interface
├── configs/              # Configuration directory (mounted in container)
├── backups/              # Backup directory (mounted in container)
└── logs/                 # Log directory (mounted in container)
```

## Usage

### Web Interface
1. **General Settings**: Configure server name, description, player limits, map, and tags
2. **Advanced Settings**: Set port, resource folder, auth key, and server options
3. **Backups**: View and restore previous configurations
4. **App Settings**: Customize themes, add custom maps/tags, and configure preferences

### Configuration Sections

#### General Settings
- **Server Name**: The name displayed in the server list
- **Description**: Brief description of your server
- **Max Players**: Maximum number of players allowed
- **Max Cars**: Maximum cars per player
- **Map**: Path to the map file (dropdown with all vanilla maps)
- **Tags**: Comma-separated tags for server identification

#### Advanced Settings
- **Port**: Server port (default: 30814)
- **Resource Folder**: Folder containing server resources
- **Auth Key**: Your BeamMP authentication key
- **Private Server**: Whether the server is private
- **Debug Mode**: Enable debug logging
- **Log Chat**: Log chat messages to console
- **Show Error Messages**: Display error messages on startup
- **Send Errors**: Send error reports to BeamMP developers
- **Hide Update Messages**: Hide periodic update notifications

### App Settings
- **Theme Selection**: Choose from BeamNG Dark, Light, Blue, or Green themes
- **Custom Maps**: Add custom maps to the dropdown
- **Custom Tags**: Add custom tags to the selection
- **Auto Save**: Enable automatic saving
- **Backup Retention**: Set how long to keep backup files

## Backup System

The configurator automatically creates backups before saving changes. Backups are stored with timestamps and can be restored through the web interface.

### Restoring Backups
1. Go to the "Backups" tab
2. Click "Restore" next to the backup you want to restore
3. Confirm the restoration

## Production Deployment

### With Nginx Reverse Proxy
```bash
# Deploy with production setup
./deploy.sh --production

# Configure SSL certificates
mkdir -p ssl
# Add your SSL certificates to ./ssl/
# Edit nginx.conf to enable HTTPS
```

### Environment Variables for Production
```bash
export SECRET_KEY="your-secure-secret-key"
export FLASK_ENV="production"
export CONFIG_DIR="/path/to/configs"
export BACKUP_DIR="/path/to/backups"
```

### Security Considerations
- Use HTTPS in production
- Set a strong SECRET_KEY
- Configure firewall rules
- Use rate limiting (configured in nginx.conf)
- Regular backups of configuration files

## Troubleshooting

### Common Issues

1. **"Error loading configuration"**
   - Ensure `ServerConfig.toml` exists in the configs directory
   - Check file permissions
   - Verify the CONFIG_DIR environment variable

2. **"Failed to save configuration"**
   - Ensure you have write permissions in the directory
   - Check if the file is being used by another process
   - Verify volume mounts in Docker

3. **Port already in use**
   - Change the port in docker-compose.yml or environment variables
   - Stop other services using the port

4. **Container won't start**
   - Check Docker logs: `docker-compose logs`
   - Verify Docker and Docker Compose are installed
   - Ensure ports are not in use

5. **Permission denied errors**
   - Set proper permissions: `chmod 755 configs backups logs`
   - Check volume mount permissions

### Docker Commands
```bash
# View container logs
docker-compose logs -f

# Restart the application
docker-compose restart

# Update the application
docker-compose pull && docker-compose up -d

# Access container shell
docker-compose exec beammp-configurator bash

# Check container health
docker-compose ps
```

### Health Check
The application includes a health check endpoint at `/health` that returns:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00"
}
```

## Development

### Adding New Features
1. **New configuration fields**: Update the HTML form in `templates/index.html`
2. **Modify styling**: Edit the CSS in the `<style>` sections
3. **Add new features**: Extend the Flask routes in `app.py`

### Building for Production
```bash
# Build optimized container
docker build --target production -t beammp-configurator:latest .

# Push to registry
docker tag beammp-configurator:latest your-registry/beammp-configurator:latest
docker push your-registry/beammp-configurator:latest
```

## License

This project is open source and available under the MIT License.

## Support

For issues related to:
- **BeamMP Server**: Visit [BeamMP Documentation](https://docs.beammp.com/)
- **This Configurator**: Check the troubleshooting section above or create an issue in the repository
- **Container Deployment**: Check Docker logs and ensure all prerequisites are met 