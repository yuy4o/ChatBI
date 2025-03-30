import sqlite3
from services.logger import broadcast_log
from config.constants import METADATA_DB_PATH

def generate_freeshot_metadata_from_schema(schema_data):
    """
    从数据库中获取自由查询示例数据
    返回格式：[{"name": "今天的播放量", "content":"SELECT COUNT(*) FROM video_play_logs WHERE date(created_at) = CURRENT_DATE"}]
    """
    broadcast_log("system", "", "根据用户问题召回相关示例")
    
    try:
        conn = sqlite3.connect(METADATA_DB_PATH)
        cursor = conn.cursor()
        
        # 查询freeshots表，按likes降序排列
        cursor.execute('SELECT name, content FROM freeshots ORDER BY likes DESC')
        rows = cursor.fetchall()
        
        conn.close()
        
        # 转换为所需格式
        return [{"name": row[0], "content": row[1]} for row in rows]
    except Exception as e:
        print(f"Error fetching freeshot data: {e}")
        # 如果出错，返回默认数据
        return [
            {"name": "今天的播放量", "content":"SELECT COUNT(*) FROM video_play_logs WHERE dt='2023-05-19'"},
            {"name": "最近一周的播放量", "content":"SELECT COUNT(*) FROM video_play_logs WHERE dt>='2023-05-12' and dt<='2023-05-19'"}
        ]