#!/bin/bash

# NoviKash Admin - Quick Start Script
# Usage: ./start-admin.sh [dev|prod|docker]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ADMIN_DIR="$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 not found. Please install it first."
        exit 1
    fi
}

check_env() {
    print_header "Checking environment..."
    
    check_command "node"
    check_command "npm"
    
    NODE_VERSION=$(node --version)
    print_success "Node.js $NODE_VERSION"
    
    # Check if Backend is running (optional)
    if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
        print_success "Backend API accessible at http://localhost:8000"
    else
        print_warning "Backend API not detected at http://localhost:8000"
        print_warning "Make sure to start backend: cd .. && python -m uvicorn app.main:app --reload"
    fi
}

setup_env() {
    print_header "Setting up environment..."
    
    if [ ! -f "$ADMIN_DIR/.env.local" ]; then
        cp "$ADMIN_DIR/.env.local.example" "$ADMIN_DIR/.env.local"
        print_success "Created .env.local"
        
        # Auto-detect backend URL
        if [ -n "$BACKEND_URL" ]; then
            sed -i "s|http://localhost:8000|$BACKEND_URL|g" "$ADMIN_DIR/.env.local"
            print_success "Backend URL set to $BACKEND_URL"
        fi
    else
        print_success ".env.local already exists"
    fi
}

install_deps() {
    print_header "Installing dependencies..."
    
    if [ ! -d "$ADMIN_DIR/node_modules" ]; then
        cd "$ADMIN_DIR"
        npm ci
        print_success "Dependencies installed"
    else
        print_success "Dependencies already installed"
    fi
}

dev_mode() {
    print_header "Starting NoviKash Admin in DEVELOPMENT mode"
    echo ""
    echo "Prerequisites:"
    echo "  • Backend API running on http://localhost:8000"
    echo "  • SuperAdmin created: python ../create_admin.py +phone password"
    echo ""
    
    check_env
    setup_env
    install_deps
    
    print_header "Launching Next.js dev server..."
    echo -e "${YELLOW}→ Admin accessible at ${BLUE}http://localhost:3000${NC}"
    echo -e "${YELLOW}→ Login with your SuperAdmin credentials${NC}"
    echo ""
    
    cd "$ADMIN_DIR"
    npm run dev
}

prod_mode() {
    print_header "Building NoviKash Admin for PRODUCTION"
    
    check_env
    setup_env
    install_deps
    
    print_header "Building Next.js app..."
    cd "$ADMIN_DIR"
    npm run build
    
    print_success "Build complete!"
    echo ""
    echo "To start production server:"
    echo "  npm start"
    echo ""
    echo "Or run with environment variable:"
    echo "  NEXT_PUBLIC_API_URL=https://api.example.com npm start"
}

docker_mode() {
    print_header "Building Docker image for production"
    
    API_URL="${NEXT_PUBLIC_API_URL:-https://api.example.com}"
    echo ""
    echo "Configuration:"
    echo "  Image name: novikash-admin"
    echo "  API URL: $API_URL"
    echo ""
    
    cd "$ADMIN_DIR"
    docker build \
        -t novikash-admin \
        --build-arg NEXT_PUBLIC_API_URL="$API_URL" \
        .
    
    print_success "Docker image built: novikash-admin"
    echo ""
    echo "To run:"
    echo "  docker run -p 3000:3000 novikash-admin"
    echo ""
    echo "Or with custom API URL:"
    echo "  docker run -p 3000:3000 \\"
    echo "    -e NEXT_PUBLIC_API_URL=https://api.example.com \\"
    echo "    novikash-admin"
}

# Main
MODE="${1:-dev}"

case "$MODE" in
    dev)
        dev_mode
        ;;
    prod)
        prod_mode
        ;;
    docker)
        docker_mode
        ;;
    *)
        echo "Usage: $0 [dev|prod|docker]"
        echo ""
        echo "Modes:"
        echo "  dev    - Start development server (npm run dev)"
        echo "  prod   - Build for production (npm run build)"
        echo "  docker - Build Docker image for production"
        echo ""
        exit 1
        ;;
esac
