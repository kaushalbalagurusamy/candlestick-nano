#!/usr/bin/env python3
"""
Independent Timer-Based SOL Airdrop Script
Each faucet runs on its own timer - truly parallel and efficient
Runs in background by default with minimal compute usage
"""
import os
import asyncio
import json
import base58
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair

# Configuration from environment
WALLET_ADDRESS = os.environ["WALLET_ADDRESS"]
PRIVATE_KEY = os.environ["WALLET_PRIVATE_KEY"]
CLUSTER = os.environ.get("SOLANA_CLUSTER", "devnet")
RPC_URL = os.environ["QUICKNODE_ENDPOINT"]

# Faucet configuration with independent timers
FAUCETS = {
    "solana_official": {
        "method": "rpc",
        "endpoint": "https://api.devnet.solana.com",
        "amount": 1_000_000_000,  # 1 SOL
        "rate_limit": 8 * 3600,  # 8 hours
        "name": "Solana Official RPC"
    },
    "quicknode_rpc": {
        "method": "rpc", 
        "endpoint": RPC_URL,
        "amount": 2_000_000_000,  # 2 SOL
        "rate_limit": 12 * 3600,  # 12 hours
        "name": "QuickNode RPC Direct"
    }
}

class IndependentFaucetManager:
    def __init__(self):
        self.client = None
        self.keypair = Keypair.from_bytes(base58.b58decode(PRIVATE_KEY))
        self.state_file = "faucet_state.json"
        self.running = True
        self.tasks = []
        self.load_state()
        
    def load_state(self):
        """Load faucet usage state from file"""
        try:
            with open(self.state_file, 'r') as f:
                self.state = json.load(f)
        except FileNotFoundError:
            self.state = {}
            
    def save_state(self):
        """Save faucet usage state to file"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def get_next_collection_time(self, faucet_id: str) -> datetime:
        """Get when this specific faucet will next be available"""
        if faucet_id not in self.state:
            return datetime.now()  # Available immediately if never used
            
        last_used = datetime.fromisoformat(self.state[faucet_id]["last_used"])
        rate_limit = FAUCETS[faucet_id]["rate_limit"]
        
        next_time = last_used + timedelta(seconds=rate_limit)
        return max(next_time, datetime.now())  # Don't return past times
    
    async def setup(self):
        """Initialize async client"""
        self.client = AsyncClient(RPC_URL)
        
    async def cleanup(self):
        """Cleanup resources"""
        self.running = False
        
        # Cancel all tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        if self.client:
            await self.client.close()
    
    async def get_balance(self) -> float:
        """Get current SOL balance"""
        try:
            response = await self.client.get_balance(self.keypair.pubkey())
            return response.value / 1_000_000_000
        except Exception as e:
            return 0.0
    
    async def collect_from_faucet(self, faucet_id: str) -> bool:
        """Collect from a specific faucet"""
        faucet = FAUCETS[faucet_id]
        
        try:
            if faucet_id == "quicknode_rpc":
                client = self.client
            else:
                client = AsyncClient(faucet["endpoint"])
            
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"[{timestamp}] 🎯 {faucet['name']}: Attempting collection...")
            
            sig = await client.request_airdrop(self.keypair.pubkey(), faucet["amount"])
            
            if sig.value:
                amount_sol = faucet['amount'] / 1_000_000_000
                balance = await self.get_balance()
                print(f"[{timestamp}] ✅ {faucet['name']}: Collected {amount_sol} SOL | Balance: {balance:.4f}")
                
                # Update state
                self.state[faucet_id] = {
                    "last_used": datetime.now().isoformat(),
                    "amount": faucet["amount"],
                    "signature": str(sig.value)
                }
                self.save_state()
                
                if faucet_id != "quicknode_rpc":
                    await client.close()
                    
                return True
                
        except Exception as e:
            error_msg = str(e).lower()
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            if "rate" in error_msg or "limit" in error_msg or "airdrop request limit" in error_msg:
                print(f"[{timestamp}] ⏳ {faucet['name']}: Rate limited")
                # Update state to prevent immediate retry
                self.state[faucet_id] = {
                    "last_used": datetime.now().isoformat(),
                    "amount": 0,
                    "error": "rate_limited"
                }
                self.save_state()
            else:
                print(f"[{timestamp}] ❌ {faucet['name']}: {e}")
            
            if faucet_id != "quicknode_rpc" and 'client' in locals():
                await client.close()
                
        return False
    
    def format_duration(self, seconds: float) -> str:
        """Format duration in human-readable way"""
        if seconds < 60:
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
    
    async def faucet_timer_task(self, faucet_id: str):
        """Independent timer task for a specific faucet"""
        faucet = FAUCETS[faucet_id]
        
        while self.running:
            try:
                # Calculate next collection time
                next_time = self.get_next_collection_time(faucet_id)
                now = datetime.now()
                
                if next_time <= now:
                    # Time to collect!
                    await self.collect_from_faucet(faucet_id)
                    
                    # Recalculate next time after collection
                    next_time = self.get_next_collection_time(faucet_id)
                
                # Sleep until next collection
                sleep_seconds = (next_time - datetime.now()).total_seconds()
                sleep_seconds = max(30, sleep_seconds)  # Minimum 30 seconds
                
                timestamp = datetime.now().strftime('%H:%M:%S')
                print(f"[{timestamp}] ⏰ {faucet['name']}: Next in {self.format_duration(sleep_seconds)} ({next_time.strftime('%H:%M:%S')})")
                
                await asyncio.sleep(sleep_seconds)
                
            except asyncio.CancelledError:
                timestamp = datetime.now().strftime('%H:%M:%S')
                print(f"[{timestamp}] 🛑 {faucet['name']}: Timer stopped")
                break
            except Exception as e:
                timestamp = datetime.now().strftime('%H:%M:%S')
                print(f"[{timestamp}] ❌ {faucet['name']}: Timer error - {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def status_task(self):
        """Periodic status reporting task"""
        while self.running:
            try:
                await asyncio.sleep(3600)  # Report every hour
                
                if not self.running:
                    break
                    
                balance = await self.get_balance()
                timestamp = datetime.now().strftime('%H:%M:%S')
                print(f"[{timestamp}] 📊 Balance: {balance:.4f} SOL | Active timers: {len(self.tasks)-1}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Status task error: {e}")
                await asyncio.sleep(300)
    
    async def run_independent_timers(self):
        """Run independent timers for each faucet + status reporting"""
        print(f"⏰ Starting Independent Faucet Timers for {WALLET_ADDRESS}")
        print(f"🎯 {len(FAUCETS)} faucets on {CLUSTER} | Running in background")
        print(f"🔄 Each faucet operates independently with its own timer")
        print("=" * 60)
        
        # Show initial status
        balance = await self.get_balance()
        print(f"💰 Starting balance: {balance:.4f} SOL")
        
        # Initialize all faucet states and show next collection times
        print("\n📋 Initializing faucet timers:")
        for faucet_id, faucet in FAUCETS.items():
            next_time = self.get_next_collection_time(faucet_id)
            if next_time <= datetime.now():
                print(f"   {faucet['name']}: Ready now")
            else:
                wait_seconds = (next_time - datetime.now()).total_seconds()
                print(f"   {faucet['name']}: Next in {self.format_duration(wait_seconds)}")
        
        print(f"\n🚀 Starting {len(FAUCETS)} independent timer tasks...")
        
        # Create independent tasks for each faucet
        for faucet_id in FAUCETS:
            task = asyncio.create_task(self.faucet_timer_task(faucet_id))
            self.tasks.append(task)
        
        # Add status reporting task
        status_task = asyncio.create_task(self.status_task())
        self.tasks.append(status_task)
        
        # Wait for all tasks (they run indefinitely until cancelled)
        try:
            await asyncio.gather(*self.tasks)
        except KeyboardInterrupt:
            print("\n⏹️  Stopping all faucet timers...")
        except Exception as e:
            print(f"❌ Task error: {e}")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

async def main():
    """Main entry point - runs in background by default"""
    if CLUSTER not in {"devnet", "testnet"}:
        print("❌ Independent timer airdrop only supported on devnet or testnet")
        print(f"   Current cluster: {CLUSTER}")
        print("   Set SOLANA_CLUSTER=devnet in config/.envrc")
        return
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    manager = IndependentFaucetManager()
    await manager.setup()
    
    try:
        await manager.run_independent_timers()
    finally:
        await manager.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
