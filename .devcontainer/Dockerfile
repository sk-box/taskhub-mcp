FROM mcr.microsoft.com/devcontainers/python:3.10

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tmux \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js LTS
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install uv for the vscode user
USER vscode
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/home/vscode/.local/bin:${PATH}"

# Switch back to root for workspace setup
USER root

# Setup workspace
WORKDIR /workspace

# Install TaskHub MCP from public repository
ENV PATH="/home/vscode/.local/bin:${PATH}"
RUN uv pip install --system git+https://github.com/sk-box/taskhub-mcp.git

# Install Claude Code
# Switch to vscode user for npm global installation
USER vscode
RUN mkdir -p ~/.npm-global && \
    npm config set prefix '~/.npm-global' && \
    echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc && \
    export PATH=~/.npm-global/bin:$PATH && \
    npm install -g @anthropic-ai/claude-code

# Switch back to root
USER root

# Environment variables will be set by devcontainer.json
# TASKHUB_DATA_DIR will be dynamically set based on workspace folder
ENV TASKHUB_PORT=5173

# Create .mcp.json template for workspace
RUN echo '{\n  "mcpServers": {\n    "taskhub": {\n      "type": "sse",\n      "url": "http://localhost:'${TASKHUB_PORT}'/mcp"\n    }\n  }\n}' > /tmp/mcp.json.template

# Expose TaskHub port
EXPOSE 5173

# Set the default user
USER vscode

# Update PATH for Claude Code
ENV PATH="/home/vscode/.npm-global/bin:${PATH}"

# Add helpful aliases
RUN echo 'alias taskhub-status="ps aux | grep taskhub-mcp | grep -v grep || echo \"TaskHub MCP is not running\""' >> ~/.bashrc && \
    echo 'alias taskhub-logs="tail -f \${TASKHUB_DATA_DIR}/logs/taskhub-mcp.log"' >> ~/.bashrc && \
    echo 'alias taskhub-start="nohup taskhub-mcp > \${TASKHUB_DATA_DIR}/logs/taskhub-mcp.log 2>&1 & echo \$! > \${TASKHUB_DATA_DIR}/taskhub-mcp.pid && echo \"TaskHub MCP started (PID: \$(cat \${TASKHUB_DATA_DIR}/taskhub-mcp.pid))\""' >> ~/.bashrc && \
    echo 'alias taskhub-stop="if [ -f \${TASKHUB_DATA_DIR}/taskhub-mcp.pid ]; then kill \$(cat \${TASKHUB_DATA_DIR}/taskhub-mcp.pid) && rm \${TASKHUB_DATA_DIR}/taskhub-mcp.pid && echo \"TaskHub MCP stopped\"; else echo \"PID file not found\"; fi"' >> ~/.bashrc && \
    echo 'alias taskhub-restart="taskhub-stop && sleep 1 && taskhub-start"' >> ~/.bashrc