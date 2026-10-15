"""任务接口。

所有查询都强制带上 user_id 维度，不属于自己的任务一律按 404 处理。
"""

from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.errors import AppError
from app.db.session import get_db
from app.models.task import Task
from app.models.user import User
from app.schemas.task import (
    COMPLETED_WINDOW_DAYS,
    CompletionUpdate,
    TaskCreate,
    TaskRead,
    TaskStatus,
    TaskUpdate,
)

router = APIRouter(prefix="/tasks", tags=["任务"])


def get_owned_task(task_id: int, db: Session, user: User) -> Task:
    """取出任务并校验归属。不存在或不属于当前用户，统一返回 404。"""
    task = db.get(Task, task_id)
    if task is None or task.user_id != user.id:
        raise AppError(404, "任务不存在", "task_not_found")
    return task


@router.get("", response_model=list[TaskRead], summary="任务列表")
def list_tasks(
    status: TaskStatus = Query(TaskStatus.OPEN, description="open=未完成（默认），done=最近 30 天已完成"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Task]:
    query = select(Task).where(Task.user_id == user.id)

    if status is TaskStatus.OPEN:
        # 未完成：计划执行时间升序，没填计划时间的排后面，组内按创建时间倒序
        query = query.where(Task.completed_at.is_(None)).order_by(
            Task.planned_at.is_(None),
            Task.planned_at.asc(),
            Task.created_at.desc(),
        )
    else:
        cutoff = datetime.now() - timedelta(days=COMPLETED_WINDOW_DAYS)
        query = query.where(
            Task.completed_at.is_not(None),
            Task.completed_at >= cutoff,
        ).order_by(Task.completed_at.desc())

    return list(db.scalars(query).all())


@router.post("", response_model=TaskRead, status_code=201, summary="创建任务")
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Task:
    task = Task(
        user_id=user.id,
        title=payload.title,
        description=payload.description,
        planned_at=payload.planned_at,
        email_reminder_enabled=payload.email_reminder_enabled,
        email_reminder_mode=payload.email_reminder_mode,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.patch("/{task_id}", response_model=TaskRead, summary="修改任务")
def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Task:
    task = get_owned_task(task_id, db, user)
    changes = payload.model_dump(exclude_unset=True)
    if changes:
        planned_changed = "planned_at" in changes
        mode_changed = "email_reminder_mode" in changes
        for field, value in changes.items():
            setattr(task, field, value)
        if planned_changed or mode_changed:
            # 计划时间或提醒频率被改动：重置发送/失败标记，使提醒按新规则重新计时
            task.email_reminder_sent_at = None
            task.email_reminder_failed_at = None
        db.commit()
        db.refresh(task)
    return task


@router.delete(
    "/{task_id}",
    status_code=204,
    # 必须显式声明：本文件启用了 postponed annotations，`-> None` 会被 FastAPI
    # 解析成 NoneType（真值），不设为 None 会触发 "204 must not have a response body" 断言
    response_model=None,
    summary="删除任务",
)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    task = get_owned_task(task_id, db, user)
    db.delete(task)
    db.commit()


@router.patch("/{task_id}/completion", response_model=TaskRead, summary="标记完成或恢复未完成")
def update_completion(
    task_id: int,
    payload: CompletionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Task:
    task = get_owned_task(task_id, db, user)

    if payload.completed:
        # 重复标记不覆盖首次完成时间，保持幂等
        if task.completed_at is None:
            task.completed_at = datetime.now()
    else:
        task.completed_at = None

    db.commit()
    db.refresh(task)
    return task
