# Dockerfile for infrastructure/mcp
# Build context: repo root
# Build: docker build -f infrastructure/mcp/Dockerfile .

FROM node:20-alpine AS builder
WORKDIR /workspace
COPY pnpm-workspace.yaml package.json pnpm-lock.yaml ./
COPY shared/package.json shared/
COPY infrastructure/mcp/package.json infrastructure/mcp/
RUN corepack enable && corepack prepare pnpm@9 --activate
RUN pnpm install --frozen-lockfile --filter @accessitech/mcp...

COPY shared/ shared/
COPY infrastructure/mcp/ infrastructure/mcp/
WORKDIR /workspace/infrastructure/mcp
RUN pnpm run build

FROM node:20-alpine AS runtime
RUN addgroup -g 65534 nobody-group && adduser -u 65534 -G nobody-group -s /sbin/nologin -D nobody-user 2>/dev/null || true
WORKDIR /app
COPY --from=builder /workspace/infrastructure/mcp/dist ./dist
COPY --from=builder /workspace/infrastructure/mcp/node_modules ./node_modules
COPY --from=builder /workspace/infrastructure/mcp/package.json ./
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=5s --start-period=15s \
  CMD wget -qO- http://localhost:8000/.well-known/oauth-protected-resource || exit 1
USER nobody-user
CMD ["node", "dist/run.js"]
