# Dockerfile for sensory-input module
# Build context: repo root (so shared packages are accessible)
# Build: docker build -f modules/group-i-signal-processing/sensory-input/Dockerfile .

FROM python:3.11-slim

RUN pip install --no-cache-dir "uv==0.6.1"

WORKDIR /repo

# Shared local dependencies (copied first for layer caching)
COPY shared/vector-store/python/ shared/vector-store/python/
COPY shared/a2a/python/ shared/a2a/python/

# Module source
COPY modules/group-i-signal-processing/sensory-input/ \
     modules/group-i-signal-processing/sensory-input/

WORKDIR /repo/modules/group-i-signal-processing/sensory-input

RUN uv sync --no-dev

EXPOSE 8201 8301

HEALTHCHECK --interval=10s --timeout=5s --start-period=20s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8201/.well-known/agent-card.json')"

CMD ["uv", "run", "python", "-m", "uvicorn", "endogenai_sensory_input.server:app", "--host", "0.0.0.0", "--port", "8201"]
