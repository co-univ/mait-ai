import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.router import router
from app.api.health import router as health_router
from app.utils.utils import setup_logging
from app.middleware.request_id import RequestIDMiddleware

# 로깅 설정 초기화
setup_logging(log_level="INFO")

app = FastAPI(
    title="Java-Backend->Python-AI-Server",
    description="Java Spring 백엔드가 호출하는 AI 서비스",
    version="0.1.0"
)

# Request ID 미들웨어 추가 (가장 먼저 실행되도록)
app.add_middleware(RequestIDMiddleware)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록 (prefix 붙이기)
app.include_router(router, prefix="/api/ai")
app.include_router(health_router, prefix="/api/ai")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
