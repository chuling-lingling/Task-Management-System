"""一键冒烟：依次执行认证与任务两套端到端检查。

在项目根目录执行（后端需已启动）：

    python scripts/smoke.py
    python scripts/smoke.py http://127.0.0.1:8000   # 指定后端地址

脚本会先探活，再逐个调用 scripts/smoke_auth.py 与 scripts/smoke_tasks.py，
最后汇总通过/失败数量。任一环节失败即以非零码退出，可直接挂到 CI 上。
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import httpx

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
SCRIPTS_DIR = Path(__file__).resolve().parent
SMOKE_SCRIPTS = [
    ("认证模块", SCRIPTS_DIR / "smoke_auth.py"),
    ("任务模块", SCRIPTS_DIR / "smoke_tasks.py"),
]


def check_service() -> bool:
    try:
        response = httpx.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except httpx.HTTPError:
        return False


def main() -> None:
    print(f"目标服务：{BASE_URL}")

    if not check_service():
        print(f"无法访问 {BASE_URL}/health")
        print("请先启动后端：python -m uvicorn app.main:app --app-dir backend --reload")
        sys.exit(1)

    print("服务探活通过\n")

    results: list[tuple[str, int]] = []
    for label, script in SMOKE_SCRIPTS:
        print(f"===== {label}（{script.name}） =====")
        exit_code = subprocess.call([sys.executable, str(script), BASE_URL])
        results.append((label, exit_code))
        print()

    print("===== 汇总 =====")
    failed = [label for label, code in results if code != 0]
    for label, code in results:
        print(f"  {label}: {'通过' if code == 0 else '失败'}")

    if failed:
        print(f"\n存在失败模块：{', '.join(failed)}")
        sys.exit(1)
    print("\n全部模块冒烟通过")


if __name__ == "__main__":
    main()
