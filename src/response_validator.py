"""
응답 검증 시스템 v2.1 (Enhanced Response Validator)
LLM 응답 품질 검증, 자동 수정 및 일관성 보장

기능:
- 공감 표현 존재 여부 검증
- 문화적 적절성 검사
- 안전성 언어 검증
- 반복 응답 감지
- 응답 길이 적절성 검사
- 위기 대응 적절성 검증
- 질문 개수 최적화 검증
- 자동 응답 개선/보완
- 멀티스테이지 검증 파이프라인
- 실시간 품질 점수 트래킹
- 한국어 자연스러움 후처리 (NEW in v2.1)
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import Counter
import difflib

# Korean naturalizer for natural Korean responses
try:
    from korean_naturalizer import ResponsePolisher
    NATURALIZER_AVAILABLE = True
except ImportError:
    NATURALIZER_AVAILABLE = False

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

        # 검증 체크리스트 (NEW: question_count 추가)
        self.checks = [
            ("empathy", self._check_empathy_presence, 25),
            ("safety", self._check_safety_language, 20),
            ("cultural", self._check_cultural_sensitivity, 15),
            ("length", self._check_length_appropriateness, 10),
            ("repetition", self._check_repetition, 15),
            ("prohibited", self._check_prohibited_phrases, 10),
            ("question_count", self._check_question_count, 5),  # NEW
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

    def _check_question_count(
        self,
        response: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """질문 개수 최적화 검증 (NEW)"""
        # 물음표로 끝나는 문장 개수
        questions = re.findall(r'[^.!?]*\?', response)
        question_count = len(questions)

        # 이상적인 질문 개수: 1개
        # 허용 범위: 0-2개
        if question_count == 1:
            return {
                "passed": True,
                "issue": None,
                "severity": 0,
                "details": {"question_count": question_count, "optimal": True}
            }
        elif question_count == 0:
            return {
                "passed": True,  # 질문 없어도 허용
                "issue": None,
                "severity": 0,
                "details": {"question_count": question_count, "suggestion": "탐색 질문 추가 권장"}
            }
        elif question_count == 2:
            return {
                "passed": True,
                "issue": None,
                "severity": 0,
                "details": {"question_count": question_count, "warning": "질문이 2개입니다"}
            }
        else:
            return {
                "passed": False,
                "issue": f"질문이 {question_count}개로 너무 많음 (권장: 1개)",
                "suggestion": "한 번에 하나의 질문만 하세요",
                "severity": 0.8,
                "details": {"question_count": question_count, "questions": questions}
            }

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


# =============================================================================
# NEW: 자동 응답 개선 시스템 (Auto Response Enhancer)
# =============================================================================

class ResponseEnhancer:
    """
    응답 자동 개선 시스템 (NEW)

    검증 결과를 바탕으로 응답을 자동으로 보완/수정합니다.
    LLM 재생성 없이 규칙 기반으로 빠르게 개선합니다.
    """

    def __init__(self):
        # 공감 표현 템플릿
        self.empathy_templates = {
            "우울": [
                "많이 힘드셨겠어요.",
                "마음이 무거우셨을 것 같아요.",
                "그런 감정을 느끼시는 건 자연스러운 거예요."
            ],
            "불안": [
                "많이 걱정되셨겠어요.",
                "불안한 마음이 크셨을 것 같아요.",
                "그런 상황에서 걱정이 드시는 건 당연해요."
            ],
            "분노": [
                "정말 화가 나셨겠어요.",
                "그런 상황이라면 누구나 화가 날 수 있어요.",
                "답답하고 속상하셨겠어요."
            ],
            "스트레스": [
                "많이 지치셨겠어요.",
                "버거우셨을 것 같아요.",
                "힘든 상황에서 잘 버텨오셨네요."
            ],
            "default": [
                "말씀 들으니 마음이 쓰이네요.",
                "그런 마음이 드셨군요.",
                "충분히 그러실 수 있어요."
            ]
        }

        # 피상적 표현 → 공감적 표현 변환 맵
        self.replacement_map = {
            "힘내세요": "많이 힘드셨겠어요",
            "힘내요": "지금 많이 지치셨을 것 같아요",
            "괜찮아질 거예요": "지금 이 순간이 힘드시죠",
            "다 잘 될 거예요": "지금 느끼시는 감정이 중요해요",
            "화이팅": "함께 이야기 나눠요",
            "파이팅": "천천히 얘기해 주세요",
            "걱정 마세요": "걱정이 되시는 거 이해해요",
            "별거 아니에요": "그런 마음이 드셨군요",
        }

        # 질문 템플릿
        self.follow_up_questions = {
            "exploration": [
                "조금 더 자세히 이야기해 주실 수 있을까요?",
                "어떤 부분이 특히 힘드셨어요?",
                "그때 어떤 마음이 드셨어요?"
            ],
            "emotion": [
                "그 상황에서 어떤 감정이 드셨어요?",
                "지금은 어떤 마음이세요?",
                "그때 어떤 느낌이셨어요?"
            ],
            "support": [
                "주변에 이야기 나눌 분이 계신가요?",
                "평소에 마음이 힘들 때 어떻게 하세요?",
                "조금이라도 도움이 되는 것이 있을까요?"
            ]
        }

        logger.info("ResponseEnhancer initialized")

    def enhance(
        self,
        response: str,
        validation_result: ValidationResult,
        context: Dict[str, Any]
    ) -> Tuple[str, List[str]]:
        """
        응답 자동 개선

        Args:
            response: 원본 응답
            validation_result: 검증 결과
            context: 컨텍스트

        Returns:
            Tuple[str, List[str]]: (개선된 응답, 적용된 개선 목록)
        """
        enhanced = response
        applied_enhancements = []

        # 1. 피상적 표현 대체
        for old_phrase, new_phrase in self.replacement_map.items():
            if old_phrase in enhanced:
                enhanced = enhanced.replace(old_phrase, new_phrase)
                applied_enhancements.append(f"표현 대체: '{old_phrase}' → '{new_phrase}'")

        # 2. 공감 표현 부족시 추가
        details = validation_result.details.get("empathy", {})
        if details.get("passed") == False or details.get("details", {}).get("empathy_score", 0) < 2:
            emotion = context.get("emotion", "default")
            templates = self.empathy_templates.get(emotion, self.empathy_templates["default"])
            empathy_phrase = templates[0]

            # 응답 시작 부분에 공감 표현 추가
            if not any(marker in enhanced[:50] for marker in ["군요", "겠어요", "네요"]):
                enhanced = empathy_phrase + " " + enhanced
                applied_enhancements.append(f"공감 표현 추가: '{empathy_phrase}'")

        # 3. 질문 없을 때 추가 (탐색 단계인 경우)
        details = validation_result.details.get("question_count", {})
        question_count = details.get("details", {}).get("question_count", 0)
        turn_count = context.get("turn_count", 0)

        if question_count == 0 and turn_count < 8:  # 탐색 단계
            if "?" not in enhanced:
                questions = self.follow_up_questions["exploration"]
                enhanced = enhanced.rstrip() + " " + questions[0]
                applied_enhancements.append("탐색 질문 추가")

        # 4. 너무 긴 응답 축약
        if len(enhanced) > 400:
            sentences = re.split(r'(?<=[.!?])\s+', enhanced)
            if len(sentences) > 4:
                enhanced = ' '.join(sentences[:4])
                applied_enhancements.append("응답 길이 축약 (4문장)")

        return enhanced, applied_enhancements

    def add_crisis_resources(self, response: str) -> str:
        """위기 자원 정보 추가"""
        crisis_info = "\n\n🆘 전문 도움이 필요하시면:\n- 자살예방상담전화: 1393 (24시간)\n- 정신건강위기상담전화: 1577-0199"

        if "1393" not in response and "1577-0199" not in response:
            return response + crisis_info
        return response


# =============================================================================
# NEW: 멀티스테이지 검증 파이프라인 (Multi-Stage Validation Pipeline)
# =============================================================================

class ValidationPipeline:
    """
    멀티스테이지 검증 파이프라인 (NEW)

    [응답 생성] → [1차 검증] → [자동 수정] → [2차 검증] → [출력]

    자동 수정으로 해결 가능한 문제는 재생성 없이 처리합니다.
    """

    def __init__(
        self,
        strict_mode: bool = False,
        auto_enhance: bool = True,
        naturalize: bool = True
    ):
        """
        초기화

        Args:
            strict_mode: 엄격 검증 모드
            auto_enhance: 자동 개선 활성화
            naturalize: 한국어 자연스러움 후처리 활성화
        """
        self.validator = ResponseValidator(strict_mode=strict_mode)
        self.enhancer = ResponseEnhancer() if auto_enhance else None
        self.auto_enhance = auto_enhance

        # 한국어 자연스러움 처리기
        self.naturalizer = None
        self.naturalize = naturalize
        if naturalize and NATURALIZER_AVAILABLE:
            self.naturalizer = ResponsePolisher()
            logger.info("Korean naturalizer enabled")
        elif naturalize and not NATURALIZER_AVAILABLE:
            logger.warning("Korean naturalizer not available - module not found")

        # 품질 추적
        self.quality_history: List[Dict[str, Any]] = []
        self.total_processed = 0
        self.auto_enhanced_count = 0
        self.naturalized_count = 0
        self.regeneration_count = 0

        logger.info(f"ValidationPipeline initialized (strict={strict_mode}, auto_enhance={auto_enhance}, naturalize={naturalize})")

    def process(
        self,
        response: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        응답 처리 파이프라인

        Args:
            response: LLM 응답
            context: 컨텍스트

        Returns:
            Dict: {
                "response": 최종 응답,
                "original_response": 원본 응답,
                "validation": 검증 결과,
                "enhanced": 개선 여부,
                "enhancements": 적용된 개선 목록,
                "needs_regeneration": 재생성 필요 여부,
                "quality_score": 품질 점수
            }
        """
        self.total_processed += 1
        result = {
            "original_response": response,
            "enhanced": False,
            "enhancements": [],
            "needs_regeneration": False
        }

        # 1차 검증
        validation_result = self.validator.validate(response, context)
        result["validation_stage1"] = {
            "level": validation_result.level.value,
            "score": validation_result.score,
            "issues": validation_result.issues
        }

        # 위기 상황 특별 처리
        if context.get("crisis_detected"):
            if self.enhancer:
                response = self.enhancer.add_crisis_resources(response)
                result["enhancements"].append("위기 자원 정보 추가")

        # 2. 자동 개선 시도 (PASS가 아닌 경우)
        if self.auto_enhance and self.enhancer and validation_result.level != ValidationLevel.PASS:
            enhanced_response, enhancements = self.enhancer.enhance(
                response, validation_result, context
            )

            if enhancements:
                self.auto_enhanced_count += 1
                result["enhanced"] = True
                result["enhancements"] = enhancements
                response = enhanced_response

                # 2차 검증
                validation_result = self.validator.validate(response, context)
                result["validation_stage2"] = {
                    "level": validation_result.level.value,
                    "score": validation_result.score,
                    "issues": validation_result.issues
                }

        # 3. 한국어 자연스러움 처리 (최종 단계)
        naturalness_info = {}
        if self.naturalizer and not validation_result.needs_regeneration:
            # 감정 컨텍스트 추출
            emotion = context.get("detected_emotion") or context.get("emotion")
            turn_count = context.get("turn_count", 0)

            polish_result = self.naturalizer.polish(
                response,
                emotion=emotion,
                turn_count=turn_count
            )

            if polish_result["changes"]:
                self.naturalized_count += 1
                response = polish_result["response"]
                naturalness_info = {
                    "applied": True,
                    "naturalness_score": polish_result["naturalness_score"],
                    "changes": polish_result["changes"]
                }
                result["enhancements"].extend([f"자연스러움: {c}" for c in polish_result["changes"]])
            else:
                naturalness_info = {"applied": False, "naturalness_score": polish_result["naturalness_score"]}

        result["naturalization"] = naturalness_info

        # 4. 최종 결정
        result["response"] = response
        result["validation"] = validation_result
        result["quality_score"] = validation_result.score
        result["needs_regeneration"] = validation_result.needs_regeneration

        if result["needs_regeneration"]:
            self.regeneration_count += 1

        # 품질 기록
        self._track_quality(result)

        return result

    def _track_quality(self, result: Dict[str, Any]):
        """품질 추적"""
        naturalness_score = result.get("naturalization", {}).get("naturalness_score")

        self.quality_history.append({
            "score": result["quality_score"],
            "enhanced": result["enhanced"],
            "naturalized": result.get("naturalization", {}).get("applied", False),
            "naturalness_score": naturalness_score,
            "needs_regeneration": result["needs_regeneration"],
            "issues_count": len(result.get("validation_stage1", {}).get("issues", []))
        })

        # 최근 100개만 유지
        if len(self.quality_history) > 100:
            self.quality_history = self.quality_history[-100:]

    def get_statistics(self) -> Dict[str, Any]:
        """품질 통계 반환"""
        if not self.quality_history:
            return {"message": "No data yet"}

        scores = [h["score"] for h in self.quality_history]
        naturalness_scores = [h["naturalness_score"] for h in self.quality_history if h.get("naturalness_score")]

        stats = {
            "total_processed": self.total_processed,
            "auto_enhanced_count": self.auto_enhanced_count,
            "auto_enhance_rate": self.auto_enhanced_count / max(1, self.total_processed),
            "naturalized_count": self.naturalized_count,
            "naturalize_rate": self.naturalized_count / max(1, self.total_processed),
            "regeneration_count": self.regeneration_count,
            "regeneration_rate": self.regeneration_count / max(1, self.total_processed),
            "average_score": sum(scores) / len(scores),
            "min_score": min(scores),
            "max_score": max(scores),
            "score_distribution": {
                "excellent (90+)": sum(1 for s in scores if s >= 90),
                "good (70-89)": sum(1 for s in scores if 70 <= s < 90),
                "fair (50-69)": sum(1 for s in scores if 50 <= s < 70),
                "poor (<50)": sum(1 for s in scores if s < 50)
            }
        }

        # 자연스러움 점수 통계 추가
        if naturalness_scores:
            stats["naturalness"] = {
                "average": sum(naturalness_scores) / len(naturalness_scores),
                "min": min(naturalness_scores),
                "max": max(naturalness_scores)
            }

        return stats

    def get_recent_issues(self, n: int = 10) -> List[Dict[str, Any]]:
        """최근 이슈 목록"""
        issues_list = []
        for h in self.quality_history[-n:]:
            if h.get("issues_count", 0) > 0:
                issues_list.append(h)
        return issues_list


