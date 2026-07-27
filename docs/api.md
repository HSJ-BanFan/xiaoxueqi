# API 契约

Base URL（本地）：`http://127.0.0.1:8000`  
API 前缀：`/api/v1`  
交互文档：`/docs`（Swagger）、`/redoc`

> 下列路径以当前代码与规划为准。实现时若有偏差，**先改代码再改本文**，保持同步。

## 1. 约定

### 1.1 鉴权

- 除注册/登录/健康检查外，业务接口需要：

```http
Authorization: Bearer <access_token>
```

- 登录使用 OAuth2 Password Flow 表单：

```http
POST /api/v1/users/login
Content-Type: application/x-www-form-urlencoded

username=<email>&password=<password>
```

### 1.2 错误体（目标统一）

```json
{
  "detail": "人类可读说明",
  "code": "forbidden",
  "details": {}
}
```

常见 `code`：`http_error` | `auth_error` | `forbidden` | `validation` | `not_found` | `llm_unavailable` | `tool_failed` | `app_error`

### 1.3 用户隔离

- 列表类接口：只返回 `current_user` 数据  
- 写接口：body 中 `user_id` 必须等于当前用户，或服务端强制覆盖  
- Agent tools：不接受外部 `user_id`  

---

## 2. System

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|
| GET | `/` | 否 | 服务信息（main.py） |
| GET | `/api/v1/system/healthz` | 否 | 存活（`system.py`，需挂载路由） |
| GET | `/api/v1/system/readyz` | 否 | DB + agent 配置摘要 |

**readyz 示例：**

```json
{
  "status": "ok",
  "checks": {
    "database": { "ok": true, "error": null },
    "agent": { "enabled": true, "model": "gemini/gemini-3.6-flash" }
  }
}
```

挂载示例（`app/api/__init__.py`）：

```python
from app.api.endpoints import system
router.include_router(system.router, prefix="/system", tags=["系统"])
```

---

## 3. Users  `/api/v1/users`

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|
| POST | `/register` | 否 | 注册 |
| POST | `/login` | 否 | 登录，返回 token |
| GET | `/profile` | 是 | 当前用户 |
| PUT | `/profile` | 是 | 更新资料 |
| POST | `/risk-assessment` | 是 | 风险评估（简易） |

**登录响应示例：**

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "user_id": "<uuid>",
  "email": "user@example.com"
}
```

### 3.1 当前用户 profile

`GET /api/v1/users/profile` 返回完整账户与健康档案；`PUT /api/v1/users/profile` 接受同名可更新字段并返回更新后的完整对象。前端字段必须使用 snake_case。

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` / `email` / `phone` | string | 基础资料 |
| `gender` | `male \| female \| other` | 可选 |
| `birth_date` / `diagnosis_date` | datetime | 可选 |
| `diabetes_type` | `type1 \| type2 \| gestational \| prediabetes \| other` | 可选 |
| `height` / `weight` | number | cm / kg，可选 |
| `target_glucose_min` / `target_glucose_max` | number | mmol/L，可选 |
| `avatar` | string | 头像地址，可选 |

资料编辑 UI 不提交 `id`、`created_at`、`updated_at`、`is_active` 或 `is_superuser`；密码更新使用独立请求体 `{ "password": "..." }`。

---

## 4. Glucose  `/api/v1/glucose`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `` | 创建血糖记录 |
| GET | `` | 列表（可 start_date/end_date） |
| GET | `/statistics?period=week` | 统计 day/week/month/quarter |
| GET | `/recent?days=7` | 最近 N 天 |
| GET | `/{record_id}` | 单条（需属主校验） |
| PUT/PATCH | `/{record_id}` | 更新（若已实现） |
| DELETE | `/{record_id}` | 删除（若已实现） |

**创建 body 要点（Pydantic `GlucoseCreate`）：**

```json
{
  "user_id": "<必须为当前用户>",
  "value": 6.5,
  "measurement_time": "BEFORE_BREAKFAST",
  "measurement_method": "FINGER_STICK",
  "measured_at": "2025-07-01T08:00:00",
  "notes": "可选"
}
```

