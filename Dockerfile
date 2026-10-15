# syntax=docker/dockerfile:1

# 国内服务器首次构建可能很慢（apt/pip/npm 官方源）。可在 .env 配置换源
# （见 .env.example 的 APT_MIRROR / PIP_INDEX_URL / NPM_REGISTRY），
# 由 docker-compose 作为构建参数传入；不配置则用官方源，行为不变。
ARG APT_MIRROR=deb.debian.org
ARG PIP_INDEX_URL=
ARG NPM_REGISTRY=

# ---------- 1) 构建前端（多阶段） ----------
FROM node:22-slim AS frontend-builder
ARG NPM_REGISTRY
WORKDIR /build
# 只拷 package.json，不使用仓库里的 package-lock.json：
# 该锁文件在 Windows 上生成（为规避本机原生包缺失，package.json 显式锁定了
# win32 平台包），锁中缺少 Linux 平台原生包（@rollup/rollup-linux-x64-gnu、
# @esbuild/linux-x64 等）的可安装条目，容器内构建会报
# "Cannot find module @rollup/rollup-linux-x64-gnu"（npm/cli#4828）。
# 这里在 linux/x64 容器内基于 package.json 全新解析，自动装齐当前平台原生包。
COPY frontend/package.json ./
RUN npm install --ignore-scripts ${NPM_REGISTRY:+--registry=$NPM_REGISTRY}
# 再拷源码并构建
COPY frontend/ ./
RUN npm run build

# ---------- 2) 运行后端 ----------
FROM python:3.13-slim AS runtime
ARG APT_MIRROR
ARG PIP_INDEX_URL
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Shanghai

WORKDIR /app

# 仅保留证书等基础包；cryptography / argon2 在 slim 上通常有预编译 wheel
# tzdata 用于支持 TZ 时区（见下方 ENV TZ）
# APT_MIRROR 用于国内服务器换 Debian 源（不配置则为官方源）
RUN sed -i "s|deb.debian.org|${APT_MIRROR}|g" /etc/apt/sources.list.d/debian.sources /etc/apt/sources.list 2>/dev/null || true \
    && apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY backend/ ./backend/
COPY scripts/ ./scripts/
COPY requirements.txt ./
RUN pip install --no-cache-dir ${PIP_INDEX_URL:+--index-url=$PIP_INDEX_URL} -r requirements.txt

# 把构建好的前端静态文件放进 backend 同级；main.py 会自动托管 frontend/dist
COPY --from=frontend-builder /build/dist ./frontend/dist

EXPOSE 8000

# 数据库就绪后先幂等建表，再用 exec 启动（确保容器 PID 1 是 uvicorn，信号能正确传递）
CMD ["sh", "-c", "python scripts/init_db.py && exec python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000"]
