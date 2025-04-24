import os

def getenv():
    import dotenv
    dotenv.load_dotenv()

if __name__ == "__main__":
    getenv()
    print(os.environ["LANGCHAIN_API_KEY"])
    print(os.environ["EMAIL_PASSWORD"])

