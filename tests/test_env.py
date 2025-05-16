import os
import pytest
import pytest_asyncio
import base58
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from jupiter_python_sdk.jupiter import Jupiter
import aiohttp
from solana.rpc.api import GetVersionResp

@pytest.mark.asyncio
async def test_env_variables():
    required_vars = ["WALLET_PRIVATE_KEY", "SOLANA_CLUSTER", "QUICKNODE_ENDPOINT", "JUPITER_API_BASE_URL"]
    for var in required_vars:
        assert var in os.environ, f"{var} is not set"
    assert os.environ["SOLANA_CLUSTER"] in ["devnet", "testnet", "mainnet-beta"]

@pytest.mark.asyncio
async def test_rpc_endpoint():
    rpc_url = os.environ["QUICKNODE_ENDPOINT"]
    client = AsyncClient(rpc_url)
    version = await client.get_version()
    # Ensure we get a proper GetVersionResp object
    assert isinstance(version, GetVersionResp), "RPC endpoint did not return GetVersionResp"
    await client.close()

@pytest.mark.asyncio
async def test_wallet_connection_and_balance():
    rpc_url = os.environ["QUICKNODE_ENDPOINT"]
    private_key = os.environ["WALLET_PRIVATE_KEY"]
    kp = Keypair.from_bytes(base58.b58decode(private_key))
    client = AsyncClient(rpc_url)
    balance_resp = await client.get_balance(kp.pubkey())
    assert isinstance(balance_resp.value, int)
    await client.close()

@pytest.mark.asyncio
async def test_jupiter_endpoints_configuration():
    rpc_url = os.environ["QUICKNODE_ENDPOINT"]
    metis_url = os.environ["JUPITER_API_BASE_URL"]
    client = AsyncClient(rpc_url)
    private_key = os.environ["WALLET_PRIVATE_KEY"]
    kp = Keypair.from_bytes(base58.b58decode(private_key))
    jup = Jupiter(
        async_client=client,
        keypair=kp,
        quote_api_url=f"{metis_url}/quote",
        swap_api_url=f"{metis_url}/swap"
    )
    assert hasattr(jup, 'quote') and callable(jup.quote), "Jupiter missing quote method"
    assert hasattr(jup, 'swap') and callable(jup.swap), "Jupiter missing swap method"
    await client.close()

@pytest.mark.asyncio
async def test_jupiter_tokens_endpoint():
    metis_url = os.environ["JUPITER_API_BASE_URL"]
    async with aiohttp.ClientSession() as session:
        resp = await session.get(f"{metis_url}/tokens")
        assert resp.status == 200, f"METIS tokens endpoint returned {resp.status}"
        data = await resp.json()
        assert isinstance(data, list), "METIS tokens endpoint did not return a list"
        assert data, "METIS tokens endpoint returned an empty list"

@pytest_asyncio.fixture(scope="module")
async def sample_mint():
    metis_url = os.environ["JUPITER_API_BASE_URL"]
    async with aiohttp.ClientSession() as session:
        resp = await session.get(f"{metis_url}/tokens")
        data = await resp.json()
        assert isinstance(data, list) and data, "No mints returned from METIS_URL"
        return data[0]

@pytest.mark.asyncio
async def test_dexscreener_endpoint(sample_mint):
    rpc_chain = "solana"
    url = f"https://api.dexscreener.com/token-pairs/v1/{rpc_chain}/{sample_mint}"
    async with aiohttp.ClientSession() as session:
        resp = await session.get(url)
        assert resp.status == 200, f"Dexscreener endpoint returned {resp.status}"
        pools = await resp.json()
        assert isinstance(pools, list), "Dexscreener endpoint did not return a list"

@pytest.mark.asyncio
async def test_onchain_extractor_rpc():
    # Use the native SOL mint which should always exist
    sol_mint = "So11111111111111111111111111111111111111112"
    rpc_url = os.environ["QUICKNODE_ENDPOINT"]
    client = AsyncClient(rpc_url)
    # supply
    supply_resp = await client.get_token_supply(Pubkey.from_string(sol_mint))
    assert isinstance(supply_resp.value.amount, int) or supply_resp.value.amount.isdigit(), "get_token_supply failed or returned invalid amount"
    # We only test token supply; largest accounts call can be flaky/timeout and is covered elsewhere
    await client.close() 