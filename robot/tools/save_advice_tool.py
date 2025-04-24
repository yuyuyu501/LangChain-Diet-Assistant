# 健康建议保存工具
import json
from datetime import datetime
from typing import Dict, Any, Optional
from langchain_core.tools import tool
import aiomysql
import os
from dotenv import load_dotenv
from .. import globals

# 加载环境变量
load_dotenv()

@tool
async def save_health_advice(
    content: str,
    symptoms: Optional[str] = None,
    recommended_foods: Optional[str] = None,
) -> Dict[str, Any]:
    """
    保存健康建议到数据库的工具函数

    Args:
        content (str): 建议内容
        symptoms (Optional[str], optional): 症状描述. Defaults to None.
        recommended_foods (Optional[str], optional): 推荐食物. Defaults to None.

    Returns:
        Dict[str, Any]: 包含保存结果的字典
    """
    try:
        # 使用全局变量获取用户ID
        user_id = globals.current_user_id
        # user_id = 10
        if not user_id:
            return {
                'status': 'failed',
                'message': '未找到用户ID'
            }

        # 创建数据库连接
        async with aiomysql.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "root123"),
            db=os.getenv("DB_NAME", "robot")
        ) as conn:
            async with conn.cursor() as cur:
                # 准备当前时间
                current_time = datetime.now()
                
                # 插入健康建议记录
                await cur.execute("""
                    INSERT INTO health_advice (
                        user_id,
                        content,
                        symptoms,
                        recommended_foods,
                        created_at,
                        updated_at,
                        is_favorite,
                        is_deleted,
                        device_id,
                        sync_status
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    user_id,
                    content,
                    symptoms,
                    recommended_foods,
                    current_time,
                    current_time,
                    0,  # is_favorite 默认为否
                    0,  # is_deleted 默认为否
                    None,
                    'pending'  # sync_status 默认为待同步
                ))
                
                # 获取插入的记录ID
                advice_id = cur.lastrowid
                
                # 提交事务
                await conn.commit()

                return {
                    'status': 'success',
                    'message': '健康建议保存成功',
                    'data': {
                        'advice_id': advice_id,
                        'user_id': user_id,
                        'content': content,
                        'symptoms': symptoms,
                        'recommended_foods': recommended_foods,
                        'created_at': current_time.isoformat(),
                    }
                }

    except Exception as e:
        return {
            'status': 'failed',
            'message': f'保存健康建议时发生错误: {str(e)}'
        }

if __name__ == '__main__':
    # 测试代码
    import asyncio
    
    async def test_save_health_advice():
        # 设置测试用户ID
        current_user_id = 10
        
        # 测试数据
        test_advice = {
            'content': '建议增加蛋白质的摄入，每天可以吃一些鸡胸肉和鱼。',
            'symptoms': '感觉疲劳，没有精神',
            'recommended_foods': '鸡胸肉,三文鱼,豆制品',
        }
        
        # 调用保存函数
        result = await save_health_advice.ainvoke(test_advice)
        print('保存结果:', result)

    # 运行测试
    asyncio.run(test_save_health_advice()) 