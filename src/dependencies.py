"""
Dependency injection container for better testability
"""
from typing import Protocol, Optional, Dict, Any
from dataclasses import dataclass
from config import config

class ClientProtocol(Protocol):
    """Protocol for Solana RPC client"""
    async def setup(self): ...
    async def cleanup(self): ...
    async def get_quote(self, input_mint: str, output_mint: str, amount: int, slippage_bps: int) -> Optional[Dict]: ...
    async def execute_swap(self, quote_data: Dict) -> Optional[str]: ...
    async def check_token_safety(self, mint: str) -> bool: ...
    async def create_limit_order(self, mint: str, amount: int, profit_percentage: float) -> Optional[str]: ...
    async def get_open_orders(self) -> list: ...
    async def cancel_limit_order(self, order_pubkey: str) -> Optional[str]: ...

class HTTPClientProtocol(Protocol):
    """Protocol for HTTP client"""
    def get(self, url: str, **kwargs) -> Any: ...
    def post(self, url: str, **kwargs) -> Any: ...

class ConfigProtocol(Protocol):
    """Protocol for configuration"""
    @property
    def quicknode_endpoint(self) -> str: ...
    @property
    def wallet_address(self) -> str: ...
    @property
    def wallet_private_key(self) -> str: ...
    @property
    def min_liquidity_threshold(self) -> int: ...
    @property
    def max_token_age(self) -> int: ...
    @property
    def slippage_bps(self) -> int: ...
    @property
    def stop_loss_percentage(self) -> float: ...
    @property
    def take_profit_percentage(self) -> float: ...
    @property
    def monitoring_interval(self) -> int: ...

@dataclass
class Dependencies:
    """Dependency container"""
    config: ConfigProtocol
    trading_client: Optional[ClientProtocol] = None
    http_client: Optional[HTTPClientProtocol] = None
    
    def __post_init__(self):
        """Initialize default dependencies if not provided"""
        if self.http_client is None:
            import requests
            self.http_client = requests
            
        if self.trading_client is None:
            # Only create real TradingBotCore if config looks real
            # (not a mock and has valid private key format)
            try:
                # Check if this looks like a real config
                endpoint = self.config.quicknode_endpoint
                address = self.config.wallet_address  
                private_key = self.config.wallet_private_key
                
                # Simple validation - if any look like mocks, skip creation
                if (isinstance(endpoint, str) and endpoint.startswith("http") and
                    isinstance(address, str) and len(address) > 10 and
                    isinstance(private_key, str) and len(private_key) > 10):
                    
                    from trading_bot_core import TradingBotCore
                    self.trading_client = TradingBotCore(endpoint, address, private_key)
                
            except Exception:
                # If anything fails during validation, leave trading_client as None
                pass

class DependencyContainer:
    """Singleton dependency container"""
    _instance: Optional['DependencyContainer'] = None
    _dependencies: Optional[Dependencies] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def configure(self, dependencies: Dependencies):
        """Configure the container with dependencies"""
        self._dependencies = dependencies
    
    def get_dependencies(self) -> Dependencies:
        """Get the configured dependencies"""
        if self._dependencies is None:
            # Use default configuration
            self._dependencies = Dependencies(config=config)
        return self._dependencies
    
    def reset(self):
        """Reset container (useful for testing)"""
        self._dependencies = None

# Global container instance
container = DependencyContainer()

def get_deps() -> Dependencies:
    """Convenience function to get dependencies"""
    return container.get_dependencies()

def configure_deps(config_override=None, **kwargs):
    """Convenience function to configure dependencies"""
    deps = Dependencies(config=config_override or config, **kwargs)
    container.configure(deps) 