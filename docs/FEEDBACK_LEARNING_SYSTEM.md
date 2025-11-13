# 피드백 학습 시스템 (Feedback Learning System)
# Persona Recommendation Learning with User Feedback

## 📊 개요 (Overview)

페르소나 추천 시스템이 **사용자 피드백을 통해 자동으로 학습하고 개선**되는 기계학습 기반 시스템입니다.

**핵심 기능:**
- ✅ 사용자 만족도 수집 (1-5점 평점)
- ✅ 실시간 추천 가중치 학습
- ✅ 페르소나별 성능 통계
- ✅ 고민/나이대별 맞춤 최적화
- ✅ 신뢰도 기반 점진적 학습

---

## 🏗️ 시스템 아키텍처 (Architecture)

### 1. 데이터 수집 계층 (Data Collection Layer)

```
User Interaction → Feedback Submission → Database Storage
                                       ↓
                                  Learning Algorithm
                                       ↓
                                Weight Adjustment
```

### 2. 학습 알고리즘 (Learning Algorithm)

**이동 평균 기반 성공률 계산:**
```python
success_rate = (old_success_rate * (n-1) + new_result) / n
```

**가중치 조정 공식:**
```python
adjustment = (success_rate - 0.7) * 2.0 * confidence
final_weight = max(0.5, base_weight + adjustment)
```

**신뢰도 계산:**
```python
confidence = min(1.0, sample_count / 20.0)
```

### 3. 데이터베이스 스키마 (Database Schema)

#### PersonaFeedback (피드백 저장)
```sql
CREATE TABLE persona_feedback (
    id INTEGER PRIMARY KEY,
    user_id INTEGER FOREIGN KEY,
    session_id VARCHAR(64),
    persona_id VARCHAR(50),
    rating INTEGER CHECK(rating >= 1 AND rating <= 5),
    helpful BOOLEAN,
    appropriate BOOLEAN,
    would_recommend_again BOOLEAN,
    concerns_addressed JSON,
    feedback_text TEXT,
    user_age_range VARCHAR(20),
    created_at DATETIME
);
```

#### PersonaPerformance (성능 통계)
```sql
CREATE TABLE persona_performance (
    id INTEGER PRIMARY KEY,
    persona_id VARCHAR(50) UNIQUE,
    total_sessions INTEGER,
    total_feedback_count INTEGER,
    average_rating FLOAT,
    helpful_rate FLOAT,
    appropriate_rate FLOAT,
    recommendation_rate FLOAT,
    last_updated DATETIME
);
```

#### PersonaWeightAdjustment (학습된 가중치)
```sql
CREATE TABLE persona_weight_adjustments (
    id INTEGER PRIMARY KEY,
    persona_id VARCHAR(50),
    concern VARCHAR(50),
    age_range VARCHAR(20),
    base_weight FLOAT,
    adjustment FLOAT,
    final_weight FLOAT,
    sample_count INTEGER,
    success_rate FLOAT,
    confidence FLOAT,
    last_updated DATETIME
);
```

---

## 🚀 API 사용법 (API Usage)

### 1. 피드백 제출 (Submit Feedback)

**엔드포인트:** `POST /api/v1/personas/{persona_id}/feedback`

**요청 예시:**
```json
{
  "session_id": "session_123",
  "user_id": "user_456",
  "rating": 5,
  "helpful": true,
  "appropriate": true,
  "would_recommend_again": true,
  "concerns_addressed": ["우울", "불안"],
  "feedback_text": "매우 도움이 되었습니다. 공감능력이 뛰어나고 실질적인 조언을 주셨습니다.",
  "user_age_range": "20대"
}
```

**응답:**
```json
{
  "success": true,
  "message": "Feedback submitted successfully. Thank you for helping us improve!",
  "feedback_id": 123
}
```

**Python 예시:**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/personas/warm_mother/feedback",
    json={
        "session_id": "session_123",
        "rating": 5,
        "helpful": True,
        "appropriate": True,
        "would_recommend_again": True,
        "concerns_addressed": ["우울", "불안"],
        "user_age_range": "20대"
    },
    headers={"X-API-Key": "your-api-key"}
)

