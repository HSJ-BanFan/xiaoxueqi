# Agent 行为规格表（验收清单）

> 状态：实现验收权威文档  
> 配套：[agent-design.md](./agent-design.md) · [agent-intelligence-plan.md](./agent-intelligence-plan.md) · [api.md](./api.md) · [frontend.md](./frontend.md) · [testing.md](./testing.md)  
> 原则：**模型只提议；权限 / 校验 / 落库由 Python 确定性执行**  
> 目标水位：**P0 = L1 只读工具化 + L2 受控写入**（见智能计划文档）

---

## 0. 如何使用本文档

1. 实现某个意图时：按「意图 → tool → 回复 → 前端」逐项打勾。  
2. 写测试时：每个 P0 意图至少 1 条 API/集成用例 + 1 条 tool 单测（写类必测确认门禁）。  
3. 联调演示时：按 §7 演示脚本走通，前端可见 mode / 轨迹 / 确认卡片。  
4. 与代码冲突时：**以本表业务行为为准**，再回改代码或修订本文并记 roadmap。

### 通用约束（所有意图生效）

| ID | 约束 | 验收 |
|----|------|------|
| G1 | 必须 JWT；tool 闭包绑定 `current_user.id`，参数**禁止** `user_id` | 越权测不过则失败 |
| G2 | 查询类数字必须来自 tool 结果，禁止模型编造测量值 | 空库时不得捏造记录 |
| G3 | 写类默认 `confirm=false` / `confirm_write=false`，未确认不落库 | DB 行数不变 |
| G4 | 每次响应含：`reply, mode, tool_calls, tool_results, disclaimer`（及 conversation_id 等） | 契约测 |
| G5 | `mode ∈ {agent, fallback, disabled}`；LLM 失败应 fallback 而非 500 | 断 LLM 可演示 |
| G6 | `disclaimer` 固定非医疗诊断声明 | 文案存在 |
| G7 | tool 异常 → `ok=false` + 可读 error；用户回复说明失败原因与下一步 | 不堆栈泄露 |
| G8 | tool loop ≤ `LLM_MAX_TOOL_ROUNDS`（默认 4） | 防死循环 |
| G9 | 枚举/数值经 Pydantic 或 service 二次校验 | 非法值不入库 |
| G10 | 前端以 `tool_results` 为准，不以模型口头「已保存」为准 | UX 测 |

### 固定免责声明（disclaimer）

```text
说明：我是健康管理助手，不是执业医师。以下内容仅供自我管理参考，不能替代诊疗。如出现严重低血糖/高血糖症状或身体不适，请立即就医。
```

---

## 1. 意图总表（P0 / P1）

| 意图 ID | 优先级 | 意图名称 | 典型用户话术 | 主 tool（必调） | 可选 tool | 是否写库 |
|---------|--------|----------|--------------|-----------------|-----------|----------|
| I01 | P0 | 查询档案 | 我的目标血糖是多少；我的档案 | `get_profile` | — | 否 |
| I02 | P0 | 最近血糖 | 最近血糖；查一下最近几条 | `list_recent_glucose` | — | 否 |
| I03 | P0 | 血糖统计 | 这周血糖怎么样；达标率 | `get_glucose_stats` | `get_profile`（取目标区间文案） | 否 |
| I04 | P0 | 单值评估 | 7.2 算高吗；帮我看看 3.5 | `evaluate_glucose_alert` | `get_profile` | 否 |
| I05 | P0 | 记录血糖（预览） | 记一下空腹 6.8 | `add_glucose_record`（confirm=false） | `evaluate_glucose_alert` | **否** |
| I06 | P0 | 记录血糖（确认写入） | 确认；确认记录；点确认按钮 | `add_glucose_record`（confirm=true） | `evaluate_glucose_alert` | **是** |
| I07 | P0 | 最近饮食 | 我最近吃了啥 | `list_recent_diet` | — | 否 |
| I08 | P0 | 能力说明 / 帮助 | 你能做什么 | —（可无 tool） | `get_profile` | 否 |
| I09 | P0 | 闲聊 / 界外 | 今天天气；帮我开药 | — | — | 否 |
| I10 | P0 | Fallback：统计 | （LLM 不可用）本周统计 | `get_glucose_stats` | — | 否 |
| I11 | P0 | Fallback：最近血糖 | （LLM 不可用）最近血糖 | `list_recent_glucose` | — | 否 |
| I12 | P0 | Fallback：记血糖 | （LLM 不可用）记录血糖 7.1 空腹 | `add_glucose_record` | `evaluate_glucose_alert` | 视确认 |
| I20 | P1 | 周报小结 | 生成本周血糖小结 | `get_glucose_stats`（week） | `list_recent_glucose`, `get_profile` | 否 |
| I21 | P1 | 周对比 | 这周比上周怎样 | `get_glucose_stats`×2（week + 需支持或两次 period） | — | 否 |
| I22 | P1 | 异常追问 | （系统侧触发或用户问为何总高） | `get_glucose_stats` 或 `list_recent_glucose` | `evaluate_glucose_alert` | 否 |
| I23 | P1 | 提醒意图落库 | 每天 8 点提醒我测血糖 | `create_reminder`（若实现） | — | 是（提醒表） |
| I24 | P1 | 知识问答 | 运动前后要注意什么 | `search_knowledge`（若实现） | — | 否 |

