"""
치료적 질문 시스템 (Therapeutic Questioning System)

효과적인 상담을 위한 고급 질문 기술:
1. 순환 질문 (Circular Questions) - 관계 패턴 탐색
2. 기적 질문 (Miracle Questions) - 변화 비전 구체화
3. 척도 질문 (Scaling Questions) - 변화 측정
4. 예외 질문 (Exception Questions) - 강점/자원 발견
5. 소크라테스식 질문 (Socratic Questions) - 인지적 재구성
6. 반영 질문 (Reflective Questions) - 자기 탐색 촉진
"""

from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass, field
import logging
import random
from datetime import datetime

logger = logging.getLogger(__name__)


# =============================================================================
# 질문 유형 및 데이터 구조
# =============================================================================

class QuestionType(Enum):
    """질문 유형"""
    CIRCULAR = "circular"              # 순환 질문
    MIRACLE = "miracle"                # 기적 질문
    SCALING = "scaling"                # 척도 질문
    EXCEPTION = "exception"            # 예외 질문
    SOCRATIC = "socratic"              # 소크라테스식 질문
    REFLECTIVE = "reflective"          # 반영 질문
    COPING = "coping"                  # 대처 질문
    FUTURE_ORIENTED = "future"         # 미래지향 질문
    RELATIONSHIP = "relationship"      # 관계 질문


class QuestionPurpose(Enum):
    """질문 목적"""
    EXPLORATION = "exploration"        # 탐색
    INSIGHT = "insight"                # 통찰 촉진
    CHANGE = "change"                  # 변화 동기
    RESOURCE = "resource"              # 자원 발견
    PATTERN = "pattern"                # 패턴 인식
    COGNITIVE = "cognitive"            # 인지 재구성
    EMOTION = "emotion"                # 감정 심화
    SOLUTION = "solution"              # 해결 지향


class QuestionTiming(Enum):
    """질문 타이밍"""
    OPENING = "opening"                # 세션 초반
    EXPLORATION = "exploration"        # 탐색 단계
    WORKING = "working"                # 작업 단계
    CLOSING = "closing"                # 마무리 단계
    ANY = "any"                        # 언제든


@dataclass
class TherapeuticQuestion:
    """치료적 질문"""
    question: str
    question_type: QuestionType
    purpose: QuestionPurpose
    timing: QuestionTiming
    follow_up: List[str] = field(default_factory=list)
    context_tags: List[str] = field(default_factory=list)
    effectiveness_score: float = 0.7


@dataclass
class QuestionContext:
    """질문 맥락"""
    topic: str = ""
    emotion: str = ""
    relationship_mentioned: str = ""
    problem_statement: str = ""
    change_readiness: float = 0.5
    session_phase: QuestionTiming = QuestionTiming.ANY
    previous_questions: List[str] = field(default_factory=list)


# =============================================================================
# 1. 순환 질문 (Circular Questions)
# =============================================================================

class CircularQuestionGenerator:
    """
    순환 질문 생성기

    관계 패턴과 상호작용을 탐색하는 질문
    가족치료에서 유래, 관계적 맥락 이해에 효과적
    """

    # 관계 탐색 질문
    RELATIONSHIP_PATTERNS = {
        "perspective": [
            "{person}은(는) 이 상황을 어떻게 보고 있을까요?",
            "{person}의 입장에서 보면 어떤 마음일 것 같아요?",
            "만약 {person}에게 물어본다면, 뭐라고 할 것 같아요?",
            "{person}은(는) 지금 무엇을 느끼고 있을까요?",
        ],
        "interaction": [
            "당신이 {action}할 때, {person}은(는) 어떻게 반응하나요?",
            "{person}이(가) 그렇게 할 때, 당신은 보통 어떻게 하세요?",
            "그러면 {person}은(는) 또 어떻게 하나요?",
            "그 후에 당신은 어떻게 느끼세요?",
        ],
        "difference": [
            "{person1}과 {person2}는 이 문제를 각각 어떻게 보나요?",
            "두 사람의 반응이 어떻게 다른가요?",
            "누가 가장 걱정을 많이 하나요?",
            "이 상황에서 누가 가장 영향을 받나요?",
        ],
        "hypothetical": [
            "만약 {person}이(가) 여기 있다면 뭐라고 할까요?",
            "{person}이(가) 이 대화를 듣는다면 어떤 생각을 할까요?",
            "만약 상황이 달라진다면, {person}은(는) 어떻게 반응할까요?",
        ],
        "observer": [
            "제3자가 본다면 이 상황을 어떻게 설명할까요?",
            "가까운 친구가 본다면 뭐라고 할 것 같아요?",
            "10년 후의 당신이 본다면 어떻게 생각할까요?",
        ]
    }

    def __init__(self):
        logger.info("CircularQuestionGenerator initialized")

    def generate(self, context: QuestionContext,
                 relationship: Optional[str] = None) -> List[TherapeuticQuestion]:
        """
        순환 질문 생성

        Args:
            context: 질문 맥락
            relationship: 관계 대상 (예: "어머니", "상사")

        Returns:
            List[TherapeuticQuestion]: 생성된 질문들
        """
        questions = []
        person = relationship or context.relationship_mentioned or "그 사람"

        # 관점 탐색 질문
        for template in self.RELATIONSHIP_PATTERNS["perspective"]:
            q = template.format(person=person)
            questions.append(TherapeuticQuestion(
                question=q,
                question_type=QuestionType.CIRCULAR,
                purpose=QuestionPurpose.PATTERN,
                timing=QuestionTiming.EXPLORATION,
                context_tags=["relationship", "perspective"]
            ))

        # 상호작용 패턴 질문
        for template in self.RELATIONSHIP_PATTERNS["interaction"][:2]:
            q = template.format(person=person, action="그렇게")
            questions.append(TherapeuticQuestion(
                question=q,
                question_type=QuestionType.CIRCULAR,
                purpose=QuestionPurpose.PATTERN,
                timing=QuestionTiming.EXPLORATION,
                context_tags=["relationship", "interaction"]
            ))

        # 관찰자 시점 질문
        for template in self.RELATIONSHIP_PATTERNS["observer"]:
            questions.append(TherapeuticQuestion(
                question=template,
                question_type=QuestionType.CIRCULAR,
                purpose=QuestionPurpose.INSIGHT,
                timing=QuestionTiming.WORKING,
                context_tags=["observer", "reflection"]
            ))

        return questions[:5]  # 최대 5개


