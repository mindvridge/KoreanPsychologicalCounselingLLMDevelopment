# =============================================================================
# 로컬 서버 구동 설정 스크립트 (Windows PowerShell)
# =============================================================================

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "한국어 심리상담 LLM - 로컬 서버 설정" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Python 버전 확인
Write-Host "`n[1/8] Python 버전 확인..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Python이 설치되어 있지 않습니다. Python 3.10 이상을 설치하세요." -ForegroundColor Red
    exit 1
}
Write-Host "Python 버전: $pythonVersion" -ForegroundColor Green

# 2. 가상환경 생성
Write-Host "`n[2/8] 가상환경 생성..." -ForegroundColor Yellow
if (-Not (Test-Path "venv")) {
    python -m venv venv
    Write-Host "가상환경 생성 완료" -ForegroundColor Green
} else {
    Write-Host "가상환경 이미 존재" -ForegroundColor Green
}

# 가상환경 활성화
Write-Host "가상환경 활성화 중..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# 3. pip 업그레이드
Write-Host "`n[3/8] pip 업그레이드..." -ForegroundColor Yellow
python -m pip install --upgrade pip wheel setuptools

# 4. PyTorch 설치 확인
Write-Host "`n[4/8] PyTorch 설치 확인..." -ForegroundColor Yellow
$torchInstalled = python -c "import torch; print('OK')" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyTorch가 설치되어 있지 않습니다. 설치 중..." -ForegroundColor Yellow
    python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
} else {
    Write-Host "PyTorch 설치 확인됨" -ForegroundColor Green
}

# 5. 의존성 설치
Write-Host "`n[5/8] 의존성 설치..." -ForegroundColor Yellow
python -m pip install -r requirements.txt

# 6. 필요 디렉토리 생성
Write-Host "`n[6/8] 필요 디렉토리 생성..." -ForegroundColor Yellow
$directories = @("logs", "outputs", "voice_profiles", "data\finetuning", "data")
foreach ($dir in $directories) {
    if (-Not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  생성: $dir" -ForegroundColor Gray
    }
}

# 7. .env 파일 생성
Write-Host "`n[7/8] .env 파일 설정..." -ForegroundColor Yellow
if (-Not (Test-Path ".env")) {
    $envContent = @"
# =============================================================================
# 환경 변수 설정
# =============================================================================

# Hugging Face 토큰 (필수)
# https://huggingface.co/settings/tokens 에서 발급
HUGGINGFACE_TOKEN=your_token_here

# CUDA 설정
CUDA_VISIBLE_DEVICES=0

# 로그 레벨
LOG_LEVEL=INFO

# 데이터베이스 설정
DATABASE_PATH=./data/mental_health.db
DATABASE_URL=sqlite:///./data/mental_health.db

# 장기 기억 활성화
ENABLE_LONG_TERM_MEMORY=true

# 데이터 보관 기간 (일)
USER_DATA_RETENTION_DAYS=90

# PII 마스킹 활성화
MASK_PII=true

# 설정 파일 경로
CONFIG_PATH=configs/config.local-test.yaml

# API 설정
API_HOST=127.0.0.1
API_PORT=8000

# 테스트 모드
TEST_MODE=true
"@
    $envContent | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host ".env 파일 생성 완료" -ForegroundColor Green
    Write-Host "⚠️  .env 파일에 HUGGINGFACE_TOKEN을 설정하세요!" -ForegroundColor Red
} else {
    Write-Host ".env 파일 이미 존재" -ForegroundColor Green
}

# 8. 데이터베이스 초기화
Write-Host "`n[8/8] 데이터베이스 초기화..." -ForegroundColor Yellow
python -c "from src.database import DatabaseManager; db = DatabaseManager(); print('데이터베이스 초기화 완료')" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "데이터베이스 초기화 완료" -ForegroundColor Green
} else {
    Write-Host "데이터베이스 초기화 실패 (이미 존재할 수 있음)" -ForegroundColor Yellow
}

# CUDA 확인
Write-Host "`nCUDA 확인 중..." -ForegroundColor Yellow
python -c "import torch; print(f'CUDA 사용 가능: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"없음\"}')"

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "설정 완료!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan

Write-Host "`n다음 단계:" -ForegroundColor Yellow
Write-Host "  1. .env 파일을 열어 HUGGINGFACE_TOKEN을 설정하세요" -ForegroundColor White
Write-Host "  2. 가상환경이 활성화되어 있는지 확인하세요" -ForegroundColor White
Write-Host "`n서버 실행 방법:" -ForegroundColor Yellow
Write-Host "  # Gradio 웹 인터페이스:" -ForegroundColor White
Write-Host "  python app.py" -ForegroundColor Cyan
Write-Host "`n  # API 서버:" -ForegroundColor White
Write-Host "  uvicorn src.api:app --host 127.0.0.1 --port 8000 --reload" -ForegroundColor Cyan
Write-Host "`n  # 통합 시스템:" -ForegroundColor White
Write-Host "  python main_integrated.py" -ForegroundColor Cyan
Write-Host "`n접속 주소:" -ForegroundColor Yellow
Write-Host "  - Gradio: http://localhost:7860" -ForegroundColor Green
Write-Host "  - API: http://localhost:8000" -ForegroundColor Green
Write-Host "  - API 문서: http://localhost:8000/docs" -ForegroundColor Green

