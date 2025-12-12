"""
자기 점검 시스템 (Self-Check System)

AI 응답 생성 전후 품질 검증:
1. 통합 안전성 검사 - 모든 안전 시스템 통합
2. 품질 점수 계산 - 종합 품질 평가
3. 자동 재생성 트리거 - 문제 응답 재생성
4. 대체 응답 제안 - 안전한 대안 제공
5. 검사 리포트 생성 - 상세 검사 결과
"""

from typing import Dict, List, Optional, Tuple, Any, Callable
from enum import Enum
from dataclasses import dataclass, field
import logging
from datetime import datetime

# 다른 안전 시스템 임포트
try:
    from .response_guardrails import (
        get_guardrail_system, check_response_safety, GuardrailResult
    )
except ImportError:
    get_guardrail_system = None
    check_response_safety = None
    GuardrailResult = None

try:
    from .ethical_boundaries import (
        get_ethical_system, assess_ethical_boundaries, EthicalAssessment
    )
except ImportError:
    get_ethical_system = None
    assess_ethical_boundaries = None
    EthicalAssessment = None

try:
    from .emotional_safety import (
        get_emotional_safety_system, check_emotional_safety, EmotionalSafetyResult
    )
except ImportError:
    get_emotional_safety_system = None
    check_emotional_safety = None
    EmotionalSafetyResult = None

try:
    from .consistency_checker import (
        get_consistency_system, check_response_consistency, ConsistencyResult
    )
except ImportError:
    get_consistency_system = None
    check_response_consistency = None
    ConsistencyResult = None

try:
    from .hallucination_prevention import (
        get_hallucination_system, check_hallucination_risks, HallucinationCheckResult
    )
except ImportError:
    get_hallucination_system = None
    check_hallucination_risks = None
    HallucinationCheckResult = None

logger = logging.getLogger(__name__)


# =============================================================================
# 자기 점검 데이터 구조
# =============================================================================

class CheckCategory(Enum):
    """검사 카테고리"""
    GUARDRAILS = "guardrails"           # 가드레일
    ETHICAL = "ethical"                 # 윤리적 경계
    EMOTIONAL = "emotional"             # 감정적 안전
    CONSISTENCY = "consistency"         # 일관성
    HALLUCINATION = "hallucination"     # 환각
    QUALITY = "quality"                 # 품질


class ResponseStatus(Enum):
    """응답 상태"""
    SAFE = "safe"                       # 안전
    WARNING = "warning"                 # 경고
    NEEDS_REVISION = "needs_revision"   # 수정 필요
    BLOCKED = "blocked"                 # 차단


@dataclass
class CategoryResult:
    """카테고리별 검사 결과"""
    category: CheckCategory
    passed: bool
    score: float  # 0-100
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SelfCheckReport:
    """자기 점검 리포트"""
    response_status: ResponseStatus
    overall_score: float  # 0-100
    category_results: Dict[CheckCategory, CategoryResult] = field(default_factory=dict)
    critical_issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)
    recommended_action: str = ""
    revised_response: Optional[str] = None
    check_timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "status": self.response_status.value,
            "overall_score": self.overall_score,
            "categories": {
                cat.value: {
                    "passed": result.passed,
                    "score": result.score,
                    "issues": result.issues
                }
                for cat, result in self.category_results.items()
            },
            "critical_issues": self.critical_issues,
            "warnings": self.warnings,
            "suggestions": self.improvement_suggestions,
            "action": self.recommended_action,
            "timestamp": self.check_timestamp
        }


# =============================================================================
# 기본 품질 검사기
# =============================================================================

