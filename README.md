# Candlestick Nano

A Solana-based trading toolkit that: 

- Monitors token prices and liquidity using the Jupiter SDK 
- Executes SOL↔token swaps via QuickNode & Jupiter 
- Extracts and filters candidate tokens using Jupiter/Metis, DexScreener, and BirdEye APIs

---

## Prerequisites

- Python 3.9+
- [direnv](https://direnv.net/) (optional, for automatic env loading)
- `pip` or equivalent

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/kaushalbalagurusamy/candlestick-nano.git
   cd candlestick-nano
   ```

2. (Optional) Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Environment Variables

Copy `.envrc.sample` to `.envrc` and update the placeholders with your credentials:

```bash
export WALLET_PRIVATE_KEY="<your_base58_private_key>"
export SOLANA_CLUSTER="devnet"          # one of devnet | testnet | mainnet-beta
export QUICKNODE_ENDPOINT="<your_rpc_url>"
export JUPITER_API_BASE_URL="<your_jupiter_api_base_url>"
export BIRDEYE_API_KEY="<your_birdeye_api_key>"
# Optional overrides:
# export AMOUNT_SOL=1.0               # SOL amount to swap per token in buy.py
# export AMOUNT_SOL_DEFAULT=...      # etc.
```

Then allow the `.envrc`:

```bash
direnv allow
```

## Usage


### 1. Extract Candidates

```bash
python extractor.py
```

Fetches tradable mints from Jupiter/Metis, evaluates volume, liquidity, security, filters by criteria, and writes `candidates.json`.

### 2. Buy Tokens

```bash
python buy.py
```

Reads `tokens.json` and swaps a fixed SOL amount into each token.

### 3. Request Devnet/Testnet Airdrop

```bash
python airdrop.py
```

Triggers a faucet request for 1 SOL on the configured devnet or testnet RPC.
Run this script on a daily schedule so the wallet always has enough SOL for
testing.

### 4. Exit Monitor

```bash
python exit_monitor.py
```

Spawns watchers for each mint in your `WATCH_MINTS` env var and executes swaps when thresholds are met.

## Running Tests

This project includes async pytest tests for environment configuration, RPC & API endpoints, and wallet connectivity.

```bash
pytest
```

Ensure `pytest-asyncio` and other dependencies are installed. For devnet tests
you may need SOL; use `python airdrop.py` to request an airdrop first.

## End-to-End Devnet Workflow

For a complete Devnet run (buys and watchers), use the dedicated end-to-end test:

```bash
SOLANA_CLUSTER=devnet pytest tests/test_end_to_end_devnet.py
```

This will:
- Fetch the top 10 tokens from Jupiter/Metis
- Execute buys via `buy.py`
- Spawn watcher daemons for each token (runs for a short period then cancels)
- Generate logs in `devnet_test_results/YYYYMMDD_HHMMSS.txt`

## Agent Reference

An AI agent guide (`AGENTS.md`) is provided for automated integrations, outlining module entry points, CI hooks, and testing workflows.

## Project Structure

```
.
├── .envrc              # direnv configuration to load environment vars
├── AGENTS.md           # agent-specific guide for AI assistants
├── api_contract.yaml   # OpenAPI spec for HTTP endpoints
├── buy.py              # script to batch-buy tokens
├── extractor.py        # pipeline to extract/filter candidate tokens
├── exit_monitor.py     # daemon to monitor and auto-swap
├── airdrop.py          # helper to request devnet/testnet SOL
├── tokens.json         # input list of tokens for buy.py
├── candidates.json     # output of extractor.py
├── requirements.txt    # Python dependencies
├── requirements-dev.txt# development dependencies
├── pyproject.toml      # Ruff lint configuration
├── pytest.ini          # pytest configuration
├── .github/
│   └── workflows/
│       └── ci.yml      # GitHub Actions CI pipeline
└── tests/
    ├── test_env.py
    └── test_end_to_end_devnet.py
```

---

Happy trading! 🚀 