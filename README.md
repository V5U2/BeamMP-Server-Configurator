# BeamMP Server Configurator

A modern web-based configuration tool for BeamMP servers with a beautiful UI, automatic backups, and optional Docker integration.

---

## Running with Docker (Recommended)

You can use the prebuilt image from GitHub Container Registry (GHCR):

### Linux/macOS
```sh
docker run -d -p 5000:5000 \
  -v ./config:/config \
  -v ./backup:/backup \
  -v ./server:/server \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --name beammp-configurator \
  ghcr.io/v5u2/beammp-server-configurator:latest
```

### PowerShell/Windows
```powershell
docker run -d -p 5000:5000 `
  -v ./config:/config `
  -v ./backup:/backup `
  -v ./server:/server `
  -v //var/run/docker.sock:/var/run/docker.sock `
  --name beammp-configurator `
  ghcr.io/v5u2/beammp-server-configurator:latest
```
- This will start the configurator on port 5000.
- App config, server data, and backups will be stored in `./config`, `./server`, and `./backup` on your host.
- The Docker socket mount is required for server container management features.

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

You can also use the included `docker-compose.yml` for easier setup and management:

```sh
docker compose up -d
```

This will create bind mounts for the following directories:
- `./config` → `/config` (app config) - bind mount
- `./backup` → `/backup` (server config backups) - bind mount  
- `./server` → `/server` (server config/log) - bind mount

The bind mounts ensure that your local files are directly accessible to the container and persist between container restarts.

---

## Project Structure

- `/app` — Application code and templates
- `/config` — App config files (`app_config.json`, `user_config.json`)
- `/server` — Server data (`ServerConfig.toml`, `Server.log`)
- `/backup` — Server config backups (`ServerConfig_backup_*.toml`)

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