# =============================================================================
# 2. 기적 질문 (Miracle Questions)
# =============================================================================

class MiracleQuestionGenerator:
    """
    기적 질문 생성기

    해결중심단기치료(SFBT)의 핵심 기법
    원하는 미래를 구체화하여 변화 동기 강화
    """

    # 기본 기적 질문
    CLASSIC_MIRACLE = """
오늘 밤 잠자리에 드셨을 때, 자는 동안 기적이 일어났다고 상상해 보세요.
그 기적으로 지금 고민하시는 문제가 해결되었어요.
하지만 잠을 자고 있었기 때문에 기적이 일어난 걸 모르세요.
내일 아침에 일어났을 때, 기적이 일어났다는 것을 어떻게 알 수 있을까요?
무엇이 달라져 있을까요?
"""

    # 기적 질문 변형들
    VARIATIONS = {
        "morning": [
            "내일 아침, 기적이 일어나서 문제가 해결됐다면, 가장 먼저 무엇이 다를까요?",
            "아침에 눈을 떴을 때 어떤 느낌이 들까요?",
            "첫 번째로 하는 행동이 어떻게 달라질까요?",
        ],
        "relationship": [
            "기적이 일어났다면, 가족/친구는 당신의 어떤 변화를 알아챌까요?",
            "주변 사람들이 당신을 어떻게 다르게 대할까요?",
            "당신과 {person}의 관계는 어떻게 달라져 있을까요?",
        ],
        "feeling": [
            "기적 후에 당신은 어떤 기분이 들까요?",
            "지금과 어떻게 다르게 느끼실까요?",
            "그 느낌을 단어로 표현한다면요?",
        ],
        "behavior": [
            "기적이 일어난 날, 당신은 무엇을 하고 있을까요?",
            "어떤 것들을 다르게 하고 계실까요?",
            "하루 일과가 어떻게 달라질까요?",
        ],
        "small_signs": [
            "그 기적의 작은 조각이 이미 일어나고 있다면, 어디서 찾을 수 있을까요?",
            "기적의 1%라도 이미 일어난 적이 있나요?",
            "작은 변화의 씨앗이 있다면 어디에 있을까요?",
        ]
    }

    # 후속 질문
    FOLLOW_UPS = [
        "그게 일어난다면 어떤 기분이 들까요?",
        "그 변화가 일어나면 또 뭐가 달라질까요?",
        "그걸 알아챈 사람이 있다면 어떻게 반응할까요?",
        "그런 날이 오면 가장 먼저 누구에게 알리고 싶으세요?",
        "그 상황을 10점 만점으로 표현한다면 몇 점일까요?",
    ]

    def __init__(self):
        logger.info("MiracleQuestionGenerator initialized")

    def generate(self, context: QuestionContext,
                 style: str = "classic") -> List[TherapeuticQuestion]:
        """
        기적 질문 생성

        Args:
            context: 질문 맥락
            style: 질문 스타일 (classic, brief, detailed)

        Returns:
            List[TherapeuticQuestion]: 생성된 질문들
        """
        questions = []

        # 클래식 기적 질문
        if style == "classic":
            questions.append(TherapeuticQuestion(
                question=self.CLASSIC_MIRACLE.strip(),
                question_type=QuestionType.MIRACLE,
                purpose=QuestionPurpose.CHANGE,
                timing=QuestionTiming.WORKING,
                follow_up=self.FOLLOW_UPS[:3],
                context_tags=["miracle", "future", "change"]
            ))

        # 변형 질문들
        for category, templates in self.VARIATIONS.items():
            for template in templates:
                if "{person}" in template:
                    q = template.format(
                        person=context.relationship_mentioned or "중요한 사람"
                    )
                else:
                    q = template

                questions.append(TherapeuticQuestion(
                    question=q,
                    question_type=QuestionType.MIRACLE,
                    purpose=QuestionPurpose.CHANGE,
                    timing=QuestionTiming.WORKING,
                    follow_up=self.FOLLOW_UPS[:2],
                    context_tags=["miracle", category]
                ))

        return questions[:6]

    def generate_brief(self, topic: str = "") -> TherapeuticQuestion:
        """간단한 기적 질문 생성"""
        brief_versions = [
            f"만약 오늘 밤 자는 동안 {topic or '이 문제'}가 해결된다면, 내일 아침 무엇이 달라져 있을까요?",
            "문제가 완전히 해결된 내일을 상상해 보세요. 어떤 모습인가요?",
            "원하는 변화가 일어난 후의 하루는 어떨까요?",
        ]

        return TherapeuticQuestion(
            question=random.choice(brief_versions),
            question_type=QuestionType.MIRACLE,
            purpose=QuestionPurpose.CHANGE,
            timing=QuestionTiming.WORKING,
            context_tags=["miracle", "brief"]
        )


