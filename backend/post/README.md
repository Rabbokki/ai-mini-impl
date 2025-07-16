# Mini Blog API - MongoDB 설정 가이드

블로그 글 작성, 조회, 수정, 삭제 기능과 이미지 업로드(최대 3장, 5MB)를 지원하는 FastAPI 기반 REST API입니다.

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
- **이미지 파일**: http://localhost:8000/uploads/images/ (업로드된 이미지 접근)

## 🗂️ 데이터베이스 구조

### posts 컬렉션

```javascript
{
  "_id": ObjectId("..."),           // MongoDB 고유 ID
  "post_id": "uuid-string",         // FastAPI에서 사용하는 글 ID
  "title": "글 제목",                // 글 제목 (최대 100자)
  "content": "글 내용",              // 글 내용
  "status": "published|deleted",    // 글 상태
  "images": [                       // 첨부 이미지 목록
    {
      "filename": "uuid_filename.jpg",
      "original_filename": "original.jpg",
      "file_path": "uploads/images/uuid_filename.jpg",
      "file_size": 1024,
      "upload_date": ISODate("...")
    }
  ],
  "created_at": ISODate("..."),     // 생성일시
  "updated_at": ISODate("...")      // 수정일시
}
```

### 인덱스 설정

1. **created_at_desc**: 최신 글 조회용 (날짜별 정렬)
2. **status_asc**: 글 상태별 조회용  
3. **status_created_at_compound**: 효율적인 글 목록 조회용

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

**이미지 업로드 설정 (코드에서 하드코딩됨):**
- 최대 이미지 크기: 5MB
- 글당 최대 이미지 수: 3장
- 지원 형식: JPG, JPEG, PNG, GIF, WebP

## 📚 API 엔드포인트

### 글 관리
| 메서드 | 엔드포인트 | 설명 |
|--------|------------|------|
| POST | `/posts/` | 글 작성 |
| GET | `/posts/` | 글 목록 조회 |
| GET | `/posts/{post_id}` | 글 상세 조회 |
| PUT | `/posts/{post_id}` | 글 수정 |
| DELETE | `/posts/{post_id}` | 글 삭제 |

### 이미지 관리
| 메서드 | 엔드포인트 | 설명 |
|--------|------------|------|
| POST | `/posts/images/upload` | 임시 이미지 업로드 (최대 3장, 5MB) |
| DELETE | `/posts/images/temp/{filename}` | 임시 이미지 삭제 |

### 시스템
| 메서드 | 엔드포인트 | 설명 |
|--------|------------|------|
| GET | `/health` | 전체 시스템 헬스 체크 |
| GET | `/posts/health` | 일기 서비스 헬스 체크 |

## 🔍 문제 해결

### MongoDB 연결 실패
1. MongoDB 서비스가 실행 중인지 확인
2. 포트 27017이 사용 중인지 확인
3. 방화벽 설정 확인

### 의존성 오류
```bash
pip install --upgrade pymongo fastapi uvicorn pydantic python-multipart aiofiles
```

### 이미지 업로드 문제
1. 업로드 폴더 권한 확인: `uploads/images`, `uploads/temp`
2. 파일 크기 제한: 최대 5MB
3. 지원 형식: JPG, JPEG, PNG, GIF, WebP
4. 최대 이미지 수: 일기당 3장

### 포트 충돌
`.env` 파일에서 `API_PORT` 변경 또는:
```bash
python app.py --port 8001
```

## 🧪 데이터베이스 초기화

`init_db.py` 실행 시:

- Mini Blog 데이터베이스와 컬렉션 생성
- 필요한 인덱스 설정 (날짜, 상태 기반)
- **샘플 데이터는 생성하지 않음** (깔끔한 빈 블로그로 시작)

### 📝 첫 번째 글 작성 예시

**1. 이미지 없는 글 작성:**
```bash
curl -X POST "http://localhost:8000/posts/" \
-H "Content-Type: application/json" \
-d '{
  "title": "첫 번째 글",
  "content": "Mini Blog의 첫 번째 글입니다!",
  "status": "published"
}'
```

**2. 이미지가 있는 글 작성 워크플로우:**
```bash
# Step 1: 임시 이미지 업로드
curl -X POST "http://localhost:8000/posts/images/upload" \
-F "file=@my_photo.jpg"
# 응답: {"filename": "temp_uuid_filename.jpg", ...}

# Step 2: 임시 파일명을 포함하여 글 작성
curl -X POST "http://localhost:8000/posts/" \
-H "Content-Type: application/json" \
-d '{
  "title": "사진이 있는 글",
  "content": "오늘 찍은 사진과 함께",
  "images": ["temp_uuid_filename.jpg"],
  "status": "published"
}'
```

## 📞 지원

문제가 발생하면 다음을 확인해주세요:

1. MongoDB 서비스 상태
2. Python 의존성 설치 상태 (python-multipart, aiofiles 포함)
3. 포트 사용 현황 (8000, 27017)
4. 업로드 폴더 권한 (`uploads/images`, `uploads/temp`)
5. 로그 메시지

## 🎯 주요 특징

- ✅ **캘린더 형식**: 날짜별 글 조회 최적화
- ✅ **이미지 지원**: 글당 최대 3장, 5MB 이하
- ✅ **임시 업로드**: 이미지 미리 업로드 후 글 작성
- ✅ **상태 관리**: published/deleted 상태로 소프트 삭제
- ✅ **MongoDB**: NoSQL 기반 확장 가능한 구조
- ✅ **RESTful API**: 표준 HTTP 메서드 지원 