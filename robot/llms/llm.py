from langchain_community.chat_models import ChatZhipuAI
from langchain_ollama import ChatOllama
from typing import Optional

def get_llm(model_name: str = "glm-4-plus", temperature: float = 0.5):
    """
    根据模型名称获取对应的语言模型实例
    
    Args:
        model_name: 模型名称，支持 'glm-4-plus', 'deepseek-r1-1.5b', 'qwen2.5-1.5b', 'llama3.2-3b', 'deepseek-v1-latest'
        temperature: 温度参数，控制输出的随机性
    
    Returns:
        对应的语言模型实例
    """
    if model_name == "glm-4-plus":
        return ChatZhipuAI(
            api_key="c932cbee2dce48869aaa2d6072d09f79.4fMXPn8wdCfaXO0f",
            model="glm-4-plus",
            temperature=temperature,
        )
    elif model_name == "deepseek-r1-1.5b":
        return ChatOllama(
            model="MFDoom/deepseek-r1-tool-calling:1.5b",
            temperature=temperature
        )
    elif model_name == "qwen2.5-1.5b":
        return ChatOllama(
            model="qwen2.5:1.5b",
            temperature=temperature
        )
    elif model_name == "llama3.2-3b":
        return ChatOllama(
            model="llama3.2:3b",
            temperature=temperature
        )
    elif model_name == "deepseek-v3-latest":
        return ChatOllama(
            model="nezahatkorkmaz/deepseek-v3:latest",
            temperature=temperature
        )
    else:
        raise ValueError(f"不支持的模型: {model_name}")

# 默认使用 GLM-4-Plus 模型
model = get_llm()

if __name__ == "__main__":
    # 测试不同模型
    models = ["glm-4-plus", "deepseek-r1-1.5b", "qwen2.5-1.5b", "llama3.2-3b", "deepseek-v3-latest"]
    for model_name in models:
        try:
            model = get_llm(model_name)
            print(f"\n测试 {model_name}:")
            print(model.invoke("你好"))
        except Exception as e:
            print(f"{model_name} 测试失败: {str(e)}")