# -*- coding: utf-8 -*-
"""
통합 치료적 개입 시스템 (Integrated Therapeutic Interventions System)

채팅 상담 중 다양한 치료적 개입(호흡, 그라운딩, CBT, 저널링, 마음챙김,
행동활성화, 음악치료, 그림치료)을 통합하여 자연스럽게 제공합니다.

Author: MindVridge AI Team
Version: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
import re

# 각 모듈 임포트
try:
    from breathing_relaxation import IntegratedBreathingChat, BreathingTechnique
    BREATHING_AVAILABLE = True
except ImportError:
    BREATHING_AVAILABLE = False

try:
    from grounding_techniques import IntegratedGroundingChat, GroundingType
    GROUNDING_AVAILABLE = True
except ImportError:
    GROUNDING_AVAILABLE = False

try:
    from cbt_thought_record import IntegratedCBTChat
    CBT_AVAILABLE = True
except ImportError:
    CBT_AVAILABLE = False

try:
    from journaling_therapy import IntegratedJournalingChat, JournalingType
    JOURNALING_AVAILABLE = True
except ImportError:
    JOURNALING_AVAILABLE = False

try:
    from mindfulness_meditation import IntegratedMindfulnessChat, MeditationType
    MINDFULNESS_AVAILABLE = True
except ImportError:
    MINDFULNESS_AVAILABLE = False

try:
    from behavioral_activation import IntegratedBehavioralActivation
    BA_AVAILABLE = True
except ImportError:
    BA_AVAILABLE = False

try:
    from music_therapy import IntegratedMusicTherapyChat, MusicMood
    MUSIC_AVAILABLE = True
except ImportError:
    MUSIC_AVAILABLE = False

try:
    from integrated_art_chat import IntegratedArtTherapyChat
    ART_AVAILABLE = True
except ImportError:
    ART_AVAILABLE = False


class InterventionType(Enum):
    """개입 유형"""
    BREATHING = "breathing"
    GROUNDING = "grounding"
    CBT = "cbt"
    JOURNALING = "journaling"
    MINDFULNESS = "mindfulness"
    BEHAVIORAL_ACTIVATION = "behavioral_activation"
    MUSIC = "music"
    ART = "art"


class EmotionalState(Enum):
    """감정 상태"""
    PANIC = "panic"              # 공황/급성 불안
    HIGH_ANXIETY = "high_anxiety"     # 높은 불안
    DISSOCIATION = "dissociation"     # 해리
    DEPRESSION = "depression"         # 우울
    ANGER = "anger"                   # 분노
    STRESS = "stress"                 # 스트레스
    RUMINATION = "rumination"         # 반추
    OVERWHELM = "overwhelm"           # 압도
    LOW_ENERGY = "low_energy"         # 낮은 에너지
    EMOTIONAL_DYSREGULATION = "dysregulation"  # 감정 조절 어려움
    GRIEF = "grief"                   # 슬픔/상실
    TRAUMA_RESPONSE = "trauma"        # 트라우마 반응


@dataclass
class InterventionPriority:
    """개입 우선순위"""
    intervention_type: InterventionType
    priority_score: float  # 0-1
    rationale: str
    estimated_duration: int  # 분


@dataclass
class InterventionSession:
    """통합 개입 세션"""
    session_id: str
    user_id: str
    active_intervention: Optional[InterventionType] = None
    emotional_state: Optional[EmotionalState] = None
    intervention_history: List[Dict] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)


class EmotionalStateDetector:
    """감정 상태 감지기"""

    def __init__(self):
        self.state_patterns = {
            EmotionalState.PANIC: {
                "keywords": ["공황", "숨이 안 쉬어", "죽을 것 같", "심장이", "과호흡"],
                "weight": 1.0,  # 최고 우선순위
                "urgent": True
            },
            EmotionalState.DISSOCIATION: {
                "keywords": ["현실감이 없", "내 몸이 아닌 것 같", "멍해", "꿈 같", "비현실"],
                "weight": 0.95,
                "urgent": True
            },
            EmotionalState.TRAUMA_RESPONSE: {
                "keywords": ["플래시백", "그때 일이 떠올", "악몽", "트라우마"],
                "weight": 0.9,
                "urgent": True
            },
            EmotionalState.HIGH_ANXIETY: {
                "keywords": ["너무 불안", "긴장", "두근두근", "초조", "불안해서"],
                "weight": 0.8,
                "urgent": False
            },
            EmotionalState.ANGER: {
                "keywords": ["화가 나", "짜증", "미치겠", "열받", "답답해서"],
                "weight": 0.7,
                "urgent": False
            },
            EmotionalState.OVERWHELM: {
                "keywords": ["감당이 안", "버거워", "압도", "너무 많아", "미칠 것 같"],
                "weight": 0.7,
                "urgent": False
            },
            EmotionalState.DEPRESSION: {
                "keywords": ["우울", "의욕이 없", "무기력", "슬퍼", "삶이 의미없"],
                "weight": 0.6,
                "urgent": False
            },
            EmotionalState.RUMINATION: {
                "keywords": ["계속 생각", "머릿속에서 떠나지 않", "자꾸 되뇌", "멈출 수가 없"],
                "weight": 0.6,
                "urgent": False
            },
            EmotionalState.LOW_ENERGY: {
                "keywords": ["기운이 없", "피곤", "힘들어", "움직이기 싫", "누워만"],
                "weight": 0.5,
                "urgent": False
            },
            EmotionalState.STRESS: {
                "keywords": ["스트레스", "힘들", "지쳤", "쉬고 싶"],
                "weight": 0.5,
                "urgent": False
            },
            EmotionalState.GRIEF: {
                "keywords": ["잃었", "그리워", "보고 싶", "슬퍼", "상실"],
                "weight": 0.5,
                "urgent": False
            },
            EmotionalState.EMOTIONAL_DYSREGULATION: {
                "keywords": ["감정 조절이 안", "울다가 웃다가", "감정 기복", "폭발"],
                "weight": 0.6,
                "urgent": False
            }
        }

    def detect(self, message: str) -> Dict[str, Any]:
        """감정 상태 감지"""
        message_lower = message.lower()
        detected_states = []

        for state, config in self.state_patterns.items():
            matches = [kw for kw in config["keywords"] if kw in message_lower]
            if matches:
                score = min(len(matches) * 0.3 * config["weight"], 1.0)
                detected_states.append({
                    "state": state,
                    "score": score,
                    "urgent": config["urgent"],
                    "matches": matches
                })

        # 점수순 정렬
        detected_states.sort(key=lambda x: x["score"], reverse=True)

        primary_state = detected_states[0]["state"] if detected_states else None
        is_urgent = detected_states[0]["urgent"] if detected_states else False

        return {
            "primary_state": primary_state,
            "all_states": detected_states,
            "is_urgent": is_urgent,
            "confidence": detected_states[0]["score"] if detected_states else 0
        }


class InterventionSelector:
    """개입 선택기"""

    def __init__(self):
        # 감정 상태별 권장 개입
        self.intervention_map = {
            EmotionalState.PANIC: [
                (InterventionType.BREATHING, 1.0, "즉각적 안정화"),
                (InterventionType.GROUNDING, 0.9, "현재 집중"),
            ],
            EmotionalState.DISSOCIATION: [
                (InterventionType.GROUNDING, 1.0, "현실 연결"),
                (InterventionType.BREATHING, 0.8, "신체 인식"),
            ],
            EmotionalState.TRAUMA_RESPONSE: [
                (InterventionType.GROUNDING, 1.0, "안전감 회복"),
                (InterventionType.BREATHING, 0.9, "진정"),
            ],
            EmotionalState.HIGH_ANXIETY: [
                (InterventionType.BREATHING, 0.9, "생리적 안정"),
                (InterventionType.MINDFULNESS, 0.8, "현재 인식"),
                (InterventionType.CBT, 0.7, "불안 사고 검토"),
            ],
            EmotionalState.ANGER: [
                (InterventionType.BREATHING, 0.9, "진정"),
                (InterventionType.MUSIC, 0.7, "감정 표출"),
                (InterventionType.JOURNALING, 0.6, "감정 표현"),
            ],
            EmotionalState.DEPRESSION: [
                (InterventionType.BEHAVIORAL_ACTIVATION, 1.0, "활동 활성화"),
                (InterventionType.JOURNALING, 0.7, "감정 표현"),
                (InterventionType.MUSIC, 0.6, "기분 전환"),
            ],
            EmotionalState.RUMINATION: [
                (InterventionType.CBT, 0.9, "사고 패턴 검토"),
                (InterventionType.MINDFULNESS, 0.8, "생각 관찰"),
                (InterventionType.GROUNDING, 0.6, "현재 집중"),
            ],
            EmotionalState.OVERWHELM: [
                (InterventionType.BREATHING, 0.9, "안정화"),
                (InterventionType.MINDFULNESS, 0.8, "마음 정리"),
                (InterventionType.JOURNALING, 0.6, "정리"),
            ],
            EmotionalState.LOW_ENERGY: [
                (InterventionType.BEHAVIORAL_ACTIVATION, 1.0, "작은 활동"),
                (InterventionType.MUSIC, 0.7, "에너지 충전"),
            ],
            EmotionalState.STRESS: [
                (InterventionType.BREATHING, 0.9, "이완"),
                (InterventionType.MINDFULNESS, 0.8, "마음챙김"),
                (InterventionType.MUSIC, 0.6, "힐링"),
            ],
            EmotionalState.GRIEF: [
                (InterventionType.JOURNALING, 0.9, "감정 표현"),
                (InterventionType.MUSIC, 0.8, "회상/위로"),
                (InterventionType.ART, 0.7, "창의적 표현"),
            ],
            EmotionalState.EMOTIONAL_DYSREGULATION: [
                (InterventionType.GROUNDING, 0.9, "안정화"),
                (InterventionType.BREATHING, 0.8, "조절"),
                (InterventionType.MINDFULNESS, 0.7, "인식"),
            ]
        }

    def get_recommendations(
        self,
        emotional_state: EmotionalState,
        user_preferences: Optional[Dict] = None,
        recent_interventions: Optional[List[InterventionType]] = None
    ) -> List[InterventionPriority]:
        """감정 상태에 맞는 개입 추천"""
        recommendations = []

        interventions = self.intervention_map.get(emotional_state, [])

        for intervention_type, score, rationale in interventions:
            # 사용 가능 여부 확인
            if not self._is_available(intervention_type):
                continue

            # 최근 사용 개입 점수 조정
            if recent_interventions and intervention_type in recent_interventions:
                score *= 0.7  # 다양성을 위해 점수 감소

            # 사용자 선호도 반영
            if user_preferences:
                pref_score = user_preferences.get(intervention_type.value, 1.0)
                score *= pref_score

            # 소요 시간 추정
            duration = self._estimate_duration(intervention_type)

            recommendations.append(InterventionPriority(
                intervention_type=intervention_type,
                priority_score=score,
                rationale=rationale,
                estimated_duration=duration
            ))

        # 점수순 정렬
        recommendations.sort(key=lambda x: x.priority_score, reverse=True)

        return recommendations[:3]  # 상위 3개

    def _is_available(self, intervention_type: InterventionType) -> bool:
        """모듈 사용 가능 여부"""
        availability = {
            InterventionType.BREATHING: BREATHING_AVAILABLE,
            InterventionType.GROUNDING: GROUNDING_AVAILABLE,
            InterventionType.CBT: CBT_AVAILABLE,
            InterventionType.JOURNALING: JOURNALING_AVAILABLE,
            InterventionType.MINDFULNESS: MINDFULNESS_AVAILABLE,
            InterventionType.BEHAVIORAL_ACTIVATION: BA_AVAILABLE,
            InterventionType.MUSIC: MUSIC_AVAILABLE,
            InterventionType.ART: ART_AVAILABLE
        }
        return availability.get(intervention_type, False)

    def _estimate_duration(self, intervention_type: InterventionType) -> int:
        """소요 시간 추정 (분)"""
        durations = {
            InterventionType.BREATHING: 5,
            InterventionType.GROUNDING: 5,
            InterventionType.CBT: 15,
            InterventionType.JOURNALING: 10,
            InterventionType.MINDFULNESS: 7,
            InterventionType.BEHAVIORAL_ACTIVATION: 10,
            InterventionType.MUSIC: 10,
            InterventionType.ART: 15
        }
        return durations.get(intervention_type, 10)


class IntegratedTherapeuticSystem:
    """통합 치료적 개입 시스템"""

    def __init__(self):
        self.state_detector = EmotionalStateDetector()
        self.intervention_selector = InterventionSelector()

        # 각 개입 시스템 초기화
        self.breathing_system = IntegratedBreathingChat() if BREATHING_AVAILABLE else None
        self.grounding_system = IntegratedGroundingChat() if GROUNDING_AVAILABLE else None
        self.cbt_system = IntegratedCBTChat() if CBT_AVAILABLE else None
        self.journaling_system = IntegratedJournalingChat() if JOURNALING_AVAILABLE else None
        self.mindfulness_system = IntegratedMindfulnessChat() if MINDFULNESS_AVAILABLE else None
        self.ba_system = IntegratedBehavioralActivation() if BA_AVAILABLE else None
        self.music_system = IntegratedMusicTherapyChat() if MUSIC_AVAILABLE else None
        self.art_system = IntegratedArtTherapyChat() if ART_AVAILABLE else None

        self.active_sessions: Dict[str, InterventionSession] = {}
        self.user_history: Dict[str, List[Dict]] = {}

    def process_message(
        self,
        session_id: str,
        user_id: str,
        user_message: str,
        emotion_context: Optional[Dict] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        메시지 처리 및 적절한 치료적 개입 제공

        Returns:
            Dict containing:
            - intervention_suggested: bool
            - intervention_type: str (if suggested)
            - response: str
            - emotional_state: str
            - is_urgent: bool
            - continue_conversation: bool
        """
        # 진행 중인 개입 확인
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            if session.active_intervention:
                return self._delegate_to_active_intervention(
                    session_id, user_message, emotion_context
                )

        # 감정 상태 감지
        state_result = self.state_detector.detect(user_message)

        if not state_result["primary_state"]:
            return {
                "intervention_suggested": False,
                "response": None,
                "continue_conversation": True
            }

        # 긴급 상황 처리
        if state_result["is_urgent"]:
            return self._handle_urgent_situation(
                session_id, user_id, state_result, user_message
            )

        # 일반 개입 추천
        return self._suggest_intervention(
            session_id, user_id, state_result, user_message
        )

    def _handle_urgent_situation(
        self,
        session_id: str,
        user_id: str,
        state_result: Dict,
        user_message: str
    ) -> Dict[str, Any]:
        """긴급 상황 처리 (공황, 해리, 트라우마)"""
        primary_state = state_result["primary_state"]

        # 즉각적 안정화 개입
        if primary_state == EmotionalState.PANIC:
            if self.breathing_system:
                response = """지금 많이 힘드시군요. 제가 함께 있을게요. 💙

🫁 **지금 바로 해보세요:**

1. 숨을 천천히 들이마시세요... (4초)
2. 잠시 멈추세요... (4초)
3. 천천히 내쉬세요... (4초)

이 호흡을 함께 해볼까요? '네'라고 말씀해 주세요."""

                # 세션 시작
                self._start_session(session_id, user_id, InterventionType.BREATHING, primary_state)

                return {
                    "intervention_suggested": True,
                    "intervention_type": "breathing",
                    "response": response,
                    "emotional_state": primary_state.value,
                    "is_urgent": True,
                    "continue_conversation": True
                }

        elif primary_state in [EmotionalState.DISSOCIATION, EmotionalState.TRAUMA_RESPONSE]:
            if self.grounding_system:
                quick_grounding = """지금 여기에 있어요. 안전해요. 💙

🦶 **지금 바로:**
1. 발바닥을 바닥에 꾹 눌러보세요
2. 주변에서 보이는 것 3가지를 말해주세요
3. 지금 들리는 소리 2가지를 찾아보세요

함께 해볼까요?"""

                self._start_session(session_id, user_id, InterventionType.GROUNDING, primary_state)

                return {
                    "intervention_suggested": True,
                    "intervention_type": "grounding",
                    "response": quick_grounding,
                    "emotional_state": primary_state.value,
                    "is_urgent": True,
                    "continue_conversation": True
                }

        # 기본 긴급 응답
        return {
            "intervention_suggested": True,
            "response": "지금 많이 힘드시군요. 깊은 숨을 한 번 쉬어보세요. 제가 여기 있을게요. 💙",
            "emotional_state": primary_state.value,
            "is_urgent": True,
            "continue_conversation": True
        }

    def _suggest_intervention(
        self,
        session_id: str,
        user_id: str,
        state_result: Dict,
        user_message: str
    ) -> Dict[str, Any]:
        """일반 개입 제안"""
        primary_state = state_result["primary_state"]

        # 최근 사용 개입 확인
        recent = self._get_recent_interventions(user_id)

        # 개입 추천
        recommendations = self.intervention_selector.get_recommendations(
            primary_state,
            recent_interventions=recent
        )

        if not recommendations:
            return {
                "intervention_suggested": False,
                "response": None,
                "continue_conversation": True
            }

        # 상위 추천
        top_rec = recommendations[0]

        # 감정 상태별 공감 메시지
        empathy = self._get_empathy_message(primary_state)

        # 개입 설명
        intervention_info = self._get_intervention_info(top_rec.intervention_type)

        response = f"""{empathy}

{intervention_info['emoji']} **{intervention_info['name']}**을 해보시는 건 어떨까요?
{top_rec.rationale}에 도움이 될 수 있어요.

⏱️ 약 {top_rec.estimated_duration}분 소요

해보시겠어요? (네/아니요)"""

        # 세션 대기 상태로 설정
        self._start_session(session_id, user_id, top_rec.intervention_type, primary_state)

        return {
            "intervention_suggested": True,
            "intervention_type": top_rec.intervention_type.value,
            "response": response,
            "emotional_state": primary_state.value,
            "is_urgent": False,
            "recommendations": [r.intervention_type.value for r in recommendations],
            "continue_conversation": True,
            "awaiting_acceptance": True
        }

    def _delegate_to_active_intervention(
        self,
        session_id: str,
        user_message: str,
        emotion_context: Optional[Dict]
    ) -> Dict[str, Any]:
        """활성 개입에 처리 위임"""
        session = self.active_sessions[session_id]
        intervention_type = session.active_intervention

        # 수락/거절 처리
        message_lower = user_message.lower()
        if any(word in message_lower for word in ["아니", "괜찮", "안 할", "싫"]):
            return self._end_intervention(session_id, declined=True)

        # 각 시스템에 위임
        system_map = {
            InterventionType.BREATHING: self.breathing_system,
            InterventionType.GROUNDING: self.grounding_system,
            InterventionType.CBT: self.cbt_system,
            InterventionType.JOURNALING: self.journaling_system,
            InterventionType.MINDFULNESS: self.mindfulness_system,
            InterventionType.BEHAVIORAL_ACTIVATION: self.ba_system,
            InterventionType.MUSIC: self.music_system,
            InterventionType.ART: self.art_system
        }

        system = system_map.get(intervention_type)
        if system:
            result = system.process_message(session_id, user_message, emotion_context)

            # 세션 완료 확인
            if result.get("session_completed") or result.get("session_ended"):
                self._end_intervention(session_id)
                # 기록 저장
                self._record_intervention(session.user_id, intervention_type)

            return result

        return {
            "response": "개입 시스템에 문제가 발생했어요. 계속 이야기해 주세요.",
            "continue_conversation": True
        }

    def start_specific_intervention(
        self,
        session_id: str,
        user_id: str,
        intervention_type: InterventionType
    ) -> Dict[str, Any]:
        """특정 개입 시작"""
        system_map = {
            InterventionType.BREATHING: (self.breathing_system, "start_exercise"),
            InterventionType.GROUNDING: (self.grounding_system, "start_grounding"),
            InterventionType.CBT: (self.cbt_system, "start_thought_record"),
            InterventionType.JOURNALING: (self.journaling_system, "start_journaling"),
            InterventionType.MINDFULNESS: (self.mindfulness_system, "start_meditation"),
            InterventionType.BEHAVIORAL_ACTIVATION: (self.ba_system, "start_session"),
            InterventionType.MUSIC: (self.music_system, "start_lyric_analysis"),
            InterventionType.ART: (self.art_system, "start_activity")
        }

        if intervention_type not in system_map:
            return {"error": "지원되지 않는 개입 유형입니다."}

        system, method_name = system_map[intervention_type]
        if not system:
            return {"error": f"{intervention_type.value} 모듈을 사용할 수 없습니다."}

        # 세션 시작
        self._start_session(session_id, user_id, intervention_type)

        # 각 시스템의 시작 메소드 호출
        method = getattr(system, method_name, None)
        if method:
            return method(session_id, user_id)

        return {"error": "개입을 시작할 수 없습니다."}

    def _start_session(
        self,
        session_id: str,
        user_id: str,
        intervention_type: InterventionType,
        emotional_state: Optional[EmotionalState] = None
    ):
        """세션 시작"""
        self.active_sessions[session_id] = InterventionSession(
            session_id=session_id,
            user_id=user_id,
            active_intervention=intervention_type,
            emotional_state=emotional_state
        )

    def _end_intervention(
        self,
        session_id: str,
        declined: bool = False
    ) -> Dict[str, Any]:
        """개입 종료"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

        if declined:
            return {
                "response": "괜찮아요, 언제든 필요하시면 말씀해 주세요. 계속 이야기를 나눠볼까요? 💙",
                "intervention_ended": True,
                "declined": True,
                "continue_conversation": True
            }

        return {
            "intervention_ended": True,
            "continue_conversation": True
        }

    def _record_intervention(
        self,
        user_id: str,
        intervention_type: InterventionType
    ):
        """개입 기록"""
        if user_id not in self.user_history:
            self.user_history[user_id] = []

        self.user_history[user_id].append({
            "intervention": intervention_type.value,
            "timestamp": datetime.now().isoformat()
        })

    def _get_recent_interventions(
        self,
        user_id: str,
        limit: int = 5
    ) -> List[InterventionType]:
        """최근 개입 목록"""
        history = self.user_history.get(user_id, [])
        recent = history[-limit:] if history else []
        return [InterventionType(h["intervention"]) for h in recent]

    def _get_empathy_message(self, state: EmotionalState) -> str:
        """감정 상태별 공감 메시지"""
        messages = {
            EmotionalState.HIGH_ANXIETY: "불안한 마음이 크시군요.",
            EmotionalState.DEPRESSION: "마음이 많이 무거우시네요.",
            EmotionalState.ANGER: "화가 많이 나셨군요.",
            EmotionalState.STRESS: "스트레스가 많이 쌓이셨네요.",
            EmotionalState.RUMINATION: "생각이 계속 맴도시는군요.",
            EmotionalState.OVERWHELM: "감당하기 힘드시죠.",
            EmotionalState.LOW_ENERGY: "기운이 없으시군요.",
            EmotionalState.GRIEF: "많이 슬프시군요.",
            EmotionalState.EMOTIONAL_DYSREGULATION: "감정이 요동치시는군요."
        }
        return messages.get(state, "힘드시군요.")

    def _get_intervention_info(self, intervention_type: InterventionType) -> Dict[str, str]:
        """개입 정보"""
        info = {
            InterventionType.BREATHING: {"name": "호흡 훈련", "emoji": "🫁"},
            InterventionType.GROUNDING: {"name": "그라운딩", "emoji": "🌿"},
            InterventionType.CBT: {"name": "사고 기록", "emoji": "📝"},
            InterventionType.JOURNALING: {"name": "글쓰기", "emoji": "✍️"},
            InterventionType.MINDFULNESS: {"name": "마음챙김", "emoji": "🧘"},
            InterventionType.BEHAVIORAL_ACTIVATION: {"name": "활동 활성화", "emoji": "🌱"},
            InterventionType.MUSIC: {"name": "음악 치료", "emoji": "🎵"},
            InterventionType.ART: {"name": "그림 치료", "emoji": "🎨"}
        }
        return info.get(intervention_type, {"name": "치료적 개입", "emoji": "💙"})

    def get_available_interventions(self) -> List[Dict[str, Any]]:
        """사용 가능한 개입 목록"""
        interventions = [
            {"type": "breathing", "name": "호흡 훈련", "available": BREATHING_AVAILABLE,
             "description": "호흡을 통한 심신 안정화"},
            {"type": "grounding", "name": "그라운딩", "available": GROUNDING_AVAILABLE,
             "description": "현재 순간에 집중하여 안정감 찾기"},
            {"type": "cbt", "name": "사고 기록 (CBT)", "available": CBT_AVAILABLE,
             "description": "부정적 사고 패턴 인식 및 수정"},
            {"type": "journaling", "name": "글쓰기 치료", "available": JOURNALING_AVAILABLE,
             "description": "글로 감정 표현 및 정리"},
            {"type": "mindfulness", "name": "마음챙김/명상", "available": MINDFULNESS_AVAILABLE,
             "description": "현재 순간 인식과 수용"},
            {"type": "behavioral_activation", "name": "행동 활성화", "available": BA_AVAILABLE,
             "description": "작은 활동으로 기분 개선"},
            {"type": "music", "name": "음악 치료", "available": MUSIC_AVAILABLE,
             "description": "음악을 통한 감정 표현과 치유"},
            {"type": "art", "name": "그림 치료", "available": ART_AVAILABLE,
             "description": "그림으로 내면 표현"}
        ]
        return interventions

    def get_intervention_menu(self) -> str:
        """개입 메뉴 텍스트"""
        interventions = self.get_available_interventions()

        menu = "🌟 **치료적 개입 메뉴**\n\n"
        for i, interv in enumerate(interventions, 1):
            status = "✅" if interv["available"] else "❌"
            menu += f"{i}. {status} **{interv['name']}**\n   {interv['description']}\n\n"

        menu += "원하시는 것을 선택해 주세요. (번호 또는 이름)"
        return menu


# 사용 예시
if __name__ == "__main__":
    system = IntegratedTherapeuticSystem()

    # 공황 상황 테스트
    print("=== 공황 상황 ===")
    result = system.process_message(
        "session_1", "user_1",
        "숨이 안 쉬어져요... 심장이 너무 빨리 뛰고 죽을 것 같아요"
    )
    print(result["response"])

    # 우울 상황 테스트
    print("\n=== 우울 상황 ===")
    result = system.process_message(
        "session_2", "user_1",
        "아무것도 하기 싫어요... 무기력하고 의욕이 없어요"
    )
    print(result["response"])

    # 사용 가능한 개입
    print("\n=== 사용 가능한 개입 ===")
    for interv in system.get_available_interventions():
        status = "✅" if interv["available"] else "❌"
        print(f"{status} {interv['name']}: {interv['description']}")
