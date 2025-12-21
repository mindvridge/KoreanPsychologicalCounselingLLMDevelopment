"""
Windows 실행파일 빌드 스크립트
PyInstaller를 사용하여 .exe 파일 생성
"""

import os
import sys
import subprocess
from pathlib import Path

# Windows 인코딩 문제 해결
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent

def check_pyinstaller():
    """PyInstaller 설치 확인"""
    try:
        import PyInstaller
        print("[OK] PyInstaller가 설치되어 있습니다.")
        return True
    except ImportError:
        print("[INFO] PyInstaller가 설치되어 있지 않습니다.")
        print("설치 중...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("[OK] PyInstaller 설치 완료")
        return True

def create_spec_file():
    """PyInstaller spec 파일 생성"""
    # 데이터 파일 경로 확인
    datas = []
    data_dirs = ['configs', 'frontend', 'knowledge_base', 'data', 'voice_profiles']
    for dir_name in data_dirs:
        dir_path = PROJECT_ROOT / dir_name
        if dir_path.exists():
            datas.append((str(dir_path), dir_name))
    
    # .env 파일 확인
    env_path = PROJECT_ROOT / '.env'
    if env_path.exists():
        datas.append((str(env_path), '.'))
    
    # datas 리스트를 문자열로 변환 (경로를 raw string으로 변환)
    datas_str = ',\n    '.join([f"(r'{src}', '{dst}')" for src, dst in datas])
    
    # PROJECT_ROOT 경로 (raw string)
    project_root_str = str(PROJECT_ROOT).replace('\\', '\\\\')
    
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
# 마음챗 Windows 실행파일 빌드 스펙

import sys
from pathlib import Path

block_cipher = None

# 프로젝트 루트 경로
PROJECT_ROOT = Path(r'{project_root_str}')

# 데이터 파일들
datas = [
    {datas_str}
]

# 숨겨진 임포트들 (동적 임포트 포함)
hiddenimports = [
    # 웹 프레임워크
    'uvicorn',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.websockets',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'fastapi',
    'fastapi.middleware',
    'fastapi.middleware.cors',
    'fastapi.responses',
    'fastapi.staticfiles',
    'starlette',
    'starlette.applications',
    'starlette.middleware',
    'starlette.routing',
    'starlette.websockets',
    'pydantic',
    'pydantic.fields',
    'pydantic.types',
    
    # 데이터베이스
    'sqlalchemy',
    'sqlalchemy.orm',
    'sqlalchemy.ext',
    'sqlalchemy.ext.declarative',
    
    # 딥러닝 프레임워크
    'torch',
    'torch.nn',
    'torch.utils',
    'torch._dynamo',
    'transformers',
    'transformers.models',
    'transformers.tokenization_utils',
    'accelerate',
    'bitsandbytes',
    'peft',
    
    # 오디오 처리
    'soundfile',
    'librosa',
    'librosa.core',
    'librosa.filters',
    'audioread',
    'sounddevice',
    'webrtcvad',
    
    # STT/TTS
    'whisper',
    'whisper.model',
    'whisper.audio',
    'faster_whisper',
    'faster_whisper.transcribe',
    'zonos',
    'zonos.model',
    'zonos.conditioning',
    'zonos.utils',
    'phonemizer',
    'phonemizer.backend',
    'phonemizer.backend.espeak',
    'phonemizer.backend.espeak.wrapper',
    'gtts',
    'TTS',
    
    # API 클라이언트
    'openai',
    'httpx',
    'websockets',
    'aiofiles',
    
    # 설정 및 유틸리티
    'dotenv',
    'yaml',
    'prometheus_client',
    'slowapi',
    'psutil',
    'tqdm',
    'requests',
    
    # 한국어 처리
    'kobert_tokenizer',
    'konlpy',
    'konlpy.tag',
    
    # RAG 및 벡터 DB
    'langchain',
    'chromadb',
    'sentence_transformers',
    
    # 데이터 처리
    'datasets',
    'scipy',
    'pandas',
    'numpy',
    
    # 로깅 및 보안
    'loguru',
    'cryptography',
    
    # UI
    'gradio',
    
    # 프로젝트 모듈
    'src',
    'src.api',
    'src.voice_api',
    'src.tts',
    'src.stt',
    'src.streaming_tts',
    'src.voice_streaming',
    'src.openai_adapter',
    'src.gpu_check',  # GPU 검증 모듈
    'main_integrated',  # 통합 시스템 메인 모듈
    'main_integrated.IntegratedMentalHealthSystem',  # 명시적 클래스 임포트
]

a = Analysis(
    ['start_all.py'],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'matplotlib',  # 불필요한 라이브러리 제외
        'tkinter',     # GUI 라이브러리 제외
        'PIL',         # 이미지 처리 제외 (필요시 포함)
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='마음챗',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX는 때때로 문제를 일으킬 수 있음
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 콘솔 창 표시 (디버깅용)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 아이콘 파일이 있으면 경로 지정
    version=None,  # 버전 정보 파일이 있으면 경로 지정
)
"""
    
    spec_path = PROJECT_ROOT / "마음챗.spec"
    with open(spec_path, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print(f"[OK] Spec 파일 생성: {spec_path}")
    return spec_path

def build_exe():
    """실행파일 빌드"""
    print("\n" + "="*60)
    print("마음챗 Windows 실행파일 빌드 시작")
    print("="*60 + "\n")
    
    # PyInstaller 확인
    if not check_pyinstaller():
        return False
    
    # Spec 파일 생성
    spec_path = create_spec_file()
    
    # 빌드 명령 실행
    print("\n빌드 시작...")
    print("이 작업은 몇 분이 걸릴 수 있습니다.\n")
    
    try:
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean",  # 빌드 전 임시 파일 정리
            "--noconfirm",  # 기존 파일 덮어쓰기 확인 없음
            str(spec_path)
        ]
        
        subprocess.check_call(cmd, cwd=str(PROJECT_ROOT))
        
        print("\n" + "="*60)
        print("[OK] 빌드 완료!")
        print("="*60)
        print(f"\n실행파일 위치: {PROJECT_ROOT / 'dist' / '마음챗.exe'}")
        print(f"\n실행 방법:")
        print(f"  1. dist 폴더로 이동")
        print(f"  2. '마음챗.exe' 더블클릭 또는 명령줄에서 실행")
        print(f"\n주의사항:")
        print(f"  - .env 파일이 필요합니다 (API 키 등)")
        print(f"  - espeak-ng가 설치되어 있어야 합니다")
        print(f"  - CUDA가 설치되어 있어야 GPU를 사용할 수 있습니다")
        print(f"  - 모든 데이터 파일이 dist 폴더에 포함되어 있습니다")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] 빌드 실패: {e}")
        return False
    except Exception as e:
        print(f"\n[ERROR] 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = build_exe()
    sys.exit(0 if success else 1)

