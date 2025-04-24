from typing import List, Dict, Any
from .neo4j.graph_store import Neo4jGraphStore
import json

class GraphQuery:
    def __init__(self):
        self.store = Neo4jGraphStore()
        
    async def initialize(self):
        """初始化连接"""
        await self.store.connect()
        
    async def cleanup(self):
        """清理连接"""
        await self.store.close()
        
    async def get_compatible_foods(self, food_name: str) -> List[Dict]:
        """获取相配食材"""
        # 先通过名称获取食材ID
        food = await self.store.get_food_by_name(food_name)
        if not food:
            return []
            
        return await self.store.get_compatible_foods(food['id'])
        
    async def get_incompatible_foods(self, food_name: str) -> List[Dict]:
        """获取相克食材"""
        # 先通过名称获取食材ID
        food = await self.store.get_food_by_name(food_name)
        if not food:
            return []
            
        return await self.store.get_incompatible_foods(food['id'])
        
    async def get_seasonal_foods(self, season: str) -> List[Dict]:
        """获取时令食材"""
        query = """
        MATCH (f:Food)
        WHERE $season IN apoc.convert.fromJsonList(f.season)
        RETURN f
        """
        async with self.store.driver.session() as session:
            result = await session.run(query, season=season)
            return [record["f"] async for record in result]
        
    async def get_food_nutrients(self, food_name: str) -> List[Dict]:
        """获取食材的营养成分"""
        query = """
        MATCH (f:Food {name: $name})-[r:HAS_NUTRIENT]->(n:Nutrient)
        RETURN n.name as nutrient, n.amount as amount, n.unit as unit
        """
        async with self.store.driver.session() as session:
            result = await session.run(query, name=food_name)
            return [{"nutrient": record["nutrient"],
                    "amount": record["amount"],
                    "unit": record["unit"]} async for record in result]
        
    async def get_therapeutic_foods(self, symptom: str) -> List[Dict]:
        """获取具有特定功效的食材"""
        query = """
        MATCH (f:Food)-[r:HAS_EFFECT]->(e:Effect)
        WHERE $symptom IN apoc.convert.fromJsonList(e.related_symptoms)
        AND r.confidence >= 0.7
        RETURN f, e, r.confidence as confidence, r.reference as reference
        """
        async with self.store.driver.session() as session:
            result = await session.run(query, symptom=symptom)
            return [{"food": record["f"],
                    "effect": record["e"],
                    "confidence": record["confidence"],
                    "reference": record["reference"]} async for record in result] 