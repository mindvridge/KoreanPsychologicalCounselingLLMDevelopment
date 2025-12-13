# -*- coding: utf-8 -*-
"""
저널링/글쓰기 치료 모듈 (Journaling Therapy Module)

표현적 글쓰기, 감사 일기, 자기 성찰 일지 등 다양한 저널링 기법을
채팅에 통합하여 감정 표현과 자기 이해를 돕습니다.

Author: MindVridge AI Team
Version: 1.0.0
"""

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple


class JournalingType(Enum):
    """저널링 유형"""
    EXPRESSIVE = "expressive"           # 표현적 글쓰기
    GRATITUDE = "gratitude"             # 감사 일기
    SELF_REFLECTION = "self_reflection" # 자기 성찰
    EMOTION_PROCESSING = "emotion"      # 감정 처리
    LETTER_WRITING = "letter"           # 편지 쓰기
    FUTURE_SELF = "future_self"         # 미래의 나에게
    STREAM_OF_CONSCIOUSNESS = "stream"  # 의식의 흐름
    PROMPTED = "prompted"               # 질문 기반


class LetterType(Enum):
    """편지 유형"""
    TO_SELF = "to_self"                 # 자기 자신에게
    TO_PAST_SELF = "to_past_self"       # 과거의 나에게
    TO_FUTURE_SELF = "to_future_self"   # 미래의 나에게
    TO_EMOTION = "to_emotion"           # 감정에게
    TO_UNSENT = "to_unsent"             # 보내지 못한 편지
    FORGIVENESS = "forgiveness"         # 용서의 편지


@dataclass
class JournalPrompt:
    """저널링 프롬프트"""
    prompt_id: str
    journaling_type: JournalingType
    prompt: str
    follow_up_questions: List[str]
    therapeutic_purpose: str
    suitable_emotions: List[str]
    difficulty: str = "easy"


@dataclass
class JournalEntry:
    """저널 항목"""
    entry_id: str
    user_id: str
    journaling_type: JournalingType
    timestamp: datetime
    prompt_used: Optional[str] = None
    content: str = ""
    emotion_before: Optional[Dict] = None
    emotion_after: Optional[Dict] = None
    insights: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class JournalingSession:
    """저널링 세션"""
    session_id: str
    user_id: str
    journaling_type: JournalingType
    current_step: str = "intro"
    started_at: datetime = field(default_factory=datetime.now)
    entries: List[str] = field(default_factory=list)
    prompt_used: Optional[JournalPrompt] = None
    completed: bool = False


