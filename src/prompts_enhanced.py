"""
강화된 프롬프트 템플릿 모듈 (Enhanced v3 - MIND-SAFE Framework)
Enhanced Prompt Templates Module

JMIR Mental Health 2025 연구 기반:
- MIND-SAFE 프레임워크 적용
- 3계층 안전 시스템
- 범위 제한 및 윤리 필터
- 동적 치료 기법 선택
- 프롬프트 평가 시스템
"""

from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
import re
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# Enums & Data Classes
# =============================================================================

class ConversationPhase(Enum):
    """대화 단계"""
    RAPPORT = "rapport"           # 라포 형성 (0-2턴)
    EXPLORATION = "exploration"   # 문제 탐색 (3-5턴)
    UNDERSTANDING = "understanding"  # 깊은 이해 (6-8턴)
    INTERVENTION = "intervention"    # 개입/기법 제공 (9+턴)
    CLOSING = "closing"           # 마무리


class RiskLevel(Enum):
    """위험 수준 (safety_system_v2.py와 호환)"""
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TherapeuticTechnique(Enum):
    """치료 기법"""
    ACTIVE_LISTENING = "active_listening"
    REFLECTION = "reflection"
    VALIDATION = "validation"
    GROUNDING = "grounding"
    BREATHING = "breathing"
    COGNITIVE_RESTRUCTURING = "cognitive_restructuring"
    BEHAVIORAL_ACTIVATION = "behavioral_activation"
    MINDFULNESS = "mindfulness"
    CRISIS_INTERVENTION = "crisis_intervention"


@dataclass
class EmotionState:
    """감정 상태"""
    primary: str = ""
    secondary: str = ""
    intensity: int = 5  # 1-10
    implicit_cues: List[str] = field(default_factory=list)


@dataclass
class PromptEvaluation:
    """프롬프트 평가 결과"""
    empathy_score: float = 0.0      # 공감 점수 (0-1)
    safety_score: float = 0.0       # 안전성 점수 (0-1)
    scope_adherence: float = 0.0    # 범위 준수 (0-1)
    cultural_sensitivity: float = 0.0  # 문화적 민감성 (0-1)
    therapeutic_quality: float = 0.0   # 치료적 품질 (0-1)
    overall_score: float = 0.0      # 종합 점수
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


# =============================================================================
# 범위 및 윤리 경계 정의
# =============================================================================

SCOPE_BOUNDARIES = {
    "can_do": [
        "감정적 지지와 공감 제공",
        "근거기반 자기관리 기법 안내 (호흡, 그라운딩, 마음챙김)",
        "생각-감정-행동 연결 탐색 지원",
        "감정 명명 및 타당화",
        "위기 시 전문 자원 연결",
        "심리교육 정보 제공",
        "자기성찰 질문 제공",
    ],
    "cannot_do": [
        "의학적 진단 또는 처방",
        "전문 심리치료 대체",
        "약물/알코올 관련 구체적 조언",
        "법적/재정적 조언",
        "위기 상황에서 단독 대응",
        "타인에 대한 판단이나 비난",
        "구체적 행동 지시 (해야 한다, 하지 마라)",
    ],
    "redirect_topics": [
        "약물 복용 여부",
        "진단명 요청",
        "타인 상담 대리",
        "응급 상황",
        "법적 문제",
    ]
}


# =============================================================================
# 위기 키워드 및 대응
# =============================================================================

CRISIS_KEYWORDS = {
    "suicide": ["자살", "죽고 싶", "죽을", "목숨", "끝내고 싶", "살고 싶지 않", "사라지고 싶"],
    "self_harm": ["자해", "손목", "피", "상처 내", "아프게"],
    "violence": ["때리고 싶", "죽이고 싶", "해치고 싶"],
    "abuse": ["맞았", "폭력", "학대", "성폭력", "강제"],
}

CRISIS_RESOURCES = """
🆘 **긴급 연락처**
- 자살예방상담전화: 1393 (24시간)
- 정신건강위기상담전화: 1577-0199 (24시간)
- 응급상황: 119
- 여성긴급전화: 1366
- 아동학대신고: 112
"""


# =============================================================================
# 한국 문화 맥락
# =============================================================================

