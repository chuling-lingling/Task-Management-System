# AGENTS.md

本文件是给 AI 助手与协作者看的工程约定。修改代码前先读它，提交前确保没有违反其中的红线条款。

## 项目定位

一个前后端分离的个人任务管理系统。核心链路：**注册 / 登录 → 创建任务 → 按计划执行时间查看未完成列表 → 修改、删除、标记完成 → 查看最近 30 天已完成的任务**。

范围之外的东西一律不提前实现。邮箱邮件提醒已在 M7 实现：用户在设置页填收件邮箱，任务可勾选启用提醒，到达计划时间由后台定时任务经 SMTP 发信（详见 README「邮件提醒」章节）。

## 技术栈

| 层 | 选型 | 版本约束 |
|---|---|---|
| 后端框架 | FastAPI | 0.115.x |
| ASGI 服务器 | Uvicorn | 最新稳定 |
| ORM | SQLAlchemy（2.0 风格 `Mapped` / `select()`） | 2.0.x |
| 数据库 | MySQL 8 + PyMySQL 驱动 | — |
| 数据校验 | Pydantic v2 / pydantic-settings | 2.x |
| 认证 | JWT（PyJWT，HS256） | 2.x |
| 密码哈希 | Argon2id（argon2-cffi） | 23.x |
| 前端 | Vue 3 + Vite + Pinia + Axios | 3.x / 5.x |

Python 虚拟环境固定在项目根目录 `.venv`，依赖清单在根目录 `requirements.txt`。

## 目录结构与依赖方向

```
backend/app/
  main.py         FastAPI 实例、CORS、路由注册、lifespan（启动自愈迁移 + 提醒后台任务）；检测到 frontend/dist 时托管前端静态文件并做 SPA 路由回退（生产态无需 nginx 伺服前端）
  core/           config（读取 .env）、security（哈希/JWT）、errors（统一错误）
  db/             base（DeclarativeBase）、session（engine / get_db 依赖）、migrate（自愈式加列）
  models/         ORM 模型，一张表一个文件
  schemas/        Pydantic 入参/出参模型，与领域对象一一对应
  services/       email（SMTP 发送）/ reminder（到期扫描，纯函数供后台任务与脚本复用）
  api/            deps（get_current_user 等依赖）、v1/（路由按资源分文件）
scripts/          init_db.py / send_reminders.py / migrate_email.py / smoke*.py
frontend/src/     api / views / components / stores / router / styles
```

**依赖方向严格单向**：`api → schemas → models → db`，`core` 是被各层复用的工具层。

禁止事项：
- `models` 不得 import `schemas` 或 `api`；`db` 不得 import `models` 的业务逻辑。
- 不要在路由函数里直接拼 SQL，一律走 ORM。
- 不要为了少写一个文件而跨层塞代码。

## 命名约定

- 文件与目录：小写 + 下划线（`task_service.py`）；Vue 组件：大驼峰（`TaskItem.vue`）。
- 数据库表名：复数小写（`users` / `tasks`）；字段名：小写下划线。
- Python 类名大驼峰，函数名小写下划线，常量全大写。
- API 路径：全小写复数资源（`/api/v1/tasks`），动词性操作作为子资源。

## 数据约定（不可协商）

1. **三个时间字段语义分离**，禁止互相复用：
   - `created_at`：记录写入系统的时刻，由服务端生成，**永不修改**。
   - `planned_at`：用户设定的计划执行时间，可为空，可随时修改。
   - `completed_at`：任务真正被标记完成的时刻。
2. **完成状态以 `completed_at` 是否为 NULL 为唯一真源**。删除任务表里任何 `is_completed` / `status` 布尔字段的设想，两个字段必然会在某天不一致。
3. 已完成筛选的时间窗口是**最近 30 天**，比较基准是 `completed_at`，不是 `created_at`。
4. 未完成任务列表默认排序：**`planned_at` 升序优先，未设置计划时间的排在后面，组内按 `created_at` 倒序**。已完成任务列表按 `completed_at` 倒序。
5. **时间统一由应用层生成**：所有时间字段用 SQLAlchemy 的 Python 侧默认值（`default=datetime.now`），不使用数据库的 `NOW()`，这样时区行为可预测。服务端与 MySQL 必须处于同一时区：本机部署默认满足；**Docker 部署时镜像内已装 tzdata，`Dockerfile` 设 `ENV TZ=Asia/Shanghai`，compose 两个服务均可用 `.env` 的 `TZ` 覆盖**——绝不允许容器裸跑 UTC（否则「计划执行时间」到期判断与界面展示都会偏移，东八区用户会晚 8 小时）。
6. 索引约定：列表查询永远带 `user_id` 维度，因此 `tasks` 只需 `(user_id, completed_at)` 复合索引即可覆盖"未完成过滤"与"最近 30 天已完成筛选"两种场景，不要重复给单个字段加索引。
7. **邮箱提醒用 `email_reminder_sent_at` 是否为 NULL 作为"是否已成功发送"的唯一真源**，与 `completed_at` 同理：由服务端在发送成功后写入，前端不可伪造；修改 `planned_at` 或 `email_reminder_mode` 时重置它与 `email_reminder_failed_at`，使提醒按新时间/新频率重新计时。频率模式 `email_reminder_mode`（`once`/`hourly`/`daily`，默认 `once`）：`once` 只发一次，`hourly`/`daily` 在首次发送后每隔 1 小时/1 天持续发送直到任务完成。失败不标记 `sent_at`，只记 `failed_at` 并加 5 分钟退避重试（SMTP 恢复后自动补发）。

