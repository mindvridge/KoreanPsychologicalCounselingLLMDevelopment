"""
서버 시작 스크립트
"""
import os
import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv()

# 로깅 설정
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        logger.info("서버 시작 중...")
        logger.info(f"작업 디렉토리: {os.getcwd()}")
        logger.info(f"CONFIG_PATH: {os.getenv('CONFIG_PATH', '없음')}")
        logger.info(f"OPENAI_API_KEY: {'설정됨' if os.getenv('OPENAI_API_KEY') else '없음'}")
        
        import uvicorn
        uvicorn.run(
            "src.api:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"서버 시작 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

