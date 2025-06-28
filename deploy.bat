@echo off
setlocal enabledelayedexpansion

echo 🚀 BeamMP Server Configurator Deployment Script
echo ================================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed. Please install Docker Desktop first.
    echo Download from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

echo [INFO] Creating directories...
if not exist "configs" mkdir configs
if not exist "backups" mkdir backups
if not exist "logs" mkdir logs
if not exist "ssl" mkdir ssl

REM Copy example config if it doesn't exist
if not exist "configs\ServerConfig.toml" (
    echo [INFO] Creating example configuration...
    copy "ServerConfig.example.toml" "configs\ServerConfig.toml"
    echo [WARNING] Please edit configs\ServerConfig.toml with your server settings before starting.
    echo.
)

echo [INFO] Building and starting containers...
docker-compose up -d --build

if errorlevel 1 (
    echo [ERROR] Failed to build or start containers.
    echo Check Docker logs with: docker-compose logs
    pause
    exit /b 1
)

echo [INFO] Waiting for container to be ready...
timeout /t 10 /nobreak >nul

REM Check if container is running
docker-compose ps | findstr "Up" >nul
if errorlevel 1 (
    echo [ERROR] Container failed to start. Check logs with: docker-compose logs
    pause
    exit /b 1
)

echo [INFO] ✅ Container is running successfully!
echo.
echo 🌐 Access the configurator at: http://localhost:5000
echo 📁 Configuration files are in: .\configs\
echo 💾 Backups are stored in: .\backups\
echo 📋 Logs are in: .\logs\
echo.
echo 📖 Useful commands:
echo   View logs: docker-compose logs -f
echo   Stop: docker-compose down
echo   Restart: docker-compose restart
echo   Update: docker-compose pull ^&^& docker-compose up -d
echo.

REM Check if production flag is provided
if "%1"=="--production" (
    echo [INFO] Starting with nginx reverse proxy...
    docker-compose --profile production up -d nginx
    echo 🌐 Production setup complete! Access at: http://localhost
    echo 🔒 For HTTPS, configure SSL certificates in .\ssl\ and uncomment HTTPS in nginx.conf
    echo.
)

echo [INFO] Deployment complete! 🎉
echo.
pause 