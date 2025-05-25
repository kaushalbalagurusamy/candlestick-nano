# exit_utils.py
import json
import requests
from websocket import create_connection

async def get_open_limit_orders(endpoint: str, wallet_address: str):
    """Fetch all open limit orders for the wallet"""
    try:
        response = requests.get(
            f"{endpoint}/limit-orders/open",
            params={"wallet": wallet_address}
        )
        response.raise_for_status()
        return response.json().get("orders", [])
    except Exception as e:
        print(f"Error fetching open orders: {e}")
        return []

async def cancel_limit_order_request(endpoint: str, wallet_address: str, order_pubkey: str):
    """Get cancel transaction for a limit order"""
    try:
        response = requests.post(
            f"{endpoint}/limit-orders/cancel",
            json={
                "owner": wallet_address,
                "orderPubkey": order_pubkey
            }
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error getting cancel transaction: {e}")
        return None

async def get_market_sell_quote(endpoint: str, mint: str, wsol_mint: str, amount: int):
    """Get quote for market sell"""
    try:
        params = {
            "inputMint": mint,
            "outputMint": wsol_mint,
            "amount": str(amount),
            "slippageBps": "500"  # 5% slippage for emergency sells
        }
        quote_response = requests.get(f"{endpoint}/quote", params=params)
        quote_response.raise_for_status()
        return quote_response.json()
    except Exception as e:
        print(f"Error getting sell quote: {e}")
        return None

async def get_swap_transaction(endpoint: str, wallet_address: str, quote_data: dict):
    """Get swap transaction from quote"""
    try:
        swap_response = requests.post(
            f"{endpoint}/swap",
            json={
                "owner": wallet_address,
                "quoteResponse": quote_data
            }
        )
        swap_response.raise_for_status()
        return swap_response.json()
    except Exception as e:
        print(f"Error getting swap transaction: {e}")
        return None

def create_websocket_connection(endpoint: str):
    """Create WebSocket connection for price monitoring"""
    try:
        ws_url = endpoint.replace("https", "wss")
        ws = create_connection(ws_url)
        return ws
    except Exception as e:
        print(f"Error creating WebSocket connection: {e}")
        return None

def subscribe_to_chainlink_logs(ws, aggregator_address: str):
    """Subscribe to Chainlink aggregator logs"""
    subscribe_msg = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "logs_subscribe",
        "params": [{
            "mentions": [aggregator_address]
        }]
    })
    ws.send(subscribe_msg) 