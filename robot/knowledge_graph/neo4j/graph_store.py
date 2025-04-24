from neo4j import AsyncGraphDatabase
from typing import List, Dict, Any, Union
import json
from ..models.entities import FoodEntity, EffectEntity
from ..models.relations import FoodRelation, NutrientRelation, EffectRelation

EntityType = Union[FoodEntity, EffectEntity]
RelationType = Union[FoodRelation, NutrientRelation, EffectRelation]

class Neo4jGraphStore:
    def __init__(self, uri="neo4j+s://6ffdfd27.databases.neo4j.io", user="neo4j", password="Ci--01lfzgrxOFanTMt3IKh_ENvCe85hpd1h5x4iFy8"):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        
    async def connect(self):
        """连接到Neo4j"""
        self.driver = AsyncGraphDatabase.driver(self.uri, auth=(self.user, self.password))
        
    async def close(self):
        """关闭连接"""
        if self.driver:
            await self.driver.close()
            
    async def store_food_entity(self, entity: FoodEntity):
        """存储食材实体"""
        query = """
        CREATE (f:Food {
            id: $id,
            name: $name,
            category: $category,
            properties: $properties,
            season: $season
        })
        """
        async with self.driver.session() as session:
            await session.run(
                query,
                id=entity.id,
                name=entity.name,
                category=entity.category,
                properties=json.dumps(entity.properties),
                season=json.dumps(entity.season)
            )
            
    async def store_effect_entity(self, entity: EffectEntity):
        """存储功效实体"""
        query = """
        CREATE (e:Effect {
            id: $id,
            name: $name,
            description: $description,
            related_symptoms: $symptoms
        })
        """
        async with self.driver.session() as session:
            await session.run(
                query,
                id=entity.id,
                name=entity.name,
                description=entity.description,
                symptoms=json.dumps(entity.related_symptoms)
            )
            
    async def store_food_relation(self, relation: FoodRelation):
        """存储食材关系"""
        query = """
        MATCH (f1:Food {id: $source_id})
        MATCH (f2:Food {id: $target_id})
        CREATE (f1)-[r:FOOD_RELATION {
            type: $relation_type,
            weight: $weight,
            evidence: $evidence
        }]->(f2)
        """
        async with self.driver.session() as session:
            await session.run(
                query,
                source_id=relation.source_id,
                target_id=relation.target_id,
                relation_type=relation.relation_type,
                weight=relation.weight,
                evidence=relation.evidence
            )
            
    async def store_nutrient_relation(self, relation: NutrientRelation):
        """存储营养成分关系"""
        query = """
        MATCH (f:Food {id: $food_id})
        CREATE (n:Nutrient {
            name: $nutrient_name,
            amount: $amount,
            unit: $unit
        })
        CREATE (f)-[r:HAS_NUTRIENT]->(n)
        """
        async with self.driver.session() as session:
            await session.run(
                query,
                food_id=relation.food_id,
                nutrient_name=relation.nutrient_name,
                amount=relation.amount,
                unit=relation.unit
            )
            
    async def store_effect_relation(self, relation: EffectRelation):
        """存储功效关系"""
        query = """
        MATCH (f:Food {id: $food_id})
        MATCH (e:Effect {id: $effect_id})
        CREATE (f)-[r:HAS_EFFECT {
            confidence: $confidence,
            reference: $reference
        }]->(e)
        """
        async with self.driver.session() as session:
            await session.run(
                query,
                food_id=relation.food_id,
                effect_id=relation.effect_id,
                confidence=relation.confidence,
                reference=relation.reference_info
            )
            
    async def get_food_by_name(self, name: str) -> Dict:
        """通过名称查询食材"""
        query = """
        MATCH (f:Food {name: $name})
        RETURN f
        """
        async with self.driver.session() as session:
            result = await session.run(query, name=name)
            record = await result.single()
            return record["f"] if record else None
            
    async def get_compatible_foods(self, food_id: int) -> List[Dict]:
        """查询相配食材"""
        query = """
        MATCH (f1:Food {id: $food_id})-[r:FOOD_RELATION {type: '相生'}]->(f2:Food)
        RETURN f2, r.weight as weight, r.evidence as evidence
        """
        async with self.driver.session() as session:
            result = await session.run(query, food_id=food_id)
            return [{"food": record["f2"], "weight": record["weight"], "evidence": record["evidence"]}
                   async for record in result]
                   
    async def get_incompatible_foods(self, food_id: int) -> List[Dict]:
        """查询相克食材"""
        query = """
        MATCH (f1:Food {id: $food_id})-[r:FOOD_RELATION {type: '相克'}]->(f2:Food)
        RETURN f2, r.weight as weight, r.evidence as evidence
        """
        async with self.driver.session() as session:
            result = await session.run(query, food_id=food_id)
            return [{"food": record["f2"], "weight": record["weight"], "evidence": record["evidence"]}
                   async for record in result] 