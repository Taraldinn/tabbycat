#!/bin/bash

# Quick Environment Setup for DigitalOcean Deployment

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

echo "🚀 DigitalOcean Deployment Environment Setup"
echo "=============================================="
echo ""

# Database URL
print_status "Step 1: Database Configuration"
echo ""
echo "You need a PostgreSQL database. Here are some options:"
echo ""
echo "💰 Budget Options:"
echo "  • Railway: \$5/mo - https://railway.app/"
echo "  • Supabase: Free tier - https://supabase.com/"
echo "  • ElephantSQL: Free tier (20MB) - https://www.elephantsql.com/"
echo ""
echo "🏢 Production Options:"
echo "  • DigitalOcean Managed DB: \$15/mo"
echo "  • AWS RDS: \$13/mo (t3.micro)"
echo ""

read -p "Enter your PostgreSQL DATABASE_URL: " DATABASE_URL

if [ -z "$DATABASE_URL" ]; then
    print_error "DATABASE_URL is required!"
    echo "Example: postgresql://username:password@host:port/database"
    exit 1
fi

# Validate DATABASE_URL format
if [[ ! "$DATABASE_URL" =~ ^postgresql:// ]]; then
    print_warning "DATABASE_URL should start with 'postgresql://'"
fi

print_success "Database URL configured"
echo ""

# Django Secret Key
print_status "Step 2: Django Secret Key"
echo ""
echo "Generating a secure Django secret key..."

# Generate Django secret key using Python
DJANGO_SECRET_KEY=$(python3 -c "
import secrets
import string
chars = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
print(''.join(secrets.choice(chars) for i in range(50)))
")

print_success "Django secret key generated"
echo ""

# Tab Director Email
print_status "Step 3: Contact Information"
echo ""
read -p "Enter Tab Director email (for notifications): " TAB_DIRECTOR_EMAIL

if [ -z "$TAB_DIRECTOR_EMAIL" ]; then
    TAB_DIRECTOR_EMAIL="admin@example.com"
    print_warning "Using default email: $TAB_DIRECTOR_EMAIL"
fi

echo ""

# Time Zone
print_status "Step 4: Time Zone"
echo ""
echo "Common time zones:"
echo "  • UTC (default)"
echo "  • America/New_York"
echo "  • America/Los_Angeles"
echo "  • Europe/London"
echo "  • Asia/Tokyo"
echo ""

read -p "Enter your time zone (default: UTC): " TIME_ZONE
TIME_ZONE=${TIME_ZONE:-UTC}

print_success "Time zone set to: $TIME_ZONE"
echo ""

# Update app-basic.yaml with values
print_status "Step 5: Updating configuration file"
echo ""

# Create a backup
cp .do/app-basic.yaml .do/app-basic.yaml.backup

# Update the configuration file
sed -i "s|postgresql://username:password@host:port/database|$DATABASE_URL|g" .do/app-basic.yaml
sed -i "s|your-super-secret-key-change-this-in-production|$DJANGO_SECRET_KEY|g" .do/app-basic.yaml
sed -i "s|your-email@example.com|$TAB_DIRECTOR_EMAIL|g" .do/app-basic.yaml
sed -i "s|UTC|$TIME_ZONE|g" .do/app-basic.yaml

print_success "Configuration file updated"
echo ""

# Show deployment summary
echo "📋 DEPLOYMENT SUMMARY"
echo "====================="
echo ""
echo "GitHub Repository: https://github.com/Taraldinn/tabbycat"
echo "Database: $(echo $DATABASE_URL | sed 's/:.*/.../' | sed 's|postgresql://||')"
echo "Email: $TAB_DIRECTOR_EMAIL"
echo "Time Zone: $TIME_ZONE"
echo ""

# Next steps
echo "🚀 NEXT STEPS"
echo "============="
echo ""
echo "1. Deploy to DigitalOcean:"
echo "   doctl apps create --spec .do/app-basic.yaml"
echo ""
echo "2. Monitor deployment:"
echo "   doctl apps list"
echo "   doctl apps logs YOUR_APP_ID --follow"
echo ""
echo "3. After deployment, run database migrations:"
echo "   # Access app console and run:"
echo "   python manage.py migrate"
echo "   python manage.py createsuperuser"
echo ""

# Commit updated configuration
read -p "Commit and push updated configuration to GitHub? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    git add .do/app-basic.yaml
    git commit -m "Update deployment configuration with environment variables"
    git push origin master
    print_success "Configuration pushed to GitHub"
fi

echo ""
print_success "Setup complete! You can now deploy with:"
echo "doctl apps create --spec .do/app-basic.yaml"
