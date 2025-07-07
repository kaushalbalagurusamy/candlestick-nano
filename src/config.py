"""
Configuration management with lazy loading and defaults
Prevents import-time failures when environment variables are missing
"""
import os
from typing import Optional, Union

class Config:
    """Configuration manager with lazy loading"""
    
    def __init__(self):
        self._cache = {}
    
    def get(self, key: str, default: Optional[Union[str, int, float]] = None, 
            cast_type: type = str) -> Union[str, int, float]:
        """Get configuration value with caching and type casting"""
        if key in self._cache:
            return self._cache[key]
        
        value = os.getenv(key, default)
        if value is None:
            raise ValueError(f"Required environment variable {key} is not set")
        
        # Type casting
        if cast_type == int:
            value = int(value)
        elif cast_type == float:
            value = float(value)
        elif cast_type == bool:
            value = value.lower() in ('true', '1', 'yes', 'on')
        
        self._cache[key] = value
        return value
    
    def get_optional(self, key: str, default: Optional[Union[str, int, float]] = None, 
                    cast_type: type = str) -> Optional[Union[str, int, float]]:
        """Get optional configuration value"""
        try:
            return self.get(key, default, cast_type)
        except ValueError:
            return default
    
    def clear_cache(self):
        """Clear cached values (useful for testing)"""
        self._cache.clear()
    
    # Convenience properties for common configurations
    @property
    def quicknode_endpoint(self) -> str:
        return self.get("QUICKNODE_ENDPOINT")
    
    @property
    def jupiter_api_base_url(self) -> str:
        return self.get("JUPITER_API_BASE_URL", "https://quote-api.jup.ag/v6")
    
    @property
    def wallet_address(self) -> str:
        return self.get("WALLET_ADDRESS")
    
    @property
    def wallet_private_key(self) -> str:
        return self.get("WALLET_PRIVATE_KEY")
    
    @property
    def solana_cluster(self) -> str:
        return self.get("SOLANA_CLUSTER", "devnet")
    
    @property
    def min_liquidity_threshold(self) -> int:
        return self.get("MIN_LIQUIDITY_THRESHOLD", 100000, int)
    
    @property
    def max_token_age(self) -> int:
        return self.get("MAX_TOKEN_AGE", 82800, int)  # 23 hours default
    
    @property
    def slippage_bps(self) -> int:
        return self.get("SLIPPAGE_BPS", 100, int)
    
    @property
    def stop_loss_percentage(self) -> float:
        return self.get("STOP_LOSS_PERCENTAGE", 10.0, float)
    
    @property
    def take_profit_percentage(self) -> float:
        return self.get("TAKE_PROFIT_PERCENTAGE", 20.0, float)
    
    @property
    def monitoring_interval(self) -> int:
        return self.get("MONITORING_INTERVAL", 30, int)
    
    @property
    def amount_sol(self) -> float:
        return self.get("AMOUNT_SOL", 1.0, float)
    
    @property
    def chainlink_aggregator(self) -> Optional[str]:
        return self.get_optional("CHAINLINK_AGGREGATOR")

# Global config instance
config = Config()

# Constants
WSOL_MINT = "So11111111111111111111111111111111111111112"
SOL_MINT = WSOL_MINT  # Alias for compatibility 