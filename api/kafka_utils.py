from kafka import KafkaProducer
import json
from datetime import datetime

# Kafka Producer 설정
producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

#kafka 토픽이름 
KAFKA_TOPIC = 'chat-messages'

def send_to_kafka(user_message, ai_response):
    """Kafka로 메시지를 전송하는 함수"""
    try:
        message = {
            'timestamp': datetime.now().isoformat(),
            'user_message': user_message,
            'ai_response': ai_response,
            'message_type': 'chat_interaction'
        }
        
        # 비동기로 메시지 전송
        future = producer.send(KAFKA_TOPIC, value=message)
        future.get(timeout=10)  # 전송 결과 확인
        print(json.dumps(message).encode('utf-8') + " 전송")
        print(f"Message sent to Kafka topic {KAFKA_TOPIC}")
        
    except Exception as e:
        print(f"Error sending message to Kafka: {str(e)}")
