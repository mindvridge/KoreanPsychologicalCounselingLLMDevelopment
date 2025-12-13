"""
세션 연속성 시스템 (Session Continuity System)
이전 대화 맥락 깊이 활용

기능:
- 세션 상태 관리 및 저장
- 핵심 정보 추출 및 기억
- 감정 변화 추적
- 이전 대화 요약 생성
- 맞춤형 컨텍스트 프롬프트 생성
- 멀티세션 지속성 (크로스 세션 기억)
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum
import json
import hashlib

logger = logging.getLogger(__name__)


class ConversationPhase(Enum):
    """대화 단계"""
    OPENING = "opening"           # 시작 (1-2턴)
    EXPLORATION = "exploration"   # 탐색 (3-8턴)
    DEEPENING = "deepening"       # 심화 (9-15턴)
    RESOLUTION = "resolution"     # 해결 (16+ 턴)
    CLOSING = "closing"           # 마무리


@dataclass
class ExtractedInfo:
    """추출된 정보"""
    key: str                    # 정보 키
    value: str                  # 정보 값
    category: str               # 카테고리 (personal, situation, emotion, etc.)
    confidence: float           # 신뢰도
    turn_extracted: int         # 추출된 턴
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class EmotionState:
    """감정 상태"""
    primary: str
    secondary: Optional[str]
    intensity: float
    turn: int
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SessionState:
    """세션 상태"""
    session_id: str
    user_id: Optional[str]
    created_at: datetime
    last_active: datetime
    turn_count: int
    phase: ConversationPhase
    extracted_info: List[ExtractedInfo]
    emotion_history: List[EmotionState]
    topics_discussed: List[str]
    key_messages: List[Dict[str, str]]  # 중요 메시지들
    summary: Optional[str]

    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "turn_count": self.turn_count,
            "phase": self.phase.value,
            "extracted_info": [
                {"key": i.key, "value": i.value, "category": i.category}
                for i in self.extracted_info
            ],
            "emotion_history": [
                {"primary": e.primary, "intensity": e.intensity, "turn": e.turn}
                for e in self.emotion_history
            ],
            "topics_discussed": self.topics_discussed,
            "summary": self.summary
        }


class SessionManager:
    """
    세션 관리자

    대화 세션의 상태를 관리하고
    맥락 연속성을 유지합니다.
    """

    def __init__(self, session_timeout_minutes: int = 30):
        """
        초기화

        Args:
            session_timeout_minutes: 세션 타임아웃 (분)
        """
        self.sessions: Dict[str, SessionState] = {}
        self.user_sessions: Dict[str, List[str]] = defaultdict(list)
        self.session_timeout = timedelta(minutes=session_timeout_minutes)

        # 정보 추출 패턴
        self.extraction_patterns = self._init_extraction_patterns()

        # 주제 키워드
        self.topic_keywords = {
            "직장": ["회사", "직장", "상사", "동료", "업무", "야근", "퇴사", "이직"],
            "가족": ["부모", "엄마", "아빠", "형", "누나", "동생", "가족", "집"],
            "연애": ["남자친구", "여자친구", "애인", "연인", "사랑", "이별", "썸"],
            "학업": ["학교", "공부", "시험", "성적", "취업", "진로"],
            "건강": ["아프", "병원", "건강", "몸", "수면", "잠"],
            "대인관계": ["친구", "사람들", "관계", "외로", "혼자"],
            "자존감": ["자신", "자존", "못나", "부족", "비교"],
            "미래불안": ["미래", "앞으로", "계획", "불확실"]
        }

        logger.info(f"SessionManager initialized (timeout={session_timeout_minutes}min)")

    def _init_extraction_patterns(self) -> Dict[str, List[Tuple[str, str]]]:
        """정보 추출 패턴 초기화"""
        return {
            "age_hint": [
                (r"(\d{2})살", "나이"),
                (r"(\d{2})세", "나이"),
                (r"(대학생|고등학생|중학생|직장인)", "신분")
            ],
            "relationship": [
                (r"(남자친구|여자친구|애인|배우자|남편|아내)", "관계"),
                (r"(부모님|엄마|아빠|어머니|아버지)", "가족관계"),
                (r"(상사|동료|부하직원|사장)", "직장관계")
            ],
            "situation": [
                (r"(이직|퇴사|취업|입사)(?:했|하려|할)", "상황"),
                (r"(이별|헤어|결별)(?:했|하려)", "상황"),
                (r"(결혼|약혼)(?:했|하려|할)", "상황")
            ],
            "duration": [
                (r"(\d+)년(?:째|간|동안)", "기간"),
                (r"(\d+)개월(?:째|간|동안)", "기간"),
                (r"(오래|최근|얼마 전)", "시점")
            ]
        }

    def get_or_create_session(
        self,
        session_id: str,
        user_id: Optional[str] = None
    ) -> SessionState:
        """
        세션 가져오기 또는 생성

        Args:
            session_id: 세션 ID
            user_id: 사용자 ID

        Returns:
            SessionState: 세션 상태
        """
        now = datetime.now()

        # 기존 세션 확인
        if session_id in self.sessions:
            session = self.sessions[session_id]

            # 타임아웃 확인
            if now - session.last_active > self.session_timeout:
                logger.info(f"Session {session_id} timed out, creating new session")
                session = self._create_new_session(session_id, user_id)
            else:
                session.last_active = now

            return session

        # 새 세션 생성
        return self._create_new_session(session_id, user_id)

    def _create_new_session(
        self,
        session_id: str,
        user_id: Optional[str]
    ) -> SessionState:
        """새 세션 생성"""
        now = datetime.now()

        session = SessionState(
            session_id=session_id,
            user_id=user_id,
            created_at=now,
            last_active=now,
            turn_count=0,
            phase=ConversationPhase.OPENING,
            extracted_info=[],
            emotion_history=[],
            topics_discussed=[],
            key_messages=[],
            summary=None
        )

        self.sessions[session_id] = session

        if user_id:
            self.user_sessions[user_id].append(session_id)

        logger.info(f"Created new session: {session_id}")
        return session

    def update_session(
        self,
        session_id: str,
        user_message: str,
        assistant_response: str,
        emotion_result: Optional[Dict] = None
    ) -> SessionState:
        """
        세션 업데이트

        Args:
            session_id: 세션 ID
            user_message: 사용자 메시지
            assistant_response: AI 응답
            emotion_result: 감정 분석 결과

        Returns:
            SessionState: 업데이트된 세션
        """
        session = self.get_or_create_session(session_id)
        session.turn_count += 1
        session.last_active = datetime.now()

        # 단계 업데이트
        session.phase = self._determine_phase(session.turn_count)

        # 정보 추출
        new_info = self._extract_information(user_message, session.turn_count)
        session.extracted_info.extend(new_info)

        # 감정 기록
        if emotion_result:
            emotion_state = EmotionState(
                primary=emotion_result.get("primary_emotion", "중립"),
                secondary=emotion_result.get("secondary_emotion"),
                intensity=emotion_result.get("intensity", 0.5),
                turn=session.turn_count
            )
            session.emotion_history.append(emotion_state)

        # 주제 추출
        topics = self._extract_topics(user_message)
        for topic in topics:
            if topic not in session.topics_discussed:
                session.topics_discussed.append(topic)

        # 중요 메시지 저장 (감정 강도가 높은 경우)
        if emotion_result and emotion_result.get("intensity", 0) > 0.7:
            session.key_messages.append({
                "turn": session.turn_count,
                "user": user_message[:200],
                "emotion": emotion_result.get("primary_emotion")
            })

        # 최근 5개만 유지
        if len(session.key_messages) > 5:
            session.key_messages = session.key_messages[-5:]

        return session

    def _determine_phase(self, turn_count: int) -> ConversationPhase:
        """대화 단계 결정"""
        if turn_count <= 2:
            return ConversationPhase.OPENING
        elif turn_count <= 8:
            return ConversationPhase.EXPLORATION
        elif turn_count <= 15:
            return ConversationPhase.DEEPENING
        else:
            return ConversationPhase.RESOLUTION

    def _extract_information(
        self,
        text: str,
        turn: int
    ) -> List[ExtractedInfo]:
        """텍스트에서 정보 추출"""
        extracted = []

        for category, patterns in self.extraction_patterns.items():
            for pattern, label in patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    extracted.append(ExtractedInfo(
                        key=label,
                        value=match,
                        category=category,
                        confidence=0.8,
                        turn_extracted=turn
                    ))

        return extracted

    def _extract_topics(self, text: str) -> List[str]:
        """텍스트에서 주제 추출"""
        topics = []

        for topic, keywords in self.topic_keywords.items():
            if any(kw in text for kw in keywords):
                topics.append(topic)

        return topics

    def generate_context_prompt(self, session_id: str) -> str:
        """
        컨텍스트 프롬프트 생성

        세션 정보를 바탕으로 LLM에 제공할
        컨텍스트 프롬프트를 생성합니다.

        Args:
            session_id: 세션 ID

        Returns:
            str: 컨텍스트 프롬프트
        """
        session = self.sessions.get(session_id)
        if not session:
            return ""

        prompt_parts = ["## 대화 맥락 정보\n"]

        # 대화 단계
        phase_desc = {
            ConversationPhase.OPENING: "시작 단계 - 라포 형성에 집중",
            ConversationPhase.EXPLORATION: "탐색 단계 - 상황과 감정 탐색",
            ConversationPhase.DEEPENING: "심화 단계 - 핵심 문제 탐색",
            ConversationPhase.RESOLUTION: "해결 단계 - 대처 방안 탐색"
        }
        prompt_parts.append(f"대화 단계: {phase_desc.get(session.phase, '진행 중')}")
        prompt_parts.append(f"대화 턴: {session.turn_count}회\n")

        # 추출된 정보
        if session.extracted_info:
            prompt_parts.append("### 파악된 정보:")
            unique_info = {}
            for info in session.extracted_info:
                key = f"{info.key}:{info.value}"
                if key not in unique_info:
                    unique_info[key] = info

            for info in unique_info.values():
                prompt_parts.append(f"- {info.key}: {info.value}")
            prompt_parts.append("")

        # 논의된 주제
        if session.topics_discussed:
            prompt_parts.append(f"### 논의된 주제: {', '.join(session.topics_discussed)}\n")

        # 감정 추이
        if session.emotion_history:
            recent_emotions = session.emotion_history[-3:]
            emotion_str = " → ".join(
                f"{e.primary}({e.intensity:.1f})" for e in recent_emotions
            )
            prompt_parts.append(f"### 감정 변화: {emotion_str}\n")

            # 감정 악화 경고
            if len(session.emotion_history) >= 2:
                recent = session.emotion_history[-1]
                previous = session.emotion_history[-2]
                if recent.intensity > previous.intensity + 0.2:
                    prompt_parts.append("⚠️ 감정 강도가 증가하고 있습니다. 주의 깊게 경청하세요.\n")

        # 핵심 메시지
        if session.key_messages:
            prompt_parts.append("### 핵심 표현:")
            for msg in session.key_messages[-2:]:
                prompt_parts.append(f"- \"{msg['user'][:80]}...\" (감정: {msg.get('emotion', '?')})")
            prompt_parts.append("")

        # 단계별 가이드
        phase_guide = {
            ConversationPhase.OPENING: "첫 인사와 안전한 분위기 조성에 집중하세요.",
            ConversationPhase.EXPLORATION: "열린 질문으로 상황과 감정을 탐색하세요.",
            ConversationPhase.DEEPENING: "핵심 감정과 욕구를 깊이 탐색하세요.",
            ConversationPhase.RESOLUTION: "대처 방안과 자원을 함께 탐색하세요."
        }
        prompt_parts.append(f"### 가이드: {phase_guide.get(session.phase, '')}")

        return "\n".join(prompt_parts)

    def get_session_summary(self, session_id: str) -> str:
        """
        세션 요약 생성

        Args:
            session_id: 세션 ID

        Returns:
            str: 세션 요약
        """
        session = self.sessions.get(session_id)
        if not session:
            return "세션 정보 없음"

        summary_parts = []

        # 기본 정보
        duration = session.last_active - session.created_at
        summary_parts.append(f"대화 시간: {duration.seconds // 60}분")
        summary_parts.append(f"대화 횟수: {session.turn_count}회")

        # 주요 주제
        if session.topics_discussed:
            summary_parts.append(f"주요 주제: {', '.join(session.topics_discussed[:3])}")

        # 감정 변화
        if session.emotion_history:
            first = session.emotion_history[0]
            last = session.emotion_history[-1]
            if first.primary != last.primary:
                summary_parts.append(f"감정 변화: {first.primary} → {last.primary}")
            else:
                intensity_change = last.intensity - first.intensity
                if abs(intensity_change) > 0.2:
                    direction = "완화" if intensity_change < 0 else "심화"
                    summary_parts.append(f"감정 강도: {direction}됨")

        return " | ".join(summary_parts)


# =============================================================================
# 크로스 세션 기억 시스템
# =============================================================================

class CrossSessionMemory:
    """
    크로스 세션 기억

    여러 세션에 걸친 사용자 정보를
    기억하고 활용합니다.
    """

    def __init__(self):
        self.user_memory: Dict[str, Dict[str, Any]] = {}
        self.user_patterns: Dict[str, Dict[str, Any]] = {}

    def store_user_info(
        self,
        user_id: str,
        session_state: SessionState
    ):
        """
        사용자 정보 저장

        Args:
            user_id: 사용자 ID
            session_state: 세션 상태
        """
        if user_id not in self.user_memory:
            self.user_memory[user_id] = {
                "first_seen": datetime.now(),
                "total_sessions": 0,
                "extracted_info": [],
                "recurring_topics": [],
                "typical_emotions": []
            }

        memory = self.user_memory[user_id]
        memory["total_sessions"] += 1
        memory["last_seen"] = datetime.now()

        # 추출된 정보 병합
        for info in session_state.extracted_info:
            existing = [i for i in memory["extracted_info"] if i["key"] == info.key]
            if not existing:
                memory["extracted_info"].append({
                    "key": info.key,
                    "value": info.value,
                    "category": info.category
                })

        # 반복 주제 추적
        for topic in session_state.topics_discussed:
            if topic not in memory["recurring_topics"]:
                memory["recurring_topics"].append(topic)

        # 전형적 감정 추적
        if session_state.emotion_history:
            typical_emotion = max(
                set(e.primary for e in session_state.emotion_history),
                key=lambda x: sum(1 for e in session_state.emotion_history if e.primary == x)
            )
            if typical_emotion not in memory["typical_emotions"]:
                memory["typical_emotions"].append(typical_emotion)

        logger.info(f"Updated cross-session memory for user {user_id}")

    def get_user_context(self, user_id: str) -> Optional[str]:
        """
        사용자 컨텍스트 가져오기

        Args:
            user_id: 사용자 ID

        Returns:
            Optional[str]: 사용자 컨텍스트 프롬프트
        """
        if user_id not in self.user_memory:
            return None

        memory = self.user_memory[user_id]

        if memory["total_sessions"] < 2:
            return None

        parts = ["## 이전 대화 기반 사용자 정보\n"]

        # 방문 정보
        parts.append(f"방문 횟수: {memory['total_sessions']}회")

        # 기억된 정보
        if memory["extracted_info"]:
            parts.append("\n기억된 정보:")
            for info in memory["extracted_info"][:5]:
                parts.append(f"- {info['key']}: {info['value']}")

        # 반복 주제
        if memory["recurring_topics"]:
            parts.append(f"\n자주 나오는 주제: {', '.join(memory['recurring_topics'][:3])}")

        # 전형적 감정
        if memory["typical_emotions"]:
            parts.append(f"자주 느끼는 감정: {', '.join(memory['typical_emotions'][:3])}")

        return "\n".join(parts)


# =============================================================================
# 컨텍스트 컴파일러
# =============================================================================

class ContextCompiler:
    """
    컨텍스트 컴파일러

    다양한 소스에서 컨텍스트를 수집하여
    최적화된 프롬프트를 생성합니다.
    """

    def __init__(
        self,
        session_manager: SessionManager,
        cross_session: Optional[CrossSessionMemory] = None
    ):
        self.session_manager = session_manager
        self.cross_session = cross_session

    def compile(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        additional_context: Optional[Dict] = None
    ) -> str:
        """
        컨텍스트 컴파일

        Args:
            session_id: 세션 ID
            user_id: 사용자 ID
            additional_context: 추가 컨텍스트

        Returns:
            str: 컴파일된 컨텍스트 프롬프트
        """
        parts = []

        # 1. 세션 컨텍스트
        session_context = self.session_manager.generate_context_prompt(session_id)
        if session_context:
            parts.append(session_context)

        # 2. 크로스 세션 컨텍스트
        if self.cross_session and user_id:
            user_context = self.cross_session.get_user_context(user_id)
            if user_context:
                parts.append(user_context)

        # 3. 추가 컨텍스트
        if additional_context:
            add_parts = ["## 추가 컨텍스트"]
            for key, value in additional_context.items():
                add_parts.append(f"- {key}: {value}")
            parts.append("\n".join(add_parts))

        return "\n\n".join(parts)


# =============================================================================
# 테스트
# =============================================================================

def test_session_continuity():
    """세션 연속성 테스트"""
    print("=== 세션 연속성 시스템 테스트 ===\n")

    manager = SessionManager()
    cross_memory = CrossSessionMemory()
    compiler = ContextCompiler(manager, cross_memory)

    session_id = "test_session_001"
    user_id = "user_001"

    # 첫 번째 메시지
    manager.get_or_create_session(session_id, user_id)
    manager.update_session(
        session_id,
        user_message="안녕하세요. 요즘 회사에서 너무 힘들어요. 상사가 너무 싫어요.",
        assistant_response="많이 힘드셨겠어요. 회사에서 어떤 일이 있으셨나요?",
        emotion_result={"primary_emotion": "스트레스", "intensity": 0.7}
    )

    # 두 번째 메시지
    manager.update_session(
        session_id,
        user_message="3년째 이 회사에 다니고 있는데, 상사가 계속 저한테만 업무를 몰아줘요.",
        assistant_response="3년이나 다니셨군요. 불공평하게 느껴지셨겠어요.",
        emotion_result={"primary_emotion": "분노", "intensity": 0.8}
    )

    # 세 번째 메시지
    manager.update_session(
        session_id,
        user_message="28살인데 이직할지 고민이에요. 여자친구도 걱정하고...",
        assistant_response="이직 고민과 여자친구 걱정까지, 여러 가지가 겹치셨네요.",
        emotion_result={"primary_emotion": "불안", "intensity": 0.6}
    )

    # 컨텍스트 프롬프트 확인
    context = manager.generate_context_prompt(session_id)
    print("=== 생성된 컨텍스트 프롬프트 ===")
    print(context)

    # 세션 요약
    summary = manager.get_session_summary(session_id)
    print(f"\n=== 세션 요약 ===\n{summary}")

    # 크로스 세션 메모리 저장
    session = manager.sessions[session_id]
    cross_memory.store_user_info(user_id, session)

    # 컴파일된 컨텍스트
    compiled = compiler.compile(session_id, user_id)
    print(f"\n=== 컴파일된 전체 컨텍스트 ===\n{compiled}")


if __name__ == "__main__":
    test_session_continuity()
