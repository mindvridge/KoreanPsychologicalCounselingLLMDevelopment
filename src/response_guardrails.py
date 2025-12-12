"""
응답 가드레일 시스템 (Response Guardrails System)

AI 상담 챗봇의 부적절한 응답을 방지하는 다층 가드레일:
1. 의학적/법적 조언 차단
2. 위험 정보 제공 방지
3. 지시적 표현 감지
4. 진단명 언급 방지
5. 중대 결정 조언 차단
6. 경계 위반 감지
"""

from typing import Dict, List, Optional, Tuple, Any, Set
from enum import Enum
from dataclasses import dataclass, field
import logging
import re

logger = logging.getLogger(__name__)


# =============================================================================
# 가드레일 유형 및 데이터 구조
# =============================================================================

class GuardrailType(Enum):
    """가드레일 유형"""
    MEDICAL_ADVICE = "medical_advice"           # 의학적 조언
    LEGAL_ADVICE = "legal_advice"               # 법적 조언
    HARMFUL_INFO = "harmful_info"               # 유해 정보
    DIRECTIVE_LANGUAGE = "directive_language"   # 지시적 표현
    DIAGNOSIS_MENTION = "diagnosis_mention"     # 진단명 언급
    MAJOR_DECISION = "major_decision"           # 중대 결정 조언
    BOUNDARY_VIOLATION = "boundary_violation"   # 경계 위반
    PROMISE_MAKING = "promise_making"           # 부적절한 약속
    FALSE_HOPE = "false_hope"                   # 거짓 희망
    MINIMIZATION = "minimization"               # 감정 최소화


class Severity(Enum):
    """위반 심각도"""
    CRITICAL = "critical"   # 즉시 차단 및 수정 필요
    HIGH = "high"           # 차단 권장
    MEDIUM = "medium"       # 경고 및 수정 권장
    LOW = "low"             # 주의


@dataclass
class GuardrailViolation:
    """가드레일 위반 정보"""
    guardrail_type: GuardrailType
    severity: Severity
    matched_pattern: str
    matched_text: str
    position: Tuple[int, int]  # (start, end)
    suggestion: str
    explanation: str


@dataclass
class GuardrailResult:
    """가드레일 검사 결과"""
    is_safe: bool
    violations: List[GuardrailViolation] = field(default_factory=list)
    risk_score: float = 0.0  # 0-100
    blocked: bool = False
    corrected_response: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

    @property
    def critical_violations(self) -> List[GuardrailViolation]:
        return [v for v in self.violations if v.severity == Severity.CRITICAL]

    @property
    def high_violations(self) -> List[GuardrailViolation]:
        return [v for v in self.violations if v.severity == Severity.HIGH]


# =============================================================================
# 1. 의학적 조언 가드레일
# =============================================================================

class MedicalAdviceGuardrail:
    """
    의학적 조언 감지 및 차단

    AI가 의학적 조언을 하지 않도록 방지
    """

    # 의학적 조언 패턴
    MEDICAL_ADVICE_PATTERNS = {
        "medication": {
            "patterns": [
                r"약을?\s*(먹|복용|드시|섭취)",
                r"(항우울제|항불안제|수면제|안정제)를?\s*(추천|권장|드려요)",
                r"(처방|투약|복약).*?(하세요|해보세요|권해)",
                r"약\s*용량",
                r"(mg|밀리그램).*?(늘리|줄이|조절)",
            ],
            "severity": Severity.CRITICAL,
            "explanation": "약물 관련 조언은 의료 전문가만 할 수 있습니다."
        },
        "diagnosis_suggestion": {
            "patterns": [
                r"(우울증|불안장애|공황장애|PTSD|조현병|양극성).*?(있으신|이신|같아요|보여요)",
                r"(~증|~장애).*?(의심|추정|가능성)",
                r"증상으로\s*봐서는?\s*~",
                r"(진단|검사).*?(필요|받으셔야)",
            ],
            "severity": Severity.HIGH,
            "explanation": "진단은 전문 의료인만 할 수 있습니다."
        },
        "treatment_advice": {
            "patterns": [
                r"치료.*?(방법|받으세요|해보세요)",
                r"(입원|통원).*?(하세요|권해|필요)",
                r"(정신과|신경과|심리상담).*?(가세요|방문)",
            ],
            "severity": Severity.MEDIUM,
            "explanation": "치료 결정은 전문가 상담 후 이루어져야 합니다."
        }
    }

    # 안전한 대안 표현
    SAFE_ALTERNATIVES = {
        "medication": "약물에 대해서는 정신건강의학과 전문의와 상담하시는 것이 좋겠어요.",
        "diagnosis": "정확한 상태 파악을 위해 전문가와 상담해 보시는 것을 권해드려요.",
        "treatment": "다양한 도움 방법이 있는데, 전문가와 함께 맞는 방법을 찾아보시면 어떨까요?"
    }

    def __init__(self):
        self._compile_patterns()
        logger.info("MedicalAdviceGuardrail initialized")

    def _compile_patterns(self):
        """패턴 컴파일"""
        self.compiled_patterns = {}
        for category, info in self.MEDICAL_ADVICE_PATTERNS.items():
            self.compiled_patterns[category] = {
                "patterns": [re.compile(p, re.IGNORECASE) for p in info["patterns"]],
                "severity": info["severity"],
                "explanation": info["explanation"]
            }

    def check(self, response: str) -> List[GuardrailViolation]:
        """의학적 조언 검사"""
        violations = []

        for category, info in self.compiled_patterns.items():
            for pattern in info["patterns"]:
                matches = pattern.finditer(response)
                for match in matches:
                    violations.append(GuardrailViolation(
                        guardrail_type=GuardrailType.MEDICAL_ADVICE,
                        severity=info["severity"],
                        matched_pattern=pattern.pattern,
                        matched_text=match.group(),
                        position=(match.start(), match.end()),
                        suggestion=self.SAFE_ALTERNATIVES.get(
                            category.split("_")[0],
                            "전문가와 상담을 권해드립니다."
                        ),
                        explanation=info["explanation"]
                    ))

        return violations


