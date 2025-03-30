from services.llm_service import generate_sql

def generate_sql_from_query(query, ddl=None, freeshot=None, term=None):
    """
    根据用户查询和相关信息生成SQL查询语句
    """
    # 调用LLM服务生成SQL
    result = generate_sql(query, ddl, freeshot, term)
    
    # 返回结果
    return result