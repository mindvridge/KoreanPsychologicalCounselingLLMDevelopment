"""API 모듈 임포트 테스트"""
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
print("API 모듈 임포트 테스트")
print("="*70)

try:
    from src.api import app
    print("\n✅ API 모듈 임포트 성공!")
    print(f"앱 타입: {type(app)}")
    print(f"앱 제목: {app.title}")
except Exception as e:
    print(f"\n❌ API 모듈 임포트 실패: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*70)
print("✅ 모든 테스트 통과!")
print("="*70)

