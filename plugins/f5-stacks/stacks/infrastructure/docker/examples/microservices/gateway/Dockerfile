# syntax=docker/dockerfile:1

# ===== Build Stage =====
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build && npm prune --production

# ===== Production Stage =====
FROM node:20-alpine AS production

WORKDIR /app

RUN addgroup -g 1001 nodejs && \
    adduser -u 1001 -G nodejs -D nodejs

# Install curl for healthcheck
RUN apk add --no-cache curl

COPY --from=builder --chown=nodejs:nodejs /app/dist ./dist
COPY --from=builder --chown=nodejs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nodejs:nodejs /app/package.json ./

ENV NODE_ENV=production

USER nodejs

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

CMD ["node", "dist/server.js"]
