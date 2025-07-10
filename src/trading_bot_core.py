"""
Core trading bot functionality for interacting with QuickNode Métis API.

This module provides the central trading logic used across all bot implementations,
including swap execution, limit order management, and safety checks.
"""
import time
import base64
import base58
import requests
from typing import Dict, Optional, Any
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solana.rpc.types import TxOpts

class TradingBotCore:
    """
    Core trading functionality shared across daemons.
    
    Provides unified interface for interacting with QuickNode Métis API
    for token swaps, limit orders, and safety checks.
    
    Attributes:
        endpoint: QuickNode Métis API endpoint URL
        wallet_address: Public key of trading wallet
        keypair: Solana keypair for transaction signing
        client: Async Solana RPC client
    """
    
    def __init__(self, endpoint: str, wallet_address: str, private_key: str) -> None:
        """
        Initialize trading bot core.
        
        Args:
            endpoint: QuickNode Métis-enabled endpoint URL
            wallet_address: Public wallet address
            private_key: Base58-encoded private key
            
        Raises:
            ValueError: If private key is invalid
        """
        self.endpoint: str = endpoint
        self.wallet_address: str = wallet_address
        self.keypair: Keypair = Keypair.from_bytes(base58.b58decode(private_key))
        self.client: Optional[AsyncClient] = None
        
    async def setup(self) -> None:
        """
        Initialize async client.
        
        Must be called before using any async methods.
        """
        self.client = AsyncClient(self.endpoint)
        
    async def cleanup(self) -> None:
        """
        Cleanup resources.
        
        Should be called when shutting down to properly close connections.
        """
        if self.client:
            await self.client.close()
    
    async def get_quote(self, input_mint: str, output_mint: str, amount: int, slippage_bps: int) -> Optional[Dict[str, Any]]:
        """
        Get swap quote from Métis API.
        
        Args:
            input_mint: Token mint address to swap from
            output_mint: Token mint address to swap to
            amount: Amount in smallest unit (lamports for SOL)
            slippage_bps: Slippage tolerance in basis points (100 = 1%)
            
        Returns:
            Quote response dictionary if successful, None if failed
            
        Raises:
            requests.RequestException: If API request fails
        """
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
    
    async def execute_swap(self, quote_data: Dict[str, Any]) -> Optional[str]:
        """
        Execute swap transaction.
        
        Args:
            quote_data: Quote response from get_quote method
            
        Returns:
            Transaction signature if successful, None if failed
            
        Raises:
            requests.RequestException: If API request fails
            Exception: If transaction signing or sending fails
        """
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
    
    async def create_limit_order(self, mint: str, amount: int, profit_percentage: float) -> Optional[Dict[str, Any]]:
        """
        Create take-profit limit order.
        
        Args:
            mint: Token mint address to sell
            amount: Amount of tokens to sell
            profit_percentage: Target profit percentage (e.g., 20 for 20%)
            
        Returns:
            Limit order response if successful, None if failed
            
        Raises:
            requests.RequestException: If API request fails
        """
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
    
    async def get_open_orders(self) -> list[Dict[str, Any]]:
        """
        Get all open limit orders for the wallet.
        
        Returns:
            List of open order dictionaries, empty list if failed
            
        Raises:
            requests.RequestException: If API request fails
        """
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
    
    async def cancel_limit_order(self, order_pubkey: str) -> Optional[str]:
        """
        Cancel a limit order.
        
        Args:
            order_pubkey: Public key of the order to cancel
            
        Returns:
            Transaction signature if successful, None if failed
            
        Raises:
            requests.RequestException: If API request fails
            Exception: If transaction signing or sending fails
        """
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
        """
        Check if token is safe to trade (no freeze authority).
        
        Tokens with freeze authority can have transfers frozen by the authority,
        making them potentially unsafe for trading.
        
        Args:
            mint: Token mint address to check
            
        Returns:
            True if token has no freeze authority, False otherwise
            
        Raises:
            Exception: If RPC call fails
        """
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