"""
환각 방지 시스템 (Hallucination Prevention System)

AI의 부정확한 정보 생성(환각)을 방지:
1. 사실 주장 감지 - 검증 필요한 주장 식별
2. 불확실성 표현 강제 - 확실하지 않은 내용에 표현 추가
3. 사용자 정보 추측 방지 - 말하지 않은 내용 추측 감지
4. 거짓 기억 유도 방지 - "기억하시죠?" 형태 방지
5. 전문 지식 주장 검증 - 심리학 용어/개념 정확성
6. 출처 없는 통계 감지 - 근거 없는 수치 주장
"""

from typing import Dict, List, Optional, Tuple, Any, Set
from enum import Enum
from dataclasses import dataclass, field
import logging
import re

logger = logging.getLogger(__name__)


# =============================================================================
# 환각 유형 및 데이터 구조
# =============================================================================

class HallucinationType(Enum):
    """환각 유형"""
    FACTUAL_CLAIM = "factual_claim"           # 사실 주장
    USER_ASSUMPTION = "user_assumption"       # 사용자 정보 추측
    FALSE_MEMORY = "false_memory"             # 거짓 기억 유도
    UNVERIFIED_STAT = "unverified_stat"       # 검증 안 된 통계
    EXPERT_CLAIM = "expert_claim"             # 전문가 주장
    MADE_UP_QUOTE = "made_up_quote"           # 만들어낸 인용
    INVENTED_REFERENCE = "invented_reference" # 가짜 출처
    OVERCONFIDENCE = "overconfidence"         # 과신


class RiskLevel(Enum):
    """위험 수준"""
    HIGH = "high"       # 심각한 환각 위험
    MEDIUM = "medium"   # 주의 필요
    LOW = "low"         # 경미한 위험


@dataclass
class HallucinationRisk:
    """환각 위험 정보"""
    hallucination_type: HallucinationType
    risk_level: RiskLevel
    detected_text: str
    position: Tuple[int, int]
    why_risky: str
    mitigation: str


@dataclass
class HallucinationCheckResult:
    """환각 검사 결과"""
    has_risks: bool
    risks: List[HallucinationRisk] = field(default_factory=list)
    risk_score: float = 0.0
    mitigated_response: Optional[str] = None
    suggestions: List[str] = field(default_factory=list)


# =============================================================================
# 1. 사실 주장 감지기
# =============================================================================

class FactualClaimDetector:
    """
    사실 주장 감지

    검증이 필요한 사실적 주장을 감지
    """

    # 사실 주장 패턴
    FACTUAL_CLAIM_PATTERNS = [
        (r"(연구|연구결과).*?(보여|밝혀|나타나)", "연구 결과 주장"),
        (r"(과학적|심리학적)으로.*?(증명|밝혀)", "과학적 주장"),
        (r"(통계|데이터).*?(따르면|의하면)", "통계 인용"),
        (r"(\d+)%.*?(사람|경우|확률)", "수치 주장"),
        (r"(항상|절대|반드시|모든).*?(~이다|~입니다)", "절대적 주장"),
        (r"(효과가\s*있|도움이\s*된)다고\s*(알려|입증|증명)", "효과 주장"),
    ]

    # 확실성 표현 (과신 위험)
    OVERCONFIDENCE_MARKERS = [
        "확실히", "틀림없이", "분명히", "100%", "반드시",
        "항상", "절대", "무조건", "당연히"
    ]

    # 권장 불확실성 표현
    UNCERTAINTY_PHRASES = [
        "~일 수 있어요",
        "~라고 알려져 있어요",
        "일반적으로 ~",
        "많은 경우에 ~",
        "제 이해로는 ~",
    ]

    def __init__(self):
        self.patterns = [(re.compile(p), desc) for p, desc in self.FACTUAL_CLAIM_PATTERNS]
        logger.info("FactualClaimDetector initialized")

    def detect(self, response: str) -> List[HallucinationRisk]:
        """사실 주장 감지"""
        risks = []

        # 패턴 기반 감지
        for pattern, description in self.patterns:
            matches = pattern.finditer(response)
            for match in matches:
                risks.append(HallucinationRisk(
                    hallucination_type=HallucinationType.FACTUAL_CLAIM,
                    risk_level=RiskLevel.MEDIUM,
                    detected_text=match.group(),
                    position=(match.start(), match.end()),
                    why_risky=f"{description} - 출처 확인 필요",
                    mitigation="'~라고 알려져 있어요' 등 불확실성 표현 추가"
                ))

        # 과신 표현 감지
        for marker in self.OVERCONFIDENCE_MARKERS:
            if marker in response:
                idx = response.find(marker)
                risks.append(HallucinationRisk(
                    hallucination_type=HallucinationType.OVERCONFIDENCE,
                    risk_level=RiskLevel.LOW,
                    detected_text=marker,
                    position=(idx, idx + len(marker)),
                    why_risky="과도한 확신 표현",
                    mitigation=f"'{marker}' 대신 '아마도', '~일 수 있어요' 등 사용"
                ))

        return risks


