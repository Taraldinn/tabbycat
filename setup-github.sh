#!/bin/bash

# GitHub Repository Setup Script for DigitalOcean Deployment

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

# Check if git is available
check_git() {
    if ! command -v git &> /dev/null; then
        print_error "Git is not installed. Please install git first."
        exit 1
    fi
    print_success "Git is available"
}

# Check if gh CLI is available
check_gh_cli() {
    if ! command -v gh &> /dev/null; then
        print_warning "GitHub CLI (gh) is not installed."
        echo "You can install it with:"
        echo "  - Ubuntu/Debian: sudo apt install gh"
        echo "  - macOS: brew install gh"
        echo "  - Or manually create repository on GitHub"
        return 1
    fi
    print_success "GitHub CLI is available"
    return 0
}

# Initialize git repository
init_git() {
    if [ ! -d ".git" ]; then
        print_status "Initializing git repository..."
        git init
        print_success "Git repository initialized"
    else
        print_status "Git repository already exists"
    fi
}

# Create .gitignore if it doesn't exist
create_gitignore() {
    if [ ! -f ".gitignore" ]; then
        print_status "Creating .gitignore file..."
        cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Django
*.log
local_settings.py
db.sqlite3
media/

# Environment variables
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Build outputs
staticfiles/
tabbycat/static/vue/js/
tabbycat/static/css/

# Deployment
.do/app_id
deploy.log

# Local development
local.py
development.py
EOF
        print_success ".gitignore created"
    else
        print_status ".gitignore already exists"
    fi
}

# Add and commit files
commit_files() {
    print_status "Adding files to git..."
    git add .
    
    if git diff --staged --quiet; then
        print_status "No changes to commit"
    else
        print_status "Committing files..."
        git commit -m "Initial commit: Tabbycat with DigitalOcean deployment configuration"
        print_success "Files committed"
    fi
}

# Create GitHub repository using CLI
create_github_repo() {
    if ! check_gh_cli; then
        print_warning "Please create repository manually on GitHub"
        return 1
    fi
    
    if ! gh auth status &> /dev/null; then
        print_status "Authenticating with GitHub..."
        gh auth login
    fi
    
    print_status "Creating GitHub repository..."
    read -p "Repository name (default: tabbycat-deployment): " repo_name
    repo_name=${repo_name:-tabbycat-deployment}
    
    read -p "Make repository private? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        visibility="private"
    else
        visibility="public"
    fi
    
    gh repo create "$repo_name" --$visibility --source=. --remote=origin --push
    
    if [ $? -eq 0 ]; then
        print_success "GitHub repository created: $(gh repo view --json url -q .url)"
        GITHUB_REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
        return 0
    else
        print_error "Failed to create GitHub repository"
        return 1
    fi
}

# Update app.yaml with GitHub repository
update_app_yaml() {
    local repo_name="$1"
    
    if [ -z "$repo_name" ]; then
        print_error "Repository name not provided"
        return 1
    fi
    
    print_status "Updating app.yaml with repository: $repo_name"
    
    # Update app-basic.yaml
    if [ -f ".do/app-basic.yaml" ]; then
        sed -i "s|your-username/tabbycat-2.9.3|$repo_name|g" .do/app-basic.yaml
        print_success "Updated .do/app-basic.yaml"
    fi
    
    # Update app.yaml
    if [ -f ".do/app.yaml" ]; then
        sed -i "s|your-username/tabbycat-2.9.3|$repo_name|g" .do/app.yaml
        print_success "Updated .do/app.yaml"
    fi
}

# Manual setup instructions
manual_setup() {
    print_status "Manual GitHub Setup Instructions:"
    echo ""
    echo "1. Create a new repository on GitHub:"
    echo "   https://github.com/new"
    echo ""
    echo "2. Copy the repository URL (e.g., yourusername/your-repo-name)"
    echo ""
    echo "3. Add remote and push:"
    echo "   git remote add origin https://github.com/YOURUSERNAME/YOUR-REPO-NAME.git"
    echo "   git branch -M main"
    echo "   git push -u origin main"
    echo ""
    echo "4. Update .do/app-basic.yaml with your repository name"
    echo ""
    
    read -p "Enter your GitHub repository (username/repo-name): " manual_repo
    if [ ! -z "$manual_repo" ]; then
        update_app_yaml "$manual_repo"
    fi
}

# Main function
main() {
    print_status "GitHub Repository Setup for DigitalOcean Deployment"
    echo ""
    
    check_git
    init_git
    create_gitignore
    commit_files
    
    echo ""
    print_status "Choose setup method:"
    echo "1. Automatic (using GitHub CLI)"
    echo "2. Manual (create repository yourself)"
    echo ""
    
    read -p "Enter choice (1 or 2): " -n 1 -r
    echo ""
    
    case $REPLY in
        1)
            if create_github_repo; then
                update_app_yaml "$GITHUB_REPO"
                print_success "Setup complete! You can now deploy with GitHub integration."
            else
                manual_setup
            fi
            ;;
        2)
            manual_setup
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
