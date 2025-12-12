"""
감정적 해악 방지 시스템 (Emotional Safety System)

의도치 않게 내담자에게 상처를 주는 표현 감지 및 방지:
1. 비난/판단적 표현 감지
2. 감정 최소화 표현 감지
3. 성급한 긍정/조언 감지
4. 비교 표현 감지
5. 무효화 표현 감지
6. 책임 전가 표현 감지
"""

from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass, field
import logging
import re

logger = logging.getLogger(__name__)


# =============================================================================
# 감정적 해악 유형 및 데이터 구조
# =============================================================================

class HarmType(Enum):
    """감정적 해악 유형"""
    JUDGMENT = "judgment"                   # 비난/판단
    MINIMIZATION = "minimization"           # 감정 최소화
    PREMATURE_POSITIVITY = "premature_positivity"  # 성급한 긍정
    COMPARISON = "comparison"               # 비교
    INVALIDATION = "invalidation"           # 무효화
    BLAME = "blame"                         # 책임 전가
    UNSOLICITED_ADVICE = "unsolicited_advice"  # 요청하지 않은 조언
    TOXIC_POSITIVITY = "toxic_positivity"   # 독성 긍정
    DISMISSIVENESS = "dismissiveness"       # 무시/경시
    RUSHING = "rushing"                     # 재촉


class HarmSeverity(Enum):
    """해악 심각도"""
    HIGH = "high"           # 즉시 수정 필요
    MEDIUM = "medium"       # 수정 권장
    LOW = "low"             # 주의


@dataclass
class HarmfulExpression:
    """해악 표현 정보"""
    harm_type: HarmType
    severity: HarmSeverity
    expression: str
    position: Tuple[int, int]
    why_harmful: str
    better_alternative: str


@dataclass
class EmotionalSafetyResult:
    """감정적 안전성 검사 결과"""
    is_safe: bool
    harmful_expressions: List[HarmfulExpression] = field(default_factory=list)
    risk_score: float = 0.0
    suggestions: List[str] = field(default_factory=list)
    corrected_response: Optional[str] = None


# =============================================================================
# 1. 비난/판단적 표현 감지
# =============================================================================

class JudgmentDetector:
    """
    비난/판단적 표현 감지

    내담자를 비난하거나 판단하는 표현 감지
    """

    # 직접적 비난
    DIRECT_JUDGMENT_PATTERNS = [
        (r"(왜|어째서)\s*(그랬|그러셨|그런\s*행동)", "왜 그랬어요?는 비난으로 들릴 수 있습니다"),
        (r"(잘못|실수).*?(하셨|했)", "잘못/실수 지적은 비난으로 느껴질 수 있습니다"),
        (r"(그러면|그럼)\s*안\s*(되|돼)", "안 된다는 표현은 판단적입니다"),
        (r"(당연히|당연한|마땅히)", "당연하다는 표현은 판단을 내포합니다"),
    ]

    # 암시적 판단
    IMPLICIT_JUDGMENT_PATTERNS = [
        (r"(보통|일반적으로|대부분).*?(안\s*그래|아닌데)", "일반화로 비교/판단하는 표현입니다"),
        (r"(생각|마음)이\s*좀\s*(이상|특이|독특)", "생각이 이상하다는 암시입니다"),
        (r"(좀|조금)\s*(과하|심하)", "과하다는 표현은 판단적입니다"),
    ]

    # 도덕적 판단
    MORAL_JUDGMENT_PATTERNS = [
        (r"(옳|그름|옳고\s*그름)", "도덕적 판단 표현입니다"),
        (r"(나쁜|나쁘게|못된)", "도덕적 평가 표현입니다"),
        (r"(이기적|무책임|게으른)", "성격 비난 표현입니다"),
    ]

    # 대안 표현
    ALTERNATIVES = {
        "왜 그랬": "어떤 마음에서 그러셨는지 궁금해요",
        "잘못": "그 상황에서 어려우셨겠어요",
        "안 돼": "다른 방법도 생각해 볼 수 있을까요?",
        "당연히": "그럴 수 있어요",
    }

    def __init__(self):
        self._compile_patterns()
        logger.info("JudgmentDetector initialized")

    def _compile_patterns(self):
        self.patterns = []
        for pattern, explanation in self.DIRECT_JUDGMENT_PATTERNS:
            self.patterns.append((re.compile(pattern), explanation, HarmSeverity.HIGH))
        for pattern, explanation in self.IMPLICIT_JUDGMENT_PATTERNS:
            self.patterns.append((re.compile(pattern), explanation, HarmSeverity.MEDIUM))
        for pattern, explanation in self.MORAL_JUDGMENT_PATTERNS:
            self.patterns.append((re.compile(pattern), explanation, HarmSeverity.HIGH))

    def detect(self, response: str) -> List[HarmfulExpression]:
        """비난/판단 표현 감지"""
        harmful = []

        for pattern, explanation, severity in self.patterns:
            matches = pattern.finditer(response)
            for match in matches:
                # 대안 찾기
                alternative = self._find_alternative(match.group())

                harmful.append(HarmfulExpression(
                    harm_type=HarmType.JUDGMENT,
                    severity=severity,
                    expression=match.group(),
                    position=(match.start(), match.end()),
                    why_harmful=explanation,
                    better_alternative=alternative
                ))

        return harmful

    def _find_alternative(self, expression: str) -> str:
        """대안 표현 찾기"""
        for key, alt in self.ALTERNATIVES.items():
            if key in expression:
                return alt
        return "판단 없이 있는 그대로 반영해 보세요"