# =============================================================================
# 3. 척도 질문 (Scaling Questions)
# =============================================================================

class ScalingQuestionGenerator:
    """
    척도 질문 생성기

    0-10 척도를 사용하여 변화를 측정하고 목표를 구체화
    """

    # 척도 질문 템플릿
    TEMPLATES = {
        "current_state": [
            "지금 상태를 0점에서 10점으로 표현한다면 몇 점인가요? (0은 최악, 10은 최상)",
            "현재 기분을 1부터 10까지 숫자로 말씀해 주신다면요?",
            "지금 이 문제의 심각도를 0~10으로 표현하면요?",
        ],
        "goal": [
            "원하시는 상태가 10점이라면, 지금은 몇 점쯤 되나요?",
            "목표에 10점 만점으로 얼마나 가까워졌나요?",
            "완전히 해결된 상태를 10점이라고 할 때, 현재는요?",
        ],
        "progress": [
            "지난번보다 점수가 달라졌나요?",
            "처음 오셨을 때와 비교하면 몇 점 정도 달라졌나요?",
            "한 달 전과 비교하면요?",
        ],
        "small_step": [
            "지금보다 1점 높아지려면 무엇이 필요할까요?",
            "0.5점만 올리려면 뭘 할 수 있을까요?",
            "다음 한 걸음은 무엇일까요?",
        ],
        "confidence": [
            "이 문제를 해결할 수 있다는 자신감은 몇 점인가요?",
            "변화할 수 있다는 믿음을 점수로 매긴다면요?",
            "성공할 가능성을 0~10으로 표현해 주세요.",
        ],
        "importance": [
            "이 변화가 얼마나 중요한가요? 0~10으로요.",
            "이걸 해결하는 게 당신에게 얼마나 의미있나요?",
            "우선순위로 매긴다면 몇 점인가요?",
        ],
        "coping": [
            "지금 점수에서 더 내려가지 않게 하는 건 뭔가요?",
            "그 점수를 유지하게 해주는 것은 무엇인가요?",
            "0점이 아닌 이유는 뭘까요?",
        ]
    }

    # 점수별 후속 질문
    SCORE_BASED_FOLLOW_UPS = {
        "low": [  # 1-3점
            "그 점수에서 버티고 계신 건 대단한 거예요. 어떻게 버티고 계세요?",
            "최악의 상황에서 조금이라도 올라온 적이 있나요?",
            "1점이라도 올리는 데 도움이 될 것은요?",
        ],
        "medium": [  # 4-6점
            "절반은 오신 거네요! 여기까지 어떻게 오셨어요?",
            "이 점수를 유지하게 해주는 것은 무엇인가요?",
            "다음 한 걸음은 무엇일 것 같아요?",
        ],
        "high": [  # 7-10점
            "정말 많이 오셨네요! 비결이 뭔가요?",
            "이 점수를 유지하려면 무엇이 필요할까요?",
            "10점이 되면 뭐가 달라질까요?",
        ]
    }

    def __init__(self):
        logger.info("ScalingQuestionGenerator initialized")

    def generate(self, context: QuestionContext,
                 category: str = "current_state") -> List[TherapeuticQuestion]:
        """
        척도 질문 생성

        Args:
            context: 질문 맥락
            category: 질문 카테고리

        Returns:
            List[TherapeuticQuestion]: 생성된 질문들
        """
        questions = []

        templates = self.TEMPLATES.get(category, self.TEMPLATES["current_state"])

        for template in templates:
            questions.append(TherapeuticQuestion(
                question=template,
                question_type=QuestionType.SCALING,
                purpose=QuestionPurpose.CHANGE,
                timing=QuestionTiming.ANY,
                context_tags=["scaling", category]
            ))

        return questions

    def get_follow_up(self, score: int) -> List[str]:
        """점수에 따른 후속 질문"""
        if score <= 3:
            return self.SCORE_BASED_FOLLOW_UPS["low"]
        elif score <= 6:
            return self.SCORE_BASED_FOLLOW_UPS["medium"]
        else:
            return self.SCORE_BASED_FOLLOW_UPS["high"]

    def generate_sequence(self, topic: str = "") -> List[TherapeuticQuestion]:
        """척도 질문 시퀀스 생성"""
        sequence = []
        topic_text = topic or "이 상황"

        # 1. 현재 상태
        sequence.append(TherapeuticQuestion(
            question=f"{topic_text}을 0~10점으로 표현한다면 지금 몇 점인가요?",
            question_type=QuestionType.SCALING,
            purpose=QuestionPurpose.EXPLORATION,
            timing=QuestionTiming.ANY
        ))

        # 2. 강점 발견
        sequence.append(TherapeuticQuestion(
            question="0점이 아닌 이유는 뭘까요? 무엇이 그 점수를 지탱해주나요?",
            question_type=QuestionType.SCALING,
            purpose=QuestionPurpose.RESOURCE,
            timing=QuestionTiming.ANY
        ))

        # 3. 작은 변화
        sequence.append(TherapeuticQuestion(
            question="1점만 올리려면 무엇이 달라져야 할까요?",
            question_type=QuestionType.SCALING,
            purpose=QuestionPurpose.CHANGE,
            timing=QuestionTiming.ANY
        ))

        # 4. 자신감
        sequence.append(TherapeuticQuestion(
            question="그 1점을 올릴 수 있다는 자신감은 몇 점인가요?",
            question_type=QuestionType.SCALING,
            purpose=QuestionPurpose.CHANGE,
            timing=QuestionTiming.ANY
        ))

        return sequence


