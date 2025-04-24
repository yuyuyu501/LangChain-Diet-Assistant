# 用户个性化工具
import json
from datetime import datetime, timedelta
from collections import Counter
from typing import Dict, List, Any
from langchain_core.tools import tool
import aiomysql
import os
from dotenv import load_dotenv
from .. import globals



# 加载环境变量
load_dotenv()

class PersonalizedTool:
    def __init__(self, user_profile, dietary_records):
        """初始化个性化工具"""
        self.user_profile = user_profile  # 用户档案
        self.dietary_records = dietary_records  # 饮食记录

    async def track_dietary_preferences(self, days: int = 30) -> Dict[str, Any]:
        """
        跟踪用户饮食偏好，分析用户档案和饮食记录
        
        Args:
            days (int): 分析最近几天的数据，默认30天
            
        Returns:
            Dict[str, Any]: 包含用户饮食偏好分析结果的字典
        """
        try:
            # 获取基础用户信息
            user_info = {
                'diet_type': self.user_profile.get('diet_type', 'normal'),
                'allergies': self.user_profile.get('allergies', []),
                'favorite_ingredients': self.user_profile.get('favorite_ingredients', []),
                'disliked_ingredients': self.user_profile.get('disliked_ingredients', []),
                'spicy_level': self.user_profile.get('spicy_level', 'medium'),
                'cooking_time_preference': self.user_profile.get('cooking_time_preference', 30)
            }
            print(f"用户基础信息: {user_info}")  # 添加调试信息

            # 计算时间范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # 分析饮食记录
            recent_records = [
                record for record in self.dietary_records
                if start_date <= datetime.fromisoformat(record['recorded_at']) <= end_date
            ]
            print(f"最近的饮食记录数量: {len(recent_records)}")  # 添加调试信息

            # 统计分析
            analysis = {
                'total_meals': len(recent_records),
                'average_calories': 0,
                'favorite_meal_types': Counter(),
                'most_consumed_ingredients': Counter(),
                'satisfaction_levels': Counter(),
                'nutrition_stats': {
                    'protein': 0,
                    'carbs': 0,
                    'fat': 0
                }
            }

            if recent_records:
                # 计算平均卡路里
                total_calories = sum(record.get('calories', 0) for record in recent_records)
                analysis['average_calories'] = total_calories / len(recent_records)

                # 统计餐食类型
                for record in recent_records:
                    analysis['favorite_meal_types'][record.get('meal_type', 'unknown')] += 1

                    # 统计食材
                    food_items = record.get('food_items', [])
                    for item in food_items:
                        analysis['most_consumed_ingredients'][item] += 1

                    # 统计满意度
                    if 'satisfaction' in record:
                        analysis['satisfaction_levels'][record['satisfaction']] += 1

                    # 累计营养数据
                    analysis['nutrition_stats']['protein'] += record.get('protein', 0)
                    analysis['nutrition_stats']['carbs'] += record.get('carbs', 0)
                    analysis['nutrition_stats']['fat'] += record.get('fat', 0)

                # 计算营养平均值
                for nutrient in analysis['nutrition_stats']:
                    analysis['nutrition_stats'][nutrient] /= len(recent_records)

            # 计算 BMI
            height_m = self.user_profile.get('height', 0) / 100  # 将身高转换为米
            weight_kg = self.user_profile.get('weight', 0)
            if height_m > 0:
                bmi = weight_kg / (height_m ** 2)
            else:
                bmi = 0

            # 判断体重状态
            if bmi < 18.5:
                weight_status = '偏瘦'
            elif 18.5 <= bmi < 24.9:
                weight_status = '正常'
            elif 25 <= bmi < 29.9:
                weight_status = '偏重'
            else:
                weight_status = '肥胖'

            # 将 BMI 和体重状态添加到分析结果中
            analysis['bmi'] = bmi
            analysis['weight_status'] = weight_status

            # 合并用户信息和分析结果
            preference_analysis = {
                'user_info': user_info,
                'dietary_analysis': analysis,
                'recommendations': {
                    'suggested_meal_types': self._get_suggested_meal_types(analysis),
                    'nutrition_advice': self._get_nutrition_advice(analysis),
                    'cooking_suggestions': self._get_cooking_suggestions(user_info, analysis)
                }
            }
            print(f"生成的偏好分析结果: {preference_analysis}")  # 添加调试信息
            return preference_analysis

        except Exception as e:
            print(f"track_dietary_preferences 发生错误: {str(e)}")
            # 返回一个基本的分析结果
            return {
                'user_info': {
                    'diet_type': 'normal',
                    'allergies': [],
                    'favorite_ingredients': [],
                    'disliked_ingredients': [],
                    'spicy_level': 'medium',
                    'cooking_time_preference': 30
                },
                'dietary_analysis': {
                    'total_meals': 0,
                    'average_calories': 0,
                    'bmi': 0,
                    'weight_status': '未知'
                },
                'recommendations': {
                    'suggested_meal_types': [],
                    'nutrition_advice': [],
                    'cooking_suggestions': []
                }
            }

    def _get_suggested_meal_types(self, analysis: Dict) -> List[str]:
        """根据分析结果生成建议的餐食类型"""
        # 获取用户最常吃的餐食类型
        favorite_types = analysis['favorite_meal_types'].most_common()
        return [meal_type for meal_type, _ in favorite_types[:3]]

    def _get_nutrition_advice(self, analysis: Dict) -> List[str]:
        """根据营养分析生成建议"""
        advice = []
        stats = analysis['nutrition_stats']
        
        # 简单的营养建议逻辑
        if stats['protein'] < 50:
            advice.append("建议增加蛋白质的摄入")
        if stats['carbs'] > 300:
            advice.append("建议适当减少碳水化合物的摄入")
        if stats['fat'] > 70:
            advice.append("建议控制脂肪的摄入")
            
        return advice

    def _get_cooking_suggestions(self, user_info: Dict, analysis: Dict) -> List[str]:
        """根据用户信息和分析结果生成烹饪建议"""
        suggestions = []
        
        # 根据用户喜好生成建议
        if user_info['cooking_time_preference'] <= 20:
            suggestions.append("建议选择快手菜谱和简单的烹饪方法")
        
        # 根据饮食类型给出建议
        if user_info['diet_type'] == 'vegetarian':
            suggestions.append("推荐多样化的素食搭配，保证营养均衡")
        
        # 根据辣度偏好给出建议
        spicy_level = user_info['spicy_level']
        if spicy_level in ['hot', 'extra_hot']:
            suggestions.append("注意控制辛辣食材的使用量")
            
        return suggestions