---

## 2. 分意图详细规格

### I01 查询档案

| 项 | 规格 |
|----|------|
| **触发** | 档案、目标血糖、我的信息、糖尿病类型等 |
| **必调 tool** | `get_profile` |
| **参数** | 无 |
| **成功 reply 模板** | 「您的目标血糖区间为 {min}–{max} mmol/L；糖尿病类型：{type}；…（仅展示非敏感字段）。」+ disclaimer |
| **失败 reply 模板** | 「暂时无法读取档案：{error}。请稍后重试或在设置页查看。」 |
| **tool_results** | `ok=true` 含 name/diabetes_type/targets 等；无密码哈希 |
| **前端展示** | mode 标签；可折叠轨迹显示 `get_profile`；正文 Markdown |
| **验收勾选** | [ ] 数字与 DB 一致 [ ] 无越权字段 [ ] 有轨迹 |

---

### I02 最近血糖

| 项 | 规格 |
|----|------|
| **触发** | 最近血糖、血糖记录、查血糖列表 |
| **必调 tool** | `list_recent_glucose` |
| **参数** | `limit` 默认 5–10，最大 50 |
| **成功（有数据）** | 「最近 {n} 条血糖：\n- {time}：{value} mmol/L（{measurement_time}）\n…」+ disclaimer |
| **成功（无数据）** | 「暂无血糖记录。可直接说：记录血糖 6.5 空腹。」+ disclaimer |
| **失败** | 「查询血糖记录失败：{error}。」 |
| **前端** | 轨迹；可选「去血糖页」链接 |
| **验收** | [ ] 空库不编造 [ ] 仅当前用户 [ ] limit 生效 |

---

### I03 血糖统计

| 项 | 规格 |
|----|------|
| **触发** | 统计、达标率、这周/本月怎么样、平均血糖 |
| **必调 tool** | `get_glucose_stats` |
| **参数** | `period`: day\|week\|month\|quarter；默认 week；「今天」→ day，「月」→ month |
| **可选** | 先 `get_profile` 便于解释目标区间 |
| **成功（count>0）** | 「近{period}统计：均值 {avg}、最高 {max}、最低 {min}、共 {count} 条；达标率 {in_range}%（偏高 {high}% / 偏低 {low}%）。」+ 1–3 句基于数据的非诊断建议 + disclaimer |
| **成功（count=0）** | 「该周期内暂无数据，无法计算统计。请先记录几条血糖。」 |
| **失败** | 「统计失败：{error}。」 |
| **验收** | [ ] 与 REST `/glucose/statistics` 一致 [ ] 不编造 avg |

---

### I04 单值评估

