import sqlite3
import json
import os
from typing import List, Dict, Any, Union, Optional
from config.constants import CONFIG_DB_PATH, INITIAL_DIR
from services.db_service import DatabaseError

# 配置文件路径
CONFIG_JSON_PATH = os.path.join(INITIAL_DIR, 'config', 'config.json')

def load_default_configs() -> List[Dict[str, str]]:
    """
    从config.json文件加载默认配置
    
    Returns:
        List[Dict[str, str]]: 配置项列表
    """
    try:
        with open(CONFIG_JSON_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载配置文件失败: {str(e)}，使用内置默认配置")
        # 如果配置文件不存在或读取失败，返回内置的默认配置
        return [
            {
                "key": "llm_api_key",
                "value": "02fb5cc3-e828-436e-a1b6-c114916c15c6",
                "name": "大模型API密钥"
            },
            {
                "key": "llm_base_url",
                "value": "https://ark.cn-beijing.volces.com/api/v3",
                "name": "大模型接入点"
            },
            {
                "key": "llm_model",
                "value": "deepseek-v3-250324",
                "name": "大模型名称"
            },
            {
                "key": "llm_timeout",
                "value": "1800",
                "name": "大模型超时时间(秒)"
            },
            {
                "key": "embedding_api_key",
                "value": "02fb5cc3-e828-436e-a1b6-c114916c15c6",
                "name": "向量化API密钥"
            },
            {
                "key": "embedding_api_url",
                "value": "https://ark.cn-beijing.volces.com/api/v3/embeddings",
                "name": "向量化接入点"
            },
            {
                "key": "embedding_model",
                "value": "doubao-embedding-text-240715",
                "name": "向量化模型名称"
            }
        ]

def init_config_db():
    """
    初始化配置数据库，如果不存在则创建并写入默认配置
    """
    # 检查数据库文件是否存在
    if os.path.exists(CONFIG_DB_PATH):
        return
    
    # 创建数据库连接
    conn = None
    try:
        conn = sqlite3.connect(CONFIG_DB_PATH)
        cursor = conn.cursor()
        
        # 创建配置表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS configs (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            name TEXT NOT NULL
        )
        """)
        
        # 从配置文件加载默认配置
        default_configs = load_default_configs()
        
        # 插入默认配置
        for config in default_configs:
            cursor.execute(
                "INSERT INTO configs (key, value, name) VALUES (?, ?, ?)",
                (config["key"], config["value"], config["name"])
            )
        
        conn.commit()
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        raise DatabaseError(f"初始化配置数据库失败: {str(e)}")
    finally:
        if conn:
            conn.close()

def get_all_configs() -> List[Dict[str, str]]:
    """
    获取所有配置项
    
    Returns:
        List[Dict[str, str]]: 配置项列表，每项包含key, value, name
    """
    conn = None
    try:
        conn = sqlite3.connect(CONFIG_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT key, value, name FROM configs")
        rows = cursor.fetchall()
        
        # 转换为字典列表
        configs = [{"key": row["key"], "value": row["value"], "name": row["name"]} for row in rows]
        return configs
    except sqlite3.Error as e:
        raise DatabaseError(f"获取配置失败: {str(e)}")
    finally:
        if conn:
            conn.close()

def get_config(key: str) -> Optional[Dict[str, str]]:
    """
    获取指定key的配置项
    
    Args:
        key (str): 配置项的key
        
    Returns:
        Optional[Dict[str, str]]: 配置项，包含key, value, name，如果不存在则返回None
    """
    conn = None
    try:
        conn = sqlite3.connect(CONFIG_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT key, value, name FROM configs WHERE key = ?", (key,))
        row = cursor.fetchone()
        
        if row:
            return {"key": row["key"], "value": row["value"], "name": row["name"]}
        return None
    except sqlite3.Error as e:
        raise DatabaseError(f"获取配置失败: {str(e)}")
    finally:
        if conn:
            conn.close()

def update_configs(configs: List[Dict[str, str]]) -> bool:
    """
    更新配置项
    
    Args:
        configs (List[Dict[str, str]]): 要更新的配置项列表，每项包含key和value
        
    Returns:
        bool: 更新是否成功
    """
    conn = None
    try:
        conn = sqlite3.connect(CONFIG_DB_PATH)
        cursor = conn.cursor()
        
        for config in configs:
            cursor.execute(
                "UPDATE configs SET value = ? WHERE key = ?",
                (config["value"], config["key"])
            )
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        raise DatabaseError(f"更新配置失败: {str(e)}")
    finally:
        if conn:
            conn.close()

def get_llm_config() -> Dict[str, Any]:
    """
    获取LLM相关配置，用于替代llm_config.py中的硬编码配置
    
    Returns:
        Dict[str, Any]: LLM配置字典
    """
    try:
        configs = get_all_configs()
        llm_config = {}
        
        # 提取LLM相关配置
        for config in configs:
            if config["key"] == "llm_api_key":
                llm_config["api_key"] = config["value"]
            elif config["key"] == "llm_base_url":
                llm_config["base_url"] = config["value"]
            elif config["key"] == "llm_model":
                llm_config["model"] = config["value"]
            elif config["key"] == "llm_timeout":
                llm_config["timeout"] = int(config["value"])
        
        # 确保所有必要的配置都存在
        if not all(k in llm_config for k in ["api_key", "base_url", "model", "timeout"]):
            # 如果缺少某些配置，使用默认值
            if "api_key" not in llm_config:
                llm_config["api_key"] = "02fb5cc3-e828-436e-a1b6-c114916c15c6"
            if "base_url" not in llm_config:
                llm_config["base_url"] = "https://ark.cn-beijing.volces.com/api/v3"
            if "model" not in llm_config:
                llm_config["model"] = "deepseek-v3-250324"
            if "timeout" not in llm_config:
                llm_config["timeout"] = 1800
        
        return llm_config
    except Exception as e:
        # 出错时返回默认配置
        print(f"获取LLM配置失败，使用默认配置: {str(e)}")
        return {
            "api_key": "02fb5cc3-e828-436e-a1b6-c114916c15c6",
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            "model": "deepseek-v3-250324",
            "timeout": 1800
        }

def get_embedding_config() -> Dict[str, Any]:
    """
    获取向量嵌入配置
    
    Returns:
        Dict[str, Any]: 向量嵌入配置字典
    """
    try:
        configs = get_all_configs()
        embedding_config = {}
        
        # 提取向量嵌入相关配置
        for config in configs:
            if config["key"] == "embedding_api_key":
                embedding_config["api_key"] = config["value"]
            elif config["key"] == "embedding_api_url":
                embedding_config["api_url"] = config["value"]
            elif config["key"] == "embedding_model":
                embedding_config["model"] = config["value"]
        
        # 确保所有必要的配置都存在
        if not all(k in embedding_config for k in ["api_key", "api_url", "model"]):
            # 如果缺少某些配置，使用默认值
            if "api_key" not in embedding_config:
                embedding_config["api_key"] = "02fb5cc3-e828-436e-a1b6-c114916c15c6"
            if "api_url" not in embedding_config:
                embedding_config["api_url"] = "https://ark.cn-beijing.volces.com/api/v3/embeddings"
            if "model" not in embedding_config:
                embedding_config["model"] = "doubao-embedding-text-240715"
        
        return embedding_config
    except Exception as e:
        # 出错时返回默认配置
        print(f"获取向量嵌入配置失败，使用默认配置: {str(e)}")
        return {
            "api_key": "02fb5cc3-e828-436e-a1b6-c114916c15c6",
            "api_url": "https://ark.cn-beijing.volces.com/api/v3/embeddings",
            "model": "doubao-embedding-text-240715"
        }