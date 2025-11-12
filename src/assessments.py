"""
표준 심리검사 통합 모듈
Psychological Assessment Integration Module

PHQ-9, GAD-7, K-10 등 표준화된 심리검사 도구를 제공합니다.
대화형 진행 방식으로 자연스럽게 검사를 통합합니다.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class SeverityLevel(Enum):
    """심각도 수준"""
    MINIMAL = "minimal"
    MILD = "mild"
    MODERATE = "moderate"
    MODERATELY_SEVERE = "moderately_severe"
    SEVERE = "severe"


@dataclass
class AssessmentResult:
    """검사 결과"""
    assessment_type: str
    score: int
    max_score: int
    severity: SeverityLevel
    interpretation: str
    recommendations: List[str]
    requires_intervention: bool
    timestamp: datetime = field(default_factory=datetime.now)
    item_scores: Dict[int, int] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            "assessment_type": self.assessment_type,
            "score": self.score,
            "max_score": self.max_score,
            "severity": self.severity.value,
            "interpretation": self.interpretation,
            "recommendations": self.recommendations,
            "requires_intervention": self.requires_intervention,
            "timestamp": self.timestamp.isoformat(),
            "item_scores": self.item_scores
        }


class PHQ9Assessment:
    """
    Patient Health Questionnaire-9 (PHQ-9)
    우울증 선별 검사 (한국어 버전)

    9개 문항으로 구성되며, 최근 2주간의 우울 증상을 평가합니다.
    Item 9는 자살 사고를 평가하는 중요한 문항입니다.
    """

    def __init__(self):
        """초기화"""
        self.questions = self._load_questions()
        self.current_question = 0
        self.responses = {}

    def _load_questions(self) -> List[str]:
        """
        PHQ-9 문항 로드 (한국어 표준 버전)

        Returns:
            List[str]: 9개 문항
        """
        return [
            # Item 1
            "일이나 여가 활동을 하는 데 흥미나 즐거움을 느끼지 못함",

            # Item 2
            "기분이 가라앉거나, 우울하거나, 희망이 없음",

            # Item 3
            "잠들기 어렵거나 자주 깨어남, 또는 너무 많이 잠",

            # Item 4
            "피곤하다고 느끼거나 기운이 거의 없음",

            # Item 5
            "식욕이 줄거나 과식을 함",

            # Item 6
            "자신을 부정적으로 봄 - 혹은 자신이 실패자라고 느끼거나 자신 또는 가족을 실망시킴",

            # Item 7
            "신문을 읽거나 텔레비전을 보는 것과 같은 일에 집중하기 어려움",

            # Item 8
            "다른 사람들이 알아챌 정도로 말과 행동이 느려짐, 또는 반대로 너무 안절부절못하여 가만히 앉아 있을 수 없음",

            # Item 9 (자살 사고 - 특별 처리)
            "자신을 해치거나 차라리 죽는 것이 더 낫다고 생각함"
        ]

    def get_conversational_intro(self) -> str:
        """
        자연스러운 대화체 도입부

        Returns:
            str: 도입 메시지
        """
        return """지금부터 최근 2주간의 기분 상태에 대해 몇 가지 여쭤볼게요.

편안하게 답변해주시면 됩니다. 정해진 답은 없으니, 솔직하게 느끼신 대로 말씀해주세요.

각 문항에 대해 최근 2주 동안 얼마나 자주 다음과 같은 일들로 고민했는지 알려주세요:
• 전혀 없음 (0점)
• 며칠 동안 (1점)
• 7일 이상 (2점)
• 거의 매일 (3점)

준비되셨나요? 첫 번째 질문 드릴게요."""

    def get_next_question(self) -> Optional[Tuple[int, str]]:
        """
        다음 질문 가져오기

        Returns:
            Optional[Tuple[int, str]]: (문항 번호, 질문) 또는 None
        """
        if self.current_question >= len(self.questions):
            return None

        question_num = self.current_question + 1
        question_text = self.questions[self.current_question]

        # Item 9는 특별히 조심스럽게 물어봄
        if question_num == 9:
            formatted = f"""마지막 질문입니다.

