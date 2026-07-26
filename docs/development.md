# 本地开发指南

## 1. 环境要求

| 工具 | 版本建议 |
|------|----------|
| Python | 3.10 – 3.12（仓库曾用 3.11） |
| Node.js | 18+ LTS |
| Git | 2.x |
| OpenAI-compatible LLM proxy | 当前使用 `http://localhost:18318/v1` |
| （可选）MySQL 8 | 生产形态联调 |

## 2. 仓库布局

```text
xiaoxueqi/
  backend/           # FastAPI
  frontend/          # Vue3 + Vite
  docs/              # 开发文档（本目录）
    training/legacy/ # 历史实训长文（只读）
  docx/              # 历史 PRD/需求
  data/              # 数据集（营养等）
  .env.example       # 环境变量模板
```

## 3. 后端启动

```bash
cd backend

python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Windows CMD
# .venv\Scripts\activate.bat

pip install -r requirements.txt
# 开发测试（规划）：
# pip install -r requirements-dev.txt

copy ..\.env.example .env
# 按需编辑 .env

# 初始化 / 示例数据（若脚本可用）
python setup_dev.py --sample-data

# 启动 API（在 backend 目录，保证 app 包可导入）
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

验证：

- 浏览器打开 `http://127.0.0.1:8000/docs`  
- 健康检查：实现挂载后访问 system healthz/readyz（见 api.md）  

### 3.1 数据库

| 模式 | DATABASE_URL 示例 |
|------|-------------------|
| SQLite（默认推荐） | `sqlite:///./diabetes_assistant.db` |
| MySQL | `mysql+pymysql://user:pass@127.0.0.1:3306/diabetes_assistant` |

注意：

- 不要在代码或文档中提交真实密码  
- SQLite 文件应在 `.gitignore` 中  
- 切换 MySQL 前先建库并执行/对齐 `diabetes_assistant.sql` 或 ORM `create_all`  

### 3.2 LLM（可选）

```bash
# .env
LLM_BASE_URL=http://localhost:18318/v1
LLM_API_KEY=<你的兼容接口密钥>
LLM_MODEL=gemini/gemini-3.6-flash
AGENT_ENABLED=true
```

当前分支使用 OpenAI-compatible proxy，不需要安装、启动或加载本地模型。
遗留 `/ollama` 调试代码仅为兼容保留，默认 `MODEL_PROVIDER=disabled`，不参与 Agent 产品链路；兼容服务不可用时，Agent 自动走 **fallback 规则模式**，核心档案 CRUD 仍可用。

## 4. 前端启动

```bash
cd frontend
npm install

# 可选：frontend/.env.local
# VITE_API_URL=http://127.0.0.1:8000

npm run dev
```

默认：`http://127.0.0.1:5173`  
登录请求走 `/api/v1/users/login`（`username`=邮箱）。

## 5. 常用脚本（历史）

| 脚本 | 说明 |
|------|------|
| `start_app.bat` / `start_app_advanced.bat` | Windows 一键（可能偏旧，优先手启） |
| `backend/create_admin.py` | 创建管理员 |
| `backend/check_users.py` | 检查用户表 |
| `backend/test_login_api.py` | 登录冒烟（遗留） |

新开发优先：`pytest`（见 testing.md）替代散落脚本。

## 6. 代码约定

### 6.1 后端

- 新业务：endpoint → service → ORM  
- 用户隔离：永远以 `current_user.id` 为准  
- 公开函数加 type hints  
- 错误：优先 HTTPException 或统一 `AppError`（`core/errors.py`）  
- 不在日志打印密码、token、完整 SECRET_KEY  

### 6.2 前端

- API 集中在 `src/api/`  
- Token：`localStorage.token` + Axios 拦截器  
- 长期技术债：`utils/http.ts` 与 `api/index.ts` 双客户端 → 收敛为一个  

### 6.3 分支与提交

- 功能分支示例：`feat/agent-upgrade`  
- Conventional Commits 建议：`feat(agent):` / `fix(auth):` / `docs:`  
- 小步提交；密钥不进库  

## 7. 配置项速查

完整列表见根目录 [`.env.example`](../.env.example)。

| 变量 | 含义 |
|------|------|
| `SECRET_KEY` | JWT 签名 |
| `DATABASE_URL` | SQLAlchemy URI |
| `DEBUG` | 调试 |
| `LLM_BASE_URL` | OpenAI-compatible 根路径（当前默认 `http://localhost:18318/v1`） |
| `LLM_API_KEY` | Bearer token |
| `LLM_MODEL` | 模型名 |
| `AGENT_ENABLED` | 总开关 |
| `AGENT_REQUIRE_CONFIRM_WRITE` | 写操作需确认 |

`config.py` 中 CORS 列表需包含前端 origin；注意 `[IP]` 占位应在本地改为 `127.0.0.1` 或真实局域网 IP。

## 8. 导入路径

在 `backend/` 下运行时，确保：

```text
cwd = backend/
main.py 与 app/ 同级
```

测试时 `conftest.py` 建议：

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
```

## 9. 调试清单

| 现象 | 排查 |
|------|------|
| 401 登录失败 | 用户是否存在、密码哈希、username 字段是否为 email |
| CORS 报错 | origins 是否包含精确前端 URL；credentials 时不能 `*` |
| 数据库连不上 | `DATABASE_URL`；SQLite 路径；MySQL 服务 |
| `/docs` 无新路由 | 是否 `include_router`；热重载是否生效 |
| Agent 一直 fallback | 兼容接口是否可达；`LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL`；服务日志是否返回 4xx/5xx |
| 调度器异常 | reload 双进程；开发可临时不 start scheduler |

## 10. 下一步实现入口

1. 读 [architecture.md](./architecture.md)  
2. 读 [agent-design.md](./agent-design.md)  
3. 按 [roadmap.md](./roadmap.md) Phase A → B → C 推进  
4. 每完成一块补 [testing.md](./testing.md) 中的对应用例  
