"""
프롬프트 템플릿 모듈 (Compatibility Layer)
Prompt Templates Module

이 파일은 하위 호환성을 위한 래퍼입니다.
실제 구현은 prompts_enhanced.py에 있습니다.

사용 권장:
    from src.prompts_enhanced import EnhancedPromptTemplate
"""

import logging
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass

# Enhanced 모듈에서 실제 구현 import
from .prompts_enhanced import (
    EnhancedPromptTemplate,
    ConversationPhase as EnhancedConversationPhase,
    RiskLevel,
    TherapeuticTechnique,
    EmotionState,
    PromptEvaluation,
    PromptEvaluator,
    SCOPE_BOUNDARIES,
    CRISIS_KEYWORDS,
    CRISIS_RESOURCES,
    KOREAN_CULTURAL_CONTEXT,
    TRAUMA_INFORMED_GUIDELINES,
    GENERATIONAL_CONTEXT,
    MIND_BODY_CONNECTION,
    COMPLEX_EMOTIONS,
    TECHNIQUE_MAPPING,
    get_enhanced_template,
    evaluate_response
)

logger = logging.getLogger(__name__)


# 레거시 호환성을 위한 ConversationPhase (v1 값 유지)
class ConversationPhase(Enum):
    """대화 단계 (레거시 호환)"""
    OPENING = "opening"           # 초기 라포 형성 (v2의 RAPPORT와 매핑)
    EXPLORATION = "exploration"   # 문제 탐색
    UNDERSTANDING = "understanding"  # 깊은 이해
    INTERVENTION = "intervention"    # 개입/기법 제공
    CLOSING = "closing"           # 마무리


@dataclass
class FewShotExample:
    """Few-shot 예시 데이터 (레거시 호환)"""
    user_input: str
    emotion: str
    thinking: str
    response: str


