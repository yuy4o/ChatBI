# Mock API services for development and testing

def mock_freeshot_response(query, tables):
    """
    Generate mock freeshot response data
    """
    # Mock data - in a real implementation, this would be generated based on the query and tables
    mock_data = {
        "count": 2,
        "freeshot": [
            {"query": "今天的播放量", "sql": "SELECT COUNT(*) FROM video_play_logs WHERE date(created_at) = CURRENT_DATE"},
            {"query": "最近天气怎么样", "sql": "SELECT date, weather_condition FROM weather_data ORDER BY date DESC LIMIT 7"}
        ]
    }
    return mock_data


def mock_term_response(query, dbs):
    """
    Generate mock term response data
    """
    # Mock data - in a real implementation, this would be generated based on the query and dbs
    mock_data = {
        "count": 3,
        "terms": [
            {"term": "高级用户", "description": "通常指在平台上消费金额较高或使用频率较高的用户"},
            {"term": "播放量", "description": "视频被观看的次数总和，是衡量视频受欢迎程度的重要指标"},
            {"term": "互动率", "description": "用户与视频进行互动（如点赞、评论、分享）的比例，通常用互动次数除以播放量计算"}
        ]
    }
    return mock_data


def mock_sql_response(query, ddl=None, freeshot=None, term=None, sql=None, reason=None):
    """
    Generate mock SQL generation response data
    """
    # Mock data - in a real implementation, this would be generated based on the input parameters
    mock_data = {
        "thought": "针对'最近3天的播放量'需求，我考虑计算逻辑如下：需要从video_play_logs表中统计最近3天的记录数量，按天进行分组展示，并按日期排序。",
        "sql": "SELECT DATE(created_at) as date, COUNT(*) as play_count FROM video_play_logs WHERE created_at >= DATE('now', '-3 days') GROUP BY DATE(created_at) ORDER BY date DESC"
    }
    return mock_data


def mock_execute_response(sql):
    """
    Generate mock SQL execution response data
    """
    # Mock data - in a real implementation, this would be the result of executing the SQL
    mock_data = {
        "columns": [
            {
                "name": "date",
                "type": "DATE",
                "nullable": False
            },
            {
                "name": "play_count",
                "type": "INTEGER",
                "nullable": False
            }
        ],
        "data": [
            ["2023-05-15", 12543],
            ["2023-05-14", 10982],
            ["2023-05-13", 11756]
        ],
        "totalRows": 3
    }
    return mock_data