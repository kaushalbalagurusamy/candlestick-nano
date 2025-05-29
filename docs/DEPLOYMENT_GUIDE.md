# Candlestick Nano - Trading Bot Deployment Guide

This guide covers deploying the automated Solana trading bot using either self-hosted daemons or serverless QuickNode Functions.

## Architecture Overview

The trading bot consists of two main components:
- **Entry Logic**: Monitors new pools, filters tokens, and executes buys
- **Exit Logic**: Manages take-profit limit orders and stop-loss triggers

## Option 1: Self-Hosted Daemons

### Prerequisites
- Python 3.9+
- QuickNode Métis API access
- Solana wallet with funds

### Setup

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Configure environment**:
Update `.envrc` with your credentials:
```bash
export QUICKNODE_ENDPOINT="https://your-quicknode-metis-endpoint"
export WALLET_ADDRESS="your-wallet-address"
export WALLET_PRIVATE_KEY="your-private-key"
export MIN_LIQUIDITY_THRESHOLD="100000"
export STOP_LOSS_PERCENTAGE="10"
export TAKE_PROFIT_PERCENTAGE="20"
```

### Running the Daemons

#### Option A: Run separately
```bash
# Terminal 1 - Entry daemon
python entry_daemon.py

# Terminal 2 - Exit daemon  
python exit_daemon.py
```

#### Option B: Run combined
```bash
python combined_daemon.py
```

### Process Management

For production, use systemd or supervisor:

**systemd service** (`/etc/systemd/system/trading-bot.service`):
```ini
[Unit]
Description=Solana Trading Bot
After=network.target

[Service]
Type=simple
User=trading
WorkingDirectory=/opt/candlestick-nano
Environment="PATH=/opt/candlestick-nano/.venv/bin"
ExecStart=/opt/candlestick-nano/.venv/bin/python combined_daemon.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Option 2: QuickNode Functions (Serverless)

### Prerequisites
- QuickNode account with Functions access
- QuickNode CLI installed

### Setup

1. **Install QuickNode CLI**:
```bash
npm install -g @quicknode/cli
qn login
```

2. **Configure functions**:
Edit `quicknode_functions/deployment_config.json` with your values.

### Deploy Functions

```bash
# Deploy entry function
cd quicknode_functions
qn function deploy entry_function.js --config deployment_config.json --function entry_function

# Deploy exit function  
qn function deploy exit_function.js --config deployment_config.json --function exit_function
```

### Configure Triggers

1. **Entry Function - New Pool Stream**:
   - Go to QuickNode dashboard
   - Create a new Stream for pool creation events
   - Target your entry function endpoint

2. **Exit Function - Price Alerts**:
   - Create QuickAlerts for Chainlink price feeds
   - Set threshold conditions
   - Target your exit function endpoint

## Configuration Parameters

### Entry Parameters
- `MIN_LIQUIDITY_THRESHOLD`: Minimum token liquidity (default: 100,000)
- `MAX_TOKEN_AGE`: Maximum age of token in seconds (default: 82,800)
- `SLIPPAGE_BPS`: Buy slippage in basis points (default: 100)

### Exit Parameters
- `STOP_LOSS_PERCENTAGE`: Stop-loss trigger percentage (default: 10%)
- `TAKE_PROFIT_PERCENTAGE`: Take-profit target percentage (default: 20%)
- `CHAINLINK_AGGREGATOR`: Chainlink price feed address (optional)

## Monitoring & Maintenance

### Logs
- Self-hosted: Check daemon output or systemd logs
- Functions: View in QuickNode dashboard

### Performance Metrics
- Monitor transaction success rate
- Track profit/loss per position
- Review gas costs

### Security Best Practices
1. Never commit private keys
2. Use environment variables or secrets management
3. Implement rate limiting
4. Monitor for unusual activity

## API Rate Limits

QuickNode Métis rate limits:
- Free tier: 10 RPS, 25M requests/month
- Paid tiers: Up to 999 RPS

Adjust `MONITORING_INTERVAL` based on your tier.

## Troubleshooting

### Common Issues

1. **Transaction failures**:
   - Check wallet balance
   - Increase slippage
   - Verify token liquidity

2. **Rate limit errors**:
   - Increase monitoring interval
   - Upgrade QuickNode tier

3. **Missed opportunities**:
   - Decrease monitoring interval
   - Optimize filters

### Support

- QuickNode Discord: [discord.gg/quicknode](https://discord.gg/quicknode)
- GitHub Issues: [github.com/your-repo/issues](https://github.com/your-repo/issues)

## Advanced Features

### Custom Filters
Modify `entry_daemon.py` to add custom token filters:
- Volume requirements
- Holder distribution
- Social signals

### Alternative DEXs
The bot supports Jupiter aggregation which includes:
- Raydium
- Orca
- Serum
- And more

### Position Sizing
Implement dynamic position sizing based on:
- Liquidity depth
- Risk parameters
- Portfolio balance

## Cost Analysis

### Self-Hosted
- Server: ~$20-100/month
- RPC costs: Based on QuickNode tier
- Gas fees: ~0.001 SOL per transaction

### Serverless
- Functions: Pay per execution
- No server costs
- Same RPC and gas fees

## Next Steps

1. Start with testnet/devnet deployment
2. Run paper trading for validation
3. Deploy with small amounts
4. Scale based on performance

Remember: This is experimental software. Always test thoroughly and never risk more than you can afford to lose. 