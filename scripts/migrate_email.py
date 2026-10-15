"""幂等迁移：为 users / tasks 表补充邮箱与提醒相关列。

用法（在项目根目录执行）：

    python scripts/migrate_email.py

正常情况下应用启动时已通过 lifespan 自动执行 ensure_email_columns()，
本脚本用于独立初始化或排查列缺失问题。
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
)

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.db.migrate import ensure_email_columns  # noqa: E402


def main() -> int:
    ensure_email_columns()
    print("邮箱相关列迁移检查完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
