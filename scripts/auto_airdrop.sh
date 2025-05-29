#!/bin/bash
# Background daemon script for independent timer-based SOL airdrop
# Runs each faucet on its own timer in parallel

set -e

# Change to project directory
cd "$(dirname "$0")"

# Load environment variables
if [ -f ".envrc" ]; then
    # Remove direnv-specific commands for background operation
    grep -v "layout python3" .envrc > /tmp/airdrop_env
    source /tmp/airdrop_env
    rm /tmp/airdrop_env
else
    echo "Error: .envrc file not found"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check if already running
if pgrep -f "python.*legacy/airdrop.py" > /dev/null; then
    echo "⚠️  Airdrop daemon already running"
    echo "Use 'pkill -f airdrop.py' to stop it first"
    exit 1
fi

# Start independent timer daemon in background
echo "$(date): Starting independent timer airdrop daemon..." >> airdrop.log
echo "🚀 Starting independent timer airdrop daemon in background..."
echo "📁 Logs: tail -f $(pwd)/airdrop.log"

# Run with nohup for true background operation
nohup python legacy/airdrop.py >> logs/airdrop.log 2>&1 &
PID=$!

echo "✅ Daemon started with PID: $PID"
echo "🔄 Each faucet runs on independent timers"
echo "⏹️  To stop: kill $PID"

# Save PID for easy stopping
echo $PID > airdrop.pid 