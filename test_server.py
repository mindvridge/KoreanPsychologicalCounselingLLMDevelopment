"""
서버 시작 테스트 스크립트
"""
import sys
import os
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv()

print("="*70)
print("서버 시작 테스트")
print("="*70)

# 1. 환경 변수 확인
print("\n[1] 환경 변수 확인:")
print(f"  CONFIG_PATH: {os.getenv('CONFIG_PATH', '없음')}")
print(f"  OPENAI_API_KEY: {'설정됨' if os.getenv('OPENAI_API_KEY') else '없음'}")

# 2. 필수 모듈 임포트 테스트
print("\n[2] 모듈 임포트 테스트:")
try:
    from src.api import app
    print("  ✅ src.api 임포트 성공")
except Exception as e:
    print(f"  ❌ src.api 임포트 실패: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 3. 통합 시스템 임포트 테스트
print("\n[3] 통합 시스템 임포트 테스트:")
try:
    from main_integrated import IntegratedMentalHealthSystem
    print("  ✅ IntegratedMentalHealthSystem 임포트 성공")
except Exception as e:
    print(f"  ⚠️ IntegratedMentalHealthSystem 임포트 실패: {e}")
    print("  (서버는 실행되지만 일부 기능이 제한될 수 있습니다)")

# 4. 서버 시작
print("\n[4] 서버 시작:")
print("  Uvicorn 서버를 시작합니다...")
print("="*70)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )

