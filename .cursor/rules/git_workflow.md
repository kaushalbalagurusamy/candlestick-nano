# Git Workflow Automation Rules

You are an expert in **Git workflow automation**, **version control best practices**, and **collaborative development**.

## Automated Git Workflow Requirements

### Core Principles
- **Commit Early, Commit Often**: Save progress incrementally with meaningful messages
- **Push Frequently**: Keep remote repository synchronized with local changes  
- **Atomic Commits**: Each commit represents a single logical change
- **Descriptive Messages**: Use conventional commit format with clear descriptions
- **Branch Protection**: Always work on main branch for core development
- **Clean History**: Maintain readable commit history for collaboration

### Automatic Commit and Push Pattern

After implementing features, fixes, or improvements, **ALWAYS** follow this automated workflow:

```bash
# 1. Check current status
git status

# 2. Add all relevant changes  
git add .

# 3. Commit with descriptive message
git commit -m "feat/fix/docs: descriptive message

- Detailed explanation of changes
- Impact and benefits
- Related issues or requirements"

# 4. Push to remote repository
git push origin main

# 5. Verify push success
git status
```

### Commit Message Standards

Use **Conventional Commits** format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer]
```

#### Commit Types:
- `feat`: New feature implementation
- `fix`: Bug fix or error correction
- `docs`: Documentation updates
- `style`: Code formatting/style changes
- `refactor`: Code restructuring without behavior change
- `test`: Adding or updating tests
- `chore`: Maintenance tasks, deps updates
- `perf`: Performance improvements
- `ci`: CI/CD configuration changes

#### Examples:
```bash
# Feature addition
git commit -m "feat: add comprehensive Cursor rules for trading bot development

- Added trading_bot_core.md with async patterns and type safety
- Added ml_ai_workflow.md for real-time ML inference  
- Added trading_safety.md with risk management protocols
- Integrated with existing architecture guidelines"

# Bug fix
git commit -m "fix: resolve git push failures and broken refs

- Removed large Terraform provider files (644MB) 
- Cleaned up broken git refs with spaces in names
- Fixed merge conflicts in README.md and test files
- Successfully merged origin/main with local changes"

# Documentation update  
git commit -m "docs: update README with new architecture and deployment info

- Added AWS infrastructure overview
- Updated directory structure documentation
- Enhanced quick start instructions
- Added deployment guide references"
```

### Automated Workflow Triggers

Implement automated git workflow **AFTER**:

1. **Feature Implementation**: Any new functionality added
2. **Bug Fixes**: Error corrections or issue resolutions  
3. **Code Refactoring**: Structure or organization improvements
4. **Documentation Updates**: README, docs, or inline documentation changes
5. **Configuration Changes**: Environment, deployment, or tool configurations
6. **Test Additions**: New test coverage or test improvements
7. **Dependency Updates**: Package upgrades or new dependencies

### Pre-Commit Checklist

Before committing, **ALWAYS** verify:

```bash
# 1. Code quality checks
python -m ruff check src/ tests/  # Linting
python -m black src/ tests/       # Formatting  

# 2. Test suite validation
python -m pytest tests/ -v       # Run tests

# 3. File size validation
find . -size +50M -type f | grep -v ".venv" | grep -v ".git"

# 4. Security validation  
grep -r "TODO\|FIXME\|XXX" src/ || true
grep -r "password\|secret\|key" src/ --exclude-dir=.git || true
```

### Repository Health Maintenance

#### Weekly Git Maintenance:
```bash
# Clean up local branches
git remote prune origin
git branch -d $(git branch --merged | grep -v main)

# Optimize repository
git gc --aggressive
git repack -Ad

# Validate repository integrity
git fsck --full
```

#### Monthly Repository Audit:
```bash
# Check large files
git rev-list --objects --all | \
  git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | \
  awk '/^blob/ {print substr($0,6)}' | sort --numeric-sort --key=2 | tail -10

# Check commit frequency
git log --since="1 month ago" --oneline | wc -l

# Check contributor activity  
git shortlog -sn --since="1 month ago"
```

### Branch Management Strategy

For this trading bot project, use **main-based development**:

```bash
# Always ensure you're on main
git checkout main

# Keep main updated
git pull origin main

# Make changes directly on main (for solo development)
# Commit and push frequently

