"""
위기 대응 2단계 시스템 v2.0 (Enhanced Crisis Response System)
Multi-Stage Crisis Detection and Response

기존 단순 키워드 감지를 넘어서:
1단계: 키워드 감지 (기존)
2단계: 맥락 분석 (NEW) - 시제, 의도, 구체성 분석
3단계: 차등 대응 (NEW) - 위험 수준별 맞춤 대응

특징:
- 과거형 vs 현재형 구분 ("그때 죽고 싶었어요" vs "지금 죽고 싶어요")
- 구체적 계획 유무 파악
- 보호 요인 탐색
- 단계별 차등 대응
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


# =============================================================================
# 열거형 및 데이터 클래스
# =============================================================================

class CrisisLevel(Enum):
    """위기 수준"""
    IMMINENT = "imminent"      # 즉각적 위험 (자살 시도 중, 구체적 계획)
    HIGH = "high"              # 고위험 (현재 자살 사고, 수단 접근 가능)
    MODERATE = "moderate"      # 중위험 (자살 사고 있으나 계획 없음)
    LOW = "low"                # 저위험 (과거 경험 언급, 모호한 표현)
    NONE = "none"              # 위험 없음


class TemporalContext(Enum):
    """시제 맥락"""
    PAST = "past"              # 과거 경험
    CURRENT = "current"        # 현재 상태
    FUTURE = "future"          # 미래 의도
    AMBIGUOUS = "ambiguous"    # 모호함


@dataclass
class ContextualAnalysis:
    """맥락 분석 결과"""
    temporal: TemporalContext
    has_specific_plan: bool
    has_means_access: bool
    has_timeline: bool
    protective_factors: List[str]
    risk_factors: List[str]
    raw_indicators: Dict[str, bool]


@dataclass
class CrisisAssessment:
    """위기 평가 결과"""
    level: CrisisLevel
    confidence: float
    keyword_detected: bool
    contextual_analysis: ContextualAnalysis
    recommended_response: str
    resources: List[Dict[str, str]]
    follow_up_questions: List[str]
    safety_planning_needed: bool


# =============================================================================
# 2단계: 맥락 분석기 (Contextual Analyzer)
# =============================================================================

class ContextualCrisisAnalyzer:
    """
    2단계 맥락 분석기 (NEW)

    키워드가 감지된 후 맥락을 분석하여
    실제 위험 수준을 정확하게 평가합니다.
    """

    def __init__(self):
        # 시제 표현 사전
        self.temporal_markers = {
            "past": [
                "었", "았", "었어", "았어", "었었", "았었",
                "예전에", "그때", "전에", "과거에", "옛날에",
                "한 적", "적이 있", "경험", "기억"
            ],
            "current": [
                "지금", "현재", "오늘", "요즘", "이제",
                "계속", "여전히", "아직도", "지금도"
            ],
            "future": [
                "할 거", "할거", "할게", "하려고", "하고 싶",
                "계획", "생각", "결심", "다음에", "나중에",
                "오늘 밤", "내일"
            ]
        }

        # 구체적 계획 지표
        self.plan_indicators = [
            "방법", "어떻게", "언제", "어디서",
            "준비", "구했", "샀", "찾았",
            "유서", "편지", "정리", "맡기"
        ]

        # 수단 접근 지표
        self.means_indicators = [
            "약", "줄", "가스", "다리", "옥상", "높은 곳",
            "칼", "면도기", "목", "손목", "차"
        ]

        # 시간 압박 지표
        self.timeline_indicators = [
            "오늘", "지금", "당장", "바로", "곧",
            "오늘 밤", "내일", "이번 주"
        ]

        # 보호 요인
        self.protective_indicators = [
            "살고 싶", "가족", "아이", "자녀", "부모님",
            "친구", "반려동물", "강아지", "고양이",
            "해야 할", "책임", "두렵", "무섭",
            "도움", "상담", "치료"
        ]

        logger.info("ContextualCrisisAnalyzer initialized")

    def analyze(self, text: str, conversation_history: List[Dict] = None) -> ContextualAnalysis:
        """
        맥락 분석 수행

        Args:
            text: 분석할 텍스트
            conversation_history: 대화 이력 (선택)

        Returns:
            ContextualAnalysis: 맥락 분석 결과
        """
        text_lower = text.lower()

        # 1. 시제 분석
        temporal = self._analyze_temporal(text_lower)

        # 2. 구체적 계획 유무
        has_plan = self._check_specific_plan(text_lower)

        # 3. 수단 접근 가능성
        has_means = self._check_means_access(text_lower)

        # 4. 시간 압박
        has_timeline = self._check_timeline(text_lower)

        # 5. 보호 요인
        protective = self._identify_protective_factors(text_lower)

        # 6. 위험 요인
        risk = self._identify_risk_factors(text_lower)

        # 원시 지표
        raw_indicators = {
            "past_tense": temporal == TemporalContext.PAST,
            "current_tense": temporal == TemporalContext.CURRENT,
            "future_intent": temporal == TemporalContext.FUTURE,
            "specific_plan": has_plan,
            "means_access": has_means,
            "time_pressure": has_timeline,
            "has_protective_factors": len(protective) > 0
        }

        return ContextualAnalysis(
            temporal=temporal,
            has_specific_plan=has_plan,
            has_means_access=has_means,
            has_timeline=has_timeline,
            protective_factors=protective,
            risk_factors=risk,
            raw_indicators=raw_indicators
        )

    def _analyze_temporal(self, text: str) -> TemporalContext:
        """시제 분석"""
        past_count = sum(1 for m in self.temporal_markers["past"] if m in text)
        current_count = sum(1 for m in self.temporal_markers["current"] if m in text)
        future_count = sum(1 for m in self.temporal_markers["future"] if m in text)

        if future_count > 0 and future_count >= past_count:
            return TemporalContext.FUTURE
        elif current_count > 0 and current_count >= past_count:
            return TemporalContext.CURRENT
        elif past_count > 0:
            return TemporalContext.PAST
        else:
            return TemporalContext.AMBIGUOUS

    def _check_specific_plan(self, text: str) -> bool:
        """구체적 계획 확인"""
        return any(indicator in text for indicator in self.plan_indicators)

    def _check_means_access(self, text: str) -> bool:
        """수단 접근 가능성 확인"""
        return any(indicator in text for indicator in self.means_indicators)

    def _check_timeline(self, text: str) -> bool:
        """시간 압박 확인"""
        return any(indicator in text for indicator in self.timeline_indicators)

    def _identify_protective_factors(self, text: str) -> List[str]:
        """보호 요인 식별"""
        return [factor for factor in self.protective_indicators if factor in text]

    def _identify_risk_factors(self, text: str) -> List[str]:
        """위험 요인 식별"""
        risk_factors = []

        if self._check_specific_plan(text):
            risk_factors.append("구체적 계획")
        if self._check_means_access(text):
            risk_factors.append("수단 접근")
        if self._check_timeline(text):
            risk_factors.append("시간 압박")

        # 추가 위험 지표
        if "아무도 모르" in text or "혼자" in text:
            risk_factors.append("고립감")
        if "희망 없" in text or "방법 없" in text:
            risk_factors.append("절망감")
        if "짐" in text or "폐" in text or "부담" in text:
            risk_factors.append("자기 부담감")

        return risk_factors


# =============================================================================
# 3단계: 차등 대응 시스템 (Graduated Response System)
# =============================================================================

class GraduatedResponseSystem:
    """
    3단계 차등 대응 시스템 (NEW)

    위기 수준에 따라 맞춤형 대응을 제공합니다.
    """

    def __init__(self):
        self.responses = self._load_responses()
        self.resources = self._load_resources()
        self.follow_up_questions = self._load_follow_up_questions()

        logger.info("GraduatedResponseSystem initialized")

    def _load_responses(self) -> Dict[CrisisLevel, Dict[str, Any]]:
        """수준별 대응 로드"""
        return {
            CrisisLevel.IMMINENT: {
                "primary": """지금 많이 힘드시군요. 당신의 안전이 가장 중요해요.

