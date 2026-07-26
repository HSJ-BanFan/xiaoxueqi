# 开发入口

本仓库的**当前开发文档**在 [`docs/`](./docs/README.md)。

| 文档 | 用途 |
|------|------|
| [docs/README.md](./docs/README.md) | 文档索引 |
| [docs/architecture.md](./docs/architecture.md) | 架构 |
| [docs/agent-design.md](./docs/agent-design.md) | Agent 设计（优先实现） |
| [docs/development.md](./docs/development.md) | 本地启动 |
| [docs/api.md](./docs/api.md) | API 契约 |
| [docs/roadmap.md](./docs/roadmap.md) | 分阶段任务 |
| [docs/testing.md](./docs/testing.md) | 测试 |
| [docs/frontend.md](./docs/frontend.md) | 前端 |
| [docs/security.md](./docs/security.md) | 安全 |
| [docs/database.md](./docs/database.md) | 数据库 |

环境变量模板：[`.env.example`](./.env.example)

历史实训长文（根目录 `README.md`、各中文总结/报告）仅作参考，**实现以 `docs/*` 与代码为准**。

## 5 分钟上手

```bash
# 后端
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy ..\.env.example .env
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

# 前端（新终端）
cd frontend
npm install
npm run dev
```

升级工作从 [docs/roadmap.md](./docs/roadmap.md) Phase A 开始。
