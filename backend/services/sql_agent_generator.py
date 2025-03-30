import json
from typing import Dict, List, Any, Optional, Union
from services.db_service import execute_query, DatabaseError
from services.logger import broadcast_log
from services.llm_service import get_client
from services.llm_config import get_model
from services.prompt_manager import PromptManager
from services.sql_agent import SQLAgent, generate_sql_with_agent


def generate_sql_with_react_agent(ddl: List = None, freeshot: List = None, term: List = None, messages: List = None) -> Dict:
    """
    使用基于ReAct范式的SQLAgent生成SQL并执行
    
    Args:
        ddl: 数据库定义信息
        freeshot: 相似查询示例
        term: 术语解释
        messages: 历史对话消息
        
    Returns:
        Dict: 包含思考过程、SQL和执行结果的字典
    """
    # 调用SQLAgent生成SQL并执行
    return generate_sql_with_agent(ddl, freeshot, term, messages)