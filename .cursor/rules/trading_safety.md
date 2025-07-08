# Trading Safety & Risk Management Rules

You are an expert in **trading risk management**, **financial safety protocols**, **blockchain security**, and **automated trading system protection**.

## CRITICAL SAFETY REQUIREMENTS

### Pre-Trade Validation (MANDATORY)
Every trade MUST pass ALL validation checks before execution:

```python
from decimal import Decimal
from typing import Optional, Dict, Any
import logging

class TradingValidator:
    """Comprehensive trading validation before execution."""
    
    def __init__(
        self,
        max_position_size: Decimal,
        max_daily_loss: Decimal,
        min_liquidity_threshold: Decimal
    ):
        self.max_position_size = max_position_size
        self.max_daily_loss = max_daily_loss
        self.min_liquidity_threshold = min_liquidity_threshold
    
    async def validate_trade(
        self,
        token_address: str,
        trade_amount: Decimal,
        account_balance: Decimal,
        daily_pnl: Decimal
    ) -> TradingValidationResult:
        """Validate trade before execution - ALL checks must pass.
        
        CRITICAL: This function prevents financial loss through validation.
        Never bypass these checks in production.
        """
        validation_result = TradingValidationResult()
        
        # 1. CRITICAL: Validate token address format
        if not await self._validate_token_address(token_address):
            validation_result.add_error("INVALID_TOKEN_ADDRESS", "Token address format invalid")
            return validation_result
        
        # 2. CRITICAL: Check sufficient account balance
        if trade_amount > account_balance * Decimal("0.95"):  # Keep 5% buffer
            validation_result.add_error(
                "INSUFFICIENT_BALANCE",
                f"Trade amount {trade_amount} exceeds available balance {account_balance}"
            )
        
        # 3. CRITICAL: Position size limits
        if trade_amount > self.max_position_size:
            validation_result.add_error(
                "POSITION_TOO_LARGE",
                f"Trade amount {trade_amount} exceeds max position size {self.max_position_size}"
            )
        
        # 4. CRITICAL: Daily loss limits
        projected_loss = daily_pnl - trade_amount  # Worst case scenario
        if projected_loss < -self.max_daily_loss:
            validation_result.add_error(
                "DAILY_LOSS_LIMIT",
                f"Potential daily loss {projected_loss} exceeds limit {self.max_daily_loss}"
            )
        
        # 5. CRITICAL: Liquidity validation
        liquidity = await self._check_token_liquidity(token_address)
        if liquidity < self.min_liquidity_threshold:
            validation_result.add_error(
                "INSUFFICIENT_LIQUIDITY",
                f"Token liquidity {liquidity} below threshold {self.min_liquidity_threshold}"
            )
        
        # 6. CRITICAL: Market hours validation (if applicable)
        if not await self._is_market_open():
            validation_result.add_error(
                "MARKET_CLOSED",
                "Trading not allowed during market closure"
            )
        
        # 7. CRITICAL: Rate limiting validation
        if not await self._check_rate_limits():
            validation_result.add_error(
                "RATE_LIMIT_EXCEEDED",
                "API rate limit exceeded, trade rejected"
            )
        
        return validation_result
    
    async def _validate_token_address(self, token_address: str) -> bool:
        """Validate Solana token address format."""
        if not token_address or len(token_address) < 32:
            return False
        
        # Add comprehensive Solana address validation
        try:
            # Implement proper base58 validation here
            return await validate_solana_address(token_address)
        except Exception:
            return False
    
    async def _check_token_liquidity(self, token_address: str) -> Decimal:
        """Check token liquidity on DEX."""
        try:
            # Implement actual liquidity check via DEX API
            return await get_token_liquidity(token_address)
        except Exception as e:
            logging.error(f"Liquidity check failed for {token_address}: {e}")
            return Decimal("0")  # Fail safe - no liquidity
```

