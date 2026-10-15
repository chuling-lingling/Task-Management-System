"""手动/定时发送到期提醒邮件。

用法（在项目根目录执行）：

    python scripts/send_reminders.py

设计上它与 FastAPI 的后台定时任务是二选一的提醒发送方式：
- 已开启 enable_reminder_worker：本脚本可用于补发或手动验证；
- 关闭了后台任务（如多 worker 部署）：用 cron / 任务计划程序周期性调用本脚本。

扫描逻辑见 app.services.reminder.send_due_reminders。
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
)

# 把 backend 目录加入导入路径，使脚本能直接 import app.*
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import SessionLocal  # noqa: E402
from app.services.reminder import send_due_reminders  # noqa: E402


def main() -> int:
    db = SessionLocal()
    try:
        sent = send_due_reminders(db)
        print(f"发送提醒邮件 {sent} 封")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
