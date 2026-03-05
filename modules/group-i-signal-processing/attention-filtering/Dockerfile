# Dockerfile for attention-filtering module
# Build context: repo root (so shared packages are accessible)
# Build: docker build -f modules/group-i-signal-processing/attention-filtering/Dockerfile .

FROM python:3.11-slim

RUN pip install --no-cache-dir "uv==0.6.1"

WORKDIR /repo

# Shared local dependencies (copied first for layer caching)
COPY shared/vector-store/python/ shared/vector-store/python/
COPY shared/a2a/python/ shared/a2a/python/

# Module source
COPY modules/group-i-signal-processing/attention-filtering/ \
     modules/group-i-signal-processing/attention-filtering/

WORKDIR /repo/modules/group-i-signal-processing/attention-filtering

RUN uv sync --no-dev

EXPOSE 8102

HEALTHCHECK --interval=10s --timeout=5s --start-period=20s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8102/.well-known/agent-card.json')"

CMD ["uv", "run", "python", "-m", "uvicorn", "endogenai_attention_filtering.server:app", "--host", "0.0.0.0", "--port", "8102"]
