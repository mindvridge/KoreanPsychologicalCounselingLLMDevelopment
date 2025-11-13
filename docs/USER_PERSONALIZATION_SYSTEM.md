# 사용자별 개인화 시스템 (User Personalization System)
# Individualized Persona Recommendations

## 📊 개요 (Overview)

각 사용자의 **개인 선호도를 학습**하여 맞춤형 페르소나 추천을 제공하는 시스템입니다.

**핵심 기능:**
- ✅ 사용자별 페르소나 선호도 추적
- ✅ 개인 상호작용 이력 기록
- ✅ 개인화 가중치 자동 학습
- ✅ 전역 학습 + 개인화 결합 추천
- ✅ 선호 페르소나 표시 (⭐ 마커)

---

## 🏗️ 3단계 추천 시스템 (Three-Tier Recommendation)

```
Level 1: 규칙 기반 (Rule-Based)
         ↓
Level 2: 전역 학습 (Global Learning from All Users)
         ↓
Level 3: 개인화 (User-Specific Personalization)
         ↓
    최종 추천 (Final Recommendations)
```

### 가중치 계산 공식

```python
final_score = rule_score + global_learned_weight + personal_weight

where:
  rule_score = age_match(2.0) + concern_match(3.0~1.5)
  global_learned_weight = from feedback learning (all users)
  personal_weight = preference_score * 2.0 * confidence
```

---

## 🗄️ 데이터베이스 스키마

### UserPersonaPreference (사용자별 선호도)
```sql
CREATE TABLE user_persona_preferences (
    id INTEGER PRIMARY KEY,
    user_id INTEGER FOREIGN KEY,
    persona_id VARCHAR(50),

    -- 사용 통계
    total_sessions INTEGER,
    total_feedback_count INTEGER,
    average_rating FLOAT,

    -- 선호도 점수
    preference_score FLOAT,  -- -1 to +1 normalized

    -- 성공 통계
    successful_sessions INTEGER,
    success_rate FLOAT,

    -- 개인화 가중치
    personal_weight_adjustment FLOAT,  -- 최종 개인 가중치
    confidence FLOAT,  -- 신뢰도 (0-1)

    -- 시간 정보
    first_interaction DATETIME,
    last_interaction DATETIME
);
```

**선호도 계산:**
```python
# 평균 평점 기준 정규화 (3점 중립)
normalized_rating = (average_rating - 3.0) / 2.0  # -1 to +1

# 선호도 점수 (-1: 싫어함, 0: 중립, +1: 선호)
preference_score = clamp(normalized_rating, -1.0, 1.0)

# 신뢰도 (최소 10개 피드백 필요)
confidence = min(1.0, total_feedback_count / 10.0)

# 개인 가중치 조정
personal_weight_adjustment = preference_score * 2.0 * confidence
```

### UserInteractionHistory (상호작용 이력)
```sql
CREATE TABLE user_interaction_history (
    id INTEGER PRIMARY KEY,
    user_id INTEGER FOREIGN KEY,
    session_id VARCHAR(64),
    persona_id VARCHAR(50),

    -- 상호작용 정보
    interaction_type VARCHAR(20),  -- chat, feedback, recommendation
    duration_seconds INTEGER,
    message_count INTEGER,

    -- 결과
    rating INTEGER,  -- 1-5
    helpful BOOLEAN,
    completed BOOLEAN,

    -- 컨텍스트
    concerns JSON,  -- ["우울", "불안"]
    user_age_range VARCHAR(20),

    created_at DATETIME
);
```

---

## 📈 개인화 학습 알고리즘

### 1. 선호도 업데이트 (Preference Update)

**트리거:** 사용자가 페르소나에 피드백 제출 시

```python
# 평균 평점 업데이트 (이동 평균)
new_average = (old_average * (count-1) + new_rating) / count

# 성공 세션 카운트
if rating >= 4:
    successful_sessions += 1

# 성공률 계산
success_rate = successful_sessions / total_feedback_count

# 선호도 점수 계산
preference_score = (new_average - 3.0) / 2.0  # 정규화

# 신뢰도 계산
confidence = min(1.0, total_feedback_count / 10.0)

# 개인 가중치
personal_weight = preference_score * 2.0 * confidence
```

