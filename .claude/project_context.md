# Candlestick Nano Trading Bot - Project Context

## Project Overview
**Candlestick Nano** is an AI-first automated trading bot for Solana blockchain tokens. The system uses machine learning models to detect profitable trading opportunities through real-time market analysis and executes trades automatically with comprehensive risk management.

## Core Architecture

### Technology Stack
- **Language**: Python 3.10+
- **Blockchain**: Solana (devnet/mainnet)
- **APIs**: QuickNode Metis, Solana RPC
- **ML Framework**: scikit-learn, custom feature engineering
- **Async Framework**: asyncio, aiohttp
- **Data Validation**: Pydantic v2
- **Testing**: pytest with async support
- **Containerization**: Docker with devcontainer support

### Directory Structure
```
candlestick-nano/
├── src/                          # Core trading logic (200 lines max per file)
│   ├── trading_bot_core.py       # Central trading coordinator
│   ├── entry_daemon.py           # Entry signal processing
│   ├── exit_daemon.py            # Exit signal management
│   ├── buy.py                    # Buy execution logic
│   ├── exit_utils.py             # Exit utilities and calculations
│   ├── combined_daemon.py        # Unified daemon for production
│   ├── config.py                 # Configuration management
│   └── dependencies.py           # Dependency injection container
├── tests/                        # Comprehensive test suite (97.6% passing)
├── config/                       # Configuration files
├── logs/                         # Trading operation logs
├── .devcontainer/               # Development container config
├── .cursor/rules/               # Cursor IDE development rules
└── .claude/                     # Claude AI project context
```

## Key Business Logic

### Trading Flow
1. **Market Monitoring**: Continuous monitoring of Solana token markets
2. **Signal Generation**: ML models analyze market data for entry/exit signals
3. **Risk Assessment**: Comprehensive risk evaluation before trade execution
4. **Trade Execution**: Automated swap execution with slippage protection
5. **Position Management**: Active monitoring and exit condition evaluation
6. **Performance Tracking**: Real-time PnL tracking and performance metrics

### Core Modules

#### `trading_bot_core.py`
- Central coordinator for all trading operations
- Integrates entry/exit daemons with execution logic
- Manages overall system state and health monitoring

#### `entry_daemon.py`
- Monitors market conditions for entry opportunities
- Filters tokens based on age, liquidity, and technical criteria
- Generates buy signals with confidence scores

#### `exit_daemon.py`
- Manages active positions and exit conditions
- Implements stop-loss and take-profit logic
- Handles emergency exit scenarios

#### `buy.py`
- Executes token purchase transactions
- Implements slippage protection and transaction validation
- Handles swap routing and execution confirmation

#### `exit_utils.py`
- Utility functions for exit condition evaluation
- Stop-loss calculation and profit-taking logic
- Position sizing and risk management calculations

## AI/ML Components

### Signal Processing
- **Entry Signals**: ML models analyze price patterns, volume, and market sentiment
- **Exit Signals**: Predictive models for optimal exit timing
- **Risk Assessment**: AI-powered risk scoring for position sizing

### Feature Engineering
- Price-based technical indicators (RSI, moving averages, momentum)
- Volume analysis and liquidity metrics
- Market sentiment and social signals
- Cross-token correlation analysis

### Model Architecture
- Real-time inference with <100ms latency requirements
- Stateless design for scalability
- Continuous learning from trading outcomes
- A/B testing framework for model comparison

## Risk Management Framework

### Safety Protocols
- **Pre-trade Validation**: All trades must pass comprehensive validation
- **Position Limits**: Maximum 2% of portfolio per trade
- **Daily Loss Limits**: 5% maximum daily drawdown
- **Slippage Protection**: Configurable slippage tolerance (default 1%)
- **Liquidity Checks**: Minimum liquidity thresholds before trading

### Circuit Breakers
- API failure protection with exponential backoff
- Trading halt on consecutive losses
- System health monitoring with automated recovery

### Security Measures
- Encrypted private key storage
- Environment variable configuration
- HTTPS-only API connections
- Comprehensive audit logging

## Development Guidelines

