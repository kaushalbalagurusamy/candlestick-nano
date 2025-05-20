# AGENTS.md

This guide is intended for AI code assistants (e.g., Devin, Codex) to navigate and interact autonomously with the Candlestick Nano repository. It focuses on code structure, entry points, automated tasks, and testing hooks—minimizing redundancy with the human-oriented README.

## 1. Project Layout

Root directory files:

- `.envrc.sample` — environment variable template
- `buy.py` — batch-buy script using Jupiter SDK
- `exit_monitor.py` — token monitoring and auto-swap daemon
- `extractor.py` — candidate token extraction pipeline
- `tokens.json` — input for `buy.py`
- `candidates.json` — output of extractor
- `requirements.txt` and `requirements-dev.txt` — runtime and dev deps
- `pyproject.toml` — Ruff lint config
- `.github/workflows/ci.yml` — CI: lint, test, type-check, security scan

Key directory:

- `tests/` — pytest suites:
  - `test_env.py` — environment & API connectivity tests
  - `test_end_to_end_devnet.py` — Devnet end-to-end workflow

## 2. Environment & Configuration

- Source `.envrc` (copied from `.envrc.sample`) to load:
  - `WALLET_PRIVATE_KEY`, `SOLANA_CLUSTER`, `QUICKNODE_ENDPOINT`, `JUPITER_API_BASE_URL`, etc.
- Agents can inspect `.envrc.sample` for all required variables.

## 3. Entry Points & APIs

### buy.py

- `async def main()` — reads `tokens.json`, performs swaps via Jupiter SDK.
  - Invocation: `await buy.main()` when imported; or `python buy.py` as CLI.

### exit_monitor.py

- `async def monitor_coin(mint: str)` — watch and auto-swap a single token.
- `async def main()` — spawns one `monitor_coin` task per mint in `WATCH_MINTS`.
  - Invocation: `await exit_monitor.main()` when imported; or `python exit_monitor.py` as CLI.

### extractor.py

- `async def main()` — orchestration: fetch tokens, evaluate via extractors, write `candidates.json`.
- Helper functions:
  - `jupiter_extractor(session, mint)`
  - `dexscreener_extractor(session, mint)`
  - `onchain_extractor(client, mint)`
  - `evaluate_token(mint, client, session)`

## 4. Automated Workflows

### CI Pipeline

Defined in `.github/workflows/ci.yml`:

1. **lint**: Ruff + Flake8 checks
2. **test**: `pytest` (async tests via pytest-asyncio)
3. **pylint**: deep static analysis
4. **type-check**: MyPy
5. **security**: Bandit scan

Agents can trigger or monitor this workflow via GitHub Actions API.

## 5. Testing Hooks

- **test_env.py**: validates env vars, RPC connectivity, endpoint health, on-chain functions.
- **test_end_to_end_devnet.py**: Devnet E2E:
  1. Fetch first 10 mints
  2. Serialize to `devnet_tokens.json`
  3. Call `buy.main()` asynchronously
  4. Spawn `monitor_coin` tasks, verify liveness, cancel cleanly
  5. Emit logs to `devnet_test_results/YYYYMMDD_HHMMSS.txt`

Agents should run with `pytest tests/test_end_to_end_devnet.py` for full workflow (skip unless `SOLANA_CLUSTER=devnet`).

## 6. Agent Integration Tips

- **Import paths**: Add project root to `sys.path` to import modules (`buy`, `exit_monitor`, `extractor`).
- **Async runtime**: Use `pytest.mark.asyncio` or an `asyncio` event loop for direct invocation.
- **Logging**: Tests use Python `logging` for structured output.
- **Cleanup**: Restore or remove side-effects (e.g., `tokens.json`, background tasks) after automated runs.

---

Agents can reference this file for module entry points, testing hooks, and CI integration. For human instructions, refer to `README.md`. 