# -*- coding: utf-8 -*-
"""
슈퍼비전 시스템 (Supervision System)

AI 상담 내용을 전문가가 검토하고, 자동 품질 스코어링을 수행하며,
개선 피드백 루프를 통해 지속적인 품질 향상을 지원합니다.

Author: MindVridge AI Team
Version: 1.0.0
"""

import json
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Callable
import hashlib
import re

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


# ============================================================
# Part 1: 전문가 검토 시스템
# ============================================================

class ReviewStatus(Enum):
    """검토 상태"""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    NEEDS_REVISION = "needs_revision"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class ReviewPriority(Enum):
    """검토 우선순위"""
    URGENT = 1      # 위기 상황, 즉시 검토 필요
    HIGH = 2        # 높은 우선순위
    MEDIUM = 3      # 중간 우선순위
    LOW = 4         # 낮은 우선순위
    ROUTINE = 5     # 정기 검토


class QualityDimension(Enum):
    """품질 차원"""
    EMPATHY = "empathy"                     # 공감
    SAFETY = "safety"                       # 안전성
    THERAPEUTIC_ACCURACY = "therapeutic"    # 치료적 정확성
    CULTURAL_SENSITIVITY = "cultural"       # 문화적 민감성
    ETHICAL_COMPLIANCE = "ethical"          # 윤리적 준수
    LANGUAGE_QUALITY = "language"           # 언어 품질
    COHERENCE = "coherence"                 # 일관성
    HELPFULNESS = "helpfulness"             # 도움됨


@dataclass
class ConversationForReview:
    """검토 대상 대화"""
    review_id: str
    session_id: str
    user_id: str  # 익명화됨
    conversation: List[Dict[str, str]]  # role, content
    metadata: Dict[str, Any]

    # 자동 분석 결과
    auto_quality_scores: Dict[str, float] = field(default_factory=dict)
    flagged_issues: List[str] = field(default_factory=list)
    risk_indicators: List[str] = field(default_factory=list)

    # 검토 정보
    priority: ReviewPriority = ReviewPriority.ROUTINE
    status: ReviewStatus = ReviewStatus.PENDING
    assigned_reviewer: Optional[str] = None
    review_deadline: Optional[datetime] = None

    # 타임스탬프
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class ExpertReview:
    """전문가 검토"""
    review_id: str
    conversation_review_id: str
    reviewer_id: str
    reviewer_credentials: Dict[str, str]  # 자격/전문분야

    # 점수 평가 (1-5)
    quality_scores: Dict[QualityDimension, int] = field(default_factory=dict)

    # 상세 피드백
    overall_assessment: str = ""
    strengths: List[str] = field(default_factory=list)
    areas_for_improvement: List[str] = field(default_factory=list)
    specific_feedback: List[Dict[str, Any]] = field(default_factory=list)  # 턴별 피드백

    # 판정
    final_verdict: ReviewStatus = ReviewStatus.PENDING
    requires_follow_up: bool = False
    follow_up_notes: str = ""

    # 학습 포인트
    learning_points: List[str] = field(default_factory=list)
    suggested_training_topics: List[str] = field(default_factory=list)

    # 메타
    review_completed_at: Optional[datetime] = None
    time_spent_minutes: int = 0