# =============================================================================
# 4. 예외 질문 (Exception Questions)
# =============================================================================

class ExceptionQuestionGenerator:
    """
    예외 질문 생성기

    문제가 없거나 덜했던 예외적 상황을 탐색
    강점과 자원을 발견하고 해결책의 단서를 찾음
    """

    # 예외 탐색 질문
    TEMPLATES = {
        "occurrence": [
            "이 문제가 조금이라도 덜했던 적이 있나요?",
            "최근에 이런 상황이 일어나지 않았던 때가 있었나요?",
            "괜찮았던 날이 있다면 언제였나요?",
            "문제가 완전히 없었던 순간을 떠올려 보시겠어요?",
        ],
        "what_different": [
            "그때는 뭐가 달랐나요?",
            "어떤 점이 지금과 달랐을까요?",
            "그 상황에서 당신은 무엇을 다르게 하셨나요?",
            "그때 주변 환경이나 상황은 어땠나요?",
        ],
        "how_did": [
            "어떻게 그렇게 하실 수 있었나요?",
            "그때 당신이 사용한 방법은 무엇이었나요?",
            "그 순간 당신 안에 어떤 힘이 있었나요?",
            "무엇이 그걸 가능하게 했나요?",
        ],
        "who_noticed": [
            "그때 주변에서 알아챈 사람이 있나요?",
            "누군가 당신의 변화를 눈치챘나요?",
            "가까운 사람은 뭐라고 했나요?",
        ],
        "replicate": [
            "그때처럼 다시 해볼 수 있을까요?",
            "그 방법을 지금 상황에 적용한다면요?",
            "그때의 당신을 다시 불러올 수 있다면 어떨까요?",
        ],
        "strengths": [
            "그걸 해낸 당신 안에 어떤 강점이 있을까요?",
            "그 상황에서 발휘된 당신의 능력은 뭘까요?",
            "그때 당신이 가진 자원은 무엇이었나요?",
        ]
    }

    def __init__(self):
        logger.info("ExceptionQuestionGenerator initialized")

    def generate(self, context: QuestionContext) -> List[TherapeuticQuestion]:
        """예외 질문 생성"""
        questions = []

        for category, templates in self.TEMPLATES.items():
            for template in templates[:2]:  # 각 카테고리에서 2개씩
                questions.append(TherapeuticQuestion(
                    question=template,
                    question_type=QuestionType.EXCEPTION,
                    purpose=QuestionPurpose.RESOURCE,
                    timing=QuestionTiming.WORKING,
                    context_tags=["exception", category]
                ))

        return questions

    def generate_sequence(self, problem: str = "") -> List[TherapeuticQuestion]:
        """예외 질문 시퀀스 생성"""
        problem_text = problem or "이 문제"

        return [
            TherapeuticQuestion(
                question=f"{problem_text}가 조금이라도 나았던 적이 있나요?",
                question_type=QuestionType.EXCEPTION,
                purpose=QuestionPurpose.RESOURCE,
                timing=QuestionTiming.WORKING
            ),
            TherapeuticQuestion(
                question="그때는 무엇이 달랐나요?",
                question_type=QuestionType.EXCEPTION,
                purpose=QuestionPurpose.INSIGHT,
                timing=QuestionTiming.WORKING
            ),
            TherapeuticQuestion(
                question="당신이 무엇을 다르게 했나요?",
                question_type=QuestionType.EXCEPTION,
                purpose=QuestionPurpose.RESOURCE,
                timing=QuestionTiming.WORKING
            ),
            TherapeuticQuestion(
                question="그때의 그 방법/힘을 지금 다시 쓸 수 있을까요?",
                question_type=QuestionType.EXCEPTION,
                purpose=QuestionPurpose.CHANGE,
                timing=QuestionTiming.WORKING
            ),
        ]


