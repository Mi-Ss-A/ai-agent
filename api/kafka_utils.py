from kafka import KafkaProducer
import json
from datetime import datetime
import time
import logging, os

# Logger 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL", "localhost:9092")  # 기본값은 localhost
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "chat-topic")  # 기본값은 chat-topic

def create_kafka_producer(retries=3, retry_delay=5):
    """Kafka Producer 생성 함수 with 재시도 로직"""
    for i in range(retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers=[KAFKA_BROKER_URL],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                api_version=(0, 10, 1),  # API 버전 명시
                acks='all',  # 모든 복제본이 메시지를 받았는지 확인
                retries=3,  # 재시도 횟수
                retry_backoff_ms=1000,  # 재시도 간격
                request_timeout_ms=30000,  # 요청 타임아웃
                security_protocol="PLAINTEXT"
            )
            print("Successfully connected to Kafka")
            return producer
        except Exception as e:
            print(f"Attempt {i + 1}/{retries} failed: {str(e)}")
            if i < retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                raise Exception("Failed to connect to Kafka after multiple attempts")


# Kafka Producer 초기화
try:
    producer = create_kafka_producer()
except Exception as e:
    print(f"Failed to initialize Kafka producer: {str(e)}")
    producer = None


def send_message_to_kafka(content: str, sender: str, sessionId: str) -> None:
    """Kafka로 메시지를 전송하는 헬퍼 함수"""
    if producer is None:
        raise Exception("Kafka producer not initialized")

    message = {
        'content': content,
        'sender': sender,
        'timestamp': datetime.now().isoformat(),
        'sessionId': sessionId  
    }

    try:
        future = producer.send(KAFKA_TOPIC, value=message)
        record_metadata = future.get(timeout=10)
        print(f"Message sent to partition {record_metadata.partition} at offset {record_metadata.offset}")
        print(f"Sent message: {json.dumps(message, ensure_ascii=False)}")
    except Exception as e:
        print(f"Error sending message: {str(e)}")
        raise


def send_to_kafka(user_message: str, ai_response: str,session_id: str = None) -> bool:
    """Kafka로 사용자 메시지와 AI 응답을 전송하는 함수."""
    try:
        # 사용자 메시지 전송
        send_message_to_kafka(
            content=user_message,
            sender="USER",
            sessionId=session_id  # 메타데이터 포함
        )
        # AI 응답 전송
        send_message_to_kafka(
            content=ai_response,
            sender="AI",
            sessionId=session_id 
        )
        return True
    except Exception as e:
        logger.error(f"Kafka 메시지 전송 실패: {e}")
        return False
