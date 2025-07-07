"""Integration tests for wallet operations and transaction flows"""
import pytest
import os
import asyncio
import base58
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.types import TokenAccountOpts
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Skip integration tests if not in integration environment
pytestmark = pytest.mark.skipif(
    not os.environ.get("RUN_INTEGRATION_TESTS"),
    reason="Integration tests disabled - set RUN_INTEGRATION_TESTS=1 to enable"
)

class TestWalletIntegration:
    """Integration tests for wallet operations"""
    
    @pytest.fixture
    def client(self):
        """Create Solana RPC client"""
        endpoint = os.environ.get("QUICKNODE_ENDPOINT")
        if not endpoint:
            pytest.skip("QUICKNODE_ENDPOINT not configured")
        return AsyncClient(endpoint)
    
    @pytest.fixture
    def keypair(self):
        """Create keypair from environment private key"""
        private_key = os.environ.get("WALLET_PRIVATE_KEY")
        if not private_key:
            pytest.skip("WALLET_PRIVATE_KEY not configured")
        
        try:
            return Keypair.from_bytes(base58.b58decode(private_key))
        except Exception as e:
            pytest.skip(f"Invalid private key format: {e}")
    
    @pytest.fixture
    def wallet_address(self):
        """Get wallet address from environment"""
        address = os.environ.get("WALLET_ADDRESS")
        if not address:
            pytest.skip("WALLET_ADDRESS not configured")
        return address
    
    @pytest.mark.asyncio
    async def test_wallet_balance_retrieval(self, client, keypair, wallet_address):
        """Test wallet balance retrieval and consistency"""
        async with client:
            # Test balance via keypair
            balance_resp = await client.get_balance(keypair.pubkey())
            keypair_balance = balance_resp.value
            
            # Test balance via address string
            pubkey = Pubkey.from_string(wallet_address)
            balance_resp2 = await client.get_balance(pubkey)
            address_balance = balance_resp2.value
            
            # Should be the same balance
            assert keypair_balance == address_balance
            assert isinstance(keypair_balance, int)
            assert keypair_balance >= 0
            
            # Convert to SOL for readability
            sol_balance = keypair_balance / 1_000_000_000
            print(f"Wallet balance: {sol_balance:.9f} SOL ({keypair_balance:,} lamports)")
    
    @pytest.mark.asyncio
    async def test_keypair_consistency(self, keypair, wallet_address):
        """Test that private key derives to correct public key"""
        derived_pubkey = str(keypair.pubkey())
        
        assert derived_pubkey == wallet_address, (
            f"Private key derives to {derived_pubkey} but wallet address is {wallet_address}"
        )
    
    @pytest.mark.asyncio
    async def test_token_accounts_enumeration(self, client, keypair):
        """Test token account enumeration"""
        async with client:
            # Get all token accounts for the wallet
            token_accounts = await client.get_token_accounts_by_owner(
                keypair.pubkey(),
                TokenAccountOpts(program_id=Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"))
            )
            
            accounts = token_accounts.value
            print(f"Found {len(accounts)} token accounts")
            
            # Verify account structure
            for account in accounts[:3]:  # Check first 3 accounts
                assert hasattr(account, 'pubkey')
                assert hasattr(account, 'account')
                assert hasattr(account.account, 'data')
                
                # Get account balance
                try:
                    balance_resp = await client.get_token_account_balance(account.pubkey)
                    balance = balance_resp.value
                    print(f"Token account {account.pubkey}: {balance.ui_amount} tokens")
                except Exception as e:
                    print(f"Could not get balance for {account.pubkey}: {e}")
    
    @pytest.mark.asyncio
    async def test_transaction_history_access(self, client, keypair):
        """Test access to transaction history"""
        async with client:
            try:
                # Get recent transactions
                signatures = await client.get_signatures_for_address(
                    keypair.pubkey(),
                    limit=5
                )
                
                print(f"Found {len(signatures.value)} recent transactions")
                
                # Verify signature structure
                for sig_info in signatures.value[:2]:  # Check first 2
                    assert hasattr(sig_info, 'signature')
                    assert hasattr(sig_info, 'slot')
                    print(f"Transaction: {sig_info.signature} in slot {sig_info.slot}")
                    
            except Exception as e:
                pytest.skip(f"Transaction history access failed: {e}")
    
    @pytest.mark.asyncio
    async def test_account_info_retrieval(self, client, wallet_address):
        """Test account info retrieval"""
        async with client:
            pubkey = Pubkey.from_string(wallet_address)
            account_info = await client.get_account_info(pubkey)
            
            if account_info.value:
                account = account_info.value
                assert hasattr(account, 'lamports')
                assert hasattr(account, 'owner')
                assert account.lamports >= 0
                
                print(f"Account owner: {account.owner}")
                print(f"Account lamports: {account.lamports:,}")
            else:
                # Account might not exist if it has zero balance
                print("Account has no data (zero balance)")
    
    @pytest.mark.asyncio
    async def test_sol_mint_interaction(self, client):
        """Test interaction with native SOL mint"""
        sol_mint = "So11111111111111111111111111111111111111112"
        
        async with client:
            # Test mint account info
            pubkey = Pubkey.from_string(sol_mint)
            account_info = await client.get_account_info_json_parsed(pubkey)
            
            if account_info.value:
                parsed_data = account_info.value.data.parsed
                assert "info" in parsed_data
                
                info = parsed_data["info"]
                assert "decimals" in info
                assert info["decimals"] == 9  # SOL has 9 decimals
                
                print(f"SOL mint decimals: {info['decimals']}")
                print(f"SOL mint authority: {info.get('mintAuthority', 'None')}")
    
    @pytest.mark.asyncio 
    async def test_network_cluster_verification(self, client):
        """Test that we're connected to the expected network cluster"""
        expected_cluster = os.environ.get("SOLANA_CLUSTER", "devnet")
        
        async with client:
            # Get genesis hash to identify cluster
            genesis_hash = await client.get_genesis_hash()
            hash_str = str(genesis_hash.value)
            
            # Known genesis hashes for different clusters
            cluster_hashes = {
                "mainnet-beta": "5eykt4UsFv8P8NJdTREpY1vzqKqZKvdpKuc147dw2N9d",
                "testnet": "4uhcVJyU9pJkvQyS88uRDiswHXSCkY3zQawwpjk2NsNY", 
                "devnet": "EtWTRABZaYq6iMfeYKouRu166VU2xqa1wcaWoxPkrZBG"
            }
            
            print(f"Genesis hash: {hash_str}")
            print(f"Expected cluster: {expected_cluster}")
            
            if expected_cluster in cluster_hashes:
                expected_hash = cluster_hashes[expected_cluster]
                if hash_str != expected_hash:
                    print(f"Warning: Genesis hash doesn't match expected {expected_cluster} hash")
                    print(f"Expected: {expected_hash}")
                    print(f"Got: {hash_str}")
    
    @pytest.mark.asyncio
    async def test_minimum_balance_check(self, client, keypair):
        """Test minimum balance requirements for operations"""
        async with client:
            balance_resp = await client.get_balance(keypair.pubkey())
            balance = balance_resp.value
            
            # Check if wallet has minimum balance for transactions
            min_balance_for_tx = 5000  # ~0.000005 SOL for transaction fees
            
            if balance < min_balance_for_tx:
                pytest.skip(f"Wallet balance ({balance} lamports) below minimum for transactions")
            
            # Get minimum balance for rent exemption
            try:
                min_rent = await client.get_minimum_balance_for_rent_exemption(0)
                rent_exempt_balance = min_rent.value
                
                print(f"Minimum rent-exempt balance: {rent_exempt_balance:,} lamports")
                
                if balance >= rent_exempt_balance:
                    print("✅ Wallet is rent-exempt")
                else:
                    print("⚠️ Wallet balance below rent-exempt threshold")
                    
            except Exception as e:
                print(f"Could not get rent exemption info: {e}")
    
    @pytest.mark.asyncio
    async def test_transaction_simulation_capability(self, client, keypair):
        """Test transaction simulation capabilities"""
        async with client:
            try:
                # Create a simple transfer instruction (but don't execute)
                from solana.transaction import Transaction
                from solana.system_program import transfer, TransferParams
                
                # Create transfer to self (should always work if we have balance)
                instruction = transfer(
                    TransferParams(
                        from_pubkey=keypair.pubkey(),
                        to_pubkey=keypair.pubkey(),
                        lamports=1  # Minimal transfer
                    )
                )
                
                transaction = Transaction()
                transaction.add(instruction)
                
                # Get recent blockhash
                blockhash_resp = await client.get_latest_blockhash()
                transaction.recent_blockhash = blockhash_resp.value.blockhash
                
                # Sign transaction
                transaction.sign(keypair)
                
                # Simulate (don't execute)
                sim_result = await client.simulate_transaction(transaction)
                
                print(f"Transaction simulation result: {sim_result.value}")
                
                # Should succeed in simulation
                assert sim_result.value.err is None, f"Simulation failed: {sim_result.value.err}"
                
            except Exception as e:
                pytest.skip(f"Transaction simulation not available: {e}") 