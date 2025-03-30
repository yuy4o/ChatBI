
from services.logger import broadcast_log
from services.llm_config import get_client, get_model
from services.prompt_manager import PromptManager

# 构建表选择提示词
def build_table_select_prompt(query, ddl_list):
    """
    构建发送给大模型的表选择提示词
    
    Args:
        query (str): 用户查询
        ddl_list (list): 数据库定义语句列表，格式为[{"table_name": "", "table_desc": "", "ddl":"create table xxx"}]
    
    Returns:
        str: 完整的提示词
    """
    return PromptManager.build_table_select_prompt(query, ddl_list)

# 解析表选择API响应
def parse_table_response(response):
    """
    解析大模型API的表选择响应
    
    Args:
        response: API响应对象
    
    Returns:
        list: 表名列表
    """
    # 获取响应内容
    content = response.choices[0].message.content
    broadcast_log("ai", content, "筛选数据表-推理结束")
    
    # 按行分割并清理空行和空格
    lines = content.strip().split('\n')
    table_names = [line.strip() for line in lines if line.strip()]
    
    # 过滤掉可能的非表名行（如标题、解释等）
    filtered_table_names = []
    for name in table_names:
        # 跳过可能的标题行或解释行
        if name.startswith('#') or ':' in name or '表名' in name or '相关表' in name:
            continue
        filtered_table_names.append(name)
    
    return filtered_table_names

def get_tables_from_suggest(query, ddl_list):
    """
    根据用户问题，从向量数据库搜索出来的元数据中，找到跟用户问题相关的一个或多个表，ddl_list为[{"table_name": "", "table_desc": "", "ddl":"create table xxx"}]
    返回新的ddl_list，但只返回相关的ddl_list
    """
    try:
        # 构建提示词
        prompt = build_table_select_prompt(query, ddl_list)
        broadcast_log("ai", prompt, "筛选数据表-已构建提示词")
        broadcast_log("ai", prompt, "筛选数据表-推理中...")
        # 调用API
        client = get_client()
        response = client.chat.completions.create(
            model=get_model(),
            messages=[
                {"role": "system", "content": "你是一个专业的数据分析助手，根据用户的查询需求选择相关的数据表。"}, 
                {"role": "user", "content": prompt}
            ]
        )
        
        # 解析响应
        table_names = parse_table_response(response)
        
        # 根据表名过滤DDL列表
        filtered_ddl_list = []
        for item in ddl_list:
            if item["table_name"] in table_names:
                filtered_ddl_list.append(item)
        
        # 如果没有找到相关表，返回原始列表
        if not filtered_ddl_list:
            return ddl_list
            
        return filtered_ddl_list
        
    except Exception as e:
        # 发生错误时返回原始列表
        print(f"Error calling LLM API for table selection: {str(e)}")
        return ddl_list