# 한국어 심리상담 LLM 시스템 - 대화 일관성 분석 보고서

## 작성 일자: 2025-11-23
## 분석 범위: 대화 컨텍스트, 세션 관리, 페르소나, 감정 추적, RAG 통합

---

## 1. 현재 시스템 개요

### 1.1 주요 아키텍처
```
API 요청 → Chat Endpoint (/api/v1/chat)
    ↓
Session 관리 (메모리 기반)
    ↓
PersonalizationManager (DB 기반 장기 메모리)
    ↓
IntegratedMentalHealthSystem.process_message()
    ↓
감정분석 → 위기감지 → RAG → LLM 생성 → 응답
    ↓
세션 히스토리 업데이트 → DB 저장
```

---

## 2. 대화 컨텍스트/히스토리 관리 분석

### 2.1 현재 구조

#### A. 세션 레벨 저장소 (메모리)
**파일: src/api.py:299-301, 331-350**

```python
# In-memory session storage (use Redis in production)
sessions: Dict[str, Dict] = {}

def get_or_create_session(session_id: Optional[str] = None) -> str:
    """Get existing session or create new one"""
    # 새 세션 생성 시:
    sessions[new_session_id] = {
        "session_id": new_session_id,
        "created_at": datetime.now(),
        "last_activity": datetime.now(),
        "conversation_history": [],
        "crisis_detected_count": 0,
        "assessments": []
    }
```

**문제점:**
- ❌ 메모리 기반으로 서버 재시작 시 모든 대화 히스토리 손실
- ❌ 분산 시스템에서 세션 공유 불가능
- ❌ 프로덕션 환경에서 데이터 손실 위험

#### B. 히스토리 길이 제한
**파일: src/api.py:621-623**

```python
# Limit history length (keep last 20 messages)
if len(session_data["conversation_history"]) > 40:  # 20 pairs
    session_data["conversation_history"] = session_data["conversation_history"][-40:]
```

**문제점:**
- ❌ 최대 20개 턴만 유지하면, 긴 상담에서 초기 맥락 손실
- ❌ 초기 신뢰 형성 단계의 대화가 삭제될 수 있음
- ❌ 사용자의 장기 패턴 인식 불가능

#### C. LLM 생성 시 컨텍스트 활용
**파일: main_integrated.py:407-413**

```python
response = self.llm.generate_response(
    user_message,
    context=system_context,
    conversation_history=conversation_history,
    max_length=300
)
```

**문제점:**
- ❌ LLM이 장기 대화 컨텍스트를 모델 자체로 처리하지 못함
- ❌ 토큰 길이 제한(300 토큰)으로 충분한 응답 생성 어려움
- ❌ 복잡한 감정 상황에서 충분한 설명 불가

---

## 3. 세션 상태 유지 분석

### 3.1 세션 생명주기 관리

**파일: src/api.py:353-365**

```python
def cleanup_old_sessions(max_age_hours: int = 24):
    """Remove sessions older than max_age_hours"""
    cutoff = datetime.now() - timedelta(hours=max_age_hours)
    to_remove = [
        sid for sid, data in sessions.items()
        if data["last_activity"] < cutoff
    ]
    # 24시간 후 자동 삭제
```

**문제점:**
- ❌ 24시간 이상 간격을 둔 재방문 사용자의 맥락 완전 손실
- ❌ 심리상담에서는 여러 날에 걸친 추적이 매우 중요한데 미지원
- ❌ 사용자 동의 없이 자동 삭제

### 3.2 상태 추적 메커니즘

**파일: src/api.py:554-555**

```python
session_data = sessions[session_id]
history = chat_request.conversation_history or session_data["conversation_history"]
```

**문제점:**
- ❌ 클라이언트 제공 히스토리와 서버 히스토리 간 동기화 메커니즘 없음
- ❌ 클라이언트에서 전송한 히스토리가 신뢰할 수 없을 수 있음
- ❌ 부분적 히스토리 제공 시 불완전한 컨텍스트

---

## 4. 페르소나 일관성 유지 분석

### 4.1 페르소나 선택 메커니즘

**파일: src/api.py:93-102 (ChatRequest)**

```python
class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    persona_id: Optional[str] = None  # ← 요청에서 수신
    message: str = Field(...)
    conversation_history: Optional[List[Dict[str, str]]] = None
    consent: bool = Field(default=True)
```

**파일: src/api.py:592-596 (메시지 처리)**

