# -*- coding: utf-8 -*-
"""
호흡 및 이완 훈련 모듈 (Breathing & Relaxation Training Module)

채팅 상담 중 불안, 스트레스, 공황 상태에서 즉각적인 안정화를 위한
호흡 및 이완 기법을 통합하여 제공합니다.

Author: MindVridge AI Team
Version: 1.0.0
"""

import json
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path


class BreathingTechnique(Enum):
    """호흡 기법 종류"""
    BOX_BREATHING = "box_breathing"           # 박스 호흡 (4-4-4-4)
    BREATHING_478 = "breathing_478"           # 4-7-8 호흡
    DIAPHRAGMATIC = "diaphragmatic"           # 복식 호흡
    PURSED_LIP = "pursed_lip"                 # 입술 오므리기 호흡
    ALTERNATE_NOSTRIL = "alternate_nostril"   # 교대 비공 호흡
    CALM_BREATHING = "calm_breathing"         # 차분한 호흡 (단순)


class RelaxationTechnique(Enum):
    """이완 기법 종류"""
    PMR = "pmr"                               # 점진적 근육 이완
    BODY_SCAN = "body_scan"                   # 바디 스캔
    AUTOGENIC = "autogenic"                   # 자율 훈련
    VISUALIZATION = "visualization"           # 시각화 이완
    QUICK_RELEASE = "quick_release"           # 빠른 긴장 해소


class SessionPhase(Enum):
    """세션 단계"""
    INTRODUCTION = "introduction"
    PREPARATION = "preparation"
    PRACTICE = "practice"
    INTEGRATION = "integration"
    CLOSING = "closing"


@dataclass
class BreathingStep:
    """호흡 단계"""
    action: str           # 들숨, 멈춤, 날숨
    duration: int         # 초
    instruction: str      # 한국어 안내
    visual_cue: str       # 시각적 표시


@dataclass
class BreathingExercise:
    """호흡 운동 정의"""
    technique: BreathingTechnique
    name: str
    description: str
    benefits: List[str]
    suitable_for: List[str]          # 적합한 상황
    contraindications: List[str]     # 주의사항
    steps: List[BreathingStep]
    cycles: int = 4
    difficulty: str = "easy"


@dataclass
class RelaxationExercise:
    """이완 운동 정의"""
    technique: RelaxationTechnique
    name: str
    description: str
    duration_minutes: int
    body_parts: List[str]
    instructions: List[str]
    audio_cues: List[str]            # 음성 안내 스크립트


@dataclass
class BreathingSession:
    """호흡 세션 상태"""
    session_id: str
    user_id: str
    technique: BreathingTechnique
    phase: SessionPhase = SessionPhase.INTRODUCTION
    current_cycle: int = 0
    current_step: int = 0
    started_at: datetime = field(default_factory=datetime.now)
    completed_cycles: int = 0
    user_feedback: Dict[str, Any] = field(default_factory=dict)
    interruptions: int = 0


