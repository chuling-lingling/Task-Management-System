"""一次性建表脚本。

在项目根目录执行：

    python scripts/init_db.py

脚本会先确认目标数据库存在（不存在则创建，需要 CREATE DATABASE 权限），
再按 ORM 模型创建全部表。已存在的表不会被改动；
若修改了模型字段，请手动删表后重跑，或引入迁移工具。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pymysql  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.models import Task, User  # noqa: E402,F401  (导入即注册模型)

DATABASE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")


def ensure_database_exists() -> None:
    """目标库不存在则创建。库名先做白名单校验，避免拼进 DDL 出问题。"""
    settings = get_settings()
    db_name = settings.mysql_db
    if not DATABASE_NAME_PATTERN.fullmatch(db_name):
        raise ValueError(f"MYSQL_DB 只允许字母、数字和下划线，当前值非法：{db_name!r}")

    connection = pymysql.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
        charset="utf8mb4",
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        connection.commit()
    finally:
        connection.close()


def create_tables() -> None:
    """按 Base.metadata 创建全部表，已存在则跳过。"""
    Base.metadata.create_all(bind=engine)


def verify_tables() -> None:
    """逐表做一次探测查询，确认真的可读写。"""
    with engine.connect() as connection:
        for table_name in sorted(Base.metadata.tables):
            connection.execute(text(f"SELECT 1 FROM `{table_name}` LIMIT 1"))


def main() -> None:
    settings = get_settings()
    print(f"目标数据库：{settings.mysql_user}@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_db}")
    try:
        ensure_database_exists()
        print("数据库已就绪")
        create_tables()
        print(f"建表完成，共 {len(Base.metadata.tables)} 张表：{', '.join(sorted(Base.metadata.tables))}")
        verify_tables()
        print("全部表可读，初始化成功")
    except pymysql.err.OperationalError as exc:
        print(f"连接 MySQL 失败：{exc}")
        print("请确认：MySQL 服务已启动，且 .env 中 MYSQL_HOST / MYSQL_PORT / MYSQL_USER / MYSQL_PASSWORD 填写正确")
        sys.exit(1)
    except ValueError as exc:
        print(f"配置错误：{exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