```python
# Process message through integrated system
result = mental_health_system.process_message(
    session_id=session_id,
    user_message=enhanced_message,
    conversation_history=history
)
# ❌ persona_id를 전달하지 않음!
```

**파일: main_integrated.py:333-356 (process_message)**

```python
def process_message(
    self,
    session_id: str,
    user_message: str,
    conversation_history: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """
    Args:
        session_id: Session identifier
        user_message: User's message
        conversation_history: Previous conversation turns
    """
    # ❌ persona_id 매개변수 없음!
```

### 📍 **심각한 문제: 페르소나 정보가 LLM 생성에 반영되지 않음**

**파일: main_integrated.py:496-523**

```python
def _build_system_context(
    self,
    emotion_result: Optional[Dict],
    crisis_result: Optional[Dict],
    rag_context: str
) -> str:
    """Build system context for LLM"""
    context_parts = [
        "당신은 한국 정신건강 상담 AI입니다.",  # ← 고정 프롬프트
        "공감적이고 전문적으로 응답하세요.",
        "의료 진단이나 처방은 하지 마세요."
    ]
    # ❌ 선택된 페르소나(예: warm_mother, logical_analyst 등)가 반영되지 않음
```

**파일: src/prompts.py:33-100**

```python
def get_system_prompt(self, context: Optional[Dict] = None) -> str:
    """시스템 프롬프트 생성"""
    base_prompt = f"""당신은 '{self.persona_name}'입니다. 
    한국어를 사용하는 따뜻하고 전문적인 디지털 심리상담 도우미입니다.
    # ... 고정된 프롬프트"""
    # ✓ 페르소나 기반 프롬프트는 존재하지만, 
    # LLM 생성 때 사용되지 않음!
```

### 4.2 페르소나 일관성 부족의 영향

**예시 문제 시나리오:**
```
사용자1: "따뜻한 엄마(warm_mother) 페르소나 선택"
사용자2: "같은 메시지: '제 남친이 저를 무시해요...'"

warm_mother 페르소나 응답:
"안녕, 사랑하는 마음 헤아려. 그럼 남친분 태도에 대해 더 자세히..."

logical_analyst 페르소나 응답:
"당신의 관계 역학을 분석해보겠습니다. 먼저..."

⚠️ 현재 시스템: 어떤 페르소나를 선택하든 동일한 응답 생성!
```

---

## 5. 감정 상태 추적 분석

### 5.1 감정 분석 방식

**파일: src/emotion_analyzer_v2.py:44-56**

```python
def __init__(self, history_size: int = 20):
    """
    Args:
        history_size: 추적할 감정 히스토리 크기
    """
    self.emotion_expressions = self._load_emotion_expressions()
    self.korean_specific_emotions = self._load_korean_emotions()
    self.age_group_expressions = self._load_age_group_expressions()
    self.emotion_history = deque(maxlen=history_size)  # ← 최대 20개
    
    logger.info("KoreanEmotionAnalyzer initialized")
```

### 5.2 감정 히스토리 제한의 문제

**파일: src/emotion_analyzer_v2.py:54**

```python
self.emotion_history = deque(maxlen=history_size)  # ← 기본값: 20
```

**문제점:**
- ❌ 20개 감정 기록만 유지하면, 50개 턴 대화에서 처음 30개 턴의 감정 정보 손실
- ❌ 감정 변화 추적 불가능 (예: 우울 → 희망 → 다시 불안)
- ❌ 사용자의 감정 안정성 평가 불가능

### 5.3 감정 추적이 컨텍스트에 미치는 영향

**파일: main_integrated.py:365-369**

```python
# 1. Emotion analysis
emotion_result = None
if self.emotion_analyzer:
    emotion_result = self.emotion_analyzer.analyze_comprehensive(user_message)
    # ❌ 현재 메시지의 감정만 분석, 감정 추세 고려 안 함
```

**파일: main_integrated.py:509-512**

```python
if emotion_result:
    primary_emotion = emotion_result.get("primary_emotion", {}).get("emotion")
    if primary_emotion:
        context_parts.append(f"내담자의 주 감정: {primary_emotion}")
        # ✓ 현재 감정만 반영, 감정 변화 패턴 미반영
```

---

## 6. RAG 시스템과의 통합 분석

### 6.1 RAG 활성화 조건

**파일: main_integrated.py:384-394**

```python
# 3. RAG context retrieval (if not crisis)
rag_context = ""
if self.rag_system and not crisis_detected:  # ← 위기 시 비활성화!
    try:
        rag_context = self.rag_system.augment(
            query=user_message,
            conversation_history=conversation_history,
            k=self.config.get("rag", {}).get("max_results", 3)
        )
    except Exception as e:
        logger.warning(f"RAG retrieval failed: {e}")
```

