#!/bin/bash
# Production setup script for Candlestick Nano

set -e

echo "🚀 Candlestick Nano - Production Setup"
echo "===================================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "This script should not be run as root. Please run as a regular user with sudo privileges."
   exit 1
fi

# Create trading user
echo "📦 Creating trading user..."
sudo useradd -m -s /bin/bash trading 2>/dev/null || echo "User 'trading' already exists"

# Clone repository
echo "📥 Setting up application..."
sudo mkdir -p /opt/candlestick-nano
sudo chown trading:trading /opt/candlestick-nano
sudo -u trading git clone https://github.com/kaushalbalagurusamy/candlestick-nano.git /opt/candlestick-nano 2>/dev/null || echo "Repository already cloned"

# Setup Python environment
echo "🐍 Setting up Python environment..."
cd /opt/candlestick-nano
sudo -u trading python3 -m venv .venv
sudo -u trading .venv/bin/pip install --upgrade pip
sudo -u trading .venv/bin/pip install -r requirements.txt

# Create environment file
echo "🔧 Creating environment configuration..."
if [ ! -f /opt/candlestick-nano/.env ]; then
    sudo -u trading cp .envrc.sample .env
    echo ""
    echo "⚠️  IMPORTANT: Edit /opt/candlestick-nano/.env with your credentials:"
    echo "   - QUICKNODE_ENDPOINT"
    echo "   - WALLET_ADDRESS"
    echo "   - WALLET_PRIVATE_KEY"
    echo ""
fi

# Install systemd service
echo "⚙️  Installing systemd service..."
sudo cp candlestick-bot.service /etc/systemd/system/
sudo systemctl daemon-reload

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit /opt/candlestick-nano/.env with your credentials"
echo "2. Start the bot: sudo systemctl start candlestick-bot"
echo "3. Enable auto-start: sudo systemctl enable candlestick-bot"
echo "4. View logs: sudo journalctl -u candlestick-bot -f"
echo ""
echo "Happy trading! 🚀" 