# =============================================================================
# 2. 법적 조언 가드레일
# =============================================================================

class LegalAdviceGuardrail:
    """
    법적 조언 감지 및 차단
    """

    LEGAL_ADVICE_PATTERNS = {
        "legal_action": {
            "patterns": [
                r"(소송|고소|고발).*?(하세요|해야|권해)",
                r"(변호사|법률).*?(상담|선임|의뢰).*?(하세요|해야)",
                r"법적.*?(조치|대응).*?(하세요|취하)",
                r"(합의|배상|보상).*?(받으세요|요구)",
            ],
            "severity": Severity.HIGH,
            "explanation": "법적 조언은 법률 전문가만 할 수 있습니다."
        },
        "legal_interpretation": {
            "patterns": [
                r"(법적으로|법률상).*?(~입니다|~이에요|~됩니다)",
                r"(위법|불법|합법).*?(이에요|입니다|해당)",
                r"(권리|의무)가?\s*(있|없).*?(습니다|어요)",
            ],
            "severity": Severity.MEDIUM,
            "explanation": "법률 해석은 법률 전문가의 영역입니다."
        }
    }

    SAFE_ALTERNATIVE = "법적인 부분은 법률 전문가나 법률구조공단(132)에 상담해 보시면 정확한 안내를 받으실 수 있어요."

    def __init__(self):
        self._compile_patterns()
        logger.info("LegalAdviceGuardrail initialized")

    def _compile_patterns(self):
        self.compiled_patterns = {}
        for category, info in self.LEGAL_ADVICE_PATTERNS.items():
            self.compiled_patterns[category] = {
                "patterns": [re.compile(p, re.IGNORECASE) for p in info["patterns"]],
                "severity": info["severity"],
                "explanation": info["explanation"]
            }

    def check(self, response: str) -> List[GuardrailViolation]:
        violations = []

        for category, info in self.compiled_patterns.items():
            for pattern in info["patterns"]:
                matches = pattern.finditer(response)
                for match in matches:
                    violations.append(GuardrailViolation(
                        guardrail_type=GuardrailType.LEGAL_ADVICE,
                        severity=info["severity"],
                        matched_pattern=pattern.pattern,
                        matched_text=match.group(),
                        position=(match.start(), match.end()),
                        suggestion=self.SAFE_ALTERNATIVE,
                        explanation=info["explanation"]
                    ))

        return violations


# =============================================================================
# 3. 유해 정보 가드레일
# =============================================================================