class BreathingTriggerDetector:
    """호흡 훈련 필요 상황 감지"""

    def __init__(self):
        self.anxiety_keywords = [
            "불안", "긴장", "떨려", "심장이 빨리", "가슴이 답답",
            "숨이 막", "호흡이 가빠", "과호흡", "두근두근", "조마조마",
            "초조", "안절부절", "손이 떨", "식은땀", "어지러"
        ]

        self.panic_keywords = [
            "공황", "panic", "죽을 것 같", "미칠 것 같", "숨을 못",
            "심장마비", "정신을 잃을", "제어가 안", "무서워"
        ]

        self.stress_keywords = [
            "스트레스", "지쳤", "힘들", "압박", "부담", "짜증",
            "화가 나", "열받", "못 참겠", "터질 것 같"
        ]

        self.sleep_keywords = [
            "잠이 안", "불면", "뒤척", "새벽에 깨", "잠들기 어려",
            "수면", "잠을 못"
        ]

    def detect(self, message: str, emotion_context: Optional[Dict] = None) -> Dict[str, Any]:
        """호흡 훈련 필요 상황 감지"""
        message_lower = message.lower()

        triggers = {
            "anxiety": self._check_keywords(message_lower, self.anxiety_keywords),
            "panic": self._check_keywords(message_lower, self.panic_keywords),
            "stress": self._check_keywords(message_lower, self.stress_keywords),
            "sleep": self._check_keywords(message_lower, self.sleep_keywords)
        }

        # 감정 컨텍스트 확인
        if emotion_context:
            anxiety_level = emotion_context.get("anxiety", 0)
            stress_level = emotion_context.get("stress", 0)

            if anxiety_level > 0.7:
                triggers["anxiety"]["detected"] = True
                triggers["anxiety"]["confidence"] = max(triggers["anxiety"]["confidence"], anxiety_level)
            if stress_level > 0.7:
                triggers["stress"]["detected"] = True
                triggers["stress"]["confidence"] = max(triggers["stress"]["confidence"], stress_level)

        # 우선순위 결정
        priority = None
        if triggers["panic"]["detected"]:
            priority = "panic"
        elif triggers["anxiety"]["detected"]:
            priority = "anxiety"
        elif triggers["stress"]["detected"]:
            priority = "stress"
        elif triggers["sleep"]["detected"]:
            priority = "sleep"

        return {
            "should_suggest": any(t["detected"] for t in triggers.values()),
            "triggers": triggers,
            "priority": priority,
            "recommended_technique": self._recommend_technique(priority)
        }

    def _check_keywords(self, message: str, keywords: List[str]) -> Dict[str, Any]:
        """키워드 매칭 확인"""
        matches = [kw for kw in keywords if kw in message]
        return {
            "detected": len(matches) > 0,
            "matches": matches,
            "confidence": min(len(matches) * 0.3, 1.0)
        }

    def _recommend_technique(self, priority: Optional[str]) -> Optional[BreathingTechnique]:
        """상황에 맞는 기법 추천"""
        recommendations = {
            "panic": BreathingTechnique.CALM_BREATHING,      # 단순하고 빠른 안정
            "anxiety": BreathingTechnique.BOX_BREATHING,     # 균형 잡힌 호흡
            "stress": BreathingTechnique.BREATHING_478,      # 이완 효과
            "sleep": BreathingTechnique.BREATHING_478        # 수면 유도
        }
        return recommendations.get(priority)


