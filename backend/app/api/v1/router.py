"""API v1 路由聚合。

后续阶段在此挂载子路由：
- M3 认证：已挂载
- M4 任务：已挂载
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import auth, tasks

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(tasks.router)