class HarmfulInfoGuardrail:
    """
    유해 정보 제공 방지

    자해/자살 방법, 위험한 행동 방법 등 차단
    """

    # 절대 차단 (CRITICAL)
    BLOCKED_PATTERNS = {
        "self_harm_methods": {
            "patterns": [
                r"(자해|자살).*?(방법|수단|도구)",
                r"(손목|목|약).*?(긋|그|삼키|먹)",
                r"(높은\s*곳|다리|옥상).*?(뛰어|올라)",
                r"(약물|독|가스).*?(치사량|과다)",
                r"어떻게\s*(죽|자살)",
            ],
            "severity": Severity.CRITICAL,
            "explanation": "자해/자살 방법에 대한 정보는 절대 제공할 수 없습니다."
        },
        "violence_methods": {
            "patterns": [
                r"(폭행|공격|해치).*?(방법|수단)",
                r"(무기|칼|총).*?(사용법|구하|구입)",
                r"(복수|보복).*?(방법|하는\s*법)",
            ],
            "severity": Severity.CRITICAL,
            "explanation": "폭력적 방법에 대한 정보는 제공할 수 없습니다."
        }
    }

    # 위험 물질/행동 언급
    RISKY_MENTIONS = [
        "수면제", "안정제", "농약", "번개탄", "일산화탄소",
        "높은 곳", "철로", "차도"
    ]

    CRISIS_RESPONSE = """
지금 많이 힘드신 것 같아 걱정이 됩니다.
혹시 자해나 자살에 대한 생각이 있으시다면,
지금 바로 자살예방상담전화 1393이나 정신건강위기상담전화 1577-0199로 연락해 주세요.
24시간 전문 상담원이 도움을 드릴 수 있습니다.
"""

    def __init__(self):
        self._compile_patterns()
        logger.info("HarmfulInfoGuardrail initialized")

    def _compile_patterns(self):
        self.compiled_patterns = {}
        for category, info in self.BLOCKED_PATTERNS.items():
            self.compiled_patterns[category] = {
                "patterns": [re.compile(p, re.IGNORECASE) for p in info["patterns"]],
                "severity": info["severity"],
                "explanation": info["explanation"]
            }

    def check(self, response: str) -> List[GuardrailViolation]:
        violations = []

        # 패턴 기반 검사
        for category, info in self.compiled_patterns.items():
            for pattern in info["patterns"]:
                matches = pattern.finditer(response)
                for match in matches:
                    violations.append(GuardrailViolation(
                        guardrail_type=GuardrailType.HARMFUL_INFO,
                        severity=info["severity"],
                        matched_pattern=pattern.pattern,
                        matched_text=match.group(),
                        position=(match.start(), match.end()),
                        suggestion=self.CRISIS_RESPONSE,
                        explanation=info["explanation"]
                    ))

        # 위험 물질 언급 검사
        for mention in self.RISKY_MENTIONS:
            if mention in response:
                # 맥락 확인 (위기 대응 맥락이면 OK)
                if not self._is_safety_context(response, mention):
                    idx = response.find(mention)
                    violations.append(GuardrailViolation(
                        guardrail_type=GuardrailType.HARMFUL_INFO,
                        severity=Severity.HIGH,
                        matched_pattern=mention,
                        matched_text=mention,
                        position=(idx, idx + len(mention)),
                        suggestion="위험 물질 언급을 피하고 안전한 표현으로 대체하세요.",
                        explanation=f"'{mention}' 언급은 위험할 수 있습니다."
                    ))

        return violations

    def _is_safety_context(self, response: str, mention: str) -> bool:
        """안전 맥락인지 확인 (예: 위기 개입 메시지)"""
        safety_markers = ["도움", "상담", "전화", "연락", "1393", "1577"]
        return any(marker in response for marker in safety_markers)


# =============================================================================
# 4. 지시적 표현 가드레일
# =============================================================================