class BreathingExerciseLibrary:
    """호흡 운동 라이브러리"""

    def __init__(self):
        self.exercises = self._initialize_exercises()

    def _initialize_exercises(self) -> Dict[BreathingTechnique, BreathingExercise]:
        """호흡 운동 초기화"""
        return {
            BreathingTechnique.BOX_BREATHING: BreathingExercise(
                technique=BreathingTechnique.BOX_BREATHING,
                name="박스 호흡",
                description="4-4-4-4 리듬의 균형 잡힌 호흡법입니다. 네이비 실에서도 사용하는 스트레스 관리 기법입니다.",
                benefits=[
                    "스트레스와 불안 감소",
                    "집중력 향상",
                    "자율신경계 균형",
                    "혈압 안정화"
                ],
                suitable_for=["일상적 스트레스", "불안", "집중력 필요 시", "업무 전"],
                contraindications=["호흡기 질환자는 주의"],
                steps=[
                    BreathingStep("들숨", 4, "코로 천천히 숨을 들이마시세요", "🫁 ━━━━"),
                    BreathingStep("멈춤", 4, "숨을 잠시 멈추세요", "⏸️ ━━━━"),
                    BreathingStep("날숨", 4, "입으로 천천히 내쉬세요", "💨 ━━━━"),
                    BreathingStep("멈춤", 4, "잠시 쉬어가세요", "🔄 ━━━━")
                ],
                cycles=4,
                difficulty="easy"
            ),

            BreathingTechnique.BREATHING_478: BreathingExercise(
                technique=BreathingTechnique.BREATHING_478,
                name="4-7-8 호흡",
                description="앤드류 와일 박사가 개발한 자연적 이완 호흡법입니다. 불면증과 불안에 특히 효과적입니다.",
                benefits=[
                    "깊은 이완 유도",
                    "수면 개선",
                    "불안 감소",
                    "분노 조절"
                ],
                suitable_for=["불면증", "심한 불안", "분노 조절", "취침 전"],
                contraindications=["심장 질환자는 의사와 상담 후 진행"],
                steps=[
                    BreathingStep("들숨", 4, "코로 조용히 숨을 들이마시세요", "🫁 ━━━━"),
                    BreathingStep("멈춤", 7, "숨을 참으세요", "⏸️ ━━━━━━━"),
                    BreathingStep("날숨", 8, "'후~' 소리를 내며 입으로 완전히 내쉬세요", "💨 ━━━━━━━━")
                ],
                cycles=4,
                difficulty="medium"
            ),

            BreathingTechnique.DIAPHRAGMATIC: BreathingExercise(
                technique=BreathingTechnique.DIAPHRAGMATIC,
                name="복식 호흡",
                description="횡격막을 사용하는 깊은 호흡법입니다. 가장 기본적이고 효과적인 호흡법입니다.",
                benefits=[
                    "산소 공급 증가",
                    "부교감신경 활성화",
                    "근육 긴장 완화",
                    "에너지 증진"
                ],
                suitable_for=["일상적 사용", "초보자", "모든 상황"],
                contraindications=[],
                steps=[
                    BreathingStep("준비", 0, "한 손은 가슴에, 다른 손은 배에 올려두세요", "🤲"),
                    BreathingStep("들숨", 4, "배가 부풀어 오르도록 코로 깊이 들이마시세요", "🫁 배↑"),
                    BreathingStep("날숨", 6, "배가 들어가도록 천천히 내쉬세요", "💨 배↓")
                ],
                cycles=6,
                difficulty="easy"
            ),

            BreathingTechnique.CALM_BREATHING: BreathingExercise(
                technique=BreathingTechnique.CALM_BREATHING,
                name="진정 호흡",
                description="공황 발작 시 사용하는 단순하고 효과적인 호흡법입니다.",
                benefits=[
                    "빠른 진정 효과",
                    "과호흡 방지",
                    "공황 발작 완화"
                ],
                suitable_for=["공황 발작", "급성 불안", "과호흡"],
                contraindications=[],
                steps=[
                    BreathingStep("들숨", 3, "천천히, 부드럽게 숨을 들이마시세요", "🫁 ━━━"),
                    BreathingStep("날숨", 3, "천천히, 부드럽게 내쉬세요", "💨 ━━━")
                ],
                cycles=10,
                difficulty="very_easy"
            ),

            BreathingTechnique.PURSED_LIP: BreathingExercise(
                technique=BreathingTechnique.PURSED_LIP,
                name="입술 오므리기 호흡",
                description="촛불을 끄듯이 입술을 오므리고 천천히 내쉬는 호흡법입니다.",
                benefits=[
                    "호흡 조절력 향상",
                    "폐 기능 개선",
                    "긴장 완화"
                ],
                suitable_for=["호흡 곤란", "스트레스", "운동 후"],
                contraindications=[],
                steps=[
                    BreathingStep("들숨", 2, "코로 숨을 들이마시세요", "👃 ━━"),
                    BreathingStep("날숨", 4, "입술을 촛불 끄듯이 오므리고 천천히 내쉬세요", "😗💨 ━━━━")
                ],
                cycles=5,
                difficulty="easy"
            ),

            BreathingTechnique.ALTERNATE_NOSTRIL: BreathingExercise(
                technique=BreathingTechnique.ALTERNATE_NOSTRIL,
                name="교대 비공 호흡",
                description="요가에서 유래한 호흡법으로, 좌우 뇌의 균형을 맞춥니다.",
                benefits=[
                    "마음의 균형",
                    "집중력 향상",
                    "스트레스 감소",
                    "에너지 균형"
                ],
                suitable_for=["명상 전", "집중력 필요 시", "에너지 균형"],
                contraindications=["코막힘 시 피하기"],
                steps=[
                    BreathingStep("준비", 0, "오른손 엄지로 오른쪽 코를 막으세요", "👆👃"),
                    BreathingStep("들숨", 4, "왼쪽 코로 숨을 들이마시세요", "🫁← ━━━━"),
                    BreathingStep("전환", 0, "왼쪽 코를 막고 오른쪽 코를 열어주세요", "🔄"),
                    BreathingStep("날숨", 4, "오른쪽 코로 내쉬세요", "💨→ ━━━━"),
                    BreathingStep("들숨", 4, "오른쪽 코로 들이마시세요", "🫁→ ━━━━"),
                    BreathingStep("전환", 0, "오른쪽 코를 막고 왼쪽 코를 열어주세요", "🔄"),
                    BreathingStep("날숨", 4, "왼쪽 코로 내쉬세요", "💨← ━━━━")
                ],
                cycles=3,
                difficulty="medium"
            )
        }

    def get_exercise(self, technique: BreathingTechnique) -> BreathingExercise:
        """특정 호흡 운동 반환"""
        return self.exercises.get(technique)

    def get_suitable_exercises(self, situation: str) -> List[BreathingExercise]:
        """상황에 맞는 호흡 운동 목록"""
        suitable = []
        for exercise in self.exercises.values():
            if any(situation in s for s in exercise.suitable_for):
                suitable.append(exercise)
        return suitable


