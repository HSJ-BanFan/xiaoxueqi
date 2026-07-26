from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from enum import Enum


class ExerciseTypeEnum(str, Enum):
    WALKING = "walking"
    RUNNING = "running"
    CYCLING = "cycling"
    SWIMMING = "swimming"
    YOGA = "yoga"
    WEIGHT_TRAINING = "weight_training"
    AEROBICS = "aerobics"
    OTHER = "other"


class ExerciseIntensityEnum(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class ExerciseRecord(BaseModel):
    user_id: str
    exercise_type: ExerciseTypeEnum
    duration: int = Field(..., description="运动时长，单位分钟")
    intensity: ExerciseIntensityEnum
    calories_burned: Optional[float] = Field(None, description="消耗的热量，单位kcal")
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    notes: Optional[str] = None


class BloodPressureRecord(BaseModel):
    user_id: str
    systolic: int = Field(..., description="收缩压，单位mmHg")
    diastolic: int = Field(..., description="舒张压，单位mmHg")
    pulse: Optional[int] = Field(None, description="脉搏，单位次/分钟")
    measured_at: datetime = Field(default_factory=datetime.now)
    notes: Optional[str] = None


class WeightRecord(BaseModel):
    user_id: str
    weight: float = Field(..., description="体重，单位kg")
    bmi: Optional[float] = None
    body_fat: Optional[float] = Field(None, description="体脂率，百分比")
    measured_at: datetime = Field(default_factory=datetime.now)
    notes: Optional[str] = None


class MedicationRecord(BaseModel):
    user_id: str
    name: str
    dosage: str
    taken_at: datetime = Field(default_factory=datetime.now)
    scheduled_at: Optional[datetime] = None
    is_taken: bool = True
    notes: Optional[str] = None


class HealthBase(BaseModel):
    user_id: str
    record_date: datetime = Field(default_factory=datetime.now)
    weight_records: Optional[List[WeightRecord]] = None
    blood_pressure_records: Optional[List[BloodPressureRecord]] = None
    exercise_records: Optional[List[ExerciseRecord]] = None
    medication_records: Optional[List[MedicationRecord]] = None
    notes: Optional[str] = None


class HealthCreate(HealthBase):
    pass


class HealthUpdate(BaseModel):
    weight_records: Optional[List[WeightRecord]] = None
    blood_pressure_records: Optional[List[BloodPressureRecord]] = None
    exercise_records: Optional[List[ExerciseRecord]] = None
    medication_records: Optional[List[MedicationRecord]] = None
    notes: Optional[str] = None


class Health(HealthBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