### 2. 추천 통합 (Recommendation Integration)

```python
# 1단계: 규칙 기반 점수
score = age_match_score + concern_match_score

# 2단계: 전역 학습 가중치 추가
if persona has global_learned_weight:
    score += global_learned_weight

# 3단계: 개인화 가중치 추가
if user has personal_weight for persona:
    score += personal_weight
    mark as personalized (⭐)

# 정렬 및 반환
return top_k_personas_by_score
```

---

## 🚀 API 사용법

### 1. 개인화된 추천 받기

**엔드포인트:** `POST /api/v1/personas/recommend`

**요청 (with user_id):**
```json
{
  "age_range": "20대",
  "concerns": ["우울", "불안"],
  "top_k": 3,
  "user_id": "user_abc123"
}
```

**응답:**
```json
{
  "recommendations": [
    {
      "id": "clinical_professional",
      "display_name": "김민준 박사",
      "score": 12.5,
      "reason": "⭐ 회원님 선호 | 우울, 불안 전문 | 20대 연령대에 적합",
      "personalized": true
    },
    {
      "id": "warm_mother",
      "display_name": "박은희 교수",
      "score": 10.2,
      "reason": "우울, 불안 전문 | 20대 연령대에 적합",
      "personalized": false
    }
  ],
  "reason": "Based on age: 20대, concerns: ['우울', '불안'] (AI-enhanced) + Personalized for you"
}
```

**⭐ 표시:** 사용자가 이전에 높은 평가를 준 페르소나

### 2. 사용자 선호도 조회

**엔드포인트:** `GET /api/v1/users/{user_id}/preferences`

**응답:**
```json
{
  "user_id": "user_abc123",
  "preferences": [
    {
      "persona_id": "clinical_professional",
      "preference_score": 0.8,
      "average_rating": 4.8,
      "total_feedback_count": 8,
      "success_rate": 1.0,
      "personal_weight_adjustment": 1.6,
      "confidence": 0.8,
      "first_interaction": "2025-10-01T10:00:00",
      "last_interaction": "2025-11-10T15:30:00"
    },
    {
      "persona_id": "warm_mother",
      "preference_score": 0.4,
      "average_rating": 4.2,
      "total_feedback_count": 5,
      "success_rate": 0.8,
      "personal_weight_adjustment": 0.4,
      "confidence": 0.5
    }
  ]
}
```

### 3. 사용자 통계 조회

**엔드포인트:** `GET /api/v1/users/{user_id}/stats`

**응답:**
```json
{
  "user_id": "user_abc123",
  "total_personas_tried": 5,
  "total_feedback_count": 15,
  "overall_average_rating": 4.5,
  "total_interactions": 25,
  "completed_interactions": 23,
  "completion_rate": 0.92,
  "favorite_persona": {
    "persona_id": "clinical_professional",
    "preference_score": 0.8,
    "interaction_count": 8
  },
  "personalization_active": true
}
```

**personalization_active:** 최소 3개 페르소나 경험 필요

---

## 🎯 사용 시나리오

### 시나리오 1: 신규 사용자 (Cold Start)

**Week 1: 규칙 기반 추천**
```
User: "20대, 우울, 불안"
→ clinical_professional (규칙: 20대 + 우울/불안 전문)
→ Rating: 5점 ✅
```

**Week 2: 전역 학습 시작**
```
User: Same concerns
→ clinical_professional (규칙 + 전역 학습 +0.2)
→ trauma_specialist (전역 학습에서 발견됨)
→ Rating: clinical_professional 5점, trauma_specialist 4점
```

**Week 3: 개인화 활성화!**
```
User: Same concerns
→ clinical_professional (규칙 + 전역 + ⭐개인 +1.6)
  Score: 12.8 (압도적 1위!)
→ Reason: "⭐ 회원님 선호 | 우울, 불안 전문"
```

### 시나리오 2: 싫어하는 페르소나 자동 배제

**상황:**
- 사용자가 workplace_specialist를 3번 시도
- 평균 평점 2.0 (낮음)

**학습 과정:**
```python
average_rating = 2.0
preference_score = (2.0 - 3.0) / 2.0 = -0.5  # 부정적
confidence = 3 / 10 = 0.3
personal_weight = -0.5 * 2.0 * 0.3 = -0.3

→ workplace_specialist의 점수 감소
→ 추천 순위에서 자동 하락 또는 제외
```

