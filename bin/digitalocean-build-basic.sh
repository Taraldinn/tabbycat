#!/bin/bash

# DigitalOcean App Platform Build Script - Basic Plan Optimized
# This script prepares the Tabbycat application for deployment on Basic plan

set -e  # Exit on any error

echo "Starting DigitalOcean build process (Basic Plan)..."

# Update system packages (minimal)
echo "Updating essential packages..."
apt-get update -y

# Install only essential system dependencies
echo "Installing minimal system dependencies..."
apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gettext \
    postgresql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies with optimizations
echo "Installing Python dependencies..."
pip install --upgrade pip --no-cache-dir
pip install --no-cache-dir -r requirements.txt

# Install Node.js dependencies (production only)
echo "Installing Node.js dependencies..."
npm ci --only=production --no-audit --no-fund

# Build frontend assets with optimizations
echo "Building frontend assets..."
NODE_ENV=production npm run build

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Compile translations
echo "Compiling translations..."
python manage.py compilemessages

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p /tmp/tabbycat-media
mkdir -p /tmp/tabbycat-logs

# Optimize for memory usage
echo "Cleaning up build artifacts..."
npm cache clean --force
pip cache purge

echo "Build completed successfully for Basic plan!"
