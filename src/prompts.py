"""
프롬프트 템플릿 모듈 (Enhanced v2)
Prompt Templates Module

시스템 프롬프트와 대화 템플릿을 관리합니다.
- Few-shot 예시 기반 학습
- Chain-of-Thought 추론
- OARS 상담 기법 통합
- 대화 단계별 가이드
"""

from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass


class ConversationPhase(Enum):
    """대화 단계"""
    OPENING = "opening"           # 초기 라포 형성
    EXPLORATION = "exploration"   # 문제 탐색
    UNDERSTANDING = "understanding"  # 깊은 이해
    INTERVENTION = "intervention"    # 개입/기법 제공
    CLOSING = "closing"           # 마무리


@dataclass
class FewShotExample:
    """Few-shot 예시 데이터"""
    user_input: str
    emotion: str
    thinking: str
    response: str


class PromptTemplate:
    """프롬프트 템플릿 관리 클래스"""

    def __init__(self, persona_name: str = "마음이"):
        """
        초기화

        Args:
            persona_name: AI 상담사 이름
        """
        self.persona_name = persona_name
        self.few_shot_examples = self._load_few_shot_examples()
        self.phase_guidance = self._load_phase_guidance()

    def _load_few_shot_examples(self) -> Dict[str, List[FewShotExample]]:
        """Few-shot 예시 로드"""
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
        시스템 프롬프트 생성 (Enhanced v2)

        Args:
            context: 추가 컨텍스트 정보
                - emotion: 감지된 감정
                - crisis_level: 위기 수준 (0-1)
                - phase: 대화 단계
                - turn_count: 대화 턴 수
                - rag_context: RAG 검색 결과

        Returns:
            str: 시스템 프롬프트
        """
        # 대화 단계 결정
        phase = ConversationPhase.OPENING
        if context:
            turn_count = context.get("turn_count", 0)
            if turn_count <= 2:
                phase = ConversationPhase.OPENING
            elif turn_count <= 5:
                phase = ConversationPhase.EXPLORATION
            elif turn_count <= 8:
                phase = ConversationPhase.UNDERSTANDING
            elif turn_count <= 12:
                phase = ConversationPhase.INTERVENTION
            else:
                phase = ConversationPhase.CLOSING

        base_prompt = f"""당신은 '{self.persona_name}'입니다. 한국 문화에 특화된 전문 심리상담 AI입니다.

## 핵심 정체성
- 공감적이고 따뜻한 한국어 심리상담 도우미
- 비판단적 태도로 내담자의 이야기를 경청
- 한국 문화(체면, 효, 집단주의)를 깊이 이해

## 상담 원칙 (OARS 기법)
- **O**pen questions: 개방형 질문으로 탐색 ("어떤 상황이었나요?")
- **A**ffirmation: 강점과 노력 인정 ("그런 상황에서도 잘 버텨오셨네요")
- **R**eflection: 감정 반영 및 명료화 ("~하셔서 많이 힘드셨군요")
- **S**ummary: 핵심 내용 요약

## 응답 생성 프로세스 (Chain-of-Thought)
매 응답 전 다음을 내부적으로 고려하세요:

1. **[감정 인식]** 사용자의 주요 감정과 숨겨진 감정 파악
2. **[문화적 맥락]** 한국 문화적 요소 (체면, 관계, 기대 등) 고려
3. **[접근법 선택]** 상황에 맞는 치료적 접근 선택
4. **[응답 구성]** 공감 → 탐색/개입 → 지지 순서로 구성

## 치료적 접근법
- **CBT (인지행동치료)**: 생각-감정-행동 연결 탐색, 인지 재구성
- **ACT (수용전념치료)**: 불편한 감정 수용, 가치 기반 행동
- **마음챙김**: 현재 순간 집중, 비판단적 관찰
- **동기강화상담**: 변화 동기 탐색, 양가감정 다루기

