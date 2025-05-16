import os
import asyncio
import base64
import base58
from solana.rpc.async_api import AsyncClient
from solana.publickey import PublicKey
from solana.rpc.types import TokenAccountOpts, TxOpts
from solders.transaction import VersionedTransaction
from solders.keypair import Keypair
from jupiter_python_sdk.jupiter import Jupiter

RPC_URL     = os.environ["QUICKNODE_ENDPOINT"]
METIS_URL   = os.environ["JUPITER_API_BASE_URL"]
PRIVATE_KEY = os.environ["WALLET_PRIVATE_KEY"]
WATCH_MINTS = os.environ.get("WATCH_MINTS", "").split(",")

SOL_MINT     = "So11111111111111111111111111111111111111112"
SLIPPAGE_BPS = 10   # 0.1%

async def monitor_coin(mint: str):
    """Watch a single mint indefinitely and exit at 0.9× or 1.2×."""
    # create fresh clients per watcher to isolate connections
    client = AsyncClient(RPC_URL)
    kp     = Keypair.from_bytes(base58.b58decode(PRIVATE_KEY))
    jup    = Jupiter(
        async_client  = client,
        keypair       = kp,
        quote_api_url = f"{METIS_URL}/quote",
        swap_api_url  = f"{METIS_URL}/swap",
    )

    # record entry price once
    q = await jup.quote(mint, SOL_MINT, 1_000)
    entry_price = float(q.output_amount) / 1e9

    while True:
        try:
            # re-quote
            q     = await jup.quote(mint, SOL_MINT, 1_000)
            price = float(q.output_amount) / 1e9
            ratio = price / entry_price

            if ratio <= 0.9 or ratio >= 1.2:
                resp = await client.get_token_accounts_by_owner(
                    kp.pubkey(),
                    TokenAccountOpts(mint=mint)
                )
                if resp.value:
                    acct_pubkey = PublicKey(resp.value[0].pubkey)
                    bal_resp    = await client.get_token_account_balance(acct_pubkey)
                    amt         = int(bal_resp.value.ui_amount * 1e9)

                    tx_b64 = await jup.swap(mint, SOL_MINT, amt, SLIPPAGE_BPS)
                    tx     = VersionedTransaction.from_bytes(base64.b64decode(tx_b64))
                    await client.send_raw_transaction(
                        bytes(tx), opts=TxOpts(skip_preflight=True)
                    )
                # once swapped, break out and stop watching this mint
                break

        except Exception as e:
            # log the error and continue without exiting
            print(f"[{mint}] watcher error: {e}. Restarting check loop.")
        finally:
            # pause briefly, then immediately resume checking—no gaps
            await asyncio.sleep(5)

    await client.close()
    print(f"[{mint}] monitoring task completed and daemonized exit.")

async def main():
    # spawn one daemon task per mint
    tasks = []
    for mint in WATCH_MINTS:
        if not mint:
            continue
        # create_task schedules it under the running loop
        task = asyncio.create_task(monitor_coin(mint), name=f"watcher-{mint}")
        task.add_done_callback(lambda t: print(f"Task {t.get_name()} ended"))
        tasks.append(task)

    if not tasks:
        print("No WATCH_MINTS defined. Nothing to monitor.")
        return

    # keep the loop alive indefinitely (daemon-style)
    print(f"Spawned {len(tasks)} watcher daemons. Running forever...")
    await asyncio.Event().wait()  # never returns

if __name__ == "__main__":
    # Use run() which will run until all tasks complete or are cancelled,
    # but since main() awaits an Event that never fires, it never exits.
    asyncio.run(main())