from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from routes.posts import router as posts_router
from database.mongodb import init_mongodb

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="Mini Blog API",
    description="글 작성, 조회, 수정, 삭제 기능을 제공하는 간단한 블로그 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 애플리케이션 시작 시 MongoDB 초기화
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    print("애플리케이션을 시작합니다...")
    success = init_mongodb()
    if success:
        print("[OK] MongoDB 연결 성공")
    else:
        print("[WARNING] MongoDB 연결 실패 - 일부 기능이 제한될 수 있습니다")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경에서만 사용, 프로덕션에서는 구체적인 도메인 설정 필요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(posts_router)

# 루트 경로
@app.get("/")
async def root():
    """루트 경로 - API 정보 반환"""
    return {
        "message": "Mini Blog API에 오신 것을 환영합니다!",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

# 헬스 체크 엔드포인트
@app.get("/health")
async def health_check():
    """애플리케이션 상태 확인"""
    return {"status": "healthy", "message": "API가 정상적으로 작동 중입니다"}

# 전역 예외 처리기
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP 예외 처리"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """일반 예외 처리"""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "서버 내부 오류가 발생했습니다",
            "status_code": 500
        }
    )

# 애플리케이션 실행
if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 개발 환경에서만 사용
        log_level="info"
    ) 