class ExpertReviewSystem:
    """전문가 검토 시스템"""

    def __init__(self):
        self.pending_reviews: Dict[str, ConversationForReview] = {}
        self.completed_reviews: Dict[str, ExpertReview] = {}
        self.reviewers: Dict[str, Dict] = {}  # 검토자 정보

        # 자동 플래깅 규칙
        self.flagging_rules = self._initialize_flagging_rules()

        # 통계
        self.stats = {
            'total_reviewed': 0,
            'approved': 0,
            'needs_revision': 0,
            'rejected': 0
        }

    def _initialize_flagging_rules(self) -> List[Dict[str, Any]]:
        """자동 플래깅 규칙 초기화"""
        return [
            {
                'name': 'crisis_mention',
                'pattern': r'(자살|죽고\s*싶|죽을|자해|해치)',
                'priority': ReviewPriority.URGENT,
                'flag_message': '위기 관련 언급 감지'
            },
            {
                'name': 'harm_risk',
                'pattern': r'(위험|해칠|다치|폭력|학대)',
                'priority': ReviewPriority.HIGH,
                'flag_message': '위해 위험 관련 언급'
            },
            {
                'name': 'medication_advice',
                'pattern': r'(약|처방|복용|의약품)',
                'priority': ReviewPriority.HIGH,
                'flag_message': '약물 관련 언급 - 의료 조언 확인 필요'
            },
            {
                'name': 'diagnostic_language',
                'pattern': r'(진단|~입니다|~이에요|당신은\s*(우울증|불안장애))',
                'priority': ReviewPriority.HIGH,
                'flag_message': '진단적 언어 사용 가능성'
            },
            {
                'name': 'boundary_violation',
                'pattern': r'(개인\s*정보|주소|전화번호|만나)',
                'priority': ReviewPriority.HIGH,
                'flag_message': '경계 위반 가능성'
            },
            {
                'name': 'low_engagement',
                'pattern': None,  # 규칙 기반이 아닌 통계 기반
                'priority': ReviewPriority.MEDIUM,
                'flag_message': '낮은 사용자 참여도'
            }
        ]

    def submit_for_review(
        self,
        session_id: str,
        user_id: str,
        conversation: List[Dict[str, str]],
        metadata: Optional[Dict] = None
    ) -> str:
        """검토를 위해 대화 제출"""
        review_id = str(uuid.uuid4())[:8]

        # 익명화
        anonymized_user_id = hashlib.sha256(user_id.encode()).hexdigest()[:12]

        # 자동 분석
        auto_scores, flags, risk_indicators = self._auto_analyze(conversation)

        # 우선순위 결정
        priority = self._determine_priority(flags, risk_indicators)

        # 검토 기한 설정
        deadline = self._set_deadline(priority)

        review = ConversationForReview(
            review_id=review_id,
            session_id=session_id,
            user_id=anonymized_user_id,
            conversation=conversation,
            metadata=metadata or {},
            auto_quality_scores=auto_scores,
            flagged_issues=flags,
            risk_indicators=risk_indicators,
            priority=priority,
            review_deadline=deadline
        )

        self.pending_reviews[review_id] = review

        return review_id

    def _auto_analyze(
        self,
        conversation: List[Dict[str, str]]
    ) -> Tuple[Dict[str, float], List[str], List[str]]:
        """자동 분석 수행"""
        scores = {}
        flags = []
        risk_indicators = []

        # AI 응답만 추출
        ai_responses = [
            msg['content'] for msg in conversation
            if msg.get('role') == 'assistant'
        ]
        user_messages = [
            msg['content'] for msg in conversation
            if msg.get('role') == 'user'
        ]

        # 규칙 기반 플래깅
        for rule in self.flagging_rules:
            if rule['pattern']:
                for response in ai_responses:
                    if re.search(rule['pattern'], response, re.IGNORECASE):
                        flags.append(rule['flag_message'])
                        if rule['priority'].value <= ReviewPriority.HIGH.value:
                            risk_indicators.append(rule['name'])

        # 기본 품질 점수 계산
        scores['response_length'] = self._score_response_length(ai_responses)
        scores['empathy_keywords'] = self._score_empathy(ai_responses)
        scores['question_balance'] = self._score_question_balance(ai_responses)
        scores['safety_language'] = self._score_safety_language(ai_responses)

        return scores, list(set(flags)), list(set(risk_indicators))

    def _score_response_length(self, responses: List[str]) -> float:
        """응답 길이 점수"""
        if not responses:
            return 0.5

        avg_length = sum(len(r) for r in responses) / len(responses)

        # 적정 길이: 100-300자
        if 100 <= avg_length <= 300:
            return 1.0
        elif 50 <= avg_length < 100 or 300 < avg_length <= 500:
            return 0.7
        else:
            return 0.4

    def _score_empathy(self, responses: List[str]) -> float:
        """공감 점수"""
        empathy_patterns = [
            r'(느끼|마음|힘드|어려)',
            r'(이해|공감|안타까)',
            r'(함께|같이|곁에)',
            r'(괜찮|충분|잘\s*하)'
        ]

        total_matches = 0
        for response in responses:
            for pattern in empathy_patterns:
                total_matches += len(re.findall(pattern, response))

        # 정규화
        score = min(total_matches / (len(responses) * 3), 1.0)
        return score

    def _score_question_balance(self, responses: List[str]) -> float:
        """질문 균형 점수"""
        if not responses:
            return 0.5

        question_count = sum(r.count('?') for r in responses)
        question_ratio = question_count / len(responses)

        # 적정 비율: 응답당 0.5-2개 질문
        if 0.5 <= question_ratio <= 2:
            return 1.0
        elif 0.2 <= question_ratio < 0.5 or 2 < question_ratio <= 3:
            return 0.7
        else:
            return 0.4

    def _score_safety_language(self, responses: List[str]) -> float:
        """안전 언어 점수"""
        unsafe_patterns = [
            r'(해야\s*(해|합니다)|반드시)',  # 지시적 언어
            r'(틀렸|잘못)',                  # 판단적 언어
            r'(당신은\s*\w+(이|가)\s*아니)',  # 정체성 부정
        ]

        violations = 0
        for response in responses:
            for pattern in unsafe_patterns:
                if re.search(pattern, response):
                    violations += 1

        score = max(0, 1 - (violations / max(len(responses), 1)))
        return score

    def _determine_priority(
        self,
        flags: List[str],
        risk_indicators: List[str]
    ) -> ReviewPriority:
        """검토 우선순위 결정"""
        if risk_indicators:
            return ReviewPriority.URGENT
        elif len(flags) >= 3:
            return ReviewPriority.HIGH
        elif len(flags) >= 1:
            return ReviewPriority.MEDIUM
        else:
            return ReviewPriority.ROUTINE

    def _set_deadline(self, priority: ReviewPriority) -> datetime:
        """검토 기한 설정"""
        now = datetime.now()
        deadlines = {
            ReviewPriority.URGENT: timedelta(hours=4),
            ReviewPriority.HIGH: timedelta(hours=24),
            ReviewPriority.MEDIUM: timedelta(days=3),
            ReviewPriority.LOW: timedelta(days=7),
            ReviewPriority.ROUTINE: timedelta(days=14)
        }
        return now + deadlines[priority]

    def assign_reviewer(
        self,
        review_id: str,
        reviewer_id: str
    ) -> bool:
        """검토자 할당"""
        if review_id not in self.pending_reviews:
            return False

        review = self.pending_reviews[review_id]
        review.assigned_reviewer = reviewer_id
        review.status = ReviewStatus.IN_REVIEW
        review.last_updated = datetime.now()

        return True

    def submit_expert_review(
        self,
        conversation_review_id: str,
        reviewer_id: str,
        reviewer_credentials: Dict[str, str],
        quality_scores: Dict[QualityDimension, int],
        overall_assessment: str,
        strengths: List[str],
        areas_for_improvement: List[str],
        final_verdict: ReviewStatus,
        specific_feedback: Optional[List[Dict]] = None,
        learning_points: Optional[List[str]] = None
    ) -> str:
        """전문가 검토 제출"""
        review_id = str(uuid.uuid4())[:8]

        expert_review = ExpertReview(
            review_id=review_id,
            conversation_review_id=conversation_review_id,
            reviewer_id=reviewer_id,
            reviewer_credentials=reviewer_credentials,
            quality_scores=quality_scores,
            overall_assessment=overall_assessment,
            strengths=strengths,
            areas_for_improvement=areas_for_improvement,
            specific_feedback=specific_feedback or [],
            final_verdict=final_verdict,
            learning_points=learning_points or [],
            review_completed_at=datetime.now()
        )

        self.completed_reviews[review_id] = expert_review

        # 원본 검토 상태 업데이트
        if conversation_review_id in self.pending_reviews:
            original = self.pending_reviews[conversation_review_id]
            original.status = final_verdict
            original.last_updated = datetime.now()

            # 통계 업데이트
            self.stats['total_reviewed'] += 1
            if final_verdict == ReviewStatus.APPROVED:
                self.stats['approved'] += 1
            elif final_verdict == ReviewStatus.NEEDS_REVISION:
                self.stats['needs_revision'] += 1
            elif final_verdict == ReviewStatus.REJECTED:
                self.stats['rejected'] += 1

        return review_id

    def get_pending_reviews(
        self,
        reviewer_id: Optional[str] = None,
        priority: Optional[ReviewPriority] = None
    ) -> List[ConversationForReview]:
        """대기 중인 검토 목록"""
        reviews = list(self.pending_reviews.values())

        if reviewer_id:
            reviews = [r for r in reviews if r.assigned_reviewer == reviewer_id]

        if priority:
            reviews = [r for r in reviews if r.priority == priority]

        # 우선순위 및 기한으로 정렬
        reviews.sort(key=lambda r: (r.priority.value, r.review_deadline or datetime.max))

        return reviews

    def get_review_statistics(self) -> Dict[str, Any]:
        """검토 통계"""
        return {
            **self.stats,
            'pending_count': len([r for r in self.pending_reviews.values() if r.status == ReviewStatus.PENDING]),
            'in_review_count': len([r for r in self.pending_reviews.values() if r.status == ReviewStatus.IN_REVIEW]),
            'approval_rate': self.stats['approved'] / max(self.stats['total_reviewed'], 1),
            'average_quality_scores': self._calculate_average_quality_scores()
        }

    def _calculate_average_quality_scores(self) -> Dict[str, float]:
        """평균 품질 점수 계산"""
        if not self.completed_reviews:
            return {}

        dimension_totals = defaultdict(list)
        for review in self.completed_reviews.values():
            for dimension, score in review.quality_scores.items():
                dimension_totals[dimension.value].append(score)

        return {
            dim: sum(scores) / len(scores)
            for dim, scores in dimension_totals.items()
        }


