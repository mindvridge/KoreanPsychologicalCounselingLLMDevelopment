# Korean Mental Health Counseling API Guide

한국형 심리상담 LLM 시스템의 REST API 완벽 가이드

## 목차

- [시작하기](#시작하기)
- [인증](#인증)
- [엔드포인트](#엔드포인트)
- [사용 예제](#사용-예제)
- [에러 처리](#에러-처리)
- [Rate Limiting](#rate-limiting)
- [모니터링](#모니터링)

---

## 시작하기

### 서버 실행

#### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

#### 2. 환경 변수 설정

```bash
# .env.example을 .env로 복사
cp .env.example .env

# .env 파일 수정 (선택사항)
vim .env
```

#### 3. API 서버 시작

```bash
# 방법 1: Python으로 직접 실행
python -m uvicorn src.api:app --host 0.0.0.0 --port 8000

# 방법 2: Python 스크립트로 실행
python src/api.py

# 방법 3: Docker로 실행
docker-compose up mental-health-llm
```

#### 4. API 문서 확인

서버 실행 후 브라우저에서:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 인증

### API Key 인증 (선택사항)

API Key를 설정하려면 `.env` 파일에 추가:

```bash
API_KEY=your-secret-api-key-here
```

API Key 생성 예제:

```python
import secrets
print(secrets.token_urlsafe(32))
# 출력: 'AbC123XyZ789...'
```

### 사용 방법

모든 요청에 `X-API-Key` 헤더 추가:

```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "X-API-Key: your-secret-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{"message": "안녕하세요"}'
```

**참고**: `API_KEY`를 설정하지 않으면 인증 없이 사용 가능 (개발 환경 전용)

---

## 엔드포인트

### 1. 건강 체크

시스템 상태 확인

**Endpoint**: `GET /api/v1/health`

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "components": {
    "llm": true,
    "crisis_detector": true,
    "emotion_analyzer": true,
    "rag_system": true,
    "monitoring": true,
    "logging": true
  },
  "uptime_seconds": 3600.5
}
```

**상태 코드**:
- `200`: 정상 작동
- `503`: 시스템 초기화 중 또는 일부 컴포넌트 실패

---

### 2. 대화 처리

사용자 메시지 처리 및 AI 응답 생성

**Endpoint**: `POST /api/v1/chat`

**Request Body**:
```json
{
  "session_id": "optional-session-id",
  "message": "요즘 우울해서 힘들어요",
  "conversation_history": [
    {"role": "user", "content": "안녕하세요"},
    {"role": "assistant", "content": "안녕하세요. 무엇을 도와드릴까요?"}
  ]
}
```

**Parameters**:
- `session_id` (optional): 세션 ID. 없으면 자동 생성
- `message` (required): 사용자 메시지 (1-2000자)
- `conversation_history` (optional): 대화 기록 (자동으로 관리됨)

**Response**:
```json
{
  "session_id": "abc-123-def-456",
  "response": "우울하신 마음이 드시는군요. 어떤 상황에서 특히 그런 감정이 드시나요?",
  "crisis_detected": false,
  "crisis_level": 0,
  "emotions": {
    "primary_emotion": {
      "emotion": "슬픔",
      "confidence": 0.85
    },
    "korean_emotions": {
      "han": 0.3,
      "jeong": 0.1
    }
  },
  "suggested_assessment": "phq9",
  "response_time": 2.5,
  "metadata": {
    "session_id": "abc-123-def-456",
    "timestamp": "2024-01-15T10:30:00",
    "rag_used": true
  }
}
```

**상태 코드**:
- `200`: 성공
- `400`: 잘못된 요청 (메시지 누락 등)
- `429`: Rate limit 초과
- `500`: 내부 서버 오류
- `503`: 시스템 초기화 중

**Rate Limit**: 100 requests/minute

---

### 3. 세션 조회

세션 정보 조회

**Endpoint**: `GET /api/v1/session/{session_id}`

**Response**:
```json
{
  "session_id": "abc-123-def-456",
  "created_at": "2024-01-15T10:00:00",
  "total_messages": 10,
  "crisis_detected_count": 0,
  "last_activity": "2024-01-15T10:30:00"
}
```

**상태 코드**:
- `200`: 성공
- `404`: 세션을 찾을 수 없음

---

### 4. 세션 삭제

세션 데이터 삭제

**Endpoint**: `DELETE /api/v1/session/{session_id}`

**Response**:
```json
{
  "message": "Session deleted successfully",
  "session_id": "abc-123-def-456"
}
```

**상태 코드**:
- `200`: 성공
- `404`: 세션을 찾을 수 없음

---

### 5. 심리 평가

심리 평가 도구 실행 (PHQ-9, GAD-7, K-10)

**Endpoint**: `POST /api/v1/assessment`

**Request Body**:
```json
{
  "session_id": "abc-123-def-456",
  "assessment_type": "phq9",
  "responses": [0, 1, 1, 2, 1, 0, 1, 2, 1]
}
```

**Parameters**:
- `assessment_type`: `phq9`, `gad7`, 또는 `k10`
- `responses`: 응답 배열
  - PHQ-9: 9개 응답 (0-3)
  - GAD-7: 7개 응답 (0-3)
  - K-10: 10개 응답 (1-5)

**Response**:
```json
{
  "session_id": "abc-123-def-456",
  "assessment_type": "phq9",
  "score": 9,
  "severity": "경증 우울",
  "interpretation": "가벼운 우울 증상이 있습니다. 전문가 상담을 권장합니다.",
  "recommendations": [
    "정신건강의학과 전문의 상담 권장",
    "규칙적인 운동과 수면 습관 유지",
    "가까운 사람들과 대화하기"
  ],
  "timestamp": "2024-01-15T10:30:00"
}
```

**PHQ-9 점수 해석**:
- 0-4: 우울증 아님
- 5-9: 경증 우울
- 10-14: 중등도 우울
- 15-19: 중증 우울
- 20-27: 최중증 우울

**상태 코드**:
- `200`: 성공
- `400`: 잘못된 요청 (응답 개수 불일치 등)
- `429`: Rate limit 초과 (20/minute)
- `503`: 평가 시스템 사용 불가

**Rate Limit**: 20 requests/minute

---

### 6. 피드백 제출

사용자 피드백 수집

**Endpoint**: `POST /api/v1/feedback`

**Request Body**:
```json
{
  "session_id": "abc-123-def-456",
  "message_id": "msg-789",
  "rating": 5,
  "feedback_text": "정말 도움이 되었습니다",
  "feedback_type": "helpful"
}
```

**Parameters**:
- `rating`: 1-5 (필수)
- `feedback_type`: `helpful`, `not_helpful`, `inappropriate`, `other`

**Response**:
```json
{
  "message": "Feedback received successfully",
  "feedback_id": "fb-123-456"
}
```

**상태 코드**:
- `200`: 성공
- `400`: 잘못된 요청
- `429`: Rate limit 초과 (50/minute)

**Rate Limit**: 50 requests/minute

---

### 7. 시스템 통계

전체 시스템 통계 조회

**Endpoint**: `GET /api/v1/stats`

**Response**:
```json
{
  "total_conversations": 1234,
  "crisis_detections": 45,
  "assessments_conducted": 234,
  "active_sessions": 12,
  "uptime_seconds": 86400,
  "uptime_hours": 24.0,
  "timestamp": "2024-01-15T10:30:00"
}
```

---

### 8. 시스템 정보

시스템 기능 및 설정 정보

**Endpoint**: `GET /api/v1/system/info`

**Response**:
```json
{
  "system": "Korean Mental Health Counseling AI",
  "version": "1.0.0",
  "capabilities": {
    "crisis_detection": true,
    "emotion_analysis": true,
    "rag_system": true,
    "assessments": true,
    "monitoring": true,
    "logging": true
  },
  "model": {
    "name": "beomi/OPEN-SOLAR-KO-10.7B",
    "quantization": "4bit"
  },
  "features": [
    "Korean language support",
    "Multi-layered crisis detection",
    "Korean emotion analysis (han, jeong, etc.)",
    "Psychological assessments (PHQ-9, GAD-7, K-10)",
    "RAG-based knowledge retrieval",
    "Real-time monitoring",
    "PIPA-compliant logging"
  ]
}
```

---

### 9. Prometheus 메트릭

모니터링 메트릭 (Prometheus 형식)

**Endpoint**: `GET /metrics`

**Response** (Prometheus 형식):
```
# HELP api_requests_total Total API requests
# TYPE api_requests_total counter
api_requests_total{method="POST",endpoint="/chat",status="200"} 1234

# HELP api_response_time_seconds API response time
# TYPE api_response_time_seconds histogram
api_response_time_seconds_bucket{endpoint="/chat",le="0.5"} 500
api_response_time_seconds_bucket{endpoint="/chat",le="1.0"} 800

# HELP crisis_detections_total Total crisis detections
# TYPE crisis_detections_total counter
crisis_detections_total 45
```

---

### 10. 세션 정리

오래된 세션 삭제

**Endpoint**: `POST /api/v1/sessions/cleanup`

**Query Parameters**:
- `max_age_hours`: 최대 유지 시간 (기본값: 24시간)

**Response**:
```json
{
  "message": "Cleaned up 5 old sessions",
  "removed_count": 5
}
```

---

## 사용 예제

### Python 예제

```python
import requests

API_URL = "http://localhost:8000"
API_KEY = "your-api-key"  # 선택사항

headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY  # API Key 사용 시
}

# 1. 건강 체크
response = requests.get(f"{API_URL}/api/v1/health")
print(response.json())

# 2. 대화 시작
chat_data = {
    "message": "안녕하세요, 요즘 우울해서 힘들어요"
}

response = requests.post(
    f"{API_URL}/api/v1/chat",
    json=chat_data,
    headers=headers
)

result = response.json()
session_id = result["session_id"]
print(f"AI 응답: {result['response']}")
print(f"위기 감지: {result['crisis_detected']}")

# 3. 대화 계속하기 (같은 세션)
chat_data = {
    "session_id": session_id,
    "message": "2주 넘게 이런 상태예요"
}

response = requests.post(
    f"{API_URL}/api/v1/chat",
    json=chat_data,
    headers=headers
)

result = response.json()
print(f"AI 응답: {result['response']}")

# 4. PHQ-9 평가 실시
assessment_data = {
    "session_id": session_id,
    "assessment_type": "phq9",
    "responses": [2, 2, 2, 1, 1, 0, 1, 2, 0]  # 9개 응답
}

response = requests.post(
    f"{API_URL}/api/v1/assessment",
    json=assessment_data,
    headers=headers
)

result = response.json()
print(f"PHQ-9 점수: {result['score']}")
print(f"심각도: {result['severity']}")
print(f"해석: {result['interpretation']}")

# 5. 피드백 제출
feedback_data = {
    "session_id": session_id,
    "rating": 5,
    "feedback_text": "정말 도움이 되었습니다",
    "feedback_type": "helpful"
}

response = requests.post(
    f"{API_URL}/api/v1/feedback",
    json=feedback_data,
    headers=headers
)

print(response.json())
```

---

### JavaScript (Node.js) 예제

```javascript
const axios = require('axios');

const API_URL = 'http://localhost:8000';
const API_KEY = 'your-api-key';  // 선택사항

const headers = {
  'Content-Type': 'application/json',
  'X-API-Key': API_KEY  // API Key 사용 시
};

async function chatExample() {
  try {
    // 1. 건강 체크
    const health = await axios.get(`${API_URL}/api/v1/health`);
    console.log('Health:', health.data);

    // 2. 대화 시작
    const chatResponse = await axios.post(
      `${API_URL}/api/v1/chat`,
      {
        message: '안녕하세요, 요즘 우울해서 힘들어요'
      },
      { headers }
    );

    const { session_id, response, crisis_detected } = chatResponse.data;
    console.log('Session ID:', session_id);
    console.log('AI 응답:', response);
    console.log('위기 감지:', crisis_detected);

    // 3. 대화 계속하기
    const followUp = await axios.post(
      `${API_URL}/api/v1/chat`,
      {
        session_id: session_id,
        message: '2주 넘게 이런 상태예요'
      },
      { headers }
    );

    console.log('AI 응답:', followUp.data.response);

    // 4. PHQ-9 평가
    const assessment = await axios.post(
      `${API_URL}/api/v1/assessment`,
      {
        session_id: session_id,
        assessment_type: 'phq9',
        responses: [2, 2, 2, 1, 1, 0, 1, 2, 0]
      },
      { headers }
    );

    console.log('PHQ-9 점수:', assessment.data.score);
    console.log('심각도:', assessment.data.severity);

  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
}

chatExample();
```

---

### cURL 예제

```bash
# 1. 건강 체크
curl -X GET "http://localhost:8000/api/v1/health"

# 2. 대화 (API Key 없이)
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "안녕하세요, 요즘 우울해서 힘들어요"
  }'

# 3. 대화 (API Key 사용)
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "session_id": "abc-123",
    "message": "2주 넘게 이런 상태예요"
  }'

# 4. PHQ-9 평가
curl -X POST "http://localhost:8000/api/v1/assessment" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "session_id": "abc-123",
    "assessment_type": "phq9",
    "responses": [2, 2, 2, 1, 1, 0, 1, 2, 0]
  }'

# 5. 세션 조회
curl -X GET "http://localhost:8000/api/v1/session/abc-123" \
  -H "X-API-Key: your-api-key"

# 6. 시스템 통계
curl -X GET "http://localhost:8000/api/v1/stats" \
  -H "X-API-Key: your-api-key"
```

---

## 에러 처리

### 에러 응답 형식

모든 에러는 다음 형식으로 반환됩니다:

```json
{
  "error": "Error message",
  "detail": "Detailed error information",
  "status_code": 400,
  "timestamp": "2024-01-15T10:30:00"
}
```

### 주요 에러 코드

| 코드 | 의미 | 설명 |
|------|------|------|
| 400 | Bad Request | 잘못된 요청 (필수 필드 누락, 형식 오류 등) |
| 401 | Unauthorized | API Key 인증 실패 |
| 404 | Not Found | 리소스를 찾을 수 없음 (세션 등) |
| 429 | Too Many Requests | Rate limit 초과 |
| 500 | Internal Server Error | 내부 서버 오류 |
| 503 | Service Unavailable | 시스템 초기화 중 또는 사용 불가 |

### 에러 처리 예제 (Python)

```python
import requests

try:
    response = requests.post(
        "http://localhost:8000/api/v1/chat",
        json={"message": "안녕하세요"},
        headers={"X-API-Key": "invalid-key"}
    )
    response.raise_for_status()
    
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 401:
        print("API Key가 잘못되었습니다")
    elif e.response.status_code == 429:
        print("너무 많은 요청. 잠시 후 다시 시도하세요")
    elif e.response.status_code == 503:
        print("시스템이 초기화 중입니다. 잠시 후 다시 시도하세요")
    else:
        print(f"에러 발생: {e.response.json()}")
        
except requests.exceptions.RequestException as e:
    print(f"연결 오류: {e}")
```

---

## Rate Limiting

### 기본 제한

| 엔드포인트 | 제한 |
|-----------|------|
| `/api/v1/chat` | 100 requests/minute |
| `/api/v1/assessment` | 20 requests/minute |
| `/api/v1/feedback` | 50 requests/minute |
| 기타 엔드포인트 | 제한 없음 |

### Rate Limit 응답

제한 초과 시:

```json
{
  "error": "Rate limit exceeded: 100 per 1 minute",
  "status_code": 429,
  "timestamp": "2024-01-15T10:30:00"
}
```

### Rate Limit 변경

`.env` 파일에서 설정:

```bash
CHAT_RATE_LIMIT=200
ASSESSMENT_RATE_LIMIT=50
FEEDBACK_RATE_LIMIT=100
```

---

## 모니터링

### Prometheus 통합

`/metrics` 엔드포인트에서 Prometheus 메트릭 수집:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'mental-health-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### 주요 메트릭

- `api_requests_total`: 총 API 요청 수
- `api_response_time_seconds`: API 응답 시간
- `crisis_detections_total`: 총 위기 감지 횟수

### Grafana 대시보드

Grafana에서 메트릭 시각화:

1. Prometheus 데이터 소스 추가
2. 대시보드 생성
3. 주요 패널:
   - API 요청 수 (시계열)
   - 응답 시간 (히스토그램)
   - 위기 감지 횟수 (카운터)
   - 활성 세션 수 (게이지)

---

## 보안 권장사항

### 프로덕션 배포 시

1. **API Key 필수 사용**
   ```bash
   API_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
   ```

2. **HTTPS 사용**
   - Nginx 리버스 프록시 설정
   - Let's Encrypt SSL 인증서

3. **CORS 제한**
   ```bash
   ALLOWED_ORIGINS=https://your-domain.com,https://app.your-domain.com
   ```

4. **Rate Limiting 강화**
   - IP 기반 제한
   - 사용자별 제한

5. **로깅 및 모니터링**
   - 모든 요청 로그 기록
   - 이상 트래픽 감지
   - 알람 설정

---

## 문제 해결

### 시스템이 초기화되지 않음

```bash
# 로그 확인
docker logs mental-health-llm

# 수동 초기화 테스트
python -c "from main_integrated import IntegratedMentalHealthSystem; sys = IntegratedMentalHealthSystem(); sys.initialize_all_components()"
```

### GPU 메모리 부족

```bash
# .env 파일에서 메모리 제한 조정
MAX_MEMORY=30GB

# 또는 CPU 모드 사용
CUDA_ENABLED=false
```

### 느린 응답 속도

- RAG 시스템 비활성화 테스트: `ENABLE_RAG=false`
- 최대 응답 길이 축소: `MAX_LENGTH=200`
- GPU 사용 확인: CUDA가 활성화되어 있는지 확인

---

## 추가 리소스

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000

---

## 라이센스 및 책임

본 시스템은 정신건강 상담 지원 도구이며, 전문 의료 서비스를 대체하지 않습니다. 
긴급 상황 시 반드시 전문가에게 연락하시기 바랍니다.

- 자살예방상담전화: 1393 (24시간)
- 정신건강위기상담: 1577-0199
- 응급: 119

---

**문서 버전**: 1.0.0  
**마지막 업데이트**: 2024-01-15
