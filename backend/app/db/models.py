from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime

from app.db.base_class import Base
from app.models.user import GenderEnum, DiabetesTypeEnum
from app.models.glucose import MeasurementTimeEnum, MeasurementMethodEnum
from app.models.diet import MealTypeEnum
from app.models.health import ExerciseTypeEnum, ExerciseIntensityEnum
from app.models.assistant import MessageRoleEnum


def generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(100), unique=True, index=True)
    name = Column(String(100))
    hashed_password = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    gender = Column(Enum(GenderEnum), nullable=True)
    birth_date = Column(DateTime, nullable=True)
    diabetes_type = Column(Enum(DiabetesTypeEnum), nullable=True)
    diagnosis_date = Column(DateTime, nullable=True)
    height = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)
    phone = Column(String(20), nullable=True)
    avatar = Column(String(255), nullable=True)
    target_glucose_min = Column(Float, nullable=True)
    target_glucose_max = Column(Float, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关联
    glucose_records = relationship("GlucoseRecord", back_populates="user")
    diet_records = relationship("DietRecord", back_populates="user")
    health_records = relationship("HealthRecord", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")


class GlucoseRecord(Base):
    __tablename__ = "glucose_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"))
    value = Column(Float, nullable=False)  # 血糖值(mmol/L)
    measurement_time = Column(Enum(MeasurementTimeEnum), nullable=False)  # 测量类型(空腹/餐后等)
    measurement_method = Column(Enum(MeasurementMethodEnum), nullable=False)  # 测量方法
    measured_at = Column(DateTime, default=func.now())  # 测量时间
    notes = Column(Text, nullable=True)  # 备注
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关联
    user = relationship("User", back_populates="glucose_records")


class DietRecord(Base):
    __tablename__ = "diet_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"))
    meal_type = Column(Enum(MealTypeEnum), nullable=False)
    meal_time = Column(DateTime, default=func.now())
    food_items = Column(JSON, nullable=False)  # 存储食物列表的JSON
    total_carbs = Column(Float, nullable=False)
    total_calories = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
    image_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关联
    user = relationship("User", back_populates="diet_records")


class HealthRecord(Base):
    __tablename__ = "health_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"))
    record_date = Column(DateTime, default=func.now())
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关联
    user = relationship("User", back_populates="health_records")
    weight_records = relationship("WeightRecord", back_populates="health_record")
    blood_pressure_records = relationship("BloodPressureRecord", back_populates="health_record")
    exercise_records = relationship("ExerciseRecord", back_populates="health_record")
    medication_records = relationship("MedicationRecord", back_populates="health_record")


class WeightRecord(Base):
    __tablename__ = "weight_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    health_record_id = Column(String(36), ForeignKey("health_records.id"))
    user_id = Column(String(36), ForeignKey("users.id"))
    weight = Column(Float, nullable=False)
    bmi = Column(Float, nullable=True)
    body_fat = Column(Float, nullable=True)
    measured_at = Column(DateTime, default=func.now())
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关联
    health_record = relationship("HealthRecord", back_populates="weight_records")


class BloodPressureRecord(Base):
    __tablename__ = "blood_pressure_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    health_record_id = Column(String(36), ForeignKey("health_records.id"))
    user_id = Column(String(36), ForeignKey("users.id"))
    systolic = Column(Integer, nullable=False)
    diastolic = Column(Integer, nullable=False)
    pulse = Column(Integer, nullable=True)
    measured_at = Column(DateTime, default=func.now())
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关联
    health_record = relationship("HealthRecord", back_populates="blood_pressure_records")


class ExerciseRecord(Base):
    __tablename__ = "exercise_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    health_record_id = Column(String(36), ForeignKey("health_records.id"))
    user_id = Column(String(36), ForeignKey("users.id"))
    exercise_type = Column(Enum(ExerciseTypeEnum), nullable=False)
    duration = Column(Integer, nullable=False)  # 单位：分钟
    intensity = Column(Enum(ExerciseIntensityEnum), nullable=False)
    calories_burned = Column(Float, nullable=True)
    start_time = Column(DateTime, default=func.now())
    end_time = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关联
    health_record = relationship("HealthRecord", back_populates="exercise_records")


class MedicationRecord(Base):
    __tablename__ = "medication_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    health_record_id = Column(String(36), ForeignKey("health_records.id"))
    user_id = Column(String(36), ForeignKey("users.id"))
    name = Column(String(100), nullable=False)
    dosage = Column(String(50), nullable=False)
    taken_at = Column(DateTime, default=func.now())
    scheduled_at = Column(DateTime, nullable=True)
    is_taken = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关联
    health_record = relationship("HealthRecord", back_populates="medication_records")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"))
    title = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关联
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id"))
    role = Column(Enum(MessageRoleEnum), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=func.now())
    message_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关联
    conversation = relationship("Conversation", back_populates="messages")


class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(255), nullable=True)
    tags = Column(JSON, nullable=False, default=list)
    source_key = Column(String(32), nullable=True, index=True)
    source_url = Column(String(512), nullable=True)
    title_en = Column(String(255), nullable=True)
    license = Column(String(255), nullable=True)
    retrieved_at = Column(DateTime, nullable=True)
    content_hash = Column(String(64), nullable=True, index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    chunks = relationship(
        "KnowledgeChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="KnowledgeChunk.chunk_index",
    )


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_knowledge_chunk_document_index"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(
        String(36),
        ForeignKey("knowledge_base.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index = Column(Integer, nullable=False)
    text_zh = Column(Text, nullable=False)
    text_en = Column(Text, nullable=True)
    char_count = Column(Integer, nullable=False)
    embedding = Column(JSON, nullable=True)
    embedding_model = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=func.now())

    document = relationship("KnowledgeBase", back_populates="chunks")


class FoodNutrition(Base):
    __tablename__ = "food_nutrition"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name_cn = Column(Text, nullable=False)
    calories = Column(Integer, nullable=False)
    protein = Column(Float, nullable=False)
    fat = Column(Float, nullable=False)
    carbs = Column(Float, nullable=False)
    gi = Column(Integer, nullable=True)
    category = Column(Text, nullable=False)
    diabetes_index = Column(Float, nullable=True)
    diabetes_friendly = Column(Integer, nullable=True)
    image_url = Column(Text, nullable=True)