class PromptTemplate:
    """
    프롬프트 템플릿 호환성 클래스

    이 클래스는 하위 호환성을 위해 유지됩니다.
    새로운 코드에서는 EnhancedPromptTemplate을 직접 사용하세요.

    Example:
        # 권장 (새로운 코드)
        from src.prompts_enhanced import EnhancedPromptTemplate
        template = EnhancedPromptTemplate("마음이")

        # 레거시 지원 (기존 코드)
        from src.prompts import PromptTemplate
        template = PromptTemplate("마음이")
    """

    def __init__(self, persona_name: str = "마음이"):
        """
        초기화

        Args:
            persona_name: AI 상담사 이름
        """
        logger.info("PromptTemplate initialized (using EnhancedPromptTemplate)")
        self.persona_name = persona_name
        self._template = EnhancedPromptTemplate(persona_name)
        self.few_shot_examples = self._load_few_shot_examples()
        self.phase_guidance = self._load_phase_guidance()

    def _load_few_shot_examples(self) -> Dict[str, List[FewShotExample]]:
        """Few-shot 예시 로드 (레거시 형식)"""
        return {
            "empathy": [
                FewShotExample(
                    user_input="요즘 너무 지쳐요. 아무것도 하기 싫어요.",
                    emotion="우울, 무기력",
                    thinking="[감정 인식] 무기력과 피로감 표현. 우울 증상 가능성. "
                            "[접근법] 감정 수용 → 상황 탐색 → 공감 표현",
                    response="많이 지치셨군요. 아무것도 하고 싶지 않을 정도로 힘이 드시는 거 같아요. "
                            "최근에 특별히 에너지를 많이 쓰게 된 일이 있으셨나요?"
                ),
                FewShotExample(
                    user_input="직장 상사가 저만 괴롭히는 것 같아요. 너무 억울해요.",
                    emotion="분노, 억울함, 고립감",
                    thinking="[감정 인식] 억울함, 불공정함, 고립감. 직장 내 갈등 상황. "
                            "[문화적 맥락] 한국 직장 문화의 위계, 체면 문제. "
                            "[접근법] 감정 인정 → 구체적 상황 탐색",
                    response="직장에서 상사분과의 관계에서 유독 본인만 어려움을 겪는다고 느끼시면 "
                            "정말 억울하고 외로우셨을 것 같아요. 어떤 상황들이 특히 힘드셨는지 "
                            "조금 더 이야기해 주실 수 있을까요?"
                ),
                FewShotExample(
                    user_input="부모님 기대에 못 미쳐서 죄책감이 들어요.",
                    emotion="죄책감, 수치심, 부담감",
                    thinking="[감정 인식] 죄책감, 자기비난, 수치심. "
                            "[문화적 맥락] 한국의 효 문화, 부모 기대에 대한 압박. "
                            "[접근법] 감정 타당화 → 기대와 현실 탐색",
                    response="부모님의 기대에 미치지 못한다고 느끼실 때 마음이 많이 무거우셨을 것 같아요. "
                            "한국 사회에서 부모님의 기대는 정말 큰 무게로 다가올 수 있죠. "
                            "어떤 부분에서 특히 그런 마음이 드시나요?"
                ),
            ],
            "crisis": [
                FewShotExample(
                    user_input="더 이상 살고 싶지 않아요.",
                    emotion="절망, 자살 사고",
                    thinking="[위기 감지] 자살 사고 표현 - 즉각 개입 필요. "
                            "[접근법] 감정 수용 → 안전 확인 → 전문 자원 연결",
                    response="지금 정말 힘든 상황에 계시군요. 그 고통이 얼마나 큰지 느껴집니다. "
                            "당신의 안전이 가장 중요합니다. 지금 혼자 계신가요? "
                            "전문가의 도움이 필요한 상황이에요. "
                            "자살예방상담전화 1393(24시간)에 바로 연락해 주세요."
                ),
            ],
            "exploration": [
                FewShotExample(
                    user_input="그냥... 뭔가 마음이 불편해요.",
                    emotion="모호한 불편감",
                    thinking="[감정 인식] 불명확한 감정 표현. 간접적 표현 패턴. "
                            "[문화적 맥락] 한국어의 '그냥' - 더 깊은 감정 숨김 가능성. "
                            "[접근법] 개방형 질문으로 탐색",
                    response="마음이 불편하시군요. '그냥'이라고 하셨지만, 뭔가 마음에 걸리는 게 "
                            "있으신 것 같아요. 지금 떠오르는 게 있으시다면 편하게 말씀해 주세요."
                ),
            ],
        }

    def _load_phase_guidance(self) -> Dict[ConversationPhase, str]:
        """대화 단계별 가이드"""
        return {
            ConversationPhase.OPENING:
                "라포 형성에 집중. 따뜻한 환영, 안전한 공간 조성, 개방형 질문 사용. "
                "판단 없이 경청하는 자세 표현.",
            ConversationPhase.EXPLORATION:
                "문제 탐색 단계. 구체적 상황, 감정, 생각 파악. "
                "반영(Reflection) 기법 사용. 열린 질문으로 확장.",
            ConversationPhase.UNDERSTANDING:
                "깊은 이해 단계. 패턴 파악, 핵심 감정 명료화, 요약 제공. "
                "내담자의 경험을 재구성하여 반영.",
            ConversationPhase.INTERVENTION:
                "개입 단계. 내담자가 준비되었을 때 치료 기법 제안. "
                "CBT 인지재구성, ACT 수용, 마음챙김 등 적절히 활용. "
                "내담자 선택권 존중.",
            ConversationPhase.CLOSING:
                "마무리 단계. 핵심 내용 요약, 긍정적 변화 인정, "
                "구체적 다음 단계 안내, 지지와 격려로 마무리."
        }

    def get_system_prompt(self, context: Optional[Dict] = None) -> str:
        """
        시스템 프롬프트 생성

        Args:
            context: 추가 컨텍스트 정보

        Returns:
            str: 시스템 프롬프트
        """
        return self._template.get_system_prompt(context)

    def get_enhanced_prompt(
        self,
        user_message: str,
        emotion_analysis: Optional[Dict] = None,
        crisis_info: Optional[Dict] = None,
        conversation_history: Optional[List[Dict]] = None,
        rag_context: Optional[str] = None
    ) -> str:
        """
        강화된 프롬프트 생성 (모든 정보 통합)

        Args:
            user_message: 사용자 메시지
            emotion_analysis: 감정 분석 결과
            crisis_info: 위기 감지 정보
            conversation_history: 대화 이력
            rag_context: RAG 검색 결과

        Returns:
            str: 통합 프롬프트
        """
        # 컨텍스트 구성
        context = {
            "turn_count": len(conversation_history) if conversation_history else 0
        }

        if emotion_analysis:
            context["emotion"] = emotion_analysis.get("primary_emotion", "")
            context["emotion_intensity"] = emotion_analysis.get("intensity", 5)

        if crisis_info:
            context["risk_level"] = crisis_info.get("risk_score", 0)

        if rag_context:
            context["rag_context"] = rag_context

        # v4 시스템 프롬프트 사용 (고급 상담 분석 포함)
        system_prompt = self._template.get_enhanced_system_prompt_v4(
            context=context,
            current_message=user_message,
            conversation_history=conversation_history
        )

        # 대화 이력 포맷팅
        history_text = ""
        if conversation_history:
            recent_history = conversation_history[-6:]
            for turn in recent_history:
                role = "내담자" if turn["role"] == "user" else self.persona_name
                history_text += f"\n{role}: {turn['content']}"

        # 현재 메시지와 응답 요청
        full_prompt = f"""{system_prompt}

## 대화 기록{history_text}

내담자: {user_message}

{self.persona_name}:"""

        return full_prompt

    def get_crisis_intervention_prompt(self, crisis_type: str) -> str:
        """위기 개입 프롬프트"""
        return self._template.get_crisis_response(crisis_type)

    def format_conversation_turn(
        self,
        user_message: str,
        emotion: Optional[str] = None,
        crisis_detected: bool = False
    ) -> str:
        """대화 턴 포맷팅"""
        formatted = f"내담자: {user_message}"

        if emotion:
            formatted += f"\n[감지된 감정: {emotion}]"

        if crisis_detected:
            formatted += "\n[⚠️ 위기 상황 감지됨]"

        return formatted

    def get_greeting_prompt(self) -> str:
        """인사 프롬프트"""
        return f"안녕하세요, {self.persona_name}입니다. 오늘은 어떤 이야기를 나누고 싶으신가요? 편안하게 말씀해주세요."

    def get_closing_prompt(self) -> str:
        """종료 프롬프트"""
        return "오늘 함께 이야기 나눠주셔서 감사합니다. 힘든 시간이지만 스스로를 잘 돌보시길 바랍니다. 언제든 다시 찾아와주세요."

    def get_reflection_question(self, topic: str = "general") -> List[str]:
        """성찰 질문 생성"""
        questions = {
            "general": [
                "그 상황에서 어떤 생각이 드셨나요?",
                "그때 느꼈던 감정을 좀 더 자세히 말씀해주실 수 있나요?",
                "그것이 당신에게 어떤 의미인가요?"
            ],
            "emotion": [
                "지금 어떤 감정이 가장 크게 느껴지시나요?",
                "그 감정은 몸의 어느 부분에서 느껴지나요?",
                "이 감정이 당신에게 무엇을 말해주고 있는 것 같나요?"
            ],
            "thought": [
                "그런 생각이 들 때, 어떤 근거가 있나요?",
                "만약 친구가 같은 상황이라면, 뭐라고 말해주고 싶으세요?",
                "다른 관점에서 볼 수 있는 방법이 있을까요?"
            ],
            "behavior": [
                "그 상황에서 실제로 어떻게 행동하셨나요?",
                "다르게 행동했다면 어떻게 했을 것 같나요?",
                "앞으로는 어떻게 하고 싶으신가요?"
            ]
        }
        return questions.get(topic, questions["general"])

    def get_coping_strategy_prompt(self, emotion_type: str) -> str:
        """대처 전략 프롬프트"""
        strategies = {
            "anxiety": """불안할 때 도움이 될 수 있는 방법들입니다:

1. **호흡 연습**: 4초 들이마시고, 4초 멈추고, 6초 내쉬어보세요
2. **그라운딩**: 지금 보이는 것 5개, 들리는 것 4개, 만질 수 있는 것 3개를 찾아보세요
3. **현재에 집중**: 과거나 미래가 아닌 지금 이 순간에 머물러보세요

어떤 방법을 시도해보시겠어요?""",

            "depression": """우울한 마음이 드실 때는:

1. **작은 활동**: 침대에서 일어나는 것만으로도 큰 성과입니다
2. **햇빛 쐬기**: 가능하다면 잠시 밖에 나가보세요
3. **규칙적 일상**: 작은 루틴이라도 유지해보세요

무리하지 마시고, 할 수 있는 만큼만 해보는 건 어떨까요?""",

            "anger": """화가 날 때 시도해볼 수 있는 방법들:

1. **멈추기**: 즉각 반응하기 전에 잠시 멈춰보세요
2. **심호흡**: 깊게 호흡하며 마음을 가라앉혀보세요
3. **감정 관찰**: 화 뒤에 숨은 다른 감정(상처, 두려움 등)을 찾아보세요

지금 시도해볼 수 있는 것이 있을까요?""",

            "stress": """스트레스가 클 때는:

1. **우선순위**: 꼭 해야 할 일과 나중에 해도 되는 일을 구분해보세요
2. **휴식**: 5분이라도 완전히 쉬는 시간을 가져보세요
3. **도움 요청**: 혼자 다 하려고 하지 마세요

어떤 것부터 시작해보시겠어요?"""
        }
        return strategies.get(emotion_type, "함께 도움이 될 만한 방법을 찾아봐요.")

    def get_validation_response(self) -> List[str]:
        """타당화 응답 생성"""
        return [
            "그런 상황에서 그렇게 느끼시는 것은 충분히 이해가 됩니다.",
            "당신의 감정은 모두 타당하고 소중합니다.",
            "그렇게 생각하신 것은 자연스러운 반응이에요.",
            "지금 느끼시는 것을 느끼셔도 괜찮아요."
        ]

    # Enhanced 기능 접근자
    def get_technique_prompt(self, emotion_type: str, level: str = "immediate") -> str:
        """치료 기법 프롬프트"""
        return self._template.get_technique_prompt(emotion_type, level)

    def detect_risk_level(self, message: str):
        """위험 수준 감지"""
        return self._template.detect_risk_level(message)

    def get_generational_context(self, age_group: str) -> str:
        """세대별 맥락"""
        return self._template.get_generational_context(age_group)

    def get_trauma_informed_response(self, indicator_type: str = "general") -> str:
        """트라우마 인식 대응"""
        return self._template.get_trauma_informed_response(indicator_type)

    def get_grounding_technique(self, technique_name: str = "5-4-3-2-1") -> str:
        """그라운딩 기법"""
        return self._template.get_grounding_technique(technique_name)


