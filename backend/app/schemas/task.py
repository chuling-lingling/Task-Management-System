"""任务接口的入参出参模型。"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.task import EMAIL_REMINDER_MODES

TITLE_MAX_LENGTH = 200
DESCRIPTION_MAX_LENGTH = 2000
COMPLETED_WINDOW_DAYS = 30


class TaskStatus(str, Enum):
    """列表筛选维度。默认只看未完成。"""

    OPEN = "open"
    DONE = "done"


def clean_title(value: str) -> str:
    """去掉首尾空白并要求非空。

    注意：不能只靠 Field 的 min_length + strip_whitespace——Pydantic 的长度校验
    发生在 strip 之前，"   " 会被判为合法 3 个字符后又被 strip 成空串。
    """
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("标题不能为空")
    return cleaned


def clean_optional_text(value: str | None) -> str | None:
    """描述允许为空串，统一归一化成 None 存库。"""
    if value is None:
        return None
    return value.strip() or None


class TaskCreate(BaseModel):
    """创建任务。`completed_at` 不接受客户端传入，只能由服务端在标记完成时写入。"""

    title: str = Field(
        min_length=1,
        max_length=TITLE_MAX_LENGTH,
        examples=["写季度总结"],
    )
    description: str | None = Field(
        default=None,
        max_length=DESCRIPTION_MAX_LENGTH,
        examples=["重点复盘留存数据"],
    )
    planned_at: datetime | None = Field(
        default=None,
        examples=["2026-10-20T09:30:00"],
        description="计划执行时间，ISO 8601 格式，可为空。语义不同于创建时间",
    )
    email_reminder_enabled: bool = Field(
        default=False,
        description="是否启用邮箱提醒，到达计划时间时发信到用户预设邮箱",
    )
    email_reminder_mode: str = Field(
        default="once",
        description="提醒频率：once=只发一次（默认），hourly=每小时一次，daily=每天一次（持续直到完成）",
    )

    @field_validator("email_reminder_mode")
    @classmethod
    def validate_reminder_mode(cls, value: str) -> str:
        if value not in EMAIL_REMINDER_MODES:
            raise ValueError("email_reminder_mode 必须是 once / hourly / daily 之一")
        return value

    @field_validator("title")
    @classmethod
    def title_must_contain_text(cls, value: str) -> str:
        return clean_title(value)

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        return clean_optional_text(value)


class TaskUpdate(BaseModel):
    """修改任务。字段全可选，用 model_dump(exclude_unset=True) 区分"未传"与"显式传空"。"""

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=TITLE_MAX_LENGTH,
        examples=["写季度总结终版"],
    )
    description: str | None = Field(
        default=None,
        max_length=DESCRIPTION_MAX_LENGTH,
    )
    planned_at: datetime | None = Field(default=None)
    email_reminder_enabled: bool | None = Field(
        default=None,
        description="是否启用邮箱提醒；不传则保持原值",
    )
    email_reminder_mode: str | None = Field(
        default=None,
        description="提醒频率；不传则保持原值",
    )

    @field_validator("email_reminder_mode")
    @classmethod
    def validate_reminder_mode_update(cls, value: str | None) -> str | None:
        if value is not None and value not in EMAIL_REMINDER_MODES:
            raise ValueError("email_reminder_mode 必须是 once / hourly / daily 之一")
        return value

    @field_validator("title")
    @classmethod
    def title_must_contain_text(cls, value: str | None) -> str | None:
        return clean_title(value) if value is not None else None

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        return clean_optional_text(value)


class CompletionUpdate(BaseModel):
    """标记完成或恢复未完成。"""

    completed: bool = Field(examples=[True], description="true 标记完成，false 恢复未完成")


class TaskRead(BaseModel):
    """对外返回的任务信息，不含 user_id（调用方天然知道是自己的任务）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    planned_at: datetime | None
    completed_at: datetime | None
    email_reminder_enabled: bool = Field(description="是否启用邮箱提醒")
    email_reminder_mode: str = Field(
        default="once",
        description="提醒频率：once=只发一次，hourly=每小时一次，daily=每天一次",
    )
    email_reminder_sent_at: datetime | None = Field(
        default=None,
        description="提醒邮件发送时刻；NULL 表示尚未发送",
    )
    created_at: datetime
    updated_at: datetime
    is_completed: bool = Field(description="由 completed_at 推导，true 表示已完成")
