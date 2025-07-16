import os
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from typing import Optional
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoDB:
    """MongoDB 연결 및 관리 클래스"""
    
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db = None
        self.posts_collection = None
        
        # MongoDB 연결 설정
        self.mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.database_name = os.getenv("DATABASE_NAME", "mini_blog")
        self.posts_collection_name = "posts"
    
    def connect(self):
        """MongoDB에 연결"""
        try:
            self.client = MongoClient(self.mongodb_url, serverSelectionTimeoutMS=5000)
            
            # 연결 테스트
            self.client.admin.command('ping')
            logger.info("MongoDB 연결 성공")
            
            # 데이터베이스 선택
            self.db = self.client[self.database_name]
            self.posts_collection = self.db[self.posts_collection_name]
            
            # 컬렉션 초기화
            self._initialize_collection()
            
            return True
            
        except ConnectionFailure as e:
            logger.error(f"MongoDB 연결 실패: {e}")
            return False
        except Exception as e:
            logger.error(f"MongoDB 초기화 중 오류: {e}")
            return False
    
    def _initialize_collection(self):
        """posts 컬렉션 초기화 및 인덱스 설정"""
        try:
            if self.posts_collection is None:
                logger.error("posts_collection이 초기화되지 않았습니다")
                return
                
            # 기존 인덱스 확인
            existing_indexes = list(self.posts_collection.list_indexes())
            index_names = [index['name'] for index in existing_indexes]
            
            # 필요한 인덱스들 생성
            indexes_to_create = []
            
            # 1. created_at 인덱스 (최신 글 조회용)
            if 'created_at_desc' not in index_names:
                indexes_to_create.append(
                    ("created_at", DESCENDING)
                )
            
            # 2. status 인덱스 (글 상태별 조회용)
            if 'status_asc' not in index_names:
                indexes_to_create.append(
                    ("status", ASCENDING)
                )
            
            # 3. 복합 인덱스: status + created_at (효율적인 게시글 목록 조회용)
            if 'status_created_at_compound' not in index_names:
                indexes_to_create.append(
                    [("status", ASCENDING), ("created_at", DESCENDING)]
                )
            
            # 인덱스 생성
            for index in indexes_to_create:
                if isinstance(index, tuple):
                    self.posts_collection.create_index([index])
                    logger.info(f"인덱스 생성: {index}")
                else:
                    self.posts_collection.create_index(index)
                    logger.info(f"복합 인덱스 생성: {index}")
            
            logger.info("posts 컬렉션 초기화 완료")
            
        except Exception as e:
            logger.error(f"컬렉션 초기화 중 오류: {e}")
    
    def disconnect(self):
        """MongoDB 연결 해제"""
        if self.client:
            self.client.close()
            logger.info("MongoDB 연결 해제")
    
    def get_posts_collection(self):
        """posts 컬렉션 반환"""
        return self.posts_collection
    
    def check_connection(self) -> bool:
        """연결 상태 확인"""
        try:
            if self.client:
                self.client.admin.command('ping')
                return True
        except:
            pass
        return False
    
    def create_post_document(self, post_data: dict) -> dict:
        """posts 컬렉션에 맞는 문서 구조 생성"""
        return {
            "post_id": post_data["id"],  # FastAPI에서 사용하는 id를 post_id로 저장
            "title": post_data["title"],
            "content": post_data["content"],
            "status": post_data["status"],
            "images": post_data.get("images", []),  # 이미지 정보 목록
            "created_at": post_data["created_at"],
            "updated_at": post_data["updated_at"]
        }
    
    def get_database_info(self) -> dict:
        """데이터베이스 정보 반환"""
        try:
            if self.db is None:
                return {"error": "데이터베이스에 연결되지 않음"}
            
            if self.posts_collection is None:
                return {"error": "컬렉션이 초기화되지 않음"}
            
            # 컬렉션 통계
            stats = self.db.command("collStats", self.posts_collection_name)
            
            return {
                "database_name": self.database_name,
                "collection_name": self.posts_collection_name,
                "document_count": stats.get("count", 0),
                "storage_size": stats.get("storageSize", 0),
                "indexes": list(self.posts_collection.list_indexes())
            }
        except Exception as e:
            return {"error": f"데이터베이스 정보 조회 실패: {e}"}

# 전역 MongoDB 인스턴스
mongodb_client = MongoDB()

def get_mongodb():
    """MongoDB 클라이언트 반환"""
    return mongodb_client

def init_mongodb():
    """MongoDB 초기화"""
    success = mongodb_client.connect()
    if success:
        logger.info("MongoDB 초기화 완료")
    else:
        logger.error("MongoDB 초기화 실패")
    return success 