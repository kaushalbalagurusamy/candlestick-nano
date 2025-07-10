# entry_daemon.py
import time
import base64
import requests
import base58
import asyncio
from datetime import datetime
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solana.rpc.types import TxOpts
from config import config, WSOL_MINT

# Track seen pools to avoid duplicates
seen_pools = set()

async def fetch_new_pools():
    """Fetch recently deployed pools from QuickNode Métis /new-pools endpoint"""
    try:
        response = requests.get(f"{config.quicknode_endpoint}/new-pools")
        response.raise_for_status()
        return response.json().get("data", [])
    except Exception as e:
        print(f"Error fetching new pools: {e}")
        return []

async def check_freeze_authority(client: AsyncClient, mint: str) -> bool:
    """Check if token has freeze authority (potential rug)"""
    try:
        # Get mint account info
        resp = await client.get_account_info_json_parsed(mint)
        if not resp.value:
            return True  # Skip if can't get info
        
        # Check freeze authority - if exists, it's a potential rug
        mint_data = resp.value.data.parsed.get("info", {})
        freeze_authority = mint_data.get("freezeAuthority")
        
        return freeze_authority is not None
    except Exception as e:
        print(f"Error checking freeze authority for {mint}: {e}")
        return True  # Skip on error

async def get_liquidity_quote(mint: str, amount: int = 1_000_000_000) -> dict:
    """Get quote to check liquidity and slippage"""
    try:
        params = {
            "inputMint": WSOL_MINT,
            "outputMint": mint,
            "amount": str(amount),
            "slippageBps": str(config.slippage_bps)
        }
        response = requests.get(f"{config.quicknode_endpoint}/quote", params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error getting quote for {mint}: {e}")
        return None

async def execute_swap(quote_data: dict) -> str:
    """Execute swap transaction using quote data"""
    try:
        # Get swap transaction
        swap_response = requests.post(
            f"{config.quicknode_endpoint}/swap",
            json={
                "owner": config.wallet_address,
                "quoteResponse": quote_data
            }
        )
        swap_response.raise_for_status()
        swap_data = swap_response.json()
        
        # Sign and send transaction
        async with AsyncClient(config.quicknode_endpoint) as client:
            keypair = Keypair.from_bytes(base58.b58decode(config.wallet_private_key))
            tx_bytes = base64.b64decode(swap_data["swapTransaction"])
            tx = VersionedTransaction.from_bytes(tx_bytes)
            
            # Sign transaction
            tx.sign([keypair])
            
            # Send transaction
            sig = await client.send_raw_transaction(
                bytes(tx),
                opts=TxOpts(skip_preflight=True)
            )
            
            return sig.value
    except Exception as e:
        print(f"Error executing swap: {e}")
        return None

async def process_new_token(pool_data: dict, client: AsyncClient):
    """Process a new token from pool data"""
    mint = pool_data.get("tokenAddress")
    if not mint or mint in seen_pools:
        return
    
    seen_pools.add(mint)
    timestamp = pool_data.get("timestamp", "")
    
    # Age check
    try:
        pool_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        age_seconds = (datetime.utcnow() - pool_time.replace(tzinfo=None)).total_seconds()
        if age_seconds > config.max_token_age:
            print(f"Skipping {mint}: Too old ({age_seconds/3600:.1f} hours)")
            return
    except (ValueError, TypeError):
        print(f"Skipping {mint}: Invalid timestamp format")
        return
    
    # Freeze authority check
    if await check_freeze_authority(client, mint):
        print(f"Skipping {mint}: Has freeze authority (potential rug)")
        return
    
    # Liquidity check
    quote = await get_liquidity_quote(mint)
    if not quote:
        return
    
    out_amount = int(quote.get("outAmount", 0))
    if out_amount < config.min_liquidity_threshold:
        print(f"Skipping {mint}: Insufficient liquidity ({out_amount})")
        return
    
    # All checks passed - execute buy
    print(f"Buying {mint} - Liquidity: {out_amount}")
    tx_sig = await execute_swap(quote)
    if tx_sig:
        print(f"✅ Bought {mint} - TX: {tx_sig}")
        
        # Create take-profit limit order
        await create_limit_order(mint, out_amount)

async def create_limit_order(mint: str, amount: int):
    """Create a take-profit limit order"""
    try:
        # Calculate take-profit amount (e.g., 20% profit)
        take_profit_amount = int(amount * 1.2)
        
        response = requests.post(
            f"{config.quicknode_endpoint}/limit-orders/create",
            json={
                "maker": config.wallet_address,
                "payer": config.wallet_address,
                "inputMint": mint,
                "outputMint": WSOL_MINT,
                "params": {
                    "makingAmount": str(amount),
                    "takingAmount": str(take_profit_amount),
                    "expiredAt": str(int(time.time()) + 86400)  # 24h expiry
                }
            }
        )
        if response.status_code == 200:
            print(f"✅ Created limit order for {mint}")
    except Exception as e:
        print(f"Error creating limit order: {e}")

async def main():
    """Main entry daemon loop"""
    print("🚀 Starting entry daemon...")
    print(f"Min Liquidity: {config.min_liquidity_threshold}")
    print(f"Max Token Age: {config.max_token_age}s")
    print(f"Monitoring Interval: {config.monitoring_interval}s")
    
    async with AsyncClient(config.quicknode_endpoint) as client:
        while True:
            try:
                # Fetch new pools
                pools = await fetch_new_pools()
                
                # Process each pool
                for pool in pools:
                    await process_new_token(pool, client)
                
                # Wait before next check
                await asyncio.sleep(config.monitoring_interval)
                
            except Exception as e:
                print(f"Error in main loop: {e}")
                await asyncio.sleep(config.monitoring_interval)

if __name__ == "__main__":
    asyncio.run(main()) 