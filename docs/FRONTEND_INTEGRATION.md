# 프론트엔드 통합 가이드
# Frontend Integration Guide

## 📋 목차 (Table of Contents)

1. [개요](#개요-overview)
2. [시스템 아키텍처](#시스템-아키텍처-system-architecture)
3. [프론트엔드 구조](#프론트엔드-구조-frontend-structure)
4. [백엔드 통합](#백엔드-통합-backend-integration)
5. [설치 및 실행](#설치-및-실행-installation--running)
6. [API 엔드포인트](#api-엔드포인트-api-endpoints)
7. [사용자 플로우](#사용자-플로우-user-flow)
8. [개발 가이드](#개발-가이드-development-guide)
9. [문제 해결](#문제-해결-troubleshooting)

---

## 개요 (Overview)

마음챗은 한국어 심리상담을 위한 AI 기반 웹 애플리케이션입니다. 이 문서는 프론트엔드와 백엔드의 통합 방법을 설명합니다.

### 핵심 기능
- ✅ **18명의 다양한 상담사 페르소나**: 따뜻한 어머니, 임상 전문가, 트라우마 전문가, 부부상담사 등
- ✅ **3단계 추천 시스템**: 규칙 기반 → 글로벌 학습 → 개인화
- ✅ **실시간 AI 채팅**: 선택한 페르소나와 1:1 상담
- ✅ **피드백 학습**: 사용자 피드백으로 추천 개선
- ✅ **개인화 시스템**: 사용자별 선호도 학습 및 맞춤 추천
- ✅ **위기 감지**: 자살/자해 위험 실시간 감지
- ✅ **개인 대시보드**: 상담 통계 및 선호도 시각화

---

## 시스템 아키텍처 (System Architecture)

```
┌─────────────────────────────────────────────────────────┐
│                    사용자 브라우저                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │           프론트엔드 (Frontend)                   │  │
│  │  • index.html (UI 구조)                          │  │
│  │  • styles.css (스타일링)                         │  │
│  │  • app.js (애플리케이션 로직)                    │  │
│  │  • config.js (설정)                              │  │
│  └──────────────────────────────────────────────────┘  │
│                         ↕ HTTP/HTTPS                    │
└─────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────┐
│               FastAPI 서버 (Backend)                     │
│  ┌──────────────────────────────────────────────────┐  │
│  │  정적 파일 서버 (Static Files)                   │  │
│  │  • GET /                → index.html             │  │
│  │  • GET /static/*        → CSS/JS/assets          │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  REST API (api.py)                               │  │
│  │  • POST /api/v1/personas/recommend              │  │
│  │  • POST /api/v1/chat                            │  │
│  │  • POST /api/v1/personas/{id}/feedback          │  │
│  │  • GET  /api/v1/users/{id}/preferences          │  │
│  └──────────────────────────────────────────────────┘  │
│                         ↕                               │
│  ┌──────────────────────────────────────────────────┐  │
│  │  비즈니스 로직 (Business Logic)                  │  │
│  │  • PersonaManager (persona_manager.py)           │  │
│  │  • IntegratedMentalHealthSystem (main.py)        │  │
│  │  • SafetySystem (safety_system_v2.py)            │  │
│  └──────────────────────────────────────────────────┘  │
│                         ↕                               │
│  ┌──────────────────────────────────────────────────┐  │
│  │  데이터 레이어 (Data Layer)                      │  │
│  │  • DatabaseManager (database.py)                 │  │
│  │  • PersonaFeedbackManager                        │  │
│  │  • UserPersonalizationManager                    │  │
│  └──────────────────────────────────────────────────┘  │
│                         ↕                               │
│  ┌──────────────────────────────────────────────────┐  │
│  │  데이터베이스 (SQLite)                           │  │
│  │  • users, sessions, messages                     │  │
│  │  • persona_feedback, persona_performance         │  │
│  │  • user_persona_preferences                      │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 프론트엔드 구조 (Frontend Structure)

### 파일 구조

```
frontend/
├── index.html      # 메인 HTML (4개 화면: Home, Chat, Feedback, Dashboard)
├── styles.css      # 스타일시트 (18KB, 반응형)
├── app.js          # 애플리케이션 로직 (26KB)
├── config.js       # 설정 파일 (2.6KB)
└── README.md       # 프론트엔드 문서
```

### 화면 구성

#### 1. **홈 화면 (Home Screen)** - `#home-screen`
- 연령대 선택 (10대 ~ 60대+)
- 고민 선택 (우울, 불안, 스트레스 등 15개)
- 사용자 ID 입력 (개인화 추천)
- 상담사 추천 버튼
- 추천 상담사 목록 (⭐ 개인화 마크)
- 전체 상담사 보기

#### 2. **채팅 화면 (Chat Screen)** - `#chat-screen`
- 상담사 정보 헤더
- 메시지 목록 (사용자/봇 구분)
- 메시지 입력창
- 위기 상황 경고
- 상담 종료 버튼

#### 3. **피드백 화면 (Feedback Screen)** - `#feedback-screen`
- 별점 평가 (1-5점)
- 도움됨/적절함/재사용 체크박스
- 자유 텍스트 피드백
- 제출/건너뛰기 버튼

#### 4. **대시보드 화면 (Dashboard Screen)** - `#dashboard-screen`
- 상담 통계 (총 횟수, 피드백 수, 선호 상담사)
- 상담사별 선호도 바 그래프
- 홈 돌아가기 버튼

### CSS 하이라이트

```css
/* 색상 변수 */
--primary-color: #6366f1;        /* 인디고 (주요 버튼) */
--secondary-color: #10b981;      /* 녹색 (성공) */
--danger-color: #ef4444;         /* 빨강 (위기) */
--warning-color: #f59e0b;        /* 주황 (개인화 배지) */

/* 반응형 브레이크포인트 */
@media (max-width: 768px) { /* 태블릿 */ }
@media (max-width: 480px) { /* 모바일 */ }

/* 한글 폰트 */
font-family: 'Noto Sans KR', ...;
```

### JavaScript 아키텍처

```javascript
// 전역 상태
AppState = {
    currentScreen, userId, currentCounselor,
    currentSession, chatHistory, selectedConcerns, allPersonas
}

// API 클라이언트
APIClient {
    getPersonaRecommendations(), getAllPersonas(),
    sendChatMessage(), submitFeedback(),
    getUserPreferences(), getUserStats()
}

// UI 헬퍼
UI {
    showScreen(), showLoading(), hideLoading(),
    showToast(), getAvatar(), formatTime()
}

// 화면 초기화 함수
initializeHomeScreen()
initializeChatScreen()
initializeFeedbackScreen()
loadDashboard()
```

---

## 백엔드 통합 (Backend Integration)

### FastAPI 정적 파일 설정 (src/api.py)

#### 1. 임포트 추가

```python
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
```

#### 2. 정적 파일 마운트

```python
# Static files (Frontend)
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
    logger.info(f"Frontend static files mounted at /static from {frontend_path}")
```

#### 3. 루트 엔드포인트 수정

```python
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - Serve frontend application"""
    frontend_path = Path(__file__).parent.parent / "frontend" / "index.html"
    if frontend_path.exists():
        return FileResponse(str(frontend_path))
    else:
        # Fallback to API info
        return {"name": "Korean Mental Health Counseling API", ...}
```

### CORS 설정

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 설치 및 실행 (Installation & Running)

### 전제 조건

```bash
# Python 3.8+
python --version

# 필요한 패키지 설치
pip install -r requirements.txt
```

### 백엔드 서버 시작

#### 방법 1: 직접 실행

```bash
cd /path/to/KoreanPsychologicalCounselingLLMDevelopment
python src/api.py
```

#### 방법 2: uvicorn 사용

```bash
uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
```

#### 방법 3: 환경 변수 설정

```bash
# .env 파일 생성
API_HOST=0.0.0.0
API_PORT=8000
RELOAD=true
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# 실행
python src/api.py
```

### 프론트엔드 접속

1. **웹 브라우저 열기**
   ```
   http://localhost:8000/
   ```

2. **API 문서 확인** (선택사항)
   ```
   http://localhost:8000/docs      # Swagger UI
   http://localhost:8000/redoc     # ReDoc
   ```

3. **정적 파일 직접 접근** (선택사항)
   ```
   http://localhost:8000/static/index.html
   http://localhost:8000/static/styles.css
   http://localhost:8000/static/app.js
   ```

---

## API 엔드포인트 (API Endpoints)

### Persona Endpoints

#### 1. 상담사 추천

```http
POST /api/v1/personas/recommend
Content-Type: application/json

{
    "age_range": "20대",
    "concerns": ["우울", "불안"],
    "user_id": "user_123",
    "top_k": 3
}
```

**응답:**
```json
{
    "recommendations": [
        {
            "id": "warm_mother",
            "name": "박은희",
            "display_name": "박은희 교수 (따뜻한 어머니)",
            "score": 8.5,
            "reason": "우울, 불안 문제에 전문성. ⭐ 회원님이 선호하는 스타일",
            "personalized": true,
            ...
        }
    ],
    "total": 3,
    "filters_applied": {...}
}
```

#### 2. 전체 상담사 조회

```http
GET /api/v1/personas/all
```

#### 3. 개별 상담사 조회

```http
GET /api/v1/personas/warm_mother
```

### Chat Endpoints

#### 채팅 메시지 전송

```http
POST /api/v1/chat
Content-Type: application/json

{
    "persona_id": "warm_mother",
    "message": "최근 우울감이 심해요",
    "session_id": "session_123",
    "user_id": "user_123"
}
```

**응답:**
```json
{
    "session_id": "session_123",
    "response": "힘든 시간을 보내고 계시는군요...",
    "crisis_detected": false,
    "crisis_level": 0,
    "safety_check": {
        "risk_level": "LOW",
        "keywords_found": [],
        "emergency_resources": []
    },
    "response_time": 1.23,
    "metadata": {...}
}
```

### Feedback Endpoints

#### 피드백 제출

```http
POST /api/v1/personas/warm_mother/feedback
Content-Type: application/json

{
    "user_id": "user_123",
    "session_id": "session_123",
    "rating": 5,
    "helpful": true,
    "appropriate": true,
    "would_recommend_again": true,
    "concerns_addressed": ["우울", "불안"],
    "feedback_text": "매우 도움이 되었습니다",
    "user_age_range": "20대"
}
```

#### 상담사 성과 조회

```http
GET /api/v1/personas/warm_mother/performance
```

**응답:**
```json
{
    "persona_id": "warm_mother",
    "total_feedback": 150,
    "average_rating": 4.7,
    "helpful_rate": 0.92,
    "appropriate_rate": 0.95,
    "recommendation_rate": 0.89
}
```

### User Endpoints

#### 사용자 선호도 조회

```http
GET /api/v1/users/user_123/preferences
```

**응답:**
```json
{
    "user_id": "user_123",
    "preferences": [
        {
            "persona_id": "warm_mother",
            "persona_name": "박은희 교수",
            "preference_score": 0.85,
            "average_rating": 4.8,
            "feedback_count": 12,
            "personal_weight_adjustment": 1.7
        }
    ],
    "total": 5,
    "personalization_active": true
}
```

#### 사용자 통계 조회

```http
GET /api/v1/users/user_123/stats
```

**응답:**
```json
{
    "user_id": "user_123",
    "total_sessions": 25,
    "total_feedback": 18,
    "favorite_persona": {
        "id": "warm_mother",
        "display_name": "박은희 교수",
        "interaction_count": 12
    },
    "average_session_rating": 4.6
}
```

---

## 사용자 플로우 (User Flow)

### 1. 초기 접속

```
사용자 접속 (http://localhost:8000/)
    ↓
index.html 로드 (FastAPI FileResponse)
    ↓
styles.css, config.js, app.js 로드 (/static/)
    ↓
홈 화면 표시
```

### 2. 상담사 선택 플로우

```
[홈 화면]
1. 사용자 ID 입력 (선택)
2. 연령대 선택
3. 고민 선택 (복수)
4. "상담사 추천받기" 클릭
    ↓
POST /api/v1/personas/recommend
    ↓
[추천 결과 표시]
• 매칭도 점수
• ⭐ 개인화 마크 (user_id 입력 시)
• 추천 이유
    ↓
5. 상담사 카드 클릭
    ↓
[채팅 화면 전환]
```

### 3. 채팅 플로우

```
[채팅 화면]
1. 초기 인사 메시지 표시
2. 사용자 메시지 입력
3. "전송" 버튼 클릭
    ↓
POST /api/v1/chat
    ↓
4. AI 응답 표시
5. 위기 감지 시 경고 표시
    ↓
6. 대화 반복
    ↓
7. "상담 종료" 클릭
    ↓
[피드백 화면 전환]
```

### 4. 피드백 플로우

```
[피드백 화면]
1. 상담사 이름 표시
2. 별점 선택 (1-5)
3. 체크박스 선택
4. 자유 텍스트 입력 (선택)
5. "제출하기" 클릭
    ↓
POST /api/v1/personas/{id}/feedback
    ↓
6. 성공 메시지 표시
    ↓
[홈 화면 복귀]
```

### 5. 대시보드 플로우

```
[헤더]
1. 사용자 메뉴 버튼 클릭
    ↓
GET /api/v1/users/{user_id}/stats
GET /api/v1/users/{user_id}/preferences
    ↓
[대시보드 화면]
• 총 상담 횟수
• 피드백 제출 횟수
• 선호 상담사
• 상담사별 선호도 바 그래프
```

---

## 개발 가이드 (Development Guide)

### 프론트엔드 커스터마이징

#### 새로운 화면 추가

1. **HTML에 화면 추가**
   ```html
   <div id="new-screen" class="screen">
       <!-- 내용 -->
   </div>
   ```

2. **CSS 스타일 추가**
   ```css
   #new-screen {
       /* 스타일 */
   }
   ```

3. **JavaScript 초기화 함수 추가**
   ```javascript
   function initializeNewScreen() {
       // 화면 로직
   }

   // 화면 전환
   UI.showScreen('new');
   ```

#### 새로운 API 호출 추가

```javascript
class APIClient {
    async newEndpoint(param) {
        return this.request('/new-endpoint', {
            method: 'POST',
            body: JSON.stringify({ param })
        });
    }
}
```

### 백엔드 엔드포인트 추가

```python
@app.post("/api/v1/new-endpoint", tags=["New"])
async def new_endpoint(request: NewRequest):
    """New endpoint description"""
    # 로직 구현
    return {"result": "success"}
```

### 로컬 개발 환경

#### 핫 리로드 활성화

```bash
uvicorn src.api:app --reload
```

#### 프론트엔드 수정 시
- HTML/CSS/JS 파일 저장
- 브라우저 새로고침 (Ctrl+F5)

#### 백엔드 수정 시
- Python 파일 저장
- uvicorn 자동 재시작 (--reload 옵션 시)

---

## 문제 해결 (Troubleshooting)

### 1. 프론트엔드가 로드되지 않음

**증상:** http://localhost:8000/ 접속 시 JSON 응답만 표시

**원인:**
- `frontend/` 디렉토리가 없거나 잘못된 위치

**해결:**
```bash
# 디렉토리 확인
ls -la frontend/

# 파일 존재 확인
ls frontend/index.html

# 권한 확인
chmod -R 755 frontend/
```

### 2. CORS 오류

**증상:** 브라우저 콘솔에 "Access-Control-Allow-Origin" 오류

**원인:**
- 다른 포트/도메인에서 프론트엔드 실행

**해결:**
```python
# src/api.py에서 CORS 설정 수정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 허용할 도메인
    ...
)
```

### 3. API 호출 실패

**증상:** 네트워크 오류, 404, 500 에러

**원인:**
- API 서버 미실행
- 잘못된 엔드포인트 URL
- 데이터베이스 미초기화

**해결:**
```bash
# API 서버 상태 확인
curl http://localhost:8000/api/v1/health

# 데이터베이스 확인
ls data/*.db

# 로그 확인
tail -f logs/api.log
```

### 4. 정적 파일 404 오류

**증상:** CSS/JS 파일 로드 실패

**원인:**
- 상대 경로 오류
- Static mount 미설정

**해결:**
```html
<!-- index.html에서 절대 경로 사용 -->
<link rel="stylesheet" href="/static/styles.css">
<script src="/static/config.js"></script>
<script src="/static/app.js"></script>
```

### 5. 로컬 스토리지 오류

**증상:** 사용자 ID 저장 실패, 세션 유지 안됨

**원인:**
- 브라우저 프라이빗 모드
- 로컬 스토리지 용량 초과

**해결:**
```javascript
// 브라우저 개발자 도구 → Console
localStorage.clear();  // 초기화
```

### 6. 개인화 추천 안됨

**증상:** ⭐ 마크가 표시되지 않음

**원인:**
- user_id 미입력
- 피드백 데이터 부족 (최소 3회 필요)

**해결:**
```bash
# 사용자 데이터 확인
curl http://localhost:8000/api/v1/users/user_123/preferences

# 피드백 확인
curl http://localhost:8000/api/v1/personas/warm_mother/performance
```

---

## 성능 최적화 (Performance Optimization)

### 프론트엔드

1. **CSS 최소화**: 프로덕션 빌드 시 CSS 압축
2. **JS 번들링**: Webpack/Rollup 사용
3. **이미지 최적화**: WebP 형식 사용
4. **캐싱**: Service Worker 활용
5. **레이지 로딩**: 화면별 코드 분할

### 백엔드

1. **응답 캐싱**: Redis 사용
2. **데이터베이스 인덱싱**: 자주 조회되는 컬럼
3. **비동기 처리**: async/await 최대 활용
4. **연결 풀링**: SQLAlchemy connection pool
5. **로드 밸런싱**: Nginx + Gunicorn

---

## 보안 고려사항 (Security Considerations)

### 1. 인증 (Authentication)

현재: API 키 (선택사항)
권장: JWT 토큰 기반 인증

```python
# 향후 개선: JWT 인증
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
```

### 2. 데이터 암호화

- HTTPS 사용 (프로덕션)
- 민감 데이터 암호화 저장
- 환경 변수로 시크릿 관리

### 3. 입력 검증

- Pydantic으로 요청 검증
- XSS 방지: 사용자 입력 이스케이프
- SQL Injection 방지: ORM 사용

### 4. 레이트 리미팅

```python
# src/api.py에서 이미 구현됨
@limiter.limit("5/minute")
async def endpoint():
    ...
```

---

## 배포 가이드 (Deployment Guide)

### Docker 배포

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ src/
COPY frontend/ frontend/
COPY configs/ configs/

EXPOSE 8000

CMD ["python", "src/api.py"]
```

```bash
# 빌드 및 실행
docker build -t maum-chat .
docker run -p 8000:8000 maum-chat
```

### Nginx 설정 (프록시)

```nginx
server {
    listen 80;
    server_name maum-chat.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        alias /path/to/frontend/;
    }
}
```

---

## 리소스 (Resources)

### 문서

- [프론트엔드 README](../frontend/README.md)
- [페르소나 시스템 가이드](PERSONA_SYSTEM_GUIDE.md)
- [피드백 학습 시스템](FEEDBACK_LEARNING_SYSTEM.md)
- [사용자 개인화 시스템](USER_PERSONALIZATION_SYSTEM.md)

### API 문서

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 외부 링크

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [Noto Sans KR 폰트](https://fonts.google.com/noto/specimen/Noto+Sans+KR)

---

## 라이선스 (License)

이 프로젝트의 라이선스를 따릅니다.

---

## 문의 (Contact)

문제가 있거나 개선 제안이 있으시면 이슈를 등록해주세요.

**🎉 프론트엔드 통합 완료!**
