"""
대화 상태 관리 시스템 (Conversation State Manager)
세션 전반의 대화 흐름과 맥락을 추적 관리

기능:
- 대화 단계 자동 추적 (OPENING → EXPLORATION → UNDERSTANDING → INTERVENTION → CLOSING)
- 감정 변화 추이 모니터링
- 주요 고민/주제 추출 및 관리
- 위기 플래그 누적 추적
- 치료 기법 사용 이력
- 세션 목표 및 진행 상황
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import uuid
import json

logger = logging.getLogger(__name__)


class ConversationPhase(Enum):
    """대화 단계"""
    OPENING = "opening"           # 초기 라포 형성 (턴 1-2)
    EXPLORATION = "exploration"   # 문제 탐색 (턴 3-5)
    UNDERSTANDING = "understanding"  # 깊은 이해 (턴 6-8)
    INTERVENTION = "intervention"    # 개입/기법 제공 (턴 9-12)
    CLOSING = "closing"           # 마무리 (턴 13+)


class ConcernCategory(Enum):
    """고민 카테고리"""
    WORK = "직장/업무"
    RELATIONSHIP = "대인관계"
    FAMILY = "가족"
    ACADEMIC = "학업"
    SELF_ESTEEM = "자존감"
    ANXIETY = "불안"
    DEPRESSION = "우울"
    STRESS = "스트레스"
    LIFE_TRANSITION = "삶의 변화"
    HEALTH = "건강"
    FINANCIAL = "경제"
    EXISTENTIAL = "존재/의미"
    OTHER = "기타"


class TherapeuticTechnique(Enum):
    """치료 기법"""
    ACTIVE_LISTENING = "적극적 경청"
    REFLECTION = "감정 반영"
    VALIDATION = "타당화"
    OPEN_QUESTIONS = "개방형 질문"
    SUMMARIZING = "요약"
    COGNITIVE_RESTRUCTURING = "인지 재구성"  # CBT
    BEHAVIORAL_ACTIVATION = "행동 활성화"  # CBT
    ACCEPTANCE = "수용"  # ACT
    VALUES_EXPLORATION = "가치 탐색"  # ACT
    MINDFULNESS = "마음챙김"
    GROUNDING = "그라운딩"
    PSYCHOEDUCATION = "심리교육"
    CRISIS_INTERVENTION = "위기 개입"


@dataclass
class EmotionSnapshot:
    """감정 스냅샷"""
    timestamp: datetime
    primary_emotion: str
    intensity: float  # 1-10
    secondary_emotions: List[str] = field(default_factory=list)
    turn_number: int = 0


@dataclass
class ConcernItem:
    """고민 항목"""
    content: str
    category: ConcernCategory
    first_mentioned: datetime
    last_mentioned: datetime
    mention_count: int = 1
    resolved: bool = False
    priority: int = 1  # 1=높음, 3=낮음


@dataclass
class TechniqueUsage:
    """기법 사용 기록"""
    technique: TherapeuticTechnique
    turn_number: int
    timestamp: datetime
    effectiveness: Optional[float] = None  # 0-1, 사후 평가


@dataclass
class ConversationState:
    """
    대화 상태 전체 컨테이너

    세션의 모든 상태 정보를 포함합니다.
    """
    session_id: str
    user_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    # 대화 진행
    phase: ConversationPhase = ConversationPhase.OPENING
    turn_count: int = 0
    message_history: List[Dict[str, Any]] = field(default_factory=list)

    # 감정 추적
    emotion_trajectory: List[EmotionSnapshot] = field(default_factory=list)
    current_emotion: Optional[str] = None
    current_intensity: float = 5.0
    emotion_trend: str = "stable"  # improving, worsening, stable

    # 고민/주제
    identified_concerns: List[ConcernItem] = field(default_factory=list)
    current_topic: Optional[str] = None
    topics_discussed: List[str] = field(default_factory=list)

    # 위기 관리
    crisis_flags: List[Dict[str, Any]] = field(default_factory=list)
    risk_level: int = 0  # 0-5
    crisis_interventions: int = 0

    # 치료적 개입
    techniques_used: List[TechniqueUsage] = field(default_factory=list)
    session_goals: List[str] = field(default_factory=list)
    insights_gained: List[str] = field(default_factory=list)

    # 메타 정보
    persona_id: str = "maumi"
    language: str = "ko"

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "phase": self.phase.value,
            "turn_count": self.turn_count,
            "current_emotion": self.current_emotion,
            "current_intensity": self.current_intensity,
            "emotion_trend": self.emotion_trend,
            "risk_level": self.risk_level,
            "concerns_count": len(self.identified_concerns),
            "techniques_count": len(self.techniques_used)
        }


class ConversationStateManager:
    """
    대화 상태 관리자

    세션의 상태를 추적하고 업데이트하며,
    다음 응답 생성에 필요한 컨텍스트를 제공합니다.
    """

    def __init__(self, max_history: int = 20):
        """
        초기화

        Args:
            max_history: 유지할 최대 메시지 이력 수
        """
        self.max_history = max_history
        self.active_sessions: Dict[str, ConversationState] = {}

        # 고민 카테고리 키워드 매핑
        self.concern_keywords = {
            ConcernCategory.WORK: ["직장", "회사", "상사", "동료", "업무", "일", "야근", "이직", "퇴사"],
            ConcernCategory.RELATIONSHIP: ["친구", "연인", "남친", "여친", "사람들", "관계", "사이"],
            ConcernCategory.FAMILY: ["가족", "부모", "엄마", "아빠", "형제", "자매", "남편", "아내", "자녀"],
            ConcernCategory.ACADEMIC: ["학교", "공부", "시험", "성적", "대학", "수업", "학업"],
            ConcernCategory.SELF_ESTEEM: ["자존감", "자신감", "못나", "부족", "열등", "비교"],
            ConcernCategory.ANXIETY: ["불안", "걱정", "초조", "긴장", "두렵"],
            ConcernCategory.DEPRESSION: ["우울", "무기력", "의욕", "힘들", "지쳐"],
            ConcernCategory.STRESS: ["스트레스", "압박", "부담", "피곤"],
            ConcernCategory.HEALTH: ["건강", "아프", "병", "잠", "수면"],
            ConcernCategory.FINANCIAL: ["돈", "경제", "빚", "취업", "실업"],
        }

        logger.info("ConversationStateManager initialized")

    def create_session(
        self,
        user_id: Optional[str] = None,
        persona_id: str = "maumi"
    ) -> ConversationState:
        """
        새 세션 생성

        Args:
            user_id: 사용자 ID
            persona_id: 페르소나 ID

        Returns:
            ConversationState: 새 세션 상태
        """
        session_id = str(uuid.uuid4())
        state = ConversationState(
            session_id=session_id,
            user_id=user_id,
            persona_id=persona_id
        )
        self.active_sessions[session_id] = state

        logger.info(f"New session created: {session_id}")
        return state

    def get_session(self, session_id: str) -> Optional[ConversationState]:
        """세션 조회"""
        return self.active_sessions.get(session_id)

    def update_state(
        self,
        session_id: str,
        user_message: str,
        assistant_response: str,
        emotion_analysis: Optional[Dict] = None,
        crisis_info: Optional[Dict] = None
    ) -> ConversationState:
        """
        상태 업데이트

        Args:
            session_id: 세션 ID
            user_message: 사용자 메시지
            assistant_response: 어시스턴트 응답
            emotion_analysis: 감정 분석 결과
            crisis_info: 위기 감지 정보

        Returns:
            ConversationState: 업데이트된 상태
        """
        state = self.get_session(session_id)
        if not state:
            state = self.create_session()
            self.active_sessions[session_id] = state

        now = datetime.now()
        state.last_updated = now

        # 턴 카운트 증가
        state.turn_count += 1

        # 메시지 이력 추가
        state.message_history.append({
            "role": "user",
            "content": user_message,
            "timestamp": now.isoformat(),
            "turn": state.turn_count
        })
        state.message_history.append({
            "role": "assistant",
            "content": assistant_response,
            "timestamp": now.isoformat(),
            "turn": state.turn_count
        })

        # 이력 제한
        if len(state.message_history) > self.max_history * 2:
            state.message_history = state.message_history[-(self.max_history * 2):]

        # 감정 업데이트
        if emotion_analysis:
            self._update_emotion(state, emotion_analysis)

        # 위기 정보 업데이트
        if crisis_info:
            self._update_crisis_info(state, crisis_info)

        # 고민 추출 및 업데이트
        self._extract_concerns(state, user_message)

        # 대화 단계 업데이트
        self._update_phase(state)

        # 사용된 기법 추론
        self._infer_techniques(state, assistant_response)

        return state

    def _update_emotion(
        self,
        state: ConversationState,
        emotion_analysis: Dict
    ):
        """감정 상태 업데이트"""
        primary = emotion_analysis.get("primary_emotion", "중립")
        intensity = emotion_analysis.get("intensity", 5.0)
        secondary = emotion_analysis.get("secondary_emotions", [])

        # 현재 감정 업데이트
        state.current_emotion = primary
        state.current_intensity = intensity

        # 스냅샷 추가
        snapshot = EmotionSnapshot(
            timestamp=datetime.now(),
            primary_emotion=primary,
            intensity=intensity,
            secondary_emotions=secondary,
            turn_number=state.turn_count
        )
        state.emotion_trajectory.append(snapshot)

        # 감정 추세 분석
        if len(state.emotion_trajectory) >= 3:
            recent = state.emotion_trajectory[-3:]
            intensities = [s.intensity for s in recent]

            if intensities[-1] < intensities[-2] < intensities[-3]:
                state.emotion_trend = "improving"
            elif intensities[-1] > intensities[-2] > intensities[-3]:
                state.emotion_trend = "worsening"
            else:
                state.emotion_trend = "stable"

    def _update_crisis_info(
        self,
        state: ConversationState,
        crisis_info: Dict
    ):
        """위기 정보 업데이트"""
        risk_score = crisis_info.get("risk_score", 0)
        risk_level = crisis_info.get("risk_level", "NONE")

        # 위험 수준 매핑
        level_map = {"NONE": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        state.risk_level = max(state.risk_level, level_map.get(risk_level, 0))

        # 위기 플래그 추가
        if risk_level not in ["NONE", "LOW"]:
            state.crisis_flags.append({
                "timestamp": datetime.now().isoformat(),
                "level": risk_level,
                "score": risk_score,
                "turn": state.turn_count,
                "details": crisis_info.get("details", {})
            })

            if risk_level in ["HIGH", "CRITICAL"]:
                state.crisis_interventions += 1

    def _extract_concerns(self, state: ConversationState, message: str):
        """메시지에서 고민 추출"""
        message_lower = message.lower()

        for category, keywords in self.concern_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    # 기존 고민 찾기
                    existing = next(
                        (c for c in state.identified_concerns if c.category == category),
                        None
                    )

                    if existing:
                        existing.last_mentioned = datetime.now()
                        existing.mention_count += 1
                    else:
                        concern = ConcernItem(
                            content=self._extract_concern_context(message, keyword),
                            category=category,
                            first_mentioned=datetime.now(),
                            last_mentioned=datetime.now()
                        )
                        state.identified_concerns.append(concern)

                    # 현재 주제 업데이트
                    state.current_topic = category.value
                    if category.value not in state.topics_discussed:
                        state.topics_discussed.append(category.value)

                    break  # 카테고리당 하나만

    def _extract_concern_context(self, message: str, keyword: str) -> str:
        """고민 맥락 추출"""
        # 키워드 주변 컨텍스트 추출 (간단한 구현)
        idx = message.find(keyword)
        start = max(0, idx - 20)
        end = min(len(message), idx + len(keyword) + 30)
        return message[start:end].strip()

    def _update_phase(self, state: ConversationState):
        """대화 단계 업데이트"""
        turn = state.turn_count

        # 위기 상황에서는 단계 고정
        if state.risk_level >= 3:
            # 위기 개입 상태 유지
            return

        if turn <= 2:
            state.phase = ConversationPhase.OPENING
        elif turn <= 5:
            state.phase = ConversationPhase.EXPLORATION
        elif turn <= 8:
            state.phase = ConversationPhase.UNDERSTANDING
        elif turn <= 12:
            state.phase = ConversationPhase.INTERVENTION
        else:
            state.phase = ConversationPhase.CLOSING

    def _infer_techniques(self, state: ConversationState, response: str):
        """응답에서 사용된 기법 추론"""
        techniques_detected = []

        # 기법 패턴 매칭
        technique_patterns = {
            TherapeuticTechnique.REFLECTION: ["군요", "시군요", "셨군요", "느끼시"],
            TherapeuticTechnique.VALIDATION: ["당연", "자연스러", "충분히", "타당"],
            TherapeuticTechnique.OPEN_QUESTIONS: ["어떤", "어떻게", "무엇", "왜", "?"],
            TherapeuticTechnique.SUMMARIZING: ["정리하면", "요약하면", "말씀하신"],
            TherapeuticTechnique.COGNITIVE_RESTRUCTURING: ["다른 관점", "생각해보면", "만약"],
            TherapeuticTechnique.MINDFULNESS: ["지금 이 순간", "현재", "호흡", "관찰"],
            TherapeuticTechnique.GROUNDING: ["보이는 것", "들리는 것", "느껴지는"],
            TherapeuticTechnique.ACCEPTANCE: ["수용", "받아들이", "함께 있"],
            TherapeuticTechnique.CRISIS_INTERVENTION: ["1393", "1577-0199", "안전", "응급"],
        }

        for technique, patterns in technique_patterns.items():
            if any(pattern in response for pattern in patterns):
                techniques_detected.append(technique)

        # 기법 사용 기록
        for technique in techniques_detected:
            usage = TechniqueUsage(
                technique=technique,
                turn_number=state.turn_count,
                timestamp=datetime.now()
            )
            state.techniques_used.append(usage)

    def get_context_for_prompt(self, session_id: str) -> Dict[str, Any]:
        """
        프롬프트 생성용 컨텍스트 반환

        Args:
            session_id: 세션 ID

        Returns:
            Dict: 프롬프트 컨텍스트
        """
        state = self.get_session(session_id)
        if not state:
            return {}

        # 최근 고민 추출
        recent_concerns = [
            c.category.value for c in state.identified_concerns
            if (datetime.now() - c.last_mentioned) < timedelta(minutes=30)
        ]

        # 최근 사용 기법
        recent_techniques = [
            t.technique.value for t in state.techniques_used[-5:]
        ]

        return {
            "turn_count": state.turn_count,
            "phase": state.phase.value,
            "phase_guidance": self._get_phase_guidance(state.phase),
            "current_emotion": state.current_emotion,
            "emotion_intensity": state.current_intensity,
            "emotion_trend": state.emotion_trend,
            "risk_level": state.risk_level,
            "concerns": recent_concerns,
            "current_topic": state.current_topic,
            "techniques_used": recent_techniques,
            "crisis_active": state.risk_level >= 3,
            "session_duration_minutes": self._get_session_duration(state)
        }

    def _get_phase_guidance(self, phase: ConversationPhase) -> str:
        """단계별 가이드라인 반환"""
        guidance = {
            ConversationPhase.OPENING:
                "라포 형성 중. 따뜻한 환영, 안전한 공간 조성. 개방형 질문 사용.",
            ConversationPhase.EXPLORATION:
                "탐색 단계. 구체적 상황과 감정 파악. 반영 기법 적극 활용.",
            ConversationPhase.UNDERSTANDING:
                "이해 단계. 패턴 파악, 핵심 감정 명료화. 요약 제공.",
            ConversationPhase.INTERVENTION:
                "개입 단계. 적절한 치료 기법 제안. 내담자 선택권 존중.",
            ConversationPhase.CLOSING:
                "마무리 단계. 핵심 요약, 변화 인정, 다음 단계 안내."
        }
        return guidance.get(phase, "")

    def _get_session_duration(self, state: ConversationState) -> int:
        """세션 지속 시간 (분)"""
        duration = datetime.now() - state.created_at
        return int(duration.total_seconds() / 60)

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """
        세션 요약 생성

        Args:
            session_id: 세션 ID

        Returns:
            Dict: 세션 요약
        """
        state = self.get_session(session_id)
        if not state:
            return {}

        # 감정 변화 분석
        emotion_changes = []
        if len(state.emotion_trajectory) >= 2:
            for i in range(1, len(state.emotion_trajectory)):
                prev = state.emotion_trajectory[i-1]
                curr = state.emotion_trajectory[i]
                if prev.primary_emotion != curr.primary_emotion:
                    emotion_changes.append({
                        "from": prev.primary_emotion,
                        "to": curr.primary_emotion,
                        "turn": curr.turn_number
                    })

        # 주요 고민 정리
        main_concerns = [
            {
                "category": c.category.value,
                "mention_count": c.mention_count,
                "resolved": c.resolved
            }
            for c in sorted(
                state.identified_concerns,
                key=lambda x: x.mention_count,
                reverse=True
            )[:5]
        ]

        # 사용된 기법 통계
        technique_counts = {}
        for usage in state.techniques_used:
            name = usage.technique.value
            technique_counts[name] = technique_counts.get(name, 0) + 1

        return {
            "session_id": session_id,
            "duration_minutes": self._get_session_duration(state),
            "total_turns": state.turn_count,
            "final_phase": state.phase.value,
            "emotion_summary": {
                "start": state.emotion_trajectory[0].primary_emotion if state.emotion_trajectory else None,
                "end": state.current_emotion,
                "trend": state.emotion_trend,
                "changes": emotion_changes
            },
            "concerns": main_concerns,
            "crisis_events": len(state.crisis_flags),
            "techniques_used": technique_counts,
            "topics_discussed": state.topics_discussed
        }

    def end_session(self, session_id: str) -> Dict[str, Any]:
        """
        세션 종료

        Args:
            session_id: 세션 ID

        Returns:
            Dict: 세션 요약
        """
        summary = self.get_session_summary(session_id)

        # 세션 정리
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.info(f"Session ended: {session_id}")

        return summary


# 전역 상태 관리자 인스턴스
_state_manager: Optional[ConversationStateManager] = None


def get_state_manager() -> ConversationStateManager:
    """상태 관리자 싱글톤"""
    global _state_manager
    if _state_manager is None:
        _state_manager = ConversationStateManager()
    return _state_manager


if __name__ == "__main__":
    # 테스트
    print("=== 대화 상태 관리 시스템 테스트 ===\n")

    manager = ConversationStateManager()

    # 세션 생성
    state = manager.create_session(user_id="test_user")
    session_id = state.session_id
    print(f"세션 생성: {session_id}")

    # 대화 시뮬레이션
    conversations = [
        {
            "user": "안녕하세요. 요즘 직장 때문에 너무 스트레스받아요.",
            "assistant": "안녕하세요. 직장 일로 많이 스트레스를 받고 계시는군요. 어떤 부분이 특히 힘드신가요?",
            "emotion": {"primary_emotion": "스트레스", "intensity": 6.5}
        },
        {
            "user": "상사가 저한테만 일을 몰아줘요. 너무 억울해요.",
            "assistant": "상사분이 유독 본인에게만 업무를 몰아주시는 것 같아 정말 억울하고 힘드셨겠어요. 그런 상황이 언제부터 있었나요?",
            "emotion": {"primary_emotion": "분노", "intensity": 7.5, "secondary_emotions": ["억울함"]}
        },
        {
            "user": "한 달 전부터요. 가끔 출근하기 싫어질 정도예요.",
            "assistant": "한 달이나 그런 상황이 계속되셨군요. 출근하기 싫어질 만큼 지치셨을 것 같아요. 그 마음 충분히 이해됩니다.",
            "emotion": {"primary_emotion": "우울", "intensity": 7.0}
        }
    ]

    for i, conv in enumerate(conversations, 1):
        print(f"\n--- 턴 {i} ---")
        state = manager.update_state(
            session_id=session_id,
            user_message=conv["user"],
            assistant_response=conv["assistant"],
            emotion_analysis=conv.get("emotion")
        )
        print(f"단계: {state.phase.value}")
        print(f"현재 감정: {state.current_emotion} (강도: {state.current_intensity})")
        print(f"추세: {state.emotion_trend}")
        print(f"파악된 고민: {[c.category.value for c in state.identified_concerns]}")

    # 세션 요약
    print("\n=== 세션 요약 ===")
    summary = manager.get_session_summary(session_id)
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    # 프롬프트 컨텍스트
    print("\n=== 프롬프트 컨텍스트 ===")
    context = manager.get_context_for_prompt(session_id)
    print(json.dumps(context, ensure_ascii=False, indent=2))
