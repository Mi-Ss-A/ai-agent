import sys
from flask import Blueprint, request, jsonify
from langchain.agents.agent_toolkits import create_retriever_tool   
sys.path.append('..')
from models.document_loader import DocumentLoader
from models.vector_store import VectorStore
from models.chat_agent import ChatAgent
import traceback
from api.kafka_utils import send_to_kafka  # Kafka 메시지 전송 함수 임포트

api = Blueprint('api', __name__)

class ChatbotAPI:
    def __init__(self):
        self.doc_loader = DocumentLoader()
        self.vector_store = VectorStore()
        self.chat_agent = ChatAgent()
        self.agent_executor = None
        self.initialize_chatbot()

    def initialize_chatbot(self):
        # 문서 로드 및 벡터 저장소 초기화
        faq_data = self.doc_loader.load_faq_documents()
        splits = self.doc_loader.split_documents(faq_data)
        retriever = self.vector_store.initialize_store(splits)
        
        # 검색 도구 생성
        tool = create_retriever_tool(
            retriever,
            "wibee_ChatBot",
            "Searches and returns information regarding the financial service guide.",
        )
        
        # 에이전트 생성
        self.agent_executor = self.chat_agent.create_agent([tool])

# ChatbotAPI 클래스 인스턴스를 생성
chatbot_api = ChatbotAPI()

#front(react) 서버로 부터 text 전달 
@api.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message')
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    try:
        # chatbot_api를 사용하여 agent_executor에 접근
        result = chatbot_api.agent_executor({"input": user_message})
         # 출력 결과가 예상된 형식인지 확인 (result.get('output') 사용)
        if not result or 'output' not in result:
            return jsonify({'error': 'Unexpected response format', 'status': 'error'}), 500
        
        ai_response = result['output']

        # Kafka로 사용자 메시지와 AI 응답 전송
        send_to_kafka(user_message, ai_response)
        
        # 정상적인 응답 반환
        return jsonify({
            'response': ai_response,
            'status': 'success'
        })
    except Exception as e:
    # 상세 에러 로그 기록 (디버깅용)
        error_message = str(e)
        error_trace = traceback.format_exc()  # traceback 추가
        print(f"Error occurred: {error_message}")
        print(f"Stack trace: {error_trace}")

        return jsonify({
            'error': error_message,
            'status': 'error'
        }), 500