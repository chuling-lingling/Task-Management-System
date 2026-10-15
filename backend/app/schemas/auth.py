"""认证接口的入参出参模型。"""

from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

# 用户名白名单：字母、数字、下划线。避免空格、表情、SQL 符号进库
USERNAME_PATTERN = r"^[A-Za-z0-9_]+$"

# 邮箱格式：轻量正则，避免引入 email-validator 依赖
EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class RegisterRequest(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=32,
        pattern=USERNAME_PATTERN,
        strip_whitespace=True,
        examples=["alice"],
        description="3-32 位，仅支持字母、数字、下划线",
    )
    password: str = Field(
        min_length=8,
        max_length=64,
        examples=["Passw0rd2026"],
        description="8-64 位，不做字符类型限制",
    )


class LoginRequest(BaseModel):
    """登录时不套用注册的格式白名单，老账号或特殊用户名仍能登录。"""

    username: str = Field(min_length=1, max_length=32, strip_whitespace=True, examples=["alice"])
    password: str = Field(min_length=1, max_length=64)


class UserRead(BaseModel):
    """对外返回的用户信息，**刻意不包含 password_hash**。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str | None = Field(default=None, description="提醒邮件收件人，可空")
    created_at: datetime


class UpdateEmailRequest(BaseModel):
    """更新当前用户的收件邮箱。传 null 或空串表示清空（不再接收提醒）。"""

    email: str | None = Field(default=None, max_length=254, examples=["me@example.com"])

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            return None
        if not re.match(EMAIL_PATTERN, cleaned):
            raise ValueError("邮箱格式不正确")
        return cleaned


class TokenResponse(BaseModel):
    """登录响应。一并带上用户信息，省掉前端再调一次 /me。"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="令牌有效期，单位秒")
    user: UserRead
