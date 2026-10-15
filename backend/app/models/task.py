"""任务表模型。

时间字段语义严格区分，禁止互相复用：
- created_at：记录写入系统的时刻，写入后永不变更。
- planned_at：用户设定的计划执行时间，可为空，可随时修改。
- completed_at：真正标记完成的时刻，NULL 表示未完成，这是完成状态的唯一真源。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# 提醒频率取值：once=只发一次；hourly=每小时一次；daily=每天一次（持续直到完成）
EMAIL_REMINDER_MODES = ("once", "hourly", "daily")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属用户，所有查询都必须带这个维度",
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="任务标题")
    description: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
        default=None,
        comment="任务描述，可为空",
    )
    planned_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        default=None,
        comment="计划执行时间，可为空。语义完全不同于 created_at",
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        default=None,
        comment="完成时刻；NULL 表示未完成。完成状态的唯一真源",
    )
    email_reminder_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否启用邮箱提醒，默认关闭",
    )
    email_reminder_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        default=None,
        comment="提醒邮件成功发送时刻；NULL 表示尚未成功发送，防重复发送的真源",
    )
    email_reminder_mode: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="once",
        comment="提醒频率：once=只发一次，hourly=每小时一次，daily=每天一次（持续直到完成）",
    )
    email_reminder_failed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        default=None,
        comment="最近一次发信失败时刻；用于失败重试退避，避免反复轰炸 SMTP",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
        comment="任务创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
        comment="最后一次修改时间",
    )

    user: Mapped["User"] = relationship(back_populates="tasks")

    @property
    def is_completed(self) -> bool:
        """派生属性，由 completed_at 推导，不额外存字段，杜绝两处状态不一致。"""
        return self.completed_at is not None

    __table_args__ = (
        # 列表查询永远带 user_id，且按 completed_at 过滤或排序，复合索引即可覆盖
        Index("ix_tasks_user_completed", "user_id", "completed_at"),
        # 提醒扫描按「已启用 + 计划时间」过滤，加速后台查询
        Index("ix_tasks_reminder", "email_reminder_enabled", "planned_at"),
    )
