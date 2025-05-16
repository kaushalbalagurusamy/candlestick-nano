import os
import json
import asyncio
import pytest
import logging
from datetime import datetime
from pathlib import Path
import aiohttp

from buy import main as buy_main
from watcher_daemon import monitor_coin
from solana.rpc.async_api import AsyncClient

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
    mints = data.get("mints", [])[:10]
    tokens = [{"symbol": t.get("symbol"), "address": t.get("address")} for t in mints]
    assert tokens, "No tokens fetched"
    logger.info(f"Fetched {len(tokens)} tokens: {tokens}")

    # 3. Serialize tokens to tests/devnet_tokens.json
    tokens_file = Path(__file__).parent / "devnet_tokens.json"
    tokens_file.write_text(json.dumps(tokens))

    # 4. Perform buys via buy_main
    # Copy the test token file to root tokens.json
    root_tokens = Path(__file__).parent.parent / "tokens.json"
    backup = root_tokens.read_text() if root_tokens.exists() else None
    root_tokens.write_text(tokens_file.read_text())
    try:
        # Run buy script
        await buy_main()
        logger.info("buy_main completed successfully")
    finally:
        # Restore original tokens.json
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
    # Cleanup
    logger.removeHandler(fh) 