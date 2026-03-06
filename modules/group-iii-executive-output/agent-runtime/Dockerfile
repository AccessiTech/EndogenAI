FROM python:3.11-slim

# Install uv
RUN pip install --no-cache-dir uv

WORKDIR /repo

# Shared local dependencies — paths relative to repo-root build context
COPY shared/vector-store/python/ shared/vector-store/python/
COPY shared/a2a/python/ shared/a2a/python/

# Module source (preserves pyproject.toml, src/, agent-card.json, etc.)
COPY modules/group-iii-executive-output/agent-runtime/ \
     modules/group-iii-executive-output/agent-runtime/

WORKDIR /repo/modules/group-iii-executive-output/agent-runtime

# Install dependencies
RUN uv sync --no-dev

EXPOSE 8162

ENV AR_PORT=8162 \
    MOTOR_OUTPUT_URL=http://motor-output:8163 \
    EXECUTIVE_AGENT_URL=http://executive-agent:8161

CMD ["uv", "run", "serve"]