print(response.json())
```

### 2. 페르소나 성능 조회 (Get Performance Stats)

**엔드포인트:** `GET /api/v1/personas/{persona_id}/performance`

**응답 예시:**
```json
{
  "persona_id": "warm_mother",
  "total_feedback_count": 150,
  "average_rating": 4.7,
  "helpful_rate": 0.95,
  "appropriate_rate": 0.92,
  "recommendation_rate": 0.94,
  "last_updated": "2025-11-13T10:30:00"
}
```

**해석:**
- `average_rating: 4.7` → 평균 4.7점 (매우 우수)
- `helpful_rate: 0.95` → 95%의 사용자가 도움이 되었다고 평가
- `appropriate_rate: 0.92` → 92%가 적절한 추천이었다고 평가
- `recommendation_rate: 0.94` → 94%가 다시 추천받고 싶다고 응답

### 3. 전체 페르소나 분석 (All Personas Analytics)

**엔드포인트:** `GET /api/v1/personas/analytics/all`

**응답 예시:**
```json
{
  "personas": [
    {
      "persona_id": "trauma_specialist",
      "display_name": "박서현 박사 (트라우마 전문가)",
      "personality_type": "차분하고 안정적인",
      "total_feedback_count": 80,
      "average_rating": 4.9,
      "helpful_rate": 0.97,
      "appropriate_rate": 0.95,
      "recommendation_rate": 0.96
    },
    {
      "persona_id": "warm_mother",
      "display_name": "박은희 교수 (따뜻한 어머니)",
      "total_feedback_count": 150,
      "average_rating": 4.7,
      "helpful_rate": 0.95,
      "appropriate_rate": 0.92,
      "recommendation_rate": 0.94
    }
  ],
  "total_feedback_count": 1250,
  "overall_average_rating": 4.5
}
```

### 4. 학습된 가중치 조회 (Get Learned Weights)

**엔드포인트:** `GET /api/v1/personas/learning/weights`

**쿼리 파라미터:**
- `persona_id` (optional): 특정 페르소나 필터
- `concern` (optional): 고민 유형 필터 (예: "우울", "불안")
- `age_range` (optional): 나이대 필터 (예: "20대")

**응답 예시:**
```json
{
  "adjustments": [
    {
      "persona_id": "trauma_specialist",
      "concern": "성폭력",
      "age_range": "20대",
      "base_weight": 3.0,
      "adjustment": 0.8,
      "final_weight": 3.8,
      "sample_count": 25,
      "success_rate": 0.96,
      "confidence": 1.0
    },
    {
      "persona_id": "clinical_professional",
      "concern": "우울",
      "age_range": "30대",
      "base_weight": 3.0,
      "adjustment": 0.4,
      "final_weight": 3.4,
      "sample_count": 18,
      "success_rate": 0.85,
      "confidence": 0.9
    }
  ],
  "total": 2,
  "description": "Learned weight adjustments from user feedback"
}
```

**해석:**
- `trauma_specialist`는 20대 "성폭력" 고민에 대해 **96% 성공률**
- 기본 가중치 3.0에서 **+0.8 조정** → 최종 3.8
- 25개 샘플로 **신뢰도 100%** 달성

### 5. 학습 기반 추천 (Learned Recommendations)

**엔드포인트:** `POST /api/v1/personas/recommend`

학습된 가중치가 **자동으로 적용**됩니다.

**요청:**
```json
{
  "age_range": "20대",
  "concerns": ["성폭력", "트라우마"],
  "top_k": 3
}
```

**응답 (학습 전):**
```json
{
  "recommendations": [
    {"id": "warm_mother", "score": 8.0},
    {"id": "clinical_professional", "score": 7.5},
    {"id": "trauma_specialist", "score": 5.0}
  ]
}
```

**응답 (학습 후 - 피드백 반영):**
```json
{
  "recommendations": [
    {"id": "trauma_specialist", "score": 11.6},  // +3.8 (학습된 가중치)
    {"id": "warm_mother", "score": 8.0},
    {"id": "clinical_professional", "score": 7.5}
  ],
  "reason": "Based on age: 20대, concerns: ['성폭력', '트라우마'] (AI-enhanced with user feedback learning)"
}
```

---

## 📈 학습 메커니즘 (Learning Mechanism)

### 1. 성공 정의 (Success Criteria)

피드백이 **"성공"으로 간주되는 조건:**
- `rating >= 4` (4점 또는 5점)

### 2. 가중치 조정 로직 (Weight Adjustment Logic)

```python
# 1. 성공률 업데이트 (이동 평균)
new_success_rate = (old_success_rate * (n-1) + is_success) / n

# 2. 신뢰도 계산 (샘플 수에 비례, 최대 1.0)
confidence = min(1.0, sample_count / 20.0)

# 3. 가중치 조정 계산
success_delta = success_rate - 0.7  # 70%를 기준점으로
adjustment = success_delta * 2.0 * confidence