class DirectiveLanguageGuardrail:
    """
    지시적/명령적 표현 감지

    상담에서 지시적 표현은 내담자의 자율성을 침해할 수 있음
    """

    # 강한 지시적 표현 (차단)
    STRONG_DIRECTIVE_PATTERNS = [
        r"(반드시|꼭|무조건)\s*~?(해야|하세요|해)",
        r"~(하지\s*마세요|하면\s*안\s*돼요|금지)",
        r"절대로?\s*~(하지|안)",
        r"(이렇게|저렇게)\s*하세요",
        r"제\s*말대로\s*하세요",
    ]

    # 약한 지시적 표현 (경고)
    MILD_DIRECTIVE_PATTERNS = [
        r"~해야\s*(해요|합니다|돼요)",
        r"~(하세요|드세요|가세요)(?!.*(어떨까요|좋겠어요))",
        r"~하는\s*게\s*좋아요",
        r"당연히\s*~",
    ]

    # 권장 대안 표현
    ALTERNATIVE_EXPRESSIONS = {
        "해야 해요": "해보시면 어떨까요?",
        "하세요": "해보시는 건 어떠세요?",
        "하지 마세요": "~하지 않는 것도 방법일 수 있어요",
        "반드시": "가능하다면",
        "꼭": "할 수 있다면",
        "무조건": "상황이 허락한다면",
    }

    def __init__(self):
        self.strong_patterns = [re.compile(p) for p in self.STRONG_DIRECTIVE_PATTERNS]
        self.mild_patterns = [re.compile(p) for p in self.MILD_DIRECTIVE_PATTERNS]
        logger.info("DirectiveLanguageGuardrail initialized")

    def check(self, response: str) -> List[GuardrailViolation]:
        violations = []

        # 강한 지시적 표현
        for pattern in self.strong_patterns:
            matches = pattern.finditer(response)
            for match in matches:
                violations.append(GuardrailViolation(
                    guardrail_type=GuardrailType.DIRECTIVE_LANGUAGE,
                    severity=Severity.HIGH,
                    matched_pattern=pattern.pattern,
                    matched_text=match.group(),
                    position=(match.start(), match.end()),
                    suggestion="제안형 표현으로 바꿔주세요: '~해보시면 어떨까요?'",
                    explanation="강한 지시적 표현은 내담자의 자율성을 침해할 수 있습니다."
                ))

        # 약한 지시적 표현
        for pattern in self.mild_patterns:
            matches = pattern.finditer(response)
            for match in matches:
                # 이미 제안형이면 스킵
                text = match.group()
                if "어떨까요" in text or "좋겠어요" in text:
                    continue

                violations.append(GuardrailViolation(
                    guardrail_type=GuardrailType.DIRECTIVE_LANGUAGE,
                    severity=Severity.LOW,
                    matched_pattern=pattern.pattern,
                    matched_text=text,
                    position=(match.start(), match.end()),
                    suggestion=self._suggest_alternative(text),
                    explanation="지시적 표현보다 제안형 표현이 더 효과적입니다."
                ))

        return violations

    def _suggest_alternative(self, text: str) -> str:
        """대안 표현 제안"""
        for directive, alternative in self.ALTERNATIVE_EXPRESSIONS.items():
            if directive in text:
                return f"'{directive}' 대신 '{alternative}' 표현을 사용해 보세요."
        return "제안형 표현으로 바꿔보세요: '~해보시면 어떨까요?'"


# =============================================================================
# 5. 진단명 언급 가드레일
# =============================================================================

class DiagnosisMentionGuardrail:
    """
    진단명 부적절 사용 방지

    AI가 진단을 내리거나 진단명을 확정적으로 언급하는 것 방지
    """

    # 정신건강 진단명 목록
    DIAGNOSIS_TERMS = [
        # 기분장애
        "우울증", "주요우울장애", "기분부전장애", "양극성장애", "조울증",
        # 불안장애
        "불안장애", "범불안장애", "공황장애", "사회불안장애", "광장공포증",
        "특정공포증", "분리불안장애",
        # 트라우마 관련
        "PTSD", "외상후스트레스장애", "급성스트레스장애", "적응장애",
        # 강박 관련
        "강박장애", "OCD", "강박증",
        # 신체 관련
        "신체화장애", "건강염려증", "전환장애",
        # 섭식장애
        "거식증", "폭식증", "섭식장애",
        # 수면장애
        "불면증", "수면장애", "과다수면",
        # 성격장애
        "경계성성격장애", "자기애성성격장애", "반사회성성격장애", "회피성성격장애",
        # 기타
        "조현병", "정신분열", "ADHD", "주의력결핍", "자폐", "아스퍼거",
    ]

    # 진단적 표현 패턴
    DIAGNOSTIC_PATTERNS = [
        r"({terms}).*?(이시네요|이세요|있으시네요|같아요|보여요|의심)",
        r"({terms}).*?(진단|증상|증세)",
        r"({terms}).*?(환자|분|사람)",
    ]

    # 안전한 표현
    SAFE_EXPRESSION = """
정확한 상태 파악은 전문가의 평가가 필요해요.
혹시 관련해서 걱정이 되신다면, 전문 상담을 받아보시는 것도 좋은 방법이에요.
"""

    def __init__(self):
        terms_pattern = "|".join(self.DIAGNOSIS_TERMS)
        self.diagnostic_patterns = [
            re.compile(p.format(terms=terms_pattern), re.IGNORECASE)
            for p in self.DIAGNOSTIC_PATTERNS
        ]
        self.terms_set = set(self.DIAGNOSIS_TERMS)
        logger.info("DiagnosisMentionGuardrail initialized")

    def check(self, response: str) -> List[GuardrailViolation]:
        violations = []

        # 진단적 표현 패턴 검사
        for pattern in self.diagnostic_patterns:
            matches = pattern.finditer(response)
            for match in matches:
                violations.append(GuardrailViolation(
                    guardrail_type=GuardrailType.DIAGNOSIS_MENTION,
                    severity=Severity.HIGH,
                    matched_pattern=pattern.pattern[:50] + "...",
                    matched_text=match.group(),
                    position=(match.start(), match.end()),
                    suggestion=self.SAFE_EXPRESSION,
                    explanation="AI는 진단을 내릴 수 없습니다. 전문가 연계를 권유하세요."
                ))

        # 단순 진단명 언급 (맥락에 따라)
        for term in self.DIAGNOSIS_TERMS:
            if term in response:
                # 이미 위반으로 감지되지 않은 경우만
                already_detected = any(term in v.matched_text for v in violations)
                if not already_detected:
                    # 교육적 맥락인지 확인
                    if not self._is_educational_context(response, term):
                        idx = response.find(term)
                        violations.append(GuardrailViolation(
                            guardrail_type=GuardrailType.DIAGNOSIS_MENTION,
                            severity=Severity.MEDIUM,
                            matched_pattern=term,
                            matched_text=term,
                            position=(idx, idx + len(term)),
                            suggestion="진단명 대신 증상이나 경험을 설명하는 표현을 사용하세요.",
                            explanation="진단명 직접 언급은 낙인을 줄 수 있습니다."
                        ))

        return violations

    def _is_educational_context(self, response: str, term: str) -> bool:
        """교육적/정보 제공 맥락인지 확인"""
        educational_markers = [
            "일반적으로", "알려져 있", "정보로는", "설명드리자면",
            "궁금하신", "알아보시면"
        ]
        return any(marker in response for marker in educational_markers)