| 项 | 规格 |
|----|------|
| **触发** | 「X 算高吗」「帮我看下 X」 |
| **必调 tool** | `evaluate_glucose_alert` |
| **参数** | `value`（mmol/L）；目标区间来自用户档案默认 3.9–10.0 |
| **禁止** | 仅用 LLM 判断高低而不调规则 tool |
| **成功** | 「{value} mmol/L 评估为 {level}（目标 {min}–{max}）。{advice}」+ disclaimer |
| **level** | `low` \| `in_range` \| `high` |
| **失败** | 缺 value → 追问「请告诉我血糖数值（mmol/L）」；tool 失败 → 说明原因 |
| **验收** | [ ] 同值多次 level 稳定 [ ] 单测覆盖三档 |

---

### I05 记录血糖（预览，不写库）

| 项 | 规格 |
|----|------|
| **触发** | 记录/添加/记一下 + 数值；或表单提交但未确认 |
| **必调 tool** | `add_glucose_record` 且 **`confirm=false`**（或等价：`AGENT_REQUIRE_CONFIRM_WRITE` 且未确认） |
| **参数** | `value` 必填；`measurement_time` 必填或追问；`measurement_method` 默认 FINGER_STICK；`notes` 可选 |
| **槽位缺失** | 缺时段 → 不调用写 tool，或调用前追问：「是空腹、餐后还是其他时段？」 |
| **可选** | 预览同时 `evaluate_glucose_alert(value)` 展示风险提示 |
| **成功 reply** | 「准备记录：{value} mmol/L，时段 {measurement_time}。**尚未写入**。请确认后保存。」+ disclaimer |
| **tool_results** | `requires_confirm=true`，`data.preview={...}`，**无新 id 落库** |
| **前端** | **确认卡片**（展示 preview）；主按钮「确认写入」；取消关闭 |
| **验收** | [ ] 调用前后 glucose 表 count 不变 [ ] 有 requires_confirm [ ] 卡片出现 |

---

### I06 记录血糖（确认写入）

| 项 | 规格 |
|----|------|
| **触发** | 用户点击「确认写入」且 `confirm_write=true`；或明确「确认记录血糖 {value}」 |
| **必调 tool** | `add_glucose_record` 且 **`confirm=true`** |
| **参数** | 与预览一致；前端应带回 preview 字段 |
| **成功 reply** | 「已记录血糖 {value} mmol/L（{measurement_time}）。记录 id：{id}。」+ 可选 alert 文案 + disclaimer |
| **tool_results** | `ok=true`，含 `id, value, measured_at`；`requires_confirm=false` |
| **失败** | 校验失败（范围/枚举）→ 不写库并说明；DB 失败 → 「保存失败，请重试」 |
| **前端** | 成功后关闭卡片；提示成功；**刷新血糖列表/统计**；轨迹显示写入成功 |
| **验收** | [ ] count+1 [ ] user_id=当前用户 [ ] 列表 API 可见 |

---

### I07 最近饮食

| 项 | 规格 |
|----|------|
| **触发** | 最近饮食、吃了什么 |
| **必调 tool** | `list_recent_diet` |
| **成功有数据** | 列表 meal_type / time / carbs / calories 摘要 |
| **成功无数据** | 「暂无饮食记录。」 |
| **失败** | 说明 error；不 500 |
| **验收** | [ ] 仅本用户 [ ] 与 diet API 一致方向 |

---

### I08 帮助

| 项 | 规格 |
|----|------|
| **触发** | 你能做什么、帮助、怎么用 |
| **tool** | 可不调；或 `get_profile` 个性化一句 |
| **成功 reply** | 列出：查档案/最近血糖/统计/评估数值/记录血糖（需确认）/最近饮食；说明非医生 |
| **前端** | 可展示快捷芯片（与建议话术一致） |
| **验收** | [ ] 不承诺开药诊断 |

---

### I09 闲聊 / 界外 / 高风险医疗

