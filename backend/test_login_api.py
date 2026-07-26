#!/usr/bin/env python
"""
测试登录API并打印详细错误信息
"""

import requests
import json
import logging
import os

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# API基本URL
BASE_URL = "http://localhost:8000/api/v1"

def test_login_api():
    """测试登录API"""
    print("开始测试登录API...")

    # API地址
    url = f"{BASE_URL}/users/login"

    # 登录数据
    login_data = {
        "username": "admin@example.com",
        "password": os.getenv("TEST_PASSWORD", ""),
    }
    if not login_data["password"]:
        raise RuntimeError("请先设置 TEST_PASSWORD 环境变量")

    # 将登录数据转换为表单格式
    form_data = {
        "username": login_data["username"],
        "password": login_data["password"]
    }

    # 发送请求
    try:
        print(f"发送POST请求到: {url}")
        print(f"请求数据: {form_data}")

        # 使用表单格式发送请求
        response = requests.post(
            url,
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        print(f"响应状态码: {response.status_code}")

        if response.status_code == 200:
            print("登录成功!")
            print(f"响应数据: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        else:
            print(f"登录失败! 状态码: {response.status_code}")
            print(f"错误信息: {response.text}")

    except Exception as e:
        print(f"请求失败: {str(e)}")

if __name__ == "__main__":
    test_login_api()
