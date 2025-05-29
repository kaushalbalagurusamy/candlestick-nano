# Directory Restructure Guide

This document outlines the directory reorganization implemented to improve codebase maintainability and follow best practices.

## Overview

The codebase has been reorganized from a cluttered root directory into a clean, logical structure that separates concerns and improves maintainability.

## New Directory Structure

```
candlestick-nano/
├── src/                    # Core application code
│   ├── combined_daemon.py  # All-in-one trading bot
│   ├── entry_daemon.py     # Entry monitoring daemon
│   ├── exit_daemon.py      # Exit monitoring daemon
│   ├── exit_monitor.py     # Legacy exit monitoring
│   ├── exit_utils.py       # Exit strategy utilities
│   ├── extractor.py        # Data extraction utilities
│   ├── trading_bot_core.py # Core trading logic
│   ├── buy.py             # Manual buy functionality
│   └── quick_start_mvp.py  # Quick start MVP script
├── config/                 # Configuration files
│   ├── .envrc              # Environment variables
│   ├── .envrc.sample       # Environment template
│   ├── api_contract.yaml   # API contract definitions
│   ├── tokens.json         # Token configurations
│   └── faucet_state.json   # Airdrop state tracking
├── scripts/                # Utility scripts
│   ├── setup_production.sh # Production setup
│   ├── setup_auto_airdrop.sh # Airdrop setup
│   ├── auto_airdrop.sh     # Background airdrop runner
│   ├── cursor_start.sh     # Development helper
│   └── fix_cursor_shell.sh # Shell fix utility
├── legacy/                 # Legacy components
│   ├── airdrop.py          # SOL airdrop collector
│   └── airdrop_status.py   # Airdrop status checker
├── logs/                   # Log files and process IDs
│   ├── airdrop.log         # Airdrop activity logs
│   └── airdrop.pid         # Process ID files
├── systemd/                # System service files
│   ├── candlestick-bot.service  # Main bot service
│   └── airdrop-auto.service     # Airdrop service
├── tests/                  # Test suite
├── docs/                   # Documentation
├── infra/                  # Infrastructure (Terraform)
├── quicknode_functions/    # Serverless functions
├── requirements.txt        # Python dependencies
├── docker-compose.yml      # Container orchestration
├── Dockerfile             # Container definition
└── README.md              # Main documentation
```

## Migration Details

### Files Moved

#### Core Application (`src/`)
- `combined_daemon.py` → `src/combined_daemon.py`
- `entry_daemon.py` → `src/entry_daemon.py`
- `exit_daemon.py` → `src/exit_daemon.py`
- `exit_monitor.py` → `src/exit_monitor.py`
- `exit_utils.py` → `src/exit_utils.py`
- `extractor.py` → `src/extractor.py`
- `trading_bot_core.py` → `src/trading_bot_core.py`
- `buy.py` → `src/buy.py`
- `quick_start_mvp.py` → `src/quick_start_mvp.py`

#### Configuration (`config/`)
- `.envrc` → `config/.envrc`
- `.envrc.backup` → `config/.envrc.backup`
- `.envrc.sample` → `config/.envrc.sample`
- `api_contract.yaml` → `config/api_contract.yaml`
- `tokens.json` → `config/tokens.json`
- `faucet_state.json` → `config/faucet_state.json`

#### Scripts (`scripts/`)
- `auto_airdrop.sh` → `scripts/auto_airdrop.sh`
- `cursor_start.sh` → `scripts/cursor_start.sh`
- `fix_cursor_shell.sh` → `scripts/fix_cursor_shell.sh`
- `setup_auto_airdrop.sh` → `scripts/setup_auto_airdrop.sh`
- `setup_production.sh` → `scripts/setup_production.sh`

#### Legacy Components (`legacy/`)
- `airdrop.py` → `legacy/airdrop.py`
- `airdrop_status.py` → `legacy/airdrop_status.py`

#### Logs (`logs/`)
- `airdrop.log` → `logs/airdrop.log`
- `airdrop.pid` → `logs/airdrop.pid`

#### System Services (`systemd/`)
- `airdrop-auto.service` → `systemd/airdrop-auto.service`
- `candlestick-bot.service` → `systemd/candlestick-bot.service`

#### Documentation (`docs/`)
- `AGENTS.md` → `docs/AGENTS.md`
- `DEPLOYMENT_GUIDE.md` → `docs/DEPLOYMENT_GUIDE.md`
- `INTEGRATION_SUMMARY.md` → `docs/INTEGRATION_SUMMARY.md`

### Updated References

#### Import Statements
- Updated test files to import from `src.` modules
- Updated relative imports in application code

#### Configuration Paths
- Docker Compose: Updated `env_file` paths to `config/.envrc`
- SystemD services: Updated `EnvironmentFile` paths
- Scripts: Updated script paths and log destinations

#### Documentation
- Updated README.md with new directory structure
- Updated path references in quick start guide
- Updated deployment guide references

## Benefits of Restructure

### 1. **Separation of Concerns**
- Core application code isolated in `src/`
- Configuration files centralized in `config/`
- Utilities and scripts organized in `scripts/`

### 2. **Improved Maintainability**
- Easier to locate specific components
- Clear distinction between active and legacy code
- Consistent file organization

### 3. **Better Development Experience**
- Cleaner root directory
- Logical grouping of related files
- Easier navigation for developers and AI agents

### 4. **Deployment Clarity**
- Clear separation of runtime vs configuration
- System services properly organized
- Infrastructure code isolated

### 5. **Best Practices Compliance**
- Follows standard project structure conventions
- Improves code discoverability
- Facilitates automated tooling

## Migration Commands

If you have an existing checkout, you can manually sync with the new structure:

```bash
# Backup your current .envrc
cp .envrc config/.envrc

# Update any custom scripts or configurations
# to use the new paths as documented above
```

## Breaking Changes

### Environment Loading
- Change: `.envrc` → `config/.envrc`
- Impact: direnv users need to re-allow the new path
- Solution: `direnv allow config/.envrc`

### Script Execution
- Change: Direct script execution requires path updates
- Impact: Custom automation may need updates
- Solution: Use `python src/script_name.py` or update your paths

### Docker/Container Deployments
- Change: Environment file paths updated in docker-compose.yml
- Impact: Container deployments automatically updated
- Solution: No action needed (already updated)

## Validation

After migration, verify the new structure works:

```bash
# Test environment loading
direnv allow config/.envrc

# Test core functionality
python src/quick_start_mvp.py

# Test configuration access
ls -la config/

# Test legacy functionality
python legacy/airdrop.py --help

# Run tests
pytest
```

## Future Considerations

This structure supports:
- Additional microservices in `src/`
- Environment-specific configs in `config/`
- Deployment automation from `scripts/`
- Clear legacy code management
- Comprehensive documentation in `docs/`

The organization follows Python packaging best practices and is optimized for both human developers and AI code assistants. 