#!/bin/bash
# 로컬 서버 설정 스크립트
# Local Server Setup Script

set -e  # 오류 발생 시 중단

echo "========================================================================"
echo "  한국어 심리 상담 AI - 로컬 서버 설정"
echo "  Korean Psychological Counseling AI - Local Server Setup"
echo "========================================================================"
echo ""

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 함수: 성공 메시지
success() {
    echo -e "${GREEN}✓${NC} $1"
}

# 함수: 경고 메시지
warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# 함수: 오류 메시지
error() {
    echo -e "${RED}✗${NC} $1"
}

# 1. Python 버전 확인
echo "1. Python 버전 확인 중..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    success "Python $PYTHON_VERSION 설치됨"
else
    error "Python 3이 설치되지 않았습니다. Python 3.8+ 를 설치해주세요."
    exit 1
fi

# 2. 가상 환경 생성 (선택)
echo ""
echo "2. 가상 환경 설정..."
if [ ! -d "venv" ]; then
    warning "가상 환경이 없습니다. 가상 환경을 생성하시겠습니까? (y/n)"
    read -r create_venv
    if [ "$create_venv" = "y" ] || [ "$create_venv" = "Y" ]; then
        python3 -m venv venv
        success "가상 환경 생성 완료"
        echo "가상 환경을 활성화하려면: source venv/bin/activate"
    fi
else
    success "가상 환경이 이미 존재합니다"
fi

# 3. 디렉토리 생성
echo ""
echo "3. 필요한 디렉토리 생성 중..."
mkdir -p data logs mental_health_vectors
success "디렉토리 생성 완료 (data/, logs/, mental_health_vectors/)"

# 4. .env 파일 생성
echo ""
echo "4. 환경 설정 파일 생성 중..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        success ".env 파일 생성 완료 (.env.example에서 복사)"

        # 암호화 키 자동 생성
        warning "암호화 키를 자동 생성하시겠습니까? (y/n)"
        read -r generate_keys
        if [ "$generate_keys" = "y" ] || [ "$generate_keys" = "Y" ]; then
            if python3 scripts/generate_encryption_key.py --save --no-backup; then
                success "암호화 키 생성 및 .env 파일 업데이트 완료"
            else
                warning "암호화 키 생성 실패. 나중에 수동으로 생성하세요."
            fi
        fi
    else
        error ".env.example 파일이 없습니다."
        exit 1
    fi
else
    warning ".env 파일이 이미 존재합니다. 건너뜁니다."
fi

# 5. CORS 설정 업데이트 (로컬 개발용)
echo ""
echo "5. CORS 설정 업데이트 중..."
if [ -f ".env" ]; then
    # ALLOWED_ORIGINS를 로컬 개발용으로 설정
    sed -i 's/^ALLOWED_ORIGINS=.*/ALLOWED_ORIGINS=http:\/\/localhost:3000,http:\/\/localhost:7860,http:\/\/localhost:8000/' .env
    success "CORS 설정 완료 (localhost 허용)"
fi

# 6. 데이터베이스 초기화
echo ""
echo "6. 데이터베이스 초기화 중..."
if python3 scripts/init_database.py; then
    success "데이터베이스 초기화 완료"
else
    warning "데이터베이스 초기화 실패. 서버 시작 시 자동으로 생성됩니다."
fi

# 7. 지식 베이스 확인
echo ""
echo "7. RAG 지식 베이스 확인 중..."
if [ -d "knowledge_base" ] && [ "$(ls -A knowledge_base)" ]; then
    KB_FILES=$(find knowledge_base -type f | wc -l)
    success "지식 베이스 파일 $KB_FILES개 발견"
else
    warning "knowledge_base 디렉토리가 비어있습니다."
    warning "RAG 시스템이 작동하려면 지식 베이스 문서를 추가하세요."
fi

# 8. 설정 완료 안내
echo ""
echo "========================================================================"
echo -e "${GREEN}✓ 로컬 서버 설정 완료!${NC}"
echo "========================================================================"
echo ""
echo "다음 단계:"
echo ""
echo "1. 의존성 설치 (아직 안 했다면):"
echo "   pip install -r requirements.txt"
echo ""
echo "2. .env 파일 확인 및 수정:"
echo "   nano .env"
echo "   # 또는"
echo "   vi .env"
echo ""
echo "3. 서버 시작:"
echo "   python src/api.py"
echo "   # 또는"
echo "   uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "4. 브라우저에서 접속:"
echo "   http://localhost:8000        (메인 페이지)"
echo "   http://localhost:8000/docs   (API 문서)"
echo ""
echo "5. 성능 벤치마크 실행:"
echo "   python scripts/benchmark_api.py"
echo ""
echo "========================================================================"
echo ""
echo "주요 설정:"
echo "  - 데이터베이스: SQLite (data/mental_health.db)"
echo "  - 로그: logs/"
echo "  - 벡터 저장소: mental_health_vectors/"
echo "  - API 포트: 8000"
echo ""
echo "문제 발생 시:"
echo "  - 로그 확인: tail -f logs/app.log"
echo "  - 이슈 리포트: https://github.com/mindvridge/KoreanPsychologicalCounselingLLMDevelopment/issues"
echo ""
echo "========================================================================"
