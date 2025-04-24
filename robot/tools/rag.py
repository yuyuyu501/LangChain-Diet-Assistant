from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List, Dict, Any, Optional, Union
import sys
import os
import pandas as pd
from langchain_community.embeddings.huggingface import HuggingFaceEmbeddings
import torch
import logging
from operator import itemgetter
import asyncio
from functools import lru_cache
from huggingface_hub import snapshot_download
from pathlib import Path
import json
from langchain.tools import Tool, StructuredTool, BaseTool
from langchain.agents import Tool

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

from robot.llms import model
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_community.document_loaders import UnstructuredMarkdownLoader, CSVLoader
from langchain_core.tools import tool

# 定义模型相关常量
MODEL_NAME = "shibing624/text2vec-base-chinese"
MODEL_CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "EmbeddingModel")

def ensure_model_downloaded(use_local_model: bool = False):  # 默认使用网上模型
    """
    确保模型已下载到本地
    
    Args:
        use_local_model (bool): 是否使用本地模型，默认为True。
            如果为True，将使用本地缓存的模型；
            如果为False，将直接使用HuggingFace的在线模型。
    """
    try:
        if not use_local_model:
            logger.info("使用HuggingFace在线模型")
            return MODEL_NAME
            
        # 创建缓存目录
        os.makedirs(MODEL_CACHE_DIR, exist_ok=True)
        
        # 检查模型是否已下载
        model_path = os.path.join(MODEL_CACHE_DIR, MODEL_NAME.split('/')[-1])
        if not os.path.exists(model_path):
            logger.info(f"模型未找到，开始下载到: {model_path}")
            # 下载模型
            snapshot_download(
                repo_id=MODEL_NAME,
                local_dir=model_path,
                local_dir_use_symlinks=False
            )
            logger.info("模型下载完成")
        else:
            logger.info("使用本地缓存的模型")
            
        return model_path
    except Exception as e:
        logger.error(f"下载模型时出错: {str(e)}")
        raise

# 初始化嵌入模型
try:
    model_path = ensure_model_downloaded(use_local_model=False)
    embeddings = HuggingFaceEmbeddings(
        model_name=model_path,
        model_kwargs={'device': 'cuda' if torch.cuda.is_available() else 'cpu'}
    )
    logger.info(f"成功加载模型，使用设备: {'cuda' if torch.cuda.is_available() else 'cpu'}")
except Exception as e:
    logger.error(f"加载模型失败: {str(e)}")
    raise

# 定义营养素关键词映射
nutrient_keywords = {
    '蛋白质': ('蛋白质(g)', True),
    '高蛋白': ('蛋白质(g)', True),
    '低脂': ('脂肪(g)', False),
    '低脂肪': ('脂肪(g)', False),
    '高能量': ('能量(kcal)', True),
    '热量高': ('能量(kcal)', True),
    '低能量': ('能量(kcal)', False),
    '热量低': ('能量(kcal)', False),
    '碳水': ('碳水化合物(g)', True),
    '纤维': ('膳食纤维(g)', True),
    '膳食纤维': ('膳食纤维(g)', True),
    '铁质': ('铁(mg)', True),
    '钙质': ('钙(mg)', True),
    '维生素C': ('维生素C(mg)', True),
    '维生素A': ('维生素A(μg)', True),
    '维生素E': ('维生素E(mg)', True),
    '维生素B1': ('维生素B1(mg)', True),
    '维生素B2': ('维生素B2(mg)', True)
}

# 定义食谱关键词映射
recipe_keywords = {
    '简单': ('难度等级', ['简单', '容易']),
    '家常': ('烹饪方法', ['炒', '煮', '炖']),
    '养胃': ('功效', ['养胃', '健胃', '护胃']),
    '安神': ('功效', ['安神', '助眠', '养心']),
    '补血': ('功效', ['补血', '养血', '益气']),
    '降火': ('功效', ['清热', '降火', '去火']),
    '开胃': ('功效', ['开胃', '促进食欲', '健脾']),
    '减肥': ('功效', ['减肥', '瘦身', '低热量']),
    '补钙': ('功效', ['补钙', '强骨', '养骨']),
    '补铁': ('功效', ['补铁', '养血', '贫血']),
    '清淡': ('口味', ['清淡', '淡味', '原味']),
    '易消化': ('功效', ['易消化', '健脾', '开胃'])
}

