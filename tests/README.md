# Candlestick Nano Test Suite

Comprehensive testing framework for the Candlestick Nano Solana trading bot with advanced dependency injection and architecture integration.

## Test Categories

### 🧪 Unit Tests
Fast, isolated tests for individual components:
- `test_trading_bot_core.py` - Core trading functionality
- `test_combined_daemon.py` - Combined daemon operations  
- `test_entry_daemon.py` - Entry daemon logic
- `test_exit_daemon.py` - Exit daemon logic
- `test_exit_utils.py` - Exit utility functions
- `test_buy.py` - Buy module functions
- `test_dependency_injection.py` - Dependency injection system tests

### 🔗 Integration Tests
Tests with real API endpoints (requires environment setup):
- `test_integration_api.py` - QuickNode and Jupiter API integration
- `test_integration_wallet.py` - Wallet operations and transactions
- `test_metis_integration.py` - QuickNode Métis API integration

### 🏗️ Architecture Tests
Tests for improved architecture and dependency injection:
- `test_architecture_integration.py` - Integration between existing code and new DI system
- `test_config.py` - Configuration management and lazy loading tests

### 🎯 End-to-End Tests
Complete workflow tests (devnet only):
- `test_e2e_trading_flow.py` - Complete trading workflows
- `test_end_to_end_devnet.py` - Real devnet trading scenarios

### ⚡ Performance Tests
Load and performance testing:
- `test_performance.py` - Performance benchmarks and scalability

### 🔧 Environment Tests
Configuration and setup validation:
- `test_env.py` - Environment variables and connectivity

## Recent Improvements (2024)

### ✅ Resolved Import-Time Dependencies
- **Issue**: Modules failed to import without environment variables
- **Solution**: Implemented lazy configuration loading with defaults
- **Impact**: All tests can now run in clean environments without crashes

### ✅ Enhanced Architecture with Dependency Injection
- **New Features**:
  - `Dependencies` container for clean testability
  - `ConfigProtocol`, `ClientProtocol`, `HTTPClientProtocol` for type safety
  - Lazy dependency resolution with automatic fallbacks
- **Benefits**:
  - Easy mocking and testing isolation
  - Better separation of concerns
  - Backward compatibility with existing code

### ✅ Fixed Critical Test Issues
- **Async Context Managers**: Fixed AsyncClient mocking in entry/exit daemons
- **Keypair Validation**: Proper base58 decoding mocks to avoid validation errors
- **Transaction Signing**: Fixed bytes() conversion issues in transaction tests
- **Timestamp Logic**: Corrected age-based filtering tests

### ✅ Performance Optimizations
- **Dependency Injection Overhead**: < 50% increase vs direct calls
- **Test Execution Speed**: Unit tests run in < 1 second each
- **Memory Management**: < 100MB growth during extensive processing

## Quick Start

### Using the Test Runner Script

```bash
# Run unit tests (fastest)
python scripts/run_tests.py unit

# Run with verbose output  
python scripts/run_tests.py unit -v

# Run architecture tests (new)
python scripts/run_tests.py --test-file test_architecture_integration.py

# Run dependency injection tests
python scripts/run_tests.py --test-file test_dependency_injection.py

# Run all tests
python scripts/run_tests.py all

# Run specific test file
python scripts/run_tests.py --test-file test_trading_bot_core.py

# Run specific test function
python scripts/run_tests.py --test-file test_trading_bot_core.py --test-name test_get_quote_success
```

### Using pytest directly

```bash
# Unit tests only
pytest tests/test_trading_bot_core.py tests/test_combined_daemon.py -v

# Architecture integration tests
pytest tests/test_architecture_integration.py -v

# Integration tests (requires environment)
RUN_INTEGRATION_TESTS=1 pytest tests/test_integration_api.py -v

# All tests except slow ones
pytest tests/ -m "not slow" -v
```

## Environment Setup

### For Unit Tests
No special setup required - uses mocked dependencies and lazy loading.

### For Integration Tests
Set environment variable:
```bash
export RUN_INTEGRATION_TESTS=1
```

