#!/bin/bash
# =============================================================================
# A100 80GB 프로덕션 서버 시작 스크립트
# =============================================================================

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  한국어 심리상담 LLM - A100 80GB 서버${NC}"
echo -e "${BLUE}=========================================${NC}"

# 환경 변수 설정
export CUDA_VISIBLE_DEVICES=0
export CONFIG_PATH="configs/config.a100-80gb.yaml"
export PYTORCH_CUDA_ALLOC_CONF="max_split_size_mb:512"
export TOKENIZERS_PARALLELISM=false

# HuggingFace 캐시 디렉토리 (선택)
# export HF_HOME="/data/huggingface"
# export TRANSFORMERS_CACHE="/data/huggingface/transformers"

# 1. 환경 확인
echo -e "\n${YELLOW}[1/5] 환경 확인...${NC}"

# CUDA 확인
if ! command -v nvidia-smi &> /dev/null; then
    echo -e "${RED}NVIDIA 드라이버가 설치되지 않았습니다.${NC}"
    exit 1
fi

GPU_MEM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
echo -e "  GPU 메모리: ${GPU_MEM}MB"

if [ "$GPU_MEM" -lt 70000 ]; then
    echo -e "${RED}A100 80GB가 필요합니다. 현재: ${GPU_MEM}MB${NC}"
    exit 1
fi
echo -e "${GREEN}  ✓ A100 80GB 확인됨${NC}"

# 2. 가상환경 활성화
echo -e "\n${YELLOW}[2/5] 가상환경 활성화...${NC}"
if [ -d "venv" ]; then
    source venv/bin/activate
    echo -e "${GREEN}  ✓ 가상환경 활성화됨${NC}"
else
    echo -e "${RED}가상환경이 없습니다. 먼저 setup을 실행하세요.${NC}"
    exit 1
fi

# 3. 필수 디렉토리 확인
echo -e "\n${YELLOW}[3/5] 디렉토리 확인...${NC}"
mkdir -p logs outputs voice_profiles data/finetuning
echo -e "${GREEN}  ✓ 디렉토리 준비됨${NC}"

# 4. 모델 프리로드 (선택)
echo -e "\n${YELLOW}[4/5] 모델 확인...${NC}"
python3 -c "
from transformers import AutoTokenizer
print('  Qwen2.5-32B 토크나이저 확인 중...')
tokenizer = AutoTokenizer.from_pretrained('Qwen/Qwen2.5-32B-Instruct', trust_remote_code=True)
print('  ✓ 토크나이저 로드 성공')
" 2>/dev/null || echo -e "${YELLOW}  ⚠ 첫 실행 시 모델 다운로드가 필요합니다 (~60GB)${NC}"

# 5. 서버 시작
echo -e "\n${YELLOW}[5/5] 서버 시작...${NC}"
echo -e "${BLUE}=========================================${NC}"
echo -e "  설정 파일: $CONFIG_PATH"
echo -e "  채팅 API: http://0.0.0.0:8000"
echo -e "  음성 API: http://0.0.0.0:8001"
echo -e "  배치 API: http://0.0.0.0:8002"
echo -e "${BLUE}=========================================${NC}"

# 실행 모드 선택
MODE=${1:-"all"}

case $MODE in
    "chat")
        echo -e "\n${GREEN}채팅 API 서버만 시작...${NC}"
        uvicorn src.api:app --host 0.0.0.0 --port 8000 --workers 1
        ;;
    "voice")
        echo -e "\n${GREEN}음성 API 서버만 시작...${NC}"
        uvicorn src.voice_api:app --host 0.0.0.0 --port 8001 --workers 1
        ;;
    "batch")
        echo -e "\n${GREEN}배치 API 서버만 시작...${NC}"
        uvicorn src.batch_api:app --host 0.0.0.0 --port 8002 --workers 1
        ;;
    "all")
        echo -e "\n${GREEN}모든 서버 시작 (백그라운드)...${NC}"

        # 채팅 API
        echo -e "  채팅 API 시작 (포트 8000)..."
        nohup uvicorn src.api:app --host 0.0.0.0 --port 8000 --workers 1 \
            > logs/api_chat.log 2>&1 &
        echo $! > logs/api_chat.pid

        # 음성 API
        echo -e "  음성 API 시작 (포트 8001)..."
        nohup uvicorn src.voice_api:app --host 0.0.0.0 --port 8001 --workers 1 \
            > logs/api_voice.log 2>&1 &
        echo $! > logs/api_voice.pid

        # 배치 API
        echo -e "  배치 API 시작 (포트 8002)..."
        nohup uvicorn src.batch_api:app --host 0.0.0.0 --port 8002 --workers 1 \
            > logs/api_batch.log 2>&1 &
        echo $! > logs/api_batch.pid

        sleep 3
        echo -e "\n${GREEN}✓ 모든 서버 시작됨${NC}"
        echo -e "\n로그 확인:"
        echo -e "  tail -f logs/api_chat.log"
        echo -e "  tail -f logs/api_voice.log"
        echo -e "  tail -f logs/api_batch.log"
        echo -e "\n종료:"
        echo -e "  ./scripts/stop_servers.sh"
        ;;
    *)
        echo -e "${RED}알 수 없는 모드: $MODE${NC}"
        echo -e "사용법: $0 [chat|voice|batch|all]"
        exit 1
        ;;
esac
