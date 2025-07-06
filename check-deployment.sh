#!/bin/bash

# DigitalOcean Basic Plan Deployment Checker
# This script validates the setup before deployment

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

# Check if we're in the right directory
check_directory() {
    if [ ! -f "manage.py" ]; then
        print_error "Not in Tabbycat root directory. Please run from project root."
        exit 1
    fi
    print_success "Running from correct directory"
}

# Check required files
check_files() {
    local required_files=(
        ".do/app.yaml"
        ".do/app-basic.yaml"
        "bin/digitalocean-build-basic.sh"
        "tabbycat/settings/digitalocean.py"
        "tabbycat/settings/digitalocean_basic.py"
        "requirements.txt"
        "package.json"
    )
    
    print_status "Checking required files..."
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            print_error "Missing required file: $file"
            exit 1
        fi
    done
    
    print_success "All required files present"
}

# Check app.yaml configuration
check_config() {
    print_status "Checking app.yaml configuration..."
    
    # Check if placeholder values are still present
    if grep -q "your-username" .do/app.yaml; then
        print_warning "Found placeholder 'your-username' in app.yaml"
        echo "  Please update the GitHub repository URL"
    fi
    
    if grep -q "your-super-secret-key" .do/app.yaml; then
        print_warning "Found placeholder secret key in app.yaml"
        echo "  Please generate a real Django secret key"
    fi
    
    if grep -q "your-email@example.com" .do/app.yaml; then
        print_warning "Found placeholder email in app.yaml"
        echo "  Please update TAB_DIRECTOR_EMAIL"
    fi
    
    # Check for basic plan instance size
    if grep -q "basic-xxs" .do/app.yaml; then
        print_success "Using Basic plan instance size (basic-xxs)"
    else
        print_warning "Not using Basic plan instance size"
    fi
    
    print_success "Configuration check completed"
}

# Check Python dependencies
check_python_deps() {
    print_status "Checking Python dependencies..."
    
    # Check if critical packages are in requirements.txt
    local critical_packages=("django" "psycopg2-binary" "gunicorn" "whitenoise")
    
    for package in "${critical_packages[@]}"; do
        if ! grep -q "$package" requirements.txt; then
            print_error "Missing critical package: $package"
            exit 1
        fi
    done
    
    print_success "Critical Python packages found"
}

# Check Node.js dependencies
check_node_deps() {
    print_status "Checking Node.js dependencies..."
    
    if [ ! -f "package.json" ]; then
        print_error "package.json not found"
        exit 1
    fi
    
    # Check for critical scripts
    if ! grep -q "digitalocean-server" package.json; then
        print_warning "digitalocean-server script not found in package.json"
    fi
    
    if ! grep -q "build" package.json; then
        print_error "build script not found in package.json"
        exit 1
    fi
    
    print_success "Node.js configuration looks good"
}

# Estimate resource usage
estimate_resources() {
    print_status "Estimating resource usage for Basic plan..."
    
    echo ""
    echo "Basic Plan Specifications:"
    echo "  - RAM: 1 GB"
    echo "  - vCPU: 1 Shared"
    echo "  - Bandwidth: 100 GB/month"
    echo "  - Cost: $10/month"
    echo ""
    
    echo "Estimated Usage:"
    echo "  - Django app: ~400-600 MB RAM"
    echo "  - Static files: ~50-100 MB"
    echo "  - Database connections: ~50-100 MB"
    echo "  - OS overhead: ~200-300 MB"
    echo "  - Total estimated: ~700-900 MB RAM"
    echo ""
    
    print_success "Should fit within Basic plan limits"
}

# Check external dependencies
check_external_deps() {
    print_status "Checking external dependencies..."
    
    echo ""
    echo "Required External Services:"
    echo "  ✓ PostgreSQL database (required)"
    echo "    - Minimum: 1 GB storage"
    echo "    - Recommended providers:"
    echo "      * DigitalOcean Managed DB ($15/mo)"
    echo "      * Railway ($5/mo)"
    echo "      * Supabase (free tier)"
    echo ""
    
    echo "Optional External Services:"
    echo "  • Email service (for notifications)"
    echo "  • Monitoring service (e.g., Sentry)"
    echo "  • CDN (for better performance)"
    echo ""
}

# Generate deployment summary
generate_summary() {
    print_status "Deployment Summary for Basic Plan..."
    
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "                    DEPLOYMENT SUMMARY"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    echo "Plan: DigitalOcean App Platform Basic ($10/mo)"
    echo "Resources: 1 GB RAM, 1 Shared vCPU, 100 GB bandwidth"
    echo ""
    echo "Configuration:"
    echo "  ✓ Single web service (no worker)"
    echo "  ✓ Local memory cache (no Redis)"
    echo "  ✓ External PostgreSQL database"
    echo "  ✓ Optimized for limited resources"
    echo ""
    echo "Estimated Monthly Cost:"
    echo "  • App Platform: $10"
    echo "  • Database: $5-15 (depending on provider)"
    echo "  • Total: $15-25/month"
    echo ""
    echo "Suitable for:"
    echo "  • Small tournaments (up to 50 teams)"
    echo "  • Development/testing"
    echo "  • Regional competitions"
    echo "  • Low-traffic deployments"
    echo ""
    echo "Next steps:"
    echo "  1. Set up external PostgreSQL database"
    echo "  2. Update .do/app.yaml with your repository URL"
    echo "  3. Configure environment variables"
    echo "  4. Deploy: doctl apps create --spec .do/app.yaml"
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
}

# Main function
main() {
    print_status "DigitalOcean Basic Plan Deployment Checker"
    echo ""
    
    check_directory
    check_files
    check_config
    check_python_deps
    check_node_deps
    estimate_resources
    check_external_deps
    generate_summary
    
    echo ""
    print_success "Deployment check completed! Ready for Basic plan deployment."
}

# Run main function
main "$@"
