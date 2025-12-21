"""
효과성 측정 도구 (Effectiveness Measurement Tools)
치료/상담 효과를 측정하고 추적하는 종합 시스템

기능:
- 치료 전후 비교 (Pre-Post Comparison)
- 증상 변화 추적 (Symptom Change Tracking)
- 회기별 진전도 측정 (Session-by-Session Progress)
- 임상적 유의미한 변화 판정 (Reliable Change Index)
- 결과 측정 도구 (Outcome Measures)
- 효과 크기 계산 (Effect Size)
- 시각화 및 리포트 생성
"""

import logging
import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import statistics

logger = logging.getLogger(__name__)


# =============================================================================
# Enums & Constants
# =============================================================================

class OutcomeCategory(Enum):
    """결과 측정 카테고리"""
    SYMPTOM = "symptom"             # 증상 관련
    FUNCTIONING = "functioning"     # 기능 수준
    WELLBEING = "wellbeing"         # 웰빙/삶의 질
    SATISFACTION = "satisfaction"   # 만족도
    ALLIANCE = "alliance"           # 치료 동맹


class ChangeCategory(Enum):
    """변화 카테고리"""
    RECOVERED = "recovered"         # 회복됨
    IMPROVED = "improved"           # 개선됨
    UNCHANGED = "unchanged"         # 변화 없음
    DETERIORATED = "deteriorated"   # 악화됨


class AssessmentTiming(Enum):
    """평가 시점"""
    BASELINE = "baseline"           # 기저선 (치료 전)
    SESSION = "session"             # 매 회기
    MID_TREATMENT = "mid_treatment" # 치료 중간
    POST_TREATMENT = "post_treatment"  # 치료 후
    FOLLOW_UP_1M = "follow_up_1m"   # 1개월 추적
    FOLLOW_UP_3M = "follow_up_3m"   # 3개월 추적
    FOLLOW_UP_6M = "follow_up_6m"   # 6개월 추적


# =============================================================================
# Outcome Measures (결과 측정 도구)
# =============================================================================

