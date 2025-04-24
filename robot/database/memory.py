from functools import wraps
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.checkpoint.memory import MemorySaver
import inspect
import asyncio
from typing import AsyncGenerator, Any
import aiomysql
import os
from dotenv import load_dotenv
import logging

# 加载环境变量
load_dotenv()

# 内存存储器实例
memory_saver = MemorySaver()

# MySQL 连接池
_pool = None

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_pool():
    """获取 MySQL 连接池"""
    global _pool
    try:
        if _pool is None:
            logger.info("正在创建MySQL连接池...")
            _pool = await aiomysql.create_pool(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', 3306)),
                user=os.getenv('DB_USER', 'root'),
                password=os.getenv('DB_PASSWORD', 'root123'),
                db=os.getenv('DB_NAME', 'robot'),
                charset='utf8mb4',
                autocommit=True,
                minsize=1,
                maxsize=10
            )
            logger.info("MySQL连接池创建成功")
        return _pool
    except Exception as e:
        logger.error(f"MySQL连接池创建失败: {str(e)}")
        raise

def with_mysql_pool(func):
    """MySQL 连接池装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            pool = await get_pool()
            kwargs['pool'] = pool
            
            if inspect.isasyncgenfunction(func):
                # 创建异步生成器包装
                async def async_gen():
                    async for item in await func(*args, **kwargs):
                        yield item
                return async_gen()
            else:
                # 处理普通异步函数或同步函数
                return await func(*args, **kwargs) if inspect.iscoroutinefunction(func) else func(*args, **kwargs)
        except Exception as e:
            logger.error(f"数据库操作失败: {str(e)}")
            raise
            
    return wrapper

def with_async_sqlite_saver(conn_string):
    """SQLite 存储装饰器 (保留用于兼容性)"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs) -> AsyncGenerator[Any, None]:
            async with AsyncSqliteSaver.from_conn_string(conn_string) as memory:
                kwargs['memory'] = memory
                
                if inspect.isasyncgenfunction(func):
                    async for item in func(*args, **kwargs):
                        yield item
                else:
                    result = await func(*args, **kwargs) if inspect.iscoroutinefunction(func) else func(*args, **kwargs)
                    yield result
                    
        return wrapper
    return decorator