### Transaction Safety Patterns
```python
class SafeTransactionExecutor:
    """Execute transactions with comprehensive safety checks."""
    
    async def execute_swap_with_safety(
        self,
        token_in: str,
        token_out: str,
        amount: Decimal,
        max_slippage: float = 0.01
    ) -> TransactionResult:
        """Execute swap with full safety protocol.
        
        SAFETY PROTOCOL:
        1. Simulate transaction first
        2. Check slippage limits
        3. Verify sufficient balance
        4. Execute with timeout
        5. Verify transaction success
        6. Log complete audit trail
        """
        
        # Step 1: Transaction simulation (MANDATORY)
        simulation_result = await self._simulate_transaction(
            token_in, token_out, amount, max_slippage
        )
        
        if not simulation_result.success:
            raise TransactionSimulationError(
                f"Transaction simulation failed: {simulation_result.error}"
            )
        
        # Step 2: Final balance verification
        current_balance = await self._get_wallet_balance(token_in)
        if current_balance < amount:
            raise InsufficientBalanceError(
                f"Balance {current_balance} insufficient for amount {amount}"
            )
        
        # Step 3: Slippage protection
        expected_output = simulation_result.expected_output
        min_output = expected_output * (1 - max_slippage)
        
        try:
            # Step 4: Execute with timeout protection
            transaction_signature = await asyncio.wait_for(
                self._execute_swap_transaction(
                    token_in, token_out, amount, min_output
                ),
                timeout=30.0  # 30 second timeout
            )
            
            # Step 5: Verify transaction confirmation
            confirmation = await self._wait_for_confirmation(
                transaction_signature,
                max_wait_time=60
            )
            
            if not confirmation.success:
                raise TransactionConfirmationError(
                    f"Transaction {transaction_signature} failed confirmation"
                )
            
            # Step 6: Audit logging
            await self._log_transaction_audit(
                transaction_signature,
                token_in,
                token_out, 
                amount,
                confirmation.actual_output,
                simulation_result
            )
            
            return TransactionResult(
                success=True,
                transaction_signature=transaction_signature,
                actual_output=confirmation.actual_output,
                slippage=float(
                    (expected_output - confirmation.actual_output) / expected_output
                )
            )
            
        except asyncio.TimeoutError:
            raise TransactionTimeoutError("Transaction execution timed out")
        except Exception as e:
            # Log error with full context
            logging.error(
                f"Transaction execution failed: {e}",
                extra={
                    "token_in": token_in,
                    "token_out": token_out,
                    "amount": float(amount),
                    "max_slippage": max_slippage
                }
            )
            raise TransactionExecutionError(f"Transaction failed: {e}")
```

