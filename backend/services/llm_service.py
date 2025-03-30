import time
from services.logger import broadcast_log
from services.llm_config import get_client, get_model
from services.prompt_manager import PromptManager

# 调用大模型API生成SQL
def generate_sql(query, ddl=None, freeshot=None, term=None):
    """
    调用大模型API生成SQL
    """
    try:
        # 构建提示词
        prompt = build_prompt(query, ddl, freeshot, term)
        broadcast_log("ai", prompt, "生成SQL-已构建提示词")
        broadcast_log("ai", prompt, "生成SQL-推理中...")
        
        # 调用API
        client = get_client()
        response = client.chat.completions.create(
            model=get_model(),
            messages=[
                {"role": "system", "content": "你是一个专业的SQL生成助手，根据用户的需求和提供的数据库信息生成准确的SQL查询语句。"},
                {"role": "user", "content": prompt}
            ]
        )
        
        # 解析响应
        result = parse_response(response)
        return result
    
    except Exception as e:
        # 发生错误时返回错误信息
        print(f"Error calling LLM API: {str(e)}")
        return {
            "thought": f"调用大模型API时发生错误: {str(e)}",
            "sql": ""
        }

# 构建提示词
def build_prompt(query, ddl=None, freeshot=None, term=None):
    """
    构建发送给大模型的提示词
    """
    return PromptManager.build_sql_prompt(query, ddl, freeshot, term)

# 解析API响应
def parse_response(response):
    """
    解析大模型API的响应
    
    Args:
        response: API响应对象
    
    Returns:
        dict: 包含思考过程和生成的SQL的字典
    """
    # 获取响应内容
    content = response.choices[0].message.content
    
    # 检查是否有推理内容
    reasoning_content = ""
    if hasattr(response.choices[0].message, 'reasoning_content'):
        reasoning_content = response.choices[0].message.reasoning_content
    
    # 解析思考过程和SQL
    thought = ""
    sql = ""
    broadcast_log("ai", reasoning_content, "生成SQL-推理过程")
    
    # 如果有推理内容，优先使用推理内容作为思考过程
    thought = reasoning_content
    
    # 从内容中提取SQL
    if "```sql" in content:
        sql_parts = content.split("```sql", 1)
        if len(sql_parts) > 1:
            sql_code = sql_parts[1].split("```", 1)[0].strip()
            sql = sql_code
    elif "SQL：" in content:
        sql_parts = content.split("SQL：", 1)
        if len(sql_parts) > 1:
            sql = sql_parts[1].strip()

    broadcast_log("ai", sql, "生成SQL-推理结束")
    
    # 如果没有提取到思考过程，使用整个内容
    if not thought:
        thought = content
    
    return {
        "thought": thought,
        "sql": sql
    }