# =============================================================================
# 5. 소크라테스식 질문 (Socratic Questions)
# =============================================================================

class SocraticQuestionGenerator:
    """
    소크라테스식 질문 생성기

    인지치료의 핵심 기법
    자동적 사고를 탐색하고 인지적 재구성을 촉진
    """

    # 인지 왜곡 유형
    COGNITIVE_DISTORTIONS = {
        "all_or_nothing": {
            "name": "흑백논리",
            "markers": ["항상", "절대", "완전히", "전혀", "모든", "아무것도"],
            "questions": [
                "정말 '항상' 그런가요? 예외는 없었나요?",
                "'전혀' 없었다고 하셨는데, 조금이라도 있었던 적은요?",
                "중간 지점은 없을까요?",
                "회색 영역은 어디 있을까요?",
            ]
        },
        "overgeneralization": {
            "name": "과잉일반화",
            "markers": ["늘", "매번", "어차피", "다", "결국"],
            "questions": [
                "이번 일이 다른 상황에도 적용될까요?",
                "'매번'이라고 하셨는데, 다른 결과가 있었던 적은요?",
                "이 한 가지 일로 전체를 판단해도 될까요?",
            ]
        },
        "mind_reading": {
            "name": "독심술",
            "markers": ["분명히 ~라고 생각", "나를 ~로 본다", "~일 게 뻔해"],
            "questions": [
                "그 사람이 정말 그렇게 생각하는지 어떻게 아셨어요?",
                "다른 가능성은 없을까요?",
                "직접 확인해 본 적이 있나요?",
                "그게 사실이라는 증거가 있나요?",
            ]
        },
        "catastrophizing": {
            "name": "파국화",
            "markers": ["끝장", "망했", "최악", "재앙", "끝이야"],
            "questions": [
                "최악의 상황이 정말 일어날 가능성은 몇 퍼센트일까요?",
                "실제로 그런 일이 일어난다면 어떻게 대처할 수 있을까요?",
                "이전에 비슷한 걱정을 했을 때 실제로 어떻게 됐나요?",
            ]
        },
        "should_statements": {
            "name": "당위적 사고",
            "markers": ["~해야", "~여야", "~하면 안 돼", "당연히"],
            "questions": [
                "그 '해야 한다'는 생각은 어디서 온 걸까요?",
                "만약 그렇게 하지 않으면 어떻게 되나요?",
                "그 기준을 다른 사람에게도 똑같이 적용하시나요?",
                "'~하면 좋겠다'로 바꿔 생각하면 어떨까요?",
            ]
        },
        "labeling": {
            "name": "낙인찍기",
            "markers": ["나는 ~야", "~한 사람이야", "루저", "실패자", "바보"],
            "questions": [
                "그 단어가 당신의 전부를 설명하나요?",
                "그 행동이 당신 자체를 정의할까요?",
                "소중한 사람이 그렇게 말한다면 뭐라고 하시겠어요?",
                "그 레이블 외에 당신을 설명하는 다른 말은요?",
            ]
        },
        "personalization": {
            "name": "개인화",
            "markers": ["내 탓", "내가 ~해서", "내 책임"],
            "questions": [
                "정말 당신 때문인가요?",
                "다른 원인은 없을까요?",
                "100% 당신 책임이라고 할 수 있을까요?",
                "상대방이나 상황의 영향은요?",
            ]
        },
        "emotional_reasoning": {
            "name": "감정적 추론",
            "markers": ["느껴지니까", "기분이 그러니까", "불안하니까 ~일 거야"],
            "questions": [
                "그 느낌이 사실을 반영하나요?",
                "기분과 현실이 다를 수도 있지 않을까요?",
                "불안할 때 생각이 더 부정적으로 기울지 않나요?",
            ]
        }
    }

    # 증거 탐색 질문
    EVIDENCE_QUESTIONS = {
        "supporting": [
            "그 생각을 뒷받침하는 증거는 무엇인가요?",
            "그렇게 생각하게 된 근거가 있나요?",
            "어떤 사실이 그 생각을 지지하나요?",
        ],
        "contradicting": [
            "반대되는 증거는 없나요?",
            "그 생각에 맞지 않는 경험이 있나요?",
            "다르게 볼 수 있는 부분은요?",
        ],
        "alternative": [
            "다른 설명이 가능할까요?",
            "다른 가능성은 없을까요?",
            "친한 친구라면 이 상황을 어떻게 볼까요?",
        ]
    }

    # 재구성 촉진 질문
    REFRAMING_QUESTIONS = [
        "다르게 생각한다면 기분이 어떻게 달라질까요?",
        "5년 후의 당신이 지금을 돌아본다면 어떻게 생각할까요?",
        "가장 친한 친구가 같은 상황이라면 뭐라고 해주겠어요?",
        "이 상황에서 배울 수 있는 점이 있다면요?",
        "이 경험이 당신을 어떻게 성장시킬 수 있을까요?",
    ]

    def __init__(self):
        logger.info("SocraticQuestionGenerator initialized")

    def detect_distortion(self, message: str) -> List[Dict[str, Any]]:
        """인지 왜곡 감지"""
        detected = []

        for distortion_type, info in self.COGNITIVE_DISTORTIONS.items():
            for marker in info["markers"]:
                if marker in message:
                    detected.append({
                        "type": distortion_type,
                        "name": info["name"],
                        "marker": marker,
                        "questions": info["questions"]
                    })
                    break  # 유형당 한 번만

        return detected

    def generate(self, context: QuestionContext,
                 message: str = "") -> List[TherapeuticQuestion]:
        """소크라테스식 질문 생성"""
        questions = []

        # 인지 왜곡 감지
        distortions = self.detect_distortion(message)

        for d in distortions:
            for q in d["questions"][:2]:
                questions.append(TherapeuticQuestion(
                    question=q,
                    question_type=QuestionType.SOCRATIC,
                    purpose=QuestionPurpose.COGNITIVE,
                    timing=QuestionTiming.WORKING,
                    context_tags=["socratic", d["type"], d["name"]]
                ))

        # 증거 탐색 질문
        for category, templates in self.EVIDENCE_QUESTIONS.items():
            questions.append(TherapeuticQuestion(
                question=templates[0],
                question_type=QuestionType.SOCRATIC,
                purpose=QuestionPurpose.COGNITIVE,
                timing=QuestionTiming.WORKING,
                context_tags=["socratic", "evidence", category]
            ))

        # 재구성 질문
        for q in self.REFRAMING_QUESTIONS[:2]:
            questions.append(TherapeuticQuestion(
                question=q,
                question_type=QuestionType.SOCRATIC,
                purpose=QuestionPurpose.INSIGHT,
                timing=QuestionTiming.WORKING,
                context_tags=["socratic", "reframing"]
            ))

        return questions

    def generate_for_thought(self, automatic_thought: str) -> List[TherapeuticQuestion]:
        """특정 자동적 사고에 대한 질문 생성"""
        questions = []

        # 1. 증거 탐색
        questions.append(TherapeuticQuestion(
            question=f"'{automatic_thought}'라는 생각을 뒷받침하는 증거는 무엇인가요?",
            question_type=QuestionType.SOCRATIC,
            purpose=QuestionPurpose.COGNITIVE,
            timing=QuestionTiming.WORKING
        ))

        # 2. 반증 탐색
        questions.append(TherapeuticQuestion(
            question="이 생각과 다른 경험이나 사실은 없나요?",
            question_type=QuestionType.SOCRATIC,
            purpose=QuestionPurpose.COGNITIVE,
            timing=QuestionTiming.WORKING
        ))

        # 3. 대안적 해석
        questions.append(TherapeuticQuestion(
            question="이 상황을 다르게 해석할 수 있는 방법이 있을까요?",
            question_type=QuestionType.SOCRATIC,
            purpose=QuestionPurpose.INSIGHT,
            timing=QuestionTiming.WORKING
        ))

        # 4. 최악/최선/현실적
        questions.append(TherapeuticQuestion(
            question="최악의 결과, 최선의 결과, 가장 현실적인 결과는 각각 무엇일까요?",
            question_type=QuestionType.SOCRATIC,
            purpose=QuestionPurpose.COGNITIVE,
            timing=QuestionTiming.WORKING
        ))

        return questions


