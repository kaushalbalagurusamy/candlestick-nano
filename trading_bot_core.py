# trading_bot_core.py
import os
import time
import json
import base64
import base58
import requests
from datetime import datetime
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solana.rpc.types import TxOpts

class TradingBotCore:
    """Core trading functionality shared across daemons"""
    
    def __init__(self, endpoint: str, wallet_address: str, private_key: str):
        self.endpoint = endpoint
        self.wallet_address = wallet_address
        self.keypair = Keypair.from_bytes(base58.b58decode(private_key))
        self.client = None
        
    async def setup(self):
        """Initialize async client"""
        self.client = AsyncClient(self.endpoint)
        
    async def cleanup(self):
        """Cleanup resources"""
        if self.client:
            await self.client.close()
    
    async def get_quote(self, input_mint: str, output_mint: str, amount: int, slippage_bps: int) -> dict:
        """Get swap quote from Métis"""
        try:
            params = {
                "inputMint": input_mint,
                "outputMint": output_mint,
                "amount": str(amount),
                "slippageBps": str(slippage_bps)
            }
            response = requests.get(f"{self.endpoint}/quote", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting quote: {e}")
            return None
    
    async def execute_swap(self, quote_data: dict) -> str:
        """Execute swap transaction"""
        try:
            swap_response = requests.post(
                f"{self.endpoint}/swap",
                json={
                    "owner": self.wallet_address,
                    "quoteResponse": quote_data
                }
            )
            swap_response.raise_for_status()
            swap_data = swap_response.json()
            
            tx_bytes = base64.b64decode(swap_data["swapTransaction"])
            tx = VersionedTransaction.from_bytes(tx_bytes)
            tx.sign([self.keypair])
            
            sig = await self.client.send_raw_transaction(
                bytes(tx),
                opts=TxOpts(skip_preflight=True)
            )
            
            return sig.value
        except Exception as e:
            print(f"Error executing swap: {e}")
            return None
    
    async def create_limit_order(self, mint: str, amount: int, profit_percentage: float):
        """Create take-profit limit order"""
        try:
            take_profit_amount = int(amount * (1 + profit_percentage / 100))
            
            response = requests.post(
                f"{self.endpoint}/limit-orders/create",
                json={
                    "maker": self.wallet_address,
                    "payer": self.wallet_address,
                    "inputMint": mint,
                    "outputMint": "So11111111111111111111111111111111111111112",
                    "params": {
                        "makingAmount": str(amount),
                        "takingAmount": str(take_profit_amount),
                        "expiredAt": str(int(time.time()) + 86400)
                    }
                }
            )
            
            if response.status_code == 200:
                return response.json().get("order")
        except Exception as e:
            print(f"Error creating limit order: {e}")
        return None
    
    async def get_open_orders(self) -> list:
        """Get all open limit orders"""
        try:
            response = requests.get(
                f"{self.endpoint}/limit-orders/open",
                params={"wallet": self.wallet_address}
            )
            response.raise_for_status()
            return response.json().get("orders", [])
        except Exception as e:
            print(f"Error fetching open orders: {e}")
            return []
    
    async def cancel_limit_order(self, order_pubkey: str):
        """Cancel a limit order"""
        try:
            response = requests.post(
                f"{self.endpoint}/limit-orders/cancel",
                json={
                    "owner": self.wallet_address,
                    "orderPubkey": order_pubkey
                }
            )
            response.raise_for_status()
            
            cancel_data = response.json()
            tx_bytes = base64.b64decode(cancel_data["tx"])
            tx = VersionedTransaction.from_bytes(tx_bytes)
            tx.sign([self.keypair])
            
            sig = await self.client.send_raw_transaction(
                bytes(tx),
                opts=TxOpts(skip_preflight=True)
            )
            return sig.value
        except Exception as e:
            print(f"Error canceling order: {e}")
            return None

    async def check_token_safety(self, mint: str) -> bool:
        """Check if token is safe (no freeze authority)"""
        try:
            resp = await self.client.get_account_info_json_parsed(mint)
            if not resp.value:
                return False
            
            mint_data = resp.value.data.parsed.get("info", {})
            freeze_authority = mint_data.get("freezeAuthority")
            
            # Safe if no freeze authority
            return freeze_authority is None
        except Exception as e:
            print(f"Error checking token safety: {e}")
            return False 