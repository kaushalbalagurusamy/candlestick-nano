# combined_daemon.py
import asyncio
import requests
from datetime import datetime
from typing import Dict, Set
from trading_bot_core import TradingBotCore
from config import config, WSOL_MINT

# State management
seen_pools: Set[str] = set()
active_positions: Dict[str, dict] = {}

async def fetch_new_pools() -> list:
    """Fetch recently deployed pools"""
    try:
        response = requests.get(f"{config.quicknode_endpoint}/new-pools")
        response.raise_for_status()
        return response.json().get("data", [])
    except Exception as e:
        print(f"Error fetching new pools: {e}")
        return []

async def process_new_pools(bot: TradingBotCore):
    """Process new pools for entry opportunities"""
    pools = await fetch_new_pools()
    
    for pool in pools:
        mint = pool.get("tokenAddress")
        if not mint or mint in seen_pools:
            continue
            
        seen_pools.add(mint)
        
        # Age check
        try:
            timestamp = pool.get("timestamp", "")
            pool_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            age_seconds = (datetime.utcnow() - pool_time.replace(tzinfo=None)).total_seconds()
            
            if age_seconds > config.max_token_age:
                print(f"Skipping {mint}: Too old ({age_seconds/3600:.1f} hours)")
                continue
        except:
            pass
        
        # Safety check
        if not await bot.check_token_safety(mint):
            print(f"Skipping {mint}: Has freeze authority")
            continue
        
        # Liquidity check
        quote = await bot.get_quote(WSOL_MINT, mint, 1_000_000_000, config.slippage_bps)
        if not quote:
            continue
            
        out_amount = int(quote.get("outAmount", 0))
        if out_amount < config.min_liquidity_threshold:
            print(f"Skipping {mint}: Insufficient liquidity")
            continue
        
        # Execute buy
        print(f"📈 Buying {mint} - Liquidity: {out_amount}")
        tx_sig = await bot.execute_swap(quote)
        
        if tx_sig:
            print(f"✅ Bought {mint} - TX: {tx_sig}")
            
            # Create limit order and track position
            order_pubkey = await bot.create_limit_order(mint, out_amount, config.take_profit_percentage)
            if order_pubkey:
                active_positions[mint] = {
                    "order_pubkey": order_pubkey,
                    "amount": out_amount,
                    "entry_price": 1_000_000_000 / out_amount,
                    "timestamp": datetime.utcnow()
                }

async def check_stop_loss_conditions(bot: TradingBotCore):
    """Check and execute stop-loss for all positions"""
    for mint, position in list(active_positions.items()):
        try:
            # Get current price via quote
            quote = await bot.get_quote(mint, WSOL_MINT, position["amount"], config.slippage_bps * 5)
            if not quote:
                continue
            
            # Calculate current value and price change
            current_value = int(quote.get("outAmount", 0))
            entry_value = position["amount"] * position["entry_price"]
            price_change = ((current_value - entry_value) / entry_value) * 100
            
            # Check stop-loss
            if price_change <= -config.stop_loss_percentage:
                print(f"⚠️ Stop-loss triggered for {mint}: {price_change:.2f}%")
                
                # Cancel limit order
                if position.get("order_pubkey"):
                    await bot.cancel_limit_order(position["order_pubkey"])
                
                # Execute market sell
                tx_sig = await bot.execute_swap(quote)
                if tx_sig:
                    print(f"🛑 Stop-loss executed - TX: {tx_sig}")
                    del active_positions[mint]
                    
        except Exception as e:
            print(f"Error checking stop-loss for {mint}: {e}")

async def update_positions(bot: TradingBotCore):
    """Update active positions from open orders"""
    orders = await bot.get_open_orders()
    
    # Sync positions with open orders
    order_mints = set()
    for order in orders:
        mint = order.get("inputMint")
        if mint and mint != WSOL_MINT:
            order_mints.add(mint)
            
            # Update position if not tracked
            if mint not in active_positions:
                active_positions[mint] = {
                    "order_pubkey": order.get("pubkey"),
                    "amount": int(order.get("makingAmount", 0)),
                    "entry_price": 1.0,  # Default
                    "timestamp": datetime.utcnow()
                }
    
    # Remove positions without orders
    for mint in list(active_positions.keys()):
        if mint not in order_mints:
            del active_positions[mint]

async def main():
    """Main combined daemon loop - MVP version"""
    print("🤖 Starting Combined Trading Bot (MVP)...")
    print(f"📊 Min Liquidity: {config.min_liquidity_threshold}")
    print(f"🛑 Stop-loss: {config.stop_loss_percentage}%")
    print(f"🎯 Take-profit: {config.take_profit_percentage}%")
    
    bot = TradingBotCore(config.quicknode_endpoint, config.wallet_address, config.wallet_private_key)
    await bot.setup()
    
    try:
        while True:
            try:
                # Entry: Process new pools
                await process_new_pools(bot)
                
                # Exit: Update positions and check stop-loss
                await update_positions(bot)
                await check_stop_loss_conditions(bot)
                
                # Status
                print(f"💼 Active positions: {len(active_positions)}")
                
                # Wait
                await asyncio.sleep(config.monitoring_interval)
                
            except Exception as e:
                print(f"Error in main loop: {e}")
                await asyncio.sleep(config.monitoring_interval)
                
    finally:
        await bot.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 