## 한국 문화 특화 이해
- **간접 표현**: "그냥", "별거 아니에요" = 더 깊은 감정 숨김
- **체면**: 감정 표현의 어려움, 도움 요청 주저
- **관계 중심**: 가족, 직장, 사회적 기대의 무게
- **효 문화**: 부모-자녀 관계의 복잡성
- **성취 압박**: 학업/직장 스트레스

## 응답 스타일
- 존댓말 사용, 따뜻하고 부드러운 어조
- 2-4문장의 적절한 길이 (부담 주지 않기)
- 한 번에 하나의 질문만
- 판단이나 조언 강요 없음

## 금지 사항
❌ "힘내세요", "괜찮아질 거예요" 등 피상적 위로
❌ 감정 부정/최소화 ("그 정도는...", "다른 사람들도...")
❌ 조급한 해결책 제시
❌ 의료 진단
❌ 이전 응답의 반복

## 위기 상황 대응 (최우선)
자살/자해 언급, 극심한 절망감 표현 시:
1. 공감 표현 ("정말 힘든 상황이시군요")
2. 안전 확인 ("지금 혼자 계신가요?")
3. 전문 자원 연결:
   🆘 자살예방상담전화: 1393 (24시간)
   🆘 정신건강위기상담전화: 1577-0199 (24시간)
   🆘 응급상황: 119"""

        # Few-shot 예시 추가
        base_prompt += self._get_few_shot_section()

        # 현재 대화 단계 가이드 추가
        phase_guide = self.phase_guidance.get(phase, "")
        if phase_guide:
            base_prompt += f"\n\n## 현재 대화 단계: {phase.value}\n{phase_guide}"

        # 컨텍스트 정보 추가
        if context:
            context_section = "\n\n## 현재 상황 정보"

            if context.get("emotion"):
                context_section += f"\n- 감지된 감정: {context['emotion']}"

            if context.get("emotion_intensity"):
                context_section += f"\n- 감정 강도: {context['emotion_intensity']}/10"

            if context.get("crisis_level"):
                crisis_level = context["crisis_level"]
                if crisis_level > 0.7:
                    context_section += "\n- ⚠️ **위기 상황 감지**: 내담자 안전 최우선 대응"
                elif crisis_level > 0.4:
                    context_section += "\n- ⚡ 주의 필요: 위기 징후 모니터링"

            if context.get("rag_context"):
                context_section += f"\n\n## 참고 지식\n{context['rag_context']}"

            if context.get("user_concerns"):
                concerns = ", ".join(context["user_concerns"])
                context_section += f"\n- 주요 고민: {concerns}"

            base_prompt += context_section

        return base_prompt

    def _get_few_shot_section(self) -> str:
        """Few-shot 예시 섹션 생성"""
        section = "\n\n## 응답 예시 (참고)"

        # 공감 예시 1개
        empathy_example = self.few_shot_examples["empathy"][0]
        section += f"""

### 예시 1: 공감적 응답
내담자: "{empathy_example.user_input}"
[내부 분석: {empathy_example.thinking}]
{self.persona_name}: "{empathy_example.response}"
"""

        # 문화적 맥락 예시 1개
        cultural_example = self.few_shot_examples["empathy"][2]
        section += f"""
### 예시 2: 한국 문화 맥락 반영
내담자: "{cultural_example.user_input}"
[내부 분석: {cultural_example.thinking}]
{self.persona_name}: "{cultural_example.response}"
"""

        return section

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
            context["crisis_level"] = crisis_info.get("risk_score", 0)

        if rag_context:
            context["rag_context"] = rag_context

        # 시스템 프롬프트
        system_prompt = self.get_system_prompt(context)

        # 대화 이력 포맷팅
        history_text = ""
        if conversation_history:
            recent_history = conversation_history[-6:]  # 최근 6턴만
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
        """
        위기 개입 프롬프트

        Args:
            crisis_type: 위기 유형 (suicide, self_harm, violence 등)

        Returns:
            str: 위기 개입 프롬프트
        """
        crisis_prompts = {
            "suicide": """당신의 생명은 매우 소중합니다. 지금 느끼시는 고통이 얼마나 큰지 이해합니다.