# 定义中医功效关键词
tcm_keywords = {
    '补气': ['人参', '黄芪', '山药', '大枣'],
    '养血': ['当归', '枸杞', '红枣', '阿胶'],
    '健脾': ['白术', '茯苓', '山药', '薏米'],
    '养胃': ['生姜', '大枣', '陈皮', '山楂'],
    '清热': ['菊花', '金银花', '绿豆', '荷叶'],
    '滋阴': ['玉竹', '麦冬', '石斛', '百合'],
    '安神': ['酸枣仁', '百合', '莲子', '龙眼肉']
}

def clean_numeric_value(value: Any) -> float:
    """清理数值数据，处理特殊字符"""
    if pd.isna(value):
        return 0.0
    
    if isinstance(value, (int, float)):
        return float(value)
        
    value = str(value).strip()
    if value in ['—', '…', 'Tr', '', '-']:
        return 0.0
        
    try:
        return float(value)
    except ValueError:
        logger.warning(f"无法转换为数值: {value}")
        return 0.0

def process_food_data(row: pd.Series) -> Optional[Dict[str, Any]]:
    """处理食物成分数据"""
    try:
        if pd.isna(row['食物名称']):
            logger.warning("跳过缺失食物名称的数据")
            return None
            
        return {
            '食物名称': str(row['食物名称']),
            '能量(kcal)': clean_numeric_value(row['能量(kcal)']),
            '蛋白质(g)': clean_numeric_value(row['蛋白质(g)']),
            '脂肪(g)': clean_numeric_value(row['脂肪(g)']),
            '碳水化合物(g)': clean_numeric_value(row['碳水化合物(g)']),
            '膳食纤维(g)': clean_numeric_value(row.get('膳食纤维(g)', 0.0)),
            '食物类别': str(row.get('大类名称', '未分类')),
            '子类名称': str(row.get('子类名称', '未分类')),
            '数据类型': '食物成分'
        }
    except Exception as e:
        logger.error(f"处理食物成分数据时出错: {str(e)}")
        return None

def process_recipe_data(row: pd.Series) -> Optional[Dict[str, Any]]:
    """处理食谱数据"""
    try:
        if pd.isna(row['菜名']):
            logger.warning("跳过缺失菜名的数据")
            return None
            
        return {
            '菜名': str(row['菜名']),
            '烹饪方法': str(row.get('烹饪方法', '未知')),
            '口味': str(row.get('口味', '未知')),
            '难度等级': str(row.get('难度等级', '未知')),
            '预估成本': str(row.get('预估成本', '未知')),
            '烹饪时长': str(row.get('烹饪时长', '未知')),
            '主料': str(row.get('主料', '')),
            '辅料': str(row.get('辅料', '')),
            '调料': str(row.get('调料', '')),
            '步骤': str(row.get('步骤', '')),
            '功效': str(row.get('功效', '')),
            '注意事项': str(row.get('注意事项', '')),
            '数据类型': '食谱'
        }
    except Exception as e:
        logger.error(f"处理食谱数据时出错: {str(e)}")
        return None