class BasicQualityChecker:
    """
    기본 응답 품질 검사

    길이, 구조, 공감 표현 등 기본 품질 검사
    """

    # 최소/최대 응답 길이
    MIN_LENGTH = 20
    MAX_LENGTH = 1000

    # 공감 표현 키워드
    EMPATHY_MARKERS = [
        "힘드", "어려", "마음", "느끼", "이해", "공감",
        "함께", "곁에", "들어", "~시겠", "~셨", "군요", "네요"
    ]

    # 질문 표현
    QUESTION_MARKERS = ["?", "까요", "가요", "나요", "세요"]

    # 구조화 마커
    STRUCTURE_MARKERS = ["\n", ".", "그리고", "또한", "그래서"]

    def __init__(self):
        logger.info("BasicQualityChecker initialized")

    def check(self, response: str) -> CategoryResult:
        """기본 품질 검사"""
        issues = []
        suggestions = []
        score = 100.0

        # 1. 길이 검사
        length = len(response)
        if length < self.MIN_LENGTH:
            issues.append(f"응답이 너무 짧음 ({length}자)")
            suggestions.append("더 충분한 응답을 제공하세요")
            score -= 20
        elif length > self.MAX_LENGTH:
            issues.append(f"응답이 너무 김 ({length}자)")
            suggestions.append("핵심 내용 위주로 간결하게 응답하세요")
            score -= 10

        # 2. 공감 표현 검사
        empathy_count = sum(1 for m in self.EMPATHY_MARKERS if m in response)
        if empathy_count == 0:
            issues.append("공감 표현이 없음")
            suggestions.append("공감 표현을 추가하세요 (예: '힘드셨겠어요')")
            score -= 25
        elif empathy_count < 2:
            suggestions.append("공감 표현을 더 추가하면 좋겠습니다")
            score -= 10

        # 3. 질문 포함 검사 (탐색적 대화)
        has_question = any(m in response for m in self.QUESTION_MARKERS)
        if not has_question:
            suggestions.append("탐색 질문을 포함하면 대화가 풍부해집니다")
            score -= 5

        # 4. 구조화 검사
        structure_count = sum(1 for m in self.STRUCTURE_MARKERS if m in response)
        if structure_count < 2 and length > 100:
            suggestions.append("응답을 더 구조화하면 읽기 좋습니다")
            score -= 5

        return CategoryResult(
            category=CheckCategory.QUALITY,
            passed=score >= 60,
            score=max(0, score),
            issues=issues,
            suggestions=suggestions,
            details={"length": length, "empathy_count": empathy_count}
        )


# =============================================================================
# 통합 자기 점검 시스템
# =============================================================================

