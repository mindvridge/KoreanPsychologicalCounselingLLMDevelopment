"""
간단한 API 서버 시작 스크립트
초기화 오류가 있어도 서버는 시작되도록 함
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
print("API 서버 시작 (간단 모드)")
print("="*70)

# FastAPI 앱 임포트
try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    import uvicorn
    
    # 기본 앱 생성
    app = FastAPI(
        title="Korean Mental Health Counseling API",
        description="AI-powered mental health counseling system",
        version="1.0.0"
    )
    
    # CORS 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/")
    def root():
        return {
            "name": "Korean Mental Health Counseling API",
            "version": "1.0.0",
            "status": "running",
            "endpoints": {
                "docs": "/docs",
                "health": "/api/v1/health"
            }
        }
    
    @app.get("/api/v1/health")
    def health():
        return {
            "status": "healthy",
            "timestamp": "2025-12-10T15:45:00",
            "components": {
                "api": True
            }
        }
    
    # 실제 API 모듈 로드 시도
    print("\n실제 API 모듈 로드 시도...")
    try:
        from src.api import app as full_app
        print("✅ 전체 API 모듈 로드 성공")
        app = full_app
    except Exception as e:
        print(f"⚠️ 전체 API 모듈 로드 실패: {e}")
        print("기본 API만 사용합니다.")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    print("서버 시작: http://127.0.0.1:8000")
    print("API 문서: http://127.0.0.1:8000/docs")
    print("="*70 + "\n")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )
    
except Exception as e:
    print(f"❌ 서버 시작 실패: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

