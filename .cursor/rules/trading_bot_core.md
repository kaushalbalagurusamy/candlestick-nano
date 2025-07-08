# Trading Bot Core Development Rules

You are an expert in **Python 3.10+**, **FastAPI**, **async programming**, **Solana blockchain development**, and **AI-first trading bot architecture**.

## Core Principles

### Code Organization & Architecture
- **MANDATORY**: Files must not exceed 200 lines - break into logical modules immediately
- Use **functional and declarative programming patterns**; avoid classes unless absolutely necessary
- Prefer **composition over inheritance** for trading strategy components
- Use descriptive variable names with auxiliary verbs (e.g., `is_profitable`, `has_liquidity`, `should_exit`)
- Follow **single responsibility principle** - each module has one trading concern

### File Naming & Structure
- Use lowercase with underscores: `trading_bot_core.py`, `entry_daemon.py`, `exit_utils.py`
- Directory structure:
  ```
  src/
  ├── trading_bot_core.py      # Central trading logic
  ├── entry_daemon.py          # Entry signal processing
  ├── exit_daemon.py           # Exit signal processing  
  ├── buy.py                   # Buy execution logic
  ├── exit_utils.py            # Exit utilities
  ├── config.py                # Configuration management
  └── dependencies.py          # Dependency injection
  ```

### Trading Safety Requirements
- **CRITICAL**: Always validate token addresses before operations
- **CRITICAL**: Check wallet balance before executing trades
- **CRITICAL**: Implement slippage protection on all swaps
- **CRITICAL**: Log all transaction attempts with full context
- **CRITICAL**: Use transaction simulation before execution
- **CRITICAL**: Never hardcode private keys - use environment variables only

## Python/FastAPI Best Practices

### Type Safety (MANDATORY)
```python
from typing import Dict, List, Optional, Union, Literal
from pydantic import BaseModel
from decimal import Decimal

async def execute_swap(
    token_address: str,
    amount: Decimal,
    slippage_tolerance: float = 0.01
) -> Dict[str, Union[str, bool, Decimal]]:
    """Execute token swap with comprehensive validation."""
```

### Async Programming Patterns
- Use `async def` for **ALL** I/O operations (RPC calls, API requests, file operations)
- Use `aiohttp` for HTTP requests to external APIs
- Implement proper timeout handling with `asyncio.wait_for()`
- Use connection pooling for persistent connections

```python
import aiohttp
import asyncio
from typing import Dict, Any

async def fetch_token_price(
    session: aiohttp.ClientSession,
    token_address: str,
    timeout: int = 10
) -> Optional[Decimal]:
    """Fetch current token price with timeout protection."""
    try:
        async with asyncio.wait_for(
            session.get(f"/price/{token_address}"),
            timeout=timeout
        ) as response:
            data = await response.json()
            return Decimal(str(data["price"]))
    except asyncio.TimeoutError:
        logger.warning(f"Price fetch timeout for {token_address}")
        return None
```

### Error Handling & Trading Safety
- Create **domain-specific exceptions** for trading scenarios
- **NEVER** use bare `except` clauses
- Always provide actionable error messages
- Implement circuit breakers for API failures

```python
class TradingError(Exception):
    """Base exception for trading operations."""

class InsufficientLiquidityError(TradingError):
    """Raised when token has insufficient liquidity for trade."""

class SlippageExceededError(TradingError):
    """Raised when actual slippage exceeds tolerance."""

class RPCConnectionError(TradingError):
    """Raised when RPC connection fails."""

async def validate_trade_conditions(
    token_address: str,
    amount: Decimal
) -> None:
    """Validate all conditions before executing trade."""
    if not await has_sufficient_liquidity(token_address, amount):
        raise InsufficientLiquidityError(
            f"Insufficient liquidity for {amount} of {token_address}"
        )
```

### Pydantic Models for Trading Data
```python
from pydantic import BaseModel, Field, validator
from decimal import Decimal
from typing import Literal

class TradeSignal(BaseModel):
    """Validated trade signal from analysis."""
    token_address: str = Field(..., min_length=32, max_length=44)
    signal_type: Literal["BUY", "SELL"] = Field(...)
    confidence: float = Field(..., ge=0.0, le=1.0)
    target_amount: Decimal = Field(..., gt=0)
    max_slippage: float = Field(default=0.01, ge=0.0, le=0.1)
    
    @validator("token_address")
    def validate_token_address(cls, v):
        """Ensure token address is valid Solana format."""
        if not is_valid_solana_address(v):
            raise ValueError("Invalid Solana token address")
        return v

class TradeResult(BaseModel):
    """Result of executed trade."""
    success: bool
    transaction_signature: Optional[str] = None
    actual_amount: Optional[Decimal] = None
    actual_slippage: Optional[float] = None
    error_message: Optional[str] = None
    execution_time: float
```

