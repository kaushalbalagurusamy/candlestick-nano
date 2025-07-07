# CLAUDE.md - Candlestick Nano Trading Bot

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Candlestick Nano is a high-performance Solana trading bot that leverages QuickNode's Métis API for automated token trading. The bot monitors new liquidity pools, applies safety filters, executes trades, and manages positions with stop-loss and take-profit strategies.

## Essential Commands

### Development

```bash
# Install dependencies
pip install -r requirements.txt

# Quick start interactive setup
python src/quick_start_mvp.py

# Run combined daemon (recommended)
python src/combined_daemon.py

# Run tests
pytest

# Run linting
ruff check src/

# Auto-fix linting issues
ruff check --fix src/
```

### Code Quality

- **Linting**: `ruff check src/` - Uses Ruff for Python linting
- **Testing**: `pytest` - Test framework for unit and integration tests
- **Type Checking**: Python type hints enforced throughout codebase

## Terminal Interaction Guidelines

### **CRITICAL: Terminal Execution Protocol**

#### ReAct Pattern Implementation (Thought-Action-Observation-Reflection)

Every terminal interaction MUST follow this structured approach:

1. **THOUGHT**: Analyze what needs to be done
   - Example: "I need to check if wallet has SOL before running the bot"
2. **ACTION**: Execute ONE single, atomic command
   - Example: `solana balance`
3. **OBSERVATION**: Wait for complete output and analyze
   - Example: Check balance output or error messages
4. **REFLECTION**: Determine next step based on observation
   - Example: "Sufficient balance confirmed, can proceed with bot execution"

#### Common Terminal Failures to Avoid

- **Premature Continuation (42% of failures)**: NEVER proceed before command completes
- **Output Misinterpretation (23% of failures)**: Don't assume failure from partial output
- **Path Confusion (18% of failures)**: Always track current directory with `pwd`
- **Command Chaining Issues (12% of failures)**: Avoid `&&` or `;` - execute one command at a time

### **MANDATORY: Command Execution Rules**

#### Single Command Execution

```bash
# ❌ WRONG - Don't chain commands
pip install -r requirements.txt && python src/combined_daemon.py

# ✅ CORRECT - Execute separately
pip install -r requirements.txt
# (wait for completion)
python src/combined_daemon.py
```

#### State Tracking Requirements

**Before ANY file operation:**

```bash
pwd                    # Verify current directory
ls -la                 # Check file existence (includes hidden files)
```

**After directory changes:**

```bash
cd src
pwd                    # ALWAYS confirm location after cd
```

**Environment verification:**

```bash
echo $SHELL           # Check shell type
which python          # Verify Python availability
echo $PATH            # Check PATH if command not found
solana --version      # Verify Solana CLI installed
```

### **Shell State Management**

#### Working Directory Awareness

- **ALWAYS** run `pwd` after `cd` commands
- **NEVER** assume you're in a specific directory
- **VERIFY** location before file operations

#### Process Management

**Long-running processes** (daemons, monitoring):

```bash
# These run indefinitely - don't wait for completion
python src/combined_daemon.py  # Trading bot daemon
python src/entry_daemon.py     # Entry monitoring
python src/exit_daemon.py      # Exit monitoring

# Check if running (in another terminal):
ps aux | grep python          # Find Python processes
lsof -i :8080                 # Check port usage
```

**Background execution:**

- Use `&` suffix for Unix/Mac: `python src/combined_daemon.py &`
- Use `nohup` for persistent background: `nohup python src/combined_daemon.py > bot.log 2>&1 &`
- Track PID for later termination

### **Error Recovery Strategies**

#### Permission Errors

```bash
# Detection: "Permission denied", "EACCES"
ls -la config/.envrc         # Check ownership
chmod 600 config/.envrc      # Secure private key file
```

#### RPC Connection Errors

```bash
# Detection: "Connection refused", "RPC error"
curl -X POST $QUICKNODE_ENDPOINT  # Test endpoint
solana config get                  # Check Solana config
```

