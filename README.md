# Candlestick Nano

On-chain high-frequency trading algorithm and automated liquidity execution engine for the Solana blockchain. Integrates QuickNode Metis for sub-millisecond pool discovery with Jupiter DEX routing for automated trade execution, take-profit limit orders, and stop-loss protection in volatile cryptocurrency markets.

---

## Architecture Overview

```
                            +----------------------------------+
                            | QuickNode Metis /new-pools Stream|
                            +-----------------+----------------+
                                              |
                                              v
                            +----------------------------------+
                            |     Token Evaluation Pipeline    |
                            | - Token Age Verification (< 23h) |
                            | - Freeze Authority Detection     |
                            | - Liquidity & Slippage Checks    |
                            +-----------------+----------------+
                                              |
                                              v
                            +----------------------------------+
                            |  Entry Execution (Jupiter v6)    |
                            | - Quote routing & optimal path   |
                            | - Atomic WSOL swap transaction   |
                            +-----------------+----------------+
                                              |
                                              v
                       +----------------------+----------------------+
                       |                                             |
                       v                                             v
        +------------------------------+             +-------------------------------+
        |  Take-Profit Management      |             |  Stop-Loss Position Monitor   |
        | - Jupiter limit order creation|             | - Periodic mark-to-market quote|
        | - Automated on-chain settlement|            | - Limit cancellation & sell   |
        +------------------------------+             +-------------------------------+
```

---

## Core Capabilities

* **Real-Time Pool Discovery**: Polls QuickNode Metis endpoints to detect newly deployed token pools with sub-second latency.
* **Rug-Pull & Safety Protections**: Inspects token mint metadata to reject contracts with active freeze authorities, verify minimum liquidity thresholds, and filter out stale tokens.
* **Automated Order Execution**: Executes swaps using the Jupiter v6 API with configurable slippage tolerance (basis points) and optimal route selection.
* **Dynamic Risk Management**: Automatically registers take-profit limit orders upon entry while concurrently monitoring mark-to-market prices to execute stop-loss market sells.
* **Flexible Process Architecture**: Supports single-process execution for local operations or decoupled modular daemons for scalable containerized deployment.

---

## Repository Structure

```
candlestick-nano/
├── src/
│   ├── config.py             # Lazy-loaded configuration manager with type casting
│   ├── trading_bot_core.py   # Core trading client (Solana RPC, Jupiter API, safety filters)
│   ├── combined_daemon.py    # Unified single-process entry and exit trading daemon
│   ├── entry_daemon.py       # Standalone pool discovery and entry execution daemon
│   ├── exit_daemon.py        # Standalone position monitoring and exit daemon
│   ├── quick_start_mvp.py    # Interactive terminal setup and wallet verification wizard
│   ├── extractor.py          # Candidate token filtering pipeline
│   ├── buy.py                # Manual single-token purchase utility
│   └── dependencies.py       # Dependency injection and client initialization
├── config/
│   ├── .envrc.sample         # Environment configuration template
│   ├── api_contract.yaml     # OpenAPI 3.0 specification for service endpoints
│   └── tokens.json           # Watchlist and seed token configurations
├── docs/
│   └── adr/                  # Architectural Decision Records (ADRs 0001 - 0005)
├── scripts/                  # Operational scripts for production and container management
├── tests/                    # Unit, integration, and devnet end-to-end test suite
├── docker-compose.yml        # Multi-container orchestration definition
├── Dockerfile                # Production container build specification
├── pyproject.toml            # Code style and Ruff linter configuration
└── requirements.txt          # Production Python dependencies
```

---

## Prerequisites

* **Python**: 3.9 or higher
* **QuickNode Account**: RPC endpoint with Metis API access
* **Solana Wallet**: Funded keypair (Devnet for testing, Mainnet-Beta for live operations)

---

## Quickstart

### 1. Installation

Clone the repository and install the dependencies:

