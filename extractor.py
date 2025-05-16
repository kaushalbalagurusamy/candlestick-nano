import os, json, asyncio, aiohttp, base64, base58
from datetime import datetime
from solana.publickey import PublicKey
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TokenAccountOpts, TxOpts
from spl.token.async_client import AsyncToken
from solders.transaction import VersionedTransaction

# ----------------------------------------
# Configuration & Criteria (as before)
# ----------------------------------------
METIS_URL       = os.getenv("METIS_URL")
RPC_URL         = os.getenv("RPC_URL")
PRIVATE_KEY     = os.getenv("PRIVATE_KEY")
BATCH_CONCURRENCY = 10

FILTER_CRITERIA = {
    "max_mintable":         False,
    "max_freezable":        False,
    "max_transfer_fee_pct": 1.0,    # will skip, as on-chain tokens rarely have Solana fees
    "max_top_holder_pct":   20.0,
    "max_age_hours":        24,
}

# ----------------------------------------
# Helper to fetch Jupiter’s token list
# ----------------------------------------
async def fetch_json(session, url, **kwargs):
    async with session.get(url, **kwargs) as resp:
        resp.raise_for_status()
        return await resp.json()

# ----------------------------------------
# On-Chain Extractor replacing BirdEye
# ----------------------------------------
async def onchain_extractor(client: AsyncClient, mint: str):
    """Fetch on-chain safety and holder metrics via RPC calls."""
    m_pk = PublicKey(mint)

    # 1. Total supply
    supply_resp = await client.get_token_supply(m_pk)  # getTokenSupply  [oai_citation:4‡QuickNode](https://www.quicknode.com/docs/solana/getTokenSupply?utm_source=chatgpt.com)
    total_supply = int(supply_resp.value.amount)

    # 2. Top accounts
    largest = await client.get_token_largest_accounts(m_pk)  # getTokenLargestAccounts  [oai_citation:5‡QuickNode](https://www.quicknode.com/docs/solana/getTokenLargestAccounts?utm_source=chatgpt.com)
    if not largest.value:
        return None
    top_amount = int(largest.value[0].amount)
    top_pct    = (top_amount / total_supply * 100) if total_supply else 100.0

    # 3. Mint & Freeze authority via AsyncToken.get_mint_info
    token_client = AsyncToken(client, m_pk, PublicKey("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"), payer=None)
    mint_info    = await token_client.get_mint_info()         # get_mint_info  [oai_citation:6‡michaelhly.com](https://michaelhly.com/solana-py/spl/token/async_client/?utm_source=chatgpt.com)
    mintable     = mint_info.mint_authority is not None
    freezable    = mint_info.freeze_authority is not None

    # 4. Holder count via getTokenAccountsByOwner
    acct_resp = await client.get_token_accounts_by_owner(
        PublicKey(mint_info.mint_authority or PublicKey(0)),  # dummy owner to skip
        TokenAccountOpts(mint=m_pk)
    )  # getTokenAccountsByOwner  [oai_citation:7‡QuickNode](https://www.quicknode.com/docs/solana/getTokenAccountsByOwner?utm_source=chatgpt.com)
    holder_count = len(acct_resp.value)

    return {
        "mintable":       mintable,
        "freezable":      freezable,
        "top_holder_pct": top_pct,
        "holders_count":  holder_count,
    }

# ----------------------------------------
# Remaining Extractors (unchanged)
# ----------------------------------------
# ... include jupiter_extractor() and dexscreener_extractor() here ...

# ----------------------------------------
# Evaluation Function
# ----------------------------------------
async def evaluate_token(mint, client, session):
    # parallel extractors: jupiter, dexscreener, onchain
    jup_task  = jupiter_extractor(session, mint)
    dex_task  = dexscreener_extractor(session, mint)
    chain_task= onchain_extractor(client, mint)
    jup, dex, chain = await asyncio.gather(jup_task, dex_task, chain_task)

    if any(x is None for x in (jup, dex, chain)):
        return None

    # age check
    age_h = (datetime.utcnow() - jup["launch_time"]).total_seconds() / 3600

    # apply filters
    crit = FILTER_CRITERIA
    checks = [
        not chain["mintable"] or crit["max_mintable"],
        not chain["freezable"] or crit["max_freezable"],
        chain["top_holder_pct"] <= crit["max_top_holder_pct"],
        age_h <= crit["max_age_hours"],
    ]
    if all(checks):
        # assemble result as before
        return { "mint": mint, **jup, **dex, **chain }
    return None

# ----------------------------------------
# Orchestration (main)
# ----------------------------------------
async def main():
    async with aiohttp.ClientSession() as session, AsyncClient(RPC_URL) as client:
        # 1. discover mints from Jupiter/Metis
        tokens = await fetch_json(session, f"{METIS_URL}/tokens")  # 
        mints  = tokens.get("mints", [])

        # 2. evaluate in bounded concurrency
        sem  = asyncio.Semaphore(BATCH_CONCURRENCY)
        async def sem_eval(m):
            async with sem:
                return await evaluate_token(m, client, session)

        results = await asyncio.gather(*[sem_eval(m) for m in mints])
        passed  = [r for r in results if r]

        # 3. output
        with open("candidates.json","w") as f:
            json.dump(passed, f, default=str, indent=2)
        print(f"Found {len(passed)} candidates.")

if __name__=="__main__":
    asyncio.run(main())