#### Wallet Balance Errors

```bash
# Detection: "Insufficient funds", "Transaction failed"
solana balance                     # Check SOL balance
solana balance --url devnet        # Check on devnet
```

### **Platform-Specific Commands**

#### Solana CLI Commands

| Purpose              | Command                        | Notes                    |
| -------------------- | ------------------------------ | ------------------------ |
| Check balance        | `solana balance`               | Shows SOL in wallet      |
| Airdrop (devnet)     | `solana airdrop 2`             | Request 2 SOL on devnet  |
| Show wallet address  | `solana address`               | Display public key       |
| Check cluster        | `solana config get`            | Show current RPC         |
| Recent transactions  | `solana transaction-history`   | Last 20 transactions     |

### **Output Interpretation**

#### Success Indicators

- Exit code 0 (check with `echo $?`)
- Transaction signatures in output
- "Success" or "Complete" messages
- Expected balance changes

#### Trading Bot Specific Outputs

- "Found new pool: [address]" - New liquidity pool detected
- "Executing buy order" - Trade initiated
- "Stop-loss triggered" - Position closed at loss
- "Limit order created" - Take-profit order placed

### **Safety Protocols**

#### Dangerous Commands - REQUIRE EXPLICIT CONFIRMATION

- ANY mainnet transactions without testing
- Private key operations
- Large trade executions
- Configuration changes affecting real funds

#### Credential Handling

- **NEVER** echo private keys
- **USE** environment variables: `export WALLET_PRIVATE_KEY=xxx`
- **READ** from `.envrc` files with proper permissions
- **SECURE** config files: `chmod 600 config/.envrc`

## Key Architecture Decisions

### 1. Modular Design
- **Core Module** (`trading_bot_core.py`): Centralized trading logic shared across all implementations
- **Multiple Entry Points**: Combined daemon, separate daemons, or serverless functions
- **Clean Separation**: Entry logic (finding tokens) vs Exit logic (managing positions)

### 2. Deployment Flexibility
- **Self-Hosted**: Python daemons for full control
- **Serverless**: QuickNode Functions for zero maintenance
- **Containerized**: Docker support for easy deployment

### 3. Safety First
- Freeze authority detection prevents rug pulls
- Minimum liquidity thresholds ensure tradability
- Configurable stop-loss and take-profit parameters

## Core Components

### Trading Bot Core (`src/trading_bot_core.py`)
Central module providing:
- `get_quote()`: Price quotes via Métis `/quote` endpoint
- `execute_swap()`: Trade execution via `/swap`
- `create_limit_order()`: Take-profit orders via `/limit-orders/create`
- `check_token_safety()`: Freeze authority verification
- `cancel_limit_order()`: Stop-loss execution

### Combined Daemon (`src/combined_daemon.py`) ⭐ RECOMMENDED
Single process handling both entry and exit:
- Monitors new pools every 30 seconds
- Applies safety and liquidity filters
- Executes buys and creates limit orders
- Tracks positions and triggers stop-loss

### Entry Daemon (`src/entry_daemon.py`)
Dedicated pool monitoring:
- Fetches new pools from `/new-pools`
- Filters by age, safety, and liquidity
- Executes buy trades
- Creates take-profit limit orders

### Exit Daemon (`src/exit_daemon.py`)
Position management:
- Syncs with open limit orders
- Monitors price movements
- Triggers stop-loss orders
- Cancels and market sells when needed

## Configuration

### Environment Variables (config/.envrc)
```bash
# Core Requirements
QUICKNODE_ENDPOINT          # Métis-enabled endpoint
WALLET_ADDRESS             # Public key
WALLET_PRIVATE_KEY         # Base58 private key

# Trading Parameters
MIN_LIQUIDITY_THRESHOLD    # Min token liquidity (default: 100000)
MAX_TOKEN_AGE             # Max token age in seconds (default: 82800)
STOP_LOSS_PERCENTAGE      # Stop-loss trigger % (default: 10)
TAKE_PROFIT_PERCENTAGE    # Take-profit target % (default: 20)
MONITORING_INTERVAL       # Check interval seconds (default: 30)
SLIPPAGE_BPS             # Buy slippage tolerance (default: 100)
```

