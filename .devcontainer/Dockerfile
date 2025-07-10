FROM python:3.12-slim

# Install only essentials
RUN apt-get update && apt-get install -y \
  git \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Create user
RUN useradd -m -s /bin/bash developer && \
  echo 'developer ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

USER developer
WORKDIR /workspace

# Install Python packages
RUN pip install --user pytest pytest-asyncio aiohttp httpx ruff

ENV PATH="/home/developer/.local/bin:$PATH"