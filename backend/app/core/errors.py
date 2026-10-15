"""统一错误处理。

对外暴露两个东西：
- `AppError`：业务异常，携带机器可读的 code，供前端分支处理。
- `register_exception_handlers`：在 main.py 注册一次即可。

安全红线：未捕获异常的详细信息只写服务端日志，**绝不返回给客户端**，
避免泄漏数据库连接串、堆栈等敏感信息。请求体（可能含密码）也不记录。
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    """业务异常。路由里 raise 即可，由异常处理器统一转成响应。"""

    def __init__(self, status_code: int, message: str, code: str) -> None:
        self.status_code = status_code
        self.message = message
        self.code = code
        super().__init__(message)


def _body(message: str, code: str) -> dict[str, Any]:
    return {"detail": message, "code": code}


async def _handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=_body(exc.message, exc.code))


async def _handle_http_exception(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(status_code=exc.status_code, content=_body(detail, "http_error"))


async def _handle_validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
    """把 Pydantic 的原始报错整理成前端好用的字段名 + 提示。"""
    errors = [
        {
            "field": ".".join(str(part) for part in item["loc"][1:]) or "body",
            "message": item["msg"],
        }
        for item in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": errors, "code": "validation_error"})


async def _handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("未捕获异常 method=%s path=%s type=%s", request.method, request.url.path, type(exc).__name__)
    return JSONResponse(status_code=500, content=_body("服务器内部错误，请稍后重试", "internal_error"))


def register_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器，顺序无所谓，Starlette 按类型匹配。"""
    app.add_exception_handler(AppError, _handle_app_error)
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(Exception, _handle_unexpected_error)
