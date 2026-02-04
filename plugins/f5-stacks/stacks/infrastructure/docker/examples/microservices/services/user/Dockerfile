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

RUN apk add --no-cache curl

COPY --from=builder --chown=nodejs:nodejs /app/dist ./dist
COPY --from=builder --chown=nodejs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nodejs:nodejs /app/package.json ./

ENV NODE_ENV=production
ENV SERVICE_NAME=user-service
ENV SERVICE_PORT=3001

USER nodejs

EXPOSE 3001

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:3001/health || exit 1

CMD ["node", "dist/server.js"]