class RelaxationExerciseLibrary:
    """이완 운동 라이브러리"""

    def __init__(self):
        self.exercises = self._initialize_exercises()

    def _initialize_exercises(self) -> Dict[RelaxationTechnique, RelaxationExercise]:
        """이완 운동 초기화"""
        return {
            RelaxationTechnique.PMR: RelaxationExercise(
                technique=RelaxationTechnique.PMR,
                name="점진적 근육 이완",
                description="에드먼드 제이콥슨이 개발한 기법으로, 근육을 긴장시켰다가 이완하며 몸 전체의 긴장을 풀어줍니다.",
                duration_minutes=15,
                body_parts=["발", "종아리", "허벅지", "복부", "가슴", "손", "팔", "어깨", "목", "얼굴"],
                instructions=[
                    "편안한 자세로 앉거나 누우세요.",
                    "눈을 감고 몇 번 깊은 호흡을 합니다.",
                    "발부터 시작합니다. 발가락에 힘을 주어 5초간 긴장시키세요.",
                    "힘을 빼고 10초간 이완하며 긴장이 풀리는 것을 느끼세요.",
                    "이 과정을 각 신체 부위에서 반복합니다."
                ],
                audio_cues=[
                    "이제 발에 집중해 볼까요? 발가락을 움츠리며 긴장을 주세요...",
                    "좋습니다. 이제 힘을 빼세요. 긴장이 녹아내리는 것을 느껴보세요...",
                    "종아리로 올라갑니다. 발끝을 당기며 종아리에 힘을 주세요...",
                    "네, 이제 놓아주세요. 따뜻하고 무거운 느낌이 퍼져나갑니다..."
                ]
            ),

            RelaxationTechnique.BODY_SCAN: RelaxationExercise(
                technique=RelaxationTechnique.BODY_SCAN,
                name="바디 스캔",
                description="몸의 각 부위에 주의를 기울이며 긴장을 알아차리고 이완하는 마음챙김 기법입니다.",
                duration_minutes=10,
                body_parts=["발", "다리", "골반", "복부", "가슴", "등", "손", "팔", "어깨", "목", "얼굴", "머리"],
                instructions=[
                    "편안하게 누워서 눈을 감으세요.",
                    "발끝부터 시작하여 천천히 위로 올라가며 주의를 기울입니다.",
                    "각 부위에서 어떤 감각이 느껴지는지 관찰하세요.",
                    "긴장이 느껴지면 호흡과 함께 내보내세요.",
                    "판단 없이 있는 그대로 느끼세요."
                ],
                audio_cues=[
                    "발끝에 주의를 가져가세요. 어떤 감각이 느껴지나요?",
                    "따뜻함, 시원함, 아무것도 느껴지지 않아도 괜찮습니다.",
                    "천천히 발목으로, 종아리로 주의를 올려보세요...",
                    "그저 관찰하세요. 바꾸려 하지 않아도 됩니다..."
                ]
            ),

            RelaxationTechnique.AUTOGENIC: RelaxationExercise(
                technique=RelaxationTechnique.AUTOGENIC,
                name="자율 훈련",
                description="자기 암시를 통해 신체의 이완 반응을 유도하는 기법입니다.",
                duration_minutes=10,
                body_parts=["팔", "다리", "심장", "호흡", "복부", "이마"],
                instructions=[
                    "편안한 자세를 취하고 눈을 감으세요.",
                    "'오른팔이 무겁다'를 천천히 되뇌세요.",
                    "실제로 팔이 무거워지는 것을 상상하세요.",
                    "각 신체 부위에 대해 무거움, 따뜻함을 암시합니다."
                ],
                audio_cues=[
                    "오른팔이 무겁습니다... 점점 더 무거워집니다...",
                    "오른팔이 따뜻합니다... 따뜻한 온기가 퍼집니다...",
                    "심장이 규칙적으로 뜁니다... 편안하고 안정적입니다...",
                    "호흡이 자연스럽게 흐릅니다... 이완되고 있습니다..."
                ]
            ),

            RelaxationTechnique.VISUALIZATION: RelaxationExercise(
                technique=RelaxationTechnique.VISUALIZATION,
                name="시각화 이완",
                description="평화로운 장면을 상상하며 마음과 몸을 이완시키는 기법입니다.",
                duration_minutes=8,
                body_parts=[],
                instructions=[
                    "눈을 감고 몇 번 깊은 호흡을 하세요.",
                    "평화로운 장소를 떠올려 보세요. 해변, 숲, 초원 등",
                    "그 장소의 색깔, 소리, 냄새, 촉감을 상상하세요.",
                    "그 공간에서 완전히 안전하고 평화로움을 느끼세요.",
                    "충분히 머무른 후 천천히 현재로 돌아오세요."
                ],
                audio_cues=[
                    "평화로운 해변에 있다고 상상해 보세요...",
                    "부드러운 모래 위에 누워 있습니다. 따뜻한 햇살이 내리쬐고...",
                    "파도 소리가 들립니다... 규칙적이고 평화로운...",
                    "바다 내음이 느껴집니다... 시원하고 상쾌한...",
                    "온몸이 이완되고 마음이 평화로워집니다..."
                ]
            ),

            RelaxationTechnique.QUICK_RELEASE: RelaxationExercise(
                technique=RelaxationTechnique.QUICK_RELEASE,
                name="빠른 긴장 해소",
                description="바쁜 일상에서 1-2분 내에 빠르게 긴장을 풀 수 있는 기법입니다.",
                duration_minutes=2,
                body_parts=["어깨", "얼굴", "손"],
                instructions=[
                    "어깨를 귀 쪽으로 올렸다가 떨어뜨리세요. 3회 반복",
                    "얼굴 전체에 힘을 주어 구기듯이 하다가 풀어주세요.",
                    "양손을 꽉 쥐었다가 펴면서 긴장을 내보내세요.",
                    "깊은 숨을 한 번 쉬고 '후~' 하고 내쉬세요."
                ],
                audio_cues=[
                    "어깨를 귀까지 올려보세요... 쭉... 그리고 떨어뜨리세요!",
                    "얼굴을 구기세요... 더 구기세요... 그리고 풀어주세요!",
                    "손을 꽉 쥐세요... 더 세게... 그리고 펴세요!",
                    "좋습니다. 긴장이 빠져나갔습니다."
                ]
            )
        }

    def get_exercise(self, technique: RelaxationTechnique) -> RelaxationExercise:
        """특정 이완 운동 반환"""
        return self.exercises.get(technique)