지금 바로 자살예방상담전화 1393에 전화해 주세요. 24시간 전문 상담사가 함께 해드려요.

전화하기 어려우시면 119에 연락해 주세요.

저도 여기 있을게요. 전화하시는 동안 기다릴게요.""",
                "follow_up": "전화 연결되셨나요? 어떠세요?",
                "must_include": ["1393", "119", "안전"],
                "tone": "urgent_caring"
            },
            CrisisLevel.HIGH: {
                "primary": """정말 힘든 상황이시군요. 그 고통이 얼마나 큰지 느껴져요.

당신의 안전이 가장 중요해요. 혼자 감당하지 않으셔도 돼요.

지금 자살예방상담전화 1393에 연락하시면 24시간 전문 상담사가 함께 해드려요.

지금 안전하신 곳에 계신가요?""",
                "follow_up": "지금 어디 계세요? 주변에 누가 있으신가요?",
                "must_include": ["1393", "안전"],
                "tone": "concerned_supportive"
            },
            CrisisLevel.MODERATE: {
                "primary": """죽고 싶다는 생각이 드셨군요. 정말 힘드셨겠어요.

그런 생각이 드는 건 고통이 크다는 신호예요. 당신 잘못이 아니에요.

혼자 감당하시기 어려우시면, 전문 상담사와 이야기 나눠보시는 것도 도움이 될 수 있어요.
자살예방상담전화 1393은 24시간 무료로 상담받으실 수 있어요.

