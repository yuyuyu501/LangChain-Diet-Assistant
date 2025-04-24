import sys
import os
from pathlib import Path
from langchain_core.tools import tool
import asyncio

# 添加项目根目录到Python路径
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from knowledge_graph.graph_query import GraphQuery
import logging

logger = logging.getLogger(__name__)

# 创建一个GraphQuery实例
graph_query = GraphQuery()
_is_initialized = False

async def ensure_initialized():
    """确保Neo4j连接已初始化"""
    global _is_initialized
    if not _is_initialized:
        try:
            await graph_query.initialize()
            _is_initialized = True
            logger.info("Neo4j connection initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j connection: {e}")
            raise

@tool
async def query_food_relations(food_name: str) -> str:
    """查询食材的相生相克关系。

    Args:
        food_name (str): 食材名称，例如"苹果"、"牛肉"等

    Returns:
        str: 返回食材的相生相克分析结果，格式为：
            食材关系分析：
            相配食材：A, B, C
            相克食材：X, Y, Z
    """
    await ensure_initialized()
    compatible = await graph_query.get_compatible_foods(food_name)
    incompatible = await graph_query.get_incompatible_foods(food_name)
    
    compatible_names = [food['food']['name'] for food in compatible]
    incompatible_names = [food['food']['name'] for food in incompatible]
    
    return f"""食材关系分析：
相配食材：{', '.join(compatible_names)}
相克食材：{', '.join(incompatible_names)}"""

@tool
async def query_seasonal_foods(season: str) -> str:
    """查询特定季节的时令食材。

    Args:
        season (str): 季节名称，必须是以下之一：春季、夏季、秋季、冬季

    Returns:
        str: 返回该季节的时令食材列表，格式为：
            XX季时令食材：A, B, C, D...
    """
    await ensure_initialized()
    foods = await graph_query.get_seasonal_foods(season)
    food_names = [food['name'] for food in foods]
    return f"{season}时令食材：{', '.join(food_names)}"

@tool
async def query_therapeutic_foods(symptom: str) -> str:
    """查询对特定症状有帮助的食材。

    Args:
        symptom (str): 症状或功效名称，例如"感冒"、"补血"、"降血压"等

    Returns:
        str: 返回具有该功效的食材列表，每个食材包含其功效和置信度，格式为：
            适合XX的食材：
            A（功效：YY，置信度：0.95）
            B（功效：YY，置信度：0.90）
            ...
    """
    await ensure_initialized()
    foods = await graph_query.get_therapeutic_foods(symptom)
    result = []
    for food in foods:
        result.append(f"{food['food']['name']}（功效：{food['effect']['name']}，置信度：{food['confidence']}）")
    return f"适合{symptom}的食材：\n" + "\n".join(result)

# 在模块退出时清理连接
import atexit

def cleanup():
    """清理Neo4j连接"""
    if _is_initialized:
        try:
            asyncio.run(graph_query.cleanup())
            logger.info("Neo4j connection cleaned up successfully")
        except Exception as e:
            logger.error(f"Error cleaning up Neo4j connection: {e}")

atexit.register(cleanup)

if __name__ == '__main__':
    async def test_tools():
        try:
            # 测试食材关系查询
            print("\n=== 测试食材关系查询 ===")
            food_name = "苹果"
            result = await query_food_relations.ainvoke({"food_name": food_name})
            print(result)
            
            # 测试时令食材查询
            print("\n=== 测试时令食材查询 ===")
            season = "夏季"
            result = await query_seasonal_foods.ainvoke({"season": season})
            print(result)
            
            # 测试功效食材查询
            print("\n=== 测试功效食材查询 ===")
            symptom = "感冒"
            result = await query_therapeutic_foods.ainvoke({"symptom": symptom})
            print(result)
            
        except Exception as e:
            print(f"Error during testing: {e}")
            raise
    
    # 运行测试
    asyncio.run(test_tools())