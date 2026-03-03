FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency manifests
COPY pyproject.toml ./

# Copy shared packages (path dependencies)
COPY ../../../shared/vector-store/python /shared/vector-store/python
COPY ../../../shared/a2a/python /shared/a2a/python

# Sync dependencies via uv
RUN uv sync --no-dev

# Copy source
COPY src/ ./src/
COPY policies/ ./policies/

# Copy config files
COPY identity.config.json ./
COPY vector-store.config.json ./
COPY embedding.config.json ./
COPY agent-card.json ./

# Expose A2A and MCP ports
EXPOSE 8161 8261

ENV PYTHONUNBUFFERED=1 \
    EA_PORT=8161 \
    MCP_PORT=8261

CMD ["uv", "run", "serve"]