### 📍 **문제: 위기 상황에서 RAG 컨텍스트가 완전히 비활성화됨**

**문제점:**
- ❌ 위기 상황에서 오히려 전문 지식 기반의 지원이 필요한데 무시됨
- ❌ 비위기 상황에서만 치료 기법 기반 응답 제공
- ❌ 대화 연속성 끊김 (위기 상황 전후로 응답 방식이 급격히 변함)

### 6.2 RAG 검색의 대화 이력 활용

**파일: src/rag_system.py에서 augment 메서드 추정**

```python
rag_context = self.rag_system.augment(
    query=user_message,
    conversation_history=conversation_history,  # ← 전체 히스토리 전달
    k=3
)
```

**문제점:**
- ❌ 40개 메시지(20 턴)로 제한된 히스토리만 사용
- ❌ 초기 맥락이 손실되면 RAG 검색도 편향될 수 있음
- ❌ 사용자의 초기 호소(chief complaint) 손실 시 부적절한 지식 검색

---

## 7. 대화 일관성을 저해하는 주요 요소 정리

### 7.1 심각도별 문제 분류

#### 🔴 **CRITICAL - 즉시 해결 필요**

| # | 문제 | 파일:라인 | 영향 | 심각도 |
|---|------|---------|------|--------|
| 1 | 페르소나 정보가 LLM 생성에 반영 안 됨 | src/api.py:592-596, main_integrated.py:333-356, 496-523 | 사용자가 선택한 상담사가 무시됨 | 🔴🔴🔴 |
| 2 | 위기 상황에서 RAG 완전 비활성화 | main_integrated.py:386 | 위기 상황 대응 품질 저하 | 🔴🔴 |
| 3 | 메모리 기반 세션 저장 (서버 재시작 시 손실) | src/api.py:299-350 | 데이터 손실, 프로덕션 부적합 | 🔴🔴 |

#### 🟠 **HIGH - 빠른 시일 내 개선 필요**

| # | 문제 | 파일:라인 | 영향 | 심각도 |
|---|------|---------|------|--------|
| 4 | 대화 히스토리 20 턴으로 제한 | src/api.py:622 | 긴 상담에서 초기 맥락 손실 | 🟠🟠 |
| 5 | 감정 히스토리 20개로 제한 | src/emotion_analyzer_v2.py:54 | 감정 추세 추적 불가 | 🟠🟠 |
| 6 | 24시간 자동 세션 삭제 | src/api.py:353-365 | 장기 추적 불가능 | 🟠🟠 |

#### 🟡 **MEDIUM - 개선 권장**

| # | 문제 | 파일:라인 | 영향 | 심각도 |
|---|------|---------|------|--------|
| 7 | 감정 정보가 현재 턴만 반영 | main_integrated.py:509-512 | 감정 변화 패턴 미반영 | 🟡 |
| 8 | 사용자 컨텍스트 LLM 반영 방식 미흡 | src/api.py:586-589 | 개인화 수준 저하 | 🟡 |
| 9 | 응답 길이 제한 (300 토큰) | main_integrated.py:412 | 복잡한 상황에 대한 설명 부족 | 🟡 |

---

## 8. 개선 방안

### 8.1 [우선순위 1] 페르소나 일관성 개선

#### 목표: 선택된 페르소나가 모든 응답에 반영되도록 개선

**구현 계획:**

1. **API 엔드포인트 수정**
   - 파일: `src/api.py:592-596`
   ```python
   # BEFORE
   result = mental_health_system.process_message(
       session_id=session_id,
       user_message=enhanced_message,
       conversation_history=history
   )
   
   # AFTER
   result = mental_health_system.process_message(
       session_id=session_id,
       user_message=enhanced_message,
       conversation_history=history,
       persona_id=chat_request.persona_id  # ← 추가
   )
   ```

2. **process_message 메서드 수정**
   - 파일: `main_integrated.py:333-356`
   ```python
   def process_message(
       self,
       session_id: str,
       user_message: str,
       conversation_history: Optional[List[Dict]] = None,
       persona_id: Optional[str] = None  # ← 추가
   ) -> Dict[str, Any]:
   ```

