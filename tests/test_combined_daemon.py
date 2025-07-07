"""Unit tests for combined_daemon module"""
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch, MagicMock
import sys
import os
from datetime import datetime, timezone, timedelta

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock environment variables before import
mock_env = {
    "QUICKNODE_ENDPOINT": "https://test.com",
    "WALLET_ADDRESS": "TestWallet123",
    "WALLET_PRIVATE_KEY": "test_private_key",
    "MIN_LIQUIDITY_THRESHOLD": "100000",
    "MAX_TOKEN_AGE": "82800",
    "SLIPPAGE_BPS": "100",
    "STOP_LOSS_PERCENTAGE": "10",
    "TAKE_PROFIT_PERCENTAGE": "20",
    "MONITORING_INTERVAL": "30"
}

with patch.dict(os.environ, mock_env):
    import combined_daemon

class TestCombinedDaemon:
    """Test combined_daemon module functions"""
    
    def setup_method(self):
        """Reset state before each test"""
        combined_daemon.seen_pools.clear()
        combined_daemon.active_positions.clear()
    
    @pytest.mark.asyncio
    async def test_fetch_new_pools_success(self):
        """Test successful new pools fetching"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "data": [
                {"tokenAddress": "mint1", "timestamp": "2024-01-01T00:00:00Z"},
                {"tokenAddress": "mint2", "timestamp": "2024-01-01T01:00:00Z"}
            ]
        }
        
        with patch('requests.get', return_value=mock_response):
            result = await combined_daemon.fetch_new_pools()
            
            assert len(result) == 2
            assert result[0]["tokenAddress"] == "mint1"
    
    @pytest.mark.asyncio
    async def test_fetch_new_pools_failure(self):
        """Test new pools fetching failure"""
        with patch('requests.get', side_effect=Exception("Network error")):
            result = await combined_daemon.fetch_new_pools()
            assert result == []
    
    @pytest.mark.asyncio
    async def test_process_new_pools_skip_seen(self):
        """Test process_new_pools skips already seen pools"""
        # Add a pool to seen_pools
        combined_daemon.seen_pools.add("seen_mint")
        
        pools = [{"tokenAddress": "seen_mint", "timestamp": "2024-01-01T00:00:00Z"}]
        
        mock_bot = AsyncMock()
        
        with patch('combined_daemon.fetch_new_pools', return_value=pools):
            await combined_daemon.process_new_pools(mock_bot)
            
            # Should not call any bot methods since pool was already seen
            mock_bot.check_token_safety.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_new_pools_age_filter(self):
        """Test process_new_pools filters old tokens"""
        # Create old timestamp - 2 days ago to ensure it's older than MAX_TOKEN_AGE
        old_time = datetime.now(timezone.utc) - timedelta(days=2)
        old_timestamp = old_time.isoformat().replace('+00:00', 'Z')
        
        pools = [{"tokenAddress": "old_mint", "timestamp": old_timestamp}]
        
        mock_bot = AsyncMock()
        # The token should be filtered out due to age, so get_quote should not be called
        # But if it is called for some reason, provide a valid response
        mock_bot.get_quote.return_value = {"outAmount": "500000"}
        
        with patch('combined_daemon.fetch_new_pools', return_value=pools):
            await combined_daemon.process_new_pools(mock_bot)
            
            # Should not proceed to safety check for old token
            mock_bot.check_token_safety.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_new_pools_safety_filter(self):
        """Test process_new_pools filters unsafe tokens"""
        recent_time = datetime.now(timezone.utc)
        recent_timestamp = recent_time.isoformat().replace('+00:00', 'Z')
        
        pools = [{"tokenAddress": "unsafe_mint", "timestamp": recent_timestamp}]
        
        mock_bot = AsyncMock()
        mock_bot.check_token_safety.return_value = False  # Unsafe token
        
        with patch('combined_daemon.fetch_new_pools', return_value=pools):
            await combined_daemon.process_new_pools(mock_bot)
            
            # Should check safety but not proceed to quote
            mock_bot.check_token_safety.assert_called_once()
            mock_bot.get_quote.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_new_pools_liquidity_filter(self):
        """Test process_new_pools filters low liquidity tokens"""
        recent_time = datetime.now(timezone.utc)
        recent_timestamp = recent_time.isoformat().replace('+00:00', 'Z')
        
        pools = [{"tokenAddress": "lowliq_mint", "timestamp": recent_timestamp}]
        
        mock_bot = AsyncMock()
        mock_bot.check_token_safety.return_value = True  # Safe token
        mock_bot.get_quote.return_value = {"outAmount": "50000"}  # Below threshold of 100000
        
        # Ensure config cache is cleared and environment is properly set
        with patch.dict(os.environ, mock_env):
            from config import config
            config.clear_cache()  # Clear any cached values
            
            with patch('combined_daemon.fetch_new_pools', return_value=pools):
                await combined_daemon.process_new_pools(mock_bot)
                
                # Should check liquidity but not execute swap
                mock_bot.get_quote.assert_called_once()
                mock_bot.execute_swap.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_new_pools_successful_trade(self):
        """Test process_new_pools executes successful trade"""
        recent_time = datetime.now(timezone.utc)
        recent_timestamp = recent_time.isoformat().replace('+00:00', 'Z')
        
        pools = [{"tokenAddress": "good_mint", "timestamp": recent_timestamp}]
        
        mock_bot = AsyncMock()
        mock_bot.check_token_safety.return_value = True
        mock_bot.get_quote.return_value = {"outAmount": "500000"}  # Above threshold
        mock_bot.execute_swap.return_value = "tx_signature"
        mock_bot.create_limit_order.return_value = "order_pubkey"
        
        with patch('combined_daemon.fetch_new_pools', return_value=pools):
            await combined_daemon.process_new_pools(mock_bot)
            
            # Should execute full trading flow
            mock_bot.check_token_safety.assert_called_once()
            mock_bot.get_quote.assert_called_once()
            mock_bot.execute_swap.assert_called_once()
            mock_bot.create_limit_order.assert_called_once()
            
            # Should track position
            assert "good_mint" in combined_daemon.active_positions
            position = combined_daemon.active_positions["good_mint"]
            assert position["order_pubkey"] == "order_pubkey"
            assert position["amount"] == 500000
    
    @pytest.mark.asyncio
    async def test_check_stop_loss_conditions_no_trigger(self):
        """Test stop-loss check with no trigger"""
        # Setup position
        combined_daemon.active_positions["test_mint"] = {
            "order_pubkey": "order123",
            "amount": 1000000,
            "entry_price": 1.0,
            "timestamp": datetime.utcnow()
        }
        
        mock_bot = AsyncMock()
        # Price went up 5% (no stop-loss trigger)
        mock_bot.get_quote.return_value = {"outAmount": "1050000"}
        
        await combined_daemon.check_stop_loss_conditions(mock_bot)
        
        # Should not cancel or execute sells
        mock_bot.cancel_limit_order.assert_not_called()
        mock_bot.execute_swap.assert_not_called()
        
        # Position should remain
        assert "test_mint" in combined_daemon.active_positions
    
    @pytest.mark.asyncio
    async def test_check_stop_loss_conditions_trigger(self):
        """Test stop-loss trigger and execution"""
        # Setup position
        combined_daemon.active_positions["test_mint"] = {
            "order_pubkey": "order123", 
            "amount": 1000000,
            "entry_price": 1.0,
            "timestamp": datetime.utcnow()
        }
        
        mock_bot = AsyncMock()
        # Price dropped 15% (triggers 10% stop-loss)
        mock_bot.get_quote.return_value = {"outAmount": "850000"}
        mock_bot.execute_swap.return_value = "sell_tx_signature"
        
        await combined_daemon.check_stop_loss_conditions(mock_bot)
        
        # Should cancel limit order and execute market sell
        mock_bot.cancel_limit_order.assert_called_once_with("order123")
        mock_bot.execute_swap.assert_called_once()
        
        # Position should be removed
        assert "test_mint" not in combined_daemon.active_positions
    
    @pytest.mark.asyncio
    async def test_update_positions_sync_with_orders(self):
        """Test update_positions syncs with open orders"""
        mock_orders = [
            {
                "pubkey": "order1",
                "inputMint": "mint1",
                "makingAmount": "1000000"
            },
            {
                "pubkey": "order2", 
                "inputMint": "mint2",
                "makingAmount": "2000000"
            }
        ]
        
        mock_bot = AsyncMock()
        mock_bot.get_open_orders.return_value = mock_orders
        
        await combined_daemon.update_positions(mock_bot)
        
        # Should create positions for both orders
        assert "mint1" in combined_daemon.active_positions
        assert "mint2" in combined_daemon.active_positions
        
        assert combined_daemon.active_positions["mint1"]["order_pubkey"] == "order1"
        assert combined_daemon.active_positions["mint1"]["amount"] == 1000000
    
    @pytest.mark.asyncio
    async def test_update_positions_remove_closed_orders(self):
        """Test update_positions removes positions without orders"""
        # Setup existing position
        combined_daemon.active_positions["old_mint"] = {
            "order_pubkey": "old_order",
            "amount": 500000,
            "entry_price": 1.0
        }
        
        mock_bot = AsyncMock()
        mock_bot.get_open_orders.return_value = []  # No open orders
        
        await combined_daemon.update_positions(mock_bot)
        
        # Should remove position since no corresponding order
        assert "old_mint" not in combined_daemon.active_positions
    
    @pytest.mark.asyncio
    async def test_main_loop_structure(self):
        """Test main function loop structure"""
        mock_bot = Mock()
        mock_bot.setup = AsyncMock()
        mock_bot.cleanup = AsyncMock()
        
        # Mock environment variables needed by config
        with patch.dict(os.environ, mock_env):
            # Mock all the loop functions
            with patch('combined_daemon.TradingBotCore', return_value=mock_bot):
                with patch('combined_daemon.process_new_pools') as mock_process:
                    with patch('combined_daemon.update_positions') as mock_update:
                        with patch('combined_daemon.check_stop_loss_conditions') as mock_stop_loss:
                            with patch('asyncio.sleep', side_effect=KeyboardInterrupt):  # Exit after first loop
                                
                                try:
                                    await combined_daemon.main()
                                except KeyboardInterrupt:
                                    pass
                                
                                # Verify setup and cleanup
                                mock_bot.setup.assert_called_once()
                                mock_bot.cleanup.assert_called_once()
                                
                                # Verify loop functions called
                                mock_process.assert_called_once()
                                mock_update.assert_called_once() 
                                mock_stop_loss.assert_called_once() 