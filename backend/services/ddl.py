from services.logger import broadcast_log
def generate_ddl_from_schema(schema_data):
    """
    从API请求中的schema数据生成CREATE TABLE DDL语句，包含列描述和ENUM值描述作为注释
    同时从数据库中获取主键字段和dt字段（如果存在）
    
    Args:
        schema_data (dict): 包含数据库和表结构信息的字典
    
    Returns:
        list: 包含表名和DDL语句的字典列表，格式为 [{"table_name": "", "table_desc": "", "ddl":""}]
    """
    from services.db_service import execute_query
    
    result = []
    
    for db in schema_data.get("schema", []):
        db_id = db.get("id")
        for table in db.get("tables", []):
            table_name = table.get("table")
            table_desc = table.get("description", "")
            table_type = table.get("type", "")
            columns = table.get("columns", [])
            
            # 获取表的ID
            table_rows = execute_query('metadata', 'SELECT id FROM tables_view WHERE db_id = ? AND name = ?', (db_id, table_name))
            if not table_rows:
                continue
            table_id = table_rows[0]['id']
            
            # 获取表的所有列，包括主键和dt字段
            db_columns = execute_query('metadata', 'SELECT id, name, type, is_primary, description FROM columns_view WHERE table_id = ?', (table_id,))
            
            # 创建一个集合来存储schema_data中已有的列名
            existing_column_names = {col.get("column") for col in columns}
            
            # 查找主键字段和dt字段
            primary_key_columns = []
            dt_column = None
            for col_row in db_columns:
                col_name = col_row["name"]
                is_primary = col_row["is_primary"]
                
                # 如果是主键且不在现有列中，添加到主键列表
                if is_primary and col_name not in existing_column_names:
                    primary_key_columns.append({
                        "column": col_name,
                        "type": col_row['type'],
                        "description": col_row['description'] or "",
                        "is_primary": True
                    })
                
                # 如果是dt字段且不在现有列中，记录下来
                if col_name == "dt" and col_name not in existing_column_names:
                    dt_column = {
                        "column": "dt",
                        "type": col_row['type'],
                        "description": col_row['description'] or "日期分区字段",
                        "is_primary": False
                    }
            
            # 将主键和dt字段添加到columns列表中
            if primary_key_columns:
                columns = primary_key_columns + columns
            if dt_column:
                columns.append(dt_column)
            
            # 开始构建CREATE TABLE语句
            ddl = f"CREATE TABLE {table_name} (\n"
            
            # 添加列定义
            column_definitions = []
            for col in columns:
                col_name = col.get("column")
                col_type = col.get("type")
                col_desc = col.get("description", "")
                col_is_primary = col.get("is_primary", False)

                
                # 处理ENUM类型
                if col_type == "ENUM":
                    values = [f"'{val['value']}'" for val in col.get("values", [])]
                    if values:
                        col_type = f"ENUM({', '.join(values)})"
                    else:
                        col_type = "VARCHAR(50)"  # 如果没有提供枚举值，使用VARCHAR作为默认
                    
                    # 处理ENUM值的描述
                    enum_values = col.get("values", [])
                    if enum_values and col_desc:
                        # 添加每个ENUM值的描述到列描述中
                        enum_descriptions = []
                        for val in enum_values:
                            if val.get("desc"):
                                enum_descriptions.append(f"{val['value']}: {val['desc']}")
                        
                        if enum_descriptions:
                            col_desc += f" [{', '.join(enum_descriptions)}]"
                
                # 添加列定义、主键标识和注释
                column_def = f"    {col_name} {col_type}"
                
                # 添加主键标识
                if col_is_primary:
                    column_def += " PRIMARY KEY"
                    
                # 添加注释
                if col_desc:
                    # 转义单引号，避免SQL语法错误
                    col_desc = col_desc.replace("'", "''")
                    column_def += f" COMMENT '{col_desc}'"
                    
                column_definitions.append(column_def)
            
            ddl += ",\n".join(column_definitions)
            
            # 添加表注释
            ddl += "\n)"
            
            # 构建表注释，包含表类型信息
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
            
            result.append({"table_name": table_name, "table_desc": table_desc, "ddl": ddl})
    
    return result


def generate_ddl_metadata_from_schema(schema_data):
    """
    将schema数据转换为元数据格式
    
    Args:
        schema_data (dict): 包含数据库和表结构信息的字典
    
    Returns:
        list: 包含表名和DDL语句的元数据列表，格式为 [{"name": "", "content":""}]
    """
    # 先使用generate_ddl_from_schema生成DDL语句
    ddl_list = generate_ddl_from_schema(schema_data)
    from services.llm_table_select_service import get_tables_from_suggest
    # 然后使用get_tables_from_suggest获取相关的DDL语句
    ddl_list = get_tables_from_suggest(schema_data.get("query", []), ddl_list)
    
    # 转换格式
    metadata_list = []
    ddls_content = ""
    for item in ddl_list:
        metadata_list.append({
            "table_name": item["table_name"],
            "name": item["table_desc"],
            "content": item["ddl"]
        })
        ddls_content += item["ddl"] + "\n"
    broadcast_log("system", ddls_content, "已将元数据解析为DDL")
    return metadata_list