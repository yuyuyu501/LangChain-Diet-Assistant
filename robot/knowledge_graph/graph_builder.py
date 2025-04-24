import os
from typing import List, Dict, Any
from pathlib import Path
import aiomysql
from dotenv import load_dotenv
import json
from datetime import datetime
from .models.entities import FoodEntity, EffectEntity
from .models.relations import FoodRelation, NutrientRelation, EffectRelation

class KnowledgeGraphBuilder:
    def __init__(self):
        load_dotenv()
        self.db_config = {
            'host': os.getenv("MYSQL_HOST", "localhost"),
            'port': int(os.getenv("MYSQL_PORT", 3306)),
            'user': os.getenv("MYSQL_USER", "root"),
            'password': os.getenv("MYSQL_PASSWORD", "root123"),
            'db': os.getenv("MYSQL_DATABASE", "robot")
        }
        
    async def get_db_connection(self):
        """获取数据库连接"""
        return await aiomysql.connect(**self.db_config)

    async def build_food_entities(self) -> List[FoodEntity]:
        """从food_base表构建食材实体"""
        entities = []
        conn = await self.get_db_connection()
        try:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("""
                    SELECT * FROM food_base
                """)
                rows = await cur.fetchall()
                
                for row in rows:
                    # 解析JSON字符串
                    properties = json.loads(row['properties']) if row['properties'] else {}
                    season = json.loads(row['season']) if row['season'] else []
                    
                    # 转换时间戳为字符串
                    created_at = row['created_at'].isoformat() if row['created_at'] else None
                    updated_at = row['updated_at'].isoformat() if row['updated_at'] else None
                    
                    entity = FoodEntity(
                        id=row['id'],
                        name=row['name'],
                        category=row['category'],
                        properties=properties,
                        season=season,
                        created_at=created_at,
                        updated_at=updated_at
                    )
                    entities.append(entity)
        finally:
            conn.close()
        return entities

    async def build_effect_entities(self) -> List[EffectEntity]:
        """从effects表构建功效实体"""
        entities = []
        conn = await self.get_db_connection()
        try:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("""
                    SELECT * FROM effects
                """)
                rows = await cur.fetchall()
                
                for row in rows:
                    # 解析JSON字符串
                    related_symptoms = json.loads(row['related_symptoms']) if row['related_symptoms'] else []
                    
                    # 转换时间戳为字符串
                    created_at = row['created_at'].isoformat() if row['created_at'] else None
                    updated_at = row['updated_at'].isoformat() if row['updated_at'] else None
                    
                    entity = EffectEntity(
                        id=row['id'],
                        name=row['name'],
                        description=row['description'],
                        related_symptoms=related_symptoms,
                        created_at=created_at,
                        updated_at=updated_at
                    )
                    entities.append(entity)
        finally:
            conn.close()
        return entities
        
    async def build_relations(self) -> Dict[str, List[Any]]:
        """构建所有关系"""
        relations = {
            'food_relations': [],
            'nutrient_relations': [],
            'effect_relations': []
        }
        
        conn = await self.get_db_connection()
        try:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                # 构建食材关系
                await cur.execute("""
                    SELECT * FROM food_relations
                """)
                food_relations = await cur.fetchall()
                for row in food_relations:
                    created_at = row['created_at'].isoformat() if row['created_at'] else None
                    updated_at = row['updated_at'].isoformat() if row['updated_at'] else None
                    
                    relation = FoodRelation(
                        id=row['id'],
                        source_id=row['source_id'],
                        target_id=row['target_id'],
                        relation_type=row['relation_type'],
                        weight=float(row['weight']),
                        evidence=row['evidence'],
                        created_at=created_at,
                        updated_at=updated_at
                    )
                    relations['food_relations'].append(relation)
                
                # 构建营养成分关系
                await cur.execute("""
                    SELECT * FROM food_nutrients
                """)
                nutrient_relations = await cur.fetchall()
                for row in nutrient_relations:
                    created_at = row['created_at'].isoformat() if row['created_at'] else None
                    
                    relation = NutrientRelation(
                        id=row['id'],
                        food_id=row['food_id'],
                        nutrient_name=row['nutrient_name'],
                        amount=float(row['amount']),
                        unit=row['unit'],
                        created_at=created_at
                    )
                    relations['nutrient_relations'].append(relation)
                
                # 构建功效关系
                await cur.execute("""
                    SELECT * FROM food_effects
                """)
                effect_relations = await cur.fetchall()
                for row in effect_relations:
                    created_at = row['created_at'].isoformat() if row['created_at'] else None
                    
                    relation = EffectRelation(
                        id=row['id'],
                        food_id=row['food_id'],
                        effect_id=row['effect_id'],
                        confidence=float(row['confidence']),
                        reference_info=row['reference_info'],
                        created_at=created_at
                    )
                    relations['effect_relations'].append(relation)
        finally:
            conn.close()
            
        return relations 