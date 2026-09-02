# ADR 0005: Elimination of Cloud Infrastructure in Favor of Self-Hosting

* **Status**: Accepted & Executed
* **Date**: 2026-09-02
* **Deciders**: Engineering & Security Team

---

## Context & Problem Statement

Earlier iterations of the project contained extensive Terraform configurations targeting AWS ECS Fargate, Lambda, CloudFront, Cognito, and DynamoDB. This infrastructure introduced high operational friction, complex secret management across multiple cloud services, slow CI/CD deployments, and continuous AWS hosting costs.

The core Python trading daemons are lightweight ($< 15\text{MB}$ memory footprint, single-threaded async event loop) and do not require heavy cloud orchestration to operate effectively.

---

## Decision Drivers

1. **Security & Key Management**: Storing Solana private keys in cloud environment variables across multiple AWS services created unnecessary attack surface.
2. **Operational Simplicity**: Running a local process or a standard Docker container provides identical execution speed without Terraform lock files or IAM complexity.
3. **CI/CD Reliability**: Eliminating Terraform deploy steps from GitHub Actions prevents broken CI builds caused by expired cloud credentials or IAM permission drifts.

---

## Decision Outcome

1. **Remove AWS Terraform Files**:
   * Completely deleted the `infra/` directory containing Terraform scripts and dead AWS configurations.
2. **Standardize on Local & Docker Deployments**:
   * Support standalone process execution via Python virtualenv or containerized execution via `docker-compose.yml`.
3. **Clean CI/CD Pipeline**:
   * Streamlined `.github/workflows/ci.yml` to focus purely on automated linting (Ruff, Mypy), unit testing (Pytest), and Docker container builds.

### Positive Consequences
* Zero monthly cloud infrastructure overhead.
* Drastically reduced attack surface for private key leakage.
* Fast, deterministic CI runs in under 45 seconds.
