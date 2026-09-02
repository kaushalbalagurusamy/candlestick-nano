# ADR 0002: Jupiter DEX Routing and Swap Protocol

* **Status**: Accepted
* **Date**: 2026-09-02
* **Deciders**: Engineering & Systems Architecture Team

---

## Context & Problem Statement

Solana liquidity is fragmented across disparate DEX protocols (Raydium AMM, Raydium CLMM, Orca Whirlpools, Meteora, and OpenBook). Interacting directly with individual AMM program instructions requires maintaining complex custom SDK integrations and manual route optimization.

---

## Decision Drivers

1. **Optimal Execution Price**: Aggregating multi-hop routes across all major Solana liquidity pools.
2. **Atomic WSOL Swaps**: Automated wrapping and unwrapping of SOL/WSOL within transaction payloads.
3. **Slippage Bounds**: Enforcing strict basis-point slippage tolerances to mitigate sandwich and front-running attacks.

---

## Decision Outcome

Adopt Jupiter v6 API (`https://quote-api.jup.ag/v6`) as the canonical DEX routing and settlement layer:

1. **Quote Ingestion**:
   * Request dynamic routes via `/quote` specifying `inputMint` (WSOL), `outputMint` (Target Token), `amount`, and `slippageBps`.
2. **Transaction Serialization**:
   * Fetch serialized versioned transactions via `/swap`, sign locally with the private keypair using `solders`, and broadcast via Solana RPC.
3. **Limit Order Protocol**:
   * Utilize Jupiter Limit Order API (`/limit-orders/*`) for trustless, on-chain take-profit settlement.

### Positive Consequences
* Instant access to liquidity across all Solana DEXes without custom protocol smart contract integrations.
* Automatic route splitting and MEV protection.
