# Claude CLI Container Setup

This document explains how to use Claude Code CLI within the Candlestick Nano trading bot's Docker environment. The setup has been enhanced to provide a lightweight, secure, and fully functional development environment.

## Overview

The Claude CLI container provides:
- **Claude Code CLI**: Official Anthropic CLI for AI-powered coding assistance
- **Python 3 Environment**: Pre-configured virtual environment with all dependencies
- **Development Tools**: Git, zsh, fzf, ripgrep for enhanced development experience
- **VS Code Integration**: Full devcontainer support for seamless development
- **Security**: Non-root user execution with proper permissions

## Quick Start

### 1. Prerequisites

- Docker and Docker Compose installed
- ANTHROPIC_API_KEY environment variable set
- Your Claude account with API access

### 2. Set Up API Key

```bash
# Set your Anthropic API key
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Or add it to your shell profile
echo 'export ANTHROPIC_API_KEY="sk-ant-your-key-here"' >> ~/.zshrc
```

### 3. Start the Container

```bash
# Use the helper script
./scripts/claude_cli_docker.sh start

# Or manually with docker-compose
docker-compose --profile claude up -d claude-cli
```

### 4. Authenticate Claude CLI

```bash
# Run authentication (required on first use)
./scripts/claude_cli_docker.sh auth
```

### 5. Use Claude CLI

```bash
# Enter interactive shell
./scripts/claude_cli_docker.sh shell

# Run specific commands
./scripts/claude_cli_docker.sh run "explain this codebase"
```

## Container Architecture

### Base Image
- **Node.js 20**: Required for Claude CLI npm package
- **Python 3**: For the trading bot application
- **Lightweight**: Based on slim images for minimal footprint

### User Setup
- **Non-root user**: `claude` (UID 1000, GID 100)
- **Shell**: zsh with productivity enhancements
- **Home directory**: `/home/claude`
- **Working directory**: `/home/claude/workspace` (your project)

### Volume Mounts
- **Project files**: `.` → `/home/claude/workspace`
- **Claude config**: Persistent volume for authentication
- **Claude cache**: Persistent volume for CLI cache
- **Shell history**: Persistent zsh history

## Available Commands

### Helper Script Commands

```bash
# Container management
./scripts/claude_cli_docker.sh start     # Start container
./scripts/claude_cli_docker.sh stop      # Stop container
./scripts/claude_cli_docker.sh restart   # Restart container
./scripts/claude_cli_docker.sh rebuild   # Rebuild from scratch

# Claude CLI operations
./scripts/claude_cli_docker.sh auth      # Authenticate Claude CLI
./scripts/claude_cli_docker.sh shell     # Enter interactive shell
./scripts/claude_cli_docker.sh run "cmd" # Run specific command

# Monitoring
./scripts/claude_cli_docker.sh status    # Check status
./scripts/claude_cli_docker.sh logs      # View logs
```

### Inside the Container

```bash
# Claude CLI commands
claude                              # Start interactive Claude session
claude --version                    # Check version
claude "explain this function"      # Direct command
claude-check                        # Alias for version check

# Python environment (auto-activated)
python3                             # Python interpreter
pip                                 # Package manager
pytest                              # Run tests

# Development tools
git                                 # Version control
rg                                  # Ripgrep for fast searching
fzf                                 # Fuzzy finder
```

## VS Code Development Container

### Setup
1. Install the "Remote - Containers" extension in VS Code
2. Open the project in VS Code
3. Click "Reopen in Container" when prompted
4. Or use Command Palette: `Remote-Containers: Reopen in Container`

### Features
- **Integrated Terminal**: zsh with claude user
- **Python Support**: Full debugging and IntelliSense
- **Claude CLI Access**: Available in the integrated terminal
- **Port Forwarding**: Automatic forwarding of port 8000
- **Extensions**: Pre-configured development extensions

### Configuration

The devcontainer includes:
- Python development tools (black, isort, pylint)
- Git integration (GitLens, Git Graph)
- Docker support
- Additional productivity extensions

## Authentication

### First-time Setup

1. **Start the container**:
   ```bash
   ./scripts/claude_cli_docker.sh start
   ```

2. **Run authentication**:
   ```bash
   ./scripts/claude_cli_docker.sh auth
   ```

3. **Follow the OAuth flow**:
   - This will open an interactive session
   - Run `claude` in the container
   - Follow the prompts to authenticate via browser
   - Complete the OAuth process with your Claude account

### Verification

Check authentication status:
```bash
./scripts/claude_cli_docker.sh status
```

You should see:
- ✓ Claude CLI container is running
- ✓ Claude CLI is installed and accessible
- ✓ API key is configured
- ✓ Claude CLI appears to be authenticated

## Usage Examples

### Basic Commands

```bash
# Explain code
./scripts/claude_cli_docker.sh run "explain the main trading logic"

# Generate documentation
./scripts/claude_cli_docker.sh run "generate README for this project"

# Code review
./scripts/claude_cli_docker.sh run "review the latest changes"

# Debug assistance
./scripts/claude_cli_docker.sh run "help debug this error: [error message]"
```

### Interactive Sessions

```bash
# Enter the container
./scripts/claude_cli_docker.sh shell

# Inside the container
claude@container:/home/claude/workspace$ claude
# Now you're in interactive Claude session
# Type your questions or commands
# Use Ctrl+C to exit Claude, then 'exit' to leave container
```

### Project Analysis

