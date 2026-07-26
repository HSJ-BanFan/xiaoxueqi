# 糖尿病助手项目之食物营养API服务开发指南

## 1. 概述

本文将详细介绍糖尿病助手项目中食物营养数据API服务`/api/v1/nutrition`的完整设计与实现过程。从数据库结构分析、API设计、代码实现到API测试，一步步带领新手开发者完成整个流程。

## 2. 数据库结构分析

首先，我们需要分析数据库表结构，确保我们的API服务能够正确处理和存储食物营养数据。

### 2.1 食物营养表(food_nutrition)结构

```
| 字段名 | 类型 | 约束 | 描述 |
|-------|------|------|------|
| id | int | PRIMARY KEY, AUTO_INCREMENT | 食物记录唯一标识符 |
| name_cn | text | | 食物中文名称 |
| calories | bigint | | 卡路里(kcal) |
| protein | double | | 蛋白质(g) |
| fat | double | | 脂肪(g) |
| carbs | double | | 碳水化合物(g) |
| gi | bigint | | 血糖指数 |
| category | text | | 食物分类 |
| diabetes_index | double | | 糖尿病指数 |
| diabetes_friendly | bigint | | 是否适合糖尿病患者 |
| image_url | text | | 食物图片URL或SVG数据 |
```

这个表结构包含了食物的基本信息、营养成分和与糖尿病相关的属性，非常适合作为我们的数据源。

## 3. API服务设计

根据数据库结构和项目需求，我们设计以下API接口：

1. **基础CRUD操作**：
   - 创建食物记录
   - 获取食物记录列表
   - 获取单个食物记录
   - 更新食物记录
   - 删除食物记录

2. **专业查询功能**：
   - 按分类获取食物
   - 获取所有食物分类
   - 获取适合糖尿病患者的食物
   - 获取低GI食物
   - 根据血糖指数范围查询食物
   - 搜索食物

3. **图片管理**：
   - 上传食物图片
   - 删除食物图片

4. **数据管理**：
   - 批量导入食物营养数据

## 4. 模型设计 (Pydantic Models)

我们使用Pydantic来定义数据模型，实现请求验证和响应序列化。

```python
# 在backend/app/models/nutrition.py中实现

# 定义食物分类枚举
class FoodCategoryEnum(str, Enum):
    GRAINS = "谷物类"
    VEGETABLES = "蔬菜类"
    FRUITS = "水果类"
    # ...其他分类

# 基础食物营养模型
class FoodNutritionBase(BaseModel):
    name_cn: str = Field(..., description="食物中文名称")
    calories: int = Field(..., description="卡路里(kcal)")
    protein: float = Field(..., description="蛋白质(g)")
    # ...其他字段

# 创建模型
class FoodNutritionCreate(FoodNutritionBase):
    pass

# 更新模型
class FoodNutritionUpdate(BaseModel):
    name_cn: Optional[str] = None
    calories: Optional[int] = None
    # ...所有字段设为可选

# 完整模型
class FoodNutrition(FoodNutritionBase):
    id: int
    
    class Config:
        from_attributes = True

# 分页模型
class FoodNutritionPage(BaseModel):
    items: List[FoodNutrition]
    total: int
    page: int
    size: int
    pages: int

# 其他辅助模型...
```

## 5. API实现

使用FastAPI框架实现API路由和业务逻辑：

```python
# 在backend/app/api/endpoints/nutrition.py中实现

router = APIRouter()

@router.post("", response_model=FoodNutritionModel)
def create_food(
    food_in: FoodNutritionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """创建食物营养记录"""
    # 检查管理员权限
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限才能创建食物营养记录"
        )
    
    return create_food_nutrition(db=db, food_in=food_in)

# 获取食物列表
@router.get("", response_model=FoodNutritionPage)
def read_foods(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    # ...其他参数
) -> Any:
    """获取食物营养记录列表"""
    # 实现代码...

# 获取单个食物
@router.get("/{food_id:int}", response_model=FoodNutritionModel)
def read_food(
    food_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
) -> Any:
    """获取单个食物营养记录"""
    # 实现代码...

# 其他路由实现...
```

### 5.1 路径参数约束

注意我们使用了`/{food_id:int}`形式的路径参数约束，这是FastAPI的一个重要特性，可以确保路由只匹配整数类型的参数，避免与其他路由如`/low-gi`产生冲突。

