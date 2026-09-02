# ADR 0001: Asyncio Daemon Execution Architecture

* **Status**: Accepted
* **Date**: 2026-09-02
* **Deciders**: Engineering & Systems Architecture Team

---

## Context & Problem Statement

High-frequency pool discovery and sub-second trade execution on Solana require low-latency event processing. Initial architectures considered serverless cloud functions (e.g. QuickNode Functions or AWS Lambda), but these introduced cold-start penalties, ephemeral state loss for open positions, and heightened latency during volatile launch drops.

---

## Decision Drivers

1. **Sub-Second Execution**: Zero cold-start overhead when new pools are broadcast on QuickNode Metis.
2. **Stateful Position Tracking**: Real-time in-memory tracking of active token balances, limit order pubkeys, and mark-to-market prices.
3. **Operational Simplicity**: Ability to execute as a single local process for MVP testing or decoupled multi-process daemons in production.

---

## Decision Outcome

Standardize on a native Python 3.9+ `asyncio` daemon topology:

1. **Unified Event Loop (`src/combined_daemon.py`)**:
   * Single asynchronous process running concurrent non-blocking tasks for pool polling (`fetch_new_pools`), safety evaluation, swap execution, and stop-loss monitoring.
2. **Decoupled Daemons (`src/entry_daemon.py` / `src/exit_daemon.py`)**:
   * Separate entry and exit processes for horizontal scaling and independent fault isolation.
3. **Lazy Configuration (`src/config.py`)**:
   * Type-safe, cached environment parameter resolution without import-time side effects.

### Positive Consequences
* Sub-millisecond internal dispatch between pool detection and quote requests.
* Zero dependence on cloud function runtimes or external key-value stores for local trading.