### Dependency Injection Pattern
```python
from typing import Protocol

class TokenPriceProvider(Protocol):
    """Protocol for token price data providers."""
    async def get_price(self, token_address: str) -> Optional[Decimal]: ...

class QuickNodePriceProvider:
    """QuickNode Metis API price provider."""
    def __init__(self, api_key: str, rate_limit: int = 10):
        self.api_key = api_key
        self.rate_limit = rate_limit
    
    async def get_price(self, token_address: str) -> Optional[Decimal]:
        # Implementation with rate limiting
        pass

# Dependency injection in trading core
async def analyze_entry_opportunity(
    token_address: str,
    price_provider: TokenPriceProvider,
    liquidity_provider: LiquidityProvider
) -> Optional[TradeSignal]:
    """Analyze entry opportunity using injected dependencies."""
```

### Performance Optimization
- **Cache frequently accessed data** (token metadata, price history)
- **Batch RPC requests** where possible using Solana's batch RPC
- **Use connection pooling** for HTTP clients
- **Implement proper resource cleanup** in finally blocks

```python
from functools import lru_cache
import asyncio

@lru_cache(maxsize=1000)
def get_token_metadata(token_address: str) -> Dict[str, Any]:
    """Cache token metadata to reduce API calls."""
    return fetch_token_metadata_sync(token_address)

async def batch_rpc_requests(requests: List[Dict[str, Any]]) -> List[Any]:
    """Batch multiple RPC requests for efficiency."""
    async with aiohttp.ClientSession() as session:
        tasks = [send_rpc_request(session, req) for req in requests]
        return await asyncio.gather(*tasks, return_exceptions=True)
```

### Logging & Monitoring
- **Log ALL trading decisions** with full context
- **Track performance metrics** (latency, success rates)
- **Maintain audit trail** of all transactions
- **Use structured logging** with JSON format

```python
import logging
import json
from datetime import datetime

# Configure structured logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def log_trade_attempt(
    token_address: str,
    signal: TradeSignal,
    wallet_balance: Decimal
) -> None:
    """Log trade attempt with full context."""
    log_data = {
        "event": "trade_attempt",
        "timestamp": datetime.utcnow().isoformat(),
        "token_address": token_address,
        "signal_type": signal.signal_type,
        "confidence": float(signal.confidence),
        "target_amount": float(signal.target_amount),
        "wallet_balance": float(wallet_balance)
    }
    logging.info(json.dumps(log_data))
```

### Testing Requirements
- **Unit tests** for all trading logic with mocked dependencies
- **Integration tests** with recorded API responses
- **Minimum 90% test coverage** for core trading modules
- **Property-based testing** for mathematical calculations

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal

@pytest.mark.asyncio
async def test_execute_swap_success():
    """Test successful swap execution."""
    # Mock dependencies
    mock_rpc = AsyncMock()
    mock_rpc.send_transaction.return_value = "mock_signature"
    
    # Test execution
    result = await execute_swap(
        token_address="So11111111111111111111111111111112",
        amount=Decimal("1.0"),
        rpc_client=mock_rpc
    )
    
    assert result.success is True
    assert result.transaction_signature == "mock_signature"
    mock_rpc.send_transaction.assert_called_once()
```

## Documentation Requirements
- **Google-style docstrings** for ALL functions
- **Document trading risks** and safety considerations
- **Include usage examples** in docstrings
- **Maintain AGENTS.md** with architecture decisions

```python
async def calculate_position_size(
    account_balance: Decimal,
    risk_percentage: float,
    entry_price: Decimal,
    stop_loss_price: Decimal
) -> Decimal:
    """Calculate position size based on risk management rules.
    
    Args:
        account_balance: Total account balance in SOL
        risk_percentage: Percentage of account to risk (0.0-1.0)
        entry_price: Price at which to enter position
        stop_loss_price: Price at which to exit with loss
        
    Returns:
        Position size in tokens to purchase
        
    Raises:
        ValueError: If risk parameters are invalid
        
    Example:
        >>> balance = Decimal("10.0")  # 10 SOL
        >>> risk = 0.02  # 2% risk
        >>> entry = Decimal("0.1")
        >>> stop = Decimal("0.09")
        >>> size = await calculate_position_size(balance, risk, entry, stop)
        >>> assert size == Decimal("2.0")  # 2 tokens
    """
```

## Module Size Enforcement
- **NEVER exceed 200 lines per file**
- Break large modules into logical components:
  - `entry_signals.py` - Entry signal detection
  - `exit_conditions.py` - Exit condition evaluation  
  - `risk_management.py` - Position sizing and risk controls
  - `transaction_executor.py` - Transaction execution logic 