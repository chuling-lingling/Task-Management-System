"""FastAPI 应用入口。"""

from __future__ import annotations

import logging
from pathlib import Path

from contextlib import asynccontextmanager

import asyncio

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.db.session import SessionLocal
from app.services.reminder import send_due_reminders

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)
settings = get_settings()


def _reminder_tick() -> None:
    """单次扫描并发送到期提醒（在线程中执行，避免阻塞事件循环）。"""
    db = SessionLocal()
    try:
        sent = send_due_reminders(db)
        if sent:
            logger.info("提醒循环：本轮发送 %d 封邮件", sent)
    finally:
        db.close()


async def reminder_loop() -> None:
    """后台定时循环：每隔 reminder_interval_seconds 扫描一次到期任务。

    注意：单进程部署下只跑一个循环。若以多 worker（--workers N）部署，需把
    enable_reminder_worker 设为 false，改用 scripts/send_reminders.py 独立调度，
    否则多个进程会重复发送。
    """
    if not settings.enable_reminder_worker:
        logger.info("提醒后台任务已禁用（enable_reminder_worker=false）")
        return
    logger.info("提醒后台任务已启动，间隔 %d 秒", settings.reminder_interval_seconds)
    while True:
        try:
            await asyncio.to_thread(_reminder_tick)
        except Exception as exc:  # noqa: BLE001
            logger.error("提醒循环异常：%s", exc)
        await asyncio.sleep(settings.reminder_interval_seconds)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # 启动时幂等补齐邮箱与提醒相关列（无 Alembic，自愈式迁移）
    from app.db.migrate import ensure_email_columns

    ensure_email_columns()
    worker = asyncio.create_task(reminder_loop())
    yield
    worker.cancel()
    try:
        await worker
    except asyncio.CancelledError:
        pass


app = FastAPI(
    lifespan=lifespan,
    title="任务管理系统 API",
    version="0.1.0",
    description="个人任务管理：注册登录、任务增删改查、完成状态与时间排序、邮件提醒",
    docs_url="/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["系统"], summary="健康检查")
def health() -> dict:
    """用于验证服务是否启动、配置是否可读。不返回任何敏感信息。"""
    return {"status": "ok", "env": settings.app_env}


def _mount_frontend() -> None:
    """生产态直接托管前端静态文件，省去额外 nginx。

    仅当项目根下的 frontend/dist 构建产物存在时才挂载；开发期不构建则无影响。
    Vue Router 使用 history 模式，未知前端路由统一回退到 index.html。
    """
    dist_dir = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    if not dist_dir.exists():
        return

    assets_dir = dist_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        # 未匹配的 API 路径仍返回 404，避免被 SPA 回退吞掉
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="not found")
        candidate = dist_dir / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(dist_dir / "index.html")


_mount_frontend()
