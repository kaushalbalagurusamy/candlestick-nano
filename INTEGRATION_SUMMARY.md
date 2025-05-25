# Candlestick Nano - QuickNode Métis Integration Summary

## Overview

The codebase has been enhanced with QuickNode's Métis API integration, providing real-time pool monitoring, advanced filtering, and both self-hosted and serverless deployment options.

## New Components Added

### 1. Self-Hosted Daemons

- **`combined_daemon.py`** (181 lines) ⭐ **RECOMMENDED FOR MVP**
  - Single process combining entry and exit logic
  - Lowest operational cost
  - Easiest to deploy and monitor
  - Uses `trading_bot_core.py` for shared functionality

- **`trading_bot_core.py`** (157 lines)
  - Core trading functionality module
  - Swap execution, limit orders, safety checks
  - Shared by all daemon implementations

- **`entry_daemon.py`** (198 lines) - Optional standalone
  - Dedicated pool monitoring
  - Can be used if you want separate processes

- **`exit_daemon.py`** (197 lines) - Optional standalone  
  - Dedicated position monitoring
  - Uses `exit_utils.py` for helper functions

### 2. QuickNode Functions (Serverless)

- **`quicknode_functions/entry_function.js`** (172 lines)
  - Event-driven pool monitoring
  - Stateless execution with KV store
  - Stream/webhook triggers

- **`quicknode_functions/exit_function.js`** (193 lines)
  - Alert-based stop-loss execution
  - Scheduled position monitoring
  - Chainlink integration ready

- **`quicknode_functions/package.json`**
  - Dependencies for serverless functions

- **`quicknode_functions/deployment_config.json`**
  - Trigger and environment configuration

### 3. Documentation

- **`DEPLOYMENT_GUIDE.md`** (195 lines)
  - Comprehensive deployment instructions
  - Self-hosted and serverless setup
  - Troubleshooting guide

- **Updated `README.md`**
  - New architecture overview
  - Feature highlights
  - Safety disclaimers

- **Updated `AGENTS.md`**
  - AI agent integration guide
  - New entry points documented
  - Common tasks explained

### 4. Testing

- **`tests/test_metis_integration.py`** (119 lines)
  - Unit tests for Métis endpoints
  - Mock-based testing
  - Environment validation

## Key Features Implemented

### Entry Logic
- Real-time pool discovery via `/new-pools`
- Freeze authority detection (rug protection)
- Liquidity threshold checks via `/quote`
- Automatic buy execution via `/swap`
- Take-profit order creation via `/limit-orders/create`

### Exit Logic
- Limit order monitoring via `/limit-orders/open`
- Stop-loss percentage triggers
- Order cancellation via `/limit-orders/cancel`
- Market sell execution
- Optional Chainlink price feed support

### State Management
- Self-hosted: In-memory tracking
- Serverless: QuickNode KV store
- Position tracking with entry prices

## Configuration Updates

### New Environment Variables
- `MIN_LIQUIDITY_THRESHOLD` - Minimum token liquidity
- `MAX_TOKEN_AGE` - Token age limit
- `STOP_LOSS_PERCENTAGE` - Stop-loss trigger
- `TAKE_PROFIT_PERCENTAGE` - Take-profit target
- `SLIPPAGE_BPS` - Buy slippage tolerance
- `CHAINLINK_AGGREGATOR` - Price feed address

### Updated Files
- `.envrc.sample` - Complete configuration template
- `requirements.txt` - Added `requests`, `websocket-client`
- `extractor.py` - Fixed import issue

## Architecture Benefits

### Self-Hosted Benefits
- Full control over execution
- Lower latency for high-frequency trading
- Custom modifications easy
- No per-execution costs

### Serverless Benefits
- Zero infrastructure management
- Auto-scaling
- Pay-per-use pricing
- Built-in monitoring

## API Endpoints Used

### QuickNode Métis
- `/new-pools` - Pool discovery
- `/quote` - Price quotes
- `/swap` - Trade execution
- `/limit-orders/*` - Order management

### Rate Limits
- Free: 10 RPS, 25M requests/month
- Paid: Up to 999 RPS

## Migration Path

1. Existing users can continue using legacy scripts
2. New deployments should use combined_daemon.py
3. High-scale users should consider serverless
4. Test on devnet before mainnet

## Security Considerations

- Private keys never committed
- Environment variable isolation
- Slippage protection built-in
- Freeze authority checks mandatory

## MVP Recommendations

### For Fastest Path to Production:

1. **Use `combined_daemon.py`** - Single process, all features
2. **Start on devnet** - Test with free tokens first
3. **Use minimal parameters** - Start conservative:
   - MIN_LIQUIDITY_THRESHOLD: 100000
   - STOP_LOSS_PERCENTAGE: 10
   - TAKE_PROFIT_PERCENTAGE: 20
   - MONITORING_INTERVAL: 30

### Cost Comparison:

| Deployment | Setup Time | Monthly Cost | Best For |
|------------|------------|--------------|----------|
| Combined Daemon | 5 minutes | $5-20 (VPS) | MVP, Testing |
| QuickNode Functions | 30 minutes | $0-50 (usage) | Production |
| Separate Daemons | 10 minutes | $5-20 (VPS) | Advanced users |

### Quick Commands:

```bash
# Test your setup
python quick_start_mvp.py

# Run MVP bot
python combined_daemon.py

# Deploy to production
systemctl start trading-bot
```

## Next Steps

1. Run `./quick_start_mvp.py` to get started
2. Test on devnet with small amounts
3. Monitor for 24-48 hours
4. Gradually increase parameters
5. Consider serverless for production scale

The integration maintains backward compatibility while providing superior features for automated trading on Solana. 