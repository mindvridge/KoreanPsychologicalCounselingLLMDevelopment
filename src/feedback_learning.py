"""
피드백 학습 시스템 (Feedback Learning System)

사용자 반응 기반 기법 효과 학습 및 개인화

기능:
1. 암묵적 피드백 수집 (감정 변화, 대화 패턴)
2. 명시적 피드백 수집 (평점, 도움됨 여부)
3. 기법별 효과 학습
4. 개인화된 기법 추천
5. 지속적 모델 개선
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum
import statistics
import json

logger = logging.getLogger(__name__)


# =============================================================================
# 피드백 유형 정의
# =============================================================================

class FeedbackType(Enum):
    """피드백 유형"""
    EXPLICIT_RATING = "explicit_rating"           # 명시적 평점
    EXPLICIT_HELPFUL = "explicit_helpful"         # 도움됨 여부
    IMPLICIT_EMOTION = "implicit_emotion"         # 감정 변화
    IMPLICIT_ENGAGEMENT = "implicit_engagement"   # 참여도
    IMPLICIT_CONTINUATION = "implicit_continuation"  # 대화 지속
    OUTCOME_BASED = "outcome_based"               # 결과 기반


class TechniqueCategory(Enum):
    """기법 카테고리"""
    COGNITIVE = "cognitive"           # 인지적 기법
    BEHAVIORAL = "behavioral"         # 행동적 기법
    EMOTIONAL = "emotional"           # 정서적 기법
    SOMATIC = "somatic"              # 신체적 기법
    RELATIONAL = "relational"        # 관계적 기법
    MINDFULNESS = "mindfulness"      # 마음챙김 기법


@dataclass
class TechniqueUsage:
    """기법 사용 기록"""
    technique_id: str
    technique_name: str
    category: TechniqueCategory
    context: Dict[str, Any]  # 사용 맥락 (감정, 고민, 단계 등)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class FeedbackRecord:
    """피드백 기록"""
    feedback_type: FeedbackType
    technique_id: str
    value: float  # -1 to 1 (부정 ~ 긍정)
    confidence: float  # 0 to 1
    context: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TechniqueEffectiveness:
    """기법 효과성 데이터"""
    technique_id: str
    technique_name: str
    overall_score: float  # 0 to 1
    usage_count: int
    positive_feedback_rate: float
    average_emotion_improvement: float
    effective_contexts: List[str]  # 효과적인 맥락
    ineffective_contexts: List[str]  # 비효과적인 맥락
    confidence: float  # 데이터 충분성 기반


# =============================================================================
# 기법 데이터베이스
# =============================================================================

class TechniqueDatabase:
    """상담 기법 데이터베이스"""

    TECHNIQUES = {
        # 인지적 기법
        "cognitive_restructuring": {
            "name": "인지 재구성",
            "category": TechniqueCategory.COGNITIVE,
            "description": "부정적 생각 패턴을 인식하고 균형 잡힌 생각으로 전환",
            "suitable_for": ["우울", "불안", "자존감"],
            "keywords": ["생각", "해석", "관점", "다르게 보면"]
        },
        "thought_record": {
            "name": "생각 기록",
            "category": TechniqueCategory.COGNITIVE,
            "description": "상황-생각-감정-행동 기록",
            "suitable_for": ["우울", "불안"],
            "keywords": ["기록", "적어보", "상황"]
        },
        "decatastrophizing": {
            "name": "파국화 멈추기",
            "category": TechniqueCategory.COGNITIVE,
            "description": "최악의 시나리오 vs 현실적 시나리오 비교",
            "suitable_for": ["불안", "걱정"],
            "keywords": ["최악", "실제로", "가능성"]
        },

        # 행동적 기법
        "behavioral_activation": {
            "name": "행동 활성화",
            "category": TechniqueCategory.BEHAVIORAL,
            "description": "즐거운 활동과 성취 활동 계획 및 실행",
            "suitable_for": ["우울", "무기력"],
            "keywords": ["활동", "해보", "시작", "작은 것"]
        },
        "exposure": {
            "name": "노출 기법",
            "category": TechniqueCategory.BEHAVIORAL,
            "description": "두려운 상황에 점진적으로 노출",
            "suitable_for": ["불안", "공포", "회피"],
            "keywords": ["조금씩", "시도", "마주"]
        },
        "problem_solving": {
            "name": "문제 해결",
            "category": TechniqueCategory.BEHAVIORAL,
            "description": "체계적인 문제 해결 단계 적용",
            "suitable_for": ["스트레스", "결정"],
            "keywords": ["방법", "해결", "단계"]
        },

        # 정서적 기법
        "emotion_validation": {
            "name": "감정 타당화",
            "category": TechniqueCategory.EMOTIONAL,
            "description": "감정을 있는 그대로 인정하고 수용",
            "suitable_for": ["모든 감정"],
            "keywords": ["당연", "자연스러운", "이해"]
        },
        "emotion_naming": {
            "name": "감정 명명",
            "category": TechniqueCategory.EMOTIONAL,
            "description": "감정에 이름 붙이기",
            "suitable_for": ["모든 감정"],
            "keywords": ["어떤 감정", "느껴지", "이름"]
        },
        "self_compassion": {
            "name": "자기 자비",
            "category": TechniqueCategory.EMOTIONAL,
            "description": "자신에게 친절하고 이해하는 태도",
            "suitable_for": ["자기비난", "수치심", "죄책감"],
            "keywords": ["친구에게", "자신에게", "괜찮아"]
        },

        # 신체적 기법
        "breathing_478": {
            "name": "4-7-8 호흡법",
            "category": TechniqueCategory.SOMATIC,
            "description": "4초 들이쉬기, 7초 멈추기, 8초 내쉬기",
            "suitable_for": ["불안", "공황", "긴장"],
            "keywords": ["호흡", "숨", "4-7-8"]
        },
        "grounding_54321": {
            "name": "5-4-3-2-1 그라운딩",
            "category": TechniqueCategory.SOMATIC,
            "description": "감각을 활용한 현재 순간 집중",
            "suitable_for": ["불안", "해리", "플래시백"],
            "keywords": ["보이는", "들리는", "느껴지는"]
        },
        "pmr": {
            "name": "점진적 근육 이완",
            "category": TechniqueCategory.SOMATIC,
            "description": "근육을 긴장시켰다 이완하기",
            "suitable_for": ["긴장", "불면", "스트레스"],
            "keywords": ["긴장", "이완", "근육"]
        },
        "body_scan": {
            "name": "바디 스캔",
            "category": TechniqueCategory.SOMATIC,
            "description": "몸 전체를 훑으며 감각 인식",
            "suitable_for": ["긴장", "수면", "스트레스"],
            "keywords": ["몸", "느껴", "감각"]
        },

        # 마음챙김 기법
        "mindful_breathing": {
            "name": "마음챙김 호흡",
            "category": TechniqueCategory.MINDFULNESS,
            "description": "호흡에 주의를 기울이며 관찰",
            "suitable_for": ["불안", "스트레스", "반추"],
            "keywords": ["관찰", "지켜보", "흘려보내"]
        },
        "acceptance": {
            "name": "수용",
            "category": TechniqueCategory.MINDFULNESS,
            "description": "통제할 수 없는 것 받아들이기",
            "suitable_for": ["불안", "스트레스"],
            "keywords": ["받아들", "통제", "있는 그대로"]
        },
        "present_moment": {
            "name": "현재 순간 집중",
            "category": TechniqueCategory.MINDFULNESS,
            "description": "지금 여기에 주의 집중",
            "suitable_for": ["불안", "걱정", "반추"],
            "keywords": ["지금", "현재", "이 순간"]
        },

        # 관계적 기법
        "active_listening": {
            "name": "적극적 경청",
            "category": TechniqueCategory.RELATIONAL,
            "description": "공감적으로 듣고 반영",
            "suitable_for": ["모든 상황"],
            "keywords": []  # 기본 기법
        },
        "reflection": {
            "name": "반영",
            "category": TechniqueCategory.RELATIONAL,
            "description": "내담자의 말과 감정 반영",
            "suitable_for": ["모든 상황"],
            "keywords": []
        },
        "summarizing": {
            "name": "요약",
            "category": TechniqueCategory.RELATIONAL,
            "description": "대화 내용 요약",
            "suitable_for": ["모든 상황"],
            "keywords": ["정리하면", "요약"]
        }
    }

    @classmethod
    def get_technique(cls, technique_id: str) -> Optional[Dict]:
        """기법 정보 조회"""
        return cls.TECHNIQUES.get(technique_id)

    @classmethod
    def get_techniques_for_context(
        cls,
        emotion: str = None,
        concern: str = None
    ) -> List[str]:
        """맥락에 적합한 기법 목록"""
        suitable = []
        for tech_id, tech in cls.TECHNIQUES.items():
            if emotion and emotion in tech.get("suitable_for", []):
                suitable.append(tech_id)
            if concern and concern in tech.get("suitable_for", []):
                suitable.append(tech_id)
        return list(set(suitable))


# =============================================================================
# 암묵적 피드백 추출기
# =============================================================================

class ImplicitFeedbackExtractor:
    """
    대화에서 암묵적 피드백 추출

    분석 대상:
    - 감정 변화
    - 응답 길이/깊이
    - 대화 지속 여부
    - 긍정/부정 표현
    """

    # 긍정적 반응 키워드
    POSITIVE_KEYWORDS = [
        "도움이 됐", "좋아졌", "나아진", "편해", "고마워", "감사",
        "해볼게", "시도해볼", "좋은 것 같", "맞아요", "그렇네요",
        "몰랐", "깨달았", "알게 됐", "이해가", "좀 나은"
    ]

    # 부정적 반응 키워드
    NEGATIVE_KEYWORDS = [
        "잘 모르겠", "어려워", "안 될", "못 하겠", "소용없",
        "그런 거 아니", "아닌데", "글쎄", "별로", "그냥"
    ]

    # 중립/회피 키워드
    NEUTRAL_KEYWORDS = [
        "네", "네네", "알겠어요", "그렇군요"
    ]

    def extract_feedback(
        self,
        technique_used: str,
        user_response: str,
        pre_emotion: str,
        post_emotion: str,
        response_length: int,
        conversation_continued: bool
    ) -> FeedbackRecord:
        """
        암묵적 피드백 추출

        Args:
            technique_used: 사용된 기법
            user_response: 사용자 응답
            pre_emotion: 기법 사용 전 감정
            post_emotion: 기법 사용 후 감정
            response_length: 응답 길이
            conversation_continued: 대화 지속 여부

        Returns:
            FeedbackRecord 객체
        """
        scores = []
        confidences = []

        # 1. 언어적 반응 분석
        verbal_score, verbal_conf = self._analyze_verbal_response(user_response)
        scores.append(verbal_score)
        confidences.append(verbal_conf)

        # 2. 감정 변화 분석
        emotion_score, emotion_conf = self._analyze_emotion_change(pre_emotion, post_emotion)
        scores.append(emotion_score)
        confidences.append(emotion_conf)

        # 3. 참여도 분석
        engagement_score, engagement_conf = self._analyze_engagement(
            response_length, conversation_continued
        )
        scores.append(engagement_score)
        confidences.append(engagement_conf)

        # 가중 평균 계산
        total_conf = sum(confidences)
        if total_conf > 0:
            weighted_score = sum(s * c for s, c in zip(scores, confidences)) / total_conf
        else:
            weighted_score = 0.0

        overall_confidence = sum(confidences) / len(confidences)

        return FeedbackRecord(
            feedback_type=FeedbackType.IMPLICIT_EMOTION,
            technique_id=technique_used,
            value=weighted_score,
            confidence=overall_confidence,
            context={
                "pre_emotion": pre_emotion,
                "post_emotion": post_emotion,
                "verbal_score": verbal_score,
                "emotion_score": emotion_score,
                "engagement_score": engagement_score
            }
        )

    def _analyze_verbal_response(self, response: str) -> Tuple[float, float]:
        """언어적 반응 분석"""
        positive_count = sum(1 for kw in self.POSITIVE_KEYWORDS if kw in response)
        negative_count = sum(1 for kw in self.NEGATIVE_KEYWORDS if kw in response)
        neutral_count = sum(1 for kw in self.NEUTRAL_KEYWORDS if kw in response)

        total = positive_count + negative_count + neutral_count

        if total == 0:
            return 0.0, 0.3  # 낮은 신뢰도

        score = (positive_count - negative_count) / total
        confidence = min(0.8, total * 0.2)

        return score, confidence

    def _analyze_emotion_change(
        self,
        pre: str,
        post: str
    ) -> Tuple[float, float]:
        """감정 변화 분석"""
        # 부정 감정
        negative_emotions = ["불안", "우울", "분노", "슬픔", "스트레스", "두려움"]
        # 긍정 감정
        positive_emotions = ["평온", "희망", "안도", "기쁨"]
        # 중립
        neutral_emotions = ["중립", "보통"]

        pre_valence = (
            -1 if pre in negative_emotions else
            1 if pre in positive_emotions else
            0
        )

        post_valence = (
            -1 if post in negative_emotions else
            1 if post in positive_emotions else
            0
        )

        change = post_valence - pre_valence
        score = change / 2  # -1 to 1 범위로 정규화

        confidence = 0.7 if pre != post else 0.5

        return score, confidence

    def _analyze_engagement(
        self,
        length: int,
        continued: bool
    ) -> Tuple[float, float]:
        """참여도 분석"""
        # 응답 길이 점수
        if length < 10:
            length_score = -0.3
        elif length < 30:
            length_score = 0.0
        elif length < 100:
            length_score = 0.3
        else:
            length_score = 0.5

        # 대화 지속 점수
        continuation_score = 0.3 if continued else -0.3

        score = (length_score + continuation_score) / 2
        confidence = 0.5

        return score, confidence


# =============================================================================
# 기법 효과 학습기
# =============================================================================

class TechniqueEffectivenessLearner:
    """기법 효과성 학습"""

    def __init__(self):
        # 사용자별 피드백 이력
        self.user_feedback: Dict[str, List[FeedbackRecord]] = defaultdict(list)

        # 기법별 글로벌 통계
        self.global_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "positive_count": 0,
                "negative_count": 0,
                "total_count": 0,
                "score_sum": 0.0,
                "context_scores": defaultdict(list)  # 맥락별 점수
            }
        )

        # 사용자별 기법 효과
        self.user_technique_scores: Dict[str, Dict[str, float]] = defaultdict(
            lambda: defaultdict(float)
        )

    def record_feedback(
        self,
        user_id: str,
        feedback: FeedbackRecord
    ):
        """피드백 기록 및 학습"""
        # 이력 저장
        self.user_feedback[user_id].append(feedback)

        # 글로벌 통계 업데이트
        tech_id = feedback.technique_id
        stats = self.global_stats[tech_id]

        stats["total_count"] += 1
        stats["score_sum"] += feedback.value

        if feedback.value > 0.2:
            stats["positive_count"] += 1
        elif feedback.value < -0.2:
            stats["negative_count"] += 1

        # 맥락별 점수 기록
        if feedback.context:
            emotion = feedback.context.get("pre_emotion", "unknown")
            stats["context_scores"][emotion].append(feedback.value)

        # 사용자별 점수 업데이트 (지수이동평균)
        alpha = 0.3  # 최근 데이터 가중치
        current = self.user_technique_scores[user_id][tech_id]
        new_score = alpha * feedback.value + (1 - alpha) * current
        self.user_technique_scores[user_id][tech_id] = new_score

    def get_technique_effectiveness(
        self,
        technique_id: str
    ) -> TechniqueEffectiveness:
        """기법 효과성 조회"""
        stats = self.global_stats[technique_id]
        tech_info = TechniqueDatabase.get_technique(technique_id)

        if stats["total_count"] == 0:
            return TechniqueEffectiveness(
                technique_id=technique_id,
                technique_name=tech_info["name"] if tech_info else technique_id,
                overall_score=0.5,  # 기본값
                usage_count=0,
                positive_feedback_rate=0.5,
                average_emotion_improvement=0.0,
                effective_contexts=[],
                ineffective_contexts=[],
                confidence=0.0
            )

        overall_score = (stats["score_sum"] / stats["total_count"] + 1) / 2  # 0-1 범위
        positive_rate = stats["positive_count"] / stats["total_count"]

        # 효과적/비효과적 맥락 분석
        effective = []
        ineffective = []
        for context, scores in stats["context_scores"].items():
            avg = statistics.mean(scores) if scores else 0
            if avg > 0.3:
                effective.append(context)
            elif avg < -0.3:
                ineffective.append(context)

        # 신뢰도 (데이터 충분성)
        confidence = min(1.0, stats["total_count"] / 20)

        return TechniqueEffectiveness(
            technique_id=technique_id,
            technique_name=tech_info["name"] if tech_info else technique_id,
            overall_score=overall_score,
            usage_count=stats["total_count"],
            positive_feedback_rate=positive_rate,
            average_emotion_improvement=stats["score_sum"] / stats["total_count"],
            effective_contexts=effective,
            ineffective_contexts=ineffective,
            confidence=confidence
        )

    def get_user_preferences(
        self,
        user_id: str
    ) -> Dict[str, float]:
        """사용자별 기법 선호도"""
        return dict(self.user_technique_scores[user_id])


# =============================================================================
# 개인화 추천 시스템
# =============================================================================

class PersonalizedRecommender:
    """개인화된 기법 추천"""

    def __init__(self, learner: TechniqueEffectivenessLearner):
        self.learner = learner

    def recommend_techniques(
        self,
        user_id: str,
        current_emotion: str,
        current_concern: Optional[str] = None,
        exclude: Optional[List[str]] = None,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        개인화된 기법 추천

        Args:
            user_id: 사용자 ID
            current_emotion: 현재 감정
            current_concern: 현재 고민
            exclude: 제외할 기법 ID
            top_k: 추천 개수

        Returns:
            추천 기법 리스트
        """
        exclude = exclude or []

        # 1. 맥락 기반 후보 선정
        candidates = TechniqueDatabase.get_techniques_for_context(
            emotion=current_emotion,
            concern=current_concern
        )

        if not candidates:
            # 기본 기법 추가
            candidates = ["breathing_478", "emotion_validation", "grounding_54321"]

        # 2. 점수 계산
        scored_techniques = []

        # 사용자 선호도
        user_prefs = self.learner.get_user_preferences(user_id)

        for tech_id in candidates:
            if tech_id in exclude:
                continue

            # 글로벌 효과성
            effectiveness = self.learner.get_technique_effectiveness(tech_id)

            # 사용자 개인 점수
            user_score = user_prefs.get(tech_id, 0.0)

            # 맥락 적합성
            context_bonus = 0.0
            if current_emotion in effectiveness.effective_contexts:
                context_bonus = 0.2
            elif current_emotion in effectiveness.ineffective_contexts:
                context_bonus = -0.2

            # 종합 점수 (가중 평균)
            combined_score = (
                effectiveness.overall_score * 0.4 +
                (user_score + 1) / 2 * 0.4 +  # -1~1을 0~1로 변환
                context_bonus + 0.5 * 0.2
            )

            # 신뢰도 반영
            if effectiveness.confidence < 0.3:
                combined_score = combined_score * 0.8 + 0.5 * 0.2  # 기본값 쪽으로 보정

            scored_techniques.append({
                "technique_id": tech_id,
                "technique_name": effectiveness.technique_name,
                "score": combined_score,
                "confidence": effectiveness.confidence,
                "reason": self._generate_reason(effectiveness, user_score, current_emotion)
            })

        # 3. 정렬 및 반환
        scored_techniques.sort(key=lambda x: x["score"], reverse=True)

        return scored_techniques[:top_k]

    def _generate_reason(
        self,
        effectiveness: TechniqueEffectiveness,
        user_score: float,
        emotion: str
    ) -> str:
        """추천 이유 생성"""
        reasons = []

        if effectiveness.positive_feedback_rate > 0.6:
            reasons.append("많은 사용자에게 효과적")

        if user_score > 0.3:
            reasons.append("이전에 도움이 되었음")

        if emotion in effectiveness.effective_contexts:
            reasons.append(f"'{emotion}' 감정에 적합")

        if effectiveness.usage_count < 3:
            reasons.append("새로운 기법 시도")

        return ", ".join(reasons) if reasons else "일반적 권장"


