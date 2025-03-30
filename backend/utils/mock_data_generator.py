import sys
import os

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from utils.mock_iqiyi_video_play_logs import generate_iqiyi_data
from utils.mock_iqiyi_video_interactions import generate_iqiyi_interaction_data
from config.constants import INITIAL_DATA_DIR
import json

def generate_mock_data(num_records=3000, start_date=None, end_date=None, video_id_list=None):
    """
    统一生成爱奇艺视频播放日志和交互数据的入口函数
    
    Args:
        num_records: 要生成的记录数量，默认3000条
        start_date: 数据开始日期，格式'YYYY-MM-DD'，默认为当前日期前14天
        end_date: 数据结束日期，格式'YYYY-MM-DD'，默认为当前日期
        video_id_list: 视频ID列表，如果不提供则使用默认列表
    
    Returns:
        tuple: (play_logs_data, interactions_data) 包含生成的播放日志和交互数据的元组
    """
    # 如果没有提供日期范围，使用最近两周
    if not end_date:
        end_date = datetime.now().date()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    if not start_date:
        start_date = end_date - timedelta(days=14)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    # 转换日期格式
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    # 如果没有提供视频ID列表，使用默认列表
    if video_id_list is None:
        video_id_list = [
            5001234579, 5001234580, 5001234581, 5001234582, 5001234583,
            5001234584, 5001234585, 5001234586, 5001234587, 5001234588,
            5001234589, 5001234590, 5001234591, 5001234592, 5001234593,
            5001234594, 5001234595, 5001234596, 5001234597, 5001234598
        ]
    
    # 生成播放日志数据
    play_logs_data = generate_iqiyi_data(
        num_records=num_records,
        start_date=start_date_str,
        end_date=end_date_str,
        video_id_list=video_id_list
    )
    
    # 生成交互数据
    interactions_data = generate_iqiyi_interaction_data(
        num_records=num_records,
        start_date=start_date_str,
        end_date=end_date_str,
        video_id_list=video_id_list
    )
    
    # 保存数据到文件
    with open(INITIAL_DATA_DIR + '/iqiyi_data_video_play_logs.json', 'w', encoding='utf-8') as f:
        json.dump(play_logs_data, f, ensure_ascii=False, indent=2)
    
    with open(INITIAL_DATA_DIR + '/iqiyi_data_video_interaction.json', 'w', encoding='utf-8') as f:
        json.dump(interactions_data, f, ensure_ascii=False, indent=2)
    
    print(f"已生成 {len(play_logs_data['video_play_logs'])} 条播放日志记录")
    print(f"已生成 {len(interactions_data['video_interactions'])} 条交互数据记录")
    
    return play_logs_data, interactions_data