# Agent 智能化完整计划

> 目标：把 xiaoxueqi 从「业务 CRUD + 可选闲聊」升级为  
> **「确定性业务后端 + 智能操作层（Agent）」**  
> 水位：**P0 = L1 只读工具化 + L2 受控写入**；P1 = 主动助理增强  
> 权威行为验收：[agent-behavior-spec.md](./agent-behavior-spec.md)  
> 运行时设计：[agent-design.md](./agent-design.md)  
> 工程阶段：[roadmap.md](./roadmap.md)

---

## 1. 背景与问题

### 1.1 现状痛点

| 问题 | 表现 | 后果 |
|------|------|------|
| 助理像套壳 | prompt 拼上下文自由生成 | 编造血糖、不可测 |
| 与业务脱节 | 闲聊不打 DB | 无「智能办事」价值 |
| 写入危险 | 模型直接暗示已保存 | 脏数据、失去信任 |
| 同质化 | 纯 CRUD 课设 | 面试被看穿、难差异化 |

### 1.2 目标叙事（简历 / 面试）

> 业务数据与权限是确定性的；预警是规则引擎；  
> LLM 只负责理解用户意图并调用工具；写入可确认、可审计、可降级。

### 1.3 非目标

- 医疗诊断 / 开药 / 临床级 CGM  
- 多 Agent 大编排、完全自治写库  
- 用 LangChain/Claude Code SDK 作为产品 runtime 核心  
- 一期上 MQ / 微服务拆分  

---

## 2. 智能成熟度模型

| 级别 | 名称 | 能力摘要 | 是否本计划必达 |
|------|------|----------|----------------|
| L0 | 套壳聊天 | 自由生成 | 淘汰 |
| **L1** | 工具化只读 | profile/recent/stats/alert 真查数 | **P0** |
| **L2** | 受控写入 | 预览确认落库 + 多轮补槽 | **P0** |
| **L3** | 主动助理 | 周报、异常追问、提醒意图 | **P1 选做** |
| L4 | 工作流增强 | 多工具编排、知识库引用 | P2 |
| L5 | 过度智能 | 医疗自治等 | **不做** |

---

## 3. 目标架构

```text
Vue AssistantView
    │  POST /api/v1/agent/chat  (JWT)
    ▼
┌─────────────────────────────────────┐
│ HealthAgent.runtime                 │
│  · system prompt + history          │
│  · OpenAI-compatible tool loop      │
│  · max_rounds / timeout             │
│  · fallback rules (no LLM)          │
└──────────────┬──────────────────────┘
               │ dispatch
               ▼
┌─────────────────────────────────────┐
│ Tools (bind current_user)           │
│  get_profile                        │
│  list_recent_glucose                │
│  get_glucose_stats                  │
│  evaluate_glucose_alert  (rules)    │
│  add_glucose_record (confirm gate)  │
│  list_recent_diet                   │
│  (P1) create_reminder / search_kb   │
└──────────────┬──────────────────────┘
               ▼
         services/*  →  SQLAlchemy  →  DB
               │
               ▼
     audit: tool_calls + tool_results → message metadata
```

**真相源优先级：** DB 与规则引擎 > tool 结果 > 模型文案。

---

## 4. P0 范围（必达 · 智能合格线）

### 4.1 后端

| 模块 | 交付物 |
|------|--------|
| `app/agent/schemas.py` | Chat 请求/响应、ToolResult DTO |
| `app/agent/prompts.py` | 系统提示（禁止编数、禁止医嘱、写确认） |
| `app/agent/llm_client.py` | OpenAI-compatible Chat Completions |
| `app/agent/tools.py` | P0 六个 tool + dispatch |
| `app/agent/runtime.py` | tool loop + fallback + mode |
| `app/api/endpoints/agent.py` | `POST /agent/chat` |
| 路由挂载 | `api/__init__.py` include agent |
| 对话落库 | 复用 conversations/messages + metadata 审计 |
| 配置 | `AGENT_*` / `LLM_*` 已在 settings，核对默认值 |

### 4.2 行为（详见行为规格）

- I01–I09 全覆盖  
- I10–I12 fallback  
- G1–G10 通用约束  

### 4.3 前端

| 项 | 交付 |
|----|------|
| `api/agent.ts` | chat 客户端，超时 60–90s |
| AssistantView | 主路径走 `/agent/chat` |
| UI | mode 标签、工具轨迹、确认卡片、快捷芯片、disclaimer |
| 写入成功 | 刷新血糖数据 |

### 4.4 测试

| 类型 | 内容 |
|------|------|
| tool 单测 | 六工具 + 写确认门禁 |
| runtime | mock LLM tool_calls；fallback 无网 |
| API | JWT、I05 不落库、I06 落库、越权 |
| 演示 | behavior-spec §7 脚本 |

### 4.5 P0 完成定义（DoD）

- [ ] §7 演示 9 步全过  
- [ ] 断 LLM 仍可统计/预览记血糖  
- [ ] pytest P0 矩阵绿  
- [ ] 简历可写：Tool Calling、写门禁、审计、Fallback（不写虚假 QPS）  

---

## 5. P1 范围（增强 · 更有记忆点）

在 P0 稳定后，按优先级选做：

