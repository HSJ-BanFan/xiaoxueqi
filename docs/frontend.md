# 前端开发说明

## 1. 技术栈

- Vue 3 + TypeScript  
- Vite  
- Pinia  
- Vue Router  
- Element Plus  
- Axios  
- ECharts / Chart.js（图表）  
- marked（助理消息 Markdown）  

## 2. 目录

```text
frontend/src/
  api/
    index.ts              # 主 API 客户端 + 各业务 API（现状）
    glucose.ts
    glucose-monitor.ts
    agent.ts              # Agent chat 类型与请求封装（90s timeout）
  views/
    LoginView.vue
    RegisterView.vue
    DashboardView.vue
    GlucoseView.vue / GlucoseRecordView.vue
    DietView.vue
    HealthView.vue
    AssistantView.vue     # 【重点改造】
    KnowledgeView.vue
    SettingsView.vue
  stores/user.ts          # token / 用户信息
  utils/http.ts           # 与 api/index 重复，建议收敛
  router/index.ts
  components/
    UserProfileCard.vue   # Dashboard 用户档案与近 7 天血糖摘要
```

## 3. 环境变量

`frontend/.env.local`：

```env
VITE_API_URL=http://127.0.0.1:8000
```

Axios `baseURL` 必须使用该变量，避免写死 `localhost` 与后端 CORS 不一致。

## 4. 鉴权流

1. 登录成功 → `localStorage.setItem('token', access_token)`  
2. 请求拦截器附加 `Authorization: Bearer ...`  
3. 401 → 清 token，跳转登录（在 store 或路由守卫统一处理）  

登录 body 必须是 `application/x-www-form-urlencoded`，字段名 `username`（邮箱）、`password`。

## 5. Assistant 页改造规格（Phase C）

### 5.1 主路径

- 发送消息默认调用 `POST /api/v1/agent/chat`  
- 超时建议 `60000`–`90000`  
- 维护 `conversation_id` 与本地 `history`  

### 5.2 UI 元素

| 元素 | 行为 |
|------|------|
| 消息气泡 | 用户 / 助理；助理支持 Markdown |
| mode 标签 | `Agent` / `规则模式` / `已关闭` |
| 工具轨迹 | 可折叠列表：name、arguments 摘要、ok/error |
| 确认卡片 | 当 `requires_confirm`：展示 preview，按钮「确认写入」 |
| 快捷芯片 | 最近血糖；本周血糖统计；记录血糖引导（填入自然语言示例） |
| 免责声明 | 页脚固定 |

### 5.3 确认写入时序

```text
用户自然语言记血糖
  → agent 返回 requires_confirm
  → UI 展示预览
  → 用户点确认
  → POST { message, confirm_write: true, conversation_id }
  → 成功后刷新血糖页或轻提示
```

### 5.4 与旧 Ollama 旁路

- `AssistantView` 当前不再暴露 Ollama 开关，默认且唯一产品主路径为 Agent
- 遗留 `/ollama` API 仍保留给其他调试场景，不参与助理页交互

### 5.5 当前实现说明

- 页面内维护 `messages`、最多 50 条请求 `history` 与服务端 `conversation_id`
- 新对话会重置页面消息和 `conversation_id`，不会调用旧 assistant 生成接口
- 支持 `/assistant?prefill=...` 预填输入框；Dashboard 接线仍为可选项
- 401 复用现有用户 store 的清 token / 跳登录逻辑；网络和 90 秒超时显示可读错误

## 6. API 模块建议

```ts
// api/agent.ts
export interface AgentChatRequest {
  message: string
  conversation_id?: string | null
  history?: { role: 'user' | 'assistant'; content: string }[]
  confirm_write?: boolean
}

export interface ToolResult {
  name: string
  ok: boolean
  data?: unknown
  error?: string | null
  requires_confirm?: boolean
}

export interface AgentChatResponse {
  reply: string
  conversation_id: string
  mode: 'agent' | 'fallback' | 'disabled'
  model?: string | null
  rounds: number
  tool_calls: { name: string; arguments: Record<string, unknown> }[]
  tool_results: ToolResult[]
  disclaimer: string
}
```

## 7. 技术债

| 问题 | 建议 |
|------|------|
| `http.ts` 与 `api/index.ts` 双客户端 | 合并为一个，统一错误提示 |
| baseURL 写死 | 全部改 `import.meta.env.VITE_API_URL` |
| 调试 console.log 密码相关 | 删除 |
| Assistant 时间格式依赖 | 已改用浏览器 `Intl.DateTimeFormat`，不再依赖 dayjs |

## 8. 本地命令

```bash
cd frontend
npm install
npm run dev
npm run type-check   # 可选
npm run build        # 发版前
```

## 9. 手动验收清单

- [ ] 注册 / 登录  
- [ ] 录一条血糖，Dashboard/列表可见  
- [ ] 助理「本周血糖统计」返回数字（fallback 亦可）  
- [ ] 记血糖未确认不落库；确认后落库  
- [ ] 工具轨迹可见  
- [ ] token 过期跳转登录  

## 10. 健康档案与用户信息卡

`SettingsView` 进入页面时必须调用 `GET /api/v1/users/profile`，不能只依赖登录响应或 localStorage 中的残缺用户对象。个人资料、健康档案、密码使用独立提交：

| 区域 | profile 字段 |
|------|--------------|
| 个人资料 | `name`、`email`、`phone`、`birth_date`、`gender` |
| 健康档案 | `diabetes_type`、`diagnosis_date`、`height`、`weight`、`target_glucose_min`、`target_glucose_max` |
| 修改密码 | 仅提交 `password`，不与资料表单混合 |

前端校验：身高 `50–250 cm`、体重 `20–300 kg`、目标血糖 `1–30 mmol/L`，并保证 `target_glucose_min < target_glucose_max`。保存成功后用服务端返回的完整 `User` 同步 Pinia 与 localStorage。

`UserProfileCard` 挂在 Dashboard 右侧栏顶部，展示姓名/头像、糖尿病类型、目标区间、身高、体重、BMI，以及 `/api/v1/glucose/statistics?period=week` 的均值、条数和达标率。组件包含 skeleton、请求失败提示和无记录 empty 状态；操作入口分别前往：

- `/settings#health-profile`：完善健康档案
- `/glucose-record`：记录血糖
- `/assistant?prefill=请解读我的健康档案和最近血糖概况`：请求助理解读
