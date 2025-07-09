#!/bin/bash
# Setup script to prepare environment for DevContainer

echo "🔧 Preparing Candlestick Nano for DevContainer..."

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating required directories..."
mkdir -p config logs data tests/fixtures

# Check for environment file
if [ ! -f "config/.envrc" ]; then
    if [ -f "config/.envrc.sample" ]; then
        echo "📝 Creating .envrc from sample..."
        cp config/.envrc.sample config/.envrc
        chmod 600 config/.envrc
        echo "⚠️  Please edit config/.envrc with your actual values before proceeding."
    else
        echo "❌ No environment configuration found. Please create config/.envrc"
        exit 1
    fi
fi

# Ensure git config exists (required for dev container)
if [ ! -f "$HOME/.gitconfig" ]; then
    echo "⚠️  No .gitconfig found. Creating basic configuration..."
    git config --global user.name "Developer"
    git config --global user.email "developer@example.com"
fi

# Clean up any existing containers or volumes
echo "🧹 Cleaning up any existing containers..."
docker compose -f docker-compose.yml down 2>/dev/null || true

# Optionally remove the dev container image to force rebuild
read -p "Do you want to rebuild the dev container from scratch? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️  Removing existing dev container image..."
    docker rmi candlestick-nano-devcontainer 2>/dev/null || true
    docker volume rm candlestick-bashhistory 2>/dev/null || true
fi

echo "✅ Environment is ready for DevContainer!"
echo ""
echo "📚 Next steps:"
echo "  1. Review and update config/.envrc with your values"
echo "  2. In VS Code: Press Cmd+Shift+P and select 'Dev Containers: Reopen in Container'"
echo "  3. Once in container, run: sudo /usr/local/bin/init-dev-env.sh"
echo ""
echo "🚀 Happy coding!"