class OutcomeMeasures:
    """결과 측정 도구 모음"""

    def __init__(self):
        self.measures = self._init_measures()

    def _init_measures(self) -> Dict[str, Dict]:
        """표준화된 측정 도구"""
        return {
            # 증상 측정
            "PHQ-9": {
                "name": "Patient Health Questionnaire-9",
                "korean_name": "우울증 선별 검사",
                "category": OutcomeCategory.SYMPTOM,
                "items": 9,
                "scale": "0-3",
                "total_range": (0, 27),
                "clinical_cutoff": 10,
                "severity_levels": {
                    (0, 4): "최소",
                    (5, 9): "경도",
                    (10, 14): "중등도",
                    (15, 19): "중등도-중증",
                    (20, 27): "중증"
                },
                "reliable_change_index": 6,  # RCI 기준
                "mcid": 5,  # Minimal Clinically Important Difference
                "internal_consistency": 0.89,
                "test_retest": 0.84
            },
            "GAD-7": {
                "name": "Generalized Anxiety Disorder-7",
                "korean_name": "범불안장애 선별 검사",
                "category": OutcomeCategory.SYMPTOM,
                "items": 7,
                "scale": "0-3",
                "total_range": (0, 21),
                "clinical_cutoff": 10,
                "severity_levels": {
                    (0, 4): "최소",
                    (5, 9): "경도",
                    (10, 14): "중등도",
                    (15, 21): "중증"
                },
                "reliable_change_index": 5,
                "mcid": 4,
                "internal_consistency": 0.92,
                "test_retest": 0.83
            },
            "K-10": {
                "name": "Kessler Psychological Distress Scale",
                "korean_name": "심리적 고통 척도",
                "category": OutcomeCategory.SYMPTOM,
                "items": 10,
                "scale": "1-5",
                "total_range": (10, 50),
                "clinical_cutoff": 20,
                "severity_levels": {
                    (10, 15): "정상",
                    (16, 21): "경도",
                    (22, 29): "중등도",
                    (30, 50): "중증"
                },
                "reliable_change_index": 7,
                "mcid": 5,
                "internal_consistency": 0.93,
                "test_retest": 0.81
            },
            # 삶의 질/웰빙
            "WEMWBS": {
                "name": "Warwick-Edinburgh Mental Well-being Scale",
                "korean_name": "정신적 웰빙 척도",
                "category": OutcomeCategory.WELLBEING,
                "items": 14,
                "scale": "1-5",
                "total_range": (14, 70),
                "clinical_cutoff": None,  # 높을수록 좋음
                "direction": "positive",  # 높은 점수가 좋음
                "reliable_change_index": 8,
                "mcid": 3,
                "internal_consistency": 0.89,
                "test_retest": 0.83
            },
            "SWLS": {
                "name": "Satisfaction With Life Scale",
                "korean_name": "삶의 만족도 척도",
                "category": OutcomeCategory.WELLBEING,
                "items": 5,
                "scale": "1-7",
                "total_range": (5, 35),
                "clinical_cutoff": None,
                "direction": "positive",
                "severity_levels": {
                    (5, 9): "극히 불만족",
                    (10, 14): "불만족",
                    (15, 19): "약간 불만족",
                    (20, 20): "중립",
                    (21, 25): "약간 만족",
                    (26, 30): "만족",
                    (31, 35): "극히 만족"
                },
                "reliable_change_index": 5,
                "mcid": 3,
                "internal_consistency": 0.87,
                "test_retest": 0.82
            },
            # 기능 수준
            "WSAS": {
                "name": "Work and Social Adjustment Scale",
                "korean_name": "직업/사회적 적응 척도",
                "category": OutcomeCategory.FUNCTIONING,
                "items": 5,
                "scale": "0-8",
                "total_range": (0, 40),
                "clinical_cutoff": 10,
                "severity_levels": {
                    (0, 9): "경미한 손상",
                    (10, 19): "중등도 손상",
                    (20, 40): "심각한 손상"
                },
                "reliable_change_index": 6,
                "mcid": 4,
                "internal_consistency": 0.88,
                "test_retest": 0.79
            },
            # 치료 동맹
            "WAI-SR": {
                "name": "Working Alliance Inventory - Short Revised",
                "korean_name": "작업 동맹 척도 단축형",
                "category": OutcomeCategory.ALLIANCE,
                "items": 12,
                "scale": "1-5",
                "total_range": (12, 60),
                "clinical_cutoff": None,
                "direction": "positive",
                "subscales": {
                    "goal": (4, 20),
                    "task": (4, 20),
                    "bond": (4, 20)
                },
                "internal_consistency": 0.93,
                "test_retest": 0.80
            },
            # 상담 만족도
            "CSQ-8": {
                "name": "Client Satisfaction Questionnaire-8",
                "korean_name": "내담자 만족도 질문지",
                "category": OutcomeCategory.SATISFACTION,
                "items": 8,
                "scale": "1-4",
                "total_range": (8, 32),
                "clinical_cutoff": None,
                "direction": "positive",
                "internal_consistency": 0.93,
                "test_retest": 0.87
            }
        }

    def get_measure(self, measure_name: str) -> Optional[Dict]:
        """측정 도구 정보 반환"""
        return self.measures.get(measure_name)

    def get_measures_by_category(self, category: OutcomeCategory) -> List[str]:
        """카테고리별 측정 도구 목록"""
        return [
            name for name, info in self.measures.items()
            if info.get("category") == category
        ]

    def interpret_score(self, measure_name: str, score: int) -> Dict:
        """점수 해석"""
        measure = self.get_measure(measure_name)
        if not measure:
            return {"error": "Unknown measure"}

        result = {
            "measure": measure_name,
            "score": score,
            "max_score": measure["total_range"][1]
        }

        # 심각도 수준 결정
        severity_levels = measure.get("severity_levels", {})
        for range_tuple, level in severity_levels.items():
            if range_tuple[0] <= score <= range_tuple[1]:
                result["severity"] = level
                break

        # 임상적 컷오프 확인
        cutoff = measure.get("clinical_cutoff")
        if cutoff:
            direction = measure.get("direction", "negative")
            if direction == "positive":
                result["clinical_significance"] = "above_cutoff" if score >= cutoff else "below_cutoff"
            else:
                result["clinical_significance"] = "above_cutoff" if score >= cutoff else "below_cutoff"
                result["above_clinical_threshold"] = score >= cutoff

        return result


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class AssessmentScore:
    """평가 점수"""
    assessment_id: str
    participant_id: str
    measure_name: str
    timing: AssessmentTiming
    session_number: Optional[int]
    total_score: int
    item_scores: Dict[int, int]
    timestamp: datetime
    subscale_scores: Optional[Dict[str, int]] = None


@dataclass
class ChangeAnalysis:
    """변화 분석 결과"""
    participant_id: str
    measure_name: str
    pre_score: int
    post_score: int
    raw_change: int
    percent_change: float
    rci: float  # Reliable Change Index
    is_reliable_change: bool
    change_category: ChangeCategory
    effect_size: float
    clinical_significance: bool
    analysis_date: datetime