class SelfCheckSystem:
    """
    통합 자기 점검 시스템

    모든 안전/품질 검사를 통합하여 응답 검증
    """

    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
        self.quality_checker = BasicQualityChecker()

        # 카테고리별 가중치
        self.category_weights = {
            CheckCategory.GUARDRAILS: 0.25,
            CheckCategory.ETHICAL: 0.20,
            CheckCategory.EMOTIONAL: 0.20,
            CheckCategory.CONSISTENCY: 0.15,
            CheckCategory.HALLUCINATION: 0.10,
            CheckCategory.QUALITY: 0.10,
        }

        # 임계값
        self.block_threshold = 30  # 이 점수 이하면 차단
        self.warning_threshold = 60  # 이 점수 이하면 경고
        self.revision_threshold = 50  # 이 점수 이하면 수정 필요

        logger.info("SelfCheckSystem initialized")

    def check_response(
        self,
        response: str,
        user_message: str = "",
        context: Optional[Dict[str, Any]] = None
    ) -> SelfCheckReport:
        """
        응답 종합 검사

        Args:
            response: 검사할 응답
            user_message: 사용자 메시지
            context: 추가 컨텍스트

        Returns:
            SelfCheckReport: 검사 리포트
        """
        context = context or {}
        category_results = {}
        critical_issues = []
        warnings = []
        suggestions = []

        # 1. 가드레일 검사
        if check_response_safety:
            guardrail_result = check_response_safety(response, self.strict_mode)
            category_results[CheckCategory.GUARDRAILS] = self._convert_guardrail_result(
                guardrail_result
            )
            if guardrail_result.blocked:
                critical_issues.append("가드레일 위반으로 차단됨")
        else:
            category_results[CheckCategory.GUARDRAILS] = CategoryResult(
                category=CheckCategory.GUARDRAILS,
                passed=True,
                score=100.0
            )

        # 2. 윤리적 경계 검사
        if assess_ethical_boundaries:
            ethical_result = assess_ethical_boundaries(user_message, response)
            category_results[CheckCategory.ETHICAL] = self._convert_ethical_result(
                ethical_result
            )
            if ethical_result.issues:
                for issue in ethical_result.issues:
                    warnings.append(f"윤리: {issue.description}")
        else:
            category_results[CheckCategory.ETHICAL] = CategoryResult(
                category=CheckCategory.ETHICAL,
                passed=True,
                score=100.0
            )

        # 3. 감정적 안전 검사
        if check_emotional_safety:
            emotional_result = check_emotional_safety(response)
            category_results[CheckCategory.EMOTIONAL] = self._convert_emotional_result(
                emotional_result
            )
            if not emotional_result.is_safe:
                for expr in emotional_result.harmful_expressions[:3]:
                    warnings.append(f"감정 안전: {expr.why_harmful}")
        else:
            category_results[CheckCategory.EMOTIONAL] = CategoryResult(
                category=CheckCategory.EMOTIONAL,
                passed=True,
                score=100.0
            )

        # 4. 일관성 검사
        if check_response_consistency:
            consistency_result = check_response_consistency(response)
            category_results[CheckCategory.CONSISTENCY] = self._convert_consistency_result(
                consistency_result
            )
            if consistency_result.warnings:
                warnings.extend([f"일관성: {w}" for w in consistency_result.warnings[:3]])
        else:
            category_results[CheckCategory.CONSISTENCY] = CategoryResult(
                category=CheckCategory.CONSISTENCY,
                passed=True,
                score=100.0
            )

        # 5. 환각 검사
        if check_hallucination_risks:
            hallucination_result = check_hallucination_risks(response)
            category_results[CheckCategory.HALLUCINATION] = self._convert_hallucination_result(
                hallucination_result
            )
            if hallucination_result.has_risks:
                for risk in hallucination_result.risks[:3]:
                    if risk.risk_level.value == "high":
                        warnings.append(f"환각 위험: {risk.why_risky}")
        else:
            category_results[CheckCategory.HALLUCINATION] = CategoryResult(
                category=CheckCategory.HALLUCINATION,
                passed=True,
                score=100.0
            )

        # 6. 기본 품질 검사
        quality_result = self.quality_checker.check(response)
        category_results[CheckCategory.QUALITY] = quality_result
        suggestions.extend(quality_result.suggestions)

        # 종합 점수 계산
        overall_score = self._calculate_overall_score(category_results)

        # 응답 상태 결정
        response_status = self._determine_status(overall_score, critical_issues)

        # 권장 조치 결정
        recommended_action = self._determine_action(response_status, category_results)

        # 개선 제안 수집
        for result in category_results.values():
            suggestions.extend(result.suggestions[:2])
        suggestions = list(set(suggestions))[:10]

        # 수정된 응답 생성 (필요시)
        revised_response = None
        if response_status in [ResponseStatus.NEEDS_REVISION, ResponseStatus.WARNING]:
            revised_response = self._generate_revised_response(response, category_results)

        # 리포트 생성
        report = SelfCheckReport(
            response_status=response_status,
            overall_score=overall_score,
            category_results=category_results,
            critical_issues=critical_issues,
            warnings=warnings,
            improvement_suggestions=suggestions,
            recommended_action=recommended_action,
            revised_response=revised_response,
            check_timestamp=datetime.now().isoformat()
        )

        logger.info(f"Self-check complete: status={response_status.value}, "
                   f"score={overall_score:.1f}")

        return report

    def _convert_guardrail_result(self, result) -> CategoryResult:
        """가드레일 결과 변환"""
        issues = [v.explanation for v in result.violations[:5]]
        score = 100 - result.risk_score

        return CategoryResult(
            category=CheckCategory.GUARDRAILS,
            passed=not result.blocked,
            score=max(0, score),
            issues=issues,
            suggestions=["가드레일 위반 항목 수정 필요"] if result.violations else [],
            details={"blocked": result.blocked, "violation_count": len(result.violations)}
        )

    def _convert_ethical_result(self, result) -> CategoryResult:
        """윤리적 경계 결과 변환"""
        issues = [i.description for i in result.issues[:5]]
        score = 100 - (len(result.issues) * 15)

        return CategoryResult(
            category=CheckCategory.ETHICAL,
            passed=len(result.issues) == 0,
            score=max(0, score),
            issues=issues,
            suggestions=result.recommended_actions[:3],
            details={
                "referral_needed": result.referral_needed,
                "ai_disclosure_needed": result.ai_disclosure_needed
            }
        )

    def _convert_emotional_result(self, result) -> CategoryResult:
        """감정적 안전 결과 변환"""
        issues = [e.why_harmful for e in result.harmful_expressions[:5]]
        score = 100 - result.risk_score

        return CategoryResult(
            category=CheckCategory.EMOTIONAL,
            passed=result.is_safe,
            score=max(0, score),
            issues=issues,
            suggestions=result.suggestions[:3],
            details={"harmful_count": len(result.harmful_expressions)}
        )

    def _convert_consistency_result(self, result) -> CategoryResult:
        """일관성 결과 변환"""
        issues = [i.description for i in result.issues[:5]]
        score = result.confidence * 100

        return CategoryResult(
            category=CheckCategory.CONSISTENCY,
            passed=result.is_consistent,
            score=max(0, score),
            issues=issues,
            suggestions=[i.suggestion for i in result.issues[:3]],
            details={"issue_count": len(result.issues)}
        )

    def _convert_hallucination_result(self, result) -> CategoryResult:
        """환각 결과 변환"""
        issues = [r.why_risky for r in result.risks[:5]]
        score = 100 - result.risk_score

        return CategoryResult(
            category=CheckCategory.HALLUCINATION,
            passed=not result.has_risks,
            score=max(0, score),
            issues=issues,
            suggestions=result.suggestions[:3],
            details={"risk_count": len(result.risks)}
        )

    def _calculate_overall_score(self, results: Dict[CheckCategory, CategoryResult]) -> float:
        """종합 점수 계산"""
        weighted_sum = 0.0
        total_weight = 0.0

        for category, result in results.items():
            weight = self.category_weights.get(category, 0.1)
            weighted_sum += result.score * weight
            total_weight += weight

        if total_weight > 0:
            return weighted_sum / total_weight
        return 0.0

    def _determine_status(
        self,
        score: float,
        critical_issues: List[str]
    ) -> ResponseStatus:
        """응답 상태 결정"""
        if critical_issues:
            return ResponseStatus.BLOCKED
        elif score < self.block_threshold:
            return ResponseStatus.BLOCKED
        elif score < self.revision_threshold:
            return ResponseStatus.NEEDS_REVISION
        elif score < self.warning_threshold:
            return ResponseStatus.WARNING
        else:
            return ResponseStatus.SAFE

    def _determine_action(
        self,
        status: ResponseStatus,
        results: Dict[CheckCategory, CategoryResult]
    ) -> str:
        """권장 조치 결정"""
        if status == ResponseStatus.BLOCKED:
            return "응답 재생성 필요 - 안전 가이드라인 위반"
        elif status == ResponseStatus.NEEDS_REVISION:
            # 가장 낮은 점수 카테고리 찾기
            lowest = min(results.values(), key=lambda r: r.score)
            return f"응답 수정 필요 - {lowest.category.value} 개선"
        elif status == ResponseStatus.WARNING:
            return "응답 사용 가능하나 개선 권장"
        else:
            return "응답 사용 가능"

    def _generate_revised_response(
        self,
        original: str,
        results: Dict[CheckCategory, CategoryResult]
    ) -> str:
        """수정된 응답 생성"""
        revised = original

        # 각 카테고리의 이슈에 따라 수정 표시
        for category, result in results.items():
            if not result.passed and result.issues:
                # 첫 번째 이슈에 대한 표시
                revised += f"\n\n[{category.value} 수정 필요: {result.issues[0]}]"

        return revised

    def should_regenerate(self, report: SelfCheckReport) -> bool:
        """응답 재생성 필요 여부"""
        return report.response_status == ResponseStatus.BLOCKED

    def get_fallback_response(self, issue_type: str = "general") -> str:
        """안전한 대체 응답 반환"""
        fallbacks = {
            "general": "말씀해 주신 내용을 듣고 있어요. 조금 더 이야기해 주시겠어요?",
            "crisis": "지금 많이 힘드신 것 같아 걱정됩니다. 전문 상담원과 이야기하시면 도움이 될 것 같아요. 자살예방상담전화 1393으로 연락해 주세요.",
            "boundary": "저는 AI 상담 도우미로서 한계가 있어요. 전문 상담사와 이야기 나누시는 것을 권해드려요.",
            "ethical": "그 부분은 제가 도움드리기 어려워요. 다른 방식으로 이야기해 볼까요?",
            "error": "죄송해요, 적절한 응답을 드리기 어려워요. 다시 한번 말씀해 주시겠어요?"
        }
        return fallbacks.get(issue_type, fallbacks["general"])

    def get_prompt_section(self) -> str:
        """프롬프트에 삽입할 자기 점검 가이드"""
        return """
## 자기 점검 체크리스트 - 응답 전 확인

### 필수 확인 (체크 안 되면 응답 불가)
□ 의학적/법적 조언 없음
□ 자해/자살 방법 정보 없음
□ 진단적 표현 없음
□ 경계 위반 없음

### 권장 확인 (가능한 모두 체크)
□ 공감 표현 포함
□ 판단/비난 표현 없음
□ 감정 최소화 없음
□ 사용자 정보 추측 없음
□ 거짓 기억 유도 없음
□ 이전 대화와 일관됨

### 품질 확인
□ 적절한 길이 (너무 짧거나 길지 않음)
□ 탐색 질문 포함
□ 구조화된 응답

### 불확실한 경우
- 확실하지 않으면 하지 않기
- 추측 대신 질문하기
- "~일 수 있어요" 표현 사용
- 전문가 연계 권유 고려
"""


