import os
import sys
from pathlib import Path
import json

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from robot.aagent import build_graph
from robot.database.memory import with_mysql_pool, get_pool
import asyncio
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from llms import gen_prompt, prompt
from llms.prompt import get_chat_system_message
from robot.tools.image_parser_tool import image_parser
from robot import globals
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@with_mysql_pool
async def chat(session_id: str, message: str, pool=None, memory=None, has_images: int = 0):
    '''
    聊天函数
    :param session_id: 会话ID
    :param message: 用户消息
    :param pool: 数据库连接池
    :param memory: 内存对象
    :param has_images: 图片数量
    :return: 异步生成器，生成回复消息
    '''
    try:
        logger.info(f"[接收请求] session_id: {session_id}, message: {message}, has_images: {has_images}张图片")
        
        # 从session_id获取user_id
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT user_id FROM robot_sessions WHERE session_id = %s",
                    (session_id,)
                )
                result = await cur.fetchone()
                if not result:
                    raise Exception("会话不存在")
                user_id = result[0]
        
        if prompt:
            message = gen_prompt(message)
            logger.info(f"[提示词生成] 生成的提示词: {message}")

        config = {
            "configurable": {
                "thread_id": session_id,
                "model": globals.current_model  # 使用全局模型
            }
        }
        current_graph = build_graph()  # 使用build_graph函数创建新的图实例
        
        # 加载历史消息
        history_messages = []
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT user_message, bot_response 
                    FROM chat_records 
                    WHERE session_id = %s 
                    AND bot_response IS NOT NULL
                    ORDER BY created_at ASC
                    LIMIT 10
                    """,
                    (session_id,)
                )
                async for row in cur:
                    user_msg, bot_msg = row
                    if user_msg:
                        history_messages.append(HumanMessage(content=user_msg))
                    if bot_msg:
                        history_messages.append(AIMessage(content=bot_msg))
        
        logger.info(f"[历史消息] 加载了 {len(history_messages)} 条历史消息")
        
        # 构建基本消息列表
        message_list = [
            get_chat_system_message(),  # 系统消息
        ]
        
        # 添加个性化规则（如果启用）
        if globals.current_rules_enabled and globals.current_ai_rules:
            logger.info(f"[个性化规则] 当前规则启用状态: {globals.current_rules_enabled}, 规则内容: {globals.current_ai_rules}")
            logger.info("[个性化规则] 应用用户自定义规则")
            message_list.append(SystemMessage(content=f"请严格遵守以下规则：\n{globals.current_ai_rules}"))
        else:
            logger.info("[个性化规则] 用户自定义规则未启用")
            
        # 添加历史消息和用户消息
        message_list.extend([
            *history_messages,  # 历史消息
            HumanMessage(content=message)  # 用户消息
        ])
        
        # 如果有图片，先使用image_parser分析图片
        if has_images > 0:
            try:
                image_description = await image_parser.ainvoke(
                    "C:\\Users\\yuyuyu\\Desktop\\毕设\\代码\\robot\\global_image"
                )
                message_list.append(SystemMessage(content=f"图片分析结果（共{has_images}张）：\n{image_description}"))
                logger.info(f"[图片分析] {image_description}")
            except Exception as e:
                logger.error(f"[图片分析错误] {str(e)}")
                message_list.append(SystemMessage(content=f"图片分析失败：{str(e)}"))
            
        # 创建异步生成器
        async def message_generator():
            logger.info("[开始生成] 正在生成回复...")
            last_response = None
            try:
                # 添加user_id到配置中
                config["user_id"] = user_id
                events = current_graph.astream(
                    input={
                        "messages": message_list,
                        "next_step": "chatbot",
                        "error_info": None
                    },
                    config=config,
                    stream_mode="values",
                )
                
                async for event in events:
                    if "messages" in event:
                        for msg in event["messages"]:
                            if isinstance(msg, AIMessage):
                                content = msg.content
                                # 处理可能的JSON格式响应
                                try:
                                    # 尝试解析JSON
                                    content_json = json.loads(content)
                                    if isinstance(content_json, dict) and "response" in content_json:
                                        content = content_json["response"]
                                except json.JSONDecodeError:
                                    # 如果不是JSON格式，保持原样
                                    pass
                                
                                last_response = content
                                # 如果是结束对话的消息，立即返回
                                if "结束对话" in last_response:
                                    logger.info(f"[对话结束] {last_response}")
                                    yield last_response
                                    return
                        
                # 只返回最终的回复
                if last_response:
                    logger.info(f"[最终回复] {last_response}")
                    yield last_response
                else:
                    error_msg = "生成回复失败：没有有效的回复内容"
                    logger.error(f"[错误] {error_msg}")
                    yield error_msg
                    
            except Exception as e:
                error_msg = f"生成回复时出错: {str(e)}"
                logger.error(f"[错误] {error_msg}")
                yield error_msg
        
        # 返回异步生成器
        return message_generator()
                
    except Exception as e:
        logger.error(f"[错误] Chat error in chat function: {str(e)}")
        async def error_generator():
            error_msg = f"抱歉，处理消息时出现错误: {str(e)}"
            logger.error(f"[错误响应] {error_msg}")
            yield error_msg
        return error_generator()

async def test_chat():
    """测试聊天功能"""
    try:
        # 初始化数据库连接池
        pool = await get_pool()
        
        while True:
            try:
                message = input("请输入消息（输入'exit'退出）：")
                if message.lower() == 'exit':
                    break
                    
                # 获取聊天生成器
                chat_gen = await chat(session_id='1', message=message, pool=pool)
                
                # 处理响应
                async for response in chat_gen:
                    if response:
                        print("\nAI:", response)
                        
            except Exception as e:
                logger.error(f"处理消息时出错: {str(e)}")
                print(f"\n错误: {str(e)}")
                
    except Exception as e:
        logger.error(f"测试过程中出错: {str(e)}")
    finally:
        # 关闭连接池
        if pool:
            pool.close()
            await pool.wait_closed()

if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_chat())
