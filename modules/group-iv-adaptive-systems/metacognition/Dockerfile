# Dockerfile for metacognition module
# Build context: repo root (so shared packages are accessible)
# Build: docker build -f modules/group-iv-adaptive-systems/metacognition/Dockerfile .

FROM python:3.11-slim

RUN pip install --no-cache-dir "uv==0.6.1"

WORKDIR /repo

# Shared local dependencies (copied first for layer caching)
COPY shared/vector-store/python/ shared/vector-store/python/
COPY shared/a2a/python/ shared/a2a/python/

# Module source
COPY modules/group-iv-adaptive-systems/metacognition/ \
     modules/group-iv-adaptive-systems/metacognition/

WORKDIR /repo/modules/group-iv-adaptive-systems/metacognition

RUN uv sync --no-dev

EXPOSE 8171

HEALTHCHECK --interval=10s --timeout=5s --start-period=20s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8171/.well-known/agent-card.json')"

CMD ["uv", "run", "python", "-m", "uvicorn", "metacognition.server:app", "--host", "0.0.0.0", "--port", "8171"]
