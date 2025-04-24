from typing import Annotated, Dict, Any, List, Optional
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import ToolMessage, AIMessage, HumanMessage, BaseMessage
from langchain.tools import Tool
import sys
from pathlib import Path
import asyncio
import json

# 添加项目根目录到Python路径
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from robot.tools import tools
from robot import globals
import logging
import traceback

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 绑定工具到模型
def get_model_with_tools():
    """获取绑定了工具的模型实例"""
    return globals.current_model.bind_tools(tools)

class State(TypedDict):
    """对话状态"""
    messages: Annotated[list[BaseMessage], add_messages]  # 消息历史
    next_step: str  # 下一步操作
    error_info: str | None  # 错误信息
    completed_tools: set[str]  # 已完成的工具集合

class ToolPriority:
    """工具优先级定义"""
    PRIORITIES = {
        "chat_history": 1,
        "generate_personalized_advice": 2,  # 生成个性化建议的优先级应该很高
        "query_food_relations": 3,  # 食材相生相克关系查询
        "query_seasonal_foods": 4,  # 时令食材查询
        "query_therapeutic_foods": 5,  # 功效食材查询
        "retrieve": 6,
        "search": 7,
        "image_parser": 8,
        "save_health_advice": 9  # 保存健康建议应该最后执行
    }

    @staticmethod
    def get_priority(tool_name: str) -> int:
        return ToolPriority.PRIORITIES.get(tool_name, 999)

class ToolDependency:
    """工具依赖关系定义"""
    DEPENDENCIES = {
        # # 个性化建议依赖于对话历史
        # "generate_personalized_advice": ["chat_history"],
        
        # # 知识图谱工具依赖于对话历史和个性化建议
        # "query_food_relations": ["chat_history", "generate_personalized_advice"],
        # "query_seasonal_foods": ["chat_history", "generate_personalized_advice"],
        # "query_therapeutic_foods": ["chat_history", "generate_personalized_advice"],
        
        # # 检索和搜索工具也应该依赖于个性化建议
        # "retrieve": ["generate_personalized_advice"],
        # "search": ["generate_personalized_advice"],
        
        # # 保存健康建议依赖于所有相关工具的执行结果
        # "save_health_advice": [
        #     "chat_history",
        #     "generate_personalized_advice",
        #     "query_food_relations",
        #     "query_seasonal_foods",
        #     "query_therapeutic_foods",
        #     "retrieve"
        # ]
    }

    @staticmethod
    def get_dependencies(tool_name: str) -> List[str]:
        return ToolDependency.DEPENDENCIES.get(tool_name, [])

class ToolResultManager:
    """工具结果管理器"""
    def __init__(self):
        self.results = {}

    def add_result(self, tool_name: str, result: Any):
        """添加工具执行结果"""
        self.results[tool_name] = result

    def get_result(self, tool_name: str) -> Optional[Any]:
        """获取工具执行结果"""
        return self.results.get(tool_name)

    def get_all_results(self) -> Dict[str, Any]:
        """获取所有工具执行结果"""
        return self.results

async def execute_tools(tools: List[Tool], query: str) -> str:
    """执行工具链"""
    result_manager = ToolResultManager()
    
    # 按优先级排序工具
    sorted_tools = sorted(tools, key=lambda x: ToolPriority.get_priority(x.name))
    
    for tool in sorted_tools:
        # 检查依赖是否满足
        dependencies = ToolDependency.get_dependencies(tool.name)
        if not all(result_manager.get_result(dep) for dep in dependencies):
            continue
            
        # 执行工具
        print(f"正在执行工具: {tool.name}")  # 添加日志记录
        if tool.name == "save_health_advice":
            # 特殊处理save_health_advice，传入其他工具的结果
            result = await tool(
                content=query,
                personalized_advice=result_manager.get_result("get_personalized_advice"),
                retrieve_results=result_manager.get_result("retrieve")
            )
        else:
            result = await tool(query)
            
        result_manager.add_result(tool.name, result)
    
    # 返回最终结果
    return result_manager.get_result("save_health_advice")

