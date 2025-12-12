"""
상담 효과 통합 시스템 (Integrated Counseling Effectiveness System)

세 가지 핵심 시스템 통합:
1. 공감 시스템 (Empathy System) - 다차원 공감 분석 및 반응 생성
2. 치료적 질문 시스템 (Therapeutic Questions) - 상황별 질문 추천
3. 세션 구조 시스템 (Session Structure) - 단계별 진행 관리

통합 기능:
- 실시간 상담 품질 분석
- 상황별 개입 추천
- 프롬프트 섹션 자동 생성
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime

# 하위 시스템 임포트
try:
    from .empathy_system import (
        get_empathy_system, IntegratedEmpathySystem,
        get_empathy_prompt_section, EmpathyDimension
    )
except ImportError:
    get_empathy_system = None
    IntegratedEmpathySystem = None
    get_empathy_prompt_section = None

try:
    from .therapeutic_questions import (
        get_question_system, TherapeuticQuestionSystem,
        get_question_prompt_section, QuestionType
    )
except ImportError:
    get_question_system = None
    TherapeuticQuestionSystem = None
    get_question_prompt_section = None

try:
    from .session_structure import (
        get_session_system, SessionStructureSystem,
        get_session_structure_prompt_section, SessionPhase
    )
except ImportError:
    get_session_system = None
    SessionStructureSystem = None
    get_session_structure_prompt_section = None

logger = logging.getLogger(__name__)


# =============================================================================
# 데이터 구조
# =============================================================================

class CounselingQuality(Enum):
    """상담 품질 등급"""
    EXCELLENT = "excellent"    # 90-100
    GOOD = "good"              # 75-89
    ADEQUATE = "adequate"      # 60-74
    NEEDS_IMPROVEMENT = "needs_improvement"  # 40-59
    POOR = "poor"              # 0-39


@dataclass
class EmpathyAnalysis:
    """공감 분석 결과"""
    cognitive_score: float = 0.0
    emotional_score: float = 0.0
    behavioral_score: float = 0.0
    overall_score: float = 0.0
    suggested_response: str = ""
    improvement_tips: List[str] = field(default_factory=list)


@dataclass
class QuestionRecommendation:
    """질문 추천"""
    recommended_questions: List[Dict[str, Any]] = field(default_factory=list)
    question_rationale: str = ""
    timing_advice: str = ""


@dataclass
class SessionProgress:
    """세션 진행 상황"""
    current_phase: str = "opening"
    phase_completion: float = 0.0
    suggested_transitions: List[str] = field(default_factory=list)
    next_tasks: List[str] = field(default_factory=list)


@dataclass
class CounselingEffectivenessReport:
    """상담 효과 종합 리포트"""
    timestamp: datetime = field(default_factory=datetime.now)

    # 품질 점수
    overall_quality_score: float = 0.0
    quality_grade: CounselingQuality = CounselingQuality.ADEQUATE

    # 세부 분석
    empathy_analysis: Optional[EmpathyAnalysis] = None
    question_recommendation: Optional[QuestionRecommendation] = None
    session_progress: Optional[SessionProgress] = None

    # 통합 추천
    recommended_interventions: List[str] = field(default_factory=list)
    prompt_enhancements: str = ""

    # 메타정보
    analysis_confidence: float = 0.8


# =============================================================================
# 통합 상담 효과 시스템
# =============================================================================

class CounselingEffectivenessSystem:
    """
    통합 상담 효과 시스템

    세 가지 하위 시스템을 통합하여 실시간 상담 품질 분석 및 개입 추천 제공
    """

    def __init__(self):
        """초기화"""
        # 하위 시스템 초기화
        self.empathy_system = get_empathy_system() if get_empathy_system else None
        self.question_system = get_question_system() if get_question_system else None
        self.session_system = get_session_system() if get_session_system else None

        # 세션별 상태 관리
        self.session_states: Dict[str, Dict[str, Any]] = {}

        # 가중치 설정
        self.quality_weights = {
            "empathy": 0.40,
            "questioning": 0.30,
            "structure": 0.30
        }

        logger.info("CounselingEffectivenessSystem initialized")
        logger.info(f"  - Empathy system: {'✓' if self.empathy_system else '✗'}")
        logger.info(f"  - Question system: {'✓' if self.question_system else '✗'}")
        logger.info(f"  - Session system: {'✓' if self.session_system else '✗'}")

    def analyze_interaction(
        self,
        session_id: str,
        user_message: str,
        assistant_response: str,
        context: Optional[Dict[str, Any]] = None
    ) -> CounselingEffectivenessReport:
        """
        상호작용 분석

        Args:
            session_id: 세션 ID
            user_message: 사용자 메시지
            assistant_response: 어시스턴트 응답
            context: 추가 컨텍스트

        Returns:
            CounselingEffectivenessReport: 분석 리포트
        """
        context = context or {}
        report = CounselingEffectivenessReport()

        scores = []

        # 1. 공감 분석
        if self.empathy_system:
            try:
                empathy_result = self.empathy_system.analyze_empathy(
                    user_message=user_message,
                    response=assistant_response,
                    context=context
                )

                report.empathy_analysis = EmpathyAnalysis(
                    cognitive_score=empathy_result.get("cognitive_score", 0),
                    emotional_score=empathy_result.get("emotional_score", 0),
                    behavioral_score=empathy_result.get("behavioral_score", 0),
                    overall_score=empathy_result.get("overall_score", 0),
                    suggested_response=empathy_result.get("suggested_response", ""),
                    improvement_tips=empathy_result.get("improvement_tips", [])
                )
                scores.append(("empathy", report.empathy_analysis.overall_score))
            except Exception as e:
                logger.warning(f"Empathy analysis failed: {e}")

        # 2. 질문 추천
        if self.question_system:
            try:
                # 현재 단계에 맞는 질문 추천
                phase = context.get("session_phase", "exploration")
                emotion = context.get("emotion", "")
                topic = context.get("topic", "")

                questions = self.question_system.get_recommended_questions(
                    context={
                        "phase": phase,
                        "emotion": emotion,
                        "topic": topic,
                        "message": user_message
                    },
                    count=3
                )

                report.question_recommendation = QuestionRecommendation(
                    recommended_questions=questions,
                    question_rationale=self._get_question_rationale(phase, emotion),
                    timing_advice=self._get_timing_advice(phase)
                )

                # 질문 적절성 점수 (응답에 질문이 포함되어 있는지 등)
                question_score = self._evaluate_question_usage(assistant_response)
                scores.append(("questioning", question_score))
            except Exception as e:
                logger.warning(f"Question recommendation failed: {e}")

        # 3. 세션 구조 분석
        if self.session_system:
            try:
                # 세션 상태 업데이트
                if session_id not in self.session_states:
                    self.session_states[session_id] = {
                        "turn_count": 0,
                        "phase": "opening",
                        "started_at": datetime.now()
                    }

                state = self.session_states[session_id]
                state["turn_count"] += 1

                # 단계 자동 전환 체크
                new_phase = self._determine_phase(state["turn_count"])
                phase_changed = new_phase != state["phase"]
                state["phase"] = new_phase

                report.session_progress = SessionProgress(
                    current_phase=new_phase,
                    phase_completion=self._calculate_phase_completion(state),
                    suggested_transitions=self._get_transition_suggestions(new_phase, phase_changed),
                    next_tasks=self._get_next_tasks(new_phase)
                )

                # 구조 적절성 점수
                structure_score = self._evaluate_structure_adherence(
                    assistant_response, new_phase
                )
                scores.append(("structure", structure_score))
            except Exception as e:
                logger.warning(f"Session structure analysis failed: {e}")

        # 4. 종합 점수 계산
        if scores:
            weighted_sum = sum(
                score * self.quality_weights.get(category, 0.33)
                for category, score in scores
            )
            total_weight = sum(
                self.quality_weights.get(category, 0.33)
                for category, _ in scores
            )
            report.overall_quality_score = weighted_sum / total_weight if total_weight > 0 else 0

        # 5. 품질 등급 결정
        report.quality_grade = self._determine_quality_grade(report.overall_quality_score)

        # 6. 통합 추천 생성
        report.recommended_interventions = self._generate_interventions(report)

        # 7. 프롬프트 개선 섹션 생성
        report.prompt_enhancements = self._generate_prompt_enhancements(report, context)

        return report

    def _determine_phase(self, turn_count: int) -> str:
        """턴 수에 따른 세션 단계 결정"""
        if turn_count <= 2:
            return "opening"
        elif turn_count <= 6:
            return "exploration"
        elif turn_count <= 12:
            return "working"
        else:
            return "closing"

    def _calculate_phase_completion(self, state: Dict) -> float:
        """단계 완료율 계산"""
        turn = state["turn_count"]
        phase = state["phase"]

        phase_ranges = {
            "opening": (1, 2),
            "exploration": (3, 6),
            "working": (7, 12),
            "closing": (13, 15)
        }

        start, end = phase_ranges.get(phase, (1, 5))
        if turn < start:
            return 0.0
        elif turn >= end:
            return 1.0
        else:
            return (turn - start + 1) / (end - start + 1)

    def _get_transition_suggestions(self, phase: str, phase_changed: bool) -> List[str]:
        """단계 전환 제안"""
        suggestions = []

        if phase_changed:
            phase_intros = {
                "exploration": "이제 문제를 더 깊이 탐색해볼 시간입니다.",
                "working": "함께 해결책을 찾아볼 준비가 되셨나요?",
                "closing": "오늘 대화를 마무리할 시간이 다가오고 있습니다."
            }
            if phase in phase_intros:
                suggestions.append(phase_intros[phase])

        return suggestions

    def _get_next_tasks(self, phase: str) -> List[str]:
        """다음 과제 목록"""
        tasks = {
            "opening": ["라포 형성", "오늘의 주제 확인", "안전 점검"],
            "exploration": ["감정 탐색", "상황 구체화", "패턴 인식"],
            "working": ["통찰 촉진", "대처 전략 탐색", "인지 재구성"],
            "closing": ["핵심 요약", "다음 단계 안내", "격려와 지지"]
        }
        return tasks.get(phase, [])

    def _get_question_rationale(self, phase: str, emotion: str) -> str:
        """질문 추천 근거"""
        rationales = {
            "opening": "라포 형성과 안전 확인을 위한 개방형 질문이 적합합니다.",
            "exploration": "감정과 상황을 깊이 탐색하는 질문이 필요합니다.",
            "working": "통찰과 변화를 촉진하는 질문이 효과적입니다.",
            "closing": "요약과 다음 단계를 확인하는 질문이 좋습니다."
        }
        return rationales.get(phase, "상황에 맞는 개방형 질문을 사용하세요.")

    def _get_timing_advice(self, phase: str) -> str:
        """질문 타이밍 조언"""
        advice = {
            "opening": "내담자가 안정감을 느낀 후 질문하세요.",
            "exploration": "감정 반영 후에 질문하세요.",
            "working": "내담자의 준비도를 확인한 후 질문하세요.",
            "closing": "충분한 시간을 두고 마무리 질문을 하세요."
        }
        return advice.get(phase, "적절한 타이밍을 선택하세요.")

    def _evaluate_question_usage(self, response: str) -> float:
        """응답의 질문 사용 적절성 평가"""
        score = 70.0  # 기본 점수

        # 질문 포함 여부
        if "?" in response or "까요" in response or "나요" in response:
            score += 10

        # 개방형 질문 사용
        open_markers = ["어떻", "무엇", "어떤", "어느"]
        if any(marker in response for marker in open_markers):
            score += 10

        # 질문이 하나만 있는지 (과도한 질문 방지)
        question_count = response.count("?")
        if question_count == 1:
            score += 5
        elif question_count > 2:
            score -= 10

        return min(100, max(0, score))

    def _evaluate_structure_adherence(self, response: str, phase: str) -> float:
        """응답의 구조 준수도 평가"""
        score = 70.0

        phase_markers = {
            "opening": ["안녕", "오늘", "어떻게"],
            "exploration": ["말씀해주신", "느끼", "상황"],
            "working": ["생각", "방법", "시도"],
            "closing": ["오늘", "다음", "감사"]
        }

        markers = phase_markers.get(phase, [])
        marker_count = sum(1 for m in markers if m in response)
        score += marker_count * 5

        return min(100, max(0, score))

    def _determine_quality_grade(self, score: float) -> CounselingQuality:
        """점수에 따른 품질 등급 결정"""
        if score >= 90:
            return CounselingQuality.EXCELLENT
        elif score >= 75:
            return CounselingQuality.GOOD
        elif score >= 60:
            return CounselingQuality.ADEQUATE
        elif score >= 40:
            return CounselingQuality.NEEDS_IMPROVEMENT
        else:
            return CounselingQuality.POOR

    def _generate_interventions(self, report: CounselingEffectivenessReport) -> List[str]:
        """개입 추천 생성"""
        interventions = []

        # 공감 기반 추천
        if report.empathy_analysis:
            if report.empathy_analysis.emotional_score < 60:
                interventions.append("감정 반영을 더 적극적으로 사용하세요")
            if report.empathy_analysis.cognitive_score < 60:
                interventions.append("내담자의 관점을 더 구체적으로 이해하고 표현하세요")

        # 질문 기반 추천
        if report.question_recommendation:
            if report.question_recommendation.recommended_questions:
                q = report.question_recommendation.recommended_questions[0]
                interventions.append(f"추천 질문: {q.get('question', '')}")

        # 세션 진행 기반 추천
        if report.session_progress:
            interventions.extend(report.session_progress.suggested_transitions)

        return interventions[:5]  # 최대 5개

    def _generate_prompt_enhancements(
        self,
        report: CounselingEffectivenessReport,
        context: Dict[str, Any]
    ) -> str:
        """프롬프트 개선 섹션 생성"""
        sections = []

        # 현재 단계 정보
        if report.session_progress:
            sections.append(f"## 현재 세션 단계: {report.session_progress.current_phase}")
            if report.session_progress.next_tasks:
                sections.append(f"다음 과제: {', '.join(report.session_progress.next_tasks)}")

        # 공감 가이드
        if report.empathy_analysis and report.empathy_analysis.improvement_tips:
            sections.append("\n## 공감 가이드")
            for tip in report.empathy_analysis.improvement_tips[:2]:
                sections.append(f"- {tip}")

        # 추천 질문
        if report.question_recommendation and report.question_recommendation.recommended_questions:
            sections.append("\n## 추천 질문")
            for q in report.question_recommendation.recommended_questions[:2]:
                sections.append(f"- {q.get('question', '')}")

        return "\n".join(sections)

    def get_prompt_section(
        self,
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        프롬프트에 추가할 섹션 생성

        Args:
            session_id: 세션 ID
            context: 컨텍스트

        Returns:
            str: 프롬프트 섹션
        """
        sections = []
        context = context or {}

        # 세션 상태
        state = self.session_states.get(session_id, {})
        phase = state.get("phase", "exploration")
        turn_count = state.get("turn_count", 0)

        sections.append(f"## 세션 정보")
        sections.append(f"- 현재 단계: {phase}")
        sections.append(f"- 대화 턴: {turn_count}")

        # 단계별 가이드
        phase_guides = {
            "opening": "라포 형성에 집중하세요. 따뜻한 환영과 안전한 공간 조성이 중요합니다.",
            "exploration": "문제와 감정을 깊이 탐색하세요. 반영 기법을 적극 활용하세요.",
            "working": "통찰을 촉진하고 대처 전략을 함께 탐색하세요.",
            "closing": "핵심 내용을 요약하고, 긍정적 변화를 인정해주세요."
        }
        sections.append(f"\n## 현재 단계 가이드")
        sections.append(phase_guides.get(phase, ""))

        # 추천 질문
        if self.question_system:
            try:
                questions = self.question_system.get_recommended_questions(
                    context={"phase": phase, **context},
                    count=2
                )
                if questions:
                    sections.append(f"\n## 추천 질문")
                    for q in questions:
                        sections.append(f"- {q.get('question', '')}")
            except Exception:
                pass

        return "\n".join(sections)

    def reset_session(self, session_id: str):
        """세션 상태 초기화"""
        if session_id in self.session_states:
            del self.session_states[session_id]


