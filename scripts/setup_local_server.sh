#!/bin/bash
# =============================================================================
# 로컬 서버 구축 스크립트 (Local Server Setup)
# =============================================================================
# 하이브리드 테스트 환경: ChatGPT API + 로컬 GPU (STT/TTS)
# 하드웨어 요구사항: NVIDIA GPU 16GB+ VRAM
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}=========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}=========================================${NC}"
}

print_step() {
    echo -e "\n${YELLOW}[$1/$TOTAL_STEPS] $2${NC}"
}

print_success() {
    echo -e "${GREEN}  ✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}  ⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}  ✗ $1${NC}"
}

TOTAL_STEPS=10

print_header "한국어 심리상담 LLM - 로컬 서버 구축"
echo -e "${CYAN}하이브리드 테스트: ChatGPT API + 로컬 GPU (STT/TTS)${NC}"

# =============================================================================
# Step 1: 시스템 확인
# =============================================================================
print_step 1 "시스템 환경 확인..."

# OS 확인
OS_TYPE=$(uname -s)
echo -e "  OS: $OS_TYPE"

# Python 버전 확인
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
        print_success "Python $PYTHON_VERSION"
    else
        print_error "Python 3.10+ 필요 (현재: $PYTHON_VERSION)"
        exit 1
    fi
else
    print_error "Python3가 설치되지 않았습니다"
    exit 1
fi

# =============================================================================
# Step 2: GPU 확인
# =============================================================================
print_step 2 "GPU 확인..."

if command -v nvidia-smi &> /dev/null; then
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
    GPU_MEM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -1)

    if [ -n "$GPU_NAME" ]; then
        print_success "GPU: $GPU_NAME"
        print_success "VRAM: ${GPU_MEM}MB"

        # VRAM 체크 (16GB = 16384MB)
        if [ "$GPU_MEM" -lt 15000 ]; then
            print_warning "16GB VRAM 권장 (현재: ${GPU_MEM}MB)"
            print_warning "STT/TTS 경량 모델 사용을 고려하세요"
        fi
    else
        print_warning "GPU 정보를 가져올 수 없습니다"
    fi
else
    print_warning "nvidia-smi를 찾을 수 없습니다"
    print_warning "GPU 없이 CPU 모드로 진행합니다"
fi

# =============================================================================
# Step 3: 가상환경 생성
# =============================================================================
print_step 3 "가상환경 생성..."

if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "가상환경 생성 완료"
else
    print_success "가상환경 이미 존재"
fi

# 가상환경 활성화
source venv/bin/activate
print_success "가상환경 활성화됨"

# =============================================================================
# Step 4: pip 업그레이드
# =============================================================================
print_step 4 "pip 업그레이드..."

pip install --upgrade pip wheel setuptools -q
print_success "pip 업그레이드 완료"

# =============================================================================
# Step 5: PyTorch 설치
# =============================================================================
print_step 5 "PyTorch 설치 (CUDA)..."

# CUDA 버전 확인
if command -v nvidia-smi &> /dev/null; then
    CUDA_VERSION=$(nvidia-smi | grep "CUDA Version" | awk '{print $9}' | cut -d'.' -f1)

    if [ -n "$CUDA_VERSION" ]; then
        if [ "$CUDA_VERSION" -ge 12 ]; then
            pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 -q
            print_success "PyTorch (CUDA 12.1) 설치 완료"
        else
            pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 -q
            print_success "PyTorch (CUDA 11.8) 설치 완료"
        fi
    else
        pip install torch torchvision torchaudio -q
        print_success "PyTorch 설치 완료"
    fi
else
    pip install torch torchvision torchaudio -q
    print_success "PyTorch (CPU) 설치 완료"
fi

# PyTorch 확인
python3 -c "import torch; print(f'  PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}')"

# =============================================================================
# Step 6: 기본 의존성 설치
# =============================================================================
print_step 6 "기본 의존성 설치..."

pip install -r requirements.txt -q
print_success "기본 의존성 설치 완료"

# =============================================================================
# Step 7: 음성 처리 패키지 설치
# =============================================================================
print_step 7 "음성 처리 패키지 설치..."

# faster-whisper (STT)
pip install faster-whisper -q
print_success "faster-whisper 설치 완료"

