#!/bin/bash

# DigitalOcean App Platform Build Script
# This script prepares the Tabbycat application for deployment

set -e  # Exit on any error

echo "Starting DigitalOcean build process..."

# Update system packages
echo "Updating system packages..."
apt-get update

# Install system dependencies
echo "Installing system dependencies..."
apt-get install -y \
    build-essential \
    libpq-dev \
    gettext \
    postgresql-client

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install pipenv
pipenv install --system --deploy

# Install Node.js dependencies  
echo "Installing Node.js dependencies..."
npm ci --only=production

# Build frontend assets
echo "Building frontend assets..."
npm run build

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Compile translations
echo "Compiling translations..."
python manage.py compilemessages

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p /app/media
mkdir -p /app/logs

# Set proper permissions
echo "Setting file permissions..."
chmod -R 755 /app/media
chmod -R 755 /app/logs

echo "Build completed successfully!"