## API 约定

- 统一前缀 `/api/v1`。路由版本号升到 v2 时必须保留 v1 一段时间，不做破坏性下线。
- 成功响应直接返回业务对象，不额外包 `{data: ...}` 外壳（保持 FastAPI 原生风格便于 Swagger 阅读）。
- 错误响应统一结构：`{"detail": "面向用户的提示", "code": "machine_readable_code"}`，`code` 供前端分支处理，业务异常一律 `raise AppError(status_code, message, code)`（`app/core/errors.py`）。
- 状态码语义：
  - `200` 查询/更新成功，`201` 创建成功，`204` 删除成功。
  - `401` 未携带凭证（`not_authenticated`）、凭证无效或过期（`token_invalid` / `token_expired`）、账号密码错误（`invalid_credentials`）。
  - `404` 资源不存在**或不属于当前用户**（越权一律伪装成不存在，不返回 403）。
  - `409` 资源冲突，目前仅用户名被占用（`username_taken`）。
  - `422` 入参校验失败，响应体是结构化的 `[{"field": "字段名", "message": "提示"}]`。
  - `500` 未捕获异常，**对外只返回通用提示，堆栈与敏感信息仅写服务端日志**。
- 所有列表接口默认带上当前用户维度过滤，不接受由前端传 `user_id` 决定查谁的数据。
- `completed_at` 不允许客户端直接写入：任务修改接口只接受 `title` / `description` / `planned_at`，完成时间一律由服务端在标记完成时写入当前时刻，重复标记不覆盖首次完成时间。

## 已知坑（踩过一次就不必再踩）

1. **`status_code=204` 的路由必须显式写 `response_model=None`**。本仓库所有模块都启用了 `from __future__ import annotations`，此时 `-> None` 会被 FastAPI 解析成 `NoneType`（真值），不写会直接抛 `AssertionError: Status code 204 must not have a response body`。
2. **别用 `Field(strip_whitespace=True)` 防空白字符串**。Pydantic 的长度校验发生在 strip 之前，`"   "` 会被判为合法后再被 strip 成空串，必须自己写 `field_validator` 在 strip 后判空（见 `schemas/task.py` 的 `clean_title`）。
3. **MySQL `DATETIME` 默认精度到秒**，同一秒内连续更新时 `updated_at` 看起来没变化，测试里要先等待跨秒。
4. **改完代码记得确认端口上没有旧 uvicorn 进程**，否则新代码不生效，表现为新接口全部 404。
5. **不要引入外部字体 / 渲染阻塞型外部资源**。`fonts.googleapis.com` 在不可达网络下会让样式表挂起、页面永远不出首屏（表现为白屏/截图全黑）。字体一律走本地栈（见 `frontend/src/styles/tokens.css`）。
6. **Windows 下 `npm install` 若报 esbuild spawn 失败并回滚**，用 `npm install --ignore-scripts` 装依赖，再按 README 补装 `@esbuild/win32-x64` 与 `@rollup/rollup-win32-x64-msvc` 两个平台包。
7. **提醒后台任务把同步 SMTP 发送包在 `asyncio.to_thread` 里**。SMTP 是阻塞 IO，绝不可直接在事件循环里调用，否则会卡住整个 uvicorn 的请求处理。
8. **多 worker 部署时关掉内置后台任务**：`ENABLE_REMINDER_WORKER=false`，改用 `scripts/send_reminders.py` 由 cron/任务计划程序调度，否则每个 worker 都会扫到同一批到期任务并重复发信。

## 安全红线

1. 密码必须使用 Argon2id 哈希存储，**明文密码从不落盘、从不写日志、从不在响应中返回**（包括 `UserRead` 也要排除哈希字段）。
2. 除 `/auth/register`、`/auth/login` 外，所有接口必须挂 `Depends(get_current_user)`。
3. 任何任务级读写都必须追加 `Task.user_id == current_user.id` 过滤，禁止只用主键查询。
4. 全局异常处理器不得把异常原始信息（可能包含连接串、堆栈）返回给客户端；只返回通用提示，细节记服务端日志。
5. `.env` 不入库；`JWT_SECRET_KEY` 在生产环境必须为随机值；不要在代码里硬编码任何凭据。
6. SMTP 发件凭据（SMTP_PASSWORD 等）只存在于 `.env`，**绝不进代码、绝不进数据库、绝不写日志**；收件邮箱由用户在设置页填写（存 `users.email`），发件与收件是两个独立概念，勿混为一谈。
6. 所有入参经 Pydantic 校验：字符串长度上限、`planned_at` 必须是合法 ISO 8601 时间。

## 协作方式

- **分阶段交付**：每完成一个模块即停下等待人工验收，验收通过才动下一个模块。禁止一次性把后面几个阶段的代码都写完。
- **不做无关重构**：不要顺手重命名、拆分、优化本次需求范围外的文件。看到坏味道先在回复里提出，得到确认再动。
- **优先简单成熟的方案**：不引入消息队列、缓存、CQRS、过度抽象的服务层。业务逻辑写在路由层可直读的位置，等确实出现复用需求再抽取 service。
- 修改数据库模型后，同步更新 `scripts/init_db.py` 并在 README 注明，避免模型与库表漂移。
