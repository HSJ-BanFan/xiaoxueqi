# 登录问题诊断与修复文档

## 问题描述

用户在尝试登录系统时遇到了认证失败的问题，具体表现为：

- 前端登录请求返回 401 Unauthorized 错误
- 后端日志显示 `ERROR:app.db.session:数据库会话错误`
- 响应状态码为 401 Unauthorized

## 诊断过程

### 1. 检查数据库连接

首先检查数据库连接是否正常：

```python
from app.db.session import engine
print('数据库连接测试:', engine.connect())
```

测试结果表明数据库连接正常，能够成功建立连接。

### 2. 检查用户表

使用 `check_users.py` 脚本检查数据库中的用户记录：

```bash
python check_users.py
```

结果显示数据库中有管理员用户记录：

```
数据库中共有 1 个用户:
{
  "id": "admin-id",
  "email": "admin@local.test",
  "name": "系统管理员",
  "is_active": true,
  "is_superuser": true,
  "hashed_password": "$2b$12$dnH..."
}
```

### 3. 测试后端登录API

使用 `test_login_api.py` 脚本直接测试后端登录API：

```bash
python test_login_api.py
```

测试结果成功，能够获取到访问令牌：

```
开始测试登录API...
发送POST请求到: http://localhost:8000/api/v1/users/login
请求数据: {'username': 'admin@local.test', 'password': '<redacted>'}
响应状态码: 200
登录成功!
响应数据: {
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "admin-id",
  "email": "admin@local.test"
}
```

### 4. 验证完整登录流程

使用 `verify_login.py` 脚本验证完整的登录流程，包括获取用户资料：

```bash
python verify_login.py
```

测试结果表明完整流程正常：

```
开始验证登录过程...
发送POST请求到: http://localhost:8000/api/v1/users/login
请求数据: {'username': 'admin@local.test', 'password': '<redacted>'}
请求头: Content-Type: application/x-www-form-urlencoded
响应状态码: 200
登录成功!
响应数据: {
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "admin-id",
  "email": "admin@local.test"
}

使用令牌获取用户资料...
资料请求状态码: 200
获取用户资料成功!
用户资料: {
  "email": "admin@local.test",
  "name": "系统管理员",
  "is_active": true,
  "phone": null,
  "avatar": null,
  "target_glucose_min": null,
  "target_glucose_max": null,
  "created_at": "2025-07-07T22:11:27",
  "updated_at": "2025-07-07T22:11:27"
}
```

### 5. 检查前端请求

如需在浏览器控制台手工测试，可临时运行以下片段；不要把真实凭据保存到仓库：

```javascript
// 前端登录测试脚本
async function testLogin() {
  console.log('开始测试登录...');
  
  const email = 'admin@local.test';
  const password = '<ADMIN_PASSWORD>';
  
  // 创建表单数据
  const formData = new URLSearchParams();
  formData.append('username', email);
  formData.append('password', password);
  
  // 发送请求
  const response = await fetch('http://localhost:8000/api/v1/users/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData,
    credentials: 'include' // 包含凭证
  });
  
  // ...处理响应...
}
```

## 问题原因

经过诊断，我们发现了以下几个可能的问题原因：

1. **前端请求格式问题**：前端可能没有正确使用表单格式发送登录请求。OAuth2PasswordRequestForm 要求使用 `application/x-www-form-urlencoded` 格式，并且用户名字段必须是 `username` 而不是 `email`。

2. **CORS配置问题**：前端使用了 `withCredentials: true`，这要求后端的 CORS 配置必须明确指定允许的域名，不能使用通配符 `*`。

3. **数据库会话问题**：虽然数据库连接正常，但在处理请求时可能出现会话错误。

## 解决方案

1. **确保正确的请求格式**：
   - 修改前端登录请求，确保使用 `application/x-www-form-urlencoded` 格式
   - 使用 `URLSearchParams` 构造表单数据
   - 确保用户名字段为 `username`（不是 `email`）

2. **优化CORS配置**：
   - 确保后端的 CORS 配置明确列出了所有允许的源
   - 确保 `allow_credentials=True` 已在后端 CORS 中间件中设置

3. **创建管理员账号**：
   - 使用 `create_admin.py` 脚本确保管理员账号存在

4. **添加调试日志**：
   - 在前端添加更详细的日志，记录登录请求的详细信息
   - 在后端添加更详细的日志，记录认证过程中的关键步骤

## 实施结果

通过上述解决方案，登录问题得到了解决：

1. 确认后端API工作正常，能够成功处理登录请求
2. 确认数据库中存在有效的用户记录
3. 修正前端请求格式，确保与后端期望的格式一致
4. 优化CORS配置，解决跨域请求问题

## 预防措施

为了防止类似问题再次发生，我们建议：

1. 添加更详细的错误日志，特别是在认证过程中
2. 为前端开发人员提供API文档，明确说明登录请求的格式要求
3. 添加自动化测试，定期验证登录功能是否正常
4. 在开发环境中提供测试账号信息，方便开发和测试

## 相关文件

- `backend/check_users.py` - 检查数据库中的用户记录
- `backend/create_admin.py` - 创建管理员账号
- `backend/test_login_api.py` - 测试登录API
- `backend/verify_login.py` - 验证完整登录流程
- `frontend/src/test-login.js` - 前端登录测试脚本

## 参考资料

- [FastAPI OAuth2 with Password Flow](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)
- [CORS with credentials](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS/Errors/CORSNotSupportingCredentials)
- [URLSearchParams API](https://developer.mozilla.org/en-US/docs/Web/API/URLSearchParams)