# =============================================================================
# 6. 반영 질문 (Reflective Questions)
# =============================================================================

class ReflectiveQuestionGenerator:
    """
    반영 질문 생성기

    자기 탐색과 자기 이해를 촉진하는 질문
    """

    TEMPLATES = {
        "feeling": [
            "그 순간 어떤 기분이 드셨어요?",
            "지금 이 이야기를 하면서 어떤 감정이 올라오나요?",
            "몸에서는 어떤 느낌이 있나요?",
            "그 감정을 색깔로 표현한다면요?",
        ],
        "meaning": [
            "그게 당신에게 어떤 의미인가요?",
            "이 일이 당신에게 중요한 이유는 뭘까요?",
            "이 상황이 당신에게 말해주는 것이 있다면요?",
        ],
        "values": [
            "이 상황에서 당신에게 가장 중요한 건 뭔가요?",
            "어떤 가치가 흔들리는 느낌인가요?",
            "당신이 진정으로 원하는 것은 무엇일까요?",
        ],
        "pattern": [
            "이런 상황이 전에도 있었나요?",
            "비슷한 패턴을 느끼시나요?",
            "언제부터 이런 느낌이 있었나요?",
        ],
        "self_understanding": [
            "이 경험을 통해 자신에 대해 알게 된 것이 있나요?",
            "당신은 어떤 사람인 것 같아요?",
            "가장 중요하게 여기는 것은 무엇인가요?",
        ],
        "needs": [
            "지금 가장 필요한 것은 무엇인가요?",
            "무엇이 채워지면 좋을 것 같아요?",
            "당신이 진정으로 원하는 것은요?",
        ]
    }

    def __init__(self):
        logger.info("ReflectiveQuestionGenerator initialized")

    def generate(self, context: QuestionContext,
                 category: str = "") -> List[TherapeuticQuestion]:
        """반영 질문 생성"""
        questions = []

        if category and category in self.TEMPLATES:
            templates = {category: self.TEMPLATES[category]}
        else:
            templates = self.TEMPLATES

        for cat, temps in templates.items():
            for template in temps[:2]:
                questions.append(TherapeuticQuestion(
                    question=template,
                    question_type=QuestionType.REFLECTIVE,
                    purpose=QuestionPurpose.INSIGHT,
                    timing=QuestionTiming.ANY,
                    context_tags=["reflective", cat]
                ))

        return questions