```bash
git clone https://github.com/kaushalbalagurusamy/candlestick-nano.git
cd candlestick-nano

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment Configuration

Create your environment configuration from the template:

```bash
cp config/.envrc.sample config/.envrc
```

Configure the parameters in `config/.envrc`:

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `WALLET_PRIVATE_KEY` | String | *Required* | Base58-encoded private key |
| `WALLET_ADDRESS` | String | *Required* | Solana public wallet address |
| `QUICKNODE_ENDPOINT` | String | *Required* | QuickNode Metis RPC endpoint URL |
| `SOLANA_CLUSTER` | String | `devnet` | Target cluster (`devnet` or `mainnet-beta`) |
| `JUPITER_API_BASE_URL` | String | `https://quote-api.jup.ag/v6` | Jupiter quote API base URL |
| `AMOUNT_SOL` | Float | `1.0` | Base trade size in SOL |
| `MIN_LIQUIDITY_THRESHOLD` | Integer | `100000` | Minimum token output required for buy signal |
| `MAX_TOKEN_AGE` | Integer | `82800` | Maximum token age in seconds (default: 23 hours) |
| `SLIPPAGE_BPS` | Integer | `100` | Slippage tolerance in basis points (100 = 1%) |
| `TAKE_PROFIT_PERCENTAGE` | Float | `20.0` | Target gain percentage for limit orders |
| `STOP_LOSS_PERCENTAGE` | Float | `10.0` | Maximum loss percentage before market sell |
| `MONITORING_INTERVAL` | Integer | `30` | Interval between exit checks in seconds |

Load the environment into your active shell:

```bash
# Using direnv (recommended)
direnv allow config/.envrc

# Or export directly
export $(cat config/.envrc | grep -v '^#' | xargs)
```

---

## Running the Engine

### Option A: Interactive Quickstart Wizard

Validate your RPC connection, inspect current wallet balances, and select execution options:

```bash
python src/quick_start_mvp.py
```

### Option B: Unified Single-Process Daemon

Runs pool discovery, entry evaluation, and position monitoring within a single asynchronous event loop:

```bash
python src/combined_daemon.py
```

### Option C: Decoupled Multi-Daemon Pipeline

Run entry discovery and position management independently for isolated resource scaling:

```bash
# Terminal 1: Pool discovery and entry buys
python src/entry_daemon.py

# Terminal 2: Position monitoring and stop-loss / take-profit
python src/exit_daemon.py
```

### Option D: Docker Container Deployment

```bash
docker-compose up -d --build
```

---

## Testing & Verification

The test suite includes unit tests, API integration tests, and end-to-end devnet transaction validation:

```bash
# Run complete test suite
pytest

# Run devnet integration tests specifically
pytest tests/test_end_to_end_devnet.py -v

# Run with stdout logging
pytest -s
```

## Technical Documentation & ADRs

All architectural choices and operational guidelines are recorded in [`docs/adr/`](docs/adr/):

* [`docs/adr/0001-asyncio-daemon-execution-architecture.md`](docs/adr/0001-asyncio-daemon-execution-architecture.md) — Asyncio Daemon Execution Architecture
* [`docs/adr/0002-jupiter-dex-routing-and-swap-protocol.md`](docs/adr/0002-jupiter-dex-routing-and-swap-protocol.md) — Jupiter DEX Routing and Swap Protocol
* [`docs/adr/0003-pre-trade-safety-filters-and-freeze-detection.md`](docs/adr/0003-pre-trade-safety-filters-and-freeze-detection.md) — Pre-Trade Safety Filters and Freeze Detection
* [`docs/adr/0004-dual-track-position-risk-management.md`](docs/adr/0004-dual-track-position-risk-management.md) — Dual-Track Position Risk Management
* [`docs/adr/0005-elimination-of-cloud-infrastructure-in-favor-of-self-hosting.md`](docs/adr/0005-elimination-of-cloud-infrastructure-in-favor-of-self-hosting.md) — Elimination of Cloud Infrastructure in Favor of Self-Hosting
* [`docs/adr/0006-transition-to-embedded-zero-cloud-operating-model.md`](docs/adr/0006-transition-to-embedded-zero-cloud-operating-model.md) — Transition to Embedded Zero-Cloud Operating Model

---

## Risk & Safety Disclaimers

Automated trading on decentralized networks involves inherent financial and technical risks:
* **Market Volatility & Slippage**: High-frequency token launches on Solana may experience extreme volatility, front-running, and rapid liquidity extraction.
* **Testing Protocol**: Always validate configuration parameters and transaction flows against Solana `devnet` before routing real capital on `mainnet-beta`.
* **Private Key Security**: Never commit `.envrc` or plain-text private keys to version control. Keys should be provided strictly via environment variables or runtime secret injection.