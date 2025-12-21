"""
구조화된 치료 시스템 (Structured Therapy System)
==============================================

효과적인 심리상담을 위한 구조화된 치료 프레임워크

6가지 핵심 기능:
1. 기저선 평가 필수화 (Baseline Assessment)
2. 매 회기 2문항 체크인 (Session Check-in)
3. 시각적 진전 피드백 (Progress Visualization)
4. 단계별 기법 제공 (Staged Technique Delivery)
5. 숙제 체크 시스템 (Homework System)
6. 사후 추적 알림 (Follow-up Alerts)
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import base64


# ============================================================================
# 1. 기저선 평가 필수화 시스템 (Baseline Assessment System)
# ============================================================================

class AssessmentType(Enum):
    """표준화된 평가 도구 유형"""
    PHQ_9 = "PHQ-9"           # 우울증
    GAD_7 = "GAD-7"           # 범불안장애
    K_10 = "K-10"             # 심리적 디스트레스
    WEMWBS = "WEMWBS"         # 웰빙
    SWLS = "SWLS"             # 삶의 만족도
    WSAS = "WSAS"             # 기능 손상
    PCL_5 = "PCL-5"           # PTSD
    BDI_II = "BDI-II"         # 벡 우울 척도
    BAI = "BAI"               # 벡 불안 척도


@dataclass
class AssessmentItem:
    """평가 문항"""
    question_id: str
    question_text: str
    options: List[Dict[str, Any]]  # [{"value": 0, "label": "전혀 없음"}, ...]
    response: Optional[int] = None


@dataclass
class AssessmentResult:
    """평가 결과"""
    assessment_type: AssessmentType
    client_id: str
    session_id: str
    timestamp: datetime
    responses: Dict[str, int]
    total_score: int
    severity_level: str
    clinical_interpretation: str
    is_baseline: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "assessment_type": self.assessment_type.value,
            "client_id": self.client_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "responses": self.responses,
            "total_score": self.total_score,
            "severity_level": self.severity_level,
            "clinical_interpretation": self.clinical_interpretation,
            "is_baseline": self.is_baseline
        }


class BaselineAssessmentManager:
    """
    기저선 평가 관리자

    첫 회기에 PHQ-9, GAD-7 필수 실시
    치료 효과 측정을 위한 기준점 설정
    """

    # 필수 기저선 평가 도구
    REQUIRED_BASELINE_ASSESSMENTS = [AssessmentType.PHQ_9, AssessmentType.GAD_7]

    def __init__(self):
        self.assessments: Dict[str, List[AssessmentResult]] = {}  # client_id -> results
        self.baseline_completed: Dict[str, Dict[str, bool]] = {}  # client_id -> {assessment: completed}

    def _get_phq9_items(self) -> List[AssessmentItem]:
        """PHQ-9 문항 (우울증 선별 도구)"""
        questions = [
            "일 또는 여가 활동을 하는 것에 대한 흥미나 즐거움을 느끼지 못함",
            "기분이 가라앉거나, 우울하거나, 희망이 없다고 느낌",
            "잠이 들거나 계속 잠을 자는 것이 어렵거나, 또는 잠을 너무 많이 잠",
            "피곤하다고 느끼거나 기운이 거의 없음",
            "입맛이 없거나 과식을 함",
            "자신을 부정적으로 봄 - 혹은 자신이 실패자라고 느끼거나 자신 또는 가족을 실망시킴",
            "신문을 읽거나 텔레비전을 보는 것과 같은 일에 집중하는 것이 어려움",
            "다른 사람들이 주목할 정도로 너무 느리게 움직이거나 말함. 또는 반대로 평상시보다 훨씬 더 많이 움직여서, 안절부절 못하거나 들떠 있음",
            "자신이 죽는 것이 더 낫다고 생각하거나 어떤 식으로든 자신을 해칠 것이라고 생각함"
        ]

        options = [
            {"value": 0, "label": "전혀 없음"},
            {"value": 1, "label": "며칠 동안"},
            {"value": 2, "label": "1주일 이상"},
            {"value": 3, "label": "거의 매일"}
        ]

        return [
            AssessmentItem(
                question_id=f"phq9_{i+1}",
                question_text=q,
                options=options
            ) for i, q in enumerate(questions)
        ]

    def _get_gad7_items(self) -> List[AssessmentItem]:
        """GAD-7 문항 (범불안장애 선별 도구)"""
        questions = [
            "초조하거나, 불안하거나, 조마조마하게 느낌",
            "걱정하는 것을 멈추거나 조절할 수 없음",
            "여러 가지 일들에 대해 너무 많이 걱정함",
            "편하게 있기가 어려움",
            "너무 안절부절 못해서 가만히 있기가 어려움",
            "쉽게 짜증이 나거나 화가 남",
            "무서운 일이 일어날 것 같은 느낌이 들어 두려움"
        ]

        options = [
            {"value": 0, "label": "전혀 없음"},
            {"value": 1, "label": "며칠 동안"},
            {"value": 2, "label": "1주일 이상"},
            {"value": 3, "label": "거의 매일"}
        ]

        return [
            AssessmentItem(
                question_id=f"gad7_{i+1}",
                question_text=q,
                options=options
            ) for i, q in enumerate(questions)
        ]

    def get_assessment_items(self, assessment_type: AssessmentType) -> List[AssessmentItem]:
        """평가 도구별 문항 반환"""
        if assessment_type == AssessmentType.PHQ_9:
            return self._get_phq9_items()
        elif assessment_type == AssessmentType.GAD_7:
            return self._get_gad7_items()
        else:
            raise ValueError(f"지원하지 않는 평가 유형: {assessment_type}")

    def check_baseline_required(self, client_id: str) -> Dict[str, Any]:
        """
        기저선 평가 필수 여부 확인

        Returns:
            {
                "required": bool,
                "missing_assessments": List[AssessmentType],
                "message": str
            }
        """
        if client_id not in self.baseline_completed:
            self.baseline_completed[client_id] = {
                at.value: False for at in self.REQUIRED_BASELINE_ASSESSMENTS
            }

        missing = [
            at for at in self.REQUIRED_BASELINE_ASSESSMENTS
            if not self.baseline_completed[client_id].get(at.value, False)
        ]

        if missing:
            return {
                "required": True,
                "missing_assessments": missing,
                "message": f"첫 상담 시작 전 기저선 평가가 필요합니다. "
                          f"진행할 평가: {', '.join([m.value for m in missing])}"
            }

        return {
            "required": False,
            "missing_assessments": [],
            "message": "기저선 평가가 완료되었습니다."
        }

    def calculate_phq9_score(self, responses: Dict[str, int]) -> Tuple[int, str, str]:
        """PHQ-9 점수 계산 및 해석"""
        total = sum(responses.values())

        if total <= 4:
            severity = "최소"
            interpretation = "우울 증상이 거의 없습니다. 현재 상태를 유지하세요."
        elif total <= 9:
            severity = "경도"
            interpretation = "경미한 우울 증상이 있습니다. 자기관리와 모니터링을 권장합니다."
        elif total <= 14:
            severity = "중등도"
            interpretation = "중등도 우울 증상입니다. 상담 치료가 도움이 될 수 있습니다."
        elif total <= 19:
            severity = "중등도-중증"
            interpretation = "중등도에서 중증 수준의 우울 증상입니다. 전문적 치료가 필요합니다."
        else:
            severity = "중증"
            interpretation = "심한 우울 증상입니다. 즉시 전문적 도움이 필요합니다."

        # 자살 사고 문항(9번) 체크
        if responses.get("phq9_9", 0) > 0:
            interpretation += " ⚠️ 자해/자살 관련 생각이 보고되었습니다. 안전 평가가 필요합니다."

        return total, severity, interpretation

    def calculate_gad7_score(self, responses: Dict[str, int]) -> Tuple[int, str, str]:
        """GAD-7 점수 계산 및 해석"""
        total = sum(responses.values())

        if total <= 4:
            severity = "최소"
            interpretation = "불안 증상이 거의 없습니다."
        elif total <= 9:
            severity = "경도"
            interpretation = "경미한 불안 증상이 있습니다. 이완 기법이 도움이 될 수 있습니다."
        elif total <= 14:
            severity = "중등도"
            interpretation = "중등도 불안 증상입니다. 인지행동치료가 권장됩니다."
        else:
            severity = "중증"
            interpretation = "심한 불안 증상입니다. 전문적 치료가 필요합니다."

        return total, severity, interpretation

    def submit_assessment(
        self,
        client_id: str,
        session_id: str,
        assessment_type: AssessmentType,
        responses: Dict[str, int],
        is_baseline: bool = False
    ) -> AssessmentResult:
        """평가 제출 및 결과 생성"""

        if assessment_type == AssessmentType.PHQ_9:
            total, severity, interpretation = self.calculate_phq9_score(responses)
        elif assessment_type == AssessmentType.GAD_7:
            total, severity, interpretation = self.calculate_gad7_score(responses)
        else:
            raise ValueError(f"지원하지 않는 평가 유형: {assessment_type}")

        result = AssessmentResult(
            assessment_type=assessment_type,
            client_id=client_id,
            session_id=session_id,
            timestamp=datetime.now(),
            responses=responses,
            total_score=total,
            severity_level=severity,
            clinical_interpretation=interpretation,
            is_baseline=is_baseline
        )

        # 저장
        if client_id not in self.assessments:
            self.assessments[client_id] = []
        self.assessments[client_id].append(result)

        # 기저선 완료 표시
        if is_baseline:
            if client_id not in self.baseline_completed:
                self.baseline_completed[client_id] = {}
            self.baseline_completed[client_id][assessment_type.value] = True

        return result

    def get_baseline_summary(self, client_id: str) -> Optional[Dict[str, Any]]:
        """기저선 평가 요약"""
        if client_id not in self.assessments:
            return None

        baseline_results = [
            r for r in self.assessments[client_id] if r.is_baseline
        ]

        if not baseline_results:
            return None

        return {
            "client_id": client_id,
            "baseline_date": min(r.timestamp for r in baseline_results).isoformat(),
            "assessments": [r.to_dict() for r in baseline_results],
            "summary": self._generate_baseline_summary(baseline_results)
        }

    def _generate_baseline_summary(self, results: List[AssessmentResult]) -> str:
        """기저선 평가 요약 텍스트 생성"""
        lines = ["=== 기저선 평가 요약 ===\n"]

        for r in results:
            lines.append(f"• {r.assessment_type.value}: {r.total_score}점 ({r.severity_level})")
            lines.append(f"  → {r.clinical_interpretation}")

        return "\n".join(lines)


# ============================================================================
# 2. 매 회기 2문항 체크인 시스템 (Session Check-in System)
# ============================================================================

@dataclass
class SessionCheckIn:
    """회기 시작 체크인 데이터"""
    client_id: str
    session_id: str
    session_number: int
    timestamp: datetime
    mood_rating: int  # 1-10
    mood_description: str
    session_goal: str
    homework_completed: Optional[bool] = None
    homework_reflection: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "client_id": self.client_id,
            "session_id": self.session_id,
            "session_number": self.session_number,
            "timestamp": self.timestamp.isoformat(),
            "mood_rating": self.mood_rating,
            "mood_description": self.mood_description,
            "session_goal": self.session_goal,
            "homework_completed": self.homework_completed,
            "homework_reflection": self.homework_reflection
        }


class SessionCheckInSystem:
    """
    매 회기 2문항 체크인 시스템

    질문 1: "지난 1주일 동안 기분은 어떠셨나요?" (1-10 척도 + 설명)
    질문 2: "오늘 상담에서 이루고 싶은 목표는 무엇인가요?"
    """

    # 기분 척도 설명
    MOOD_SCALE_DESCRIPTIONS = {
        1: "매우 안 좋음 - 힘든 하루하루",
        2: "안 좋음 - 많이 힘들었음",
        3: "다소 안 좋음 - 어려움이 있었음",
        4: "약간 안 좋음 - 살짝 힘들었음",
        5: "보통 - 괜찮았음",
        6: "약간 좋음 - 조금 나아짐",
        7: "다소 좋음 - 괜찮은 편",
        8: "좋음 - 잘 지냈음",
        9: "매우 좋음 - 활기차게 지냄",
        10: "최고 - 정말 행복했음"
    }

    def __init__(self):
        self.check_ins: Dict[str, List[SessionCheckIn]] = {}  # client_id -> list
        self.session_counts: Dict[str, int] = {}

    def get_check_in_prompts(self, client_id: str, has_homework: bool = False) -> Dict[str, Any]:
        """체크인 질문 프롬프트 반환"""
        session_number = self.session_counts.get(client_id, 0) + 1

        prompts = {
            "session_number": session_number,
            "questions": [
                {
                    "id": "mood",
                    "type": "scale_with_description",
                    "question": "지난 1주일 동안 전반적인 기분은 어떠셨나요?",
                    "scale": {"min": 1, "max": 10},
                    "scale_labels": self.MOOD_SCALE_DESCRIPTIONS,
                    "follow_up": "구체적으로 어떤 점이 그랬나요?"
                },
                {
                    "id": "goal",
                    "type": "open_text",
                    "question": "오늘 상담에서 이루고 싶은 목표나 다루고 싶은 주제가 있으신가요?",
                    "examples": [
                        "최근 있었던 갈등 상황 정리하기",
                        "불안을 다루는 새로운 방법 배우기",
                        "지난 주 숙제 경험 나누기"
                    ]
                }
            ]
        }

        # 숙제가 있는 경우 추가 질문
        if has_homework:
            prompts["questions"].insert(1, {
                "id": "homework",
                "type": "boolean_with_reflection",
                "question": "지난 회기에 드린 숙제를 해보셨나요?",
                "follow_up": "숙제를 하시면서 어떤 경험이나 생각이 드셨나요?"
            })

        return prompts

    def submit_check_in(
        self,
        client_id: str,
        session_id: str,
        mood_rating: int,
        mood_description: str,
        session_goal: str,
        homework_completed: Optional[bool] = None,
        homework_reflection: Optional[str] = None
    ) -> SessionCheckIn:
        """체크인 제출"""

        if not 1 <= mood_rating <= 10:
            raise ValueError("기분 점수는 1-10 사이여야 합니다.")

        # 회기 번호 증가
        if client_id not in self.session_counts:
            self.session_counts[client_id] = 0
        self.session_counts[client_id] += 1

        check_in = SessionCheckIn(
            client_id=client_id,
            session_id=session_id,
            session_number=self.session_counts[client_id],
            timestamp=datetime.now(),
            mood_rating=mood_rating,
            mood_description=mood_description,
            session_goal=session_goal,
            homework_completed=homework_completed,
            homework_reflection=homework_reflection
        )

        if client_id not in self.check_ins:
            self.check_ins[client_id] = []
        self.check_ins[client_id].append(check_in)

        return check_in

    def get_mood_trend(self, client_id: str, last_n: int = 8) -> Dict[str, Any]:
        """최근 N회기 기분 추이"""
        if client_id not in self.check_ins:
            return {"data": [], "trend": "데이터 없음"}

        recent = self.check_ins[client_id][-last_n:]

        if len(recent) < 2:
            trend = "데이터 부족"
            trend_direction = 0
        else:
            first_half = recent[:len(recent)//2]
            second_half = recent[len(recent)//2:]

            first_avg = sum(c.mood_rating for c in first_half) / len(first_half)
            second_avg = sum(c.mood_rating for c in second_half) / len(second_half)

            diff = second_avg - first_avg
            trend_direction = diff

            if diff > 1:
                trend = "개선 중 📈"
            elif diff < -1:
                trend = "주의 필요 📉"
            else:
                trend = "안정적 ➡️"

        return {
            "data": [
                {
                    "session": c.session_number,
                    "rating": c.mood_rating,
                    "date": c.timestamp.strftime("%m/%d")
                }
                for c in recent
            ],
            "trend": trend,
            "trend_value": trend_direction if len(recent) >= 2 else 0,
            "current_average": sum(c.mood_rating for c in recent) / len(recent) if recent else 0
        }

    def generate_session_context(self, client_id: str) -> str:
        """상담 시작 시 컨텍스트 생성"""
        if client_id not in self.check_ins or not self.check_ins[client_id]:
            return "첫 상담 세션입니다."

        latest = self.check_ins[client_id][-1]
        trend = self.get_mood_trend(client_id)

        context_lines = [
            f"=== 회기 {latest.session_number} 체크인 요약 ===",
            f"• 기분 점수: {latest.mood_rating}/10 ({self.MOOD_SCALE_DESCRIPTIONS[latest.mood_rating]})",
            f"• 상세: {latest.mood_description}",
            f"• 오늘 목표: {latest.session_goal}",
            f"• 최근 추이: {trend['trend']} (평균 {trend['current_average']:.1f}점)"
        ]

        if latest.homework_completed is not None:
            status = "완료 ✓" if latest.homework_completed else "미완료"
            context_lines.append(f"• 숙제 상태: {status}")
            if latest.homework_reflection:
                context_lines.append(f"• 숙제 소감: {latest.homework_reflection}")

        return "\n".join(context_lines)


# ============================================================================
# 3. 시각적 진전 피드백 시스템 (Progress Visualization)
# ============================================================================

class ProgressVisualizationSystem:
    """
    시각적 진전 피드백 시스템

    점수 변화 그래프 및 진전 지표 제공
    ASCII 기반 그래프 + 데이터 시각화 지원
    """

    def __init__(self, baseline_manager: BaselineAssessmentManager,
                 check_in_system: SessionCheckInSystem):
        self.baseline_manager = baseline_manager
        self.check_in_system = check_in_system

    def generate_ascii_graph(
        self,
        data_points: List[Tuple[str, float]],
        max_value: float,
        title: str,
        width: int = 40,
        height: int = 10
    ) -> str:
        """ASCII 막대 그래프 생성"""
        if not data_points:
            return "데이터 없음"

        lines = [f"\n{title}", "=" * (width + 15)]

        for label, value in data_points:
            bar_length = int((value / max_value) * width) if max_value > 0 else 0
            bar = "█" * bar_length + "░" * (width - bar_length)
            lines.append(f"{label:>8} │{bar}│ {value:.1f}")

        lines.append("=" * (width + 15))
        return "\n".join(lines)

    def generate_trend_line(
        self,
        data_points: List[float],
        labels: List[str],
        title: str,
        height: int = 8
    ) -> str:
        """ASCII 라인 그래프 생성"""
        if not data_points:
            return "데이터 없음"

        min_val = min(data_points)
        max_val = max(data_points)
        range_val = max_val - min_val if max_val != min_val else 1

        # 정규화
        normalized = [
            int(((v - min_val) / range_val) * (height - 1))
            for v in data_points
        ]

        lines = [f"\n{title}"]
        lines.append(f"{max_val:>5} ┤")

        # 그래프 본문
        for row in range(height - 1, -1, -1):
            line = "     │"
            for i, n in enumerate(normalized):
                if n == row:
                    line += " ●"
                elif n > row and (i == 0 or normalized[i-1] <= row):
                    line += " │"
                elif n < row and (i == 0 or normalized[i-1] >= row):
                    line += " │"
                elif i > 0:
                    prev = normalized[i-1]
                    if prev < row < n or n < row < prev:
                        line += " /"
                    else:
                        line += "  "
                else:
                    line += "  "
            lines.append(line)

        lines.append(f"{min_val:>5} ┴" + "──" * len(data_points))
        lines.append("      " + "".join(f"{l:>2}" for l in labels))

        return "\n".join(lines)

    def get_progress_report(self, client_id: str) -> Dict[str, Any]:
        """종합 진전 보고서 생성"""

        report = {
            "client_id": client_id,
            "generated_at": datetime.now().isoformat(),
            "sections": {}
        }

        # 1. 증상 점수 변화 (PHQ-9, GAD-7)
        if client_id in self.baseline_manager.assessments:
            assessments = self.baseline_manager.assessments[client_id]

            phq_scores = [
                (a.timestamp.strftime("%m/%d"), a.total_score)
                for a in assessments if a.assessment_type == AssessmentType.PHQ_9
            ]
            gad_scores = [
                (a.timestamp.strftime("%m/%d"), a.total_score)
                for a in assessments if a.assessment_type == AssessmentType.GAD_7
            ]

            if phq_scores:
                report["sections"]["phq9"] = {
                    "title": "PHQ-9 우울 점수 변화",
                    "data": phq_scores,
                    "baseline": phq_scores[0][1] if phq_scores else None,
                    "current": phq_scores[-1][1] if phq_scores else None,
                    "change": phq_scores[-1][1] - phq_scores[0][1] if len(phq_scores) > 1 else 0,
                    "graph": self.generate_ascii_graph(phq_scores, 27, "PHQ-9 점수 변화")
                }

            if gad_scores:
                report["sections"]["gad7"] = {
                    "title": "GAD-7 불안 점수 변화",
                    "data": gad_scores,
                    "baseline": gad_scores[0][1] if gad_scores else None,
                    "current": gad_scores[-1][1] if gad_scores else None,
                    "change": gad_scores[-1][1] - gad_scores[0][1] if len(gad_scores) > 1 else 0,
                    "graph": self.generate_ascii_graph(gad_scores, 21, "GAD-7 점수 변화")
                }

        # 2. 기분 추이
        mood_trend = self.check_in_system.get_mood_trend(client_id)
        if mood_trend["data"]:
            mood_data = [(d["date"], d["rating"]) for d in mood_trend["data"]]
            report["sections"]["mood"] = {
                "title": "주간 기분 추이",
                "data": mood_data,
                "trend": mood_trend["trend"],
                "average": mood_trend["current_average"],
                "graph": self.generate_ascii_graph(mood_data, 10, "기분 점수 변화 (1-10)")
            }

        # 3. 진전 요약
        report["summary"] = self._generate_progress_summary(report)

        return report

    def _generate_progress_summary(self, report: Dict[str, Any]) -> str:
        """진전 요약 텍스트 생성"""
        lines = ["\n📊 진전 요약 보고서", "=" * 40]

        improvements = []
        concerns = []

        # PHQ-9 분석
        if "phq9" in report["sections"]:
            phq = report["sections"]["phq9"]
            change = phq["change"]
            if change < -5:
                improvements.append(f"우울 증상 큰 폭 개선 ({phq['baseline']} → {phq['current']})")
            elif change < 0:
                improvements.append(f"우울 증상 개선 ({phq['baseline']} → {phq['current']})")
            elif change > 5:
                concerns.append(f"우울 증상 악화 주의 ({phq['baseline']} → {phq['current']})")

        # GAD-7 분석
        if "gad7" in report["sections"]:
            gad = report["sections"]["gad7"]
            change = gad["change"]
            if change < -4:
                improvements.append(f"불안 증상 큰 폭 개선 ({gad['baseline']} → {gad['current']})")
            elif change < 0:
                improvements.append(f"불안 증상 개선 ({gad['baseline']} → {gad['current']})")
            elif change > 4:
                concerns.append(f"불안 증상 악화 주의 ({gad['baseline']} → {gad['current']})")

        # 기분 추이 분석
        if "mood" in report["sections"]:
            mood = report["sections"]["mood"]
            avg = mood["average"]
            if avg >= 7:
                improvements.append(f"전반적 기분 양호 (평균 {avg:.1f}/10)")
            elif avg <= 4:
                concerns.append(f"전반적 기분 저조 (평균 {avg:.1f}/10)")

        # 출력
        if improvements:
            lines.append("\n✅ 개선된 영역:")
            for item in improvements:
                lines.append(f"  • {item}")

        if concerns:
            lines.append("\n⚠️ 주의 필요:")
            for item in concerns:
                lines.append(f"  • {item}")

        if not improvements and not concerns:
            lines.append("\n데이터 수집 중...")

        return "\n".join(lines)

    def get_visualization_data(self, client_id: str) -> Dict[str, Any]:
        """프론트엔드 시각화용 데이터 반환 (Chart.js 호환 형식)"""
        report = self.get_progress_report(client_id)

        chart_data = {
            "labels": [],
            "datasets": []
        }

        # PHQ-9 데이터셋
        if "phq9" in report["sections"]:
            phq = report["sections"]["phq9"]
            chart_data["labels"] = [d[0] for d in phq["data"]]
            chart_data["datasets"].append({
                "label": "PHQ-9 (우울)",
                "data": [d[1] for d in phq["data"]],
                "borderColor": "#ef4444",
                "backgroundColor": "rgba(239, 68, 68, 0.1)",
                "tension": 0.4
            })

        # GAD-7 데이터셋
        if "gad7" in report["sections"]:
            gad = report["sections"]["gad7"]
            if not chart_data["labels"]:
                chart_data["labels"] = [d[0] for d in gad["data"]]
            chart_data["datasets"].append({
                "label": "GAD-7 (불안)",
                "data": [d[1] for d in gad["data"]],
                "borderColor": "#f59e0b",
                "backgroundColor": "rgba(245, 158, 11, 0.1)",
                "tension": 0.4
            })

        # 기분 데이터셋
        if "mood" in report["sections"]:
            mood = report["sections"]["mood"]
            chart_data["datasets"].append({
                "label": "주간 기분 (1-10)",
                "data": [d[1] for d in mood["data"]],
                "borderColor": "#22c55e",
                "backgroundColor": "rgba(34, 197, 94, 0.1)",
                "tension": 0.4,
                "yAxisID": "y1"
            })

        return chart_data


# ============================================================================
# 4. 단계별 기법 제공 시스템 (Staged Technique Delivery)
# ============================================================================

class TechniqueDifficulty(Enum):
    """기법 난이도 수준"""
    BEGINNER = "beginner"      # 초급
    INTERMEDIATE = "intermediate"  # 중급
    ADVANCED = "advanced"      # 고급


@dataclass
class TherapyTechnique:
    """치료 기법"""
    id: str
    name: str
    category: str  # breathing, cognitive, behavioral, mindfulness, etc.
    difficulty: TechniqueDifficulty
    description: str
    instructions: List[str]
    duration_minutes: int
    prerequisites: List[str] = field(default_factory=list)
    success_indicators: List[str] = field(default_factory=list)


class StagedTechniqueSystem:
    """
    단계별 기법 제공 시스템

    쉬운 기법 → 복잡한 기법 순서로 체계적 제공
    내담자 수준과 진전에 따른 맞춤형 기법 추천
    """

    def __init__(self):
        self.techniques: Dict[str, TherapyTechnique] = {}
        self.client_progress: Dict[str, Dict[str, Any]] = {}
        self._initialize_techniques()

    def _initialize_techniques(self):
        """치료 기법 라이브러리 초기화"""

        techniques_data = [
            # ===== 초급 기법 (BEGINNER) =====
            TherapyTechnique(
                id="breathing_basic",
                name="기본 복식호흡",
                category="breathing",
                difficulty=TechniqueDifficulty.BEGINNER,
                description="긴장 완화를 위한 가장 기본적인 호흡법",
                instructions=[
                    "편안한 자세로 앉거나 누워주세요",
                    "한 손은 가슴에, 다른 손은 배에 올려주세요",
                    "코로 천천히 숨을 들이마시며 배가 부풀어오르게 해주세요",
                    "입으로 천천히 내쉬며 배가 들어가는 것을 느껴주세요",
                    "4초 들이마시고, 4초 내쉬기를 5회 반복해주세요"
                ],
                duration_minutes=5,
                success_indicators=["근육 긴장 감소", "심박수 안정화"]
            ),
            TherapyTechnique(
                id="grounding_54321",
                name="5-4-3-2-1 그라운딩",
                category="grounding",
                difficulty=TechniqueDifficulty.BEGINNER,
                description="현재 순간에 집중하기 위한 감각 활용 기법",
                instructions=[
                    "주변에서 보이는 것 5가지를 찾아 말해주세요",
                    "만질 수 있는 것 4가지를 찾아 촉감을 느껴보세요",
                    "들리는 소리 3가지에 집중해주세요",
                    "맡을 수 있는 냄새 2가지를 찾아보세요",
                    "맛볼 수 있는 것 1가지를 생각해주세요"
                ],
                duration_minutes=5,
                success_indicators=["불안 감소", "현재 순간 집중력 향상"]
            ),
            TherapyTechnique(
                id="thought_diary_basic",
                name="기본 생각 기록",
                category="cognitive",
                difficulty=TechniqueDifficulty.BEGINNER,
                description="감정과 생각을 기록하는 기본 기법",
                instructions=[
                    "불편한 감정을 느꼈을 때 상황을 적어주세요",
                    "그 순간 어떤 감정을 느꼈는지 적어주세요 (예: 슬픔, 화남, 불안)",
                    "감정의 강도를 0-100으로 평가해주세요",
                    "그 순간 어떤 생각이 들었는지 적어주세요",
                    "하루에 1-2번 연습해주세요"
                ],
                duration_minutes=10,
                success_indicators=["감정 인식 능력 향상", "자기 관찰력 증가"]
            ),
            TherapyTechnique(
                id="progressive_relaxation_simple",
                name="간단한 근육 이완",
                category="relaxation",
                difficulty=TechniqueDifficulty.BEGINNER,
                description="주요 근육군의 긴장과 이완을 통한 스트레스 해소",
                instructions=[
                    "편안하게 앉아서 눈을 감아주세요",
                    "주먹을 꽉 쥐고 5초간 유지해주세요",
                    "천천히 손을 펴며 긴장을 풀어주세요",
                    "어깨를 귀 쪽으로 올리고 5초간 유지해주세요",
                    "어깨를 내리며 긴장을 풀어주세요",
                    "각 동작 후 이완감을 느껴보세요"
                ],
                duration_minutes=10,
                success_indicators=["신체 긴장 감소", "이완감 증가"]
            ),

            # ===== 중급 기법 (INTERMEDIATE) =====
            TherapyTechnique(
                id="breathing_478",
                name="4-7-8 호흡법",
                category="breathing",
                difficulty=TechniqueDifficulty.INTERMEDIATE,
                description="깊은 이완을 위한 리듬 호흡법",
                instructions=[
                    "코로 4초간 숨을 들이마셔주세요",
                    "7초간 숨을 참아주세요",
                    "입으로 8초간 천천히 내쉬어주세요",
                    "이 과정을 4회 반복해주세요",
                    "어지러우면 멈추고 자연스러운 호흡을 해주세요"
                ],
                duration_minutes=5,
                prerequisites=["breathing_basic"],
                success_indicators=["깊은 이완 상태", "수면 개선"]
            ),
            TherapyTechnique(
                id="cognitive_restructuring",
                name="인지 재구성",
                category="cognitive",
                difficulty=TechniqueDifficulty.INTERMEDIATE,
                description="부정적 자동적 사고를 균형 잡힌 사고로 전환",
                instructions=[
                    "부정적 생각을 구체적으로 적어주세요",
                    "그 생각을 지지하는 증거를 찾아보세요",
                    "그 생각에 반하는 증거도 찾아보세요",
                    "증거들을 고려한 균형 잡힌 생각을 만들어주세요",
                    "새로운 생각으로 감정이 어떻게 변하는지 확인해주세요"
                ],
                duration_minutes=15,
                prerequisites=["thought_diary_basic"],
                success_indicators=["사고 유연성 증가", "감정 강도 감소"]
            ),
            TherapyTechnique(
                id="behavioral_activation",
                name="행동 활성화",
                category="behavioral",
                difficulty=TechniqueDifficulty.INTERMEDIATE,
                description="가치 기반 활동 계획 및 실천",
                instructions=[
                    "즐거웠던 활동 목록을 작성해주세요",
                    "쉬운 활동 하나를 골라 구체적으로 계획해주세요",
                    "언제, 어디서, 어떻게 할지 정해주세요",
                    "활동을 실천하고 경험을 기록해주세요",
                    "활동 전후의 기분 변화를 평가해주세요"
                ],
                duration_minutes=20,
                prerequisites=["thought_diary_basic"],
                success_indicators=["활동량 증가", "즐거움 경험 증가"]
            ),
            TherapyTechnique(
                id="mindfulness_body_scan",
                name="마음챙김 바디스캔",
                category="mindfulness",
                difficulty=TechniqueDifficulty.INTERMEDIATE,
                description="신체 각 부위에 주의를 기울이는 명상",
                instructions=[
                    "편안하게 누워 눈을 감아주세요",
                    "발끝부터 시작해 주의를 기울여주세요",
                    "각 부위의 감각을 있는 그대로 느껴보세요",
                    "발 → 다리 → 배 → 가슴 → 팔 → 얼굴 순서로 진행해주세요",
                    "판단 없이 감각을 관찰하고 넘어가주세요"
                ],
                duration_minutes=20,
                prerequisites=["grounding_54321", "breathing_basic"],
                success_indicators=["신체 자각력 향상", "현재 순간 집중력 향상"]
            ),

            # ===== 고급 기법 (ADVANCED) =====
            TherapyTechnique(
                id="cognitive_defusion",
                name="인지적 탈융합",
                category="act",
                difficulty=TechniqueDifficulty.ADVANCED,
                description="생각을 단지 생각으로 바라보는 ACT 기법",
                instructions=[
                    "힘든 생각을 떠올려주세요",
                    "'나는 ~라는 생각을 하고 있다'라고 표현해보세요",
                    "그 생각에 '고맙지만 안녕'이라고 말해보세요",
                    "생각을 구름처럼 떠다니는 것으로 상상해보세요",
                    "생각이 왔다 가도록 그냥 두어보세요"
                ],
                duration_minutes=15,
                prerequisites=["mindfulness_body_scan", "cognitive_restructuring"],
                success_indicators=["생각과 자기 분리", "심리적 유연성 증가"]
            ),
            TherapyTechnique(
                id="exposure_hierarchy",
                name="노출 위계 설정",
                category="exposure",
                difficulty=TechniqueDifficulty.ADVANCED,
                description="불안 유발 상황의 단계적 노출 계획",
                instructions=[
                    "두려운 상황들을 모두 나열해주세요",
                    "각 상황의 불안 수준을 0-100으로 평가해주세요",
                    "가장 쉬운 것부터 어려운 순으로 정렬해주세요",
                    "각 단계별 노출 계획을 세워주세요",
                    "상담사와 함께 첫 단계부터 시작해주세요"
                ],
                duration_minutes=30,
                prerequisites=["breathing_478", "cognitive_restructuring"],
                success_indicators=["회피 행동 감소", "불안 상황 대처력 향상"]
            ),
            TherapyTechnique(
                id="values_clarification",
                name="가치 명료화",
                category="act",
                difficulty=TechniqueDifficulty.ADVANCED,
                description="삶의 핵심 가치를 탐색하고 명료화하는 작업",
                instructions=[
                    "삶에서 정말 중요한 것이 무엇인지 생각해보세요",
                    "10가지 삶의 영역을 검토해보세요 (가족, 일, 건강 등)",
                    "각 영역에서 어떤 사람이 되고 싶은지 적어보세요",
                    "현재 삶이 그 가치와 얼마나 일치하는지 평가해보세요",
                    "가치를 향한 작은 실천 계획을 세워보세요"
                ],
                duration_minutes=30,
                prerequisites=["behavioral_activation", "mindfulness_body_scan"],
                success_indicators=["삶의 방향성 명확화", "동기 부여 증가"]
            ),
            TherapyTechnique(
                id="compassionate_letter",
                name="자기자비 편지",
                category="self_compassion",
                difficulty=TechniqueDifficulty.ADVANCED,
                description="자신에게 따뜻한 편지를 쓰는 자기자비 기법",
                instructions=[
                    "최근 자신을 비난했던 상황을 떠올려주세요",
                    "친한 친구가 같은 상황이라면 뭐라고 해줄지 생각해보세요",
                    "그 따뜻한 말을 자신에게 편지로 써보세요",
                    "고통을 인정하고, 인간이라 실수할 수 있음을 적어주세요",
                    "자신에게 따뜻함과 격려를 담아주세요"
                ],
                duration_minutes=20,
                prerequisites=["cognitive_restructuring"],
                success_indicators=["자기비판 감소", "자기수용 증가"]
            )
        ]

        for tech in techniques_data:
            self.techniques[tech.id] = tech

    def get_client_level(self, client_id: str) -> TechniqueDifficulty:
        """내담자 현재 수준 파악"""
        if client_id not in self.client_progress:
            return TechniqueDifficulty.BEGINNER

        progress = self.client_progress[client_id]
        mastered = progress.get("mastered_techniques", [])

        # 초급 기법 4개 이상 숙달 → 중급
        beginner_mastered = sum(
            1 for t_id in mastered
            if t_id in self.techniques and
            self.techniques[t_id].difficulty == TechniqueDifficulty.BEGINNER
        )

        intermediate_mastered = sum(
            1 for t_id in mastered
            if t_id in self.techniques and
            self.techniques[t_id].difficulty == TechniqueDifficulty.INTERMEDIATE
        )

        if intermediate_mastered >= 3:
            return TechniqueDifficulty.ADVANCED
        elif beginner_mastered >= 3:
            return TechniqueDifficulty.INTERMEDIATE
        else:
            return TechniqueDifficulty.BEGINNER

    def recommend_next_technique(
        self,
        client_id: str,
        category_preference: Optional[str] = None
    ) -> Optional[TherapyTechnique]:
        """다음 추천 기법"""
        current_level = self.get_client_level(client_id)

        if client_id not in self.client_progress:
            self.client_progress[client_id] = {
                "mastered_techniques": [],
                "in_progress": [],
                "technique_history": []
            }

        progress = self.client_progress[client_id]
        mastered = set(progress["mastered_techniques"])
        in_progress = set(progress["in_progress"])

        # 현재 수준 또는 한 단계 아래에서 추천
        target_levels = [current_level]
        if current_level == TechniqueDifficulty.INTERMEDIATE:
            target_levels.append(TechniqueDifficulty.BEGINNER)
        elif current_level == TechniqueDifficulty.ADVANCED:
            target_levels.extend([TechniqueDifficulty.INTERMEDIATE, TechniqueDifficulty.BEGINNER])

        candidates = []
        for tech in self.techniques.values():
            # 이미 숙달 또는 진행 중인 기법 제외
            if tech.id in mastered or tech.id in in_progress:
                continue

            # 수준 확인
            if tech.difficulty not in target_levels:
                continue

            # 선행 조건 확인
            if tech.prerequisites and not all(p in mastered for p in tech.prerequisites):
                continue

            # 카테고리 선호도 반영
            if category_preference and tech.category != category_preference:
                continue

            candidates.append(tech)

        if not candidates:
            return None

        # 가장 낮은 난이도부터 추천
        candidates.sort(key=lambda t: list(TechniqueDifficulty).index(t.difficulty))
        return candidates[0]

    def start_technique(self, client_id: str, technique_id: str) -> Dict[str, Any]:
        """기법 연습 시작"""
        if technique_id not in self.techniques:
            return {"success": False, "error": "존재하지 않는 기법입니다."}

        if client_id not in self.client_progress:
            self.client_progress[client_id] = {
                "mastered_techniques": [],
                "in_progress": [],
                "technique_history": []
            }

        tech = self.techniques[technique_id]
        progress = self.client_progress[client_id]

        # 선행 조건 확인
        mastered = set(progress["mastered_techniques"])
        if tech.prerequisites:
            missing = [p for p in tech.prerequisites if p not in mastered]
            if missing:
                missing_names = [self.techniques[p].name for p in missing if p in self.techniques]
                return {
                    "success": False,
                    "error": f"먼저 다음 기법을 익혀주세요: {', '.join(missing_names)}"
                }

        # 진행 중 추가
        if technique_id not in progress["in_progress"]:
            progress["in_progress"].append(technique_id)

        # 히스토리 기록
        progress["technique_history"].append({
            "technique_id": technique_id,
            "action": "started",
            "timestamp": datetime.now().isoformat()
        })

        return {
            "success": True,
            "technique": {
                "id": tech.id,
                "name": tech.name,
                "description": tech.description,
                "instructions": tech.instructions,
                "duration_minutes": tech.duration_minutes
            }
        }

    def complete_technique(
        self,
        client_id: str,
        technique_id: str,
        practice_count: int = 1,
        feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """기법 연습 완료 기록"""
        if client_id not in self.client_progress:
            return {"success": False, "error": "진행 기록이 없습니다."}

        progress = self.client_progress[client_id]

        # 히스토리에 완료 기록
        progress["technique_history"].append({
            "technique_id": technique_id,
            "action": "completed",
            "practice_count": practice_count,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat()
        })

        # 충분한 연습 시 숙달로 표시 (3회 이상)
        total_practice = sum(
            1 for h in progress["technique_history"]
            if h["technique_id"] == technique_id and h["action"] == "completed"
        )

        if total_practice >= 3:
            if technique_id in progress["in_progress"]:
                progress["in_progress"].remove(technique_id)
            if technique_id not in progress["mastered_techniques"]:
                progress["mastered_techniques"].append(technique_id)

            return {
                "success": True,
                "mastered": True,
                "message": f"'{self.techniques[technique_id].name}' 기법을 숙달하셨습니다! 🎉",
                "total_practice": total_practice
            }

        return {
            "success": True,
            "mastered": False,
            "message": f"좋습니다! {3 - total_practice}회 더 연습하면 숙달됩니다.",
            "total_practice": total_practice
        }

    def get_progress_summary(self, client_id: str) -> Dict[str, Any]:
        """기법 학습 진전 요약"""
        if client_id not in self.client_progress:
            return {
                "level": TechniqueDifficulty.BEGINNER.value,
                "mastered": [],
                "in_progress": [],
                "recommended_next": None
            }

        progress = self.client_progress[client_id]
        level = self.get_client_level(client_id)
        next_tech = self.recommend_next_technique(client_id)

        return {
            "level": level.value,
            "level_label": {"beginner": "초급", "intermediate": "중급", "advanced": "고급"}[level.value],
            "mastered": [
                {"id": t_id, "name": self.techniques[t_id].name}
                for t_id in progress["mastered_techniques"]
                if t_id in self.techniques
            ],
            "in_progress": [
                {"id": t_id, "name": self.techniques[t_id].name}
                for t_id in progress["in_progress"]
                if t_id in self.techniques
            ],
            "recommended_next": {
                "id": next_tech.id,
                "name": next_tech.name,
                "category": next_tech.category,
                "description": next_tech.description
            } if next_tech else None
        }


# ============================================================================
# 5. 숙제 체크 시스템 (Homework System)
# ============================================================================

class HomeworkStatus(Enum):
    """숙제 상태"""
    ASSIGNED = "assigned"      # 할당됨
    IN_PROGRESS = "in_progress"  # 진행 중
    COMPLETED = "completed"    # 완료
    PARTIAL = "partial"        # 부분 완료
    NOT_DONE = "not_done"      # 미완료


@dataclass
class HomeworkAssignment:
    """숙제 과제"""
    id: str
    client_id: str
    session_id: str
    assigned_date: datetime
    due_date: datetime
    title: str
    description: str
    instructions: List[str]
    related_technique: Optional[str] = None
    status: HomeworkStatus = HomeworkStatus.ASSIGNED
    completion_notes: Optional[str] = None
    completion_date: Optional[datetime] = None
    reflection: Optional[str] = None
    difficulty_rating: Optional[int] = None  # 1-5
    usefulness_rating: Optional[int] = None  # 1-5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "client_id": self.client_id,
            "session_id": self.session_id,
            "assigned_date": self.assigned_date.isoformat(),
            "due_date": self.due_date.isoformat(),
            "title": self.title,
            "description": self.description,
            "instructions": self.instructions,
            "related_technique": self.related_technique,
            "status": self.status.value,
            "completion_notes": self.completion_notes,
            "completion_date": self.completion_date.isoformat() if self.completion_date else None,
            "reflection": self.reflection,
            "difficulty_rating": self.difficulty_rating,
            "usefulness_rating": self.usefulness_rating
        }


class HomeworkSystem:
    """
    숙제 체크 시스템

    다음 회기 시작 시 숙제 완료 여부 확인
    숙제 할당, 추적, 피드백 관리
    """

    def __init__(self, technique_system: StagedTechniqueSystem):
        self.assignments: Dict[str, List[HomeworkAssignment]] = {}  # client_id -> list
        self.technique_system = technique_system

    def _generate_homework_id(self) -> str:
        """고유 숙제 ID 생성"""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()[:12]

    def assign_homework(
        self,
        client_id: str,
        session_id: str,
        title: str,
        description: str,
        instructions: List[str],
        days_until_due: int = 7,
        related_technique: Optional[str] = None
    ) -> HomeworkAssignment:
        """숙제 할당"""

        homework = HomeworkAssignment(
            id=self._generate_homework_id(),
            client_id=client_id,
            session_id=session_id,
            assigned_date=datetime.now(),
            due_date=datetime.now() + timedelta(days=days_until_due),
            title=title,
            description=description,
            instructions=instructions,
            related_technique=related_technique
        )

        if client_id not in self.assignments:
            self.assignments[client_id] = []
        self.assignments[client_id].append(homework)

        return homework

    def assign_technique_practice(
        self,
        client_id: str,
        session_id: str,
        technique_id: str,
        practice_frequency: str = "매일 1회",
        additional_notes: str = ""
    ) -> Optional[HomeworkAssignment]:
        """기법 연습 숙제 할당"""

        if technique_id not in self.technique_system.techniques:
            return None

        tech = self.technique_system.techniques[technique_id]

        instructions = [
            f"'{tech.name}' 기법을 {practice_frequency} 연습해주세요.",
            *tech.instructions,
            "연습 후 어떤 느낌이 들었는지 간단히 메모해주세요."
        ]

        if additional_notes:
            instructions.append(additional_notes)

        return self.assign_homework(
            client_id=client_id,
            session_id=session_id,
            title=f"'{tech.name}' 연습하기",
            description=f"{tech.description} - {practice_frequency} 연습",
            instructions=instructions,
            related_technique=technique_id
        )

    def get_pending_homework(self, client_id: str) -> List[HomeworkAssignment]:
        """미완료 숙제 목록"""
        if client_id not in self.assignments:
            return []

        return [
            hw for hw in self.assignments[client_id]
            if hw.status in [HomeworkStatus.ASSIGNED, HomeworkStatus.IN_PROGRESS]
        ]

    def get_overdue_homework(self, client_id: str) -> List[HomeworkAssignment]:
        """기한 초과 숙제 목록"""
        pending = self.get_pending_homework(client_id)
        now = datetime.now()
        return [hw for hw in pending if hw.due_date < now]

    def check_homework_at_session_start(self, client_id: str) -> Dict[str, Any]:
        """회기 시작 시 숙제 확인"""
        pending = self.get_pending_homework(client_id)
        overdue = self.get_overdue_homework(client_id)

        if not pending:
            return {
                "has_homework": False,
                "message": "현재 진행 중인 숙제가 없습니다."
            }

        result = {
            "has_homework": True,
            "total_pending": len(pending),
            "overdue_count": len(overdue),
            "homework_list": [
                {
                    "id": hw.id,
                    "title": hw.title,
                    "due_date": hw.due_date.strftime("%m/%d"),
                    "is_overdue": hw in overdue,
                    "status": hw.status.value
                }
                for hw in pending
            ],
            "check_prompts": []
        }

        for hw in pending:
            overdue_text = " (기한 지남)" if hw in overdue else ""
            result["check_prompts"].append({
                "homework_id": hw.id,
                "prompt": f"'{hw.title}'{overdue_text} 숙제는 어떻게 되셨나요?",
                "follow_up": "어떤 경험을 하셨는지 나눠주실 수 있을까요?"
            })

        return result

    def update_homework_status(
        self,
        client_id: str,
        homework_id: str,
        status: HomeworkStatus,
        completion_notes: Optional[str] = None,
        reflection: Optional[str] = None,
        difficulty_rating: Optional[int] = None,
        usefulness_rating: Optional[int] = None
    ) -> Optional[HomeworkAssignment]:
        """숙제 상태 업데이트"""
        if client_id not in self.assignments:
            return None

        for hw in self.assignments[client_id]:
            if hw.id == homework_id:
                hw.status = status
                if status in [HomeworkStatus.COMPLETED, HomeworkStatus.PARTIAL]:
                    hw.completion_date = datetime.now()
                if completion_notes:
                    hw.completion_notes = completion_notes
                if reflection:
                    hw.reflection = reflection
                if difficulty_rating:
                    hw.difficulty_rating = difficulty_rating
                if usefulness_rating:
                    hw.usefulness_rating = usefulness_rating

                # 관련 기법이 있으면 연습 완료 기록
                if hw.related_technique and status == HomeworkStatus.COMPLETED:
                    self.technique_system.complete_technique(
                        client_id,
                        hw.related_technique,
                        feedback=reflection
                    )

                return hw

        return None

    def get_homework_summary(self, client_id: str) -> Dict[str, Any]:
        """숙제 이행 요약"""
        if client_id not in self.assignments:
            return {
                "total": 0,
                "completed": 0,
                "completion_rate": 0,
                "message": "숙제 기록이 없습니다."
            }

        all_homework = self.assignments[client_id]
        completed = [hw for hw in all_homework if hw.status == HomeworkStatus.COMPLETED]
        partial = [hw for hw in all_homework if hw.status == HomeworkStatus.PARTIAL]
        not_done = [hw for hw in all_homework if hw.status == HomeworkStatus.NOT_DONE]

        total = len(all_homework)
        completion_rate = (len(completed) + 0.5 * len(partial)) / total * 100 if total > 0 else 0

        # 평균 평점
        useful_ratings = [hw.usefulness_rating for hw in all_homework if hw.usefulness_rating]
        avg_usefulness = sum(useful_ratings) / len(useful_ratings) if useful_ratings else None

        return {
            "total": total,
            "completed": len(completed),
            "partial": len(partial),
            "not_done": len(not_done),
            "pending": len(self.get_pending_homework(client_id)),
            "completion_rate": round(completion_rate, 1),
            "average_usefulness": round(avg_usefulness, 1) if avg_usefulness else None,
            "message": self._get_homework_feedback_message(completion_rate)
        }

    def _get_homework_feedback_message(self, completion_rate: float) -> str:
        """숙제 완료율에 따른 피드백"""
        if completion_rate >= 80:
            return "숙제 이행이 매우 우수합니다! 이러한 적극적인 참여가 상담 효과를 높입니다. 👏"
        elif completion_rate >= 60:
            return "숙제를 꾸준히 하고 계시네요. 조금 더 완수하면 더 좋은 효과를 기대할 수 있습니다."
        elif completion_rate >= 40:
            return "숙제 실천이 어려우신 것 같습니다. 어떤 부분이 힘드신지 이야기해볼까요?"
        else:
            return "숙제 실천률이 낮습니다. 숙제 양을 조절하거나 다른 방법을 찾아보면 좋겠습니다."


# ============================================================================
# 6. 사후 추적 알림 시스템 (Follow-up Alert System)
# ============================================================================

class FollowUpType(Enum):
    """추적 유형"""
    ONE_MONTH = "1_month"       # 1개월 후
    THREE_MONTHS = "3_months"  # 3개월 후
    SIX_MONTHS = "6_months"    # 6개월 후
    ONE_YEAR = "1_year"        # 1년 후
    CUSTOM = "custom"          # 커스텀


@dataclass
class FollowUpSchedule:
    """사후 추적 일정"""
    id: str
    client_id: str
    follow_up_type: FollowUpType
    scheduled_date: datetime
    status: str  # pending, sent, completed, cancelled
    created_at: datetime
    message_template: str
    assessments_to_include: List[AssessmentType]
    completed_at: Optional[datetime] = None
    response_received: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "client_id": self.client_id,
            "follow_up_type": self.follow_up_type.value,
            "scheduled_date": self.scheduled_date.isoformat(),
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "message_template": self.message_template,
            "assessments_to_include": [a.value for a in self.assessments_to_include],
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "response_received": self.response_received
        }


class FollowUpAlertSystem:
    """
    사후 추적 알림 시스템

    치료 종결 후 1개월, 3개월, 6개월 후 체크인
    장기적 효과 추적 및 재발 예방
    """

    # 기본 추적 일정 (종결 후)
    DEFAULT_FOLLOW_UP_SCHEDULE = [
        (FollowUpType.ONE_MONTH, 30),
        (FollowUpType.THREE_MONTHS, 90),
        (FollowUpType.SIX_MONTHS, 180)
    ]

    # 메시지 템플릿
    MESSAGE_TEMPLATES = {
        FollowUpType.ONE_MONTH: """
