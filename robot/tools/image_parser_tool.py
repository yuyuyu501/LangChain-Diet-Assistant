import base64
import os
from langchain_core.tools import tool
import sys
from pathlib import Path

# 添加ImageModel目录到系统路径
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from ImageModel.food_predict import FoodPredictor

# 初始化食物预测器
predictor = FoodPredictor(checkpoint_path=os.path.join(ROOT_DIR, 'ImageModel', 'checkpoint-3125'))

@tool
def image_parser(base_path: str):
    """
    分析图片并返回食物识别结果，并为每张图片添加序号。
    这个工具只会分析 `robot/global_image` 目录下的图片。
    :param base_path: 图片文件夹路径
    :return: 每张图片的识别结果，格式为：
             第1张图：XXX（置信度：XX%）
             第2张图：XXX（置信度：XX%）
             ...
    """
    # 确保使用正确的路径分隔符
    base_path = os.path.join(ROOT_DIR, 'global_image')
    
    # 如果目录不存在，创建它
    if not os.path.exists(base_path):
        os.makedirs(base_path)
        return "图片目录已创建，请添加图片后再次尝试。"
    
    # 获取目录中的所有图片文件
    image_files = [f for f in os.listdir(base_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not image_files:
        return "目录中没有找到图片文件。"
    
    result_list = []
    for index, img_path in enumerate(image_files, start=1):
        # 调用本地模型分析图片
        result = analyze_image(os.path.join(base_path, img_path))
        # 添加序号
        result_list.append(f"第{index}张图：{result}")
    return "\n".join(result_list)

def analyze_image(img_path: str):
    """使用本地ViT模型分析图片内容"""
    try:
        # 获取预测结果（返回top-5的预测及其概率）
        predictions = predictor.predict(img_path)
        
        # 获取最高置信度的预测结果
        food_name, confidence = predictions[0]
        
        # 格式化输出结果
        result = f"{food_name}（置信度：{confidence:.2%}）"
        return result
    except Exception as e:
        return f"图片分析失败：{str(e)}"

if __name__ == '__main__':
    print(image_parser("C:\\Users\\yuyuyu\\Desktop\\毕设\\代码\\robot\\global_image"))
