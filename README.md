# BeamMP Server Configurator

A modern web-based configuration tool for BeamMP servers with a beautiful UI, automatic backups, and optional Docker integration.

---

## Running with Docker (Recommended)

You can use the prebuilt image from GitHub Container Registry (GHCR):

1. **Pull the image:**
   ```sh
   docker pull ghcr.io/v5u2/beammp-server-configurator:latest
   ```

2. **Run the container:**
   ```sh
   docker run -d -p 5000:5000 \
     -v $(pwd)/configs:/app/configs \
     -v $(pwd)/backups:/app/backups \
     --name beammp-configurator \
     ghcr.io/v5u2/beammp-server-configurator:latest
   ```
   - This will start the configurator on port 5000.
   - Config and backup data will be stored in `./configs` and `./backups` on your host.

3. **Access the web UI:**
   - Open your browser to [http://localhost:5000](http://localhost:5000)

4. **Stop the container:**
   ```sh
   docker stop beammp-configurator
   ```

5. **Remove the container:**
   ```sh
   docker rm beammp-configurator
   ```

---

## Using Docker Compose

You can also use the included `docker-compose.yml` for easier setup and management.  
This will build the image, set up volumes for configs, backups, and logs, and expose the web UI on port 5000.

```sh
docker compose up -d
```

---

## Features

- **Modern UI:** Beautiful, responsive interface with dark/light themes
- **Easy Configuration:** Intuitive form-based server configuration
- **Automatic Backups:** Configurable backup system with retention policies
- **Docker Integration:** Optional container management (restart/status) if running in Docker
- **Server Restart:** Restart BeamMP server containers directly from the UI
- **Server Status:** Real-time container status monitoring
- **Tag Management:** Comprehensive server tag selection system
- **Map Selection:** Dropdown with all vanilla maps plus custom maps
- **Custom Mods:** Support for custom server mods
- **Advanced Settings:** Complete control over server parameters
- **Responsive Design:** Works on desktop, tablet, and mobile

---

## Configuration

- Place your `ServerConfig.toml` in the `configs` directory (or as specified by `CONFIG_DIR`).
- Backups are stored in the `backups` directory.
- You can manage backups (restore/delete) from the web UI.

---

## Environment Variables

| Variable                | Default           | Description                                 |
|-------------------------|-------------------|---------------------------------------------|
| `CONFIG_DIR`            | `/app/configs`    | Directory containing ServerConfig.toml       |
| `BACKUP_DIR`            | `/app/backups`    | Directory for backup files                  |
| `BEAMMP_CONTAINER_NAME` | `beammp-server`   | Name of the BeamMP server container         |
| `PORT`                  | `5000`            | Port for the web interface                  |
| `HOST`                  | `0.0.0.0`         | Host binding for the web interface          |

---

## Backup System

- **Automatic Backups:** Created before each configuration save
- **Configurable Retention:** Set backup retention period in the App Settings tab
- **Manual Restoration:** Restore or delete any backup file from the Backups tab

---

## API Endpoints

- `GET /api/config` - Get current configuration
- `POST /api/config` - Update configuration
- `GET /api/app-config` - Get application configuration
- `GET /api/server-status` - Get BeamMP server container status
- `POST /api/restart-server` - Restart BeamMP server container
- `GET /api/maps` - Get available maps
- `GET /api/tags` - Get available tags
- `GET /health` - Health check endpoint

---

## Development

- Clone the repository and install dependencies from `requirements.txt`.
- Run the app with `python app.py` for local development (no Docker required).

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

## Support

- For issues and questions, open an issue on the [GitHub repository](https://github.com/V5U2/BeamMP-Server-Configurator).

## Quick Start

### Using Docker (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd beammp-server-configurator
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
