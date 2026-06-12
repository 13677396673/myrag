# ═══════════════════════════════════════════════════════════
# MyRAG 前端 — Dockerfile（多阶段构建）
# ═══════════════════════════════════════════════════════════

# ── Stage 1: 构建 ──
FROM node:20-alpine AS build

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

# ── Stage 2: Nginx 运行 ──
FROM nginx:alpine

# 复制构建产物
COPY --from=build /app/dist /usr/share/nginx/html

# 复制 Nginx 配置
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
