#!/bin/bash
# Fix Cursor shell environment issues

echo "🔧 Fixing Cursor shell environment issues..."

# 1. Create a fast-loading shell profile for Cursor
echo "📝 Creating optimized shell profile..."
cat > ~/.zshrc_cursor << 'EOF'
# Minimal .zshrc for Cursor IDE
export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"

# Conda (lazy loading)
if [ -f "/Users/kaushal/opt/anaconda3/etc/profile.d/conda.sh" ]; then
    . "/Users/kaushal/opt/anaconda3/etc/profile.d/conda.sh"
fi

# Direnv hook (essential for project environments)
eval "$(direnv hook zsh)"

# Essential exports
export SHELL=/bin/zsh
export TERM=xterm-256color
EOF

# 2. Set Cursor-specific environment variables
echo "⚙️  Setting Cursor environment variables..."
mkdir -p ~/.config/cursor

cat > ~/.config/cursor/shell_env << 'EOF'
# Fast shell environment for Cursor
export SHELL_SESSION_TIMEOUT=10
export DIRENV_WARN_TIMEOUT=5s
EOF

# 3. Create a project-specific launch script
echo "🚀 Creating project launch script..."
cat > ./cursor_start.sh << 'EOF'
#!/bin/bash
# Start Cursor with optimized environment
export SHELL_SESSION_TIMEOUT=10
export DIRENV_WARN_TIMEOUT=5s
cd "$(dirname "$0")"
/Applications/Cursor.app/Contents/MacOS/Cursor . &
EOF

chmod +x ./cursor_start.sh

echo "✅ Fixes applied! Try these solutions:"
echo ""
echo "1. Restart Cursor and wait for it to initialize"
echo "2. If still slow, run: ./cursor_start.sh"
echo "3. In Cursor settings, increase shell timeout:"
echo "   - Open Cursor Settings (Cmd+,)"
echo "   - Search for 'shell'"
echo "   - Increase 'Terminal: Integrated Shell Timeout' to 30 seconds"
echo ""
echo "4. Alternative: Use the optimized shell profile:"
echo "   export ZDOTDIR=~/.config/zsh && mkdir -p ~/.config/zsh"
echo "   cp ~/.zshrc_cursor ~/.config/zsh/.zshrc"
echo ""
echo "Your original .envrc is backed up as .envrc.backup" 