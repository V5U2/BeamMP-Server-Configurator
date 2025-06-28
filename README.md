# BeamMP Server Configurator

A modern web-based configuration tool for BeamMP servers with a beautiful UI, automatic backups, and Docker container management.

## Features

- 🎨 **Modern UI**: Beautiful, responsive interface with dark/light themes
- ⚙️ **Easy Configuration**: Intuitive form-based server configuration
- 💾 **Automatic Backups**: Configurable backup system with retention policies
- 🐳 **Docker Integration**: Built-in Docker container management
- 🔄 **Server Restart**: Restart BeamMP server containers directly from the UI
- 📊 **Server Status**: Real-time container status monitoring
- 🏷️ **Tag Management**: Comprehensive server tag selection system
- 🗺️ **Map Selection**: Dropdown with all vanilla maps plus custom maps
- 🎛️ **Custom Mods**: Support for custom server mods
- 🔧 **Advanced Settings**: Complete control over server parameters
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile

## Quick Start

### Using Docker (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd beammp_server_tool
   ```

2. **Deploy with Docker:**
   ```bash
   # Linux/macOS
   ./deploy.sh
   
   # Windows
   deploy.bat
   ```

3. **Access the configurator:**
   - Open your browser to `http://localhost:5000`
   - Configure your server settings
   - Use the Advanced Settings tab to manage your BeamMP server container

### Manual Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python app.py
   ```

3. **Access the configurator:**
   - Open your browser to `http://localhost:5000`

### Docker Module Installation (Optional)

The server management features require the Docker Python module. If you want to use container management features:

**Windows:**
```bash
install_docker.bat
```

**Linux/macOS:**
```bash
chmod +x install_docker.sh
./install_docker.sh
```

**Manual installation:**
```bash
# For current user only (recommended to avoid permission issues)
python -m pip install --user docker==6.1.3

# System-wide installation (requires administrator privileges)
python -m pip install docker==6.1.3
```

**Note:** The configurator works perfectly without the Docker module - only the server management features (restart, status) will be disabled.

### Fixing pip Issues

If you encounter pip installation problems:

**Windows:**
```bash
# Fix pip installation
fix_pip.bat

# Or manually fix pip
python -m ensurepip --user --upgrade
```

**Linux/macOS:**
```bash
# Reinstall pip
python -m ensurepip --user --upgrade
```

## Docker Container Management

The configurator includes built-in Docker container management capabilities:

### Server Status Monitoring
- Real-time status display (Running, Stopped, Paused, Restarting)
- Container information (name, ID, image, creation date)
- Automatic status refresh

### Server Restart Functionality
- One-click server restart from the Advanced Settings tab
- Confirmation dialog to prevent accidental restarts
- Automatic status update after restart

### Configuration
- Set the BeamMP container name via `BEAMMP_CONTAINER_NAME` environment variable
- Default container name: `beammp-server`
- Docker socket access for container management

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CONFIG_DIR` | `.` | Directory containing ServerConfig.toml |
| `BACKUP_DIR` | `backups` | Directory for backup files |
| `BEAMMP_CONTAINER_NAME` | `beammp-server` | Name of the BeamMP server container |
| `PORT` | `5000` | Port for the web interface |
| `HOST` | `0.0.0.0` | Host binding for the web interface |

### Server Configuration

The configurator manages the following BeamMP server settings:

#### General Settings
- **Server Name**: Display name in server list
- **Description**: Server description
- **Max Players**: Maximum concurrent players
- **Max Cars**: Maximum cars per player
- **Map**: Server map selection
- **Tags**: Server categorization tags
- **Custom Server Mods**: Comma-separated list of mod folder names
- **Port**: Server port (default: 30814)
- **Resource Folder**: Server resources directory
- **Auth Key**: BeamMP authentication key
- **Private Server**: Server visibility setting
- **Debug Mode**: Enable debug logging
- **Log Chat**: Log chat messages

#### Advanced Settings
- **Show Error Messages**: Display error messages on startup
- **Send Errors**: Send error reports to BeamMP developers
- **Hide Update Messages**: Suppress update notifications

## Customization

### Custom Maps
Add custom maps in the App Settings tab:
```
My Custom Map|/levels/custom_map/info.json
Another Map|/levels/another_map/info.json
```

### Custom Tags
Add custom tags in the App Settings tab:
```
Custom Category|MyTag
Events|Special Event
```

### Themes
Choose between Light and Dark themes in the App Settings tab.

## Backup System

- **Automatic Backups**: Created before each configuration save
- **Configurable Retention**: Set backup retention period (1-365 days)
- **Manual Restoration**: Restore from any backup file
- **Backup Management**: View, download, and delete backups

## API Endpoints

### Configuration
- `GET /api/config` - Get current configuration
- `POST /api/config` - Update configuration
- `GET /api/app-config` - Get application configuration

### Server Management
- `GET /api/server-status` - Get BeamMP server container status
- `POST /api/restart-server` - Restart BeamMP server container

### Maps and Tags
- `GET /api/maps` - Get available maps
- `GET /api/tags` - Get available tags

### Health Check
- `GET /health` - Health check endpoint

## Deployment

### Docker Compose
```yaml
version: '3.8'
services:
  beammp-configurator:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./configs:/app/configs
      - ./backups:/app/backups
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - BEAMMP_CONTAINER_NAME=beammp-server
```

### Kubernetes
Use the provided `k8s-deployment.yaml` for Kubernetes deployment.

## Security Considerations

- The configurator requires Docker socket access for container management
- Ensure proper access controls on the Docker socket
- Use environment variables for sensitive configuration
- Consider using Docker secrets for production deployments

## Troubleshooting

### Docker Connection Issues
- Ensure Docker daemon is running
- Check Docker socket permissions
- Verify container name configuration

### Configuration Issues
- Check file permissions on config directories
- Verify TOML syntax in configuration files
- Review application logs for errors

### Server Restart Issues
- Confirm BeamMP container exists and is running
- Check Docker daemon status
- Verify container name matches configuration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Check the troubleshooting section
- Review the official BeamMP documentation
- Open an issue on the repository 