# =============================================================================
# 7. 대처 질문 (Coping Questions)
# =============================================================================

class CopingQuestionGenerator:
    """
    대처 질문 생성기

    힘든 상황에서 버텨온 방법과 자원을 탐색
    """

    TEMPLATES = [
        "지금까지 어떻게 버텨오셨어요?",
        "이 힘든 상황에서 당신을 지탱해준 것은 무엇인가요?",
        "최악의 순간에 무엇이 도움이 됐나요?",
        "그래도 여기까지 오신 건 대단한 거예요. 비결이 뭘까요?",
        "하루하루를 살아내게 하는 힘은 어디서 오나요?",
        "무너지지 않게 해준 것이 있다면요?",
        "이 상황에서도 지키고 있는 것이 있나요?",
        "당신만의 대처 방법이 있나요?",
        "위기의 순간에 떠오르는 것이 있나요?",
        "버틸 수 있게 하는 작은 것들이 있다면요?",
    ]

    STRENGTH_DISCOVERY = [
        "그렇게 할 수 있는 힘은 어디서 오나요?",
        "그게 쉽지 않은데, 어떻게 하셨어요?",
        "그 안에 있는 당신의 강점은 무엇일까요?",
        "다른 사람이라면 못했을 수도 있는데, 당신은 어떻게 해내셨어요?",
    ]

    def __init__(self):
        logger.info("CopingQuestionGenerator initialized")

    def generate(self, context: QuestionContext) -> List[TherapeuticQuestion]:
        """대처 질문 생성"""
        questions = []

        for template in self.TEMPLATES:
            questions.append(TherapeuticQuestion(
                question=template,
                question_type=QuestionType.COPING,
                purpose=QuestionPurpose.RESOURCE,
                timing=QuestionTiming.ANY,
                follow_up=self.STRENGTH_DISCOVERY[:2],
                context_tags=["coping", "strength"]
            ))

        return questions


# =============================================================================
# 통합 질문 시스템
# =============================================================================

