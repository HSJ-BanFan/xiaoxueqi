# 糖尿病助手项目API文档

## 概述

糖尿病助手项目使用FastAPI框架构建，所有API路由前缀为`/api/v1`。API遵循RESTful设计原则，使用标准HTTP方法（GET、POST、PUT、DELETE）进行资源操作。

## 认证机制

除了注册和登录接口外，所有API都需要认证。认证使用JWT令牌，通过Authorization头部传递：

```
Authorization: Bearer {token}
```

## 通用响应格式

### 成功响应

```json
{
  "data": {}, // 响应数据，根据API不同而变化
  "message": "操作成功", // 可选的成功消息
  "status": "success" // 状态标识
}
```

### 错误响应

```json
{
  "detail": "错误信息" // 字符串或详细的验证错误对象
}
```

验证错误格式：

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "错误描述",
      "type": "错误类型"
    }
  ]
}
```

## 分页响应格式

支持分页的接口返回以下格式：

```json
{
  "items": [], // 当前页的数据项
  "total": 100, // 总记录数
  "page": 1, // 当前页码
  "size": 20, // 每页大小
  "pages": 5 // 总页数
}
```

## API详细说明

### 1. 用户管理 `/api/v1/users`

#### 1.1 注册新用户 `POST /register`

**请求体**：

```json
{
  "email": "user@example.com", // 必填，有效的邮箱地址
  "username": "username", // 必填，3-20个字符
  "password": "password", // 必填，至少8个字符
  "full_name": "Full Name" // 可选
}
```

**响应**：

```json
{
  "id": "user_id",
  "email": "user@example.com",
  "username": "username",
  "full_name": "Full Name",
  "is_active": true,
  "created_at": "2023-01-01T00:00:00",
  "updated_at": "2023-01-01T00:00:00"
}
```

#### 1.2 用户登录 `POST /login`

**请求体**：

```json
{
  "username": "username", // 必填
  "password": "password" // 必填
}
```

**响应**：

```json
{
  "access_token": "eyJhbGciOiJIUzI1...",
  "token_type": "bearer"
}
```

#### 1.3 健康风险评估 `POST /risk-assessment`

**请求体**：

```json
{
  "age": 45, // 必填，年龄
  "gender": "male", // 必填，性别 (male/female)
  "fasting_glucose": 7.2, // 必填，空腹血糖值 (mmol/L)
  "bmi": 28.5, // 必填，体质指数
  "family_history": true, // 必填，家族糖尿病史
  "physical_activity": "low", // 必填，身体活动水平 (low/moderate/high)
  "smoking": false // 必填，是否吸烟
}
```

**响应**：

```json
{
  "risk_score": 75, // 风险评分 (0-100)
  "risk_level": "high", // 风险等级 (low/moderate/high)
  "recommendations": [
    "建议每周进行至少150分钟中等强度的有氧运动",
    "控制碳水化合物摄入，增加蔬菜和优质蛋白质的比例"
  ]
}
```

### 2. 健康记录 `/api/v1/health`

#### 2.1 创建健康记录 `POST /`

**请求体**：

```json
{
  "user_id": "user_id", // 必填，用户ID
  "weight": 68.5, // 可选，体重(kg)
  "blood_pressure_systolic": 120, // 可选，收缩压(mmHg)
  "blood_pressure_diastolic": 80, // 可选，舒张压(mmHg)
  "heart_rate": 72, // 可选，心率(bpm)
  "temperature": 36.5, // 可选，体温(°C)
  "oxygen_saturation": 98, // 可选，血氧饱和度(%)
  "steps": 8000, // 可选，步数
  "sleep_hours": 7.5, // 可选，睡眠时间(小时)
  "notes": "感觉良好", // 可选，备注
  "recorded_at": "2023-01-01T08:00:00" // 必填，记录时间
}
```

**响应**：返回创建的健康记录，包含ID和时间戳。

#### 2.2 获取健康记录 `GET /`

**查询参数**：

- `page`: 页码，默认1
- `size`: 每页大小，默认20
- `start_date`: 开始日期，格式YYYY-MM-DD
- `end_date`: 结束日期，格式YYYY-MM-DD

**响应**：返回分页的健康记录列表。

#### 2.3 获取单条健康记录 `GET /{record_id}`

**路径参数**：

- `record_id`: 健康记录ID

**响应**：返回指定ID的健康记录详情。

#### 2.4 更新健康记录 `PUT /{record_id}`

**路径参数**：

- `record_id`: 健康记录ID

**请求体**：与创建健康记录相同，所有字段均为可选。

**响应**：返回更新后的健康记录。

#### 2.5 删除健康记录 `DELETE /{record_id}`

**路径参数**：

- `record_id`: 健康记录ID

**响应**：

```json
{
  "message": "健康记录已删除",
  "status": "success"
}
```

### 3. 血糖记录 `/api/v1/glucose`

#### 3.1 创建血糖记录 `POST /`

**请求体**：

```json
{
  "user_id": "user_id", // 必填，用户ID
  "value": 5.6, // 必填，血糖值(mmol/L)
  "measured_at": "2023-01-01T08:00:00", // 必填，测量时间
  "measurement_time": "BEFORE_BREAKFAST", // 必填，测量类型
  "measurement_method": "FINGER_STICK", // 必填，测量方法
  "notes": "早餐前测量" // 可选，备注
}
```

**测量类型选项**：
- `BEFORE_BREAKFAST`: 早餐前
- `AFTER_BREAKFAST`: 早餐后
- `BEFORE_LUNCH`: 午餐前
- `AFTER_LUNCH`: 午餐后
- `BEFORE_DINNER`: 晚餐前
- `AFTER_DINNER`: 晚餐后
- `BEFORE_SLEEP`: 睡前
- `MIDNIGHT`: 半夜
- `OTHER`: 其他

**测量方法选项**：
- `FINGER_STICK`: 指尖采血
- `CONTINUOUS_MONITOR`: 连续监测
- `LAB_TEST`: 实验室检验
- `OTHER`: 其他

**响应**：返回创建的血糖记录，包含ID和时间戳。

#### 3.2 获取血糖记录列表 `GET /`

**查询参数**：

- `page`: 页码，默认1
- `size`: 每页大小，默认20
- `start_date`: 开始日期，格式YYYY-MM-DD
- `end_date`: 结束日期，格式YYYY-MM-DD

**响应**：返回分页的血糖记录列表。

#### 3.3 获取血糖统计数据 `GET /statistics`

**查询参数**：

- `period`: 统计周期，可选值为`day`、`week`、`month`、`year`，默认`week`
- `start_date`: 开始日期，格式YYYY-MM-DD
- `end_date`: 结束日期，格式YYYY-MM-DD

**响应**：

```json
{
  "average": 5.8, // 平均血糖值
  "max_value": 8.2, // 最高血糖值
  "min_value": 4.1, // 最低血糖值
  "count": 28, // 记录总数
  "high_count": 3, // 高血糖记录数
  "low_count": 1, // 低血糖记录数
  "in_range_percentage": 85.7, // 达标率(%)
  "high_percentage": 10.7, // 高血糖率(%)
  "low_percentage": 3.6, // 低血糖率(%)
  "std_deviation": 0.9, // 标准差
  "period": "week" // 统计周期
}
```

#### 3.4 获取最近血糖记录 `GET /recent`

**查询参数**：

- `days`: 天数，默认7

**响应**：返回指定天数内的血糖记录列表。

#### 3.5 获取单条血糖记录 `GET /{record_id}`

**路径参数**：

- `record_id`: 血糖记录ID

**响应**：返回指定ID的血糖记录详情。

#### 3.6 更新血糖记录 `PUT /{record_id}`

**路径参数**：

- `record_id`: 血糖记录ID

**请求体**：与创建血糖记录相同，所有字段均为可选。

**响应**：返回更新后的血糖记录。

#### 3.7 删除血糖记录 `DELETE /{record_id}`

**路径参数**：

- `record_id`: 血糖记录ID

**响应**：

```json
{
  "message": "血糖记录已删除",
  "status": "success"
}
```

### 4. 饮食记录 `/api/v1/diet`

#### 4.1 创建饮食记录 `POST /`

**请求体**：

```json
{
  "user_id": "user_id", // 必填，用户ID
  "meal_type": "BREAKFAST", // 必填，餐食类型
  "food_items": ["全麦面包", "鸡蛋", "牛奶"], // 必填，食物列表
  "carbohydrates": 45, // 可选，碳水化合物(g)
  "proteins": 20, // 可选，蛋白质(g)
  "fats": 15, // 可选，脂肪(g)
  "calories": 400, // 可选，卡路里(kcal)
  "notes": "早餐", // 可选，备注
  "consumed_at": "2023-01-01T08:00:00" // 必填，用餐时间
}
```

**餐食类型选项**：
- `BREAKFAST`: 早餐
- `LUNCH`: 午餐
- `DINNER`: 晚餐
- `SNACK`: 零食
- `OTHER`: 其他

**响应**：返回创建的饮食记录，包含ID和时间戳。

#### 4.2 获取饮食记录列表 `GET /`

**查询参数**：

- `page`: 页码，默认1
- `size`: 每页大小，默认20
- `start_date`: 开始日期，格式YYYY-MM-DD
- `end_date`: 结束日期，格式YYYY-MM-DD

**响应**：返回分页的饮食记录列表。

#### 4.3 获取最近饮食记录 `GET /recent`

**查询参数**：

- `days`: 天数，默认1

**响应**：返回指定天数内的饮食记录列表。

#### 4.4 获取饮食统计数据 `GET /statistics`

**查询参数**：

- `period`: 统计周期，可选值为`day`、`week`、`month`，默认`day`

**响应**：

```json
{
  "total_calories": 1850, // 总卡路里
  "total_carbs": 210, // 总碳水化合物(g)
  "total_proteins": 95, // 总蛋白质(g)
  "total_fats": 65, // 总脂肪(g)
  "carbs_percentage": 45.4, // 碳水化合物占比(%)
  "proteins_percentage": 20.5, // 蛋白质占比(%)
  "fats_percentage": 31.6, // 脂肪占比(%)
  "meal_count": 4, // 餐食数量
  "period": "day" // 统计周期
}
```

#### 4.5 获取单条饮食记录 `GET /{record_id}`

**路径参数**：

- `record_id`: 饮食记录ID

**响应**：返回指定ID的饮食记录详情。

#### 4.6 上传食物图片 `POST /upload-image`

**请求体**：

```
Content-Type: multipart/form-data
file: [图片文件]
```

**响应**：

```json
{
  "file_path": "/uploads/foods/image.jpg",
  "file_size": 1024,
  "message": "图片上传成功"
}
```

### 5. 智能助手 `/api/v1/assistant`

#### 5.1 聊天接口 `POST /chat`

**请求体**：

```json
{
  "user_id": "user_id", // 必填，用户ID
  "message": "我的血糖有点高，应该怎么办？", // 必填，用户消息
  "conversation_id": "conversation_id" // 可选，对话ID，不提供则创建新对话
}
```

**响应**：

```json
{
  "message_id": "message_id",
  "response": "高血糖可能与饮食、运动等因素有关...",
  "conversation_id": "conversation_id",
  "created_at": "2023-01-01T12:00:00"
}
```

#### 5.2 获取聊天历史 `GET /history`

**查询参数**：

- `user_id`: 用户ID，必填
- `conversation_id`: 对话ID，可选
- `limit`: 消息数量限制，默认50

**响应**：返回聊天历史记录列表。

#### 5.3 清空聊天历史 `DELETE /history`

**查询参数**：

- `user_id`: 用户ID，必填
- `conversation_id`: 对话ID，可选，不提供则清空所有对话

**响应**：

```json
{
  "message": "聊天历史已清空",
  "status": "success"
}
```

#### 5.4 创建对话 `POST /conversations`

**请求体**：

```json
{
  "user_id": "user_id", // 必填，用户ID
  "title": "血糖管理咨询" // 必填，对话标题
}
```

**响应**：返回创建的对话信息。

#### 5.5 获取对话列表 `GET /conversations`

**查询参数**：

- `user_id`: 用户ID，必填
- `page`: 页码，默认1
- `size`: 每页大小，默认20

**响应**：返回分页的对话列表。

#### 5.6 获取单个对话 `GET /conversations/{conversation_id}`

**路径参数**：

- `conversation_id`: 对话ID

**响应**：返回指定ID的对话详情。

#### 5.7 更新对话 `PUT /conversations/{conversation_id}`

**路径参数**：

- `conversation_id`: 对话ID

**请求体**：

```json
{
  "title": "新的对话标题" // 必填，对话标题
}
```

**响应**：返回更新后的对话信息。

#### 5.8 删除对话 `DELETE /conversations/{conversation_id}`

**路径参数**：

- `conversation_id`: 对话ID

**响应**：

```json
{
  "message": "对话已删除",
  "status": "success"
}
```

#### 5.9 创建消息 `POST /messages`

**请求体**：

```json
{
  "conversation_id": "conversation_id", // 必填，对话ID
  "role": "user", // 必填，角色(user/assistant)
  "content": "我的血糖有点高，应该怎么办？" // 必填，消息内容
}
```

**响应**：返回创建的消息信息。

#### 5.10 获取对话消息 `GET /conversations/{conversation_id}/messages`

**路径参数**：

- `conversation_id`: 对话ID

**查询参数**：

- `page`: 页码，默认1
- `size`: 每页大小，默认50

**响应**：返回分页的消息列表。

### 6. 知识库 `/api/v1/knowledge`

#### 6.1 创建知识库条目 `POST /`

**请求体**：

```json
{
  "title": "如何控制餐后血糖", // 必填，标题
  "content": "餐后血糖控制是糖尿病管理的关键...", // 必填，内容
  "category": "饮食管理", // 必填，分类
  "tags": ["血糖控制", "饮食", "餐后"] // 必填，标签
}
```

**响应**：返回创建的知识库条目。

#### 6.2 获取知识库条目列表 `GET /`

**查询参数**：

- `page`: 页码，默认1
- `size`: 每页大小，默认20
- `category`: 分类过滤，可选
- `tag`: 标签过滤，可选
- `search`: 搜索关键词，可选

**响应**：返回分页的知识库条目列表。

#### 6.3 获取单个知识库条目 `GET /{entry_id}`

**路径参数**：

- `entry_id`: 知识库条目ID

**响应**：返回指定ID的知识库条目详情。

#### 6.4 更新知识库条目 `PUT /{entry_id}`

**路径参数**：

- `entry_id`: 知识库条目ID

**请求体**：与创建知识库条目相同，所有字段均为可选。

**响应**：返回更新后的知识库条目。

#### 6.5 删除知识库条目 `DELETE /{entry_id}`

**路径参数**：

- `entry_id`: 知识库条目ID

**响应**：

```json
{
  "message": "知识库条目已删除",
  "status": "success"
}
```

### 7. 大模型服务 `/api/v1/ollama`

#### 7.1 获取可用模型列表 `GET /models`

**响应**：

```json
{
  "models": [
    {
      "name": "llama2",
      "modified_at": "2023-01-01T00:00:00",
      "size": 4000000000,
      "parameters": "7B"
    }
  ]
}
```

#### 7.2 获取模型信息 `GET /models/{model_name}`

**路径参数**：

- `model_name`: 模型名称

**响应**：返回指定模型的详细信息。

#### 7.3 生成文本(GET方法) `GET /generate`

**查询参数**：

- `model`: 模型名称，必填
- `prompt`: 提示词，必填
- `max_tokens`: 最大生成token数，默认256

**响应**：

```json
{
  "model": "llama2",
  "created_at": "2023-01-01T12:00:00",
  "response": "生成的文本内容...",
  "done": true,
  "total_duration": 2500,
  "load_duration": 500,
  "prompt_eval_count": 10,
  "prompt_eval_duration": 1000,
  "eval_count": 50,
  "eval_duration": 1000
}
```

#### 7.4 生成文本(POST方法) `POST /generate`

**请求体**：

```json
{
  "model": "llama2", // 必填，模型名称
  "prompt": "请给我一些控制血糖的建议", // 必填，提示词
  "stream": false, // 可选，是否流式输出，默认false
  "max_tokens": 512, // 可选，最大生成token数，默认256
  "temperature": 0.7 // 可选，温度参数，默认0.8
}
```

**响应**：与GET方法相同。

#### 7.5 检查服务健康状态 `GET /health`

**响应**：

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "models_loaded": ["llama2"]
}
```

