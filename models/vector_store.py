from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from config import Config

class VectorStore:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(openai_api_key=Config.OPENAI_API_KEY)
        self.vectorstore = None

    def initialize_store(self, documents):
        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=Config.VECTOR_STORE_PATH
        )
        return self.vectorstore.as_retriever()
