# 测试策略

## 1. 目标

- 门面项目必须有**可重复的自动化测试**  
- CI/本地不依赖真实 Ollama、不依赖外网 LLM  
- 覆盖：鉴权、越权、血糖主路径、Agent fallback、写确认门禁  

## 2. 目录规划

```text
backend/tests/
  conftest.py
  test_health.py
  test_auth.py
  test_glucose_authz.py
  test_glucose_stats.py
  test_agent_fallback.py
  test_agent_tools.py
  test_agent_runtime_mock_llm.py
```

遗留脚本（`test_login_api.py` 等）可保留作手工冒烟，**新逻辑以 pytest 为准**。

## 3. 依赖

`requirements-dev.txt`（建议新建）：

```text
pytest>=7.4
httpx>=0.25
```

运行：

```bash
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
$env:DATABASE_URL = "sqlite:///./test_diabetes.db"
$env:SECRET_KEY = "test-secret-key"
$env:AGENT_ENABLED = "true"
$env:AGENT_REQUIRE_CONFIRM_WRITE = "true"
pytest -q
```

## 4. conftest 要点

```text
- 使用临时 SQLite（tmp_path 或 memory + StaticPool）
- 覆盖 settings / engine，避免连开发库
- fixture: client (TestClient), user_a, user_b, auth_header_a
- 每个测试函数前 create_all / 后 drop_all 或 transaction rollback
```

注意：`config.SECRET_KEY` 若在 import 时 random，测试与发 token 必须同一 settings 实例。

## 5. 必测用例清单

### 5.1 System

| ID | 用例 | 期望 |
|----|------|------|
| H1 | GET healthz | 200, status=ok |
| H2 | GET readyz（DB 正常） | 200, database.ok=true |

### 5.2 Auth

| ID | 用例 | 期望 |
|----|------|------|
| A1 | 注册新用户 | 200/201 |
| A2 | 重复邮箱注册 | 400 |
| A3 | 正确密码登录 | 返回 access_token |
| A4 | 错误密码 | 401 |
| A5 | 无 token 访问 /glucose | 401 |

### 5.3 Glucose 授权

| ID | 用例 | 期望 |
|----|------|------|
| G1 | A 创建自己的血糖 | 200 |
| G2 | A 列表仅见自己的 | 不含 B |
| G3 | A 读 B 的 record_id | 403 或 404 |
| G4 | body.user_id ≠ current_user | 403 |
| G5 | statistics 空数据 | 200，count=0，不 500 |

### 5.4 Agent tools（无 LLM）

| ID | 用例 | 期望 |
|----|------|------|
| T1 | get_profile | ok，含目标血糖字段 |
| T2 | list_recent_glucose | 与 DB 一致 |
| T3 | get_glucose_stats week | 聚合正确 |
| T4 | evaluate_glucose_alert 低/高/正常 | level 正确 |
| T5 | add 未 confirm | 不落库，requires_confirm=true |
| T6 | add confirm=true | 落库 1 条 |

### 5.5 Agent runtime

| ID | 用例 | 期望 |
|----|------|------|
| R1 | fallback「最近血糖」 | mode=fallback，有 tool_results |
| R2 | fallback「本周统计」 | 含 average 等 |
| R3 | mock LLM 返回 get_glucose_stats tool_call | mode=agent，执行 tool |
| R4 | LLM 超时/连接失败 | 降级 fallback，不 500 |
| R5 | AGENT_ENABLED=false | mode=disabled |

### 5.6 API Agent（集成）

| ID | 用例 | 期望 |
|----|------|------|
| C1 | POST /agent/chat 带 JWT | 200 + reply |
| C2 | 无 JWT | 401 |
| C3 | confirm 写入闭环 | 第二条请求后 DB +1 |

## 6. Mock LLM 方法

优先依赖注入：

```text
HealthAgent(client=FakeClient(...))
```

或 `httpx.MockTransport` 拦截 `{LLM_BASE_URL}/chat/completions`。

Fake 第一轮返回：

```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "tool_calls": [{
        "id": "call_1",
        "type": "function",
        "function": {
          "name": "get_glucose_stats",
          "arguments": "{\"period\":\"week\"}"
        }
      }]
    }
  }]
}
```

第二轮返回纯文本 content。

## 7. 前端测试（可选）

- MVP 可不做组件单测  
- 手动验收清单见 roadmap Phase C  
- 有余力：Vitest + 对 agent API client 的 mock  

## 8. 质量门禁（建议）

合并前至少：

```bash
pytest -q
# 可选
# ruff check app
# cd frontend && npm run type-check
```

## 9. 与简历的关系

可写「pytest 覆盖鉴权、越权、Agent 工具门禁与 fallback」——**以真实通过的用例为准，勿虚报数量**。
