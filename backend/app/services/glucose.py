from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from fastapi import HTTPException, status
import logging

from app.db.models import GlucoseRecord, User
from app.models.glucose import GlucoseCreate, GlucoseUpdate, Glucose, GlucoseStatistics

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_glucose_record(db: Session, record_in: GlucoseCreate) -> GlucoseRecord:
    """创建新的血糖记录"""
    logger.info("Creating glucose record for user %s", record_in.user_id)

    # 检查用户是否存在
    user = db.query(User).filter(User.id == record_in.user_id).first()
    if not user:
        logger.error(f"用户不存在: {record_in.user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 创建记录
    db_record = GlucoseRecord(
        id=str(uuid.uuid4()),
        **record_in.model_dump()
    )

    # 保存到数据库
    try:
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        logger.info(f"血糖记录创建成功: {db_record.id}")
        return db_record
    except Exception as e:
        db.rollback()
        logger.error(f"保存血糖记录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存血糖记录失败: {str(e)}"
        )


def get_glucose_record(db: Session, record_id: str) -> Optional[GlucoseRecord]:
    """通过ID获取血糖记录"""
    return db.query(GlucoseRecord).filter(GlucoseRecord.id == record_id).first()


def get_user_glucose_records(
    db: Session,
    user_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: Optional[int] = None,
) -> List[GlucoseRecord]:
    """
    获取用户在指定时间范围内的血糖记录

    Args:
        db: 数据库会话
        user_id: 用户ID
        start_date: 开始时间，如果为None则不限制开始时间
        end_date: 结束时间，如果为None则不限制结束时间

    Returns:
        血糖记录列表
    """
    query = db.query(GlucoseRecord).filter(GlucoseRecord.user_id == user_id)

    if start_date:
        query = query.filter(GlucoseRecord.measured_at >= start_date)

    if end_date:
        query = query.filter(GlucoseRecord.measured_at <= end_date)

    # 按时间降序排序
    query = query.order_by(GlucoseRecord.measured_at.desc())

    if skip:
        query = query.offset(skip)
    if limit is not None:
        query = query.limit(limit)

    return query.all()


def update_glucose_record(db: Session, record_id: str, record_in: GlucoseUpdate) -> GlucoseRecord:
    """更新血糖记录"""
    # 获取记录
    db_record = get_glucose_record(db, record_id)
    if not db_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="血糖记录不存在"
        )

    # 更新记录
    update_data = record_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(db_record, field) and value is not None:
            setattr(db_record, field, value)

    # 保存到数据库
    db.commit()
    db.refresh(db_record)

    return db_record


def delete_glucose_record(db: Session, record_id: str) -> bool:
    """删除血糖记录"""
    db_record = get_glucose_record(db, record_id)
    if not db_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="血糖记录不存在"
        )

    db.delete(db_record)
    db.commit()

    return True


def get_glucose_statistics(
    db: Session,
    user_id: str,
    period: str = "week"
) -> GlucoseStatistics:
    """获取用户的血糖统计数据"""
    # 确定日期范围
    now = datetime.now()
    if period == "day":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    else:
        start_date = now - timedelta(days=90)  # 默认3个月

    # 获取用户
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 获取目标血糖范围
    target_min = user.target_glucose_min or 3.9  # 默认值
    target_max = user.target_glucose_max or 7.8  # 默认值

    # 查询记录
    records = db.query(GlucoseRecord).filter(
        and_(
            GlucoseRecord.user_id == user_id,
            GlucoseRecord.measured_at >= start_date
        )
    ).all()

    # 如果没有记录，返回空统计
    if not records:
        return GlucoseStatistics(
            average=0,
            max=0,
            min=0,
            count=0,
            in_range_percentage=0,
            high_percentage=0,
            low_percentage=0,
            period=period
        )

    # 计算统计数据
    values = [r.value for r in records]
    count = len(values)
    avg_value = sum(values) / count
    max_value = max(values)
    min_value = min(values)

    # 计算范围内的百分比
    in_range = sum(1 for v in values if target_min <= v <= target_max)
    high = sum(1 for v in values if v > target_max)
    low = sum(1 for v in values if v < target_min)

    in_range_percentage = (in_range / count) * 100 if count > 0 else 0
    high_percentage = (high / count) * 100 if count > 0 else 0
    low_percentage = (low / count) * 100 if count > 0 else 0

    return GlucoseStatistics(
        average=round(avg_value, 2),
        max=max_value,
        min=min_value,
        count=count,
        in_range_percentage=round(in_range_percentage, 2),
        high_percentage=round(high_percentage, 2),
        low_percentage=round(low_percentage, 2),
        period=period
    )