class TherapeuticQuestionSystem:
    """
    통합 치료적 질문 시스템

    상황에 맞는 최적의 질문을 선택하고 생성
    """

    def __init__(self):
        self.circular = CircularQuestionGenerator()
        self.miracle = MiracleQuestionGenerator()
        self.scaling = ScalingQuestionGenerator()
        self.exception = ExceptionQuestionGenerator()
        self.socratic = SocraticQuestionGenerator()
        self.reflective = ReflectiveQuestionGenerator()
        self.coping = CopingQuestionGenerator()

        self.question_history: List[str] = []
        logger.info("TherapeuticQuestionSystem initialized")

    def recommend_questions(
        self,
        context: QuestionContext,
        message: str = "",
        max_questions: int = 5
    ) -> List[TherapeuticQuestion]:
        """
        맥락에 맞는 질문 추천

        Args:
            context: 질문 맥락
            message: 내담자 메시지
            max_questions: 최대 추천 개수

        Returns:
            List[TherapeuticQuestion]: 추천 질문들
        """
        all_questions = []

        # 1. 관계가 언급된 경우 - 순환 질문
        if context.relationship_mentioned:
            all_questions.extend(self.circular.generate(context))

        # 2. 변화 준비도가 높은 경우 - 기적/척도 질문
        if context.change_readiness > 0.5:
            all_questions.extend(self.miracle.generate(context))
            all_questions.extend(self.scaling.generate(context))

        # 3. 인지 왜곡이 감지된 경우 - 소크라테스식 질문
        if message:
            distortions = self.socratic.detect_distortion(message)
            if distortions:
                all_questions.extend(self.socratic.generate(context, message))

        # 4. 문제 상황 - 예외/대처 질문
        if context.problem_statement:
            all_questions.extend(self.exception.generate(context))
            all_questions.extend(self.coping.generate(context))

        # 5. 기본 - 반영 질문
        all_questions.extend(self.reflective.generate(context))

        # 중복 제거 및 이전 질문 필터링
        unique_questions = []
        seen = set()
        for q in all_questions:
            if q.question not in seen and q.question not in self.question_history:
                seen.add(q.question)
                unique_questions.append(q)

        # 점수 기반 정렬
        scored = self._score_questions(unique_questions, context)
        scored.sort(key=lambda x: x[1], reverse=True)

        result = [q for q, _ in scored[:max_questions]]

        # 히스토리 업데이트
        for q in result:
            self.question_history.append(q.question)
            if len(self.question_history) > 50:
                self.question_history.pop(0)

        return result

    def _score_questions(
        self,
        questions: List[TherapeuticQuestion],
        context: QuestionContext
    ) -> List[Tuple[TherapeuticQuestion, float]]:
        """질문 점수 계산"""
        scored = []

        for q in questions:
            score = q.effectiveness_score

            # 세션 단계 일치 보너스
            if q.timing == context.session_phase or q.timing == QuestionTiming.ANY:
                score += 0.1

            # 맥락 일치 보너스
            if context.topic and context.topic in str(q.context_tags):
                score += 0.1

            # 감정 기반 조정
            if context.emotion:
                if q.purpose == QuestionPurpose.EMOTION:
                    score += 0.15
                elif context.emotion in ["분노", "슬픔", "두려움"]:
                    if q.question_type == QuestionType.COPING:
                        score += 0.1

            scored.append((q, score))

        return scored

    def get_question_for_purpose(
        self,
        purpose: QuestionPurpose,
        context: QuestionContext,
        message: str = ""
    ) -> Optional[TherapeuticQuestion]:
        """특정 목적에 맞는 질문 반환"""
        questions = self.recommend_questions(context, message)

        for q in questions:
            if q.purpose == purpose:
                return q

        return questions[0] if questions else None

    def get_prompt_section(
        self,
        context: QuestionContext,
        message: str = ""
    ) -> str:
        """
        프롬프트에 삽입할 질문 가이드 섹션 생성
        """
        questions = self.recommend_questions(context, message, max_questions=5)

        section = """
## 치료적 질문 가이드

### 추천 질문
"""

        for i, q in enumerate(questions, 1):
            section += f"""
{i}. [{q.question_type.value}] {q.question}
   - 목적: {q.purpose.value}
   - 타이밍: {q.timing.value}
"""
            if q.follow_up:
                section += f"   - 후속 질문: {q.follow_up[0]}\n"

        # 인지 왜곡 감지 결과
        if message:
            distortions = self.socratic.detect_distortion(message)
            if distortions:
                section += "\n### 감지된 인지 패턴\n"
                for d in distortions:
                    section += f"- {d['name']}: \"{d['marker']}\" 발견\n"

        section += """
### 질문 팁
- 한 번에 하나의 질문만 하세요
- 내담자의 대답을 충분히 기다리세요
- 답변에 따라 후속 질문을 조절하세요
- 공감 후에 질문하면 더 효과적입니다
"""

        return section


# =============================================================================
# 편의 함수
# =============================================================================

_question_system = None

def get_question_system() -> TherapeuticQuestionSystem:
    """질문 시스템 싱글톤 반환"""
    global _question_system
    if _question_system is None:
        _question_system = TherapeuticQuestionSystem()
    return _question_system


def recommend_therapeutic_questions(
    message: str = "",
    topic: str = "",
    emotion: str = "",
    relationship: str = "",
    session_phase: str = "exploration"
) -> List[Dict[str, Any]]:
    """
    치료적 질문 추천

    Args:
        message: 내담자 메시지
        topic: 주제
        emotion: 감정
        relationship: 관계 대상
        session_phase: 세션 단계

    Returns:
        List[Dict]: 추천 질문 목록
    """
    system = get_question_system()

    phase_map = {
        "opening": QuestionTiming.OPENING,
        "exploration": QuestionTiming.EXPLORATION,
        "working": QuestionTiming.WORKING,
        "closing": QuestionTiming.CLOSING
    }

    context = QuestionContext(
        topic=topic,
        emotion=emotion,
        relationship_mentioned=relationship,
        session_phase=phase_map.get(session_phase, QuestionTiming.ANY)
    )

    questions = system.recommend_questions(context, message)

    return [
        {
            "question": q.question,
            "type": q.question_type.value,
            "purpose": q.purpose.value,
            "timing": q.timing.value,
            "follow_up": q.follow_up
        }
        for q in questions
    ]


def get_question_prompt_section(
    message: str = "",
    topic: str = "",
    emotion: str = "",
    session_phase: str = "exploration"
) -> str:
    """프롬프트용 질문 가이드 섹션"""
    system = get_question_system()

    phase_map = {
        "opening": QuestionTiming.OPENING,
        "exploration": QuestionTiming.EXPLORATION,
        "working": QuestionTiming.WORKING,
        "closing": QuestionTiming.CLOSING
    }

    context = QuestionContext(
        topic=topic,
        emotion=emotion,
        session_phase=phase_map.get(session_phase, QuestionTiming.ANY)
    )

    return system.get_prompt_section(context, message)