### Quick Start Commands
```bash
# Test setup
python src/quick_start_mvp.py

# Run combined daemon (recommended)
python src/combined_daemon.py

# Docker deployment
docker-compose up combined-daemon

# Systemd service
sudo systemctl start candlestick-bot
```

## API Endpoints Used

### QuickNode Métis
- `/new-pools` - Discover new liquidity pools
- `/quote` - Get swap quotes and check liquidity
- `/swap` - Execute token swaps
- `/limit-orders/create` - Create take-profit orders
- `/limit-orders/open` - List active orders
- `/limit-orders/cancel` - Cancel orders for stop-loss

### Rate Limits
- Free Tier: 10 RPS, 25M requests/month
- Adjust `MONITORING_INTERVAL` based on tier

## Trading Flow

### Entry Process
1. Fetch new pools from Métis
2. Filter out seen pools
3. Check token age (<23 hours default)
4. Verify no freeze authority
5. Check liquidity via quote
6. Execute buy swap
7. Create take-profit limit order
8. Track position internally

### Exit Process
1. Sync positions with open orders
2. Get current price via quote
3. Calculate price change %
4. If below stop-loss:
   - Cancel limit order
   - Execute market sell
5. If limit order fills:
   - Position auto-closes

## Testing & Development

### Local Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Test on devnet first
export SOLANA_CLUSTER="devnet"
```

### Debugging Tips
- Check logs for transaction signatures
- Verify wallet has SOL for fees
- Monitor rate limit usage
- Test with small amounts first

## Production Deployment

### Option 1: VPS/Cloud Server
```bash
# Setup systemd service
sudo cp systemd/candlestick-bot.service /etc/systemd/system/
sudo systemctl enable candlestick-bot
sudo systemctl start candlestick-bot
```

### Option 2: Docker
```bash
# Build and run
docker-compose up -d combined-daemon

# View logs
docker logs -f candlestick-combined
```

### Option 3: Serverless (QuickNode Functions)
See `docs/DEPLOYMENT_GUIDE.md` for detailed setup

## AWS Infrastructure

The project includes Terraform configs for AWS deployment:
- S3 for static content
- CloudFront CDN
- ECS Fargate for bot containers
- DynamoDB for state storage
- Lambda for data extraction

Cost: ~$0.40-$0.80/month with Free Tier

## Common Commands

### Linting & Type Checking
```bash
# Run linter
ruff check src/

# Auto-fix issues
ruff check --fix src/
```

### Manual Trading (Legacy)
```bash
# Find tokens
python src/extractor.py

# Buy specific token
python src/buy.py

# Monitor positions
python src/exit_monitor.py
```

### Background Services
```bash
# Auto-airdrop service (devnet)
./scripts/setup_auto_airdrop.sh

