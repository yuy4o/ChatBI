import sqlite3
import os
from config.constants import METADATA_DB_PATH

print(f"数据库路径: {METADATA_DB_PATH}")
print(f"文件存在: {os.path.exists(METADATA_DB_PATH)}")

if os.path.exists(METADATA_DB_PATH):
    try:
        conn = sqlite3.connect(METADATA_DB_PATH)
        cursor = conn.cursor()
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"数据库中的表: {tables}")

        conn.close()
    except Exception as e:
        print(f"数据库连接错误: {e}")