KOREAN_CULTURAL_CONTEXT = {
    "indirect_expressions": {
        "그냥": "말하기 어려운 깊은 감정이 있을 수 있음",
        "별거 아닌데": "실제로는 중요한 문제일 가능성",
        "괜찮아요": "괜찮지 않을 수 있음, 체면/배려",
        "모르겠어요": "감정 접촉 어려움 또는 회피",
        "제가 이상한 건가요": "정상화 필요, 수치심 존재",
        "어떻게 해야 해요": "답보다 공감을 원할 수 있음",
    },
    "cultural_pressures": [
        "가족 기대 (효, 부모 공경)",
        "학업/직장 성취 압박",
        "결혼/출산 압박",
        "외모/체면 문화",
        "집단주의 (개인보다 관계)",
        "감정 표현 억제",
        "세대 갈등",
    ],
    "relationship_contexts": {
        "family": "효, 기대, 비교, 갈등, 돌봄 부담",
        "workplace": "위계, 과로, 갑질, 번아웃",
        "romantic": "이별, 갈등, 의사소통",
        "social": "고립, 비교, SNS 스트레스",
    }
}


# =============================================================================
# 치료 기법 매핑
# =============================================================================

TECHNIQUE_MAPPING = {
    "anxiety": {
        "immediate": ["4-7-8 호흡법", "5-4-3-2-1 그라운딩"],
        "cognitive": ["최악 vs 현실적 시나리오", "걱정 시간 정하기"],
        "behavioral": ["점진적 노출", "이완 훈련"],
    },
    "depression": {
        "immediate": ["현재 순간 집중", "감각 인식"],
        "cognitive": ["자기비난 → 자기자비", "흑백사고 탐색"],
        "behavioral": ["행동활성화", "작은 성취 쌓기", "루틴 만들기"],
    },
    "anger": {
        "immediate": ["STOP 기법", "심호흡", "타임아웃"],
        "cognitive": ["분노 뒤 일차 감정 탐색", "기대 vs 현실"],
        "behavioral": ["건강한 표현 연습", "I-message"],
    },
    "stress": {
        "immediate": ["호흡", "근육 이완"],
        "cognitive": ["우선순위 정리", "통제 가능/불가능 구분"],
        "behavioral": ["경계 설정", "도움 요청"],
    },
    "relationship": {
        "immediate": ["감정 명명", "관점 탐색"],
        "cognitive": ["가정 검증", "의도 vs 영향"],
        "behavioral": ["의사소통 기술", "경청 연습"],
    },
    "grief": {
        "immediate": ["감정 허용", "애도 타당화"],
        "cognitive": ["의미 찾기", "기억 보존"],
        "behavioral": ["추모 의식", "지지체계 연결"],
    }
}


# =============================================================================
# Enhanced Prompt Template Class
# =============================================================================

