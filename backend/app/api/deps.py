"""接口层公共依赖。

所有需要登录的接口都通过 Depends(get_current_user) 取当前用户，
绝不信任请求参数里的 user_id。
"""

from __future__ import annotations

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

bearer_scheme = HTTPBearer(
    auto_error=False,
    description="请求头格式：Authorization: Bearer <access_token>",
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """解析 Bearer 令牌并取出用户。

    令牌有效但用户已被删除时同样按 401 处理。
    """
    if credentials is None:
        raise AppError(401, "请先登录", "not_authenticated")

    user_id = decode_access_token(credentials.credentials)
    user = db.get(User, user_id)
    if user is None:
        raise AppError(401, "账号不存在，请重新登录", "user_not_found")
    return user