@dataclass
class SessionProgress:
    """회기별 진전"""
    participant_id: str
    session_number: int
    scores: Dict[str, int]  # measure_name: score
    change_from_baseline: Dict[str, int]
    on_track: bool
    predicted_outcome: str
    timestamp: datetime


@dataclass
class TreatmentOutcome:
    """치료 결과"""
    participant_id: str
    treatment_start: datetime
    treatment_end: datetime
    total_sessions: int
    primary_outcome: ChangeAnalysis
    secondary_outcomes: List[ChangeAnalysis]
    response_status: str  # responder, partial_responder, non_responder
    remission_status: bool
    overall_rating: str
    summary: str


# =============================================================================
# Reliable Change Index Calculator
# =============================================================================

class ReliableChangeCalculator:
    """신뢰로운 변화 지수 (RCI) 계산기"""

    def __init__(self, outcome_measures: OutcomeMeasures):
        self.measures = outcome_measures

    def calculate_rci(
        self,
        measure_name: str,
        pre_score: int,
        post_score: int,
        sd: float = None,
        reliability: float = None
    ) -> Tuple[float, bool]:
        """
        RCI 계산

        RCI = (X2 - X1) / SE_diff
        SE_diff = SD * sqrt(2) * sqrt(1 - reliability)

        Args:
            measure_name: 측정 도구 이름
            pre_score: 사전 점수
            post_score: 사후 점수
            sd: 표준편차 (없으면 기본값 사용)
            reliability: 신뢰도 (없으면 도구의 test-retest 사용)

        Returns:
            Tuple[RCI 값, 유의미한 변화 여부]
        """
        measure = self.measures.get_measure(measure_name)
        if not measure:
            raise ValueError(f"Unknown measure: {measure_name}")

        # 기본값 사용
        if reliability is None:
            reliability = measure.get("test_retest", 0.80)

        # SD 추정 (범위의 1/4 사용)
        if sd is None:
            score_range = measure["total_range"][1] - measure["total_range"][0]
            sd = score_range / 4

        # 측정의 표준오차
        se_measurement = sd * math.sqrt(1 - reliability)

        # 차이 점수의 표준오차
        se_diff = math.sqrt(2) * se_measurement

        # RCI 계산
        raw_change = post_score - pre_score
        rci = raw_change / se_diff if se_diff > 0 else 0

        # 유의미한 변화 판정 (|RCI| > 1.96)
        is_reliable = abs(rci) > 1.96

        return rci, is_reliable

    def calculate_effect_size(
        self,
        pre_score: int,
        post_score: int,
        sd_pre: float
    ) -> float:
        """
        효과 크기 계산 (Cohen's d)

        d = (M_post - M_pre) / SD_pre
        """
        if sd_pre == 0:
            return 0.0

        d = (post_score - pre_score) / sd_pre
        return round(d, 2)

    def interpret_effect_size(self, d: float) -> str:
        """효과 크기 해석"""
        abs_d = abs(d)
        if abs_d < 0.2:
            return "무시할 수준"
        elif abs_d < 0.5:
            return "작은 효과"
        elif abs_d < 0.8:
            return "중간 효과"
        else:
            return "큰 효과"


# =============================================================================
# Progress Tracker
# =============================================================================

