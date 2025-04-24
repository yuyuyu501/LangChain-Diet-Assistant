import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from ..graph_builder import KnowledgeGraphBuilder
from .graph_store import Neo4jGraphStore

async def init_neo4j_graph():
    """初始化Neo4j图数据库"""
    # 创建Neo4j存储实例
    store = Neo4jGraphStore(
        uri="neo4j+s://6ffdfd27.databases.neo4j.io",
        user="neo4j",
        password="Ci--01lfzgrxOFanTMt3IKh_ENvCe85hpd1h5x4iFy8"
    )
    
    # 创建构建器实例
    builder = KnowledgeGraphBuilder()
    
    try:
        # 连接Neo4j
        await store.connect()
        print("已连接到Neo4j数据库")
        
        # 构建并存储食材实体
        print("开始构建食材实体...")
        food_entities = await builder.build_food_entities()
        for entity in food_entities:
            await store.store_food_entity(entity)
        print(f"已导入 {len(food_entities)} 个食材实体")
        
        # 构建并存储功效实体
        print("开始构建功效实体...")
        effect_entities = await builder.build_effect_entities()
        for entity in effect_entities:
            await store.store_effect_entity(entity)
        print(f"已导入 {len(effect_entities)} 个功效实体")
        
        # 构建并存储关系
        print("开始构建关系...")
        relations = await builder.build_relations()
        
        # 存储食材关系
        for relation in relations['food_relations']:
            await store.store_food_relation(relation)
        print(f"已导入 {len(relations['food_relations'])} 个食材关系")
        
        # 存储营养成分关系
        for relation in relations['nutrient_relations']:
            await store.store_nutrient_relation(relation)
        print(f"已导入 {len(relations['nutrient_relations'])} 个营养成分关系")
        
        # 存储功效关系
        for relation in relations['effect_relations']:
            await store.store_effect_relation(relation)
        print(f"已导入 {len(relations['effect_relations'])} 个功效关系")
        
        print("Neo4j图数据库初始化完成！")
        
    except Exception as e:
        print(f"初始化过程中出错: {str(e)}")
        raise
    finally:
        await store.close()
        print("数据库连接已关闭")

if __name__ == "__main__":
    asyncio.run(init_neo4j_graph()) 