@tool
async def generate_personalized_advice(
    time_frame: int = 30
) -> Dict[str, Any]:
    """
    生成个性化饮食建议的工具函数

    Args:
        time_frame (int, optional): 分析的时间范围（天数），默认30天

    Returns:
        Dict[str, Any]: 包含个性化建议的字典
    """
    try:
        # 使用全局变量获取用户ID
        user_id = globals.current_user_id
        # 从数据库获取用户档案和饮食记录
        print(f"当前用户ID: {user_id}")  # 添加调试信息
        user_profile = await get_user_profile(user_id)
        print(f"用户档案: {user_profile}")  # 添加调试信息
        dietary_records = await get_dietary_records(user_id, time_frame)
        print(f"饮食记录: {dietary_records}")  # 添加调试信息
        # 从用户档案中获取健康状况和过敏信息
        health_conditions = user_profile.get('health_conditions', [])
        allergies = user_profile.get('allergies', [])

        # 创建个性化工具实例
        personal_tool = PersonalizedTool(user_profile, dietary_records)

        # 获取饮食偏好分析
        preference_analysis = await personal_tool.track_dietary_preferences(days=time_frame)

        # 整合所有信息生成最终建议
        final_advice = {
            '分析周期': f'最近{time_frame}天',
            '用户档案摘要': {
                '健康状况': health_conditions,
                '过敏信息': allergies,
                '当前体重': user_profile.get('weight'),
                '目标体重': user_profile.get('weight_goal'),
                '饮食类型': user_profile.get('diet_type'),
                '每日卡路里目标': user_profile.get('calorie_target'),
                '身高': user_profile.get('height'),
                'BMI': preference_analysis['dietary_analysis']['bmi'],
                '体重状态': preference_analysis['dietary_analysis']['weight_status']
            },
            '偏好分析': preference_analysis,
            '个性化建议': {
                '每日膳食计划': _generate_meal_plan(preference_analysis, health_conditions),
                '健康建议': _generate_health_tips(preference_analysis, health_conditions),
                '饮食调整建议': _generate_dietary_adjustments(
                    preference_analysis,
                    health_conditions,
                    allergies
                )
            }
        }

        return final_advice

    except Exception as e:
        return {
            'error': f'生成个性化建议时发生错误: {str(e)}',
            'status': 'failed'
        }

