# Builder: uses npm (standalone context — no workspace pnpm-lock.yaml available)
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json ./
# npm install installs all deps (including devDependencies needed for tsc build)
RUN npm install
COPY . .
RUN npm run build

# Runtime: production deps only
FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/package.json ./
RUN npm install --omit=dev
COPY --from=builder /app/dist ./dist
EXPOSE 3001
USER 65534
CMD ["node", "dist/index.js"]
