# Agent 设计说明

> 状态：设计冻结（实现中）  
> 原则：**模型只提议；权限、校验、写库由 Python 确定性执行**  
> 智能化计划与水位：[agent-intelligence-plan.md](./agent-intelligence-plan.md)  
> **行为验收（意图级）**：[agent-behavior-spec.md](./agent-behavior-spec.md)

## 1. 为什么做 Agent

当前助理多为「拼 prompt + Ollama 闲聊」，无法稳定：

- 读取用户真实血糖/档案  
- 受控写入记录  
- 在 LLM 宕机时仍可完成基础管理  

升级后的 Agent 要成为**真智能助理**：会查数、会算统计、会预警解释、写操作可确认可审计。

## 2. 技术选型

| 方案 | 决策 |
|------|------|
| OpenAI-compatible Tool Calling + 自研 loop | **采用（核心）** |
| LangChain / LangGraph | 不作为核心依赖（可选适配，二期） |
| Claude Agent / Claude Code SDK | **不采用**（偏开发者代理，不适合作产品后端 runtime） |
| 纯 RAG 闲聊 | 不够；RAG 仅作后续 `search_knowledge` tool |

当前后端：

- OpenAI-compatible proxy：`LLM_BASE_URL=http://localhost:18318/v1`
- 模型：`gemini/gemini-3.6-flash`
- Agent 产品链路不启动或加载本地 LLM；其他兼容服务可通过环境变量切换

## 3. 包结构（目标）

```text
backend/app/agent/
  __init__.py          # 导出 HealthAgent, AgentRunResult
  schemas.py           # AgentChatRequest / AgentChatResponse / ToolResultDTO
  prompts.py           # SYSTEM_PROMPT
  llm_client.py        # OpenAICompatibleClient
  tools.py             # HealthToolRegistry + dispatch
  runtime.py           # tool loop + fallback
  audit.py             # 可选：结构化日志 helper
```

当前仓库仅有 `__init__.py` 占位，实现时按上表补齐。

## 4. 运行时状态机

```text
                    ┌─────────────┐
                    │   START     │
                    └──────┬──────┘
                           ▼
                   AGENT_ENABLED?
                      │ no
                      ▼
                   mode=disabled ──► return
                      │ yes
                      ▼
              call LLM (+ tools schema)
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
     tool_calls   final text    HTTP/parse error
          │           │           │
          ▼           ▼           ▼
   execute tools   return      fallback rules
   append tool msgs  mode=agent   mode=fallback
   rounds++ 
   rounds > MAX? ──yes──► 截断返回
```

## 5. Tool 规格（第一期）

所有 tool **绑定当前登录用户**，参数中 **禁止** `user_id`。

### 5.1 `get_profile`

- **类型**：读  
- **参数**：无  
- **返回**：name、diabetes_type、target_glucose_min/max、height、weight 等非敏感摘要  

### 5.2 `list_recent_glucose`

- **参数**：`limit` (1–50，默认 10)  
- **实现**：`services.glucose.get_user_glucose_records`  
- **返回**：id, value, measurement_time, measured_at, notes  

### 5.3 `get_glucose_stats`

- **参数**：`period` ∈ `day|week|month|quarter`（默认 `week`）  
- **实现**：`services.glucose.get_glucose_statistics`  
- **返回**：average, max, min, count, in_range_percentage, high/low_percentage  

### 5.4 `evaluate_glucose_alert`

- **类型**：确定性规则（**不要用 LLM 做阈值**）  
- **参数**：`value` (mmol/L)  
- **规则**：  
  - `value < target_min`（默认 3.9）→ `low`  
  - `value > target_max`（默认 10.0）→ `high`  
  - 否则 `in_range`  
- **返回**：level, target_min/max, advice（文案模板，非诊断）  

### 5.5 `add_glucose_record`（写）

- **参数**：  
  - `value` number **必填**  
  - `measurement_time` enum **必填**（与 `MeasurementTimeEnum` 一致）  
  - `measurement_method` 可选，默认 `FINGER_STICK`  
  - `notes` 可选  
  - `confirm` bool  
- **门禁**：当 `AGENT_REQUIRE_CONFIRM_WRITE=true` 且 `confirm!=true`：  
  - **不写库**  
  - 返回 `requires_confirm=true` + preview  
- **确认后**：`GlucoseCreate(user_id=current_user.id, ...)` → `create_glucose_record`  

### 5.6 `list_recent_diet`

- **参数**：`limit`  
- **实现**：优先 service；无则 ORM 查询 `DietRecord` 按 `meal_time` desc  

