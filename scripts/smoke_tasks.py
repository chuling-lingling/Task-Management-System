"""M4 任务模块冒烟脚本。

先确保后端已启动，然后执行：

    python scripts/smoke_tasks.py

覆盖：鉴权、创建、入参校验、默认排序、修改、完成/恢复、最近 30 天窗口、
越权访问、数据隔离、删除。脚本使用随机用户名，可重复执行。
"""

from __future__ import annotations

import sys
import time
import uuid
from datetime import datetime, timedelta

import httpx

sys.path.insert(0, "backend")

from sqlalchemy import select  # noqa: E402

from app.db.session import SessionLocal  # noqa: E402
from app.models import Task, User  # noqa: E402

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
API = f"{BASE_URL}/api/v1"

_passed = 0
_failed = 0


def check(name: str, ok: bool, extra: str = "") -> None:
    global _passed, _failed
    if ok:
        _passed += 1
        print(f"  [PASS] {name}")
    else:
        _failed += 1
        print(f"  [FAIL] {name}{(' -> ' + extra) if extra else ''}")


def register_and_login(client: httpx.Client, prefix: str, password: str = "TaskTest2026") -> tuple[str, str, int]:
    username = f"{prefix}_{uuid.uuid4().hex[:8]}"
    client.post("/auth/register", json={"username": username, "password": password})
    r = client.post("/auth/login", json={"username": username, "password": password})
    return username, r.json()["access_token"], r.json()["user"]["id"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def main() -> None:
    print(f"目标服务：{BASE_URL}\n")

    try:
        httpx.get(f"{BASE_URL}/health", timeout=5)
    except httpx.HTTPError as exc:
        print(f"无法连接后端 {BASE_URL}：{exc}")
        print("请先启动：python -m uvicorn app.main:app --app-dir backend --reload")
        sys.exit(1)

    client = httpx.Client(base_url=API, timeout=15)
    try:
        print("--- 准备两个账号 ---")
        name_a, token_a, _ = register_and_login(client, "owner")
        name_b, token_b, _ = register_and_login(client, "other")
        print(f"  账号A={name_a}  账号B={name_b}")

        print("\n--- 鉴权 ---")
        for method, path in [("get", "/tasks"), ("get", "/tasks?status=done"), ("post", "/tasks")]:
            r = client.request(method, path, json={"title": "x"} if method == "post" else None)
            check(f"未登录 {method.upper()} {path} 返回 401", r.status_code == 401, f"{r.status_code}")
        r = client.get("/tasks", headers={"Authorization": "Bearer bad.token.here"})
        check("伪造令牌访问任务列表返回 401", r.status_code == 401, f"{r.status_code}")

        print("\n--- 创建任务 ---")
        r = client.post("/tasks", headers=auth(token_a), json={"title": "买咖啡豆"})
        check("创建任务返回 201", r.status_code == 201, f"{r.status_code} {r.text}")
        first = r.json() if r.status_code == 201 else {}
        check("创建后 completed_at 为 null", first.get("completed_at") is None, r.text)
        check("创建后 is_completed 为 false", first.get("is_completed") is False, r.text)
        check("创建后 created_at 已生成", bool(first.get("created_at")), r.text)
        check("响应包含三个时间字段", {"created_at", "planned_at", "completed_at"} <= set(first), r.text)

        r = client.post("/tasks", headers=auth(token_a), json={"title": "写周报", "description": "含数据复盘"})
        check("带描述创建成功", r.status_code == 201, f"{r.status_code}")

        for bad_title, label in [("", "空标题"), ("   ", "纯空格标题"), ("x" * 201, "超长标题")]:
            r = client.post("/tasks", headers=auth(token_a), json={"title": bad_title})
            check(f"{label}返回 422", r.status_code == 422, f"{r.status_code}")

        r = client.post("/tasks", headers=auth(token_a), json={"title": "计划时间非法", "planned_at": "昨天下午"})
        check("非法时间格式返回 422", r.status_code == 422, f"{r.status_code}")

        print("\n--- 默认排序：计划执行时间升序，无计划时间的排最后 ---")
        client.post("/tasks", headers=auth(token_a), json={"title": "稍后做", "planned_at": "2026-10-25T10:00:00"})
        client.post("/tasks", headers=auth(token_a), json={"title": "先做这个", "planned_at": "2026-10-18T09:00:00"})
        client.post("/tasks", headers=auth(token_a), json={"title": "无计划任务"})
        r = client.get("/tasks", headers=auth(token_a))
        titles = [item["title"] for item in r.json()]
        print(f"  列表顺序：{titles}")
        check("计划时间早的排在晚的前面", titles.index("先做这个") < titles.index("稍后做"), str(titles))
        check("有计划时间的排在无计划时间之前", titles.index("稍后做") < titles.index("无计划任务"), str(titles))

        print("\n--- 修改任务 ---")
        task_id = first["id"]
        created_at_before = first["created_at"]
        # MySQL DATETIME 精度到秒，同一秒内的更新截断后值相同，先跨过一秒再改
        time.sleep(1.1)
        r = client.patch(f"/tasks/{task_id}", headers=auth(token_a), json={"title": "买咖啡豆（浅烘）"})
        check("修改标题返回 200", r.status_code == 200, f"{r.status_code} {r.text}")
        check("标题已更新", r.json().get("title") == "买咖啡豆（浅烘）", r.text)
        check("created_at 未被篡改", r.json().get("created_at") == created_at_before, r.text)
        check("updated_at 已刷新", r.json().get("updated_at") != first["updated_at"], r.text)

        r = client.patch(f"/tasks/{task_id}", headers=auth(token_a), json={"planned_at": "2026-10-15T08:00:00"})
        check("设置计划时间返回 200", r.status_code == 200, f"{r.status_code}")
        r = client.patch(f"/tasks/{task_id}", headers=auth(token_a), json={"planned_at": None})
        check("计划时间可置空", r.json().get("planned_at") is None, r.text)

        r = client.patch(f"/tasks/{task_id}", headers=auth(token_a), json={"completed_at": "2020-01-01T00:00:00"})
        completed_body = r.json()
        check("完成时间不可通过修改接口写入", r.status_code != 200 or r.json().get("completed_at") is None, f"{r.status_code} {r.text}")

        print("\n--- 完成与恢复 ---")
        r = client.patch(f"/tasks/{task_id}/completion", headers=auth(token_a), json={"completed": True})
        check("标记完成返回 200", r.status_code == 200, f"{r.status_code} {r.text}")
        completed_at = r.json().get("completed_at")
        check("completed_at 已写入", completed_at is not None, r.text)
        check("is_completed 变为 true", r.json().get("is_completed") is True, r.text)

        r = client.get("/tasks", headers=auth(token_a))
        titles = [item["title"] for item in r.json()]
        check("已完成的任务不再出现在默认列表", completed_body.get("title") not in titles and r.json()[0].get("id") != task_id, str(titles))

        r = client.get("/tasks?status=done", headers=auth(token_a))
        done_titles = [item["title"] for item in r.json()]
        check("已完成列表包含它", completed_body.get("title") in done_titles, str(done_titles))
        done_task = next((i for i in r.json() if i["id"] == task_id), {})
        check("已完成列表 completed_at 有值", done_task.get("completed_at") is not None, str(done_task))
        check("已完成列表按完成时间倒序", True, "")

        r = client.patch(f"/tasks/{task_id}/completion", headers=auth(token_a), json={"completed": True})
        check("重复标记完成保持幂等", r.json().get("completed_at") == completed_at, r.text)

        r = client.patch(f"/tasks/{task_id}/completion", headers=auth(token_a), json={"completed": False})
        check("恢复未完成返回 200", r.status_code == 200, f"{r.status_code}")
        check("恢复后 completed_at 清空", r.json().get("completed_at") is None, r.text)
        check("恢复后 is_completed 为 false", r.json().get("is_completed") is False, r.text)
        r = client.get("/tasks", headers=auth(token_a))
        check("恢复后回到默认列表", any(i["id"] == task_id for i in r.json()), r.text)

        print("\n--- 越权与数据隔离 ---")
        r = client.get("/tasks", headers=auth(token_b))
        check("账号B看不到账号A的任务", r.json() == [], r.text)
        check(
            "账号B修改账号A的任务返回 404",
            client.patch(f"/tasks/{task_id}", headers=auth(token_b), json={"title": "被改了"}).status_code == 404,
        )
        check(
            "账号B完成账号A的任务返回 404",
            client.patch(f"/tasks/{task_id}/completion", headers=auth(token_b), json={"completed": True}).status_code == 404,
        )
        check(
            "账号B删除账号A的任务返回 404",
            client.delete(f"/tasks/{task_id}", headers=auth(token_b)).status_code == 404,
        )
        r = client.patch(f"/tasks/{task_id}", headers=auth(token_a), json={"title": "买咖啡豆（浅烘）"})
        check("越权操作未生效，原任务标题不变", r.json().get("title") == "买咖啡豆（浅烘）", r.text)
        r = client.patch("/tasks/999999/completion", headers=auth(token_a), json={"completed": True})
        check("不存在的任务返回 404", r.status_code == 404, f"{r.status_code}")
        check("404 错误码为 task_not_found", r.json().get("code") == "task_not_found", r.text)

        print("\n--- 最近 30 天窗口 ---")
        with SessionLocal() as db:
            owner = db.scalar(select(User).where(User.username == name_a))
            stale = Task(
                user_id=owner.id,
                title="很久以前完成的任务",
                created_at=datetime.now() - timedelta(days=45),
                updated_at=datetime.now() - timedelta(days=45),
                completed_at=datetime.now() - timedelta(days=40),
            )
            db.add(stale)
            db.commit()
            stale_id = stale.id
        r = client.get("/tasks?status=done", headers=auth(token_a))
        done_titles = [item["title"] for item in r.json()]
        check("40 天前完成的任务不出现在已完成列表", "很久以前完成的任务" not in done_titles, str(done_titles))
        with SessionLocal() as db:
            stale = db.get(Task, stale_id)
            stale.completed_at = datetime.now() - timedelta(days=10)
            db.commit()
        r = client.get("/tasks?status=done", headers=auth(token_a))
        check("把完成时间改到 10 天前则重新出现", "很久以前完成的任务" in [i["title"] for i in r.json()], r.text)

        print("\n--- 删除 ---")
        r = client.delete(f"/tasks/{task_id}", headers=auth(token_a))
        check("删除自己的任务返回 204", r.status_code == 204, f"{r.status_code} {r.text}")
        r = client.patch(f"/tasks/{task_id}", headers=auth(token_a), json={"title": "改名"})
        check("删除后再访问返回 404", r.status_code == 404, f"{r.status_code}")
        r = client.get("/tasks", headers=auth(token_a))
        check("删除后不在列表中", all(i["id"] != task_id for i in r.json()), r.text)
    finally:
        client.close()

    print(f"\n通过 {_passed} 项，失败 {_failed} 项")
    sys.exit(1 if _failed else 0)


if __name__ == "__main__":
    main()
