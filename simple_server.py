"""
간단한 테스트 서버 - 오류 확인용
"""
import sys
import os
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv()

print("="*70)
print("간단한 테스트 서버 시작")
print("="*70)

# FastAPI 앱 생성
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Korean Mental Health API - Test")

@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "서버가 정상 작동 중입니다",
        "endpoints": {
            "health": "/api/v1/health",
            "docs": "/docs"
        }
    }

@app.get("/api/v1/health")
def health():
    return {
        "status": "healthy",
        "timestamp": "2025-12-10T15:30:00"
    }

if __name__ == "__main__":
    import uvicorn
    print("\n서버 시작: http://127.0.0.1:8000")
    print("="*70)
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

