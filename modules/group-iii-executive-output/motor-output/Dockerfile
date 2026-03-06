FROM python:3.11-slim

RUN pip install uv

WORKDIR /repo

# Shared local dependencies — paths relative to repo-root build context
COPY shared/vector-store/python/ shared/vector-store/python/
COPY shared/a2a/python/ shared/a2a/python/

# Module source (preserves pyproject.toml, src/, channels.config.json, etc.)
COPY modules/group-iii-executive-output/motor-output/ \
     modules/group-iii-executive-output/motor-output/

WORKDIR /repo/modules/group-iii-executive-output/motor-output

RUN uv sync --no-dev

EXPOSE 8163

ENV MO_PORT=8163

CMD ["uv", "run", "python", "-m", "uvicorn", "motor_output.server:app", "--host", "0.0.0.0", "--port", "8163"]
