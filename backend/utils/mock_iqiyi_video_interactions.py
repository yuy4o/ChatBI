import sys
import os

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import random
from datetime import datetime, timedelta
import uuid
import numpy as np
from config.constants import INITIAL_DATA_DIR

def generate_iqiyi_interaction_data(num_records=1000, 
                                   start_date="2025-03-10", 
                                   end_date="2025-03-25", 
                                   video_id_list=None):
    """
    Generate mock data for iQiyi video interactions
    
    Args:
        num_records: Number of interaction records to generate
        start_date: Start date for data partition (inclusive)
        end_date: End date for data partition (inclusive)
        video_id_list: List of video IDs to use
    
    Returns:
        Dictionary containing generated data
    """
    if video_id_list is None:
        video_id_list = [5001234579, 5001234580, 5001234581, 5001234582, 5001234583, 
                         5001234584, 5001234585, 5001234586, 5001234587]
    
    # Define interaction types and their weights (to make distribution realistic)
    interaction_types = ["like", "dislike", "comment", "share", "favorite", "report"]
    interaction_weights = [0.45, 0.05, 0.25, 0.15, 0.08, 0.02]  # More likes than reports
    
    # Generate date range
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    date_range = [(start + timedelta(days=i)).strftime("%Y-%m-%d") 
                  for i in range((end - start).days + 1)]
    
    # Date distribution - more interactions on weekends and recent dates
    date_weights = []
    for date_str in date_range:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        # Weight based on day of week (higher for weekends)
        day_weight = 1.5 if date.weekday() >= 5 else 1.0
        # Weight based on recency (more recent = more interactions)
        recency_weight = 1.0 + (date - start).days / ((end - start).days) * 0.5
        date_weights.append(day_weight * recency_weight)
    
    # Normalize weights
    date_weights = [w/sum(date_weights) for w in date_weights]
    
    # Generate user IDs (simulate a user base of about 5000 users)
    user_ids = list(range(10000001, 10005001))
    
    # Comment templates to make data more realistic
    comment_templates = [
        "这部电视剧太{adj}了！", 
        "演员的表演{adv}{adj}！",
        "剧情发展{adj}，很{adj2}。",
        "第{episode}集简直{adj}到不行！",
        "这个场景拍得真{adj}！",
        "导演的手法很{adj}，{adv}喜欢。",
        "音乐配得{adv}{adj}！",
        "这集的节奏感{adv}好。",
        "这部电视剧值得{number}分！",
        "希望后面的剧情能更{adj}一些。",
        "{character}这个角色{adv}{adj}！",
        "看完这集我{adv}{feeling}了。",
        "这部电视剧{adv}值得推荐！",
        "特效做得{adj}！",
        "这集的转折{adv}出乎意料。",
        "剧中的细节处理得{adv}好。"
    ]
    
    positive_adj = ["精彩", "好看", "感动", "震撼", "出色", "优秀", "精良", "绝妙", "惊艳", "完美"]
    negative_adj = ["无聊", "拖沓", "老套", "俗套", "平淡", "尴尬", "失望", "混乱", "生硬"]
    neutral_adj = ["有趣", "特别", "独特", "不错", "新颖", "意外", "复杂", "深刻"]
    adverbs = ["非常", "真的", "特别", "十分", "太", "超级", "格外", "异常", "相当", ""]
    feelings = ["感动", "震惊", "惊喜", "失望", "期待", "满足", "兴奋", "感慨", "思考"]
    characters = ["男主", "女主", "配角", "反派", "主角", "男二", "女二"]
    
    # Device types for realistic device_ids
    device_types = [
        ("PHONE", 0.65, ["iPhone", "Xiaomi", "Huawei", "OPPO", "vivo", "Samsung"]),
        ("PAD", 0.15, ["iPad", "HuaweiPad", "MiPad", "SamsungTab"]),
        ("TV", 0.15, ["iQiyiTV", "XiaomiTV", "HuaweiTV", "SonyTV", "SamsungTV"]),
        ("PC", 0.05, ["Windows", "MacOS", "Linux"])
    ]
    
    interactions = []
    
    for i in range(num_records):
        # Generate basic fields
        interaction_id = 10000000000 + i
        video_id = random.choice(video_id_list)
        user_id = random.choice(user_ids)
        
        # Select interaction type based on weights
        interaction_type = random.choices(interaction_types, weights=interaction_weights)[0]
        
        # Generate dt (date) based on weighted distribution
        dt = random.choices(date_range, weights=date_weights)[0]
        
        # Generate device ID
        device_category = random.choices([d[0] for d in device_types], 
                                        weights=[d[1] for d in device_types])[0]
        device_brand = random.choice(next(d[2] for d in device_types if d[0] == device_category))
        device_id = f"{device_brand}-{uuid.uuid4().hex[:8].upper()}"
        
        # Generate content based on interaction type
        content = None
        if interaction_type == "comment":
            template = random.choice(comment_templates)
            
            # Determine sentiment - more positive than negative
            sentiment = random.choices(["positive", "neutral", "negative"], weights=[0.65, 0.25, 0.1])[0]
            
            if sentiment == "positive":
                adj = random.choice(positive_adj)
                adj2 = random.choice(positive_adj)
            elif sentiment == "negative":
                adj = random.choice(negative_adj)
                adj2 = random.choice(negative_adj)
            else:
                adj = random.choice(neutral_adj)
                adj2 = random.choice(neutral_adj)
                
            adv = random.choice(adverbs)
            episode = random.randint(1, 20)
            number = random.randint(7, 10)
            character = random.choice(characters)
            feeling = random.choice(feelings)
            
            content = template.format(
                adj=adj, 
                adj2=adj2,
                adv=adv, 
                episode=episode,
                number=number,
                character=character,
                feeling=feeling
            )
        
        interaction = {
            "interaction_id": interaction_id,
            "video_id": video_id,
            "user_id": user_id,
            "interaction_type": interaction_type,
            "content": content,
            "device_id": device_id,
            "dt": dt
        }
        
        interactions.append(interaction)
    
    # Sort by date and then by interaction_id for a more realistic data order
    interactions.sort(key=lambda x: (x["dt"], x["interaction_id"]))
    
    return {"video_interactions": interactions}