### 8. 食物营养数据 `/api/v1/nutrition`

#### 8.1 创建食物营养记录 `POST /`

**请求体**：

```json
{
  "name_cn": "全麦面包", // 必填，食物中文名称
  "calories": 265, // 必填，卡路里(kcal)
  "protein": 11.0, // 必填，蛋白质(g)
  "fat": 3.5, // 必填，脂肪(g)
  "carbs": 48.0, // 必填，碳水化合物(g)
  "gi": 50, // 可选，血糖指数
  "category": "谷物类", // 必填，食物分类
  "diabetes_index": 2.5, // 可选，糖尿病指数
  "diabetes_friendly": 1, // 可选，是否适合糖尿病患者(1是，0否)
  "image_url": "https://example.com/foods/whole-wheat-bread.jpg" // 可选，食物图片URL或SVG数据
}
```

**响应**：返回创建的食物营养记录，包含ID。

#### 8.2 获取食物营养记录列表 `GET /`

**查询参数**：

- `page`: 页码，默认1
- `size`: 每页大小，默认20
- `category`: 食物分类，可选
- `diabetes_friendly`: 是否适合糖尿病患者(1是，0否)，可选
- `search`: 食物名称搜索关键词，可选
- `sort_by`: 排序字段，可选值为`calories`、`protein`、`fat`、`carbs`、`gi`，默认不排序
- `sort_order`: 排序方向，可选值为`asc`、`desc`，默认`asc`