조금 더 이야기해 주실 수 있으세요?""",
                "follow_up": "요즘 얼마나 자주 그런 생각이 드세요?",
                "must_include": ["1393"],
                "tone": "empathetic_curious"
            },
            CrisisLevel.LOW: {
                "primary": """그때 정말 힘드셨군요. 그런 생각까지 드셨을 정도면 얼마나 고통스러우셨을지 느껴져요.

지금은 어떠세요? 그때와 비교해서요.""",
                "follow_up": "지금은 그런 생각이 드시나요?",
                "must_include": [],
                "tone": "validating_exploring"
            }
        }

    def _load_resources(self) -> Dict[str, Dict[str, str]]:
        """위기 자원 정보"""
        return {
            "suicide_prevention": {
                "name": "자살예방상담전화",
                "number": "1393",
                "hours": "24시간",
                "description": "자살 위기 전문 상담"
            },
            "mental_health_crisis": {
                "name": "정신건강위기상담전화",
                "number": "1577-0199",
                "hours": "24시간",
                "description": "정신건강 위기 상담"
            },
            "emergency": {
                "name": "응급서비스",
                "number": "119",
                "hours": "24시간",
                "description": "긴급 상황 시"
            },
            "youth": {
                "name": "청소년전화",
                "number": "1388",
                "hours": "24시간",
                "description": "청소년 위기 상담"
            }
        }

    def _load_follow_up_questions(self) -> Dict[CrisisLevel, List[str]]:
        """후속 질문"""
        return {
            CrisisLevel.IMMINENT: [
                "전화 연결되셨나요?",
                "지금 안전하신 곳에 계신가요?",
                "주변에 도움 요청할 분이 계신가요?"
            ],
            CrisisLevel.HIGH: [
                "지금 어디 계세요?",
                "주변에 누가 있으신가요?",
                "오늘 밤 안전하게 지낼 수 있으신가요?",
                "위험한 물건에 접근할 수 있으신가요?"
            ],
            CrisisLevel.MODERATE: [
                "요즘 얼마나 자주 그런 생각이 드세요?",
                "구체적인 계획을 세우신 적이 있으신가요?",
                "주변에 이야기 나눌 분이 계신가요?",
                "이전에 비슷한 생각을 하셨던 적이 있으신가요?"
            ],
            CrisisLevel.LOW: [
                "지금은 어떠세요?",
                "그때 어떻게 이겨내셨어요?",
                "힘들 때 도움이 되는 것이 있으신가요?"
            ]
        }

    def generate_response(self, assessment: CrisisAssessment) -> Dict[str, Any]:
        """
        평가 결과에 따른 대응 생성

        Args:
            assessment: 위기 평가 결과

        Returns:
            Dict: 대응 정보
        """
        level = assessment.level
        response_template = self.responses.get(level, self.responses[CrisisLevel.MODERATE])

        # 보호 요인이 있으면 언급
        protective_mention = ""
        if assessment.contextual_analysis.protective_factors:
            factors = assessment.contextual_analysis.protective_factors[:2]
            if "가족" in factors or "아이" in factors or "자녀" in factors:
                protective_mention = "\n\n소중한 가족분들이 계시네요."
            elif "친구" in factors:
                protective_mention = "\n\n함께 해주는 친구분이 계시네요."

        # 필수 자원 정보
        resources = []
        if level in [CrisisLevel.IMMINENT, CrisisLevel.HIGH]:
            resources = [
                self.resources["suicide_prevention"],
                self.resources["emergency"]
            ]
        elif level == CrisisLevel.MODERATE:
            resources = [self.resources["suicide_prevention"]]

        return {
            "response": response_template["primary"] + protective_mention,
            "level": level.value,
            "tone": response_template["tone"],
            "resources": resources,
            "follow_up_questions": self.follow_up_questions.get(level, []),
            "must_include": response_template["must_include"]
        }


# =============================================================================
# 통합 위기 대응 시스템 (Integrated Crisis Response)
# =============================================================================

class CrisisResponseSystem:
    """
    통합 위기 대응 시스템 v2.0

    1단계: 키워드 감지
    2단계: 맥락 분석
    3단계: 차등 대응
    """

    def __init__(self):
        self.contextual_analyzer = ContextualCrisisAnalyzer()
        self.response_system = GraduatedResponseSystem()

        # 위기 키워드 (1단계)
        self.crisis_keywords = {
            "direct": [
                "죽고 싶", "죽을래", "자살", "목숨", "끝내고 싶",
                "사라지고 싶", "없어지고 싶"
            ],
            "self_harm": [
                "자해", "손목", "긋", "피", "상처"
            ],
            "indirect": [
                "더 이상 못", "살기 싫", "의미 없", "희망 없",
                "짐이 되", "없어져야", "떠나고 싶"
            ]
        }

        # 통계 추적
        self.crisis_count = 0
        self.response_history = []

        logger.info("CrisisResponseSystem v2.0 initialized")

    def assess(
        self,
        text: str,
        conversation_history: List[Dict] = None
    ) -> CrisisAssessment:
        """
        위기 평가 수행

        Args:
            text: 사용자 입력
            conversation_history: 대화 이력

        Returns:
            CrisisAssessment: 위기 평가 결과
        """
        # 1단계: 키워드 감지
        keyword_detected, keyword_category = self._detect_keywords(text)

        if not keyword_detected:
            # 키워드 없으면 위험 없음
            return CrisisAssessment(
                level=CrisisLevel.NONE,
                confidence=0.9,
                keyword_detected=False,
                contextual_analysis=ContextualAnalysis(
                    temporal=TemporalContext.AMBIGUOUS,
                    has_specific_plan=False,
                    has_means_access=False,
                    has_timeline=False,
                    protective_factors=[],
                    risk_factors=[],
                    raw_indicators={}
                ),
                recommended_response="",
                resources=[],
                follow_up_questions=[],
                safety_planning_needed=False
            )

        # 2단계: 맥락 분석
        contextual = self.contextual_analyzer.analyze(text, conversation_history)

        # 3단계: 위험 수준 결정
        level = self._determine_level(keyword_category, contextual)

        # 신뢰도 계산
        confidence = self._calculate_confidence(keyword_category, contextual)

        # 대응 생성
        response_info = self.response_system.generate_response(
            CrisisAssessment(
                level=level,
                confidence=confidence,
                keyword_detected=True,
                contextual_analysis=contextual,
                recommended_response="",
                resources=[],
                follow_up_questions=[],
                safety_planning_needed=level in [CrisisLevel.IMMINENT, CrisisLevel.HIGH]
            )
        )

        assessment = CrisisAssessment(
            level=level,
            confidence=confidence,
            keyword_detected=True,
            contextual_analysis=contextual,
            recommended_response=response_info["response"],
            resources=response_info["resources"],
            follow_up_questions=response_info["follow_up_questions"],
            safety_planning_needed=level in [CrisisLevel.IMMINENT, CrisisLevel.HIGH]
        )

        # 로깅
        self._log_crisis(text, assessment)

        return assessment

    def _detect_keywords(self, text: str) -> Tuple[bool, Optional[str]]:
        """1단계: 키워드 감지"""
        text_lower = text.lower()

        for category, keywords in self.crisis_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return True, category

        return False, None

    def _determine_level(
        self,
        keyword_category: str,
        contextual: ContextualAnalysis
    ) -> CrisisLevel:
        """위험 수준 결정"""

        # 즉각적 위험 (IMMINENT)
        if contextual.has_timeline and contextual.has_means_access:
            return CrisisLevel.IMMINENT

        if contextual.temporal == TemporalContext.FUTURE and contextual.has_specific_plan:
            return CrisisLevel.IMMINENT

        # 고위험 (HIGH)
        if keyword_category == "direct":
            if contextual.temporal in [TemporalContext.CURRENT, TemporalContext.FUTURE]:
                if contextual.has_specific_plan or contextual.has_means_access:
                    return CrisisLevel.HIGH
                return CrisisLevel.MODERATE if contextual.protective_factors else CrisisLevel.HIGH

        # 중위험 (MODERATE)
        if keyword_category in ["direct", "self_harm"]:
            if contextual.temporal == TemporalContext.CURRENT:
                return CrisisLevel.MODERATE

        if keyword_category == "indirect":
            if contextual.temporal in [TemporalContext.CURRENT, TemporalContext.FUTURE]:
                return CrisisLevel.MODERATE

        # 저위험 (LOW) - 과거 경험
        if contextual.temporal == TemporalContext.PAST:
            return CrisisLevel.LOW

        # 보호 요인 있으면 수준 하향
        if len(contextual.protective_factors) >= 2:
            return CrisisLevel.LOW

        return CrisisLevel.MODERATE

    def _calculate_confidence(
        self,
        keyword_category: str,
        contextual: ContextualAnalysis
    ) -> float:
        """신뢰도 계산"""
        confidence = 0.5

        # 명확한 지표들이 있으면 신뢰도 증가
        if keyword_category == "direct":
            confidence += 0.2
        if contextual.temporal != TemporalContext.AMBIGUOUS:
            confidence += 0.15
        if contextual.has_specific_plan:
            confidence += 0.1
        if contextual.has_timeline:
            confidence += 0.1

        return min(confidence, 1.0)

    def _log_crisis(self, text: str, assessment: CrisisAssessment):
        """위기 로깅"""
        self.crisis_count += 1

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": assessment.level.value,
            "confidence": assessment.confidence,
            "text_snippet": text[:50] + "..." if len(text) > 50 else text,
            "risk_factors": assessment.contextual_analysis.risk_factors,
            "protective_factors": assessment.contextual_analysis.protective_factors
        }

        self.response_history.append(log_entry)

        # 최근 100개만 유지
        if len(self.response_history) > 100:
            self.response_history = self.response_history[-100:]

        logger.warning(
            f"Crisis detected: level={assessment.level.value}, "
            f"confidence={assessment.confidence:.2f}"
        )

    def get_statistics(self) -> Dict[str, Any]:
        """통계 반환"""
        if not self.response_history:
            return {"total_crises": 0}

        level_counts = {}
        for entry in self.response_history:
            level = entry["level"]
            level_counts[level] = level_counts.get(level, 0) + 1

        return {
            "total_crises": self.crisis_count,
            "level_distribution": level_counts,
            "recent_count": len(self.response_history)
        }


# =============================================================================
# 안전 계획 생성기 (Safety Planning)
# =============================================================================

class SafetyPlanGenerator:
    """
    안전 계획 생성기

    위기 상황에서 사용자와 함께 안전 계획을 수립합니다.
    """

    def __init__(self):
        self.safety_plan_template = {
            "warning_signs": {
                "title": "경고 신호",
                "question": "힘들어지기 시작할 때 어떤 느낌이나 생각이 드시나요?",
                "examples": ["잠을 못 자요", "식욕이 없어요", "혼자 있고 싶어요"]
            },
            "coping_strategies": {
                "title": "대처 방법",
                "question": "힘들 때 혼자서 해볼 수 있는 것들이 있을까요?",
                "examples": ["산책하기", "음악 듣기", "따뜻한 물 마시기", "호흡 운동"]
            },
            "social_contacts": {
                "title": "연락할 사람",
                "question": "힘들 때 연락할 수 있는 가족이나 친구가 있으신가요?",
                "examples": ["가족", "친구", "동료"]
            },
            "professional_resources": {
                "title": "전문 도움",
                "question": "전문가 도움이 필요할 때 연락할 곳을 알고 계신가요?",
                "resources": [
                    {"name": "자살예방상담전화", "number": "1393"},
                    {"name": "정신건강위기상담전화", "number": "1577-0199"}
                ]
            },
            "environment_safety": {
                "title": "환경 안전",
                "question": "위험할 수 있는 물건들을 안전하게 보관하거나 치울 수 있으신가요?",
                "tips": ["약물 보관 위치 변경", "위험한 물건 접근 제한"]
            },
            "reasons_to_live": {
                "title": "삶의 이유",
                "question": "살아가는 이유가 되는 것들이 있으신가요?",
                "examples": ["가족", "반려동물", "하고 싶은 일", "보고 싶은 사람"]
            }
        }

    def generate_prompt(self, section: str) -> Dict[str, Any]:
        """안전 계획 섹션별 프롬프트 생성"""
        if section not in self.safety_plan_template:
            return {"error": "Unknown section"}

        return self.safety_plan_template[section]

    def get_full_template(self) -> Dict[str, Any]:
        """전체 안전 계획 템플릿 반환"""
        return self.safety_plan_template


# =============================================================================
# 테스트 함수
# =============================================================================

def test_crisis_system():
    """위기 대응 시스템 테스트"""
    system = CrisisResponseSystem()

    test_cases = [
        # 과거형 - 저위험
        "예전에 정말 힘들 때 죽고 싶다는 생각을 한 적 있어요.",

        # 현재형, 계획 없음 - 중위험
        "요즘 너무 힘들어서 죽고 싶어요.",

        # 현재형, 구체적 계획 - 고위험
        "죽고 싶어요. 약을 모아뒀어요.",

        # 즉각적 위험 - IMMINENT
        "지금 옥상에 있어요. 오늘 끝내려고요.",

        # 간접 표현
        "더 이상 살고 싶지 않아요.",

        # 보호 요인 있음
        "죽고 싶지만 아이들 생각에 못하겠어요."
    ]

    print("=== 위기 대응 2단계 시스템 테스트 ===\n")

    for text in test_cases:
        print(f"입력: {text}")
        assessment = system.assess(text)

        print(f"수준: {assessment.level.value}")
        print(f"신뢰도: {assessment.confidence:.2f}")
        print(f"시제: {assessment.contextual_analysis.temporal.value}")
        print(f"보호요인: {assessment.contextual_analysis.protective_factors}")
        print(f"위험요인: {assessment.contextual_analysis.risk_factors}")
        print(f"\n권장 대응:\n{assessment.recommended_response[:200]}...")
        print("-" * 60 + "\n")


if __name__ == "__main__":
    test_crisis_system()
