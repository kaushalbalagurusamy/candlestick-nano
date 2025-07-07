"""
Manual token buying script for executing individual trades.

This script reads tokens from a JSON file and executes buy orders
using Jupiter aggregator for best price execution.
"""
import json
import asyncio
import base64
import base58
from typing import Dict, List, Any, Optional

from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TxOpts
from solders.transaction import VersionedTransaction
from solders.keypair import Keypair
from jupiter_python_sdk.jupiter import Jupiter
from config import config, SOL_MINT

# Constants
SLIPPAGE_BPS: int = 500  # 5% slippage tolerance

async def buy_token(jup: Jupiter, client: AsyncClient, mint: str) -> Optional[str]:
    """
    Execute a buy order for a specific token.
    
    Args:
        jup: Jupiter SDK instance for swap execution
        client: Solana RPC client
        mint: Token mint address to buy
        
    Returns:
        Transaction signature if successful, None if failed
        
    Raises:
        Exception: If swap construction or execution fails
    """
    try:
        amount: int = int(config.amount_sol * 1e9)  # Convert SOL to lamports
        
        # Get swap transaction from Jupiter
        tx_b64: str = await jup.swap(
            input_mint   = SOL_MINT,
            output_mint  = mint,
            amount       = amount,
            slippage_bps = SLIPPAGE_BPS
        )
        
        # Decode and send transaction
        tx: VersionedTransaction = VersionedTransaction.from_bytes(base64.b64decode(tx_b64))
        sig = await client.send_raw_transaction(
            bytes(tx),
            opts=TxOpts(skip_preflight=True)
        )
        
        print(f"Swapped SOL→{mint}, tx sig: {sig}")
        return sig.value
    except Exception as e:
        print(f"Error buying {mint}: {e}")
        return None

async def main() -> None:
    """
    Main execution function.
    
    Reads tokens from tokens.json and executes concurrent buy orders
    for all tokens in the list.
    
    Expected JSON format:
    [
        {"symbol": "TOKEN", "address": "mint_address"},
        ...
    ]
    """
    # Load tokens from JSON file
    tokens: List[Dict[str, str]] = []
    try:
        with open("tokens.json", "r") as f:
            tokens = json.load(f)
    except FileNotFoundError:
        print("Error: tokens.json not found")
        return
    except json.JSONDecodeError:
        print("Error: Invalid JSON in tokens.json")
        return
    
    if not tokens:
        print("No tokens to buy")
        return
    
    # Setup Solana client and Jupiter SDK
    client: AsyncClient = AsyncClient(config.quicknode_endpoint)
    keypair: Keypair = Keypair.from_bytes(base58.b58decode(config.wallet_private_key))
    jup: Jupiter = Jupiter(
        async_client    = client,
        keypair         = keypair,
        quote_api_url   = f"{config.jupiter_api_base_url}/quote",
        swap_api_url    = f"{config.jupiter_api_base_url}/swap"
    )

    # Create concurrent buy tasks for all tokens
    tasks: List[asyncio.Task] = []
    while tokens:
        token: Dict[str, str] = tokens.pop(0)
        mint: str = token["address"]
        print(f"Queuing buy order for {token.get('symbol', 'Unknown')} ({mint})")
        tasks.append(asyncio.create_task(buy_token(jup, client, mint)))

    # Wait for all swaps to complete
    results: List[Optional[str]] = await asyncio.gather(*tasks)
    
    # Report results
    successful: int = sum(1 for r in results if r is not None)
    print(f"\nCompleted {successful}/{len(results)} buy orders successfully")

    await client.close()

if __name__ == "__main__":
    asyncio.run(main())