class IntegratedBreathingChat:
    """채팅 통합형 호흡/이완 훈련 시스템"""

    def __init__(self):
        self.trigger_detector = BreathingTriggerDetector()
        self.breathing_library = BreathingExerciseLibrary()
        self.relaxation_library = RelaxationExerciseLibrary()
        self.active_sessions: Dict[str, BreathingSession] = {}

    def process_message(
        self,
        session_id: str,
        user_message: str,
        emotion_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        사용자 메시지 처리 및 호흡 훈련 통합

        Returns:
            Dict with response, suggestions, and session state
        """
        # 진행 중인 세션이 있는지 확인
        if session_id in self.active_sessions:
            return self._handle_active_session(session_id, user_message)

        # 호흡 훈련 필요 상황 감지
        trigger_result = self.trigger_detector.detect(user_message, emotion_context)

        if trigger_result["should_suggest"]:
            return self._suggest_breathing_exercise(
                session_id,
                trigger_result
            )

        return {
            "breathing_suggested": False,
            "response": None,
            "continue_conversation": True
        }

    def _suggest_breathing_exercise(
        self,
        session_id: str,
        trigger_result: Dict
    ) -> Dict[str, Any]:
        """호흡 운동 제안"""
        priority = trigger_result["priority"]
        technique = trigger_result["recommended_technique"]
        exercise = self.breathing_library.get_exercise(technique)

        # 상황에 맞는 공감 + 제안 메시지
        empathy_messages = {
            "panic": "지금 많이 힘드시겠어요. 먼저 함께 호흡을 해볼까요? 제가 옆에서 안내해 드릴게요.",
            "anxiety": "불안한 마음이 느껴지시는군요. 잠시 호흡을 가다듬으면 도움이 될 수 있어요.",
            "stress": "스트레스가 많이 쌓이셨네요. 잠깐 호흡 운동으로 마음을 가라앉혀 볼까요?",
            "sleep": "잠들기가 어려우시군요. 4-7-8 호흡법이 수면에 도움이 될 수 있어요."
        }

        response = f"""{empathy_messages.get(priority, "잠시 호흡 운동을 해보시는 건 어떨까요?")}

💨 **{exercise.name}** 을 추천드려요.

{exercise.description}

✨ **효과**: {', '.join(exercise.benefits[:3])}

함께 해보시겠어요? (네/괜찮아요 중 선택해 주세요)"""

        return {
            "breathing_suggested": True,
            "technique": technique.value,
            "response": response,
            "trigger_type": priority,
            "continue_conversation": True,
            "awaiting_acceptance": True
        }

    def start_exercise(
        self,
        session_id: str,
        user_id: str,
        technique: BreathingTechnique
    ) -> Dict[str, Any]:
        """호흡 운동 시작"""
        exercise = self.breathing_library.get_exercise(technique)

        # 세션 생성
        self.active_sessions[session_id] = BreathingSession(
            session_id=session_id,
            user_id=user_id,
            technique=technique,
            phase=SessionPhase.PREPARATION
        )

        # 시작 안내
        intro = f"""좋아요, 함께 **{exercise.name}**을 시작해 볼게요! 🌬️

**준비하기**
• 편안한 자세로 앉거나 누우세요
• 가능하면 조용한 곳을 찾아주세요
• 몸을 조금 움직여서 긴장을 풀어주세요

준비가 되시면 '시작'이라고 말씀해 주세요."""

        return {
            "session_started": True,
            "response": intro,
            "phase": "preparation",
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

        exercise = self.breathing_library.get_exercise(session.technique)

        # 단계별 처리
        if session.phase == SessionPhase.PREPARATION:
            if any(word in message_lower for word in ["시작", "준비", "네", "응"]):
                session.phase = SessionPhase.PRACTICE
                session.current_cycle = 1
                session.current_step = 0
                return self._get_next_instruction(session_id)

        elif session.phase == SessionPhase.PRACTICE:
            # 다음 단계로 진행
            return self._get_next_instruction(session_id)

        elif session.phase == SessionPhase.INTEGRATION:
            return self._complete_session(session_id)

        return {
            "response": "천천히 진행해 주세요. 준비되시면 말씀해 주세요.",
            "continue_conversation": True
        }

    def _get_next_instruction(self, session_id: str) -> Dict[str, Any]:
        """다음 호흡 안내 반환"""
        session = self.active_sessions[session_id]
        exercise = self.breathing_library.get_exercise(session.technique)

        # 모든 사이클 완료 확인
        if session.current_cycle > exercise.cycles:
            session.phase = SessionPhase.INTEGRATION
            return self._integration_phase(session_id)

        # 현재 단계
        if session.current_step >= len(exercise.steps):
            session.current_step = 0
            session.current_cycle += 1
            session.completed_cycles += 1

            if session.current_cycle > exercise.cycles:
                session.phase = SessionPhase.INTEGRATION
                return self._integration_phase(session_id)

        step = exercise.steps[session.current_step]
        session.current_step += 1

        # 시각적 타이머 생성
        visual_timer = self._create_visual_timer(step)

        response = f"""**[{session.current_cycle}/{exercise.cycles} 사이클]**

{step.visual_cue}

**{step.action}** ({step.duration}초)
{step.instruction}

{visual_timer}

(다음 단계로 넘어가려면 아무 말씀이나 해주세요)"""

        return {
            "response": response,
            "phase": "practice",
            "current_cycle": session.current_cycle,
            "current_step": session.current_step,
            "step_duration": step.duration,
            "continue_conversation": True
        }

    def _create_visual_timer(self, step: BreathingStep) -> str:
        """시각적 타이머 생성"""
        if step.duration == 0:
            return ""

        blocks = "█" * step.duration
        return f"`{blocks}` {step.duration}초"

    def _integration_phase(self, session_id: str) -> Dict[str, Any]:
        """마무리 통합 단계"""
        session = self.active_sessions[session_id]
        exercise = self.breathing_library.get_exercise(session.technique)

        response = f"""🎉 **{exercise.name}** {session.completed_cycles}사이클을 완료하셨습니다!

**잠시 자신의 상태를 느껴보세요:**
• 호흡이 어떻게 느껴지나요?
• 몸의 긴장이 조금 풀렸나요?
• 마음은 조금 가라앉았나요?

느끼시는 것을 편하게 말씀해 주세요."""

        return {
            "response": response,
            "phase": "integration",
            "completed_cycles": session.completed_cycles,
            "continue_conversation": True
        }

    def _complete_session(self, session_id: str) -> Dict[str, Any]:
        """세션 완료 처리"""
        session = self.active_sessions[session_id]

        response = """호흡 운동을 잘 마치셨어요. 💙

이 기법은 언제든 필요할 때 혼자서도 할 수 있어요.
스트레스를 느끼거나 마음이 복잡할 때 잠시 멈추고 호흡에 집중해 보세요.

이제 계속 이야기를 나눠볼까요?"""

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
            session = self.active_sessions[session_id]
            del self.active_sessions[session_id]

        if interrupted:
            response = """괜찮아요, 언제든 다시 시도해 볼 수 있어요.
지금 하고 싶은 이야기가 있으시면 편하게 말씀해 주세요."""
        else:
            response = "호흡 운동을 마쳤습니다. 계속 이야기를 나눠볼까요?"

        return {
            "response": response,
            "session_ended": True,
            "interrupted": interrupted,
            "continue_conversation": True
        }

    def get_relaxation_guide(
        self,
        technique: RelaxationTechnique
    ) -> Dict[str, Any]:
        """이완 운동 가이드 반환"""
        exercise = self.relaxation_library.get_exercise(technique)

        if not exercise:
            return {"error": "이완 기법을 찾을 수 없습니다."}

        guide = f"""🧘 **{exercise.name}**

{exercise.description}

⏱️ **소요 시간**: 약 {exercise.duration_minutes}분

**진행 방법**:
"""
        for i, instruction in enumerate(exercise.instructions, 1):
            guide += f"{i}. {instruction}\n"

        if exercise.body_parts:
            guide += f"\n**다루는 부위**: {' → '.join(exercise.body_parts)}"

        return {
            "technique": technique.value,
            "name": exercise.name,
            "guide": guide,
            "duration": exercise.duration_minutes,
            "audio_cues": exercise.audio_cues
        }

    def list_available_techniques(self) -> Dict[str, List[Dict]]:
        """사용 가능한 모든 기법 목록"""
        breathing = []
        for technique, exercise in self.breathing_library.exercises.items():
            breathing.append({
                "technique": technique.value,
                "name": exercise.name,
                "description": exercise.description,
                "difficulty": exercise.difficulty,
                "suitable_for": exercise.suitable_for
            })

        relaxation = []
        for technique, exercise in self.relaxation_library.exercises.items():
            relaxation.append({
                "technique": technique.value,
                "name": exercise.name,
                "description": exercise.description,
                "duration_minutes": exercise.duration_minutes
            })

        return {
            "breathing_techniques": breathing,
            "relaxation_techniques": relaxation
        }


# 사용 예시
if __name__ == "__main__":
    system = IntegratedBreathingChat()

    # 불안 감지 테스트
    result = system.process_message(
        "session_1",
        "가슴이 너무 답답하고 숨이 잘 안 쉬어져요... 불안해서 미칠 것 같아요",
        {"anxiety": 0.8}
    )
    print("=== 호흡 운동 제안 ===")
    print(result["response"])

    # 운동 시작
    start_result = system.start_exercise(
        "session_1",
        "user_1",
        BreathingTechnique.BOX_BREATHING
    )
    print("\n=== 운동 시작 ===")
    print(start_result["response"])

    # 연습 진행
    practice_result = system._handle_active_session("session_1", "시작할게요")
    print("\n=== 연습 ===")
    print(practice_result["response"])

    # 기법 목록
    print("\n=== 사용 가능한 기법 ===")
    techniques = system.list_available_techniques()
    for t in techniques["breathing_techniques"]:
        print(f"- {t['name']}: {t['description'][:50]}...")