# =============================================================================
# 2. 사용자 정보 추측 감지기
# =============================================================================

class UserAssumptionDetector:
    """
    사용자 정보 추측 감지

    사용자가 말하지 않은 정보를 추측하는 것 감지
    """

    # 추측 패턴
    ASSUMPTION_PATTERNS = [
        (r"(아마|아마도)\s*(~하셨|~이신|~겠)", "추측 표현"),
        (r"(분명|틀림없이)\s*(~하셨|~이셨)", "확정적 추측"),
        (r"(당신|그|그녀).*?(~겠죠|~일\s*거예요)", "상대방 상태 추측"),
        (r"(부모님|가족|친구).*?(~하셨을|~했을)", "타인 행동 추측"),
    ]

    # 위험 추측 키워드
    RISKY_ASSUMPTIONS = [
        "원인은", "이유는", "때문에", "덕분에",
        "항상 그랬", "늘 그래", "매번"
    ]

    # 안전한 탐색 표현
    SAFE_EXPLORATION = [
        "혹시 ~인가요?",
        "~하신 건 아닌지 궁금해요",
        "~일 수도 있을까요?",
        "어떤 ~인지 여쭤봐도 될까요?",
    ]

    def __init__(self):
        self.patterns = [(re.compile(p), desc) for p, desc in self.ASSUMPTION_PATTERNS]
        logger.info("UserAssumptionDetector initialized")

    def detect(self, response: str, user_mentioned: Set[str] = None) -> List[HallucinationRisk]:
        """사용자 정보 추측 감지"""
        risks = []
        user_mentioned = user_mentioned or set()

        # 패턴 기반 감지
        for pattern, description in self.patterns:
            matches = pattern.finditer(response)
            for match in matches:
                risks.append(HallucinationRisk(
                    hallucination_type=HallucinationType.USER_ASSUMPTION,
                    risk_level=RiskLevel.MEDIUM,
                    detected_text=match.group(),
                    position=(match.start(), match.end()),
                    why_risky=f"{description} - 사용자가 말하지 않은 내용 추측",
                    mitigation="추측 대신 질문으로 확인: '혹시 ~인가요?'"
                ))

        # 원인/이유 단정 감지
        for keyword in self.RISKY_ASSUMPTIONS:
            if keyword in response:
                idx = response.find(keyword)
                # 뒤에 단정적 표현이 있는지 확인
                context = response[idx:idx+50]
                if any(marker in context for marker in ["것 같아요", "겠네요", "이에요", "입니다"]):
                    risks.append(HallucinationRisk(
                        hallucination_type=HallucinationType.USER_ASSUMPTION,
                        risk_level=RiskLevel.MEDIUM,
                        detected_text=context[:30],
                        position=(idx, min(idx+50, len(response))),
                        why_risky="원인/이유를 단정적으로 추측",
                        mitigation="'혹시 ~ 때문일까요?' 형태로 질문"
                    ))

        return risks


# =============================================================================
# 3. 거짓 기억 유도 감지기
# =============================================================================

