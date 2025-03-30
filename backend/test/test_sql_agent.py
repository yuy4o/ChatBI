import unittest
from services.sql_agent import generate_sql_with_agent

class TestSQLAgent(unittest.TestCase):
    def test_gold_member_play_duration(self):
        # 准备测试数据

        # DDL信息
        ddl = [
            {
                "content": """CREATE TABLE video_play_logs (
    log_id BIGINT PRIMARY KEY COMMENT '日志ID',
    video_id BIGINT PRIMARY KEY COMMENT '视频ID',
    device_id VARCHAR(100) PRIMARY KEY COMMENT '设备ID',
    start_time TIMESTAMP COMMENT '开始播放时间',
    end_time TIMESTAMP COMMENT '结束播放时间',
    duration INT COMMENT '播放时长(秒)',
    video_duration INT COMMENT '视频总时长(秒)',
    playback_quality ENUM('720p') COMMENT '播放质量 [720p: 超清]',
    dt VARCHAR(50) COMMENT '日期分区'
) COMMENT = '视频播放日志表';""",
                "name": "视频播放日志表",
                "table_name": "video_play_logs"
            }
        ]
        
        # 相似查询示例
        freeshot = [
            {
                "content": "SELECT COUNT(*) FROM video_play_logs WHERE dt='2025-03-27'",
                "name": "昨天的播放量"
            }
        ]
        
        # 术语解释
        term = [
            {
                "content": "一般指等级大于3的用户",
                "name": "高级用户"
            },
            {
                "content": "一般指等级大于1的用户",
                "name": "普通用户"
            }
        ]
        
        # 历史对话消息
        messages = [
            {"role":"user", "content":"最近3天的播放时长、播放次数"}
        ]
        
        # 调用SQLAgent生成SQL并执行
        result = generate_sql_with_agent(
            ddl=ddl,
            freeshot=freeshot,
            term=term,
            messages=messages
        )
        print(result)

if __name__ == '__main__':
    unittest.main()