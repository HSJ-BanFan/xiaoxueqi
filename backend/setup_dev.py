#!/usr/bin/env python
"""
开发环境设置脚本
用于快速设置开发环境，包括:
1. 初始化数据库
2. 创建超级管理员
3. 添加示例数据（可选）
4. 导入食物营养数据（可选）

使用方法:
- 初始化数据库（使用SQL文件创建所有表）: python setup_dev.py --init-db
- 初始化数据库（使用ORM模型创建表）: python setup_dev.py --init-db --use-orm
- 重置数据库（删除所有表并重新创建）: python setup_dev.py --reset
- 创建示例数据: python setup_dev.py --sample-data
- 导入食物营养数据: python setup_dev.py --import-food

注意:
- 默认使用diabetes_assistant.sql文件创建表结构，确保该文件位于backend目录下
- food_nutrition表会自动创建包含id字段的结构，无需额外操作
- 使用--use-orm参数可以使用SQLAlchemy ORM模型创建表，但可能与SQL文件定义的表结构有差异
- 初始化后会按 ADMIN_PASSWORD / TEST_USER_PASSWORD 环境变量创建账号。
"""

import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
import random
import sqlalchemy
import csv
import uuid

# 确保能够导入app包
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.init_db import init_db, reset_db
from app.db.session import SessionLocal, engine
from app.models.user import UserCreate
from app.services.user import create_superuser, get_user_by_email

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def create_tables_from_sql():
    """从SQL文件创建所有表"""
    try:
        # 获取SQL文件路径
        sql_file_path = os.path.join(os.path.dirname(__file__), "diabetes_assistant.sql")

        if not os.path.exists(sql_file_path):
            logger.warning(f"SQL文件不存在: {sql_file_path}")
            return False

        # 读取SQL文件内容
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        # 分割SQL语句
        sql_statements = []
        current_statement = []

        for line in sql_content.split('\n'):
            # 跳过注释和空行
            if line.strip().startswith('--') or line.strip() == '' or line.strip().startswith('/*') or line.strip().startswith('*/'):
                continue

            # 添加到当前语句
            current_statement.append(line)

            # 如果行以分号结束，则完成一个语句
            if line.strip().endswith(';'):
                sql_statements.append('\n'.join(current_statement))
                current_statement = []

        # 执行SQL语句
        with engine.begin() as conn:
            # 设置外键检查为0
            conn.execute(sqlalchemy.text("SET FOREIGN_KEY_CHECKS = 0;"))

            for statement in sql_statements:
                if statement.strip():
                    # 只执行创建表的语句
                    if "CREATE TABLE" in statement:
                        # 特殊处理food_nutrition表，确保包含id字段
                        if "food_nutrition" in statement and "id" not in statement:
                            logger.info("检测到food_nutrition表，添加id字段作为主键")
                            # 创建带有id字段的food_nutrition表
                            create_food_nutrition_table(conn)
                        else:
                            try:
                                conn.execute(sqlalchemy.text(statement))
                                logger.info(f"已执行: {statement[:50]}...")
                            except Exception as e:
                                logger.error(f"执行SQL语句失败: {str(e)}")

            # 恢复外键检查
            conn.execute(sqlalchemy.text("SET FOREIGN_KEY_CHECKS = 1;"))

        logger.info("从SQL文件创建表完成")
        return True

    except Exception as e:
        logger.error(f"从SQL文件创建表失败: {str(e)}")
        return False


