# Backend

FastAPI 后端负责用户认证、健康数据管理、Agent Tool Calling、会话审计与数据库访问。

当前智能助理主路径位于 app/agent：

- llm_client.py：OpenAI-compatible Chat Completions 客户端
- runtime.py：多轮工具调用、异常降级与最终回复
- tools.py：绑定当前用户的工具注册表与参数校验
- prompts.py：医疗边界和工具使用约束
- schemas.py：Agent 请求、响应和审计 DTO

知识检索主路径位于 `app/services/knowledge_retrieval.py`：默认使用中文 bigram BM25，可选叠加 OpenAI-compatible query embedding，并通过 RRF 融合。运行时不抓取外网。

app/ml 与 ml/llm 是早期模型实验代码，不是当前 Agent 启动的必需依赖。

## 本地启动

~~~powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item ..\.env.example .env
python scripts/seed_knowledge.py
python -m uvicorn main:app --reload --port 8000
~~~

默认使用 SQLite，AUTO_CREATE_TABLES=true 时会在启动阶段自动创建表。

API 文档：

- Swagger UI：<http://127.0.0.1:8000/docs>
- ReDoc：<http://127.0.0.1:8000/redoc>
- Health：<http://127.0.0.1:8000/api/v1/system/healthz>
- Readiness：<http://127.0.0.1:8000/api/v1/system/readyz>

## 环境变量

从仓库根目录复制 .env.example，然后至少修改 SECRET_KEY。主要配置：

| 变量 | 说明 |
|------|------|
| DATABASE_URL | SQLAlchemy 数据库连接地址 |
| SECRET_KEY | JWT 签名密钥 |
| AUTO_CREATE_TABLES | 启动时是否自动建表 |
| AGENT_ENABLED | 是否启用 Agent |
| AGENT_REQUIRE_CONFIRM_WRITE | 写工具是否要求显式确认 |
| LLM_BASE_URL | OpenAI-compatible API 根地址 |
| LLM_API_KEY | 模型服务密钥 |
| LLM_MODEL | 模型名称 |
| LLM_MAX_TOOL_ROUNDS | 单次 Agent 调用的最大工具轮数 |
| EMBEDDING_ENABLED | 是否为知识检索启用可选向量层 |
| EMBEDDING_BASE_URL / API_KEY / MODEL | OpenAI-compatible embeddings 配置 |

LLM 不可用时，Agent 会进入 fallback 规则模式；只要已执行知识 seed，规则模式仍可回答命中关键词的知识问题并返回来源链接。

## 知识语料

~~~powershell
# 导入仓库自带完整语料；可重复执行
python scripts/seed_knowledge.py

# 仅验证一个白名单页面，不改写、不写产物
python scripts/ingest_knowledge.py --only niddk --limit 1 --no-rewrite --dry-run

# 无可用 LLM 端点时，使用构建期翻译 fallback 生成完整产物
python scripts/ingest_knowledge.py --rewrite-provider google --no-embed
~~~

摄取脚本只访问 `scripts/sources.py` 的 60 个显式白名单 URL，按源站 robots 动态取最大请求间隔（NIDDK 当前为 10 秒），并默认只在 40–60 篇、300–500 chunks、0 失败时覆盖产物。仓库语料当前为 60 篇、429 chunks，维护者已于 2026-07-28 完成人工许可复核；重新运行摄取脚本会恢复待复核状态，发布新产物前必须再次检查 `../data/knowledge/LICENSES.md`。

## 创建本地管理员

项目不提供固定默认密码。设置环境变量后执行：

~~~powershell
$env:ADMIN_EMAIL = "admin@local.test"
$env:ADMIN_PASSWORD = "choose-a-strong-local-password"
python create_admin.py
~~~

不要把本地 .env、数据库或真实账号信息提交到 Git。

## 核心 API

| 路径 | 作用 |
|------|------|
| POST /api/v1/users/register | 注册用户 |
| POST /api/v1/users/login | 获取 JWT |
| GET /api/v1/users/profile | 获取当前用户资料 |
| GET/POST /api/v1/glucose | 查询或新增血糖记录 |
| GET /api/v1/glucose/statistics | 血糖统计 |
| GET/POST /api/v1/diet | 饮食记录 |
| GET/POST /api/v1/health | 健康记录 |
| POST /api/v1/agent/chat | Tool Calling 智能助理 |
| GET /api/v1/knowledge/search?q=... | 带来源的知识检索 |

完整契约见 ../docs/api.md。

## 测试

测试使用内存 SQLite 和假 LLM，不读取本地开发数据库：

~~~powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
~~~

离线复现 RAG 检索指标：

~~~powershell
python scripts/evaluate_rag.py --split test --k 3
~~~

脚本会在内存 SQLite 中导入正式语料，同时运行提交 `9a37edc` 的 SQL `ILIKE` 基线与当前检索器，输出 JSON、Markdown、三项宏指标和逐题失败清单；全程禁用 embedding、网络和真实 LLM。当前 50 题数据集的 held-out test 结果为 Recall@3 `0.0% → 84.0%`、Citation Hit@3（引用命中率）`92.0%`、Citation Precision@3 `41.3%`。

重点覆盖：

- 注册、登录和无 Token 拒绝
- 用户间数据隔离与越权访问
- Agent 工具参数校验
- Tool Calling 多轮执行
- 写操作预览与二次确认
- 模型故障时 fallback

## 安全边界

- Tool Registry 在请求级别绑定 current_user。
- 模型不能指定任意 user_id。
- 写工具只有在 confirm_write=true 时才可落库。
- 密码使用 bcrypt 哈希保存。
- 工具失败返回受控错误，不向模型或客户端泄露内部异常。
- Agent 回复包含健康管理免责声明。