```bash
# Analyze the entire codebase
./scripts/claude_cli_docker.sh run "analyze this trading bot codebase and provide insights"

# Focus on specific components
./scripts/claude_cli_docker.sh run "explain how the entry daemon works"

# Performance suggestions
./scripts/claude_cli_docker.sh run "suggest performance improvements for the trading algorithms"
```

## Troubleshooting

### Common Issues

1. **Container fails to start**
   ```bash
   # Check Docker status
   docker info
   
   # Rebuild container
   ./scripts/claude_cli_docker.sh rebuild
   ```

2. **Claude CLI not found**
   ```bash
   # Check installation
   docker exec -it candlestick-claude-cli ls -la /home/claude/.local/bin/
   
   # Rebuild with no cache
   ./scripts/claude_cli_docker.sh rebuild
   ```

3. **Authentication issues**
   ```bash
   # Clear authentication and retry
   docker exec -it candlestick-claude-cli rm -rf /home/claude/.anthropic
   ./scripts/claude_cli_docker.sh auth
   ```

4. **Permission errors**
   ```bash
   # Check user permissions
   docker exec -it candlestick-claude-cli id
   
   # Should show: uid=1000(claude) gid=100(users)
   ```

### Debugging

1. **View container logs**:
   ```bash
   ./scripts/claude_cli_docker.sh logs
   ```

2. **Check container status**:
   ```bash
   ./scripts/claude_cli_docker.sh status
   ```

3. **Inspect container**:
   ```bash
   docker exec -it candlestick-claude-cli bash
   ```

4. **Test Claude CLI directly**:
   ```bash
   docker exec -it --user claude candlestick-claude-cli /home/claude/.local/bin/claude --version
   ```

### Reset Everything

If you encounter persistent issues:

```bash
# Stop and remove container
docker-compose --profile claude down claude-cli

# Remove volumes
docker volume rm candlestick-nano_claude-config
docker volume rm candlestick-nano_claude-cache
docker volume rm candlestick-nano_claude-home

# Rebuild and restart
./scripts/claude_cli_docker.sh rebuild
./scripts/claude_cli_docker.sh start
./scripts/claude_cli_docker.sh auth
```

## Security Considerations

### Container Security
- **Non-root execution**: All commands run as `claude` user
- **Limited privileges**: Container runs with minimal required permissions
- **Volume isolation**: Only necessary directories are mounted
- **Network isolation**: Container uses default Docker networking

### API Key Security
- **Environment variables**: API key passed securely via environment
- **No hardcoding**: No sensitive data stored in images
- **Volume persistence**: Authentication stored in named volumes

### Best Practices
- **Regular updates**: Keep Claude CLI updated
- **Key rotation**: Rotate API keys periodically
- **Access control**: Limit container access to necessary users
- **Monitoring**: Review Claude CLI usage and logs

## Integration with Trading Bot

### Development Workflow

1. **Code Analysis**: Use Claude to understand complex trading algorithms
2. **Documentation**: Generate comprehensive API documentation
3. **Testing**: Get suggestions for test cases and edge cases
4. **Debugging**: Analyze error logs and get debugging suggestions
5. **Optimization**: Get performance improvement recommendations

### Trading-Specific Commands

```bash
# Analyze trading strategies
./scripts/claude_cli_docker.sh run "explain the stop-loss mechanism in exit_utils.py"

# Review risk management
./scripts/claude_cli_docker.sh run "review the risk management in trading_bot_core.py"

# Optimize performance
./scripts/claude_cli_docker.sh run "suggest optimizations for the entry daemon"

# Generate tests
./scripts/claude_cli_docker.sh run "create unit tests for the buy module"
```

## Advanced Usage

### Custom Claude Commands

Create custom aliases in the container:

```bash
# Enter container
./scripts/claude_cli_docker.sh shell

# Add custom aliases
echo 'alias claude-review="claude \"review the latest git changes\""' >> ~/.zshrc
echo 'alias claude-test="claude \"suggest test cases for recent changes\""' >> ~/.zshrc
echo 'alias claude-docs="claude \"update documentation for recent changes\""' >> ~/.zshrc
```

### Scripting with Claude

Create scripts that use Claude CLI:

```bash
#!/bin/bash
# analyze_changes.sh

# Run inside container
./scripts/claude_cli_docker.sh run "
Analyze the recent changes in this git repository:
$(git log --oneline -10)

Provide:
1. Summary of changes
2. Potential impacts
3. Testing recommendations
4. Documentation updates needed
"
```

### Integration with CI/CD

Use in automated workflows:

```yaml
# GitHub Actions example
- name: Claude Code Review
  run: |
    ./scripts/claude_cli_docker.sh start
    ./scripts/claude_cli_docker.sh run "review this pull request changes"
```

## Support and Resources

### Official Documentation
- [Claude Code CLI Documentation](https://docs.anthropic.com/claude/docs/claude-code)
- [Docker Documentation](https://docs.docker.com/)
- [VS Code Remote Containers](https://code.visualstudio.com/docs/remote/containers)

### Project Resources
- Helper script: `scripts/claude_cli_docker.sh`
- Devcontainer config: `.devcontainer/devcontainer.json`
- Docker configuration: `docker-compose.yml`

### Getting Help

1. **Check status**: `./scripts/claude_cli_docker.sh status`
2. **Review logs**: `./scripts/claude_cli_docker.sh logs`
3. **Rebuild container**: `./scripts/claude_cli_docker.sh rebuild`
4. **Check GitHub issues**: [Candlestick Nano Issues](https://github.com/your-repo/issues)

This enhanced setup provides a professional-grade development environment for AI-powered trading bot development with Claude Code CLI integration. 