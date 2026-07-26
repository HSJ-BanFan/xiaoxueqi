from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from enum import Enum


class MeasurementTimeEnum(str, Enum):
    BEFORE_BREAKFAST = "BEFORE_BREAKFAST"
    AFTER_BREAKFAST = "AFTER_BREAKFAST"
    BEFORE_LUNCH = "BEFORE_LUNCH"
    AFTER_LUNCH = "AFTER_LUNCH"
    BEFORE_DINNER = "BEFORE_DINNER"
    AFTER_DINNER = "AFTER_DINNER"
    BEFORE_SLEEP = "BEFORE_SLEEP"
    MIDNIGHT = "MIDNIGHT"
    OTHER = "OTHER"


class MeasurementMethodEnum(str, Enum):
    FINGER_STICK = "FINGER_STICK"
    CONTINUOUS_MONITOR = "CONTINUOUS_MONITOR"
    LAB_TEST = "LAB_TEST"
    OTHER = "OTHER"


class GlucoseBase(BaseModel):
    user_id: str
    value: float = Field(..., description="血糖值，单位mmol/L")
    measurement_time: MeasurementTimeEnum
    measurement_method: MeasurementMethodEnum = MeasurementMethodEnum.FINGER_STICK
    measured_at: datetime = Field(default_factory=datetime.now)
    notes: Optional[str] = None


class GlucoseCreate(GlucoseBase):
    pass


class GlucoseUpdate(BaseModel):
    value: Optional[float] = None
    measurement_time: Optional[MeasurementTimeEnum] = None
    measurement_method: Optional[MeasurementMethodEnum] = None
    measured_at: Optional[datetime] = None
    notes: Optional[str] = None


class Glucose(GlucoseBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GlucoseStatistics(BaseModel):
    average: float
    max: float
    min: float
    count: int
    in_range_percentage: float
    high_percentage: float
    low_percentage: float
    period: str  # 统计周期，如"day", "week", "month"