# =============================================================================
# 2. 감정 최소화 표현 감지
# =============================================================================

class MinimizationDetector:
    """
    감정 최소화 표현 감지

    내담자의 감정을 축소하거나 무시하는 표현 감지
    """

    # 직접적 최소화
    DIRECT_MINIMIZATION = [
        (r"(별거|별\s*거)\s*(아니|아닐)", "별거 아니다는 감정을 축소합니다"),
        (r"(그\s*정도|그까짓)", "그 정도는 감정을 경시합니다"),
        (r"(뭐|뭘)\s*(그렇게|그리)", "뭘 그렇게는 반응을 비난합니다"),
        (r"너무\s*(예민|민감)", "예민하다는 표현은 감정을 부정합니다"),
        (r"(대수|대단한\s*일)", "대수롭지 않다는 표현입니다"),
    ]

    # 비교를 통한 최소화
    COMPARATIVE_MINIMIZATION = [
        (r"(더\s*힘든|더\s*심한)\s*(사람|경우)", "더 힘든 사람과 비교는 감정을 최소화합니다"),
        (r"(세상에|다른\s*사람).*?(더|훨씬)", "타인과 비교로 감정을 축소합니다"),
        (r"(나이|어린|젊)", "나이를 이유로 감정을 축소합니다"),
    ]

    # 시간을 이용한 최소화
    TIME_BASED_MINIMIZATION = [
        (r"(시간이\s*지나면|곧|금방)", "시간이 지나면 괜찮다는 표현입니다"),
        (r"(잊어|잊으면|잊혀)", "잊으라는 표현은 감정을 무시합니다"),
        (r"(다\s*지나간|이미\s*끝난)", "지나갔다는 표현은 현재 감정을 무시합니다"),
    ]

    # 대안 표현
    ALTERNATIVES = {
        "별거 아니": "그 마음이 힘드셨겠어요",
        "그 정도": "당신에게는 중요한 일이었군요",
        "뭘 그렇게": "그만큼 마음이 아프셨네요",
        "예민": "감정이 예민해지셨군요, 이유가 있을 거예요",
        "시간이 지나면": "지금 이 순간이 힘드시죠",
        "잊어": "쉽게 잊히지 않는 마음이시군요",
    }

    def __init__(self):
        self._compile_patterns()
        logger.info("MinimizationDetector initialized")

    def _compile_patterns(self):
        self.patterns = []
        for pattern, explanation in self.DIRECT_MINIMIZATION:
            self.patterns.append((re.compile(pattern), explanation, HarmSeverity.HIGH))
        for pattern, explanation in self.COMPARATIVE_MINIMIZATION:
            self.patterns.append((re.compile(pattern), explanation, HarmSeverity.MEDIUM))
        for pattern, explanation in self.TIME_BASED_MINIMIZATION:
            self.patterns.append((re.compile(pattern), explanation, HarmSeverity.MEDIUM))

    def detect(self, response: str) -> List[HarmfulExpression]:
        """감정 최소화 표현 감지"""
        harmful = []

        for pattern, explanation, severity in self.patterns:
            matches = pattern.finditer(response)
            for match in matches:
                alternative = self._find_alternative(match.group())

                harmful.append(HarmfulExpression(
                    harm_type=HarmType.MINIMIZATION,
                    severity=severity,
                    expression=match.group(),
                    position=(match.start(), match.end()),
                    why_harmful=explanation,
                    better_alternative=alternative
                ))

        return harmful

    def _find_alternative(self, expression: str) -> str:
        for key, alt in self.ALTERNATIVES.items():
            if key in expression:
                return alt
        return "감정을 있는 그대로 인정해 주세요"