# =============================================================================
# 6. 중대 결정 조언 가드레일
# =============================================================================

class MajorDecisionGuardrail:
    """
    중대한 인생 결정에 대한 직접적 조언 방지

    이혼, 퇴사, 관계 단절 등 중대 결정은 내담자 스스로 해야 함
    """

    # 중대 결정 영역
    MAJOR_DECISION_AREAS = {
        "relationship": {
            "keywords": ["이혼", "헤어지", "결별", "파혼", "별거"],
            "advice_patterns": [
                r"(이혼|헤어지|결별).*?(하세요|하는\s*게|해야|추천)",
                r"(떠나|관두|끝내).*?(세요|시는\s*게)",
            ]
        },
        "career": {
            "keywords": ["퇴사", "사직", "그만두", "이직", "퇴직"],
            "advice_patterns": [
                r"(퇴사|그만두|사직).*?(하세요|하는\s*게|해야)",
                r"(회사|직장).*?(나오|떠나|관두).*?(세요|시는\s*게)",
            ]
        },
        "family": {
            "keywords": ["연 끊", "의절", "절연", "인연 끊"],
            "advice_patterns": [
                r"(연|인연|관계).*?(끊|정리).*?(세요|하는\s*게)",
                r"(부모|가족).*?(떠나|끊).*?(세요|시는\s*게)",
            ]
        },
        "financial": {
            "keywords": ["투자", "대출", "빚", "파산", "매매"],
            "advice_patterns": [
                r"(투자|매매|매수|매도).*?(하세요|추천|권해)",
                r"(빚|대출).*?(갚|내).*?(세요|방법)",
            ]
        }
    }

    SAFE_RESPONSE = """
이런 중요한 결정은 충분히 고민하시고,
필요하다면 관련 전문가(변호사, 재무상담사 등)와도 상담해 보시는 게 좋겠어요.
제가 도와드릴 수 있는 건, 결정을 내리시기까지의 마음을 함께 살펴보는 거예요.
"""

    def __init__(self):
        self._compile_patterns()
        logger.info("MajorDecisionGuardrail initialized")

    def _compile_patterns(self):
        self.compiled_patterns = {}
        for area, info in self.MAJOR_DECISION_AREAS.items():
            self.compiled_patterns[area] = {
                "keywords": info["keywords"],
                "patterns": [re.compile(p) for p in info["advice_patterns"]]
            }

    def check(self, response: str) -> List[GuardrailViolation]:
        violations = []

        for area, info in self.compiled_patterns.items():
            for pattern in info["patterns"]:
                matches = pattern.finditer(response)
                for match in matches:
                    violations.append(GuardrailViolation(
                        guardrail_type=GuardrailType.MAJOR_DECISION,
                        severity=Severity.HIGH,
                        matched_pattern=pattern.pattern,
                        matched_text=match.group(),
                        position=(match.start(), match.end()),
                        suggestion=self.SAFE_RESPONSE,
                        explanation=f"{area} 관련 중대 결정에 대한 직접적 조언은 피해야 합니다."
                    ))

        return violations


