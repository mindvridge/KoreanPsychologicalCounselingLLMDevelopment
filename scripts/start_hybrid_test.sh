#!/bin/bash
# =============================================================================
# 하이브리드 테스트 서버 시작 스크립트
# LLM: ChatGPT API / STT+TTS: 로컬 GPU
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  하이브리드 테스트 환경${NC}"
echo -e "${BLUE}  LLM: ChatGPT API / STT+TTS: 로컬 GPU${NC}"
echo -e "${BLUE}=========================================${NC}"

# 환경 변수 설정
export CONFIG_PATH="configs/config.hybrid-test.yaml"
export CUDA_VISIBLE_DEVICES=0
export LLM_PROVIDER=openai

# 1. 환경 확인
echo -e "\n${YELLOW}[1/4] 환경 확인...${NC}"

# OpenAI API 키 확인
if [ -z "$OPENAI_API_KEY" ]; then
    if [ -f ".env" ]; then
        source .env
    fi
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}✗ OPENAI_API_KEY가 설정되지 않았습니다${NC}"
    echo -e "  export OPENAI_API_KEY=sk-your-key"
    exit 1
fi
echo -e "${GREEN}  ✓ OpenAI API 키 확인됨${NC}"

# GPU 확인
if command -v nvidia-smi &> /dev/null; then
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)
    GPU_MEM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader | head -1)
    echo -e "${GREEN}  ✓ GPU: $GPU_NAME ($GPU_MEM)${NC}"
else
    echo -e "${RED}✗ NVIDIA GPU를 찾을 수 없습니다${NC}"
    exit 1
fi

# 2. 가상환경 활성화
echo -e "\n${YELLOW}[2/4] 가상환경 활성화...${NC}"
if [ -d "venv" ]; then
    source venv/bin/activate
    echo -e "${GREEN}  ✓ 가상환경 활성화됨${NC}"
else
    echo -e "${RED}✗ 가상환경이 없습니다${NC}"
    echo -e "  python -m venv venv && source venv/bin/activate"
    exit 1
fi

# 3. 디렉토리 확인
echo -e "\n${YELLOW}[3/4] 디렉토리 확인...${NC}"
mkdir -p logs outputs voice_profiles
echo -e "${GREEN}  ✓ 디렉토리 준비됨${NC}"

# 4. 서버 시작
echo -e "\n${YELLOW}[4/4] 서버 시작...${NC}"
echo -e "${BLUE}=========================================${NC}"
echo -e "  설정: $CONFIG_PATH"
echo -e "  LLM: ChatGPT API (${OPENAI_MODEL:-gpt-4o-mini})"
echo -e "  STT: Whisper large-v3 (로컬 GPU)"
echo -e "  TTS: Zonos (로컬 GPU)"
echo -e "${BLUE}=========================================${NC}"
echo -e "  채팅 API: http://127.0.0.1:8000"
echo -e "  음성 API: http://127.0.0.1:8001"
echo -e "  API 문서: http://127.0.0.1:8000/docs"
echo -e "${BLUE}=========================================${NC}"

MODE=${1:-"all"}

case $MODE in
    "chat")
        echo -e "\n${GREEN}채팅 API만 시작...${NC}"
        uvicorn src.api:app --host 127.0.0.1 --port 8000 --reload
        ;;
    "voice")
        echo -e "\n${GREEN}음성 API만 시작...${NC}"
        uvicorn src.voice_api:app --host 127.0.0.1 --port 8001 --reload
        ;;
    "all")
        echo -e "\n${GREEN}모든 서버 시작...${NC}"

        # 채팅 API (백그라운드)
        echo -e "  채팅 API 시작 (포트 8000)..."
        nohup uvicorn src.api:app --host 127.0.0.1 --port 8000 \
            > logs/api_chat.log 2>&1 &
        echo $! > logs/api_chat.pid

        # 음성 API (백그라운드)
        echo -e "  음성 API 시작 (포트 8001)..."
        nohup uvicorn src.voice_api:app --host 127.0.0.1 --port 8001 \
            > logs/api_voice.log 2>&1 &
        echo $! > logs/api_voice.pid

        sleep 3
        echo -e "\n${GREEN}✓ 서버 시작됨${NC}"
        echo -e "\n로그 확인:"
        echo -e "  tail -f logs/api_chat.log"
        echo -e "  tail -f logs/api_voice.log"
        echo -e "\n종료: ./scripts/stop_servers.sh"
        ;;
    "cli")
        echo -e "\n${GREEN}CLI 테스트 모드 시작...${NC}"
        python src/openai_adapter.py
        ;;
    *)
        echo -e "사용법: $0 [chat|voice|all|cli]"
        exit 1
        ;;
esac