### Risk Management Framework
```python
from enum import Enum
from dataclasses import dataclass
from typing import List

class RiskLevel(Enum):
    """Risk level classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class RiskAssessment:
    """Comprehensive risk assessment result."""
    overall_risk: RiskLevel
    risk_factors: List[str]
    risk_score: float  # 0.0 to 1.0
    recommended_position_size: Decimal
    stop_loss_price: Optional[Decimal]
    take_profit_price: Optional[Decimal]

class RiskManager:
    """Comprehensive trading risk management."""
    
    def __init__(
        self,
        max_portfolio_risk: float = 0.02,  # 2% of portfolio per trade
        max_daily_drawdown: float = 0.05,  # 5% daily drawdown limit
        volatility_threshold: float = 0.15  # 15% volatility threshold
    ):
        self.max_portfolio_risk = max_portfolio_risk
        self.max_daily_drawdown = max_daily_drawdown
        self.volatility_threshold = volatility_threshold
    
    async def assess_trade_risk(
        self,
        token_address: str,
        current_price: Decimal,
        portfolio_value: Decimal,
        position_size: Decimal
    ) -> RiskAssessment:
        """Assess comprehensive trading risk before execution."""
        
        risk_factors = []
        risk_score = 0.0
        
        # 1. Volatility risk assessment
        volatility = await self._calculate_token_volatility(token_address)
        if volatility > self.volatility_threshold:
            risk_factors.append(f"High volatility: {volatility:.2%}")
            risk_score += 0.3
        
        # 2. Liquidity risk assessment
        liquidity_ratio = await self._assess_liquidity_risk(token_address, position_size)
        if liquidity_ratio < 0.1:  # Less than 10% of available liquidity
            risk_factors.append("Low liquidity risk")
            risk_score += 0.2
        elif liquidity_ratio > 0.5:  # More than 50% of available liquidity
            risk_factors.append("High market impact risk")
            risk_score += 0.4
        
        # 3. Portfolio concentration risk
        position_percentage = (position_size * current_price) / portfolio_value
        if position_percentage > self.max_portfolio_risk:
            risk_factors.append(f"Oversized position: {position_percentage:.2%}")
            risk_score += 0.3
        
        # 4. Market condition risk
        market_sentiment = await self._assess_market_sentiment()
        if market_sentiment < -0.5:  # Bearish market
            risk_factors.append("Bearish market conditions")
            risk_score += 0.2
        
        # 5. Historical performance risk
        historical_performance = await self._get_token_performance_history(token_address)
        if historical_performance['max_drawdown'] > 0.5:  # 50% historical drawdown
            risk_factors.append("High historical drawdown risk")
            risk_score += 0.25
        
        # Determine overall risk level
        if risk_score >= 0.8:
            overall_risk = RiskLevel.CRITICAL
        elif risk_score >= 0.6:
            overall_risk = RiskLevel.HIGH
        elif risk_score >= 0.3:
            overall_risk = RiskLevel.MEDIUM
        else:
            overall_risk = RiskLevel.LOW
        
        # Calculate recommended position size based on risk
        risk_adjusted_position = self._calculate_risk_adjusted_position(
            portfolio_value, risk_score, position_size
        )
        
        # Calculate stop loss and take profit
        stop_loss = current_price * Decimal("0.95")  # 5% stop loss
        take_profit = current_price * Decimal("1.15")  # 15% take profit
        
        return RiskAssessment(
            overall_risk=overall_risk,
            risk_factors=risk_factors,
            risk_score=risk_score,
            recommended_position_size=risk_adjusted_position,
            stop_loss_price=stop_loss,
            take_profit_price=take_profit
        )
    
    def _calculate_risk_adjusted_position(
        self,
        portfolio_value: Decimal,
        risk_score: float,
        requested_position: Decimal
    ) -> Decimal:
        """Calculate position size adjusted for risk."""
        max_position = portfolio_value * Decimal(str(self.max_portfolio_risk))
        
        # Reduce position size based on risk score
        risk_multiplier = Decimal(str(1.0 - risk_score))
        adjusted_position = min(
            requested_position,
            max_position * risk_multiplier
        )
        
        return adjusted_position
```

### Security Best Practices
```python
import os
from cryptography.fernet import Fernet
from pathlib import Path

class SecurityManager:
    """Manage security aspects of trading bot."""
    
    @staticmethod
    def validate_environment_security() -> List[str]:
        """Validate trading bot security configuration."""
        security_issues = []
        
        # 1. Check for hardcoded secrets
        if not os.getenv('PRIVATE_KEY_ENCRYPTED'):
            security_issues.append("CRITICAL: Private key not properly encrypted")
        
        # 2. Validate file permissions
        config_files = ['.env', 'config/trading_config.yaml']
        for config_file in config_files:
            if Path(config_file).exists():
                file_stat = Path(config_file).stat()
                if oct(file_stat.st_mode)[-3:] != '600':
                    security_issues.append(f"WARNING: {config_file} has insecure permissions")
        
        # 3. Check for proper API key management
        api_keys = ['QUICKNODE_API_KEY', 'SOLANA_RPC_URL']
        for key in api_keys:
            if not os.getenv(key):
                security_issues.append(f"WARNING: {key} not configured")
        
        # 4. Validate network security
        rpc_url = os.getenv('SOLANA_RPC_URL', '')
        if not rpc_url.startswith('https://'):
            security_issues.append("CRITICAL: RPC URL not using HTTPS")
        
        return security_issues
    
    @staticmethod
    def encrypt_sensitive_data(data: str, key: bytes) -> bytes:
        """Encrypt sensitive trading data."""
        f = Fernet(key)
        return f.encrypt(data.encode())
    
    @staticmethod
    def decrypt_sensitive_data(encrypted_data: bytes, key: bytes) -> str:
        """Decrypt sensitive trading data."""
        f = Fernet(key)
        return f.decrypt(encrypted_data).decode()
```