**响应**：返回分页的食物营养记录列表。

#### 8.3 获取单个食物营养记录 `GET /{food_id}`

**路径参数**：

- `food_id`: 食物记录ID

**响应**：返回指定ID的食物营养记录详情。

#### 8.4 更新食物营养记录 `PUT /{food_id}`

**路径参数**：

- `food_id`: 食物记录ID

**请求体**：与创建食物营养记录相同，所有字段均为可选。

**响应**：返回更新后的食物营养记录。

#### 8.5 删除食物营养记录 `DELETE /{food_id}`

**路径参数**：

- `food_id`: 食物记录ID

**响应**：

```json
{
  "message": "食物营养记录已删除",
  "status": "success"
}
```

#### 8.6 批量导入食物营养数据 `POST /import`

**请求体**：

```json
{
  "items": [
    {
      "name_cn": "全麦面包",
      "calories": 265,
      "protein": 11.0,
      "fat": 3.5,
      "carbs": 48.0,
      "gi": 50,
      "category": "谷物类",
      "diabetes_index": 2.5,
      "diabetes_friendly": 1,
      "image_url": "https://example.com/foods/whole-wheat-bread.jpg"
    },
    // 更多食物记录...
  ]
}
```

**响应**：

```json
{
  "imported_count": 10,
  "failed_count": 0,
  "message": "食物营养数据导入成功",
  "status": "success"
}
```

