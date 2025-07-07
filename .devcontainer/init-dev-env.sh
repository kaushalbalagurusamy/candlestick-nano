#!/bin/bash
# Development environment initialization script for Candlestick Trading Bot

echo "🔧 Initializing Candlestick Trading Bot Development Environment..."

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Set up Solana CLI configuration
if command_exists solana; then
    echo "📡 Configuring Solana CLI..."
    solana config set --url devnet
    echo "✅ Solana CLI configured for devnet"
else
    echo "⚠️  Solana CLI not found. Installing..."
    sh -c "$(curl -sSfL https://release.solana.com/stable/install)"
    export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"
fi

# Create required directories
echo "📁 Creating project directories..."
mkdir -p config logs data tests/fixtures

# Set up Python virtual environment (optional)
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python -m venv venv
    echo "✅ Virtual environment created. Activate with: source venv/bin/activate"
fi

# Install project dependencies
echo "📦 Installing project dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

if [ -f "requirements-dev.txt" ]; then
    pip install -r requirements-dev.txt
fi

# Set up pre-commit hooks (if pre-commit is configured)
if [ -f ".pre-commit-config.yaml" ] && command_exists pre-commit; then
    echo "🔗 Installing pre-commit hooks..."
    pre-commit install
fi

# Check for environment variables
echo "🔐 Checking environment configuration..."
if [ -f "config/.envrc.sample" ] && [ ! -f "config/.envrc" ]; then
    echo "📝 Creating .envrc from sample..."
    cp config/.envrc.sample config/.envrc
    chmod 600 config/.envrc
    echo "⚠️  Please edit config/.envrc with your actual values"
fi

# Run initial tests
echo "🧪 Running initial tests..."
if command_exists pytest; then
    pytest tests/ -v --tb=short || echo "⚠️  Some tests failed. This is expected for initial setup."
fi

# Display helpful information
echo ""
echo "✨ Development environment initialized!"
echo ""
echo "📚 Quick Start Guide:"
echo "  1. Edit config/.envrc with your QuickNode endpoint and wallet"
echo "  2. Run: source config/.envrc"
echo "  3. Test setup: python src/quick_start_mvp.py"
echo "  4. Run bot: python src/combined_daemon.py"
echo ""
echo "🛠️  Useful Commands:"
echo "  - ruff check src/          # Run linter"
echo "  - pytest                   # Run tests"
echo "  - solana balance          # Check wallet balance"
echo "  - solana airdrop 2        # Get devnet SOL"
echo ""
echo "📖 Documentation: See CLAUDE.md for detailed guidelines"