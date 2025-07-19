# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    lsb-release \
    xmlsec1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY app/requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copy application code and templates
COPY app/ /app/

# Create directories for server data and backups
RUN mkdir -p /server /backup /config

# Expose port
EXPOSE 5000

# Copy gunicorn-entrypoint.sh
COPY gunicorn-entrypoint.sh /app/
RUN chmod +x /app/gunicorn-entrypoint.sh

# Run the application
CMD ["/app/gunicorn-entrypoint.sh"] 