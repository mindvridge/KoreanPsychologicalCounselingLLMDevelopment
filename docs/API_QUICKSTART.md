# FastAPI REST API 빠른 시작 가이드

## 1. 의존성 설치

```bash
pip install -r requirements.txt
```

주요 설치 패키지:
- `fastapi>=0.104.0` - 웹 프레임워크
- `uvicorn>=0.24.0` - ASGI 서버
- `pydantic>=2.5.0` - 데이터 검증
- `slowapi>=0.1.9` - Rate limiting
- `prometheus-client>=0.19.0` - 메트릭
- `cryptography>=41.0.0` - 암호화

## 2. 환경 설정 (선택사항)

```bash
# .env.example 복사
cp .env.example .env

# .env 파일 편집 (선택사항)
# API_KEY, CUDA_VISIBLE_DEVICES 등 설정
```

## 3. API 서버 실행

### 방법 1: 직접 실행

```bash
python src/api.py
```

### 방법 2: uvicorn으로 실행

```bash
uvicorn src.api:app --host 0.0.0.0 --port 8000
```

### 방법 3: 개발 모드 (자동 재시작)

```bash
uvicorn src.api:app --reload
```

## 4. API 문서 확인

서버 시작 후:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 5. 빠른 테스트

### cURL로 테스트

```bash
# 건강 체크
curl http://localhost:8000/api/v1/health

# 대화 테스트
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "안녕하세요"}'
```

### Python으로 테스트

```bash
python examples/api_client_example.py
```

## 6. Docker로 실행

```bash
# Docker Compose로 전체 스택 실행
docker-compose up

# 또는 특정 서비스만
docker-compose up mental-health-llm
```

## 주요 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/v1/health` | GET | 건강 체크 |
| `/api/v1/chat` | POST | 대화 처리 |
| `/api/v1/assessment` | POST | 심리 평가 |
| `/api/v1/session/{id}` | GET | 세션 조회 |
| `/api/v1/stats` | GET | 시스템 통계 |
| `/metrics` | GET | Prometheus 메트릭 |
| `/docs` | GET | API 문서 (Swagger) |

## 문제 해결

### FastAPI 설치 안 됨
```bash
pip install fastapi uvicorn pydantic slowapi prometheus-client
```

### 포트 충돌
```bash
# 다른 포트 사용
export API_PORT=8080
python src/api.py
```

### GPU 메모리 부족
```bash
# CPU 모드로 실행
export CUDA_ENABLED=false
python src/api.py
```

상세 가이드: [docs/API_GUIDE.md](API_GUIDE.md)
