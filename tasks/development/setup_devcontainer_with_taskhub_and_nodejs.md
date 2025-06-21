---
created_at: 2025-06-22 01:08:34.578393
priority: high
status: todo
title: Setup Devcontainer with TaskHub and Node.js
updated_at: 2025-06-22 01:08:34.578402
---

# Setup Devcontainer with TaskHub and Node.js

## Overview
Configure a devcontainer environment that includes:
- TaskHub MCP pre-installed and configured
- Node.js (latest stable version) runtime environment
- Required development dependencies

## Requirements
- [ ] Create `.devcontainer/devcontainer.json` configuration
- [ ] Setup Dockerfile or use appropriate base image
- [ ] Install TaskHub MCP and its dependencies
- [ ] Install Node.js latest stable version
- [ ] Configure environment variables and settings
- [ ] Add necessary VS Code extensions
- [ ] Test the devcontainer setup

## Technical Details

### Base Image
- Use a Python 3.10+ base image (for TaskHub)
- Add Node.js repository and install latest stable

### TaskHub Installation
- Install uv package manager
- Install TaskHub MCP from current directory
- Configure MCP server settings

### Node.js Setup
- Use NodeSource repository for latest stable
- Install npm and common global packages
- Configure npm settings if needed

### VS Code Extensions
- Python extensions
- Node.js/JavaScript extensions
- MCP-related extensions if available

## Implementation Script
```bash
#!/bin/bash
# This script will be executed when implementing the task

# Create .devcontainer directory
mkdir -p .devcontainer

# Generate devcontainer.json
cat > .devcontainer/devcontainer.json << 'EOF'
{
  "name": "TaskHub MCP Development",
  "build": {
    "dockerfile": "Dockerfile"
  },
  "features": {
    "ghcr.io/devcontainers/features/python:1": {
      "version": "3.10"
    },
    "ghcr.io/devcontainers/features/node:1": {
      "version": "lts"
    }
  },
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "dbaeumer.vscode-eslint",
        "esbenp.prettier-vscode"
      ]
    }
  },
  "postCreateCommand": "uv pip install -e . && mkdir -p tasks logs db",
  "remoteUser": "vscode"
}
EOF

# Generate Dockerfile
cat > .devcontainer/Dockerfile << 'EOF'
FROM mcr.microsoft.com/devcontainers/python:3.10

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tmux \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Setup TaskHub MCP
WORKDIR /workspace
COPY . /workspace

# Install TaskHub dependencies
RUN /root/.cargo/bin/uv pip install -e .

# Expose MCP server port
EXPOSE 5173

EOF

echo "Devcontainer configuration created successfully!"
```

## Testing
1. Open the project in VS Code
2. Reopen in Container when prompted
3. Verify TaskHub MCP is installed: `uv run python -m taskhub_mcp.main --help`
4. Verify Node.js is installed: `node --version`
5. Test MCP server: `./start_server.sh`