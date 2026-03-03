FROM python:3.11-slim

WORKDIR /app

RUN pip install uv

# Copy shared packages (path dependencies) — paths relative to repo-root build context
COPY shared/vector-store/python /shared/vector-store/python
COPY shared/a2a/python /shared/a2a/python

COPY pyproject.toml .
COPY src/ src/

RUN uv sync --no-dev

EXPOSE 8163

ENV MO_PORT=8163

CMD ["uv", "run", "python", "-m", "uvicorn", "motor_output.server:app", "--host", "0.0.0.0", "--port", "8163"]