# 4. 최종 가중치 (최소 0.5 보장)
final_weight = max(0.5, base_weight + adjustment)
```

**예시 시나리오:**

| 샘플 수 | 성공률 | 신뢰도 | 조정값 | 최종 가중치 |
|--------|--------|--------|--------|------------|
| 5      | 0.80   | 0.25   | +0.05  | 3.05       |
| 10     | 0.85   | 0.50   | +0.15  | 3.15       |
| 20     | 0.90   | 1.00   | +0.40  | 3.40       |
| 30     | 0.95   | 1.00   | +0.50  | 3.50       |

**낮은 성공률 예시:**

| 샘플 수 | 성공률 | 신뢰도 | 조정값 | 최종 가중치 |
|--------|--------|--------|--------|------------|
| 5      | 0.40   | 0.25   | -0.15  | 2.85       |
| 10     | 0.35   | 0.50   | -0.35  | 2.65       |
| 20     | 0.30   | 1.00   | -0.80  | 2.20       |

### 3. 점진적 학습 (Progressive Learning)

**초기 단계 (샘플 < 5):**
- 신뢰도 낮음 (< 0.25)
- 작은 조정만 적용
- 규칙 기반 가중치 우세

**중간 단계 (샘플 5-20):**
- 신뢰도 증가 (0.25-1.0)
- 점진적 조정 증가
- 규칙과 학습의 균형

**성숙 단계 (샘플 >= 20):**
- 최대 신뢰도 (1.0)
- 완전한 학습 적용
- 데이터 기반 최적화

---

## 🎯 사용 시나리오 (Use Cases)

### 시나리오 1: 트라우마 전문가 발견

**상황:**
- 초기: "trauma_specialist"가 성폭력 고민에 낮은 순위
- 사용자들이 지속적으로 높은 평가 제공

**학습 과정:**
```
Week 1: 5건 피드백, 평균 5.0점 → 가중치 +0.1
Week 2: 15건 피드백, 평균 4.8점 → 가중치 +0.3
Week 4: 30건 피드백, 평균 4.9점 → 가중치 +0.5
```

**결과:**
- 성폭력 고민에 대해 1순위 추천으로 상승
- 사용자 만족도 지속적으로 높음

### 시나리오 2: 부적절한 매칭 감지

**상황:**
- "workplace_specialist"가 청소년 학업 스트레스에 추천됨
- 사용자들이 낮은 평가 제공

**학습 과정:**
```
Week 1: 4건 피드백, 평균 2.5점 → 가중치 -0.2
Week 2: 8건 피드백, 평균 2.3점 → 가중치 -0.4
Week 4: 15건 피드백, 평균 2.0점 → 가중치 -0.8
```

**결과:**
- 청소년 학업 고민에서 자동으로 순위 하락
- 더 적절한 "teen_specialist"가 상위 추천

### 시나리오 3: 연령대별 최적화

**상황:**
- "elderly_counselor"가 다양한 연령대에 추천됨
- 60대 이상에서만 높은 평가

**학습 결과:**
```
20대 + 노년: 성공률 30% → 가중치 -0.8
30대 + 노년: 성공률 40% → 가중치 -0.6
40대 + 노년: 성공률 60% → 가중치 -0.2
50대 + 노년: 성공률 80% → 가중치 +0.2
60대+ + 노년: 성공률 95% → 가중치 +0.5
```

**결과:**
- 60대 이상에 강력히 추천
- 젊은 연령대에는 자동 제외

---

## 🔧 개발자 가이드 (Developer Guide)

### 1. 피드백 수집 통합

**웹 인터페이스에서 수집:**
```javascript
// 상담 종료 시 피드백 요청
async function submitFeedback(personaId, sessionId) {
  const feedback = {
    session_id: sessionId,
    rating: document.getElementById('rating').value,
    helpful: document.getElementById('helpful').checked,
    appropriate: document.getElementById('appropriate').checked,
    would_recommend_again: document.getElementById('recommend').checked,
    concerns_addressed: selectedConcerns,
    feedback_text: document.getElementById('feedback-text').value,
    user_age_range: userAgeRange
  };

  const response = await fetch(
    `http://localhost:8000/api/v1/personas/${personaId}/feedback`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey
      },
      body: JSON.stringify(feedback)
    }
  );

  return response.json();
}
```

### 2. 성능 모니터링 대시보드

**Python 예시:**
```python
import requests
import pandas as pd
import matplotlib.pyplot as plt

def get_persona_analytics():
    response = requests.get(
        "http://localhost:8000/api/v1/personas/analytics/all",
        headers={"X-API-Key": "your-api-key"}
    )
    data = response.json()

    df = pd.DataFrame(data['personas'])

    # 평균 평점 순으로 정렬
    df = df.sort_values('average_rating', ascending=False)

    # 시각화
    plt.figure(figsize=(12, 6))
    plt.barh(df['display_name'], df['average_rating'])
    plt.xlabel('Average Rating')
    plt.title('Persona Performance Comparison')
    plt.tight_layout()
    plt.show()

    return df