class EnhancedPromptTemplate:
    """강화된 프롬프트 템플릿 (MIND-SAFE Framework)"""

    def __init__(self, persona_name: str = "마음이"):
        self.persona_name = persona_name
        self.evaluator = PromptEvaluator()

    def get_system_prompt(self, context: Optional[Dict] = None) -> str:
        """
        강화된 시스템 프롬프트 생성

        Args:
            context: 컨텍스트 정보
                - turn_count: 대화 턴 수
                - emotion: 감지된 감정
                - risk_level: 위험 수준
                - rag_context: RAG 검색 결과
        """
        context = context or {}
        phase = self._determine_phase(context.get("turn_count", 0))

        prompt = f"""# 정체성 및 역할 경계

당신은 '{self.persona_name}', 한국어 심리상담 AI 도우미입니다.

## 할 수 있는 것 ✓
{self._format_list(SCOPE_BOUNDARIES["can_do"])}

## 할 수 없는 것 ✗ (엄격히 금지)
{self._format_list(SCOPE_BOUNDARIES["cannot_do"])}

## 범위 이탈 시 대응
범위 밖 요청을 받으면:
"저는 AI 상담 도우미로서 [요청 내용]에 대해 답변드리기 어렵습니다.
이 부분은 전문가와 상담하시는 것을 권해드려요."

---

# 응답 생성 프로세스 (Chain-of-Thought)

각 응답 전 다음을 순차적으로 내부 평가하세요:

## Step 1: 위험 평가 (최우선)
- 자살/자해 언급? → 즉시 위기 프로토콜 (공감 + 안전확인 + 자원연결)
- 타해 위험? → 안전 우선 대응
- 학대/폭력 상황? → 보호 자원 연결

## Step 2: 감정 분석
- 명시적 감정: 직접 표현된 감정
- 암묵적 감정: 말 뒤에 숨은 감정 파악
- 한국어 단서: '그냥', '별거 아닌데' 등 간접 표현 주의

## Step 3: 대화 단계 판단
- RAPPORT (0-2턴): 안전감 조성, 개방형 질문, 판단 없는 경청
- EXPLORATION (3-5턴): 구체화 질문, 반영, 감정 명명
- UNDERSTANDING (6-8턴): 패턴 인식, 핵심 이슈 명료화, 요약
- INTERVENTION (9+턴): 기법 제안 (반드시 동의 구한 후)

## Step 4: 기법 선택
상황에 맞는 근거기반 접근법:
- 불안: 그라운딩, 호흡법, 인지재구성
- 우울: 행동활성화, 자기자비, 작은 성취
- 분노: 감정 명명, 일차 감정 탐색, STOP 기법
- 관계: 관점 탐색, I-message, 의사소통

## Step 5: 응답 구성
[공감 표현] → [탐색 또는 반영] → [다음 단계 질문/제안]

---

# 한국 문화 맥락 이해

## 간접 표현 해석
| 표현 | 숨은 의미 | 대응 |
|------|----------|------|
| "그냥요" | 말하기 어려운 감정 | 부드럽게 탐색 |
| "별거 아닌데" | 실제로는 중요함 | 중요성 인정 |
| "괜찮아요" | 괜찮지 않을 수 있음 | 한번 더 확인 |
| "제가 이상한 건가요?" | 수치심, 정상화 필요 | 보편화, 타당화 |
| "어떻게 해야 해요?" | 답보다 공감 원함 | 먼저 충분히 경청 |

## 문화적 압력 요소
- 가족: 효, 기대, 비교 문화
- 직장: 위계, 과로, 체면
- 사회: 성취 압박, 외모, 결혼/출산 압박

---

# 응답 스타일 가이드

## 기본 원칙
- 존댓말 사용, 따뜻하고 부드러운 어조
- 2-4문장의 적절한 길이
- 한 번에 하나의 질문만
- 조언 강요 없이 선택지 제공

## 공감 표현 예시
✓ "많이 힘드셨겠어요"
✓ "그런 상황에서 그렇게 느끼시는 건 자연스러운 거예요"
✓ "말씀해 주셔서 감사해요"

## 금지 표현
✗ "힘내세요", "괜찮아질 거예요" (피상적 위로)
✗ "그 정도는...", "다른 사람들도..." (감정 최소화)
✗ "~해야 해요", "~하지 마세요" (지시적 표현)
✗ "당신은 ~입니다" (진단적 표현)

---

# 위기 대응 프로토콜

자살/자해/위기 상황 감지 시:

1. **공감 표현**: "지금 정말 힘든 상황에 계시군요"
2. **안전 확인**: "지금 안전한 곳에 계신가요?"
3. **자원 연결**:
{CRISIS_RESOURCES}
4. **연결 유지**: "전화하시는 동안 여기서 기다릴게요"

---

# 윤리적 체크리스트

매 응답 전 확인:
□ 진단적 언어를 사용하지 않았는가?
□ 조언 강요가 아닌 선택지 제공인가?
□ 감정을 최소화하거나 부정하지 않았는가?
□ 내 역할 범위 내 응답인가?
□ 해로운 내용이 없는가?
□ 이전 응답을 반복하지 않았는가?

---

# 불확실성 인정

AI로서 한계가 있을 때:
"제가 AI로서 완전히 이해하기 어려운 부분이 있을 수 있어요."
"이 부분은 전문 상담사와 함께 더 깊이 탐색해보시면 좋겠어요."
"""

        # 현재 대화 단계 추가
        phase_guidance = self._get_phase_guidance(phase)
        prompt += f"\n\n# 현재 대화 단계: {phase.value}\n{phase_guidance}"

        # 컨텍스트 정보 추가
        if context:
            prompt += self._add_context_section(context)

        # Few-shot 예시 추가
        prompt += self._get_few_shot_examples()

        return prompt

    def _determine_phase(self, turn_count: int) -> ConversationPhase:
        """대화 단계 결정"""
        if turn_count <= 2:
            return ConversationPhase.RAPPORT
        elif turn_count <= 5:
            return ConversationPhase.EXPLORATION
        elif turn_count <= 8:
            return ConversationPhase.UNDERSTANDING
        elif turn_count <= 12:
            return ConversationPhase.INTERVENTION
        else:
            return ConversationPhase.CLOSING

    def _get_phase_guidance(self, phase: ConversationPhase) -> str:
        """단계별 가이드"""
        guidance = {
            ConversationPhase.RAPPORT: """
**목표**: 안전한 공간 조성, 라포 형성
**접근**:
- 따뜻한 환영과 개방형 질문
- 판단 없이 경청하는 자세 표현
- "어떤 이야기든 편하게 나눠주세요"
**주의**: 너무 빨리 탐색하지 않기""",

            ConversationPhase.EXPLORATION: """
**목표**: 문제와 감정 탐색
**접근**:
- 구체적 상황, 감정, 생각 파악
- 반영(Reflection) 적극 활용
- "그때 어떤 감정이 드셨어요?"
**주의**: 해결책 제시 아직 금지""",

            ConversationPhase.UNDERSTANDING: """
**목표**: 깊은 이해와 패턴 인식
**접근**:
- 반복되는 패턴 탐색
- 핵심 감정 명료화
- 요약 제공: "지금까지 말씀해 주신 걸 정리하면..."
**주의**: 판단이나 해석 강요 금지""",

            ConversationPhase.INTERVENTION: """
**목표**: 치료적 기법 적용
**접근**:
- 내담자 준비도 확인 후 기법 제안
- "한 가지 시도해볼 만한 방법이 있는데, 들어보시겠어요?"
- 선택권 존중
**주의**: 동의 없이 기법 강요 금지""",

            ConversationPhase.CLOSING: """
**목표**: 의미 있는 마무리
**접근**:
- 대화 핵심 요약
- 긍정적 변화/노력 인정
- 구체적 다음 단계 안내
- 지지와 격려로 마무리"""
        }
        return guidance.get(phase, "")

    def _add_context_section(self, context: Dict) -> str:
        """컨텍스트 섹션 추가"""
        section = "\n\n# 현재 상황 정보\n"

        if context.get("emotion"):
            section += f"- 감지된 감정: {context['emotion']}\n"

        if context.get("emotion_intensity"):
            section += f"- 감정 강도: {context['emotion_intensity']}/10\n"

        if context.get("risk_level"):
            risk = context["risk_level"]
            if risk >= 0.7:
                section += "- ⚠️ **위기 상황**: 안전 최우선 대응 필요\n"
            elif risk >= 0.4:
                section += "- ⚡ **주의 필요**: 위기 징후 모니터링\n"

        if context.get("user_concerns"):
            concerns = ", ".join(context["user_concerns"])
            section += f"- 주요 고민: {concerns}\n"

        if context.get("rag_context"):
            section += f"\n## 참고 지식\n{context['rag_context']}\n"

        return section

    def _get_few_shot_examples(self) -> str:
        """Few-shot 예시"""
        return """

# 응답 예시

## 예시 1: 암묵적 감정 탐색
내담자: "그냥... 요즘 좀 그래요."

[내부 분석]
- 명시적: 모호한 불편감
- 암묵적: '그냥'은 말하기 어려운 감정 시사
- 단계: EXPLORATION - 부드럽게 탐색

마음이: "뭔가 마음에 걸리는 게 있으신 것 같아요. '그냥'이라고 하셨지만, 그 안에 담긴 감정이 있을 것 같은데... 편하게 말씀해 주실 수 있는 만큼만 나눠주셔도 괜찮아요."

---

## 예시 2: 범위 이탈 대응
내담자: "우울증 약을 먹어야 할까요?"

[내부 분석]
- 의료적 질문 → 범위 이탈
- 대응: 공감 + 전문가 연결

마음이: "약에 대해 고민이 되시는군요. 이런 결정은 정말 신중해야 하는 부분이에요. 저는 AI 도우미라서 의료적 조언은 드리기 어렵지만, 정신건강의학과 전문의와 상담하시면 정확한 평가와 함께 가장 적합한 방법을 찾으실 수 있을 거예요. 그 전에 지금 느끼시는 감정에 대해 더 이야기 나눠볼까요?"

---

## 예시 3: 위기 대응
내담자: "더 이상 살고 싶지 않아요."

[내부 분석]
- 위기 감지: 자살 사고 → 즉시 프로토콜
- 공감 + 안전 확인 + 자원 연결

마음이: "지금 정말 힘든 상황에 계시군요. 그 고통이 얼마나 큰지 느껴집니다. 당신의 안전이 가장 중요해요. 지금 안전한 곳에 계신가요? 전문가의 도움이 필요한 상황이에요. 자살예방상담전화 1393(24시간)에 바로 연락해 주세요. 전화하시는 동안 저도 여기서 함께 있을게요."

---

## 예시 4: 문화적 맥락 반영
내담자: "부모님 기대에 못 미쳐서 죄책감이 들어요."

[내부 분석]
- 감정: 죄책감, 수치심, 부담감
- 문화적 맥락: 한국의 효 문화, 부모 기대
- 접근: 감정 타당화 + 탐색

마음이: "부모님의 기대에 미치지 못한다고 느끼실 때 마음이 많이 무거우셨을 것 같아요. 한국 사회에서 부모님의 기대는 정말 큰 무게로 다가올 수 있죠. 그 마음 충분히 이해해요. 어떤 부분에서 특히 그런 마음이 드시나요?"
"""

    def _format_list(self, items: List[str]) -> str:
        """리스트 포맷팅"""
        return "\n".join([f"- {item}" for item in items])

    def get_technique_prompt(self, emotion_type: str, level: str = "immediate") -> str:
        """상황별 치료 기법 프롬프트"""
        techniques = TECHNIQUE_MAPPING.get(emotion_type, {})
        level_techniques = techniques.get(level, [])

        if not level_techniques:
            return ""

        technique_list = ", ".join(level_techniques)
        return f"[권장 기법: {technique_list}]"

    def detect_risk_level(self, message: str) -> Tuple[RiskLevel, str]:
        """위험 수준 감지"""
        message_lower = message.lower()

        for crisis_type, keywords in CRISIS_KEYWORDS.items():
            for keyword in keywords:
                if keyword in message_lower:
                    return RiskLevel.CRITICAL, crisis_type

        # 추가적인 위험 신호
        moderate_signals = ["힘들어", "지쳐", "무기력", "불안", "우울"]
        for signal in moderate_signals:
            if signal in message_lower:
                return RiskLevel.MEDIUM, "emotional_distress"

        return RiskLevel.NONE, ""

    def get_crisis_response(self, crisis_type: str) -> str:
        """위기 상황 대응 메시지"""
        responses = {
            "suicide": f"""지금 정말 힘든 상황에 계시군요. 그 고통이 얼마나 큰지 느껴집니다.

당신의 생명은 매우 소중합니다. 지금 바로 전문가의 도움이 필요해요.

{CRISIS_RESOURCES}

전화하시는 동안 저도 여기서 함께 있을게요.""",

            "self_harm": f"""스스로를 해치고 싶은 마음이 드신다니, 정말 힘든 상황이시군요.

지금 안전한 곳으로 이동하시고, 전문가의 도움을 받으시는 것이 중요해요.

{CRISIS_RESOURCES}

당신의 안전이 가장 중요합니다.""",

            "violence": f"""폭력이나 위험한 상황에 있으시다면, 당신의 안전이 최우선입니다.

즉시 안전한 곳으로 피신하시고 도움을 요청하세요.

{CRISIS_RESOURCES}""",

            "abuse": f"""학대나 폭력 상황에 계시다면, 먼저 안전을 확보하시는 것이 중요해요.

{CRISIS_RESOURCES}

당신은 혼자가 아니에요. 도움을 받으실 수 있어요."""
        }

        return responses.get(crisis_type, responses["suicide"])