### Code Standards
- **File Size Limit**: 200 lines maximum per file (MANDATORY)
- **Type Safety**: Full type hints on all functions
- **Async First**: All I/O operations use async/await
- **Error Handling**: Domain-specific exceptions with detailed context
- **Documentation**: Google-style docstrings with examples

### Testing Requirements
- 97.6% test coverage achieved (123/126 tests passing)
- Unit tests with mocked dependencies
- Integration tests with recorded API responses
- End-to-end devnet testing before mainnet deployment

### Performance Targets
- **Trade Execution**: <5 seconds from signal to confirmation
- **API Response**: <500ms for market data queries
- **ML Inference**: <100ms for signal generation
- **System Uptime**: 99.9% availability target

## Configuration Management

### Environment Variables
```bash
# Blockchain Configuration
SOLANA_CLUSTER=devnet|mainnet
SOLANA_RPC_URL=https://...
PRIVATE_KEY_ENCRYPTED=...

# API Configuration
QUICKNODE_API_KEY=...
QUICKNODE_ENDPOINT=...

# Trading Parameters
MAX_POSITION_SIZE=1000
MAX_DAILY_LOSS=500
DEFAULT_SLIPPAGE=0.01

# Risk Management
STOP_LOSS_PERCENTAGE=0.05
TAKE_PROFIT_PERCENTAGE=0.15
MAX_TRADE_FREQUENCY=10
```

### Configuration Files
- `config/api_contract.yaml`: API specification and validation rules
- `config/faucet_state.json`: Devnet faucet management
- `pyproject.toml`: Python dependencies and project metadata
- `pytest.ini`: Test configuration and markers

## Deployment Architecture

### Development Environment
- Docker devcontainer with full development stack
- Automated testing on every commit
- Devnet integration for safe testing

### Production Environment
- Systemd service management
- Docker containerization for isolation
- Automated log rotation and monitoring
- Health check endpoints for monitoring

### Infrastructure
- AWS/cloud deployment ready
- Terraform infrastructure as code
- Lambda functions for QuickNode integration
- Centralized logging and monitoring

## Current Status

### Test Suite Health
- **Total Tests**: 126
- **Passing**: 123 (97.6%)
- **Failing**: 3 (environment/API related, not business logic)
- **Core Modules**: 100% working (all business logic tests pass)

### Recent Achievements
- Fixed all base58 encoding issues
- Resolved stop-loss calculation bugs
- Improved async mocking in tests
- Optimized entry daemon age filtering
- Enhanced performance test reliability

### Known Issues
- 3 integration API tests failing (environment dependent)
- Some rate limiting edge cases in high-volume scenarios
- Documentation needs updates for latest architecture changes

## Development Workflow

### Local Development
1. Start devcontainer: `cursor devcontainer up`
2. Install dependencies: `pip install -r requirements-dev.txt`
3. Run tests: `python scripts/run_tests.py`
4. Start development server: `python src/quick_start_mvp.py`

### Testing Strategy
1. Unit tests for business logic
2. Integration tests with mocked APIs
3. End-to-end tests on devnet
4. Performance benchmarking
5. Security validation

### Deployment Process
1. Full test suite validation
2. Devnet deployment and testing
3. Performance monitoring
4. Gradual mainnet rollout
5. Real-time monitoring and alerting

## Key Metrics to Monitor

### Trading Performance
- Total return and Sharpe ratio
- Win rate and average trade duration
- Maximum drawdown and risk-adjusted returns
- Transaction success rate and slippage

### System Performance
- API response times and error rates
- ML model accuracy and inference time
- System uptime and error recovery
- Resource utilization and scaling needs

### Risk Metrics
- Daily/weekly PnL and drawdown
- Position concentration and exposure
- Correlation with market movements
- Stress testing results

## Integration Points

### External APIs
- **QuickNode Metis**: Market data and token analysis
- **Solana RPC**: Blockchain interaction and transaction execution
- **DEX APIs**: Liquidity and pricing data
- **Social APIs**: Sentiment analysis (future enhancement)

### Internal Components
- Configuration management system
- Logging and monitoring infrastructure
- Alert and notification system
- Performance analytics dashboard

This context provides Claude AI with comprehensive understanding of the trading bot's architecture, business logic, and development requirements for effective assistance. 