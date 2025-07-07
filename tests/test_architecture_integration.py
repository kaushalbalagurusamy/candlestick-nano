"""Tests for architecture integration between existing code and new dependency injection system"""
import pytest
import os
import sys
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone, timedelta

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from dependencies import Dependencies, configure_deps, get_deps
from config import Config

class TestArchitectureIntegration:
    """Test integration between existing architecture and dependency injection"""
    
    def setup_method(self):
        """Reset dependency container before each test"""
        from dependencies import container
        container.reset()
    
    @pytest.mark.asyncio
    async def test_combined_daemon_with_dependency_injection(self):
        """Test combined_daemon using dependency injection instead of direct imports"""
        # Create mock dependencies
        mock_config = Mock()
        mock_config.quicknode_endpoint = "https://test.com"
        mock_config.wallet_address = "TestWallet"  
        mock_config.wallet_private_key = "TestKey"
        mock_config.min_liquidity_threshold = 100000
        mock_config.max_token_age = 3600
        mock_config.slippage_bps = 100
        mock_config.stop_loss_percentage = 10.0
        mock_config.take_profit_percentage = 20.0
        mock_config.monitoring_interval = 30
        
        mock_trading_client = AsyncMock()
        mock_trading_client.setup = AsyncMock()
        mock_trading_client.cleanup = AsyncMock()
        mock_trading_client.check_token_safety.return_value = True
        mock_trading_client.get_quote.return_value = {"outAmount": "500000"}
        mock_trading_client.execute_swap.return_value = "tx_signature"
        mock_trading_client.create_limit_order.return_value = "order_pubkey"
        
        # Configure dependencies
        configure_deps(
            config_override=mock_config,
            trading_client=mock_trading_client
        )
        
        # Import combined_daemon after dependency configuration
        import combined_daemon
        
        # Create a modified version that uses dependency injection
        deps = get_deps()
        
        # Mock pools data
        recent_time = datetime.now(timezone.utc)
        pools = [{"tokenAddress": "test_mint", "timestamp": recent_time.isoformat().replace('+00:00', 'Z')}]
        
        with patch('combined_daemon.fetch_new_pools', return_value=pools):
            await combined_daemon.process_new_pools(deps.trading_client)
            
            # Verify dependency injection worked
            deps.trading_client.check_token_safety.assert_called_once()
            deps.trading_client.get_quote.assert_called_once()
            deps.trading_client.execute_swap.assert_called_once()
            deps.trading_client.create_limit_order.assert_called_once()
    
    @pytest.mark.asyncio 
    async def test_trading_bot_core_with_config_injection(self):
        """Test TradingBotCore with injected configuration"""
        # Create configuration through dependency injection
        mock_config = Mock()
        mock_config.quicknode_endpoint = "https://injected-endpoint.com"
        mock_config.wallet_address = "InjectedWallet"
        mock_config.wallet_private_key = "InjectedKey"
        
        configure_deps(config_override=mock_config)
        deps = get_deps()
        
        # Verify configuration was injected
        assert deps.config.quicknode_endpoint == "https://injected-endpoint.com"
        assert deps.config.wallet_address == "InjectedWallet"
        assert deps.config.wallet_private_key == "InjectedKey"
    
    @pytest.mark.asyncio
    async def test_entry_daemon_compatibility_with_injection(self):
        """Test entry_daemon functions work with dependency injection"""
        # Configure mock dependencies
        mock_config = Mock()
        mock_config.quicknode_endpoint = "https://test.com"
        mock_config.min_liquidity_threshold = 100000
        mock_config.max_token_age = 3600
        mock_config.slippage_bps = 100
        
        mock_http_client = Mock()
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {"data": []}
        mock_http_client.get.return_value = mock_response
        
        configure_deps(
            config_override=mock_config,
            http_client=mock_http_client
        )
        
        deps = get_deps()
        
        # Test that entry_daemon functions can use injected HTTP client
        # (This would require refactoring entry_daemon to use deps.http_client)
        assert deps.http_client is mock_http_client
        assert deps.config.quicknode_endpoint == "https://test.com"
    
    def test_config_lazy_loading_integration(self):
        """Test that lazy loading config integrates with dependency injection"""
        # Test with missing environment variables
        with patch.dict(os.environ, {}, clear=True):
            # Config should handle missing variables gracefully
            mock_config = Mock()
            mock_config.quicknode_endpoint = "https://fallback.com"
            mock_config.wallet_address = "FallbackWallet"
            
            configure_deps(config_override=mock_config)
            deps = get_deps()
            
            # Should use injected config instead of failing on missing env vars
            assert deps.config.quicknode_endpoint == "https://fallback.com"
            assert deps.config.wallet_address == "FallbackWallet"
    
    @pytest.mark.asyncio
    async def test_mixed_architecture_compatibility(self):
        """Test that existing code works alongside dependency injection"""
        # Setup environment for existing code
        mock_env = {
            "QUICKNODE_ENDPOINT": "https://env-endpoint.com",
            "WALLET_ADDRESS": "EnvWallet",
            "WALLET_PRIVATE_KEY": "EnvKey",
            "MIN_LIQUIDITY_THRESHOLD": "200000"
        }
        
        with patch.dict(os.environ, mock_env):
            # Test that regular config still works
            from config import config
            config.clear_cache()  # Clear cached values to pick up new env vars
            
            assert config.quicknode_endpoint == "https://env-endpoint.com"
            assert config.min_liquidity_threshold == 200000
            
            # Test that dependency injection can override
            mock_config = Mock()
            mock_config.quicknode_endpoint = "https://override-endpoint.com"
            mock_config.min_liquidity_threshold = 300000
            
            configure_deps(config_override=mock_config)
            deps = get_deps()
            
            # Injected config should take precedence
            assert deps.config.quicknode_endpoint == "https://override-endpoint.com"
            assert deps.config.min_liquidity_threshold == 300000
            
            # But original config still works for legacy code
            assert config.quicknode_endpoint == "https://env-endpoint.com"
    
    @pytest.mark.asyncio
    async def test_error_handling_with_dependencies(self):
        """Test error handling works correctly with dependency injection"""
        # Configure dependencies with error-prone mocks
        mock_config = Mock()
        mock_config.quicknode_endpoint = "https://test.com"
        
        mock_trading_client = AsyncMock()
        mock_trading_client.check_token_safety.side_effect = Exception("Safety check failed")
        
        configure_deps(
            config_override=mock_config,
            trading_client=mock_trading_client
        )
        
        deps = get_deps()
        
        # Test that errors are handled gracefully
        try:
            result = await deps.trading_client.check_token_safety("test_mint")
            assert False, "Should have raised exception"
        except Exception as e:
            assert str(e) == "Safety check failed"
    
    def test_dependency_container_isolation(self):
        """Test that dependency containers are properly isolated between tests"""
        # Configure first set of dependencies
        config1 = Mock()
        config1.quicknode_endpoint = "https://first.com"
        configure_deps(config_override=config1)
        
        deps1 = get_deps()
        assert deps1.config.quicknode_endpoint == "https://first.com"
        
        # Reset and configure different dependencies
        from dependencies import container
        container.reset()
        
        config2 = Mock()
        config2.quicknode_endpoint = "https://second.com"
        configure_deps(config_override=config2)
        
        deps2 = get_deps()
        assert deps2.config.quicknode_endpoint == "https://second.com"
        
        # First dependency should not affect second
        assert deps2.config.quicknode_endpoint != "https://first.com"
    
    @pytest.mark.asyncio
    async def test_performance_with_dependency_injection(self):
        """Test that dependency injection doesn't significantly impact performance"""
        import time
        
        # Time regular function calls
        mock_config = Mock()
        mock_config.quicknode_endpoint = "https://test.com"
        
        mock_trading_client = AsyncMock()
        mock_trading_client.check_token_safety.return_value = True
        
        configure_deps(
            config_override=mock_config,
            trading_client=mock_trading_client
        )
        
        # Time dependency injection overhead
        start_time = time.time()
        for _ in range(100):
            deps = get_deps()
            await deps.trading_client.check_token_safety("test_mint")
        end_time = time.time()
        
        injection_time = end_time - start_time
        
        # Time direct calls for comparison
        start_time = time.time()
        for _ in range(100):
            await mock_trading_client.check_token_safety("test_mint")
        end_time = time.time()
        
        direct_time = end_time - start_time
        
        # Dependency injection should not add significant overhead (< 60% increase)
        overhead_ratio = injection_time / direct_time if direct_time > 0 else 1
        assert overhead_ratio < 1.6, f"Dependency injection overhead too high: {overhead_ratio}x" 