def create_food_nutrition_table(conn):
    """创建带有id字段的food_nutrition表"""
    try:
        # 检查表是否已存在
        result = conn.execute(sqlalchemy.text("SHOW TABLES LIKE 'food_nutrition'"))
        if result.rowcount > 0:
            logger.info("food_nutrition表已存在，将重新创建")
            conn.execute(sqlalchemy.text("DROP TABLE IF EXISTS food_nutrition"))

        # 创建新表
        create_table_sql = """
        CREATE TABLE food_nutrition (
          id INT AUTO_INCREMENT PRIMARY KEY,
          name_cn TEXT,
          calories BIGINT,
          protein DOUBLE,
          fat DOUBLE,
          carbs DOUBLE,
          gi BIGINT,
          category TEXT,
          diabetes_index DOUBLE,
          diabetes_friendly BIGINT,
          image_url TEXT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        conn.execute(sqlalchemy.text(create_table_sql))
        logger.info("创建food_nutrition表成功，包含id字段作为主键")
        return True
    except Exception as e:
        logger.error(f"创建food_nutrition表失败: {str(e)}")
        return False


def create_admin_user(db):
    """创建超级管理员账户"""
    try:
        from app.db.models import User

        admin_password = os.getenv("ADMIN_PASSWORD")
        if not admin_password:
            logger.warning("未设置 ADMIN_PASSWORD，跳过创建超级管理员")
            return None

        # 检查用户是否已存在
        existing_user = get_user_by_email(db, email="admin@example.com")
        if existing_user:
            logger.info(f"超级管理员账户已存在: {existing_user.email}")
            return existing_user

        admin = UserCreate(
            email="admin@example.com",
            name="系统管理员",
            password=admin_password,
            is_active=True,
            is_superuser=True
        )

        user = create_superuser(db, admin)
        logger.info(f"超级管理员账户创建成功: {user.email}")
        return user
    except Exception as e:
        logger.error(f"创建超级管理员失败: {str(e)}")
        return None


def create_test_user(db):
    """创建测试用户账户"""
    try:
        from app.services.user import create_user

        test_password = os.getenv("TEST_USER_PASSWORD")
        if not test_password:
            logger.warning("未设置 TEST_USER_PASSWORD，跳过创建测试用户")
            return None

        # 检查用户是否已存在
        existing_user = get_user_by_email(db, email="test@example.com")
        if existing_user:
            logger.info(f"测试用户账户已存在: {existing_user.email}")
            return existing_user

        test_user = UserCreate(
            email="test@example.com",
            name="测试用户",
            password=test_password,
            is_active=True
        )

        user = create_user(db, test_user)
        logger.info(f"测试用户创建成功: {user.email}")
        return user
    except Exception as e:
        logger.error(f"创建测试用户失败: {str(e)}")
        return None


def create_sample_glucose_data(db, user_id, num_records=30):
    """为用户创建示例血糖数据"""
    try:
        from app.db.models import GlucoseRecord
        from app.models.glucose import MeasurementTimeEnum, MeasurementMethodEnum

        # 获取枚举值的实际字符串表示
        measurement_time_values = [
            MeasurementTimeEnum.FASTING,
            MeasurementTimeEnum.BEFORE_MEAL,
            MeasurementTimeEnum.AFTER_MEAL,
            MeasurementTimeEnum.BEFORE_SLEEP
        ]

        measurement_method_values = [
            MeasurementMethodEnum.FINGER_STICK,
            MeasurementMethodEnum.CONTINUOUS_MONITOR,
            MeasurementMethodEnum.LAB_TEST
        ]

        # 生成过去30天的记录
        today = datetime.now()

        # 随机血糖值区间
        ranges = {
            MeasurementTimeEnum.FASTING: (4.0, 7.0),  # 空腹
            MeasurementTimeEnum.BEFORE_MEAL: (4.0, 7.0),  # 餐前
            MeasurementTimeEnum.AFTER_MEAL: (5.0, 10.0),  # 餐后
            MeasurementTimeEnum.BEFORE_SLEEP: (5.0, 8.5)   # 睡前
        }

        records = []
        for i in range(num_records):
            # 随机日期（过去1个月内）
            days_ago = random.randint(0, 29)
            record_date = today - timedelta(days=days_ago)

            # 随机测量类型
            measurement_time = random.choice(measurement_time_values)

            # 根据测量类型生成合理范围内的血糖值
            min_val, max_val = ranges.get(measurement_time, (4.0, 10.0))

            # 生成正态分布的随机血糖值
            mu = (min_val + max_val) / 2
            sigma = (max_val - min_val) / 6  # 99.7%的值将在6sigma范围内
            value = random.normalvariate(mu, sigma)
            value = round(max(min_val * 0.8, min(max_val * 1.2, value)), 1)  # 限制在合理范围内并保留1位小数

            # 创建记录
            record = GlucoseRecord(
                user_id=user_id,
                value=value,
                measurement_time=measurement_time,
                measurement_method=random.choice(measurement_method_values),
                measured_at=record_date,
                notes=f"示例数据 #{i+1}"
            )
            records.append(record)

        # 批量添加记录
        db.add_all(records)
        db.commit()

        logger.info(f"已为用户 {user_id} 创建 {len(records)} 条示例血糖记录")
        return records

    except Exception as e:
        logger.error(f"创建示例血糖数据失败: {str(e)}")
        db.rollback()
        return []


def import_food_nutrition_data(db):
    """导入食物营养数据到数据库"""
    try:
        # 获取CSV文件路径
        csv_file_path = os.path.join(os.path.dirname(__file__), "..", "data", "static_food_data.csv")

        if not os.path.exists(csv_file_path):
            logger.warning(f"食物数据CSV文件不存在: {csv_file_path}")
            return False

        # 检查food_nutrition表是否存在
        try:
            with engine.connect() as conn:
                result = conn.execute(sqlalchemy.text("SHOW TABLES LIKE 'food_nutrition'"))
                if result.rowcount == 0:
                    logger.warning("food_nutrition表不存在，请先初始化数据库")
                    return False
        except Exception as e:
            logger.error(f"检查表是否存在失败: {str(e)}")
            return False

        # 读取CSV文件
        food_data = []
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                food_data.append(row)

        # 清空现有数据
        with engine.begin() as conn:
            conn.execute(sqlalchemy.text("TRUNCATE TABLE food_nutrition"))

        # 准备插入语句
        insert_sql = """
        INSERT INTO food_nutrition
        (name_cn, calories, protein, fat, carbs, gi, category, diabetes_index, diabetes_friendly, image_url)
        VALUES (:name_cn, :calories, :protein, :fat, :carbs, :gi, :category, :diabetes_index, :diabetes_friendly, :image_url)
        """

        # 批量插入数据
        with engine.begin() as conn:
            for food in food_data:
                # 生成食物外形的SVG图标
                svg_icon = get_food_svg(food['name_cn'], food['category'])
                image_url = f"data:image/svg+xml;utf8,{svg_icon}"

                # 插入数据
                conn.execute(
                    sqlalchemy.text(insert_sql),
                    {
                        "name_cn": food['name_cn'],
                        "calories": int(float(food['calories'])),
                        "protein": float(food['protein']),
                        "fat": float(food['fat']),
                        "carbs": float(food['carbs']),
                        "gi": int(float(food['gi'])),
                        "category": food['category'],
                        "diabetes_index": float(food['diabetes_index']),
                        "diabetes_friendly": int(food['diabetes_friendly']),
                        "image_url": image_url
                    }
                )

        logger.info(f"成功导入 {len(food_data)} 条食物营养数据")
        return True

    except Exception as e:
        logger.error(f"导入食物营养数据失败: {str(e)}")
        return False


def get_category_color(category):
    """根据食物类别返回对应的颜色"""
    category_colors = {
        "谷物类": "#F5DEB3",  # 浅黄褐色
        "蔬菜类": "#90EE90",  # 淡绿色
        "水果类": "#FFA07A",  # 浅橙色
        "肉蛋类": "#FA8072",  # 浅红色
        "奶制品": "#FFFAF0",  # 奶白色
        "豆制品": "#FAEBD7",  # 米色
        "坚果类": "#D2B48C",  # 棕褐色
        "零食饮料": "#FFB6C1",  # 浅粉色
        "调味品": "#E6E6FA",  # 淡紫色
        "油脂类": "#FFFF00",  # 黄色
        "其他食物": "#D3D3D3",  # 浅灰色
    }
    return category_colors.get(category, "#CCCCCC")  # 默认为浅灰色


def get_food_svg(food_name, category):
    """根据食物名称和类别生成具有代表性的食物外形SVG图标"""
    main_color = get_category_color(category)

    # 根据食物类别选择不同的图标模板
    if category == "谷物类":
        if "米饭" in food_name or "饭" in food_name:
            # 米饭/饭类图标 - 碗装米饭
            return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
                <ellipse cx="50" cy="40" rx="35" ry="10" fill="#F5F5DC" />
                <path d="M15,40 Q50,60 85,40 L85,55 Q50,75 15,55 Z" fill="{main_color}" />
                <text x="50" y="52" font-family="Arial" font-size="12" text-anchor="middle" fill="#333">{food_name[:2]}</text>
            </svg>"""
        elif "面" in food_name or "馒头" in food_name:
            # 面食/馒头图标
            return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
                <path d="M25,30 Q50,15 75,30 Q90,45 75,60 Q50,75 25,60 Q10,45 25,30 Z" fill="{main_color}" />
                <path d="M35,40 Q50,35 65,40 Q70,45 65,50 Q50,55 35,50 Q30,45 35,40 Z" fill="#F5F5DC" />
                <text x="50" y="45" font-family="Arial" font-size="12" text-anchor="middle" fill="#333">{food_name[:2]}</text>
            </svg>"""
        else:
            # 其他谷物类通用图标
            return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
                <ellipse cx="50" cy="50" rx="35" ry="25" fill="{main_color}" />
                <ellipse cx="50" cy="40" rx="25" ry="15" fill="#F5F5DC" />
                <text x="50" y="55" font-family="Arial" font-size="12" text-anchor="middle" fill="#333">{food_name[:2]}</text>
            </svg>"""

    elif category == "蔬菜类":
        if "西红柿" in food_name or "番茄" in food_name:
            # 西红柿/番茄图标
            return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
                <circle cx="50" cy="55" r="30" fill="#FF6347" />
                <path d="M50,25 L55,35 L45,35 Z" fill="#228B22" />
                <path d="M50,25 Q60,15 65,25" stroke="#228B22" stroke-width="2" fill="none" />
                <text x="50" y="60" font-family="Arial" font-size="12" text-anchor="middle" fill="#FFF">{food_name[:2]}</text>
            </svg>"""
        elif "黄瓜" in food_name:
            # 黄瓜图标
            return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
                <path d="M30,30 Q50,10 70,30 Q90,50 70,70 Q50,90 30,70 Q10,50 30,30 Z" fill="#90EE90" />
                <path d="M35,35 Q50,20 65,35 Q80,50 65,65 Q50,80 35,65 Q20,50 35,35 Z" fill="#ADFF2F" stroke="#006400" stroke-width="0.5" stroke-dasharray="2,2" />
                <text x="50" y="55" font-family="Arial" font-size="12" text-anchor="middle" fill="#006400">{food_name[:2]}</text>
            </svg>"""
        elif "胡萝卜" in food_name or "萝卜" in food_name:
            # 胡萝卜/萝卜图标
            return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
                <path d="M50,30 L60,40 Q70,60 60,80 Q50,90 40,80 Q30,60 40,40 Z" fill="#FFA500" />
                <path d="M50,30 L45,20 L50,15 L55,20 L50,30" fill="#228B22" />
                <path d="M45,20 L40,15" stroke="#228B22" stroke-width="2" />
                <path d="M55,20 L60,15" stroke="#228B22" stroke-width="2" />
                <text x="50" y="60" font-family="Arial" font-size="12" text-anchor="middle" fill="#FFF">{food_name[:2]}</text>
            </svg>"""
        else:
            # 其他蔬菜类通用图标
            return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
                <path d="M30,50 Q50,20 70,50 Q50,80 30,50 Z" fill="{main_color}" />
                <path d="M50,30 L50,15" stroke="#228B22" stroke-width="2" />
                <text x="50" y="55" font-family="Arial" font-size="12" text-anchor="middle" fill="#006400">{food_name[:2]}</text>
            </svg>"""

    elif category == "水果类":
        if "苹果" in food_name:
            # 苹果图标
            return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
                <path d="M50,35 Q70,35 70,60 Q70,85 50,85 Q30,85 30,60 Q30,35 50,35 Z" fill="#FF0000" />
                <path d="M50,35 Q60,20 50,10" stroke="#A52A2A" stroke-width="2" fill="none" />
                <path d="M50,10 L55,15" stroke="#228B22" stroke-width="2" fill="none" />
                <text x="50" y="65" font-family="Arial" font-size="12" text-anchor="middle" fill="#FFF">{food_name[:2]}</text>
            </svg>"""
        elif "香蕉" in food_name:
            # 香蕉图标
            return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
                <path d="M30,30 Q70,20 80,60 Q60,70 30,60 Q20,40 30,30 Z" fill="#FFD700" />
                <path d="M30,30 L25,25" stroke="#8B4513" stroke-width="2" fill="none" />
                <text x="50" y="50" font-family="Arial" font-size="12" text-anchor="middle" fill="#8B4513">{food_name[:2]}</text>
            </svg>"""
        elif "橙子" in food_name or "橘子" in food_name:
            # 橙子/橘子图标
            return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
                <circle cx="50" cy="55" r="30" fill="#FFA500" />
                <path d="M50,25 L50,15" stroke="#228B22" stroke-width="2" />
                <path d="M50,25 Q55,25 55,20" stroke="#228B22" stroke-width="2" fill="none" />
                <text x="50" y="60" font-family="Arial" font-size="12" text-anchor="middle" fill="#FFF">{food_name[:2]}</text>
            </svg>"""
        else:
            # 其他水果类通用图标
            return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
                <circle cx="50" cy="55" r="30" fill="{main_color}" />
                <path d="M50,25 L50,15" stroke="#228B22" stroke-width="2" />
                <text x="50" y="60" font-family="Arial" font-size="12" text-anchor="middle" fill="#FFF">{food_name[:2]}</text>
            </svg>"""

    elif category == "肉蛋类":
        if "蛋" in food_name:
            # 蛋类图标
            return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
                <ellipse cx="50" cy="55" rx="25" ry="30" fill="#FFFACD" />
                <circle cx="50" cy="55" r="10" fill="#FFD700" />
                <text x="50" y="40" font-family="Arial" font-size="12" text-anchor="middle" fill="#8B4513">{food_name[:2]}</text>
            </svg>"""
        else:
            # 肉类图标
            return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
                <path d="M25,40 Q50,30 75,40 Q85,50 75,60 Q50,70 25,60 Q15,50 25,40 Z" fill="{main_color}" />
                <path d="M35,45 Q50,40 65,45 Q70,50 65,55 Q50,60 35,55 Q30,50 35,45 Z" fill="#FFE4E1" />
                <text x="50" y="52" font-family="Arial" font-size="12" text-anchor="middle" fill="#8B4513">{food_name[:2]}</text>
            </svg>"""

    elif category == "奶制品":
        # 奶制品图标 - 奶瓶/杯
        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <path d="M35,30 L40,80 L60,80 L65,30 Z" fill="{main_color}" />
            <path d="M35,30 L65,30 L65,25 L35,25 Z" fill="#D3D3D3" />
            <text x="50" y="55" font-family="Arial" font-size="12" text-anchor="middle" fill="#333">{food_name[:2]}</text>
        </svg>"""

    elif category == "豆制品":
        # 豆制品图标 - 豆腐块
        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <rect x="30" y="35" width="40" height="40" fill="{main_color}" />
            <line x1="30" y1="45" x2="70" y2="45" stroke="#EEE" stroke-width="1" />
            <line x1="30" y1="55" x2="70" y2="55" stroke="#EEE" stroke-width="1" />
            <line x1="30" y1="65" x2="70" y2="65" stroke="#EEE" stroke-width="1" />
            <line x1="40" y1="35" x2="40" y2="75" stroke="#EEE" stroke-width="1" />
            <line x1="50" y1="35" x2="50" y2="75" stroke="#EEE" stroke-width="1" />
            <line x1="60" y1="35" x2="60" y2="75" stroke="#EEE" stroke-width="1" />
            <text x="50" y="55" font-family="Arial" font-size="12" text-anchor="middle" fill="#333">{food_name[:2]}</text>
        </svg>"""

    elif category == "坚果类":
        # 坚果类图标 - 坚果形状
        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <ellipse cx="50" cy="55" rx="25" ry="30" fill="{main_color}" />
            <path d="M35,45 Q50,35 65,45 Q50,55 35,45 Z" fill="#8B4513" />
            <text x="50" y="65" font-family="Arial" font-size="12" text-anchor="middle" fill="#333">{food_name[:2]}</text>
        </svg>"""

    elif category == "零食饮料":
        if "可乐" in food_name or "饮料" in food_name:
            # 饮料图标 - 瓶/罐
            return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
                <path d="M40,25 L40,30 L35,35 L35,75 L65,75 L65,35 L60,30 L60,25 Z" fill="{main_color}" />
                <path d="M40,25 L60,25 L60,30 L40,30 Z" fill="#D3D3D3" />
                <text x="50" y="55" font-family="Arial" font-size="12" text-anchor="middle" fill="#FFF">{food_name[:2]}</text>
            </svg>"""
        else:
            # 零食图标 - 薯片/饼干
            return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
                <path d="M30,40 Q50,20 70,40 Q90,60 70,80 Q50,100 30,80 Q10,60 30,40 Z" fill="{main_color}" />
                <text x="50" y="60" font-family="Arial" font-size="12" text-anchor="middle" fill="#333">{food_name[:2]}</text>
            </svg>"""

    elif category == "调味品":
        # 调味品图标 - 调味瓶
        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <path d="M45,25 L55,25 L55,35 L60,40 L60,75 L40,75 L40,40 L45,35 Z" fill="{main_color}" />
            <rect x="47" y="20" width="6" height="5" fill="#D3D3D3" />
            <text x="50" y="55" font-family="Arial" font-size="12" text-anchor="middle" fill="#333">{food_name[:2]}</text>
        </svg>"""

    elif category == "油脂类":
        # 油脂类图标 - 油瓶
        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <path d="M45,30 L55,30 L60,40 L60,70 L40,70 L40,40 Z" fill="{main_color}" />
            <path d="M47,25 L53,25 L53,30 L47,30 Z" fill="#D3D3D3" />
            <path d="M45,50 L55,50 L55,60 L45,60 Z" fill="rgba(255,255,255,0.3)" />
            <text x="50" y="45" font-family="Arial" font-size="12" text-anchor="middle" fill="#333">{food_name[:2]}</text>
        </svg>"""

    else:
        # 其他食物通用图标
        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="30" fill="{main_color}" />
            <text x="50" y="55" font-family="Arial" font-size="14" text-anchor="middle" fill="#333">{food_name[:2]}</text>
        </svg>"""