#### 8.7 按分类获取食物列表 `GET /categories/{category}`

**路径参数**：

- `category`: 食物分类名称

**查询参数**：

- `page`: 页码，默认1
- `size`: 每页大小，默认20

**响应**：返回指定分类的食物营养记录分页列表。

#### 8.8 获取所有食物分类 `GET /categories`

**响应**：

```json
{
  "categories": [
    "谷物类",
    "蔬菜类",
    "水果类",
    "肉蛋类",
    "豆制品",
    "坚果类",
    "油脂类",
    "饮料类",
    "调味品"
  ]
}
```

#### 8.9 获取适合糖尿病患者的食物 `GET /diabetes-friendly`

**查询参数**：

- `page`: 页码，默认1
- `size`: 每页大小，默认20
- `category`: 食物分类，可选

**响应**：返回适合糖尿病患者的食物营养记录分页列表。

#### 8.10 获取低GI食物 `GET /low-gi`

**查询参数**：

- `page`: 页码，默认1
- `size`: 每页大小，默认20
- `threshold`: GI阈值，默认55

**响应**：返回GI值低于指定阈值的食物营养记录分页列表。

#### 8.11 根据血糖指数范围查询食物 `GET /gi-range`

**查询参数**：

- `min`: 最小GI值，默认0
- `max`: 最大GI值，默认100
- `page`: 页码，默认1
- `size`: 每页大小，默认20