# =============================================================================
# 7. 경계 위반 가드레일
# =============================================================================

class BoundaryViolationGuardrail:
    """
    상담 경계 위반 감지

    부적절한 관계 형성, 개인정보 요청 등 방지
    """

    # 경계 위반 패턴
    BOUNDARY_VIOLATION_PATTERNS = {
        "personal_relationship": {
            "patterns": [
                r"(친구|연인).*?(되고\s*싶|하고\s*싶|될\s*수)",
                r"(만나|데이트).*?(싶|할까)",
                r"(연락처|번호|카톡|SNS).*?(알려|교환)",
                r"개인적으로.*?(만나|연락)",
            ],
            "severity": Severity.CRITICAL,
            "explanation": "상담 관계 외 개인적 관계 형성은 부적절합니다."
        },
        "inappropriate_curiosity": {
            "patterns": [
                r"(외모|얼굴|몸|나이).*?(어떻|궁금|알고\s*싶)",
                r"(어디\s*사|집이\s*어디)",
                r"(학교|직장).*?(어디|이름)",
            ],
            "severity": Severity.HIGH,
            "explanation": "상담과 무관한 개인정보 질문은 부적절합니다."
        },
        "dual_relationship": {
            "patterns": [
                r"(도와|해결).*?(드릴게요|줄게요).*?(외|밖)",
                r"상담\s*외.*?(도움|만남)",
            ],
            "severity": Severity.HIGH,
            "explanation": "이중관계 형성은 피해야 합니다."
        }
    }

    def __init__(self):
        self._compile_patterns()
        logger.info("BoundaryViolationGuardrail initialized")

    def _compile_patterns(self):
        self.compiled_patterns = {}
        for category, info in self.BOUNDARY_VIOLATION_PATTERNS.items():
            self.compiled_patterns[category] = {
                "patterns": [re.compile(p) for p in info["patterns"]],
                "severity": info["severity"],
                "explanation": info["explanation"]
            }

    def check(self, response: str) -> List[GuardrailViolation]:
        violations = []

        for category, info in self.compiled_patterns.items():
            for pattern in info["patterns"]:
                matches = pattern.finditer(response)
                for match in matches:
                    violations.append(GuardrailViolation(
                        guardrail_type=GuardrailType.BOUNDARY_VIOLATION,
                        severity=info["severity"],
                        matched_pattern=pattern.pattern,
                        matched_text=match.group(),
                        position=(match.start(), match.end()),
                        suggestion="상담 관계의 경계를 유지하는 표현으로 수정하세요.",
                        explanation=info["explanation"]
                    ))

        return violations


# =============================================================================
# 8. 부적절한 약속/희망 가드레일
# =============================================================================

class PromiseHopeGuardrail:
    """
    부적절한 약속이나 거짓 희망 제공 방지
    """

    # 부적절한 약속 패턴
    PROMISE_PATTERNS = [
        r"(반드시|꼭|무조건).*?(나아질|좋아질|해결될)",
        r"(약속|보장|확신).*?(드려요|할게요|합니다)",
        r"(100%|확실히).*?(괜찮|좋아|나아)",
        r"제가\s*(책임|보장|약속)",
    ]

    # 거짓 희망 패턴
    FALSE_HOPE_PATTERNS = [
        r"금방\s*(나아|좋아|해결)",
        r"(쉽게|간단히).*?(해결|극복|나아)",
        r"(걱정\s*마|다\s*잘\s*될|문제\s*없)",
        r"(시간이\s*지나면|조금만\s*참으면).*?(괜찮|좋아)",
    ]

    # 현실적인 대안 표현
    REALISTIC_ALTERNATIVES = [
        "변화에는 시간이 필요할 수 있어요. 함께 천천히 나아가 봐요.",
        "쉽지 않은 과정일 수 있지만, 조금씩 나아질 수 있어요.",
        "확실한 건 지금 여기서 함께 이야기 나눌 수 있다는 거예요.",
        "어려운 시간이지만, 작은 변화부터 시작해 볼 수 있어요.",
    ]

    def __init__(self):
        self.promise_patterns = [re.compile(p) for p in self.PROMISE_PATTERNS]
        self.hope_patterns = [re.compile(p) for p in self.FALSE_HOPE_PATTERNS]
        logger.info("PromiseHopeGuardrail initialized")

    def check(self, response: str) -> List[GuardrailViolation]:
        violations = []

        # 부적절한 약속
        for pattern in self.promise_patterns:
            matches = pattern.finditer(response)
            for match in matches:
                violations.append(GuardrailViolation(
                    guardrail_type=GuardrailType.PROMISE_MAKING,
                    severity=Severity.HIGH,
                    matched_pattern=pattern.pattern,
                    matched_text=match.group(),
                    position=(match.start(), match.end()),
                    suggestion=self.REALISTIC_ALTERNATIVES[0],
                    explanation="확실하지 않은 약속은 신뢰를 해칠 수 있습니다."
                ))

        # 거짓 희망
        for pattern in self.hope_patterns:
            matches = pattern.finditer(response)
            for match in matches:
                violations.append(GuardrailViolation(
                    guardrail_type=GuardrailType.FALSE_HOPE,
                    severity=Severity.MEDIUM,
                    matched_pattern=pattern.pattern,
                    matched_text=match.group(),
                    position=(match.start(), match.end()),
                    suggestion=self.REALISTIC_ALTERNATIVES[1],
                    explanation="비현실적인 희망은 오히려 해가 될 수 있습니다."
                ))

        return violations


