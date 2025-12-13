"""
사용자 피드백 수집 시스템 (User Feedback Collection System)
만족도/불만족 패턴 학습

기능:
- 다양한 피드백 유형 수집 (별점, 반응, 텍스트)
- 불만족 패턴 자동 분석
- 개선 인사이트 도출
- 피드백 기반 응답 개선 제안
- 실시간 만족도 트래킹
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from enum import Enum
import json

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """피드백 유형"""
    RATING = "rating"           # 별점 (1-5)
    REACTION = "reaction"       # 반응 (helpful, not_helpful)
    TEXT = "text"               # 텍스트 피드백
    IMPLICIT = "implicit"       # 암시적 피드백 (응답 시간, 이탈 등)
    CORRECTION = "correction"   # 수정 요청


class DissatisfactionReason(Enum):
    """불만족 원인"""
    GENERIC = "generic"             # 너무 일반적
    NOT_EMPATHETIC = "no_empathy"   # 공감 부족
    TOO_LONG = "too_long"           # 너무 김
    TOO_SHORT = "too_short"         # 너무 짧음
    OFF_TOPIC = "off_topic"         # 주제 벗어남
    UNNATURAL = "unnatural"         # 부자연스러움
    INSENSITIVE = "insensitive"     # 민감성 부족
    REPETITIVE = "repetitive"       # 반복적
    UNHELPFUL = "unhelpful"         # 도움 안됨
    INAPPROPRIATE = "inappropriate" # 부적절


@dataclass
class Feedback:
    """피드백 데이터"""
    id: str
    session_id: str
    message_id: str
    feedback_type: FeedbackType
    value: Any  # rating: int, reaction: str, text: str
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "message_id": self.message_id,
            "type": self.feedback_type.value,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context
        }


@dataclass
class FeedbackAnalysis:
    """피드백 분석 결과"""
    total_feedback: int
    satisfaction_rate: float
    average_rating: float
    dissatisfaction_reasons: Dict[str, int]
    improvement_suggestions: List[str]
    trends: Dict[str, Any]


class FeedbackCollector:
    """
    사용자 피드백 수집기

    다양한 형태의 피드백을 수집하고 분석합니다.
    """

    def __init__(self):
        self.feedbacks: List[Feedback] = []
        self.session_feedbacks: Dict[str, List[Feedback]] = defaultdict(list)

        # 불만족 키워드 패턴
        self.dissatisfaction_patterns = {
            DissatisfactionReason.GENERIC: [
                "뻔한", "일반적", "누구나", "당연한", "그런 말",
                "아무 말", "의미 없", "도움 안"
            ],
            DissatisfactionReason.NOT_EMPATHETIC: [
                "공감", "이해 못", "내 마음", "모르", "차갑",
                "기계적", "형식적", "진심 없"
            ],
            DissatisfactionReason.TOO_LONG: [
                "길어", "너무 많", "읽기 힘", "요약", "짧게"
            ],
            DissatisfactionReason.TOO_SHORT: [
                "짧아", "더 말해", "그게 다", "부족", "성의 없"
            ],
            DissatisfactionReason.OFF_TOPIC: [
                "다른 말", "엉뚱", "주제", "그게 아니", "딴 소리"
            ],
            DissatisfactionReason.UNNATURAL: [
                "어색", "번역", "이상", "부자연", "말투"
            ],
            DissatisfactionReason.REPETITIVE: [
                "반복", "같은 말", "계속", "또", "이미 말했"
            ],
            DissatisfactionReason.UNHELPFUL: [
                "도움", "안 됨", "쓸모", "소용없", "해결"
            ]
        }

        # 만족 키워드 패턴
        self.satisfaction_patterns = [
            "고마워", "감사", "도움이 됐", "위로가 됐", "좋아",
            "이해해", "공감", "맞아", "정확", "좋네", "편안"
        ]

        logger.info("FeedbackCollector initialized")

    def collect_rating(
        self,
        session_id: str,
        message_id: str,
        rating: int,
        context: Optional[Dict] = None
    ) -> Feedback:
        """
        별점 피드백 수집

        Args:
            session_id: 세션 ID
            message_id: 메시지 ID
            rating: 별점 (1-5)
            context: 추가 컨텍스트

        Returns:
            Feedback: 수집된 피드백
        """
        rating = max(1, min(5, rating))  # 1-5 범위로 제한

        feedback = Feedback(
            id=f"fb_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            session_id=session_id,
            message_id=message_id,
            feedback_type=FeedbackType.RATING,
            value=rating,
            context=context or {}
        )

        self._store_feedback(feedback)
        logger.info(f"Rating feedback collected: {rating}/5 for message {message_id}")

        return feedback

    def collect_reaction(
        self,
        session_id: str,
        message_id: str,
        reaction: str,
        context: Optional[Dict] = None
    ) -> Feedback:
        """
        반응 피드백 수집 (helpful / not_helpful)

        Args:
            session_id: 세션 ID
            message_id: 메시지 ID
            reaction: 반응 (helpful, not_helpful)
            context: 추가 컨텍스트
        """
        if reaction not in ["helpful", "not_helpful", "neutral"]:
            reaction = "neutral"

        feedback = Feedback(
            id=f"fb_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            session_id=session_id,
            message_id=message_id,
            feedback_type=FeedbackType.REACTION,
            value=reaction,
            context=context or {}
        )

        self._store_feedback(feedback)
        logger.info(f"Reaction feedback collected: {reaction} for message {message_id}")

        return feedback

    def collect_text_feedback(
        self,
        session_id: str,
        message_id: str,
        text: str,
        context: Optional[Dict] = None
    ) -> Feedback:
        """
        텍스트 피드백 수집

        Args:
            session_id: 세션 ID
            message_id: 메시지 ID
            text: 피드백 텍스트
            context: 추가 컨텍스트
        """
        # 불만족 원인 자동 분류
        reasons = self._classify_dissatisfaction(text)

        feedback = Feedback(
            id=f"fb_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            session_id=session_id,
            message_id=message_id,
            feedback_type=FeedbackType.TEXT,
            value=text,
            context={
                **(context or {}),
                "classified_reasons": [r.value for r in reasons],
                "sentiment": self._analyze_sentiment(text)
            }
        )

        self._store_feedback(feedback)
        logger.info(f"Text feedback collected for message {message_id}")

        return feedback

    def collect_implicit_feedback(
        self,
        session_id: str,
        message_id: str,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> Feedback:
        """
        암시적 피드백 수집 (사용자 행동 기반)

        Args:
            session_id: 세션 ID
            message_id: 메시지 ID
            event_type: 이벤트 유형 (abandon, quick_response, long_pause, etc.)
            event_data: 이벤트 데이터
        """
        feedback = Feedback(
            id=f"fb_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            session_id=session_id,
            message_id=message_id,
            feedback_type=FeedbackType.IMPLICIT,
            value=event_type,
            context=event_data
        )

        self._store_feedback(feedback)
        logger.debug(f"Implicit feedback collected: {event_type}")

        return feedback

    def _store_feedback(self, feedback: Feedback):
        """피드백 저장"""
        self.feedbacks.append(feedback)
        self.session_feedbacks[feedback.session_id].append(feedback)

        # 메모리 관리: 최근 10000개만 유지
        if len(self.feedbacks) > 10000:
            self.feedbacks = self.feedbacks[-10000:]

    def _classify_dissatisfaction(self, text: str) -> List[DissatisfactionReason]:
        """불만족 원인 분류"""
        reasons = []
        text_lower = text.lower()

        for reason, patterns in self.dissatisfaction_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    reasons.append(reason)
                    break

        return reasons if reasons else [DissatisfactionReason.GENERIC]

    def _analyze_sentiment(self, text: str) -> str:
        """간단한 감정 분석"""
        text_lower = text.lower()

        positive_count = sum(1 for p in self.satisfaction_patterns if p in text_lower)
        negative_count = sum(
            1 for patterns in self.dissatisfaction_patterns.values()
            for p in patterns if p in text_lower
        )

        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """세션별 피드백 요약"""
        feedbacks = self.session_feedbacks.get(session_id, [])

        if not feedbacks:
            return {"message": "No feedback for this session"}

        ratings = [f.value for f in feedbacks if f.feedback_type == FeedbackType.RATING]
        reactions = [f.value for f in feedbacks if f.feedback_type == FeedbackType.REACTION]

        return {
            "session_id": session_id,
            "total_feedbacks": len(feedbacks),
            "average_rating": sum(ratings) / len(ratings) if ratings else None,
            "helpful_ratio": reactions.count("helpful") / len(reactions) if reactions else None,
            "text_feedbacks": [
                f.value for f in feedbacks if f.feedback_type == FeedbackType.TEXT
            ]
        }

    def analyze_feedback(
        self,
        time_range_hours: int = 24
    ) -> FeedbackAnalysis:
        """
        피드백 종합 분석

        Args:
            time_range_hours: 분석 기간 (시간)

        Returns:
            FeedbackAnalysis: 분석 결과
        """
        cutoff = datetime.now() - timedelta(hours=time_range_hours)
        recent_feedbacks = [f for f in self.feedbacks if f.timestamp >= cutoff]

        if not recent_feedbacks:
            return FeedbackAnalysis(
                total_feedback=0,
                satisfaction_rate=0.0,
                average_rating=0.0,
                dissatisfaction_reasons={},
                improvement_suggestions=[],
                trends={}
            )

        # 만족도 계산
        ratings = [f.value for f in recent_feedbacks if f.feedback_type == FeedbackType.RATING]
        reactions = [f.value for f in recent_feedbacks if f.feedback_type == FeedbackType.REACTION]

        average_rating = sum(ratings) / len(ratings) if ratings else 0
        satisfaction_rate = (
            (sum(1 for r in ratings if r >= 4) / len(ratings)) if ratings
            else (reactions.count("helpful") / len(reactions) if reactions else 0)
        )

        # 불만족 원인 집계
        dissatisfaction_reasons: Counter = Counter()
        for f in recent_feedbacks:
            if f.feedback_type == FeedbackType.TEXT:
                reasons = f.context.get("classified_reasons", [])
                for r in reasons:
                    dissatisfaction_reasons[r] += 1

        # 개선 제안 생성
        suggestions = self._generate_improvement_suggestions(dissatisfaction_reasons)

        # 트렌드 분석
        trends = self._analyze_trends(recent_feedbacks)

        return FeedbackAnalysis(
            total_feedback=len(recent_feedbacks),
            satisfaction_rate=satisfaction_rate,
            average_rating=average_rating,
            dissatisfaction_reasons=dict(dissatisfaction_reasons),
            improvement_suggestions=suggestions,
            trends=trends
        )

    def _generate_improvement_suggestions(
        self,
        reasons: Counter
    ) -> List[str]:
        """불만족 원인 기반 개선 제안 생성"""
        suggestions = []

        suggestion_map = {
            DissatisfactionReason.GENERIC.value: "응답의 구체성을 높이세요. 사용자 상황에 맞는 맞춤 응답을 제공하세요.",
            DissatisfactionReason.NOT_EMPATHETIC.value: "공감 표현을 강화하세요. '~셨군요', '~하셨겠어요' 등의 표현을 늘리세요.",
            DissatisfactionReason.TOO_LONG.value: "응답 길이를 줄이세요. 2-3문장이 적절합니다.",
            DissatisfactionReason.TOO_SHORT.value: "응답에 더 많은 공감과 탐색 질문을 추가하세요.",
            DissatisfactionReason.OFF_TOPIC.value: "사용자 메시지에 더 집중하세요. 맥락 파악을 강화하세요.",
            DissatisfactionReason.UNNATURAL.value: "자연스러운 한국어 표현을 사용하세요. 번역투를 피하세요.",
            DissatisfactionReason.REPETITIVE.value: "다양한 표현을 사용하세요. 같은 패턴 반복을 피하세요.",
            DissatisfactionReason.UNHELPFUL.value: "실용적인 조언과 리소스를 제공하세요."
        }

        # 빈도 순으로 제안 추가
        for reason, count in reasons.most_common(5):
            if reason in suggestion_map:
                suggestions.append(f"[{count}건] {suggestion_map[reason]}")

        return suggestions

    def _analyze_trends(self, feedbacks: List[Feedback]) -> Dict[str, Any]:
        """피드백 트렌드 분석"""
        if not feedbacks:
            return {}

        # 시간대별 만족도
        hourly_ratings: Dict[str, List[int]] = defaultdict(list)
        for f in feedbacks:
            if f.feedback_type == FeedbackType.RATING:
                hour_key = f.timestamp.strftime("%Y-%m-%d %H:00")
                hourly_ratings[hour_key].append(f.value)

        hourly_averages = {
            k: sum(v) / len(v) for k, v in hourly_ratings.items()
        }

        # 전체 추세 계산
        if len(hourly_averages) >= 2:
            values = list(hourly_averages.values())
            recent_avg = sum(values[-3:]) / min(3, len(values))
            older_avg = sum(values[:-3]) / max(1, len(values) - 3) if len(values) > 3 else recent_avg
            trend = "improving" if recent_avg > older_avg else "declining" if recent_avg < older_avg else "stable"
        else:
            trend = "insufficient_data"

        return {
            "hourly_ratings": hourly_averages,
            "overall_trend": trend
        }

    def get_improvement_prompt(self) -> str:
        """
        피드백 기반 개선 프롬프트 생성

        Returns:
            str: 시스템 프롬프트에 추가할 개선 지침
        """
        analysis = self.analyze_feedback(time_range_hours=24)

        if analysis.total_feedback < 10:
            return ""

        prompt_parts = ["## 최근 피드백 기반 개선 사항\n"]

        if analysis.satisfaction_rate < 0.7:
            prompt_parts.append("⚠️ 만족도가 낮습니다. 다음 사항을 개선하세요:\n")

        for suggestion in analysis.improvement_suggestions[:3]:
            prompt_parts.append(f"- {suggestion}")

        return "\n".join(prompt_parts)


# =============================================================================
# 피드백 패턴 학습기
# =============================================================================

class FeedbackPatternLearner:
    """
    피드백 패턴 학습기

    불만족 응답과 만족 응답의 패턴을 학습하여
    응답 개선에 활용합니다.
    """

    def __init__(self, collector: FeedbackCollector):
        self.collector = collector
        self.positive_patterns: List[Dict] = []
        self.negative_patterns: List[Dict] = []

    def learn_patterns(
        self,
        responses_with_feedback: List[Dict[str, Any]]
    ):
        """
        패턴 학습

        Args:
            responses_with_feedback: [
                {
                    "response": "응답 텍스트",
                    "rating": 4,
                    "context": {...}
                }
            ]
        """
        for item in responses_with_feedback:
            response = item.get("response", "")
            rating = item.get("rating", 3)
            context = item.get("context", {})

            pattern = self._extract_pattern(response)
            pattern["context"] = context

            if rating >= 4:
                self.positive_patterns.append(pattern)
            elif rating <= 2:
                self.negative_patterns.append(pattern)

        logger.info(
            f"Patterns learned: {len(self.positive_patterns)} positive, "
            f"{len(self.negative_patterns)} negative"
        )

    def _extract_pattern(self, response: str) -> Dict[str, Any]:
        """응답에서 패턴 추출"""
        return {
            "length": len(response),
            "sentence_count": len(re.split(r'[.!?]', response)),
            "question_count": response.count("?"),
            "empathy_markers": self._count_empathy_markers(response),
            "starts_with_empathy": self._starts_with_empathy(response),
            "has_interjection": bool(re.match(r'^[아어네음에]', response))
        }

    def _count_empathy_markers(self, text: str) -> int:
        """공감 마커 개수"""
        markers = ["군요", "셨군요", "네요", "겠어요", "셨겠", "힘드", "걱정"]
        return sum(1 for m in markers if m in text)

    def _starts_with_empathy(self, text: str) -> bool:
        """공감으로 시작하는지"""
        empathy_starters = ["정말", "많이", "아,", "네,", "그러셨"]
        return any(text.strip().startswith(s) for s in empathy_starters)

    def get_recommendations(self) -> Dict[str, Any]:
        """패턴 기반 권장사항"""
        if not self.positive_patterns or not self.negative_patterns:
            return {"message": "Need more data"}

        # 긍정 패턴 평균
        pos_avg = {
            "length": sum(p["length"] for p in self.positive_patterns) / len(self.positive_patterns),
            "questions": sum(p["question_count"] for p in self.positive_patterns) / len(self.positive_patterns),
            "empathy_markers": sum(p["empathy_markers"] for p in self.positive_patterns) / len(self.positive_patterns)
        }

        # 부정 패턴 평균
        neg_avg = {
            "length": sum(p["length"] for p in self.negative_patterns) / len(self.negative_patterns),
            "questions": sum(p["question_count"] for p in self.negative_patterns) / len(self.negative_patterns),
            "empathy_markers": sum(p["empathy_markers"] for p in self.negative_patterns) / len(self.negative_patterns)
        }

        recommendations = []

        if pos_avg["length"] < neg_avg["length"]:
            recommendations.append("짧은 응답이 선호됩니다.")
        elif pos_avg["length"] > neg_avg["length"] * 1.2:
            recommendations.append("더 상세한 응답이 선호됩니다.")

        if pos_avg["empathy_markers"] > neg_avg["empathy_markers"]:
            recommendations.append("공감 표현을 더 많이 사용하세요.")

        if pos_avg["questions"] > neg_avg["questions"]:
            recommendations.append("탐색 질문을 포함하세요.")

        return {
            "positive_avg": pos_avg,
            "negative_avg": neg_avg,
            "recommendations": recommendations
        }


# =============================================================================
# 테스트
# =============================================================================

def test_feedback_collector():
    """피드백 수집기 테스트"""
    print("=== 피드백 수집 시스템 테스트 ===\n")

    collector = FeedbackCollector()

    # 샘플 피드백 수집
    session_id = "test_session_001"

    # 별점 피드백
    collector.collect_rating(session_id, "msg_001", 4)
    collector.collect_rating(session_id, "msg_002", 2)
    collector.collect_rating(session_id, "msg_003", 5)

    # 반응 피드백
    collector.collect_reaction(session_id, "msg_001", "helpful")
    collector.collect_reaction(session_id, "msg_002", "not_helpful")

    # 텍스트 피드백
    collector.collect_text_feedback(
        session_id, "msg_002",
        "너무 뻔한 말이에요. 공감이 안 느껴져요."
    )
    collector.collect_text_feedback(
        session_id, "msg_003",
        "위로가 됐어요. 고마워요."
    )

    # 세션 요약
    summary = collector.get_session_summary(session_id)
    print(f"세션 요약: {summary}")

    # 전체 분석
    analysis = collector.analyze_feedback(time_range_hours=1)
    print(f"\n총 피드백: {analysis.total_feedback}")
    print(f"만족률: {analysis.satisfaction_rate:.1%}")
    print(f"평균 별점: {analysis.average_rating:.1f}")
    print(f"불만족 원인: {analysis.dissatisfaction_reasons}")
    print(f"\n개선 제안:")
    for s in analysis.improvement_suggestions:
        print(f"  - {s}")

    # 개선 프롬프트
    prompt = collector.get_improvement_prompt()
    print(f"\n개선 프롬프트:\n{prompt}")


if __name__ == "__main__":
    test_feedback_collector()
