# -*- mode: python ; coding: utf-8 -*-
# 마음챗 Windows 실행파일 빌드 스펙

import sys
from pathlib import Path

block_cipher = None

# 프로젝트 루트 경로
PROJECT_ROOT = Path(r'C:\\KoreanPsychologicalCounselingLLMDevelopment')

# 데이터 파일들
datas = [
    (r'C:\KoreanPsychologicalCounselingLLMDevelopment\configs', 'configs'),
    (r'C:\KoreanPsychologicalCounselingLLMDevelopment\frontend', 'frontend'),
    (r'C:\KoreanPsychologicalCounselingLLMDevelopment\knowledge_base', 'knowledge_base'),
    (r'C:\KoreanPsychologicalCounselingLLMDevelopment\data', 'data'),
    (r'C:\KoreanPsychologicalCounselingLLMDevelopment\voice_profiles', 'voice_profiles'),
    (r'C:\KoreanPsychologicalCounselingLLMDevelopment\.env', '.')
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
    'main_integrated',
]

a = Analysis(
    ['start_all.py'],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
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
