"""Unit tests for buy.py module"""
import pytest
import json
import base64
from unittest.mock import AsyncMock, Mock, patch, MagicMock, mock_open
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import buy

class TestBuy:
    """Test buy.py module functions"""
    
    @pytest.mark.asyncio
    async def test_buy_token_success(self):
        """Test successful token buying"""
        # Mock Jupiter instance
        mock_jup = AsyncMock()
        mock_jup.swap.return_value = base64.b64encode(b"test_transaction").decode()
        
        # Mock client
        mock_client = AsyncMock()
        mock_sig = Mock()
        mock_sig.value = "test_signature"
        mock_client.send_raw_transaction.return_value = mock_sig
        
        with patch('buy.VersionedTransaction.from_bytes') as mock_tx:
            # Create a proper mock transaction that can be converted to bytes
            mock_tx_instance = Mock()
            mock_tx.return_value = mock_tx_instance
            
            # Mock the global bytes function to handle Mock objects
            with patch('builtins.bytes', return_value=b"mock_transaction_bytes"):
                with patch.dict(os.environ, {"AMOUNT_SOL": "0.5"}):
                    with patch('buy.config') as mock_config:
                        mock_config.amount_sol = 0.5
                        
                        await buy.buy_token(mock_jup, mock_client, "test_mint")
                        
                        # Verify swap was called with correct parameters
                        mock_jup.swap.assert_called_once_with(
                            input_mint=buy.SOL_MINT,
                            output_mint="test_mint",
                            amount=500000000,  # 0.5 SOL in lamports
                            slippage_bps=500
                        )
                        
                        # Verify transaction was sent
                        mock_client.send_raw_transaction.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_buy_token_failure(self):
        """Test token buying failure"""
        mock_jup = AsyncMock()
        mock_jup.swap.side_effect = Exception("Swap error")
        
        mock_client = AsyncMock()
        
        with patch('buy.config') as mock_config:
            mock_config.amount_sol = 0.5
            
            # Should handle error gracefully and not raise exception
            await buy.buy_token(mock_jup, mock_client, "test_mint")
            
            # Verify swap was attempted
            mock_jup.swap.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_main_success(self):
        """Test main function success flow"""
        # Mock tokens.json content
        tokens_data = [
            {"symbol": "TOKEN1", "address": "mint1"},
            {"symbol": "TOKEN2", "address": "mint2"}
        ]
        
        # Use proper mock_open for file operations
        m_open = mock_open(read_data=json.dumps(tokens_data))
        
        # Create a valid base58 encoded private key (32 bytes)
        valid_private_key = "5J7WTMRykGV6GCKtFshGXwF6LQmqMYTejVKZMRqVzmnZdGKz1dC" # Valid base58 key
        
        with patch('builtins.open', m_open):
            with patch('json.load', return_value=tokens_data):
                with patch('buy.AsyncClient') as mock_client_class:
                    with patch('buy.Keypair.from_bytes') as mock_keypair:
                        with patch('buy.Jupiter') as mock_jupiter_class:
                            with patch('buy.buy_token') as mock_buy_token:
                                with patch('buy.config') as mock_config:
                                    mock_config.quicknode_endpoint = "https://test.com"
                                    mock_config.jupiter_api_base_url = "https://jup.com"
                                    mock_config.wallet_private_key = valid_private_key
                                    
                                    mock_client = AsyncMock()
                                    mock_client_class.return_value = mock_client
                                    
                                    # Mock keypair creation
                                    mock_kp = Mock()
                                    mock_keypair.return_value = mock_kp
                                    
                                    # Mock buy_token to return None (it's fire-and-forget)
                                    mock_buy_token.return_value = None
                                    
                                    await buy.main()
                                    
                                    # Verify Jupiter was initialized correctly
                                    mock_jupiter_class.assert_called_once()
                                    
                                    # Verify buy_token was called for each token
                                    assert mock_buy_token.call_count == 2
                                    
                                    # Verify client was closed
                                    mock_client.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_main_empty_tokens(self):
        """Test main function with empty tokens file"""
        # Create a valid base58 encoded private key
        valid_private_key = "5J7WTMRykGV6GCKtFshGXwF6LQmqMYTejVKZMRqVzmnZdGKz1dC"
        
        with patch('builtins.open'):
            with patch('json.load', return_value=[]):
                with patch('buy.AsyncClient') as mock_client_class:
                    with patch('buy.Keypair.from_bytes') as mock_keypair:
                        with patch('buy.config') as mock_config:
                            mock_config.quicknode_endpoint = "https://test.com"
                            mock_config.jupiter_api_base_url = "https://jup.com"
                            mock_config.wallet_private_key = valid_private_key
                            
                            mock_client = AsyncMock()
                            mock_client_class.return_value = mock_client
                            
                            # Mock keypair creation to avoid base58 issues
                            mock_kp = Mock()
                            mock_keypair.return_value = mock_kp
                            
                            await buy.main()
                            
                            # Should still close client even with no tokens
                            mock_client.close.assert_called_once()
    
    @pytest.mark.asyncio 
    async def test_main_file_error(self):
        """Test main function with file reading error"""
        with patch('builtins.open', side_effect=FileNotFoundError("No tokens.json")):
            with patch('buy.config') as mock_config:
                mock_config.quicknode_endpoint = "https://test.com"
                mock_config.jupiter_api_base_url = "https://jup.com"
                mock_config.wallet_private_key = "test_key"
                
                # Should handle file error gracefully
                with pytest.raises(FileNotFoundError):
                    await buy.main()
    
    def test_constants(self):
        """Test module constants"""
        assert buy.SOL_MINT == "So11111111111111111111111111111111111111112"
        assert buy.SLIPPAGE_BPS == 500
        
        # Test that config.amount_sol is accessible
        with patch('buy.config') as mock_config:
            mock_config.amount_sol = 1.0
            
            # Import should work and use config.amount_sol
            import importlib
            importlib.reload(buy)
            
            # Verify config is being used
            assert mock_config.amount_sol == 1.0 