`measurement_time` 枚举：

`BEFORE_BREAKFAST | AFTER_BREAKFAST | BEFORE_LUNCH | AFTER_LUNCH | BEFORE_DINNER | AFTER_DINNER | BEFORE_SLEEP | MIDNIGHT | OTHER`

---

## 5. Diet / Health / Nutrition / Knowledge

| 前缀 | 模块 | 说明 |
|------|------|------|
| `/api/v1/diet` | 饮食记录 CRUD | 见 `endpoints/diet.py` |
| `/api/v1/health` | 综合健康 | `endpoints/health.py` |
| `/api/v1/nutrition` | 食物营养 | `endpoints/nutrition.py` |
| `/api/v1/knowledge` | 知识库条目 | `endpoints/knowledge.py` |
| `/api/v1/glucose-monitor` | 监测/mock 设备 | **非生产 CGM** |
| `/api/v1/ollama` | Ollama 调试 | 非产品主路径 |
| `/api/v1/assistant` | 会话与消息 | 旧助理链路 |

实现细节以对应 endpoint 与 `/docs` 为准；新增字段时更新本节。

---

## 6. Assistant（会话） `/api/v1/assistant`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/conversations` | 创建会话（user_id=自己） |
| GET | `/conversations` | 我的会话列表 |
| GET | `/conversations/{id}` | 详情 |
| PUT | `/conversations/{id}` | 更新标题等 |
| DELETE | `/conversations/{id}` | 删除 |
| （消息相关） | 见 `assistant.py` | 创建消息、列表消息、生成回复 |

Agent 升级后：会话 CRUD 可继续用；**生成回复主路径改为 Agent**。

---

## 7. Agent `/api/v1/agent`

### 7.1 `POST /chat`

**Request：**

```json
{
  "message": "我这周血糖怎么样？",
  "conversation_id": null,
  "history": [
    { "role": "user", "content": "你好" },
    { "role": "assistant", "content": "你好，我是小雪琪" }
  ],
  "confirm_write": false
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| message | string | 必填 |
| conversation_id | string\|null | 不传则新建或由服务端策略决定 |
| history | array | 可选；也可服务端读 DB |
| confirm_write | bool | true 时写类 tool 带 confirm |

**Response：**

```json
{
  "reply": "近7天均值 6.8 mmol/L ...\n\n说明：...",
  "conversation_id": "uuid",
  "mode": "agent",
  "model": "configured-tool-capable-model",
  "rounds": 2,
  "tool_calls": [
    { "name": "get_glucose_stats", "arguments": { "period": "week" } }
  ],
  "tool_results": [
    {
      "name": "get_glucose_stats",
      "ok": true,
      "data": { "average": 6.8, "count": 12 },
      "requires_confirm": false,
      "error": null
    }
  ],
  "disclaimer": "说明：我是健康管理助手，不是执业医师。..."
}
```

`mode`：`agent` | `fallback` | `disabled`

### 7.2 写确认交互

1. 用户：「记录血糖 7.2 空腹」  
2. 返回 `requires_confirm=true` 的 tool_result + 预览文案  
3. 前端点「确认写入」→ 再次 `POST /chat`，`confirm_write=true`，message 可重复或固定确认话术  
4. 服务端 tool `confirm=true` 后落库  

（可选）另增 `POST /api/v1/agent/confirm` 携带 `pending_id`——非必须。

---

## 8. 前端调用示例

```ts
// 登录
const form = new URLSearchParams()
form.set('username', email)
form.set('password', password)
await api.post('/api/v1/users/login', form, {
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
})

// Agent
await api.post('/api/v1/agent/chat', {
  message: '本周血糖统计',
  conversation_id: currentId,
  confirm_write: false,
}, {
  headers: { Authorization: `Bearer ${token}` },
  timeout: 90000,
})
```

---

## 9. 变更流程

1. 改 endpoint / schema  
2. 更新本文对应表格  
3. 若破坏兼容，在 roadmap 记一笔  
4. 补测试  