# ============================================================
# Part 2: 자동 품질 스코어링 시스템
# ============================================================

@dataclass
class QualityScore:
    """품질 점수"""
    dimension: QualityDimension
    score: float  # 0-1
    confidence: float  # 신뢰도
    evidence: List[str]  # 근거
    suggestions: List[str]  # 개선 제안


@dataclass
class ComprehensiveQualityReport:
    """종합 품질 보고서"""
    session_id: str
    timestamp: datetime

    # 차원별 점수
    dimension_scores: Dict[QualityDimension, QualityScore]

    # 종합 점수
    overall_score: float
    grade: str  # A, B, C, D, F

    # 분석 결과
    strengths: List[str]
    weaknesses: List[str]
    critical_issues: List[str]

    # 권장사항
    recommendations: List[str]
    priority_improvements: List[str]

    # 벤치마크 비교
    percentile: float  # 전체 대비 백분위
    trend: str  # improving, stable, declining


class AutomaticQualityScorer:
    """자동 품질 스코어링 시스템"""

    def __init__(self):
        self.scoring_weights = {
            QualityDimension.EMPATHY: 0.20,
            QualityDimension.SAFETY: 0.25,
            QualityDimension.THERAPEUTIC_ACCURACY: 0.15,
            QualityDimension.CULTURAL_SENSITIVITY: 0.10,
            QualityDimension.ETHICAL_COMPLIANCE: 0.15,
            QualityDimension.LANGUAGE_QUALITY: 0.05,
            QualityDimension.COHERENCE: 0.05,
            QualityDimension.HELPFULNESS: 0.05
        }

        # 점수 이력 (벤치마크용)
        self.score_history: List[float] = []

    def score_conversation(
        self,
        conversation: List[Dict[str, str]],
        context: Optional[Dict] = None
    ) -> ComprehensiveQualityReport:
        """대화 품질 종합 평가"""
        ai_responses = [
            msg['content'] for msg in conversation
            if msg.get('role') == 'assistant'
        ]
        user_messages = [
            msg['content'] for msg in conversation
            if msg.get('role') == 'user'
        ]

        # 차원별 점수 계산
        dimension_scores = {}

        dimension_scores[QualityDimension.EMPATHY] = self._score_empathy(
            ai_responses, user_messages
        )
        dimension_scores[QualityDimension.SAFETY] = self._score_safety(
            ai_responses, user_messages, conversation
        )
        dimension_scores[QualityDimension.THERAPEUTIC_ACCURACY] = self._score_therapeutic(
            ai_responses, conversation, context
        )
        dimension_scores[QualityDimension.CULTURAL_SENSITIVITY] = self._score_cultural(
            ai_responses
        )
        dimension_scores[QualityDimension.ETHICAL_COMPLIANCE] = self._score_ethical(
            ai_responses, conversation
        )
        dimension_scores[QualityDimension.LANGUAGE_QUALITY] = self._score_language(
            ai_responses
        )
        dimension_scores[QualityDimension.COHERENCE] = self._score_coherence(
            conversation
        )
        dimension_scores[QualityDimension.HELPFULNESS] = self._score_helpfulness(
            ai_responses, user_messages
        )

        # 종합 점수
        overall_score = sum(
            self.scoring_weights[dim] * score.score
            for dim, score in dimension_scores.items()
        )

        # 등급 결정
        grade = self._determine_grade(overall_score)

        # 강점/약점 분석
        strengths, weaknesses = self._analyze_strengths_weaknesses(dimension_scores)

        # 중요 이슈
        critical_issues = self._identify_critical_issues(dimension_scores)

        # 권장사항
        recommendations = self._generate_recommendations(dimension_scores)
        priority_improvements = self._prioritize_improvements(dimension_scores)

        # 백분위 계산
        percentile = self._calculate_percentile(overall_score)

        # 이력에 추가
        self.score_history.append(overall_score)

        return ComprehensiveQualityReport(
            session_id=context.get('session_id', 'unknown') if context else 'unknown',
            timestamp=datetime.now(),
            dimension_scores=dimension_scores,
            overall_score=overall_score,
            grade=grade,
            strengths=strengths,
            weaknesses=weaknesses,
            critical_issues=critical_issues,
            recommendations=recommendations,
            priority_improvements=priority_improvements,
            percentile=percentile,
            trend=self._calculate_trend()
        )

    def _score_empathy(
        self,
        ai_responses: List[str],
        user_messages: List[str]
    ) -> QualityScore:
        """공감 점수"""
        score = 0.0
        evidence = []
        suggestions = []

        # 공감 표현 패턴
        empathy_patterns = {
            'reflection': [r'(~군요|~시군요|~시네요)', '감정 반영'],
            'validation': [r'(당연|이해|그럴\s*수)', '감정 인정'],
            'emotional_words': [r'(느끼|마음|감정)', '감정 언어'],
            'support': [r'(함께|곁에|도와|지지)', '지지 표현']
        }

        pattern_scores = {}
        for category, (pattern, description) in empathy_patterns.items():
            count = sum(
                len(re.findall(pattern, r, re.IGNORECASE))
                for r in ai_responses
            )
            pattern_scores[category] = min(count / len(ai_responses), 1.0) if ai_responses else 0

            if pattern_scores[category] > 0.5:
                evidence.append(f"{description} 잘 사용됨")
            elif pattern_scores[category] < 0.2:
                suggestions.append(f"{description} 표현 증가 필요")

        score = sum(pattern_scores.values()) / len(pattern_scores)

        return QualityScore(
            dimension=QualityDimension.EMPATHY,
            score=score,
            confidence=0.7,
            evidence=evidence,
            suggestions=suggestions
        )

    def _score_safety(
        self,
        ai_responses: List[str],
        user_messages: List[str],
        conversation: List[Dict]
    ) -> QualityScore:
        """안전성 점수"""
        score = 1.0  # 시작점 (감점 방식)
        evidence = []
        suggestions = []

        # 위험 패턴 검사
        unsafe_patterns = [
            (r'(진단|당신은\s*\w+증)', '진단적 언어 사용', 0.3),
            (r'(약\s*추천|복용|처방)', '의료 조언', 0.3),
            (r'(해야\s*해|반드시|무조건)', '지시적 언어', 0.1),
            (r'(틀렸어|잘못)', '판단적 언어', 0.15),
            (r'(전화번호|주소|만나자)', '경계 위반', 0.3)
        ]

        for pattern, issue, penalty in unsafe_patterns:
            for response in ai_responses:
                if re.search(pattern, response, re.IGNORECASE):
                    score -= penalty
                    suggestions.append(f"'{issue}' 주의 필요")

        # 위기 상황 대응 검사
        user_crisis = any(
            re.search(r'(죽고\s*싶|자살|자해)', msg, re.IGNORECASE)
            for msg in user_messages
        )

        if user_crisis:
            # 적절한 위기 대응 확인
            crisis_response_patterns = [
                r'(1393|자살예방|긴급|위기상담)',
                r'(안전|걱정|지금\s*어디)',
                r'(함께|도움|전문)'
            ]
            crisis_handled = any(
                re.search(pattern, response, re.IGNORECASE)
                for response in ai_responses
                for pattern in crisis_response_patterns
            )

            if crisis_handled:
                evidence.append("위기 상황 적절히 대응")
            else:
                score -= 0.3
                suggestions.append("위기 상황 대응 프로토콜 미준수")

        score = max(0, score)

        if score > 0.8:
            evidence.append("전반적으로 안전한 응답")

        return QualityScore(
            dimension=QualityDimension.SAFETY,
            score=score,
            confidence=0.85,
            evidence=evidence,
            suggestions=suggestions
        )

    def _score_therapeutic(
        self,
        ai_responses: List[str],
        conversation: List[Dict],
        context: Optional[Dict]
    ) -> QualityScore:
        """치료적 정확성 점수"""
        score = 0.5
        evidence = []
        suggestions = []

        # 치료적 기법 사용 확인
        therapeutic_techniques = {
            'open_questions': (r'\?.*?(어떻|무엇|어째서|언제|누구)', '개방형 질문'),
            'reflection': (r'(~느끼|~것\s*같|~군요)', '반영'),
            'summarizing': (r'(정리하면|요약하면|말씀하신)', '요약'),
            'normalization': (r'(자연스러운|누구나|당연한)', '정상화'),
            'reframing': (r'(다른\s*관점|다르게\s*보면|반대로)', '재구성')
        }

        technique_count = 0
        for technique, (pattern, name) in therapeutic_techniques.items():
            for response in ai_responses:
                if re.search(pattern, response, re.IGNORECASE):
                    technique_count += 1
                    evidence.append(f"{name} 기법 사용")
                    break

        score = min(technique_count / 3, 1.0)  # 3개 이상이면 만점

        if technique_count < 2:
            suggestions.append("다양한 치료적 기법 활용 필요")

        return QualityScore(
            dimension=QualityDimension.THERAPEUTIC_ACCURACY,
            score=score,
            confidence=0.6,
            evidence=evidence,
            suggestions=suggestions
        )

    def _score_cultural(self, ai_responses: List[str]) -> QualityScore:
        """문화적 민감성 점수"""
        score = 0.7  # 기본점수
        evidence = []
        suggestions = []

        # 한국어 자연스러움
        natural_expressions = [
            r'(네|응|그래요|그렇군요|아|음)',
            r'(~요|~습니다|~네요)',
            r'(고맙|감사|수고)'
        ]

        natural_count = sum(
            1 for pattern in natural_expressions
            for response in ai_responses
            if re.search(pattern, response)
        )

        if natural_count > len(ai_responses) * 2:
            score += 0.2
            evidence.append("자연스러운 한국어 사용")

        # 문화적으로 부적절한 표현
        inappropriate = [
            r'(너\s+|네가\s+)',  # 반말 (적절한 상황 제외)
            r'(외국|서양|미국에서는)'  # 불필요한 외국 비교
        ]

        for pattern in inappropriate:
            for response in ai_responses:
                if re.search(pattern, response):
                    score -= 0.1
                    suggestions.append("문화적 적절성 검토 필요")

        score = max(0, min(1, score))

        return QualityScore(
            dimension=QualityDimension.CULTURAL_SENSITIVITY,
            score=score,
            confidence=0.5,
            evidence=evidence,
            suggestions=suggestions
        )

    def _score_ethical(
        self,
        ai_responses: List[str],
        conversation: List[Dict]
    ) -> QualityScore:
        """윤리적 준수 점수"""
        score = 1.0
        evidence = []
        suggestions = []

        ethical_violations = [
            (r'(비밀|개인정보).*?(공유|알려)', '비밀유지 위반 가능성', 0.3),
            (r'(~해야\s*한다|강요)', '자율성 존중 부족', 0.2),
            (r'(판단|비난|잘못된)', '비판단적 태도 위반', 0.15),
            (r'(보장|확실|100%)', '비현실적 보장', 0.2)
        ]

        for pattern, issue, penalty in ethical_violations:
            for response in ai_responses:
                if re.search(pattern, response, re.IGNORECASE):
                    score -= penalty
                    suggestions.append(issue)

        score = max(0, score)

        if score > 0.8:
            evidence.append("윤리적 기준 준수")

        return QualityScore(
            dimension=QualityDimension.ETHICAL_COMPLIANCE,
            score=score,
            confidence=0.75,
            evidence=evidence,
            suggestions=suggestions
        )

    def _score_language(self, ai_responses: List[str]) -> QualityScore:
        """언어 품질 점수"""
        score = 0.7
        evidence = []
        suggestions = []

        # 평균 문장 길이
        total_chars = sum(len(r) for r in ai_responses)
        avg_length = total_chars / len(ai_responses) if ai_responses else 0

        if 80 <= avg_length <= 250:
            score += 0.15
            evidence.append("적절한 응답 길이")
        elif avg_length < 50:
            score -= 0.1
            suggestions.append("응답이 너무 짧음")
        elif avg_length > 400:
            score -= 0.1
            suggestions.append("응답이 너무 김")

        # 반복 검사
        all_text = ' '.join(ai_responses)
        words = all_text.split()
        if len(words) > 10:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio > 0.7:
                score += 0.1
                evidence.append("다양한 어휘 사용")
            elif unique_ratio < 0.5:
                score -= 0.1
                suggestions.append("반복적인 표현 줄이기")

        score = max(0, min(1, score))

        return QualityScore(
            dimension=QualityDimension.LANGUAGE_QUALITY,
            score=score,
            confidence=0.8,
            evidence=evidence,
            suggestions=suggestions
        )

    def _score_coherence(self, conversation: List[Dict]) -> QualityScore:
        """일관성 점수"""
        score = 0.7
        evidence = []
        suggestions = []

        # 대화 흐름 검사
        if len(conversation) >= 4:
            # 이전 맥락 참조 확인
            context_references = 0
            for i, msg in enumerate(conversation):
                if msg.get('role') == 'assistant' and i > 0:
                    prev_user_msg = conversation[i-1].get('content', '')
                    # 이전 메시지 키워드 참조
                    prev_keywords = set(prev_user_msg.split()[:5])
                    current = msg.get('content', '')
                    if any(kw in current for kw in prev_keywords if len(kw) > 2):
                        context_references += 1

            if context_references >= 2:
                score += 0.2
                evidence.append("이전 맥락 잘 연결")
            elif context_references == 0:
                score -= 0.1
                suggestions.append("이전 대화 맥락 더 반영 필요")

        return QualityScore(
            dimension=QualityDimension.COHERENCE,
            score=min(1, score),
            confidence=0.6,
            evidence=evidence,
            suggestions=suggestions
        )

    def _score_helpfulness(
        self,
        ai_responses: List[str],
        user_messages: List[str]
    ) -> QualityScore:
        """도움됨 점수"""
        score = 0.6
        evidence = []
        suggestions = []

        # 구체적 제안 확인
        suggestion_patterns = [
            r'(해보시는\s*건|~어떨까요|시도해\s*보)',
            r'(방법|전략|기법)',
            r'(예를\s*들어|예시|구체적으로)'
        ]

        suggestion_count = sum(
            1 for pattern in suggestion_patterns
            for response in ai_responses
            if re.search(pattern, response)
        )

        if suggestion_count >= 2:
            score += 0.25
            evidence.append("구체적인 제안 제공")
        elif suggestion_count == 0:
            suggestions.append("구체적인 도움 제안 추가 고려")

        # 질문에 대한 응답 확인
        user_questions = sum(1 for msg in user_messages if '?' in msg)
        if user_questions > 0:
            # 질문 후 응답에 관련 내용이 있는지 (간단히 확인)
            score += 0.1
            evidence.append("사용자 질문에 응답")

        return QualityScore(
            dimension=QualityDimension.HELPFULNESS,
            score=min(1, score),
            confidence=0.5,
            evidence=evidence,
            suggestions=suggestions
        )

    def _determine_grade(self, score: float) -> str:
        """등급 결정"""
        if score >= 0.9:
            return 'A'
        elif score >= 0.8:
            return 'B'
        elif score >= 0.7:
            return 'C'
        elif score >= 0.6:
            return 'D'
        else:
            return 'F'

    def _analyze_strengths_weaknesses(
        self,
        dimension_scores: Dict[QualityDimension, QualityScore]
    ) -> Tuple[List[str], List[str]]:
        """강점/약점 분석"""
        strengths = []
        weaknesses = []

        for dimension, score in dimension_scores.items():
            if score.score >= 0.8:
                strengths.extend(score.evidence)
            elif score.score < 0.6:
                weaknesses.extend(score.suggestions)

        return strengths[:5], weaknesses[:5]

    def _identify_critical_issues(
        self,
        dimension_scores: Dict[QualityDimension, QualityScore]
    ) -> List[str]:
        """중요 이슈 식별"""
        critical = []

        # 안전성이 낮으면 중요 이슈
        safety_score = dimension_scores.get(QualityDimension.SAFETY)
        if safety_score and safety_score.score < 0.7:
            critical.extend(safety_score.suggestions)

        # 윤리적 준수가 낮으면 중요 이슈
        ethical_score = dimension_scores.get(QualityDimension.ETHICAL_COMPLIANCE)
        if ethical_score and ethical_score.score < 0.7:
            critical.extend(ethical_score.suggestions)

        return critical

    def _generate_recommendations(
        self,
        dimension_scores: Dict[QualityDimension, QualityScore]
    ) -> List[str]:
        """권장사항 생성"""
        recommendations = []

        for dimension, score in dimension_scores.items():
            if score.score < 0.7:
                recommendations.extend(score.suggestions)

        return list(set(recommendations))[:7]

    def _prioritize_improvements(
        self,
        dimension_scores: Dict[QualityDimension, QualityScore]
    ) -> List[str]:
        """우선 개선 사항"""
        # 가중치가 높은 차원 중 점수가 낮은 것 우선
        priority_items = []

        sorted_dimensions = sorted(
            dimension_scores.items(),
            key=lambda x: self.scoring_weights.get(x[0], 0) * (1 - x[1].score),
            reverse=True
        )

        for dimension, score in sorted_dimensions[:3]:
            if score.suggestions:
                priority_items.append(f"[{dimension.value}] {score.suggestions[0]}")

        return priority_items

    def _calculate_percentile(self, score: float) -> float:
        """백분위 계산"""
        if not self.score_history:
            return 50.0

        below_count = sum(1 for s in self.score_history if s < score)
        return (below_count / len(self.score_history)) * 100

    def _calculate_trend(self) -> str:
        """추세 계산"""
        if len(self.score_history) < 5:
            return "데이터 부족"

        recent = self.score_history[-5:]
        older = self.score_history[-10:-5] if len(self.score_history) >= 10 else self.score_history[:-5]

        if not older:
            return "데이터 부족"

        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)

        if recent_avg > older_avg + 0.05:
            return "향상 중"
        elif recent_avg < older_avg - 0.05:
            return "하락 중"
        else:
            return "안정적"


