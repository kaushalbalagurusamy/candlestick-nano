"""Pytest configuration and shared fixtures"""
import pytest
import os
import sys
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, Mock

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Configure pytest markers
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )

# Shared fixtures
@pytest.fixture
def mock_environment():
    """Provide clean mock environment variables"""
    return {
        "QUICKNODE_ENDPOINT": "https://test-endpoint.solana.com",
        "JUPITER_API_BASE_URL": "https://quote-api.jup.ag/v6",
        "WALLET_ADDRESS": "2C4X2sFhnb212uC1W2GdfKL4uCRkdKhXyfxktg3T3vmA",
        "WALLET_PRIVATE_KEY": "test_private_key_32_bytes_long_123456",
        "SOLANA_CLUSTER": "devnet",
        "MIN_LIQUIDITY_THRESHOLD": "100000",
        "MAX_TOKEN_AGE": "82800",
        "SLIPPAGE_BPS": "100",
        "STOP_LOSS_PERCENTAGE": "10",
        "TAKE_PROFIT_PERCENTAGE": "20",
        "MONITORING_INTERVAL": "30",
        "AMOUNT_SOL": "0.001"
    }

@pytest.fixture
def clean_environment(mock_environment):
    """Clean environment context manager"""
    with patch.dict(os.environ, mock_environment, clear=True):
        yield mock_environment

@pytest.fixture
def mock_keypair():
    """Mock Solana keypair"""
    mock_kp = Mock()
    mock_kp.pubkey.return_value = Mock()
    mock_kp.pubkey.return_value.__str__ = Mock(return_value="2C4X2sFhnb212uC1W2GdfKL4uCRkdKhXyfxktg3T3vmA")
    return mock_kp

@pytest.fixture
def mock_solana_client():
    """Mock Solana RPC client"""
    from unittest.mock import AsyncMock
    client = AsyncMock()
    
    # Mock common responses
    client.get_balance.return_value.value = 6000000000  # 6 SOL
    client.get_version.return_value.solana_core = "1.17.0"
    client.get_slot.return_value.value = 123456789
    
    return client

@pytest.fixture
def mock_successful_quote():
    """Mock successful Jupiter quote response"""
    return {
        "outAmount": "1000000",
        "slippageBps": "100",
        "priceImpactPct": "0.01",
        "platformFee": None,
        "routePlan": []
    }

@pytest.fixture
def mock_swap_transaction():
    """Mock swap transaction response"""
    import base64
    return {
        "swapTransaction": base64.b64encode(b"mock_transaction_bytes").decode(),
        "lastValidBlockHeight": 123456789
    }