# =============================================================================
# 명시적 피드백 수집기
# =============================================================================

class ExplicitFeedbackCollector:
    """명시적 피드백 수집"""

    FEEDBACK_PROMPTS = {
        "session_end": "오늘 대화가 도움이 되셨나요?",
        "technique_specific": "방금 알려드린 방법이 도움이 되셨나요?",
        "rating": "오늘 상담에 대해 1-5점으로 평가해 주세요.",
        "helpful": "오늘 대화에서 가장 도움이 된 부분은 무엇인가요?",
        "improvement": "더 나은 도움을 드리려면 어떤 점을 개선하면 좋을까요?"
    }

    RATING_OPTIONS = {
        1: "전혀 도움 안 됨",
        2: "별로 도움 안 됨",
        3: "보통",
        4: "도움이 됨",
        5: "매우 도움이 됨"
    }

    def collect_session_rating(
        self,
        rating: int,
        helpful_aspect: Optional[str] = None,
        improvement_suggestion: Optional[str] = None
    ) -> Dict[str, Any]:
        """세션 평가 수집"""
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")

        normalized_score = (rating - 3) / 2  # -1 to 1

        return {
            "feedback_type": FeedbackType.EXPLICIT_RATING.value,
            "rating": rating,
            "normalized_score": normalized_score,
            "helpful_aspect": helpful_aspect,
            "improvement_suggestion": improvement_suggestion,
            "timestamp": datetime.now().isoformat()
        }

    def collect_technique_feedback(
        self,
        technique_id: str,
        helpful: bool,
        comment: Optional[str] = None
    ) -> FeedbackRecord:
        """기법별 피드백 수집"""
        return FeedbackRecord(
            feedback_type=FeedbackType.EXPLICIT_HELPFUL,
            technique_id=technique_id,
            value=1.0 if helpful else -0.5,
            confidence=0.9,  # 명시적 피드백은 높은 신뢰도
            context={"comment": comment}
        )


