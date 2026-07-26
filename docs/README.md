# 文档索引

本目录是 **糖尿病智能健康助理（xiaoxueqi）** 的开发文档入口。  
实现代码以仓库根目录与 `backend/`、`frontend/` 为准；历史实训材料见文末。

## 必读（按顺序）

| 顺序 | 文档 | 说明 |
|:----:|------|------|
| 1 | [architecture.md](./architecture.md) | 系统边界、分层、数据流 |
| 2 | [agent-design.md](./agent-design.md) | Tool Calling Agent 设计（门面升级核心） |
| 3 | [development.md](./development.md) | 本地启动、目录约定、开发流程 |
| 4 | [api.md](./api.md) | REST / Agent API 契约 |
| 5 | [testing.md](./testing.md) | 测试策略与用例清单 |
| 6 | [roadmap.md](./roadmap.md) | 分阶段任务与完成定义 |

## 专题

| 文档 | 说明 |
|------|------|
| [frontend.md](./frontend.md) | Vue3 前端结构与助理页改造要点 |
| [security.md](./security.md) | 鉴权、数据隔离、密钥与医疗免责 |
| [database.md](./database.md) | 表结构摘要与约定（指向完整 SQL 文档） |

## 环境与配置

- 根目录 [`.env.example`](../.env.example) — 后端/Agent 环境变量模板  
- 复制为 `backend/.env` 或仓库根 `.env`（以实现读取路径为准，见 development.md）

## 历史 / 实训材料（只读参考）

以下文件多为小学期交付物，**不要当作当前架构真理**；实现以 `docs/*` 与代码为准。

| 位置 | 内容 |
|------|------|
| 仓库根 `*实训*` / `任务清单.md` / `实现*.md` | 实训过程文档 |
| `docx/` | PRD、需求分析 |
| `糖尿病助手项目*.md` | 早期 API/优化笔记 |
| `数据库结构文档.md` | 较完整的表结构说明（仍有效） |
| `docs/login-*.md` | 登录问题排查历史 |

升级原则：**去实训化展示、保留业务能力、补齐 Agent 与工程化**。
