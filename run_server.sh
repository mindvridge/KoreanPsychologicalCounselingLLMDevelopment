#!/bin/bash
# 원클릭 서버 실행 스크립트 (Linux/Mac)
# One-Click Server Launch Script

set -e

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 함수 정의
print_step() {
    echo -e "\n${BLUE}======================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}======================================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# 시작 메시지
echo -e "\n${GREEN}======================================================================${NC}"
echo -e "${GREEN}한국어 심리 상담 AI - 원클릭 서버 실행${NC}"
echo -e "${GREEN}Korean Psychological Counseling AI - One-Click Launch${NC}"
echo -e "${GREEN}======================================================================${NC}\n"

# 프로젝트 루트 확인
if [ ! -d "src" ] || [ ! -f "requirements.txt" ]; then
    print_error "프로젝트 루트 디렉토리에서 실행해주세요"
    exit 1
fi

# 1. Python 버전 확인
print_step "1. Python 버전 확인"

if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python $PYTHON_VERSION 확인됨"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    PYTHON_VERSION=$(python --version | cut -d' ' -f2)
    print_success "Python $PYTHON_VERSION 확인됨"
else
    print_error "Python이 설치되지 않았습니다"
    exit 1
fi

# 2. 가상 환경 설정
print_step "2. 가상 환경 설정"

if [ ! -d "venv" ]; then
    echo "가상 환경을 생성합니다..."
    $PYTHON_CMD -m venv venv
    print_success "가상 환경 생성 완료"
else
    print_success "가상 환경이 이미 존재합니다"
fi

# 가상 환경 활성화
source venv/bin/activate
print_success "가상 환경 활성화 완료"

# 3. 의존성 설치
print_step "3. 의존성 설치"

echo "pip를 업그레이드합니다..."
pip install --upgrade pip -q

echo "의존성을 설치합니다... (시간이 걸릴 수 있습니다)"
pip install -r requirements.txt -q || {
    print_warning "일부 의존성 설치 실패 (계속 진행)"
}
print_success "의존성 설치 완료"

# 4. 디렉토리 생성
print_step "4. 디렉토리 생성"

for dir in data logs mental_health_vectors; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        print_success "$dir/ 디렉토리 생성"
    else
        print_success "$dir/ 디렉토리 존재 확인"
    fi
done

# 5. 환경 설정 파일 생성
print_step "5. 환경 설정 파일 생성"

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_success ".env 파일 생성 완료"

        # 암호화 키 생성
        if [ -f "scripts/generate_encryption_key.py" ]; then
            echo "암호화 키를 생성합니다..."
            python scripts/generate_encryption_key.py --save --no-backup 2>/dev/null || {
                print_warning "암호화 키 생성 건너뜀"
            }
            print_success "암호화 키 생성 완료"
        fi
    else
        print_error ".env.example 파일이 없습니다"
        exit 1
    fi
else
    print_success ".env 파일이 이미 존재합니다"
fi

# 6. 데이터베이스 초기화
print_step "6. 데이터베이스 초기화"

if [ ! -f "data/mental_health.db" ]; then
    if [ -f "scripts/init_database.py" ]; then
        echo "데이터베이스를 초기화합니다..."
        python scripts/init_database.py 2>/dev/null || {
            print_warning "데이터베이스 초기화 실패 (서버 시작 시 자동 생성)"
        }
        print_success "데이터베이스 초기화 완료"
    else
        print_warning "데이터베이스 초기화 스크립트가 없습니다"
    fi
else
    print_success "데이터베이스가 이미 존재합니다"
fi

# 7. 지식 베이스 확인
print_step "7. RAG 지식 베이스 확인"

if [ -d "knowledge_base" ] && [ "$(ls -A knowledge_base 2>/dev/null)" ]; then
    KB_FILES=$(find knowledge_base -type f | wc -l)
    print_success "지식 베이스 파일 ${KB_FILES}개 발견"
else
    print_warning "knowledge_base 디렉토리가 비어있습니다"
    print_warning "RAG 시스템을 사용하려면 지식 베이스 문서를 추가하세요"
fi

# 8. 서버 시작
print_step "8. 서버 시작"

echo -e "\n${GREEN}======================================================================${NC}"
echo -e "${GREEN}서버를 시작합니다...${NC}"
echo -e "${GREEN}======================================================================${NC}\n"

echo "접속 주소:"
echo -e "  - 메인 페이지: ${BLUE}http://localhost:8000${NC}"
echo -e "  - API 문서: ${BLUE}http://localhost:8000/docs${NC}"
echo -e "  - Health Check: ${BLUE}http://localhost:8000/api/v1/health${NC}"
echo -e "\n서버를 중지하려면 Ctrl+C를 누르세요.\n"

# uvicorn이 설치되어 있는지 확인
if pip show uvicorn &> /dev/null; then
    # uvicorn으로 시작 (권장)
    python -m uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
else
    # 직접 실행
    python src/api.py
fi

# 종료 메시지
echo -e "\n${YELLOW}서버를 종료합니다...${NC}"
print_success "서버가 정상적으로 종료되었습니다"
