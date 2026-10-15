# syntax=docker/dockerfile:1

# ---------- 1) 构建前端（多阶段） ----------
FROM node:22-slim AS frontend-builder
WORKDIR /build
# 先只拷依赖清单，利用层缓存
COPY frontend/package.json frontend/package-lock.json ./
RUN npm install --ignore-scripts
# 再拷源码并构建
COPY frontend/ ./
RUN npm run build

# ---------- 2) 运行后端 ----------
FROM python:3.13-slim AS runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Shanghai

WORKDIR /app

# 仅保留证书等基础包；cryptography / argon2 在 slim 上通常有预编译 wheel
# tzdata 用于支持 TZ 时区（见下方 ENV TZ）
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY backend/ ./backend/
COPY scripts/ ./scripts/
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 把构建好的前端静态文件放进 backend 同级；main.py 会自动托管 frontend/dist
COPY --from=frontend-builder /build/dist ./frontend/dist

EXPOSE 8000

# 数据库就绪后先幂等建表，再用 exec 启动（确保容器 PID 1 是 uvicorn，信号能正确传递）
CMD ["sh", "-c", "python scripts/init_db.py && exec python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000"]