최근 2주 동안, 이런 생각이 드신 적이 있나요?
"{question_text}"

이 질문은 매우 중요한 질문이에요. 편안하게 답변해주세요."""
        else:
            formatted = f"""질문 {question_num}/9

최근 2주 동안:
"{question_text}"

이런 일이 얼마나 자주 있었나요?"""

        return (question_num, formatted)

    def record_response(self, question_num: int, score: int) -> bool:
        """
        응답 기록

        Args:
            question_num: 문항 번호 (1-9)
            score: 점수 (0-3)

        Returns:
            bool: 성공 여부
        """
        if not (1 <= question_num <= 9 and 0 <= score <= 3):
            return False

        self.responses[question_num] = score
        self.current_question = question_num

        return True

    def calculate_score(self) -> AssessmentResult:
        """
        PHQ-9 점수 계산 및 해석

        Returns:
            AssessmentResult: 검사 결과
        """
        if len(self.responses) != 9:
            raise ValueError("모든 문항에 응답하지 않았습니다")

        total_score = sum(self.responses.values())

        # 심각도 판정 (한국 임상 기준)
        if total_score <= 4:
            severity = SeverityLevel.MINIMAL
            interpretation = "최소 수준의 우울 증상"
        elif total_score <= 9:
            severity = SeverityLevel.MILD
            interpretation = "가벼운 우울 증상"
        elif total_score <= 14:
            severity = SeverityLevel.MODERATE
            interpretation = "중간 정도의 우울 증상"
        elif total_score <= 19:
            severity = SeverityLevel.MODERATELY_SEVERE
            interpretation = "중간에서 심한 정도의 우울 증상"
        else:  # 20-27
            severity = SeverityLevel.SEVERE
            interpretation = "심한 우울 증상"

        # Item 9 특별 체크
        item9_score = self.responses.get(9, 0)
        has_suicidal_ideation = item9_score > 0

        # 권고사항 생성
        recommendations = self._generate_recommendations(
            severity,
            total_score,
            has_suicidal_ideation
        )

        # 개입 필요 여부
        requires_intervention = (
            severity in [SeverityLevel.MODERATELY_SEVERE, SeverityLevel.SEVERE] or
            has_suicidal_ideation
        )

        result = AssessmentResult(
            assessment_type="PHQ-9",
            score=total_score,
            max_score=27,
            severity=severity,
            interpretation=interpretation,
            recommendations=recommendations,
            requires_intervention=requires_intervention,
            item_scores=self.responses.copy()
        )

        logger.info(f"PHQ-9 완료: 점수 {total_score}/27, 심각도 {severity.value}")

        return result

    def _generate_recommendations(
        self,
        severity: SeverityLevel,
        score: int,
        has_suicidal_ideation: bool
    ) -> List[str]:
        """
        권고사항 생성

        Args:
            severity: 심각도
            score: 총점
            has_suicidal_ideation: 자살 사고 여부

        Returns:
            List[str]: 권고사항 리스트
        """
        recommendations = []

        # Item 9 양성 반응 시 최우선
        if has_suicidal_ideation:
            recommendations.append("⚠️ 자살 사고가 감지되었습니다. 즉시 전문가의 도움이 필요합니다.")
            recommendations.append("🆘 자살예방상담전화: 1393 (24시간 무료)")
            recommendations.append("🆘 정신건강위기상담전화: 1577-0199")

        # 심각도별 권고
        if severity == SeverityLevel.MINIMAL:
            recommendations.append("✅ 현재 우울 증상은 최소 수준입니다.")
            recommendations.append("💪 현재의 긍정적인 상태를 유지하세요.")
            recommendations.append("🏃 규칙적인 운동과 충분한 수면을 추천합니다.")

        elif severity == SeverityLevel.MILD:
            recommendations.append("📊 가벼운 우울 증상이 있습니다.")
            recommendations.append("🧘 셀프케어 활동을 늘려보세요 (운동, 취미, 사회활동).")
            recommendations.append("📖 인지행동치료(CBT) 자가 학습을 시도해보세요.")
            recommendations.append("💬 신뢰할 수 있는 사람과 대화를 나누세요.")

        elif severity == SeverityLevel.MODERATE:
            recommendations.append("⚠️ 중간 정도의 우울 증상이 있습니다.")
            recommendations.append("👨‍⚕️ 전문가 상담을 고려해보시길 권장합니다.")
            recommendations.append("📞 정신건강복지센터(1577-0199) 또는 가까운 상담센터에 연락하세요.")
            recommendations.append("📝 대학 상담센터나 EAP 프로그램을 이용하세요 (해당 시).")

        elif severity == SeverityLevel.MODERATELY_SEVERE:
            recommendations.append("🚨 중간에서 심한 정도의 우울 증상입니다.")
            recommendations.append("⚕️ 정신건강의학과 진료를 강력히 권장합니다.")
            recommendations.append("💊 약물치료와 함께 심리치료를 병행하는 것이 효과적일 수 있습니다.")
            recommendations.append("👥 가족이나 가까운 사람에게 도움을 요청하세요.")

        else:  # SEVERE
            recommendations.append("🆘 심한 우울 증상입니다. 즉시 전문가의 도움이 필요합니다.")
            recommendations.append("🏥 가능한 빨리 정신건강의학과를 방문하세요.")
            recommendations.append("💊 입원치료가 필요할 수 있습니다.")
            recommendations.append("👨‍👩‍👧 가족이나 보호자와 함께 병원을 방문하세요.")

        return recommendations

    def reset(self):
        """검사 초기화"""
        self.current_question = 0
        self.responses = {}


class GAD7Assessment:
    """
    Generalized Anxiety Disorder-7 (GAD-7)
    범불안장애 선별 검사 (한국어 버전)

    7개 문항으로 구성되며, 최근 2주간의 불안 증상을 평가합니다.
    """

    def __init__(self):
        """초기화"""
        self.questions = self._load_questions()
        self.current_question = 0
        self.responses = {}

    def _load_questions(self) -> List[str]:
        """
        GAD-7 문항 로드

        Returns:
            List[str]: 7개 문항
        """
        return [
            "초조하거나 불안하거나 조마조마하게 느낌",
            "걱정하는 것을 멈추거나 조절할 수 없음",
            "여러 가지 것들에 대해 걱정을 너무 많이 함",
            "편하게 있기가 어려움",
            "너무 안절부절못해서 가만히 있기 힘듦",
            "쉽게 짜증이 나거나 쉽게 성을 냄",
            "마치 끔찍한 일이 일어날 것처럼 두려움을 느낌"
        ]

    def get_conversational_intro(self) -> str:
        """대화체 도입부"""
        return """이번에는 최근 2주간의 불안이나 긴장 상태에 대해 여쭤볼게요.

