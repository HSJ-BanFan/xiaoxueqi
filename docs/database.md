# 数据库说明

## 1. 引擎

| 环境 | 推荐 |
|------|------|
| 本地开发 / 测试 | SQLite（`sqlite:///./diabetes_assistant.db`） |
| 接近生产 | MySQL 8，`utf8mb4` |

SQLAlchemy URI 由环境变量 `DATABASE_URL` 注入（见 `app/core/config.py` 字段 `SQLALCHEMY_DATABASE_URI`）。

## 2. 完整表结构

历史完整说明（字段级）：

- 仓库根目录：[数据库结构文档.md](../数据库结构文档.md)  
- SQL 脚本：`backend/diabetes_assistant.sql`、`backend/create_db.sql`  

ORM 定义真相源：`backend/app/db/models.py`。  
**若文档与 ORM 冲突，以 ORM + 迁移/SQL 脚本为准，并回写文档。**

## 3. 核心表一览

| 表 | 用途 | 属主键 |
|----|------|--------|
| `users` | 账户与健康档案字段 | 自身 id |
| `glucose_records` | 血糖 | user_id |
| `diet_records` | 饮食 | user_id |
| `health_records` | 健康主记录 | user_id |
| `weight_records` | 体重 | user_id / health_record_id |
| `blood_pressure_records` | 血压 | 同上 |
| `exercise_records` | 运动 | 同上 |
| `medication_records` | 用药 | 同上 |
| `conversations` | 助理会话 | user_id |
| `messages` | 会话消息 | conversation_id |
| `knowledge_base` | 知识条目 | 全局或按设计 |
| `reminders` | 提醒（若启用） | user_id |

## 4. 枚举约定（血糖）

与 `app/models/glucose.py` 保持一致：

**measurement_time**

- BEFORE_BREAKFAST, AFTER_BREAKFAST  
- BEFORE_LUNCH, AFTER_LUNCH  
- BEFORE_DINNER, AFTER_DINNER  
- BEFORE_SLEEP, MIDNIGHT, OTHER  

**measurement_method**

- FINGER_STICK, CONTINUOUS_MONITOR, LAB_TEST, OTHER  

## 5. 索引建议（实现/优化时）

| 表 | 建议索引 |
|----|----------|
| glucose_records | `(user_id, measured_at DESC)` |
| diet_records | `(user_id, meal_time DESC)` |
| messages | `(conversation_id, timestamp)` |
| users | `email` UNIQUE 已有 |

## 6. 初始化

```bash
cd backend
# 视脚本支持情况：
python setup_dev.py --init-db
python setup_dev.py --sample-data
# 或
python init_db.py
```

MySQL：

```sql
CREATE DATABASE diabetes_assistant
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

再导入 `diabetes_assistant.sql` 或依赖 ORM `create_all`。

## 7. Agent 相关存储

不强制新表。推荐复用：

- `conversations` / `messages`  
- 在 message 的 metadata/JSON 字段存 tool 审计  

若 metadata 字段名在模型中为 `message_metadata` 等，以 `models.py` 为准。

## 8. 测试库

- 使用独立文件 `test_*.db` 或 memory SQLite  
- 禁止 pytest 指向开发用 `diabetes_assistant.db` 除非只读  
