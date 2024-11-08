import os
import dotenv

dotenv.load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    VECTOR_STORE_PATH = "vectorstore_db"
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50