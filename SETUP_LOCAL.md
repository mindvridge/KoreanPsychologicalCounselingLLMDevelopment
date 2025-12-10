# 로컬 서버 구동 설정 가이드

## 📋 필수 사전 준비사항

### 1. 시스템 요구사항
- **Python**: 3.10 이상
- **GPU**: NVIDIA GPU (CUDA 지원, 선택사항)
  - 최소: 8GB VRAM (4-bit 양자화)
  - 권장: 16GB VRAM 이상
- **RAM**: 16GB 이상 권장
- **디스크**: 30GB 이상 (모델 캐시 포함)

### 2. 필수 소프트웨어
- Python 3.10+
- Git
- CUDA Toolkit (GPU 사용 시)

---

## 🚀 빠른 시작 (Windows)

### 방법 1: 자동 설정 스크립트 사용

```powershell
# PowerShell에서 실행
.\setup_local.ps1
```

스크립트가 자동으로:
- ✅ 가상환경 생성
- ✅ 의존성 설치
- ✅ 디렉토리 생성
- ✅ .env 파일 생성
- ✅ 데이터베이스 초기화

### 방법 2: 수동 설정

#### 1단계: 가상환경 생성 및 활성화

```powershell
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
.\venv\Scripts\Activate.ps1
```

#### 2단계: 의존성 설치

```powershell
# pip 업그레이드
python -m pip install --upgrade pip wheel setuptools

# PyTorch 설치 (CUDA 12.1)
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 나머지 의존성 설치
pip install -r requirements.txt
```

#### 3단계: 환경 변수 설정 (.env 파일 생성)

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 추가:

```env
# =============================================================================
# 필수 설정
# =============================================================================

# Hugging Face 토큰 (필수!)
# https://huggingface.co/settings/tokens 에서 발급
HUGGINGFACE_TOKEN=your_token_here

# CUDA 설정
CUDA_VISIBLE_DEVICES=0

# 로그 레벨
LOG_LEVEL=INFO

# =============================================================================
# 데이터베이스 설정
# =============================================================================

# SQLite (기본값, 개발용)
DATABASE_PATH=./data/mental_health.db
DATABASE_URL=sqlite:///./data/mental_health.db

# PostgreSQL (프로덕션 권장)
# DATABASE_URL=postgresql://user:password@localhost:5432/mental_health

# =============================================================================
# 장기 기억 설정
# =============================================================================

# 장기 기억 활성화
ENABLE_LONG_TERM_MEMORY=true

# 데이터 보관 기간 (일)
USER_DATA_RETENTION_DAYS=90

# PII 마스킹 활성화
MASK_PII=true

# =============================================================================
# 애플리케이션 설정
# =============================================================================

# 설정 파일 경로
CONFIG_PATH=configs/config.local-test.yaml

# API 설정
API_HOST=127.0.0.1
API_PORT=8000

# 테스트 모드
TEST_MODE=true

# API Key (선택사항, 보안 강화용)
# API_KEY=your_api_key_here
```

#### 4단계: 필요 디렉토리 생성

```powershell
# 디렉토리 생성
New-Item -ItemType Directory -Path "logs" -Force
New-Item -ItemType Directory -Path "outputs" -Force
New-Item -ItemType Directory -Path "voice_profiles" -Force
New-Item -ItemType Directory -Path "data\finetuning" -Force
```

#### 5단계: 데이터베이스 초기화

```powershell
# 데이터베이스 테이블 생성
python -c "from src.database import DatabaseManager; db = DatabaseManager(); print('데이터베이스 초기화 완료')"
```

---

## 🎯 서버 실행 방법

### 옵션 1: Gradio 웹 인터페이스 (추천)

```powershell
# 가상환경 활성화
.\venv\Scripts\Activate.ps1

# Gradio 서버 실행
python app.py
```

접속: http://localhost:7860

### 옵션 2: FastAPI 서버

```powershell
# 가상환경 활성화
.\venv\Scripts\Activate.ps1

# API 서버 실행
uvicorn src.api:app --host 127.0.0.1 --port 8000 --reload
```

접속:
- API: http://localhost:8000
- API 문서: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 옵션 3: 통합 시스템

```powershell
# 가상환경 활성화
.\venv\Scripts\Activate.ps1

# 통합 시스템 실행
python main_integrated.py
```

---

## 🔧 설정 파일 선택

프로젝트에는 여러 설정 파일이 있습니다:

| 설정 파일 | 용도 | 하드웨어 요구사항 |
|---------|------|-----------------|
| `config.local-test.yaml` | 로컬 개발/테스트 | RTX 5060 Ti 16GB |
| `config.yaml` | 프로덕션 기본 | A100 80GB |
| `config.a100-80gb.yaml` | 고성능 서버 | A100 80GB |
| `config.openai-test.yaml` | OpenAI API 테스트 | API 키 필요 |

로컬 개발 시에는 `config.local-test.yaml`을 사용하세요.

`.env` 파일에서 설정:
```env
CONFIG_PATH=configs/config.local-test.yaml
```

---

## ✅ 설정 확인

### 1. Python 및 패키지 확인

```powershell
python --version  # Python 3.10 이상
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import torch; print(f'CUDA 사용 가능: {torch.cuda.is_available()}')"
```

### 2. CUDA 확인

```powershell
python -c "import torch; print(f'CUDA 사용 가능: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"없음\"}')"
```

### 3. 데이터베이스 확인

```powershell
# 데이터베이스 파일 확인
Test-Path .\data\mental_health.db
```

### 4. 환경 변수 확인

```powershell
# .env 파일 확인
Get-Content .env
```

---

## 🐛 문제 해결

### 문제 1: CUDA를 찾을 수 없음

**해결책:**
```powershell
# CPU 버전 PyTorch 설치
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio
```

또는 CUDA 버전에 맞는 PyTorch 설치:
```powershell
# CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 문제 2: Hugging Face 모델 다운로드 실패

**해결책:**
1. `.env` 파일에 `HUGGINGFACE_TOKEN` 설정
2. Hugging Face 로그인:
```powershell
huggingface-cli login
```

### 문제 3: 데이터베이스 초기화 실패

**해결책:**
```powershell
# 기존 데이터베이스 삭제 후 재생성
Remove-Item .\data\mental_health.db -ErrorAction SilentlyContinue
python -c "from src.database import DatabaseManager; db = DatabaseManager()"
```

### 문제 4: 포트가 이미 사용 중

**해결책:**
다른 포트 사용:
```powershell
# API 서버
uvicorn src.api:app --host 127.0.0.1 --port 8001 --reload

# Gradio
# app.py 파일에서 포트 변경
```

### 문제 5: 메모리 부족

**해결책:**
1. `config.local-test.yaml` 사용 (경량 모델)
2. 배치 크기 줄이기
3. 4-bit 양자화 사용 (기본값)

---

## 📚 추가 리소스

- **API 문서**: http://localhost:8000/docs
- **프로젝트 문서**: `docs/` 폴더
- **테스트 실행**: `pytest tests/ -v`

---

## 🎉 완료!

설정이 완료되면 다음 명령어로 서버를 시작할 수 있습니다:

```powershell
# Gradio 웹 인터페이스
python app.py

# 또는 API 서버
uvicorn src.api:app --host 127.0.0.1 --port 8000 --reload
```

문제가 발생하면 이슈를 제기하거나 문서를 참고하세요!

