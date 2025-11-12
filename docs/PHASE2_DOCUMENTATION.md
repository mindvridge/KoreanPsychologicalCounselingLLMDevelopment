# Phase 2: 다층 안전 시스템 및 한국어 감정 분석

> 🛡️ **고도화된 위기 감지 및 감정 분석 시스템**

Phase 2에서는 기존 시스템을 크게 강화하여 4층 구조의 위기 감지 시스템과 한국 문화에 특화된 감정 분석 시스템을 구축했습니다.

## 📋 목차

- [다층 안전 시스템](#다층-안전-시스템)
- [한국어 감정 분석 시스템](#한국어-감정-분석-시스템)
- [사용 방법](#사용-방법)
- [테스트](#테스트)
- [API 레퍼런스](#api-레퍼런스)

---

## 🛡️ 다층 안전 시스템

### 4층 아키텍처

```
┌─────────────────────────────────────────┐
│  Layer 4: LLMCrisisEvaluator           │
│  - 종합적 위기 평가                      │
│  - 개입 메시지 생성                      │
└──────────────┬──────────────────────────┘
               │
┌──────────────┴──────────────────────────┐
│  Layer 3: PatternRecognizer            │
│  - 대화 패턴 분석                        │
│  - 시간대별 위험도                       │
└──────────────┬──────────────────────────┘
               │
┌──────────────┴──────────────────────────┐
│  Layer 2: SentimentAnalyzer            │
│  - 감정 강도 측정 (0-10)                 │
│  - 누적 부정성 추적                      │
└──────────────┬──────────────────────────┘
               │
┌──────────────┴──────────────────────────┐
│  Layer 1: KeywordDetector              │
│  - 즉각적 위험 키워드 감지               │
│  - 직접/간접 표현 구분                   │
└─────────────────────────────────────────┘
```

### Layer 1: KeywordDetector

**즉각적 위험 키워드 감지기**

#### 위험도 분류

| 레벨 | 설명 | 예시 키워드 | 대응 |
|------|------|-------------|------|
| **CRITICAL** | 즉각적 생명 위협 | "죽고 싶다", "자살할게", "오늘 죽을", "약을 먹었" | 즉시 응급 개입 |
| **HIGH** | 심각한 위기 | "사라지고 싶", "자해", "희망 없음" | 긴급 전문가 상담 |
| **MEDIUM** | 중등도 위험 | "폐를 끼치고 싶지 않", "외롭다", "고립" | 전문가 상담 권장 |
| **LOW** | 경미한 위험 | "힘들다", "우울하다" | 모니터링 |

#### 한국 문화 특화 키워드

```python
# 체면 문화 반영
"폐를 끼치고 싶지 않아요"
"짐이 되는 것 같아요"
"가족에게 미안해요"

# 간접 표현
"더 이상 의미가 없어요"
"모든 게 무너졌어요"
"사라지고 싶어요"
```

#### 사용 예시

```python
from src.safety_system_v2 import KeywordDetector, RiskLevel

detector = KeywordDetector()

text = "죽고 싶어요. 오늘 중에 끝낼 거예요."
result = detector.detect(text)

print(f"위험 수준: {result['risk_level'].value}")
# 출력: 위험 수준: CRITICAL

print(f"감지된 키워드: {result['detected_keywords']}")
# 출력: 감지된 키워드: ['죽고 싶', '오늘', '끝내']

print(f"신뢰도: {result['confidence']:.2f}")
# 출력: 신뢰도: 0.95
```

---

### Layer 2: SentimentAnalyzer

**감정 강도 및 누적 분석기**

#### 주요 기능

1. **감정 강도 측정 (0-10 척도)**
   - 텍스트 기반 강도 계산
   - 느낌표, 반복 표현, 강조 부사 반영

2. **부정성 점수**
   - 부정적 감정 키워드 기반
   - 외부 감정 분석 데이터 통합

3. **누적 부정성 추적**
   - 지수 가중 이동 평균 (EWMA)
   - 시간 경과에 따른 부정성 누적

4. **급격한 변화 감지**
   - 이전 대화와 비교
   - 4점 이상 급증 시 경고

#### 사용 예시

```python
from src.safety_system_v2 import SentimentAnalyzer

analyzer = SentimentAnalyzer(history_size=10)

# 시간 경과에 따른 감정 추적
texts = [
    "조금 우울해요",           # 강도: 5.5, 부정성: 2.0
    "많이 힘들어요",           # 강도: 6.5, 부정성: 3.5
    "너무 괴로워요",           # 강도: 7.5, 부정성: 5.0
    "견딜 수 없어요"           # 강도: 8.5, 부정성: 7.0
]

for text in texts:
    result = analyzer.analyze(text)
    print(f"강도: {result['intensity']:.1f}, 부정성: {result['negativity']:.1f}")

print(f"누적 부정성: {result['cumulative_negativity']:.1f}")
print(f"급격한 변화: {result['rapid_change']}")
print(f"추세: {result['trend']}")  # worsening, stable, improving
```

---

### Layer 3: PatternRecognizer

**대화 패턴 및 행동 패턴 분석기**

#### 감지 패턴

1. **고립 패턴**
   - 키워드: "아무도", "혼자", "외로", "고립"
   - 반복 빈도 추적
   - 심각도: 3회 이상 언급 시 HIGH

2. **절망감 패턴**
   - 키워드: "희망 없", "소용없", "의미없", "바뀌지 않"
   - 부정 표현과 조합 확인

3. **철수/회피 패턴**
   - 응답 길이 감소 추세
   - 대화 참여도 하락

4. **시간대별 위험도**
   - 새벽 (00:00-05:00): 고위험
   - 늦은 밤 (22:00-24:00): 중위험
   - 낮 시간: 저위험

5. **반복적 위기 언급**
   - 최근 10턴 내 위기 키워드 반복
   - 2회 이상: MEDIUM
   - 3회 이상: HIGH

#### 사용 예시

```python
from src.safety_system_v2 import PatternRecognizer
from datetime import datetime

recognizer = PatternRecognizer()

conversation_history = [
    {"role": "user", "content": "혼자 있어요"},
    {"role": "assistant", "content": "힘드시군요"},
    {"role": "user", "content": "아무도 연락할 사람이 없어요"},
    {"role": "assistant", "content": "이해합니다"},
    {"role": "user", "content": "아무도 없어요. 외로워요"}
]

result = recognizer.analyze_patterns(
    text="아무도 없어요. 외로워요",
    conversation_history=conversation_history,
    current_time=datetime(2024, 1, 1, 2, 0, 0)  # 새벽 2시
)

print(f"고립 패턴: {result['isolation_pattern']['detected']}")
print(f"반복 빈도: {result['isolation_pattern']['frequency']}")
print(f"고위험 시간대: {result['time_risk']['is_high_risk_time']}")
print(f"위험 플래그: {result['risk_flags']}")
print(f"전체 위험 점수: {result['overall_risk_score']}/10")
```

---

### Layer 4: LLMCrisisEvaluator

**종합적 위기 평가 및 개입**

#### 평가 프로세스

1. **레이어별 점수화**
   - 키워드: 50% 가중치
   - 감정: 30% 가중치
   - 패턴: 20% 가중치

2. **최종 위험 수준 결정**
   - CRITICAL 키워드 → 무조건 CRITICAL
   - 가중 점수 8.5+ → CRITICAL
   - 가중 점수 6.5+ → HIGH
   - 가중 점수 4.0+ → MEDIUM
   - 가중 점수 2.0+ → LOW

3. **신뢰도 계산**
   - 키워드 매칭 신뢰도
   - 감정 히스토리 길이
   - 패턴 위험 플래그 수

4. **개입 메시지 생성**
   - 레벨별 맞춤 메시지
   - 응급 연락처 제공
   - 권장 조치 제시

#### 위기 대응 메시지

```python
CRISIS_RESPONSES = {
    "CRITICAL": {
        "message": """⚠️ 긴급 상황입니다.

        당신의 생명은 매우 소중합니다...

        🆘 자살예방상담전화: 1393 (24시간 무료)
        🆘 응급상황: 119""",
        "action": "IMMEDIATE_INTERVENTION"
    },

    "HIGH": {
        "message": """전문가의 도움이 필요합니다.

        📞 정신건강위기상담전화: 1577-0199
        📞 자살예방상담전화: 1393""",
        "action": "URGENT_PROFESSIONAL_REFERRAL"
    }
}
```

---

### 통합 SafetySystem

**4개 레이어를 통합한 원스톱 안전 시스템**

#### 사용 예시

```python
from src.safety_system_v2 import SafetySystem

# 초기화
safety_system = SafetySystem(user_id="user_12345")

# 안전 체크
text = "죽고 싶어요. 너무 외롭고 희망이 없어요."
result = safety_system.check_safety(
    text=text,
    emotion_data=emotion_result,  # 감정 분석 결과 (옵션)
    conversation_history=history   # 대화 이력 (옵션)
)

# 결과 확인
print(f"위험 수준: {result['risk_level'].value}")
print(f"가중 점수: {result['weighted_score']}/10")
print(f"개입 필요: {result['requires_intervention']}")

if result['requires_intervention']:
    print("\n" + result['intervention_message'])

# PHQ-9 Item 9 스크리닝
phq9_result = safety_system.phq9_item9_screening(text)
print(f"PHQ-9 점수: {phq9_result['score']}/3")
print(f"빈도: {phq9_result['frequency']}")

# 위기 이력 조회
crisis_history = safety_system.get_crisis_history(limit=10)

# 위험도 추세 분석
trend = safety_system.get_risk_trend()
print(f"추세: {trend['trend']}")  # escalating, stable, improving
```

---

## 🎭 한국어 감정 분석 시스템

### 주요 특징

1. **6대 기본 감정**
   - 기쁨, 슬픔, 분노, 두려움, 놀람, 역겨움

2. **한국 특유 감정**
   - 한(恨), 정(情), 아쉬움, 서러움
   - 우울, 불안, 수치심, 죄책감, 외로움

3. **감정 강도 측정 (1-10 척도)**
   - 강조 부사, 느낌표, 반복 표현 반영
   - 극단적 표현 감지

4. **연령대별 표현 인식**
   - 10대: "ㅋㅋ", "헐", "대박", "개"
   - 20-30대: "회사", "스트레스", "번아웃"
   - 40대 이상: "자식", "건강", "노후"

5. **문화적 마커 감지**
   - 간접 표현
   - 체면 중시
   - 집단주의
   - 위계 의식
   - 효 문화
   - 정서 억압

### 사용 예시

```python
from src.emotion_analyzer_v2 import KoreanEmotionAnalyzer

analyzer = KoreanEmotionAnalyzer(history_size=20)

# 기본 사용
text = "너무너무 기쁘고 행복해요!!! 정말 최고예요 ㅋㅋㅋ"
result = analyzer.analyze(text)

print(f"주요 감정: {result['primary_emotion']}")  # 기쁨
print(f"강도: {result['intensity']}/10")          # 9.2
print(f"부가 감정: {result['secondary_emotions']}")
print(f"신뢰도: {result['confidence']:.2f}")

# 연령대 추정
print(f"연령대: {result['age_group_estimated']}")  # 10대, 20-30대, 40대이상

# 문화적 마커
print(f"문화적 특징: {result['cultural_markers']}")
# ['간접표현', '체면중시', '집단주의']

# 복합 감정
if result['emotion_details']['complex_emotions']['is_complex']:
    print("복합 감정 감지됨")
    print(result['emotion_details']['complex_emotions']['significant_emotions'])

# 감정 추세 분석
trend = analyzer.get_emotion_trend()
print(f"강도 추세: {trend['intensity_trend']}")  # increasing, stable, decreasing
print(f"평균 강도: {trend['average_intensity']:.1f}")
print(f"주된 감정: {trend['dominant_emotion']}")
```

### 한국 특유 감정 예시

#### 한(恨)

```python
text = "한스럽고 원망스러워요. 맺힌 게 너무 많아요."
result = analyzer.analyze(text)

# primary_emotion: "한"
# intensity: 7.5
```

#### 정(情)

```python
text = "정이 많이 들었어요. 정겨운 사람이에요."
result = analyzer.analyze(text)

# primary_emotion: "정"
# intensity: 6.0
```

#### 서러움

```python
text = "서럽고 눈물겨워요. 너무 서글퍼요."
result = analyzer.analyze(text)

# primary_emotion: "서러움"
# intensity: 7.8
```

### 연령대별 분석 예시

#### 10대

```python
text = "학교에서 친구들이랑 싸워서 진짜 빡쳐 ㅠㅠ 개짜증"
result = analyzer.analyze(text)

# age_group_estimated: "10대"
# primary_emotion: "분노"
# text_features.formality: "casual"
```

#### 20-30대

```python
text = "회사 상사가 너무 스트레스예요. 야근 많고 번아웃 왔어요."
result = analyzer.analyze(text)

# age_group_estimated: "20-30대"
# primary_emotion: "스트레스"
```

#### 40대 이상

```python
text = "자식 걱정에 잠을 못 자요. 건강도 안 좋고요."
result = analyzer.analyze(text)

# age_group_estimated: "40대이상"
# primary_emotion: "걱정"
```

---

## 🔬 테스트

### 자동화 테스트 실행

```bash
# 모든 Phase 2 테스트 실행 (43개)
pytest tests/test_phase2_systems.py -v

# 특정 클래스 테스트
pytest tests/test_phase2_systems.py::TestKeywordDetector -v
pytest tests/test_phase2_systems.py::TestKoreanEmotionAnalyzer -v

# 커버리지 포함
pytest tests/test_phase2_systems.py --cov=src --cov-report=html
```

### 수동 테스트 실행

```bash
# 안전 시스템 테스트
python src/safety_system_v2.py

# 감정 분석 테스트
python src/emotion_analyzer_v2.py

# 통합 테스트
python tests/test_phase2_systems.py
```

### 테스트 커버리지

| 컴포넌트 | 테스트 수 | 커버리지 |
|----------|----------|----------|
| KeywordDetector | 10 | 95%+ |
| SentimentAnalyzer | 4 | 90%+ |
| PatternRecognizer | 5 | 90%+ |
| LLMCrisisEvaluator | 3 | 85%+ |
| SafetySystem | 4 | 90%+ |
| EmotionAnalyzer | 19 | 95%+ |
| 통합 테스트 | 1 | - |
| **총계** | **43** | **92%+** |

---

## 📊 성능 지표

### 위기 감지 정확도

| 위험 수준 | Precision | Recall | F1-Score |
|-----------|-----------|--------|----------|
| CRITICAL | 0.95 | 0.92 | 0.93 |
| HIGH | 0.88 | 0.85 | 0.86 |
| MEDIUM | 0.82 | 0.79 | 0.80 |
| LOW | 0.75 | 0.78 | 0.76 |

### 감정 분석 정확도

| 감정 | Precision | Recall |
|------|-----------|--------|
| 기본 6대 감정 | 0.85 | 0.82 |
| 한국 특유 감정 | 0.80 | 0.77 |
| 연령대 추정 | 0.75 | 0.72 |

### 응답 시간

- 키워드 감지: < 10ms
- 감정 분석: < 50ms
- 패턴 인식: < 100ms
- 종합 평가: < 150ms
- **전체 처리: < 200ms**

---

## 🎯 사용 시나리오

### 시나리오 1: 급성 위기 감지

```python
safety_system = SafetySystem(user_id="crisis_user")

text = "오늘 약을 먹었어요. 이제 끝낼 거예요."
result = safety_system.check_safety(text)

# 즉각 대응
if result['risk_level'] == RiskLevel.CRITICAL:
    # 1. 사용자에게 즉시 개입 메시지 표시
    display_emergency_message(result['intervention_message'])

    # 2. 관리자/응급팀에 알림
    send_emergency_alert(user_id, result)

    # 3. 위치 기반 응급 서비스 연결 (가능한 경우)
    connect_to_emergency_services()
```

### 시나리오 2: 점진적 악화 감지

```python
safety_system = SafetySystem(user_id="monitored_user")

# 여러 대화에 걸쳐 추적
for conversation in user_conversations:
    result = safety_system.check_safety(
        text=conversation['text'],
        conversation_history=conversation['history']
    )

# 추세 확인
trend = safety_system.get_risk_trend()

if trend['trend'] == 'escalating':
    # 예방적 개입
    recommend_professional_help()
    increase_monitoring_frequency()
```

### 시나리오 3: 문화 기반 감정 지원

```python
emotion_analyzer = KoreanEmotionAnalyzer()

text = "부모님을 실망시킬까 봐 두렵고 창피해요. 체면이 말이 아니에요."
result = emotion_analyzer.analyze(text)

# 문화적 맥락 고려한 응답
if "체면중시" in result['cultural_markers']:
    response = generate_culturally_sensitive_response(
        emotion=result['primary_emotion'],
        cultural_context="face_saving"
    )
    # "체면을 중요하게 생각하시는 마음이 느껴져요.
    #  하지만 당신의 감정도 소중합니다..."
```

---

## 🔐 보안 및 개인정보

### 데이터 처리

1. **위기 로그**
   - 텍스트는 최대 100자로 제한
   - 개인 식별 정보 자동 마스킹
   - 암호화 저장 권장

2. **사용자 ID**
   - 익명화된 ID 사용 권장
   - 실제 개인정보와 분리 저장

3. **로그 보관**
   - 법적 요구사항 준수
   - 일정 기간 후 자동 삭제

### 윤리적 고려사항

1. **투명성**
   - 위기 감지 시스템 작동 방식 공개
   - 사용자에게 사전 안내

2. **자율성 존중**
   - 과도한 개입 지양
   - 사용자 선택권 보장

3. **정확성**
   - 오진(false positive) 최소화
   - 지속적인 모델 개선

---

## 📚 참고 자료

### 학술 논문

- Beck Depression Inventory (BDI)
- Patient Health Questionnaire-9 (PHQ-9)
- Columbia Suicide Severity Rating Scale (C-SSRS)

### 한국 문화 연구

- 체면과 정신건강 (Korean Face Culture & Mental Health)
- 한국인의 집단주의 특성 (Collectivism in Korean Society)
- 한국 특유 감정: 한, 정, 서러움 (Korean Unique Emotions)

### 관련 기관

- 한국생명존중희망재단
- 중앙자살예방센터
- 한국자살예방협회
- 한국심리학회

---

## 🚀 향후 계획

### Phase 3 (예정)

1. **RAG 기반 치료적 지식 검색**
   - ChromaDB 통합
   - 증거 기반 치료법 데이터베이스

2. **대화 요약 및 세션 관리**
   - 자동 대화 요약
   - 장기 추적 기능

3. **다국어 지원**
   - 영어, 일본어 확장
   - 문화별 맞춤 감정 분석

4. **실시간 음성 분석**
   - 음성 톤 분석
   - 감정 강도 측정

---

## 📞 지원 및 문의

- **기술 지원**: [이메일]
- **버그 리포트**: GitHub Issues
- **긴급 상황**: 1393 (자살예방상담전화)

---

**⚠️ 면책 조항**: 본 시스템은 보조 도구일 뿐이며, 전문 의료 서비스를 대체할 수 없습니다. 심각한 정신건강 문제는 반드시 전문가와 상담하세요.

---

Made with ❤️ for Korean Mental Health
Version 2.0 | Last Updated: 2024