def execute_sql_script(script_name):
    """执行SQL脚本文件"""
    try:
        # 获取SQL文件路径
        sql_file_path = os.path.join(os.path.dirname(__file__), script_name)

        if not os.path.exists(sql_file_path):
            logger.warning(f"SQL脚本文件不存在: {sql_file_path}")
            return False

        # 读取SQL文件内容
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        # 分割SQL语句
        sql_statements = []
        current_statement = []

        for line in sql_content.split('\n'):
            # 跳过注释和空行
            if line.strip().startswith('--') or line.strip() == '' or line.strip().startswith('/*') or line.strip().startswith('*/'):
                continue

            # 添加到当前语句
            current_statement.append(line)

            # 如果行以分号结束，则完成一个语句
            if line.strip().endswith(';'):
                sql_statements.append('\n'.join(current_statement))
                current_statement = []

        # 执行SQL语句
        with engine.begin() as conn:
            for statement in sql_statements:
                if statement.strip():
                    try:
                        conn.execute(sqlalchemy.text(statement))
                        logger.info(f"已执行SQL语句: {statement[:50]}...")
                    except Exception as e:
                        logger.error(f"执行SQL语句失败: {str(e)}")

        logger.info(f"SQL脚本 {script_name} 执行完成")
        return True

    except Exception as e:
        logger.error(f"执行SQL脚本失败: {str(e)}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="开发环境设置")
    parser.add_argument("--reset", action="store_true", help="重置数据库（删除所有表并重新创建）")
    parser.add_argument("--sample-data", action="store_true", help="创建示例数据")
    parser.add_argument("--init-db", action="store_true", help="初始化数据库")
    parser.add_argument("--use-orm", action="store_true", help="使用ORM模型创建表结构（默认使用SQL文件）")
    parser.add_argument("--import-food", action="store_true", help="导入食物营养数据")
    args = parser.parse_args()

    try:
        if args.reset:
            logger.info("正在重置数据库...")
            reset_db()
        elif args.init_db or not args.sample_data:
            logger.info("正在初始化数据库...")
            if args.use_orm:
                logger.info("使用ORM模型创建表结构...")
                init_db()
            else:
                logger.info("使用SQL文件创建表结构...")
                create_tables_from_sql()

        db = SessionLocal()
        try:
            # 创建超级管理员
            admin = create_admin_user(db)

            # 创建测试用户
            test_user = create_test_user(db)

            # 创建示例数据
            if args.sample_data and test_user:
                logger.info("正在创建示例数据...")
                create_sample_glucose_data(db, test_user.id)

            # 导入食物营养数据
            if args.import_food:
                logger.info("正在导入食物营养数据...")
                import_food_nutrition_data(db)

            logger.info("开发环境设置完成！")
            logger.info("\n开发账号信息:")
            logger.info("开发账号已按环境变量配置创建（密码不会写入日志）")
            logger.info("\n启动应用: python main.py")

        finally:
            db.close()

    except Exception as e:
        logger.error(f"设置过程中发生错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
