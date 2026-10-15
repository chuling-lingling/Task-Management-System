"""M3 认证模块冒烟脚本。

先确保后端已启动，然后执行：

    python scripts/smoke_auth.py
    python scripts/smoke_auth.py http://127.0.0.1:8000   # 指定别的地址

脚本会用一次性随机用户名走完整流程，可重复执行不会撞用户名。
"""

from __future__ import annotations

import json
import sys
import uuid

import httpx

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


def main() -> None:
    username = f"smoke_{uuid.uuid4().hex[:8]}"
    password = "SmokeTest2026"
    print(f"目标服务：{BASE_URL}")
    print(f"测试账号：{username}\n")

    try:
        httpx.get(f"{BASE_URL}/health", timeout=5)
    except httpx.HTTPError as exc:
        print(f"无法连接后端 {BASE_URL}：{exc}")
        print("请先在另一个终端启动：python -m uvicorn app.main:app --app-dir backend --reload")
        sys.exit(1)

    client = httpx.Client(base_url=API, timeout=15)
    try:
        print("--- 注册 ---")
        r = client.post("/auth/register", json={"username": username, "password": password})
        check("注册成功返回 201", r.status_code == 201, f"{r.status_code} {r.text}")
        payload = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        user_id = payload.get("id")
        check("响应包含 id", user_id is not None, r.text)
        check("响应不含 password_hash", "password_hash" not in payload, json.dumps(payload, ensure_ascii=False))
        check("响应包含 created_at", bool(payload.get("created_at")), r.text)

        r = client.post("/auth/register", json={"username": username, "password": password})
        check("重复注册返回 409", r.status_code == 409, f"{r.status_code} {r.text}")
        check("错误码为 username_taken", r.json().get("code") == "username_taken", r.text)

        r = client.post("/auth/register", json={"username": f"{username}_weak", "password": "123"})
        check("密码过短返回 422", r.status_code == 422, f"{r.status_code}")
        check("422 返回结构化字段错误", isinstance(r.json().get("detail"), list), r.text)

        r = client.post("/auth/register", json={"username": "含空格 的用户", "password": password})
        check("非法用户名返回 422", r.status_code == 422, f"{r.status_code}")

        print("\n--- 未认证访问 ---")
        r = client.get("/auth/me")
        check("不携带令牌访问 /me 返回 401", r.status_code == 401, f"{r.status_code} {r.text}")
        check("错误码为 not_authenticated", r.json().get("code") == "not_authenticated", r.text)

        token: str = ""
        r = client.get("/auth/me", headers={"Authorization": "Bearer forged.token.value"})
        check("伪造令牌返回 401", r.status_code == 401, f"{r.status_code}")
        check("错误码为 token_invalid", r.json().get("code") == "token_invalid", r.text)

        r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}) if token else None
        if r is not None:
            check("空令牌返回 401", r.status_code == 401, f"{r.status_code}")

        print("\n--- 登录 ---")
        r = client.post("/auth/login", json={"username": username, "password": "WrongPassword1"})
        check("密码错误返回 401", r.status_code == 401, f"{r.status_code} {r.text}")
        check("错误码为 invalid_credentials", r.json().get("code") == "invalid_credentials", r.text)

        r = client.post("/auth/login", json={"username": f"{username}_not_exist", "password": password})
        check("用户名不存在返回 401", r.status_code == 401, f"{r.status_code}")
        check("不存在账号与密码错误同文案", r.json().get("code") == "invalid_credentials", r.text)

        r = client.post("/auth/login", json={"username": username, "password": password})
        check("登录成功返回 200", r.status_code == 200, f"{r.status_code} {r.text}")
        login_data = r.json() if r.status_code == 200 else {}
        token = login_data.get("access_token", "")
        check("返回 token_type=bearer", login_data.get("token_type") == "bearer", r.text)
        check("返回过期秒数", isinstance(login_data.get("expires_in"), int), r.text)
        check("登录响应附带用户信息", login_data.get("user", {}).get("id") == user_id, r.text)
        check("用户信息不含 password_hash", "password_hash" not in login_data.get("user", {}), r.text)

        print("\n--- 携带令牌访问 ---")
        if not token:
            print("  [SKIP] 未取得令牌，跳过依赖令牌的检查")
            return

        r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        check("携带令牌访问 /me 返回 200", r.status_code == 200, f"{r.status_code} {r.text}")
        check("/me 返回正确的用户名", r.json().get("username") == username, r.text)

        print("\n--- 数据隔离前置检查 ---")
        r = client.get("/auth/me", headers={"Authorization": f"Bearer {token[:-3]}xxx"})
        check("篡改令牌返回 401", r.status_code == 401, f"{r.status_code}")
    finally:
        client.close()

    print(f"\n通过 {_passed} 项，失败 {_failed} 项")
    sys.exit(1 if _failed else 0)


if __name__ == "__main__":
    main()