class FalseMemoryDetector:
    """
    거짓 기억 유도 감지

    "기억하시죠?", "말씀하셨잖아요" 등 거짓 기억 유도 방지
    """

    # 거짓 기억 유도 패턴
    FALSE_MEMORY_PATTERNS = [
        (r"기억하시(죠|잖아요|지요)", "기억 강요"),
        (r"말씀하셨(잖아요|죠|지요)", "발언 확정"),
        (r"전에\s*(~라고|~하셨다고)", "과거 발언 주장"),
        (r"아까\s*(~하셨|~라고)", "최근 발언 주장"),
        (r"(분명|분명히)\s*~(하셨|라고)", "확정적 기억 주장"),
        (r"(그때|그랬을\s*때).*?(하셨잖아요|했잖아요)", "과거 사건 확정"),
    ]

    # 안전한 확인 표현
    SAFE_CONFIRMATION = [
        "제가 잘 이해했는지 확인하고 싶은데요,",
        "앞서 ~에 대해 말씀해 주셨는데,",
        "혹시 제가 잘못 이해한 부분이 있을까요?",
        "~라고 이해했는데, 맞을까요?",
    ]

    def __init__(self):
        self.patterns = [(re.compile(p), desc) for p, desc in self.FALSE_MEMORY_PATTERNS]
        logger.info("FalseMemoryDetector initialized")

    def detect(self, response: str) -> List[HallucinationRisk]:
        """거짓 기억 유도 감지"""
        risks = []

        for pattern, description in self.patterns:
            matches = pattern.finditer(response)
            for match in matches:
                risks.append(HallucinationRisk(
                    hallucination_type=HallucinationType.FALSE_MEMORY,
                    risk_level=RiskLevel.HIGH,
                    detected_text=match.group(),
                    position=(match.start(), match.end()),
                    why_risky=f"{description} - 거짓 기억 유도 위험",
                    mitigation="확인 질문 사용: '~라고 이해했는데, 맞을까요?'"
                ))

        return risks


# =============================================================================
# 4. 검증 안 된 통계 감지기
# =============================================================================

class UnverifiedStatDetector:
    """
    검증 안 된 통계/수치 감지

    출처 없는 구체적 수치 주장 감지
    """

    # 통계 패턴
    STAT_PATTERNS = [
        (r"(\d+)\s*%", "퍼센트 수치"),
        (r"(\d+)\s*명\s*중", "인원 통계"),
        (r"(\d+)\s*배", "배수 주장"),
        (r"(\d+)\s*(번|회|차례)", "빈도 주장"),
        (r"평균.*?(\d+)", "평균 수치"),
        (r"(\d+)\s*인\s*(1|한)\s*명", "비율 주장"),
    ]

    # 가짜 정확성 (너무 구체적인 수치)
    FAKE_PRECISION_PATTERN = r"\d{2,}\.?\d*\s*%"

    # 안전한 표현
    SAFE_EXPRESSIONS = [
        "많은 사람들이",
        "일부에서는",
        "~하는 경우가 있어요",
        "~라는 연구 결과도 있어요",
    ]

    def __init__(self):
        self.patterns = [(re.compile(p), desc) for p, desc in self.STAT_PATTERNS]
        self.fake_precision = re.compile(self.FAKE_PRECISION_PATTERN)
        logger.info("UnverifiedStatDetector initialized")

    def detect(self, response: str) -> List[HallucinationRisk]:
        """검증 안 된 통계 감지"""
        risks = []

        for pattern, description in self.patterns:
            matches = pattern.finditer(response)
            for match in matches:
                # 출처가 함께 언급되었는지 확인
                context = response[max(0, match.start()-50):match.end()+50]
                has_source = any(s in context for s in ["연구", "조사", "보고", "논문", "출처"])

                if not has_source:
                    risks.append(HallucinationRisk(
                        hallucination_type=HallucinationType.UNVERIFIED_STAT,
                        risk_level=RiskLevel.MEDIUM,
                        detected_text=match.group(),
                        position=(match.start(), match.end()),
                        why_risky=f"{description} - 출처 없는 수치",
                        mitigation="'많은 경우에', '일부에서는' 등 일반적 표현 사용"
                    ))

        # 가짜 정확성 감지
        fake_matches = self.fake_precision.finditer(response)
        for match in fake_matches:
            risks.append(HallucinationRisk(
                hallucination_type=HallucinationType.UNVERIFIED_STAT,
                risk_level=RiskLevel.HIGH,
                detected_text=match.group(),
                position=(match.start(), match.end()),
                why_risky="과도하게 정확한 수치 - 환각 가능성 높음",
                mitigation="구체적 수치 대신 일반적 표현 사용"
            ))

        return risks


