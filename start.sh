#!/bin/bash

# 마음챗 - 한국어 심리상담 AI 시스템
# RTX 5060 Ti 최적화 버전

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║   마음챗 - 한국어 심리상담 AI 시스템                         ║"
echo "║   RTX 5060 Ti 최적화 버전                                    ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# 스크립트 디렉토리로 이동
cd "$(dirname "$0")"

# 가상환경 활성화 (있는 경우)
if [ -f "venv/bin/activate" ]; then
    echo "[1/3] 가상환경 활성화 중..."
    source venv/bin/activate
elif [ -f ".venv/bin/activate" ]; then
    echo "[1/3] 가상환경 활성화 중..."
    source .venv/bin/activate
fi

# 환경 변수 로드
if [ -f ".env" ]; then
    echo "[2/3] 환경 변수 로드 중..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# 서버 시작
echo "[3/3] 서버 시작 중..."
echo ""
python3 start_all.py