analytics_df = get_persona_analytics()
print(analytics_df[['display_name', 'average_rating', 'total_feedback_count']])
```

### 3. A/B 테스트

**학습 vs 규칙 기반 비교:**
```python
def compare_recommendations(age_range, concerns):
    # 학습 기반
    learned_recs = requests.post(
        "http://localhost:8000/api/v1/personas/recommend",
        json={
            "age_range": age_range,
            "concerns": concerns,
            "top_k": 3
        }
    ).json()

    # 규칙 기반만 (학습 비활성화는 내부적으로 처리)

    return {
        "learned": learned_recs,
        "baseline": baseline_recs
    }
```

---

## 📊 성능 메트릭 (Performance Metrics)

### 1. 개별 페르소나 메트릭

- **Average Rating**: 평균 평점 (1-5)
- **Helpful Rate**: 도움 비율 (0-1)
- **Appropriate Rate**: 적절성 비율 (0-1)
- **Recommendation Rate**: 재추천 의향 비율 (0-1)

### 2. 시스템 전체 메트릭

- **Overall Average Rating**: 전체 평균 평점
- **Total Feedback Count**: 총 피드백 수
- **Learning Coverage**: 학습 커버리지 (학습된 조합 수)

### 3. 학습 품질 메트릭

- **Sample Count**: 샘플 수 (신뢰도와 직결)
- **Success Rate**: 성공률 (rating >= 4)
- **Confidence**: 신뢰도 (0-1)
- **Weight Adjustment**: 가중치 조정값

---

## 🚨 주의사항 (Cautions)

### 1. 콜드 스타트 문제 (Cold Start)

**문제:** 새 페르소나는 피드백이 없어 가중치 조정 없음

**해결:**
- 기본 규칙 기반 추천으로 시작
- 초기 사용자에게 피드백 적극 요청
- 유사 페르소나의 가중치 참고 (향후 개선)

### 2. 샘플 편향 (Sample Bias)

**문제:** 특정 사용자층만 피드백 제공 시 편향 발생

**완화:**
- 다양한 사용자에게 피드백 요청
- 연령/성별/고민 분포 모니터링
- 이상치 탐지 및 필터링

### 3. 과적합 방지 (Overfitting Prevention)

**문제:** 소수 샘플에 과도하게 반응

**해결:**
- 신뢰도 기반 점진적 학습 (confidence)
- 최소 가중치 보장 (0.5)
- 정기적 성능 검토 및 조정

---

## 🔮 향후 개선 (Future Improvements)

### 1. 고급 학습 알고리즘

- [ ] Thompson Sampling (탐색-활용 균형)
- [ ] Contextual Bandits
- [ ] Neural Network 기반 개인화

### 2. 다차원 학습

- [ ] 사용자 세션 길이 고려
- [ ] 시간대별 선호도 학습
- [ ] 대화 품질 메트릭 통합

### 3. 실시간 개인화

- [ ] 사용자별 개인화 가중치
- [ ] 세션 내 동적 조정
- [ ] 실시간 A/B 테스트

---

## 📚 참고 자료 (References)

### 관련 문서
- [PERSONA_SYSTEM_GUIDE.md](./PERSONA_SYSTEM_GUIDE.md) - 페르소나 시스템 전체 가이드
- [PERSONA_EXPANSION_SUMMARY.md](./PERSONA_EXPANSION_SUMMARY.md) - 페르소나 확장 내역

### 학술 참고
- Multi-Armed Bandit Algorithms
- Collaborative Filtering
- Contextual Recommendations
- Online Learning Systems

---

## 💡 FAQ

**Q1: 피드백을 얼마나 자주 수집해야 하나요?**
- A: 각 상담 세션 종료 시 1회 권장. 최소 20개 샘플 이상 수집 시 학습 효과 극대화.

**Q2: 학습된 가중치는 언제 반영되나요?**
- A: 실시간 즉시 반영. 피드백 제출 → 가중치 업데이트 → 다음 추천부터 적용.

**Q3: 잘못된 피드백을 삭제할 수 있나요?**
- A: 현재 버전에서는 미지원. 향후 관리자 도구에서 제공 예정.

**Q4: 개인정보는 어떻게 보호되나요?**
- A: user_id는 익명 해시, 피드백 텍스트는 개인정보 마스킹 권장.

**Q5: 학습 효과를 어떻게 확인하나요?**
- A: `/api/v1/personas/learning/weights`로 조정값 확인, analytics로 전후 비교.

---

**작성일**: 2025년 11월 13일
**버전**: 1.0.0
**상태**: 구현 완료 ✅