@lru_cache(maxsize=2)
def load_documents(file_path: str, data_type: str = 'food') -> List[Document]:
    """加载并处理文档，使用缓存避免重复加载"""
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"找不到文件: {file_path}")
            
        if not file_path.endswith('.csv'):
            raise ValueError(f"不支持的文件类型: {file_path}")
            
        df = pd.read_csv(file_path)
        documents = []
    
        if data_type == 'food':
            for _, row in df.iterrows():
                data = process_food_data(row)
                if data is None:
                    continue
                
                content = (
                    f"食物：{data['食物名称']}\n"
                    f"类别：{data['食物类别']} - {data['子类名称']}\n"
                    f"营养成分：\n"
                    f"- 能量：{data['能量(kcal)']}千卡\n"
                    f"- 蛋白质：{data['蛋白质(g)']}克\n"
                    f"- 脂肪：{data['脂肪(g)']}克\n"
                    f"- 碳水化合物：{data['碳水化合物(g)']}克\n"
                    f"- 膳食纤维：{data['膳食纤维(g)']}克"
                )
                documents.append(Document(page_content=content, metadata=data))
        
        elif data_type == 'recipe':
            for _, row in df.iterrows():
                data = process_recipe_data(row)
                if data is None:
                    continue
                
                content = (
                    f"菜品：{data['菜名']}\n"
                    f"烹饪信息：\n"
                    f"- 烹饪方法：{data['烹饪方法']}\n"
                    f"- 口味：{data['口味']}\n"
                    f"- 难度等级{data['难度等级']}\n"
                    f"- 预估成本：{data['预估成本']}\n"
                    f"- 烹饪时长{data['烹饪时长']}\n"
                    f"食材配料：\n"
                    f"- 主料：{data['主料']}\n"
                    f"- 辅料：{data['辅料']}\n"
                    f"- 调料：{data['调料']}\n"
                    f"功效与注意事项：\n"
                    f"- 功效：{data['功效']}\n"
                    f"- 注意事项：{data['注意事项']}"
                )
                documents.append(Document(page_content=content, metadata=data))
        
        logger.info(f"成功加载 {len(documents)} 条{data_type}数据")
        return documents
    except Exception as e:
        logger.error(f"加载文档时出错: {str(e)}")
        raise

def filter_and_sort_results(docs: List[Document], query: str) -> List[Document]:
    """根据查询类型过滤和排序结果"""
    try:
        # 检查文档类型
        if not docs:
            return []
            
        if '数据类型' in docs[0].metadata:
            data_type = docs[0].metadata['数据类型']
            
            if data_type == '食物成分':
                # 查找匹配的营养素关键词
                for keyword, (field, reverse) in nutrient_keywords.items():
                    if keyword in query:
                        return sorted(docs, key=lambda x: x.metadata.get(field, 0), reverse=reverse)
                
                # 检查中医功效关键词
                for effect, foods in tcm_keywords.items():
                    if effect in query:
                        return [doc for doc in docs if any(food in doc.metadata['食物名称'] for food in foods)]
            
            elif data_type == '食谱':
                # 查找匹配的食谱关键词
                for keyword, (field, values) in recipe_keywords.items():
                    if keyword in query:
                        return [doc for doc in docs if any(value in str(doc.metadata.get(field, '')) for value in values)]
                
                # 检查食材关键词
                for effect, foods in tcm_keywords.items():
                    if effect in query:
                        return [doc for doc in docs if any(food in doc.metadata.get('主料', '') or food in doc.metadata.get('辅料', '') for food in foods)]
        
        # 如果没有特定的排序要求，返回原始顺序
        return docs
    except Exception as e:
        logger.error(f"过滤和排序结果时出错: {str(e)}")
        return docs

# 加载食物成分数据
food_file_path = os.path.join(project_root, "robot", "data", "中国食物成分数据表_CN.csv")
recipe_file_path = os.path.join(project_root, "robot", "data", "中国食谱数据表.csv")
# 加载过敏原数据
allergens_file_path = os.path.join(project_root, "robot", "data", "allergens_data.json")

try:
    # 加载两类数据
    food_docs = load_documents(food_file_path, 'food')
    recipe_docs = load_documents(recipe_file_path, 'recipe')
    
    # 合并所有文档
    all_docs = food_docs + recipe_docs
    
    # 文本分割
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    all_splits = text_splitter.split_documents(all_docs)
    
    # 创建向量存储
    vector_store = InMemoryVectorStore(embeddings)
    vector_store.add_documents(documents=all_splits)
    logger.info("成功初始化向量存储")
except Exception as e:
    logger.error(f"初始化向量存储时出错: {str(e)}")
    raise

# 加载过敏原数据
try:
    with open(allergens_file_path, 'r', encoding='utf-8') as f:
        allergens_data = json.load(f)
    logger.info("成功加载过敏原数据")
