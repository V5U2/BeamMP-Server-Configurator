#!/bin/bash

# BeamMP Server Configurator Deployment Script
# This script helps deploy the configurator using Docker

set -e

echo "🚀 BeamMP Server Configurator Deployment Script"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
print_status "Creating directories..."
mkdir -p configs backups logs ssl

# Copy example config if it doesn't exist
if [ ! -f "configs/ServerConfig.toml" ]; then
    print_status "Creating example configuration..."
    cp ServerConfig.example.toml configs/ServerConfig.toml
    print_warning "Please edit configs/ServerConfig.toml with your server settings before starting."
fi

# Set permissions
print_status "Setting permissions..."
chmod 755 configs backups logs

# Build and start containers
print_status "Building and starting containers..."
docker-compose up -d --build

# Wait for container to be ready
print_status "Waiting for container to be ready..."
sleep 10

# Check if container is running
if docker-compose ps | grep -q "Up"; then
    print_status "✅ Container is running successfully!"
    echo ""
    echo "🌐 Access the configurator at: http://localhost:5000"
    echo "📁 Configuration files are in: ./configs/"
    echo "💾 Backups are stored in: ./backups/"
    echo "📋 Logs are in: ./logs/"
    echo ""
    echo "📖 Useful commands:"
    echo "  View logs: docker-compose logs -f"
    echo "  Stop: docker-compose down"
    echo "  Restart: docker-compose restart"
    echo "  Update: docker-compose pull && docker-compose up -d"
    echo ""
else
    print_error "❌ Container failed to start. Check logs with: docker-compose logs"
    exit 1
fi

# Optional: Start with nginx for production
if [ "$1" = "--production" ]; then
    print_status "Starting with nginx reverse proxy..."
    docker-compose --profile production up -d nginx
    echo "🌐 Production setup complete! Access at: http://localhost"
    echo "🔒 For HTTPS, configure SSL certificates in ./ssl/ and uncomment HTTPS in nginx.conf"
fi

print_status "Deployment complete! 🎉" 