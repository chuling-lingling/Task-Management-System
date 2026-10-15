"""数据库引擎与会话。

对外只暴露两个东西：engine（脚本用）和 get_db（FastAPI 依赖用）。
"""

from __future__ import annotations

from typing import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()


def build_engine() -> Engine:
    """按配置创建引擎。

    pool_pre_ping 用于自动剔除被 MySQL wait_timeout 断开的旧连接；
    pool_recycle 主动回收长连接，避免第二天首次请求报错；
    pool_size / max_overflow 控制并发连接上限，按并发量与 worker 数调整。
    """
    return create_engine(
        settings.sqlalchemy_uri,
        echo=settings.sql_echo,
        pool_pre_ping=True,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_recycle=settings.db_pool_recycle,
        future=True,
    )


engine = build_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,  # 提交后仍可读取已加载属性，避免接口返回前再查一次
)


def get_db() -> Iterator[Session]:
    """FastAPI 依赖项：每个请求一个会话，结束后必定关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
