# Candlestick Nano

A high-performance Solana trading bot that leverages QuickNode's Métis API for automated token trading with advanced filtering and risk management.

## Features

- **Real-time Pool Monitoring**: Tracks new liquidity pools via QuickNode's `/new-pools` endpoint
- **Advanced Token Filtering**: 
  - Freeze authority detection (rug pull protection)
  - Liquidity threshold checks
  - Token age verification
- **Automated Trading**:
  - Entry: Automatic buys for qualifying tokens
  - Exit: Take-profit limit orders via Jupiter
  - Stop-loss monitoring with Chainlink integration
- **Dual Deployment Options**:
  - Self-hosted daemons for full control
  - Serverless QuickNode Functions for zero maintenance

## Architecture

The bot consists of two main components:

1. **Entry System**: Monitors new pools, filters tokens, executes buys
2. **Exit System**: Manages positions with limit orders and stop-loss

Both can run as:
- Self-hosted Python daemons
- Serverless QuickNode Functions

### AWS Infrastructure

View the [AWS Architecture Diagram](docs/architecture.mmd) for a visual representation of the infrastructure.

**✅ Deployed Infrastructure**:
- **CloudFront CDN**: https://d16t0at6xusy1j.cloudfront.net
- **Region**: us-west-2
- **Cost**: ~$0.40-$0.80/month (Free Tier eligible)

Key AWS services used (all Free Tier eligible):
- **S3**: Static content and data storage
- **CloudFront**: CDN for web interface
- **Cognito**: User authentication
- **DynamoDB**: User data storage
- **Lambda**: Solana data extraction
- **ECS Fargate**: Trading bot containers
- **EC2 Spot**: Cost-effective compute
- **Budget Alerts**: Cost monitoring

📋 **Deployment Details**: See [infra/DEPLOYMENT_SUMMARY.md](infra/DEPLOYMENT_SUMMARY.md)

---

## Prerequisites

- Python 3.9+
- [direnv](https://direnv.net/) (optional, for automatic env loading)
- QuickNode account with Métis API access
- Solana wallet with funds

## Directory Structure

The project follows a clean, organized structure:

```
candlestick-nano/
├── src/                    # Core application code
│   ├── combined_daemon.py  # All-in-one trading bot
│   ├── entry_daemon.py     # Entry monitoring daemon
│   ├── exit_daemon.py      # Exit monitoring daemon
│   ├── exit_monitor.py     # Legacy exit monitoring
│   ├── exit_utils.py       # Exit strategy utilities
│   ├── extractor.py        # Data extraction utilities
│   ├── trading_bot_core.py # Core trading logic
│   ├── buy.py             # Manual buy functionality
│   └── quick_start_mvp.py  # Quick start MVP script
├── config/                 # Configuration files
│   ├── .envrc              # Environment variables
│   ├── .envrc.sample       # Environment template
│   ├── api_contract.yaml   # API contract definitions
│   ├── tokens.json         # Token configurations
│   └── faucet_state.json   # Airdrop state tracking
├── scripts/                # Utility scripts
│   ├── setup_production.sh # Production setup
│   ├── setup_auto_airdrop.sh # Airdrop setup
│   ├── auto_airdrop.sh     # Background airdrop runner
│   ├── cursor_start.sh     # Development helper
│   └── fix_cursor_shell.sh # Shell fix utility
├── legacy/                 # Legacy components
│   ├── airdrop.py          # SOL airdrop collector
│   └── airdrop_status.py   # Airdrop status checker
├── logs/                   # Log files
│   ├── airdrop.log         # Airdrop activity logs
│   └── airdrop.pid         # Process ID files
├── systemd/                # System service files
│   ├── candlestick-bot.service  # Main bot service
│   └── airdrop-auto.service     # Airdrop service
├── tests/                  # Test suite
├── docs/                   # Documentation
├── infra/                  # Infrastructure (Terraform)
├── quicknode_functions/    # Serverless functions
├── requirements.txt        # Python dependencies
├── docker-compose.yml      # Container orchestration
├── Dockerfile             # Container definition
└── README.md              # This file
```

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

Copy `config/.envrc.sample` to `config/.envrc` and update the placeholders with your credentials:

```bash
cp config/.envrc.sample config/.envrc
# Edit config/.envrc with your credentials
```

Example `config/.envrc`:

```bash
export WALLET_PRIVATE_KEY="<your_base58_private_key>"
export WALLET_ADDRESS="<your_wallet_address>"
export SOLANA_CLUSTER="mainnet-beta"
export QUICKNODE_ENDPOINT="<your_métis_endpoint>"

# Trading Parameters
export MIN_LIQUIDITY_THRESHOLD="100000"
export MAX_TOKEN_AGE="82800"
export STOP_LOSS_PERCENTAGE="10"
export TAKE_PROFIT_PERCENTAGE="20"
export MONITORING_INTERVAL="30"
```

Then allow the `.envrc`:

```bash
direnv allow config/.envrc
```

## Quick Start (MVP)

The fastest way to get started:

```bash
python src/quick_start_mvp.py
```

This interactive script will help you choose the best deployment option.

### Option 1: Combined Daemon (Recommended for MVP)

The simplest way to run the bot:

```bash
python src/combined_daemon.py
```

This single process handles both entry (finding new tokens) and exit (stop-loss/take-profit) logic.

**Benefits:**
- ✅ Single process to manage
- ✅ Lowest operational cost
- ✅ Easy to monitor and debug
- ✅ All features included

### Option 2: Serverless (QuickNode Functions)

For production with zero infrastructure:

See [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) for detailed serverless setup.

**Benefits:**
- ✅ No servers to manage
- ✅ Pay only when trades execute
- ✅ Auto-scaling
- ✅ Built-in monitoring

### Option 3: Manual Trading (Legacy)

For manual token discovery and trading:

- `src/extractor.py` - Find candidate tokens
- `src/buy.py` - Execute manual buys
- `src/exit_monitor.py` - Monitor positions

## New Features

### QuickNode Métis Integration
- `/new-pools` - Real-time pool discovery
- `/quote` - Liquidity and slippage checks
- `/swap` - Transaction execution
- `/limit-orders/*` - Take-profit automation

### Advanced Filtering
- Freeze authority detection
- Minimum liquidity requirements
- Token age limits
- Slippage protection

### Risk Management
- Automated take-profit orders
- Stop-loss monitoring
- Position tracking via KV store

## Code Style

To aid automated agents, keep individual code files under **200 lines** whenever
possible. Split logic into smaller modules if a file grows beyond this limit.

## Running Tests

This project includes async pytest tests for environment configuration, RPC & API endpoints, and wallet connectivity.

```bash
pytest
```

## Safety & Disclaimers

⚠️ **WARNING**: This is experimental software for educational purposes. 

- Always test on devnet first
- Never risk more than you can afford to lose
- Cryptocurrency trading carries significant risk
- Past performance doesn't guarantee future results

## Contributing

1. Fork the repository
2. Create a feature branch
3. Keep files under 200 lines
4. Add tests for new features
5. Submit a pull request

## Support

- QuickNode Discord: [discord.gg/quicknode](https://discord.gg/quicknode)
- GitHub Issues: [github.com/kaushalbalagurusamy/candlestick-nano/issues](https://github.com/kaushalbalagurusamy/candlestick-nano/issues)

---

Happy trading! 🚀 