3. **system_context 생성 로직 수정**
   - 파일: `main_integrated.py:402-406`
   ```python
   system_context = self._build_system_context(
       emotion_result=emotion_result,
       crisis_result=crisis_result,
       rag_context=rag_context,
       persona_id=persona_id  # ← 추가
   )
   ```

4. **_build_system_context 메서드 수정**
   - 파일: `main_integrated.py:496-523`
   ```python
   def _build_system_context(
       self,
       emotion_result: Optional[Dict],
       crisis_result: Optional[Dict],
       rag_context: str,
       persona_id: Optional[str] = None  # ← 추가
   ) -> str:
       """Build system context for LLM"""
       # 페르소나 기반 프롬프트 로드
       if persona_id and self.persona_manager:
           persona = self.persona_manager.get_persona(persona_id)
           if persona:
               context_parts.append(f"페르소나: {persona.system_prompt}")
       else:
           context_parts.append("당신은 한국 정신건강 상담 AI입니다.")
   ```

5. **세션에 선택된 페르소나 저장**
   - 파일: `src/api.py:340-347`
   ```python
   sessions[new_session_id] = {
       "session_id": new_session_id,
       "created_at": datetime.now(),
       "last_activity": datetime.now(),
       "persona_id": chat_request.persona_id,  # ← 추가
       "conversation_history": [],
       "crisis_detected_count": 0,
       "assessments": []
   }
   ```

---

### 8.2 [우선순위 2] 장기 메모리 및 세션 지속성

#### 목표: 데이터베이스 기반 세션 관리로 지속성 확보

**구현 계획:**

1. **세션을 데이터베이스에 저장**
   - 파일: `src/database.py`에 Session 모델 추가
   ```python
   class Session(Base):
       __tablename__ = "sessions"
       
       id = Column(Integer, primary_key=True)
       session_id = Column(String(64), unique=True, nullable=False)
       user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
       persona_id = Column(String(50), nullable=True)  # ← 선택된 페르소나
       
       created_at = Column(DateTime, default=datetime.utcnow)
       last_activity = Column(DateTime, default=datetime.utcnow)
       
       # 관계
       user = relationship("User", back_populates="sessions")
       conversations = relationship("Conversation", back_populates="session")
   ```

2. **세션 조회/생성 로직 수정**
   - 파일: `src/api.py:331-350`
   ```python
   def get_or_create_session(
       session_id: Optional[str] = None,
       user_id: Optional[str] = None,
       persona_id: Optional[str] = None
   ) -> str:
       """Get existing session or create new one from DB"""
       db = next(get_db())
       try:
           # DB에서 세션 조회
           session = SessionManager.get_session(db, session_id)
           if session:
               SessionManager.update_last_activity(db, session_id)
               return session.session_id
           
           # 새 세션 DB에 저장
           session = SessionManager.create_session(
               db, user_id=user_id, persona_id=persona_id
           )
           return session.session_id
       finally:
           db.close()
   ```

3. **24시간 자동 삭제 제거 또는 완화**
   - 파일: `src/api.py:353-365` 수정
   ```python
   def cleanup_old_sessions(max_age_days: int = 90):  # 24시간 → 90일
       """Remove sessions older than max_age_days"""
       cutoff = datetime.now() - timedelta(days=max_age_days)
       # ... 유효 기간 확대
   ```

---

### 8.3 [우선순위 3] 대화 컨텍스트 길이 확대

#### 목표: 충분한 대화 이력 유지로 초기 맥락 보존

**구현 계획:**

1. **히스토리 길이 제한 확대**
   - 파일: `src/api.py:621-623` 수정
   ```python
   # BEFORE: 최대 20 턴 (40 메시지)
   if len(session_data["conversation_history"]) > 40:
       session_data["conversation_history"] = session_data["conversation_history"][-40:]
   
   # AFTER: 최대 50 턴 (100 메시지), 또는 스마트 컨텍스트 압축
   if len(session_data["conversation_history"]) > 100:
       # 스마트 요약: 초기 턴은 요약, 최근 턴은 전체 유지
       summarized = summarize_old_context(session_data["conversation_history"][:-60])
       session_data["conversation_history"] = summarized + session_data["conversation_history"][-60:]
   ```

2. **컨텍스트 압축 함수 구현**
   ```python
   def summarize_old_context(history: List[Dict]) -> List[Dict]:
       """초기 대화를 요약하여 토큰 절약"""
       if len(history) <= 5:
           return history
       
       # 처음 5개 턴은 유지, 나머지는 요약
       recent = history[-10:]
       old = history[:-10]
       
       # LLM으로 요약 생성
       summary = create_context_summary(old)
       
       return [{"role": "system", "content": f"[초기 대화 요약]\n{summary}"}] + recent
   ```

