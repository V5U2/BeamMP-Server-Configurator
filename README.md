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
# Authentication Modes
# AUTH_MODE can be NO_AUTH, BASIC, SAML, or OAUTH
AUTH_MODE=BASIC  # or SAML, OAUTH, NO_AUTH

# BASIC Auth (session-based, modal login)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=yourpassword

# SAML (for Authentik, Google Workspace, etc.)
SAML_IDP_METADATA_URL=https://your-idp.example.com/saml/metadata/
SAML_SP_ENTITY_ID=http://yourdomain.com/saml/metadata
SAML_SP_ACS_URL=http://yourdomain.com/saml/acs
SAML_SP_CERT=/config/sp-cert.pem  # optional
SAML_SP_KEY=/config/sp-key.pem    # optional

# OAuth2 / OIDC (for Authentik, Google, etc.)
OAUTH_CLIENT_ID=your_client_id
OAUTH_CLIENT_SECRET=your_client_secret
OAUTH_AUTHORIZE_URL=https://your-idp.example.com/application/o/authorize/
OAUTH_TOKEN_URL=https://your-idp.example.com/application/o/token/
OAUTH_USERINFO_URL=https://your-idp.example.com/application/o/userinfo/
OAUTH_SCOPE=openid email profile
OAUTH_REDIRECT_URI=http://yourdomain.com/oauth/callback
OAUTH_PROVIDER=authentik  # or 'google' for Google Workspace
OIDC_DISCOVERY_URL=https://your-idp.example.com/.well-known/openid-configuration  # optional, enables OIDC discovery
OIDC_JWKS_URL=https://your-idp.example.com/application/o/jwks/  # optional
```

- **AUTH_MODE**: Selects authentication mode. Options: `NO_AUTH` (no auth), `BASIC` (session-based modal login), `SAML` (SAML SSO), `OAUTH` (OAuth2/OIDC SSO).
- For SAML, set the IdP metadata URL and SP entity/ACS URLs. For OIDC, you can use discovery or manual endpoints.
- All sensitive endpoints require authentication except in `NO_AUTH` mode (not recommended for production).

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

- All sensitive endpoints require authentication (BASIC, SAML, or OAUTH) except in `NO_AUTH` mode.
- BASIC auth now uses a session-based modal login (not HTTP Basic popups).
- SAML and OAuth2/OIDC SSO are supported for enterprise/SSO environments.
- State-changing requests are protected with CSRF validation.
- Session cookies are `HttpOnly` and `SameSite=Lax`; set `COOKIE_SECURE=1` when the app is served over HTTPS.
- Production deployments must use a strong `SECRET_KEY`.
- The app uses a Docker proxy (`docker-proxy` service) to restrict permissions, allowing only server restarts and log viewing (no full Docker access required).
- The container name is set via `BEAMMP_CONTAINER_NAME` in the environment, not in the UI. This prevents users from using the app to modify other containers.
- See `SECURITY.md` for the vulnerability reporting policy, supported versions, and deployment hardening guidance.

## 🚀 Releases

- GitHub Releases are managed through `release-please` on the `main` branch.
- Container publishing is handled by GitHub Actions and pushes images to `ghcr.io/v5u2/beammp-server-configurator`.
- Tagged releases publish versioned tags such as `vX.Y.Z`, `X.Y.Z`, `X.Y`, and refresh `latest`.
- Branch pushes to `main` continue to publish a branch image tag for integration testing without redefining `latest`.
- Use Conventional Commits so release automation can infer the correct semantic version bump.

## 🖥️ UI & User Experience

- Authenticated user is shown in a floating bar with Gravatar (if email) or first letter avatar.
- Modal login form for BASIC auth; SAML/OAuth trigger SSO redirects.
- Global `isUserAuthenticated()` JS function and `window.isAuthenticated` variable for easy checks.
- UI blurs or blocks sensitive actions when not authenticated.
- Logout button in the user info bar.

## 🙋 Support

- For issues and questions, open an issue on the [GitHub repository](https://github.com/V5U2/BeamMP-Server-Configurator).

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## 🚧 TODO Roadmap

Here are some planned improvements and features for future releases:

- [x] Implement better authentication, including SSO and auth header support
- [x] Blur elements when not authenticated
- [x] Show the authenticated user in the UI
- [x] Require authentication to load Docker logs
- [ ] Mobile theme enhancements
- [ ] Add user profile settings (change password, etc.)
- [ ] Add admin audit log for config changes
- [ ] Add support for more SSO providers (Azure AD, Okta, etc.)
- [ ] Add rate limiting and brute-force protection for login