class ProgressTracker:
    """진전도 추적기"""

    def __init__(self, outcome_measures: OutcomeMeasures):
        self.measures = outcome_measures
        self.rci_calculator = ReliableChangeCalculator(outcome_measures)
        self.assessments: Dict[str, List[AssessmentScore]] = {}  # participant_id: scores
        self.expected_trajectory: Dict[str, List[float]] = {}

    def add_assessment(self, score: AssessmentScore) -> None:
        """평가 점수 추가"""
        if score.participant_id not in self.assessments:
            self.assessments[score.participant_id] = []

        self.assessments[score.participant_id].append(score)

        # 시간순 정렬
        self.assessments[score.participant_id].sort(
            key=lambda x: x.timestamp
        )

    def get_baseline_score(
        self,
        participant_id: str,
        measure_name: str
    ) -> Optional[int]:
        """기저선 점수 조회"""
        scores = self.assessments.get(participant_id, [])
        for score in scores:
            if (score.measure_name == measure_name and
                score.timing == AssessmentTiming.BASELINE):
                return score.total_score
        return None

    def calculate_session_progress(
        self,
        participant_id: str,
        session_number: int,
        current_scores: Dict[str, int]
    ) -> SessionProgress:
        """회기별 진전도 계산"""
        change_from_baseline = {}

        for measure_name, current_score in current_scores.items():
            baseline = self.get_baseline_score(participant_id, measure_name)
            if baseline is not None:
                change_from_baseline[measure_name] = current_score - baseline

        # 예상 궤적과 비교하여 on_track 판정
        # 일반적으로 50% 증상 감소는 8-12회기 예상
        expected_reduction_per_session = 0.05  # 5%
        expected_total_reduction = expected_reduction_per_session * session_number

        on_track = True
        for measure_name, change in change_from_baseline.items():
            baseline = self.get_baseline_score(participant_id, measure_name)
            if baseline and baseline > 0:
                actual_reduction = abs(change) / baseline
                # 음수 변화가 개선 (증상 감소)
                if change > 0:  # 악화
                    on_track = False
                elif actual_reduction < expected_total_reduction * 0.5:
                    on_track = False

        # 예상 결과
        if on_track:
            predicted_outcome = "호전 예상"
        else:
            predicted_outcome = "추가 개입 필요"

        return SessionProgress(
            participant_id=participant_id,
            session_number=session_number,
            scores=current_scores,
            change_from_baseline=change_from_baseline,
            on_track=on_track,
            predicted_outcome=predicted_outcome,
            timestamp=datetime.now()
        )

    def analyze_change(
        self,
        participant_id: str,
        measure_name: str,
        pre_timing: AssessmentTiming = AssessmentTiming.BASELINE,
        post_timing: AssessmentTiming = AssessmentTiming.POST_TREATMENT
    ) -> Optional[ChangeAnalysis]:
        """변화 분석"""
        scores = self.assessments.get(participant_id, [])

        pre_score = None
        post_score = None

        for score in scores:
            if score.measure_name == measure_name:
                if score.timing == pre_timing:
                    pre_score = score.total_score
                if score.timing == post_timing:
                    post_score = score.total_score

        if pre_score is None or post_score is None:
            return None

        measure = self.measures.get_measure(measure_name)
        if not measure:
            return None

        # 변화량 계산
        raw_change = post_score - pre_score
        percent_change = (raw_change / pre_score * 100) if pre_score > 0 else 0

        # RCI 계산
        rci, is_reliable = self.rci_calculator.calculate_rci(
            measure_name, pre_score, post_score
        )

        # 효과 크기 계산
        score_range = measure["total_range"][1] - measure["total_range"][0]
        sd_estimate = score_range / 4
        effect_size = self.rci_calculator.calculate_effect_size(
            pre_score, post_score, sd_estimate
        )

        # 변화 카테고리 결정
        cutoff = measure.get("clinical_cutoff")
        direction = measure.get("direction", "negative")

        if direction == "negative":  # 낮을수록 좋음 (증상 척도)
            if is_reliable and raw_change < 0:
                if cutoff and post_score < cutoff:
                    change_category = ChangeCategory.RECOVERED
                else:
                    change_category = ChangeCategory.IMPROVED
            elif is_reliable and raw_change > 0:
                change_category = ChangeCategory.DETERIORATED
            else:
                change_category = ChangeCategory.UNCHANGED

            clinical_significance = (
                cutoff is not None and
                pre_score >= cutoff and
                post_score < cutoff
            )
        else:  # 높을수록 좋음 (웰빙 척도)
            if is_reliable and raw_change > 0:
                change_category = ChangeCategory.IMPROVED
            elif is_reliable and raw_change < 0:
                change_category = ChangeCategory.DETERIORATED
            else:
                change_category = ChangeCategory.UNCHANGED

            clinical_significance = is_reliable and raw_change > 0

        return ChangeAnalysis(
            participant_id=participant_id,
            measure_name=measure_name,
            pre_score=pre_score,
            post_score=post_score,
            raw_change=raw_change,
            percent_change=round(percent_change, 1),
            rci=round(rci, 2),
            is_reliable_change=is_reliable,
            change_category=change_category,
            effect_size=effect_size,
            clinical_significance=clinical_significance,
            analysis_date=datetime.now()
        )

    def get_score_trajectory(
        self,
        participant_id: str,
        measure_name: str
    ) -> List[Dict]:
        """점수 궤적 조회"""
        scores = self.assessments.get(participant_id, [])
        trajectory = []

        for score in scores:
            if score.measure_name == measure_name:
                trajectory.append({
                    "timestamp": score.timestamp.isoformat(),
                    "timing": score.timing.value,
                    "session_number": score.session_number,
                    "score": score.total_score
                })

        return trajectory