def get_next_step(state: State) -> str:
    """决定下一步操作"""
    try:
        # 检查是否有错误
        if state.get("error_info"):
            logger.warning(f"Error detected: {state['error_info']}")
            return "error_handler"
            
        # 获取最后一条消息
        messages = state["messages"]
        if not messages:
            logger.info("No messages, starting with chatbot")
            return "chatbot"
            
        last_message = messages[-1]
        
        # 检查是否需要结束对话
        if isinstance(last_message, AIMessage) and "结束对话" in last_message.content:
            logger.info("Conversation end detected")
            return "end"
            
        # 检查是否有工具调用
        if (hasattr(last_message, "tool_calls") and 
            last_message.tool_calls):
            logger.info("Router: Detected tool calls")
            return "tools"
            
        # 检查是否是工具响应
        if isinstance(last_message, ToolMessage):
            logger.info("Router: Processing tool response")
            return "chatbot"
            
        # 默认流向chatbot
        logger.info("Router: Default to chatbot")
        return "chatbot"
        
    except Exception as e:
        logger.error(f"Router error: {str(e)}\n{traceback.format_exc()}")
        return "error_handler"

async def chatbot_node(state: State, config: Dict[str, Any]):
    """对话节点：处理用户输入并生成回复"""
    try:
        logger.info("Chatbot: Processing input")
        messages = state["messages"]
        logger.info(f"Chatbot: Input messages - {messages}")
        
        # 确保 completed_tools 存在
        if "completed_tools" not in state:
            state["completed_tools"] = set()
        
        # 检查是否已经处理过当前消息
        if messages and isinstance(messages[-1], AIMessage):
            logger.info("Already processed current message, ending turn")
            return {
                "messages": messages,
                "next_step": "end",
                "error_info": None,
                "completed_tools": state["completed_tools"]
            }
        
        # 获取最后一条用户消息
        last_user_message = next(
            (msg for msg in reversed(messages) if isinstance(msg, HumanMessage)),
            None
        )
        
        # 获取当前绑定了工具的模型实例
        model_with_tools = get_model_with_tools()
        response = await model_with_tools.ainvoke(messages)
            
        logger.info(f"Chatbot: Generated response - {response}")
        
        # 检查是否需要结束对话
        next_step = "end" if "结束对话" in response.content else get_next_step({"messages": [response]})
        
        return {
            "messages": [response],
            "next_step": next_step,
            "error_info": None,
            "completed_tools": state["completed_tools"]
        }
    except Exception as e:
        error_msg = f"Chatbot error: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return {
            "messages": [AIMessage(content=f"抱歉，系统遇到了一个错误：{str(e)}")],
            "next_step": "error_handler",
            "error_info": error_msg,
            "completed_tools": state.get("completed_tools", set())
        }

