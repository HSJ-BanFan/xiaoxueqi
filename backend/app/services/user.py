from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
import uuid
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.db.models import User
from app.db.session import get_db
from app.models.user import UserCreate, UserUpdate, User as UserSchema
from app.core.config import settings

# 密码哈希工具
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建JWT访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """通过邮箱获取用户"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    """通过ID获取用户"""
    return db.query(User).filter(User.id == user_id).first()


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """验证用户"""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_user(db: Session, user_in: UserCreate) -> User:
    """创建新用户"""
    # 检查邮箱是否已存在
    db_user = get_user_by_email(db, email=user_in.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已被注册",
        )

    # 创建用户对象
    user_data = user_in.model_dump(exclude={"password"})
    db_user = User(
        id=str(uuid.uuid4()),
        **user_data,
        hashed_password=get_password_hash(user_in.password),
    )

    # 保存到数据库
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


def create_superuser(db: Session, user_in: UserCreate) -> User:
    """创建超级用户"""
    # 检查邮箱是否已存在
    db_user = get_user_by_email(db, email=user_in.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已被注册",
        )

    # 确保is_superuser为True
    user_data = user_in.model_dump(exclude={"password"})
    user_data["is_superuser"] = True

    # 创建用户对象
    db_user = User(
        id=str(uuid.uuid4()),
        **user_data,
        hashed_password=get_password_hash(user_in.password),
    )

    # 保存到数据库
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


def update_user(db: Session, user_id: str, user_in: UserUpdate) -> User:
    """更新用户信息"""
    # 获取用户
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    # 更新用户数据
    user_data = user_in.model_dump(exclude_unset=True)

    # 如果更新密码，需要哈希处理
    if "password" in user_data and user_data["password"]:
        user_data["hashed_password"] = get_password_hash(user_data.pop("password"))

    # 更新用户属性
    for field, value in user_data.items():
        if hasattr(db_user, field) and value is not None:
            setattr(db_user, field, value)

    # 保存到数据库
    db.commit()
    db.refresh(db_user)

    return db_user


def delete_user(db: Session, user_id: str) -> bool:
    """删除用户"""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    db.delete(db_user)
    db.commit()

    return True


class UserService:
    """用户服务类"""

    def __init__(self, db: Session):
        self.db = db

    async def get_by_id(self, user_id: str) -> Optional[UserSchema]:
        """
        通过ID获取用户
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        return UserSchema(**user.__dict__)

    async def get_by_email(self, email: str) -> Optional[UserSchema]:
        """
        通过邮箱获取用户
        """
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            return None
        return UserSchema(**user.__dict__)

    async def create(self, user_in: UserCreate) -> UserSchema:
        """
        创建新用户
        """
        db_user = create_user(self.db, user_in)
        return UserSchema(**db_user.__dict__)

    async def create_superuser(self, user_in: UserCreate) -> UserSchema:
        """
        创建超级用户
        """
        db_user = create_superuser(self.db, user_in)
        return UserSchema(**db_user.__dict__)

    async def update(self, user_id: str, user_in: UserUpdate) -> UserSchema:
        """
        更新用户信息
        """
        db_user = update_user(self.db, user_id, user_in)
        return UserSchema(**db_user.__dict__)

    async def authenticate(self, email: str, password: str) -> Optional[UserSchema]:
        """
        验证用户
        """
        user = authenticate_user(self.db, email, password)
        if not user:
            return None
        return UserSchema(**{k: v for k, v in user.__dict__.items() if k != "hashed_password"})

    async def delete(self, user_id: str) -> bool:
        """
        删除用户
        """
        return delete_user(self.db, user_id)

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[UserSchema]:
        """
        获取所有用户
        """
        users = self.db.query(User).offset(skip).limit(limit).all()
        return [UserSchema(**user.__dict__) for user in users]

    async def assess_risk(self, user_id: str, data: Dict[str, Any]) -> float:
        """
        评估用户健康风险
        """
        # 这里是一个简单的风险评估示例
        # 实际应用中应该使用更复杂的模型
        risk_score = 0.0

        # 获取用户基本信息
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return risk_score

        # 基于年龄的风险
        if user.birth_date:
            age = (datetime.now() - user.birth_date).days // 365
            if age > 45:
                risk_score += 10
            if age > 60:
                risk_score += 15

        # 基于BMI的风险
        if user.height and user.weight:
            height_m = user.height / 100
            bmi = user.weight / (height_m * height_m)
            if bmi > 25:
                risk_score += 10
            if bmi > 30:
                risk_score += 20

        # 基于糖尿病类型的风险
        if user.diabetes_type:
            if user.diabetes_type == "type1":
                risk_score += 25
            elif user.diabetes_type == "type2":
                risk_score += 20

        # 基于其他因素的风险
        if data.get("has_hypertension"):
            risk_score += 15
        if data.get("has_heart_disease"):
            risk_score += 20
        if data.get("smoking"):
            risk_score += 15
        if data.get("family_history"):
            risk_score += 10

        # 确保风险分数在0-100之间
        return min(max(risk_score, 0), 100)
