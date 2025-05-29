#!/usr/bin/env python3
"""
Quick status check for SOL airdrop faucets
Shows current balance and next collection times
"""
import os
import json
import base58
import asyncio
from datetime import datetime, timedelta
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair

# Configuration
WALLET_ADDRESS = os.environ["WALLET_ADDRESS"]
PRIVATE_KEY = os.environ["WALLET_PRIVATE_KEY"]
CLUSTER = os.environ.get("SOLANA_CLUSTER", "devnet")
RPC_URL = os.environ["QUICKNODE_ENDPOINT"]

FAUCETS = {
    "solana_official": {
        "name": "Solana Official RPC",
        "amount": 1.0,
        "rate_limit": 8 * 3600
    },
    "quicknode_rpc": {
        "name": "QuickNode RPC Direct", 
        "amount": 2.0,
        "rate_limit": 12 * 3600
    }
}

async def get_balance():
    """Get current SOL balance"""
    try:
        client = AsyncClient(RPC_URL)
        kp = Keypair.from_bytes(base58.b58decode(PRIVATE_KEY))
        resp = await client.get_balance(kp.pubkey())
        await client.close()
        return resp.value / 1_000_000_000
    except Exception as e:
        print(f"⚠️  Balance check failed: {e}")
        return 0.0

def load_faucet_state():
    """Load faucet usage state"""
    try:
        with open("faucet_state.json", 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def format_duration(seconds):
    """Format duration in human-readable way"""
    if seconds < 0:
        return "Available now"
    elif seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds/60)}m"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h{minutes}m" if minutes > 0 else f"{hours}h"
    else:
        days = int(seconds / 86400)
        hours = int((seconds % 86400) / 3600)
        return f"{days}d{hours}h" if hours > 0 else f"{days}d"

async def main():
    """Show airdrop status"""
    print(f"⏰ SOL Airdrop Status - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Get current balance
    balance = await get_balance()
    print(f"💰 Current Balance: {balance:.4f} SOL")
    print(f"🌐 Cluster: {CLUSTER}")
    print(f"📍 Wallet: {WALLET_ADDRESS}")
    print()
    
    # Load faucet state
    state = load_faucet_state()
    
    # Check each faucet
    next_times = []
    available_now = []
    
    print("📋 Faucet Status:")
    print("-" * 50)
    
    for faucet_id, faucet in FAUCETS.items():
        if faucet_id in state:
            last_used = datetime.fromisoformat(state[faucet_id]["last_used"])
            next_available = last_used + timedelta(seconds=faucet["rate_limit"])
            wait_seconds = (next_available - datetime.now()).total_seconds()
            
            if wait_seconds <= 0:
                status = "🟢 Available now"
                available_now.append(faucet_id)
            else:
                status = f"🔴 Available in {format_duration(wait_seconds)}"
                next_times.append(next_available)
            
            last_amount = state[faucet_id].get("amount", 0) / 1_000_000_000
            print(f"{faucet['name']:<25} | {status}")
            print(f"{'':25} | Last: {last_used.strftime('%H:%M:%S')} ({last_amount} SOL)")
        else:
            print(f"{faucet['name']:<25} | 🟢 Available now (never used)")
            available_now.append(faucet_id)
    
    print()
    
    # Summary
    if available_now:
        total_available = sum(FAUCETS[fid]["amount"] for fid in available_now)
        faucet_names = [FAUCETS[fid]["name"] for fid in available_now]
        print(f"✅ {len(available_now)} faucet(s) available now!")
        print(f"💰 Potential collection: {total_available} SOL")
        print(f"🎯 Ready: {', '.join(faucet_names)}")
    else:
        next_time = min(next_times) if next_times else datetime.now() + timedelta(hours=1)
        wait_seconds = (next_time - datetime.now()).total_seconds()
        print(f"⏳ Next collection available in: {format_duration(wait_seconds)}")
        print(f"⏰ Next collection time: {next_time.strftime('%H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main()) 