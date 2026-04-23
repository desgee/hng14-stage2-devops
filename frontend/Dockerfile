# Stage 1 — deps
FROM node:20-slim AS deps

WORKDIR /build

COPY frontend/package.json ./
COPY frontend/package-lock.json ./

RUN npm ci --omit=dev

# Stage 2 — runtime
FROM node:20-slim AS runtime

WORKDIR /app

COPY --from=deps /build/node_modules ./node_modules
COPY frontend/app.js .
COPY frontend/views ./views
COPY frontend/package.json .

USER node

EXPOSE 3000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000/', r => process.exit(r.statusCode === 200 ? 0 : 1)).on('error', () => process.exit(1))"

CMD ["node", "app.js"]