```python
@router.get("/{food_id:int}", response_model=FoodNutritionModel)
```

这样写可以确保:

- `/nutrition/123` - 会匹配到`read_food`函数
- `/nutrition/low-gi` - 会匹配到`read_low_gi_foods`函数

## 6. 服务注册

将实现的API服务注册到主应用中：

```python
# 在backend/app/api/__init__.py中注册

from fastapi import APIRouter
from app.api.endpoints import nutrition

router = APIRouter()

# 注册nutrition路由
router.include_router(nutrition.router, prefix="/nutrition", tags=["食物营养"])
```

## 7. API测试指南

下面使用Apifox进行API测试，确保我们的实现符合预期。

### 7.1 准备工作

1. **获取JWT令牌**

   首先，我们需要登录获取JWT令牌：

   ```
   POST http://localhost:8000/api/v1/users/login
   Content-Type: application/json
   
   {
     "username": "admin",
     "password": "password"
   }
   ```

   响应中的`access_token`将用于后续请求的认证。

2. **设置环境变量**

   在Apifox中，创建一个环境并设置以下变量：
   - `base_url`: `http://localhost:8000/api/v1`
   - `token`: 从登录响应中获取的`access_token`

### 7.2 测试API接口

#### 测试1: 获取食物列表

```
GET {{base_url}}/nutrition?page=1&size=20&sort_by=calories&sort_order=desc
Authorization: Bearer {{token}}
```

预期结果：

```json
{
  "items": [
    {
      "id": 1,
      "name_cn": "全麦面包",
      "calories": 265,
      "protein": 11.0,
      // ...其他字段
    },
    // ...更多食物记录
  ],
  "total": 42,
  "page": 1,
  "size": 20,
  "pages": 3
}
```

#### 测试2: 创建新食物记录

```
POST {{base_url}}/nutrition
Authorization: Bearer {{token}}
Content-Type: application/json

{
  "name_cn": "杏仁",
  "calories": 576,
  "protein": 21.2,
  "fat": 49.4,
  "carbs": 21.7,
  "gi": 15,
  "category": "坚果类",
  "diabetes_friendly": 1
}
```

预期结果：

```json
{
  "id": 43,
  "name_cn": "杏仁",
  "calories": 576,
  "protein": 21.2,
  "fat": 49.4,
  "carbs": 21.7,
  "gi": 15,
  "category": "坚果类",
  "diabetes_friendly": 1,
  "diabetes_index": null,
  "image_url": null
}
```

> **注意**：此操作需要管理员权限，非管理员用户将收到403错误。

#### 测试3: 获取低GI食物

```
GET {{base_url}}/nutrition/low-gi?threshold=55&page=1&size=20
Authorization: Bearer {{token}}
```

预期结果：

```json
{
  "items": [
    // 血糖指数<=55的食物列表
  ],
  "total": 18,
  "page": 1,
  "size": 20,
  "pages": 1
}
```

#### 测试4: 获取所有食物分类

```
GET {{base_url}}/nutrition/categories
Authorization: Bearer {{token}}
```

预期结果：

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

## 8. 常见问题与解决方案

### 8.1 路由冲突问题

**问题**: 当定义了`/{food_id}`和`/low-gi`等特定路径时，可能会出现路由冲突。

**解决方案**: 使用路径参数约束`/{food_id:int}`，明确指定参数类型。

### 8.2 认证问题

**问题**: 401 Unauthorized错误。

**解决方案**: 确保请求中包含有效的JWT令牌，格式为`Authorization: Bearer your_token_here`。

### 8.3 权限问题

**问题**: 403 Forbidden错误。

**解决方案**: 创建、更新和删除操作需要管理员权限，请确保使用有管理员权限的账户登录。

## 9. 结论

通过本教程，我们完成了从数据库结构分析到API实现和测试的完整流程。食物营养API服务为糖尿病助手项目提供了强大的数据支持，帮助用户更好地管理饮食和血糖。

这个服务的特点是：

- 完整的CRUD操作
- 专业的查询功能，如低GI食物查询
- 强大的分页、排序和过滤能力
- 严格的权限控制
- 支持图片管理和批量导入

希望本教程能帮助你理解如何使用FastAPI构建专业的API服务，并在实际项目中灵活应用这些知识。

---

参考资源:

- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [Apifox文档](https://docs.apifox.com/)
- [SQLAlchemy文档](https://docs.sqlalchemy.org/)
