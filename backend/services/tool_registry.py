from functools import wraps
from typing import Dict, List, Any, Optional, Callable
from inspect import signature, Parameter

class ToolRegistry:
    """工具注册器类，用于管理和注册工具函数"""
    
    _instance = None
    _tools: Dict[str, Dict] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def register(cls, name: Optional[str] = None, description: Optional[str] = None):
        """装饰器，用于注册工具函数
        
        Args:
            name: 工具名称，如果不提供则使用函数名
            description: 工具描述
        """
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            
            # 获取函数名称
            tool_name = name or func.__name__
            
            # 获取函数签名
            sig = signature(func)
            parameters = {}
            required = []
            
            # 解析函数参数
            for param_name, param in sig.parameters.items():
                param_type = param.annotation if param.annotation != Parameter.empty else 'string'
                param_type = str(param_type).split("'")[1] if "'" in str(param_type) else 'string'
                
                parameters[param_name] = {
                    'type': param_type.lower(),
                    'description': ''
                }
                
                # 如果参数没有默认值且不是self，则为必需参数
                if param.default == Parameter.empty and param_name != 'self':
                    required.append(param_name)
            
            # 注册工具
            cls._tools[tool_name] = {
                'name': tool_name,
                'description': description or func.__doc__ or '',
                'parameters': {
                    'type': 'object',
                    'properties': parameters,
                    'required': required
                }
            }
            
            return wrapper
        return decorator
    
    @classmethod
    def get_tools(cls) -> List[Dict[str, Any]]:
        """获取所有注册的工具"""
        return list(cls._tools.values())

    @classmethod
    def get_tools_by_names(cls, names: List[str]) -> List[Dict[str, Any]]:
        """根据名称列表获取注册的工具"""
        return [cls._tools[name] for name in names if name in cls._tools]
    
    @classmethod
    def clear(cls):
        """清除所有注册的工具"""
        cls._tools.clear()