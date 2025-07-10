# Use Node.js 20 as base image for better Claude Code CLI compatibility
FROM node:20-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for Python, Claude CLI, and security
RUN apt-get update && apt-get install -y \
    # Python and development tools
    python3 \
    python3-pip \
    python3-venv \
    # System utilities
    curl \
    git \
    zsh \
    fzf \
    ripgrep \
    # Build essentials for npm packages
    build-essential \
    # Security and networking tools
    iptables \
    netcat-openbsd \
    # Cleanup
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create a non-root user for security
RUN useradd --create-home --shell /bin/zsh --uid 1000 --gid 100 claude \
    && mkdir -p /home/claude/.anthropic \
    && chown -R claude:users /home/claude

# Switch to non-root user early
USER claude
WORKDIR /home/claude

# Set up Node.js environment for user
ENV NODE_ENV=production
ENV PATH="/home/claude/.local/bin:$PATH"

# Install Claude Code CLI globally for the user
RUN npm config set prefix '/home/claude/.local' \
    && npm install -g @anthropic-ai/claude-code

# Create Python virtual environment
RUN python3 -m venv /home/claude/venv
ENV PATH="/home/claude/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY --chown=claude:users requirements.txt /home/claude/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=claude:users . /home/claude/app/
WORKDIR /home/claude/app

# Create necessary directories and set permissions
RUN mkdir -p /home/claude/app/logs \
    && mkdir -p /home/claude/app/data \
    && mkdir -p /home/claude/.claude

# Set up shell configuration for better UX
RUN echo 'export PATH="/home/claude/.local/bin:/home/claude/venv/bin:$PATH"' >> /home/claude/.zshrc \
    && echo 'export ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY"' >> /home/claude/.zshrc \
    && echo 'alias ll="ls -la"' >> /home/claude/.zshrc \
    && echo 'alias claude-check="claude --version"' >> /home/claude/.zshrc

# Health check for the service
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)" && node --version && claude --version || exit 1

# Expose ports for services
EXPOSE 8000

# Default command
CMD ["python3", "src/combined_daemon.py"] 