Required environment variables:
- `QUICKNODE_ENDPOINT` - Your QuickNode RPC URL
- `JUPITER_API_BASE_URL` - Jupiter API URL (usually https://quote-api.jup.ag/v6)
- `WALLET_ADDRESS` - Your wallet public key
- `WALLET_PRIVATE_KEY` - Your wallet private key (base58 encoded)

### For End-to-End Tests
Additional requirements:
```bash
export SOLANA_CLUSTER=devnet
export RUN_SLOW_TESTS=1
```

### Complete Environment Setup
```bash
# Copy and configure environment
cp config/.envrc.sample config/.envrc
# Edit config/.envrc with your values

# Load environment (if using direnv)
direnv allow

# Or source manually
source config/.envrc
```

## Dependency Injection Usage

### Basic Usage
```python
from dependencies import configure_deps, get_deps
from unittest.mock import Mock, AsyncMock

# Configure mock dependencies for testing
mock_config = Mock()
mock_config.quicknode_endpoint = "https://test.com"

mock_trading_client = AsyncMock()
mock_trading_client.get_quote.return_value = {"outAmount": "1000000"}

configure_deps(
    config_override=mock_config,
    trading_client=mock_trading_client
)

# Use in tests
deps = get_deps()
result = await deps.trading_client.get_quote("mint1", "mint2", 1000000, 100)
```

### Testing with Real Configuration
```python
# Uses environment variables
from dependencies import get_deps

deps = get_deps()  # Auto-creates TradingBotCore with real config
balance = await deps.trading_client.get_balance()
```

### Mixed Architecture Support
```python
# Legacy code continues to work
from config import config
endpoint = config.quicknode_endpoint

# New code can use dependency injection
from dependencies import get_deps
deps = get_deps()
client = deps.trading_client
```

## Test Categories and Markers

Tests are organized using pytest markers:

- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.performance` - Performance tests
- `@pytest.mark.slow` - Slow-running tests

## Running Different Test Categories

### Unit Tests Only (Fast)
```bash
python scripts/run_tests.py unit
# or
pytest tests/ -m "not integration and not e2e and not performance"
```

### Integration Tests
```bash
python scripts/run_tests.py integration
# or  
RUN_INTEGRATION_TESTS=1 pytest tests/ -m integration
```

### Architecture Tests
```bash
# Test dependency injection system
pytest tests/test_dependency_injection.py -v

# Test architecture integration
pytest tests/test_architecture_integration.py -v

# Test configuration management
pytest tests/test_config.py -v
```

### End-to-End Tests
```bash
python scripts/run_tests.py e2e
# or
RUN_SLOW_TESTS=1 pytest tests/ -m e2e
```

### Performance Tests
```bash
python scripts/run_tests.py performance
# or
RUN_PERFORMANCE_TESTS=1 pytest tests/ -m performance  
```

### All Tests
```bash
python scripts/run_tests.py all
# or
RUN_INTEGRATION_TESTS=1 RUN_PERFORMANCE_TESTS=1 pytest tests/
```

## Test Coverage

Generate coverage report:
```bash
python scripts/run_tests.py coverage
```

This creates:
- Terminal coverage report
- HTML report in `htmlcov/index.html`

## Architecture Improvements

### Configuration Management
- **Lazy Loading**: Environment variables loaded on-demand
- **Defaults**: Graceful fallbacks for missing configuration
- **Caching**: Efficient re-use of parsed values
- **Type Safety**: Automatic type conversion with validation

### Dependency Injection
- **Protocol-Based**: Type-safe dependency contracts
- **Container Pattern**: Singleton container for global state
- **Automatic Resolution**: Smart dependency creation with fallbacks
- **Test Isolation**: Easy reset and override for testing

### Testability Enhancements
- **Import Safety**: No more import-time failures
- **Mock Integration**: Seamless mocking with dependency injection
- **State Isolation**: Proper test isolation between runs
- **Performance Monitoring**: Built-in performance benchmarks

## Troubleshooting

### Common Issues

#### Missing Dependencies
```bash
# Check what's missing
python scripts/run_tests.py --check-deps

# Install missing packages
pip install -r requirements-dev.txt
```

#### Environment Variable Errors
```bash
# Unit tests failing due to environment
# Make sure you're using proper mocking in unit tests

# Integration tests failing
# Verify environment variables are set
echo $QUICKNODE_ENDPOINT
echo $WALLET_ADDRESS
```

#### Keypair Validation Errors
```bash
# Ensure private key is properly formatted
# Should be base58 encoded and derive to the correct public key
python -c "
import base58
from solders.keypair import Keypair
kp = Keypair.from_bytes(base58.b58decode('YOUR_PRIVATE_KEY'))
print(f'Public key: {kp.pubkey()}')
"
```

#### Dependency Injection Issues
```bash
# Reset dependency container if tests interfere
from dependencies import container
container.reset()

# Check dependency configuration
from dependencies import get_deps
deps = get_deps()
print(f"Config: {deps.config}")
print(f"Trading client: {deps.trading_client}")
```

### Test Debugging

Run tests with more verbose output:
```bash
pytest tests/test_specific.py -v -s --tb=long
```

Run single test with debugging:
```bash
pytest tests/test_file.py::TestClass::test_method -v -s
```

Stop on first failure:
```bash
pytest tests/ -x
```

Debug dependency injection:
```bash
pytest tests/test_dependency_injection.py::TestDependencyInjection::test_specific -v -s
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements-dev.txt
      - run: python scripts/run_tests.py unit
      - run: python scripts/run_tests.py performance
      - run: pytest tests/test_dependency_injection.py -v
      - run: pytest tests/test_architecture_integration.py -v
      # Integration tests only on specific branches
      - run: python scripts/run_tests.py integration
        if: github.ref == 'refs/heads/main'
        env:
          RUN_INTEGRATION_TESTS: 1
          QUICKNODE_ENDPOINT: ${{ secrets.QUICKNODE_ENDPOINT }}
          WALLET_ADDRESS: ${{ secrets.WALLET_ADDRESS }}
          WALLET_PRIVATE_KEY: ${{ secrets.WALLET_PRIVATE_KEY }}
```

## Test Development Guidelines

### Writing Unit Tests
- Mock all external dependencies using dependency injection
- Test edge cases and error conditions
- Keep tests fast (< 1 second each)
- Use descriptive test names
- Reset dependency container in setup methods

### Writing Integration Tests  
- Test real API interactions
- Handle network failures gracefully
- Use conservative timeouts
- Clean up resources

### Writing E2E Tests
- Test complete user workflows
- Use devnet only
- Minimal real transactions
- Comprehensive error handling

### Using Dependency Injection in Tests
```python
class TestMyComponent:
    def setup_method(self):
        """Reset container before each test"""
        from dependencies import container
        container.reset()
    
    def test_with_mocks(self):
        mock_config = Mock()
        mock_client = AsyncMock()
        configure_deps(config_override=mock_config, trading_client=mock_client)
        
        # Test your component
        deps = get_deps()
        # ... test logic
```

## Performance Benchmarks

Expected performance targets:

- **Quote Retrieval**: < 100ms average
- **Pool Processing**: > 10 pools/second
- **Position Management**: < 2 seconds for 1000 positions
- **Memory Usage**: < 100MB growth during processing
- **Dependency Injection Overhead**: < 50% vs direct calls

Run performance tests to verify:
```bash
python scripts/run_tests.py performance -v
```

## Future Improvements

### Planned Enhancements
- **Database Integration**: Test database layer with proper isolation
- **Event System**: Test event-driven architecture patterns
- **Plugin System**: Test modular plugin loading and execution
- **Metrics Collection**: Built-in performance and reliability metrics

### Architectural Goals
- **100% Test Coverage**: Comprehensive coverage of all business logic
- **Zero Import Dependencies**: Complete elimination of import-time failures
- **Sub-100ms Unit Tests**: All unit tests complete in under 100ms
- **Automated Integration**: Full CI/CD pipeline with automated deployments

## Support

For test-related issues:
1. Check this README
2. Review test logs and error messages
3. Verify environment setup
4. Check individual test files for specific requirements
5. Use dependency injection debugging techniques
6. Reset dependency container if tests interfere with each other 