# =============================================================================
# 5. 전문 지식 주장 검증기
# =============================================================================

class ExpertClaimVerifier:
    """
    전문 지식 주장 검증

    심리학 용어/개념의 정확한 사용 확인
    """

    # 검증 필요한 전문 용어
    PSYCHOLOGY_TERMS = {
        "우울증": "임상적 진단명으로, AI가 진단할 수 없음",
        "불안장애": "임상적 진단명으로, AI가 진단할 수 없음",
        "트라우마": "전문적 개념으로, 신중하게 사용",
        "PTSD": "임상적 진단명",
        "인지행동치료": "전문 치료법",
        "정신분석": "전문 치료법",
        "전이": "전문 심리학 용어",
        "무의식": "전문 심리학 용어",
    }

    # 전문가 주장 패턴
    EXPERT_CLAIM_PATTERNS = [
        (r"심리학적으로.*?(~이다|~입니다)", "심리학적 단정"),
        (r"치료.*?(효과|결과).*?(~이다|~입니다)", "치료 효과 단정"),
        (r"(뇌|신경).*?(작동|기능).*?(~이다|~입니다)", "신경과학적 주장"),
    ]

    # 안전한 표현
    SAFE_EXPERT_LANGUAGE = [
        "심리학에서는 ~라고 설명하기도 해요",
        "이런 경험을 ~라고 부르기도 해요",
        "전문가들은 ~라고 말하기도 합니다",
    ]

    def __init__(self):
        self.patterns = [(re.compile(p), desc) for p, desc in self.EXPERT_CLAIM_PATTERNS]
        logger.info("ExpertClaimVerifier initialized")

    def detect(self, response: str) -> List[HallucinationRisk]:
        """전문 지식 주장 감지"""
        risks = []

        # 전문 용어 사용 검사
        for term, note in self.PSYCHOLOGY_TERMS.items():
            if term in response:
                # 단정적으로 사용되었는지 확인
                idx = response.find(term)
                context = response[max(0, idx-20):min(len(response), idx+50)]

                if any(marker in context for marker in ["이시네요", "있으시네요", "같아요", "입니다"]):
                    risks.append(HallucinationRisk(
                        hallucination_type=HallucinationType.EXPERT_CLAIM,
                        risk_level=RiskLevel.HIGH,
                        detected_text=context,
                        position=(idx, idx + len(term)),
                        why_risky=f"전문 용어 '{term}' 부적절 사용 - {note}",
                        mitigation="진단적 표현 대신 경험 중심 표현 사용"
                    ))

        # 전문가 주장 패턴 감지
        for pattern, description in self.patterns:
            matches = pattern.finditer(response)
            for match in matches:
                risks.append(HallucinationRisk(
                    hallucination_type=HallucinationType.EXPERT_CLAIM,
                    risk_level=RiskLevel.MEDIUM,
                    detected_text=match.group(),
                    position=(match.start(), match.end()),
                    why_risky=f"{description} - 전문 지식 단정",
                    mitigation="'~라고 알려져 있어요', '~라고 하기도 해요' 사용"
                ))

        return risks


# =============================================================================
# 6. 가짜 인용/출처 감지기
# =============================================================================

