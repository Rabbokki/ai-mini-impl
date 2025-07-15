from pymongo import MongoClient
from dotenv import load_dotenv
import os

# .env 파일에서 환경변수 로드
load_dotenv()

# MongoDB 연결
client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'))
db = client['mini_project']  # 데이터베이스 이름

# 컬렉션 정의
users = db['users']  # 사용자 컬렉션



