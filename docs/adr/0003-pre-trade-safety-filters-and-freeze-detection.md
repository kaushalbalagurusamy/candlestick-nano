# ADR 0003: Pre-Trade Safety Filters and Freeze Detection

* **Status**: Accepted
* **Date**: 2026-09-02
* **Deciders**: Engineering & Systems Architecture Team

---

## Context & Problem Statement

Newly deployed token pools on Solana frequently contain honeypots, malicious freeze authorities, or insufficient liquidity, leading to instantaneous capital loss if bought automatically without validation.

---

## Decision Drivers

1. **Rug-Pull Prevention**: Immediate rejection of tokens where the creator can freeze user token accounts.
2. **Liquidity Verification**: Rejection of pools with artificial or negligible initial liquidity.
3. **Stale Pool Filtering**: Rejection of pools deployed hours or days prior that fail initial momentum checks.

---

## Decision Outcome

Enforce a mandatory three-stage deterministic pre-flight filter in `src/trading_bot_core.py` prior to transaction construction:

```
New Pool Event
      |
      v
+-------------------------------------------------+
| Stage 1: Token Age Verification                |
| - Parse ISO timestamp; reject if age > MAX_AGE  |
+---------------------+---------------------------+
                      | Passes (< 23h)
                      v
+-------------------------------------------------+
| Stage 2: Freeze Authority Audit                 |
| - Inspect mint account info on-chain via RPC    |
| - If freeze_authority != None -> REJECT         |
+---------------------+---------------------------+
                      | Passes (None)
                      v
+-------------------------------------------------+
| Stage 3: Liquidity & Output Quote Check         |
| - Request quote for AMOUNT_SOL                  |
| - If outAmount < MIN_LIQUIDITY_THRESHOLD -> DROP|
+---------------------+---------------------------+
                      | Passes
                      v
          Construct & Sign Buy Swap
```

### Positive Consequences
* Zero automated buys against tokens with active freeze authority.
* Protects capital against illiquid pools and high price impact.
