# Base Python image for EndogenAI Python modules.
# Installs: uv, system dependencies.
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libssl-dev libffi-dev curl ca-certificates \
  && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "uv==0.6.1"

# Run as non-root by default (UID 65534 = nobody). Child images that need root
# for package installs should add `USER root` before those steps, then restore.
USER 65534
