#!/bin/bash
# =============================================================================
# A100 클라우드 환경 설정 스크립트
# =============================================================================
# 지원 환경: AWS, GCP, Azure, Lambda Labs, RunPod 등
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  A100 클라우드 환경 설정${NC}"
echo -e "${BLUE}=========================================${NC}"

# 1. 시스템 정보 확인
echo -e "\n${YELLOW}[1/8] 시스템 정보 확인...${NC}"
echo -e "  OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo -e "  커널: $(uname -r)"
echo -e "  CPU: $(nproc) cores"
echo -e "  RAM: $(free -h | awk '/^Mem:/ {print $2}')"

# 2. GPU 확인
echo -e "\n${YELLOW}[2/8] GPU 확인...${NC}"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
    GPU_COUNT=$(nvidia-smi --query-gpu=count --format=csv,noheader | head -1)
    echo -e "${GREEN}  ✓ GPU ${GPU_COUNT}개 감지됨${NC}"
else
    echo -e "${RED}  ✗ NVIDIA 드라이버 미설치${NC}"
    echo -e "  설치: sudo apt install nvidia-driver-535"
    exit 1
fi

# 3. Python 환경 설정
echo -e "\n${YELLOW}[3/8] Python 환경 설정...${NC}"
if ! command -v python3.10 &> /dev/null && ! command -v python3.11 &> /dev/null; then
    echo -e "  Python 3.10+ 설치 중..."
    sudo apt update
    sudo apt install -y python3.10 python3.10-venv python3-pip
fi
python3 --version

# 4. 가상환경 생성
echo -e "\n${YELLOW}[4/8] 가상환경 생성...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip wheel setuptools

# 5. PyTorch 설치 (CUDA 12.1)
echo -e "\n${YELLOW}[5/8] PyTorch 설치 (CUDA 12.1)...${NC}"
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# CUDA 확인
python3 -c "import torch; print(f'  PyTorch: {torch.__version__}'); print(f'  CUDA: {torch.cuda.is_available()}')"

# 6. Flash Attention 2 설치 (A100 최적화)
echo -e "\n${YELLOW}[6/8] Flash Attention 2 설치...${NC}"
pip install flash-attn --no-build-isolation

# 7. 의존성 설치
echo -e "\n${YELLOW}[7/8] 의존성 설치...${NC}"
pip install -r requirements.txt

# Zonos TTS 설치
echo -e "  Zonos TTS 설치 중..."
pip install git+https://github.com/Zyphra/Zonos.git || echo -e "${YELLOW}  ⚠ Zonos 설치 실패 (선택사항)${NC}"

# 8. 디렉토리 및 설정
echo -e "\n${YELLOW}[8/8] 디렉토리 및 설정...${NC}"
mkdir -p logs outputs voice_profiles data/finetuning

# .env 파일 생성
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# A100 클라우드 환경 설정
HUGGINGFACE_TOKEN=your_token_here
CUDA_VISIBLE_DEVICES=0
CONFIG_PATH=configs/config.a100-80gb.yaml

# 로깅
LOG_LEVEL=INFO

# 성능 최적화
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
TOKENIZERS_PARALLELISM=false
EOF
    echo -e "${YELLOW}  ⚠ .env 파일에 HUGGINGFACE_TOKEN을 설정하세요!${NC}"
fi

# 설정 파일 복사
cp configs/config.a100-80gb.yaml configs/config.yaml

# 스크립트 실행 권한
chmod +x scripts/*.sh

# 완료
echo -e "\n${BLUE}=========================================${NC}"
echo -e "${GREEN}✓ A100 클라우드 환경 설정 완료!${NC}"
echo -e "${BLUE}=========================================${NC}"
echo -e "\n${YELLOW}다음 단계:${NC}"
echo -e "  1. .env 파일에 HUGGINGFACE_TOKEN 설정"
echo -e "  2. source venv/bin/activate"
echo -e "  3. ./scripts/start_a100_80gb.sh"
echo -e "\n${YELLOW}VRAM 사용량 예상:${NC}"
echo -e "  • Qwen2.5-32B (FP16): ~65GB"
echo -e "  • Whisper large-v3: ~10GB"
echo -e "  • Zonos TTS: ~6GB"
echo -e "  • 합계: ~81GB"
