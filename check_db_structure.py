import pymysql
import os

# 连接数据库
password = os.getenv("MYSQL_PASSWORD")
if not password:
    raise RuntimeError("请先设置 MYSQL_PASSWORD 环境变量")

connection = pymysql.connect(
    host=os.getenv("MYSQL_HOST", "localhost"),
    port=int(os.getenv("MYSQL_PORT", "3306")),
    user=os.getenv("MYSQL_USER", "root"),
    password=password,
    database=os.getenv("MYSQL_DATABASE", "diabetes_assistant"),
)

try:
    with connection.cursor() as cursor:
        # 查看表结构
        cursor.execute("DESCRIBE glucose_records")
        table_structure = cursor.fetchall()
        print("=== glucose_records表结构 ===")
        for column in table_structure:
            print(column)

        # 查看表中的数据
        cursor.execute("SELECT * FROM glucose_records LIMIT 5")
        records = cursor.fetchall()
        print("\n=== glucose_records表数据示例 ===")
        for record in records:
            print(record)
finally:
    connection.close()
