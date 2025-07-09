# DevContainer Troubleshooting Guide

## Common Issues and Solutions

### 1. "Cannot connect to Docker daemon"
**Solution:** Ensure Docker Desktop is running
```bash
open -a Docker
# Wait for Docker to start, then retry
```

### 2. "Failed to build container"
**Solutions:**
- Clear Docker cache and rebuild:
  ```bash
  docker system prune -a
  ./setup-devcontainer.sh
  # Choose 'y' when asked to rebuild from scratch
  ```
- Check Docker Desktop resources (Settings > Resources)
- Ensure at least 4GB RAM allocated

### 3. "Mount path does not exist"
**Issue:** Missing directories on host machine
**Solution:** Run setup script:
```bash
./setup-devcontainer.sh
```

### 4. "Permission denied" errors
**Solutions:**
- Ensure proper file permissions:
  ```bash
  chmod 600 config/.envrc
  chmod +x setup-devcontainer.sh
  ```
- Check Docker Desktop file sharing settings

### 5. "Environment variables not loaded"
**Solution:** Ensure config/.envrc exists and is properly formatted:
```bash
# Check if file exists
ls -la config/.envrc

# If missing, create from sample
cp config/.envrc.sample config/.envrc
chmod 600 config/.envrc
```

### 6. "Solana CLI not found in container"
**Solution:** Once in container, run:
```bash
sudo /usr/local/bin/init-dev-env.sh
source ~/.zshrc
```

### 7. "Python dependencies missing"
**Solution:** In the container, run:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 8. VS Code Extension Issues
**Solution:** 
1. Open Command Palette (Cmd+Shift+P)
2. Run "Developer: Reload Window"
3. If persists, rebuild container

## Verification Steps

After successful setup, verify:
1. Docker is running: `docker ps`
2. Environment file exists: `ls -la config/.envrc`
3. In container: `python --version` shows 3.12
4. Solana CLI works: `solana --version`

## Still Having Issues?

1. Check Docker Desktop logs
2. Review .devcontainer/devcontainer.json for mount issues
3. Ensure VS Code Dev Containers extension is installed
4. Try manual build: `docker build -f .devcontainer/Dockerfile -t test .`
