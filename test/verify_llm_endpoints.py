import requests
import datetime
import random
import time
import os

# --- 配置 ---
# 请在运行脚本前配置以下信息
# 你的FastAPI应用的基础URL
BASE_URL = "http://127.0.0.1:8000/api/v1"
# 用于测试的有效用户名和密码
TEST_USERNAME = "admin@example.com"
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "")

# 脚本假设你的登录端点是 /users/login (POST)
# 如果端点不同, 请修改 LOGIN_URL
LOGIN_URL = f"{BASE_URL}/users/login"
GLUCOSE_MONITOR_URL = f"{BASE_URL}/glucose-monitor"

def print_test_header(name):
    """打印测试标题"""
    print("\n" + "="*60)
    print(f"  Testing Endpoint: {name}")
    print("="*60)

def print_test_result(response, expected_fields):
    """打印测试结果"""
    print(f"-> Status Code: {response.status_code}")
    success = False
    try:
        response_data = response.json()
        print(f"-> Response JSON: {response_data}")
        # 检查关键字段是否存在且不为空
        missing_fields = [field for field in expected_fields if not response_data.get(field)]
        if response.status_code == 200 and not missing_fields:
            success = True
            print(f"✅ SUCCESS: Status code is 200 and expected fields {expected_fields} are present.")
        else:
            print(f"❌ FAILED: Status code was {response.status_code} or missing fields: {missing_fields}.")

    except ValueError:
        print("❌ FAILED: Response is not valid JSON.")
        print(f"-> Response Text: {response.text}")

    print("-" * 60)
    return success

def login():
    """登录测试用户并返回认证token"""
    print("Step 1: Attempting to log in...")
    try:
        # FastAPI的OAuth2PasswordRequestForm通常需要表单数据
        response = requests.post(LOGIN_URL, data={"username": TEST_USERNAME, "password": TEST_PASSWORD})
        if response.status_code == 200:
            token = response.json().get("access_token")
            print("Login successful. Token received.")
            return token
        else:
            print(f"Login failed! Status: {response.status_code}, Response: {response.text}")
            print("Please check your TEST_USERNAME, TEST_PASSWORD, and LOGIN_URL.")
            return None
    except requests.exceptions.ConnectionError:
        print(f"Connection Error: Could not connect to {LOGIN_URL}. Is the server running?")
        return None

def create_test_record(headers, value=None):
    """为测试创建一个血糖记录"""
    print("   ...creating a sample glucose record for analysis...")
    if value is None:
        value = round(random.uniform(8.0, 15.0), 1) # 默认创建一个偏高的值来触发预警

    payload = {
        "value": value,
        "measurement_time": random.choice(["BEFORE_BREAKFAST", "AFTER_LUNCH", "BEFORE_DINNER"]),
        "measurement_method": "FINGER_STICK",
        "measured_at": datetime.datetime.now().isoformat(),
        "notes": "Record created by verification script"
    }
    try:
        response = requests.post(GLUCOSE_MONITOR_URL, headers=headers, json=payload)
        if response.status_code == 200:
            print(f"   Successfully created a test record with value: {value}")
            return response.json()
        else:
            print(f"   Failed to create test record. Status: {response.status_code}, Response: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"   An error occurred while creating a test record: {e}")
        return None

def test_quick_diet_suggestions(headers):
    """测试 GET /quick-diet-suggestions 端点"""
    print_test_header("GET /quick-diet-suggestions")
    params = {
        "glucose_value": 12.5,  # 一个较高的值
        "meal_type": "LUNCH",
        "is_before_meal": False
    }
    try:
        response = requests.get(f"{GLUCOSE_MONITOR_URL}/quick-diet-suggestions", headers=headers, params=params)
        print_test_result(response, ["suggestion"])
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

def test_analyze(headers):
    """测试 POST /analyze 端点"""
    print_test_header("POST /analyze")
    # 确保至少有一条记录用于分析
    create_test_record(headers, value=15.0) # 创建一个高血糖记录以触发预警
    time.sleep(1) # 等待一下，确保记录时间不同

    payload = {"hours": 24}
    try:
        response = requests.post(f"{GLUCOSE_MONITOR_URL}/analyze", headers=headers, json=payload)
        print_test_result(response, ["alert_message", "statistics"])
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

def test_analyze_trend(headers):
    """测试 POST /analyze-trend 端点"""
    print_test_header("POST /analyze-trend")
    # 此端点至少需要3条记录
    print("   Creating 3 records for trend analysis...")
    for i in range(3):
        create_test_record(headers, value=random.uniform(4.0, 10.0))
        time.sleep(1) # 确保每条记录时间戳不同

    payload = {"days": 3}
    try:
        response = requests.post(f"{GLUCOSE_MONITOR_URL}/analyze-trend", headers=headers, json=payload)
        print_test_result(response, ["advice", "statistics", "patterns"])
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    print("="*60)
    print("  LLM Endpoint Verification Script")
    print("="*60)
    print("This script will test if the analysis endpoints can call the LLM.")
    print("Please make sure your FastAPI server is running before proceeding.")

    # 登录并获取Token
    token = login()

    if token:
        # 设置认证头
        auth_headers = {"Authorization": f"Bearer {token}"}

        # 按顺序执行测试
        print("\nStep 2: Running tests...")
        test_quick_diet_suggestions(auth_headers)
        test_analyze(auth_headers)
        test_analyze_trend(auth_headers)
        print("\nVerification script finished.")
    else:
        print("\nCould not retrieve auth token. Aborting tests.")
        print("Please check your server status and user credentials in the script.")
