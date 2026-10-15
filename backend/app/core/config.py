"""应用配置。

统一从项目根目录的 .env 读取，任何模块都通过 get_settings() 取值，
禁止在业务代码里散落 os.getenv。
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py → 上溯三级即为项目根目录，保证任意 cwd 都能定位 .env
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---------------- 服务 ----------------
    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    cors_origins: str = "http://localhost:5173"

    # ---------------- 数据库 ----------------
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_db: str = "task_system"
    database_url: str = ""
    sql_echo: bool = False
    # 连接池：单进程默认 10，峰值可临时借用 max_overflow 个。并发用户多或跑多 worker 时调大。
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_recycle: int = 3600

    # ---------------- 邮件提醒（SMTP）----------------
    # 发件账号：系统级统一发件人，凭据只放 .env，绝不进代码/库。
    # 用户在设置页填的是「收件邮箱」，可与发件账号是同一个邮箱（发给自己）。
    smtp_host: str = ""
    smtp_port: int = 465
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_name: str = "任务管理系统"
    # 发件人邮箱（From 显示地址）。事务中继（如 Resend）要求与登录用户名分离；
    # 阿里云邮件推送等"From=登录名"的服务留空即可，回退用 smtp_user。
    smtp_from_address: str = ""
    smtp_use_ssl: bool = True
    frontend_url: str = "http://localhost:5173"
    reminder_interval_seconds: int = 60
    enable_reminder_worker: bool = True


    # ---------------- 安全 ----------------
    jwt_secret_key: str = "change_me_dev_only_replace_with_random_string"
    jwt_algorithm: str = "HS256"
    jwt_expire_days: int = 7

    @property
    def cors_origins_list(self) -> List[str]:
        """把逗号分隔的 CORS 配置解析成列表。"""
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def sqlalchemy_uri(self) -> str:
        """优先使用完整连接串，否则由分项拼装。密码需转义以容纳特殊字符。"""
        if self.database_url.strip():
            return self.database_url.strip()
        password = quote_plus(self.mysql_password)
        return (
            f"mysql+pymysql://{quote_plus(self.mysql_user)}:{password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_db}?charset=utf8mb4"
        )

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """返回进程内唯一的配置实例。"""
    return Settings()
