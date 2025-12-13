# -*- coding: utf-8 -*-
"""
그라운딩 기법 모듈 (Grounding Techniques Module)

해리, 플래시백, 공황, 강한 감정 상태에서 현재에 집중할 수 있도록
돕는 그라운딩 기법을 채팅에 통합합니다.

Author: MindVridge AI Team
Version: 1.0.0
"""

import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any


class GroundingType(Enum):
    """그라운딩 기법 유형"""
    SENSORY_54321 = "sensory_54321"           # 5-4-3-2-1 감각 기법
    PHYSICAL = "physical"                      # 신체적 그라운딩
    MENTAL = "mental"                          # 정신적 그라운딩
    SOOTHING = "soothing"                      # 자기 위로
    OBJECT_FOCUS = "object_focus"             # 물체 집중
    CATEGORICAL = "categorical"                # 범주 나열
    TEMPERATURE = "temperature"                # 온도 자극


class TriggerSeverity(Enum):
    """트리거 심각도"""
    MILD = "mild"           # 가벼운 불안/해리
    MODERATE = "moderate"   # 중간 수준
    SEVERE = "severe"       # 심한 해리/플래시백


@dataclass
class GroundingExercise:
    """그라운딩 운동"""
    grounding_type: GroundingType
    name: str
    description: str
    target_symptoms: List[str]
    steps: List[str]
    duration_minutes: int
    difficulty: str
    requires_objects: bool = False
    required_objects: List[str] = field(default_factory=list)


@dataclass
class GroundingSession:
    """그라운딩 세션 상태"""
    session_id: str
    user_id: str
    technique: GroundingType
    current_step: int = 0
    started_at: datetime = field(default_factory=datetime.now)
    user_responses: List[str] = field(default_factory=list)
    completed: bool = False


class GroundingTriggerDetector:
    """그라운딩 필요 상황 감지"""

    def __init__(self):
        # 해리 관련 키워드
        self.dissociation_keywords = [
            "현실감이 없", "꿈인 것 같", "내가 아닌 것 같", "몸이 내 것 같지",
            "멍하", "아무 생각이 안", "기억이 안", "시간이 멈춘",
            "유체이탈", "내 몸 밖에서", "보는 것 같", "영화 속",
            "안개 낀 것 같", "유리벽", "비현실"
        ]

        # 플래시백 관련 키워드
        self.flashback_keywords = [
            "플래시백", "그때 일이", "다시 겪는 것 같", "떠오르", "악몽",
            "생생하게", "그 순간", "다시 그곳에", "트라우마", "과거가"
        ]

        # 공황/압도 관련 키워드
        self.overwhelm_keywords = [
            "압도", "감당이 안", "무너질 것 같", "터질 것 같",
            "미칠 것 같", "제어가 안", "폭발할 것 같", "견딜 수 없"
        ]

        # 해리성 증상 키워드
        self.depersonalization_keywords = [
            "내가 누군지", "정체성", "나 자신을 모르겠", "내가 낯설"
        ]

    def detect(self, message: str, emotion_context: Optional[Dict] = None) -> Dict[str, Any]:
        """그라운딩 필요 상황 감지"""
        message_lower = message.lower()

        triggers = {
            "dissociation": self._check_keywords(message_lower, self.dissociation_keywords),
            "flashback": self._check_keywords(message_lower, self.flashback_keywords),
            "overwhelm": self._check_keywords(message_lower, self.overwhelm_keywords),
            "depersonalization": self._check_keywords(message_lower, self.depersonalization_keywords)
        }

        # 심각도 평가
        severity = self._assess_severity(triggers)

        # 우선순위 결정
        priority = None
        if triggers["flashback"]["detected"]:
            priority = "flashback"
        elif triggers["dissociation"]["detected"]:
            priority = "dissociation"
        elif triggers["depersonalization"]["detected"]:
            priority = "depersonalization"
        elif triggers["overwhelm"]["detected"]:
            priority = "overwhelm"

        return {
            "should_suggest": any(t["detected"] for t in triggers.values()),
            "triggers": triggers,
            "priority": priority,
            "severity": severity.value if severity else None,
            "recommended_technique": self._recommend_technique(priority, severity)
        }

    def _check_keywords(self, message: str, keywords: List[str]) -> Dict[str, Any]:
        """키워드 매칭 확인"""
        matches = [kw for kw in keywords if kw in message]
        return {
            "detected": len(matches) > 0,
            "matches": matches,
            "confidence": min(len(matches) * 0.25, 1.0)
        }

    def _assess_severity(self, triggers: Dict) -> Optional[TriggerSeverity]:
        """심각도 평가"""
        total_matches = sum(len(t["matches"]) for t in triggers.values())

        if triggers["flashback"]["detected"]:
            return TriggerSeverity.SEVERE
        elif total_matches >= 3:
            return TriggerSeverity.SEVERE
        elif total_matches >= 2:
            return TriggerSeverity.MODERATE
        elif total_matches >= 1:
            return TriggerSeverity.MILD
        return None

    def _recommend_technique(
        self,
        priority: Optional[str],
        severity: Optional[TriggerSeverity]
    ) -> Optional[GroundingType]:
        """상황에 맞는 기법 추천"""
        if severity == TriggerSeverity.SEVERE:
            return GroundingType.SENSORY_54321  # 가장 구조화된 방법
        elif priority == "flashback":
            return GroundingType.PHYSICAL
        elif priority == "dissociation":
            return GroundingType.SENSORY_54321
        elif priority == "depersonalization":
            return GroundingType.PHYSICAL
        elif priority == "overwhelm":
            return GroundingType.SOOTHING

        return GroundingType.SENSORY_54321  # 기본값