# ============================================================
# Part 3: 개선 피드백 루프
# ============================================================

@dataclass
class ImprovementAction:
    """개선 조치"""
    action_id: str
    category: str
    description: str
    priority: int  # 1-5
    status: str  # pending, in_progress, completed, verified
    created_at: datetime
    target_completion: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    impact_assessment: Optional[str] = None


@dataclass
class FeedbackLoopCycle:
    """피드백 루프 사이클"""
    cycle_id: str
    start_date: datetime
    end_date: Optional[datetime]

    # 수집된 데이터
    reviews_analyzed: int = 0
    quality_reports_analyzed: int = 0

    # 식별된 패턴
    common_issues: List[str] = field(default_factory=list)
    recurring_strengths: List[str] = field(default_factory=list)

    # 생성된 조치
    improvement_actions: List[str] = field(default_factory=list)

    # 결과
    improvement_metrics: Dict[str, float] = field(default_factory=dict)


class ImprovementFeedbackLoop:
    """개선 피드백 루프 시스템"""

    def __init__(self):
        self.expert_review_system = ExpertReviewSystem()
        self.quality_scorer = AutomaticQualityScorer()

        self.improvement_actions: Dict[str, ImprovementAction] = {}
        self.feedback_cycles: List[FeedbackLoopCycle] = []
        self.current_cycle: Optional[FeedbackLoopCycle] = None

        # 패턴 추적
        self.issue_frequency: Dict[str, int] = defaultdict(int)
        self.improvement_history: List[Dict] = []

    def start_cycle(self) -> str:
        """새 피드백 사이클 시작"""
        cycle_id = str(uuid.uuid4())[:8]

        if self.current_cycle:
            self.current_cycle.end_date = datetime.now()
            self.feedback_cycles.append(self.current_cycle)

        self.current_cycle = FeedbackLoopCycle(
            cycle_id=cycle_id,
            start_date=datetime.now()
        )

        return cycle_id

    def collect_feedback(
        self,
        conversation: List[Dict],
        expert_review: Optional[ExpertReview] = None,
        user_feedback: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """피드백 수집 및 분석"""
        results = {
            'quality_report': None,
            'issues_identified': [],
            'actions_recommended': []
        }

        # 자동 품질 평가
        quality_report = self.quality_scorer.score_conversation(conversation)
        results['quality_report'] = quality_report

        # 이슈 빈도 업데이트
        for issue in quality_report.critical_issues:
            self.issue_frequency[issue] += 1
            results['issues_identified'].append(issue)

        for weakness in quality_report.weaknesses:
            self.issue_frequency[weakness] += 1

        # 전문가 검토 통합
        if expert_review:
            for area in expert_review.areas_for_improvement:
                self.issue_frequency[area] += 2  # 전문가 피드백 가중치

        # 사용자 피드백 통합
        if user_feedback:
            if user_feedback.get('rating', 5) <= 2:
                reason = user_feedback.get('reason', '불만족')
                self.issue_frequency[reason] += 1

        # 권장 조치 생성
        results['actions_recommended'] = self._generate_actions(quality_report)

        # 현재 사이클 업데이트
        if self.current_cycle:
            self.current_cycle.reviews_analyzed += 1
            self.current_cycle.quality_reports_analyzed += 1

        return results

    def _generate_actions(
        self,
        quality_report: ComprehensiveQualityReport
    ) -> List[ImprovementAction]:
        """개선 조치 생성"""
        actions = []

        for i, improvement in enumerate(quality_report.priority_improvements):
            action = ImprovementAction(
                action_id=str(uuid.uuid4())[:8],
                category=improvement.split(']')[0].replace('[', '') if ']' in improvement else 'general',
                description=improvement,
                priority=i + 1,
                status='pending',
                created_at=datetime.now(),
                target_completion=datetime.now() + timedelta(days=7 * (i + 1))
            )
            actions.append(action)
            self.improvement_actions[action.action_id] = action

        return actions

    def analyze_patterns(self) -> Dict[str, Any]:
        """패턴 분석"""
        # 가장 빈번한 이슈
        sorted_issues = sorted(
            self.issue_frequency.items(),
            key=lambda x: x[1],
            reverse=True
        )

        common_issues = [issue for issue, count in sorted_issues[:10]]

        # 현재 사이클 업데이트
        if self.current_cycle:
            self.current_cycle.common_issues = common_issues

        return {
            'common_issues': common_issues,
            'issue_frequency': dict(sorted_issues[:20]),
            'total_issues_tracked': sum(self.issue_frequency.values())
        }

    def generate_improvement_report(self) -> Dict[str, Any]:
        """개선 보고서 생성"""
        pattern_analysis = self.analyze_patterns()

        # 조치 상태 요약
        action_summary = {
            'pending': 0,
            'in_progress': 0,
            'completed': 0
        }

        for action in self.improvement_actions.values():
            if action.status in action_summary:
                action_summary[action.status] += 1

        # 품질 추세
        quality_trend = self.quality_scorer._calculate_trend()

        return {
            'report_date': datetime.now().isoformat(),
            'pattern_analysis': pattern_analysis,
            'action_summary': action_summary,
            'quality_trend': quality_trend,
            'top_priorities': [
                {
                    'issue': issue,
                    'frequency': self.issue_frequency[issue],
                    'recommended_action': f"'{issue}' 관련 교육 및 가이드라인 강화"
                }
                for issue in pattern_analysis['common_issues'][:5]
            ],
            'cycles_completed': len(self.feedback_cycles),
            'current_cycle_stats': {
                'reviews': self.current_cycle.reviews_analyzed if self.current_cycle else 0,
                'quality_reports': self.current_cycle.quality_reports_analyzed if self.current_cycle else 0
            }
        }

    def update_action_status(
        self,
        action_id: str,
        new_status: str,
        impact_assessment: Optional[str] = None
    ) -> bool:
        """조치 상태 업데이트"""
        if action_id not in self.improvement_actions:
            return False

        action = self.improvement_actions[action_id]
        action.status = new_status

        if new_status == 'completed':
            action.completed_at = datetime.now()
            if impact_assessment:
                action.impact_assessment = impact_assessment

            # 이력 기록
            self.improvement_history.append({
                'action_id': action_id,
                'description': action.description,
                'completed_at': action.completed_at.isoformat(),
                'impact': impact_assessment
            })

        return True

    def get_actionable_insights(self) -> List[Dict[str, Any]]:
        """실행 가능한 인사이트"""
        insights = []

        # 빈번한 이슈 기반 인사이트
        pattern_analysis = self.analyze_patterns()

        for issue, frequency in list(pattern_analysis['issue_frequency'].items())[:5]:
            insights.append({
                'type': 'recurring_issue',
                'issue': issue,
                'frequency': frequency,
                'insight': f"'{issue}'가 {frequency}회 발생. 시스템 프롬프트 또는 가이드라인 수정 권장.",
                'action_type': 'prompt_update'
            })

        # 품질 추세 기반 인사이트
        if self.quality_scorer.score_history:
            recent_scores = self.quality_scorer.score_history[-10:]
            avg_score = sum(recent_scores) / len(recent_scores)

            if avg_score < 0.7:
                insights.append({
                    'type': 'quality_alert',
                    'issue': '전반적 품질 저하',
                    'current_score': avg_score,
                    'insight': '최근 평균 품질 점수가 기준 미달. 전체적인 검토 필요.',
                    'action_type': 'comprehensive_review'
                })

        return insights


# ============================================================
# Part 4: 통합 슈퍼비전 시스템
# ============================================================

class IntegratedSupervisionSystem:
    """통합 슈퍼비전 시스템"""

    def __init__(self):
        self.expert_review = ExpertReviewSystem()
        self.quality_scorer = AutomaticQualityScorer()
        self.feedback_loop = ImprovementFeedbackLoop()

        # 알림 콜백
        self.alert_callbacks: List[Callable] = []

    def process_session(
        self,
        session_id: str,
        user_id: str,
        conversation: List[Dict],
        auto_submit_for_review: bool = True
    ) -> Dict[str, Any]:
        """세션 처리"""
        results = {
            'session_id': session_id,
            'quality_report': None,
            'review_id': None,
            'alerts': []
        }

        # 자동 품질 평가
        quality_report = self.quality_scorer.score_conversation(
            conversation,
            context={'session_id': session_id}
        )
        results['quality_report'] = quality_report

        # 피드백 수집
        feedback_result = self.feedback_loop.collect_feedback(conversation)

        # 검토 제출 여부 결정
        should_submit = auto_submit_for_review

        # 자동 에스컬레이션 조건
        if quality_report.grade in ['D', 'F']:
            should_submit = True
            results['alerts'].append({
                'type': 'low_quality',
                'message': f'품질 등급 {quality_report.grade} - 검토 필요'
            })

        if quality_report.critical_issues:
            should_submit = True
            results['alerts'].append({
                'type': 'critical_issue',
                'message': f'중요 이슈 감지: {quality_report.critical_issues}'
            })

        # 검토 제출
        if should_submit:
            review_id = self.expert_review.submit_for_review(
                session_id=session_id,
                user_id=user_id,
                conversation=conversation,
                metadata={
                    'auto_quality_score': quality_report.overall_score,
                    'grade': quality_report.grade,
                    'critical_issues': quality_report.critical_issues
                }
            )
            results['review_id'] = review_id

        # 알림 발송
        if results['alerts']:
            self._send_alerts(results['alerts'])

        return results

    def _send_alerts(self, alerts: List[Dict]):
        """알림 발송"""
        for callback in self.alert_callbacks:
            for alert in alerts:
                try:
                    callback(alert)
                except Exception as e:
                    pass  # 로깅

    def register_alert_callback(self, callback: Callable):
        """알림 콜백 등록"""
        self.alert_callbacks.append(callback)

    def get_dashboard_data(self) -> Dict[str, Any]:
        """대시보드 데이터"""
        return {
            'review_stats': self.expert_review.get_review_statistics(),
            'improvement_report': self.feedback_loop.generate_improvement_report(),
            'insights': self.feedback_loop.get_actionable_insights(),
            'pending_reviews': len(self.expert_review.get_pending_reviews()),
            'quality_trend': self.quality_scorer._calculate_trend()
        }

    def generate_summary_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> str:
        """요약 보고서 생성"""
        dashboard = self.get_dashboard_data()

        report = f"""
# 슈퍼비전 요약 보고서
기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}

## 검토 통계
- 총 검토 완료: {dashboard['review_stats']['total_reviewed']}건
- 승인: {dashboard['review_stats']['approved']}건
- 수정 필요: {dashboard['review_stats']['needs_revision']}건
- 승인율: {dashboard['review_stats']['approval_rate']*100:.1f}%

## 품질 동향
- 추세: {dashboard['quality_trend']}
- 대기 중 검토: {dashboard['pending_reviews']}건

## 주요 개선 영역
"""
        for i, insight in enumerate(dashboard['insights'][:5], 1):
            report += f"{i}. {insight['issue']}: {insight['insight']}\n"

        report += f"""
## 권장 조치
"""
        for priority in dashboard['improvement_report']['top_priorities']:
            report += f"- {priority['recommended_action']}\n"

        return report


# 사용 예시
if __name__ == "__main__":
    system = IntegratedSupervisionSystem()

    # 테스트 대화
    test_conversation = [
        {"role": "user", "content": "요즘 너무 힘들어요. 우울하고 아무것도 하기 싫어요."},
        {"role": "assistant", "content": "정말 힘드시겠어요. 우울하고 의욕이 없는 상태가 얼마나 고통스러운지 이해합니다. 이런 마음이 드신 지 얼마나 되셨나요?"},
        {"role": "user", "content": "한 달 정도 된 것 같아요. 잠도 잘 못 자고요."},
        {"role": "assistant", "content": "한 달이나 이런 상태가 지속되셨군요. 수면까지 영향을 받고 계시니 정말 힘드시겠어요. 혹시 이렇게 느끼시게 된 특별한 계기가 있으셨나요?"}
    ]

    # 세션 처리
    result = system.process_session(
        session_id="test_session_001",
        user_id="user_001",
        conversation=test_conversation
    )

    print("=== 품질 평가 결과 ===")
    print(f"종합 점수: {result['quality_report'].overall_score:.2f}")
    print(f"등급: {result['quality_report'].grade}")
    print(f"\n강점: {result['quality_report'].strengths}")
    print(f"개선점: {result['quality_report'].weaknesses}")

    if result['review_id']:
        print(f"\n검토 ID: {result['review_id']}")

    print("\n=== 대시보드 ===")
    dashboard = system.get_dashboard_data()
    print(json.dumps(dashboard['insights'], ensure_ascii=False, indent=2))
