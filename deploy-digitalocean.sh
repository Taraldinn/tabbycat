#!/bin/bash

# DigitalOcean Manual Deployment Script
# This script helps you deploy Tabbycat to DigitalOcean App Platform manually

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if doctl is installed
check_doctl() {
    if ! command -v doctl &> /dev/null; then
        print_error "doctl CLI is not installed. Please install it first:"
        echo "  - Ubuntu/Debian: sudo snap install doctl"
        echo "  - macOS: brew install doctl"
        echo "  - Or download from: https://github.com/digitalocean/doctl/releases"
        exit 1
    fi
    print_success "doctl CLI found"
}

# Check if user is authenticated
check_auth() {
    if ! doctl auth list &> /dev/null; then
        print_error "You are not authenticated with DigitalOcean. Please run:"
        echo "  doctl auth init"
        exit 1
    fi
    print_success "DigitalOcean authentication verified"
}

# Function to create app
create_app() {
    local plan=${1:-"basic"}
    print_status "Creating DigitalOcean App (Plan: $plan)..."
    
    local spec_file=".do/app.yaml"
    if [ "$plan" = "basic" ]; then
        spec_file=".do/app-basic.yaml"
    fi
    
    if [ ! -f "$spec_file" ]; then
        print_error "App specification file $spec_file not found!"
        exit 1
    fi
    
    # Create the app
    APP_ID=$(doctl apps create --spec "$spec_file" --format ID --no-header)
    
    if [ -z "$APP_ID" ]; then
        print_error "Failed to create app"
        exit 1
    fi
    
    print_success "App created with ID: $APP_ID"
    echo "$APP_ID" > .do/app_id
    
    return 0
}

# Function to update existing app
update_app() {
    if [ ! -f ".do/app_id" ]; then
        print_error "App ID file not found. Create the app first."
        exit 1
    fi
    
    APP_ID=$(cat .do/app_id)
    print_status "Updating app $APP_ID..."
    
    doctl apps update "$APP_ID" --spec .do/app.yaml
    print_success "App updated successfully"
}

# Function to get app info
get_app_info() {
    if [ ! -f ".do/app_id" ]; then
        print_error "App ID file not found. Create the app first."
        exit 1
    fi
    
    APP_ID=$(cat .do/app_id)
    print_status "Getting app information..."
    
    doctl apps get "$APP_ID"
}

# Function to get app logs
get_logs() {
    if [ ! -f ".do/app_id" ]; then
        print_error "App ID file not found. Create the app first."
        exit 1
    fi
    
    APP_ID=$(cat .do/app_id)
    print_status "Getting app logs..."
    
    doctl apps logs "$APP_ID" --follow
}

# Function to delete app
delete_app() {
    if [ ! -f ".do/app_id" ]; then
        print_error "App ID file not found."
        exit 1
    fi
    
    APP_ID=$(cat .do/app_id)
    
    print_warning "This will permanently delete the app with ID: $APP_ID"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        doctl apps delete "$APP_ID" --force
        rm -f .do/app_id
        print_success "App deleted successfully"
    else
        print_status "Deletion cancelled"
    fi
}

# Function to setup environment variables
setup_env_vars() {
    print_status "Setting up environment variables..."
    
    echo "Please provide the following environment variables:"
    
    # Database URL
    read -p "Database URL (postgresql://...): " DATABASE_URL
    if [ -z "$DATABASE_URL" ]; then
        print_error "Database URL is required!"
        exit 1
    fi
    
    # Redis URL
    read -p "Redis URL (redis://...): " REDIS_URL
    if [ -z "$REDIS_URL" ]; then
        print_error "Redis URL is required!"
        exit 1
    fi
    
    # Django Secret Key
    read -p "Django Secret Key (leave empty to generate): " DJANGO_SECRET_KEY
    if [ -z "$DJANGO_SECRET_KEY" ]; then
        DJANGO_SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
        print_status "Generated Django secret key"
    fi
    
    # Tab Director Email
    read -p "Tab Director Email (optional): " TAB_DIRECTOR_EMAIL
    
    # Time Zone
    read -p "Time Zone (default: UTC): " TIME_ZONE
    TIME_ZONE=${TIME_ZONE:-UTC}
    
    # Update the app.yaml file with environment variables
    print_status "Updating app.yaml with environment variables..."
    
    # Create a temporary file with updated values
    sed -e "s|your-database-url-here|$DATABASE_URL|g" \
        -e "s|your-redis-url-here|$REDIS_URL|g" \
        -e "s|your-super-secret-key-change-this-in-production|$DJANGO_SECRET_KEY|g" \
        -e "s|your-email@example.com|$TAB_DIRECTOR_EMAIL|g" \
        -e "s|UTC|$TIME_ZONE|g" \
        .do/app.yaml > .do/app.yaml.tmp
    
    mv .do/app.yaml.tmp .do/app.yaml
    
    print_success "Environment variables configured"
}

# Function to validate configuration
validate_config() {
    print_status "Validating configuration..."
    
    # Check if required files exist
    local required_files=(".do/app.yaml" "manage.py" "tabbycat/settings/digitalocean.py")
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            print_error "Required file missing: $file"
            exit 1
        fi
    done
    
    # Check if app.yaml has placeholder values
    if grep -q "your-username" .do/app.yaml; then
        print_warning "app.yaml still contains placeholder values. Please update:"
        echo "  - GitHub repository URL"
        echo "  - Environment variables"
    fi
    
    print_success "Configuration validation completed"
}

# Function to show help
show_help() {
    echo "DigitalOcean Tabbycat Deployment Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  create      Create a new app on DigitalOcean"
    echo "  create-basic Create app using Basic plan ($10/mo)"
    echo "  update      Update existing app"
    echo "  info        Get app information"
    echo "  logs        View app logs"
    echo "  delete      Delete the app"
    echo "  setup-env   Setup environment variables"
    echo "  validate    Validate configuration"
    echo "  check       Run deployment checker"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 check           # Check deployment readiness"
    echo "  $0 setup-env       # Setup environment variables"
    echo "  $0 create-basic    # Create app with Basic plan"
    echo "  $0 logs            # View logs"
}

# Main script logic
main() {
    print_status "DigitalOcean Tabbycat Deployment Script"
    
    case "${1:-help}" in
        "create")
            check_doctl
            check_auth
            validate_config
            create_app "standard"
            print_success "Deployment initiated! Check the DigitalOcean dashboard for build progress."
            ;;
        "create-basic")
            check_doctl
            check_auth
            validate_config
            create_app "basic"
            print_success "Basic plan deployment initiated! Check the DigitalOcean dashboard for build progress."
            ;;
        "update")
            check_doctl
            check_auth
            validate_config
            update_app
            ;;
        "info")
            check_doctl
            check_auth
            get_app_info
            ;;
        "logs")
            check_doctl
            check_auth
            get_logs
            ;;
        "delete")
            check_doctl
            check_auth
            delete_app
            ;;
        "setup-env")
            setup_env_vars
            ;;
        "validate")
            validate_config
            ;;
        "check")
            if [ -f "./check-deployment.sh" ]; then
                ./check-deployment.sh
            else
                print_error "Deployment checker not found"
            fi
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Run main function with all arguments
main "$@"
