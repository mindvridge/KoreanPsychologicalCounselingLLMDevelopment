"""
응답 검증 시스템 (Response Validator)
LLM 응답 품질 검증 및 일관성 보장

기능:
- 공감 표현 존재 여부 검증
- 문화적 적절성 검사
- 안전성 언어 검증
- 반복 응답 감지
- 응답 길이 적절성 검사
- 위기 대응 적절성 검증
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import Counter
import difflib

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """검증 수준"""
    PASS = "pass"           # 통과
    WARNING = "warning"     # 경고 (사용 가능)
    FAIL = "fail"           # 실패 (재생성 필요)
    CRITICAL = "critical"   # 치명적 (즉시 수정 필요)


@dataclass
class ValidationResult:
    """검증 결과"""
    level: ValidationLevel
    score: float  # 0-100
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        return self.level in [ValidationLevel.PASS, ValidationLevel.WARNING]

    @property
    def needs_regeneration(self) -> bool:
        return self.level in [ValidationLevel.FAIL, ValidationLevel.CRITICAL]


class ResponseValidator:
    """
    LLM 응답 품질 검증기

    심리상담 맥락에서 응답의 적절성, 공감성, 안전성을 검증합니다.
    """

    def __init__(self, strict_mode: bool = False):
        """
        초기화

        Args:
            strict_mode: 엄격 모드 (더 높은 기준 적용)
        """
        self.strict_mode = strict_mode
        self.min_score = 70 if strict_mode else 50

        # 검증 체크리스트
        self.checks = [
            ("empathy", self._check_empathy_presence, 25),
            ("safety", self._check_safety_language, 20),
            ("cultural", self._check_cultural_sensitivity, 15),
            ("length", self._check_length_appropriateness, 10),
            ("repetition", self._check_repetition, 15),
            ("prohibited", self._check_prohibited_phrases, 15),
        ]

        # 공감 표현 마커
        self.empathy_markers = {
            "reflection": [
                "군요", "시군요", "셨군요", "네요", "시네요",
                "느끼시", "힘드셨", "어려우셨", "힘들었", "어려웠"
            ],
            "validation": [
                "이해", "공감", "당연", "자연스러", "충분히",
                "그럴 수 있", "그러실 수 있", "타당", "괜찮"
            ],
            "acknowledgment": [
                "듣고 보니", "말씀하신", "이야기해 주", "나눠 주",
                "그런 상황", "그런 마음"
            ]
        }

        # 금지 표현
        self.prohibited_phrases = {
            "dismissive": [
                "그 정도는", "다른 사람들도", "별거 아니", "대수롭지 않",
                "너무 예민", "생각이 많으시", "걱정 마세요"
            ],
            "superficial": [
                "힘내세요", "힘내요", "화이팅", "파이팅",
                "괜찮아질 거예요", "다 잘 될 거예요", "시간이 해결"
            ],
            "judgmental": [
                "잘못", "틀렸", "왜 그랬", "왜 그러셨",
                "그러면 안 돼", "그러시면 안", "당연히", "마땅히"
            ],
            "diagnostic": [
                "우울증인 것 같", "불안장애", "~증상이", "진단",
                "치료가 필요", "병원에 가셔야"
            ]
        }

        # 위기 대응 필수 요소
        self.crisis_required_elements = {
            "hotline": ["1393", "1577-0199", "119"],
            "safety": ["안전", "안전이", "안전을"],
            "empathy": ["힘드", "고통", "어려"]
        }

        logger.info(f"ResponseValidator initialized (strict_mode={strict_mode})")

    def validate(
        self,
        response: str,
        context: Dict[str, Any]
    ) -> ValidationResult:
        """
        응답 종합 검증

        Args:
            response: LLM 응답
            context: 컨텍스트 정보
                - user_message: 사용자 메시지
                - emotion: 감지된 감정
                - crisis_detected: 위기 감지 여부
                - conversation_history: 대화 이력

        Returns:
            ValidationResult: 검증 결과
        """
        if not response or not response.strip():
            return ValidationResult(
                level=ValidationLevel.FAIL,
                score=0,
                issues=["빈 응답"],
                suggestions=["응답을 재생성하세요"]
            )

        total_score = 100
        all_issues = []
        all_suggestions = []
        check_details = {}

        # 각 검증 수행
        for check_name, check_func, weight in self.checks:
            result = check_func(response, context)
            check_details[check_name] = result

            if not result["passed"]:
                penalty = weight * result.get("severity", 1.0)
                total_score -= penalty
                all_issues.append(result["issue"])
                if result.get("suggestion"):
                    all_suggestions.append(result["suggestion"])

        # 위기 상황 특별 검증
        if context.get("crisis_detected"):
            crisis_result = self._check_crisis_response(response, context)
            check_details["crisis_response"] = crisis_result
            if not crisis_result["passed"]:
                total_score -= 30  # 위기 대응 실패는 큰 감점
                all_issues.append(crisis_result["issue"])
                all_suggestions.append(crisis_result["suggestion"])

        # 최종 레벨 결정
        if total_score >= 80:
            level = ValidationLevel.PASS
        elif total_score >= 60:
            level = ValidationLevel.WARNING
        elif total_score >= 40:
            level = ValidationLevel.FAIL
        else:
            level = ValidationLevel.CRITICAL

        return ValidationResult(
            level=level,
            score=max(0, total_score),
            issues=all_issues,
            suggestions=all_suggestions,
            details=check_details
        )

    def _check_empathy_presence(
        self,
        response: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """공감 표현 존재 여부 검증"""
        empathy_score = 0
        found_markers = []

        for category, markers in self.empathy_markers.items():
            for marker in markers:
                if marker in response:
                    empathy_score += 1
                    found_markers.append(f"{category}:{marker}")

        # 최소 2개의 공감 마커 필요
        passed = empathy_score >= 2

        return {
            "passed": passed,
            "issue": "공감 표현 부족" if not passed else None,
            "suggestion": "감정 반영 또는 수용적 표현을 추가하세요" if not passed else None,
            "severity": 1.0 if empathy_score == 0 else 0.5,
            "details": {
                "empathy_score": empathy_score,
                "found_markers": found_markers
            }
        }

    def _check_safety_language(
        self,
        response: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """안전성 언어 검증"""
        issues = []

        # 위험한 조언 체크
        dangerous_patterns = [
            (r"혼자.*해결", "혼자 해결하라는 조언"),
            (r"아무에게도.*말하지", "비밀 유지 강요"),
            (r"약을.*먹으면", "약물 권유"),
            (r"술을.*마시면", "음주 권유"),
        ]

        for pattern, issue_name in dangerous_patterns:
            if re.search(pattern, response):
                issues.append(issue_name)

        passed = len(issues) == 0

        return {
            "passed": passed,
            "issue": f"안전하지 않은 표현: {', '.join(issues)}" if issues else None,
            "suggestion": "안전한 표현으로 수정하세요" if not passed else None,
            "severity": 1.5,  # 안전 문제는 가중 감점
            "details": {"issues": issues}
        }

    def _check_cultural_sensitivity(
        self,
        response: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """문화적 적절성 검증"""
        issues = []

        # 서양 문화 중심 표현 체크
        western_patterns = [
            (r"개인.*자유", "지나친 개인주의 강조"),
            (r"부모.*떠나", "관계 단절 권유"),
            (r"독립.*해야", "급진적 독립 권유"),
        ]

        for pattern, issue_name in western_patterns:
            if re.search(pattern, response):
                issues.append(issue_name)

        # 한국 문화 이해 표현 확인
        cultural_understanding = any(marker in response for marker in [
            "가족", "관계", "체면", "기대", "효도", "부모님"
        ])

        # 문화적 맥락이 중요한 상황에서 이해 표현 부재
        user_message = context.get("user_message", "")
        cultural_keywords = ["부모", "가족", "직장", "상사", "선배"]
        needs_cultural = any(kw in user_message for kw in cultural_keywords)

        if needs_cultural and not cultural_understanding:
            issues.append("문화적 맥락 반영 부족")

        passed = len(issues) == 0

        return {
            "passed": passed,
            "issue": f"문화적 적절성 문제: {', '.join(issues)}" if issues else None,
            "suggestion": "한국 문화 맥락을 고려한 표현으로 수정하세요" if not passed else None,
            "severity": 0.7,
            "details": {"issues": issues, "cultural_understanding": cultural_understanding}
        }

    def _check_length_appropriateness(
        self,
        response: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """응답 길이 적절성 검증"""
        char_count = len(response)
        sentence_count = len(re.findall(r'[.?!。]', response))

        # 적절한 길이: 50-300자, 2-5문장
        too_short = char_count < 30
        too_long = char_count > 400
        too_few_sentences = sentence_count < 1
        too_many_sentences = sentence_count > 6

        issues = []
        if too_short:
            issues.append("너무 짧음")
        if too_long:
            issues.append("너무 김")
        if too_few_sentences:
            issues.append("문장이 부족함")
        if too_many_sentences:
            issues.append("문장이 너무 많음")

        passed = len(issues) == 0

        return {
            "passed": passed,
            "issue": f"길이 문제: {', '.join(issues)}" if issues else None,
            "suggestion": "2-4문장, 100-250자 내외로 조정하세요" if not passed else None,
            "severity": 0.5,
            "details": {
                "char_count": char_count,
                "sentence_count": sentence_count
            }
        }

    def _check_repetition(
        self,
        response: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """반복 응답 검증"""
        conversation_history = context.get("conversation_history", [])

        if not conversation_history:
            return {"passed": True, "issue": None, "severity": 0}

        # 이전 응답들과 유사도 비교
        max_similarity = 0
        similar_response = None

        for turn in conversation_history[-5:]:  # 최근 5개 확인
            if turn.get("role") == "assistant":
                prev_response = turn.get("content", "")
                similarity = self._calculate_similarity(response, prev_response)
                if similarity > max_similarity:
                    max_similarity = similarity
                    similar_response = prev_response[:50]

        # 70% 이상 유사하면 반복으로 판단
        passed = max_similarity < 0.7

        return {
            "passed": passed,
            "issue": f"이전 응답과 {max_similarity*100:.0f}% 유사" if not passed else None,
            "suggestion": "새로운 관점이나 표현으로 응답하세요" if not passed else None,
            "severity": 1.0,
            "details": {
                "max_similarity": max_similarity,
                "similar_to": similar_response
            }
        }

    def _check_prohibited_phrases(
        self,
        response: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """금지 표현 검증"""
        found_prohibited = []

        for category, phrases in self.prohibited_phrases.items():
            for phrase in phrases:
                if phrase in response:
                    found_prohibited.append(f"{category}:{phrase}")

        passed = len(found_prohibited) == 0

        severity = 1.0
        if any("diagnostic" in p for p in found_prohibited):
            severity = 1.5  # 진단적 표현은 더 높은 감점

        return {
            "passed": passed,
            "issue": f"금지 표현 사용: {', '.join(found_prohibited)}" if not passed else None,
            "suggestion": "피상적 위로나 판단적 표현을 제거하세요" if not passed else None,
            "severity": severity,
            "details": {"found_prohibited": found_prohibited}
        }

    def _check_crisis_response(
        self,
        response: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """위기 대응 적절성 검증"""
        missing_elements = []

        # 핫라인 번호 포함 확인
        has_hotline = any(
            hotline in response
            for hotline in self.crisis_required_elements["hotline"]
        )
        if not has_hotline:
            missing_elements.append("전문 상담 전화번호")

        # 안전 언급 확인
        has_safety = any(
            word in response
            for word in self.crisis_required_elements["safety"]
        )
        if not has_safety:
            missing_elements.append("안전 관련 언급")

        # 공감 표현 확인
        has_empathy = any(
            word in response
            for word in self.crisis_required_elements["empathy"]
        )
        if not has_empathy:
            missing_elements.append("공감 표현")

        passed = len(missing_elements) == 0

        return {
            "passed": passed,
            "issue": f"위기 대응 필수 요소 누락: {', '.join(missing_elements)}" if not passed else None,
            "suggestion": "자살예방상담전화(1393), 안전 확인, 공감 표현을 포함하세요" if not passed else None,
            "severity": 2.0,  # 위기 대응 실패는 매우 심각
            "details": {
                "missing_elements": missing_elements,
                "has_hotline": has_hotline,
                "has_safety": has_safety,
                "has_empathy": has_empathy
            }
        }

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """두 텍스트의 유사도 계산"""
        if not text1 or not text2:
            return 0.0

        # 정규화
        text1 = re.sub(r'\s+', ' ', text1.lower().strip())
        text2 = re.sub(r'\s+', ' ', text2.lower().strip())

        # SequenceMatcher를 사용한 유사도 계산
        return difflib.SequenceMatcher(None, text1, text2).ratio()

    def suggest_improvements(
        self,
        response: str,
        validation_result: ValidationResult
    ) -> str:
        """
        개선 제안 생성

        Args:
            response: 원본 응답
            validation_result: 검증 결과

        Returns:
            str: 개선 제안 텍스트
        """
        if validation_result.is_valid and not validation_result.issues:
            return "응답이 적절합니다."

        suggestions = ["## 응답 개선 제안\n"]

        for issue, suggestion in zip(
            validation_result.issues,
            validation_result.suggestions
        ):
            suggestions.append(f"- **문제**: {issue}")
            if suggestion:
                suggestions.append(f"  - **제안**: {suggestion}")

        # 점수별 추가 조언
        if validation_result.score < 50:
            suggestions.append("\n### 주요 개선 필요")
            suggestions.append("응답을 처음부터 재구성하는 것을 권장합니다.")
        elif validation_result.score < 70:
            suggestions.append("\n### 부분 수정 필요")
            suggestions.append("위 제안사항을 반영하여 응답을 수정하세요.")

        return "\n".join(suggestions)


class ResponseRegenerator:
    """
    응답 재생성 관리자

    검증 실패 시 응답을 개선하여 재생성합니다.
    """

    def __init__(self, validator: ResponseValidator, max_retries: int = 3):
        """
        초기화

        Args:
            validator: 응답 검증기
            max_retries: 최대 재시도 횟수
        """
        self.validator = validator
        self.max_retries = max_retries

    def get_regeneration_prompt(
        self,
        original_response: str,
        validation_result: ValidationResult,
        context: Dict[str, Any]
    ) -> str:
        """
        재생성을 위한 프롬프트 생성

        Args:
            original_response: 원본 응답
            validation_result: 검증 결과
            context: 컨텍스트

        Returns:
            str: 재생성 프롬프트
        """
        issues_text = "\n".join(f"- {issue}" for issue in validation_result.issues)
        suggestions_text = "\n".join(
            f"- {suggestion}" for suggestion in validation_result.suggestions
        )

        prompt = f"""이전 응답에 문제가 발견되었습니다. 다음 사항을 수정하여 새로운 응답을 생성하세요.