# =============================================================================
# Treatment Outcome Evaluator
# =============================================================================

class TreatmentOutcomeEvaluator:
    """치료 결과 평가기"""

    def __init__(self, progress_tracker: ProgressTracker):
        self.tracker = progress_tracker
        self.measures = progress_tracker.measures

    def evaluate_treatment_outcome(
        self,
        participant_id: str,
        primary_measure: str,
        secondary_measures: List[str],
        treatment_info: Dict
    ) -> TreatmentOutcome:
        """치료 결과 종합 평가"""
        # 주요 결과 분석
        primary_analysis = self.tracker.analyze_change(
            participant_id, primary_measure
        )

        # 부차 결과 분석
        secondary_analyses = []
        for measure in secondary_measures:
            analysis = self.tracker.analyze_change(participant_id, measure)
            if analysis:
                secondary_analyses.append(analysis)

        # 반응 상태 결정
        response_status = self._determine_response_status(
            primary_analysis, secondary_analyses
        )

        # 관해 상태 결정
        remission_status = self._check_remission(
            participant_id, primary_measure
        )

        # 전체 평가
        overall_rating = self._calculate_overall_rating(
            primary_analysis, secondary_analyses, response_status, remission_status
        )

        # 요약 생성
        summary = self._generate_summary(
            primary_analysis, secondary_analyses, response_status, remission_status
        )

        return TreatmentOutcome(
            participant_id=participant_id,
            treatment_start=treatment_info.get("start_date", datetime.now()),
            treatment_end=treatment_info.get("end_date", datetime.now()),
            total_sessions=treatment_info.get("total_sessions", 0),
            primary_outcome=primary_analysis,
            secondary_outcomes=secondary_analyses,
            response_status=response_status,
            remission_status=remission_status,
            overall_rating=overall_rating,
            summary=summary
        )

    def _determine_response_status(
        self,
        primary: Optional[ChangeAnalysis],
        secondary: List[ChangeAnalysis]
    ) -> str:
        """반응 상태 결정"""
        if not primary:
            return "unknown"

        # 주요 결과 50% 이상 개선 = responder
        if primary.percent_change <= -50:
            return "responder"
        elif primary.percent_change <= -25:
            return "partial_responder"
        else:
            return "non_responder"

    def _check_remission(
        self,
        participant_id: str,
        measure_name: str
    ) -> bool:
        """관해 상태 확인"""
        scores = self.tracker.assessments.get(participant_id, [])
        measure = self.measures.get_measure(measure_name)

        if not measure:
            return False

        cutoff = measure.get("clinical_cutoff")
        if cutoff is None:
            return False

        # 최종 점수 확인
        post_scores = [
            s for s in scores
            if s.measure_name == measure_name and
               s.timing == AssessmentTiming.POST_TREATMENT
        ]

        if post_scores:
            latest_score = post_scores[-1].total_score
            direction = measure.get("direction", "negative")

            if direction == "negative":
                return latest_score < cutoff
            else:
                return latest_score >= cutoff

        return False

    def _calculate_overall_rating(
        self,
        primary: Optional[ChangeAnalysis],
        secondary: List[ChangeAnalysis],
        response_status: str,
        remission_status: bool
    ) -> str:
        """전체 평가 등급"""
        if remission_status and response_status == "responder":
            return "excellent"
        elif response_status == "responder":
            return "good"
        elif response_status == "partial_responder":
            return "moderate"
        elif primary and primary.change_category == ChangeCategory.DETERIORATED:
            return "poor"
        else:
            return "minimal"

    def _generate_summary(
        self,
        primary: Optional[ChangeAnalysis],
        secondary: List[ChangeAnalysis],
        response_status: str,
        remission_status: bool
    ) -> str:
        """결과 요약 생성"""
        if not primary:
            return "평가 데이터 부족"

        summary_parts = []

        # 주요 결과
        if primary.change_category == ChangeCategory.RECOVERED:
            summary_parts.append(
                f"주요 증상({primary.measure_name})에서 임상적으로 유의미한 회복을 보였습니다."
            )
        elif primary.change_category == ChangeCategory.IMPROVED:
            summary_parts.append(
                f"주요 증상({primary.measure_name})에서 신뢰로운 개선을 보였습니다 "
                f"({primary.percent_change:.1f}% 변화, 효과크기 d={primary.effect_size})."
            )
        elif primary.change_category == ChangeCategory.UNCHANGED:
            summary_parts.append(
                f"주요 증상({primary.measure_name})에서 유의미한 변화가 없었습니다."
            )
        else:
            summary_parts.append(
                f"주의: 주요 증상({primary.measure_name})이 악화되었습니다."
            )

        # 반응 상태
        response_text = {
            "responder": "치료 반응자로 분류됩니다.",
            "partial_responder": "부분적 치료 반응자로 분류됩니다.",
            "non_responder": "치료 비반응자로 분류됩니다."
        }
        summary_parts.append(response_text.get(response_status, ""))

        # 관해 상태
        if remission_status:
            summary_parts.append("임상적 관해 기준을 충족했습니다.")

        return " ".join(summary_parts)


