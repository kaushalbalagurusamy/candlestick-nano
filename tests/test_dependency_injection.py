"""Tests for dependency injection system"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from dependencies import Dependencies, DependencyContainer, configure_deps, get_deps
from config import Config

class TestDependencyInjection:
    """Test dependency injection functionality"""
    
    def setup_method(self):
        """Reset container before each test"""
        container = DependencyContainer()
        container.reset()
    
    def test_config_protocol_compliance(self):
        """Test that Config class implements ConfigProtocol"""
        # Use mock environment for this test
        mock_env = {
            "QUICKNODE_ENDPOINT": "https://test.com",
            "WALLET_ADDRESS": "TestWallet123",
            "WALLET_PRIVATE_KEY": "test_private_key_base58_encoded_32_bytes"
        }
        
        with patch.dict(os.environ, mock_env):
            config = Config()
            
            # Test that config has all required properties
            assert hasattr(config, 'quicknode_endpoint')
            assert hasattr(config, 'wallet_address') 
            assert hasattr(config, 'wallet_private_key')
            assert hasattr(config, 'min_liquidity_threshold')
            assert hasattr(config, 'max_token_age')
            assert hasattr(config, 'slippage_bps')
            assert hasattr(config, 'stop_loss_percentage')
            assert hasattr(config, 'take_profit_percentage')
            assert hasattr(config, 'monitoring_interval')
    
    def test_dependencies_default_creation(self):
        """Test Dependencies creates defaults when not provided"""
        mock_config = Mock()
        mock_config.quicknode_endpoint = "https://test.com"
        mock_config.wallet_address = "test_wallet_that_is_long_enough"
        mock_config.wallet_private_key = "valid_base58_private_key_format_longer_than_ten"
        
        deps = Dependencies(config=mock_config)
        
        # Should create default HTTP client
        assert deps.http_client is not None
        assert hasattr(deps.http_client, 'get')
        assert hasattr(deps.http_client, 'post')
        
        # Should attempt to create trading client but may fail due to validation
        # That's okay, we're just testing the dependency system
    
    def test_dependencies_with_mocks(self):
        """Test Dependencies with mocked dependencies"""
        mock_config = Mock()
        mock_http_client = Mock()
        mock_trading_client = AsyncMock()
        
        deps = Dependencies(
            config=mock_config,
            http_client=mock_http_client,
            trading_client=mock_trading_client
        )
        
        assert deps.config is mock_config
        assert deps.http_client is mock_http_client
        assert deps.trading_client is mock_trading_client
    
    def test_dependencies_with_invalid_config(self):
        """Test Dependencies with invalid config doesn't crash"""
        mock_config = Mock()
        # Make config properties return invalid values
        mock_config.quicknode_endpoint = "not_a_url"
        mock_config.wallet_address = "short"
        mock_config.wallet_private_key = "invalid"
        
        deps = Dependencies(config=mock_config)
        
        # Should create HTTP client but not trading client
        assert deps.http_client is not None
        # Trading client should be None due to validation failure
        assert deps.trading_client is None
    
    def test_dependency_container_singleton(self):
        """Test that DependencyContainer is a singleton"""
        container1 = DependencyContainer()
        container2 = DependencyContainer()
        
        assert container1 is container2
    
    def test_dependency_container_configuration(self):
        """Test dependency container configuration"""
        container = DependencyContainer()
        
        mock_config = Mock()
        mock_trading_client = AsyncMock()
        
        deps = Dependencies(
            config=mock_config,
            trading_client=mock_trading_client
        )
        
        container.configure(deps)
        retrieved_deps = container.get_dependencies()
        
        assert retrieved_deps.config is mock_config
        assert retrieved_deps.trading_client is mock_trading_client
    
    def test_configure_deps_convenience_function(self):
        """Test convenience function for configuring dependencies"""
        mock_config = Mock()
        mock_trading_client = AsyncMock()
        
        configure_deps(config_override=mock_config, trading_client=mock_trading_client)
        deps = get_deps()
        
        assert deps.config is mock_config
        assert deps.trading_client is mock_trading_client
    
    @pytest.mark.asyncio
    async def test_mocked_trading_client_in_use(self):
        """Test using mocked trading client in business logic"""
        # Create mock dependencies
        mock_config = Mock()
        mock_config.min_liquidity_threshold = 100000
        mock_config.slippage_bps = 100
        
        mock_trading_client = AsyncMock()
        mock_trading_client.get_quote.return_value = {"outAmount": "500000"}
        mock_trading_client.check_token_safety.return_value = True
        mock_trading_client.execute_swap.return_value = "tx_signature"
        
        # Configure dependencies
        configure_deps(
            config_override=mock_config,
            trading_client=mock_trading_client
        )
        
        # Import and use combined_daemon with injected dependencies
        # This would be the actual business logic using get_deps()
        deps = get_deps()
        
        # Simulate business logic
        is_safe = await deps.trading_client.check_token_safety("test_mint")
        quote = await deps.trading_client.get_quote("wsol", "test_mint", 1000000, 100)
        
        assert is_safe is True
        assert quote["outAmount"] == "500000"
        
        # Verify mocks were called
        mock_trading_client.check_token_safety.assert_called_once_with("test_mint")
        mock_trading_client.get_quote.assert_called_once_with("wsol", "test_mint", 1000000, 100)
    
    def test_dependency_container_reset(self):
        """Test dependency container reset functionality"""
        container = DependencyContainer()
        
        # Configure with custom dependencies
        mock_config = Mock()
        mock_trading_client = AsyncMock()
        deps = Dependencies(config=mock_config, trading_client=mock_trading_client)
        container.configure(deps)
        
        # Verify configuration
        assert container.get_dependencies().config is mock_config
        assert container.get_dependencies().trading_client is mock_trading_client
        
        # Reset and verify defaults are used
        container.reset()
        default_deps = container.get_dependencies()
        
        # Should create new default dependencies
        assert default_deps.config is not mock_config
        assert default_deps.trading_client is not mock_trading_client
    
    def test_http_client_protocol_compliance(self):
        """Test that requests module implements HTTPClientProtocol"""
        import requests
        
        # Test that requests has required methods
        assert hasattr(requests, 'get')
        assert hasattr(requests, 'post')
        assert callable(requests.get)
        assert callable(requests.post) 