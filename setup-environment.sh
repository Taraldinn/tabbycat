#!/bin/bash

# DigitalOcean Environment Setup Script
# This script helps you configure the environment variables for deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Generate Django secret key
generate_secret_key() {
    python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
}

# Main configuration function
configure_environment() {
    print_status "DigitalOcean Environment Configuration"
    echo ""
    
    # Get user inputs
    echo "Please provide the following information:"
    echo ""
    
    # Database URL
    print_status "Database Configuration"
    echo "You need a PostgreSQL database. Recommended providers:"
    echo "  • Railway: $5/mo - https://railway.app"
    echo "  • Supabase: Free tier - https://supabase.com"
    echo "  • DigitalOcean: $15/mo - https://cloud.digitalocean.com"
    echo ""
    
    read -p "Enter your PostgreSQL Database URL: " DATABASE_URL
    if [ -z "$DATABASE_URL" ]; then
        print_error "Database URL is required!"
        echo "Format: postgresql://username:password@host:port/database"
        exit 1
    fi
    
    # Validate database URL format
    if [[ ! $DATABASE_URL =~ ^postgresql:// ]]; then
        print_warning "Database URL should start with 'postgresql://'"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Django Secret Key
    print_status "Django Secret Key"
    echo "Generate a new secret key or provide your own:"
    read -p "Press Enter to auto-generate or enter your own: " DJANGO_SECRET_KEY
    
    if [ -z "$DJANGO_SECRET_KEY" ]; then
        DJANGO_SECRET_KEY=$(generate_secret_key)
        print_success "Generated Django secret key"
    fi
    
    # Tab Director Email
    print_status "Tab Director Email (Optional)"
    read -p "Enter your email for notifications (optional): " TAB_DIRECTOR_EMAIL
    TAB_DIRECTOR_EMAIL=${TAB_DIRECTOR_EMAIL:-"admin@example.com"}
    
    # Time Zone
    print_status "Time Zone"
    echo "Examples: UTC, America/New_York, Europe/London, Asia/Tokyo"
    read -p "Enter your timezone (default: UTC): " TIME_ZONE
    TIME_ZONE=${TIME_ZONE:-"UTC"}
    
    # Update the configuration file
    print_status "Updating configuration file..."
    
    # Create a backup
    cp .do/app-basic.yaml .do/app-basic.yaml.backup
    
    # Update the file with actual values
    sed -i "s|postgresql://username:password@host:port/database|$DATABASE_URL|g" .do/app-basic.yaml
    sed -i "s|your-super-secret-key-change-this-in-production|$DJANGO_SECRET_KEY|g" .do/app-basic.yaml
    sed -i "s|your-email@example.com|$TAB_DIRECTOR_EMAIL|g" .do/app-basic.yaml
    sed -i "s|UTC|$TIME_ZONE|g" .do/app-basic.yaml
    
    print_success "Configuration file updated!"
    
    # Show summary
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "                    CONFIGURATION SUMMARY"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    echo "Database URL: ${DATABASE_URL:0:30}..."
    echo "Django Secret Key: ${DJANGO_SECRET_KEY:0:20}..."
    echo "Tab Director Email: $TAB_DIRECTOR_EMAIL"
    echo "Time Zone: $TIME_ZONE"
    echo ""
    echo "Configuration file: .do/app-basic.yaml"
    echo "Backup created: .do/app-basic.yaml.backup"
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    
    print_success "Environment configuration completed!"
    print_status "You can now deploy with: doctl apps create --spec .do/app-basic.yaml"
}

# Help function
show_help() {
    echo "DigitalOcean Environment Setup Script"
    echo ""
    echo "This script helps you configure environment variables for deployment."
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  configure   Interactive configuration setup"
    echo "  help        Show this help message"
    echo ""
    echo "Before running this script, make sure you have:"
    echo "  1. A PostgreSQL database URL"
    echo "  2. DigitalOcean CLI (doctl) installed and authenticated"
    echo ""
}

# Main script logic
case "${1:-configure}" in
    "configure")
        configure_environment
        ;;
    "help")
        show_help
        ;;
    *)
        show_help
        ;;
esac
