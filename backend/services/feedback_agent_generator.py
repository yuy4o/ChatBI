import json
from typing import Dict, List, Any, Optional, Union
from services.logger import broadcast_log
from services.feedback_agent import FeedbackAgent, process_feedback_good


def generate_feedback_with_agent(ddl: List = None, freeshot: List = None, term: List = None, messages: List = None) -> Dict:
    """
    使用FeedbackAgent处理用户点赞反馈，分析历史对话并更新元数据描述
    
    Args:
        ddl: 数据库定义信息
        freeshot: 相似查询示例
        term: 术语解释
        messages: 历史对话消息
        
    Returns:
        Dict: 包含处理结果的字典
    """
    # 调用FeedbackAgent处理反馈
    return process_feedback_good(ddl, freeshot, term, messages)