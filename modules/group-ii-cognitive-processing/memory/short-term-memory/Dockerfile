# Dockerfile for short-term-memory module
# Build context: repo root (so shared packages are accessible)
# Build: docker build -f modules/group-ii-cognitive-processing/memory/short-term-memory/Dockerfile .

FROM python:3.11-slim

RUN pip install --no-cache-dir uv

WORKDIR /repo

# Shared local dependencies (copied first for layer caching)
COPY shared/vector-store/python/ shared/vector-store/python/
COPY shared/a2a/python/ shared/a2a/python/

# Module source
COPY modules/group-ii-cognitive-processing/memory/short-term-memory/ \
     modules/group-ii-cognitive-processing/memory/short-term-memory/

WORKDIR /repo/modules/group-ii-cognitive-processing/memory/short-term-memory

RUN uv sync --no-dev

EXPOSE 8202 8302

HEALTHCHECK --interval=10s --timeout=5s --start-period=20s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8202/.well-known/agent-card.json')"

CMD ["uv", "run", "serve"]
