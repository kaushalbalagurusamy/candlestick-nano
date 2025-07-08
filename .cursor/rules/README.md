# Cursor Rules for Candlestick Nano Trading Bot

This directory contains comprehensive development rules specifically tailored for the Candlestick Nano AI-first trading bot project.

## Rule Files Overview

### Core Development Rules

#### `trading_bot_core.md`
- **Purpose**: Primary development guidelines for Python/FastAPI/async trading bot development
- **Focus**: Type safety, async patterns, trading safety protocols, performance optimization
- **Key Features**:
  - Mandatory 200-line file limit enforcement
  - Comprehensive error handling patterns
  - Trading-specific validation requirements
  - Pydantic models for data validation
  - Dependency injection patterns

#### `ml_ai_workflow.md`
- **Purpose**: Machine learning and AI development workflows for trading algorithms
- **Focus**: Real-time inference, feature engineering, model training pipelines
- **Key Features**:
  - Real-time ML model inference (<100ms latency)
  - Comprehensive feature extraction patterns
  - Model training and backtesting frameworks
  - Performance monitoring and model drift detection
  - MLOps best practices for trading systems

#### `trading_safety.md`
- **Purpose**: Critical safety and risk management protocols
- **Focus**: Financial safety, risk management, security best practices
- **Key Features**:
  - Pre-trade validation requirements (MANDATORY)
  - Comprehensive risk assessment frameworks
  - Circuit breaker patterns for system protection
  - Security protocols for private key management
  - Daily safety checklists

## Integration with Existing Architecture

These rules complement the existing architecture guidelines in the workspace:

```yaml
# Existing architecture rules (always applied):
- Files must not exceed 200 lines (MANDATORY)
- AI-first trading bot principles
- Modularity and dependency injection requirements
- Trading safety and documentation standards

# New Cursor rules enhance with:
- Detailed implementation patterns
- Comprehensive code examples
- Trading-specific best practices
- ML/AI development workflows
```

## How to Use These Rules

### For Development
1. **Cursor IDE** will automatically apply these rules when:
   - Writing new code
   - Refactoring existing modules
   - Implementing new features
   - Code review and suggestions

2. **Rule Priority**:
   - `trading_safety.md`: Highest priority - financial safety
   - `trading_bot_core.md`: Core development patterns
   - `ml_ai_workflow.md`: AI/ML specific implementations

### For Code Reviews
Use these rules as checklists:
- [ ] File under 200 lines
- [ ] All trading operations validated
- [ ] Async patterns used correctly
- [ ] Type hints on all functions
- [ ] Comprehensive error handling
- [ ] Trading safety protocols followed

## Rule Categories

### 🔒 Safety-Critical Rules
- Pre-trade validation (MANDATORY)
- Slippage protection
- Balance verification
- Risk limit enforcement
- Private key security

### ⚡ Performance Rules
- Async/await for all I/O
- Connection pooling
- Caching strategies
- Timeout handling
- Resource cleanup

### 🧠 AI/ML Rules
- Real-time inference patterns
- Feature engineering standards
- Model monitoring requirements
- Backtesting frameworks
- Performance optimization

### 📝 Code Quality Rules
- Type hints (mandatory)
- Google-style docstrings
- Comprehensive testing
- Error handling patterns
- Logging requirements

## Examples of Rule Application

### Trading Function Example
```python
async def execute_validated_trade(
    token_address: str,
    amount: Decimal,
    slippage_tolerance: float = 0.01
) -> TradeResult:
    """Execute trade with comprehensive validation.
    
    Applies rules from:
    - trading_safety.md: Pre-trade validation
    - trading_bot_core.md: Async patterns, type hints
    - ml_ai_workflow.md: Not applicable for execution
    """
    # Rule: Always validate before trading
    validation = await validate_trade_conditions(token_address, amount)
    if not validation.is_valid:
        raise TradingValidationError(validation.error_message)
    
    # Rule: Use timeout protection
    try:
        result = await asyncio.wait_for(
            _execute_swap(token_address, amount, slippage_tolerance),
            timeout=30.0
        )
        return result
    except asyncio.TimeoutError:
        raise TransactionTimeoutError("Trade execution timed out")
```

### ML Inference Example
```python
async def predict_entry_signal(
    market_data: MarketData,
    model: TradingModel
) -> ModelPrediction:
    """Generate entry signal prediction.
    
    Applies rules from:
    - ml_ai_workflow.md: Real-time inference patterns
    - trading_bot_core.md: Async patterns, error handling
    - trading_safety.md: Validation requirements
    """
    # Rule: Validate input features
    features = await extract_validated_features(market_data)
    
    # Rule: Real-time inference with timeout
    prediction = await asyncio.wait_for(
        model.predict(features),
        timeout=0.1  # 100ms max
    )
    
    # Rule: Log prediction for monitoring
    await log_ml_prediction(prediction, market_data)
    
    return prediction
```

## Maintenance and Updates

### When to Update Rules
- New trading requirements identified
- Performance optimizations needed
- Security vulnerabilities discovered
- ML/AI workflow improvements
- Architecture changes

### Update Process
1. Identify rule gaps or improvements
2. Update relevant rule file(s)
3. Test with existing codebase
4. Update examples and documentation
5. Commit changes with clear descriptions

## Compatibility

### Compatible With
- Python 3.10+
- FastAPI async patterns
- Pydantic v2 models
- pytest testing framework
- Docker devcontainer setup

### Rule Enforcement
- **Automatic**: Via Cursor IDE integration
- **Manual**: Code review checklists
- **CI/CD**: Linting and testing pipelines
- **Documentation**: Architecture decision records

## Quick Reference

| Need | Use Rule File |
|------|---------------|
| Trading execution | `trading_bot_core.md` + `trading_safety.md` |
| ML model development | `ml_ai_workflow.md` + `trading_bot_core.md` |
| Risk management | `trading_safety.md` |
| Performance optimization | `trading_bot_core.md` |
| New feature development | All three files |

These rules ensure consistent, safe, and high-performance development for the Candlestick Nano trading bot while maintaining the project's AI-first architecture principles. 