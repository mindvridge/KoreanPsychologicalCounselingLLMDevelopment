"""
PyTorch 업그레이드 스크립트
서버가 실행 중인 Python 환경에서 torch를 2.6.0 이상으로 업그레이드합니다.
"""

import sys
import subprocess

def upgrade_torch():
    """PyTorch를 2.6.0 이상으로 업그레이드"""
    print("=" * 60)
    print("PyTorch 업그레이드 스크립트")
    print("=" * 60)
    print(f"현재 Python 경로: {sys.executable}")
    print(f"Python 버전: {sys.version}")
    print()
    
    try:
        import torch
        current_version = torch.__version__
        print(f"현재 PyTorch 버전: {current_version}")
        
        # 버전 확인
        version_parts = current_version.split('+')[0].split('.')
        major, minor = int(version_parts[0]), int(version_parts[1])
        
        if major < 2 or (major == 2 and minor < 6):
            print("\nPyTorch 2.6.0 이상으로 업그레이드가 필요합니다.")
            print("\n업그레이드 명령어:")
            print("  pip install --upgrade torch>=2.6.0")
            print("\n또는 CUDA 버전에 맞게:")
            print("  pip install --upgrade torch>=2.6.0 --index-url https://download.pytorch.org/whl/cu121")
            print()
            
            # 업그레이드 실행
            response = input("지금 업그레이드하시겠습니까? (y/n): ")
            if response.lower() == 'y':
                print("\n업그레이드 중...")
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", 
                    "--upgrade", "torch>=2.6.0",
                    "--index-url", "https://download.pytorch.org/whl/cu121"
                ])
                print("\n업그레이드 완료!")
                print("\n서버를 재시작하세요.")
            else:
                print("업그레이드를 건너뜁니다.")
        else:
            print(f"\n✓ PyTorch 버전이 충분합니다: {current_version}")
            print("추가 업그레이드가 필요하지 않습니다.")
            
    except ImportError:
        print("PyTorch가 설치되어 있지 않습니다.")
        print("다음 명령어로 설치하세요:")
        print("  pip install torch>=2.6.0 --index-url https://download.pytorch.org/whl/cu121")
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    upgrade_torch()