### Circuit Breaker Pattern
```python
from datetime import datetime, timedelta
from typing import Dict, Optional

class TradingCircuitBreaker:
    """Implement circuit breaker for trading operations."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 300,  # 5 minutes
        success_threshold: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.success_count = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def execute_with_circuit_breaker(
        self,
        operation_name: str,
        operation_func,
        *args,
        **kwargs
    ):
        """Execute operation with circuit breaker protection."""
        
        if self.state == "OPEN":
            if await self._should_attempt_reset():
                self.state = "HALF_OPEN"
                logging.info(f"Circuit breaker HALF_OPEN for {operation_name}")
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker OPEN for {operation_name}"
                )
        
        try:
            result = await operation_func(*args, **kwargs)
            await self._on_success(operation_name)
            return result
            
        except Exception as e:
            await self._on_failure(operation_name, e)
            raise
    
    async def _on_success(self, operation_name: str):
        """Handle successful operation."""
        if self.state == "HALF_OPEN":
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = "CLOSED"
                self.failure_count = 0
                self.success_count = 0
                logging.info(f"Circuit breaker CLOSED for {operation_name}")
        else:
            self.failure_count = 0
    
    async def _on_failure(self, operation_name: str, error: Exception):
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        self.success_count = 0
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logging.error(
                f"Circuit breaker OPEN for {operation_name} after {self.failure_count} failures"
            )
    
    async def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset."""
        if self.last_failure_time is None:
            return True
            
        time_since_failure = datetime.utcnow() - self.last_failure_time
        return time_since_failure.total_seconds() >= self.recovery_timeout
```

## Trading Safety Exceptions
```python
class TradingSafetyError(Exception):
    """Base exception for trading safety violations."""

class TradingValidationError(TradingSafetyError):
    """Raised when trade validation fails."""

class InsufficientBalanceError(TradingSafetyError):
    """Raised when wallet balance is insufficient."""

class SlippageExceededError(TradingSafetyError):
    """Raised when slippage exceeds tolerance."""

class TransactionSimulationError(TradingSafetyError):
    """Raised when transaction simulation fails."""

class TransactionTimeoutError(TradingSafetyError):
    """Raised when transaction times out."""

class CircuitBreakerOpenError(TradingSafetyError):
    """Raised when circuit breaker is open."""

class RiskLimitExceededError(TradingSafetyError):
    """Raised when risk limits are exceeded."""
```

## Daily Safety Checklist
Before starting trading operations, verify:

1. **Environment Security**
   - [ ] Private keys encrypted and not hardcoded
   - [ ] API keys properly configured
   - [ ] File permissions set correctly (600)
   - [ ] HTTPS connections only

2. **Risk Management**
   - [ ] Daily loss limits configured
   - [ ] Position size limits active
   - [ ] Stop-loss mechanisms enabled
   - [ ] Portfolio risk assessment current

3. **System Health**
   - [ ] All APIs responding correctly
   - [ ] Circuit breakers reset and functional
   - [ ] Logging systems operational
   - [ ] Backup systems ready

4. **Market Conditions**
   - [ ] Market hours validated
   - [ ] Liquidity conditions acceptable
   - [ ] Volatility within acceptable ranges
   - [ ] No major news events pending

**REMEMBER: When in doubt, DO NOT TRADE. Protecting capital is the first priority.** 