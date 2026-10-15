"""密码哈希与访问令牌。

密码：Argon2id（argon2-cffi），盐值由库内部管理，不自己拼格式串。
令牌：JWT HS256，载荷只放 sub(user_id) 和过期时间，不塞任何敏感信息。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.config import get_settings
from app.core.errors import AppError

settings = get_settings()

_hasher = PasswordHasher()

# 账号不存在时用它跑一次哈希校验，让响应时间与"密码错误"一致，
# 避免攻击者通过响应快慢枚举出哪些用户名存在。
_DUMMY_HASH = _hasher.hash("account-does-not-exist")


def hash_password(raw_password: str) -> str:
    """生成密码哈希。明文密码绝不落盘。"""
    return _hasher.hash(raw_password)


def verify_password(raw_password: str, password_hash: str) -> bool:
    """校验密码，任何失败（不匹配、哈希损坏）都返回 False，不抛异常给上层。"""
    try:
        _hasher.verify(password_hash, raw_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
    return True


def burn_verify_slot(raw_password: str) -> None:
    """账号不存在时消耗一段等价的哈希计算时间，仅为了对齐响应耗时。"""
    verify_password(raw_password, _DUMMY_HASH)


def create_access_token(user_id: int) -> tuple[str, int]:
    """签发令牌，返回 (令牌字符串, 有效期秒数)。"""
    expires_in = int(timedelta(days=settings.jwt_expire_days).total_seconds())
    issued_at = datetime.now(timezone.utc)
    payload: dict[str, object] = {
        "sub": str(user_id),
        "iat": issued_at,
        "exp": issued_at + timedelta(seconds=expires_in),
        "type": "access",
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, expires_in


def decode_access_token(token: str) -> int:
    """解析令牌并返回 user_id。所有不合法情况统一转成 401，不区分细节以免泄漏信息。"""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise AppError(401, "登录已过期，请重新登录", "token_expired") from exc
    except jwt.PyJWTError as exc:
        raise AppError(401, "身份凭证无效，请重新登录", "token_invalid") from exc

    if payload.get("type") != "access":
        raise AppError(401, "身份凭证无效，请重新登录", "token_invalid")

    subject = payload.get("sub")
    if not subject or not str(subject).isdigit():
        raise AppError(401, "身份凭证无效，请重新登录", "token_invalid")
    return int(subject)
