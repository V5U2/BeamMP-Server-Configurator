# BeamMP Server Configurator

A modern web-based configuration tool for BeamMP servers with a beautiful UI, automatic backups, and secure Docker integration.

---

## Project Structure & Deployment

- **Dockerfile** and **docker-compose.yml** are in the project root.
- The **.env** file must also be in the project root and contains all required environment variables.
- All persistent data is stored using bind mounts, with paths set via .env variables.
- The app config and server config directories are separate and clearly defined.

---

## Environment Variables (.env)

Create a `.env` file in your project root with the following content (edit as needed):

```env
SECRET_KEY=supersecretkey1234
ADMIN_USERNAME=admin
ADMIN_PASSWORD=testpassword123
BEAMMP_CONTAINER_NAME=beamng-mp
DOCKER_HOST=http://docker-proxy:2375
CONFIG_DATA=./config
BACKUP_DATA=./backup
BEAMNGMP_DATA=./beamngmp_data
```

- **SECRET_KEY**: Required for Flask session security (set a strong value in production).
- **ADMIN_USERNAME/ADMIN_PASSWORD**: HTTP Basic Auth credentials for the web UI and API.
- **BEAMMP_CONTAINER_NAME**: The name of the BeamMP server container (should match the container_name in docker-compose.yml).
- **DOCKER_HOST**: Must be `http://docker-proxy:2375` (not `tcp://...`).
- **CONFIG_DATA, BACKUP_DATA, BEAMNGMP_DATA**: Host paths for config, backup, and BeamNG-MP data directories.

---

## Docker Compose Example

```yaml
version: '3.8'

services:
  beammp-configurator:
    build: .
    container_name: beammp-configurator
    ports:
      - "5000:5000"
    volumes:
      - ${CONFIG_DATA}:/config
      - ${BACKUP_DATA}:/backup
      - ./server:/server
    environment:
      - FLASK_ENV=production
      - CONFIG_DIR=/config
      - BACKUP_DIR=/backup
      - BEAMMP_CONTAINER_NAME=${BEAMMP_CONTAINER_NAME}
      - DOCKER_HOST=${DOCKER_HOST}
      - SECRET_KEY=${SECRET_KEY}
      - ADMIN_USERNAME=${ADMIN_USERNAME}
      - ADMIN_PASSWORD=${ADMIN_PASSWORD}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/config"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - beammp-network

  beamng-mp:
    image: ich777/beamng-mp-server
    container_name: beamng-mp
    environment:
      - TZ=Australia/Perth
      - GAME_PARAMS=
      - UID=99
      - GID=100
      - UMASK=0000
    ports:
      - "30814:30814/tcp"
      - "30814:30814/udp"
      - "9045:8080/tcp"
    volumes:
      - ${BEAMNGMP_DATA}:/beamngmp:rw
    restart: unless-stopped
    networks:
      - beammp-network

  docker-proxy:
    image: tecnativa/docker-socket-proxy
    container_name: docker-proxy
    environment:
      - CONTAINERS=1
      - POST=1
      - GET=1
      - LOGS=1
      - NETWORKS=0
      - IMAGES=0
      - AUTH=0
      - INFO=0
      - SYSTEM=0
      - VOLUMES=0
      - BUILD=0
      - EVENTS=0
      - PING=1
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - beammp-network

networks:
  beammp-network:
    driver: bridge
```

---

## Building and Running

1. **Build without cache:**
   ```bash
   docker compose build --no-cache
   ```
2. **Start the services:**
   ```bash
   docker compose up -d
   ```
3. **Check status:**
   ```bash
   docker compose ps
   ```

---

## Security & Features

- All sensitive endpoints require HTTP Basic Auth (set credentials in .env).
- The app uses a Docker proxy (`docker-proxy` service) and does not require the Docker CLI or Python Docker library.
- The container name is set via `BEAMMP_CONTAINER_NAME` in the environment, not in the UI.
- The backend provides a `/api/containers` endpoint for debugging container discovery.
- All persistent data is stored using bind mounts, not Docker volumes.
- The app config (`/config/app_config.json`) and server config (`/server/ServerConfig.toml`) are separate.

---

## Troubleshooting

- **.env file not working?**
  - Ensure `.env` is in the project root (same directory as `docker-compose.yml`).
  - Run `docker compose config` to see if variables are being substituted.
  - `DOCKER_HOST` must be `http://docker-proxy:2375` (not `tcp://...`).
- **Container not found errors?**
  - Make sure `BEAMMP_CONTAINER_NAME` matches the actual container name (see `docker ps -a`).
  - Use the `/api/containers` endpoint to debug what containers the app can see.
- **App config in wrong directory?**
  - Ensure `CONFIG_DIR` is set to `/config` in your compose file.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

## Support

- For issues and questions, open an issue on the [GitHub repository](https://github.com/V5U2/BeamMP-Server-Configurator).