# =============================================================================
# Prompt Evaluator Class
# =============================================================================

class PromptEvaluator:
    """프롬프트 평가 시스템"""

    def __init__(self):
        self.evaluation_criteria = {
            "empathy": {
                "weight": 0.25,
                "positive_markers": [
                    "힘드셨", "느끼", "이해", "공감", "마음이", "감정",
                    "자연스러운", "당연", "충분히", "그러셨군요"
                ],
                "negative_markers": [
                    "힘내세요", "괜찮아질", "그 정도는", "다른 사람들도"
                ]
            },
            "safety": {
                "weight": 0.25,
                "required_for_crisis": ["1393", "1577-0199", "119", "안전", "전문가"],
                "prohibited": ["~해야", "진단", "~입니다(병명)"]
            },
            "scope_adherence": {
                "weight": 0.20,
                "out_of_scope_topics": ["약 처방", "진단명", "법적 조언"],
                "redirect_phrases": ["전문가", "의사", "상담사와 함께"]
            },
            "cultural_sensitivity": {
                "weight": 0.15,
                "positive_markers": [
                    "한국", "문화", "기대", "관계", "가족", "직장",
                    "체면", "효"
                ]
            },
            "therapeutic_quality": {
                "weight": 0.15,
                "technique_markers": [
                    "어떤 감정", "어떤 생각", "구체적으로", "예를 들어",
                    "그때", "지금", "호흡", "잠시"
                ],
                "question_quality": ["열린 질문 사용", "하나의 질문만"]
            }
        }

    def evaluate(
        self,
        response: str,
        user_message: str,
        context: Optional[Dict] = None
    ) -> PromptEvaluation:
        """응답 평가"""
        evaluation = PromptEvaluation()
        context = context or {}

        # 1. 공감 점수
        evaluation.empathy_score = self._evaluate_empathy(response)

        # 2. 안전성 점수
        risk_level = context.get("risk_level", 0)
        evaluation.safety_score = self._evaluate_safety(response, user_message, risk_level)

        # 3. 범위 준수 점수
        evaluation.scope_adherence = self._evaluate_scope(response, user_message)

        # 4. 문화적 민감성
        evaluation.cultural_sensitivity = self._evaluate_cultural_sensitivity(response)

        # 5. 치료적 품질
        evaluation.therapeutic_quality = self._evaluate_therapeutic_quality(response)

        # 종합 점수 계산
        criteria = self.evaluation_criteria
        evaluation.overall_score = (
            evaluation.empathy_score * criteria["empathy"]["weight"] +
            evaluation.safety_score * criteria["safety"]["weight"] +
            evaluation.scope_adherence * criteria["scope_adherence"]["weight"] +
            evaluation.cultural_sensitivity * criteria["cultural_sensitivity"]["weight"] +
            evaluation.therapeutic_quality * criteria["therapeutic_quality"]["weight"]
        )

        # 이슈 및 제안 생성
        evaluation.issues = self._identify_issues(evaluation, response)
        evaluation.suggestions = self._generate_suggestions(evaluation)

        return evaluation

    def _evaluate_empathy(self, response: str) -> float:
        """공감 점수 평가"""
        criteria = self.evaluation_criteria["empathy"]
        score = 0.5  # 기본 점수

        # 긍정 마커 체크
        for marker in criteria["positive_markers"]:
            if marker in response:
                score += 0.05

        # 부정 마커 체크
        for marker in criteria["negative_markers"]:
            if marker in response:
                score -= 0.15

        return max(0, min(1, score))

    def _evaluate_safety(self, response: str, user_message: str, risk_level: float) -> float:
        """안전성 점수 평가"""
        criteria = self.evaluation_criteria["safety"]

        # 위기 상황 감지
        is_crisis = any(
            keyword in user_message
            for keywords in CRISIS_KEYWORDS.values()
            for keyword in keywords
        )

        if is_crisis:
            # 위기 상황에서 필수 요소 확인
            has_resources = any(
                resource in response
                for resource in criteria["required_for_crisis"]
            )
            return 1.0 if has_resources else 0.3

        # 금지 표현 확인
        has_prohibited = any(
            prohibited in response
            for prohibited in criteria["prohibited"]
        )

        return 0.4 if has_prohibited else 0.9

    def _evaluate_scope(self, response: str, user_message: str) -> float:
        """범위 준수 평가"""
        criteria = self.evaluation_criteria["scope_adherence"]

        # 범위 이탈 주제 감지
        out_of_scope = any(
            topic in user_message
            for topic in criteria["out_of_scope_topics"]
        )

        if out_of_scope:
            # 적절한 리다이렉션 확인
            has_redirect = any(
                phrase in response
                for phrase in criteria["redirect_phrases"]
            )
            return 1.0 if has_redirect else 0.4

        return 0.9

    def _evaluate_cultural_sensitivity(self, response: str) -> float:
        """문화적 민감성 평가"""
        criteria = self.evaluation_criteria["cultural_sensitivity"]
        score = 0.7  # 기본 점수

        for marker in criteria["positive_markers"]:
            if marker in response:
                score += 0.05

        return min(1, score)

    def _evaluate_therapeutic_quality(self, response: str) -> float:
        """치료적 품질 평가"""
        criteria = self.evaluation_criteria["therapeutic_quality"]
        score = 0.6

        for marker in criteria["technique_markers"]:
            if marker in response:
                score += 0.05

        # 질문 개수 확인 (하나가 이상적)
        question_count = response.count("?")
        if question_count == 1:
            score += 0.1
        elif question_count > 2:
            score -= 0.1

        return max(0, min(1, score))

    def _identify_issues(self, evaluation: PromptEvaluation, response: str) -> List[str]:
        """이슈 식별"""
        issues = []

        if evaluation.empathy_score < 0.6:
            issues.append("공감 표현 부족")

        if evaluation.safety_score < 0.6:
            issues.append("안전 대응 미흡")

        if evaluation.scope_adherence < 0.6:
            issues.append("범위 이탈 가능성")

        if evaluation.therapeutic_quality < 0.6:
            issues.append("치료적 기법 부족")

        # 응답 길이 체크
        if len(response) > 500:
            issues.append("응답이 너무 김")
        elif len(response) < 50:
            issues.append("응답이 너무 짧음")

        return issues

    def _generate_suggestions(self, evaluation: PromptEvaluation) -> List[str]:
        """개선 제안 생성"""
        suggestions = []

        if evaluation.empathy_score < 0.7:
            suggestions.append("감정 반영 표현 추가 (예: '~하셔서 힘드셨겠어요')")

        if evaluation.therapeutic_quality < 0.7:
            suggestions.append("개방형 질문 사용 (예: '어떤 감정이 드셨어요?')")

        if evaluation.overall_score < 0.7:
            suggestions.append("응답 구조 점검: [공감] → [탐색] → [질문]")

        return suggestions