class GroundingExerciseLibrary:
    """그라운딩 운동 라이브러리"""

    def __init__(self):
        self.exercises = self._initialize_exercises()

    def _initialize_exercises(self) -> Dict[GroundingType, GroundingExercise]:
        """그라운딩 운동 초기화"""
        return {
            GroundingType.SENSORY_54321: GroundingExercise(
                grounding_type=GroundingType.SENSORY_54321,
                name="5-4-3-2-1 감각 그라운딩",
                description="다섯 가지 감각을 활용하여 현재 순간에 집중하는 기법입니다. 해리나 불안 시 매우 효과적입니다.",
                target_symptoms=["해리", "불안", "플래시백", "공황"],
                steps=[
                    "👀 **보이는 것 5가지**: 지금 주변에서 보이는 것 5가지를 말해주세요.",
                    "👋 **만져지는 것 4가지**: 지금 몸에 닿는 느낌 4가지를 말해주세요.",
                    "👂 **들리는 것 3가지**: 지금 들리는 소리 3가지를 말해주세요.",
                    "👃 **냄새 2가지**: 지금 맡을 수 있는 냄새 2가지를 말해주세요.",
                    "👅 **맛 1가지**: 지금 입안에서 느껴지는 맛 1가지를 말해주세요."
                ],
                duration_minutes=5,
                difficulty="easy"
            ),

            GroundingType.PHYSICAL: GroundingExercise(
                grounding_type=GroundingType.PHYSICAL,
                name="신체 그라운딩",
                description="신체 감각에 집중하여 현재로 돌아오는 기법입니다.",
                target_symptoms=["해리", "플래시백", "비현실감"],
                steps=[
                    "🦶 **발**: 발바닥이 바닥에 닿는 느낌에 집중하세요. 바닥은 딱딱한가요, 부드러운가요?",
                    "🪑 **앉은 자리**: 의자나 바닥에 닿는 엉덩이와 허벅지의 느낌을 느껴보세요.",
                    "✊ **손**: 양손을 꽉 쥐었다가 천천히 펴보세요. 어떤 느낌인가요?",
                    "💪 **팔**: 팔을 들어 올렸다가 내려보세요. 무거움을 느껴보세요.",
                    "🫁 **호흡**: 숨을 깊이 들이마시고, 배가 부풀어 오르는 것을 느껴보세요."
                ],
                duration_minutes=5,
                difficulty="easy"
            ),

            GroundingType.MENTAL: GroundingExercise(
                grounding_type=GroundingType.MENTAL,
                name="정신적 그라운딩",
                description="인지적 과제를 통해 현재에 집중하는 기법입니다.",
                target_symptoms=["해리", "반추", "불안"],
                steps=[
                    "📅 **오늘 정보**: 오늘이 며칠, 무슨 요일인지 말해주세요.",
                    "📍 **장소**: 지금 어디에 있는지, 이 장소의 이름을 말해주세요.",
                    "⏰ **시간**: 지금 몇 시쯤인지, 아침/점심/저녁 중 언제인지 말해주세요.",
                    "👤 **이름**: 본인의 이름과 나이를 말해주세요.",
                    "🏠 **안전**: '나는 지금 안전하다'를 3번 말해보세요."
                ],
                duration_minutes=3,
                difficulty="easy"
            ),

            GroundingType.SOOTHING: GroundingExercise(
                grounding_type=GroundingType.SOOTHING,
                name="자기 위로 그라운딩",
                description="자신을 달래고 위로하며 현재로 돌아오는 기법입니다.",
                target_symptoms=["감정적 압도", "슬픔", "외로움"],
                steps=[
                    "🤗 **자기 포옹**: 양팔로 자신을 감싸안아 보세요. 따뜻한 느낌을 느껴보세요.",
                    "💬 **위로 말**: '괜찮아, 지금 이 순간은 지나갈 거야'라고 자신에게 말해보세요.",
                    "😊 **좋은 기억**: 기분이 좋았던 순간 하나를 떠올려 보세요.",
                    "🙏 **감사**: 지금 이 순간 감사한 것 한 가지를 말해주세요.",
                    "💙 **친구처럼**: 힘든 친구에게 하듯이 자신에게 따뜻한 말을 해보세요."
                ],
                duration_minutes=5,
                difficulty="easy"
            ),

            GroundingType.OBJECT_FOCUS: GroundingExercise(
                grounding_type=GroundingType.OBJECT_FOCUS,
                name="물체 집중 그라운딩",
                description="주변의 물체 하나에 깊이 집중하여 현재로 돌아오는 기법입니다.",
                target_symptoms=["해리", "불안", "산만함"],
                steps=[
                    "🔍 **선택**: 주변에서 물체 하나를 골라주세요. (펜, 컵, 돌 등)",
                    "👀 **관찰**: 그 물체의 색깔, 모양, 크기를 자세히 설명해 주세요.",
                    "👋 **촉감**: 물체를 만져보세요. 어떤 느낌인가요? (차갑다/따뜻하다, 부드럽다/거칠다)",
                    "⚖️ **무게**: 물체의 무게는 어떤가요? 가볍나요, 무거운가요?",
                    "❓ **질문**: 이 물체는 어디서 왔을까요? 어떻게 만들어졌을까요?"
                ],
                duration_minutes=5,
                difficulty="easy",
                requires_objects=True,
                required_objects=["아무 물체나"]
            ),

            GroundingType.CATEGORICAL: GroundingExercise(
                grounding_type=GroundingType.CATEGORICAL,
                name="범주 나열 그라운딩",
                description="특정 범주의 항목들을 나열하며 인지적으로 현재에 집중하는 기법입니다.",
                target_symptoms=["불안", "반추", "걱정"],
                steps=[
                    "🎨 **색깔**: 빨간색인 것 5가지를 말해주세요.",
                    "🐾 **동물**: 동물 이름 5가지를 알파벳/가나다 순으로 말해주세요.",
                    "🌏 **나라**: 가본 적 있거나 가보고 싶은 나라 5개를 말해주세요.",
                    "🍎 **음식**: 좋아하는 음식 5가지를 말해주세요.",
                    "🎵 **노래**: 좋아하는 노래 제목 3개를 말해주세요."
                ],
                duration_minutes=5,
                difficulty="easy"
            ),

            GroundingType.TEMPERATURE: GroundingExercise(
                grounding_type=GroundingType.TEMPERATURE,
                name="온도 자극 그라운딩",
                description="온도 감각을 활용하여 빠르게 현재로 돌아오는 기법입니다.",
                target_symptoms=["심한 해리", "플래시백", "공황"],
                steps=[
                    "🧊 **차가운 물**: 가능하다면 차가운 물로 손이나 얼굴을 적셔보세요.",
                    "❄️ **얼음**: 얼음을 손에 쥐거나 목 뒤에 대어보세요.",
                    "🌡️ **온도 느끼기**: 차가운 느낌이 어떤가요? 어디까지 느껴지나요?",
                    "💨 **바람**: 시원한 바람을 맞거나 부채질을 해보세요.",
                    "🔙 **돌아오기**: 점차 따뜻해지는 것을 느끼며 현재로 돌아오세요."
                ],
                duration_minutes=3,
                difficulty="easy",
                requires_objects=True,
                required_objects=["찬물 또는 얼음"]
            )
        }

    def get_exercise(self, grounding_type: GroundingType) -> GroundingExercise:
        """특정 그라운딩 운동 반환"""
        return self.exercises.get(grounding_type)

    def get_quick_grounding(self) -> List[str]:
        """빠른 그라운딩 팁"""
        return [
            "🦶 발바닥을 바닥에 꾹 누르세요",
            "👐 주변 물체를 잡고 질감을 느껴보세요",
            "❄️ 찬물로 손을 씻으세요",
            "🫁 깊이 숨을 들이쉬고 천천히 내쉬세요",
            "👀 주변에서 파란색 물건 3개를 찾아보세요",
            "🗣️ 자신의 이름과 오늘 날짜를 소리내어 말하세요"
        ]


