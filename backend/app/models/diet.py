from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
from enum import Enum
import json


class MealTypeEnum(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"
    OTHER = "other"


class FoodCategoryEnum(str, Enum):
    GRAIN = "grain"  # 谷物类
    PROTEIN = "protein"  # 蛋白质类
    VEGETABLE = "vegetable"  # 蔬菜类
    FRUIT = "fruit"  # 水果类
    DAIRY = "dairy"  # 奶制品
    FAT = "fat"  # 油脂类
    SWEET = "sweet"  # 甜食
    BEVERAGE = "beverage"  # 饮料
    OTHER = "other"  # 其他


class FoodItem(BaseModel):
    name: str
    category: FoodCategoryEnum
    carbs: float = Field(..., description="碳水化合物含量，单位g")
    protein: float = Field(..., description="蛋白质含量，单位g")
    fat: float = Field(..., description="脂肪含量，单位g")
    calories: float = Field(..., description="热量，单位kcal")
    gi: Optional[float] = Field(None, description="血糖指数")
    amount: float = Field(..., description="食用量，单位g")
    image_url: Optional[str] = None


class DietRecordBase(BaseModel):
    user_id: str
    meal_type: MealTypeEnum
    meal_time: datetime = Field(default_factory=datetime.now)
    food_items: List[FoodItem]
    total_carbs: float = Field(..., description="总碳水化合物，单位g")
    total_calories: float = Field(..., description="总热量，单位kcal")
    notes: Optional[str] = None
    image_url: Optional[str] = None


class DietRecordCreate(DietRecordBase):
    pass


class DietRecordUpdate(BaseModel):
    meal_type: Optional[MealTypeEnum] = None
    meal_time: Optional[datetime] = None
    food_items: Optional[List[FoodItem]] = None
    total_carbs: Optional[float] = None
    total_calories: Optional[float] = None
    notes: Optional[str] = None
    image_url: Optional[str] = None


class DietRecord(DietRecordBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("food_items", mode="before")
    @classmethod
    def parse_food_items(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("food_items is not a valid JSON string")
        return v


class DietRecordPage(BaseModel):
    total: int
    data: List[DietRecord]


class DietStatistics(BaseModel):
    average_daily_calories: float
    average_daily_carbs: float
    most_frequent_foods: List[str]
    period: str  # 统计周期，如"day", "week", "month"
