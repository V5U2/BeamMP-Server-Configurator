# 🚗 BeamMP Server Configurator

A modern web-based configuration tool for BeamMP servers with a beautiful UI, automatic backups, and secure Docker integration.

## ✨ Features

- Modern, user-friendly web UI
- Automatic backups and easy restore
- Secure Docker integration (no full Docker access required)
- HTTP Basic Auth for all sensitive endpoints
- Custom map and mod support
- Health checks and status endpoints

## 🗂️ Project Structure & Deployment

- **Dockerfile** and **docker-compose.yml** are in the project root.
- The **.env** file must also be in the project root and contains all required environment variables.
- All persistent data is stored using bind mounts, with paths set via .env variables.
- The app config and server config directories are separate and clearly defined.

## 🔑 Environment Variables (.env)

Create a `.env` file in your project root with the following content (edit as needed):

```env
SECRET_KEY=supersecretkey1234
ADMIN_USERNAME=admin
ADMIN_PASSWORD=testpassword123
BEAMMP_CONTAINER_NAME=beamng-mp
DOCKER_HOST=http://docker-proxy:2375
CONFIG_DATA=./config
BACKUP_DATA=./backup
SERVER_DATA=./server
BEAMNGMP_DATA=./beamngmp_data
```

- **SECRET_KEY**: Required for Flask session security (set a strong value in production).
- **ADMIN_USERNAME/ADMIN_PASSWORD**: HTTP Basic Auth credentials for the web UI and API.
- **BEAMMP_CONTAINER_NAME**: The name of the BeamMP server container (should match the container_name in docker-compose.yml).
- **DOCKER_HOST**: Must be `http://docker-proxy:2375`.
- **CONFIG_DATA, BACKUP_DATA, BEAMNGMP_DATA**: Host paths for config, backup, and BeamNG-MP data directories.

Add these for OAuth2 (Authentik, Google, etc.):

```
# OAuth2 (for Authentik, Google, etc.)
AUTH_MODE=OAUTH
OAUTH_CLIENT_ID=your_client_id
OAUTH_CLIENT_SECRET=your_client_secret
OAUTH_AUTHORIZE_URL=https://your-idp.example.com/application/o/authorize/
OAUTH_TOKEN_URL=https://your-idp.example.com/application/o/token/
OAUTH_USERINFO_URL=https://your-idp.example.com/application/o/userinfo/
OAUTH_SCOPE=openid email profile
OAUTH_REDIRECT_URI=http://yourdomain.com/oauth/callback
OAUTH_PROVIDER=authentik  # or 'google' for Google Workspace
```

- For Authentik, use the application URLs from your Authentik OAuth2 app.
- For Google, use the Google OAuth2 endpoints and set the correct client ID/secret.

## 🐳 Docker Compose Example

```yaml
services:
  beammp-configurator:
    # image: ghcr.io/v5u2/beammp-server-configurator:latest # To pull the latest image from GitHub Container Registry instead of building locally
    build: . # To build the image locally
    container_name: beammp-configurator
    ports:
      - "5000:5000"
    volumes:
      - ${CONFIG_DATA}:/config
      - ${BACKUP_DATA}:/backup
      - ${SERVER_DATA}:/server
    environment:
      - FLASK_ENV=production
      - CONFIG_DIR=/config
      - BACKUP_DIR=/backup
      - SERVER_DIR=/server
      - BEAMMP_CONTAINER_NAME=beamng-mp
      - DOCKER_HOST=http://docker-proxy:2375  # Use the secure proxy
      - SECRET_KEY=${SECRET_KEY}
      - ADMIN_PASSWORD=${ADMIN_PASSWORD}
      - ADMIN_USERNAME=${ADMIN_USERNAME}
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
      - ${SERVER_DATA}:/beamngmp
    restart: unless-stopped
    networks:
      - beammp-network

  docker-proxy:
    image: tecnativa/docker-socket-proxy
    container_name: docker-proxy
    environment:
      - CONTAINERS=1   # Allow access to containers endpoints
      - POST=1         # Allow POST (for restart)
      - GET=1          # Allow GET (for status)
      - LOGS=1         # Allow logs endpoint
      - NETWORKS=0
      - IMAGES=0
      - AUTH=0
      - INFO=0
      - SYSTEM=0
      - VOLUMES=0
      - BUILD=0
      - EVENTS=0
      - PING=1         # Allow ping for healthcheck
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - beammp-network

networks:
  beammp-network:
    driver: bridge 
```

## ⚙️ Building and Running

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

## 🛡️ Security

- All sensitive endpoints require HTTP Basic Auth (set credentials in .env).
- The app uses a Docker proxy (`docker-proxy` service) to restrict permissions, allowing only server restarts and log viewing (no full Docker access required).
- The container name is set via `BEAMMP_CONTAINER_NAME` in the environment, not in the UI. This prevents users from using the app to modify other containers.

## 🙋 Support

- For issues and questions, open an issue on the [GitHub repository](https://github.com/V5U2/BeamMP-Server-Configurator).

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## 🚧 TODO Roadmap

Here are some planned improvements and features for future releases:

- [ ] Implement better authentication, including SSO and auth header support
- [ ] Blur elements when not authenticated
- [ ] Show the authenticated user in the UI
- [ ] Require authentication to load Docker logs
- [ ] Mobile theme enhancements