# 마음챗 프론트엔드 (Frontend)

## 개요 (Overview)

마음챗 웹 프론트엔드는 한국어 심리상담 AI 시스템을 위한 사용자 인터페이스입니다.

Korean Psychological Counseling LLM의 웹 기반 사용자 인터페이스로, 상담사 선택, 채팅, 피드백 제출, 개인화 대시보드를 제공합니다.

## 기술 스택 (Tech Stack)

- **HTML5**: 구조
- **CSS3**: 스타일링 (반응형 디자인)
- **Vanilla JavaScript**: 애플리케이션 로직
- **FastAPI Static Files**: 서버 통합

## 파일 구조 (File Structure)

```
frontend/
├── index.html      # 메인 HTML 파일 (페르소나 선택, 채팅, 피드백, 대시보드)
├── styles.css      # 전체 스타일시트 (반응형, 한글 최적화)
├── app.js          # 메인 JavaScript 애플리케이션
├── config.js       # 설정 및 헬퍼 함수
└── README.md       # 이 파일
```

## 주요 기능 (Features)

### 1. 상담사 선택 (Counselor Selection)
- 연령대 및 고민 선택
- 사용자 ID 입력 (개인화 추천)
- AI 기반 상담사 추천 (3단계 시스템)
- 전체 상담사 목록 보기
- ⭐ 개인화 추천 표시

### 2. 실시간 채팅 (Real-time Chat)
- 선택한 상담사와 1:1 채팅
- 메시지 히스토리
- 위기 감지 및 경고
- 자동 스크롤

### 3. 피드백 시스템 (Feedback System)
- 5점 별점 평가
- 상세 피드백 항목
- 자유 텍스트 피드백
- 개인화 학습에 활용

### 4. 사용자 대시보드 (User Dashboard)
- 상담 통계
- 개인 선호도 시각화
- 선호 상담사 확인

## 설정 (Configuration)

`config.js`에서 다음을 설정할 수 있습니다:

```javascript
const CONFIG = {
    API_BASE_URL: 'http://localhost:8000/api/v1',  // API 서버 주소
    API_KEY: null,                                  // API 키 (필요시)
    DEFAULT_TOP_K: 3,                               // 추천 상담사 수
    // ...
};
```

## API 통합 (API Integration)

프론트엔드는 다음 백엔드 엔드포인트를 사용합니다:

### Persona Endpoints
- `POST /api/v1/personas/recommend` - 상담사 추천
- `GET /api/v1/personas/all` - 전체 상담사 조회
- `GET /api/v1/personas/{persona_id}` - 개별 상담사 조회

### Chat Endpoints
- `POST /api/v1/chat` - 채팅 메시지 전송

### Feedback Endpoints
- `POST /api/v1/personas/{persona_id}/feedback` - 피드백 제출
- `GET /api/v1/personas/{persona_id}/performance` - 상담사 성과 조회

### User Endpoints
- `GET /api/v1/users/{user_id}/preferences` - 사용자 선호도 조회
- `GET /api/v1/users/{user_id}/stats` - 사용자 통계 조회

## 실행 방법 (How to Run)

### 1. FastAPI 서버 시작

```bash
# 프로젝트 루트에서
python src/api.py
```

또는

```bash
uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 브라우저에서 접속

```
http://localhost:8000/
```

프론트엔드가 자동으로 로드됩니다.

### 3. API 문서 확인 (선택사항)

```
http://localhost:8000/docs
```

## 로컬 스토리지 (Local Storage)

프론트엔드는 다음 데이터를 브라우저 로컬 스토리지에 저장합니다:

- `maum_user_id`: 사용자 ID
- `maum_current_session`: 현재 세션 정보
- `maum_selected_counselor`: 선택된 상담사
- `maum_chat_history`: 채팅 기록

## 반응형 디자인 (Responsive Design)

모든 화면 크기에 최적화:
- 데스크톱 (1200px+)
- 태블릿 (768px ~ 1199px)
- 모바일 (< 768px)

## 접근성 (Accessibility)

- 한글 폰트 최적화 (Noto Sans KR)
- 고대비 색상
- 키보드 네비게이션 지원
- 스크린 리더 호환

## 브라우저 호환성 (Browser Compatibility)

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 개발 가이드 (Development Guide)

### 상태 관리 (State Management)

```javascript
const AppState = {
    currentScreen: 'home',       // 현재 화면
    userId: null,                // 사용자 ID
    currentCounselor: null,      // 선택된 상담사
    currentSession: null,        // 현재 세션
    chatHistory: [],             // 채팅 기록
    selectedConcerns: [],        // 선택된 고민
    allPersonas: []              // 전체 상담사 목록
};
```

### 화면 전환 (Screen Navigation)

```javascript
UI.showScreen('home');       // 홈 화면
UI.showScreen('chat');       // 채팅 화면
UI.showScreen('feedback');   // 피드백 화면
UI.showScreen('dashboard');  // 대시보드 화면
```

### API 호출 예제 (API Call Example)

```javascript
// 상담사 추천
const recommendations = await api.getPersonaRecommendations(
    '20대',              // 연령대
    ['우울', '불안'],    // 고민
    'user_123',          // 사용자 ID
    3                    // 추천 개수
);

// 채팅 메시지 전송
const response = await api.sendChatMessage(
    'warm_mother',       // 상담사 ID
    '안녕하세요',        // 메시지
    'session_123',       // 세션 ID
    'user_123'           // 사용자 ID
);

// 피드백 제출
await api.submitFeedback('warm_mother', {
    user_id: 'user_123',
    session_id: 'session_123',
    rating: 5,
    helpful: true,
    appropriate: true,
    would_recommend_again: true,
    concerns_addressed: ['우울', '불안'],
    feedback_text: '매우 도움이 되었습니다',
    user_age_range: '20대'
});
```

## 문제 해결 (Troubleshooting)

### API 연결 오류
- FastAPI 서버가 실행 중인지 확인
- CORS 설정 확인
- 브라우저 콘솔에서 오류 확인

### 정적 파일 로드 실패
- `frontend/` 디렉토리가 프로젝트 루트에 있는지 확인
- FastAPI 정적 파일 마운트 확인
- 파일 권한 확인

### 로컬 스토리지 문제
- 브라우저 개발자 도구 → Application → Local Storage 확인
- 필요시 로컬 스토리지 초기화

## 향후 개선 사항 (Future Improvements)

- [ ] PWA (Progressive Web App) 지원
- [ ] 다크 모드
- [ ] 음성 입력/출력
- [ ] 알림 시스템
- [ ] 채팅 내역 검색
- [ ] 멀티 세션 관리
- [ ] 소셜 로그인 통합

## 라이선스 (License)

이 프로젝트의 라이선스를 따릅니다.

## 문의 (Contact)

문제가 있거나 개선 제안이 있으시면 이슈를 등록해주세요.
