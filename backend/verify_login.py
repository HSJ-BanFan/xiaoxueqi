#!/usr/bin/env python
"""
验证用户登录凭据
"""

import sys
import os
import logging
from passlib.context import CryptContext
import requests
import json
from urllib.parse import urlencode

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.db.models import User
from app.core.security import verify_password

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def verify_user_credentials(email, password):
    """验证用户登录凭据"""
    db = SessionLocal()
    try:
        # 查询用户
        user = db.query(User).filter(User.email == email).first()

        if not user:
            logger.error(f"❌ 用户不存在: {email}")
            return False

        logger.info(f"✅ 找到用户: {user.email}")
        logger.info(f"用户ID: {user.id}")
        logger.info(f"用户名: {user.name}")
        logger.info(f"是否激活: {user.is_active}")
        logger.info(f"是否管理员: {user.is_superuser}")

        # 验证密码
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        password_match = pwd_context.verify(password, user.hashed_password)

        if password_match:
            logger.info(f"✅ 密码验证成功!")
            return True
        else:
            logger.error(f"❌ 密码不匹配")
            return False

    except Exception as e:
        logger.error(f"❌ 验证凭据时出错: {e}")
        return False

    finally:
        db.close()

def verify_login():
    """验证登录过程，模拟前端的登录请求"""
    print("开始验证登录过程...")

    # API地址
    base_url = "http://localhost:8000"
    login_url = f"{base_url}/api/v1/users/login"

    # 登录数据
    login_data = {
        "username": os.getenv("TEST_USER_EMAIL", "user@local.test"),
        "password": os.getenv("TEST_USER_PASSWORD", ""),
    }
    if not login_data["password"]:
        raise RuntimeError("请先设置 TEST_USER_PASSWORD 环境变量")

    # 将登录数据转换为表单格式
    form_data = urlencode(login_data)

    # 发送请求
    try:
        print(f"发送POST请求到: {login_url}")
        print(f"请求账号: {login_data['username']}，密码已隐藏")
        print(f"请求头: Content-Type: application/x-www-form-urlencoded")

        # 使用表单格式发送请求
        response = requests.post(
            login_url,
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        print(f"响应状态码: {response.status_code}")

        if response.status_code == 200:
            print("登录成功!")
            response_data = response.json()
            print(f"响应数据: {json.dumps(response_data, indent=2, ensure_ascii=False)}")

            # 获取令牌
            token = response_data.get("access_token")

            # 测试获取用户资料
            if token:
                print("\n使用令牌获取用户资料...")
                profile_url = f"{base_url}/api/v1/users/profile"
                profile_response = requests.get(
                    profile_url,
                    headers={"Authorization": f"Bearer {token}"}
                )

                print(f"资料请求状态码: {profile_response.status_code}")

                if profile_response.status_code == 200:
                    print("获取用户资料成功!")
                    print(f"用户资料: {json.dumps(profile_response.json(), indent=2, ensure_ascii=False)}")
                else:
                    print(f"获取用户资料失败! 状态码: {profile_response.status_code}")
                    print(f"错误信息: {profile_response.text}")
        else:
            print(f"登录失败! 状态码: {response.status_code}")
            print(f"错误信息: {response.text}")

    except Exception as e:
        print(f"请求失败: {str(e)}")

if __name__ == "__main__":
    verify_login()