## 이전 응답
{original_response}

## 발견된 문제
{issues_text}

## 개선 방향
{suggestions_text}

## 요청사항
위 문제를 해결한 새로운 응답을 작성하세요.
- 공감적 표현을 포함하세요
- 피상적 위로는 피하세요
- 2-4문장의 적절한 길이로 작성하세요
- 한국 문화적 맥락을 고려하세요

새로운 응답:"""

        return prompt

    def should_regenerate(self, validation_result: ValidationResult) -> bool:
        """재생성 필요 여부 판단"""
        return validation_result.needs_regeneration


# 편의 함수
def validate_response(
    response: str,
    user_message: str,
    emotion: Optional[str] = None,
    crisis_detected: bool = False,
    conversation_history: Optional[List[Dict]] = None
) -> ValidationResult:
    """
    응답 검증 편의 함수

    Args:
        response: LLM 응답
        user_message: 사용자 메시지
        emotion: 감지된 감정
        crisis_detected: 위기 감지 여부
        conversation_history: 대화 이력

    Returns:
        ValidationResult: 검증 결과
    """
    validator = ResponseValidator()
    context = {
        "user_message": user_message,
        "emotion": emotion,
        "crisis_detected": crisis_detected,
        "conversation_history": conversation_history or []
    }
    return validator.validate(response, context)


if __name__ == "__main__":
    # 테스트
    print("=== 응답 검증 시스템 테스트 ===\n")

    validator = ResponseValidator()

    test_cases = [
        {
            "name": "좋은 응답",
            "response": "많이 힘드셨군요. 직장에서 그런 일을 겪으시면 정말 마음이 무거우셨을 것 같아요. "
                       "어떤 상황이 특히 힘드셨는지 조금 더 이야기해 주실 수 있을까요?",
            "context": {
                "user_message": "직장에서 상사한테 혼났어요",
                "emotion": "분노",
                "crisis_detected": False
            }
        },
        {
            "name": "피상적 위로",
            "response": "힘내세요! 다 잘 될 거예요. 괜찮아질 거예요.",
            "context": {
                "user_message": "요즘 너무 우울해요",
                "emotion": "우울",
                "crisis_detected": False
            }
        },
        {
            "name": "위기 대응 부족",
            "response": "많이 힘드시군요. 잠시 쉬어가시는 건 어떨까요?",
            "context": {
                "user_message": "더 이상 살고 싶지 않아요",
                "emotion": "절망",
                "crisis_detected": True
            }
        },
        {
            "name": "적절한 위기 대응",
            "response": "지금 정말 힘든 상황에 계시군요. 그 고통이 얼마나 큰지 느껴집니다. "
                       "당신의 안전이 가장 중요합니다. 지금 바로 자살예방상담전화 1393에 연락해 주세요. "
                       "24시간 전문 상담사가 함께 해드릴 수 있습니다.",
            "context": {
                "user_message": "더 이상 살고 싶지 않아요",
                "emotion": "절망",
                "crisis_detected": True
            }
        },
    ]

    for test in test_cases:
        print(f"### {test['name']}")
        print(f"응답: {test['response'][:80]}...")
        print(f"상황: {test['context'].get('user_message', '')}")

        result = validator.validate(test["response"], test["context"])

        print(f"\n결과: {result.level.value} (점수: {result.score:.0f})")
        if result.issues:
            print(f"문제점: {', '.join(result.issues)}")
        if result.suggestions:
            print(f"제안: {', '.join(result.suggestions)}")
        print("-" * 60 + "\n")
