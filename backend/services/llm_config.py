import os
from initial.config import get_llm_config

# 从配置服务获取LLM配置
def get_client():
    """
    Initialize and return OpenAI client with shared configuration
    """
    from openai import OpenAI
    
    # 获取配置
    config = get_llm_config()
    
    return OpenAI(
        api_key=config["api_key"],
        base_url=config["base_url"],
        timeout=config["timeout"],
    )

# 获取模型名称
def get_model():
    """
    Get the model name from configuration
    """
    config = get_llm_config()
    return config["model"]