class JournalingPromptLibrary:
    """저널링 프롬프트 라이브러리"""

    def __init__(self):
        self.prompts = self._initialize_prompts()

    def _initialize_prompts(self) -> Dict[JournalingType, List[JournalPrompt]]:
        """프롬프트 초기화"""
        return {
            JournalingType.EXPRESSIVE: [
                JournalPrompt(
                    prompt_id="exp_1",
                    journaling_type=JournalingType.EXPRESSIVE,
                    prompt="지금 가장 마음에 걸리는 것에 대해 자유롭게 써보세요. 검열하지 말고, 떠오르는 대로 적어보세요.",
                    follow_up_questions=[
                        "이 글을 쓰면서 어떤 감정이 올라왔나요?",
                        "가장 쓰기 힘들었던 부분은 어디였나요?",
                        "이 상황에서 진정으로 원하는 것은 무엇인가요?"
                    ],
                    therapeutic_purpose="감정의 표현과 해소, 내면의 정리",
                    suitable_emotions=["슬픔", "분노", "불안", "혼란"]
                ),
                JournalPrompt(
                    prompt_id="exp_2",
                    journaling_type=JournalingType.EXPRESSIVE,
                    prompt="최근에 느낀 가장 강렬한 감정에 대해 써보세요. 그 감정이 몸에서 어떻게 느껴졌는지도 포함해 주세요.",
                    follow_up_questions=[
                        "이 감정은 언제 시작되었나요?",
                        "비슷한 감정을 느꼈던 과거의 경험이 있나요?",
                        "이 감정이 당신에게 말하려는 것은 무엇일까요?"
                    ],
                    therapeutic_purpose="감정 인식과 수용",
                    suitable_emotions=["모든 감정"]
                )
            ],

            JournalingType.GRATITUDE: [
                JournalPrompt(
                    prompt_id="grat_1",
                    journaling_type=JournalingType.GRATITUDE,
                    prompt="오늘 감사한 것 세 가지를 적어보세요. 아무리 작은 것이라도 괜찮아요.",
                    follow_up_questions=[
                        "이 것들이 왜 감사하게 느껴지나요?",
                        "이 감사함을 누군가에게 표현한다면 어떻게 할까요?",
                        "감사한 것을 생각하니 기분이 어떤가요?"
                    ],
                    therapeutic_purpose="긍정적 관점 강화, 행복감 증진",
                    suitable_emotions=["우울", "무기력", "부정적"]
                ),
                JournalPrompt(
                    prompt_id="grat_2",
                    journaling_type=JournalingType.GRATITUDE,
                    prompt="당신의 삶에 긍정적인 영향을 준 사람에 대해 써보세요. 그 사람이 어떻게 당신을 도왔나요?",
                    follow_up_questions=[
                        "그 사람에게 감사함을 표현한 적이 있나요?",
                        "그 사람에게서 배운 것은 무엇인가요?",
                        "비슷한 방식으로 다른 사람을 도울 수 있을까요?"
                    ],
                    therapeutic_purpose="관계의 소중함 인식, 연결감",
                    suitable_emotions=["외로움", "고립감"]
                ),
                JournalPrompt(
                    prompt_id="grat_3",
                    journaling_type=JournalingType.GRATITUDE,
                    prompt="힘들었지만 결국 성장할 수 있었던 경험에 대해 써보세요.",
                    follow_up_questions=[
                        "그 경험에서 무엇을 배웠나요?",
                        "지금의 당신에게 그 경험이 어떤 의미인가요?",
                        "과거의 나에게 해주고 싶은 말이 있나요?"
                    ],
                    therapeutic_purpose="역경을 통한 성장 인식",
                    suitable_emotions=["후회", "자책"]
                )
            ],

            JournalingType.SELF_REFLECTION: [
                JournalPrompt(
                    prompt_id="ref_1",
                    journaling_type=JournalingType.SELF_REFLECTION,
                    prompt="최근 당신이 자랑스럽게 생각하는 것은 무엇인가요? 왜 그렇게 느끼시나요?",
                    follow_up_questions=[
                        "이것을 이루기 위해 어떤 노력을 했나요?",
                        "이 성취가 당신에 대해 무엇을 말해주나요?",
                        "앞으로 더 자랑스럽게 여기고 싶은 것은?"
                    ],
                    therapeutic_purpose="자기 효능감 강화",
                    suitable_emotions=["자기 비하", "낮은 자존감"]
                ),
                JournalPrompt(
                    prompt_id="ref_2",
                    journaling_type=JournalingType.SELF_REFLECTION,
                    prompt="당신의 가치관 중 가장 중요한 것은 무엇인가요? 그 가치관은 어떻게 형성되었나요?",
                    follow_up_questions=[
                        "이 가치관에 따라 살고 있다고 느끼시나요?",
                        "가치관과 행동이 일치하지 않을 때 어떤 느낌인가요?",
                        "이 가치관을 더 잘 실천하려면 무엇을 할 수 있을까요?"
                    ],
                    therapeutic_purpose="정체성 탐색, 가치 명확화",
                    suitable_emotions=["혼란", "방향 상실"]
                ),
                JournalPrompt(
                    prompt_id="ref_3",
                    journaling_type=JournalingType.SELF_REFLECTION,
                    prompt="1년 후의 당신은 어떤 모습이길 원하나요? 구체적으로 상상해서 써보세요.",
                    follow_up_questions=[
                        "그 모습이 되기 위해 지금 할 수 있는 작은 것은?",
                        "어떤 어려움이 예상되나요?",
                        "그 목표를 향해 가는 과정에서 무엇이 당신을 지지해줄까요?"
                    ],
                    therapeutic_purpose="목표 설정, 동기 부여",
                    suitable_emotions=["무기력", "목표 상실"]
                )
            ],

            JournalingType.EMOTION_PROCESSING: [
                JournalPrompt(
                    prompt_id="emo_1",
                    journaling_type=JournalingType.EMOTION_PROCESSING,
                    prompt="지금 느끼는 감정에게 편지를 쓰듯이 말을 걸어보세요. '안녕, 슬픔아...' 처럼요.",
                    follow_up_questions=[
                        "이 감정은 당신에게 무엇을 말하고 있나요?",
                        "이 감정이 필요로 하는 것은 무엇일까요?",
                        "이 감정과 평화롭게 공존할 수 있을까요?"
                    ],
                    therapeutic_purpose="감정 수용, 감정과의 관계 개선",
                    suitable_emotions=["모든 강렬한 감정"]
                ),
                JournalPrompt(
                    prompt_id="emo_2",
                    journaling_type=JournalingType.EMOTION_PROCESSING,
                    prompt="만약 당신의 감정이 색깔이라면 어떤 색일까요? 그 이유와 함께 써보세요.",
                    follow_up_questions=[
                        "그 색깔이 변한다면 어떤 색으로 바뀌길 원하나요?",
                        "어떤 상황에서 그 색깔이 더 밝아지거나 어두워지나요?",
                        "지금 원하는 색깔은 무엇인가요?"
                    ],
                    therapeutic_purpose="감정의 상징적 표현, 창의적 처리",
                    suitable_emotions=["모든 감정"]
                )
            ],

            JournalingType.LETTER_WRITING: [
                JournalPrompt(
                    prompt_id="letter_1",
                    journaling_type=JournalingType.LETTER_WRITING,
                    prompt="과거의 나에게 편지를 써보세요. 힘들었던 시기의 나에게 해주고 싶은 말은?",
                    follow_up_questions=[
                        "과거의 당신은 이 편지를 받으면 어떤 기분일까요?",
                        "이 편지를 쓰면서 무엇을 느꼈나요?",
                        "지금의 당신이 과거의 당신에게 배울 점은?"
                    ],
                    therapeutic_purpose="자기 연민, 내면 아이 치유",
                    suitable_emotions=["후회", "자책", "슬픔"]
                ),
                JournalPrompt(
                    prompt_id="letter_2",
                    journaling_type=JournalingType.LETTER_WRITING,
                    prompt="미래의 나에게 편지를 써보세요. 5년 후의 나에게 하고 싶은 말은?",
                    follow_up_questions=[
                        "5년 후의 당신은 이 편지를 읽으며 무엇을 느낄까요?",
                        "미래의 당신에게 바라는 것은 무엇인가요?",
                        "지금의 당신이 미래를 위해 심을 수 있는 씨앗은?"
                    ],
                    therapeutic_purpose="희망 함양, 장기적 관점",
                    suitable_emotions=["불안", "두려움"]
                ),
                JournalPrompt(
                    prompt_id="letter_3",
                    journaling_type=JournalingType.LETTER_WRITING,
                    prompt="전하지 못한 말이 있는 사람에게 편지를 써보세요. 보내지 않아도 괜찮아요.",
                    follow_up_questions=[
                        "왜 그 말을 전하지 못했나요?",
                        "이 편지를 쓰고 나니 어떤 느낌인가요?",
                        "실제로 전달할 수 있는 부분이 있을까요?"
                    ],
                    therapeutic_purpose="미완의 감정 처리, 해소",
                    suitable_emotions=["후회", "분노", "그리움"]
                )
            ],

            JournalingType.PROMPTED: [
                JournalPrompt(
                    prompt_id="prompt_1",
                    journaling_type=JournalingType.PROMPTED,
                    prompt="오늘 하루 중 가장 기억에 남는 순간은 무엇인가요?",
                    follow_up_questions=[
                        "그 순간이 왜 기억에 남나요?",
                        "그 순간에 무엇을 느꼈나요?",
                        "비슷한 순간을 더 많이 만들려면 어떻게 해야 할까요?"
                    ],
                    therapeutic_purpose="마음챙김, 일상의 의미 발견",
                    suitable_emotions=["일반"]
                ),
                JournalPrompt(
                    prompt_id="prompt_2",
                    journaling_type=JournalingType.PROMPTED,
                    prompt="만약 두려움이 없다면 무엇을 하고 싶나요?",
                    follow_up_questions=[
                        "어떤 두려움이 당신을 막고 있나요?",
                        "그 두려움은 어디서 왔을까요?",
                        "작은 첫 걸음을 내딛을 수 있다면 무엇일까요?"
                    ],
                    therapeutic_purpose="두려움 탐색, 용기 함양",
                    suitable_emotions=["두려움", "불안"]
                ),
                JournalPrompt(
                    prompt_id="prompt_3",
                    journaling_type=JournalingType.PROMPTED,
                    prompt="당신이 가장 편안함을 느끼는 장소를 상세히 묘사해 보세요.",
                    follow_up_questions=[
                        "그 장소에서 어떤 감각을 느끼나요?",
                        "그 장소가 왜 당신에게 편안함을 주나요?",
                        "그 편안함을 일상에서 느끼려면 어떻게 할 수 있을까요?"
                    ],
                    therapeutic_purpose="안전 공간 구축, 이완",
                    suitable_emotions=["스트레스", "불안"]
                ),
                JournalPrompt(
                    prompt_id="prompt_4",
                    journaling_type=JournalingType.PROMPTED,
                    prompt="당신을 가장 잘 아는 친구가 당신을 소개한다면 뭐라고 할까요?",
                    follow_up_questions=[
                        "그 설명이 당신이 생각하는 자신과 다른가요?",
                        "친구의 시선으로 본 당신의 장점은?",
                        "자신에 대해 새롭게 발견한 것이 있나요?"
                    ],
                    therapeutic_purpose="자기 인식, 다양한 관점",
                    suitable_emotions=["자기 비하", "정체성 혼란"]
                )
            ],

            JournalingType.STREAM_OF_CONSCIOUSNESS: [
                JournalPrompt(
                    prompt_id="stream_1",
                    journaling_type=JournalingType.STREAM_OF_CONSCIOUSNESS,
                    prompt="지금 이 순간 떠오르는 생각을 그대로 적어보세요. 문법이나 구성에 신경 쓰지 마세요. 3분 동안 멈추지 말고 써보세요.",
                    follow_up_questions=[
                        "글을 쓰면서 무엇을 발견했나요?",
                        "반복되는 주제나 단어가 있었나요?",
                        "이 글에서 가장 중요한 문장은 무엇인가요?"
                    ],
                    therapeutic_purpose="무의식 탐색, 억압된 생각 표출",
                    suitable_emotions=["혼란", "복잡함"]
                )
            ]
        }

    def get_prompts(self, journaling_type: JournalingType) -> List[JournalPrompt]:
        """특정 유형의 프롬프트들 반환"""
        return self.prompts.get(journaling_type, [])

    def get_random_prompt(self, journaling_type: JournalingType = None) -> JournalPrompt:
        """랜덤 프롬프트 반환"""
        if journaling_type:
            prompts = self.prompts.get(journaling_type, [])
        else:
            prompts = [p for prompts in self.prompts.values() for p in prompts]

        return random.choice(prompts) if prompts else None

    def get_prompt_for_emotion(self, emotion: str) -> JournalPrompt:
        """감정에 맞는 프롬프트 반환"""
        suitable_prompts = []

        for prompts in self.prompts.values():
            for prompt in prompts:
                if emotion.lower() in [e.lower() for e in prompt.suitable_emotions]:
                    suitable_prompts.append(prompt)
                elif "모든" in prompt.suitable_emotions[0] or "일반" in prompt.suitable_emotions[0]:
                    suitable_prompts.append(prompt)

        return random.choice(suitable_prompts) if suitable_prompts else self.get_random_prompt()