# =============================================================================
# 통합 가드레일 시스템
# =============================================================================

class ResponseGuardrailSystem:
    """
    통합 응답 가드레일 시스템

    모든 가드레일을 통합하여 응답 안전성 검사
    """

    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode

        # 모든 가드레일 초기화
        self.guardrails = {
            "medical": MedicalAdviceGuardrail(),
            "legal": LegalAdviceGuardrail(),
            "harmful": HarmfulInfoGuardrail(),
            "directive": DirectiveLanguageGuardrail(),
            "diagnosis": DiagnosisMentionGuardrail(),
            "major_decision": MajorDecisionGuardrail(),
            "boundary": BoundaryViolationGuardrail(),
            "promise_hope": PromiseHopeGuardrail(),
        }

        # 심각도별 점수
        self.severity_scores = {
            Severity.CRITICAL: 40,
            Severity.HIGH: 25,
            Severity.MEDIUM: 15,
            Severity.LOW: 5,
        }

        logger.info("ResponseGuardrailSystem initialized")

    def check_response(self, response: str) -> GuardrailResult:
        """
        응답 안전성 검사

        Args:
            response: 검사할 응답 텍스트

        Returns:
            GuardrailResult: 검사 결과
        """
        all_violations = []

        # 모든 가드레일 검사
        for name, guardrail in self.guardrails.items():
            violations = guardrail.check(response)
            all_violations.extend(violations)

        # 위험 점수 계산
        risk_score = self._calculate_risk_score(all_violations)

        # 차단 여부 결정
        blocked = any(v.severity == Severity.CRITICAL for v in all_violations)
        if self.strict_mode:
            blocked = blocked or any(v.severity == Severity.HIGH for v in all_violations)

        # 경고 생성
        warnings = self._generate_warnings(all_violations)

        # 결과 생성
        result = GuardrailResult(
            is_safe=len(all_violations) == 0,
            violations=all_violations,
            risk_score=risk_score,
            blocked=blocked,
            warnings=warnings
        )

        # 수정된 응답 생성 (필요시)
        if all_violations and not blocked:
            result.corrected_response = self._suggest_correction(response, all_violations)

        logger.info(f"Guardrail check: {len(all_violations)} violations, "
                   f"risk_score={risk_score:.1f}, blocked={blocked}")

        return result

    def _calculate_risk_score(self, violations: List[GuardrailViolation]) -> float:
        """위험 점수 계산"""
        if not violations:
            return 0.0

        total_score = sum(self.severity_scores[v.severity] for v in violations)
        return min(100.0, total_score)

    def _generate_warnings(self, violations: List[GuardrailViolation]) -> List[str]:
        """경고 메시지 생성"""
        warnings = []

        # 유형별 그룹화
        by_type = {}
        for v in violations:
            if v.guardrail_type not in by_type:
                by_type[v.guardrail_type] = []
            by_type[v.guardrail_type].append(v)

        for gtype, vlist in by_type.items():
            count = len(vlist)
            severity = max(v.severity.value for v in vlist)
            warnings.append(f"[{severity.upper()}] {gtype.value}: {count}건 감지")

        return warnings

    def _suggest_correction(self, response: str,
                           violations: List[GuardrailViolation]) -> str:
        """수정 제안 응답 생성"""
        corrected = response

        # 심각한 위반부터 처리 (역순으로 위치 기반 수정)
        sorted_violations = sorted(
            violations,
            key=lambda v: v.position[0],
            reverse=True
        )

        for v in sorted_violations:
            if v.severity in [Severity.CRITICAL, Severity.HIGH]:
                # 해당 부분 제거 또는 대체
                start, end = v.position
                corrected = corrected[:start] + "[수정 필요]" + corrected[end:]

        return corrected

    def get_safe_response_template(self, violation_type: GuardrailType) -> str:
        """위반 유형별 안전한 응답 템플릿 반환"""
        templates = {
            GuardrailType.MEDICAL_ADVICE:
                "건강 관련 부분은 전문 의료진과 상담하시는 게 좋겠어요. "
                "지금은 마음 상태에 대해 더 이야기해 볼까요?",

            GuardrailType.LEGAL_ADVICE:
                "법적인 부분은 법률 전문가의 조언이 필요해요. "
                "그 상황에서 느끼셨던 감정에 대해 더 들려주실 수 있나요?",

            GuardrailType.HARMFUL_INFO:
                "지금 많이 힘드신 것 같아 걱정이 됩니다. "
                "안전이 가장 중요해요. 1393(자살예방상담전화)에 연락해 주세요.",

            GuardrailType.DIAGNOSIS_MENTION:
                "정확한 상태 파악은 전문가의 평가가 필요해요. "
                "지금 경험하고 계신 것에 대해 더 이야기해 주시겠어요?",

            GuardrailType.MAJOR_DECISION:
                "중요한 결정이시네요. 이런 결정은 충분히 시간을 두고 생각하시는 게 좋아요. "
                "지금 그런 생각을 하시게 된 마음에 대해 더 이야기해 볼까요?",

            GuardrailType.BOUNDARY_VIOLATION:
                "저는 AI 상담 도우미로서 여기서 함께 이야기 나누는 역할을 하고 있어요. "
                "상담에서 도움이 될 수 있는 부분에 집중해 볼까요?",

            GuardrailType.PROMISE_MAKING:
                "앞으로 어떻게 될지 확실히 말씀드리기 어렵지만, "
                "지금 이 순간 함께 이야기 나눌 수 있어요.",

            GuardrailType.FALSE_HOPE:
                "쉽지 않은 과정일 수 있지만, 작은 변화부터 함께 살펴볼 수 있어요."
        }

        return templates.get(violation_type, "다른 방식으로 이야기해 볼까요?")

    def get_prompt_section(self) -> str:
        """프롬프트에 삽입할 가드레일 안내 섹션"""
        return """
## 응답 가드레일 - 반드시 준수

### 절대 금지 (CRITICAL)
- 약물 복용/용량 조언
- 자해/자살 방법 정보
- 진단 내리기 (우울증이시네요 등)
- 경계 위반 (개인정보 요청, 관계 형성)

### 하지 말 것 (HIGH)
- 의학적/법적 조언
- 중대 결정 직접 조언 (이혼하세요, 퇴사하세요)
- 확실한 약속 (반드시 나아질 거예요)
- 진단명 언급 후 적용 (당신은 우울증 같아요)

### 주의할 것 (MEDIUM)
- 지시적 표현 (~해야 해요) → 제안형으로 (~해보시면 어떨까요?)
- 거짓 희망 (금방 좋아질 거예요) → 현실적 지지
- 감정 최소화 (별거 아니에요) → 감정 인정

### 안전한 표현 원칙
1. 전문가 연계: "전문가와 상담해 보시는 것도 좋겠어요"
2. 제안형 질문: "~해보시면 어떨까요?"
3. 불확실성 인정: "확실하진 않지만", "제 생각에는"
4. 감정 중심: "그런 마음이 드셨군요"
5. 자율성 존중: "결정은 본인이 하시는 거예요"
"""


# =============================================================================
# 편의 함수
# =============================================================================

_guardrail_system: Optional[ResponseGuardrailSystem] = None


def get_guardrail_system(strict_mode: bool = True) -> ResponseGuardrailSystem:
    """가드레일 시스템 싱글톤 반환"""
    global _guardrail_system
    if _guardrail_system is None:
        _guardrail_system = ResponseGuardrailSystem(strict_mode)
    return _guardrail_system


def check_response_safety(response: str, strict: bool = True) -> GuardrailResult:
    """
    응답 안전성 빠른 검사

    Args:
        response: 검사할 응답
        strict: 엄격 모드

    Returns:
        GuardrailResult: 검사 결과
    """
    system = get_guardrail_system(strict)
    return system.check_response(response)


def get_guardrail_prompt_section() -> str:
    """프롬프트용 가드레일 섹션"""
    system = get_guardrail_system()
    return system.get_prompt_section()


def is_response_safe(response: str) -> bool:
    """응답이 안전한지 빠른 체크"""
    result = check_response_safety(response)
    return not result.blocked
