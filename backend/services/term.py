import sqlite3
from services.logger import broadcast_log
from config.constants import METADATA_DB_PATH

def generate_term_metadata_from_schema(schema_data):
    """
    从数据库中获取业务术语数据
    返回格式：[{"name": "高级用户", "content":"一般指等级大于3的用户"}]
    """
    broadcast_log("system", "", "根据用户问题召回相关业务术语")
    
    try:
        conn = sqlite3.connect(METADATA_DB_PATH)
        cursor = conn.cursor()
        
        # 查询terms表，按likes降序排列
        cursor.execute('SELECT name, content FROM terms ORDER BY likes DESC')
        rows = cursor.fetchall()
        
        conn.close()
        
        # 转换为所需格式
        return [{"name": row[0], "content": row[1]} for row in rows]
    except Exception as e:
        print(f"Error fetching term data: {e}")
        # 如果出错，返回默认数据
        return [
            {"name": "高级用户", "content":"一般指等级大于3的用户"},
            {"name": "普通用户", "content":"一般指等级大于1的用户"}
        ]