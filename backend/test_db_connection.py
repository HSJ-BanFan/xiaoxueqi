import sys
import os
import logging
from sqlalchemy.exc import SQLAlchemyError

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.db.models import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_db_connection():
    """测试数据库连接"""
    try:
        db = SessionLocal()
        logger.info("✅ 数据库连接成功")
        return db
    except SQLAlchemyError as e:
        logger.error(f"❌ 数据库连接失败: {e}")
        return None

def check_admin_user(db):
    """检查管理员用户是否存在"""
    try:
        admin_email = os.getenv("ADMIN_EMAIL")
        if not admin_email:
            logger.info("未设置 ADMIN_EMAIL，跳过管理员账户检查")
            return None

        admin = db.query(User).filter(
            User.email == admin_email,
            User.is_superuser == True
        ).first()
        
        if admin:
            logger.info("✅ 已配置的管理员用户存在")
            return True
        else:
            logger.warning("⚠️ 管理员用户不存在")
            return False
    except SQLAlchemyError as e:
        logger.error(f"❌ 查询管理员用户失败: {e}")
        return False

def count_users(db):
    """统计用户数量，不输出账号或个人资料"""
    try:
        count = db.query(User).count()
        logger.info(f"✅ 系统中共有 {count} 个用户")
        return count
    except SQLAlchemyError as e:
        logger.error(f"❌ 查询用户列表失败: {e}")
        return 0

if __name__ == "__main__":
    logger.info("🔍 开始测试数据库连接...")
    db = test_db_connection()
    
    if db:
        try:
            check_admin_user(db)
            count_users(db)
        finally:
            db.close()
    
    logger.info("✅ 测试完成")