---

### 8.4 [우선순위 4] 감정 추적 개선

#### 목표: 감정 변화 추세 추적으로 더 정교한 응답 생성

**구현 계획:**

1. **감정 히스토리 확대**
   - 파일: `src/emotion_analyzer_v2.py:44`
   ```python
   # BEFORE
   self.emotion_history = deque(maxlen=history_size)  # 기본값: 20
   
   # AFTER
   self.emotion_history = deque(maxlen=max(100, history_size))  # 최소 100개
   ```

2. **감정 변화 분석 메서드 추가**
   ```python
   def analyze_emotion_trend(self) -> Dict[str, Any]:
       """감정 변화 추세 분석"""
       if len(self.emotion_history) < 3:
           return {"trend": "insufficient_data"}
       
       recent_emotions = list(self.emotion_history)[-10:]
       
       return {
           "trend": determine_trend(recent_emotions),  # 개선/악화/안정
           "dominant_emotion": most_common(recent_emotions),
           "emotion_diversity": calculate_diversity(recent_emotions),
           "peak_intensity": max(e.intensity for e in recent_emotions),
           "average_intensity": sum(e.intensity for e in recent_emotions) / len(recent_emotions)
       }
   ```

3. **process_message에서 감정 추세 활용**
   - 파일: `main_integrated.py:365-369` 수정
   ```python
   # BEFORE
   emotion_result = self.emotion_analyzer.analyze_comprehensive(user_message)
   
   # AFTER
   emotion_result = self.emotion_analyzer.analyze_comprehensive(user_message)
   emotion_trend = self.emotion_analyzer.analyze_emotion_trend()  # ← 추가
   
   # system_context에 반영
   if emotion_trend["trend"] == "deteriorating":
       context_parts.append("⚠️ 감정이 악화 추세입니다. 특별히 주의 깊은 대응이 필요합니다.")
   ```

---

### 8.5 [우선순위 5] RAG 시스템 개선

#### 목표: 모든 상황에서 일관된 지식 기반 지원

**구현 계획:**

1. **위기 상황에서도 RAG 활성화**
   - 파일: `main_integrated.py:384-394` 수정
   ```python
   # BEFORE
   rag_context = ""
   if self.rag_system and not crisis_detected:  # ← 위기 시 비활성화
       rag_context = self.rag_system.augment(...)
   
   # AFTER
   rag_context = ""
   if self.rag_system:
       query_type = "crisis" if crisis_detected else "normal"
       rag_context = self.rag_system.augment(
           query=user_message,
           conversation_history=conversation_history,
           k=5 if crisis_detected else 3,  # 위기 시 더 많은 참고 자료
           context_type=query_type
       )
   ```

2. **위기 상황별 RAG 검색 전략**
   ```python
   # rag_system.py에 추가
   def augment(
       self, 
       query: str, 
       conversation_history: Optional[List] = None,
       k: int = 3,
       context_type: str = "normal"
   ) -> str:
       """
       context_type:
       - "normal": 일반 상담 (예: 감정 처리, 인간관계)
       - "crisis": 위기 상황 (예: 자살, 자해)
       - "assessment": 평가 단계 (예: 증상 평가)
       """
       if context_type == "crisis":
           # 위기 대응 지식 기반 우선 검색
           documents = self.retrieve("긴급 대응", k=k, filter="crisis_protocols")
       else:
           documents = self.retrieve(query, k=k)
       
       return self._format_context(documents)
   ```

---

## 9. 대화 일관성 개선 로드맵

### Phase 1 (1주) - 페르소나 일관성
- [ ] 페르소나 정보를 `process_message`에 전달
- [ ] `_build_system_context`에서 페르소나 반영
- [ ] 세션에 선택된 페르소나 저장
- [ ] 테스트: 동일 메시지 → 다른 페르소나 선택 → 다른 응답 확인

### Phase 2 (1주) - 데이터베이스 세션 관리
- [ ] `Session` 테이블 설계 및 마이그레이션
- [ ] `SessionManager` 클래스 구현
- [ ] API 엔드포인트에서 DB 기반 세션 관리로 전환
- [ ] 테스트: 서버 재시작 후 세션 복원 확인

### Phase 3 (1주) - 컨텍스트 길이 확대
- [ ] 히스토리 길이 제한 50 턴으로 확대
- [ ] 컨텍스트 요약 함수 구현
- [ ] 토큰 길이 모니터링 추가
- [ ] 테스트: 긴 대화에서 초기 맥락 유지 확인