# =============================================================================
# 팩토리 및 편의 함수
# =============================================================================

_effectiveness_system: Optional[CounselingEffectivenessSystem] = None


def get_effectiveness_system() -> CounselingEffectivenessSystem:
    """상담 효과 시스템 인스턴스 반환"""
    global _effectiveness_system
    if _effectiveness_system is None:
        _effectiveness_system = CounselingEffectivenessSystem()
    return _effectiveness_system


def analyze_counseling_effectiveness(
    session_id: str,
    user_message: str,
    assistant_response: str,
    context: Optional[Dict[str, Any]] = None
) -> CounselingEffectivenessReport:
    """
    상담 효과 분석 (편의 함수)
    """
    system = get_effectiveness_system()
    return system.analyze_interaction(
        session_id=session_id,
        user_message=user_message,
        assistant_response=assistant_response,
        context=context
    )


def get_counseling_prompt_section(
    session_id: str,
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    프롬프트 섹션 생성 (편의 함수)
    """
    system = get_effectiveness_system()
    return system.get_prompt_section(session_id, context)


if __name__ == "__main__":
    # 테스트
    logging.basicConfig(level=logging.INFO)

    system = get_effectiveness_system()

    # 테스트 분석
    report = system.analyze_interaction(
        session_id="test_001",
        user_message="요즘 너무 힘들어요. 직장에서 스트레스가 심해요.",
        assistant_response="직장에서 많이 힘드셨군요. 어떤 일들이 특히 스트레스를 주셨나요?",
        context={"emotion": "스트레스"}
    )

    print(f"Overall Score: {report.overall_quality_score:.1f}")
    print(f"Grade: {report.quality_grade.value}")
    print(f"Interventions: {report.recommended_interventions}")

    # 프롬프트 섹션
    prompt_section = system.get_prompt_section("test_001")
    print(f"\nPrompt Section:\n{prompt_section}")