# =============================================================================
# 3. 성급한 긍정/조언 감지
# =============================================================================

class PrematurePositivityDetector:
    """
    성급한 긍정/조언 감지

    충분한 공감 없이 긍정적 전환이나 조언을 하는 것 감지
    """

    # 성급한 긍정
    PREMATURE_POSITIVITY_PATTERNS = [
        (r"(다\s*잘\s*될|잘\s*될\s*거)", "다 잘 될 거라는 말은 현재 고통을 외면할 수 있습니다"),
        (r"(괜찮아|괜찮을\s*거)", "괜찮을 거라는 말은 감정을 서두르게 합니다"),
        (r"(힘내|기운\s*내|파이팅)", "힘내라는 말은 부담이 될 수 있습니다"),
        (r"(긍정적|긍정적으로)", "긍정적으로 생각하라는 요구입니다"),
        (r"(좋은\s*쪽으로|밝은\s*면)", "밝은 면을 보라는 것은 고통을 무시합니다"),
    ]

    # 성급한 해결책
    PREMATURE_SOLUTION_PATTERNS = [
        (r"(이렇게\s*하면|이렇게\s*해보)", "충분한 탐색 없이 해결책 제시"),
        (r"(제\s*생각에는|제가\s*보기에).*?(하면)", "조언이 성급할 수 있습니다"),
        (r"(쉬운|간단한)\s*(방법|해결)", "쉬운 해결책이 있다는 암시입니다"),
    ]

    # 독성 긍정
    TOXIC_POSITIVITY_PATTERNS = [
        (r"(나쁜\s*일|나쁜\s*것).*?(없|아니)", "나쁜 일이 없다는 것은 현실 부정입니다"),
        (r"(감사|고마움).*?(찾|느끼)", "감사를 찾으라는 요구입니다"),
        (r"(긍정|positive).*?(해야|필요)", "긍정해야 한다는 압박입니다"),
        (r"(웃으면|웃어)", "웃으라는 요구입니다"),
    ]

    # 대안 표현
    ALTERNATIVES = {
        "잘 될": "지금 이 순간이 힘드시죠",
        "괜찮": "지금은 괜찮지 않아도 돼요",
        "힘내": "힘드실 때 힘내라는 말이 부담되시죠",
        "긍정적": "지금은 긍정적이지 않아도 괜찮아요",
        "해결": "먼저 마음을 좀 더 들어볼까요?",
    }

    def __init__(self):
        self._compile_patterns()
        logger.info("PrematurePositivityDetector initialized")

    def _compile_patterns(self):
        self.patterns = []
        for pattern, explanation in self.PREMATURE_POSITIVITY_PATTERNS:
            self.patterns.append((re.compile(pattern), explanation, HarmSeverity.MEDIUM))
        for pattern, explanation in self.PREMATURE_SOLUTION_PATTERNS:
            self.patterns.append((re.compile(pattern), explanation, HarmSeverity.LOW))
        for pattern, explanation in self.TOXIC_POSITIVITY_PATTERNS:
            self.patterns.append((re.compile(pattern), explanation, HarmSeverity.HIGH))

    def detect(self, response: str) -> List[HarmfulExpression]:
        """성급한 긍정/조언 감지"""
        harmful = []

        for pattern, explanation, severity in self.patterns:
            matches = pattern.finditer(response)
            for match in matches:
                alternative = self._find_alternative(match.group())

                harmful.append(HarmfulExpression(
                    harm_type=HarmType.PREMATURE_POSITIVITY,
                    severity=severity,
                    expression=match.group(),
                    position=(match.start(), match.end()),
                    why_harmful=explanation,
                    better_alternative=alternative
                ))

        return harmful

    def _find_alternative(self, expression: str) -> str:
        for key, alt in self.ALTERNATIVES.items():
            if key in expression:
                return alt
        return "먼저 충분히 공감한 후에 전환해 보세요"