def _generate_meal_plan(analysis: Dict, health_conditions: List[str]) -> List[Dict]:
    """生成每日膳食计划"""
    # 这里可以根据分析结果和健康状况生成具体的膳食计划
    meal_plan = []
    meal_types = analysis['recommendations']['suggested_meal_types']
    
    for meal_type in meal_types:
        meal_plan.append({
            'meal_type': meal_type,
            'suggested_dishes': [],  # 这里可以添加具体的推荐菜品
            'nutrition_target': {}   # 这里可以添加营养目标
        })
    
    return meal_plan

def _generate_health_tips(analysis: Dict, health_conditions: List[str]) -> List[str]:
    """生成健康建议"""
    tips = []
    nutrition_advice = analysis['recommendations']['nutrition_advice']
    
    # 添加基于营养分析的建议
    tips.extend(nutrition_advice)
    
    # 添加基于健康状况的建议
    for condition in health_conditions:
        if condition == "减重":
            tips.append("建议控制总热量摄入，增加蛋白质比例")
        elif condition == "增肌":
            tips.append("建议适当增加蛋白质和碳水化合物的摄入")
    
    return tips

def _generate_dietary_adjustments(
    analysis: Dict,
    health_conditions: List[str],
    allergies: List[str]
) -> List[str]:
    """生成饮食调整建议"""
    adjustments = []
    
    # 根据过敏信息生成建议
    if allergies:
        for allergy in allergies:
            if allergy == "无麸质":
                adjustments.append("建议选择无麸质的主食替代品")
            elif allergy == "素食":
                adjustments.append("建议通过多样化的植物蛋白来保证蛋白质摄入")
    
    # 根据健康状况生成建议
    for condition in health_conditions:
        cooking_suggestions = analysis['recommendations']['cooking_suggestions']
        adjustments.extend(cooking_suggestions)
    
    return adjustments

async def get_user_profile(user_id: str) -> Dict:
    """
    从数据库获取用户档案
    
    Args:
        user_id (str): 用户ID
        
    Returns:
        Dict: 用户档案信息
    """
    try:
        # 创建数据库连接
        async with aiomysql.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "root123"),
            db=os.getenv("DB_NAME", "robot")
        ) as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                # 查询用户档案
                await cur.execute("""
                    SELECT 
                        height,
                        weight,
                        age,
                        gender,
                        health_conditions,
                        allergies,
                        diet_type,
                        spicy_level,
                        favorite_ingredients,
                        disliked_ingredients,
                        cooking_time_preference,
                        calorie_target,
                        protein_target,
                        carb_target,
                        fat_target,
                        weight_goal
                    FROM user_profiles
                    WHERE user_id = %s
                """, (int(user_id),))
                
                result = await cur.fetchone()
                print(f"获取用户档案结果: {result}")  # 添加调试信息
                if result:
                    # 解析 health_conditions
                    try:
                        health_conditions_data = json.loads(result['health_conditions']) if result['health_conditions'] else {}
                        health_conditions = [health_conditions_data.get('goal')] if health_conditions_data.get('goal') else []
                    except json.JSONDecodeError:
                        health_conditions = []
                        print(f"解析 health_conditions 失败: {result['health_conditions']}")

                    processed_profile = {
                        'height': float(result['height'] or 170),  # 设置默认值
                        'weight': float(result['weight'] or 65),
                        'age': int(result['age'] or 25),
                        'gender': result['gender'] or 'other',
                        'health_conditions': health_conditions,  # 使用解析后的数据
                        'allergies': json.loads(result['allergies']) if result['allergies'] else [],
                        'diet_type': result['diet_type'] or 'normal',
                        'spicy_level': result['spicy_level'] or 'medium',
                        'favorite_ingredients': json.loads(result['favorite_ingredients']) if result['favorite_ingredients'] else [],
                        'disliked_ingredients': json.loads(result['disliked_ingredients']) if result['disliked_ingredients'] else [],
                        'cooking_time_preference': int(result['cooking_time_preference'] or 30),
                        'calorie_target': int(result['calorie_target'] or 2000),
                        'protein_target': int(result['protein_target'] or 60),
                        'carb_target': int(result['carb_target'] or 250),
                        'fat_target': int(result['fat_target'] or 70),
                        'weight_goal': float(result['weight_goal'] or result['weight'])  # 默认与当前体重相同
                    }
                    print(f"处理后的用户档案: {processed_profile}")  # 添加调试信息
                    return processed_profile
                else:
                    # 如果没有找到用户档案，返回默认值
                    default_profile = {
                        'height': 170.0,
                        'weight': 65.0,
                        'age': 25,
                        'gender': 'other',
                        'health_conditions': [],
                        'allergies': [],
                        'diet_type': 'normal',
                        'spicy_level': 'medium',
                        'favorite_ingredients': [],
                        'disliked_ingredients': [],
                        'cooking_time_preference': 30,
                        'calorie_target': 2000,
                        'protein_target': 60,
                        'carb_target': 250,
                        'fat_target': 70,
                        'weight_goal': 65.0
                    }
                    print(f"使用默认用户档案: {default_profile}")  # 添加调试信息
                    return default_profile
    
    except Exception as e:
        print(f"获取用户档案时发生错误: {str(e)}")
        # 发生错误时返回默认值
        return {
            'height': 170.0,
            'weight': 65.0,
            'age': 25,
            'gender': 'other',
            'health_conditions': [],
            'allergies': [],
            'diet_type': 'normal',
            'spicy_level': 'medium',
            'favorite_ingredients': [],
            'disliked_ingredients': [],
            'cooking_time_preference': 30,
            'calorie_target': 2000,
            'protein_target': 60,
            'carb_target': 250,
            'fat_target': 70,
            'weight_goal': 65.0
        }