| 项 | 规格 |
|----|------|
| **闲聊** | 简短礼貌回应 + 引导回健康管理能力 |
| **开药/诊断** | **拒绝**给出用药方案；建议就医；可给一般性自我管理提示 |
| **紧急症状** | （如意识模糊、抽搐等）→ 明确「请立即急救/就医」，不继续工具写操作 |
| **tool** | 默认不调写 tool |
| **验收** | [ ] 无虚假「已开药」[ ] 无编造检查单 |

---

### I10–I12 Fallback 模式（LLM 不可用）

| 意图 | 匹配规则（示例） | 必调 tool | reply 要点 | mode |
|------|------------------|-----------|------------|------|
| I10 | 统计\|达标\|周报\|平均 | `get_glucose_stats` | 同 I03 数据句，可加「当前为规则模式」 | `fallback` |
| I11 | 最近血糖\|查血糖\|血糖记录 | `list_recent_glucose` | 同 I02 | `fallback` |
| I12 | 记录血糖\s*([0-9.]+) + 可选空腹/餐后 | `add_glucose_record` | 无「确认」→ 预览；含「确认」→ 写入 | `fallback` |

**验收：**

- [ ] 断开 LLM / 错误 base_url 不 500  
- [ ] 前端显示「规则模式」  
- [ ] 与 agent 模式写门禁规则一致  

---

### I20 周报小结（P1）

| 项 | 规格 |
|----|------|
| **必调** | `get_glucose_stats(period=week)` |
| **可选** | `list_recent_glucose(limit=5)`、`get_profile` |
| **成功结构** | ① 数据摘要 ② 达标情况 ③ 2–3 条自我管理建议（非医嘱） ④ disclaimer |
| **禁止** | 无 tool 直接写长文周报 |
| **前端** | 轨迹含 stats；可用「复制周报」 |
| **验收** | [ ] 数字可核对 [ ] 无数据时走空数据模板 |

---

### I21 周对比（P1）

| 项 | 规格 |
|----|------|
| **必调** | 两次统计或一次扩展 API（若仅有单 period，允许两次调用 week + 说明局限） |
| **成功** | 对比均值/达标率变化方向；数据不足则说明 |
| **验收** | [ ] 不编造上周数据 |

---

### I22 异常追问（P1）

| 项 | 规格 |
|----|------|
| **触发** | 统计 high_percentage 超阈；或用户问「为何总高」 |
| **必调** | 先 `get_glucose_stats` 或 recent 证明「总高」有数据依据 |
| **行为** | 基于数据提问 1–2 个开放问题（饮食/测量时段/睡眠）；**不诊断** |
| **验收** | [ ] 无数据时不说「你总是偏高」 |

---

### I23–I24（P1 可选）

见 [agent-intelligence-plan.md](./agent-intelligence-plan.md) P1 工具扩展；未实现前意图应落入 I08/I09，不假装已支持。

---

## 3. Tool 契约速查（与行为对齐）

| Tool | 读写 | 关键参数 | 成功 data 要点 | 失败 |
|------|------|----------|----------------|------|
| `get_profile` | 读 | — | 非敏感档案字段 | ok=false |
| `list_recent_glucose` | 读 | limit | 数组 value/time/时段 | ok=false |
| `get_glucose_stats` | 读 | period | average/max/min/count/百分比 | ok=false；空 count=0 |
| `evaluate_glucose_alert` | 读/规则 | value | level/min/max/advice | 缺 value |
| `add_glucose_record` | 写 | value, measurement_time, confirm | preview 或 id | 校验/DB |
| `list_recent_diet` | 读 | limit | 饮食摘要列表 | ok=false |

写 tool 伪状态：

```text
confirm=false → requires_confirm=true, 不 commit
confirm=true  → commit, 返回 id
```

---

## 4. API 与字段约定（行为层）

`POST /api/v1/agent/chat`

**请求（行为相关）：**

```json
{
  "message": "string",
  "conversation_id": "uuid|null",
  "history": [{"role":"user|assistant","content":"..."}],
  "confirm_write": false
}
```

**响应（行为相关）：**