# 기본 템플릿 인스턴스
default_template = PromptTemplate()


# 하위 호환성을 위한 export
__all__ = [
    # 레거시 (호환성)
    'PromptTemplate',
    'ConversationPhase',
    'FewShotExample',
    'default_template',
    # Enhanced (권장)
    'EnhancedPromptTemplate',
    'RiskLevel',
    'TherapeuticTechnique',
    'EmotionState',
    'PromptEvaluation',
    'PromptEvaluator',
    'get_enhanced_template',
    'evaluate_response',
    # 상수
    'SCOPE_BOUNDARIES',
    'CRISIS_KEYWORDS',
    'CRISIS_RESOURCES',
    'KOREAN_CULTURAL_CONTEXT',
    'TRAUMA_INFORMED_GUIDELINES',
    'GENERATIONAL_CONTEXT',
    'MIND_BODY_CONNECTION',
    'COMPLEX_EMOTIONS',
    'TECHNIQUE_MAPPING',
]


if __name__ == "__main__":
    # 테스트
    print("=== PromptTemplate (compatibility) 테스트 ===\n")

    template = PromptTemplate("마음이")

    print("=== 인사말 ===")
    print(template.get_greeting_prompt())

    print("\n=== 시스템 프롬프트 (처음 500자) ===")
    prompt = template.get_system_prompt({"turn_count": 3})
    print(prompt[:500] + "...")

    print("\n=== 대처 전략 (불안) ===")
    print(template.get_coping_strategy_prompt("anxiety"))
