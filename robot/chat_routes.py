import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
import uvicorn
from robot.chat_server import chat
from fastapi.middleware.cors import CORSMiddleware
from robot.database.memory import with_mysql_pool, get_pool
import datetime
from langchain_core.messages import HumanMessage, AIMessage
from contextlib import asynccontextmanager
from robot import globals
from robot.llms import get_llm, model
import base64
import shutil
import logging
from PIL import Image
from io import BytesIO

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 定义全局图片目录
GLOBAL_IMAGE_DIR = os.path.join(project_root, "robot", "global_image")

# 确保全局图片目录存在
os.makedirs(GLOBAL_IMAGE_DIR, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    try:
        logger.info("正在初始化应用...")
        # 初始化数据库连接池
        pool = await get_pool()
        logger.info("数据库连接池初始化成功")
        logger.info("应用启动完成")
        yield
    finally:
        logger.info("正在关闭应用...")
        # 关闭数据库连接池
        if 'pool' in locals():
            pool.close()
            await pool.wait_closed()
            logger.info("数据库连接池已关闭")
        logger.info("应用关闭完成")

# 创建 FastAPI 应用实例
app = FastAPI(lifespan=lifespan)

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

@with_mysql_pool
async def get_chat_history(session_id: str, pool=None):
    """获取聊天历史记录"""
    messages = []
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT user_message, bot_response 
                    FROM chat_records 
                    WHERE session_id = %s 
                    AND bot_response IS NOT NULL 
                    ORDER BY created_at ASC
                    """,
                    (session_id,)
                )
                async for row in cur:
                    user_msg, bot_msg = row
                    if user_msg:
                        messages.append(HumanMessage(content=user_msg))
                    if bot_msg:
                        messages.append(AIMessage(content=bot_msg))
        logger.info(f"成功获取会话 {session_id} 的历史记录，共 {len(messages)} 条消息")
    except Exception as e:
        logger.error(f"获取聊天历史记录失败: {str(e)}")
        raise
    return messages

@app.get("/")
async def root():
    """健康检查接口"""
    return {"status": "ok", "message": "服务正常运行"}

@app.post("/api/chat")
@with_mysql_pool
async def chat_endpoint(request: Request, pool=None):
    """
    聊天接口
    """
    try:
        data = await request.json()
        session_id = str(data.get("session_id", ""))
        user_message = str(data.get("message", ""))
        images = data.get("images", [])
        device_id = str(data.get("device_id", ""))  # 从请求中获取 device_id
        
        logger.info(f"收到聊天请求 - session_id: {session_id}, message: {user_message}, images: {len(images)}, device_id: {device_id}")
        
        # 从session_id获取user_id并设置全局变量
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT user_id FROM robot_sessions WHERE session_id = %s",
                    (session_id,)
                )
                result = await cur.fetchone()
                if not result:
                    return JSONResponse(
                        status_code=404,
                        content={
                            "error": "Session not found",
                            "success": False
                        }
                    )
                user_id = result[0]
                
                # 设置全局变量
                globals.current_user_id = user_id
                globals.current_session_id = session_id

        # 如果有图片，先清空全局图片目录
        has_images = len(images)  # 修改为存储实际的图片数量
        if has_images > 0:
            if os.path.exists(GLOBAL_IMAGE_DIR):
                shutil.rmtree(GLOBAL_IMAGE_DIR)
            os.makedirs(GLOBAL_IMAGE_DIR)
            logger.info(f"清空并重建图片目录: {GLOBAL_IMAGE_DIR}")
            
            # 保存新的图片
            for i, img in enumerate(images):
                img_data = base64.b64decode(img["data"])
                img_path = os.path.join(GLOBAL_IMAGE_DIR, f"image_{i+1}{os.path.splitext(img['name'])[1]}")
                with open(img_path, "wb") as f:
                    f.write(img_data)
                logger.info(f"保存图片 {i+1}: {img['name']}")
                
        # 保存用户消息到数据库
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO chat_records (session_id, user_id, user_message, has_images, device_id, sync_status) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (session_id, user_id, user_message, has_images, device_id, "pending")
                )
                record_id = cur.lastrowid
                logger.info(f"保存用户消息 - record_id: {record_id}")
                
                # 保存图片到chat_images表
                if has_images > 0:
                    # 准备图片数据
                    image_data = [record_id]  # 第一个参数是record_id
                    placeholders = ['%s']  # record_id的占位符
                    
                    # 处理每张图片的数据
                    for i, img in enumerate(images):
                        img_data = base64.b64decode(img["data"])
                        image_data.append(img_data)
                        placeholders.append('%s')
                    
                    # 补充剩余的NULL值直到5个图片位置
                    remaining_images = 5 - has_images
                    for _ in range(remaining_images):
                        image_data.append(None)
                        placeholders.append('%s')
                    
                    # 构造INSERT语句
                    columns = ['record_id'] + [f'image_{i+1}' for i in range(5)]
                    insert_sql = f"""
                        INSERT INTO chat_images ({', '.join(columns)})
                        VALUES ({', '.join(placeholders)})
                    """
                    
                    # 执行INSERT
                    await cur.execute(insert_sql, tuple(image_data))
                    await conn.commit()  # 提交事务
                    logger.info(f"保存 {has_images} 张图片到chat_images表 - record_id: {record_id}")
                
                # 获取聊天响应
                bot_response = ""
                try:
                    # 先获取异步生成器
                    chat_gen = await chat(session_id, user_message, has_images=has_images)
                    # 然后迭代它
                    async for msg in chat_gen:
                        if msg:
                            bot_response = msg
                            logger.info(f"收到AI回复: {msg[:100]}...")  # 只记录前100个字符
                except Exception as e:
                    logger.error(f"生成回复失败: {str(e)}")
                    bot_response = f"抱歉，处理消息时出现错误: {str(e)}"
                
                if bot_response:
                    # 更新机器人响应
                    await cur.execute(
                        """
                        UPDATE chat_records 
                        SET bot_response = %s, response_at = CURRENT_TIMESTAMP 
                        WHERE record_id = %s
                        """,
                        (bot_response, record_id)
                    )
                    await conn.commit()
                    logger.info(f"保存AI回复 - record_id: {record_id}")

        return JSONResponse(content={
            "message": bot_response,
            "success": True
        })
        
    except Exception as e:
        logger.error(f"聊天接口错误: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": f"Internal server error: {str(e)}",
                "success": False
            }
        )

@app.post("/api/switch_model")
async def switch_model(request: Request):
    """
    切换语言模型
    """
    try:
        data = await request.json()
        model_name = data.get("model")
        
        if not model_name:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Missing model name",
                    "success": False
                }
            )
            
        try:
            logger.info(f"本次使用的模型是：{model_name}")  # 添加日志打印
            # 尝试获取新模型实例
            new_model = get_llm(model_name)
            # 如果成功，更新全局模型
            globals.current_model = new_model
            
            return JSONResponse(content={
                "message": f"Successfully switched to {model_name}",
                "success": True
            })
            
        except ValueError as e:
            return JSONResponse(
                status_code=400,
                content={
                    "error": str(e),
                    "success": False
                }
            )
            
    except Exception as e:
        logger.error(f"切换模型失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": f"Internal server error: {str(e)}",
                "success": False
            }
        )

async def test_endpoint():
    """测试聊天接口"""
    import aiohttp
    import json
    
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                message = input("请输入消息（输入'exit'退出）：")
                if message.lower() == 'exit':
                    break
                
                # 发送请求
                async with session.post(
                    'http://localhost:8001/api/chat',
                    json={
                        "session_id": "1030",
                        "message": message
                    }
                ) as response:
                    result = await response.json()
                    if result.get("success"):
                        print("\nAI:", result["message"])
                    else:
                        print("\n错误:", result.get("error", "未知错误"))
                        
            except Exception as e:
                logger.error(f"测试过程中出错: {str(e)}")
                print(f"\n错误: {str(e)}")

@app.get("/api/user_rules")
@with_mysql_pool
async def get_user_rules(pool=None):
    """获取用户的AI规则设置"""
    try:
        if not globals.current_user_id:
            return JSONResponse(content={
                "success": True,
                "data": {
                    "ai_rules": "",
                    "is_rules_enabled": False
                }
            })

        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT ai_rules, is_rules_enabled 
                    FROM user_preferences 
                    WHERE user_id = %s
                    """,
                    (globals.current_user_id,)
                )
                result = await cur.fetchone()
                
                if result:
                    ai_rules, is_rules_enabled = result
                    # 更新全局变量
                    globals.current_ai_rules = ai_rules
                    globals.current_rules_enabled = bool(is_rules_enabled)
                    
                    return JSONResponse(content={
                        "success": True,
                        "data": {
                            "ai_rules": ai_rules,
                            "is_rules_enabled": bool(is_rules_enabled)
                        }
                    })
                else:
                    # 如果没有找到记录，返回默认值
                    return JSONResponse(content={
                        "success": True,
                        "data": {
                            "ai_rules": "",
                            "is_rules_enabled": False
                        }
                    })
                    
    except Exception as e:
        logger.error(f"获取用户AI规则失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"获取用户AI规则失败: {str(e)}"
            }
        )

if __name__ == "__main__":
    import platform
    
    if platform.system() == 'Windows':
        # Windows系统需要使用这个
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # 启动服务器
    server = uvicorn.Server(uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8001,
        reload=True
    ))
    
    # 创建一个新的事件循环来运行测试
    async def main():
        # 在后台运行服务器
        server_task = asyncio.create_task(server.serve())
        
        # 等待服务器启动
        await asyncio.sleep(2)
        
        # 运行测试
        await test_endpoint()
        
        # 停止服务器
        server.should_exit = True
        await server_task
    
    # 运行主程序
    asyncio.run(main())
