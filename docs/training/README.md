# 历史实训材料

本目录保存小学期 / 校企实训期间的过程文档，**不是当前架构的权威来源**。

## 权威来源（优先阅读）

1. [`docs/architecture.md`](../architecture.md)、[`docs/agent-design.md`](../agent-design.md) 等现行设计文档  
2. 源代码 `backend/app/**`、`frontend/src/**`  
3. 环境变量模板 [`.env.example`](../../.env.example)

## 目录结构

```text
docs/training/
  README.md          # 本说明
  legacy/            # 从仓库根目录迁入的历史长文
```

## legacy 清单

| 文件 | 原用途 | 现状 |
|------|--------|------|
| [糖尿病智能健康助理系统实训报告.md](./legacy/糖尿病智能健康助理系统实训报告.md) | 实训总报告 | 只读参考；架构已升级为 Agent |
| [任务清单.md](./legacy/任务清单.md) | 早期完成度清单 | 被 [roadmap.md](../roadmap.md) 取代 |
| [实现文档.md](./legacy/实现文档.md) | 体重助手 API 实现笔记 | 局部原型，勿当全局架构 |
| [实现总结.md](./legacy/实现总结.md) | 血糖监测与预警实现总结 | 业务仍在，调度默认关闭 |
| [糖尿病助手项目API服务总结.md](./legacy/糖尿病助手项目API服务总结.md) | 早期 REST API 说明 | 被 [api.md](../api.md) 取代 |
| [糖尿病助手项目优化文档.md](./legacy/糖尿病助手项目优化文档.md) | 错误处理/模型统一笔记 | 部分思路已落地到代码 |
| [fastapi设计入门到入土.md](./legacy/fastapi设计入门到入土.md) | 营养 API 教学文 | 教学向，非规范契约 |
| [用户记忆功能实验方案.md](./legacy/用户记忆功能实验方案.md) | ChromaDB + Ollama 记忆实验 | 未作为 Agent 核心依赖 |
| [数据库结构文档.md](./legacy/数据库结构文档.md) | 字段级表结构说明 | **仍可参考**；冲突以 ORM 为准 |

## 其他历史材料

| 位置 | 内容 |
|------|------|
| [`docs/login-issue-fix.md`](../login-issue-fix.md) | 登录问题排查 |
| [`docs/login-test-plan.md`](../login-test-plan.md) | 登录测试计划 |
| [`docx/`](../../docx/) | PRD、需求分析 |

## 阅读原则

- **实现以 `docs/*`（非 training）与代码为准**  
- legacy 中的 MySQL 硬编码连接串、本地模型路径、Ollama 直连等已过时  
- 公开 README 使用作品化短文，勿把实训报告当产品说明  
