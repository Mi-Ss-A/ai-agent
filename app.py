from flask import Flask
from api.routes import api
from flask_cors import CORS #front 연결 위한 cors 설정 
from config import Config
from api.routes import ChatbotAPI


app = Flask(__name__)
CORS(app) #모든 출처에서 접근을 허용    
app.register_blueprint(api, url_prefix='/api') #api 라우팅


chatbot_api = ChatbotAPI()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)