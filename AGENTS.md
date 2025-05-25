# AGENTS.md

This guide is intended for AI code assistants (e.g., Claude, Devin, Codex) to navigate and interact autonomously with the Candlestick Nano trading bot. It focuses on the new architecture with QuickNode Métis integration.

## 1. Project Architecture

The project now supports two deployment modes:

### Self-Hosted Daemons
- `entry_daemon.py` — Monitors new pools and executes buys
- `exit_daemon.py` — Manages positions and stop-loss
- `combined_daemon.py` — Runs both entry and exit logic

### Serverless Functions
- `quicknode_functions/entry_function.js` — Event-driven entry logic
- `quicknode_functions/exit_function.js` — Alert-driven exit logic

### Legacy Scripts (still functional)
- `buy.py` — Manual batch-buy using Jupiter SDK
- `exit_monitor.py` — Original exit monitoring daemon
- `extractor.py` — Candidate token extraction pipeline

## 2. Environment & Configuration

Key environment variables:
- `QUICKNODE_ENDPOINT` — QuickNode Métis API endpoint
- `WALLET_ADDRESS` — Public key for trading
- `WALLET_PRIVATE_KEY` — Private key (base58)
- `MIN_LIQUIDITY_THRESHOLD` — Minimum token liquidity
- `MAX_TOKEN_AGE` — Maximum age in seconds
- `STOP_LOSS_PERCENTAGE` — Stop-loss trigger %
- `TAKE_PROFIT_PERCENTAGE` — Take-profit target %

## 3. Entry Points & APIs

### entry_daemon.py

Main functions:
- `fetch_new_pools()` — Get new pools from Métis `/new-pools`
- `check_freeze_authority(client, mint)` — Rug pull detection
- `get_liquidity_quote(mint)` — Check liquidity via `/quote`
- `execute_swap(quote_data)` — Execute buy via `/swap`
- `create_limit_order(mint, amount)` — Create take-profit order

Entry: `python entry_daemon.py` or `await main()`

### exit_daemon.py

Main functions:
- `get_open_limit_orders()` — Fetch open orders
- `cancel_limit_order(order_pubkey)` — Cancel an order
- `execute_market_sell(mint, amount)` — Emergency exit
- `monitor_price_feed()` — WebSocket price monitoring

Entry: `python exit_daemon.py` or `await main()`

### combined_daemon.py

Main class: `TradingBot`
- `process_new_pools()` — Entry logic
- `check_stop_loss_conditions()` — Exit logic
- `update_positions()` — Sync state

Entry: `python combined_daemon.py` or `await main()`

### QuickNode Functions

- `entry_function.main(params)` — Handles new pool events
- `exit_function.main(params)` — Handles price alerts

## 4. Key APIs Used

### QuickNode Métis Endpoints
- `GET /new-pools` — Fetch recent liquidity pools
- `GET /quote` — Get swap quotes with slippage
- `POST /swap` — Execute token swaps
- `POST /limit-orders/create` — Create limit orders
- `GET /limit-orders/open` — List open orders
- `POST /limit-orders/cancel` — Cancel orders

### Solana RPC
- `getAccountInfo` — Fetch mint data
- `sendRawTransaction` — Submit transactions

## 5. Testing Hooks

- **test_env.py**: Validates environment and API connectivity
- **test_end_to_end_devnet.py**: Full workflow test

Run with: `pytest tests/`

## 6. Agent Integration Tips

### Async Handling
All main functions are async. Use:
```python
import asyncio
asyncio.run(main())
```

### State Management
- Self-hosted: In-memory sets/dicts
- Serverless: QuickNode KV store

### Error Handling
- Wrap API calls in try/except
- Log errors but continue monitoring
- Implement exponential backoff for rate limits

### Performance Optimization
- Batch RPC calls when possible
- Use connection pooling
- Cache token metadata

## 7. Code Modifications

When modifying:
1. Keep files under 200 lines
2. Maintain async patterns
3. Update both self-hosted and serverless versions
4. Add environment variables to `.envrc.sample`
5. Update documentation

## 8. Deployment

### Self-Hosted
```bash
# Development
python combined_daemon.py

# Production
systemctl start trading-bot
```

### Serverless
```bash
cd quicknode_functions
qn function deploy entry_function.js
qn function deploy exit_function.js
```

## 9. Monitoring

Key metrics to track:
- New pools processed/hour
- Buy success rate
- Position P&L
- API rate limit usage
- Transaction costs

## 10. Common Tasks

### Add New Filter
1. Modify `process_new_token()` in entry_daemon.py
2. Update `checkTokenSafety()` in entry_function.js
3. Add config to environment variables

### Change Risk Parameters
1. Update `.envrc`
2. Restart daemons or redeploy functions
3. Existing positions use old parameters

### Debug Failed Transaction
1. Check logs for transaction signature
2. Look up on Solana Explorer
3. Common issues: slippage, insufficient funds

---

Agents should reference this file for understanding the new architecture and integration points. The codebase now emphasizes real-time monitoring and automated execution over batch processing. 