class JournalingTriggerDetector:
    """저널링 필요 상황 감지"""

    def __init__(self):
        self.processing_keywords = [
            "정리가 안", "복잡", "모르겠", "혼란", "뭐라고 해야",
            "말로 표현하기", "설명하기 어려", "머릿속이"
        ]

        self.expression_need_keywords = [
            "답답", "속에 담아", "말 못", "참아", "숨기",
            "터질 것 같", "표현하기 어려", "말해본 적 없"
        ]

        self.reflection_keywords = [
            "왜 그랬을까", "이해가 안 돼", "내가 왜", "무슨 의미",
            "돌아보면", "생각해보면", "왜 이럴까"
        ]

        self.gratitude_triggers = [
            "감사", "고마", "다행", "좋은 일", "행복"
        ]

    def detect(self, message: str, emotion_context: Optional[Dict] = None) -> Dict[str, Any]:
        """저널링 필요 상황 감지"""
        message_lower = message.lower()

        triggers = {
            "processing_need": self._check_keywords(message_lower, self.processing_keywords),
            "expression_need": self._check_keywords(message_lower, self.expression_need_keywords),
            "reflection_need": self._check_keywords(message_lower, self.reflection_keywords),
            "gratitude_moment": self._check_keywords(message_lower, self.gratitude_triggers)
        }

        # 추천 저널링 유형 결정
        recommended_type = self._recommend_type(triggers)

        return {
            "should_suggest": any(t["detected"] for t in triggers.values()),
            "triggers": triggers,
            "recommended_type": recommended_type.value if recommended_type else None,
            "urgency": self._assess_urgency(triggers)
        }

    def _check_keywords(self, message: str, keywords: List[str]) -> Dict[str, Any]:
        """키워드 매칭"""
        matches = [kw for kw in keywords if kw in message]
        return {
            "detected": len(matches) > 0,
            "matches": matches,
            "confidence": min(len(matches) * 0.25, 0.9)
        }

    def _recommend_type(self, triggers: Dict) -> Optional[JournalingType]:
        """저널링 유형 추천"""
        if triggers["gratitude_moment"]["detected"]:
            return JournalingType.GRATITUDE
        elif triggers["expression_need"]["detected"]:
            return JournalingType.EXPRESSIVE
        elif triggers["reflection_need"]["detected"]:
            return JournalingType.SELF_REFLECTION
        elif triggers["processing_need"]["detected"]:
            return JournalingType.STREAM_OF_CONSCIOUSNESS
        return None

    def _assess_urgency(self, triggers: Dict) -> str:
        """긴급도 평가"""
        detected_count = sum(1 for t in triggers.values() if t["detected"])
        if detected_count >= 2:
            return "high"
        elif detected_count == 1:
            return "medium"
        return "low"


