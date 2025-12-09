#!/bin/bash
# =============================================================================
# 로컬 테스트 환경 설정 스크립트
# RTX 5060 Ti 16GB / Intel Ultra 5 245KF / 32GB RAM
# =============================================================================

set -e

echo "=========================================="
echo "한국어 심리상담 LLM - 로컬 테스트 설정"
echo "=========================================="

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Python 버전 확인
echo -e "\n${YELLOW}[1/7] Python 버전 확인...${NC}"
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
if [[ "$python_version" < "3.10" ]]; then
    echo -e "${RED}Python 3.10 이상 필요합니다. 현재: $python_version${NC}"
    exit 1
fi
echo -e "${GREEN}Python $python_version 확인됨${NC}"

# 2. 가상환경 생성
echo -e "\n${YELLOW}[2/7] 가상환경 생성...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}가상환경 생성 완료${NC}"
else
    echo -e "${GREEN}가상환경 이미 존재${NC}"
fi

# 가상환경 활성화
source venv/bin/activate

# 3. pip 업그레이드
echo -e "\n${YELLOW}[3/7] pip 업그레이드...${NC}"
pip install --upgrade pip wheel setuptools

# 4. PyTorch 설치 (CUDA 12.4)
echo -e "\n${YELLOW}[4/7] PyTorch 설치 (CUDA)...${NC}"
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# 5. 기본 의존성 설치
echo -e "\n${YELLOW}[5/7] 기본 의존성 설치...${NC}"
pip install -r requirements.txt

# 6. 음성 처리 패키지 (선택적)
echo -e "\n${YELLOW}[6/7] 음성 처리 패키지 설치...${NC}"
pip install faster-whisper
pip install TTS  # Coqui TTS

# Zonos는 별도 설치 (선택)
# pip install git+https://github.com/Zyphra/Zonos.git

# 7. 디렉토리 생성
echo -e "\n${YELLOW}[7/7] 필요 디렉토리 생성...${NC}"
mkdir -p logs outputs voice_profiles data/finetuning

# 설정 파일 복사
echo -e "\n${YELLOW}테스트용 설정 파일 적용...${NC}"
cp configs/config.local-test.yaml configs/config.yaml.backup 2>/dev/null || true

# .env 파일 확인
if [ ! -f ".env" ]; then
    echo -e "\n${YELLOW}.env 파일 생성...${NC}"
    cat > .env << 'EOF'
# 환경 설정
HUGGINGFACE_TOKEN=your_token_here
CUDA_VISIBLE_DEVICES=0
LOG_LEVEL=INFO

# 테스트 모드
TEST_MODE=true
CONFIG_PATH=configs/config.local-test.yaml
EOF
    echo -e "${RED}.env 파일에 HUGGINGFACE_TOKEN을 설정하세요!${NC}"
fi

# CUDA 확인
echo -e "\n${YELLOW}CUDA 확인...${NC}"
python3 -c "import torch; print(f'CUDA 사용 가능: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"없음\"}')"

echo -e "\n=========================================="
echo -e "${GREEN}설정 완료!${NC}"
echo -e "=========================================="
echo -e "\n사용 방법:"
echo -e "  1. .env 파일에 HUGGINGFACE_TOKEN 설정"
echo -e "  2. source venv/bin/activate"
echo -e "  3. python -m pytest tests/ -v  # 테스트 실행"
echo -e "  4. python src/main.py  # 챗봇 실행"
echo -e "\nAPI 서버 실행:"
echo -e "  uvicorn src.api:app --host 127.0.0.1 --port 8000 --reload"
echo -e "\n음성 API 서버:"
echo -e "  uvicorn src.voice_api:app --host 127.0.0.1 --port 8001 --reload"