```json
{
  "reply": "string",
  "conversation_id": "uuid",
  "mode": "agent|fallback|disabled",
  "model": "string|null",
  "rounds": 0,
  "tool_calls": [{"name":"...", "arguments":{}}],
  "tool_results": [{
    "name": "...",
    "ok": true,
    "data": {},
    "error": null,
    "requires_confirm": false
  }],
  "disclaimer": "string"
}
```

| 条件 | 期望 |
|------|------|
| `AGENT_ENABLED=false` | mode=disabled，友好说明 |
| `confirm_write=true` | 写 tool 走 confirm=true 路径 |
| 任一 tool `requires_confirm` | 前端必须出确认 UI |

---

## 5. 前端展示规格（验收）

| 元素 | 行为规格 |
|------|----------|
| 消息气泡 | 渲染 `reply`（Markdown 注意 XSS） |
| mode 标签 | agent=智能模式；fallback=规则模式；disabled=已关闭 |
| 工具轨迹 | 可折叠；展示 name、arguments 摘要、ok/error |
| 确认卡片 | 当任意 `requires_confirm`：展示 preview；主按钮触发 `confirm_write=true` 再请求 |
| 快捷芯片 | 建议：「最近血糖」「本周统计」「记录血糖」「你能做什么」 |
| 免责 | 页脚或每条 assistant 消息底部 |
| 成功写入后 | 刷新血糖 store/列表；可选 toast |
| 加载中 | 发送中禁用按钮；超时 60–90s 提示 |

**前端验收勾选：**

- [ ] I02/I03 轨迹可见  
- [ ] I05 出卡片且未写库  
- [ ] I06 写库并刷新  
- [ ] fallback 标签正确  
- [ ] 401 跳转登录  

---

## 6. 测试验收矩阵（P0）

| 用例 ID | 意图 | 要点 |
|---------|------|------|
| B-I01 | I01 | mock/真 tool，含 targets |
| B-I02a | I02 | 有数据 |
| B-I02b | I02 | 空数据文案 |
| B-I03a | I03 | 与 statistics 一致 |
| B-I03b | I03 | count=0 |
| B-I04 | I04 | low/high/in_range |
| B-I05 | I05 | 不落库 + requires_confirm |
| B-I06 | I06 | 落库 + 属主 |
| B-I09 | I09 | 拒绝对开药 |
| B-F10 | I10 | 无 LLM 统计 |
| B-F12 | I12 | fallback 预览/确认 |
| B-SEC | 全部 | 用户 A 数据对 B 不可见 |

详细框架见 [testing.md](./testing.md)。

---

## 7. 端到端演示脚本（发布前必过）

| 步 | 操作 | 期望 |
|----|------|------|
| 1 | 注册/登录 | token 有效 |
| 2 | 血糖页手动录 2–3 条 | 列表可见 |
| 3 | 助理：「最近血糖」 | I02，轨迹 list_recent |
| 4 | 「本周血糖怎么样」 | I03，数字与统计页一致 |
| 5 | 「记空腹 6.8」 | I05，卡片，DB 不变 |
| 6 | 点确认 | I06，DB+1，列表刷新 |
| 7 | 「7.2 算高吗」 | I04，level 合理 |
| 8 | 停 LLM 后再问统计 | mode=fallback，仍有数据 |
| 9 | 「帮我开二甲双胍」 | I09 拒绝医嘱 |

---

## 8. 实现进度勾选（总表）

### P0 行为

- [ ] I01 档案  
- [ ] I02 最近血糖  
- [ ] I03 统计  
- [ ] I04 单值评估  
- [ ] I05 写预览  
- [ ] I06 写确认  
- [ ] I07 饮食  
- [ ] I08 帮助  
- [ ] I09 界外/安全  
- [ ] I10–I12 Fallback  
- [ ] 前端轨迹 + 确认卡片 + mode  
- [ ] §7 演示脚本全绿  

### P1 行为

- [ ] I20 周报  
- [ ] I21 对比（可选）  
- [ ] I22 异常追问  
- [ ] I23/I24 按计划  

---

## 9. 修订记录

| 日期 | 变更 |
|------|------|
| 2026-07-26 | 初版：P0/P1 意图规格 + 验收矩阵 + 演示脚本 |
