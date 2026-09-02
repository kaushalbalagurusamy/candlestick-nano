# ADR 0006: Transition to Embedded Zero-Cloud Operating Model

* **Status**: Accepted
* **Date**: 2026-09-02
* **Deciders**: Engineering & Systems Architecture Team

---

## Context & Problem Statement

Following the permanent deletion of the AWS account, all multi-service cloud infrastructure (AWS ECS Fargate, Lambda, DynamoDB, Cognito, S3, CloudFront, and CloudWatch) is permanently decommissioned. 

The application must function autonomously without any third-party cloud hosting accounts, relying exclusively on direct Solana RPC endpoints, local process management, and embedded state storage.

---

## Decision Drivers

1. **Zero Cloud Dependency**: Zero reliance on AWS, GCP, or Azure services, eliminating recurring monthly hosting charges.
2. **Deterministic State Persistence**: Storing open positions, trade history, and active limit order IDs locally across restarts without external database servers.
3. **Controlled Local Execution**: The trading engine operates purely on-demand as a discrete Python process or local container, with zero continuous background memory footprint unless explicitly initiated by the user.

---

## Decision Outcome

Adopt the Embedded Zero-Cloud operating architecture:

1. **State Persistence**:
   * Replace DynamoDB with a lightweight embedded SQLite store (`data/positions.db`) or local JSON state files (`config/tokens.json`, `config/faucet_state.json`).
2. **Compute & Daemon Model**:
   * Replace ECS Fargate with on-demand Python processes (`src/combined_daemon.py`, `src/quick_start_mvp.py`) or self-contained Docker Compose definitions.
3. **Telemetry & Logging**:
   * Replace AWS CloudWatch with standard rotating file logs (`logs/trading.log`) and direct console stdout.
4. **Configuration Sanitization**:
   * Purged all `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and Terraform manifests from the repository and CI/CD pipelines.

### Positive Consequences
* Completely portable codebase capable of running on any local machine (macOS/Linux) or a standalone Linux VPS.
* Elimination of cloud security vulnerabilities and private key exposure in cloud dashboards.
* Total operational cost reduced to $0.00 (beyond on-chain Solana transaction gas fees).