안녕하세요, {client_name}님.
상담을 마친 지 한 달이 되었습니다.

그동안 잘 지내고 계신가요?
상담에서 배운 것들이 일상에서 어떻게 도움이 되고 있는지 궁금합니다.

잠시 시간을 내어 간단한 체크인에 응해주시겠어요?
현재 상태를 확인하고, 필요하시다면 추가 지원을 안내해 드리겠습니다.
        """,
        FollowUpType.THREE_MONTHS: """
안녕하세요, {client_name}님.
상담 종결 후 3개월이 되었습니다.

상담에서 다루었던 것들이 잘 유지되고 있는지 확인해보고 싶습니다.
어려움이 있으시거나 추가 상담이 필요하시면 말씀해 주세요.

짧은 설문에 응해주시면 더 도움이 될 수 있습니다.
        """,
        FollowUpType.SIX_MONTHS: """
안녕하세요, {client_name}님.
상담을 마친 지 6개월이 되었습니다.

장기적인 변화와 성장을 확인하고 싶습니다.
그동안 어떻게 지내셨는지, 상담이 도움이 되었는지 여쭤보아도 될까요?

잠시 시간을 내어 근황을 나눠주시면 감사하겠습니다.
        """
    }

    def __init__(self, baseline_manager: BaselineAssessmentManager):
        self.schedules: Dict[str, List[FollowUpSchedule]] = {}  # client_id -> list
        self.baseline_manager = baseline_manager

    def _generate_schedule_id(self) -> str:
        """고유 일정 ID 생성"""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()[:12]

    def schedule_follow_ups(
        self,
        client_id: str,
        termination_date: datetime,
        client_name: str = "내담자",
        custom_schedule: Optional[List[Tuple[FollowUpType, int]]] = None
    ) -> List[FollowUpSchedule]:
        """종결 후 추적 일정 생성"""

        schedule_config = custom_schedule or self.DEFAULT_FOLLOW_UP_SCHEDULE
        created_schedules = []

        for follow_up_type, days in schedule_config:
            scheduled_date = termination_date + timedelta(days=days)

            message = self.MESSAGE_TEMPLATES.get(
                follow_up_type,
                "안녕하세요, {client_name}님. 근황 체크인 시간입니다."
            ).format(client_name=client_name)

            schedule = FollowUpSchedule(
                id=self._generate_schedule_id(),
                client_id=client_id,
                follow_up_type=follow_up_type,
                scheduled_date=scheduled_date,
                status="pending",
                created_at=datetime.now(),
                message_template=message,
                assessments_to_include=[AssessmentType.PHQ_9, AssessmentType.GAD_7]
            )

            if client_id not in self.schedules:
                self.schedules[client_id] = []
            self.schedules[client_id].append(schedule)
            created_schedules.append(schedule)

        return created_schedules

    def get_due_follow_ups(self, as_of: Optional[datetime] = None) -> List[FollowUpSchedule]:
        """현재 시점에서 발송해야 할 추적 알림"""
        check_date = as_of or datetime.now()
        due_schedules = []

        for client_id, schedules in self.schedules.items():
            for schedule in schedules:
                if schedule.status == "pending" and schedule.scheduled_date <= check_date:
                    due_schedules.append(schedule)

        return due_schedules

    def get_upcoming_follow_ups(
        self,
        days_ahead: int = 7,
        as_of: Optional[datetime] = None
    ) -> List[FollowUpSchedule]:
        """다가오는 추적 일정"""
        check_date = as_of or datetime.now()
        end_date = check_date + timedelta(days=days_ahead)

        upcoming = []
        for client_id, schedules in self.schedules.items():
            for schedule in schedules:
                if schedule.status == "pending":
                    if check_date <= schedule.scheduled_date <= end_date:
                        upcoming.append(schedule)

        return upcoming

    def send_follow_up(
        self,
        schedule_id: str,
        notification_method: str = "in_app"  # in_app, email, sms
    ) -> Dict[str, Any]:
        """추적 알림 발송"""

        for client_id, schedules in self.schedules.items():
            for schedule in schedules:
                if schedule.id == schedule_id:
                    schedule.status = "sent"

                    # 평가 도구 링크 생성
                    assessment_links = []
                    for assessment in schedule.assessments_to_include:
                        assessment_links.append({
                            "type": assessment.value,
                            "link": f"/assessment/{client_id}/{assessment.value.lower()}"
                        })

                    return {
                        "success": True,
                        "schedule_id": schedule_id,
                        "client_id": client_id,
                        "message": schedule.message_template,
                        "notification_method": notification_method,
                        "assessment_links": assessment_links,
                        "sent_at": datetime.now().isoformat()
                    }

        return {"success": False, "error": "일정을 찾을 수 없습니다."}

    def record_follow_up_response(
        self,
        client_id: str,
        schedule_id: str,
        assessment_results: Optional[List[AssessmentResult]] = None,
        qualitative_feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """추적 응답 기록"""

        if client_id not in self.schedules:
            return {"success": False, "error": "내담자를 찾을 수 없습니다."}

        for schedule in self.schedules[client_id]:
            if schedule.id == schedule_id:
                schedule.status = "completed"
                schedule.completed_at = datetime.now()
                schedule.response_received = True

                # 평가 결과가 있으면 기저선과 비교
                comparison = None
                if assessment_results:
                    comparison = self._compare_with_baseline(client_id, assessment_results)

                return {
                    "success": True,
                    "schedule_id": schedule_id,
                    "completed_at": schedule.completed_at.isoformat(),
                    "qualitative_feedback": qualitative_feedback,
                    "comparison_with_baseline": comparison
                }

        return {"success": False, "error": "일정을 찾을 수 없습니다."}

    def _compare_with_baseline(
        self,
        client_id: str,
        current_results: List[AssessmentResult]
    ) -> Dict[str, Any]:
        """기저선과 현재 결과 비교"""

        baseline_summary = self.baseline_manager.get_baseline_summary(client_id)
        if not baseline_summary:
            return {"message": "기저선 데이터가 없습니다."}

        comparisons = []

        for current in current_results:
            # 해당 유형의 기저선 찾기
            baseline_result = None
            for b in baseline_summary["assessments"]:
                if b["assessment_type"] == current.assessment_type.value:
                    baseline_result = b
                    break

            if baseline_result:
                change = current.total_score - baseline_result["total_score"]
                change_pct = (change / baseline_result["total_score"] * 100) if baseline_result["total_score"] > 0 else 0

                if change < -5:
                    interpretation = "큰 폭 개선"
                    emoji = "📈"
                elif change < 0:
                    interpretation = "개선"
                    emoji = "📊"
                elif change > 5:
                    interpretation = "악화 - 추가 지원 필요"
                    emoji = "⚠️"
                else:
                    interpretation = "유지"
                    emoji = "➡️"

                comparisons.append({
                    "assessment_type": current.assessment_type.value,
                    "baseline_score": baseline_result["total_score"],
                    "current_score": current.total_score,
                    "change": change,
                    "change_percent": round(change_pct, 1),
                    "interpretation": interpretation,
                    "emoji": emoji
                })

        return {
            "comparisons": comparisons,
            "needs_intervention": any(c["change"] > 5 for c in comparisons)
        }

    def get_client_follow_up_history(self, client_id: str) -> Dict[str, Any]:
        """내담자 추적 이력"""
        if client_id not in self.schedules:
            return {"client_id": client_id, "schedules": [], "summary": "추적 일정이 없습니다."}

        schedules = self.schedules[client_id]

        completed = [s for s in schedules if s.status == "completed"]
        pending = [s for s in schedules if s.status == "pending"]
        sent = [s for s in schedules if s.status == "sent"]

        response_rate = len(completed) / (len(completed) + len([s for s in schedules if s.status not in ["pending"]])) * 100 if schedules else 0

        return {
            "client_id": client_id,
            "schedules": [s.to_dict() for s in schedules],
            "summary": {
                "total": len(schedules),
                "completed": len(completed),
                "pending": len(pending),
                "awaiting_response": len(sent),
                "response_rate": round(response_rate, 1)
            }
        }

    def generate_follow_up_report(self, client_id: str) -> str:
        """추적 보고서 생성"""
        history = self.get_client_follow_up_history(client_id)

        lines = [
            "=" * 50,
            "📋 사후 추적 보고서",
            "=" * 50,
            f"\n내담자 ID: {client_id}",
            f"총 추적 횟수: {history['summary']['total']}",
            f"완료: {history['summary']['completed']} | 대기 중: {history['summary']['pending']}",
            f"응답률: {history['summary']['response_rate']}%",
            "\n--- 추적 일정 ---"
        ]

        for schedule_dict in history["schedules"]:
            status_emoji = {
                "pending": "⏳",
                "sent": "📤",
                "completed": "✅",
                "cancelled": "❌"
            }.get(schedule_dict["status"], "❓")

            lines.append(
                f"{status_emoji} {schedule_dict['follow_up_type']}: "
                f"{schedule_dict['scheduled_date'][:10]} - {schedule_dict['status']}"
            )

        lines.append("\n" + "=" * 50)

        return "\n".join(lines)


# ============================================================================
# 통합 세션 관리자 (Integrated Session Manager)
# ============================================================================

class StructuredTherapyManager:
    """
    구조화된 치료 통합 관리자

    6가지 시스템을 통합하여 일관된 세션 흐름 제공
    """

    def __init__(self):
        # 개별 시스템 초기화
        self.baseline_manager = BaselineAssessmentManager()
        self.check_in_system = SessionCheckInSystem()
        self.progress_viz = ProgressVisualizationSystem(
            self.baseline_manager,
            self.check_in_system
        )
        self.technique_system = StagedTechniqueSystem()
        self.homework_system = HomeworkSystem(self.technique_system)
        self.follow_up_system = FollowUpAlertSystem(self.baseline_manager)

    def start_new_client_session(self, client_id: str) -> Dict[str, Any]:
        """새 내담자 세션 시작 프로세스"""

        response = {
            "client_id": client_id,
            "steps": []
        }

        # 1. 기저선 평가 확인
        baseline_check = self.baseline_manager.check_baseline_required(client_id)
        if baseline_check["required"]:
            response["steps"].append({
                "step": 1,
                "type": "baseline_assessment",
                "required": True,
                "message": baseline_check["message"],
                "assessments": [
                    {
                        "type": a.value,
                        "items": [item.__dict__ for item in self.baseline_manager.get_assessment_items(a)]
                    }
                    for a in baseline_check["missing_assessments"]
                ]
            })
            response["needs_baseline"] = True
            return response

        response["needs_baseline"] = False

        # 2. 숙제 확인
        homework_check = self.homework_system.check_homework_at_session_start(client_id)
        response["steps"].append({
            "step": 2,
            "type": "homework_check",
            "data": homework_check
        })

        # 3. 체크인
        has_homework = homework_check["has_homework"]
        check_in_prompts = self.check_in_system.get_check_in_prompts(client_id, has_homework)
        response["steps"].append({
            "step": 3,
            "type": "session_check_in",
            "data": check_in_prompts
        })

        return response

    def process_session_start(
        self,
        client_id: str,
        session_id: str,
        check_in_data: Dict[str, Any],
        homework_updates: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """세션 시작 데이터 처리"""

        result = {
            "client_id": client_id,
            "session_id": session_id,
            "processed": []
        }

        # 숙제 업데이트
        if homework_updates:
            for hw_update in homework_updates:
                self.homework_system.update_homework_status(
                    client_id=client_id,
                    homework_id=hw_update["homework_id"],
                    status=HomeworkStatus(hw_update["status"]),
                    completion_notes=hw_update.get("notes"),
                    reflection=hw_update.get("reflection")
                )
            result["processed"].append("homework_updates")

        # 체크인 제출
        check_in = self.check_in_system.submit_check_in(
            client_id=client_id,
            session_id=session_id,
            mood_rating=check_in_data["mood_rating"],
            mood_description=check_in_data["mood_description"],
            session_goal=check_in_data["session_goal"],
            homework_completed=check_in_data.get("homework_completed"),
            homework_reflection=check_in_data.get("homework_reflection")
        )
        result["check_in"] = check_in.to_dict()
        result["processed"].append("check_in")

        # 세션 컨텍스트 생성
        result["session_context"] = self.check_in_system.generate_session_context(client_id)

        # 기법 추천
        recommended = self.technique_system.recommend_next_technique(client_id)
        if recommended:
            result["recommended_technique"] = {
                "id": recommended.id,
                "name": recommended.name,
                "description": recommended.description
            }

        return result

    def get_session_end_summary(
        self,
        client_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """세션 종료 시 요약"""

        return {
            "progress_report": self.progress_viz.get_progress_report(client_id),
            "technique_progress": self.technique_system.get_progress_summary(client_id),
            "homework_summary": self.homework_system.get_homework_summary(client_id),
            "pending_homework": [
                hw.to_dict() for hw in self.homework_system.get_pending_homework(client_id)
            ]
        }

    def terminate_treatment(
        self,
        client_id: str,
        client_name: str = "내담자",
        termination_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """치료 종결 및 추적 일정 설정"""

        termination_date = datetime.now()

        # 추적 일정 생성
        follow_ups = self.follow_up_system.schedule_follow_ups(
            client_id=client_id,
            termination_date=termination_date,
            client_name=client_name
        )

        # 최종 진전 보고서
        final_report = self.progress_viz.get_progress_report(client_id)

        return {
            "client_id": client_id,
            "termination_date": termination_date.isoformat(),
            "termination_notes": termination_notes,
            "scheduled_follow_ups": [
                {
                    "type": fu.follow_up_type.value,
                    "date": fu.scheduled_date.strftime("%Y-%m-%d")
                }
                for fu in follow_ups
            ],
            "final_progress_report": final_report,
            "message": f"치료가 종결되었습니다. {len(follow_ups)}개의 사후 추적이 예약되었습니다."
        }

    def generate_comprehensive_report(self, client_id: str) -> str:
        """종합 보고서 생성"""

        # 각 시스템에서 데이터 수집
        baseline = self.baseline_manager.get_baseline_summary(client_id)
        progress = self.progress_viz.get_progress_report(client_id)
        technique = self.technique_system.get_progress_summary(client_id)
        homework = self.homework_system.get_homework_summary(client_id)
        follow_up = self.follow_up_system.get_client_follow_up_history(client_id)

        report_lines = [
            "=" * 60,
            "📊 종합 심리상담 보고서",
            "=" * 60,
            f"\n📅 생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"👤 내담자 ID: {client_id}",
            "\n" + "-" * 60,
            "1️⃣ 기저선 평가",
            "-" * 60
        ]

        if baseline:
            report_lines.append(baseline["summary"])
        else:
            report_lines.append("기저선 평가 데이터 없음")

        report_lines.extend([
            "\n" + "-" * 60,
            "2️⃣ 증상 변화 추이",
            "-" * 60
        ])

        if "summary" in progress:
            report_lines.append(progress["summary"])

        if "phq9" in progress.get("sections", {}):
            report_lines.append(progress["sections"]["phq9"]["graph"])

        if "gad7" in progress.get("sections", {}):
            report_lines.append(progress["sections"]["gad7"]["graph"])

        report_lines.extend([
            "\n" + "-" * 60,
            "3️⃣ 기법 학습 현황",
            "-" * 60,
            f"현재 수준: {technique.get('level_label', 'N/A')}",
            f"숙달한 기법: {len(technique.get('mastered', []))}개",
            f"학습 중: {len(technique.get('in_progress', []))}개"
        ])

        if technique.get("mastered"):
            report_lines.append("\n✅ 숙달 기법:")
            for t in technique["mastered"]:
                report_lines.append(f"  • {t['name']}")

        report_lines.extend([
            "\n" + "-" * 60,
            "4️⃣ 숙제 이행 현황",
            "-" * 60,
            f"총 숙제: {homework.get('total', 0)}개",
            f"완료: {homework.get('completed', 0)}개",
            f"이행률: {homework.get('completion_rate', 0)}%",
            homework.get('message', '')
        ])

        report_lines.extend([
            "\n" + "-" * 60,
            "5️⃣ 사후 추적 일정",
            "-" * 60
        ])

        if follow_up.get("schedules"):
            for s in follow_up["schedules"][:3]:
                status = {"pending": "⏳", "sent": "📤", "completed": "✅"}.get(s["status"], "❓")
                report_lines.append(f"  {status} {s['follow_up_type']}: {s['scheduled_date'][:10]}")
        else:
            report_lines.append("예정된 추적 일정 없음")

        report_lines.extend([
            "\n" + "=" * 60,
            "보고서 끝",
            "=" * 60
        ])

        return "\n".join(report_lines)


# ============================================================================
# API 통합 인터페이스
# ============================================================================

def create_structured_therapy_api():
    """구조화된 치료 시스템 API 생성"""

    manager = StructuredTherapyManager()

    return {
        "manager": manager,
        "baseline": manager.baseline_manager,
        "check_in": manager.check_in_system,
        "progress": manager.progress_viz,
        "techniques": manager.technique_system,
        "homework": manager.homework_system,
        "follow_up": manager.follow_up_system
    }


# 테스트/데모
if __name__ == "__main__":
    print("=" * 60)
    print("구조화된 치료 시스템 데모")
    print("=" * 60)

    # 시스템 초기화
    therapy_api = create_structured_therapy_api()
    manager = therapy_api["manager"]

    # 테스트 내담자
    client_id = "test_client_001"
    session_id = "session_001"

    # 1. 새 세션 시작
    print("\n1️⃣ 새 세션 시작...")
    start_result = manager.start_new_client_session(client_id)
    print(f"기저선 평가 필요: {start_result.get('needs_baseline', False)}")

    # 2. 기저선 평가 제출 (PHQ-9, GAD-7)
    if start_result.get("needs_baseline"):
        print("\n2️⃣ 기저선 평가 제출...")

        # PHQ-9
        phq9_responses = {f"phq9_{i}": 2 for i in range(1, 10)}
        phq9_result = therapy_api["baseline"].submit_assessment(
            client_id, session_id, AssessmentType.PHQ_9, phq9_responses, is_baseline=True
        )
        print(f"PHQ-9 점수: {phq9_result.total_score} ({phq9_result.severity_level})")

        # GAD-7
        gad7_responses = {f"gad7_{i}": 2 for i in range(1, 8)}
        gad7_result = therapy_api["baseline"].submit_assessment(
            client_id, session_id, AssessmentType.GAD_7, gad7_responses, is_baseline=True
        )
        print(f"GAD-7 점수: {gad7_result.total_score} ({gad7_result.severity_level})")

    # 3. 체크인 제출
    print("\n3️⃣ 회기 체크인...")
    check_in = therapy_api["check_in"].submit_check_in(
        client_id=client_id,
        session_id=session_id,
        mood_rating=6,
        mood_description="지난 주보다 조금 나아진 느낌이에요",
        session_goal="불안을 다루는 방법 배우기"
    )
    print(f"기분 점수: {check_in.mood_rating}/10")
    print(f"오늘 목표: {check_in.session_goal}")

    # 4. 기법 추천
    print("\n4️⃣ 추천 기법...")
    recommended = therapy_api["techniques"].recommend_next_technique(client_id)
    if recommended:
        print(f"추천: {recommended.name} ({recommended.difficulty.value})")
        print(f"설명: {recommended.description}")

    # 5. 숙제 할당
    print("\n5️⃣ 숙제 할당...")
    if recommended:
        homework = therapy_api["homework"].assign_technique_practice(
            client_id, session_id, recommended.id
        )
        if homework:
            print(f"할당된 숙제: {homework.title}")

    # 6. 진전 보고서
    print("\n6️⃣ 진전 보고서...")
    report = manager.generate_comprehensive_report(client_id)
    print(report)

    print("\n✅ 데모 완료!")
