from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from enum import Enum


class FoodCategoryEnum(str, Enum):
    GRAINS = "谷物类"
    VEGETABLES = "蔬菜类"
    FRUITS = "水果类"
    PROTEIN = "肉蛋类"
    BEANS = "豆制品"
    NUTS = "坚果类"
    OILS = "油脂类"
    BEVERAGES = "饮料类"
    CONDIMENTS = "调味品"
    OTHERS = "其他"


class FoodNutritionBase(BaseModel):
    name_cn: str = Field(..., description="食物中文名称")
    calories: int = Field(..., description="卡路里(kcal)")
    protein: float = Field(..., description="蛋白质(g)")
    fat: float = Field(..., description="脂肪(g)")
    carbs: float = Field(..., description="碳水化合物(g)")
    gi: Optional[int] = Field(None, description="血糖指数")
    category: str = Field(..., description="食物分类")
    diabetes_index: Optional[float] = Field(None, description="糖尿病指数")
    diabetes_friendly: Optional[int] = Field(None, description="是否适合糖尿病患者(1是，0否)")
    image_url: Optional[str] = Field(None, description="食物图片URL或SVG数据")


class FoodNutritionCreate(FoodNutritionBase):
    pass


class FoodNutritionUpdate(BaseModel):
    name_cn: Optional[str] = None
    calories: Optional[int] = None
    protein: Optional[float] = None
    fat: Optional[float] = None
    carbs: Optional[float] = None
    gi: Optional[int] = None
    category: Optional[str] = None
    diabetes_index: Optional[float] = None
    diabetes_friendly: Optional[int] = None
    image_url: Optional[str] = None


class FoodNutrition(FoodNutritionBase):
    id: int
    # 移除时间戳字段
    # created_at: datetime
    # updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FoodNutritionPage(BaseModel):
    items: List[FoodNutrition]
    total: int
    page: int
    size: int
    pages: int


class FoodNutritionImport(BaseModel):
    items: List[FoodNutritionCreate]


class FoodNutritionImportResponse(BaseModel):
    imported_count: int
    failed_count: int
    message: str
    status: str


class FoodNutritionCategories(BaseModel):
    categories: List[str]


class ImageUploadResponse(BaseModel):
    file_path: str
    file_size: int
    message: str
    status: str
