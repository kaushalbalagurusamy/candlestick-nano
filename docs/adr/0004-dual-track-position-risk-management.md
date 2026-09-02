# ADR 0004: Dual-Track Position Risk Management

* **Status**: Accepted
* **Date**: 2026-09-02
* **Deciders**: Engineering & Systems Architecture Team

---

## Context & Problem Statement

Volatile crypto-assets require rapid profit realization alongside strict downside protection. Relying solely on polling-based market orders introduces latency risk for take-profit targets, while relying solely on on-chain limit orders prevents dynamic trailing stop-loss protection.

---

## Decision Drivers

1. **Automated Take-Profit**: Securing upside target multiples (e.g. $+20\%$) trustlessly on-chain.
2. **Capital Preservation**: Triggering emergency market exit if a position drops past the maximum acceptable loss threshold (e.g. $-10\%$).
3. **Order State Synchronization**: Ensuring limit orders are immediately cancelled on-chain before a stop-loss market sell is dispatched to prevent double-spending or stranded inventory.

---

## Decision Outcome

Implement a dual-track asynchronous risk manager in `src/exit_daemon.py` and `src/combined_daemon.py`:

1. **Track 1: On-Chain Take-Profit Limit Order**:
   * Upon successful entry swap, immediately place an on-chain Jupiter limit order at $\text{Entry Price} \times (1 + \text{TAKE\_PROFIT\_PERCENTAGE})$.
2. **Track 2: Active Mark-to-Market Stop-Loss Polling**:
   * Poll current mark-to-market prices via Jupiter quote every `MONITORING_INTERVAL` seconds.
   * If $\Delta P \le -\text{STOP\_LOSS\_PERCENTAGE}$:
     1. Cancel active on-chain limit order via `cancel_limit_order()`.
     2. Dispatch market sell swap back into WSOL with expanded slippage tolerance.
     3. Remove position from active memory registry.

### Positive Consequences
* Locks in profits passively on-chain without requiring millisecond polling loops.
* Protects capital with automated emergency stop-loss execution.
