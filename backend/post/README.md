# Mini Blog API - MongoDB 설정 가이드

## 📋 요구사항

- Python 3.8+
- MongoDB (로컬 설치 또는 Docker)

## 🚀 설정 및 실행 방법

### 1. 의존성 설치

```bash
pip install -r ../../../requirements.txt
```

### 2. MongoDB 설치 및 실행

#### Windows
```bash
# MongoDB Community Server 다운로드 및 설치
# https://www.mongodb.com/try/download/community

# MongoDB 서비스 시작
net start MongoDB
```

#### macOS
```bash
# Homebrew로 설치
brew install mongodb-community

# MongoDB 서비스 시작
brew services start mongodb-community
```

#### Docker 사용 (모든 OS)
```bash
# MongoDB 컨테이너 실행
docker run -d --name mongodb -p 27017:27017 mongo:latest
```

### 3. 데이터베이스 초기화

```bash
# database 디렉토리로 이동
cd database

# 데이터베이스 초기화 스크립트 실행
python init_db.py
```

### 4. FastAPI 애플리케이션 실행

```bash
# post 디렉토리로 이동 (app.py가 있는 곳)
cd ..

# 애플리케이션 실행
python app.py
```

### 5. API 테스트

- **API 문서**: http://localhost:8000/docs
- **ReDoc 문서**: http://localhost:8000/redoc
- **헬스 체크**: http://localhost:8000/health

## 🗂️ 데이터베이스 구조

### posts 컬렉션

```javascript
{
  "_id": ObjectId("..."),           // MongoDB 고유 ID
  "post_id": "uuid-string",         // FastAPI에서 사용하는 글 ID
  "title": "글 제목",                // 글 제목 (최대 100자)
  "content": "글 내용",              // 글 내용
  "author": "작성자명",              // 작성자
  "status": "published|deleted",    // 글 상태
  "created_at": ISODate("..."),     // 생성일시
  "updated_at": ISODate("...")      // 수정일시
}
```

### 인덱스 설정

1. **created_at_desc**: 최신 글 조회용
2. **status_asc**: 글 상태별 조회용  
3. **author_asc**: 작성자별 조회용
4. **status_created_at_compound**: 효율적인 게시글 목록 조회용

## 🔧 환경변수 설정

`.env` 파일을 생성하여 설정을 변경할 수 있습니다:

```bash
# MongoDB 설정
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=mini_blog

# FastAPI 설정  
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
```

## 📚 API 엔드포인트

| 메서드 | 엔드포인트 | 설명 |
|--------|------------|------|
| POST | `/posts/` | 글 작성 |
| GET | `/posts/` | 글 목록 조회 |
| PUT | `/posts/{post_id}` | 글 수정 |
| DELETE | `/posts/{post_id}` | 글 삭제 |
| GET | `/health` | 헬스 체크 |
| GET | `/posts/health` | 글 서비스 헬스 체크 |

## 🔍 문제 해결

### MongoDB 연결 실패
1. MongoDB 서비스가 실행 중인지 확인
2. 포트 27017이 사용 중인지 확인
3. 방화벽 설정 확인

### 의존성 오류
```bash
pip install --upgrade pymongo motor fastapi uvicorn pydantic
```

### 포트 충돌
`.env` 파일에서 `API_PORT` 변경 또는:
```bash
python app.py --port 8001
```

## 🧪 샘플 데이터

`init_db.py` 실행 시 다음 샘플 글이 생성됩니다:

1. **첫 번째 글** (published)
2. **두 번째 글** (published)  
3. **삭제될 글** (deleted) - 목록에서 보이지 않음

## 📞 지원

문제가 발생하면 다음을 확인해주세요:

1. MongoDB 서비스 상태
2. Python 의존성 설치 상태
3. 포트 사용 현황
4. 로그 메시지 