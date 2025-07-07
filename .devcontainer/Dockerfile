FROM python:3.11-slim

ARG TZ
ENV TZ="$TZ"

# Install basic development tools and Solana CLI dependencies
RUN apt-get update && apt-get install -y \
  git \
  curl \
  wget \
  build-essential \
  less \
  procps \
  sudo \
  fzf \
  zsh \
  man-db \
  unzip \
  gnupg2 \
  gh \
  jq \
  pkg-config \
  libudev-dev \
  libssl-dev \
  && rm -rf /var/lib/apt/lists/*

# Install Solana CLI
RUN sh -c "$(curl -sSfL https://release.solana.com/stable/install)" && \
  echo 'export PATH="/root/.local/share/solana/install/active_release/bin:$PATH"' >> /etc/profile

# Create non-root user
ARG USERNAME=developer
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
  && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
  && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
  && chmod 0440 /etc/sudoers.d/$USERNAME

# Persist bash history
RUN SNIPPET="export PROMPT_COMMAND='history -a' && export HISTFILE=/commandhistory/.bash_history" \
  && mkdir /commandhistory \
  && touch /commandhistory/.bash_history \
  && chown -R $USERNAME /commandhistory

# Set DEVCONTAINER environment variable
ENV DEVCONTAINER=true

# Create workspace and config directories
RUN mkdir -p /workspace /home/$USERNAME/.claude /home/$USERNAME/.config/solana \
  && chown -R $USERNAME:$USERNAME /workspace /home/$USERNAME/.claude /home/$USERNAME/.config

WORKDIR /workspace

# Install delta for better git diffs
RUN ARCH=$(dpkg --print-architecture) && \
  wget "https://github.com/dandavison/delta/releases/download/0.18.2/git-delta_0.18.2_${ARCH}.deb" && \
  dpkg -i "git-delta_0.18.2_${ARCH}.deb" && \
  rm "git-delta_0.18.2_${ARCH}.deb"

# Switch to non-root user
USER $USERNAME

# Set up Python environment
ENV PYTHONUNBUFFERED=1
ENV PATH="/home/$USERNAME/.local/bin:$PATH:/home/$USERNAME/.local/share/solana/install/active_release/bin"

# Install Python development tools
RUN pip install --user --upgrade pip setuptools wheel && \
  pip install --user \
    pytest \
    pytest-asyncio \
    pytest-cov \
    ruff \
    mypy \
    ipython \
    httpx \
    aiohttp

# Set the default shell to zsh
ENV SHELL=/bin/zsh

# Install oh-my-zsh with plugins
RUN sh -c "$(wget -O- https://github.com/deluan/zsh-in-docker/releases/download/v1.2.0/zsh-in-docker.sh)" -- \
  -p git \
  -p fzf \
  -p python \
  -p pip \
  -a "source /usr/share/doc/fzf/examples/key-bindings.zsh" \
  -a "source /usr/share/doc/fzf/examples/completion.zsh" \
  -a "export PROMPT_COMMAND='history -a' && export HISTFILE=/commandhistory/.bash_history" \
  -a "export PATH=\"/home/$USERNAME/.local/bin:$PATH:/home/$USERNAME/.local/share/solana/install/active_release/bin\"" \
  -x

# Install Claude Code (optional)
RUN pip install --user anthropic-claude-code || echo "Claude Code installation skipped"

# Copy initialization script
COPY init-dev-env.sh /usr/local/bin/
USER root
RUN chmod +x /usr/local/bin/init-dev-env.sh && \
  echo "$USERNAME ALL=(root) NOPASSWD: /usr/local/bin/init-dev-env.sh" >> /etc/sudoers.d/$USERNAME
USER $USERNAME