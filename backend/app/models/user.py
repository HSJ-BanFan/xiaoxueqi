from typing import Optional, List
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from datetime import datetime
from enum import Enum


class GenderEnum(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class DiabetesTypeEnum(str, Enum):
    TYPE1 = "type1"
    TYPE2 = "type2"
    GESTATIONAL = "gestational"
    PREDIABETES = "prediabetes"
    OTHER = "other"


class UserBase(BaseModel):
    email: EmailStr
    name: str
    is_active: bool = True
    is_superuser: bool = False


class UserCreate(UserBase):
    password: str
    gender: Optional[GenderEnum] = None
    birth_date: Optional[datetime] = None
    diabetes_type: Optional[DiabetesTypeEnum] = None
    diagnosis_date: Optional[datetime] = None
    height: Optional[float] = None  # 身高，单位cm
    weight: Optional[float] = None  # 体重，单位kg
    phone: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    password: Optional[str] = None
    gender: Optional[GenderEnum] = None
    birth_date: Optional[datetime] = None
    diabetes_type: Optional[DiabetesTypeEnum] = None
    diagnosis_date: Optional[datetime] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    target_glucose_min: Optional[float] = None  # 目标血糖下限，单位mmol/L
    target_glucose_max: Optional[float] = None  # 目标血糖上限，单位mmol/L
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None


class User(UserBase):
    id: str
    gender: Optional[GenderEnum] = None
    birth_date: Optional[datetime] = None
    diabetes_type: Optional[DiabetesTypeEnum] = None
    diagnosis_date: Optional[datetime] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    target_glucose_min: Optional[float] = Field(None, description="目标血糖下限，单位mmol/L")
    target_glucose_max: Optional[float] = Field(None, description="目标血糖上限，单位mmol/L")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserInDB(User):
    hashed_password: str