# Zonos TTS (선택적)
echo -e "  Zonos TTS 설치 중... (시간이 걸릴 수 있습니다)"
pip install git+https://github.com/Zyphra/Zonos.git -q 2>/dev/null && \
    print_success "Zonos TTS 설치 완료" || \
    print_warning "Zonos TTS 설치 실패 (gTTS로 대체 가능)"

# =============================================================================
# Step 8: 디렉토리 생성
# =============================================================================
print_step 8 "디렉토리 구조 생성..."

mkdir -p logs outputs voice_profiles data/finetuning knowledge_base
print_success "logs/ 생성"
print_success "outputs/ 생성"
print_success "voice_profiles/ 생성"
print_success "data/finetuning/ 생성"
print_success "knowledge_base/ 생성"

# =============================================================================
# Step 9: 환경 설정 파일
# =============================================================================
print_step 9 "환경 설정 파일 생성..."

# .env 파일 생성
if [ ! -f ".env" ]; then
    cat > .env << 'ENVEOF'
# =============================================================================
# 한국어 심리상담 LLM - 로컬 테스트 환경 설정
# =============================================================================

# OpenAI API 설정 (필수)
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o-mini
LLM_PROVIDER=openai

# HuggingFace 토큰 (STT 모델 다운로드용)
HUGGINGFACE_TOKEN=hf_your_token_here

# 설정 파일 경로
CONFIG_PATH=configs/config.hybrid-test.yaml

# GPU 설정
CUDA_VISIBLE_DEVICES=0

# 로깅
LOG_LEVEL=INFO
DEBUG=false

# API 서버
API_HOST=127.0.0.1
API_PORT=8000

# 음성 API 서버
VOICE_API_HOST=127.0.0.1
VOICE_API_PORT=8001
ENVEOF
    print_success ".env 파일 생성 완료"
    print_warning "⚠️  .env 파일에서 OPENAI_API_KEY를 설정하세요!"
else
    print_success ".env 파일 이미 존재"
fi

# 설정 파일 복사
cp configs/config.hybrid-test.yaml configs/config.yaml 2>/dev/null || true
print_success "config.yaml 설정 완료"

# =============================================================================
# Step 10: 설치 확인
# =============================================================================
print_step 10 "설치 확인..."

echo -e "\n${CYAN}패키지 버전 확인:${NC}"
python3 << 'PYEOF'
import sys

packages = [
    ("torch", "PyTorch"),
    ("transformers", "Transformers"),
    ("openai", "OpenAI"),
    ("faster_whisper", "Faster-Whisper"),
    ("fastapi", "FastAPI"),
    ("uvicorn", "Uvicorn"),
]

for pkg, name in packages:
    try:
        mod = __import__(pkg)
        version = getattr(mod, "__version__", "unknown")
        print(f"  ✓ {name}: {version}")
    except ImportError:
        print(f"  ✗ {name}: 미설치")

# CUDA 확인
import torch
if torch.cuda.is_available():
    print(f"  ✓ CUDA: {torch.version.cuda}")
    print(f"  ✓ GPU: {torch.cuda.get_device_name(0)}")
else:
    print("  ⚠ CUDA: 사용 불가")
PYEOF

# =============================================================================
# 완료
# =============================================================================
print_header "설치 완료!"

echo -e "
${GREEN}다음 단계:${NC}

${YELLOW}1. OpenAI API 키 설정:${NC}
   nano .env
   # OPENAI_API_KEY=sk-your-key-here

${YELLOW}2. 환경 활성화:${NC}
   source venv/bin/activate

${YELLOW}3. CLI 테스트:${NC}
   python src/openai_adapter.py

${YELLOW}4. 서버 시작:${NC}
   ./scripts/start_hybrid_test.sh all

${YELLOW}5. API 문서 확인:${NC}
   http://127.0.0.1:8000/docs

${BLUE}=========================================${NC}
${CYAN}VRAM 사용량 예상:${NC}
  • Whisper large-v3: ~10GB
  • Zonos TTS: ~6GB
  • 합계: ~16GB

${CYAN}비용 예상 (ChatGPT API):${NC}
  • gpt-4o-mini: ~\$0.0015/상담 (~2원)
${BLUE}=========================================${NC}
"
