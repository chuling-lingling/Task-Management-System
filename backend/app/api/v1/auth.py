"""认证接口：注册、登录、查看当前用户。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.errors import AppError
from app.core.security import (
    burn_verify_slot,
    create_access_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UpdateEmailRequest,
    UserRead,
)

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=UserRead, status_code=201, summary="注册账号")
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> User:
    existing_id = db.scalar(select(User.id).where(User.username == payload.username))
    if existing_id is not None:
        raise AppError(409, "该用户名已被占用", "username_taken")

    user = User(username=payload.username, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse, summary="登录并获取令牌")
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.username == payload.username))
    if user is None:
        # 走一次等价的哈希运算再返回，避免响应时间差异泄漏用户名是否存在
        burn_verify_slot(payload.password)
        raise AppError(401, "用户名或密码错误", "invalid_credentials")

    if not verify_password(payload.password, user.password_hash):
        raise AppError(401, "用户名或密码错误", "invalid_credentials")

    token, expires_in = create_access_token(user.id)
    return TokenResponse(
        access_token=token,
        expires_in=expires_in,
        user=UserRead.model_validate(user),
    )


@router.get("/me", response_model=UserRead, summary="获取当前登录用户")
def read_me(user: User = Depends(get_current_user)) -> User:
    return user


@router.patch("/me", response_model=UserRead, summary="更新当前用户信息（收件邮箱）")
def update_me(
    payload: UpdateEmailRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> User:
    """仅允许修改当前用户自己的收件邮箱。传空表示清空。"""
    user.email = payload.email
    db.commit()
    db.refresh(user)
    return user
