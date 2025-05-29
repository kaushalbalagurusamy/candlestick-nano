"""Test QuickNode Métis API integration"""
import os
import pytest
import asyncio
import requests
from solana.rpc.async_api import AsyncClient
from unittest.mock import patch, MagicMock

# Import our modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.entry_daemon import fetch_new_pools, check_freeze_authority
from src.exit_daemon import get_open_limit_orders

QN = os.getenv("QUICKNODE_ENDPOINT", "https://test-endpoint")

class TestMetisIntegration:
    """Test QuickNode Métis API endpoints"""
    
    @pytest.mark.asyncio
    async def test_new_pools_endpoint(self):
        """Test /new-pools endpoint connectivity"""
        with patch('requests.get') as mock_get:
            # Mock response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": [
                    {
                        "tokenAddress": "TestToken123",
                        "timestamp": "2024-01-20T12:00:00Z",
                        "exchange": "pump.fun"
                    }
                ]
            }
            mock_get.return_value = mock_response
            
            # Test function
            from src.entry_daemon import fetch_new_pools
            pools = await fetch_new_pools()
            
            assert len(pools) == 1
            assert pools[0]["tokenAddress"] == "TestToken123"
            mock_get.assert_called_with(f"{QN}/new-pools")
    
    @pytest.mark.asyncio
    async def test_freeze_authority_check(self):
        """Test freeze authority detection"""
        async with AsyncClient("https://api.devnet.solana.com") as client:
            # Test with a known safe token (USDC on devnet)
            safe_mint = "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"
            
            with patch.object(client, 'get_account_info_json_parsed') as mock_get:
                # Mock safe token response
                mock_response = MagicMock()
                mock_response.value.data.parsed = {
                    "info": {
                        "freezeAuthority": None
                    }
                }
                mock_get.return_value = mock_response
                
                is_safe = await check_freeze_authority(client, safe_mint)
                assert is_safe is False  # No freeze authority = safe
    
    @pytest.mark.asyncio
    async def test_quote_endpoint(self):
        """Test /quote endpoint"""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "outAmount": "1000000",
                "slippageBps": "100",
                "priceImpactPct": "0.01"
            }
            mock_get.return_value = mock_response
            
            from src.entry_daemon import get_liquidity_quote
            quote = await get_liquidity_quote("TestMint")
            
            assert quote is not None
            assert quote["outAmount"] == "1000000"
    
    @pytest.mark.asyncio
    async def test_limit_orders_endpoint(self):
        """Test /limit-orders/open endpoint"""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "orders": [
                    {
                        "pubkey": "Order123",
                        "inputMint": "TokenA",
                        "outputMint": "So11111111111111111111111111111111111111112",
                        "makingAmount": "1000000"
                    }
                ]
            }
            mock_get.return_value = mock_response
            
            orders = await get_open_limit_orders()
            
            assert len(orders) == 1
            assert orders[0]["pubkey"] == "Order123"

    def test_environment_variables(self):
        """Test required environment variables"""
        required_vars = [
            "QUICKNODE_ENDPOINT",
            "WALLET_ADDRESS", 
            "WALLET_PRIVATE_KEY",
            "MIN_LIQUIDITY_THRESHOLD",
            "STOP_LOSS_PERCENTAGE"
        ]
        
        # Check if sample env file has all required vars
        with open("config/.envrc.sample", "r") as f:
            content = f.read()
            
        for var in required_vars:
            assert f"export {var}=" in content, f"Missing {var} in config/.envrc.sample"

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 