# exit_daemon.py
import os
import json
import asyncio
import base64
import base58
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solana.rpc.types import TxOpts
from exit_utils import (
    get_open_limit_orders, 
    cancel_limit_order_request,
    get_market_sell_quote,
    get_swap_transaction,
    create_websocket_connection,
    subscribe_to_chainlink_logs
)

# Environment Configuration
QN = os.environ["QUICKNODE_ENDPOINT"]
WALLET_ADDRESS = os.environ["WALLET_ADDRESS"]
WALLET_PRIVATE_KEY = os.environ["WALLET_PRIVATE_KEY"]
STOP_LOSS_PERCENTAGE = float(os.getenv("STOP_LOSS_PERCENTAGE", "10"))
TAKE_PROFIT_PERCENTAGE = float(os.getenv("TAKE_PROFIT_PERCENTAGE", "20"))
MONITORING_INTERVAL = int(os.getenv("MONITORING_INTERVAL", "60"))
CHAINLINK_AGGREGATOR = os.getenv("CHAINLINK_AGGREGATOR", "")
WSOL_MINT = "So11111111111111111111111111111111111111112"

# Track active positions
active_positions = {}

async def cancel_limit_order(order_pubkey: str):
    """Cancel a specific limit order"""
    try:
        cancel_data = await cancel_limit_order_request(QN, WALLET_ADDRESS, order_pubkey)
        if not cancel_data:
            return None
            
        # Sign and send cancel transaction
        async with AsyncClient(QN) as client:
            keypair = Keypair.from_bytes(base58.b58decode(WALLET_PRIVATE_KEY))
            tx_bytes = base64.b64decode(cancel_data["tx"])
            tx = VersionedTransaction.from_bytes(tx_bytes)
            tx.sign([keypair])
            
            sig = await client.send_raw_transaction(
                bytes(tx),
                opts=TxOpts(skip_preflight=True)
            )
            return sig.value
    except Exception as e:
        print(f"Error canceling order: {e}")
        return None

async def execute_market_sell(mint: str, amount: int):
    """Execute immediate market sell (stop-loss)"""
    try:
        # Get quote for sell
        quote_data = await get_market_sell_quote(QN, mint, WSOL_MINT, amount)
        if not quote_data:
            return None
            
        # Get swap transaction
        swap_data = await get_swap_transaction(QN, WALLET_ADDRESS, quote_data)
        if not swap_data:
            return None
        
        # Sign and send transaction
        async with AsyncClient(QN) as client:
            keypair = Keypair.from_bytes(base58.b58decode(WALLET_PRIVATE_KEY))
            tx_bytes = base64.b64decode(swap_data["swapTransaction"])
            tx = VersionedTransaction.from_bytes(tx_bytes)
            tx.sign([keypair])
            
            sig = await client.send_raw_transaction(
                bytes(tx),
                opts=TxOpts(skip_preflight=True)
            )
            
            print(f"🛑 Stop-loss executed for {mint} - TX: {sig.value}")
            return sig.value
    except Exception as e:
        print(f"Error executing market sell: {e}")
        return None

async def monitor_price_feed():
    """Monitor Chainlink price feed for stop-loss triggers"""
    if not CHAINLINK_AGGREGATOR:
        return
    
    try:
        ws = create_websocket_connection(QN)
        if not ws:
            return
            
        subscribe_to_chainlink_logs(ws, CHAINLINK_AGGREGATOR)
        
        while True:
            try:
                result = ws.recv()
                data = json.loads(result)
                
                # Process price update
                if "params" in data and "result" in data["params"]:
                    await process_price_update(data["params"]["result"])
                    
            except Exception as e:
                print(f"WebSocket error: {e}")
                break
                
        ws.close()
    except Exception as e:
        print(f"Error monitoring price feed: {e}")

async def process_price_update(log_data: dict):
    """Process Chainlink price update and check stop-loss conditions"""
    try:
        current_price = extract_price_from_log(log_data)
        
        # Check each active position
        for mint, position in list(active_positions.items()):
            entry_price = position["entry_price"]
            amount = position["amount"]
            
            # Calculate price change percentage
            price_change = ((current_price - entry_price) / entry_price) * 100
            
            # Check stop-loss condition
            if price_change <= -STOP_LOSS_PERCENTAGE:
                print(f"⚠️ Stop-loss triggered for {mint}: {price_change:.2f}%")
                
                # Cancel limit order if exists
                if "order_pubkey" in position:
                    await cancel_limit_order(position["order_pubkey"])
                
                # Execute market sell
                await execute_market_sell(mint, amount)
                
                # Remove from active positions
                del active_positions[mint]
                
    except Exception as e:
        print(f"Error processing price update: {e}")

def extract_price_from_log(log_data: dict) -> float:
    """Extract price from Chainlink log data"""
    # This is a placeholder - actual implementation depends on the aggregator
    # Typically you'd decode the log data to get the price
    return 0.0

async def update_active_positions():
    """Update active positions from open orders and token balances"""
    try:
        # Get open limit orders
        orders = await get_open_limit_orders(QN, WALLET_ADDRESS)
        
        # Update positions
        for order in orders:
            mint = order.get("inputMint")
            if mint and mint != WSOL_MINT:
                active_positions[mint] = {
                    "order_pubkey": order.get("pubkey"),
                    "amount": int(order.get("makingAmount", 0)),
                    "entry_price": float(order.get("rate", 1.0))
                }
                
    except Exception as e:
        print(f"Error updating positions: {e}")

async def main():
    """Main exit daemon loop"""
    print("🛡️ Starting exit daemon...")
    print(f"Stop-loss: {STOP_LOSS_PERCENTAGE}%")
    print(f"Take-profit: {TAKE_PROFIT_PERCENTAGE}%")
    
    # Start price feed monitor in background
    if CHAINLINK_AGGREGATOR:
        asyncio.create_task(monitor_price_feed())
    
    while True:
        try:
            # Update active positions
            await update_active_positions()
            
            # Log status
            print(f"📊 Monitoring {len(active_positions)} positions")
            
            # Wait before next check
            await asyncio.sleep(MONITORING_INTERVAL)
            
        except Exception as e:
            print(f"Error in main loop: {e}")
            await asyncio.sleep(MONITORING_INTERVAL)

if __name__ == "__main__":
    asyncio.run(main()) 