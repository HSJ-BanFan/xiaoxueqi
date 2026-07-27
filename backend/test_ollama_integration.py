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

def make_request(method: str, endpoint: str, token: str = None, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """发送请求到API"""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"{BASE_URL}/{endpoint}"

    print(f"发送{method.upper()}请求到: {url}")
    if token:
        print(f"已使用token: {token[:20]}...")

    if data:
        print(f"请求数据: {json.dumps(data, ensure_ascii=False)}")

    try:
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
    except Exception as e:
        print(f"请求异常: {str(e)}")
        return {}

def test_assistant_chat(token: str):
    """测试智能助理聊天功能"""
    print("\n测试智能助理聊天...")
    data = {"message": "什么是糖尿病？"}

    start_time = time.time()
    result = make_request("post", "assistant/chat", token, data)
    end_time = time.time()

    print(f"生成时间: {end_time - start_time:.2f}秒")
    if "message" in result:
        print(f"回复: {result['message']}")
    else:
        print(f"响应格式异常: {result}")

def test_ollama_health():
    """测试Ollama健康检查端点"""
    print("\n测试Ollama健康检查...")
    result = make_request("get", "ollama/health")
    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")

def test_ollama_models(token: str):
    """测试获取Ollama模型列表"""
    print("\n测试获取Ollama模型列表...")
    result = make_request("get", "ollama/models", token)
    if "models" in result:
        models = result["models"]
        print(f"可用模型数量: {len(models)}")
        for i, model in enumerate(models):
            print(f"模型 {i+1}: {model['name']}")
    else:
        print(f"响应格式异常: {result}")

def test_ollama_chat(token: str):
    """测试Ollama聊天功能"""
    print("\n测试Ollama聊天功能...")
    data = {
        "messages": [
            {"role": "user", "content": "你好，请简单介绍一下糖尿病"}
        ]
    }

    start_time = time.time()
    result = make_request("post", "ollama/chat", token, data)
    end_time = time.time()

    print(f"生成时间: {end_time - start_time:.2f}秒")
    if "message" in result and "content" in result.get("message", {}):
        print(f"回复: {result['message']['content']}")
    else:
        print(f"响应格式异常: {result}")

def main():
    """主函数"""
    print("开始测试Ollama与智能助手集成...")

    # 测试Ollama健康检查
    test_ollama_health()

    # 登录获取令牌
    token = login()
    if not token:
        print("登录失败，无法继续测试")
        return

    # 测试获取Ollama模型列表
    test_ollama_models(token)

    # 测试原有智能助理
    test_assistant_chat(token)

    # 测试Ollama聊天功能
    test_ollama_chat(token)

    print("\n测试完成!")

if __name__ == "__main__":
    main()
