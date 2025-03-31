import json
from typing import Dict, List, Any, Optional, Union
from services.db_service import execute_query, DatabaseError
from services.logger import broadcast_log
from services.tool_registry import ToolRegistry
import sqlite3
from config.constants import METADATA_DB_PATH


class SQLTools:
    """SQL工具类，封装所有与SQL相关的工具函数"""
    
    @staticmethod
    @ToolRegistry.register(
        description="执行SQL查询并返回前10条结果，通常用来验证SQL使用，根据执行结果观察语法是否有问题，是否能查出结果，查不出则需要跟用户确认需求"
    )
    def tool_execute_sql_and_fetch_top_10(sql: str) -> str:
        """执行SQL查询并返回最多10条数据
        
        Args:
            sql: 要执行的SQL查询语句
            
        Returns:
            str: JSON格式的字符串，包含执行结果或错误信息
        """
        try:
            # 执行查询
            result = execute_query('data', sql)
            # 限制结果最多10条
            result = result[:10]

            # 获取列名和类型
            columns = []
            if result and len(result) > 0:
                first_row = result[0]
                for col_name in first_row.keys():
                    # 简单推断类型
                    col_type = SQLTools._infer_column_type(first_row[col_name])
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

            return json.dumps({
                "success": True,
                "columns": columns,
                "data": data,
                "totalRows": len(result)
            }, ensure_ascii=False)
        
        except DatabaseError as e:
            # 处理数据库错误
            error_message = str(e)
            
            return json.dumps({
                "success": False,
                "error": error_message
            }, ensure_ascii=False)
    
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
            return "REAL"
        elif isinstance(value, bool):
            return "BOOLEAN"
        else:
            return "TEXT"
    
    @staticmethod
    @ToolRegistry.register(
        description="获取指定表的结构信息"
    )
    def tool_get_table_schema(table_name: str) -> str:
        """获取表结构
        
        Args:
            table_name: 表名
            
        Returns:
            str: 表的DDL字符串，包括字段、类型、备注等信息
        """
        try:
            # 获取表结构
            schema_sql = f"PRAGMA table_info({table_name})"
            columns = execute_query('data', schema_sql)
            
            if not columns:
                # 返回错误信息字符串
                return f"-- 错误: 表 {table_name} 不存在或没有列信息"
            
            # 从metadata数据库中获取表信息
            # 查找表ID
            table_rows = execute_query('metadata', 'SELECT id FROM tables_view WHERE name = ?', (table_name,))
            table_id = table_rows[0]['id'] if table_rows else None
            
            # 获取表的描述信息
            table_desc = ""
            table_type = ""
            if table_id:
                table_info = execute_query('metadata', 'SELECT description, type FROM tables_view WHERE id = ?', (table_id,))
                if table_info:
                    table_desc = table_info[0]['description'] or ""
                    table_type = table_info[0]['type'] or ""
            
            # 获取列的描述信息和类型信息
            column_descriptions = {}
            column_types = {}
            column_enum_values = {}
            if table_id:
                column_desc_rows = execute_query('metadata', 'SELECT name, description, type FROM columns_view WHERE table_id = ?', (table_id,))
                for row in column_desc_rows:
                    column_descriptions[row['name']] = row['description'] or ""
                    column_types[row['name']] = row['type'] or ""
                    
                    # 如果是ENUM类型，获取枚举值及其描述
                    if row['type'] == "ENUM":
                        column_info = execute_query('metadata', 'SELECT id FROM columns_view WHERE table_id = ? AND name = ?', (table_id, row['name']))
                        if column_info:
                            enum_values = execute_query('metadata', 'SELECT value, description FROM enum_values_view WHERE column_id = ?', (column_info[0]['id'],))
                            if enum_values:
                                column_enum_values[row['name']] = [(val['value'], val['description']) for val in enum_values]
            
            # 格式化列信息
            formatted_columns = []
            for col in columns:
                formatted_columns.append({
                    "name": col["name"],
                    "type": col["type"],
                    "notnull": col["notnull"] == 1,
                    "default": col["dflt_value"],
                    "pk": col["pk"] == 1,
                    "description": column_descriptions.get(col["name"], "")
                })
            
            # 生成DDL
            ddl = f"CREATE TABLE {table_name} (\n"
            for i, col in enumerate(formatted_columns):
                col_name = col['name']
                col_type = col['type']
                
                # 处理ENUM类型
                if column_types.get(col_name) == "ENUM" and col_name in column_enum_values:
                    enum_values = column_enum_values[col_name]
                    if enum_values:
                        # 构建ENUM类型字符串，例如：ENUM('unverified', 'verified', 'enterprise')
                        values_str = ", ".join([f"'{val[0]}'" for val in enum_values])
                        col_type = f"ENUM({values_str})"
                        
                        # 添加枚举值描述到列描述中
                        if col["description"] and enum_values:
                            enum_descriptions = []
                            for val in enum_values:
                                if val[1]:  # 如果有描述
                                    enum_descriptions.append(f"{val[0]}: {val[1]}")
                            
                            if enum_descriptions:
                                col["description"] += f" [{', '.join(enum_descriptions)}]"
                
                ddl += f"    {col_name} {col_type}"
                if col["pk"]:
                    ddl += " PRIMARY KEY"
                if col["notnull"]:
                    ddl += " NOT NULL"
                if col["default"] is not None:
                    ddl += f" DEFAULT {col['default']}"
                
                # 添加列描述
                if col["description"]:
                    # 转义单引号，避免SQL语法错误
                    col_desc = col["description"].replace("'", "''")
                    ddl += f" COMMENT '{col_desc}'"
                
                if i < len(formatted_columns) - 1:
                    ddl += ",\n"
                else:
                    ddl += "\n"
            
            ddl += ")"
            
            # 添加表注释
            comment_parts = []
            if table_desc:
                comment_parts.append(table_desc)
            
            if table_type:
                type_desc = ""
                if table_type == "fact":
                    type_desc = "行为实时表，dt字段代表行为发生的日期"
                elif table_type == "dim":
                    type_desc = "维度表，一般不会发生变化"
                elif table_type == "dim_dt":
                    type_desc = "有日期分区的维度表，dt代表当日更新了全量的维度信息"
                
                if type_desc:
                    comment_parts.append(f"类型: {table_type} ({type_desc})")
            
            if comment_parts:
                # 转义单引号，避免SQL语法错误
                full_comment = " | ".join(comment_parts).replace("'", "''")
                ddl += f" COMMENT = '{full_comment}'"
            
            ddl += ";"
            
            # 返回DDL字符串
            return ddl
        
        except DatabaseError as e:
            # 返回错误信息字符串
            return f"-- 错误: {str(e)}"
    
    @staticmethod
    @ToolRegistry.register(
        description="获取所有表及其描述信息"
    )
    def tool_get_all_tables() -> str:
        """获取所有表及其描述信息
        
        Returns:
            str: 包含所有表名和描述的字符串，不同表用换行符分隔
        """
        try:
            # 获取所有表
            tables_sql = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            tables = execute_query('data', tables_sql)
            
            if not tables:
                return ""
            
            # 获取每个表的描述信息
            conn = sqlite3.connect(METADATA_DB_PATH)
            cursor = conn.cursor()
            
            result = []
            for table in tables:
                table_name = table["name"]
                
                # 查找表描述
                cursor.execute('SELECT description FROM tables_view WHERE name = ?', (table_name,))
                table_desc = cursor.fetchone()
                desc = table_desc[0] if table_desc else ""
                
                result.append(f"{table_name}: {desc}")
            
            cursor.close()
            conn.close()
            
            return "\n".join(result)
        
        except DatabaseError as e:
            # 返回错误信息字符串
            return f"-- 错误: {str(e)}"

    @staticmethod
    @ToolRegistry.register(
        description="根据用户反馈更新元数据描述信息，包括表、字段和枚举值的描述。"
    )
    def tool_update_metadata_description(table_name: str, column_name: Optional[str] = None, enum_value: Optional[str] = None, description: str = "") -> str:
        """根据用户反馈更新元数据描述信息
        
        Args:
            table_name: 表名
            column_name: 字段名（可选）
            enum_value: 枚举值（可选，仅当更新枚举值描述时需要）
            description: 新的描述信息
            
        Returns:
            str: 更新结果信息
        """
        try:
            conn = sqlite3.connect(METADATA_DB_PATH)
            cursor = conn.cursor()
            
            # 根据参数决定更新类型
            if column_name is None or column_name is "":
                # 更新表描述
                cursor.execute('INSERT OR REPLACE INTO user_tables (table_name, description) VALUES (?, ?)',
                             (table_name, description))
                message = f"已更新表 {table_name} 的描述信息"
            elif enum_value is None or enum_value is "":
                # 更新字段描述
                cursor.execute('INSERT OR REPLACE INTO user_columns (table_name, column_name, description) VALUES (?, ?, ?)',
                             (table_name, column_name, description))
                message = f"已更新表 {table_name} 的字段 {column_name} 的描述信息"
            else:
                # 更新枚举值描述
                cursor.execute('INSERT OR REPLACE INTO user_enum_values (table_name, column_name, enum_value, description) VALUES (?, ?, ?, ?)',
                             (table_name, column_name, enum_value, description))
                message = f"已更新表 {table_name} 的字段 {column_name} 的枚举值 {enum_value} 的描述信息"
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return json.dumps({
                "success": True,
                "message": message
            }, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e)
            }, ensure_ascii=False)
    
    @staticmethod
    @ToolRegistry.register(
        description="根据用户反馈更新freeshot和term数据的点赞数，在用户点赞时被调用。"
    )
    def tool_update_business_term(term_type: str, term_name: str) -> str:
        """
        根据用户反馈更新freeshot或term数据的点赞数
        
        Args:
            term_type: 类型，可选值为 'freeshot' 或 'term'
            term_name: 术语名称或自由查询示例名称
            
        Returns:
            str: 更新结果信息
        """
        try:
            if term_type not in ['freeshot', 'term']:
                return json.dumps({
                    "success": False,
                    "error": "类型必须为 'freeshot' 或 'term'"
                }, ensure_ascii=False)
            
            conn = sqlite3.connect(METADATA_DB_PATH)
            cursor = conn.cursor()
            
            # 根据类型决定更新哪个表
            if term_type == 'freeshot':
                table_name = 'freeshots'
            else:  # term
                table_name = 'terms'
            
            # 查询当前点赞数
            cursor.execute(f'SELECT id, likes FROM {table_name} WHERE name = ?', (term_name,))
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return json.dumps({
                    "success": False,
                    "error": f"未找到名为 {term_name} 的{('自由查询示例' if term_type == 'freeshot' else '业务术语')}"
                }, ensure_ascii=False)
            
            term_id, likes = row
            
            # 更新点赞数
            new_likes = likes + 1
            cursor.execute(f'UPDATE {table_name} SET likes = ? WHERE id = ?', (new_likes, term_id))
            
            conn.commit()
            conn.close()
            
            return json.dumps({
                "success": True,
                "message": f"已更新{('自由查询示例' if term_type == 'freeshot' else '业务术语')} {term_name} 的点赞数为 {new_likes}"
            }, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e)
            }, ensure_ascii=False)