### 시나리오 3: 여러 페르소나 탐색

**Week 1-2: 탐색 단계**
```
Try: warm_mother (4점), clinical_professional (5점),
     friendly_peer (3점), cbt_specialist (5점)
```

**Week 3: 개인화 완성**
```
Preferences:
  clinical_professional: +1.6 (⭐ 최고 선호)
  cbt_specialist: +1.2 (⭐ 높은 선호)
  warm_mother: +0.4 (보통)
  friendly_peer: -0.2 (낮은 선호)

→ 추천 시 clinical/cbt가 항상 상위
→ friendly_peer는 자동으로 하위 또는 제외
```

---

## 🔧 개발자 가이드

### PersonaManager 통합

```python
from src.persona_manager import PersonaManager

pm = PersonaManager()

# 개인화 없이 (기본)
recs = pm.recommend_personas(
    age_range="20대",
    concerns=["우울"],
    db_session=db
)

# 개인화 포함
recs = pm.recommend_personas(
    age_range="20대",
    concerns=["우울"],
    db_session=db,
    user_id="user_abc123",  # ← 사용자 ID 추가
    use_personalization=True
)

# 개인화 표시 확인
for rec in recs:
    if rec['personalized']:
        print(f"⭐ {rec['display_name']} - 회원님 선호")
```

### 상호작용 기록

```python
from src.database import UserPersonalizationManager

# 상담 세션 종료 시
UserPersonalizationManager.record_interaction(
    db=db,
    user_id="user_abc123",
    session_id="session_456",
    persona_id="clinical_professional",
    interaction_type="chat",
    rating=5,
    helpful=True,
    duration_seconds=1200,
    message_count=25,
    concerns=["우울", "불안"],
    user_age_range="20대",
    completed=True
)
# → 자동으로 선호도 업데이트됨
```

### 사용자 선호도 조회

```python
# 사용자의 모든 선호도
preferences = UserPersonalizationManager.get_user_preferences(
    db=db,
    user_id="user_abc123",
    min_confidence=0.3  # 최소 신뢰도 30%
)

for pref in preferences:
    print(f"{pref['persona_id']}: {pref['preference_score']:.2f}")
    print(f"  Weight: {pref['personal_weight_adjustment']:+.2f}")

# 특정 페르소나 가중치
weight = UserPersonalizationManager.get_user_persona_weight(
    db=db,
    user_id="user_abc123",
    persona_id="clinical_professional"
)
print(f"Personal weight: {weight:+.2f}")
```

---

## 📊 성능 메트릭

### 개인화 효과 측정

```python
# 개인화 전후 비교
baseline_recs = pm.recommend_personas(
    age_range="20대",
    concerns=["우울"],
    use_personalization=False
)

personalized_recs = pm.recommend_personas(
    age_range="20대",
    concerns=["우울"],
    user_id="user_abc123",
    use_personalization=True
)

# 순위 변화 분석
for i, rec in enumerate(personalized_recs):
    baseline_rank = next(
        (j for j, r in enumerate(baseline_recs) if r['id'] == rec['id']),
        None
    )
    if baseline_rank is not None:
        change = baseline_rank - i
        if change > 0:
            print(f"{rec['display_name']}: ↑{change} (개인화 부스트)")
```

### 시스템 메트릭

- **Personalization Coverage**: 개인화 활성 사용자 비율
- **Average Personal Weight**: 평균 개인 가중치 절대값
- **Preference Confidence**: 평균 신뢰도
- **Ranking Changes**: 개인화로 인한 순위 변동

---

## 🚨 주의사항

### 1. Cold Start Problem

**문제:** 신규 사용자는 선호도 데이터 없음

**해결:**
- 규칙 기반 + 전역 학습으로 시작
- 최소 3개 페르소나 경험 권장
- 빠른 피드백 수집 (팝업/알림)

### 2. Privacy (프라이버시)

**문제:** 사용자별 데이터 저장

**보호:**
- user_id 해시화
- PIPA 준수 (동의 필요)
- 보관 기간 설정 (default: 90일)
- 사용자 요청 시 삭제

