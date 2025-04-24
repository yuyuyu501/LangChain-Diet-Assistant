import asyncio
from neo4j import AsyncGraphDatabase

async def test_connection():
    # 硬编码连接信息
    uri = "neo4j+s://6ffdfd27.databases.neo4j.io"
    user = "neo4j"
    password = "Ci--01lfzgrxOFanTMt3IKh_ENvCe85hpd1h5x4iFy8"
    
    print(f"使用以下信息连接：")
    print(f"URI: {uri}")
    print(f"User: {user}")
    print(f"Password: {password}")
    
    try:
        # 创建驱动
        driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        
        # 测试连接
        print("\n尝试连接...")
        async with driver.session() as session:
            result = await session.run("RETURN 1 as num")
            record = await result.single()
            print(f"\n连接成功！测试查询结果：{record['num']}")
            
    except Exception as e:
        print(f"\n连接失败：{str(e)}")
    finally:
        await driver.close()

if __name__ == "__main__":
    asyncio.run(test_connection()) 