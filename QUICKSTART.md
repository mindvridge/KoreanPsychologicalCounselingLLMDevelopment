# 빠른 시작 가이드
Quick Start Guide

한국어 심리 상담 AI를 로컬에서 빠르게 시작하는 방법입니다.

## 📋 요구사항

- **Python**: 3.8 이상
- **메모리**: 최소 8GB RAM (16GB 권장)
- **GPU**: CUDA 지원 GPU (선택적, 더 빠른 성능)
- **디스크**: 최소 10GB 여유 공간

## 🚀 5분 만에 시작하기

### 1단계: 저장소 클론

```bash
git clone https://github.com/mindvridge/KoreanPsychologicalCounselingLLMDevelopment.git
cd KoreanPsychologicalCounselingLLMDevelopment
```

### 2단계: 자동 설정 실행

```bash
bash scripts/setup_local.sh
```

이 스크립트는 자동으로:
- ✅ Python 버전 확인
- ✅ 가상 환경 생성 (선택)
- ✅ 필요한 디렉토리 생성
- ✅ .env 파일 생성
- ✅ 암호화 키 생성
- ✅ 데이터베이스 초기화
- ✅ CORS 설정 (로컬 개발용)

### 3단계: 의존성 설치

```bash
# 가상 환경 활성화 (생성한 경우)
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 4단계: 서버 시작

```bash
# 방법 1: 직접 실행
python src/api.py

# 방법 2: uvicorn 사용 (권장)
uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
```

### 5단계: 브라우저에서 접속

- **메인 페이지**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health

## 📚 주요 기능

### 1. 심리 상담 챗봇

```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_message": "안녕하세요, 요즘 우울해요",
    "persona": "empathetic"
  }'
```

### 2. 심리 평가 (PHQ-9, GAD-7, K-10)

```bash
curl -X POST "http://localhost:8000/api/v1/assessment" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_session",
    "assessment_type": "PHQ-9",
    "responses": {
      "1": 2, "2": 1, "3": 2, "4": 1,
      "5": 0, "6": 1, "7": 1, "8": 0, "9": 0
    }
  }'
```

### 3. 페르소나 선택

사용 가능한 페르소나:
- `empathetic` - 공감적 상담사
- `professional` - 전문적 상담사
- `encouraging` - 격려하는 상담사
- `analytical` - 분석적 상담사

```bash
curl "http://localhost:8000/api/v1/personas"
```

## 🧪 테스트 실행

### 통합 테스트

```bash
pytest tests/test_integration.py -v
```

### E2E 테스트 (서버 실행 필요)

```bash
# 터미널 1: 서버 시작
python src/api.py

# 터미널 2: E2E 테스트 실행
pytest tests/test_e2e.py -v -m e2e
```

### 성능 및 보안 테스트

```bash
pytest tests/test_performance_security.py -v -m "performance or security"
```

### 모든 테스트 실행

```bash
pytest tests/ -v
```

## 📊 성능 벤치마크

```bash
# API 성능 벤치마크
python scripts/benchmark_api.py

# 특정 옵션으로 실행
python scripts/benchmark_api.py \
  --concurrent-requests 100 \
  --workers 20
```

## 🔧 설정 커스터마이징

### .env 파일 수정

```bash
# 텍스트 에디터로 .env 파일 열기
nano .env
# 또는
vi .env
```

주요 설정:

```bash
# API 서버
API_HOST=0.0.0.0
API_PORT=8000

# CORS (로컬 개발용)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:7860,http://localhost:8000

# 데이터베이스
DATABASE_URL=sqlite:///./data/mental_health.db
ENABLE_LONG_TERM_MEMORY=true

# 암호화 (PIPA 준수)
ENABLE_DATA_ENCRYPTION=true
ENCRYPT_CONVERSATIONS=true
ENCRYPT_ASSESSMENTS=true

# Redis 캐싱 (선택적)
REDIS_URL=redis://localhost:6379/0

# RAG 시스템
KNOWLEDGE_BASE_DIR=./knowledge_base
ENABLE_RAG=true