@pytest.fixture
def temp_tokens_file():
    """Create temporary tokens.json file"""
    tokens_data = [
        {"symbol": "TEST1", "address": "TestMint111111111111111111111111111111"},
        {"symbol": "TEST2", "address": "TestMint222222222222222222222222222222"},
        {"symbol": "TEST3", "address": "TestMint333333333333333333333333333333"}
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(tokens_data, f)
        temp_file = f.name
    
    yield temp_file, tokens_data
    
    # Cleanup
    try:
        os.unlink(temp_file)
    except FileNotFoundError:
        pass

@pytest.fixture
def mock_new_pools():
    """Mock new pools data"""
    from datetime import datetime, timezone
    return [
        {
            "tokenAddress": "NewPool111111111111111111111111111111",
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "exchange": "pump.fun",
            "liquidity": 500000
        },
        {
            "tokenAddress": "NewPool222222222222222222222222222222",
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "exchange": "raydium",
            "liquidity": 750000
        }
    ]

@pytest.fixture
def mock_limit_orders():
    """Mock open limit orders"""
    return [
        {
            "pubkey": "Order111111111111111111111111111111111",
            "inputMint": "Token111111111111111111111111111111111",
            "outputMint": "So11111111111111111111111111111111111111112",
            "makingAmount": "1000000",
            "takingAmount": "1200000",
            "rate": "1.2",
            "expiredAt": "1735689600"
        },
        {
            "pubkey": "Order222222222222222222222222222222222",
            "inputMint": "Token222222222222222222222222222222222",
            "outputMint": "So11111111111111111111111111111111111111112", 
            "makingAmount": "2000000",
            "takingAmount": "2400000",
            "rate": "1.2",
            "expiredAt": "1735689600"
        }
    ]

@pytest.fixture
def patch_requests():
    """Patch requests module with common successful responses"""
    def mock_get(url, **kwargs):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        if "/tokens" in url:
            mock_response.json.return_value = [
                {"address": "Token1", "symbol": "TOK1", "decimals": 9},
                {"address": "Token2", "symbol": "TOK2", "decimals": 6}
            ]
        elif "/quote" in url:
            mock_response.json.return_value = {
                "outAmount": "1000000",
                "slippageBps": "100"
            }
        elif "/new-pools" in url:
            mock_response.json.return_value = {"data": []}
        else:
            mock_response.json.return_value = {}
        
        return mock_response
    
    def mock_post(url, **kwargs):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        if "/swap" in url:
            mock_response.json.return_value = {
                "swapTransaction": "dGVzdF90eA=="  # base64 "test_tx"
            }
        elif "/limit-orders" in url:
            if "/create" in url:
                mock_response.json.return_value = {"order": "order_pubkey"}
            elif "/cancel" in url:
                mock_response.json.return_value = {"tx": "Y2FuY2VsX3R4"}  # base64 "cancel_tx"
            elif "/open" in url:
                mock_response.json.return_value = {"orders": []}
        else:
            mock_response.json.return_value = {}
        
        return mock_response
    
    with patch('requests.get', side_effect=mock_get):
        with patch('requests.post', side_effect=mock_post):
            yield

@pytest.fixture
def isolate_modules():
    """Isolate module state between tests"""
    # Store original state
    original_modules = {}
    modules_to_isolate = [
        'combined_daemon',
        'entry_daemon', 
        'exit_daemon',
        'trading_bot_core'
    ]
    
    for module_name in modules_to_isolate:
        if module_name in sys.modules:
            original_modules[module_name] = sys.modules[module_name]
            del sys.modules[module_name]
    
    yield
    
    # Restore original state
    for module_name in modules_to_isolate:
        if module_name in sys.modules:
            del sys.modules[module_name]
        if module_name in original_modules:
            sys.modules[module_name] = original_modules[module_name]

# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file patterns"""
    for item in items:
        # Add markers based on test file names
        if "test_integration" in item.fspath.basename:
            item.add_marker(pytest.mark.integration)
        if "test_e2e" in item.fspath.basename:
            item.add_marker(pytest.mark.e2e)
        if "test_performance" in item.fspath.basename:
            item.add_marker(pytest.mark.performance)
        if "test_end_to_end_devnet" in item.fspath.basename:
            item.add_marker(pytest.mark.slow)

# Test reporting hooks
@pytest.fixture(autouse=True)
def log_test_info(request):
    """Automatically log test information"""
    test_name = request.node.name
    test_file = request.node.fspath.basename
    
    print(f"\n🧪 Running: {test_file}::{test_name}")
    
    yield
    
    print(f"✅ Completed: {test_name}")

# Skip hooks for conditional tests
def pytest_runtest_setup(item):
    """Setup hook to conditionally skip tests"""
    # Skip integration tests if not explicitly enabled
    if item.get_closest_marker("integration"):
        if not os.environ.get("RUN_INTEGRATION_TESTS"):
            pytest.skip("Integration tests disabled (set RUN_INTEGRATION_TESTS=1)")
    
    # Skip performance tests in CI unless explicitly enabled
    if item.get_closest_marker("performance"):
        if os.environ.get("CI") and not os.environ.get("RUN_PERFORMANCE_TESTS"):
            pytest.skip("Performance tests disabled in CI")
    
    # Skip slow tests unless explicitly enabled
    if item.get_closest_marker("slow"):
        if not os.environ.get("RUN_SLOW_TESTS"):
            pytest.skip("Slow tests disabled (set RUN_SLOW_TESTS=1)") 