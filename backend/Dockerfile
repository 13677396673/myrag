# ═══════════════════════════════════════════════════════════
# MyRAG 后端 — Dockerfile
# ═══════════════════════════════════════════════════════════

FROM python:3.11-slim

WORKDIR /app

# ── 安装系统依赖 ──
# PyMuPDF 需要 libglib, 编译 sentence-transformers 需要 gcc
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# ── 安装 Python 依赖 ──
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── 复制代码 ──
COPY backend/app/ ./app/
COPY backend/run.py .

# ── 创建数据目录（volume 挂载点） ──
RUN mkdir -p /app/data

# ── 暴露端口 ──
EXPOSE 8000

# ── 健康检查 ──
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# ── 启动 ──
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