# For larger features, optionally use short-lived branches:
git checkout -b feature/new-trading-strategy
# ... implement feature ...
git add . && git commit -m "feat: implement new trading strategy"
git checkout main
git merge feature/new-trading-strategy --no-ff
git branch -d feature/new-trading-strategy
git push origin main
```

### Conflict Resolution Automation

When merge conflicts occur:

```bash
# 1. Identify conflicts
git status

# 2. Review conflict files
git diff --name-only --diff-filter=U

# 3. For each conflict file:
#    a. Keep our version for project-specific files (.cursor/, .claude/, src/)
#    b. Integrate changes for shared files (README.md, requirements.txt)
#    c. Remove deprecated files that were moved/reorganized

# 4. Mark resolved and commit
git add .
git commit -m "fix: resolve merge conflicts - integrate remote changes

- Resolved conflicts in [list files]
- Maintained project structure and cursor rules
- Successfully integrated upstream changes"

# 5. Push immediately  
git push origin main
```

### Automated Git Hooks

Create `.git/hooks/pre-commit` (executable):

```bash
#!/bin/bash
# Pre-commit hook for trading bot

echo "Running pre-commit checks..."

# Check for large files
large_files=$(find . -size +50M -type f | grep -v ".venv" | grep -v ".git")
if [ -n "$large_files" ]; then
    echo "ERROR: Large files detected:"
    echo "$large_files"
    echo "Add to .gitignore or use Git LFS"
    exit 1
fi

# Check for secrets (basic)
if grep -r "sk-" src/ --exclude-dir=.git 2>/dev/null; then
    echo "ERROR: Potential API keys detected"
    exit 1
fi

# Run linting
if command -v ruff &> /dev/null; then
    python -m ruff check src/ tests/ 2>/dev/null || {
        echo "WARNING: Linting issues found"
    }
fi

echo "Pre-commit checks passed"
exit 0
```

### Performance Optimization

For large repositories:

```bash
# Enable partial clone for faster operations
git config core.preloadindex true
git config core.fscache true  # Windows
git config gc.auto 256

# Use shallow clones for CI/CD
git clone --depth 1 <repo-url>

# Optimize for trading bot development
git config push.default simple
git config pull.rebase false
git config init.defaultBranch main
```

### Backup and Recovery

#### Daily Automated Backup:
```bash
#!/bin/bash
# backup_repo.sh

backup_dir="backups/$(date +%Y%m%d)"
mkdir -p "$backup_dir"

# Create repository bundle
git bundle create "$backup_dir/repo.bundle" --all

# Archive working directory
tar -czf "$backup_dir/workspace.tar.gz" \
    --exclude=".git" \
    --exclude=".venv" \
    --exclude="node_modules" \
    --exclude="__pycache__" \
    .

echo "Backup created: $backup_dir"
```

### Integration with Cursor IDE

Add to `.vscode/settings.json`:

```json
{
  "git.autofetch": true,
  "git.autofetchPeriod": 180,
  "git.confirmSync": false,
  "git.enableSmartCommit": true,
  "git.postCommitCommand": "push",
  "git.showPushSuccessNotification": true,
  "git.suggestSmartCommit": true
}
```

### Monitoring and Alerts

Track repository health with scripts:

```bash
# monitor_repo.sh
#!/bin/bash

# Check if push is needed
if [ "$(git rev-list HEAD...origin/main --count)" -gt 0 ]; then
    echo "WARNING: Local commits not pushed to remote"
    git push origin main
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "WARNING: Uncommitted changes detected"
    git status --porcelain
fi

# Check repository size
repo_size=$(du -sh .git | cut -f1)
echo "Repository size: $repo_size"
```

## Git Workflow Enforcement

### MANDATORY Git Actions

After **EVERY** development session:

1. ✅ `git add .` - Stage all changes
2. ✅ `git commit -m "..."` - Commit with descriptive message  
3. ✅ `git push origin main` - Push to remote immediately
4. ✅ `git status` - Verify clean state

### Success Metrics

Track git workflow health:
- **Commit Frequency**: Minimum 1 commit per development session
- **Push Latency**: Maximum 1 hour between commit and push
- **Message Quality**: All commits follow conventional format
- **Repository Size**: Keep under 1GB total size
- **Conflict Resolution**: Average <15 minutes per conflict

This automated git workflow ensures continuous integration, prevents data loss, and maintains high-quality version control for the trading bot project. 