class FakeReferenceDetector:
    """
    가짜 인용/출처 감지

    실제 존재하지 않는 인용이나 출처 주장 감지
    """

    # 인용 패턴
    QUOTE_PATTERNS = [
        (r'"[^"]{10,}"', "직접 인용"),
        (r"'[^']{10,}'", "직접 인용"),
        (r"~라고\s*(말했|했)다", "간접 인용"),
    ]

    # 출처 주장 패턴
    REFERENCE_PATTERNS = [
        (r"(논문|연구|보고서).*?(따르면|의하면)", "학술 출처 주장"),
        (r"(박사|교수|전문가).*?(말했|주장)", "전문가 인용 주장"),
        (r"(\d{4})년.*?(연구|조사)", "연도별 연구 주장"),
    ]

    # 위험 신호
    RISK_SIGNALS = [
        "유명한", "잘 알려진", "많은 연구에서",
        "모든 전문가가", "과학적으로 증명된"
    ]

    def __init__(self):
        self.quote_patterns = [(re.compile(p), desc) for p, desc in self.QUOTE_PATTERNS]
        self.ref_patterns = [(re.compile(p), desc) for p, desc in self.REFERENCE_PATTERNS]
        logger.info("FakeReferenceDetector initialized")

    def detect(self, response: str) -> List[HallucinationRisk]:
        """가짜 인용/출처 감지"""
        risks = []

        # 인용 감지
        for pattern, description in self.quote_patterns:
            matches = pattern.finditer(response)
            for match in matches:
                risks.append(HallucinationRisk(
                    hallucination_type=HallucinationType.MADE_UP_QUOTE,
                    risk_level=RiskLevel.HIGH,
                    detected_text=match.group()[:50],
                    position=(match.start(), match.end()),
                    why_risky=f"{description} - AI가 만들어낸 인용일 수 있음",
                    mitigation="직접 인용 대신 일반적 설명 사용"
                ))

        # 출처 주장 감지
        for pattern, description in self.ref_patterns:
            matches = pattern.finditer(response)
            for match in matches:
                risks.append(HallucinationRisk(
                    hallucination_type=HallucinationType.INVENTED_REFERENCE,
                    risk_level=RiskLevel.MEDIUM,
                    detected_text=match.group(),
                    position=(match.start(), match.end()),
                    why_risky=f"{description} - 가짜 출처일 수 있음",
                    mitigation="'~라고 알려져 있어요' 등 일반적 표현 사용"
                ))

        # 위험 신호 감지
        for signal in self.RISK_SIGNALS:
            if signal in response:
                idx = response.find(signal)
                risks.append(HallucinationRisk(
                    hallucination_type=HallucinationType.OVERCONFIDENCE,
                    risk_level=RiskLevel.LOW,
                    detected_text=signal,
                    position=(idx, idx + len(signal)),
                    why_risky="과장된 일반화 위험",
                    mitigation="'일부에서는', '~하는 경우도 있어요' 사용"
                ))

        return risks


# =============================================================================
# 통합 환각 방지 시스템
# =============================================================================

