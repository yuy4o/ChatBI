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
        print(f"加载配置文件失败: {str(e)}")

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
        return llm_config
    except Exception as e:
        # 出错时返回默认配置
        print(f"获取LLM配置失败: {str(e)}")

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

        
        return embedding_config
    except Exception as e:
        # 出错时返回默认配置
        print(f"获取向量嵌入配置失败: {str(e)}")
