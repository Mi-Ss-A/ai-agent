import sys
import requests
from flask import Blueprint, request, jsonify
from langchain.agents.agent_toolkits import create_retriever_tool   
sys.path.append('..')
from models.document_loader import DocumentLoader
from models.vector_store import VectorStore
from models.chat_agent import ChatAgent
import traceback
from api.kafka_utils import send_to_kafka  # Kafka 메시지 전송 함수 임포트
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api_agent = Blueprint('api_agent', __name__, url_prefix='/api')

class ChatbotAPI:
    def __init__(self):
        self.doc_loader = DocumentLoader()
        self.vector_store = VectorStore()
        self.chat_agent = ChatAgent()
        self.agent_executor = None
        self.initialize_chatbot()

    def initialize_chatbot(self):
        try:
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
            logger.info("챗봇 에이전트 초기화 완료")
        except Exception as e:
            logger.error("챗봇 초기화 중 에러 발생", exc_info=True)

# ChatbotAPI 클래스 인스턴스를 생성
chatbot_api = ChatbotAPI()

#front(react) 서버로 부터 text 전달 
@api_agent.route('/agent/chat', methods=['POST'])
def chat():
    # 요청 데이터 확인
    data = request.json
    if not data:
        logger.warning("요청 데이터가 없습니다.")
        return jsonify({'error': 'No data provided'}), 400

    user_message = data.get('message')
    sessionId = data.get('sessionId')

    # 필수 필드 확인
    if not user_message or not isinstance(user_message, str):
        logger.warning("유효하지 않은 메시지: %s", user_message)
        return jsonify({'error': 'Invalid or missing "message" field'}), 400

    if not sessionId or not isinstance(sessionId, str):
        logger.warning("유효하지 않은 세션 ID: %s", sessionId)
        return jsonify({'error': 'Invalid or missing "sessionId" field'}), 400

    logger.info(f"Received request with sessionId: {sessionId} and message: {user_message}")

    try:
        # 챗봇 에이전트 실행
        result = chatbot_api.agent_executor({"input": user_message})
        if not result or 'output' not in result:
            logger.error("예상치 못한 응답 형식: %s", result)
            return jsonify({'error': 'Unexpected response format', 'status': 'error'}), 500

        ai_response = result['output']

        # Kafka로 메시지 전송
        try:
            kafka_success = send_to_kafka(user_message, ai_response,sessionId)
            if not kafka_success:
                logger.warning("Kafka 메시지 전송 실패")
                return jsonify({'error': 'Kafka message sending failed', 'status': 'error'}), 500
        except Exception as kafka_error:
            logger.error("Kafka 메시지 전송 중 오류 발생", exc_info=True)
            return jsonify({'error': str(kafka_error), 'status': 'error'}), 500

        # 성공 응답
        logger.info(f"AI 응답 전송 성공: {ai_response}")
        return jsonify({
            'response': ai_response,
            'status': 'success'
        })
    except Exception as e:
        logger.error("챗봇 처리 중 에러 발생", exc_info=True)
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500
    
    
@api_agent.route('/agent/portfolio', methods=['POST'])
def portfolio():
    data = request.json
    period = data.get('period')
    sessionId = data.get('sessionId')  # sessionId 확인 및 활용

    logger.info("sessionId : %s",sessionId)

    if not period:
        logger.warning("기간 정보가 요청에 포함되지 않았습니다.")
        return jsonify({'error': 'No period provided'}), 400

    if not sessionId:
        logger.warning("세션 ID가 요청에 포함되지 않았습니다.")
        return jsonify({'error': 'No session ID provided'}), 400

    try:
        # Spring 서버 URL 가져오기
        SPRING_SERVER_URL = "http://localhost:8082/api/portfolio"


        # Spring 서버로 API 요청
        spring_response = requests.post(
            SPRING_SERVER_URL,
            json={"period": period, "redisSessionId": sessionId}  # sessionId 포함
        )

        if spring_response.status_code != 200:
            logger.error("Spring 서버 응답 오류: %s", spring_response.text)
            return jsonify({
                'error': 'Error from Spring server',
                'details': spring_response.text,
                'status': 'error'
            }), spring_response.status_code

        logger.info("Spring 서버 응답 성공: %s", spring_response.json())

        # Spring 응답 데이터를 Flask에서 React로 전달

        return jsonify(spring_response.json())
    except requests.exceptions.RequestException as e:
        logger.error("Spring 서버 요청 중 네트워크 에러 발생", exc_info=True)
        return jsonify({
            'error': 'Failed to connect to Spring server',
            'details': str(e),
            'status': 'error'
        }), 502

    except Exception as e:
        logger.error("포트폴리오 처리 중 내부 서버 에러 발생", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'details': str(e),
            'status': 'error'
        }), 500