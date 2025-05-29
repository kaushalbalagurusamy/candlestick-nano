#!/bin/bash
# Auto-setup script for timer-based SOL airdrop collection
# Minimal compute usage - only wakes when faucets are available

echo "⏰ Timer-Based SOL Airdrop Setup"
echo "================================"

# Check if we're in the right directory
if [ ! -f "airdrop.py" ]; then
    echo "❌ Error: Please run this script from the candlestick-nano directory"
    exit 1
fi

# Load environment
if [ -f ".envrc" ]; then
    source .envrc
else
    echo "❌ Error: .envrc file not found"
    exit 1
fi

if [ -z "$WALLET_ADDRESS" ]; then
    echo "❌ Error: WALLET_ADDRESS not set in .envrc"
    exit 1
fi

echo "📍 Directory: $(pwd)"
echo "💰 Wallet: $WALLET_ADDRESS"
echo "🌐 Cluster: $SOLANA_CLUSTER"

# Activate virtual environment and check dependencies
echo "🔧 Checking environment..."
source .venv/bin/activate

# Get current balance
echo "💰 Current balance:"
python -c "
import asyncio, os, base58
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair

async def balance():
    client = AsyncClient(os.environ['QUICKNODE_ENDPOINT'])
    kp = Keypair.from_bytes(base58.b58decode(os.environ['WALLET_PRIVATE_KEY']))
    resp = await client.get_balance(kp.pubkey())
    print(f'   {resp.value / 1_000_000_000:.4f} SOL')
    await client.close()

asyncio.run(balance())
" 2>/dev/null || echo "   Unable to check balance (will retry when started)"

echo ""
echo "⏰ Timer-Based Operation:"
echo "   - Calculates exact next faucet availability times"
echo "   - Sleeps until collection time (minimal compute usage)"
echo "   - Only wakes up when faucets are actually ready"
echo ""
echo "📋 Faucet Schedule:"
echo "   - Solana Official: Every 8 hours (1 SOL)"
echo "   - QuickNode RPC: Every 12 hours (2 SOL)"
echo ""
echo "🚀 Starting timer-based automated airdrop..."
echo "   The script calculates optimal sleep times"
echo "   Press Ctrl+C to stop"
echo ""

# Start the timer-based airdrop
exec python legacy/airdrop.py 