# =============================================================================
# 4. 비교 표현 감지
# =============================================================================

class ComparisonDetector:
    """
    비교 표현 감지

    다른 사람과 비교하는 표현 감지
    """

    # 타인과의 비교
    COMPARISON_PATTERNS = [
        (r"(다른\s*사람|남들).*?(도|은|는)", "다른 사람과 비교는 감정을 무효화합니다"),
        (r"(누구|모두|everyone).*?(다|도)", "모두가 겪는다는 비교입니다"),
        (r"(더\s*힘든|더\s*어려운).*?(사람|상황)", "더 힘든 상황과 비교입니다"),
        (r"(저도|나도).*?(그랬|비슷|같은)", "자기 경험과 비교입니다"),
        (r"(세상에|주변에).*?(많|수두룩)", "흔하다는 비교입니다"),
    ]

    # 과거/이상적 자신과 비교
    SELF_COMPARISON_PATTERNS = [
        (r"(예전|전에|옛날).*?(잘|더)", "과거의 자신과 비교입니다"),
        (r"(할\s*수\s*있|능력|잠재력)", "이상적 자신과 비교할 수 있습니다"),
    ]

    # 대안 표현
    ALTERNATIVES = {
        "다른 사람": "당신의 경험은 당신만의 것이에요",
        "더 힘든": "지금 당신의 고통이 중요해요",
        "저도": "비슷한 경험이 있지만, 지금은 당신 이야기에 집중할게요",
    }

    def __init__(self):
        self._compile_patterns()
        logger.info("ComparisonDetector initialized")

    def _compile_patterns(self):
        self.patterns = []
        for pattern, explanation in self.COMPARISON_PATTERNS:
            self.patterns.append((re.compile(pattern), explanation, HarmSeverity.MEDIUM))
        for pattern, explanation in self.SELF_COMPARISON_PATTERNS:
            self.patterns.append((re.compile(pattern), explanation, HarmSeverity.LOW))

    def detect(self, response: str) -> List[HarmfulExpression]:
        """비교 표현 감지"""
        harmful = []

        for pattern, explanation, severity in self.patterns:
            matches = pattern.finditer(response)
            for match in matches:
                alternative = self._find_alternative(match.group())

                harmful.append(HarmfulExpression(
                    harm_type=HarmType.COMPARISON,
                    severity=severity,
                    expression=match.group(),
                    position=(match.start(), match.end()),
                    why_harmful=explanation,
                    better_alternative=alternative
                ))

        return harmful

    def _find_alternative(self, expression: str) -> str:
        for key, alt in self.ALTERNATIVES.items():
            if key in expression:
                return alt
        return "비교 없이 그 사람의 경험 자체에 집중해 보세요"


# =============================================================================
# 5. 무효화 표현 감지
# =============================================================================

class InvalidationDetector:
    """
    무효화 표현 감지

    내담자의 경험이나 감정을 부정/무효화하는 표현 감지
    """

    # 감정 무효화
    EMOTION_INVALIDATION = [
        (r"(그런\s*감정|그렇게\s*느끼).*?(안|필요\s*없)", "감정을 느끼지 말라는 무효화입니다"),
        (r"(화|슬프|불안).*?(내면|낼\s*필요)", "감정 표현을 제한합니다"),
        (r"(너무|지나치게).*?(생각|걱정)", "생각이 과하다는 무효화입니다"),
    ]

    # 경험 무효화
    EXPERIENCE_INVALIDATION = [
        (r"(그건|그거).*?(아니|아닐)", "경험을 부정합니다"),
        (r"(오해|착각|잘못\s*생각)", "인식이 틀렸다는 무효화입니다"),
        (r"(실제로|사실은|진짜로).*?(아니|않)", "실제가 아니라는 무효화입니다"),
    ]

    # 관점 무효화
    PERSPECTIVE_INVALIDATION = [
        (r"(그렇게\s*볼|그렇게\s*생각).*?(안|아니)", "관점을 부정합니다"),
        (r"(다르게|바꿔서).*?(생각|봐야)", "관점을 바꾸라는 요구입니다"),
    ]

    # 대안 표현
    ALTERNATIVES = {
        "그런 감정": "그런 감정이 드시는군요",
        "오해": "그렇게 느끼셨군요",
        "진짜": "그게 당신에게는 진짜 경험이에요",
        "다르게 생각": "그렇게 보시는군요",
    }

    def __init__(self):
        self._compile_patterns()
        logger.info("InvalidationDetector initialized")

    def _compile_patterns(self):
        self.patterns = []
        for pattern, explanation in self.EMOTION_INVALIDATION:
            self.patterns.append((re.compile(pattern), explanation, HarmSeverity.HIGH))
        for pattern, explanation in self.EXPERIENCE_INVALIDATION:
            self.patterns.append((re.compile(pattern), explanation, HarmSeverity.HIGH))
        for pattern, explanation in self.PERSPECTIVE_INVALIDATION:
            self.patterns.append((re.compile(pattern), explanation, HarmSeverity.MEDIUM))

    def detect(self, response: str) -> List[HarmfulExpression]:
        """무효화 표현 감지"""
        harmful = []

        for pattern, explanation, severity in self.patterns:
            matches = pattern.finditer(response)
            for match in matches:
                alternative = self._find_alternative(match.group())

                harmful.append(HarmfulExpression(
                    harm_type=HarmType.INVALIDATION,
                    severity=severity,
                    expression=match.group(),
                    position=(match.start(), match.end()),
                    why_harmful=explanation,
                    better_alternative=alternative
                ))

        return harmful

    def _find_alternative(self, expression: str) -> str:
        for key, alt in self.ALTERNATIVES.items():
            if key in expression:
                return alt
        return "경험과 감정을 있는 그대로 인정해 주세요"