class HallucinationPreventionSystem:
    """
    통합 환각 방지 시스템

    모든 환각 위험을 감지하고 완화
    """

    def __init__(self):
        self.factual_detector = FactualClaimDetector()
        self.assumption_detector = UserAssumptionDetector()
        self.false_memory_detector = FalseMemoryDetector()
        self.stat_detector = UnverifiedStatDetector()
        self.expert_verifier = ExpertClaimVerifier()
        self.reference_detector = FakeReferenceDetector()

        # 위험 수준별 점수
        self.risk_scores = {
            RiskLevel.HIGH: 30,
            RiskLevel.MEDIUM: 15,
            RiskLevel.LOW: 5,
        }

        logger.info("HallucinationPreventionSystem initialized")

    def check_response(
        self,
        response: str,
        user_context: Set[str] = None
    ) -> HallucinationCheckResult:
        """
        응답의 환각 위험 검사

        Args:
            response: 검사할 응답
            user_context: 사용자가 실제 언급한 정보들

        Returns:
            HallucinationCheckResult: 검사 결과
        """
        all_risks = []

        # 모든 감지기 실행
        all_risks.extend(self.factual_detector.detect(response))
        all_risks.extend(self.assumption_detector.detect(response, user_context))
        all_risks.extend(self.false_memory_detector.detect(response))
        all_risks.extend(self.stat_detector.detect(response))
        all_risks.extend(self.expert_verifier.detect(response))
        all_risks.extend(self.reference_detector.detect(response))

        # 위험 점수 계산
        risk_score = sum(self.risk_scores[r.risk_level] for r in all_risks)
        risk_score = min(100.0, risk_score)

        # 고위험 존재 여부
        has_high_risk = any(r.risk_level == RiskLevel.HIGH for r in all_risks)

        # 제안 생성
        suggestions = list(set(r.mitigation for r in all_risks))

        # 결과 생성
        result = HallucinationCheckResult(
            has_risks=len(all_risks) > 0,
            risks=all_risks,
            risk_score=risk_score,
            suggestions=suggestions
        )

        # 완화된 응답 생성
        if all_risks:
            result.mitigated_response = self._mitigate_response(response, all_risks)

        logger.info(f"Hallucination check: {len(all_risks)} risks, "
                   f"score={risk_score:.1f}, has_high_risk={has_high_risk}")

        return result

    def _mitigate_response(self, response: str, risks: List[HallucinationRisk]) -> str:
        """환각 위험 완화된 응답 생성"""
        mitigated = response

        # 고위험 항목 표시
        for risk in sorted(risks, key=lambda r: r.position[0], reverse=True):
            if risk.risk_level == RiskLevel.HIGH:
                start, end = risk.position
                mitigated = (
                    mitigated[:start] +
                    f"[확인 필요: {mitigated[start:end]}]" +
                    mitigated[end:]
                )

        return mitigated

    def get_prompt_section(self) -> str:
        """프롬프트에 삽입할 환각 방지 가이드"""
        return """
## 환각 방지 가이드 - 정확성 유지

### 절대 하지 말 것
1. **거짓 기억 유도**
   ❌ "기억하시죠?", "말씀하셨잖아요"
   ✅ "~라고 이해했는데, 맞을까요?"

2. **사용자 정보 추측**
   ❌ "아마 ~하셨을 거예요", "분명 ~때문일 거예요"
   ✅ "혹시 ~인가요?", "~일 수도 있을까요?"

3. **진단적 표현**
   ❌ "우울증이 있으시네요", "불안장애 같아요"
   ✅ "우울한 기분이 드시는군요", "불안한 마음이 느껴지시네요"

### 불확실성 표현 사용
- "~일 수 있어요"
- "~라고 알려져 있어요"
- "일반적으로는 ~"
- "제 이해로는 ~"
- "~하는 경우가 있어요"

### 통계/수치 사용 금지
❌ "80%의 사람들이..."
❌ "연구에 따르면..."
✅ "많은 사람들이..."
✅ "~하는 경우가 있어요"

### 확인 질문 활용
- "제가 잘 이해했는지 확인하고 싶은데요"
- "혹시 ~인가요?"
- "~라고 이해해도 될까요?"

### 전문 용어 사용 시
- 진단명 대신 경험/증상 중심으로 표현
- "~라고 부르기도 해요" 형태 사용
- AI 한계 인정: "정확한 판단은 전문가 상담이 필요해요"
"""


# =============================================================================
# 편의 함수
# =============================================================================

_hallucination_system: Optional[HallucinationPreventionSystem] = None


def get_hallucination_system() -> HallucinationPreventionSystem:
    """환각 방지 시스템 싱글톤 반환"""
    global _hallucination_system
    if _hallucination_system is None:
        _hallucination_system = HallucinationPreventionSystem()
    return _hallucination_system


def check_hallucination_risks(
    response: str,
    user_context: Set[str] = None
) -> HallucinationCheckResult:
    """응답의 환각 위험 빠른 검사"""
    system = get_hallucination_system()
    return system.check_response(response, user_context)


def get_hallucination_prompt_section() -> str:
    """프롬프트용 환각 방지 섹션"""
    system = get_hallucination_system()
    return system.get_prompt_section()


def has_hallucination_risk(response: str) -> bool:
    """환각 위험이 있는지 빠른 체크"""
    result = check_hallucination_risks(response)
    return any(r.risk_level == RiskLevel.HIGH for r in result.risks)
