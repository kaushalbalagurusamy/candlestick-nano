"""Unit tests for entry_daemon functions"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, Mock
import sys
import os
from datetime import datetime, timezone, timedelta

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import entry_daemon

class TestEntryDaemon:
    """Test entry_daemon module functions"""
    
    def setup_method(self):
        """Reset state before each test to prevent pollution"""
        # Clear seen pools
        entry_daemon.seen_pools.clear()
        
        # Reset dependency container (but don't clear config cache as it interferes with env mocking)
        from dependencies import container
        container.reset()
    
    @pytest.mark.asyncio
    async def test_fetch_new_pools_success(self):
        """Test successful pool fetching"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "data": [
                {"tokenAddress": "mint1", "timestamp": "2024-01-01T00:00:00Z"},
                {"tokenAddress": "mint2", "timestamp": "2024-01-01T01:00:00Z"}
            ]
        }
        
        with patch('requests.get', return_value=mock_response) as mock_get:
            with patch.dict(os.environ, {"QUICKNODE_ENDPOINT": "https://test.com"}):
                result = await entry_daemon.fetch_new_pools()
                
                mock_get.assert_called_once_with("https://test.com/new-pools")
                assert len(result) == 2
                assert result[0]["tokenAddress"] == "mint1"
    
    @pytest.mark.asyncio
    async def test_fetch_new_pools_failure(self):
        """Test pool fetching failure"""
        with patch('requests.get', side_effect=Exception("Network error")):
            with patch.dict(os.environ, {"QUICKNODE_ENDPOINT": "https://test.com"}):
                result = await entry_daemon.fetch_new_pools()
                assert result == []
    
    @pytest.mark.asyncio
    async def test_check_freeze_authority_safe_token(self):
        """Test freeze authority check for safe token"""
        client = AsyncMock()
        
        mock_response = Mock()
        mock_response.value.data.parsed = {
            "info": {"freezeAuthority": None}
        }
        client.get_account_info_json_parsed.return_value = mock_response
        
        result = await entry_daemon.check_freeze_authority(client, "safe_mint")
        assert result is False  # False means safe (no freeze authority)
    
    @pytest.mark.asyncio
    async def test_check_freeze_authority_unsafe_token(self):
        """Test freeze authority check for unsafe token"""
        client = AsyncMock()
        
        mock_response = Mock()
        mock_response.value.data.parsed = {
            "info": {"freezeAuthority": "AuthorityAddress"}
        }
        client.get_account_info_json_parsed.return_value = mock_response
        
        result = await entry_daemon.check_freeze_authority(client, "unsafe_mint")
        assert result is True  # True means unsafe (has freeze authority)
    
    @pytest.mark.asyncio
    async def test_check_freeze_authority_error(self):
        """Test freeze authority check error handling"""
        client = AsyncMock()
        client.get_account_info_json_parsed.side_effect = Exception("RPC error")
        
        result = await entry_daemon.check_freeze_authority(client, "error_mint")
        assert result is True  # True means skip on error
    
    @pytest.mark.asyncio
    async def test_get_liquidity_quote_success(self):
        """Test successful liquidity quote"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "outAmount": "1000000",
            "slippageBps": "100"
        }
        
        with patch('requests.get', return_value=mock_response) as mock_get:
            with patch.dict(os.environ, {"QUICKNODE_ENDPOINT": "https://test.com"}):
                result = await entry_daemon.get_liquidity_quote("test_mint")
                
                mock_get.assert_called_once()
                assert result["outAmount"] == "1000000"
    
    @pytest.mark.asyncio
    async def test_get_liquidity_quote_failure(self):
        """Test liquidity quote failure"""
        with patch('requests.get', side_effect=Exception("Network error")):
            with patch.dict(os.environ, {"QUICKNODE_ENDPOINT": "https://test.com"}):
                result = await entry_daemon.get_liquidity_quote("test_mint")
                assert result is None
    
    @pytest.mark.asyncio
    async def test_execute_swap_success(self):
        """Test successful swap execution"""
        quote_data = {"test": "quote"}
        
        # Mock swap response
        mock_swap_response = Mock()
        mock_swap_response.raise_for_status = Mock()
        mock_swap_response.json.return_value = {
            "swapTransaction": "dGVzdF90cmFuc2FjdGlvbg=="  # base64 encoded "test_transaction"
        }
        
        # Mock client
        mock_client = AsyncMock()
        mock_sig = Mock()
        mock_sig.value = "test_signature"
        mock_client.send_raw_transaction.return_value = mock_sig
        
        with patch('requests.post', return_value=mock_swap_response) as mock_post:
            with patch('entry_daemon.base58.b58decode') as mock_b58decode:
                with patch('entry_daemon.Keypair.from_bytes') as mock_keypair:
                    with patch('entry_daemon.VersionedTransaction.from_bytes') as mock_tx:
                        with patch('builtins.bytes') as mock_bytes:
                            with patch('entry_daemon.AsyncClient') as mock_client_class:
                                with patch.dict(os.environ, {
                                    "QUICKNODE_ENDPOINT": "https://test.com",
                                    "WALLET_ADDRESS": "TestWallet",
                                    "WALLET_PRIVATE_KEY": "test_private_key"
                                }):
                                    # Setup async context manager properly
                                    mock_client_class.return_value.__aenter__.return_value = mock_client
                                    mock_client_class.return_value.__aexit__.return_value = None
                                    
                                    mock_b58decode.return_value = b'\x00' * 64
                                    mock_tx_instance = Mock()
                                    mock_tx.return_value = mock_tx_instance
                                    mock_bytes.return_value = b"mock_transaction_bytes"
                                    
                                    result = await entry_daemon.execute_swap(quote_data)
                                    
                                    assert result == "test_signature"
    
    @pytest.mark.asyncio
    async def test_create_limit_order_success(self):
        """Test successful limit order creation"""
        mock_response = Mock()
        mock_response.status_code = 200
        
        with patch('requests.post', return_value=mock_response) as mock_post:
            with patch.dict(os.environ, {
                "QUICKNODE_ENDPOINT": "https://test.com",
                "WALLET_ADDRESS": "TestWallet"
            }):
                with patch('time.time', return_value=1000000):
                    await entry_daemon.create_limit_order("test_mint", 1000000)
                    
                    mock_post.assert_called_once()
                    call_args = mock_post.call_args[1]['json']
                    assert call_args['inputMint'] == "test_mint"
                    assert call_args['params']['makingAmount'] == "1000000"
    
    @pytest.mark.asyncio
    async def test_process_new_token_skip_seen(self):
        """Test processing skips already seen tokens"""
        pool_data = {"tokenAddress": "seen_mint"}
        entry_daemon.seen_pools.add("seen_mint")
        
        client = AsyncMock()
        
        # Should return early without processing
        await entry_daemon.process_new_token(pool_data, client)
        
        # No RPC calls should be made
        client.get_account_info_json_parsed.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_new_token_skip_old(self):
        """Test processing skips old tokens"""
        # Create timestamp that's definitely older than MAX_TOKEN_AGE (3600 seconds = 1 hour)
        old_time = datetime.now(timezone.utc) - timedelta(hours=2)  # 2 hours ago
        old_timestamp = old_time.isoformat().replace('+00:00', 'Z')
        
        pool_data = {
            "tokenAddress": "old_mint",
            "timestamp": old_timestamp
        }
        
        entry_daemon.seen_pools.clear()
        client = AsyncMock()
        
        # Ensure that even if freeze authority is called due to a bug, it behaves properly
        mock_response = Mock()
        mock_response.value = None  # Simulate no account found
        client.get_account_info_json_parsed.return_value = mock_response
        
        # Mock config.max_token_age through environment
        with patch.dict(os.environ, {"MAX_TOKEN_AGE": "3600"}):  # 1 hour
            # Clear config cache to ensure the new environment variable is picked up
            from config import config
            config.clear_cache()
            
            with patch('entry_daemon.get_liquidity_quote') as mock_quote:
                await entry_daemon.process_new_token(pool_data, client)
                
                # Should not call get_liquidity_quote due to age filter
                mock_quote.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_new_token_skip_freeze_authority(self):
        """Test processing skips tokens with freeze authority"""
        recent_time = datetime.now(timezone.utc)
        recent_timestamp = recent_time.isoformat().replace('+00:00', 'Z')
        
        pool_data = {
            "tokenAddress": "freeze_mint",
            "timestamp": recent_timestamp
        }
        
        entry_daemon.seen_pools.clear()
        client = AsyncMock()
        
        # Mock freeze authority check to return True (unsafe)
        mock_response = Mock()
        mock_response.value.data.parsed = {
            "info": {"freezeAuthority": "AuthorityAddress"}
        }
        client.get_account_info_json_parsed.return_value = mock_response
        
        with patch.dict(os.environ, {"MAX_TOKEN_AGE": "86400"}):  # 24 hours
            with patch('entry_daemon.get_liquidity_quote') as mock_quote:
                await entry_daemon.process_new_token(pool_data, client)
                
                # Should not call get_liquidity_quote due to freeze authority
                mock_quote.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_new_token_skip_low_liquidity(self):
        """Test processing skips tokens with low liquidity"""
        recent_time = datetime.now(timezone.utc)
        recent_timestamp = recent_time.isoformat().replace('+00:00', 'Z')
        
        pool_data = {
            "tokenAddress": "lowliq_mint",
            "timestamp": recent_timestamp
        }
        
        entry_daemon.seen_pools.clear()
        client = AsyncMock()
        
        # Mock safe token (no freeze authority)
        mock_response = Mock()
        mock_response.value.data.parsed = {
            "info": {"freezeAuthority": None}
        }
        client.get_account_info_json_parsed.return_value = mock_response
        
        # Mock low liquidity quote
        mock_quote = {"outAmount": "50000"}  # Below threshold
        
        with patch.dict(os.environ, {
            "MAX_TOKEN_AGE": "86400",
            "MIN_LIQUIDITY_THRESHOLD": "100000"
        }):
            with patch('entry_daemon.get_liquidity_quote', return_value=mock_quote):
                with patch('entry_daemon.execute_swap') as mock_swap:
                    await entry_daemon.process_new_token(pool_data, client)
                    
                    # Should not execute swap due to low liquidity
                    mock_swap.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_new_token_success_flow(self):
        """Test successful token processing flow"""
        recent_time = datetime.now(timezone.utc)
        recent_timestamp = recent_time.isoformat().replace('+00:00', 'Z')
        
        pool_data = {
            "tokenAddress": "good_mint",
            "timestamp": recent_timestamp
        }
        
        entry_daemon.seen_pools.clear()
        client = AsyncMock()
        
        # Mock safe token
        mock_response = Mock()
        mock_response.value.data.parsed = {
            "info": {"freezeAuthority": None}
        }
        client.get_account_info_json_parsed.return_value = mock_response
        
        # Mock good liquidity quote
        mock_quote = {"outAmount": "500000"}  # Above threshold
        
        with patch.dict(os.environ, {
            "MAX_TOKEN_AGE": "86400",
            "MIN_LIQUIDITY_THRESHOLD": "100000"
        }):
            with patch('entry_daemon.get_liquidity_quote', return_value=mock_quote):
                with patch('entry_daemon.execute_swap', return_value="tx_sig") as mock_swap:
                    with patch('entry_daemon.create_limit_order') as mock_limit:
                        await entry_daemon.process_new_token(pool_data, client)
                        
                        # Should execute both swap and limit order
                        mock_swap.assert_called_once_with(mock_quote)
                        mock_limit.assert_called_once_with("good_mint", 500000) 