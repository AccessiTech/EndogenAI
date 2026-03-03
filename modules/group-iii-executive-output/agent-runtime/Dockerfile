FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy shared packages first (for path dependencies)
COPY shared/vector-store/python /shared/vector-store/python
COPY shared/a2a/python /shared/a2a/python

# Copy module source
COPY modules/group-iii-executive-output/agent-runtime /app

# Install dependencies
RUN uv sync --no-dev

EXPOSE 8162

ENV AR_PORT=8162 \
    MOTOR_OUTPUT_URL=http://motor-output:8163 \
    EXECUTIVE_AGENT_URL=http://executive-agent:8161

CMD ["uv", "run", "serve"]
