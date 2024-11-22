from langchain_community.document_loaders import TextLoader
#from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import glob
from config import Config

class DocumentLoader:
    @staticmethod
    def load_faq_documents(): #faq 텍스트 파일 로드 함수 
        faq_data = []
        # txt_paths = glob.glob("./files/faq/*.txt")
        txt_paths = glob.glob("./faq.txt")
        for txt_path in txt_paths:
            loader = TextLoader(file_path=txt_path, encoding='utf-8')
            txt_data = loader.load()
            faq_data.extend(txt_data)
        return faq_data

    @staticmethod
    def split_documents(data): # 문서 분할 함수 
        if not data:
            return None
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP
        )
        return text_splitter.split_documents(data)
