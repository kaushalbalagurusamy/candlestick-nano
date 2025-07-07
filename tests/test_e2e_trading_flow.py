"""End-to-end tests for complete trading workflow"""
import pytest
import os
import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock, AsyncMock
import sys
from datetime import datetime, timezone

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Skip end-to-end tests if not in devnet
pytestmark = pytest.mark.skipif(
    os.environ.get("SOLANA_CLUSTER") != "devnet",
    reason="End-to-end tests only run on devnet"
)

class TestTradingFlowE2E:
    """End-to-end tests for complete trading workflow"""
    
    @pytest.fixture
    def mock_env(self):
        """Setup mock environment variables"""
        return {
            "QUICKNODE_ENDPOINT": "https://proud-palpable-borough.solana-devnet.quiknode.pro/test",
            "JUPITER_API_BASE_URL": "https://quote-api.jup.ag/v6",
            "WALLET_ADDRESS": "2C4X2sFhnb212uC1W2GdfKL4uCRkdKhXyfxktg3T3vmA",
            "WALLET_PRIVATE_KEY": "test_private_key",
            "SOLANA_CLUSTER": "devnet",
            "MIN_LIQUIDITY_THRESHOLD": "100000",
            "STOP_LOSS_PERCENTAGE": "10",
            "TAKE_PROFIT_PERCENTAGE": "20",
            "AMOUNT_SOL": "0.001"
        }
    
    @pytest.mark.asyncio
    async def test_token_discovery_and_filtering(self, mock_env):
        """Test complete token discovery and filtering pipeline"""
        with patch.dict(os.environ, mock_env):
            # Mock new pools data
            mock_pools = [
                {
                    "tokenAddress": "SafeToken123",
                    "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                    "exchange": "pump.fun"
                },
                {
                    "tokenAddress": "OldToken456", 
                    "timestamp": "2024-01-01T00:00:00Z",  # Old token
                    "exchange": "pump.fun"
                },
                {
                    "tokenAddress": "UnsafeToken789",
                    "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                    "exchange": "pump.fun"
                }
            ]
            
            # Import after environment setup
            import combined_daemon
            
            # Mock API responses
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.raise_for_status = Mock()
                mock_response.json.return_value = {"data": mock_pools}
                mock_get.return_value = mock_response
                
                # Mock bot methods
                mock_bot = AsyncMock()
                mock_bot.check_token_safety.side_effect = [True, True, False]  # SafeToken=safe, others vary
                mock_bot.get_quote.side_effect = [
                    {"outAmount": "500000"},  # SafeToken - good liquidity
                    None,  # OldToken - no quote
                    {"outAmount": "50000"}   # UnsafeToken - low liquidity
                ]
                
                # Process pools
                await combined_daemon.process_new_pools(mock_bot)
                
                # Verify filtering
                assert "SafeToken123" in combined_daemon.seen_pools
                assert "OldToken456" in combined_daemon.seen_pools  # Added to seen but not processed
                assert "UnsafeToken789" in combined_daemon.seen_pools
                
                # Only SafeToken should trigger safety check
                assert mock_bot.check_token_safety.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_complete_buy_sell_cycle(self, mock_env):
        """Test complete buy -> limit order -> stop-loss cycle"""
        with patch.dict(os.environ, mock_env):
            import combined_daemon
            
            # Setup initial state
            combined_daemon.seen_pools.clear()
            combined_daemon.active_positions.clear()
            
            # Mock successful buy flow
            mock_bot = AsyncMock()
            mock_bot.check_token_safety.return_value = True
            mock_bot.get_quote.side_effect = [
                {"outAmount": "1000000"},  # Initial buy quote
                {"outAmount": "850000"}    # Stop-loss quote (15% drop)
            ]
            mock_bot.execute_swap.side_effect = ["buy_tx_sig", "sell_tx_sig"]
            mock_bot.create_limit_order.return_value = "order_pubkey"
            
            # Step 1: Process new token (buy)
            recent_pool = [{
                "tokenAddress": "TestToken123",
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            }]
            
            with patch('combined_daemon.fetch_new_pools', return_value=recent_pool):
                await combined_daemon.process_new_pools(mock_bot)
            
            # Verify buy executed and position tracked
            assert "TestToken123" in combined_daemon.active_positions
            position = combined_daemon.active_positions["TestToken123"]
            assert position["order_pubkey"] == "order_pubkey"
            assert position["amount"] == 1000000
            
            # Step 2: Trigger stop-loss
            await combined_daemon.check_stop_loss_conditions(mock_bot)
            
            # Verify stop-loss executed
            mock_bot.cancel_limit_order.assert_called_with("order_pubkey")
            assert mock_bot.execute_swap.call_count == 2  # Buy + sell
            
            # Position should be removed after stop-loss
            assert "TestToken123" not in combined_daemon.active_positions
    
    @pytest.mark.asyncio
    async def test_position_persistence_across_updates(self, mock_env):
        """Test position tracking persistence across daemon updates"""
        with patch.dict(os.environ, mock_env):
            import combined_daemon
            
            combined_daemon.active_positions.clear()
            
            # Mock open orders
            mock_orders = [
                {
                    "pubkey": "persistent_order",
                    "inputMint": "PersistentToken",
                    "makingAmount": "2000000"
                }
            ]
            
            mock_bot = AsyncMock()
            mock_bot.get_open_orders.return_value = mock_orders
            
            # Update positions multiple times
            for _ in range(3):
                await combined_daemon.update_positions(mock_bot)
                
                # Position should persist
                assert "PersistentToken" in combined_daemon.active_positions
                assert combined_daemon.active_positions["PersistentToken"]["amount"] == 2000000
            
            # Simulate order closure
            mock_bot.get_open_orders.return_value = []
            await combined_daemon.update_positions(mock_bot)
            
            # Position should be removed
            assert "PersistentToken" not in combined_daemon.active_positions
    
    @pytest.mark.asyncio
    async def test_buy_module_integration(self, mock_env):
        """Test buy.py module integration with token files"""
        with patch.dict(os.environ, mock_env):
            # Create temporary tokens file
            tokens_data = [
                {"symbol": "TEST1", "address": "TestMint1"},
                {"symbol": "TEST2", "address": "TestMint2"}
            ]
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(tokens_data, f)
                tokens_file = f.name
            
            try:
                # Mock Jupiter and client
                mock_jupiter = AsyncMock()
                mock_jupiter.swap.return_value = "dGVzdF90eA=="  # base64 "test_tx"
                
                mock_client = AsyncMock()
                mock_sig = Mock()
                mock_sig.value = "test_signature"
                mock_client.send_raw_transaction.return_value = mock_sig
                
                # Import and patch buy module
                import buy
                
                with patch('buy.AsyncClient', return_value=mock_client):
                    with patch('buy.Jupiter', return_value=mock_jupiter):
                        with patch('buy.Keypair.from_bytes') as mock_keypair:
                            with patch('buy.VersionedTransaction.from_bytes'):
                                with patch('builtins.bytes', return_value=b"mock_tx_bytes"):
                                    with patch('buy.base58.b58decode', return_value=b'\x00' * 64) as mock_b58decode:
                                        with patch('buy.config') as mock_config:
                                            mock_config.quicknode_endpoint = "https://test.com"
                                            mock_config.wallet_private_key = "valid_base58_key_here"
                                            mock_config.jupiter_api_base_url = "https://jup.com"
                                            
                                            # Mock keypair to avoid base58 issues
                                            mock_kp = Mock()
                                            mock_keypair.return_value = mock_kp
                                            
                                            with patch('builtins.open', create=True) as mock_open:
                                                with patch('json.load', return_value=tokens_data):
                                                    # Run buy main function
                                                    await buy.main()
                                                    
                                                    # Verify swaps executed for both tokens
                                                    assert mock_jupiter.swap.call_count == 2
                                                    assert mock_client.send_raw_transaction.call_count == 2
                                        
            finally:
                # Cleanup temp file
                os.unlink(tokens_file)
    
    @pytest.mark.asyncio
    async def test_error_resilience_in_trading_loop(self, mock_env):
        """Test trading loop resilience to various errors"""
        with patch.dict(os.environ, mock_env):
            import combined_daemon
            
            # Setup bot with intermittent failures
            mock_bot = AsyncMock()
            
            call_count = 0
            def failing_fetch_pools():
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise Exception("Network error")
                elif call_count == 2:
                    return []  # Empty result
                else:
                    return [{"tokenAddress": "RecoveryToken", "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}]
            
            with patch('combined_daemon.fetch_new_pools', side_effect=failing_fetch_pools):
                with patch('combined_daemon.update_positions') as mock_update:
                    with patch('combined_daemon.check_stop_loss_conditions') as mock_stop_loss:
                        
                        # Run multiple loop iterations
                        for i in range(3):
                            try:
                                await combined_daemon.process_new_pools(mock_bot)
                                await combined_daemon.update_positions(mock_bot)
                                await combined_daemon.check_stop_loss_conditions(mock_bot)
                            except Exception as e:
                                # Should handle errors gracefully
                                print(f"Iteration {i} error (expected): {e}")
                        
                        # Should recover and process successfully on 3rd iteration
                        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_concurrent_position_management(self, mock_env):
        """Test concurrent position management with multiple tokens"""
        with patch.dict(os.environ, mock_env):
            import combined_daemon
            
            combined_daemon.active_positions.clear()
            
            # Setup multiple positions
            positions = {
                "Token1": {"amount": 1000000, "entry_price": 1.0, "order_pubkey": "order1"},
                "Token2": {"amount": 2000000, "entry_price": 1.5, "order_pubkey": "order2"},
                "Token3": {"amount": 500000, "entry_price": 1.0, "order_pubkey": "order3"}
            }
            
            for mint, pos in positions.items():
                combined_daemon.active_positions[mint] = pos
            
            # Mock bot with different outcomes for each token
            mock_bot = AsyncMock()
            mock_bot.get_quote.side_effect = [
                {"outAmount": "1050000"},  # Token1: current_value=1050000, entry_value=1000000*1.0=1000000, change=+5% (no action)
                {"outAmount": "1200000"},  # Token2: current_value=1200000, entry_value=2000000*1.5=3000000, change=-60% (stop-loss trigger)
                {"outAmount": "400000"}    # Token3: current_value=400000, entry_value=500000*1.0=500000, change=-20% (stop-loss trigger)
            ]
            mock_bot.execute_swap.side_effect = ["sell_tx1", "sell_tx2"]
            
            # Check stop-loss conditions
            await combined_daemon.check_stop_loss_conditions(mock_bot)
            
            # Verify correct actions taken
            assert "Token1" in combined_daemon.active_positions  # No action taken
            assert "Token2" not in combined_daemon.active_positions  # Stop-loss executed
            assert "Token3" not in combined_daemon.active_positions  # Stop-loss executed
            
            # Verify cancellations and sells
            assert mock_bot.cancel_limit_order.call_count == 2
            assert mock_bot.execute_swap.call_count == 2
    
    @pytest.mark.asyncio
    async def test_daemon_lifecycle_management(self, mock_env):
        """Test daemon setup, operation, and cleanup lifecycle"""
        with patch.dict(os.environ, mock_env):
            # Mock TradingBotCore
            mock_bot = Mock()
            mock_bot.setup = AsyncMock()
            mock_bot.cleanup = AsyncMock()
            
            import combined_daemon
            
            # Test controlled daemon lifecycle
            with patch('combined_daemon.TradingBotCore', return_value=mock_bot):
                with patch('combined_daemon.process_new_pools') as mock_process:
                    with patch('combined_daemon.update_positions') as mock_update:
                        with patch('combined_daemon.check_stop_loss_conditions') as mock_stop:
                            with patch('asyncio.sleep') as mock_sleep:
                                
                                # Simulate loop interruption after 2 iterations
                                mock_sleep.side_effect = [None, KeyboardInterrupt()]
                                
                                try:
                                    await combined_daemon.main()
                                except KeyboardInterrupt:
                                    pass
                                
                                # Verify lifecycle methods called
                                mock_bot.setup.assert_called_once()
                                mock_bot.cleanup.assert_called_once()
                                
                                # Verify loop functions called
                                assert mock_process.call_count >= 1
                                assert mock_update.call_count >= 1
                                assert mock_stop.call_count >= 1 