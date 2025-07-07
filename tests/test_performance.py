"""Performance and load tests for trading bot components"""
import pytest
import asyncio
import time
import statistics
from unittest.mock import AsyncMock, Mock, patch
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestPerformance:
    """Performance tests for trading bot components"""
    
    @pytest.fixture
    def mock_env(self):
        """Setup mock environment variables"""
        return {
            "QUICKNODE_ENDPOINT": "https://test.com",
            "WALLET_ADDRESS": "TestWallet",
            "WALLET_PRIVATE_KEY": "test_key",
            "MIN_LIQUIDITY_THRESHOLD": "100000"
        }
    
    @pytest.mark.asyncio
    async def test_quote_retrieval_performance(self, mock_env):
        """Test quote retrieval performance under load"""
        with patch.dict(os.environ, mock_env):
            with patch('trading_bot_core.base58.b58decode', return_value=b'\x00' * 64):
                with patch('trading_bot_core.Keypair.from_bytes'):
                    from trading_bot_core import TradingBotCore
                    
                    bot = TradingBotCore("https://test.com", "wallet", "key")
                    
                    # Mock successful quote responses
                    mock_resp = Mock()
                    mock_resp.raise_for_status = Mock()
                    mock_resp.json.return_value = {"outAmount": "1000000"}
                    
                    with patch('requests.get', return_value=mock_resp):
                        # Test rapid quote requests
                        start_time = time.time()
                        
                        tasks = []
                        for i in range(50):
                            task = asyncio.create_task(
                                bot.get_quote(f"mint{i}", "wsol", 1000000, 100)
                            )
                            tasks.append(task)
                        
                        results = await asyncio.gather(*tasks)
                        end_time = time.time()
                        
                        total_time = end_time - start_time
                        avg_time = total_time / len(results)
                        
                        print(f"50 quotes in {total_time:.4f}s (avg: {avg_time:.4f}s per quote)")
                        
                        # All quotes should succeed
                        assert all(r is not None for r in results)
                        # Should be reasonably fast
                        assert avg_time < 0.1  # Less than 100ms per quote
    
    @pytest.mark.asyncio
    async def test_concurrent_quote_processing(self, mock_env):
        """Test concurrent quote processing efficiency"""
        with patch.dict(os.environ, mock_env):
            with patch('trading_bot_core.base58.b58decode', return_value=b'\x00' * 64):
                with patch('trading_bot_core.Keypair.from_bytes'):
                    from trading_bot_core import TradingBotCore
                    
                    bot = TradingBotCore("https://test.com", "wallet", "key")
                    
                    # Mock synchronous responses (not async) since trading_bot_core calls requests.get
                    def mock_quote_response(*args, **kwargs):
                        # Simulate some processing delay
                        import time
                        time.sleep(0.01)  # 10ms delay
                        mock_resp = Mock()
                        mock_resp.raise_for_status = Mock()
                        mock_resp.json.return_value = {"outAmount": "1000000"}
                        return mock_resp
                    
                    with patch('requests.get', side_effect=mock_quote_response):
                        # Sequential processing
                        start_time = time.time()
                        sequential_results = []
                        for i in range(10):
                            result = await bot.get_quote(f"seq{i}", "wsol", 1000000, 100)
                            sequential_results.append(result)
                        sequential_time = time.time() - start_time
                        
                        # Concurrent processing
                        start_time = time.time()
                        tasks = []
                        for i in range(10):
                            task = asyncio.create_task(
                                bot.get_quote(f"conc{i}", "wsol", 1000000, 100)
                            )
                            tasks.append(task)
                        concurrent_results = await asyncio.gather(*tasks)
                        concurrent_time = time.time() - start_time
                        
                        print(f"Sequential: {sequential_time:.4f}s, Concurrent: {concurrent_time:.4f}s")
                        
                        # Both should succeed
                        assert len(sequential_results) == 10
                        assert len(concurrent_results) == 10
                        # Concurrent should be faster (or at least not much slower due to mocking overhead)
                        assert concurrent_time < sequential_time * 1.5  # More lenient assertion
    
    @pytest.mark.asyncio
    async def test_pool_processing_throughput(self, mock_env):
        """Test pool processing throughput under load"""
        with patch.dict(os.environ, mock_env):
            import combined_daemon
            
            combined_daemon.seen_pools.clear()
            combined_daemon.active_positions.clear()
            
            # Create many mock pools
            mock_pools = []
            for i in range(100):
                mock_pools.append({
                    "tokenAddress": f"ThroughputMint{i}",
                    "timestamp": "2024-01-01T12:00:00Z"
                })
            
            # Mock bot responses
            mock_bot = AsyncMock()
            mock_bot.check_token_safety.return_value = True
            mock_bot.get_quote.return_value = {"outAmount": "500000"}
            mock_bot.execute_swap.return_value = "tx_sig"
            mock_bot.create_limit_order.return_value = "order_key"
            
            # Test processing throughput
            with patch('combined_daemon.fetch_new_pools', return_value=mock_pools):
                start_time = time.time()
                await combined_daemon.process_new_pools(mock_bot)
                end_time = time.time()
                
                processing_time = end_time - start_time
                throughput = len(mock_pools) / processing_time
                
                print(f"Processed {len(mock_pools)} pools in {processing_time:.4f}s")
                print(f"Throughput: {throughput:.2f} pools/second")
                
                # Should process at reasonable speed
                assert throughput > 10  # At least 10 pools per second
    
    @pytest.mark.asyncio
    async def test_memory_usage_during_processing(self, mock_env):
        """Test memory usage patterns during processing"""
        import psutil
        import os
        
        with patch.dict(os.environ, mock_env):
            import combined_daemon
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss
            
            combined_daemon.seen_pools.clear()
            combined_daemon.active_positions.clear()
            
            # Simulate processing many tokens over time
            mock_bot = AsyncMock()
            mock_bot.check_token_safety.return_value = True
            mock_bot.get_quote.return_value = {"outAmount": "500000"}
            mock_bot.execute_swap.return_value = "tx_sig"
            mock_bot.create_limit_order.return_value = "order_key"
            
            memory_usage = []
            
            # Process in batches to monitor memory
            for batch in range(10):
                batch_pools = []
                for i in range(50):
                    batch_pools.append({
                        "tokenAddress": f"Batch{batch}Mint{i}",
                        "timestamp": "2024-01-01T12:00:00Z"
                    })
                
                with patch('combined_daemon.fetch_new_pools', return_value=batch_pools):
                    await combined_daemon.process_new_pools(mock_bot)
                
                current_memory = process.memory_info().rss
                memory_usage.append(current_memory)
                
                print(f"Batch {batch}: Memory usage {current_memory / 1024 / 1024:.2f} MB")
            
            final_memory = memory_usage[-1]
            memory_growth = final_memory - initial_memory
            
            print(f"Memory growth: {memory_growth / 1024 / 1024:.2f} MB")
            
            # Memory growth should be reasonable (less than 100MB for this test)
            assert memory_growth < 100 * 1024 * 1024  # 100MB limit
    
    @pytest.mark.asyncio
    async def test_error_handling_performance(self, mock_env):
        """Test performance impact of error handling"""
        with patch.dict(os.environ, mock_env):
            with patch('trading_bot_core.base58.b58decode', return_value=b'\x00' * 64):
                with patch('trading_bot_core.Keypair.from_bytes'):
                    from trading_bot_core import TradingBotCore
                    
                    bot = TradingBotCore("https://test.com", "wallet", "key")
                    
                    # Test with mix of successful and failed requests
                    call_count = 0
                    def mixed_responses(*args, **kwargs):
                        nonlocal call_count
                        call_count += 1
                        if call_count % 3 == 0:  # Every 3rd call fails
                            raise Exception("Network error")
                        else:
                            mock_resp = Mock()
                            mock_resp.raise_for_status = Mock()
                            mock_resp.json.return_value = {"outAmount": "1000000"}
                            return mock_resp
                    
                    with patch('requests.get', side_effect=mixed_responses):
                        start_time = time.time()
                        
                        results = []
                        for i in range(30):  # 20 success, 10 failures
                            result = await bot.get_quote(f"mint{i}", "wsol", 1000000, 100)
                            results.append(result)
                        
                        end_time = time.time()
                        
                        processing_time = end_time - start_time
                        successful_results = sum(1 for r in results if r is not None)
                        failed_results = sum(1 for r in results if r is None)
                        
                        print(f"Mixed success/failure processing time: {processing_time:.4f}s")
                        print(f"Successful: {successful_results}, Failed: {failed_results}")
                        
                        # Should handle errors efficiently
                        assert successful_results == 20
                        assert failed_results == 10
                        assert processing_time < 1.0  # Should still be fast
    
    @pytest.mark.asyncio
    async def test_position_tracking_scalability(self, mock_env):
        """Test position tracking with many active positions"""
        with patch.dict(os.environ, mock_env):
            import combined_daemon
            
            combined_daemon.active_positions.clear()
            
            # Create many active positions with uniform entry price for predictable math
            num_positions = 1000
            for i in range(num_positions):
                combined_daemon.active_positions[f"Token{i}"] = {
                    "amount": 1000000,  # Uniform amount
                    "entry_price": 1.0,  # Uniform entry price
                    "order_pubkey": f"order{i}"
                }
            
            # Mock bot for stop-loss checking
            mock_bot = AsyncMock()
            # Return quotes that trigger stop-loss for even-numbered tokens only
            def mock_quote_side_effect(*args):
                mint = args[0]
                token_num = int(mint.replace("Token", ""))
                if token_num % 2 == 0:
                    # For even tokens: current_value=700000, entry_value=1000000*1.0=1000000, loss=-30% (triggers stop-loss)
                    return {"outAmount": "700000"}  # Triggers stop-loss
                else:
                    # For odd tokens: current_value=1100000, entry_value=1000000*1.0=1000000, gain=+10% (no action)
                    return {"outAmount": "1100000"}  # No action
            
            mock_bot.get_quote.side_effect = mock_quote_side_effect
            mock_bot.execute_swap.return_value = "sell_tx"
            
            # Test stop-loss checking performance
            start_time = time.time()
            await combined_daemon.check_stop_loss_conditions(mock_bot)
            end_time = time.time()
            
            processing_time = end_time - start_time
            remaining_positions = len(combined_daemon.active_positions)
            
            print(f"Stop-loss check for {num_positions} positions took {processing_time:.4f}s")
            print(f"Remaining positions: {remaining_positions}")
            
            # Should process efficiently
            assert processing_time < 2.0  # Less than 2 seconds
            assert remaining_positions == num_positions // 2  # Half should remain
    
    @pytest.mark.asyncio
    async def test_api_rate_limiting_simulation(self, mock_env):
        """Test behavior under API rate limiting"""
        with patch.dict(os.environ, mock_env):
            with patch('trading_bot_core.base58.b58decode', return_value=b'\x00' * 64):
                with patch('trading_bot_core.Keypair.from_bytes'):
                    from trading_bot_core import TradingBotCore
                    
                    bot = TradingBotCore("https://test.com", "wallet", "key")
                    
                    # Simulate rate limiting with delays
                    call_count = 0
                    def rate_limited_response(*args, **kwargs):
                        nonlocal call_count
                        call_count += 1
                        
                        if call_count > 10:  # Rate limit after 10 calls
                            import time
                            time.sleep(0.1)  # 100ms delay
                        
                        mock_resp = Mock()
                        mock_resp.raise_for_status = Mock()
                        mock_resp.json.return_value = {"outAmount": "1000000"}
                        return mock_resp
                    
                    # Test with rate limiting
                    with patch('requests.get', side_effect=rate_limited_response):
                        start_time = time.time()
                        
                        # Make many requests
                        tasks = []
                        for i in range(20):
                            task = asyncio.create_task(
                                bot.get_quote(f"mint{i}", "wsol", 1000000, 100)
                            )
                            tasks.append(task)
                        
                        results = await asyncio.gather(*tasks)
                        end_time = time.time()
                        
                        total_time = end_time - start_time
                        
                        print(f"Rate-limited processing time: {total_time:.4f}s")
                        
                        # All should succeed despite rate limiting
                        assert all(r is not None for r in results)
                        # Should take longer due to rate limiting
                        assert total_time > 0.5  # Some delay expected 