class IntegratedGroundingChat:
    """채팅 통합형 그라운딩 시스템"""

    def __init__(self):
        self.trigger_detector = GroundingTriggerDetector()
        self.exercise_library = GroundingExerciseLibrary()
        self.active_sessions: Dict[str, GroundingSession] = {}

    def process_message(
        self,
        session_id: str,
        user_message: str,
        emotion_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """사용자 메시지 처리 및 그라운딩 통합"""

        # 진행 중인 세션이 있는지 확인
        if session_id in self.active_sessions:
            return self._handle_active_session(session_id, user_message)

        # 그라운딩 필요 상황 감지
        trigger_result = self.trigger_detector.detect(user_message, emotion_context)

        if trigger_result["should_suggest"]:
            return self._suggest_grounding(session_id, trigger_result)

        return {
            "grounding_suggested": False,
            "response": None,
            "continue_conversation": True
        }

    def _suggest_grounding(
        self,
        session_id: str,
        trigger_result: Dict
    ) -> Dict[str, Any]:
        """그라운딩 제안"""
        priority = trigger_result["priority"]
        severity = trigger_result["severity"]
        technique = trigger_result["recommended_technique"]
        exercise = self.exercise_library.get_exercise(technique)

        # 심각도에 따른 공감 메시지
        if severity == "severe":
            empathy = """지금 정말 힘든 상태이시네요. 괜찮아요, 제가 함께 있을게요.
지금 가장 중요한 건 현재로 돌아오는 거예요."""
        else:
            empathy_messages = {
                "dissociation": "현실감이 흐릿해지는 느낌이시군요. 함께 현재로 돌아와 볼까요?",
                "flashback": "과거의 기억이 밀려오는 것 같군요. 잠시 현재에 집중해 볼까요?",
                "depersonalization": "자신이 낯설게 느껴지시는군요. 몸의 감각에 집중해 볼까요?",
                "overwhelm": "감정이 너무 강렬하시네요. 잠시 안전한 곳으로 돌아와 볼까요?"
            }
            empathy = empathy_messages.get(priority, "지금 힘드시군요. 함께 현재에 집중해 볼까요?")

        # 즉각적 그라운딩 팁
        quick_tip = random.choice(self.exercise_library.get_quick_grounding())

        response = f"""{empathy}

⚡ **지금 바로**: {quick_tip}

🌿 **{exercise.name}**을 안내해 드릴 수 있어요.
{exercise.description}

함께 해보시겠어요? (네/괜찮아요 중 선택해 주세요)"""

        return {
            "grounding_suggested": True,
            "technique": technique.value,
            "severity": severity,
            "response": response,
            "trigger_type": priority,
            "continue_conversation": True,
            "awaiting_acceptance": True
        }

    def start_grounding(
        self,
        session_id: str,
        user_id: str,
        technique: GroundingType
    ) -> Dict[str, Any]:
        """그라운딩 시작"""
        exercise = self.exercise_library.get_exercise(technique)

        # 세션 생성
        self.active_sessions[session_id] = GroundingSession(
            session_id=session_id,
            user_id=user_id,
            technique=technique
        )

        # 시작 안내
        intro = f"""좋아요, 함께 **{exercise.name}**을 시작할게요. 🌿

지금 이 순간, 당신은 안전합니다.
천천히, 저와 함께 해보세요.

준비가 되시면 '시작'이라고 말씀해 주세요."""

        return {
            "session_started": True,
            "response": intro,
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

        # 중단 요청 확인
        if any(word in message_lower for word in ["그만", "멈춰", "중단", "stop", "취소"]):
            return self._end_session(session_id, interrupted=True)

        exercise = self.exercise_library.get_exercise(session.technique)

        # 사용자 응답 저장
        session.user_responses.append(user_message)

        # 시작 요청
        if session.current_step == 0 and any(word in message_lower for word in ["시작", "네", "응", "준비"]):
            return self._get_next_step(session_id)

        # 다음 단계로 진행
        return self._process_response_and_continue(session_id, user_message)

    def _get_next_step(self, session_id: str) -> Dict[str, Any]:
        """다음 그라운딩 단계"""
        session = self.active_sessions[session_id]
        exercise = self.exercise_library.get_exercise(session.technique)

        if session.current_step >= len(exercise.steps):
            return self._complete_session(session_id)

        step = exercise.steps[session.current_step]
        session.current_step += 1

        progress = f"[{session.current_step}/{len(exercise.steps)}]"

        response = f"""**{progress}**

{step}

천천히 말씀해 주세요."""

        return {
            "response": response,
            "current_step": session.current_step,
            "total_steps": len(exercise.steps),
            "continue_conversation": True
        }

    def _process_response_and_continue(
        self,
        session_id: str,
        user_response: str
    ) -> Dict[str, Any]:
        """응답 처리 및 다음 단계 진행"""
        session = self.active_sessions[session_id]
        exercise = self.exercise_library.get_exercise(session.technique)

        # 사용자의 응답에 대한 인정과 격려
        acknowledgments = [
            "좋아요, 잘 하고 계세요.",
            "네, 그렇게 느끼셨군요.",
            "좋습니다. 계속해 볼까요?",
            "잘 하고 있어요. 다음으로 넘어갈게요.",
            "좋아요, 현재에 잘 집중하고 계세요."
        ]

        ack = random.choice(acknowledgments)

        # 마지막 단계 확인
        if session.current_step >= len(exercise.steps):
            return self._complete_session(session_id)

        # 다음 단계
        step = exercise.steps[session.current_step]
        session.current_step += 1

        progress = f"[{session.current_step}/{len(exercise.steps)}]"

        response = f"""{ack}

**{progress}**

{step}"""

        return {
            "response": response,
            "current_step": session.current_step,
            "total_steps": len(exercise.steps),
            "continue_conversation": True
        }

    def _complete_session(self, session_id: str) -> Dict[str, Any]:
        """세션 완료"""
        session = self.active_sessions[session_id]
        exercise = self.exercise_library.get_exercise(session.technique)

        response = f"""🌟 **{exercise.name}**을 완료하셨습니다!

정말 잘 하셨어요. 지금 기분이 어떠세요?

**현재 확인하기:**
• 지금 여기에 있다는 것이 느껴지시나요?
• 아까보다 몸이 좀 더 느껴지시나요?
• 마음이 조금 가라앉았나요?

어떻게 느끼시는지 편하게 말씀해 주세요."""

        # 세션 정리
        del self.active_sessions[session_id]

        return {
            "response": response,
            "session_completed": True,
            "continue_conversation": True
        }

    def _end_session(self, session_id: str, interrupted: bool = False) -> Dict[str, Any]:
        """세션 종료"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

        if interrupted:
            response = """괜찮아요, 필요할 때 다시 해볼 수 있어요.

지금 힘든 것이 있으시면 말씀해 주세요.
저는 계속 여기 있을게요. 💙"""
        else:
            response = "그라운딩을 마쳤습니다. 계속 이야기를 나눠볼까요?"

        return {
            "response": response,
            "session_ended": True,
            "interrupted": interrupted,
            "continue_conversation": True
        }

    def get_emergency_grounding(self) -> str:
        """긴급 그라운딩 가이드"""
        return """🆘 **긴급 그라운딩**

지금 바로 따라해 보세요:

1. 👀 **보세요**: 주변에서 5가지 물건을 찾아 이름을 말하세요
2. 👂 **들으세요**: 3가지 소리를 찾아보세요
3. 🦶 **느끼세요**: 발바닥이 바닥에 닿는 것을 느끼세요
4. 🫁 **숨쉬세요**: 4초 들이쉬고, 4초 내쉬세요
5. 🗣️ **말하세요**: "나는 지금 안전하다"를 3번 말하세요

**지금 여기에 있습니다. 당신은 안전합니다.** 💙"""

    def list_techniques(self) -> List[Dict]:
        """사용 가능한 그라운딩 기법 목록"""
        techniques = []
        for grounding_type, exercise in self.exercise_library.exercises.items():
            techniques.append({
                "type": grounding_type.value,
                "name": exercise.name,
                "description": exercise.description,
                "target_symptoms": exercise.target_symptoms,
                "duration": exercise.duration_minutes,
                "requires_objects": exercise.requires_objects
            })
        return techniques


# 사용 예시
if __name__ == "__main__":
    system = IntegratedGroundingChat()

    # 해리 감지 테스트
    result = system.process_message(
        "session_1",
        "현실감이 없어요... 마치 꿈속에 있는 것 같고 내 몸이 내 것 같지 않아요"
    )
    print("=== 그라운딩 제안 ===")
    print(result["response"])

    # 긴급 그라운딩
    print("\n=== 긴급 그라운딩 ===")
    print(system.get_emergency_grounding())

    # 기법 목록
    print("\n=== 사용 가능한 기법 ===")
    for technique in system.list_techniques():
        print(f"- {technique['name']}: {technique['description'][:50]}...")