마찬가지로 편안하게 답변해주시면 됩니다.

각 문항에 대해 최근 2주 동안 얼마나 자주 다음과 같은 증상으로 고민했는지 알려주세요:
• 전혀 없음 (0점)
• 며칠 동안 (1점)
• 7일 이상 (2점)
• 거의 매일 (3점)

시작할게요."""

    def get_next_question(self) -> Optional[Tuple[int, str]]:
        """다음 질문 가져오기"""
        if self.current_question >= len(self.questions):
            return None

        question_num = self.current_question + 1
        question_text = self.questions[self.current_question]

        formatted = f"""질문 {question_num}/7

최근 2주 동안:
"{question_text}"

이런 증상이 얼마나 자주 있었나요?"""

        return (question_num, formatted)

    def record_response(self, question_num: int, score: int) -> bool:
        """응답 기록"""
        if not (1 <= question_num <= 7 and 0 <= score <= 3):
            return False

        self.responses[question_num] = score
        self.current_question = question_num

        return True

    def calculate_score(self) -> AssessmentResult:
        """GAD-7 점수 계산 및 해석"""
        if len(self.responses) != 7:
            raise ValueError("모든 문항에 응답하지 않았습니다")

        total_score = sum(self.responses.values())

        # 심각도 판정
        if total_score <= 4:
            severity = SeverityLevel.MINIMAL
            interpretation = "최소 수준의 불안 증상"
        elif total_score <= 9:
            severity = SeverityLevel.MILD
            interpretation = "가벼운 불안 증상"
        elif total_score <= 14:
            severity = SeverityLevel.MODERATE
            interpretation = "중간 정도의 불안 증상"
        else:  # 15-21
            severity = SeverityLevel.SEVERE
            interpretation = "심한 불안 증상"

        recommendations = self._generate_recommendations(severity, total_score)

        requires_intervention = severity in [SeverityLevel.MODERATE, SeverityLevel.SEVERE]

        result = AssessmentResult(
            assessment_type="GAD-7",
            score=total_score,
            max_score=21,
            severity=severity,
            interpretation=interpretation,
            recommendations=recommendations,
            requires_intervention=requires_intervention,
            item_scores=self.responses.copy()
        )

        logger.info(f"GAD-7 완료: 점수 {total_score}/21, 심각도 {severity.value}")

        return result

    def _generate_recommendations(self, severity: SeverityLevel, score: int) -> List[str]:
        """권고사항 생성"""
        recommendations = []

        if severity == SeverityLevel.MINIMAL:
            recommendations.append("✅ 현재 불안 증상은 최소 수준입니다.")
            recommendations.append("🧘 마음챙김이나 명상을 통해 현재 상태를 유지하세요.")
            recommendations.append("💪 스트레스 관리 기술을 배워두면 도움이 됩니다.")

        elif severity == SeverityLevel.MILD:
            recommendations.append("📊 가벼운 불안 증상이 있습니다.")
            recommendations.append("🧘 이완 훈련과 호흡 운동을 시도해보세요.")
            recommendations.append("📖 불안 관리 기법 (4-7-8 호흡법 등)을 학습하세요.")
            recommendations.append("🏃 규칙적인 운동이 불안 감소에 효과적입니다.")

        elif severity == SeverityLevel.MODERATE:
            recommendations.append("⚠️ 중간 정도의 불안 증상이 있습니다.")
            recommendations.append("👨‍⚕️ 전문가 상담을 고려해보시길 권장합니다.")
            recommendations.append("💬 인지행동치료(CBT)가 불안장애에 매우 효과적입니다.")
            recommendations.append("📞 정신건강복지센터(1577-0199)에 연락하세요.")

        else:  # SEVERE
            recommendations.append("🚨 심한 불안 증상입니다.")
            recommendations.append("⚕️ 정신건강의학과 진료가 필요합니다.")
            recommendations.append("💊 약물치료와 심리치료 병행을 고려하세요.")
            recommendations.append("🏥 가능한 빨리 전문가를 만나보세요.")

        return recommendations

    def reset(self):
        """검사 초기화"""
        self.current_question = 0
        self.responses = {}


class K10Assessment:
    """
    Kessler Psychological Distress Scale (K-10)
    한국형 정신건강 선별 도구

    10개 문항으로 구성되며, 최근 4주간의 정신적 고통을 평가합니다.
    """

    def __init__(self):
        """초기화"""
        self.questions = self._load_questions()
        self.current_question = 0
        self.responses = {}

    def _load_questions(self) -> List[str]:
        """K-10 문항 로드"""
        return [
            "지난 4주 동안 얼마나 자주 피곤한 이유 없이 피곤함을 느꼈습니까?",
            "지난 4주 동안 얼마나 자주 초조하고 불안함을 느꼈습니까?",
            "지난 4주 동안 얼마나 자주 너무 초조하고 불안해서 아무것도 당신을 진정시킬 수 없다고 느꼈습니까?",
            "지난 4주 동안 얼마나 자주 희망이 없다고 느꼈습니까?",
            "지난 4주 동안 얼마나 자주 안절부절못하거나 들떠있다고 느꼈습니까?",
            "지난 4주 동안 얼마나 자주 너무 안절부절못해서 가만히 앉아 있을 수 없다고 느꼈습니까?",
            "지난 4주 동안 얼마나 자주 우울함을 느꼈습니까?",
            "지난 4주 동안 얼마나 자주 모든 일에 힘이 든다고 느꼈습니까?",
            "지난 4주 동안 얼마나 자주 너무 슬퍼서 아무것도 당신을 즐겁게 할 수 없다고 느꼈습니까?",
            "지난 4주 동안 얼마나 자주 자신이 가치 없는 사람이라고 느꼈습니까?"
        ]

    def get_conversational_intro(self) -> str:
        """대화체 도입부"""
        return """이번에는 지난 4주간의 전반적인 정신 건강 상태를 확인해볼게요.

