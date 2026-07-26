from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pydantic import BaseModel, ConfigDict, Field
import uuid
from statistics import fmean, pstdev

from app.api.deps import get_current_user, get_db
from app.db.models import User, GlucoseRecord
from app.services.glucose import get_user_glucose_records
from app.ml.ollama_service import ollama_service
from app.models.glucose import MeasurementTimeEnum, MeasurementMethodEnum
from app.models.diet import MealTypeEnum
import logging

router = APIRouter()

logger = logging.getLogger(__name__)

# Pydantic Models for Glucose CRUD
class GlucoseBase(BaseModel):
    value: float = Field(..., description="血糖值，单位mmol/L")
    measurement_time: MeasurementTimeEnum
    measurement_method: MeasurementMethodEnum
    measured_at: datetime = Field(default_factory=datetime.now)
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class GlucoseCreate(GlucoseBase):
    pass

class GlucoseUpdate(BaseModel):
    value: Optional[float] = None
    measurement_time: Optional[MeasurementTimeEnum] = None
    measurement_method: Optional[MeasurementMethodEnum] = None
    measured_at: Optional[datetime] = None
    notes: Optional[str] = None

class GlucoseResponse(GlucoseBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

# Pydantic Models for Analysis
class GlucoseAnalysisRequest(BaseModel):
    hours: int = 24

class AlertResponse(BaseModel):
    type: str
    value: float
    threshold: float
    timestamp: Optional[str] = None
    from_time: Optional[str] = None
    to_time: Optional[str] = None
    from_value: Optional[float] = None
    to_value: Optional[float] = None
    severity: str

class AnalysisResponse(BaseModel):
    status: str
    statistics: Optional[Dict[str, Any]] = None
    alerts: Optional[List[AlertResponse]] = None
    has_alerts: bool = False
    message: Optional[str] = None
    alert_message: Optional[str] = None

class GlucoseTrendAnalysisRequest(BaseModel):
    days: Optional[int] = 3

class QuickDietSuggestionResponse(BaseModel):
    suggestion: str

# CRUD operations for Glucose Records
@router.post("", response_model=GlucoseResponse)
def create_glucose_record(
    record_in: GlucoseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_record = GlucoseRecord(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        **record_in.model_dump()
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

@router.get("", response_model=List[GlucoseResponse])
def read_glucose_records(
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(GlucoseRecord).filter(GlucoseRecord.user_id == current_user.id)
    if start_date:
        query = query.filter(GlucoseRecord.measured_at >= start_date)
    if end_date:
        query = query.filter(GlucoseRecord.measured_at <= end_date)
    records = query.offset(skip).limit(limit).all()
    return records

@router.get("/quick-diet-suggestions", response_model=QuickDietSuggestionResponse)
async def get_quick_diet_suggestion(
    glucose_value: float = Query(..., description="Current glucose value in mmol/L"),
    meal_type: MealTypeEnum = Query(..., description="The type of meal (e.g., breakfast, lunch)"),
    is_before_meal: bool = Query(..., description="Is the suggestion for before or after the meal?"),
    current_user: User = Depends(get_current_user),
):
    """
    Provides a quick diet suggestion based on the current glucose level.
    """
    meal_time_desc = "餐前" if is_before_meal else "餐后"

    prompt = f"""
    为糖尿病患者 {current_user.name} 提供一份即时饮食建议。

    患者信息:
    - 糖尿病类型: {getattr(current_user, 'diabetes_type', '未知')}
    - 当前血糖值: {glucose_value:.1f} mmol/L
    - 用餐情况: {meal_type.value} ({meal_time_desc})

    请根据以上信息，生成一条简洁、具体、可操作的饮食建议。
    - 如果是餐前，请根据血糖水平推荐合适的食物类别和份量。
    - 如果是餐后，请根据血糖水平评价可能的上一餐情况，并对下一餐或零食提出调整建议。

    建议应友好、鼓励并易于理解。
    """

    try:
        response = await ollama_service.generate(
            prompt=prompt,
            model="deepseek-r1:1.5b",
            temperature=0.7,
            max_tokens=250
        )
        suggestion = response.get("response", "抱歉，暂时无法生成建议，请稍后再试。")
        return QuickDietSuggestionResponse(suggestion=suggestion)
    except Exception as e:
        logger.error(f"为用户 {current_user.id} 生成快速饮食建议失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="生成饮食建议时发生内部错误，请稍后重试。"
        )

@router.get("/{record_id}", response_model=GlucoseResponse)
def read_glucose_record(
    record_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(GlucoseRecord).filter(GlucoseRecord.id == record_id, GlucoseRecord.user_id == current_user.id).first()
    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return record

@router.put("/{record_id}", response_model=GlucoseResponse)
def update_glucose_record(
    record_id: str,
    record_in: GlucoseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_record = db.query(GlucoseRecord).filter(GlucoseRecord.id == record_id, GlucoseRecord.user_id == current_user.id).first()
    if db_record is None:
        raise HTTPException(status_code=404, detail="Record not found")

    update_data = record_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_record, key, value)

    db.commit()
    db.refresh(db_record)
    return db_record

@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_glucose_record(
    record_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_record = db.query(GlucoseRecord).filter(GlucoseRecord.id == record_id, GlucoseRecord.user_id == current_user.id).first()
    if db_record is None:
        raise HTTPException(status_code=404, detail="Record not found")

    db.delete(db_record)
    db.commit()

# Analysis Endpoints
@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_glucose(
    request: GlucoseAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    分析最近一段时间的血糖数据并检查异常
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=request.hours)

        records = get_user_glucose_records(
            db=db,
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date
        )

        if not records:
            return {
                "status": "ok",
                "message": f"近{request.hours}小时内没有血糖记录",
                "has_alerts": False
            }

        values = [record.value for record in records]
        avg_value = sum(values) / len(values)
        max_value = max(values)
        min_value = min(values)

        alerts = []
        low_threshold = 3.9
        if min_value < low_threshold:
            alerts.append({
                "type": "low_glucose", "value": min_value, "threshold": low_threshold,
                "timestamp": records[values.index(min_value)].measured_at.isoformat(),
                "severity": "high" if min_value < 2.9 else "medium"
            })

        high_threshold = 10.0
        if max_value > high_threshold:
            alerts.append({
                "type": "high_glucose", "value": max_value, "threshold": high_threshold,
                "timestamp": records[values.index(max_value)].measured_at.isoformat(),
                "severity": "high" if max_value > 12.0 else "medium"
            })

        alert_message = None
        if alerts:
            alert_message = await generate_alert_message(current_user, alerts, records)

        return {
            "status": "ok",
            "statistics": {
                "average": avg_value, "max": max_value, "min": min_value,
                "count": len(records), "period_hours": request.hours
            },
            "alerts": alerts, "has_alerts": len(alerts) > 0,
            "alert_message": alert_message
        }

    except Exception as e:
        logger.error(f"分析血糖数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析血糖数据失败: {str(e)}")

@router.post("/analyze-trend")
async def analyze_glucose_trend(
    request: GlucoseTrendAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    分析用户近三天的血糖趋势并提供智能建议
    """
    try:
        days = request.days if request.days else 3
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        records = get_user_glucose_records(db=db, user_id=current_user.id, start_date=start_date, end_date=end_date)

        if not records or len(records) < 3:
            return {"status": "error", "message": f"近{days}天内没有足够的血糖记录", "has_data": False}

        values = [record.value for record in records]
        avg_value = sum(values) / len(values)
        max_value = max(values)
        min_value = min(values)
        std_value = pstdev(values)

        target_min, target_max = 3.9, 7.8
        in_range_count = sum(1 for v in values if target_min <= v <= target_max)
        in_range_percentage = (in_range_count / len(values)) * 100

        high_count = sum(1 for v in values if v > target_max)
        low_count = sum(1 for v in values if v < target_min)
        high_percentage = (high_count / len(values)) * 100
        low_percentage = (low_count / len(values)) * 100

        patterns = analyze_glucose_patterns(records)

        statistics = {
            "average": avg_value, "max": max_value, "min": min_value, "std": std_value,
            "in_range_percentage": in_range_percentage, "high_percentage": high_percentage, "low_percentage": low_percentage
        }

        advice = await generate_glucose_advice(current_user, records, statistics, patterns)

        return {
            "status": "success", "has_data": True, "days": days, "record_count": len(records),
            "statistics": statistics, "patterns": patterns, "advice": advice
        }
    except Exception as e:
        logger.error(f"分析血糖趋势失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析血糖趋势失败: {str(e)}")

# Helper functions for analysis
def analyze_glucose_patterns(records):
    from collections import defaultdict
    sorted_records = sorted(records, key=lambda r: r.measured_at)
    records_by_date = defaultdict(list)
    for record in sorted_records:
        records_by_date[record.measured_at.date()].append(record)

    # ... more pattern analysis logic can be added here ...

    fasting_values = [r.value for r in sorted_records if r.measurement_time.name.startswith("BEFORE")]
    postprandial_values = [r.value for r in sorted_records if r.measurement_time.name.startswith("AFTER")]

    return {
        "fasting_avg": fmean(fasting_values) if fasting_values else 0,
        "postprandial_avg": fmean(postprandial_values) if postprandial_values else 0,
    }

async def generate_alert_message(user, alerts, records):
    """使用Ollama生成警报消息"""
    try:
        latest_alert = sorted(alerts, key=lambda a: a.get("timestamp", ""), reverse=True)[0]
        prompt = f"为糖尿病患者{user.name}生成一条血糖预警消息。警报类型: {latest_alert['type']}, 严重程度: {latest_alert['severity']}. 请提供简短描述、风险和建议措施。"
        response = await ollama_service.generate(prompt=prompt, model="deepseek-r1:1.5b", temperature=0.7, max_tokens=200)
        return response.get("response", "无法生成警报消息")
    except Exception as e:
        logger.error(f"生成警报消息失败: {str(e)}")
        return "检测到血糖异常，请及时核对并采取措施。"

async def generate_glucose_advice(user, records, statistics, patterns):
    """使用Ollama生成个性化血糖管理建议"""
    try:
        prompt = f"""
        为糖尿病患者 {user.name} (糖尿病类型: {getattr(user, 'diabetes_type', '未知')}) 生成一份详细的血糖分析报告和管理建议。
        数据概览: 平均血糖 {statistics['average']:.1f}, 范围 {statistics['min']:.1f}-{statistics['max']:.1f}, 达标率 {statistics['in_range_percentage']:.1f}%.
        模式: 空腹平均 {patterns.get('fasting_avg', 0):.1f}, 餐后平均 {patterns.get('postprandial_avg', 0):.1f}.
        请提供: 1. 总体评估 2. 具体问题分析 3. 改善建议(饮食、运动) 4. 监测重点.
        """
        response = await ollama_service.generate(prompt=prompt, model="deepseek-r1:1.5b", temperature=0.7, max_tokens=800)
        return response.get("response", "无法生成血糖管理建议")
    except Exception as e:
        logger.error(f"生成血糖管理建议失败: {str(e)}")
        return "生成建议时发生错误，请稍后再试"
