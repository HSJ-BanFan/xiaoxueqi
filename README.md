# Diabetes Health Agent

[![CI](https://github.com/HSJ-BanFan/xiaoxueqi/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/HSJ-BanFan/xiaoxueqi/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10--3.12-3776AB.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3-42b883.svg)](https://vuejs.org/)

面向糖尿病日常管理的全栈健康助理。后端以 FastAPI、SQLAlchemy 和 JWT 为基础，通过 OpenAI-compatible Tool Calling 读取用户自己的血糖、饮食和健康档案；写操作必须经过二次确认，并记录可审计的工具调用结果。

> 本项目用于健康数据管理与软件工程实践，不提供医疗诊断、处方或紧急医疗建议。

## 项目亮点

- 真实 Tool Calling：模型只负责选择工具和生成回复，数据读取、参数校验、权限判断与写库均由 Python 执行。
- 用户级数据隔离：每个工具绑定当前 JWT 用户，不接受模型传入任意 user_id。
- 写操作门禁：新增血糖记录默认只返回预览，客户端显式确认后才落库。
- 可用性降级：LLM 不可用时自动进入规则模式，仍可查询最近血糖、统计数据和预览记录。
- 调用审计：会话 metadata 保存运行模式、轮数、工具调用和工具结果。
- 可重复测试：pytest 覆盖认证、越权、Agent runtime、工具参数和写入确认。

## 系统架构

~~~mermaid
flowchart LR
    UI[Vue 3 + TypeScript] -->|HTTP + JWT| API[FastAPI]
    API --> REST[业务 REST API]
    API --> AGENT[HealthAgent runtime]
    AGENT -->|tools schema| LLM[OpenAI-compatible LLM]
    LLM -->|tool calls| AGENT
    AGENT --> REGISTRY[用户绑定的工具注册表]
    REGISTRY --> SERVICES[业务 services]
    REST --> SERVICES
    SERVICES --> ORM[SQLAlchemy]
    ORM --> DB[(SQLite / MySQL)]
    AGENT -->|失败降级| FALLBACK[规则模式]
~~~

Agent 请求的核心流程：

1. FastAPI 使用 JWT 解析当前用户。
2. HealthAgent 将严格的 JSON Schema 工具列表发送给兼容 Chat Completions 的模型。
3. 模型返回 tool_calls，Python 校验参数并调用业务 service。
4. 写工具在未确认时只生成 preview，不修改数据库。
5. 工具结果回灌模型，最终回复与审计 metadata 一并持久化。
6. 模型连接失败或响应异常时进入 fallback，不向客户端返回 500。

## Agent 工具

| 工具 | 类型 | 作用 |
|------|------|------|
| get_profile | 读 | 获取当前用户的非敏感健康档案摘要 |
| list_recent_glucose | 读 | 查询当前用户最近的血糖记录 |
| get_glucose_stats | 读 | 计算日、周、月或季度血糖统计 |
| evaluate_glucose_alert | 读 | 使用确定性目标区间规则评估血糖值 |
| add_glucose_record | 写 | 预览或确认后新增当前用户的血糖记录 |
| list_recent_diet | 读 | 查询当前用户最近的饮食记录 |

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python、FastAPI、Pydantic v2、SQLAlchemy |
| 认证 | JWT、passlib、bcrypt |
| Agent | OpenAI-compatible Chat Completions、Tool Calling、自研运行时 |
| 数据库 | SQLite（本地默认）、MySQL（可选） |
| 前端 | Vue 3、TypeScript、Pinia、Element Plus |
| 可视化 | ECharts、Chart.js |
| 测试 | pytest、FastAPI TestClient、内存 SQLite |

backend/app/ml 和 backend/ml/llm 保留了早期 Ollama、Transformers 与向量检索实验代码；当前产品主路径是 backend/app/agent，不依赖本地模型或 ChromaDB 才能启动。

## 快速开始

### 环境要求

- Python 3.10 至 3.12
- Node.js 18 或更高版本
- 可选：任意兼容 OpenAI Chat Completions 的模型服务

不配置可用的 LLM 服务时，Agent 会自动使用规则模式。

### 1. 克隆仓库

~~~bash
git clone https://github.com/HSJ-BanFan/xiaoxueqi.git
cd xiaoxueqi
~~~

### 2. 启动后端

~~~powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item ..\.env.example .env
python -m uvicorn main:app --reload --port 8000
~~~

macOS 或 Linux 激活虚拟环境：

~~~bash
source .venv/bin/activate
~~~

默认配置使用本地 SQLite，并在启动时自动创建表。数据库文件只存在于本地，不应提交到 Git。

如需连接模型服务，请在 backend/.env 中配置：

~~~dotenv
AGENT_ENABLED=true
AGENT_REQUIRE_CONFIRM_WRITE=true
LLM_BASE_URL=https://your-provider.example/v1
LLM_API_KEY=replace-with-your-key
LLM_MODEL=your-model-name
~~~

后端启动后可访问：

- API：<http://127.0.0.1:8000>
- Swagger UI：<http://127.0.0.1:8000/docs>
- 健康检查：<http://127.0.0.1:8000/api/v1/system/healthz>

### 3. 启动前端

另开一个终端：

~~~powershell
cd frontend
npm ci
npm run dev
~~~

前端默认访问 <http://127.0.0.1:5173>，API 默认指向 <http://127.0.0.1:8000>。

项目不提供公开默认密码。请通过注册页创建本地用户，或设置 ADMIN_EMAIL 与 ADMIN_PASSWORD 后运行 backend/create_admin.py。

## 测试与质量检查

后端测试不依赖真实 LLM、外部网络或已提交数据库：

~~~powershell
cd backend
python -m pip install -r requirements-dev.txt
python -m pytest -q
~~~

前端检查：

~~~powershell
cd frontend
npm ci
npm run build
~~~

GitHub Actions 会在 push 和 pull request 时执行后端测试及前端构建。

## 项目结构

~~~text
.
├── backend/
│   ├── app/
│   │   ├── agent/          # Tool Calling client、tools、runtime、schemas
│   │   ├── api/            # REST 与 Agent endpoints
│   │   ├── core/           # 配置、鉴权、错误处理、调度
│   │   ├── db/             # SQLAlchemy 会话与 ORM
│   │   ├── services/       # 业务逻辑和事务边界
│   │   └── models/         # Pydantic 请求与响应模型
│   ├── tests/              # 自动化测试
│   └── main.py
├── frontend/
│   └── src/
│       ├── api/
│       ├── stores/
│       └── views/
├── docs/                   # 架构、API、安全与 Agent 设计
└── .env.example
~~~

## 安全设计

- 密钥和数据库文件通过 .gitignore 排除。
- 密码使用 bcrypt 哈希保存，README 不提供固定默认密码。
- Agent 工具绑定当前认证用户，禁止跨用户查询。
- Pydantic 严格校验工具参数，拒绝额外字段和未知工具。
- 写操作需要 confirm_write=true，模型本身不能绕过确认。
- 医疗免责声明由 Agent 最终回复统一追加。

如果曾在公开提交中包含真实账号、健康数据或可复用凭据，应立即更换相关凭据，并根据协作情况决定是否重写 Git 历史。

## 文档

- [系统架构](docs/architecture.md)
- [Agent 设计](docs/agent-design.md)
- [API 契约](docs/api.md)
- [测试策略](docs/testing.md)
- [安全说明](docs/security.md)
- [开发指南](docs/development.md)

历史实训材料保存在 docs/training，仅用于追溯早期设计，不代表当前架构。

## 维护者与提交身份

当前规范化维护身份为 [HSJ-BanFan](https://github.com/HSJ-BanFan)。仓库历史中出现的旧 Git 作者名属于同一维护者的历史身份配置，说明见 [AUTHORS.md](AUTHORS.md)。
