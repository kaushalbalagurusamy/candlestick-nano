import os
import sys
import json
import asyncio
import pytest
import logging
from datetime import datetime
from pathlib import Path
import aiohttp
import base58
from solders.keypair import Keypair
import base64
import types
from solana.rpc.async_api import AsyncClient

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import exit_monitor
from buy import main as buy_main
from exit_monitor import monitor_coin

# Skip end-to-end if not running on devnet
pytestmark = pytest.mark.skipif(
    os.environ.get("SOLANA_CLUSTER") != "devnet",
    reason="Devnet only end-to-end tests"
)

@ pytest.mark.asyncio
async def test_end_to_end_devnet(tmp_path):
    # Setup logger
    results_dir = Path("devnet_test_results")
    results_dir.mkdir(exist_ok=True)
    log_file = results_dir / f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt"
    logger = logging.getLogger("e2e")
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(log_file)
    logger.addHandler(fh)

    # 2. Fetch top 10 tokens from Jupiter/Metis
    metis_url = os.environ["JUPITER_API_BASE_URL"]
    async with aiohttp.ClientSession() as session:
        resp = await session.get(f"{metis_url}/tokens")
        assert resp.status == 200, f"Tokens endpoint returned {resp.status}"
        data = await resp.json()
    # Data is already a list of tokens, not a dict with "mints" key
    tokens_list = data[:10] if isinstance(data, list) else data.get("mints", [])[:10]
    tokens = [{"symbol": t.get("symbol", "UNKNOWN"), "address": t.get("address", "")} for t in tokens_list if t.get("address")]
    assert tokens, "No tokens fetched"
    logger.info(f"Fetched {len(tokens)} tokens: {tokens}")

    # 3. Serialize tokens to tests/devnet_tokens.json
    tokens_file = Path(__file__).parent / "devnet_tokens.json"
    tokens_file.write_text(json.dumps(tokens))

    # 4. Perform buys via buy_main (airdrop now handled by external cron)
    root_tokens = Path(__file__).parent.parent / "tokens.json"
    backup = root_tokens.read_text() if root_tokens.exists() else None
    root_tokens.write_text(tokens_file.read_text())

    os.environ["AMOUNT_SOL"] = "0.001"

    try:
        await buy_main()
        logger.info("buy_main completed successfully")
    finally:
        if backup is not None:
            root_tokens.write_text(backup)

    # 5. Start watcher tasks
    addresses = [t["address"] for t in tokens]
    watcher_tasks = [asyncio.create_task(monitor_coin(addr)) for addr in addresses]
    # Allow watchers to run briefly
    await asyncio.sleep(5)
    for addr, task in zip(addresses, watcher_tasks):
        assert not task.done(), f"Watcher for {addr} exited prematurely"
        logger.info(f"Watcher for {addr} is running")
    # Cancel watchers
    for task in watcher_tasks:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    logger.info("Watchers cancelled cleanly")
    logger.removeHandler(fh)


@pytest.mark.asyncio
async def test_exit_monitor_executes_swap(monkeypatch):
    """Ensure the exit monitor performs a swap when price thresholds hit."""

    send_called = {
        "sent": False,
    }

    class DummyClient:
        def __init__(self, *a, **k):
            pass

        async def get_token_accounts_by_owner(self, *a, **k):
            return types.SimpleNamespace(value=[types.SimpleNamespace(pubkey="X")])

        async def get_token_account_balance(self, *a, **k):
            return types.SimpleNamespace(value=types.SimpleNamespace(ui_amount=1.0))

        async def send_raw_transaction(self, *a, **k):
            send_called["sent"] = True

        async def close(self):
            pass

    class DummyJupiter:
        def __init__(self, *a, **k):
            self.calls = 0

        async def quote(self, *a, **k):
            self.calls += 1
            amount = 1000 if self.calls == 1 else 1300
            return types.SimpleNamespace(output_amount=amount)

        async def swap(self, *a, **k):
            return base64.b64encode(b"tx").decode()

    class DummyKeypair:
        @staticmethod
        def from_bytes(b):
            return DummyKeypair()

        def pubkey(self):
            return "pk"

    class DummyTx:
        def __bytes__(self):
            return b"tx"

    monkeypatch.setattr(exit_monitor, "AsyncClient", DummyClient)
    monkeypatch.setattr(exit_monitor, "Jupiter", DummyJupiter)
    monkeypatch.setattr(exit_monitor, "Keypair", DummyKeypair)
    monkeypatch.setattr(exit_monitor.VersionedTransaction, "from_bytes", lambda b: DummyTx())
    monkeypatch.setattr(exit_monitor.PublicKey, "from_string", lambda s: s)
    monkeypatch.setattr(exit_monitor.asyncio, "sleep", lambda *a, **k: asyncio.sleep(0))

    await exit_monitor.monitor_coin("dummy_mint")

    assert send_called["sent"] is True