# Production setup
./scripts/setup_production.sh
```

## Safety Considerations

⚠️ **IMPORTANT WARNINGS**:
- This is experimental software
- Always test on devnet first
- Never risk more than you can afford to lose
- Monitor closely during initial deployment
- Keep private keys secure and never commit them

## Performance Optimization

### Reduce Latency
- Deploy close to Solana validators
- Use dedicated RPC endpoints
- Minimize monitoring interval

### Improve Success Rate
- Increase slippage for volatile tokens
- Filter by higher liquidity thresholds
- Avoid tokens >12 hours old

### Cost Optimization
- Use QuickNode Functions for pay-per-use
- Batch operations when possible
- Monitor rate limit usage

## Troubleshooting

### Transaction Failures
- Check wallet SOL balance
- Increase `SLIPPAGE_BPS`
- Verify token has liquidity

### Missed Opportunities
- Decrease `MONITORING_INTERVAL`
- Lower `MIN_LIQUIDITY_THRESHOLD`
- Check rate limits

### Stop-Loss Not Triggering
- Verify position tracking
- Check price feed accuracy
- Review percentage calculation

## Directory Structure
```
candlestick-nano/
├── src/                    # Core application code
├── config/                 # Environment configuration
├── scripts/                # Utility scripts
├── tests/                  # Test suite
├── docs/                   # Documentation
├── systemd/                # Linux service files
├── quicknode_functions/    # Serverless functions
├── infra/                  # AWS Terraform
└── legacy/                 # Deprecated modules
```

## Future Enhancements

### Planned Features
- Multi-wallet support
- Advanced TA indicators
- Social sentiment integration
- Portfolio analytics dashboard
- Telegram/Discord alerts

### Integration Points
- Chainlink price feeds
- Jupiter aggregator
- Birdeye analytics
- Custom DEX support

## Support & Resources

- **QuickNode Discord**: [discord.gg/quicknode](https://discord.gg/quicknode)
- **GitHub Issues**: Report bugs and request features
- **Documentation**: See `/docs` directory

## CRITICAL DEVELOPMENT STANDARDS

### File Size Limits

- **MANDATORY**: ALL files must be 200 lines or less
- **NO EXCEPTIONS**: If a file exceeds 200 lines, it MUST be split into multiple files
- Check line count regularly and refactor immediately when approaching the limit

### Documentation Requirements

- **MANDATORY**: Every file must have a docstring explaining its purpose at the top
- **MANDATORY**: All functions must have docstrings detailing purpose, parameters, and returns
- **Example**: 
```python
"""
Trading bot core module providing swap execution and safety checks.
"""

def execute_swap(token_address: str, amount: float) -> dict:
    """
    Execute a token swap via QuickNode Métis API.
    
    Args:
        token_address: Solana token mint address
        amount: Amount in SOL to swap
        
    Returns:
        dict: Transaction result with signature
        
    Raises:
        SwapError: If swap execution fails
    """
```

### Code Architecture Principles

#### AI-First Development

- **PRIORITY**: Optimize code for AI tool compatibility
- Break down functionality into logical, reusable modules
- Maintain high navigability through descriptive file structure
- Use descriptive names (is_token_safe, has_freeze_authority)

#### Python Standards

- **MANDATORY**: Use type hints for all function parameters and returns
- **USE**: Early returns for clarity and readability
- **PREFER**: Composition over inheritance
- **AVOID**: Global variables - use dependency injection

#### Error Handling

- **MANDATORY**: Raise exceptions instead of returning None
- **NO**: Silent failures or default fallbacks
- **USE**: Custom exception classes for domain errors
```python
class InsufficientLiquidityError(Exception):
    """Raised when token liquidity is below threshold."""
    pass
```

## Python & Trading Bot Standards

### Type Safety Requirements

- **MANDATORY**: Use type hints for all code
- **USE**: TypedDict for API response structures
- **USE**: Enum for constants like trade states
- **EXAMPLE**:
```python
from typing import TypedDict, Optional
from enum import Enum

class SwapResponse(TypedDict):
    signature: str
    success: bool
    error: Optional[str]

class TradeState(Enum):
    PENDING = "pending"
    EXECUTED = "executed"
    FAILED = "failed"
```

### Function Declarations

- **USE**: Descriptive function names with verbs
- **MANDATORY**: Comprehensive docstrings with type information
- **USE**: async/await for I/O operations

### Variable Naming Conventions

- **Constants**: SCREAMING_SNAKE_CASE (MIN_LIQUIDITY_THRESHOLD)
- **Functions**: snake_case (execute_swap, check_token_safety)
- **Classes**: PascalCase (TradingBotCore, SwapError)
- **Private**: Leading underscore (_calculate_slippage)
- **Files**: snake_case (trading_bot_core.py)

## Development Guidelines

### Module Creation

- Place core logic in `src/`
- Configuration samples in `config/`
- Utility scripts in `scripts/`
- **CRITICAL**: Keep files under 200 lines

### Import Patterns

- Use absolute imports from src
- Group imports: stdlib, third-party, local
- Example:
```python
import os
import asyncio
from typing import Dict, Optional