# =============================================================================
# 6. 책임 전가 표현 감지
# =============================================================================

class BlameDetector:
    """
    책임 전가 표현 감지

    내담자에게 책임을 전가하거나 비난하는 표현 감지
    """

    # 직접적 책임 전가
    DIRECT_BLAME_PATTERNS = [
        (r"(본인|당신).*?(탓|책임|잘못)", "책임을 전가하는 표현입니다"),
        (r"(그러니까|그래서).*?(그런|이런)\s*일", "인과관계로 비난합니다"),
        (r"(스스로|자기가)", "자초했다는 암시입니다"),
    ]

    # 암시적 책임 전가
    IMPLICIT_BLAME_PATTERNS = [
        (r"(왜|어째서).*?(안|못)", "왜 못했냐는 비난입니다"),
        (r"(그때|그랬으면).*?(됐을|않았을)", "다르게 했으면 됐다는 비난입니다"),
        (r"(생각|판단).*?(없이|안\s*하고)", "생각이 없다는 비난입니다"),
    ]

    # 대안 표현
    ALTERNATIVES = {
        "탓": "그 상황에서 최선을 다하셨을 거예요",
        "잘못": "힘든 상황이었네요",
        "왜": "어떤 상황이었는지 이해하고 싶어요",
        "스스로": "여러 요인이 있었을 거예요",
    }

    def __init__(self):
        self._compile_patterns()
        logger.info("BlameDetector initialized")

    def _compile_patterns(self):
        self.patterns = []
        for pattern, explanation in self.DIRECT_BLAME_PATTERNS:
            self.patterns.append((re.compile(pattern), explanation, HarmSeverity.HIGH))
        for pattern, explanation in self.IMPLICIT_BLAME_PATTERNS:
            self.patterns.append((re.compile(pattern), explanation, HarmSeverity.MEDIUM))

    def detect(self, response: str) -> List[HarmfulExpression]:
        """책임 전가 표현 감지"""
        harmful = []

        for pattern, explanation, severity in self.patterns:
            matches = pattern.finditer(response)
            for match in matches:
                alternative = self._find_alternative(match.group())

                harmful.append(HarmfulExpression(
                    harm_type=HarmType.BLAME,
                    severity=severity,
                    expression=match.group(),
                    position=(match.start(), match.end()),
                    why_harmful=explanation,
                    better_alternative=alternative
                ))

        return harmful

    def _find_alternative(self, expression: str) -> str:
        for key, alt in self.ALTERNATIVES.items():
            if key in expression:
                return alt
        return "비난 없이 상황을 이해하려 해보세요"


# =============================================================================
# 7. 재촉/급하게 하기 감지
# =============================================================================

