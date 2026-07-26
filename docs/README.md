# 文档索引

本目录是 **糖尿病智能健康助理（xiaoxueqi）** 的开发文档入口。  
实现代码以仓库根目录与 `backend/`、`frontend/` 为准；历史实训材料见文末。

## 必读（按顺序）

| 顺序 | 文档 | 说明 |
|:----:|------|------|
| 1 | [architecture.md](./architecture.md) | 系统边界、分层、数据流 |
| 2 | [agent-intelligence-plan.md](./agent-intelligence-plan.md) | **智能化完整计划**（水位 L1–L2、阶段、范围） |
| 3 | [agent-behavior-spec.md](./agent-behavior-spec.md) | **Agent 行为规格表**（意图→tool→回复→前端验收） |
| 4 | [agent-design.md](./agent-design.md) | Tool Calling 运行时与包结构 |
| 5 | [development.md](./development.md) | 本地启动、目录约定、开发流程 |
| 6 | [api.md](./api.md) | REST / Agent API 契约 |
| 7 | [testing.md](./testing.md) | 测试策略与用例清单 |
| 8 | [roadmap.md](./roadmap.md) | 工程分阶段任务与完成定义 |

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

小学期交付物已迁入 [`training/`](./training/README.md)，**不要当作当前架构真理**；实现以本目录现行文档与代码为准。

| 位置 | 内容 |
|------|------|
| [training/legacy/](./training/legacy/) | 实训报告、早期 API/优化笔记、营养教学文、记忆实验方案等 |
| [training/legacy/数据库结构文档.md](./training/legacy/数据库结构文档.md) | 较完整的表结构说明（字段级；与 ORM 冲突时以 ORM 为准） |
| [login-issue-fix.md](./login-issue-fix.md) / [login-test-plan.md](./login-test-plan.md) | 登录排查历史 |
| [`docx/`](../docx/) | PRD、需求分析 |

升级原则：**去实训化展示、保留业务能力、补齐 Agent 与工程化**。