| 顺序 | 项 | 意图 | 价值 |
|:----:|----|------|------|
| 1 | 周报小结 | I20 | 演示「智能感」最强 |
| 2 | 异常追问 | I22 | 产品感、非空聊 |
| 3 | 提醒意图落库 | I23 | 可扩展，推送可后做 |
| 4 | 周对比 | I21 | 需统计能力扩展 |
| 5 | 知识库 tool | I24 | 轻量检索即可 |

### P1 DoD（若做周报）

- [ ] 周报数字全部来自 stats tool  
- [ ] 无数据有空模板  
- [ ] 仍带 disclaimer  
- [ ] 行为规格 I20 验收勾满  

---

## 6. P2 / 明确不做

| 做（P2 以后） | 不做 |
|---------------|------|
| 推送通道（邮件/系统通知） | 诊断与处方 |
| 饮食写入 tool + 确认 | 真 CGM 生产对接当卖点 |
| 多 period 对比 API 优化 | 多 Agent 辩论框架 |
| Docker 一键演示增强 | 无确认自动写库 |

---

## 7. 与业务后端的关系

Agent **不替代** REST：

| 通道 | 用途 |
|------|------|
| REST `/glucose` 等 | 表单、图表、稳定 CRUD |
| Agent `/agent/chat` | 自然语言入口与编排 |

同一 `services/*`，避免两套写库逻辑。

---

## 8. 实施阶段与任务拆分

### Phase B1 — Tools + Fallback（可无 LLM 演示）

- [ ] 实现 tools.py 六工具  
- [ ] runtime fallback 正则 I10–I12  
- [ ] tool 单测 T1–T6  
- [ ] 本地脚本 curl 验证 fallback  

### Phase B2 — LLM Tool Loop

- [ ] llm_client + prompts  
- [ ] runtime agent loop  
- [ ] mock LLM 测试  
- [ ] mode=agent 路径  

### Phase B3 — API + 落库审计

- [ ] endpoints/agent.py  
- [ ] conversation/message metadata  
- [ ] API 测试 C1–C3  

### Phase C — 前端

- [ ] agent API 模块  
- [ ] 轨迹 / 确认 / mode / 芯片  
- [ ] 与血糖页数据刷新  

### Phase C+ — P1（可选）

- [ ] I20 周报  
- [ ] I22 异常追问  

### 对齐 roadmap

- Phase A 工程底座：见 [roadmap.md](./roadmap.md)（多项已完成）  
- 本文 Phase B/C 对应 roadmap 的 Agent MVP 与前端  

---

## 9. 提示词与安全策略（摘要）

System 必须包含：

1. 身份：小雪琪，健康管理助理，非医师  
2. 需要真实数据必须 call tools  
3. 禁止编造测量值  
4. 写操作未确认不得声称已保存  
5. 拒绝开药/诊断结论  
6. 严重症状引导就医  
7. 中文、简洁、可引用 tool 数字  

安全：

- Prompt 注入不能扩大 tool 权限  
- 日志禁止 token/密码  
- 详见 [security.md](./security.md)  

---

## 10. 配置清单

| 变量 | 建议默认 | 说明 |
|------|----------|------|
| AGENT_ENABLED | true | 总开关 |
| AGENT_REQUIRE_CONFIRM_WRITE | true | 写门禁 |
| LLM_BASE_URL | 兼容代理或 Ollama `/v1` | OpenAI-compatible |
| LLM_API_KEY | 本地占位 | 勿提交真实密钥 |
| LLM_MODEL | 项目选定模型 | |
| LLM_MAX_TOOL_ROUNDS | 4 | |
| LLM_TIMEOUT_SECONDS | 60 | |
| LLM_TEMPERATURE | 0.2–0.3 | 工具场景偏低 |

---

## 11. 演示与简历话术

### 60 秒演示路径

见 [agent-behavior-spec.md §7](./agent-behavior-spec.md)。

### 简历一条（后端主、AI 辅）

> 在业务 API 之上扩展智能助理：Tool Calling 查询真实档案/血糖统计，写操作确认后落库，LLM 不可用时规则降级，工具调用可审计。

### 面试金句

> 智能在交互层，真相在数据库和规则引擎。

---

## 12. 风险与缓解

| 风险 | 缓解 |
|------|------|
| 模型乱写库 | 确认门禁 + 单测 |
| 编造数据 | 强制 tool、空库模板 |
| 医疗合规 | disclaimer + 拒绝对医嘱 |
| LLM 不稳 | fallback P0 必做 |
| 范围膨胀 | 严格 P0 先收口再 P1 |
| 双写逻辑 | tools 只调 service |

---

## 13. 文档地图

| 文档 | 职责 |
|------|------|
| **本文** | 智能化目标、水位、阶段、范围 |
| [agent-behavior-spec.md](./agent-behavior-spec.md) | 意图级验收规格 |
| [agent-design.md](./agent-design.md) | 运行时/包结构/tool schema |
| [api.md](./api.md) | HTTP 契约 |
| [frontend.md](./frontend.md) | UI 改造 |
| [testing.md](./testing.md) | 测试策略 |
| [roadmap.md](./roadmap.md) | 工程总路线与勾选状态 |

---

## 14. 修订记录

| 日期 | 变更 |
|------|------|
| 2026-07-26 | 初版：L1–L2 必达、P1 增强、阶段拆分与文档地图 |