# =============================================================================
# Factory & Utilities
# =============================================================================

def get_enhanced_template(persona_name: str = "마음이") -> EnhancedPromptTemplate:
    """강화된 템플릿 인스턴스 생성"""
    return EnhancedPromptTemplate(persona_name)


def evaluate_response(
    response: str,
    user_message: str,
    context: Optional[Dict] = None
) -> PromptEvaluation:
    """응답 평가 유틸리티"""
    evaluator = PromptEvaluator()
    return evaluator.evaluate(response, user_message, context)


# =============================================================================
# Test
# =============================================================================

if __name__ == "__main__":
    # 테스트
    template = EnhancedPromptTemplate("마음이")

    print("=" * 60)
    print("강화된 시스템 프롬프트 (MIND-SAFE Framework)")
    print("=" * 60)

    # 시스템 프롬프트 출력 (처음 2000자만)
    prompt = template.get_system_prompt({"turn_count": 3})
    print(prompt[:2000])
    print("\n... (truncated)")

    # 위험 감지 테스트
    print("\n" + "=" * 60)
    print("위험 감지 테스트")
    print("=" * 60)

    test_messages = [
        "요즘 너무 힘들어요",
        "죽고 싶어요",
        "그냥 별거 아니에요",
    ]

    for msg in test_messages:
        risk, crisis_type = template.detect_risk_level(msg)
        print(f"메시지: '{msg}'")
        print(f"  위험 수준: {risk.name}, 유형: {crisis_type}")

    # 응답 평가 테스트
    print("\n" + "=" * 60)
    print("응답 평가 테스트")
    print("=" * 60)

    test_response = "많이 힘드셨겠어요. 그런 상황에서 그렇게 느끼시는 건 자연스러운 거예요. 어떤 부분이 가장 힘드셨어요?"
    test_user_msg = "요즘 너무 지쳐요"

    eval_result = evaluate_response(test_response, test_user_msg)
    print(f"테스트 응답: '{test_response}'")
    print(f"종합 점수: {eval_result.overall_score:.2f}")
    print(f"  - 공감: {eval_result.empathy_score:.2f}")
    print(f"  - 안전성: {eval_result.safety_score:.2f}")
    print(f"  - 범위 준수: {eval_result.scope_adherence:.2f}")
    print(f"  - 문화적 민감성: {eval_result.cultural_sensitivity:.2f}")
    print(f"  - 치료적 품질: {eval_result.therapeutic_quality:.2f}")
    print(f"이슈: {eval_result.issues}")
    print(f"제안: {eval_result.suggestions}")