### Phase 4 (1주) - 감정 추적 개선
- [ ] 감정 히스토리 크기 100으로 확대
- [ ] `analyze_emotion_trend` 메서드 구현
- [ ] process_message에서 감정 추세 활용
- [ ] 테스트: 감정 변화 추적 정확성 확인

### Phase 5 (1주) - RAG 일관성
- [ ] 위기 상황에서도 RAG 활성화
- [ ] 위기 특화 검색 전략 구현
- [ ] 테스트: 위기 상황에서 정보 활용도 증가 확인

---

## 10. 성공 지표 (KPI)

### 대화 일관성 측정 방법

1. **페르소나 일관성**
   - [ ] 동일 메시지에 대해 다른 페르소나가 다른 응답 생성
   - [ ] 선택된 페르소나 특성이 전체 대화에 반영

2. **컨텍스트 유지**
   - [ ] 50+ 턴 대화에서 초기 맥락 참조 확인
   - [ ] 초반 사용자 이름/관심사가 후반에도 기억됨

3. **감정 일관성**
   - [ ] 감정 변화 추세가 응답에 반영 (예: "최근 점점 기분이 개선되고 있네요")
   - [ ] 감정 급변 시 특별 대응 활성화

4. **RAG 일관성**
   - [ ] 위기 상황에서도 치료 지식 기반 응답 제공
   - [ ] 비위기/위기 상황 간 응답 방식의 자연스러운 전환

---

## 11. 추가 개선 제안

### 11.1 클라이언트 측 개선

1. **세션 관리 상태 저장**
   - 로컬스토리지에 최근 5개 세션 저장
   - 서버 세션 손실 시 복구 가능

2. **오프라인 메시지 큐**
   - 네트워크 연결 끊김 시 메시지 로컬 저장
   - 복구 후 자동 동기화

### 11.2 서버 측 추가 개선

1. **Redis 캐싱 활용**
   - 메모리 세션 → Redis로 전환 (분산 시스템 지원)
   - 파일: `src/cache.py` 활용

2. **세션 버전 관리**
   - 각 턴마다 버전 번호 부여
   - 클라이언트/서버 동기화 버전 검증

3. **대화 요약 자동화**
   - 50 턴 이상 시 자동 요약 생성
   - 초기 대화 요약본을 컨텍스트에 포함

---

## 12. 참고: 관련 코드 라인 요약표

| 기능 | 파일명 | 라인 범위 | 설명 |
|------|--------|---------|------|
| 세션 관리 | src/api.py | 299-365 | 메모리 기반 세션 저장소 |
| Chat 엔드포인트 | src/api.py | 523-683 | 대화 요청 처리 |
| 메시지 처리 | main_integrated.py | 333-483 | 통합 시스템의 핵심 로직 |
| 시스템 컨텍스트 | main_integrated.py | 496-523 | LLM용 프롬프트 생성 |
| 감정 분석 | src/emotion_analyzer_v2.py | 44-150 | 감정 추적 |
| 페르소나 관리 | src/persona_manager.py | 63-301 | 상담사 페르소나 |
| 프롬프트 템플릿 | src/prompts.py | 23-100 | 시스템 프롬프트 |
| RAG 통합 | main_integrated.py | 384-394 | 지식 기반 검색 |

---

## 최종 결론

현재 한국어 심리상담 LLM 시스템은 **개별 컴포넌트는 잘 구현**되어 있으나, **대화 일관성 측면에서 다음 문제가 있습니다:**

### 주요 문제:
1. **페르소나 정보가 LLM 생성에 반영되지 않음** (심각)
2. **메모리 기반 세션 관리로 인한 데이터 손실 위험** (심각)
3. **짧은 대화 이력으로 인한 초기 맥락 손실** (높음)
4. **감정 변화 추세 추적 불가능** (높음)
5. **위기 상황에서 RAG 비활성화** (높음)

### 개선 효과:
이 5가지를 모두 개선하면:
- ✅ 사용자가 선택한 상담사 특성이 모든 응답에 반영
- ✅ 50+턴 이상 긴 상담에서도 초기 맥락 보존
- ✅ 사용자의 감정 변화를 감지하고 대응
- ✅ 위기 상황에서도 치료 지식 기반 지원
- ✅ 서버 재시작 후에도 세션 복원

**예상 개선 기간: 4-5주 (동시 진행 시 2-3주)**

