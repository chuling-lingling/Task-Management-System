"""SMTP 邮件发送。

设计原则：
- 发件凭据全部来自配置（.env），绝不进代码或数据库。
- 任何网络/认证异常都**就地吞掉只记日志**，绝不向上抛出，
  否则会影响正常的任务增删改流程（发信是旁路，不是主链路）。
"""

from __future__ import annotations

import logging
import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def send_reminder_email(to_address: str, subject: str, body: str) -> bool:
    """发送一封纯文本提醒邮件。成功返回 True，配置缺失或发送失败返回 False。"""
    settings = get_settings()
    if not settings.smtp_host or not settings.smtp_user or not settings.smtp_password:
        logger.warning(
            "SMTP 未配置（smtp_host / smtp_user / smtp_password 需同时填写），跳过发送 to=%s",
            to_address,
        )
        return False

    message = EmailMessage()
    message["Subject"] = subject
    from_addr = settings.smtp_from_address or settings.smtp_user
    message["From"] = f"{settings.smtp_from_name} <{from_addr}>"
    message["To"] = to_address
    message.set_content(body)

    try:
        if settings.smtp_use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(
                settings.smtp_host, settings.smtp_port, timeout=10, context=context
            ) as server:
                server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(message)
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
                server.starttls(context=ssl.create_default_context())
                server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(message)
        logger.info("提醒邮件已发往 %s", to_address)
        return True
    except Exception as exc:  # noqa: BLE001 - 旁路能力，任何异常都不能外泄
        logger.error("发送提醒邮件失败 to=%s: %s", to_address, exc)
        return False
