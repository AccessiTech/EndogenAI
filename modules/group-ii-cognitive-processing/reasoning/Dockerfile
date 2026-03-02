# Dockerfile for reasoning module
# Build context: repo root (so shared packages are accessible)
# Build: docker build -f modules/group-ii-cognitive-processing/reasoning/Dockerfile .

FROM python:3.11-slim

RUN pip install --no-cache-dir uv

WORKDIR /repo

# Shared local dependencies (copied first for layer caching)
COPY shared/vector-store/python/ shared/vector-store/python/
COPY shared/a2a/python/ shared/a2a/python/

# Module source
COPY modules/group-ii-cognitive-processing/reasoning/ \
     modules/group-ii-cognitive-processing/reasoning/

WORKDIR /repo/modules/group-ii-cognitive-processing/reasoning

RUN uv sync --no-dev

EXPOSE 8206 8306

HEALTHCHECK --interval=10s --timeout=5s --start-period=20s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8206/.well-known/agent-card.json')"

CMD ["uv", "run", "serve"]
