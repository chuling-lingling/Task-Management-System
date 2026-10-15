"""ORM 基类。

所有模型统一继承 Base，建表脚本基于 Base.metadata 一次性创建全部表。
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """全项目唯一的声明式基类。"""