class RushingDetector:
    """
    재촉 표현 감지

    내담자를 급하게 하거나 재촉하는 표현 감지
    """

    # 재촉 표현
    RUSHING_PATTERNS = [
        (r"(빨리|어서|얼른)", "서두르라는 재촉입니다"),
        (r"(언제|언제까지).*?(할|하실)", "시간 압박을 주는 표현입니다"),
        (r"(이제|이젠).*?(해야|하셔야)", "이제는 해야 한다는 압박입니다"),
        (r"(그만|멈추고).*?(해|하)", "현재를 멈추라는 요구입니다"),
        (r"(다음|넘어가|진행)", "빨리 넘어가라는 재촉입니다"),
    ]

    # 대안 표현
    ALTERNATIVES = {
        "빨리": "준비되시면 천천히 해보셔도 돼요",
        "언제": "원하실 때 해보시면 돼요",
        "이제": "당신의 속도대로 하시면 돼요",
        "그만": "필요하시다면 더 이야기해도 돼요",
    }

    def __init__(self):
        self._compile_patterns()
        logger.info("RushingDetector initialized")

    def _compile_patterns(self):
        self.patterns = []
        for pattern, explanation in self.RUSHING_PATTERNS:
            self.patterns.append((re.compile(pattern), explanation, HarmSeverity.LOW))

    def detect(self, response: str) -> List[HarmfulExpression]:
        """재촉 표현 감지"""
        harmful = []

        for pattern, explanation, severity in self.patterns:
            matches = pattern.finditer(response)
            for match in matches:
                alternative = self._find_alternative(match.group())

                harmful.append(HarmfulExpression(
                    harm_type=HarmType.RUSHING,
                    severity=severity,
                    expression=match.group(),
                    position=(match.start(), match.end()),
                    why_harmful=explanation,
                    better_alternative=alternative
                ))

        return harmful

    def _find_alternative(self, expression: str) -> str:
        for key, alt in self.ALTERNATIVES.items():
            if key in expression:
                return alt
        return "내담자의 속도를 존중해 주세요"


# =============================================================================
# 통합 감정적 안전 시스템
# =============================================================================

