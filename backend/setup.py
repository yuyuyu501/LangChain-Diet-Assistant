from setuptools import setup, find_packages

setup(
    name="robot",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        "aiomysql>=0.1.1",
        "pymysql>=1.0.2",
        "python-dotenv>=0.19.0",
        "langchain>=0.0.200",
        "openai>=0.27.0",
        "pydantic>=1.8.2",
    ],
) 