각 질문에 대해 얼마나 자주 그렇게 느꼈는지 알려주세요:
• 전혀 없음 (1점)
• 거의 없음 (2점)
• 가끔 (3점)
• 자주 (4점)
• 거의 언제나 (5점)

시작하겠습니다."""

    def get_next_question(self) -> Optional[Tuple[int, str]]:
        """다음 질문 가져오기"""
        if self.current_question >= len(self.questions):
            return None

        question_num = self.current_question + 1
        question_text = self.questions[self.current_question]

        formatted = f"""질문 {question_num}/10

{question_text}"""

        return (question_num, formatted)

    def record_response(self, question_num: int, score: int) -> bool:
        """응답 기록 (1-5점)"""
        if not (1 <= question_num <= 10 and 1 <= score <= 5):
            return False

        self.responses[question_num] = score
        self.current_question = question_num

        return True

    def calculate_score(self) -> AssessmentResult:
        """K-10 점수 계산"""
        if len(self.responses) != 10:
            raise ValueError("모든 문항에 응답하지 않았습니다")

        total_score = sum(self.responses.values())

        # 심각도 판정 (한국 표준화 기준)
        if total_score <= 19:
            severity = SeverityLevel.MINIMAL
            interpretation = "정신적 고통 수준이 낮음"
        elif total_score <= 24:
            severity = SeverityLevel.MILD
            interpretation = "경미한 정신적 고통"
        elif total_score <= 29:
            severity = SeverityLevel.MODERATE
            interpretation = "중간 정도의 정신적 고통"
        else:  # 30-50
            severity = SeverityLevel.SEVERE
            interpretation = "심한 정신적 고통"

        recommendations = self._generate_recommendations(severity, total_score)

        requires_intervention = severity in [SeverityLevel.MODERATE, SeverityLevel.SEVERE]

        result = AssessmentResult(
            assessment_type="K-10",
            score=total_score,
            max_score=50,
            severity=severity,
            interpretation=interpretation,
            recommendations=recommendations,
            requires_intervention=requires_intervention,
            item_scores=self.responses.copy()
        )

        logger.info(f"K-10 완료: 점수 {total_score}/50, 심각도 {severity.value}")

        return result

    def _generate_recommendations(self, severity: SeverityLevel, score: int) -> List[str]:
        """권고사항 생성"""
        recommendations = []

        if severity == SeverityLevel.MINIMAL:
            recommendations.append("✅ 정신적 고통 수준이 낮습니다.")
            recommendations.append("💪 건강한 생활습관을 유지하세요.")

        elif severity == SeverityLevel.MILD:
            recommendations.append("📊 경미한 정신적 고통이 있습니다.")
            recommendations.append("🧘 스트레스 관리와 셀프케어를 강화하세요.")

        elif severity == SeverityLevel.MODERATE:
            recommendations.append("⚠️ 중간 정도의 정신적 고통이 있습니다.")
            recommendations.append("👨‍⚕️ 전문가 상담을 권장합니다.")
            recommendations.append("📞 정신건강복지센터(1577-0199)에 연락하세요.")

        else:  # SEVERE
            recommendations.append("🚨 심한 정신적 고통이 있습니다.")
            recommendations.append("⚕️ 즉시 정신건강 전문가를 만나보세요.")
            recommendations.append("🏥 정신건강의학과 진료가 필요합니다.")

        return recommendations

    def reset(self):
        """검사 초기화"""
        self.current_question = 0
        self.responses = {}


class AssessmentManager:
    """
    검사 통합 관리 시스템

    여러 심리검사를 관리하고, 대화 맥락에 따라
    적절한 검사를 자동으로 선택하거나 추천합니다.
    """

    def __init__(self):
        """초기화"""
        self.assessments = {
            "PHQ-9": PHQ9Assessment,
            "GAD-7": GAD7Assessment,
            "K-10": K10Assessment
        }
        self.results_history = []

    def smart_selection(self, conversation_context: Dict) -> Optional[str]:
        """
        대화 맥락 기반 검사 자동 선택

        Args:
            conversation_context: 대화 맥락 정보
                - primary_emotion: 주요 감정
                - keywords: 감지된 키워드
                - crisis_level: 위기 수준

        Returns:
            Optional[str]: 추천 검사 이름
        """
        emotion = conversation_context.get("primary_emotion", "")
        keywords = conversation_context.get("keywords", [])

        # 우울 관련
        depression_indicators = ["우울", "슬픔", "무기력", "희망 없"]
        if emotion in depression_indicators or any(k in " ".join(keywords) for k in depression_indicators):
            return "PHQ-9"

        # 불안 관련
        anxiety_indicators = ["불안", "두려움", "초조", "걱정"]
        if emotion in anxiety_indicators or any(k in " ".join(keywords) for k in anxiety_indicators):
            return "GAD-7"

        # 일반적인 정신건강 선별
        return "K-10"

    def create_assessment(self, assessment_type: str):
        """
        검사 인스턴스 생성

        Args:
            assessment_type: 검사 유형 (PHQ-9, GAD-7, K-10)

        Returns:
            Assessment 인스턴스
        """
        if assessment_type not in self.assessments:
            raise ValueError(f"알 수 없는 검사 유형: {assessment_type}")

        return self.assessments[assessment_type]()

    def save_result(self, result: AssessmentResult):
        """
        검사 결과 저장

        Args:
            result: 검사 결과
        """
        self.results_history.append(result)
        logger.info(f"검사 결과 저장: {result.assessment_type}, 점수 {result.score}")

    def get_progress_trend(self, assessment_type: str) -> Dict:
        """
        시간에 따른 점수 변화 추적

        Args:
            assessment_type: 검사 유형

        Returns:
            Dict: 추세 정보
        """
        # 해당 검사 유형의 결과만 필터링
        filtered = [r for r in self.results_history if r.assessment_type == assessment_type]

        if len(filtered) < 2:
            return {"trend": "insufficient_data"}

        # 점수 리스트
        scores = [r.score for r in filtered]
        timestamps = [r.timestamp for r in filtered]

        # 추세 계산
        if scores[-1] > scores[0]:
            trend = "worsening"
        elif scores[-1] < scores[0]:
            trend = "improving"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "scores": scores,
            "timestamps": [t.isoformat() for t in timestamps],
            "latest_score": scores[-1],
            "first_score": scores[0],
            "change": scores[-1] - scores[0]
        }

    def get_intervention_mapping(self, result: AssessmentResult) -> Dict[str, List[str]]:
        """
        검사 결과 기반 개입 전략 매핑

        Args:
            result: 검사 결과

        Returns:
            Dict: 개입 전략
        """
        INTERVENTION_MAPPING = {
            SeverityLevel.MINIMAL: {
                "activities": [
                    "규칙적인 생활 리듬 유지하기",
                    "주 3회 이상 30분 운동하기",
                    "충분한 수면 (7-8시간)"
                ],
                "techniques": [
                    "마음챙김 명상 5분",
                    "감사 일기 쓰기",
                    "사회적 활동 유지"
                ],
                "monitoring": "월 1회 자가 점검"
            },
            SeverityLevel.MILD: {
                "activities": [
                    "즐거운 활동 계획하기",
                    "햇빛 쐬기 (하루 30분)",
                    "카페인 줄이기"
                ],
                "techniques": [
                    "CBT 자가 학습",
                    "호흡 이완 훈련",
                    "인지 재구성 연습"
                ],
                "monitoring": "주 1회 자가 점검"
            },
            SeverityLevel.MODERATE: {
                "activities": [
                    "전문가 상담 예약",
                    "활동 계획표 작성",
                    "지지 체계 활용"
                ],
                "techniques": [
                    "전문가 지도 하 CBT",
                    "행동 활성화",
                    "문제 해결 훈련"
                ],
                "monitoring": "전문가 정기 상담 (주 1회)"
            },
            SeverityLevel.MODERATELY_SEVERE: {
                "activities": [
                    "정신과 진료 받기",
                    "일상 루틴 단순화",
                    "가족/친구 지원 요청"
                ],
                "techniques": [
                    "약물치료 + 심리치료",
                    "집중적 CBT",
                    "위기 대응 계획"
                ],
                "monitoring": "전문가 집중 관리 (주 2-3회)"
            },
            SeverityLevel.SEVERE: {
                "activities": [
                    "즉시 정신과 방문",
                    "안전 계획 수립",
                    "24시간 지원 체계 구축"
                ],
                "techniques": [
                    "입원치료 고려",
                    "약물치료 필수",
                    "집중 심리치료"
                ],
                "monitoring": "매일 전문가 모니터링"
            }
        }

        return INTERVENTION_MAPPING.get(result.severity, {})


if __name__ == "__main__":
    # 테스트 코드
    print("=== 심리검사 시스템 테스트 ===\n")

    # PHQ-9 테스트
    print("1. PHQ-9 우울증 선별 검사")
    print("-" * 70)

    phq9 = PHQ9Assessment()
    print(phq9.get_conversational_intro())
    print()

    # 예시 응답 (중간 정도의 우울)
    test_responses = {1: 2, 2: 2, 3: 1, 4: 2, 5: 1, 6: 2, 7: 1, 8: 1, 9: 1}

    for qnum, score in test_responses.items():
        phq9.record_response(qnum, score)

    result = phq9.calculate_score()

    print(f"총점: {result.score}/{result.max_score}")
    print(f"심각도: {result.severity.value}")
    print(f"해석: {result.interpretation}")
    print(f"개입 필요: {result.requires_intervention}")
    print("\n권고사항:")
    for rec in result.recommendations:
        print(f"  • {rec}")

    print("\n" + "=" * 70 + "\n")

    # AssessmentManager 테스트
    print("2. 검사 관리 시스템")
    print("-" * 70)

    manager = AssessmentManager()

    # 맥락 기반 검사 선택
    context1 = {"primary_emotion": "우울", "keywords": ["힘들다", "우울해"]}
    recommended = manager.smart_selection(context1)
    print(f"우울 증상 감지 → 추천 검사: {recommended}")

    context2 = {"primary_emotion": "불안", "keywords": ["걱정", "초조"]}
    recommended = manager.smart_selection(context2)
    print(f"불안 증상 감지 → 추천 검사: {recommended}")

    print("\n개입 전략 매핑:")
    interventions = manager.get_intervention_mapping(result)
    print(f"활동: {interventions.get('activities', [])}")
    print(f"기법: {interventions.get('techniques', [])}")
    print(f"모니터링: {interventions.get('monitoring', '')}")
