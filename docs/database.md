# 数据库说明

## 1. 引擎

| 环境 | 推荐 |
|------|------|
| 本地开发 / 测试 | SQLite（`sqlite:///./diabetes_assistant.db`） |
| 接近生产 | MySQL 8，`utf8mb4` |

SQLAlchemy URI 由环境变量 `DATABASE_URL` 注入（见 `app/core/config.py` 字段 `SQLALCHEMY_DATABASE_URI`）。

## 2. 完整表结构

历史完整说明（字段级）：

- [数据库结构文档.md](./training/legacy/数据库结构文档.md)（实训期整理，仍可参考）  
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
| `knowledge_base` | 知识文档与来源元数据 | 全局语料 |
| `knowledge_chunks` | 双语检索片段与可选 embedding | document_id |
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
python setup_dev.py --init-db --use-orm
```

默认配置的 `AUTO_CREATE_TABLES=true` 也会在 API 启动时自动创建表。只有显式设置 `ADMIN_PASSWORD` 或 `TEST_USER_PASSWORD` 时，初始化脚本才会创建对应的本地演示账号。

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

- 自动化测试使用 memory SQLite，不读取开发数据库。
- `*.db`、`*.sqlite`、`*.sqlite3` 均被 Git 忽略，仓库不提交数据库快照。
- 示例数据必须由初始化脚本生成，不得从真实账号、会话或健康记录复制。