# =============================================================================
# Report Generator
# =============================================================================

class EffectivenessReportGenerator:
    """효과성 리포트 생성기"""

    def __init__(
        self,
        outcome_measures: OutcomeMeasures,
        progress_tracker: ProgressTracker,
        outcome_evaluator: TreatmentOutcomeEvaluator
    ):
        self.measures = outcome_measures
        self.tracker = progress_tracker
        self.evaluator = outcome_evaluator

    def generate_individual_report(
        self,
        participant_id: str,
        treatment_info: Dict
    ) -> Dict:
        """개인 효과성 리포트 생성"""
        report = {
            "participant_id": participant_id,
            "report_date": datetime.now().isoformat(),
            "treatment_summary": treatment_info,
            "outcome_measures": {},
            "trajectories": {},
            "overall_outcome": None
        }

        # 각 측정 도구별 분석
        for score in self.tracker.assessments.get(participant_id, []):
            measure = score.measure_name
            if measure not in report["outcome_measures"]:
                analysis = self.tracker.analyze_change(participant_id, measure)
                if analysis:
                    report["outcome_measures"][measure] = {
                        "pre_score": analysis.pre_score,
                        "post_score": analysis.post_score,
                        "change": analysis.raw_change,
                        "percent_change": analysis.percent_change,
                        "rci": analysis.rci,
                        "reliable_change": analysis.is_reliable_change,
                        "change_category": analysis.change_category.value,
                        "effect_size": analysis.effect_size,
                        "clinical_significance": analysis.clinical_significance
                    }

            if measure not in report["trajectories"]:
                report["trajectories"][measure] = self.tracker.get_score_trajectory(
                    participant_id, measure
                )

        # 전체 결과
        primary_measure = treatment_info.get("primary_measure", "PHQ-9")
        secondary_measures = treatment_info.get("secondary_measures", ["GAD-7"])

        outcome = self.evaluator.evaluate_treatment_outcome(
            participant_id,
            primary_measure,
            secondary_measures,
            treatment_info
        )

        report["overall_outcome"] = {
            "response_status": outcome.response_status,
            "remission_status": outcome.remission_status,
            "overall_rating": outcome.overall_rating,
            "summary": outcome.summary
        }

        return report

    def generate_aggregate_report(
        self,
        participant_ids: List[str],
        treatment_info: Dict
    ) -> Dict:
        """집단 효과성 리포트 생성"""
        report = {
            "report_date": datetime.now().isoformat(),
            "sample_size": len(participant_ids),
            "treatment_info": treatment_info,
            "aggregate_outcomes": {},
            "response_rates": {},
            "effect_sizes": {}
        }

        primary_measure = treatment_info.get("primary_measure", "PHQ-9")

        # 모든 참여자의 분석 수집
        analyses = []
        for pid in participant_ids:
            analysis = self.tracker.analyze_change(pid, primary_measure)
            if analysis:
                analyses.append(analysis)

        if not analyses:
            return report

        # 평균 변화
        pre_scores = [a.pre_score for a in analyses]
        post_scores = [a.post_score for a in analyses]
        changes = [a.raw_change for a in analyses]
        effect_sizes = [a.effect_size for a in analyses]

        report["aggregate_outcomes"][primary_measure] = {
            "mean_pre": round(statistics.mean(pre_scores), 2),
            "sd_pre": round(statistics.stdev(pre_scores), 2) if len(pre_scores) > 1 else 0,
            "mean_post": round(statistics.mean(post_scores), 2),
            "sd_post": round(statistics.stdev(post_scores), 2) if len(post_scores) > 1 else 0,
            "mean_change": round(statistics.mean(changes), 2),
            "mean_effect_size": round(statistics.mean(effect_sizes), 2)
        }

        # 반응률
        recovered = len([a for a in analyses if a.change_category == ChangeCategory.RECOVERED])
        improved = len([a for a in analyses if a.change_category == ChangeCategory.IMPROVED])
        unchanged = len([a for a in analyses if a.change_category == ChangeCategory.UNCHANGED])
        deteriorated = len([a for a in analyses if a.change_category == ChangeCategory.DETERIORATED])

        total = len(analyses)
        report["response_rates"] = {
            "recovered": round(recovered / total * 100, 1),
            "improved": round(improved / total * 100, 1),
            "unchanged": round(unchanged / total * 100, 1),
            "deteriorated": round(deteriorated / total * 100, 1),
            "overall_improvement_rate": round((recovered + improved) / total * 100, 1)
        }

        # 효과 크기 분류
        large_effect = len([a for a in analyses if abs(a.effect_size) >= 0.8])
        medium_effect = len([a for a in analyses if 0.5 <= abs(a.effect_size) < 0.8])
        small_effect = len([a for a in analyses if 0.2 <= abs(a.effect_size) < 0.5])

        report["effect_sizes"] = {
            "large_effect_count": large_effect,
            "medium_effect_count": medium_effect,
            "small_effect_count": small_effect,
            "mean_effect_size": round(statistics.mean(effect_sizes), 2),
            "effect_size_interpretation": self._interpret_mean_effect_size(
                statistics.mean(effect_sizes)
            )
        }

        return report

    def _interpret_mean_effect_size(self, d: float) -> str:
        """평균 효과 크기 해석"""
        abs_d = abs(d)
        if abs_d >= 0.8:
            return "큰 효과: 임상적으로 매우 의미 있는 개선"
        elif abs_d >= 0.5:
            return "중간 효과: 임상적으로 의미 있는 개선"
        elif abs_d >= 0.2:
            return "작은 효과: 통계적으로 유의하나 임상적 의미 제한적"
        else:
            return "무시할 수준: 실질적 변화 없음"