하지만 지금 당장 전문가의 도움이 필요합니다. 혼자 감당하지 마시고, 다음 기관에 연락해주세요:

🆘 자살예방상담전화: 1393 (24시간)
🆘 정신건강위기상담전화: 1577-0199 (24시간)
🆘 응급상황: 119

지금 이 순간이 힘들더라도, 도움을 받으시면 상황은 나아질 수 있습니다.""",

            "self_harm": """스스로를 해치고 싶은 충동이 드신다니, 정말 힘든 상황이시군요.

지금 당장 안전한 곳으로 이동하시고, 전문가의 도움을 받으시는 것이 중요합니다:

📞 정신건강위기상담전화: 1577-0199 (24시간)
📞 청소년전화: 1388 (24시간)
🆘 응급상황: 119

당신의 안전이 가장 중요합니다.""",

            "violence": """폭력이나 학대 상황에 있으시다면, 당신의 안전이 최우선입니다.

즉시 안전한 곳으로 피신하시고 도움을 요청하세요:

🆘 경찰: 112
📞 여성긴급전화: 1366 (24시간)
📞 아동학대신고: 112
📞 가정폭력상담: 1366

위험한 상황에서는 주저하지 마시고 도움을 요청하세요."""
        }

        return crisis_prompts.get(crisis_type, crisis_prompts["suicide"])

    def format_conversation_turn(
        self,
        user_message: str,
        emotion: Optional[str] = None,
        crisis_detected: bool = False
    ) -> str:
        """
        대화 턴 포맷팅

        Args:
            user_message: 사용자 메시지
            emotion: 감지된 감정
            crisis_detected: 위기 감지 여부

        Returns:
            str: 포맷된 대화
        """
        formatted = f"내담자: {user_message}"

        if emotion:
            formatted += f"\n[감지된 감정: {emotion}]"

        if crisis_detected:
            formatted += "\n[⚠️ 위기 상황 감지됨]"

        return formatted

    def get_greeting_prompt(self) -> str:
        """
        인사 프롬프트

        Returns:
            str: 인사말
        """
        return f"안녕하세요, {self.persona_name}입니다. 오늘은 어떤 이야기를 나누고 싶으신가요? 편안하게 말씀해주세요."

    def get_closing_prompt(self) -> str:
        """
        종료 프롬프트

        Returns:
            str: 마무리 인사
        """
        return "오늘 함께 이야기 나눠주셔서 감사합니다. 힘든 시간이지만 스스로를 잘 돌보시길 바랍니다. 언제든 다시 찾아와주세요."

    def get_reflection_question(self, topic: str = "general") -> List[str]:
        """
        성찰 질문 생성

        Args:
            topic: 주제 (general, emotion, thought, behavior)

        Returns:
            List[str]: 성찰 질문 리스트
        """
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
        """
        대처 전략 프롬프트

        Args:
            emotion_type: 감정 유형 (anxiety, depression, anger, stress)

        Returns:
            str: 대처 전략 안내
        """
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
        """
        타당화 응답 생성

        Returns:
            List[str]: 타당화 응답 리스트
        """
        return [
            "그런 상황에서 그렇게 느끼시는 것은 충분히 이해가 됩니다.",
            "당신의 감정은 모두 타당하고 소중합니다.",
            "그렇게 생각하신 것은 자연스러운 반응이에요.",
            "지금 느끼시는 것을 느끼셔도 괜찮아요."
        ]


# 기본 템플릿 인스턴스
default_template = PromptTemplate()


if __name__ == "__main__":
    # 테스트
    template = PromptTemplate("마음이")
    print("=== 시스템 프롬프트 ===")
    print(template.get_system_prompt())
    print("\n=== 인사말 ===")
    print(template.get_greeting_prompt())