async def get_dietary_records(user_id: str, days: int) -> List[Dict]:
    """
    从数据库获取用户饮食记录
    
    Args:
        user_id (str): 用户ID
        days (int): 获取最近几天的记录
        
    Returns:
        List[Dict]: 饮食记录列表
    """
    try:
        # 创建数据库连接
        async with aiomysql.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "root123"),
            db=os.getenv("DB_NAME", "robot")
        ) as conn:
        
            async with conn.cursor(aiomysql.DictCursor) as cur:
                # 计算时间范围
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                # 查询饮食记录
                await cur.execute("""
                    SELECT 
                        id,
                        meal_type,
                        food_items,
                        calories,
                        protein,
                        carbs,
                        fat,
                        satisfaction,
                        notes,
                        recorded_at,
                        updated_at
                    FROM dietary_records
                    WHERE user_id = %s 
                    AND recorded_at BETWEEN %s AND %s
                    ORDER BY recorded_at DESC
                """, (int(user_id), start_date, end_date))
                
                results = await cur.fetchall()
                print(f"获取饮食记录结果: {results}")  # 添加调试信息
                
                # 处理查询结果
                records = []
                for record in results:
                    processed_record = {
                        'meal_type': record['meal_type'],
                        'food_items': json.loads(record['food_items']) if record['food_items'] else [],
                        'calories': float(record['calories'] or 0),  # 处理 NULL 或 0
                        'protein': float(record['protein'] or 0),
                        'carbs': float(record['carbs'] or 0),
                        'fat': float(record['fat'] or 0),
                        'satisfaction': int(record['satisfaction'] or 3),  # 默认满意度为3
                        'notes': record['notes'] or '',
                        'recorded_at': record['recorded_at'].isoformat() if record['recorded_at'] else datetime.now().isoformat(),
                        'updated_at': record['updated_at'].isoformat() if record['updated_at'] else None
                    }
                    records.append(processed_record)
                
                return records if records else [
                    # 如果没有记录，返回一个示例记录
                    {
                        'meal_type': 'lunch',
                        'food_items': ['米饭', '青菜', '鸡肉'],
                        'calories': 500,
                        'protein': 25,
                        'carbs': 60,
                        'fat': 15,
                        'satisfaction': 4,
                        'notes': '示例记录',
                        'recorded_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                ]
    
    except Exception as e:
        print(f"获取饮食记录时发生错误: {str(e)}")
        # 发生错误时返回空列表
        return []

if __name__ == '__main__':
    current_user_id = 10  # 测试用户ID
    
    import asyncio
    
    async def test_generate_personalized_advice():
        result = await generate_personalized_advice.ainvoke({"time_frame": 30})  # 使用异步调用
        print("最终结果：",result)
    
    asyncio.run(test_generate_personalized_advice())
