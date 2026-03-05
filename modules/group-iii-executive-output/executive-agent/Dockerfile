FROM python:3.11-slim

# Install uv
RUN pip install --no-cache-dir uv

WORKDIR /repo

# Shared local dependencies (copied first for layer caching)
# Build context: repo root — paths below are relative to repo root
COPY shared/vector-store/python/ shared/vector-store/python/
COPY shared/a2a/python/ shared/a2a/python/

# Module source (preserves ./src, ./policies, pyproject.toml, config JSONs)
COPY modules/group-iii-executive-output/executive-agent/ \
     modules/group-iii-executive-output/executive-agent/

WORKDIR /repo/modules/group-iii-executive-output/executive-agent

RUN uv sync --no-dev

# Expose A2A and MCP ports
EXPOSE 8161 8261

ENV PYTHONUNBUFFERED=1 \
    EA_PORT=8161 \
    MCP_PORT=8261

CMD ["uv", "run", "serve"]