# =============================================================================
# 통합 피드백 학습 시스템
# =============================================================================

class FeedbackLearningSystem:
    """통합 피드백 학습 시스템"""

    def __init__(self):
        self.implicit_extractor = ImplicitFeedbackExtractor()
        self.learner = TechniqueEffectivenessLearner()
        self.recommender = PersonalizedRecommender(self.learner)
        self.explicit_collector = ExplicitFeedbackCollector()

        # 세션별 기법 사용 기록
        self.session_techniques: Dict[str, List[TechniqueUsage]] = defaultdict(list)

    def record_technique_usage(
        self,
        session_id: str,
        technique_id: str,
        context: Dict[str, Any]
    ):
        """기법 사용 기록"""
        tech_info = TechniqueDatabase.get_technique(technique_id)

        usage = TechniqueUsage(
            technique_id=technique_id,
            technique_name=tech_info["name"] if tech_info else technique_id,
            category=tech_info["category"] if tech_info else TechniqueCategory.RELATIONAL,
            context=context
        )

        self.session_techniques[session_id].append(usage)

    def process_implicit_feedback(
        self,
        user_id: str,
        session_id: str,
        technique_id: str,
        user_response: str,
        pre_emotion: str,
        post_emotion: str,
        response_length: int,
        conversation_continued: bool
    ):
        """암묵적 피드백 처리"""
        feedback = self.implicit_extractor.extract_feedback(
            technique_used=technique_id,
            user_response=user_response,
            pre_emotion=pre_emotion,
            post_emotion=post_emotion,
            response_length=response_length,
            conversation_continued=conversation_continued
        )

        self.learner.record_feedback(user_id, feedback)

        logger.info(
            f"Implicit feedback recorded: user={user_id}, "
            f"technique={technique_id}, score={feedback.value:.2f}"
        )

    def process_explicit_feedback(
        self,
        user_id: str,
        technique_id: str,
        helpful: bool,
        comment: Optional[str] = None
    ):
        """명시적 피드백 처리"""
        feedback = self.explicit_collector.collect_technique_feedback(
            technique_id=technique_id,
            helpful=helpful,
            comment=comment
        )

        self.learner.record_feedback(user_id, feedback)

        logger.info(
            f"Explicit feedback recorded: user={user_id}, "
            f"technique={technique_id}, helpful={helpful}"
        )

    def get_recommendations(
        self,
        user_id: str,
        current_emotion: str,
        current_concern: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """개인화된 기법 추천"""
        # 현재 세션에서 이미 사용한 기법 제외
        exclude = []
        if session_id and session_id in self.session_techniques:
            exclude = [u.technique_id for u in self.session_techniques[session_id]]

        return self.recommender.recommend_techniques(
            user_id=user_id,
            current_emotion=current_emotion,
            current_concern=current_concern,
            exclude=exclude
        )

    def get_technique_stats(self, technique_id: str) -> Dict[str, Any]:
        """기법 통계 조회"""
        effectiveness = self.learner.get_technique_effectiveness(technique_id)
        return {
            "technique_id": effectiveness.technique_id,
            "technique_name": effectiveness.technique_name,
            "overall_score": round(effectiveness.overall_score, 2),
            "usage_count": effectiveness.usage_count,
            "positive_rate": round(effectiveness.positive_feedback_rate, 2),
            "effective_contexts": effectiveness.effective_contexts,
            "confidence": round(effectiveness.confidence, 2)
        }

    def get_user_learning_summary(self, user_id: str) -> Dict[str, Any]:
        """사용자 학습 요약"""
        preferences = self.learner.get_user_preferences(user_id)
        feedback_count = len(self.learner.user_feedback[user_id])

        # 가장 효과적인 기법
        if preferences:
            best_techniques = sorted(
                preferences.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
        else:
            best_techniques = []

        return {
            "user_id": user_id,
            "total_feedback_count": feedback_count,
            "learned_preferences": len(preferences),
            "top_effective_techniques": [
                {
                    "technique_id": t[0],
                    "score": round((t[1] + 1) / 2, 2)  # 0-1 범위로 변환
                }
                for t in best_techniques
            ],
            "personalization_level": "high" if feedback_count > 20 else (
                "medium" if feedback_count > 5 else "low"
            )
        }


# =============================================================================
# 팩토리 함수
# =============================================================================

_feedback_system: Optional[FeedbackLearningSystem] = None

def get_feedback_system() -> FeedbackLearningSystem:
    """피드백 학습 시스템 싱글톤"""
    global _feedback_system
    if _feedback_system is None:
        _feedback_system = FeedbackLearningSystem()
    return _feedback_system


# =============================================================================
# 테스트
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("피드백 학습 시스템 테스트")
    print("=" * 60)

    system = get_feedback_system()
    user_id = "test_user_001"
    session_id = "session_001"

    # 기법 사용 기록
    print("\n[기법 사용 기록]")
    system.record_technique_usage(
        session_id=session_id,
        technique_id="breathing_478",
        context={"emotion": "불안", "turn": 5}
    )

    # 암묵적 피드백 처리
    print("\n[암묵적 피드백 처리]")
    system.process_implicit_feedback(
        user_id=user_id,
        session_id=session_id,
        technique_id="breathing_478",
        user_response="해봤는데 좀 나아진 것 같아요. 고마워요.",
        pre_emotion="불안",
        post_emotion="안도",
        response_length=30,
        conversation_continued=True
    )

    # 명시적 피드백 처리
    print("\n[명시적 피드백 처리]")
    system.process_explicit_feedback(
        user_id=user_id,
        technique_id="breathing_478",
        helpful=True,
        comment="호흡법이 도움이 됐어요"
    )

    # 기법 추천
    print("\n[기법 추천]")
    recommendations = system.get_recommendations(
        user_id=user_id,
        current_emotion="불안",
        session_id=session_id
    )
    for rec in recommendations:
        print(f"  - {rec['technique_name']}: {rec['score']:.2f} ({rec['reason']})")

    # 기법 통계
    print("\n[기법 통계]")
    stats = system.get_technique_stats("breathing_478")
    print(f"  호흡법 효과: {stats['overall_score']}")
    print(f"  사용 횟수: {stats['usage_count']}")
    print(f"  긍정 반응률: {stats['positive_rate']}")

    # 사용자 학습 요약
    print("\n[사용자 학습 요약]")
    summary = system.get_user_learning_summary(user_id)
    print(f"  피드백 수: {summary['total_feedback_count']}")
    print(f"  개인화 수준: {summary['personalization_level']}")
    print(f"  효과적 기법: {summary['top_effective_techniques']}")
