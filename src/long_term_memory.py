"""
장기 기억 관리 시스템 (Long-Term Memory Manager)
교차 세션 맥락 연결, 장기 패턴 분석, 치료 효과 추적

기능:
- 세션 간 맥락 연결 (이전 세션 핵심 요약 자동 참조)
- 장기 감정/고민 패턴 분석
- 치료 기법 효과 추적 및 학습
- 개인화 컨텍스트 생성
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field
from collections import Counter, defaultdict
from enum import Enum
import json
import statistics

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class SessionMemory:
    """세션 메모리 (핵심 정보만 저장)"""
    session_id: str
    user_id: str
    date: datetime
    duration_minutes: int

    # 핵심 요약
    main_concerns: List[str]
    key_insights: List[str]
    emotional_state: str
    emotional_shift: str  # positive, negative, stable

    # 치료적 요소
    techniques_used: List[str]
    homework_given: List[str]
    homework_completed: List[str]  # 다음 세션에서 업데이트

    # 위기 정보
    crisis_events: int
    max_risk_level: int

    # 진행 상황
    progress_notes: str
    next_session_focus: List[str]


@dataclass
class UserLongTermProfile:
    """사용자 장기 프로필"""
    user_id: str
    created_at: datetime
    last_updated: datetime

    # 기본 정보 (추출됨)
    preferred_name: Optional[str] = None
    age_range: Optional[str] = None

    # 장기 패턴
    recurring_concerns: Dict[str, int] = field(default_factory=dict)  # 고민: 빈도
    emotional_patterns: Dict[str, List[float]] = field(default_factory=dict)  # 감정: [강도 이력]
    trigger_patterns: List[str] = field(default_factory=list)  # 발견된 트리거
    coping_strategies: List[str] = field(default_factory=list)  # 효과적인 대처방법

    # 치료 선호도
    effective_techniques: Dict[str, float] = field(default_factory=dict)  # 기법: 효과점수
    preferred_counseling_style: str = "balanced"  # directive, supportive, balanced

    # 강점 및 자원
    identified_strengths: List[str] = field(default_factory=list)
    support_system: List[str] = field(default_factory=list)  # 가족, 친구 등

    # 통계
    total_sessions: int = 0
    total_crisis_events: int = 0
    avg_session_duration: float = 0.0
    overall_progress: str = "unknown"  # improving, stable, declining


@dataclass
class TechniqueEffectiveness:
    """치료 기법 효과성 추적"""
    technique_name: str
    usage_count: int = 0

    # 효과 측정
    emotional_improvement_rate: float = 0.0  # -1 to 1
    user_feedback_score: float = 0.0  # 0-5
    completion_rate: float = 0.0  # 과제 완료율

    # 상황별 효과
    effectiveness_by_concern: Dict[str, float] = field(default_factory=dict)
    effectiveness_by_emotion: Dict[str, float] = field(default_factory=dict)

    # 신뢰도
    confidence: float = 0.0  # 데이터 충분성 기반


# =============================================================================
# Pattern Analysis
# =============================================================================

class PatternAnalyzer:
    """장기 패턴 분석기"""

    def __init__(self):
        self.concern_keywords = {
            "직장": ["회사", "직장", "상사", "동료", "업무", "야근", "이직"],
            "가족": ["가족", "부모", "엄마", "아빠", "형제", "자녀", "남편", "아내"],
            "관계": ["친구", "연인", "사람", "관계", "소통", "갈등"],
            "자존감": ["자존감", "자신감", "열등", "비교", "못나"],
            "불안": ["불안", "걱정", "초조", "두려움", "긴장"],
            "우울": ["우울", "무기력", "힘들", "슬프", "의욕"],
            "스트레스": ["스트레스", "압박", "부담", "피곤", "지쳐"],
            "건강": ["건강", "잠", "수면", "아프", "통증"],
        }

    def analyze_recurring_concerns(
        self,
        session_memories: List[SessionMemory]
    ) -> Dict[str, int]:
        """반복되는 고민 패턴 분석"""
        concern_counts = Counter()

        for session in session_memories:
            for concern in session.main_concerns:
                # 키워드 기반 카테고리화
                for category, keywords in self.concern_keywords.items():
                    if any(kw in concern for kw in keywords):
                        concern_counts[category] += 1
                        break
                else:
                    concern_counts[concern[:20]] += 1  # 원본 고민 (축약)

        return dict(concern_counts.most_common(10))

    def analyze_emotional_trajectory(
        self,
        session_memories: List[SessionMemory]
    ) -> Dict[str, Any]:
        """감정 변화 궤적 분석"""
        if not session_memories:
            return {"trend": "unknown", "dominant": "unknown"}

        # 시간순 정렬
        sorted_sessions = sorted(session_memories, key=lambda x: x.date)

        # 감정 변화 추세
        shifts = [s.emotional_shift for s in sorted_sessions]
        positive_count = shifts.count("positive")
        negative_count = shifts.count("negative")

        # 지배적 감정
        emotions = [s.emotional_state for s in sorted_sessions]
        dominant = Counter(emotions).most_common(1)[0][0] if emotions else "unknown"

        # 추세 판정
        recent = shifts[-5:] if len(shifts) >= 5 else shifts
        recent_positive = recent.count("positive")
        recent_negative = recent.count("negative")

        if recent_positive > recent_negative + 1:
            trend = "improving"
        elif recent_negative > recent_positive + 1:
            trend = "declining"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "dominant_emotion": dominant,
            "positive_sessions": positive_count,
            "negative_sessions": negative_count,
            "total_sessions": len(session_memories)
        }

    def identify_triggers(
        self,
        session_memories: List[SessionMemory]
    ) -> List[str]:
        """트리거 패턴 식별"""
        triggers = []

        # 위기 이벤트가 있는 세션 분석
        crisis_sessions = [s for s in session_memories if s.crisis_events > 0]

        if crisis_sessions:
            crisis_concerns = []
            for session in crisis_sessions:
                crisis_concerns.extend(session.main_concerns)

            # 위기 시 자주 등장하는 고민
            common_crisis_concerns = Counter(crisis_concerns).most_common(3)
            triggers.extend([c[0] for c in common_crisis_concerns])

        return list(set(triggers))

    def analyze_technique_effectiveness(
        self,
        session_memories: List[SessionMemory]
    ) -> Dict[str, TechniqueEffectiveness]:
        """치료 기법 효과성 분석"""
        technique_stats = defaultdict(lambda: {
            "usage_count": 0,
            "emotional_improvements": [],
            "concerns": [],
        })

        for session in session_memories:
            improvement = 1 if session.emotional_shift == "positive" else (
                -1 if session.emotional_shift == "negative" else 0
            )

            for technique in session.techniques_used:
                stats = technique_stats[technique]
                stats["usage_count"] += 1
                stats["emotional_improvements"].append(improvement)
                stats["concerns"].extend(session.main_concerns)

        # 효과성 계산
        effectiveness = {}
        for technique, stats in technique_stats.items():
            if stats["usage_count"] >= 2:  # 최소 2회 사용
                improvements = stats["emotional_improvements"]
                avg_improvement = sum(improvements) / len(improvements)

                effectiveness[technique] = TechniqueEffectiveness(
                    technique_name=technique,
                    usage_count=stats["usage_count"],
                    emotional_improvement_rate=avg_improvement,
                    confidence=min(1.0, stats["usage_count"] / 10)
                )

        return effectiveness


# =============================================================================
# Cross-Session Context Manager
# =============================================================================

class CrossSessionContextManager:
    """교차 세션 맥락 관리자"""

    def __init__(self):
        self.pattern_analyzer = PatternAnalyzer()

    def generate_session_bridge(
        self,
        user_profile: UserLongTermProfile,
        recent_sessions: List[SessionMemory],
        current_session_number: int
    ) -> str:
        """
        이전 세션과 현재 세션을 연결하는 브릿지 컨텍스트 생성

        Returns:
            LLM에 전달할 이전 세션 맥락 문자열
        """
        if not recent_sessions:
            return self._generate_first_session_context(user_profile)

        # 가장 최근 세션
        last_session = recent_sessions[0]

        # 브릿지 생성
        bridge_parts = []

        # 1. 이전 세션 요약
        bridge_parts.append(f"## 이전 세션 정보 (#{current_session_number - 1})")
        bridge_parts.append(f"- 날짜: {last_session.date.strftime('%Y년 %m월 %d일')}")

        if last_session.main_concerns:
            concerns_str = ", ".join(last_session.main_concerns[:3])
            bridge_parts.append(f"- 주요 고민: {concerns_str}")

        if last_session.key_insights:
            bridge_parts.append(f"- 핵심 인사이트: {last_session.key_insights[0]}")

        bridge_parts.append(f"- 감정 상태: {last_session.emotional_state}")
        bridge_parts.append(f"- 변화 추세: {self._translate_shift(last_session.emotional_shift)}")

        # 2. 과제 확인
        if last_session.homework_given:
            bridge_parts.append("\n## 지난 과제")
            for hw in last_session.homework_given[:3]:
                bridge_parts.append(f"- {hw}")
            bridge_parts.append("→ 자연스럽게 과제 수행 여부 확인 권장")

        # 3. 다음 세션 제안 (이전 세션에서)
        if last_session.next_session_focus:
            bridge_parts.append("\n## 이번 세션 제안 주제")
            for focus in last_session.next_session_focus[:2]:
                bridge_parts.append(f"- {focus}")

        # 4. 장기 패턴 요약 (3회 이상 세션 시)
        if len(recent_sessions) >= 3:
            bridge_parts.append(self._generate_pattern_summary(user_profile, recent_sessions))

        # 5. 주의사항
        if last_session.max_risk_level >= 3:
            bridge_parts.append("\n⚠️ **주의**: 이전 세션에서 위기 상황이 있었습니다. 안전 확인 필요.")

        return "\n".join(bridge_parts)

    def _generate_first_session_context(self, user_profile: UserLongTermProfile) -> str:
        """첫 세션 컨텍스트"""
        parts = ["## 첫 번째 세션"]

        if user_profile.preferred_name:
            parts.append(f"- 선호 호칭: {user_profile.preferred_name}")
        if user_profile.age_range:
            parts.append(f"- 연령대: {user_profile.age_range}")

        parts.append("\n**첫 세션 권장사항:**")
        parts.append("- 라포 형성에 충분한 시간 할애")
        parts.append("- 개방형 질문으로 시작")
        parts.append("- 상담 목표 함께 설정")

        return "\n".join(parts)

    def _generate_pattern_summary(
        self,
        user_profile: UserLongTermProfile,
        recent_sessions: List[SessionMemory]
    ) -> str:
        """장기 패턴 요약"""
        parts = ["\n## 장기 패턴 분석"]

        # 반복 고민
        if user_profile.recurring_concerns:
            top_concerns = sorted(
                user_profile.recurring_concerns.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            concerns_str = ", ".join([f"{c[0]}({c[1]}회)" for c in top_concerns])
            parts.append(f"- 반복 고민: {concerns_str}")

        # 감정 추세
        trajectory = self.pattern_analyzer.analyze_emotional_trajectory(recent_sessions)
        parts.append(f"- 전반적 추세: {self._translate_trend(trajectory['trend'])}")

        # 효과적 기법
        if user_profile.effective_techniques:
            top_techniques = sorted(
                user_profile.effective_techniques.items(),
                key=lambda x: x[1],
                reverse=True
            )[:2]
            if top_techniques:
                techniques_str = ", ".join([t[0] for t in top_techniques])
                parts.append(f"- 효과적 기법: {techniques_str}")

        # 강점
        if user_profile.identified_strengths:
            strengths_str = ", ".join(user_profile.identified_strengths[:3])
            parts.append(f"- 발견된 강점: {strengths_str}")

        return "\n".join(parts)

    def _translate_shift(self, shift: str) -> str:
        """감정 변화 번역"""
        translations = {
            "positive": "긍정적 변화",
            "negative": "하락",
            "stable": "안정적"
        }
        return translations.get(shift, shift)

    def _translate_trend(self, trend: str) -> str:
        """추세 번역"""
        translations = {
            "improving": "개선 중",
            "declining": "주의 필요",
            "stable": "안정적",
            "unknown": "데이터 부족"
        }
        return translations.get(trend, trend)


# =============================================================================
# Long-Term Memory Manager
# =============================================================================

class LongTermMemoryManager:
    """장기 기억 관리자 (통합 클래스)"""

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path
        self.pattern_analyzer = PatternAnalyzer()
        self.context_manager = CrossSessionContextManager()

        # 메모리 저장소
        self.user_profiles: Dict[str, UserLongTermProfile] = {}
        self.session_memories: Dict[str, List[SessionMemory]] = {}  # user_id: [sessions]
        self.technique_effectiveness: Dict[str, TechniqueEffectiveness] = {}

        # 저장된 데이터 로드
        if storage_path:
            self._load_data()

    # =========================================================================
    # Profile Management
    # =========================================================================

    def get_or_create_profile(self, user_id: str) -> UserLongTermProfile:
        """사용자 프로필 조회 또는 생성"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserLongTermProfile(
                user_id=user_id,
                created_at=datetime.now(),
                last_updated=datetime.now()
            )
            self.session_memories[user_id] = []

        return self.user_profiles[user_id]

    def update_profile_from_session(
        self,
        user_id: str,
        session_memory: SessionMemory
    ):
        """세션 정보로 프로필 업데이트"""
        profile = self.get_or_create_profile(user_id)
        sessions = self.session_memories.get(user_id, [])

        # 세션 메모리 추가
        sessions.insert(0, session_memory)  # 최신 순
        self.session_memories[user_id] = sessions[:50]  # 최대 50개 유지

        # 프로필 업데이트
        profile.last_updated = datetime.now()
        profile.total_sessions += 1
        profile.total_crisis_events += session_memory.crisis_events

        # 반복 고민 업데이트
        concerns = self.pattern_analyzer.analyze_recurring_concerns(sessions)
        profile.recurring_concerns = concerns

        # 감정 패턴 업데이트
        trajectory = self.pattern_analyzer.analyze_emotional_trajectory(sessions)
        profile.overall_progress = trajectory["trend"]

        # 기법 효과성 업데이트
        effectiveness = self.pattern_analyzer.analyze_technique_effectiveness(sessions)
        profile.effective_techniques = {
            k: v.emotional_improvement_rate
            for k, v in effectiveness.items()
        }

        # 트리거 업데이트
        triggers = self.pattern_analyzer.identify_triggers(sessions)
        profile.trigger_patterns = triggers

        # 평균 세션 시간
        if sessions:
            profile.avg_session_duration = statistics.mean(
                [s.duration_minutes for s in sessions]
            )

        # 저장
        self._save_data()

        logger.info(f"Profile updated for user {user_id}: {profile.total_sessions} sessions")

    # =========================================================================
    # Context Generation
    # =========================================================================

    def generate_personalized_context(
        self,
        user_id: str,
        include_patterns: bool = True,
        include_bridge: bool = True
    ) -> str:
        """
        개인화된 컨텍스트 생성 (LLM 프롬프트용)

        Args:
            user_id: 사용자 ID
            include_patterns: 장기 패턴 포함 여부
            include_bridge: 세션 브릿지 포함 여부

        Returns:
            컨텍스트 문자열
        """
        profile = self.get_or_create_profile(user_id)
        sessions = self.session_memories.get(user_id, [])

        context_parts = ["[사용자 장기 기억]"]

        # 1. 기본 정보
        if profile.preferred_name:
            context_parts.append(f"호칭: {profile.preferred_name}")
        if profile.age_range:
            context_parts.append(f"연령대: {profile.age_range}")

        context_parts.append(f"총 상담 횟수: {profile.total_sessions}회")

        # 2. 세션 브릿지
        if include_bridge and sessions:
            bridge = self.context_manager.generate_session_bridge(
                profile, sessions, profile.total_sessions + 1
            )
            context_parts.append(f"\n{bridge}")

        # 3. 장기 패턴
        if include_patterns and profile.total_sessions >= 3:
            pattern_context = self._generate_pattern_context(profile)
            context_parts.append(f"\n{pattern_context}")

        # 4. 주의사항
        warnings = self._generate_warnings(profile)
        if warnings:
            context_parts.append(f"\n{warnings}")

        return "\n".join(context_parts)

    def _generate_pattern_context(self, profile: UserLongTermProfile) -> str:
        """패턴 컨텍스트 생성"""
        parts = ["## 장기 인사이트"]

        # 반복 고민
        if profile.recurring_concerns:
            top = sorted(profile.recurring_concerns.items(), key=lambda x: x[1], reverse=True)[:3]
            parts.append(f"- 주요 고민 영역: {', '.join([t[0] for t in top])}")

        # 트리거
        if profile.trigger_patterns:
            parts.append(f"- 주의 트리거: {', '.join(profile.trigger_patterns[:3])}")

        # 효과적 기법
        if profile.effective_techniques:
            effective = [k for k, v in profile.effective_techniques.items() if v > 0.3]
            if effective:
                parts.append(f"- 효과적 기법: {', '.join(effective[:3])}")

        # 강점
        if profile.identified_strengths:
            parts.append(f"- 강점 활용: {', '.join(profile.identified_strengths[:3])}")

        # 대처 전략
        if profile.coping_strategies:
            parts.append(f"- 효과적 대처: {', '.join(profile.coping_strategies[:3])}")

        # 진행 상황
        progress_map = {
            "improving": "전반적으로 개선 추세입니다. 긍정적 변화를 인정해주세요.",
            "stable": "안정적인 상태를 유지하고 있습니다.",
            "declining": "주의가 필요합니다. 추가 지원을 고려하세요.",
        }
        if profile.overall_progress in progress_map:
            parts.append(f"\n**진행 상황**: {progress_map[profile.overall_progress]}")

        return "\n".join(parts)

    def _generate_warnings(self, profile: UserLongTermProfile) -> str:
        """주의사항 생성"""
        warnings = []

        if profile.total_crisis_events > 0:
            warnings.append(f"⚠️ 과거 위기 상황 {profile.total_crisis_events}회 기록")

        if profile.overall_progress == "declining":
            warnings.append("⚠️ 전반적 상태 하락 추세 - 전문가 연계 고려")

        if profile.trigger_patterns:
            warnings.append(f"⚠️ 트리거 주의: {', '.join(profile.trigger_patterns[:2])}")

        if warnings:
            return "## 주의사항\n" + "\n".join(warnings)
        return ""

    # =========================================================================
    # Session Memory Management
    # =========================================================================

    def create_session_memory(
        self,
        session_id: str,
        user_id: str,
        session_data: Dict[str, Any]
    ) -> SessionMemory:
        """세션 메모리 생성"""
        memory = SessionMemory(
            session_id=session_id,
            user_id=user_id,
            date=datetime.now(),
            duration_minutes=session_data.get("duration_minutes", 0),
            main_concerns=session_data.get("main_concerns", []),
            key_insights=session_data.get("key_insights", []),
            emotional_state=session_data.get("emotional_state", "unknown"),
            emotional_shift=session_data.get("emotional_shift", "stable"),
            techniques_used=session_data.get("techniques_used", []),
            homework_given=session_data.get("homework", []),
            homework_completed=[],
            crisis_events=session_data.get("crisis_events", 0),
            max_risk_level=session_data.get("max_risk_level", 0),
            progress_notes=session_data.get("progress_notes", ""),
            next_session_focus=session_data.get("next_session_focus", [])
        )

        # 프로필 업데이트
        self.update_profile_from_session(user_id, memory)

        return memory

    def get_recent_sessions(
        self,
        user_id: str,
        limit: int = 5
    ) -> List[SessionMemory]:
        """최근 세션 조회"""
        sessions = self.session_memories.get(user_id, [])
        return sessions[:limit]

    def update_homework_status(
        self,
        user_id: str,
        session_id: str,
        completed_homework: List[str]
    ):
        """과제 완료 상태 업데이트"""
        sessions = self.session_memories.get(user_id, [])

        for session in sessions:
            if session.session_id == session_id:
                session.homework_completed = completed_homework
                break

        self._save_data()

    def add_identified_strength(self, user_id: str, strength: str):
        """발견된 강점 추가"""
        profile = self.get_or_create_profile(user_id)

        if strength not in profile.identified_strengths:
            profile.identified_strengths.append(strength)
            self._save_data()

    def add_coping_strategy(self, user_id: str, strategy: str):
        """효과적인 대처 전략 추가"""
        profile = self.get_or_create_profile(user_id)

        if strategy not in profile.coping_strategies:
            profile.coping_strategies.append(strategy)
            self._save_data()

    # =========================================================================
    # Technique Effectiveness Tracking
    # =========================================================================

    def record_technique_usage(
        self,
        user_id: str,
        technique: str,
        context: Dict[str, Any],
        effectiveness_score: Optional[float] = None
    ):
        """기법 사용 기록"""
        if technique not in self.technique_effectiveness:
            self.technique_effectiveness[technique] = TechniqueEffectiveness(
                technique_name=technique
            )

        te = self.technique_effectiveness[technique]
        te.usage_count += 1

        # 효과 점수 업데이트 (이동 평균)
        if effectiveness_score is not None:
            old_rate = te.emotional_improvement_rate
            te.emotional_improvement_rate = (
                (old_rate * (te.usage_count - 1) + effectiveness_score) / te.usage_count
            )

        # 상황별 효과 기록
        concern = context.get("concern")
        if concern:
            if concern not in te.effectiveness_by_concern:
                te.effectiveness_by_concern[concern] = 0.0
            if effectiveness_score:
                # 이동 평균
                old = te.effectiveness_by_concern[concern]
                te.effectiveness_by_concern[concern] = (old + effectiveness_score) / 2

        # 신뢰도 업데이트
        te.confidence = min(1.0, te.usage_count / 20)

        self._save_data()

    def get_recommended_techniques(
        self,
        user_id: str,
        current_concern: Optional[str] = None,
        current_emotion: Optional[str] = None,
        limit: int = 3
    ) -> List[Tuple[str, float]]:
        """추천 기법 조회"""
        profile = self.get_or_create_profile(user_id)

        # 개인 효과성 기반 점수
        technique_scores = {}

        for technique, effectiveness in profile.effective_techniques.items():
            score = effectiveness

            # 글로벌 효과성 반영
            if technique in self.technique_effectiveness:
                global_te = self.technique_effectiveness[technique]

                # 상황별 보너스
                if current_concern and current_concern in global_te.effectiveness_by_concern:
                    score += global_te.effectiveness_by_concern[current_concern] * 0.3

                if current_emotion and current_emotion in global_te.effectiveness_by_emotion:
                    score += global_te.effectiveness_by_emotion[current_emotion] * 0.2

            technique_scores[technique] = score

        # 정렬 및 반환
        sorted_techniques = sorted(
            technique_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_techniques[:limit]

    # =========================================================================
    # Analytics & Reports
    # =========================================================================

    def generate_progress_report(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """진행 상황 리포트 생성"""
        profile = self.get_or_create_profile(user_id)
        sessions = self.session_memories.get(user_id, [])

        # 기간 필터
        cutoff = datetime.now() - timedelta(days=days)
        recent_sessions = [s for s in sessions if s.date > cutoff]

        if not recent_sessions:
            return {
                "status": "no_data",
                "message": f"최근 {days}일간 상담 기록이 없습니다."
            }

        # 감정 분석
        trajectory = self.pattern_analyzer.analyze_emotional_trajectory(recent_sessions)

        # 기법 효과
        effectiveness = self.pattern_analyzer.analyze_technique_effectiveness(recent_sessions)
        top_techniques = sorted(
            effectiveness.items(),
            key=lambda x: x[1].emotional_improvement_rate,
            reverse=True
        )[:3]

        # 과제 완료율
        total_homework = sum(len(s.homework_given) for s in recent_sessions)
        completed_homework = sum(len(s.homework_completed) for s in recent_sessions)
        homework_rate = completed_homework / total_homework if total_homework > 0 else 0

        return {
            "period_days": days,
            "total_sessions": len(recent_sessions),
            "total_duration_minutes": sum(s.duration_minutes for s in recent_sessions),
            "emotional_trajectory": trajectory,
            "top_concerns": list(profile.recurring_concerns.keys())[:5],
            "effective_techniques": [
                {"name": t[0], "score": round(t[1].emotional_improvement_rate, 2)}
                for t in top_techniques
            ],
            "homework_completion_rate": round(homework_rate, 2),
            "crisis_events": sum(s.crisis_events for s in recent_sessions),
            "overall_progress": profile.overall_progress,
            "identified_strengths": profile.identified_strengths[:5],
            "recommendations": self._generate_recommendations(profile, trajectory)
        }

    def _generate_recommendations(
        self,
        profile: UserLongTermProfile,
        trajectory: Dict[str, Any]
    ) -> List[str]:
        """권장사항 생성"""
        recommendations = []

        if trajectory["trend"] == "improving":
            recommendations.append("긍정적 변화를 유지하고 있습니다. 현재 전략을 계속 활용하세요.")
        elif trajectory["trend"] == "declining":
            recommendations.append("전문가와의 추가 상담을 고려해보세요.")
            recommendations.append("위기 상황 시 1393 자살예방상담전화 이용을 권장합니다.")

        if profile.effective_techniques:
            top_technique = max(profile.effective_techniques.items(), key=lambda x: x[1])[0]
            recommendations.append(f"'{top_technique}' 기법이 효과적이었습니다. 계속 활용해보세요.")

        if profile.trigger_patterns:
            recommendations.append(f"트리거 상황({', '.join(profile.trigger_patterns[:2])})에 주의하세요.")

        return recommendations

    # =========================================================================
    # Persistence
    # =========================================================================

    def _save_data(self):
        """데이터 저장"""
        if not self.storage_path:
            return

        try:
            data = {
                "profiles": {},
                "sessions": {},
                "technique_effectiveness": {}
            }

            # 프로필 직렬화
            for user_id, profile in self.user_profiles.items():
                data["profiles"][user_id] = {
                    "user_id": profile.user_id,
                    "created_at": profile.created_at.isoformat(),
                    "last_updated": profile.last_updated.isoformat(),
                    "preferred_name": profile.preferred_name,
                    "age_range": profile.age_range,
                    "recurring_concerns": profile.recurring_concerns,
                    "trigger_patterns": profile.trigger_patterns,
                    "coping_strategies": profile.coping_strategies,
                    "effective_techniques": profile.effective_techniques,
                    "identified_strengths": profile.identified_strengths,
                    "support_system": profile.support_system,
                    "total_sessions": profile.total_sessions,
                    "total_crisis_events": profile.total_crisis_events,
                    "avg_session_duration": profile.avg_session_duration,
                    "overall_progress": profile.overall_progress
                }

            # 세션 직렬화 (최근 20개만)
            for user_id, sessions in self.session_memories.items():
                data["sessions"][user_id] = [
                    {
                        "session_id": s.session_id,
                        "date": s.date.isoformat(),
                        "duration_minutes": s.duration_minutes,
                        "main_concerns": s.main_concerns,
                        "key_insights": s.key_insights,
                        "emotional_state": s.emotional_state,
                        "emotional_shift": s.emotional_shift,
                        "techniques_used": s.techniques_used,
                        "homework_given": s.homework_given,
                        "homework_completed": s.homework_completed,
                        "crisis_events": s.crisis_events,
                        "max_risk_level": s.max_risk_level,
                        "next_session_focus": s.next_session_focus
                    }
                    for s in sessions[:20]
                ]

            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Failed to save long-term memory: {e}")

    def _load_data(self):
        """데이터 로드"""
        import os
        if not self.storage_path or not os.path.exists(self.storage_path):
            return

        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 프로필 로드
            for user_id, profile_data in data.get("profiles", {}).items():
                profile = UserLongTermProfile(
                    user_id=profile_data["user_id"],
                    created_at=datetime.fromisoformat(profile_data["created_at"]),
                    last_updated=datetime.fromisoformat(profile_data["last_updated"]),
                    preferred_name=profile_data.get("preferred_name"),
                    age_range=profile_data.get("age_range"),
                    recurring_concerns=profile_data.get("recurring_concerns", {}),
                    trigger_patterns=profile_data.get("trigger_patterns", []),
                    coping_strategies=profile_data.get("coping_strategies", []),
                    effective_techniques=profile_data.get("effective_techniques", {}),
                    identified_strengths=profile_data.get("identified_strengths", []),
                    support_system=profile_data.get("support_system", []),
                    total_sessions=profile_data.get("total_sessions", 0),
                    total_crisis_events=profile_data.get("total_crisis_events", 0),
                    avg_session_duration=profile_data.get("avg_session_duration", 0.0),
                    overall_progress=profile_data.get("overall_progress", "unknown")
                )
                self.user_profiles[user_id] = profile

            # 세션 로드
            for user_id, sessions_data in data.get("sessions", {}).items():
                sessions = []
                for s in sessions_data:
                    session = SessionMemory(
                        session_id=s["session_id"],
                        user_id=user_id,
                        date=datetime.fromisoformat(s["date"]),
                        duration_minutes=s["duration_minutes"],
                        main_concerns=s["main_concerns"],
                        key_insights=s["key_insights"],
                        emotional_state=s["emotional_state"],
                        emotional_shift=s["emotional_shift"],
                        techniques_used=s["techniques_used"],
                        homework_given=s["homework_given"],
                        homework_completed=s.get("homework_completed", []),
                        crisis_events=s["crisis_events"],
                        max_risk_level=s["max_risk_level"],
                        progress_notes="",
                        next_session_focus=s.get("next_session_focus", [])
                    )
                    sessions.append(session)
                self.session_memories[user_id] = sessions

            logger.info(f"Loaded {len(self.user_profiles)} user profiles")

        except Exception as e:
            logger.error(f"Failed to load long-term memory: {e}")


# =============================================================================
# Singleton & Factory
# =============================================================================

_memory_manager: Optional[LongTermMemoryManager] = None


def get_memory_manager(storage_path: Optional[str] = None) -> LongTermMemoryManager:
    """장기 기억 관리자 싱글톤"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = LongTermMemoryManager(storage_path)
    return _memory_manager


# =============================================================================
# Test
# =============================================================================

if __name__ == "__main__":
    print("=== 장기 기억 관리 시스템 테스트 ===\n")

    manager = LongTermMemoryManager()
    user_id = "test_user_001"

    # 세션 1 생성
    session1 = manager.create_session_memory(
        session_id="session_001",
        user_id=user_id,
        session_data={
            "duration_minutes": 30,
            "main_concerns": ["직장 스트레스", "상사와의 갈등"],
            "key_insights": ["업무 과부하로 인한 스트레스 확인"],
            "emotional_state": "스트레스",
            "emotional_shift": "stable",
            "techniques_used": ["적극적 경청", "감정 반영"],
            "homework": ["하루 5분 호흡 연습"],
            "crisis_events": 0,
            "max_risk_level": 1,
            "next_session_focus": ["스트레스 관리 기법 탐색"]
        }
    )
    print(f"세션 1 생성: {session1.session_id}")

    # 세션 2 생성
    session2 = manager.create_session_memory(
        session_id="session_002",
        user_id=user_id,
        session_data={
            "duration_minutes": 35,
            "main_concerns": ["직장 스트레스", "수면 문제"],
            "key_insights": ["호흡 연습이 도움됨", "수면 패턴 개선 필요"],
            "emotional_state": "불안",
            "emotional_shift": "positive",
            "techniques_used": ["그라운딩", "인지 재구성"],
            "homework": ["수면 일기 작성", "4-7-8 호흡법 연습"],
            "crisis_events": 0,
            "max_risk_level": 0,
            "next_session_focus": ["수면 위생 개선"]
        }
    )
    print(f"세션 2 생성: {session2.session_id}")

    # 강점 추가
    manager.add_identified_strength(user_id, "문제 인식 능력")
    manager.add_coping_strategy(user_id, "호흡 연습")

    # 컨텍스트 생성
    print("\n=== 생성된 컨텍스트 ===")
    context = manager.generate_personalized_context(user_id)
    print(context)

    # 진행 리포트
    print("\n=== 진행 리포트 ===")
    report = manager.generate_progress_report(user_id, days=30)
    print(json.dumps(report, ensure_ascii=False, indent=2))