**响应**：返回GI值在指定范围内的食物营养记录分页列表。

#### 8.12 搜索食物 `GET /search`

**查询参数**：

- `q`: 搜索关键词，必填
- `page`: 页码，默认1
- `size`: 每页大小，默认20

**响应**：返回匹配搜索关键词的食物营养记录分页列表。

#### 8.13 上传食物图片 `POST /{food_id}/image`

**路径参数**：

- `food_id`: 食物记录ID

**请求体**：

```
Content-Type: multipart/form-data
file: [图片文件]
```

**响应**：

```json
{
  "file_path": "/uploads/foods/food_123.jpg",
  "file_size": 1024,
  "message": "食物图片上传成功",
  "status": "success"
}
```

#### 8.14 删除食物图片 `DELETE /{food_id}/image`

**路径参数**：

- `food_id`: 食物记录ID

**响应**：

```json
{
  "message": "食物图片已删除",
  "status": "success"
}
```

## 错误码说明

| 状态码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 401 | 未授权，需要登录 |
| 403 | 禁止访问，权限不足 |
| 404 | 请求的资源不存在 |
| 422 | 数据验证失败 |
| 500 | 服务器内部错误 |

## 最佳实践

1. **错误处理**：始终检查API响应的状态码和错误消息，特别是422错误，它通常包含详细的验证错误信息。

2. **认证**：确保在每个需要认证的请求中包含有效的JWT令牌。

3. **数据验证**：在发送请求前，确保数据符合API要求的格式和类型。

4. **分页处理**：处理分页数据时，注意检查总页数和当前页码，以正确实现分页导航。

5. **日期格式**：所有日期时间字段使用ISO 8601格式（YYYY-MM-DDTHH:MM:SS）。