# 로깅
LOG_LEVEL=INFO
MASK_PII=true
```

### 암호화 키 생성

```bash
# 암호화 키 생성 및 .env 파일에 자동 저장
python scripts/generate_encryption_key.py --save

# 특정 키만 생성
python scripts/generate_encryption_key.py --data-key
python scripts/generate_encryption_key.py --api-key
```

## 🗂️ 디렉토리 구조

```
KoreanPsychologicalCounselingLLMDevelopment/
├── src/                        # 소스 코드
│   ├── api.py                  # FastAPI 서버
│   ├── rag_system.py           # RAG (검색 증강 생성)
│   ├── assessments.py          # 심리 평가 (PHQ-9, GAD-7, K-10)
│   ├── database.py             # 데이터베이스 (SQLAlchemy)
│   ├── cache.py                # Redis 캐싱
│   ├── voice_service.py        # 음성 인식/합성
│   ├── export_service.py       # 데이터 내보내기 (CSV, PDF)
│   └── ...
├── tests/                      # 테스트
│   ├── test_integration.py     # 통합 테스트
│   ├── test_e2e.py             # E2E 테스트
│   ├── test_performance_security.py  # 성능/보안 테스트
│   └── ...
├── scripts/                    # 유틸리티 스크립트
│   ├── setup_local.sh          # 로컬 서버 설정
│   ├── generate_encryption_key.py  # 암호화 키 생성
│   ├── benchmark_api.py        # API 벤치마크
│   └── init_database.py        # 데이터베이스 초기화
├── knowledge_base/             # RAG 지식 베이스
│   ├── therapy_techniques/     # 치료 기법 (CBT, DBT, ACT)
│   ├── crisis_protocols/       # 위기 대응 프로토콜
│   └── cultural_context/       # 한국 문화적 맥락
├── frontend/                   # 프론트엔드 (HTML/JS)
│   ├── index.html
│   ├── app.js
│   └── style.css
├── data/                       # 데이터 (SQLite DB)
├── logs/                       # 로그 파일
├── mental_health_vectors/      # RAG 벡터 저장소
└── .env                        # 환경 설정 (생성 필요)
```

## 🔍 문제 해결

### 1. 모듈을 찾을 수 없음 (ModuleNotFoundError)

```bash
# 의존성 재설치
pip install -r requirements.txt --upgrade
```

### 2. CUDA 오류 (GPU 관련)

```bash
# CPU 모드로 전환 (.env 파일)
CUDA_ENABLED=false
SKIP_MODEL_LOADING=true  # 테스트용
```

### 3. 데이터베이스 오류

```bash
# 데이터베이스 재초기화
rm -f data/mental_health.db
python scripts/init_database.py
```

### 4. 포트 충돌 (8000 포트 사용 중)

```bash
# 다른 포트 사용 (.env 파일)
API_PORT=8001

# 또는 직접 지정
uvicorn src.api:app --port 8001
```

### 5. 로그 확인

```bash
# 실시간 로그 확인
tail -f logs/app.log

# 오류 로그만 확인
grep ERROR logs/app.log
```

## 📖 추가 문서

- **API 문서**: http://localhost:8000/docs (서버 실행 후)
- **데이터베이스 가이드**: `DATABASE_SETUP_GUIDE.md`
- **모니터링 가이드**: `monitoring/MONITORING_GUIDE.md`
- **테스트 가이드**: `tests/README_TESTS.md`

## 🆘 도움말

### 이슈 리포트

문제가 발생하면 GitHub Issues에 리포트해주세요:
https://github.com/mindvridge/KoreanPsychologicalCounselingLLMDevelopment/issues

### 필수 정보:
- Python 버전: `python --version`
- OS: `uname -a` (Linux/Mac) 또는 Windows 버전
- 오류 메시지
- 재현 단계

## 🎉 다음 단계

1. **프로덕션 배포**: Gunicorn + Nginx 설정
2. **PostgreSQL 연결**: SQLite에서 PostgreSQL로 전환
3. **Redis 캐싱 활성화**: 성능 향상
4. **모니터링 설정**: Prometheus + Grafana
5. **SSL/TLS 인증서**: HTTPS 설정

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

---

**즐거운 개발 되세요!** 🚀
