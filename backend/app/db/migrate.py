"""幂等迁移：为 users / tasks 表补充邮箱与提醒相关列。

项目未引入 Alembic，这里在应用启动时自愈式补齐列，并暴露成独立脚本。
所有 ALTER 都先查 information_schema 判断，确保可重复执行。
"""

from __future__ import annotations

import logging

from sqlalchemy import text

from app.db.session import engine

logger = logging.getLogger(__name__)

_COLUMN_DEFINITIONS = [
    ("users", "email", "VARCHAR(254) NULL"),
    ("tasks", "email_reminder_enabled", "TINYINT(1) NOT NULL DEFAULT 0"),
    ("tasks", "email_reminder_sent_at", "DATETIME NULL"),
    ("tasks", "email_reminder_mode", "VARCHAR(16) NOT NULL DEFAULT 'once'"),
    ("tasks", "email_reminder_failed_at", "DATETIME NULL"),
]


def ensure_email_columns() -> None:
    """确保邮箱与提醒相关列存在；缺失则补齐，已存在则跳过。"""
    try:
        with engine.begin() as conn:
            for table, column, definition in _COLUMN_DEFINITIONS:
                exists = conn.execute(
                    text(
                        "SELECT 1 FROM information_schema.columns "
                        "WHERE table_schema = DATABASE() "
                        "AND table_name = :table AND column_name = :column"
                    ),
                    {"table": table, "column": column},
                ).first()
                if exists is None:
                    logger.info("迁移：为 %s 添加列 %s (%s)", table, column, definition)
                    conn.execute(
                        text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
                    )
        logger.info("邮箱相关列迁移检查完成")
    except Exception as exc:  # noqa: BLE001 - 数据库未启动等异常不应阻断启动
        logger.error("邮箱列迁移失败（请确认数据库已启动且可连接）：%s", exc)