# =============================================================================
# NEW: 품질 메트릭 추적기 (Quality Metrics Tracker)
# =============================================================================

class QualityMetricsTracker:
    """
    품질 메트릭 실시간 추적기 (NEW)

    응답 품질을 시간대별로 추적하고 트렌드를 분석합니다.
    """

    def __init__(self):
        from datetime import datetime
        from collections import defaultdict

        self.metrics = defaultdict(list)
        self.hourly_scores = defaultdict(list)
        self.issue_frequency = Counter()
        self.start_time = datetime.now()

    def record(
        self,
        score: float,
        issues: List[str],
        metadata: Optional[Dict] = None
    ):
        """메트릭 기록"""
        from datetime import datetime

        timestamp = datetime.now()
        hour_key = timestamp.strftime("%Y-%m-%d %H:00")

        self.metrics["scores"].append(score)
        self.metrics["timestamps"].append(timestamp)
        self.hourly_scores[hour_key].append(score)

        for issue in issues:
            self.issue_frequency[issue] += 1

        if metadata:
            for key, value in metadata.items():
                self.metrics[key].append(value)

    def get_trend(self, hours: int = 24) -> Dict[str, Any]:
        """시간대별 트렌드"""
        from datetime import datetime, timedelta

        cutoff = datetime.now() - timedelta(hours=hours)

        recent_hours = {}
        for hour_key, scores in self.hourly_scores.items():
            try:
                hour_dt = datetime.strptime(hour_key, "%Y-%m-%d %H:00")
                if hour_dt >= cutoff:
                    recent_hours[hour_key] = {
                        "average": sum(scores) / len(scores),
                        "count": len(scores)
                    }
            except:
                pass

        return {
            "hourly_trend": recent_hours,
            "top_issues": self.issue_frequency.most_common(5),
            "total_records": len(self.metrics["scores"])
        }

    def get_summary(self) -> Dict[str, Any]:
        """전체 요약"""
        scores = self.metrics["scores"]
        if not scores:
            return {"message": "No data"}

        return {
            "total_responses": len(scores),
            "average_score": sum(scores) / len(scores),
            "score_std": self._std(scores),
            "top_issues": self.issue_frequency.most_common(10),
            "quality_distribution": {
                "excellent": sum(1 for s in scores if s >= 90) / len(scores) * 100,
                "good": sum(1 for s in scores if 70 <= s < 90) / len(scores) * 100,
                "fair": sum(1 for s in scores if 50 <= s < 70) / len(scores) * 100,
                "poor": sum(1 for s in scores if s < 50) / len(scores) * 100
            }
        }

    def _std(self, values: List[float]) -> float:
        """표준편차 계산"""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5


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