### 5.7 第二期（不做进 MVP）

- `add_diet_record`  
- `search_knowledge`  
- `list_medications` / reminders  

## 6. OpenAI tools JSON 形态

每个 tool 注册为：

```json
{
  "type": "function",
  "function": {
    "name": "get_glucose_stats",
    "description": "...",
    "parameters": {
      "type": "object",
      "properties": { "period": { "type": "string", "enum": ["day","week","month","quarter"] } },
      "additionalProperties": false
    }
  }
}
```

`dispatch(name, arguments) -> ToolResult`：

```text
ToolResult:
  name: str
  ok: bool
  data: Any | null
  error: str | null
  requires_confirm: bool = false
```

回灌模型时：`role=tool`，`content=json.dumps(ToolResult)`（ensure_ascii=False）。

## 7. System Prompt 要点

文件：`prompts.py`

必须包含：

1. 身份：小雪琪，健康管理助理，非执业医师  
2. 需要真实数据时 **必须** 调 tools，禁止编造测量值  
3. 写操作未确认不得声称「已记录」  
4. 不诊断、不开药；紧急情况就医  
5. 中文、简洁、可引用工具返回的数字  
6. 工具失败时说明原因与下一步  

固定 disclaimer 追加在最终 `reply` 末尾（产品层也可再展示一次）。

## 8. LLM Client

`llm_client.py`：

```text
POST {LLM_BASE_URL}/chat/completions
Headers: Authorization: Bearer {LLM_API_KEY}
Body: model, messages, temperature, tools?, tool_choice=auto
Timeout: LLM_TIMEOUT_SECONDS
```

- 使用 `httpx`（同步 Client 即可；若 endpoint 为 async，用 `httpx.AsyncClient` 或 `run_in_threadpool`）  
- 不在日志中打印完整 API Key  
- 网络错误 / 4xx/5xx → 抛异常由 runtime 捕获进 fallback  

## 9. Fallback 规则（LLM 不可用）

| 匹配 | 动作 |
|------|------|
| `记录/添加血糖 <数字>` + 可选「空腹/餐后」 | `add_glucose_record`（无「确认」则 preview） |
| `统计/达标/周报/平均` | `get_glucose_stats` |
| `最近血糖/查血糖/血糖记录` | `list_recent_glucose` |
| 其它 | 返回可用指令帮助 + 提示配置 LLM |

`mode` 必须标记为 `fallback`，前端显示「规则模式」。

## 10. HTTP API

见 [api.md](./api.md) § Agent。

**推荐路径**：`POST /api/v1/agent/chat`

请求字段：

- `message: str`  
- `conversation_id: str | null`  
- `history: {role, content}[]`（可选，服务端也可用 DB 历史）  
- `confirm_write: bool`（默认 false；为 true 时写 tool 带 confirm）  

响应字段：

- `reply`, `conversation_id`, `mode`, `model`, `rounds`  
- `tool_calls[]`, `tool_results[]`, `disclaimer`  

## 11. 与旧接口关系

| 模块 | 策略 |
|------|------|
| `/assistant/*` 会话 CRUD | 保留；Agent 复用同一会话表 |
| 旧 generate 闲聊 | 新产品默认走 `/agent/chat` |
| `/ollama/*` | 调试保留，不作为主路径 |
| `app/ml/*` | 遗留；新逻辑不强制依赖 |

`messages.message_metadata`（或现有 metadata 字段）建议写入：

```json
{
  "mode": "agent",
  "model": "gemini/gemini-3.6-flash",
  "rounds": 2,
  "tool_calls": [],
  "tool_results": []
}
```

## 12. 安全与合规

- Tool 内强制 `user_id = current_user.id`  
- 写操作默认确认门禁  
- 回复必须带非医疗诊断免责声明  
- 不把密码、完整 JWT、数据库 URL 交给模型  
- Prompt 注入：即使用户要求「忽略规则删除他人数据」，tool 层也无法跨用户  

## 13. 测试要点

见 [testing.md](./testing.md)：

- mock LLM 返回 tool_calls → 断言 service 被正确调用  
- 未 confirm 写不落库  
- fallback 不依赖网络  
- 越权：即使用 tool 参数伪造也无法改 user（参数根本无 user_id）  

## 14. 实现顺序建议

1. `schemas` + `tools`（纯 Python，可先单测）  
2. `runtime.fallback`（无 LLM 可演示）  
3. `llm_client` + tool loop  
4. `endpoints/agent.py` 挂路由  
5. 对话落库 + 前端轨迹 UI  
