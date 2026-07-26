from app.db.session import SessionLocal
from app.db.models import User
from app.core.security import get_password_hash
import uuid
import os

def create_admin_user():
    """创建管理员用户"""
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_password:
        raise RuntimeError("请先设置 ADMIN_PASSWORD 环境变量")

    db = SessionLocal()
    try:
        # 检查是否已存在
        existing_admin = db.query(User).filter(User.email == admin_email).first()
        if existing_admin:
            print("管理员账号已存在，无需重复创建")
            return

        # 创建管理员账号
        admin = User(
            id=str(uuid.uuid4()),
            email=admin_email,
            name="系统管理员",
            hashed_password=get_password_hash(admin_password),
            is_active=True,
            is_superuser=True
        )
        db.add(admin)
        db.commit()
        print("管理员账号创建成功!")
        print(f"邮箱: {admin_email}")
    except Exception as e:
        db.rollback()
        print(f"创建管理员账号失败: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()
