# 베이스 이미지 설정 - Python 3.9 사용
FROM python:3.9-slim

# 작업 디렉터리 설정
WORKDIR /app

# 필요한 패키지 설치를 위해 requirements.txt 파일을 컨테이너로 복사
COPY requirements.txt requirements.txt

# 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# Flask 애플리케이션 파일을 컨테이너로 복사
COPY . .

# 환경 변수 설정 (Flask 애플리케이션이 실행될 포트, 프로덕션에서 DEBUG는 False로 설정)
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000
ENV FLASK_ENV=production

# Flask 애플리케이션 실행
CMD ["flask", "run"]