except Exception as e:
    logger.error(f"加载过敏原数据时出错: {str(e)}")
    raise

@tool
async def retrieve(query: Union[str, Dict[str, Any]], allergens: Optional[List[str]] = None) -> str:
    """
    根据用户查询检索食物营养信息和食谱信息，同时支持过敏原过滤。
    
    参数:
        query (Union[str, Dict[str, Any]]): 用户的查询文本或包含查询的字典
        allergens (Optional[List[str]], optional): 用户的过敏原列表. Defaults to None.
      
    检索流程：
    1. 过敏原反向检索（如果提供了allergens参数）：
       - 首先根据用户提供的过敏原列表，排除所有包含这些过敏原的食物
       - 支持的过敏原类型：
         * milk（乳制品）
         * eggs（鸡蛋）
         * peanuts（花生）
         * tree_nuts（坚果）
         * wheat（小麦）
         * soy（大豆）
         * fish（鱼类）
         * shellfish（贝类）
         * sesame（芝麻）
         * mustard（芥末）
    
    2. 正向检索支持的查询类型：
       A. 食物营养查询：
          - 蛋白质/高蛋白：按蛋白质含量降序排序
          - 低脂/低脂肪：按脂肪含量升序排序
          - 高能量/热量高：按能量含量降序排序
          - 低能量/热量低：按能量含量升序排序
          - 碳水：按碳水化合物含量降序排序
          - 纤维/膳食纤维：按膳食纤维含量降序排序
          - 铁质：按铁含量降序排序
          - 钙质：按钙含量降序排序
          - 维生素相关：按相应维生素含量排序
       
       B. 食谱查询：
          - 按烹饪方法：炒、煮、炖等
          - 按难度：简单、普通、困难
          - 按功效：养胃、补血、降火等
          - 按主料：肉类、海鲜、蔬菜等
       
       C. 中医功效查询：
          - 补气：人参、黄芪等
          - 养血：当归、枸杞等
          - 健脾：白术、山药等
          - 养胃：生姜、陈皮等
          - 清热：菊花、绿豆等
          - 滋阴：玉竹、石斛等
          - 安神：酸枣仁、百合等
               
    返回:
        str - 格式化的检索结果，包含相关食物的营养信息或食谱信息（已排除过敏原相关食物）
    """
    try:
        # 处理参数
        query_text = ""
        if isinstance(query, dict):
            if 'query' in query:
                query_text = query['query']
            elif 'args' in query and isinstance(query['args'], dict):
                query_text = query['args'].get('query', '')
            elif 'arguments' in query:
                try:
                    import json
                    args = json.loads(query['arguments'])
                    query_text = args.get('query', '')
                except (json.JSONDecodeError, KeyError) as e:
                    logger.error(f"解析参数时出错: {str(e)}")
                    return f"抱歉，参数解析失败: {str(e)}"
        else:
            query_text = str(query)

        if not query_text.strip():
            return "抱歉，查询参数必须是非空字符串。"

        # 反向检索：排除过敏原相关食物
        excluded_food_names = []
        if allergens:
            for allergen in allergens:
                if allergen in allergens_data['common_allergens']:
                    excluded_food_names.extend(allergens_data['common_allergens'][allergen]['common_foods'])

        # 检索相似文档
        docs = await asyncio.to_thread(
            vector_store.similarity_search,
            query_text,
            k=15  # 检索更多文档以便后续筛选
        )

        # 过滤掉包含过敏原的食物
        if excluded_food_names:
            docs = [doc for doc in docs if doc.metadata.get('食物名称') not in excluded_food_names]

        # 根据查询类型过滤和排序结果
        filtered_docs = filter_and_sort_results(docs, query_text)
        
        # 只保留前5个最相关的结果
        top_docs = filtered_docs[:5]
        
        if not top_docs:
            return "抱歉，未找到相关的信息。"
        
        # 格式化输出结果
        results = []
        
        # 添加查询类型说明
        if any(keyword in query_text for keyword in ['蛋白质', '脂肪', '能量', '碳水', '纤维', '铁质', '钙质', '维生素']):
            results.append("【营养成分检索结果】")
        elif any(keyword in query_text for keyword in ['补气', '养血', '健脾', '养胃', '清热', '滋阴', '安神']):
            results.append("【中医功效检索结果】")
        elif any(keyword in query_text for keyword in ['简单', '快速', '家常', '养胃', '安神', '补血', '降火', '开胃']):
            results.append("【食谱检索结果】")
        else:
            results.append("【综合检索结果】")
        
        # 格式化每个文档的内容
        for i, doc in enumerate(top_docs, 1):
            results.append(f"\n{i}. {doc.page_content}")
            
            # 添加额外的营养信息或功效说明
            if doc.metadata.get('数据类型') == '食物成分':
                results.append("\n   主要营养成分：")
                for nutrient, (field, _) in nutrient_keywords.items():
                    if field in doc.metadata:
                        value = doc.metadata[field]
                        if isinstance(value, (int, float)) and value > 0:
                            results.append(f"   - {nutrient}: {value}")
            elif doc.metadata.get('数据类型') == '食谱':
                if '功效' in doc.metadata and doc.metadata['功效']:
                    results.append(f"\n   功效：{doc.metadata['功效']}")
                if '注意事项' in doc.metadata and doc.metadata['注意事项']:
                    results.append(f"\n   注意事项：{doc.metadata['注意事项']}")
        
        return "\n".join(results)
    
    except Exception as e:
        logger.error(f"检索过程中出错: {str(e)}")
        return f"抱歉，检索过程中出现错误: {str(e)}"