# =============================================================================
# Effectiveness Measurement System (통합 클래스)
# =============================================================================

class EffectivenessMeasurementSystem:
    """효과성 측정 시스템 통합 클래스"""

    def __init__(self):
        self.outcome_measures = OutcomeMeasures()
        self.progress_tracker = ProgressTracker(self.outcome_measures)
        self.outcome_evaluator = TreatmentOutcomeEvaluator(self.progress_tracker)
        self.report_generator = EffectivenessReportGenerator(
            self.outcome_measures,
            self.progress_tracker,
            self.outcome_evaluator
        )

        logger.info("효과성 측정 시스템 초기화 완료")

    def record_assessment(
        self,
        participant_id: str,
        measure_name: str,
        timing: AssessmentTiming,
        total_score: int,
        item_scores: Dict[int, int] = None,
        session_number: int = None
    ) -> AssessmentScore:
        """평가 점수 기록"""
        import uuid

        score = AssessmentScore(
            assessment_id=str(uuid.uuid4()),
            participant_id=participant_id,
            measure_name=measure_name,
            timing=timing,
            session_number=session_number,
            total_score=total_score,
            item_scores=item_scores or {},
            timestamp=datetime.now()
        )

        self.progress_tracker.add_assessment(score)
        return score

    def get_score_interpretation(self, measure_name: str, score: int) -> Dict:
        """점수 해석"""
        return self.outcome_measures.interpret_score(measure_name, score)

    def calculate_change(
        self,
        participant_id: str,
        measure_name: str
    ) -> Optional[ChangeAnalysis]:
        """변화 분석"""
        return self.progress_tracker.analyze_change(participant_id, measure_name)

    def get_session_progress(
        self,
        participant_id: str,
        session_number: int,
        current_scores: Dict[str, int]
    ) -> SessionProgress:
        """회기별 진전도"""
        return self.progress_tracker.calculate_session_progress(
            participant_id, session_number, current_scores
        )

    def get_score_trajectory(
        self,
        participant_id: str,
        measure_name: str
    ) -> List[Dict]:
        """점수 궤적"""
        return self.progress_tracker.get_score_trajectory(participant_id, measure_name)

    def evaluate_treatment(
        self,
        participant_id: str,
        treatment_info: Dict
    ) -> TreatmentOutcome:
        """치료 결과 평가"""
        primary_measure = treatment_info.get("primary_measure", "PHQ-9")
        secondary_measures = treatment_info.get("secondary_measures", [])

        return self.outcome_evaluator.evaluate_treatment_outcome(
            participant_id, primary_measure, secondary_measures, treatment_info
        )

    def generate_individual_report(
        self,
        participant_id: str,
        treatment_info: Dict
    ) -> Dict:
        """개인 리포트"""
        return self.report_generator.generate_individual_report(
            participant_id, treatment_info
        )

    def generate_aggregate_report(
        self,
        participant_ids: List[str],
        treatment_info: Dict
    ) -> Dict:
        """집단 리포트"""
        return self.report_generator.generate_aggregate_report(
            participant_ids, treatment_info
        )

    def get_available_measures(self) -> Dict[str, List[str]]:
        """사용 가능한 측정 도구 목록"""
        result = {}
        for category in OutcomeCategory:
            result[category.value] = self.outcome_measures.get_measures_by_category(category)
        return result

    def get_module_summary(self) -> Dict:
        """모듈 요약"""
        return {
            "name": "효과성 측정 도구",
            "version": "1.0.0",
            "components": {
                "outcome_measures": f"표준화된 측정 도구 ({len(self.outcome_measures.measures)}개)",
                "progress_tracker": "진전도 추적 (RCI, 효과 크기)",
                "outcome_evaluator": "치료 결과 평가 (반응률, 관해)",
                "report_generator": "리포트 생성 (개인/집단)"
            },
            "available_measures": list(self.outcome_measures.measures.keys()),
            "assessment_timings": [t.value for t in AssessmentTiming],
            "change_categories": [c.value for c in ChangeCategory],
            "metrics": [
                "Reliable Change Index (RCI)",
                "Effect Size (Cohen's d)",
                "Clinical Significance",
                "Response/Remission Rates"
            ]
        }


