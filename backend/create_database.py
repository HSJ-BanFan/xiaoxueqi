import pymysql
import logging
import os

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 数据库连接参数
DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_PORT = int(os.getenv("MYSQL_PORT", "3306"))
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD")
DB_NAME = os.getenv("MYSQL_DATABASE", "diabetes_assistant")

def create_database():
    """创建数据库"""
    if not DB_PASSWORD:
        logger.error("请先通过 MYSQL_PASSWORD 环境变量提供 MySQL 密码")
        return False
    try:
        # 连接MySQL服务器（不指定数据库）
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD
        )

        logger.info("✅ 成功连接到MySQL服务器")

        # 创建游标
        cursor = connection.cursor()

        # 创建数据库
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        logger.info(f"✅ 数据库 '{DB_NAME}' 创建成功")

        # 关闭连接
        cursor.close()
        connection.close()

        return True
    except Exception as e:
        logger.error(f"❌ 创建数据库失败: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 开始创建数据库...")
    success = create_database()

    if success:
        logger.info("✅ 数据库创建完成，现在可以运行 'python init_db.py' 初始化表和管理员账号")
    else:
        logger.error("❌ 数据库创建失败，请检查MySQL连接参数并重试")