async def tools_node(state: State):
    """工具节点：处理工具调用"""
    try:
        logger.info("Tools: Processing tool calls")
        new_messages = []
        last_message = state["messages"][-1]
        
        # 确保 completed_tools 存在
        if "completed_tools" not in state:
            state["completed_tools"] = set()
        
        if hasattr(last_message, "tool_calls"):
            # 按优先级排序工具调用
            sorted_tool_calls = sorted(
                last_message.tool_calls,
                key=lambda x: ToolPriority.get_priority(x["name"])
            )
            
            for tool_call in sorted_tool_calls:
                try:
                    tool_name = tool_call["name"]
                    
                    # 检查依赖是否满足
                    dependencies = ToolDependency.get_dependencies(tool_name)
                    if dependencies:
                        # 检查是否所有依赖工具都已执行（不论结果如何）
                        deps_met = all(dep in state["completed_tools"] for dep in dependencies)
                        if not deps_met:
                            logger.warning(f"Tool {tool_name} dependencies not met, skipping")
                            continue
                    
                    # 获取参数
                    if "args" in tool_call:
                        arguments = tool_call["args"]
                    else:
                        arguments = json.loads(tool_call["function"]["arguments"])
                        
                    logger.info(f"Tools: Processing {tool_name} with args {arguments}")
                    
                    tool = next((t for t in tools if t.name == tool_name), None)
                    if not tool:
                        raise ValueError(f"未找到工具: {tool_name}")
                        
                    tool_response = await tool.ainvoke(arguments)
                    
                    # 记录工具执行完成
                    state["completed_tools"].add(tool_name)
                    logger.info(f"Tool {tool_name} completed. Current completed tools: {state['completed_tools']}")
                    
                    new_messages.append(
                        ToolMessage(
                            tool_call_id=tool_call.get("id", ""),
                            content=str(tool_response),
                            tool_name=tool_name,
                        )
                    )
                                
                except Exception as e:
                    error_msg = f"工具 {tool_name} 执行失败: {str(e)}"
                    logger.error(error_msg)
                    new_messages.append(
                        ToolMessage(
                            tool_call_id=tool_call.get("id", ""),
                            content=error_msg,
                            tool_name=tool_name,
                        )
                    )
            
            return {
                "messages": state["messages"] + new_messages,
                "next_step": "chatbot",
                "error_info": None,
                "completed_tools": state["completed_tools"]
            }
        
        return state
        
    except Exception as e:
        error_msg = f"工具节点执行失败: {str(e)}"
        logger.error(error_msg)
        return {
            "messages": state["messages"],
            "next_step": "error_handler",
            "error_info": error_msg,
            "completed_tools": state.get("completed_tools", set())
        }

async def error_handler_node(state: State):
    """错误处理节点"""
    error_msg = state.get("error_info", "系统遇到了一个未知错误，请稍后重试")
    logger.error(f"Error handler: {error_msg}")
    
    return {
        "messages": [AIMessage(content=f"系统错误: {error_msg}")],
        "next_step": "end",
        "error_info": None,
        "completed_tools": state.get("completed_tools", set())
    }

def build_graph():
    """构建和编译对话图"""
    logger.info("Building graph")
    graph_builder = StateGraph(State)

    # 添加节点
    graph_builder.add_node("chatbot", chatbot_node)
    graph_builder.add_node("tools", tools_node)
    graph_builder.add_node("error_handler", error_handler_node)

    # 设置入口点
    graph_builder.set_entry_point("chatbot")

    # 添加条件边
    def route_message(state: State) -> str:
        return state["next_step"]
        
    graph_builder.add_conditional_edges(
        "chatbot",
        route_message,
        {
            "chatbot": "chatbot",
            "tools": "tools",
            "error_handler": "error_handler",
            "end": END
        }
    )

    graph_builder.add_conditional_edges(
        "tools",
        route_message,
        {
            "chatbot": "chatbot",
            "tools": "tools",
            "error_handler": "error_handler",
            "end": END
        }
    )

    graph_builder.add_conditional_edges(
        "error_handler",
        route_message,
        {
            "end": END
        }
    )

    # 编译图
    logger.info("Compiling graph")
    return graph_builder.compile()



if __name__ == '__main__':

    async def test_conversation():
        """测试对话"""
        logger.info("Starting test conversation")
        
        # 构建图
        graph = build_graph()
        
        # 构建初始状态
        initial_state = {
            "messages": [HumanMessage(content="我最近感冒了，想知道有什么食材可以帮助恢复，另外我想知道苹果和什么食材相配？")],
            "next_step": "chatbot",
            "error_info": None,
            "completed_tools": set()
        }
        
        try:
            # 运行对话
            logger.info("Starting conversation with initial state: %s", initial_state)
            result = await graph.ainvoke(initial_state)
            
            # 打印结果
            logger.info("Conversation completed successfully")
            for message in result["messages"]:
                if isinstance(message, AIMessage):
                    print("\nAI:", message.content)
                elif isinstance(message, HumanMessage):
                    print("\nHuman:", message.content)
                elif isinstance(message, ToolMessage):
                    print("\nTool Response:", message.content)
                    
        except Exception as e:
            logger.error("Conversation failed: %s", str(e))
            traceback.print_exc()
            print("\nError:", str(e))

        # 绘制图
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(graph.get_graph().draw_mermaid_png()))
        img.show()

    asyncio.run(test_conversation())