### 3. Filter Bubble (필터 버블)

**문제:** 같은 페르소나만 추천될 위험

**완화:**
- 탐색 보장 (epsilon-greedy)
- 다양성 보너스
- 주기적 새 페르소나 제안
- 사용자가 직접 선택 가능

### 4. 과적합 방지

**문제:** 소수 피드백에 과도 반응

**해결:**
- 신뢰도 기반 점진적 적용
- 최소 피드백 수 요구 (10개)
- 최대 가중치 제한

---

## 🔮 향후 개선

### 1. 컨텍스트 인식 개인화

```python
# 시간대별 선호도
if hour >= 22 or hour <= 6:
    prefer_calm_personas  # 밤에는 차분한 상담사

# 기분 기반 선호도
if mood == "angry":
    boost_anger_specialists
```

### 2. 협업 필터링 (Collaborative Filtering)

```python
# 유사 사용자 찾기
similar_users = find_similar_users(user_id, similarity_threshold=0.7)

# 유사 사용자가 좋아한 페르소나 추천
for similar_user in similar_users:
    recommend_their_favorites()
```

### 3. 딥러닝 기반 개인화

```python
# Neural Network Personalization
user_embedding = user_encoder(user_history)
persona_embedding = persona_encoder(persona_features)
score = dot_product(user_embedding, persona_embedding)
```

### 4. A/B 테스트 자동화

```python
# 개인화 효과 측정
for user in sample_users:
    group = random.choice(["control", "personalized"])

    if group == "personalized":
        recommendations = personalized_recommend()
    else:
        recommendations = baseline_recommend()

    track_satisfaction(user, recommendations, group)
```

---

## 💡 FAQ

**Q1: user_id를 제공하지 않으면 어떻게 되나요?**
- A: 규칙 기반 + 전역 학습만 적용됩니다. 개인화는 비활성화됩니다.

**Q2: 몇 번의 피드백이 필요한가요?**
- A: 최소 3개 페르소나 × 각 1번 = 3회부터 개인화 시작. 10회 이상에서 효과적입니다.

**Q3: 개인화를 비활성화할 수 있나요?**
- A: 네, `use_personalization=False` 파라미터로 비활성화 가능합니다.

**Q4: 선호도를 초기화할 수 있나요?**
- A: 현재 버전에서는 미지원. 향후 사용자 설정 기능 추가 예정.

**Q5: 여러 기기에서 동일한 개인화가 적용되나요?**
- A: 네, user_id가 동일하면 모든 기기에서 동기화됩니다.

---

## 📚 참고 자료

### 관련 문서
- [FEEDBACK_LEARNING_SYSTEM.md](./FEEDBACK_LEARNING_SYSTEM.md) - 전역 피드백 학습
- [PERSONA_SYSTEM_GUIDE.md](./PERSONA_SYSTEM_GUIDE.md) - 페르소나 시스템 전체
- [PERSONA_EXPANSION_SUMMARY.md](./PERSONA_EXPANSION_SUMMARY.md) - 18개 페르소나

### 학술 참고
- Collaborative Filtering
- Contextual Bandits
- Personalized Recommendation Systems
- User Modeling

---

## 🎯 핵심 정리

### 추천 시스템 진화

```
기본 (Basic)
  → 규칙 기반 (age + concerns)

+ 전역 학습 (Global Learning)
  → 모든 사용자 피드백 반영

+ 개인화 (Personalization)
  → 개인 선호도 반영
  → ⭐ 마커로 표시

= 완벽한 맞춤형 추천!
```

### 가중치 예시

| 페르소나 | 규칙 | 전역 학습 | 개인화 | 최종 점수 |
|---------|------|-----------|--------|----------|
| clinical_professional | 5.0 | +3.2 | ⭐ +1.6 | **9.8** |
| trauma_specialist | 5.0 | +3.8 | +0.0 | 8.8 |
| warm_mother | 5.0 | +2.5 | +0.4 | 7.9 |
| friendly_peer | 2.5 | +1.0 | -0.2 | 3.3 |

→ ⭐ clinical_professional이 압도적 1위!

---

**작성일**: 2025년 11월 13일
**버전**: 1.0.0
**상태**: 구현 완료 ✅
