"""
상담 효과 측정 시스템 (Outcome Measurement System)

표준화된 심리 척도를 활용한 상담 효과 측정 및 추적

기능:
1. PHQ-9 (우울) 자동 평가
2. GAD-7 (불안) 자동 평가
3. 세션별 감정 변화 추적
4. 장기 치료 효과 분석
5. 시각화 데이터 생성
6. 자동 알림 트리거
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


# =============================================================================
# 평가 척도 정의
# =============================================================================

class AssessmentType(Enum):
    """평가 유형"""
    PHQ9 = "PHQ-9"           # 우울
    GAD7 = "GAD-7"           # 불안
    PSS = "PSS-10"           # 스트레스
    WHO5 = "WHO-5"           # 웰빙
    SCS = "SCS"              # 자기자비
    SESSION_MOOD = "mood"    # 세션 기분


class Severity(Enum):
    """심각도 수준"""
    MINIMAL = "minimal"
    MILD = "mild"
    MODERATE = "moderate"
    MODERATELY_SEVERE = "moderately_severe"
    SEVERE = "severe"


@dataclass
class AssessmentResult:
    """평가 결과"""
    assessment_type: AssessmentType
    score: int
    max_score: int
    severity: Severity
    percentile: float
    responses: List[int]
    interpretation: str
    recommendations: List[str]
    flags: List[str]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ProgressData:
    """진행 추적 데이터"""
    user_id: str
    assessment_type: AssessmentType
    scores: List[Tuple[datetime, int]]  # (시간, 점수)
    trend: str  # improving, stable, declining
    change_percentage: float
    clinical_significance: bool  # 임상적으로 유의미한 변화
    reliable_change: bool  # 신뢰로운 변화 (RCI)


# =============================================================================
# PHQ-9 우울 척도
# =============================================================================

class PHQ9Assessment:
    """
    PHQ-9 (Patient Health Questionnaire-9)
    우울증 선별 도구

    점수 해석:
    0-4: 우울 증상 없음/최소
    5-9: 경미한 우울
    10-14: 중등도 우울
    15-19: 중등도-심각 우울
    20-27: 심각한 우울
    """

    QUESTIONS = [
        "일 또는 여가 활동을 하는 데 흥미나 즐거움을 느끼지 못함",
        "기분이 가라앉거나, 우울하거나, 희망이 없음",
        "잠이 들기 어렵거나 자주 깸, 또는 너무 많이 잠",
        "피곤하다고 느끼거나 기운이 거의 없음",
        "입맛이 없거나 과식을 함",
        "자신을 부정적으로 봄 - 실패자라고 느끼거나 자신 또는 가족을 실망시킴",
        "신문을 읽거나 TV를 보는 것과 같은 일에 집중하기 어려움",
        "다른 사람들이 눈치챌 정도로 거동이나 말이 느림. 또는 반대로, 평소보다 많이 움직이거나 안절부절못함",
        "차라리 죽는 것이 낫겠다는 생각 또는 자해에 대한 생각"
    ]

    RESPONSE_OPTIONS = {
        0: "전혀 없음",
        1: "며칠 동안",
        2: "1주일 이상",
        3: "거의 매일"
    }

    SEVERITY_CUTOFFS = [
        (0, 4, Severity.MINIMAL, "우울 증상 없음 또는 최소"),
        (5, 9, Severity.MILD, "경미한 우울 증상"),
        (10, 14, Severity.MODERATE, "중등도 우울 증상"),
        (15, 19, Severity.MODERATELY_SEVERE, "중등도-심각 우울 증상"),
        (20, 27, Severity.SEVERE, "심각한 우울 증상")
    ]

    # 신뢰로운 변화 지수 (Reliable Change Index)
    RCI_THRESHOLD = 6  # PHQ-9의 RCI

    def evaluate(self, responses: List[int]) -> AssessmentResult:
        """
        PHQ-9 평가 수행

        Args:
            responses: 9개 문항 응답 (각 0-3)

        Returns:
            AssessmentResult 객체
        """
        if len(responses) != 9:
            raise ValueError("PHQ-9 requires exactly 9 responses")

        if not all(0 <= r <= 3 for r in responses):
            raise ValueError("Each response must be between 0 and 3")

        total_score = sum(responses)
        severity, interpretation = self._get_severity(total_score)

        # 특별 플래그
        flags = []

        # 문항 9 (자살 사고) 체크
        if responses[8] > 0:
            flags.append("SUICIDE_IDEATION_POSITIVE")
            if responses[8] >= 2:
                flags.append("SUICIDE_IDEATION_FREQUENT")

        # 주요 증상 체크 (문항 1, 2)
        if responses[0] >= 2 or responses[1] >= 2:
            flags.append("CORE_SYMPTOMS_ELEVATED")

        recommendations = self._get_recommendations(severity, flags)

        return AssessmentResult(
            assessment_type=AssessmentType.PHQ9,
            score=total_score,
            max_score=27,
            severity=severity,
            percentile=self._estimate_percentile(total_score),
            responses=responses,
            interpretation=interpretation,
            recommendations=recommendations,
            flags=flags
        )

    def _get_severity(self, score: int) -> Tuple[Severity, str]:
        """점수에 따른 심각도 결정"""
        for min_score, max_score, severity, interpretation in self.SEVERITY_CUTOFFS:
            if min_score <= score <= max_score:
                return severity, interpretation
        return Severity.SEVERE, "심각한 우울 증상"

    def _estimate_percentile(self, score: int) -> float:
        """점수의 백분위 추정"""
        # 일반 인구 기준 대략적 추정
        if score <= 4:
            return 0.5  # 50%
        elif score <= 9:
            return 0.75
        elif score <= 14:
            return 0.90
        elif score <= 19:
            return 0.95
        else:
            return 0.99

    def _get_recommendations(
        self,
        severity: Severity,
        flags: List[str]
    ) -> List[str]:
        """심각도에 따른 권장사항"""
        recommendations = []

        if "SUICIDE_IDEATION_POSITIVE" in flags:
            recommendations.append("⚠️ 자살 사고 양성 - 안전 평가 필요")

        if severity == Severity.MINIMAL:
            recommendations.append("현재 상태 유지")
            recommendations.append("정기적 자기 모니터링 권장")

        elif severity == Severity.MILD:
            recommendations.append("자기 관리 전략 활용")
            recommendations.append("행동 활성화 권장")
            recommendations.append("2-4주 후 재평가")

        elif severity == Severity.MODERATE:
            recommendations.append("전문 상담 권장")
            recommendations.append("인지행동치료 고려")
            recommendations.append("1-2주 후 재평가")

        elif severity in [Severity.MODERATELY_SEVERE, Severity.SEVERE]:
            recommendations.append("정신건강의학과 진료 강력 권장")
            recommendations.append("약물치료 + 심리치료 병행 고려")
            recommendations.append("정기적 모니터링 필수")

        return recommendations

    def get_interactive_questions(self) -> List[Dict[str, Any]]:
        """대화형 평가용 질문 목록"""
        return [
            {
                "question_number": i + 1,
                "question_text": q,
                "korean_prompt": f"지난 2주 동안, '{q}'이(가) 얼마나 자주 있었나요?",
                "options": self.RESPONSE_OPTIONS
            }
            for i, q in enumerate(self.QUESTIONS)
        ]


# =============================================================================
# GAD-7 불안 척도
# =============================================================================

class GAD7Assessment:
    """
    GAD-7 (Generalized Anxiety Disorder-7)
    범불안장애 선별 도구

    점수 해석:
    0-4: 불안 증상 없음/최소
    5-9: 경미한 불안
    10-14: 중등도 불안
    15-21: 심각한 불안
    """

    QUESTIONS = [
        "초조하거나 불안하거나 조마조마하게 느낀다",
        "걱정하는 것을 멈추거나 조절할 수가 없다",
        "여러 가지 것들에 대해 걱정을 너무 많이 한다",
        "편하게 있기가 어렵다",
        "너무 안절부절못해서 가만히 있기가 어렵다",
        "쉽게 짜증이 나거나 쉽게 성을 내게 된다",
        "마치 끔찍한 일이 일어날 것처럼 두렵게 느껴진다"
    ]

    RESPONSE_OPTIONS = {
        0: "전혀 없음",
        1: "며칠 동안",
        2: "1주일 이상",
        3: "거의 매일"
    }

    SEVERITY_CUTOFFS = [
        (0, 4, Severity.MINIMAL, "불안 증상 없음 또는 최소"),
        (5, 9, Severity.MILD, "경미한 불안 증상"),
        (10, 14, Severity.MODERATE, "중등도 불안 증상"),
        (15, 21, Severity.SEVERE, "심각한 불안 증상")
    ]

    RCI_THRESHOLD = 4  # GAD-7의 RCI

    def evaluate(self, responses: List[int]) -> AssessmentResult:
        """GAD-7 평가 수행"""
        if len(responses) != 7:
            raise ValueError("GAD-7 requires exactly 7 responses")

        if not all(0 <= r <= 3 for r in responses):
            raise ValueError("Each response must be between 0 and 3")

        total_score = sum(responses)
        severity, interpretation = self._get_severity(total_score)

        flags = []

        # 핵심 증상 체크 (조절 불능 걱정)
        if responses[1] >= 2:
            flags.append("UNCONTROLLABLE_WORRY")

        # 신체 증상 체크
        if responses[3] >= 2 or responses[4] >= 2:
            flags.append("SOMATIC_SYMPTOMS")

        recommendations = self._get_recommendations(severity, flags)

        return AssessmentResult(
            assessment_type=AssessmentType.GAD7,
            score=total_score,
            max_score=21,
            severity=severity,
            percentile=self._estimate_percentile(total_score),
            responses=responses,
            interpretation=interpretation,
            recommendations=recommendations,
            flags=flags
        )

    def _get_severity(self, score: int) -> Tuple[Severity, str]:
        """점수에 따른 심각도"""
        for min_score, max_score, severity, interpretation in self.SEVERITY_CUTOFFS:
            if min_score <= score <= max_score:
                return severity, interpretation
        return Severity.SEVERE, "심각한 불안 증상"

    def _estimate_percentile(self, score: int) -> float:
        """백분위 추정"""
        if score <= 4:
            return 0.5
        elif score <= 9:
            return 0.75
        elif score <= 14:
            return 0.90
        else:
            return 0.97

    def _get_recommendations(
        self,
        severity: Severity,
        flags: List[str]
    ) -> List[str]:
        """권장사항"""
        recommendations = []

        if severity == Severity.MINIMAL:
            recommendations.append("현재 상태 유지")
            recommendations.append("스트레스 관리 기술 활용")

        elif severity == Severity.MILD:
            recommendations.append("이완 훈련 권장 (호흡법, 점진적 근육 이완)")
            recommendations.append("걱정 시간 정하기 기법")
            recommendations.append("2-4주 후 재평가")

        elif severity == Severity.MODERATE:
            recommendations.append("전문 상담 권장")
            recommendations.append("인지행동치료 고려")
            recommendations.append("노출 기반 치료 고려")

        elif severity == Severity.SEVERE:
            recommendations.append("정신건강의학과 진료 권장")
            recommendations.append("약물치료 고려")
            recommendations.append("정기적 모니터링")

        if "SOMATIC_SYMPTOMS" in flags:
            recommendations.append("신체 증상 관리 (호흡법, 이완)")

        return recommendations

    def get_interactive_questions(self) -> List[Dict[str, Any]]:
        """대화형 평가용 질문"""
        return [
            {
                "question_number": i + 1,
                "question_text": q,
                "korean_prompt": f"지난 2주 동안, '{q}'이(가) 얼마나 자주 있었나요?",
                "options": self.RESPONSE_OPTIONS
            }
            for i, q in enumerate(self.QUESTIONS)
        ]


# =============================================================================
# 세션 기분 평가
# =============================================================================

class SessionMoodTracker:
    """세션별 기분 추적"""

    MOOD_SCALE = {
        1: "매우 나쁨",
        2: "나쁨",
        3: "조금 나쁨",
        4: "보통",
        5: "조금 좋음",
        6: "좋음",
        7: "매우 좋음"
    }

    EMOTION_CATEGORIES = [
        "불안", "우울", "분노", "슬픔", "두려움",
        "스트레스", "외로움", "희망", "평온", "기쁨"
    ]

    def record_session_mood(
        self,
        pre_score: int,
        post_score: int,
        primary_emotion: str,
        emotion_intensity: int  # 1-10
    ) -> Dict[str, Any]:
        """
        세션 기분 기록

        Args:
            pre_score: 세션 전 기분 (1-7)
            post_score: 세션 후 기분 (1-7)
            primary_emotion: 주요 감정
            emotion_intensity: 감정 강도 (1-10)

        Returns:
            기분 기록 딕셔너리
        """
        change = post_score - pre_score
        change_percentage = (change / pre_score * 100) if pre_score > 0 else 0

        return {
            "timestamp": datetime.now().isoformat(),
            "pre_score": pre_score,
            "post_score": post_score,
            "change": change,
            "change_percentage": round(change_percentage, 1),
            "improvement": change > 0,
            "primary_emotion": primary_emotion,
            "emotion_intensity": emotion_intensity,
            "pre_label": self.MOOD_SCALE.get(pre_score, ""),
            "post_label": self.MOOD_SCALE.get(post_score, "")
        }


# =============================================================================
# 진행 추적기
# =============================================================================

class OutcomeTracker:
    """상담 효과 추적기"""

    def __init__(self):
        self.phq9 = PHQ9Assessment()
        self.gad7 = GAD7Assessment()
        self.mood_tracker = SessionMoodTracker()

        # 사용자별 평가 이력
        self.assessment_history: Dict[str, Dict[str, List[AssessmentResult]]] = defaultdict(
            lambda: defaultdict(list)
        )

        # 세션별 기분 이력
        self.mood_history: Dict[str, List[Dict]] = defaultdict(list)

    def record_assessment(
        self,
        user_id: str,
        assessment_type: AssessmentType,
        responses: List[int]
    ) -> AssessmentResult:
        """
        평가 기록

        Args:
            user_id: 사용자 ID
            assessment_type: 평가 유형
            responses: 응답 리스트

        Returns:
            평가 결과
        """
        if assessment_type == AssessmentType.PHQ9:
            result = self.phq9.evaluate(responses)
        elif assessment_type == AssessmentType.GAD7:
            result = self.gad7.evaluate(responses)
        else:
            raise ValueError(f"Unsupported assessment type: {assessment_type}")

        self.assessment_history[user_id][assessment_type.value].append(result)

        return result

    def record_session_mood(
        self,
        user_id: str,
        **mood_data
    ) -> Dict[str, Any]:
        """세션 기분 기록"""
        record = self.mood_tracker.record_session_mood(**mood_data)
        self.mood_history[user_id].append(record)
        return record

    def calculate_progress(
        self,
        user_id: str,
        assessment_type: AssessmentType,
        days: int = 30
    ) -> Optional[ProgressData]:
        """
        진행 상황 계산

        Args:
            user_id: 사용자 ID
            assessment_type: 평가 유형
            days: 분석 기간

        Returns:
            ProgressData 객체
        """
        history = self.assessment_history[user_id].get(assessment_type.value, [])

        if len(history) < 2:
            return None

        cutoff = datetime.now() - timedelta(days=days)
        recent = [h for h in history if h.timestamp > cutoff]

        if len(recent) < 2:
            return None

        scores = [(h.timestamp, h.score) for h in recent]
        scores.sort(key=lambda x: x[0])

        first_score = scores[0][1]
        last_score = scores[-1][1]
        change = last_score - first_score
        change_pct = (change / first_score * 100) if first_score > 0 else 0

        # 트렌드 결정
        if change <= -3:
            trend = "improving"  # 점수 감소 = 호전
        elif change >= 3:
            trend = "declining"
        else:
            trend = "stable"

        # RCI (신뢰로운 변화 지수) 계산
        rci_threshold = self.phq9.RCI_THRESHOLD if assessment_type == AssessmentType.PHQ9 else self.gad7.RCI_THRESHOLD
        reliable_change = abs(change) >= rci_threshold

        # 임상적 유의미성 (severity 수준 변화)
        clinical_sig = recent[0].severity != recent[-1].severity

        return ProgressData(
            user_id=user_id,
            assessment_type=assessment_type,
            scores=scores,
            trend=trend,
            change_percentage=round(change_pct, 1),
            clinical_significance=clinical_sig,
            reliable_change=reliable_change
        )

    def get_visualization_data(
        self,
        user_id: str,
        assessment_type: Optional[AssessmentType] = None
    ) -> Dict[str, Any]:
        """시각화용 데이터 생성"""

        data = {
            "user_id": user_id,
            "generated_at": datetime.now().isoformat(),
            "assessments": {},
            "mood_trend": []
        }

        # 평가 데이터
        if assessment_type:
            types = [assessment_type]
        else:
            types = [AssessmentType.PHQ9, AssessmentType.GAD7]

        for atype in types:
            history = self.assessment_history[user_id].get(atype.value, [])
            if history:
                data["assessments"][atype.value] = {
                    "scores": [
                        {
                            "date": h.timestamp.isoformat(),
                            "score": h.score,
                            "severity": h.severity.value
                        }
                        for h in history
                    ],
                    "latest": {
                        "score": history[-1].score,
                        "severity": history[-1].severity.value,
                        "interpretation": history[-1].interpretation
                    }
                }

        # 기분 트렌드
        mood_data = self.mood_history.get(user_id, [])
        if mood_data:
            data["mood_trend"] = [
                {
                    "date": m["timestamp"],
                    "pre": m["pre_score"],
                    "post": m["post_score"],
                    "change": m["change"]
                }
                for m in mood_data[-30:]  # 최근 30개
            ]

        return data

    def generate_progress_report(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """진행 리포트 생성"""

        report = {
            "user_id": user_id,
            "period_days": days,
            "generated_at": datetime.now().isoformat(),
            "assessments": {},
            "mood_summary": {},
            "overall_progress": "unknown",
            "recommendations": [],
            "alerts": []
        }

        # 각 평가 분석
        for atype in [AssessmentType.PHQ9, AssessmentType.GAD7]:
            progress = self.calculate_progress(user_id, atype, days)
            if progress:
                report["assessments"][atype.value] = {
                    "trend": progress.trend,
                    "change_percentage": progress.change_percentage,
                    "reliable_change": progress.reliable_change,
                    "clinical_significance": progress.clinical_significance
                }

                # 알림 생성
                if progress.trend == "declining" and progress.reliable_change:
                    report["alerts"].append(
                        f"⚠️ {atype.value}: 유의미한 악화 감지 ({progress.change_percentage:+.1f}%)"
                    )

        # 기분 요약
        mood_data = self.mood_history.get(user_id, [])
        cutoff = datetime.now() - timedelta(days=days)
        recent_moods = [
            m for m in mood_data
            if datetime.fromisoformat(m["timestamp"]) > cutoff
        ]

        if recent_moods:
            avg_pre = statistics.mean([m["pre_score"] for m in recent_moods])
            avg_post = statistics.mean([m["post_score"] for m in recent_moods])
            avg_change = statistics.mean([m["change"] for m in recent_moods])

            report["mood_summary"] = {
                "session_count": len(recent_moods),
                "average_pre_session": round(avg_pre, 1),
                "average_post_session": round(avg_post, 1),
                "average_improvement": round(avg_change, 1),
                "improvement_rate": round(
                    len([m for m in recent_moods if m["change"] > 0]) / len(recent_moods) * 100, 1
                )
            }

        # 전체 진행 상황
        trends = [v.get("trend") for v in report["assessments"].values()]
        if "declining" in trends:
            report["overall_progress"] = "declining"
            report["recommendations"].append("전문가와 상담 강화 권장")
        elif all(t == "improving" for t in trends if t):
            report["overall_progress"] = "improving"
            report["recommendations"].append("현재 접근법 유지 권장")
        else:
            report["overall_progress"] = "stable"
            report["recommendations"].append("정기적 모니터링 유지")

        return report


# =============================================================================
# 자동 평가 트리거
# =============================================================================

class AssessmentScheduler:
    """평가 일정 관리"""

    def __init__(self):
        self.user_schedules: Dict[str, Dict[str, datetime]] = defaultdict(dict)
        self.default_intervals = {
            AssessmentType.PHQ9: timedelta(days=14),
            AssessmentType.GAD7: timedelta(days=14),
        }

    def check_assessment_due(
        self,
        user_id: str,
        assessment_type: AssessmentType
    ) -> bool:
        """평가 시기 확인"""
        last_assessment = self.user_schedules[user_id].get(assessment_type.value)

        if not last_assessment:
            return True  # 첫 평가

        interval = self.default_intervals.get(assessment_type, timedelta(days=14))
        return datetime.now() - last_assessment >= interval

    def record_assessment_completed(
        self,
        user_id: str,
        assessment_type: AssessmentType
    ):
        """평가 완료 기록"""
        self.user_schedules[user_id][assessment_type.value] = datetime.now()

    def get_pending_assessments(
        self,
        user_id: str
    ) -> List[AssessmentType]:
        """대기 중인 평가 목록"""
        pending = []
        for atype in [AssessmentType.PHQ9, AssessmentType.GAD7]:
            if self.check_assessment_due(user_id, atype):
                pending.append(atype)
        return pending


# =============================================================================
# 통합 효과 측정 시스템
# =============================================================================

class OutcomeMeasurementSystem:
    """통합 효과 측정 시스템"""

    def __init__(self):
        self.tracker = OutcomeTracker()
        self.scheduler = AssessmentScheduler()

    def conduct_assessment(
        self,
        user_id: str,
        assessment_type: AssessmentType,
        responses: List[int]
    ) -> Dict[str, Any]:
        """
        평가 수행 및 결과 반환

        Args:
            user_id: 사용자 ID
            assessment_type: 평가 유형
            responses: 응답 리스트

        Returns:
            평가 결과 및 분석
        """
        # 평가 수행
        result = self.tracker.record_assessment(user_id, assessment_type, responses)

        # 일정 기록
        self.scheduler.record_assessment_completed(user_id, assessment_type)

        # 진행 상황 분석
        progress = self.tracker.calculate_progress(user_id, assessment_type)

        return {
            "result": {
                "score": result.score,
                "max_score": result.max_score,
                "severity": result.severity.value,
                "interpretation": result.interpretation,
                "recommendations": result.recommendations,
                "flags": result.flags
            },
            "progress": {
                "trend": progress.trend if progress else None,
                "change_percentage": progress.change_percentage if progress else None,
                "reliable_change": progress.reliable_change if progress else None
            } if progress else None
        }

    def get_assessment_prompt(
        self,
        assessment_type: AssessmentType
    ) -> Dict[str, Any]:
        """평가 진행용 프롬프트 데이터"""
        if assessment_type == AssessmentType.PHQ9:
            questions = self.tracker.phq9.get_interactive_questions()
            intro = "지난 2주 동안의 기분을 평가해 볼까요? 9개의 질문에 답해주세요."
        elif assessment_type == AssessmentType.GAD7:
            questions = self.tracker.gad7.get_interactive_questions()
            intro = "지난 2주 동안의 불안 상태를 평가해 볼까요? 7개의 질문에 답해주세요."
        else:
            raise ValueError(f"Unsupported: {assessment_type}")

        return {
            "type": assessment_type.value,
            "intro": intro,
            "questions": questions,
            "instructions": "각 질문에 0(전혀 없음)부터 3(거의 매일)까지 답해주세요."
        }

    def check_and_suggest_assessment(
        self,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """평가 필요 여부 확인 및 제안"""
        pending = self.scheduler.get_pending_assessments(user_id)

        if not pending:
            return None

        # 우선순위: PHQ-9 > GAD-7
        priority = pending[0]

        return {
            "suggested_assessment": priority.value,
            "reason": f"마지막 {priority.value} 평가 이후 2주가 지났습니다.",
            "prompt": f"정기적인 {priority.value} 평가를 진행해 볼까요?"
        }

    def get_user_dashboard(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """사용자 대시보드 데이터"""
        return {
            "visualization": self.tracker.get_visualization_data(user_id),
            "progress_report": self.tracker.generate_progress_report(user_id),
            "pending_assessments": [
                a.value for a in self.scheduler.get_pending_assessments(user_id)
            ]
        }


# =============================================================================
# 팩토리 함수
# =============================================================================

_outcome_system: Optional[OutcomeMeasurementSystem] = None

def get_outcome_system() -> OutcomeMeasurementSystem:
    """효과 측정 시스템 싱글톤"""
    global _outcome_system
    if _outcome_system is None:
        _outcome_system = OutcomeMeasurementSystem()
    return _outcome_system


# =============================================================================
# 테스트
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("상담 효과 측정 시스템 테스트")
    print("=" * 60)

    system = get_outcome_system()
    user_id = "test_user_001"

    # PHQ-9 테스트
    print("\n[PHQ-9 평가 테스트]")
    phq9_responses = [1, 2, 1, 2, 1, 1, 1, 0, 0]  # 경미한 우울
    result = system.conduct_assessment(user_id, AssessmentType.PHQ9, phq9_responses)
    print(f"점수: {result['result']['score']}/27")
    print(f"심각도: {result['result']['severity']}")
    print(f"해석: {result['result']['interpretation']}")
    print(f"권장사항: {result['result']['recommendations']}")

    # GAD-7 테스트
    print("\n[GAD-7 평가 테스트]")
    gad7_responses = [2, 2, 2, 1, 1, 1, 1]  # 중등도 불안
    result = system.conduct_assessment(user_id, AssessmentType.GAD7, gad7_responses)
    print(f"점수: {result['result']['score']}/21")
    print(f"심각도: {result['result']['severity']}")
    print(f"해석: {result['result']['interpretation']}")

    # 두 번째 평가 (진행 추적용)
    print("\n[두 번째 PHQ-9 평가]")
    phq9_responses_2 = [1, 1, 1, 1, 1, 0, 0, 0, 0]  # 호전
    result = system.conduct_assessment(user_id, AssessmentType.PHQ9, phq9_responses_2)
    print(f"점수: {result['result']['score']}/27")
    if result['progress']:
        print(f"진행 트렌드: {result['progress']['trend']}")
        print(f"변화율: {result['progress']['change_percentage']}%")

    # 대시보드
    print("\n[사용자 대시보드]")
    dashboard = system.get_user_dashboard(user_id)
    print(f"전체 진행: {dashboard['progress_report']['overall_progress']}")
    print(f"권장사항: {dashboard['progress_report']['recommendations']}")
