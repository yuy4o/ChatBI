import json
from typing import Dict, List, Any, Optional, Union
from services.db_service import execute_query, DatabaseError
from services.logger import broadcast_log


class SQLExecutor:
    """SQL执行器类，封装SQL执行相关的逻辑"""
    
    @staticmethod
    def execute_sql(sql: str, limit: int = None) -> Dict:
        """执行SQL查询并返回结果
        
        Args:
            sql: 要执行的SQL查询语句
            limit: 限制返回的结果数量，默认为None表示不限制
            
        Returns:
            Dict: 包含执行结果或错误信息的字典
        """
        try:
            # 广播日志
            broadcast_log('system', sql, "正在执行SQL")
            
            # 执行查询
            result = execute_query('data', sql)
            
            # 如果是SELECT查询，格式化结果
            if sql.strip().upper().startswith(('SELECT', 'WITH')):
                # 如果指定了limit，限制结果数量
                if limit is not None:
                    result = result[:limit]
                
                # 获取列名和类型
                columns = []
                if result and len(result) > 0:
                    first_row = result[0]
                    for col_name in first_row.keys():
                        # 简单推断类型
                        col_type = SQLExecutor._infer_column_type(first_row[col_name])
                        columns.append({
                            "name": col_name,
                            "type": col_type,
                            "nullable": True  # 默认可为空
                        })
                
                # 转换数据为二维数组
                data = []
                for row in result:
                    data_row = [row[col["name"]] for col in columns]
                    data.append(data_row)
                broadcast_log('system', json.dumps(data), "执行SQL成功")
                return {
                    "success": True,
                    "columns": columns,
                    "data": data,
                    "totalRows": len(result)
                }
            else:
                # 非SELECT查询，返回影响的行数
                return {
                    "success": True,
                    "affectedRows": result if isinstance(result, int) else 0,
                    "message": f"查询执行成功，影响了 {result if isinstance(result, int) else 0} 行数据"
                }
        
        except DatabaseError as e:
            # 处理数据库错误
            error_message = str(e)
            broadcast_log('system', error_message, "SQL执行错误")
            
            return {
                "success": False,
                "error": error_message,
                "message": "SQL执行错误"
            }
    
    @staticmethod
    def _infer_column_type(value: Any) -> str:
        """根据值推断列类型
        
        Args:
            value: 列值
            
        Returns:
            str: 推断的类型名称
        """
        if value is None:
            return "NULL"
        elif isinstance(value, int):
            return "INTEGER"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, bool):
            return "BOOLEAN"
        else:
            return "TEXT"
    
    @staticmethod
    def execute_sql_and_return_json(sql: str, limit: int = 10) -> str:
        """执行SQL查询并返回JSON格式的结果
        
        Args:
            sql: 要执行的SQL查询语句
            limit: 限制返回的结果数量，默认为10
            
        Returns:
            str: JSON格式的字符串，包含执行结果或错误信息
        """
        result = SQLExecutor.execute_sql(sql, limit)
        return json.dumps(result, ensure_ascii=False)