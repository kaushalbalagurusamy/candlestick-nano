import os
import asyncio
import base58
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair

RPC_URL = os.environ["QUICKNODE_ENDPOINT"]
CLUSTER = os.environ.get("SOLANA_CLUSTER", "devnet")
PRIVATE_KEY = os.environ["WALLET_PRIVATE_KEY"]

async def request_airdrop(amount_sol: float = 1.0) -> None:
    if CLUSTER == "mainnet-beta":
        raise RuntimeError("Airdrops are not available on mainnet")

    client = AsyncClient(RPC_URL)
    keypair = Keypair.from_bytes(base58.b58decode(PRIVATE_KEY))
    sig = await client.request_airdrop(keypair.pubkey(), int(amount_sol * 1e9))
    await client.confirm_transaction(sig.value)
    await client.close()
    print(f"Airdropped {amount_sol} SOL on {CLUSTER}")

async def main() -> None:
    amount = float(os.getenv("AIRDROP_AMOUNT_SOL", "1"))
    await request_airdrop(amount)

if __name__ == "__main__":
    asyncio.run(main())