# =============================================================================
# 자동 검사 데코레이터
# =============================================================================

def auto_check(strict: bool = True):
    """
    응답 자동 검사 데코레이터

    사용:
        @auto_check()
        def generate_response(message):
            return "응답 내용"
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            # 원래 응답 생성
            response = func(*args, **kwargs)

            # 자기 점검
            system = get_self_check_system()
            report = system.check_response(response)

            # 재생성 필요 여부
            if system.should_regenerate(report):
                logger.warning(f"Response blocked: {report.critical_issues}")
                return system.get_fallback_response()

            return response
        return wrapper
    return decorator


# =============================================================================
# 편의 함수
# =============================================================================

_self_check_system: Optional[SelfCheckSystem] = None


def get_self_check_system(strict_mode: bool = True) -> SelfCheckSystem:
    """자기 점검 시스템 싱글톤 반환"""
    global _self_check_system
    if _self_check_system is None:
        _self_check_system = SelfCheckSystem(strict_mode)
    return _self_check_system


def perform_self_check(
    response: str,
    user_message: str = "",
    context: Dict[str, Any] = None
) -> SelfCheckReport:
    """응답 자기 점검 수행"""
    system = get_self_check_system()
    return system.check_response(response, user_message, context)


def is_response_acceptable(response: str) -> bool:
    """응답이 수용 가능한지 빠른 체크"""
    report = perform_self_check(response)
    return report.response_status != ResponseStatus.BLOCKED


def get_self_check_prompt_section() -> str:
    """프롬프트용 자기 점검 섹션"""
    system = get_self_check_system()
    return system.get_prompt_section()


def get_safe_fallback(issue_type: str = "general") -> str:
    """안전한 대체 응답 획득"""
    system = get_self_check_system()
    return system.get_fallback_response(issue_type)
