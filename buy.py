import os
import json
import asyncio
import base64
import base58

from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TxOpts
from solders.transaction import VersionedTransaction
from solders.keypair import Keypair
from jupiter_python_sdk.jupiter import Jupiter

RPC_URL     = os.environ["QUICKNODE_ENDPOINT"]
METIS_URL   = os.environ["JUPITER_API_BASE_URL"]
PRIVATE_KEY = os.environ["WALLET_PRIVATE_KEY"]
# How much SOL to swap per token
AMOUNT_SOL  = float(os.getenv("AMOUNT_SOL", "1"))  

SOL_MINT    = "So11111111111111111111111111111111111111112"
SLIPPAGE_BPS= 10  # 0.1%

async def buy_token(jup: Jupiter, client: AsyncClient, mint: str):
    amount = int(AMOUNT_SOL * 1e9)
    tx_b64 = await jup.swap(
        input_mint   = SOL_MINT,
        output_mint  = mint,
        amount       = amount,
        slippage_bps = SLIPPAGE_BPS
    )
    tx    = VersionedTransaction.from_bytes(base64.b64decode(tx_b64))
    sig   = await client.send_raw_transaction(
        bytes(tx),
        opts=TxOpts(skip_preflight=True)
    )
    print(f"Swapped SOL→{mint}, tx sig: {sig}")

async def main():
    # 1. load and pop tokens.json
    tokens = []
    with open("tokens.json") as f:
        tokens = json.load(f)
    # assume tokens.json is a list of {"symbol":..., "address":...}
    
    # 2. setup Solana client & Jupiter once
    client = AsyncClient(RPC_URL)
    keypair = Keypair.from_bytes(base58.b58decode(PRIVATE_KEY))
    jup = Jupiter(
        async_client    = client,
        keypair         = keypair,
        quote_api_url   = f"{METIS_URL}/quote",
        swap_api_url    = f"{METIS_URL}/swap"
    )

    # 3. spawn one buy task per token popped from the list
    tasks = []
    while tokens:
        token = tokens.pop(0)
        mint  = token["address"]
        tasks.append(asyncio.create_task(buy_token(jup, client, mint)))

    # 4. wait for all swaps to finish
    await asyncio.gather(*tasks)

    await client.close()

if __name__ == "__main__":
    asyncio.run(main())