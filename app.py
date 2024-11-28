from flask import Flask
from api.routes import api_agent
from flask_cors import CORS #front 연결 위한 cors 설정 
from config import Config
from api.routes import ChatbotAPI


app = Flask(__name__)
# CORS 설정: React 애플리케이션 도메인 허용
CORS(app, origins=["http://localhost:3000", "http://localhost:8081"], supports_credentials=True)
app.register_blueprint(api_agent) #api 라우팅


chatbot_api = ChatbotAPI()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)