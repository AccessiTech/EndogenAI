FROM python:3.11-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml .
COPY src/ src/

RUN uv sync --no-dev

EXPOSE 8163

ENV MO_PORT=8163

CMD ["uv", "run", "python", "-m", "uvicorn", "motor_output.server:app", "--host", "0.0.0.0", "--port", "8163"]