class EmotionalSafetySystem:
    """
    통합 감정적 안전 시스템

    모든 해악 유형을 통합하여 검사
    """

    def __init__(self):
        self.detectors = {
            HarmType.JUDGMENT: JudgmentDetector(),
            HarmType.MINIMIZATION: MinimizationDetector(),
            HarmType.PREMATURE_POSITIVITY: PrematurePositivityDetector(),
            HarmType.COMPARISON: ComparisonDetector(),
            HarmType.INVALIDATION: InvalidationDetector(),
            HarmType.BLAME: BlameDetector(),
            HarmType.RUSHING: RushingDetector(),
        }

        # 심각도별 점수
        self.severity_scores = {
            HarmSeverity.HIGH: 30,
            HarmSeverity.MEDIUM: 15,
            HarmSeverity.LOW: 5,
        }

        logger.info("EmotionalSafetySystem initialized")

    def check_response(self, response: str) -> EmotionalSafetyResult:
        """
        응답의 감정적 안전성 검사

        Args:
            response: 검사할 응답

        Returns:
            EmotionalSafetyResult: 검사 결과
        """
        all_harmful = []

        # 모든 감지기 실행
        for harm_type, detector in self.detectors.items():
            harmful = detector.detect(response)
            all_harmful.extend(harmful)

        # 위험 점수 계산
        risk_score = sum(
            self.severity_scores[h.severity] for h in all_harmful
        )
        risk_score = min(100.0, risk_score)

        # 안전 여부
        is_safe = len([h for h in all_harmful if h.severity == HarmSeverity.HIGH]) == 0

        # 제안 생성
        suggestions = self._generate_suggestions(all_harmful)

        # 결과 생성
        result = EmotionalSafetyResult(
            is_safe=is_safe,
            harmful_expressions=all_harmful,
            risk_score=risk_score,
            suggestions=suggestions
        )

        # 수정 응답 생성
        if all_harmful:
            result.corrected_response = self._generate_corrected_response(response, all_harmful)

        logger.info(f"Emotional safety check: {len(all_harmful)} issues, "
                   f"risk_score={risk_score:.1f}, is_safe={is_safe}")

        return result

    def _generate_suggestions(self, harmful: List[HarmfulExpression]) -> List[str]:
        """개선 제안 생성"""
        suggestions = []

        # 유형별 그룹화
        by_type = {}
        for h in harmful:
            if h.harm_type not in by_type:
                by_type[h.harm_type] = []
            by_type[h.harm_type].append(h)

        # 유형별 제안
        type_suggestions = {
            HarmType.JUDGMENT: "판단 없이 있는 그대로 반영해 보세요",
            HarmType.MINIMIZATION: "감정을 축소하지 말고 인정해 주세요",
            HarmType.PREMATURE_POSITIVITY: "충분히 공감한 후에 긍정적 전환을 해보세요",
            HarmType.COMPARISON: "비교 없이 그 사람의 경험에 집중해 보세요",
            HarmType.INVALIDATION: "경험과 감정을 부정하지 말고 인정해 주세요",
            HarmType.BLAME: "책임을 묻지 말고 상황을 이해하려 해보세요",
            HarmType.RUSHING: "내담자의 속도를 존중해 주세요",
        }

        for harm_type in by_type.keys():
            suggestions.append(type_suggestions.get(harm_type, ""))

        return suggestions

    def _generate_corrected_response(
        self,
        response: str,
        harmful: List[HarmfulExpression]
    ) -> str:
        """수정된 응답 생성"""
        corrected = response

        # 위치 역순 정렬 (뒤에서부터 수정)
        sorted_harmful = sorted(harmful, key=lambda h: h.position[0], reverse=True)

        for h in sorted_harmful:
            if h.severity == HarmSeverity.HIGH:
                start, end = h.position
                # 대안으로 교체
                corrected = corrected[:start] + f"[{h.better_alternative}]" + corrected[end:]

        return corrected

    def get_prompt_section(self) -> str:
        """프롬프트에 삽입할 감정적 안전 가이드"""
        return """
## 감정적 안전 가이드 - 해로운 표현 피하기

### 절대 피할 표현 (HIGH)

#### 비난/판단
❌ "왜 그랬어요?" → ✅ "어떤 마음에서 그러셨는지 궁금해요"
❌ "잘못하셨네요" → ✅ "힘든 상황이었겠어요"
❌ "당연히 그래야죠" → ✅ "그럴 수 있어요"

#### 감정 최소화
❌ "별거 아니에요" → ✅ "그 마음이 힘드셨겠어요"
❌ "그 정도는..." → ✅ "당신에게는 중요한 일이었군요"
❌ "너무 예민해요" → ✅ "감정이 예민해지셨군요"

#### 무효화
❌ "그건 아니에요" → ✅ "그렇게 느끼셨군요"
❌ "오해하신 거예요" → ✅ "그렇게 받아들이셨군요"

### 주의할 표현 (MEDIUM)

#### 성급한 긍정
❌ "다 잘 될 거예요" → ✅ "지금 이 순간이 힘드시죠"
❌ "힘내세요" → ✅ "지금 많이 힘드시겠어요"
❌ "긍정적으로 생각해요" → ✅ "지금은 그러기 어려우시죠"

#### 비교
❌ "다른 사람들도..." → ✅ "당신의 경험은 당신만의 것이에요"
❌ "더 힘든 사람도..." → ✅ "지금 당신의 고통이 중요해요"

#### 책임 전가
❌ "본인 탓이에요" → ✅ "그 상황에서 최선을 다하셨을 거예요"

### 안전한 표현 원칙
1. **있는 그대로 반영**: "~하셨군요", "~한 마음이시군요"
2. **감정 인정**: "그런 감정이 드시는 게 자연스러워요"
3. **판단 유보**: 사실 확인보다 감정에 먼저 반응
4. **속도 존중**: "천천히 하셔도 돼요"
5. **비교 금지**: 다른 사람, 과거와 비교하지 않기
"""


# =============================================================================
# 편의 함수
# =============================================================================

_safety_system: Optional[EmotionalSafetySystem] = None


def get_emotional_safety_system() -> EmotionalSafetySystem:
    """감정적 안전 시스템 싱글톤 반환"""
    global _safety_system
    if _safety_system is None:
        _safety_system = EmotionalSafetySystem()
    return _safety_system


def check_emotional_safety(response: str) -> EmotionalSafetyResult:
    """응답의 감정적 안전성 빠른 검사"""
    system = get_emotional_safety_system()
    return system.check_response(response)


def get_emotional_safety_prompt_section() -> str:
    """프롬프트용 감정적 안전 섹션"""
    system = get_emotional_safety_system()
    return system.get_prompt_section()


def is_emotionally_safe(response: str) -> bool:
    """응답이 감정적으로 안전한지 빠른 체크"""
    result = check_emotional_safety(response)
    return result.is_safe