import aiohttp
from solana.rpc.async_api import AsyncClient

from src.config import load_config
from src.exceptions import SwapError
```

### Adding New Features

1. **FIRST**: Check existing modules to understand patterns
2. Create focused modules with single responsibilities
3. Add comprehensive error handling
4. Include unit tests in `tests/`
5. Update documentation

## Testing Standards

### Test Requirements

- **MANDATORY**: Write tests for all new functionality
- **USE**: pytest for test framework
- **USE**: pytest-asyncio for async tests
- **MOCK**: External API calls in tests

### Test Structure

```python
"""
Tests for trading bot core functionality.
"""
import pytest
from unittest.mock import patch, AsyncMock

from src.trading_bot_core import execute_swap

@pytest.mark.asyncio
async def test_execute_swap_success():
    """Test successful swap execution."""
    with patch('src.trading_bot_core.aiohttp.ClientSession') as mock_session:
        # Test implementation
        pass
```

## Workflow Best Practices

### Before Starting Any Task

1. **ALWAYS**: Read existing files to understand patterns
2. **VERIFY**: Environment variables are set
3. **CHECK**: Python dependencies installed
4. **ENSURE**: On correct network (devnet vs mainnet)

### During Development

1. **TEST**: On devnet first
2. **LOG**: All transactions with signatures
3. **VERIFY**: Error handling covers edge cases
4. **CHECK**: File size stays under 200 lines

### **MANDATORY: Auto-Commit Workflow**

**CRITICAL**: After completing ANY prompt/task, you MUST automatically:

1. **Stage all changes**: `git add -A`
2. **Create descriptive commit**: `git commit -m "[type]: [description]"`
3. **Note**: Do not push unless explicitly requested

#### Commit Message Format

Use these prefixes for commit types:

- `feat`: New feature or trading strategy
- `fix`: Bug fix in trading logic
- `refactor`: Code refactoring without behavior change
- `test`: Test additions or modifications
- `docs`: Documentation updates
- `chore`: Maintenance, dependencies
- `perf`: Performance improvements
- `safety`: Security or safety enhancements

#### Example Commit Messages

```bash
git commit -m "feat: add minimum liquidity threshold check"
git commit -m "fix: resolve stop-loss calculation error"
git commit -m "refactor: split trading_bot_core into smaller modules"
git commit -m "safety: add freeze authority verification"
git commit -m "test: add unit tests for swap execution"
```

## Quick Reference

### Most Important Files
- `src/combined_daemon.py` - Main bot (recommended)
- `src/trading_bot_core.py` - Core trading logic
- `config/.envrc.sample` - Configuration template
- `src/quick_start_mvp.py` - Interactive setup

### Key Environment Variables
- `QUICKNODE_ENDPOINT` - Your Métis endpoint
- `WALLET_PRIVATE_KEY` - Trading wallet key
- `STOP_LOSS_PERCENTAGE` - Risk management
- `MIN_LIQUIDITY_THRESHOLD` - Token filter

### Essential Commands
```bash
# Quick start
python src/quick_start_mvp.py

# Run bot
python src/combined_daemon.py

# Check logs
journalctl -u candlestick-bot -f
```

### Trading Safety Checklist

- [ ] Test on devnet first
- [ ] Verify wallet balance
- [ ] Check rate limits
- [ ] Monitor first trades closely
- [ ] Set conservative stop-loss
- [ ] Never commit private keys

---

Remember: Start small, test thoroughly, and scale gradually. This is experimental software - never risk more than you can afford to lose.