"""Unit tests for TradingBotCore class"""
import pytest
import asyncio
import base64
import base58
from unittest.mock import AsyncMock, MagicMock, patch, Mock
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from trading_bot_core import TradingBotCore

class TestTradingBotCore:
    """Test TradingBotCore class methods"""
    
    @pytest.fixture
    def bot(self):
        """Create TradingBotCore instance for testing"""
        with patch('trading_bot_core.base58.b58decode') as mock_b58decode:
            with patch('trading_bot_core.Keypair.from_bytes') as mock_keypair:
                mock_b58decode.return_value = b'\x00' * 64  # Mock 64 bytes
                mock_kp = Mock()
                mock_kp.pubkey.return_value = Mock()
                mock_keypair.return_value = mock_kp
                
                return TradingBotCore(
                    endpoint="https://test-endpoint.com",
                    wallet_address="TestWallet123", 
                    private_key="test_private_key"  # Will be mocked
                )
    
    @pytest.mark.asyncio
    async def test_setup_and_cleanup(self, bot):
        """Test setup and cleanup methods"""
        with patch('trading_bot_core.AsyncClient') as mock_client:
            await bot.setup()
            mock_client.assert_called_once_with("https://test-endpoint.com")
            assert bot.client is not None
            
            # Test cleanup
            bot.client = AsyncMock()
            await bot.cleanup()
            bot.client.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_quote_success(self, bot):
        """Test successful quote retrieval"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "outAmount": "1000000",
            "slippageBps": "100",
            "priceImpactPct": "0.01"
        }
        
        with patch('requests.get', return_value=mock_response) as mock_get:
            result = await bot.get_quote("mint1", "mint2", 1000000, 100)
            
            mock_get.assert_called_once_with(
                "https://test-endpoint.com/quote",
                params={
                    "inputMint": "mint1",
                    "outputMint": "mint2", 
                    "amount": "1000000",
                    "slippageBps": "100"
                }
            )
            assert result["outAmount"] == "1000000"
    
    @pytest.mark.asyncio
    async def test_get_quote_failure(self, bot):
        """Test quote retrieval failure"""
        with patch('requests.get', side_effect=Exception("Network error")):
            result = await bot.get_quote("mint1", "mint2", 1000000, 100)
            assert result is None
    
    @pytest.mark.asyncio 
    async def test_execute_swap_success(self, bot):
        """Test successful swap execution"""
        # Mock swap response
        mock_swap_response = Mock()
        mock_swap_response.raise_for_status = Mock()
        mock_swap_response.json.return_value = {
            "swapTransaction": base64.b64encode(b"test_transaction").decode()
        }
        
        # Mock client
        bot.client = AsyncMock()
        mock_sig = Mock()
        mock_sig.value = "test_signature"
        bot.client.send_raw_transaction.return_value = mock_sig
        
        quote_data = {"test": "data"}
        
        with patch('requests.post', return_value=mock_swap_response) as mock_post:
            with patch('trading_bot_core.VersionedTransaction.from_bytes') as mock_tx:
                with patch('builtins.bytes') as mock_bytes:
                    mock_tx_instance = Mock()
                    mock_tx.return_value = mock_tx_instance
                    mock_bytes.return_value = b"mock_transaction_bytes"
                    
                    result = await bot.execute_swap(quote_data)
                    
                    mock_post.assert_called_once_with(
                        "https://test-endpoint.com/swap",
                        json={
                            "owner": "TestWallet123",
                            "quoteResponse": quote_data
                        }
                    )
                    assert result == "test_signature"
    
    @pytest.mark.asyncio
    async def test_create_limit_order_success(self, bot):
        """Test successful limit order creation"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"order": "order_123"}
        
        with patch('requests.post', return_value=mock_response) as mock_post:
            with patch('time.time', return_value=1000000):
                result = await bot.create_limit_order("test_mint", 1000000, 20.0)
                
                mock_post.assert_called_once()
                call_args = mock_post.call_args[1]['json']
                assert call_args['inputMint'] == "test_mint"
                assert call_args['params']['makingAmount'] == "1000000"
                assert call_args['params']['takingAmount'] == "1200000"  # 20% profit
                assert result == "order_123"
    
    @pytest.mark.asyncio
    async def test_get_open_orders_success(self, bot):
        """Test successful open orders retrieval"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "orders": [{"pubkey": "order1"}, {"pubkey": "order2"}]
        }
        
        with patch('requests.get', return_value=mock_response) as mock_get:
            result = await bot.get_open_orders()
            
            mock_get.assert_called_once_with(
                "https://test-endpoint.com/limit-orders/open",
                params={"wallet": "TestWallet123"}
            )
            assert len(result) == 2
            assert result[0]["pubkey"] == "order1"
    
    @pytest.mark.asyncio
    async def test_cancel_limit_order_success(self, bot):
        """Test successful limit order cancellation"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "tx": base64.b64encode(b"cancel_transaction").decode()
        }
        
        bot.client = AsyncMock()
        mock_sig = Mock()
        mock_sig.value = "cancel_signature"
        bot.client.send_raw_transaction.return_value = mock_sig
        
        with patch('requests.post', return_value=mock_response) as mock_post:
            with patch('trading_bot_core.VersionedTransaction.from_bytes') as mock_tx:
                with patch('builtins.bytes') as mock_bytes:
                    mock_tx_instance = Mock()
                    mock_tx.return_value = mock_tx_instance
                    mock_bytes.return_value = b"mock_cancel_transaction_bytes"
                    
                    result = await bot.cancel_limit_order("order_123")
                    
                    mock_post.assert_called_once_with(
                        "https://test-endpoint.com/limit-orders/cancel",
                        json={
                            "owner": "TestWallet123",
                            "orderPubkey": "order_123"
                        }
                    )
                    assert result == "cancel_signature"
    
    @pytest.mark.asyncio
    async def test_check_token_safety_safe_token(self, bot):
        """Test token safety check for safe token (no freeze authority)"""
        bot.client = AsyncMock()
        
        mock_response = Mock()
        mock_response.value.data.parsed = {
            "info": {
                "freezeAuthority": None
            }
        }
        bot.client.get_account_info_json_parsed.return_value = mock_response
        
        result = await bot.check_token_safety("safe_mint")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_check_token_safety_unsafe_token(self, bot):
        """Test token safety check for unsafe token (has freeze authority)"""
        bot.client = AsyncMock()
        
        mock_response = Mock()
        mock_response.value.data.parsed = {
            "info": {
                "freezeAuthority": "SomeAuthorityAddress"
            }
        }
        bot.client.get_account_info_json_parsed.return_value = mock_response
        
        result = await bot.check_token_safety("unsafe_mint")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_check_token_safety_no_account(self, bot):
        """Test token safety check when account doesn't exist"""
        bot.client = AsyncMock()
        
        mock_response = Mock()
        mock_response.value = None
        bot.client.get_account_info_json_parsed.return_value = mock_response
        
        result = await bot.check_token_safety("nonexistent_mint")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_check_token_safety_error(self, bot):
        """Test token safety check error handling"""
        bot.client = AsyncMock()
        bot.client.get_account_info_json_parsed.side_effect = Exception("RPC error")
        
        result = await bot.check_token_safety("error_mint")
        assert result is False 