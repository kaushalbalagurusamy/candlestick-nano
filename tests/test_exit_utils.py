"""Unit tests for exit_utils functions"""
import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import exit_utils

class TestExitUtils:
    """Test exit_utils module functions"""
    
    @pytest.mark.asyncio
    async def test_get_open_limit_orders_success(self):
        """Test successful open orders retrieval"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "orders": [
                {"pubkey": "order1", "inputMint": "mint1"},
                {"pubkey": "order2", "inputMint": "mint2"}
            ]
        }
        
        with patch('requests.get', return_value=mock_response) as mock_get:
            result = await exit_utils.get_open_limit_orders("https://test.com", "wallet123")
            
            mock_get.assert_called_once_with(
                "https://test.com/limit-orders/open",
                params={"wallet": "wallet123"}
            )
            assert len(result) == 2
            assert result[0]["pubkey"] == "order1"
    
    @pytest.mark.asyncio
    async def test_get_open_limit_orders_failure(self):
        """Test open orders retrieval failure"""
        with patch('requests.get', side_effect=Exception("Network error")):
            result = await exit_utils.get_open_limit_orders("https://test.com", "wallet123")
            assert result == []
    
    @pytest.mark.asyncio
    async def test_cancel_limit_order_request_success(self):
        """Test successful cancel order request"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {"tx": "cancel_tx_data"}
        
        with patch('requests.post', return_value=mock_response) as mock_post:
            result = await exit_utils.cancel_limit_order_request("https://test.com", "wallet123", "order456")
            
            mock_post.assert_called_once_with(
                "https://test.com/limit-orders/cancel",
                json={
                    "owner": "wallet123",
                    "orderPubkey": "order456"
                }
            )
            assert result["tx"] == "cancel_tx_data"
    
    @pytest.mark.asyncio
    async def test_cancel_limit_order_request_failure(self):
        """Test cancel order request failure"""
        with patch('requests.post', side_effect=Exception("Network error")):
            result = await exit_utils.cancel_limit_order_request("https://test.com", "wallet123", "order456")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_market_sell_quote_success(self):
        """Test successful market sell quote"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "outAmount": "950000",
            "slippageBps": "500"
        }
        
        with patch('requests.get', return_value=mock_response) as mock_get:
            result = await exit_utils.get_market_sell_quote("https://test.com", "mint1", "wsol", 1000000)
            
            mock_get.assert_called_once_with(
                "https://test.com/quote",
                params={
                    "inputMint": "mint1",
                    "outputMint": "wsol",
                    "amount": "1000000",
                    "slippageBps": "500"
                }
            )
            assert result["outAmount"] == "950000"
    
    @pytest.mark.asyncio
    async def test_get_market_sell_quote_failure(self):
        """Test market sell quote failure"""
        with patch('requests.get', side_effect=Exception("Network error")):
            result = await exit_utils.get_market_sell_quote("https://test.com", "mint1", "wsol", 1000000)
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_swap_transaction_success(self):
        """Test successful swap transaction retrieval"""
        quote_data = {"test": "quote"}
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "swapTransaction": "swap_tx_data"
        }
        
        with patch('requests.post', return_value=mock_response) as mock_post:
            result = await exit_utils.get_swap_transaction("https://test.com", "wallet123", quote_data)
            
            mock_post.assert_called_once_with(
                "https://test.com/swap",
                json={
                    "owner": "wallet123",
                    "quoteResponse": quote_data
                }
            )
            assert result["swapTransaction"] == "swap_tx_data"
    
    @pytest.mark.asyncio
    async def test_get_swap_transaction_failure(self):
        """Test swap transaction retrieval failure"""
        with patch('requests.post', side_effect=Exception("Network error")):
            result = await exit_utils.get_swap_transaction("https://test.com", "wallet123", {"test": "quote"})
            assert result is None
    
    def test_create_websocket_connection_success(self):
        """Test successful WebSocket connection creation"""
        mock_ws = Mock()
        
        with patch('exit_utils.create_connection', return_value=mock_ws) as mock_create:
            result = exit_utils.create_websocket_connection("https://test.com")
            
            mock_create.assert_called_once_with("wss://test.com")
            assert result == mock_ws
    
    def test_create_websocket_connection_failure(self):
        """Test WebSocket connection creation failure"""
        with patch('exit_utils.create_connection', side_effect=Exception("Connection error")):
            result = exit_utils.create_websocket_connection("https://test.com")
            assert result is None
    
    def test_subscribe_to_chainlink_logs(self):
        """Test Chainlink logs subscription"""
        mock_ws = Mock()
        
        exit_utils.subscribe_to_chainlink_logs(mock_ws, "aggregator123")
        
        mock_ws.send.assert_called_once()
        call_args = mock_ws.send.call_args[0][0]
        
        # Parse the JSON to verify structure
        import json
        message = json.loads(call_args)
        assert message["method"] == "logs_subscribe"
        assert message["params"][0]["mentions"] == ["aggregator123"] 