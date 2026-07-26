# 升级路线图（门面工程化 + Agent）

## 0. 总目标

将实训作品升级为：

1. **可演示、可测试的业务后端门面**（对齐 NotifyHub 级工程叙事，但不强行上 MQ）  
2. **真·智能助理**（Tool Calling + 写确认 + 审计 + fallback）  
3. **作品化 README**（去实训/破解教程）  

分支建议：`feat/agent-upgrade`（当前）→ 完成后 PR 合入 `master`。

---

## Phase A — 工程底座（1–2 天）

### 状态

| 项 | 状态 |
|----|------|
| config 默认 SQLite + LLM 配置项 | 已完成 |
| errors.py | 已完成并挂载 |
| system healthz/readyz | 已完成并挂载 |
| .env.example | 已完成 |
| requirements 拆分 | 已完成 |
| pytest 骨架 | 已完成（34 tests） |
| 去硬编码密钥/CORS `[IP]` | 已完成 |
| README 作品化 | Phase D（本次不做） |

### 任务 Checklist

- [x] `main.py` 注册 `AppError` / HTTP 异常处理；CORS 读 settings  
- [x] `api/__init__.py` 挂载 `system` 路由  
- [x] 根目录 `.env.example` 与 `backend/.env` 本地使用  
- [x] `.gitignore`：`.env`、`*.db`、`.venv`、`node_modules`  
- [x] `requirements.txt` 瘦身；`requirements-dev.txt`  
- [x] `tests/conftest.py` + H1/A1–A5/G1–G5  
- [ ] 删除或隔离 README 中破解/超长装机内容（挪到 `docs/training/` 可选）  

### 完成定义

- 仅 SQLite 可启动 API + `/docs`  
- `pytest` 鉴权与血糖越权用例通过  

---

## Phase B — Agent MVP（2–3 天）

### 状态

| 项 | 状态 |
|----|------|
| `app/agent` 包结构 | 已完成 |
| tools / runtime / llm_client | 已完成 |
| `POST /api/v1/agent/chat` | 已完成 |
| fallback | 已完成 |
| 写确认门禁 | 已完成 |
| 消息 metadata 审计 | 已完成 |

### 任务 Checklist

- [x] 按 [agent-design.md](./agent-design.md) 实现 `schemas/prompts/llm_client/tools/runtime`  
- [x] `endpoints/agent.py` + 路由注册  
- [x] 对话落库（复用 assistant 表或最小写入）  
- [x] 单测 T1–T6、R1–R5、C1–C3  
- [x] 无 Ollama 下 fallback 全演示脚本（curl）  

### 完成定义

- 「本周血糖统计」「最近血糖」「记录血糖 + 确认」三条路径可演示  
- LLM 挂了不 500  

---

## Phase C — 前端（1–2 天）

见 [frontend.md](./frontend.md)。

- [ ] `api/agent.ts`  
- [ ] `AssistantView` 走 Agent；工具轨迹；确认卡片  
- [ ] 超时 60–90s；mode 标签  
- [ ] 快捷芯片  
- [ ] 可选：Dashboard「解读本周血糖」跳转  

### 完成定义

- UI 可见 tool 名与结果摘要  
- 确认前 DB 不增加记录  

---

## Phase D — 打磨与门面（1 天）

- [ ] Docker Compose（api ± mysql）  
- [ ] README 作品页 + 架构图  
- [ ] 演示录屏/截图  
- [ ] 简历 bullet 定稿  
- [ ] 面试 10 问自答（见 agent-design + security）  

---

## 明确不做（本周期）

- RabbitMQ / 完整通知中心  
- 真实 CGM 厂商 API  
- LangChain 重依赖重构  
- Claude Code SDK 嵌入业务  
- 医疗级诊断准确率宣传  

---

## 推荐每日节奏

| 日 | 焦点 |
|----|------|
| D1 | Phase A 路由/配置/测试骨架 |
| D2 | Phase A 收尾 + tools 单测 |
| D3 | runtime fallback + agent API |
| D4 | LLM loop + mock 测试 |
| D5 | 前端 Assistant |
| D6 | README/Docker/简历 |

---

## 进度记录（请实现时勾选并改日期）

| 日期 | 完成 | 备注 |
|------|------|------|
| 2026-07-26 | 开发文档体系 | docs/* 与 .env.example |
| 2026-07-26 | Phase A + Phase B | SQLite/Uvicorn 验收通过；Gemini Agent proxy + fallback；34 tests passed |
| | | |