# =============================================================================
# Factory & Test
# =============================================================================

def get_effectiveness_system() -> EffectivenessMeasurementSystem:
    """효과성 측정 시스템 인스턴스 생성"""
    return EffectivenessMeasurementSystem()


if __name__ == "__main__":
    # 테스트
    system = get_effectiveness_system()

    print("=" * 60)
    print("효과성 측정 도구 테스트")
    print("=" * 60)

    # 모듈 요약
    summary = system.get_module_summary()
    print(f"\n모듈: {summary['name']} v{summary['version']}")
    print("\n구성요소:")
    for key, value in summary['components'].items():
        print(f"  - {key}: {value}")

    print(f"\n사용 가능한 측정 도구: {summary['available_measures']}")

    # 평가 기록 테스트
    print("\n\n--- 평가 기록 테스트 ---")
    participant_id = "P001"

    # 기저선 (사전)
    system.record_assessment(
        participant_id=participant_id,
        measure_name="PHQ-9",
        timing=AssessmentTiming.BASELINE,
        total_score=18  # 중등도-중증
    )

    # 치료 후 (사후)
    system.record_assessment(
        participant_id=participant_id,
        measure_name="PHQ-9",
        timing=AssessmentTiming.POST_TREATMENT,
        total_score=8  # 경도
    )

    # 점수 해석
    print("\n사전 점수 해석:")
    interp = system.get_score_interpretation("PHQ-9", 18)
    print(f"  점수: {interp['score']}/{interp['max_score']}")
    print(f"  심각도: {interp.get('severity', 'N/A')}")

    # 변화 분석
    print("\n\n--- 변화 분석 테스트 ---")
    change = system.calculate_change(participant_id, "PHQ-9")
    if change:
        print(f"사전 점수: {change.pre_score}")
        print(f"사후 점수: {change.post_score}")
        print(f"변화량: {change.raw_change} ({change.percent_change}%)")
        print(f"RCI: {change.rci}")
        print(f"신뢰로운 변화: {change.is_reliable_change}")
        print(f"변화 카테고리: {change.change_category.value}")
        print(f"효과 크기: {change.effect_size}")
        print(f"임상적 유의미성: {change.clinical_significance}")

    # 치료 결과 평가
    print("\n\n--- 치료 결과 평가 테스트 ---")
    treatment_info = {
        "start_date": datetime.now() - timedelta(weeks=8),
        "end_date": datetime.now(),
        "total_sessions": 8,
        "primary_measure": "PHQ-9",
        "secondary_measures": []
    }

    outcome = system.evaluate_treatment(participant_id, treatment_info)
    print(f"반응 상태: {outcome.response_status}")
    print(f"관해 상태: {outcome.remission_status}")
    print(f"전체 평가: {outcome.overall_rating}")
    print(f"요약: {outcome.summary}")

    print("\n\n테스트 완료!")
