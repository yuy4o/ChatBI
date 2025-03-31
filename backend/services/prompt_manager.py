import os

class PromptManager:
    """
    Centralized manager for all LLM prompt templates
    """
    @staticmethod
    def build_sql_prompt(query, ddl=None, freeshot=None, term=None):
        """
        Build prompt for SQL generation
        """
        prompt_parts = []
        
        # Add user query
        prompt_parts.append(f"## 用户查询\n{query}\n")
        
        # Add database definition
        if ddl and len(ddl) > 0:
            ddls = []
            for item in ddl:
                ddls.append(f"表名: {item['name']}\n{item['content']}")
            if ddls:
                prompt_parts.append("## 数据库定义\n" + "\n\n".join(ddls) + "\n")
        
        # Add similar query examples
        if freeshot and len(freeshot) > 0:
            examples = []
            for item in freeshot:
                examples.append(f"查询: {item['name']}\nSQL: {item['content']}")
            
            if examples:
                prompt_parts.append("## 相似查询示例\n" + "\n\n".join(examples) + "\n")
        
        # Add term explanations
        if term and len(term) > 0:
            terms = []
            for item in term:
                terms.append(f"{item['name']}: {item['content']}")
            
            if terms:
                prompt_parts.append("## 术语解释\n" + "\n".join(terms) + "\n")
        
        # Add task instructions
        prompt_parts.append("""## 任务
请根据上述信息，生成一个可执行的SQL查询语句。请先分析用户需求，然后生成SQL。

请按以下格式回复：

SQL：
```sql
（在这里生成SQL语句）
```""")
        
        return "\n\n".join(prompt_parts)
    
    @staticmethod
    def build_table_select_prompt(query, ddl_list):
        """
        Build prompt for table selection
        """
        prompt_parts = []
        
        # Add user query
        prompt_parts.append(f"## 用户查询\n{query}\n")
        
        # Add database table info
        if ddl_list and len(ddl_list) > 0:
            tables_info = []
            for item in ddl_list:
                table_info = f"表名: {item['table_name']}\n"
                if item['table_desc']:
                    table_info += f"描述: {item['table_desc']}\n"
                table_info += f"DDL: {item['ddl']}"
                tables_info.append(table_info)
            
            prompt_parts.append("## 数据库表信息\n" + "\n\n".join(tables_info) + "\n")
        
        # Add task instructions
        prompt_parts.append("""## 任务
请根据用户查询，从上述数据库表中选择与查询相关的表。

请直接返回相关表名列表，每行一个表名，不要有其他内容。例如：
table1
table2
table3""")
        
        return "\n\n".join(prompt_parts)
    
    @staticmethod
    def build_sql_agent_prompt(metadata_content):
        """
        Build prompt for SQL Agent with ReAct paradigm
        """
        from datetime import datetime
        
        prompt_parts = []

        system_role = "你是一个专业的SQL助手，能够根据用户需求生成SQL查询并执行。你可以分析SQL执行结果，处理错误并自动修正。"
        prompt_parts.append(f"## 系统角色\n{system_role}\n")
        
        # Add current time information
        now = datetime.now()
        prompt_parts.append(f"## 附加信息\n今天日期{now.strftime('%Y-%m-%d %A')} 当前时间{now.strftime('%H:%M')}\n")
        
        # Add user query
        prompt_parts.append(f"## 元数据信息（注意，以下是部分表的部分字段信息，枚举值也是其部分枚举值）\n{metadata_content}\n")
        
        # Add task instructions for ReAct paradigm
        prompt_parts.append("""## 任务
请根据上述信息，帮助用户解决查询需求。你可以：

1. 生成并执行SQL查询语句
2. 分析执行结果
3. 如果SQL执行出错，分析错误并修正
4. 如果需要更多表信息，可以获取表结构或查询所有可用表
5. 如果用户需求不清晰，询问用户更多信息

注意：
1. 如果要使用tools，请简单解释下为什么需要使用tools
2. SQL语法请遵循Sqlite3语法
3. 如果发现元数据不能满足用户需求，请向用户说明，寻求用户提供更多信息
4. 尽可能一次查询就能解决用户问题，如果问题较为复杂可以使用多次子查询
5. 使用with as语句用来增加复杂sql的可读性
6. 不要sql中加入--备注
7. 当前DDL语句中的信息，包括表、字段、枚举值都是根据用户问题搜索到的，只是其中一部分，如果不能满足用户需求，需要拿到完整的表信息再做判断

请思考用户的真实需求，生成准确的SQL，并确保SQL可以成功执行。如果执行失败，请分析原因并修正。
请先思考用户需求，然后生成SQL并执行。最后，提供一个清晰的回答，包括SQL和执行结果的解释。""")
        return "\n\n".join(prompt_parts)
        
    @staticmethod
    def build_feedback_agent_prompt(metadata_content):
        """
        Build prompt for Feedback Agent to process user's positive feedback
        """
        from datetime import datetime
        
        prompt_parts = []

        system_role = "你是一个专业的元数据管理助手，能够根据用户的反馈和历史对话，分析并更新数据库元数据的描述信息、业务术语和查询示例。"
        prompt_parts.append(f"## 系统角色\n{system_role}\n")
        
        # Add current time information
        now = datetime.now()
        prompt_parts.append(f"## 附加信息\n今天日期{now.strftime('%Y-%m-%d %A')} 当前时间{now.strftime('%H:%M')}\n")
        
        # Add metadata information
        prompt_parts.append(f"## 元数据信息（注意，以下是部分表的部分字段信息）\n{metadata_content}\n")
        
        # Add task instructions for feedback processing
        prompt_parts.append("""## 任务
用户对之前的SQL查询结果表示满意并点赞。请分析历史对话内容，特别是用户的查询需求和生成的SQL，找出可能需要更新的元数据描述、业务术语和查询示例。

你需要：

1. 分析用户的原始查询需求，理解用户真正想要查询的内容
2. 分析生成的SQL查询，找出其中使用的表和字段
3. 对比用户需求和SQL中使用的字段，找出那些可能需要更新描述的元数据
4. 使用tool_update_metadata_description工具更新元数据描述
5. 识别用户查询中的业务术语，如果发现有价值的业务术语，使用tool_update_business_term工具更新（term_type设为'term'）
6. 分析用户查询和生成的SQL之间的关系，如果这是一个有代表性的查询示例，使用tool_update_business_term工具更新（term_type设为'freeshot'）

例如：
- 如果用户查询"最近3天的播放时长"，而SQL中使用了duration字段，但该字段没有描述，你可以将其描述更新为"播放时长"
- 如果用户查询"高评分的视频"，而SQL中使用了rating字段，你可以将其描述更新为"视频评分"
- 如果用户查询中出现"DAU"这样的业务术语，你可以使用tool_update_business_term更新该术语的点赞数
- 如果用户的查询和生成的SQL构成了一个很好的查询示例，你可以使用tool_update_business_term更新该示例的点赞数

注意：
1. 只更新那些确实需要更新的元数据，不要过度更新
2. 描述应该简洁明了，反映字段的实际含义
3. 业务术语应该是在领域内有特定含义的词汇，如"DAU"、"留存率"等
4. 有价值的查询示例应该具有代表性，能够帮助理解常见的业务查询模式

请思考用户的真实需求和SQL的实际使用情况，提供准确的元数据、术语和查询示例更新。""")
        
        return "\n\n".join(prompt_parts)