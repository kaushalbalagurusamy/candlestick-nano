"""Unit tests for exit_daemon module"""
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch, MagicMock
import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock environment variables before import
mock_env = {
    "QUICKNODE_ENDPOINT": "https://test.com",
    "WALLET_ADDRESS": "TestWallet123",
    "WALLET_PRIVATE_KEY": "test_private_key",
    "STOP_LOSS_PERCENTAGE": "10",
    "TAKE_PROFIT_PERCENTAGE": "20",
    "MONITORING_INTERVAL": "60",
    "CHAINLINK_AGGREGATOR": "aggregator123"
}

with patch.dict(os.environ, mock_env):
    import exit_daemon

class TestExitDaemon:
    """Test exit_daemon module functions"""
    
    def setup_method(self):
        """Reset state before each test"""
        exit_daemon.active_positions.clear()
        
        # Don't clear config cache here since tests rely on mock_env
        # Reset dependency container
        from dependencies import container
        container.reset()
    
    @pytest.mark.asyncio
    async def test_cancel_limit_order_success(self):
        """Test successful limit order cancellation"""
        mock_cancel_data = {"tx": "Y2FuY2VsX3R4"}  # base64 encoded "cancel_tx"
        
        mock_client = AsyncMock()
        mock_sig = Mock()
        mock_sig.value = "cancel_signature"
        mock_client.send_raw_transaction.return_value = mock_sig
        
        with patch('exit_daemon.cancel_limit_order_request', return_value=mock_cancel_data):
            with patch('exit_daemon.AsyncClient') as mock_client_class:
                # Properly mock async context manager
                mock_client_class.return_value.__aenter__.return_value = mock_client
                mock_client_class.return_value.__aexit__.return_value = None
                
                with patch('exit_daemon.Keypair.from_bytes') as mock_keypair:
                    with patch('exit_daemon.VersionedTransaction.from_bytes') as mock_tx:
                        with patch('builtins.bytes', return_value=b"mock_cancel_bytes"):
                            mock_tx_instance = Mock()
                            mock_tx.return_value = mock_tx_instance
                            
                            result = await exit_daemon.cancel_limit_order("order123")
                            
                            assert result == "cancel_signature"
                            mock_client.send_raw_transaction.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cancel_limit_order_failure(self):
        """Test limit order cancellation failure"""
        with patch('exit_daemon.cancel_limit_order_request', return_value=None):
            result = await exit_daemon.cancel_limit_order("order123")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_execute_market_sell_success(self):
        """Test successful market sell execution"""
        mock_quote = {"outAmount": "950000"}
        mock_swap_data = {"swapTransaction": "c3dhcF90eA=="}  # base64 encoded "swap_tx"
        
        mock_client = AsyncMock()
        mock_sig = Mock()
        mock_sig.value = "sell_signature"
        mock_client.send_raw_transaction.return_value = mock_sig
        
        with patch('exit_daemon.get_market_sell_quote', return_value=mock_quote):
            with patch('exit_daemon.get_swap_transaction', return_value=mock_swap_data):
                with patch('exit_daemon.AsyncClient') as mock_client_class:
                    # Properly mock async context manager
                    mock_client_class.return_value.__aenter__.return_value = mock_client
                    mock_client_class.return_value.__aexit__.return_value = None
                    
                    with patch('exit_daemon.Keypair.from_bytes'):
                        with patch('exit_daemon.VersionedTransaction.from_bytes'):
                            with patch('builtins.bytes', return_value=b"mock_sell_bytes"):
                                
                                result = await exit_daemon.execute_market_sell("mint123", 1000000)
                                
                                assert result == "sell_signature"
                                mock_client.send_raw_transaction.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_market_sell_no_quote(self):
        """Test market sell with no quote available"""
        with patch('exit_daemon.get_market_sell_quote', return_value=None):
            result = await exit_daemon.execute_market_sell("mint123", 1000000)
            assert result is None
    
    @pytest.mark.asyncio
    async def test_process_price_update_no_trigger(self):
        """Test price update processing with no stop-loss trigger"""
        # Setup position
        exit_daemon.active_positions["mint123"] = {
            "entry_price": 100.0,
            "amount": 1000000,
            "order_pubkey": "order123"
        }
        
        log_data = {"price_data": "encoded_price"}
        current_price = 105.0  # 5% gain (no stop-loss)
        
        with patch('exit_daemon.extract_price_from_log', return_value=current_price):
            with patch('exit_daemon.cancel_limit_order') as mock_cancel:
                with patch('exit_daemon.execute_market_sell') as mock_sell:
                    
                    await exit_daemon.process_price_update(log_data)
                    
                    # Should not trigger stop-loss
                    mock_cancel.assert_not_called()
                    mock_sell.assert_not_called()
                    
                    # Position should remain
                    assert "mint123" in exit_daemon.active_positions
    
    @pytest.mark.asyncio
    async def test_process_price_update_stop_loss_trigger(self):
        """Test price update processing with stop-loss trigger"""
        # Setup position
        exit_daemon.active_positions["mint123"] = {
            "entry_price": 100.0,
            "amount": 1000000,
            "order_pubkey": "order123"
        }
        
        log_data = {"price_data": "encoded_price"}
        current_price = 85.0  # 15% loss (triggers 10% stop-loss)
        
        with patch('exit_daemon.extract_price_from_log', return_value=current_price):
            with patch('exit_daemon.cancel_limit_order') as mock_cancel:
                with patch('exit_daemon.execute_market_sell') as mock_sell:
                    
                    await exit_daemon.process_price_update(log_data)
                    
                    # Should trigger stop-loss
                    mock_cancel.assert_called_once_with("order123")
                    mock_sell.assert_called_once_with("mint123", 1000000)
                    
                    # Position should be removed
                    assert "mint123" not in exit_daemon.active_positions
    
    @pytest.mark.asyncio
    async def test_update_active_positions_success(self):
        """Test successful active positions update"""
        mock_orders = [
            {
                "pubkey": "order1",
                "inputMint": "mint1", 
                "makingAmount": "1000000",
                "rate": "1.2"
            },
            {
                "pubkey": "order2",
                "inputMint": exit_daemon.WSOL_MINT,  # Should be skipped
                "makingAmount": "500000",
                "rate": "1.0"
            },
            {
                "pubkey": "order3",
                "inputMint": "mint3",
                "makingAmount": "2000000",
                "rate": "0.8"
            }
        ]
        
        with patch('exit_daemon.get_open_limit_orders', return_value=mock_orders):
            await exit_daemon.update_active_positions()
            
            # Should create positions for non-WSOL mints
            assert len(exit_daemon.active_positions) == 2
            assert "mint1" in exit_daemon.active_positions
            assert "mint3" in exit_daemon.active_positions
            assert exit_daemon.WSOL_MINT not in exit_daemon.active_positions
            
            # Check position details
            assert exit_daemon.active_positions["mint1"]["order_pubkey"] == "order1"
            assert exit_daemon.active_positions["mint1"]["amount"] == 1000000
            assert exit_daemon.active_positions["mint1"]["entry_price"] == 1.2
    
    @pytest.mark.asyncio
    async def test_update_active_positions_failure(self):
        """Test active positions update failure"""
        with patch('exit_daemon.get_open_limit_orders', side_effect=Exception("API error")):
            await exit_daemon.update_active_positions()
            
            # Should handle error gracefully without positions
            assert len(exit_daemon.active_positions) == 0
    
    def test_extract_price_from_log_placeholder(self):
        """Test price extraction placeholder function"""
        log_data = {"test": "data"}
        price = exit_daemon.extract_price_from_log(log_data)
        
        # Placeholder returns 0.0
        assert price == 0.0
    
    @pytest.mark.asyncio
    async def test_monitor_price_feed_no_aggregator(self):
        """Test price feed monitoring with no aggregator configured"""
        with patch.dict(os.environ, {"CHAINLINK_AGGREGATOR": ""}):
            # Should return early without error
            await exit_daemon.monitor_price_feed()
    
    @pytest.mark.asyncio
    async def test_monitor_price_feed_websocket_failure(self):
        """Test price feed monitoring with WebSocket failure"""
        with patch('exit_daemon.create_websocket_connection', return_value=None):
            await exit_daemon.monitor_price_feed()
            # Should handle connection failure gracefully
    
    @pytest.mark.asyncio
    async def test_monitor_price_feed_message_processing(self):
        """Test price feed WebSocket message processing"""
        mock_ws = Mock()
        mock_ws.recv.side_effect = [
            json.dumps({
                "params": {
                    "result": {"price_data": "test"}
                }
            }),
            KeyboardInterrupt()  # Exit loop
        ]
        
        with patch('exit_daemon.create_websocket_connection', return_value=mock_ws):
            with patch('exit_daemon.subscribe_to_chainlink_logs'):
                with patch('exit_daemon.process_price_update') as mock_process:
                    with patch('exit_daemon.config') as mock_config:
                        mock_config.chainlink_aggregator = "aggregator123"
                        mock_config.quicknode_endpoint = "https://test.com"
                        
                        try:
                            await exit_daemon.monitor_price_feed()
                        except KeyboardInterrupt:
                            pass
                        
                        # Should process the price update
                        mock_process.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_main_loop_structure(self):
        """Test main function loop structure"""
        with patch('exit_daemon.update_active_positions') as mock_update:
            with patch('asyncio.sleep', side_effect=KeyboardInterrupt):  # Exit after first loop
                with patch('asyncio.create_task') as mock_task:
                    with patch('exit_daemon.config') as mock_config:
                        mock_config.chainlink_aggregator = "aggregator123"
                        mock_config.stop_loss_percentage = 10.0
                        mock_config.take_profit_percentage = 20.0
                        mock_config.monitoring_interval = 30
                        
                        try:
                            await exit_daemon.main()
                        except KeyboardInterrupt:
                            pass
                        
                        # Should create background task for price monitoring when aggregator is set
                        mock_task.assert_called_once()
                        
                        # Should call update positions
                        mock_update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_main_loop_error_handling(self):
        """Test main function error handling"""
        call_count = 0
        
        def mock_update_with_error():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Test error")
            elif call_count == 2:
                raise KeyboardInterrupt()  # Exit loop
        
        with patch('exit_daemon.update_active_positions', side_effect=mock_update_with_error):
            with patch('asyncio.sleep'):
                with patch('asyncio.create_task'):
                    
                    try:
                        await exit_daemon.main()
                    except KeyboardInterrupt:
                        pass
                    
                    # Should handle error and continue
                    assert call_count == 2 