#!/usr/bin/env bash
# gen_certs.sh — Generate self-signed mTLS CA and per-module certificates.
#
# Usage:
#   bash scripts/gen_certs.sh
#   bash scripts/gen_certs.sh --modules "working-memory sensory-input"
#
# Output: security/certs/{ca,<module>}.{crt,key}
#
# NOTE: security/certs/ is gitignored — never commit private keys.
# Phase 10 upgrade: replace with SPIFFE/SPIRE for automatic rotation.
set -eu

CERTS_DIR="security/certs"
mkdir -p "$CERTS_DIR"

# Generate root CA
openssl req -x509 -newkey rsa:4096 -keyout "$CERTS_DIR/ca.key" \
  -out "$CERTS_DIR/ca.crt" -days 365 -nodes \
  -subj "/CN=endogenai-ca/O=EndogenAI"
echo "Generated: CA → $CERTS_DIR/ca.{crt,key}"

# Default modules list (all 16 services)
DEFAULT_MODULES="sensory-input perception attention-filtering working-memory \
  short-term-memory long-term-memory episodic-memory reasoning affective \
  executive-agent agent-runtime motor-output learning-adaptation metacognition \
  mcp-server gateway"

MODULES="${1:-$DEFAULT_MODULES}"

for MODULE in $MODULES; do
  openssl req -newkey rsa:2048 -keyout "$CERTS_DIR/$MODULE.key" \
    -out "$CERTS_DIR/$MODULE.csr" -nodes \
    -subj "/CN=$MODULE/O=EndogenAI"
  openssl x509 -req -in "$CERTS_DIR/$MODULE.csr" \
    -CA "$CERTS_DIR/ca.crt" -CAkey "$CERTS_DIR/ca.key" \
    -CAcreateserial -out "$CERTS_DIR/$MODULE.crt" -days 365
  rm "$CERTS_DIR/$MODULE.csr"
  echo "Generated: $MODULE → $CERTS_DIR/$MODULE.{crt,key}"
done
echo "Done — $CERTS_DIR/ contains CA + $(echo "$MODULES" | wc -w) module certificates."
