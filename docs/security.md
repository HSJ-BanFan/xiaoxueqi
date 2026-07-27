# 安全与合规

## 1. 认证

| 项 | 实现 |
|----|------|
| 密码存储 | bcrypt 哈希，禁止明文 |
| 会话 | JWT（HS256），`sub` = user_id |
| 登录 | OAuth2 Password Bearer；`username` 传 email |
| 传输 | 本地 HTTP 可接受；上线必须 HTTPS |

### 配置

- `SECRET_KEY`：生产必须足够长且固定来自密钥管理/环境变量  
- `ACCESS_TOKEN_EXPIRE_MINUTES`：默认较长便于演示；生产应缩短并考虑 refresh  

### 禁止

- 把 `SECRET_KEY`、数据库密码提交进 Git  
- 在日志/前端打印完整 token 或密码  
- README 出现真实连接串  

## 2. 授权与数据隔离

**规则：一切业务数据按 `current_user.id` 隔离。**

检查清单：

- [x] 列表查询带 `user_id == current_user.id`
- [x] 按主键读取后校验属主，失败 403 或 404
- [x] 创建时 body.user_id 不一致 → 403，或服务端强制覆盖
- [ ] 管理员接口单独 `is_superuser`  
- [x] Agent tools 不接受任意 user_id

相关测试见 [testing.md](./testing.md) G1–G4。

## 3. Agent 安全模型

```text
不可信：用户自然语言、模型输出的 tool 参数
可信：JWT 身份、Python tool 实现、DB 约束
```

| 风险 | 缓解 |
|------|------|
| Prompt 注入「删除全部用户」 | tool 无跨用户能力；无危险 admin tool |
| 模型谎称已写入 | 写门禁 + 前端以 tool_results 为准 |
| 参数篡改 user_id | schema 不包含该字段 |
| SSRF（若未来加 webhook tool） | 本期无此 tool；若加需 URL 白名单 |
| 密钥进 prompt | 禁止把 .env 拼进 system prompt |

## 4. CORS

- 开发：显式列出 `http://127.0.0.1:5173`、`http://localhost:5173` 等  
- `allow_credentials=True` 时 **不能** `allow_origins=["*"]`  
- 配置中的 `[IP]` 占位务必改成真实 IP 或删除  

## 5. 依赖与供应链

- 避免默认安装庞大的 `torch` 除非真用本地 embedding  
- 锁定主要依赖版本；生产安装勿用随意 `latest`  
- 定期关注 `python-jose` / `passlib` / FastAPI 安全通告  

## 6. 医疗与产品合规（文案层）

本系统是 **健康自我管理工具**，不是医疗器械或诊疗服务。

必须：

- 助理回复附免责声明  
- UI 可见「非医疗诊断」  
- 不宣传治愈率/替代就医  

简历与 Demo 同样遵守，避免「医疗 AI 诊断」表述。

## 7. 设备与第三方

- `glucose-monitor` mock **不得**宣传为已对接 Freestyle/Dexcom 生产环境  
- 若未来真实对接：OAuth、最小权限、审计日志、密钥轮转  

## 8. 安全自检（发布前）

- [x] `.env` 未进库
- [x] 无固定默认管理员密码
- [x] SQLite / Chroma 数据库文件未被 Git 跟踪
- [ ] Swagger 生产是否需关闭或加保护  
- [x] 越权测试通过
- [x] 无破解软件/盗版教程残留在公开 README
