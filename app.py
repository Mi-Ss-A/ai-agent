from flask import Flask
from api.routes import api
from config import Config
from api.routes import ChatbotAPI

app = Flask(__name__)
app.register_blueprint(api, url_prefix='/api')

chatbot_api = ChatbotAPI()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)