if __name__ == "__main__":
    # 测试用例
    test_cases = {
        "食物营养查询": [
            "高蛋白质的食物有哪些",
            "低脂肪的食物推荐",
            "富含维生素C的水果",
            "高钙的食物",
            "含铁丰富的食材"
        ],
        "食谱基础查询": [
            "简单快速的家常菜",
            "适合上班族的快手菜",
            "新手也能做的菜谱",
            "半小时能做好的菜",
            "不用复杂调料的菜"
        ],
        "功效导向查询": [
            "养胃的食谱",
            "补气养血的食物",
            "安神助眠的食材",
            "清热降火的饮品",
            "开胃促消化的菜"
        ],
        "场景化查询": [
            "适合老年人的养生汤",
            "孕妇补铁食谱",
            "儿童补钙食谱",
            "减肥期间的低卡餐",
            "运动后补充能量的食物"
        ],
        "混合查询": [
            "高蛋白低脂的减肥餐",
            "补气养血的简单食谱",
            "清淡易消化的养胃汤",
            "快手营养的早餐",
            "适合冬季的滋补汤"
        ],
        "新增列测试": [
            "测试菜品",
            "测试方法",
            "测试口味",
            "简单",
            "短"
        ],
        "过敏原测试": [
            {"query": "高蛋白的食物", "allergens": ["milk", "eggs"]},
            {"query": "补气养血的食谱", "allergens": ["peanuts", "tree_nuts"]},
            {"query": "适合儿童的早餐", "allergens": ["milk", "wheat"]},
            {"query": "清淡易消化的食物", "allergens": ["soy", "fish"]},
            {"query": "营养丰富的主食", "allergens": ["wheat", "eggs"]}
        ]
    }

    async def run_tests():
        try:
            print("开始测试RAG系统...\n")
            
            for category, queries in test_cases.items():
                print(f"\n=== 测试类别：{category} ===")
                for i, query in enumerate(queries, 1):
                    print(f"\n[测试 {i}/5] 查询：{query}")
                    try:
                        if isinstance(query, dict):
                            # 处理带过敏原的查询
                            result = await retrieve.ainvoke({"query": query["query"], "allergens": query["allergens"]})
                        else:
                            # 处理普通查询
                            result = await retrieve.ainvoke({"query": query})
                            
                        print("\n结果：")
                        print(result)
                        print("\n" + "="*50)
                    except Exception as e:
                        print(f"测试失败：{str(e)}")
                        continue
            
            print("\n所有测试完成！")
            
        except Exception as e:
            print(f"测试过程中出现错误：{str(e)}")

    # 运行测试
    asyncio.run(run_tests())

