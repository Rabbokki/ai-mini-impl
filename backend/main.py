from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes.auth import router as auth_router
from backend.post.routes.posts import router as posts_router
import uvicorn

# FastAPI 애플리케이션 생성 (Swagger UI 설정 포함)
app = FastAPI(
    title="Mini Project API",
    description="사용자 인증과 블로그 포스트 기능을 제공하는 통합 API",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI 경로
    redoc_url="/redoc"  # ReDoc 경로
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영환경에서는 구체적인 도메인을 지정해야 합니다
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(posts_router, prefix="/api/posts", tags=["Posts"])

# 기본 루트 엔드포인트
@app.get("/", tags=["Root"])
async def root():
    """API 루트 엔드포인트"""
    return {
        "message": "Mini Project API",
        "docs": "/docs",
        "redoc": "/redoc",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    print("FastAPI 서버가 시작됩니다. http://localhost:8000/docs 에서 Swagger UI를 확인하실 수 있습니다.")
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
