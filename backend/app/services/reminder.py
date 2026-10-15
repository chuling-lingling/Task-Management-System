"""扫描到期任务并发送提醒邮件。

扫描条件（必须同时满足）：
- email_reminder_enabled 为真（用户勾选了提醒）
- completed_at 为空（未完成任务才提醒）
- planned_at 不为空且已 <= 当前时间（到达计划执行时间）

提醒频率（email_reminder_mode）：
- once：首次到达计划时间发一次，之后不再发（sent_at 标记后不再触发）
- hourly：首次发后，每隔 1 小时再发一次，持续直到任务完成
- daily：首次发后，每隔 1 天再发一次，持续直到任务完成

防重复真源：email_reminder_sent_at（成功发送时刻）。
失败重试：仅发送成功才标记 sent_at；失败时只标记 failed_at 并加退避窗口，
下次扫描若距上次失败不足退避窗口则跳过，超过后再尝试，避免反复轰炸 SMTP。
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.task import EMAIL_REMINDER_MODES, Task
from app.models.user import User
from app.services.email import send_reminder_email

logger = logging.getLogger(__name__)

# 失败重试退避窗口：两次失败尝试之间至少间隔这么久，避免短间隔反复重试
RETRY_BACKOFF = timedelta(minutes=5)


def _format_planned(task: Task) -> str:
    if task.planned_at is None:
        return "未设定"
    return task.planned_at.strftime("%Y-%m-%d %H:%M")


def build_reminder_body(task: Task, frontend_url: str) -> str:
    """纯文本邮件正文。"""
    lines = [
        "你好，你有一条任务的计划执行时间已到：",
        "",
        f"任务标题：{task.title}",
        f"计划执行时间：{_format_planned(task)}",
        f"打开查看：{frontend_url.rstrip('/')}/",
        "",
        "—— 任务管理系统",
    ]
    return "\n".join(lines)


def _interval_for_mode(mode: str) -> timedelta | None:
    """返回该模式两次提醒之间的最小间隔；once 返回 None（只发一次）。"""
    if mode == "hourly":
        return timedelta(hours=1)
    if mode == "daily":
        return timedelta(days=1)
    return None


def _is_due(task: Task, now: datetime) -> bool:
    """判断任务当前是否应该发送提醒（已通过扫描基础条件）。"""
    mode = task.email_reminder_mode or "once"
    if mode not in EMAIL_REMINDER_MODES:
        mode = "once"

    # 失败退避：距上次失败不足退避窗口则跳过，避免短间隔反复重试
    if task.email_reminder_failed_at is not None:
        if now - task.email_reminder_failed_at < RETRY_BACKOFF:
            return False

    interval = _interval_for_mode(mode)
    if interval is None:
        # once：从未成功发送才发
        return task.email_reminder_sent_at is None
    # hourly / daily：未发过，或距上次成功发送已超过间隔，则再发
    if task.email_reminder_sent_at is None:
        return True
    return now - task.email_reminder_sent_at >= interval


def send_due_reminders(db: Session) -> int:
    """扫描并发送到期提醒，返回成功发送的数量。"""
    settings = get_settings()
    now = datetime.now()
    statement = (
        select(Task)
        .where(
            Task.email_reminder_enabled.is_(True),
            Task.completed_at.is_(None),
            Task.planned_at.is_not(None),
            Task.planned_at <= now,
        )
    )
    due_tasks = list(db.scalars(statement).all())

    sent = 0
    changed = False
    for task in due_tasks:
        user = db.get(User, task.user_id)
        if not user or not user.email:
            # 没有收件邮箱：不发送也不标记，等用户在设置页补填后下一轮补发
            logger.info("任务 %s 无收件邮箱，跳过", task.id)
            continue

        if not _is_due(task, now):
            continue

        body = build_reminder_body(task, settings.frontend_url)
        ok = send_reminder_email(user.email, f"任务提醒：{task.title}", body)
        changed = True
        if ok:
            # 仅成功才标记已发送，失败不标记以便下一轮重试
            task.email_reminder_sent_at = now
            task.email_reminder_failed_at = None
            sent += 1
        else:
            # 仅记录失败时刻，下一轮按退避窗口重试
            task.email_reminder_failed_at = now

    if changed:
        db.commit()
    return sent
