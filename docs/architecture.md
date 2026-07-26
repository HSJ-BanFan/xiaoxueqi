# 系统架构

## 1. 产品定位

**糖尿病智能健康助理**：面向慢病自我管理的 Web 应用。

- **业务后端**：用户认证、血糖/饮食/健康档案、统计、知识库、定时监测任务  
- **智能助理**：基于 Tool Calling 的 Agent（模型提议工具，Python 执行）  
- **前端**：Vue3 + Element Plus 管理与对话界面  

**非目标**：医疗诊断系统、真实 CGM 厂商生产对接、高并发消息中台。

## 2. 逻辑架构

```text
┌─────────────────────────────────────────────────────────────┐
│  frontend (Vue3 + TS + Pinia + Element Plus)                │
│  Login / Dashboard / Glucose / Diet / Health / Assistant    │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP + JWT Bearer
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  backend (FastAPI)                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ REST API     │  │ Agent API    │  │ System            │  │
│  │ /users       │  │ /agent/chat  │  │ /healthz /readyz  │  │
│  │ /glucose ... │  │ (planned)    │  │                   │  │
│  └──────┬───────┘  └──────┬───────┘  └───────────────────┘  │
│         │                 │                                 │
│         ▼                 ▼                                 │
│  ┌──────────────┐  ┌──────────────────────────────────────┐ │
│  │ services/*   │◄─│ agent/ (tools → services only)       │ │
│  └──────┬───────┘  └──────────────────────────────────────┘ │
│         ▼                                                   │
│  ┌──────────────┐     ┌───────────────────────────────────┐ │
│  │ SQLAlchemy   │     │ LLM OpenAI-compatible (optional)  │ │
│  │ SQLite/MySQL │     │ Ollama / DeepSeek / OpenAI ...    │ │
│  └──────────────┘     └───────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 3. 后端分层（强制约定）

| 层 | 路径 | 职责 | 禁止 |
|----|------|------|------|
| endpoints | `app/api/endpoints/` | 路由、鉴权依赖、DTO 校验 | 复杂业务、直接拼 SQL |
| deps | `app/api/deps.py` | `get_db`、`get_current_user` | — |
| services | `app/services/` | 业务逻辑、事务边界 | 依赖 FastAPI Request |
| models (Pydantic) | `app/models/` | 请求/响应 Schema | ORM 细节 |
| db models | `app/db/models.py` | ORM 表 | 业务规则 |
| agent | `app/agent/` | LLM client、tools、runtime | 绕过 service 写库 |
| core | `app/core/` | config、security、errors、scheduler | 业务 CRUD |
| ml | `app/ml/` | 遗留 LLM/Ollama 封装 | 新产品路径优先 agent |

**Agent 铁律**：Tool 只能调用 `services/*`（或只读查询封装），**禁止** tool 内复制一套写库逻辑。

## 4. 认证与数据边界

```text
Client
  → Authorization: Bearer <JWT>
  → deps.get_current_user 解析 sub=user_id
  → 所有业务查询强制 filter(user_id == current_user.id)
  → Agent tools 闭包绑定 current_user，参数中不接受任意 user_id
```

- 登录：`[密钥]`，表单字段 `username` = email，`password` = 密码  
- 密码：bcrypt（`passlib` / `security.py`）  
- 超管：`is_superuser`，仅管理类接口使用  

详见 [security.md](./security.md)。

## 5. 核心业务域

| 域 | 表（摘要） | 主要 API 前缀 |
|----|------------|----------------|
| 用户 | `users` | `/api/v1/users` |
| 血糖 | `glucose_records` | `/api/v1/glucose` |
| 饮食 | `diet_records` | `/api/v1/diet` |
| 健康 | `health_records` 及子表 | `/api/v1/health` |
| 对话 | `conversations`, `messages` | `/api/v1/assistant` |
| 知识库 | `knowledge_base` | `/api/v1/knowledge` |
| 营养 | 食物数据相关 | `/api/v1/nutrition` |
| 监测 | 调度 + mock 设备 | `/api/v1/glucose-monitor` |
| 系统 | — | `/api/v1/system`（或根路径，以实现为准） |
| Agent | 复用对话表 + metadata | `/api/v1/agent`（规划中） |

完整字段见仓库根 [数据库结构文档.md](../数据库结构文档.md) 与 [database.md](./database.md)。

## 6. 智能助理数据流（目标态）

```text
POST /api/v1/agent/chat
  1. JWT 鉴权
  2. 加载/创建 conversation（可选）
  3. HealthAgent.run(message, history)
       a. 调用 OpenAI-compatible Chat Completions（带 tools）
       b. 若 tool_calls → Python 执行 → 结果回灌 messages
       c. 循环至多 LLM_MAX_TOOL_ROUNDS 轮
       d. 失败 → fallback 规则意图
  4. 持久化 user/assistant message（metadata 含 tool 审计）
  5. 返回 reply + tool_calls + tool_results + mode
```

详细设计：[agent-design.md](./agent-design.md)。

## 7. 前端结构

```text
frontend/src/
  api/           # axios 封装与各模块 API
  views/         # 页面
  components/    # 图表、饮食建议等
  stores/        # Pinia（用户/token）
  router/        # 路由与登录守卫
  utils/http.ts  # 可与 api/index.ts 收敛（技术债）
```

详见 [frontend.md](./frontend.md)。

## 8. 部署形态（开发）

| 组件 | 默认 | 说明 |
|------|------|------|
| API | `uvicorn` :8000 | `backend/main.py` |
| DB | SQLite 文件 | `DATABASE_URL` 可切 MySQL |
| 前端 | Vite :5173 | `VITE_API_URL` 指向 API |
| LLM | 可选 | 当前默认 OpenAI-compatible proxy `localhost:18318/v1`；Ollama 仅遗留调试 |
| Scheduler | 进程内 | reload 可能双启，开发可关 |

## 9. 当前仓库状态（文档编写时）

已有/部分落地：

- 业务 REST、JWT、Vue 页面  
- `app/core/config.py` 已偏向 SQLite + LLM/Agent 配置项  
- `app/core/errors.py`、`endpoints/system.py` 健康检查草稿  
- `app/agent/` 包占位（`runtime` 等仍待实现）  

未完成（见 roadmap）：

- Agent runtime / tools / API  
- pytest 体系  
- 前端 Agent UX  
- README 作品化、Docker  

## 10. 相关文档

- [development.md](./development.md)  
- [api.md](./api.md)  
- [roadmap.md](./roadmap.md)  
