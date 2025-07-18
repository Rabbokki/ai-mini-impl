from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from openai import OpenAI
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import logging

# 로깅 설정 (UTF-8 인코딩 보장)
logging.basicConfig(level=logging.INFO, encoding='utf-8')
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

# FastAPI 앱 초기화
app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 프론트엔드 도메인으로 제한하세요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI 클라이언트 초기화
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    http_client=None  # 기본 HTTP 클라이언트 사용, 프록시 설정 무시
)

# 요청 모델 정의
class DiaryEntry(BaseModel):
    date: str  # 예상 형식: YYYY-MM-DD
    text: str

# 응답 모델 정의
class ComfortResponse(BaseModel):
    message: str

@app.post("/analyze-diary", response_model=ComfortResponse)
async def analyze_diary(entry: DiaryEntry):
    try:
        # 날짜 형식 검증
        if not entry.date or len(entry.date) != 10 or entry.date[4] != '-' or entry.date[7] != '-':
            raise HTTPException(status_code=400, detail="잘못된 날짜 형식입니다. YYYY-MM-DD 형식을 사용하세요")

        # OpenAI 프롬프트 준비
        prompt = f"""
        사용자가 작성한 한국어 일기를 분석하고, 따뜻하고 위로가 되는 한국어 메시지를 작성해 주세요.
        일기 내용: {entry.text}
        메시지는 긍정적이고 공감적인 톤으로, 2-3문장으로 작성해 주세요.
        """

        # 프롬프트 로깅 (UTF-8 인코딩 보장)
        logger.info(f"Calling OpenAI API with prompt: {prompt[:100].encode('utf-8').decode('utf-8')}...")

        # OpenAI API 호출
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # 필요 시 모델 변경 (예: gpt-4o)
            messages=[
                {"role": "system", "content": "당신은 따뜻하고 공감적인 조언을 제공하는 AI입니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.7
        )

        # 응답 검증
        if not response.choices or not response.choices[0].message.content:
            logger.error("OpenAI API returned empty response or no content")
            raise HTTPException(status_code=500, detail="OpenAI API에서 유효한 응답을 받지 못했습니다")

        # 위로 메시지 추출
        comfort_message = response.choices[0].message.content.strip()
        logger.info(f"Received response: {comfort_message.encode('utf-8').decode('utf-8')}")

        return ComfortResponse(message=comfort_message)

    except Exception as e:
        logger.error(f"Error processing diary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"일기 처리 중 오류 발생: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "API가 실행 중입니다"}