class IntegratedJournalingChat:
    """채팅 통합형 저널링 시스템"""

    def __init__(self):
        self.trigger_detector = JournalingTriggerDetector()
        self.prompt_library = JournalingPromptLibrary()
        self.active_sessions: Dict[str, JournalingSession] = {}
        self.entry_counter = 0

    def process_message(
        self,
        session_id: str,
        user_message: str,
        emotion_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """사용자 메시지 처리"""

        # 진행 중인 저널링 세션이 있는지 확인
        if session_id in self.active_sessions:
            return self._handle_active_session(session_id, user_message)

        # 저널링 필요 상황 감지
        trigger_result = self.trigger_detector.detect(user_message, emotion_context)

        if trigger_result["should_suggest"] and trigger_result["urgency"] != "low":
            return self._suggest_journaling(session_id, trigger_result, emotion_context)

        return {
            "journaling_suggested": False,
            "response": None,
            "continue_conversation": True
        }

    def _suggest_journaling(
        self,
        session_id: str,
        trigger_result: Dict,
        emotion_context: Optional[Dict]
    ) -> Dict[str, Any]:
        """저널링 제안"""
        recommended_type = trigger_result["recommended_type"]

        type_descriptions = {
            "expressive": ("표현적 글쓰기", "마음속 감정을 자유롭게 표현하는"),
            "gratitude": ("감사 일기", "좋은 것들에 집중하는"),
            "self_reflection": ("자기 성찰", "자신을 돌아보는"),
            "stream": ("의식의 흐름", "생각을 정리하는"),
            "letter": ("편지 쓰기", "마음을 전하는"),
        }

        name, desc = type_descriptions.get(
            recommended_type,
            ("글쓰기", "마음을 정리하는")
        )

        response = f"""마음이 복잡하시군요. 💭

✍️ **{name}**을 해보시는 건 어떨까요?
{desc} 글쓰기는 감정을 정리하고 새로운 관점을 얻는 데 도움이 돼요.

저와 함께 차근차근 해볼 수 있어요.
5-10분 정도면 충분해요.

해보시겠어요? (네/아니요)"""

        return {
            "journaling_suggested": True,
            "recommended_type": recommended_type,
            "response": response,
            "continue_conversation": True,
            "awaiting_acceptance": True
        }

    def start_journaling(
        self,
        session_id: str,
        user_id: str,
        journaling_type: JournalingType = None,
        emotion: str = None
    ) -> Dict[str, Any]:
        """저널링 세션 시작"""
        # 프롬프트 선택
        if emotion:
            prompt = self.prompt_library.get_prompt_for_emotion(emotion)
        elif journaling_type:
            prompts = self.prompt_library.get_prompts(journaling_type)
            prompt = random.choice(prompts) if prompts else self.prompt_library.get_random_prompt()
        else:
            prompt = self.prompt_library.get_random_prompt()

        if not prompt:
            return {
                "error": True,
                "response": "적절한 글쓰기 주제를 찾지 못했어요. 직접 쓰고 싶은 내용이 있으신가요?"
            }

        # 세션 생성
        self.active_sessions[session_id] = JournalingSession(
            session_id=session_id,
            user_id=user_id,
            journaling_type=prompt.journaling_type,
            prompt_used=prompt,
            current_step="writing"
        )

        response = f"""좋아요, 함께 글을 써볼게요. ✍️

**오늘의 질문:**
{prompt.prompt}

시간을 충분히 가지시고, 떠오르는 대로 자유롭게 적어주세요.
완벽할 필요 없어요. 진솔한 마음이 담기면 충분해요.

준비되시면 글을 시작해 주세요. 💙"""

        return {
            "session_started": True,
            "prompt": prompt.prompt,
            "journaling_type": prompt.journaling_type.value,
            "response": response,
            "continue_conversation": True
        }

    def _handle_active_session(
        self,
        session_id: str,
        user_message: str
    ) -> Dict[str, Any]:
        """진행 중인 세션 처리"""
        session = self.active_sessions[session_id]
        message_lower = user_message.lower().strip()

        # 중단 요청
        if any(word in message_lower for word in ["그만", "멈춰", "중단", "취소"]):
            return self._end_session(session_id, interrupted=True)

        # 단계별 처리
        if session.current_step == "writing":
            return self._process_writing(session_id, user_message)
        elif session.current_step == "reflection":
            return self._process_reflection(session_id, user_message)
        elif session.current_step == "closing":
            return self._complete_session(session_id, user_message)

        return {
            "response": "계속 글을 써주세요. 편하게 이야기해 주세요.",
            "continue_conversation": True
        }

    def _process_writing(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """글쓰기 단계 처리"""
        session = self.active_sessions[session_id]
        session.entries.append(user_message)

        # 글 길이에 따른 응답
        word_count = len(user_message)

        if word_count < 50:
            response = """더 이야기해 주실 것이 있으신가요?
조금 더 자세히 적어보셔도 좋아요.

마무리하셨으면 '다 썼어요'라고 말씀해 주세요."""
        else:
            prompt = session.prompt_used
            follow_up = prompt.follow_up_questions[0] if prompt.follow_up_questions else "이 글을 쓰면서 어떤 느낌이 드셨나요?"
            session.current_step = "reflection"

            response = f"""잘 쓰셨어요. 💙

글을 읽으면서 느껴지는 것들이 있네요.

**성찰 질문:**
{follow_up}

편하게 생각을 나눠주세요."""

        return {
            "response": response,
            "continue_conversation": True
        }

    def _process_reflection(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """성찰 단계 처리"""
        session = self.active_sessions[session_id]
        session.entries.append(user_message)

        prompt = session.prompt_used
        current_question_idx = len(session.entries) - 1

        # 더 많은 성찰 질문이 있는지 확인
        if current_question_idx < len(prompt.follow_up_questions) and len(session.entries) < 4:
            next_question = prompt.follow_up_questions[min(current_question_idx, len(prompt.follow_up_questions) - 1)]
            response = f"""좋은 성찰이에요.

{next_question}"""
        else:
            session.current_step = "closing"
            response = """깊이 있게 생각해 주셨네요. ✨

마지막으로, 오늘 글쓰기를 통해 새롭게 발견한 것이나
기억하고 싶은 것이 있으신가요?"""

        return {
            "response": response,
            "continue_conversation": True
        }

    def _complete_session(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """세션 완료"""
        session = self.active_sessions[session_id]
        session.entries.append(user_message)
        session.completed = True

        # 요약 생성
        insights = self._generate_insights(session)

        response = f"""🎉 **글쓰기 완료!**

오늘 자신과 대화하는 시간을 가지셨어요.
이런 시간은 마음 건강에 정말 소중해요.

{insights}

💡 **팁**: 정기적인 글쓰기는 감정 조절과 자기 이해에 큰 도움이 돼요.
힘들 때, 기쁠 때, 언제든 글로 마음을 표현해 보세요.

오늘 수고하셨어요. 💙"""

        # 세션 정리
        del self.active_sessions[session_id]

        return {
            "response": response,
            "session_completed": True,
            "continue_conversation": True
        }

    def _generate_insights(self, session: JournalingSession) -> str:
        """인사이트 생성"""
        prompt = session.prompt_used

        return f"""**📝 오늘의 기록**
• 주제: {prompt.prompt[:50]}...
• 치료적 목적: {prompt.therapeutic_purpose}
"""

    def _end_session(self, session_id: str, interrupted: bool = False) -> Dict[str, Any]:
        """세션 종료"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            # 작성한 내용이 있다면 저장
            del self.active_sessions[session_id]

        if interrupted:
            response = """괜찮아요, 나중에 다시 해볼 수 있어요.
글을 쓰고 싶은 마음이 들 때 언제든 말씀해 주세요. 💙"""
        else:
            response = "글쓰기를 마쳤습니다. 계속 이야기를 나눠볼까요?"

        return {
            "response": response,
            "session_ended": True,
            "interrupted": interrupted,
            "continue_conversation": True
        }

    def get_daily_prompt(self) -> Dict[str, Any]:
        """오늘의 글쓰기 주제"""
        prompt = self.prompt_library.get_random_prompt()

        return {
            "prompt": prompt.prompt,
            "type": prompt.journaling_type.value,
            "purpose": prompt.therapeutic_purpose
        }

    def list_journaling_types(self) -> List[Dict]:
        """저널링 유형 목록"""
        type_info = {
            JournalingType.EXPRESSIVE: {
                "name": "표현적 글쓰기",
                "description": "감정을 자유롭게 표현하여 해소하는 글쓰기"
            },
            JournalingType.GRATITUDE: {
                "name": "감사 일기",
                "description": "일상의 감사한 것들을 기록하여 긍정성을 높이는 글쓰기"
            },
            JournalingType.SELF_REFLECTION: {
                "name": "자기 성찰",
                "description": "자신의 생각, 행동, 가치관을 돌아보는 글쓰기"
            },
            JournalingType.EMOTION_PROCESSING: {
                "name": "감정 처리",
                "description": "특정 감정을 탐색하고 이해하는 글쓰기"
            },
            JournalingType.LETTER_WRITING: {
                "name": "편지 쓰기",
                "description": "자신이나 타인에게 마음을 전하는 편지"
            },
            JournalingType.STREAM_OF_CONSCIOUSNESS: {
                "name": "의식의 흐름",
                "description": "떠오르는 생각을 검열 없이 적는 자유 글쓰기"
            },
            JournalingType.PROMPTED: {
                "name": "질문 기반",
                "description": "특정 질문에 답하며 생각을 정리하는 글쓰기"
            }
        }

        return [
            {
                "type": jtype.value,
                "name": info["name"],
                "description": info["description"]
            }
            for jtype, info in type_info.items()
        ]


# 사용 예시
if __name__ == "__main__":
    system = IntegratedJournalingChat()

    # 감지 테스트
    result = system.process_message(
        "session_1",
        "마음이 너무 복잡해요... 속에 담아두기만 하고 말을 못하겠어요"
    )
    print("=== 저널링 제안 ===")
    print(result["response"])

    # 오늘의 주제
    print("\n=== 오늘의 글쓰기 주제 ===")
    daily = system.get_daily_prompt()
    print(f"주제: {daily['prompt']}")
    print(f"유형: {daily['type']}")

    # 저널링 유형 목록
    print("\n=== 저널링 유형 ===")
    for jtype in system.list_journaling_types():
        print(f"- {jtype['name']}: {jtype['description']}")
