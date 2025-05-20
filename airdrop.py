import os
import asyncio
import base58
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair

RPC_URL = os.environ["QUICKNODE_ENDPOINT"]
PRIVATE_KEY = os.environ["WALLET_PRIVATE_KEY"]
CLUSTER = os.environ.get("SOLANA_CLUSTER", "devnet")

async def main() -> None:
    if CLUSTER not in {"devnet", "testnet"}:
        raise SystemExit("Airdrop only supported on devnet or testnet")

    client = AsyncClient(RPC_URL)
    kp = Keypair.from_bytes(base58.b58decode(PRIVATE_KEY))

    sig = await client.request_airdrop(kp.pubkey(), int(1_000_000_000))
    print(f"Requested {CLUSTER} airdrop: {sig.value}")
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
