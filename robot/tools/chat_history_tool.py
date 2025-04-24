from typing import Optional
from langchain_core.tools import tool
import aiomysql
from datetime import datetime, timedelta
import sys
import os
import logging

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from database.memory import with_mysql_pool
from .. import globals


MAX_RECORDS = 100  # 设置最大记录数限制
logger = logging.getLogger(__name__)

@tool
async def chat_history(
    query: str = None,
    days: int = 7,
    limit: int = 20,
) -> str:
    """
    查询聊天历史记录的工具。当需要回忆之前的对话内容时使用。

    参数:
    - query: 搜索关键词（可选）
    - days: 查询最近几天的记录（默认7天）
    - limit: 返回记录数量限制（默认20条，最大100条）

    注意：
    - 查询结果不包括当前正在进行的对话
    - 结果按时间倒序排列
    - 可以通过参数组合实现精确查询
    """
    @with_mysql_pool
    async def _query_history(pool=None):
        try:
            session_id = globals.current_session_id
            if session_id is None:
                logger.error("当前会话ID未设置")
                return "抱歉，无法获取会话ID，请确保您在正确的会话中。"
            
            # 确保limit不超过最大限制
            nonlocal limit
            limit = min(limit, MAX_RECORDS)
            
            logger.info(f"开始查询历史记录: session_id={session_id}, query={query}, days={days}, limit={limit}")
            
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    # 构建查询条件
                    conditions = ["session_id = %s"]
                    params = [session_id]
                    
                    if query:
                        conditions.append("(user_message LIKE %s OR bot_response LIKE %s)")
                        params.extend([f"%{query}%", f"%{query}%"])
                    
                    if days:
                        conditions.append("created_at >= %s")
                        params.append((datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d'))
                    
                    # 获取当前会话的最新记录ID
                    await cur.execute(
                        "SELECT MAX(record_id) FROM chat_records WHERE session_id = %s",
                        (session_id,)
                    )
                    max_record_id = await cur.fetchone()
                    max_record_id = max_record_id[0] if max_record_id and max_record_id[0] else 0
                    
                    # 执行查询
                    sql = f"""
                    SELECT user_message, bot_response, created_at 
                    FROM chat_records 
                    WHERE {' AND '.join(conditions)}
                    AND record_id < (
                        SELECT MAX(record_id) 
                        FROM chat_records 
                        WHERE session_id = %s
                    )
                    ORDER BY created_at DESC
                    LIMIT {limit}
                    """
                    
                    # 添加最后一个session_id参数
                    params.append(session_id)
                    
                    logger.info(f"执行SQL: {sql}")
                    logger.info(f"参数: {params}")
                    
                    await cur.execute(sql, params)
                    rows = await cur.fetchall()
                    
                    if not rows:
                        logger.info("未找到历史记录")
                        return "抱歉，未找到相关的历史记录。"
                    
                    # 格式化结果
                    history = ["以下是查询到的历史对话记录：\n"]
                    for user_msg, bot_msg, timestamp in rows:
                        history.append(f"时间: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                        history.append(f"用户: {user_msg}")
                        if bot_msg:  # 只在有bot响应时添加
                            history.append(f"助手: {bot_msg}")
                        history.append("-" * 50)
                    
                    summary = f"\n共找到 {len(rows)} 条相关记录。"
                    if query:
                        summary += f" (搜索关键词: {query})"
                    
                    history.append(summary)
                    logger.info(f"成功找到 {len(rows)} 条记录")
                    return "\n".join(history)
                    
        except Exception as e:
            logger.error(f"查询历史记录时出错: {str(e)}")
            return f"查询历史记录时出错: {str(e)}"
    
    return await _query_history() 