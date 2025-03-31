import json
import traceback
from typing import Dict, List, Any, Optional, Union
from services.logger import broadcast_log,broadcast_stream_log
from services.llm_service import get_client
from services.llm_config import get_model
from services.prompt_manager import PromptManager
from services.tool_registry import ToolRegistry
from services.sql_tools import SQLTools


class FeedbackAgent:
    """处理用户反馈的智能体，根据用户点赞和历史对话更新元数据描述"""
    
    def __init__(self, ddl: List = None, freeshot: List = None, term: List = None, messages: List = None):
        """初始化FeedbackAgent
        
        Args:
            ddl: 数据库定义信息
            freeshot: 相似查询示例
            term: 术语解释
            messages: 历史对话消息
        """
        self.ddl = ddl or []
        self.freeshot = freeshot or []
        self.term = term or []
        self.messages = messages or []
        
        # 初始化系统消息
        self._init_messages()
    
    def _init_messages(self):
        """初始化消息列表，添加系统提示和历史消息"""

        # 添加元数据信息（ddl、freeshot、term）
        metadata_parts = []
        
        # 添加数据库定义
        if self.ddl and len(self.ddl) > 0:
            ddls = []
            for item in self.ddl:
                ddls.append(f"表名: {item['name']}\n{item['content']}")
            if ddls:
                metadata_parts.append("## 数据库定义\n" + "\n\n".join(ddls) + "\n")
        
        # 添加相似查询示例
        if self.freeshot and len(self.freeshot) > 0:
            examples = []
            for item in self.freeshot:
                examples.append(f"查询: {item['name']}\nSQL: {item['content']}")
            
            if examples:
                metadata_parts.append("## 相似查询示例\n" + "\n\n".join(examples) + "\n")
        
        # 添加术语解释
        if self.term and len(self.term) > 0:
            terms = []
            for item in self.term:
                terms.append(f"{item['name']}: {item['content']}")
            
            if terms:
                metadata_parts.append("## 术语解释\n" + "\n".join(terms) + "\n")

        metadata_content = ""
        # 如果有元数据，添加到系统消息中
        if metadata_parts:
            metadata_content += "\n\n" + "\n\n".join(metadata_parts)

        system_content = PromptManager.build_feedback_agent_prompt(metadata_content)
        broadcast_log("ai", "", "FeedbackAgent-构建Agent角色提示词")
        
        # 添加系统提示
        self.messages.insert(0, {
            "role": "system",
            "content": system_content
        })
    
    def _add_user_message(self, content: str):
        """添加用户消息"""
        self.messages.append({"role": "user", "content": content})
    
    def _add_assistant_message(self, content: str):
        """添加助手消息"""
        self.messages.append({"role": "assistant", "content": content})
    
    def _add_function_message(self, name: str, content: str, tool_call_id: str = None):
        """添加函数调用结果消息
        
        Args:
            name: 函数名称
            content: 函数返回内容
            tool_call_id: 工具调用ID，用于关联请求和响应
        """
        message = {
            "role": "tool",
            "name": name,
            "content": content
        }
        
        # 如果提供了tool_call_id，则添加到消息中
        if tool_call_id:
            message["tool_call_id"] = tool_call_id
            
        self.messages.append(message)
    
    def process_feedback(self) -> Dict:
        """处理用户点赞反馈，分析历史对话并更新元数据描述
        
        Returns:
            Dict: 包含处理结果的字典
        """
        try:
            # 获取注册的工具函数
            functions = ToolRegistry.get_tools_by_names(["tool_update_metadata_description", "tool_update_business_term"])
            
            # 调用API
            client = get_client()
            broadcast_log("ai", "", "FeedbackAgent-分析用户反馈中...")
            
            # 设置最大轮次，防止无限循环
            max_turns = 5
            current_turn = 0
            final_response = None
            update_results = []
            
            while current_turn < max_turns:
                current_turn += 1
                
                # 调用模型（流式输出）
                stream = client.chat.completions.create(
                    model=get_model(),
                    messages=self.messages,
                    tools=[{"type": "function", "function": func} for func in functions],
                    tool_choice="auto",
                    stream=True
                )
                
                # 用于累积完整响应的变量
                collected_message = None
                collected_content = ""
                
                # 处理流式响应
                for chunk in stream:
                    delta = chunk.choices[0].delta
                    
                    # 如果是第一个包含消息的块，初始化message对象
                    if not collected_message and hasattr(delta, 'role'):
                        collected_message = delta
                    
                    # 累积内容
                    if hasattr(delta, 'content') and delta.content:
                        collected_content += delta.content
                        # 实时广播每个token（使用流式日志）
                        broadcast_stream_log("ai", delta.content, f"FeedbackAgent-R{current_turn}:流式输出", is_first=(len(collected_content) == len(delta.content)))
                    
                    # 处理工具调用
                    try:
                        if hasattr(delta, 'tool_calls') and delta.tool_calls and hasattr(delta.tool_calls, '__iter__'):
                            # 确保collected_message有tool_calls属性
                            if not hasattr(collected_message, 'tool_calls'):
                                collected_message.tool_calls = []
                            
                            for tool_call in delta.tool_calls:
                                # 确保collected_message.tool_calls不为None
                                if collected_message.tool_calls is None:
                                    collected_message.tool_calls = []
                                
                                # 查找或创建对应的工具调用
                                existing_call = next((t for t in collected_message.tool_calls if t.index == tool_call.index), None)
                                if not existing_call:
                                    collected_message.tool_calls.append(tool_call)
                                else:
                                    # 更新现有工具调用
                                    if hasattr(tool_call, 'function'):
                                        if not hasattr(existing_call, 'function'):
                                            existing_call.function = tool_call.function
                                        else:
                                            if hasattr(tool_call.function, 'name') and tool_call.function.name:
                                                existing_call.function.name = tool_call.function.name
                                            if hasattr(tool_call.function, 'arguments'):
                                                if not hasattr(existing_call.function, 'arguments'):
                                                    existing_call.function.arguments = tool_call.function.arguments
                                                else:
                                                    existing_call.function.arguments += tool_call.function.arguments
                    except Exception as e:
                        # 打印完整的堆栈跟踪
                        print(f"Error processing tool calls: {str(e)}")
                        traceback.print_exc()
                
                # 设置最终消息
                message = collected_message
                if collected_content:
                    message.content = collected_content
                    broadcast_log("ai", collected_content, f"FeedbackAgent-R{current_turn}:完整响应")
                
                # 检查是否有工具调用
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    # 处理工具调用
                    tool_name = message.tool_calls[0].function.name if hasattr(message.tool_calls[0], 'function') and hasattr(message.tool_calls[0].function, 'name') else ""
                    tool_args = message.tool_calls[0].function.arguments if hasattr(message.tool_calls[0], 'function') and hasattr(message.tool_calls[0].function, 'arguments') else ""
                    tool_message = (f"调用工具-{tool_name}-参数-{tool_args}")
                    self._add_assistant_message(tool_message)
                    
                    for tool_call in message.tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)
                        
                        # 执行函数
                        if function_name == "tool_update_metadata_description":
                            table_name = function_args.get("table_name", "")
                            column_name = function_args.get("column_name", "")
                            enum_value = function_args.get("enum_value", "")
                            description = function_args.get("description", "")
                            result = SQLTools.tool_update_metadata_description(table_name, column_name, enum_value, description)
                            # 添加函数结果消息
                            broadcast_log("ai", result, f"FeedbackAgent-R{current_turn}:已更新表信息")
                            self._add_function_message(function_name, result, tool_call.id)
                            
                            # 记录更新结果
                            try:
                                result_json = json.loads(result)
                                if result_json.get("success"):
                                    update_results.append({
                                        "table_name": table_name,
                                        "column_name": column_name,
                                        "enum_value": enum_value,
                                        "description": description,
                                        "message": result_json.get("message")
                                    })
                            except:
                                pass
                        elif function_name == "tool_update_business_term":
                            term_type = function_args.get("term_type", "")
                            term_name = function_args.get("term_name", "")
                            result = SQLTools.tool_update_business_term(term_type, term_name)
                            # 添加函数结果消息
                            broadcast_log("ai", result, f"FeedbackAgent-R{current_turn}:已更新{term_type}点赞数")
                            self._add_function_message(function_name, result, tool_call.id)
                            
                            # 记录更新结果
                            try:
                                result_json = json.loads(result)
                                if result_json.get("success"):
                                    update_results.append({
                                        "term_type": term_type,
                                        "term_name": term_name,
                                        "message": result_json.get("message")
                                    })
                            except:
                                pass
                        
                else:
                    # 没有工具调用，处理完成
                    broadcast_log("ai", message.content, "FeedbackAgent-分析完成")
                    final_response = message.content
                    self._add_assistant_message(final_response)
                    break
            
            # 返回结果
            return {
                "content": final_response or "已根据用户反馈更新元数据描述",
                "updates": update_results
            }
        
        except Exception as e:
            # 发生错误时返回错误信息并打印堆栈跟踪
            print(f"Error in FeedbackAgent: {str(e)}")
            traceback.print_exc()
            return {
                "content": f"处理反馈过程中发生错误: {str(e)}",
                "updates": [],
                "error": str(e)
            }


def process_feedback_good(ddl: List = None, freeshot: List = None, term: List = None, messages: List = None) -> Dict:
    """处理用户点赞反馈，分析历史对话并更新元数据描述
    
    Args:
        ddl: 数据库定义信息
        freeshot: 相似查询示例
        term: 术语解释
        messages: 历史对话消息
        
    Returns:
        Dict: 包含处理结果的字典
    """
    # 创建FeedbackAgent实例
    agent = FeedbackAgent(ddl, freeshot, term, messages)
    
    # 处理反馈并返回结果
    return agent.process_feedback()