import requests
import json
import time
import os
from typing import Dict, Any

# 配置
BASE_URL = "http://localhost:8000/api/v1"
TEST_USER = {
    "email": os.getenv("TEST_USER_EMAIL", "user@local.test"),
    "password": os.getenv("TEST_USER_PASSWORD", ""),
}

def login() -> str:
    """登录并获取访问令牌"""
    if not TEST_USER["password"]:
        print("请先设置 TEST_USER_PASSWORD 环境变量")
        return ""
    response = requests.post(
        f"{BASE_URL}/users/login",
        data={
            "username": TEST_USER["email"],
            "password": TEST_USER["password"],
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    if response.status_code != 200:
        print(f"登录失败: {response.status_code} - {response.text}")
        return ""

    data = response.json()
    print(f"登录成功，获取到token: {data['access_token'][:20]}...")
    return data["access_token"]

def make_request(method: str, endpoint: str, token: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """发送请求到API"""
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BASE_URL}/ollama{endpoint}"

    print(f"发送{method.upper()}请求到: {url}")
    print(f"请求头: {headers}")
    if data:
        print(f"请求数据: {json.dumps(data, ensure_ascii=False)}")

    if method.lower() == "get":
        response = requests.get(url, headers=headers)
    elif method.lower() == "post":
        response = requests.post(url, json=data, headers=headers)
    else:
        raise ValueError(f"不支持的HTTP方法: {method}")

    if response.status_code >= 400:
        print(f"请求失败: {response.status_code} - {response.text}")
        return {}

    return response.json()

def test_health():
    """测试健康检查端点"""
    print("\n测试健康检查...")
    response = requests.get(f"{BASE_URL}/ollama/health")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")

def test_list_models(token: str):
    """测试获取模型列表"""
    print("\n测试获取模型列表...")
    result = make_request("get", "/models", token)
    print(json.dumps(result, indent=2, ensure_ascii=False))

def test_generate_text(token: str):
    """测试生成文本"""
    print("\n测试生成文本...")
    data = {
        "prompt": "你好",
        "temperature": 0.7,
        "max_tokens": 500
    }

    start_time = time.time()
    result = make_request("post", "/generate", token, data)
    end_time = time.time()

    print(f"生成时间: {end_time - start_time:.2f}秒")
    print(f"响应: {result.get('response', '')}")

def test_chat(token: str):
    """测试聊天对话"""
    print("\n测试聊天对话...")
    data = {
        "messages": [
            {"role": "user", "content": "ni==你是谁？"}
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }

    # 确保token有效
    print(f"使用的token: {token[:20]}...")

    start_time = time.time()
    result = make_request("post", "/chat", token, data)
    end_time = time.time()

    print(f"生成时间: {end_time - start_time:.2f}秒")
    if "message" in result and "content" in result.get("message", {}):
        print(f"响应: {result['message']['content']}")
    else:
        print(f"响应格式异常: {result}")

def main():
    """主函数"""
    print("开始测试Ollama API...")

    # 测试健康检查
    test_health()

    # 登录获取令牌
    token = login()
    if not token:
        print("登录失败，无法继续测试")
        return

    # 测试获取模型列表
    test_list_models(token)

    # 测试生成文本
    test_generate_text(token)

    # 测试聊天对话
    test_chat(token)

    print("\n测试完成!")

if __name__ == "__main__":
    main()
