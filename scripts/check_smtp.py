"""临时诊断：直接用当前 .env 配置发一封测试邮件，验证 Resend SMTP 通路。

用法：python scripts/check_smtp.py [收件人邮箱]
- 不传参时，优先用数据库里第一个已填的收件邮箱；
- 若数据库也无收件邮箱，发往发件地址自身，仅验证 SMTP 登录/发送能力。
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.config import get_settings
from app.services.email import send_reminder_email

settings = get_settings()
from_addr = settings.smtp_from_address or settings.smtp_user
print(
    "[config] host=%s port=%s user=%s from=%s password_set=%s"
    % (settings.smtp_host, settings.smtp_port, settings.smtp_user, from_addr, bool(settings.smtp_password))
)

to = sys.argv[1] if len(sys.argv) > 1 else None
if not to:
    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(settings.sqlalchemy_uri)
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT email FROM users WHERE email IS NOT NULL LIMIT 1")
            ).fetchone()
        if row:
            to = row[0]
            print("[db] 使用收件邮箱:", to)
    except Exception as exc:  # noqa: BLE001
        print("[db] 读取收件邮箱失败:", repr(exc))

if not to:
    to = from_addr
    print("[warn] 无收件邮箱，发往发件地址自身做 SMTP 连通性验证:", to)

print("[send] 发往", to)
ok = send_reminder_email(
    to,
    "任务管理系统 · SMTP 连通性测试",
    "如果你收到这封邮件，说明 Resend 发信配置成功。\n（这是一封用于验证发信链路的测试邮件，可忽略。）",
)
print("[result]", "成功（已被 Resend 接受发送）" if ok else "失败（请看上方日志中的报错）")
