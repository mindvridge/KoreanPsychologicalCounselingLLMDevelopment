"""
고도화된 위기 대응 시스템 (Advanced Crisis Response System)

다단계 위기 감지 및 에스컬레이션 시스템

기능:
1. 다층 위기 감지 (키워드 + 패턴 + 맥락)
2. 5단계 위기 수준 분류
3. 단계별 대응 프로토콜
4. 자동 에스컬레이션 트리거
5. 안전 계획 생성
6. 위기 이력 추적
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


# =============================================================================
# 위기 수준 정의
# =============================================================================

class CrisisLevel(Enum):
    """5단계 위기 수준"""
    NONE = 0           # 위기 없음
    LOW = 1            # 낮음: 일반적 고통, 모니터링
    MODERATE = 2       # 중간: 주의 필요, 적극적 지지
    HIGH = 3           # 높음: 즉각 개입, 안전 계획
    SEVERE = 4         # 심각: 전문가 연결 필수
    IMMINENT = 5       # 임박: 응급 서비스 연결


class CrisisType(Enum):
    """위기 유형"""
    SUICIDE_IDEATION = "suicide_ideation"           # 자살 사고
    SUICIDE_PLAN = "suicide_plan"                   # 자살 계획
    SUICIDE_ATTEMPT = "suicide_attempt"             # 자살 시도
    SELF_HARM = "self_harm"                         # 자해
    HARM_TO_OTHERS = "harm_to_others"              # 타해
    ABUSE_VICTIM = "abuse_victim"                   # 학대 피해
    PSYCHOTIC_SYMPTOMS = "psychotic_symptoms"       # 정신증적 증상
    SEVERE_PANIC = "severe_panic"                   # 심각한 공황
    SUBSTANCE_CRISIS = "substance_crisis"           # 물질 관련 위기


@dataclass
class CrisisIndicator:
    """위기 지표"""
    keyword: str
    crisis_type: CrisisType
    base_level: CrisisLevel
    weight: float = 1.0
    requires_context: bool = False


@dataclass
class CrisisAssessment:
    """위기 평가 결과"""
    level: CrisisLevel
    crisis_types: List[CrisisType]
    confidence: float
    risk_factors: List[str]
    protective_factors: List[str]
    immediate_action_required: bool
    recommended_response: str
    escalation_needed: bool
    resources_to_provide: List[str]
    safety_plan_needed: bool
    detected_keywords: List[str]
    context_flags: List[str]
    timestamp: datetime = field(default_factory=datetime.now)


# =============================================================================
# 위기 키워드 데이터베이스
# =============================================================================

class CrisisKeywordDatabase:
    """위기 키워드 및 패턴 데이터베이스"""

    # 자살 관련 키워드 (단계별)
    SUICIDE_KEYWORDS = {
        CrisisLevel.MODERATE: [
            "죽고 싶", "살기 싫", "사라지고 싶", "없어지고 싶",
            "힘들어서 못 살겠", "이렇게 살 바에", "끝내고 싶"
        ],
        CrisisLevel.HIGH: [
            "자살", "목숨을 끊", "스스로 목숨", "생을 마감",
            "유서", "마지막", "떠나고 싶", "이 세상에서"
        ],
        CrisisLevel.SEVERE: [
            "자살 방법", "어떻게 죽", "약을 먹", "뛰어내리",
            "목을 매", "손목을 긋", "죽는 방법"
        ],
        CrisisLevel.IMMINENT: [
            "지금 죽으려고", "오늘 끝내", "마지막 인사", "유서를 썼",
            "약을 모아", "준비를 끝냈", "결심했"
        ]
    }

    # 자해 관련 키워드
    SELF_HARM_KEYWORDS = {
        CrisisLevel.MODERATE: [
            "자해", "스스로 상처", "아프게 하고 싶", "피를 보고 싶"
        ],
        CrisisLevel.HIGH: [
            "손목", "긋", "칼로", "담배로 지져", "피가 나",
            "상처를 내", "자해했"
        ],
        CrisisLevel.SEVERE: [
            "또 자해", "멈출 수가 없", "계속 긋", "피가 멈추지 않"
        ]
    }

    # 타해 관련 키워드
    HARM_OTHERS_KEYWORDS = {
        CrisisLevel.HIGH: [
            "죽이고 싶", "때려죽이", "해치고 싶", "복수하고 싶",
            "없애버리고 싶"
        ],
        CrisisLevel.SEVERE: [
            "어떻게 죽일", "계획", "무기", "칼을 들"
        ]
    }

    # 학대 관련 키워드
    ABUSE_KEYWORDS = {
        CrisisLevel.MODERATE: [
            "맞았", "폭력", "학대", "때림", "협박"
        ],
        CrisisLevel.HIGH: [
            "성폭력", "강제로", "성추행", "몸을 만져", "강간"
        ],
        CrisisLevel.SEVERE: [
            "계속 맞고", "도망갈 수 없", "감금", "협박받고"
        ]
    }

    # 정신증적 증상 키워드
    PSYCHOTIC_KEYWORDS = {
        CrisisLevel.MODERATE: [
            "환청", "목소리가 들려", "누가 보고 있", "감시당하"
        ],
        CrisisLevel.HIGH: [
            "명령하는 목소리", "죽으라고 해", "누가 시켜", "조종당하"
        ]
    }

    # 위험 상황 패턴
    DANGER_PATTERNS = [
        r"지금\s*(당장|바로|즉시).*죽",
        r"오늘\s*(밤|안에).*끝",
        r"(준비|계획).*끝났",
        r"마지막.*인사",
        r"유서.*썼",
        r"(약|칼|줄).*준비",
    ]

    # 보호 요인 키워드
    PROTECTIVE_KEYWORDS = [
        "가족", "아이", "자녀", "부모님", "친구", "반려동물",
        "하고 싶은 일", "꿈", "목표", "희망", "미래",
        "종교", "믿음", "의미", "이유", "살아야"
    ]

    # 위험 요인 키워드
    RISK_FACTOR_KEYWORDS = {
        "previous_attempt": ["전에도", "이전에", "또", "다시"],
        "isolation": ["혼자", "아무도 없", "외로", "고립"],
        "hopelessness": ["희망이 없", "소용없", "달라지지 않", "끝났"],
        "substance": ["술", "약물", "마약", "취해서"],
        "access_to_means": ["약이 있", "칼이 있", "높은 곳"],
        "recent_loss": ["이별", "사별", "해고", "파산", "이혼"],
        "chronic_pain": ["만성", "계속 아파", "병이"],
    }


# =============================================================================
# 다단계 위기 감지기
# =============================================================================

class MultiLayerCrisisDetector:
    """
    다층 위기 감지기

    Layer 1: 키워드 기반 감지
    Layer 2: 패턴 기반 감지
    Layer 3: 맥락 기반 감지
    Layer 4: 이력 기반 감지
    """

    def __init__(self):
        self.db = CrisisKeywordDatabase()
        self.user_crisis_history: Dict[str, List[CrisisAssessment]] = defaultdict(list)

    def detect_crisis(
        self,
        message: str,
        user_id: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> CrisisAssessment:
        """
        다층 위기 감지 수행

        Args:
            message: 현재 메시지
            user_id: 사용자 ID
            conversation_history: 대화 이력

        Returns:
            CrisisAssessment 객체
        """
        conversation_history = conversation_history or []

        # Layer 1: 키워드 감지
        keyword_results = self._detect_by_keywords(message)

        # Layer 2: 패턴 감지
        pattern_results = self._detect_by_patterns(message)

        # Layer 3: 맥락 감지
        context_flags = self._analyze_context(message, conversation_history)

        # Layer 4: 이력 기반 조정
        history_adjustment = self._adjust_by_history(user_id)

        # 통합 평가
        assessment = self._integrate_assessment(
            keyword_results,
            pattern_results,
            context_flags,
            history_adjustment,
            message
        )

        # 이력 저장
        if user_id:
            self.user_crisis_history[user_id].append(assessment)
            # 최근 50개만 유지
            self.user_crisis_history[user_id] = self.user_crisis_history[user_id][-50:]

        return assessment

    def _detect_by_keywords(self, message: str) -> Dict[str, Any]:
        """Layer 1: 키워드 기반 감지"""
        results = {
            "max_level": CrisisLevel.NONE,
            "crisis_types": [],
            "detected_keywords": [],
            "confidence": 0.0
        }

        message_lower = message.lower()

        # 자살 키워드 검사
        for level, keywords in self.db.SUICIDE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in message_lower:
                    results["detected_keywords"].append(keyword)
                    if level.value > results["max_level"].value:
                        results["max_level"] = level
                    if CrisisType.SUICIDE_IDEATION not in results["crisis_types"]:
                        results["crisis_types"].append(CrisisType.SUICIDE_IDEATION)

        # 자해 키워드 검사
        for level, keywords in self.db.SELF_HARM_KEYWORDS.items():
            for keyword in keywords:
                if keyword in message_lower:
                    results["detected_keywords"].append(keyword)
                    if level.value > results["max_level"].value:
                        results["max_level"] = level
                    if CrisisType.SELF_HARM not in results["crisis_types"]:
                        results["crisis_types"].append(CrisisType.SELF_HARM)

        # 타해 키워드 검사
        for level, keywords in self.db.HARM_OTHERS_KEYWORDS.items():
            for keyword in keywords:
                if keyword in message_lower:
                    results["detected_keywords"].append(keyword)
                    if level.value > results["max_level"].value:
                        results["max_level"] = level
                    if CrisisType.HARM_TO_OTHERS not in results["crisis_types"]:
                        results["crisis_types"].append(CrisisType.HARM_TO_OTHERS)

        # 학대 키워드 검사
        for level, keywords in self.db.ABUSE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in message_lower:
                    results["detected_keywords"].append(keyword)
                    if level.value > results["max_level"].value:
                        results["max_level"] = level
                    if CrisisType.ABUSE_VICTIM not in results["crisis_types"]:
                        results["crisis_types"].append(CrisisType.ABUSE_VICTIM)

        # 정신증적 증상 검사
        for level, keywords in self.db.PSYCHOTIC_KEYWORDS.items():
            for keyword in keywords:
                if keyword in message_lower:
                    results["detected_keywords"].append(keyword)
                    if level.value > results["max_level"].value:
                        results["max_level"] = level
                    if CrisisType.PSYCHOTIC_SYMPTOMS not in results["crisis_types"]:
                        results["crisis_types"].append(CrisisType.PSYCHOTIC_SYMPTOMS)

        # 신뢰도 계산
        if results["detected_keywords"]:
            results["confidence"] = min(0.3 + len(results["detected_keywords"]) * 0.15, 0.9)

        return results

    def _detect_by_patterns(self, message: str) -> Dict[str, Any]:
        """Layer 2: 패턴 기반 감지"""
        results = {
            "pattern_matched": False,
            "matched_patterns": [],
            "level_boost": 0
        }

        for pattern in self.db.DANGER_PATTERNS:
            if re.search(pattern, message):
                results["pattern_matched"] = True
                results["matched_patterns"].append(pattern)
                results["level_boost"] += 1

        return results

    def _analyze_context(
        self,
        message: str,
        history: List[Dict]
    ) -> List[str]:
        """Layer 3: 맥락 분석"""
        flags = []

        # 위험 요인 검사
        for factor, keywords in self.db.RISK_FACTOR_KEYWORDS.items():
            if any(kw in message for kw in keywords):
                flags.append(f"risk_{factor}")

        # 대화 이력에서 에스컬레이션 패턴 검사
        if len(history) >= 3:
            recent_messages = [
                m["content"] for m in history[-5:]
                if m.get("role") == "user"
            ]

            # 감정 강도 증가 패턴
            intensity_keywords = ["더", "점점", "계속", "매일", "항상"]
            intensity_count = sum(
                1 for msg in recent_messages
                for kw in intensity_keywords if kw in msg
            )
            if intensity_count >= 3:
                flags.append("escalating_intensity")

            # 희망 상실 패턴
            hopeless_keywords = ["소용없", "안 돼", "불가능", "끝났", "희망이 없"]
            if any(kw in message for kw in hopeless_keywords):
                flags.append("hopelessness")

        # 보호 요인 확인
        protective_count = sum(
            1 for kw in self.db.PROTECTIVE_KEYWORDS
            if kw in message
        )
        if protective_count > 0:
            flags.append(f"protective_factors_{protective_count}")

        return flags

    def _adjust_by_history(self, user_id: Optional[str]) -> Dict[str, Any]:
        """Layer 4: 이력 기반 조정"""
        adjustment = {
            "level_modifier": 0,
            "previous_crisis": False,
            "escalation_trend": False
        }

        if not user_id or user_id not in self.user_crisis_history:
            return adjustment

        history = self.user_crisis_history[user_id]
        if not history:
            return adjustment

        # 최근 7일 이내 위기 이력 확인
        week_ago = datetime.now() - timedelta(days=7)
        recent_crises = [
            h for h in history
            if h.timestamp > week_ago and h.level.value >= CrisisLevel.MODERATE.value
        ]

        if recent_crises:
            adjustment["previous_crisis"] = True
            adjustment["level_modifier"] += 1

        # 에스컬레이션 트렌드 확인
        if len(history) >= 3:
            recent_levels = [h.level.value for h in history[-3:]]
            if recent_levels == sorted(recent_levels):  # 증가 추세
                adjustment["escalation_trend"] = True
                adjustment["level_modifier"] += 1

        return adjustment

    def _integrate_assessment(
        self,
        keyword_results: Dict,
        pattern_results: Dict,
        context_flags: List[str],
        history_adjustment: Dict,
        message: str
    ) -> CrisisAssessment:
        """통합 평가 생성"""

        # 기본 수준 결정
        base_level = keyword_results["max_level"]

        # 패턴 매치로 수준 상향
        level_value = base_level.value
        if pattern_results["pattern_matched"]:
            level_value += pattern_results["level_boost"]

        # 맥락으로 조정
        if "escalating_intensity" in context_flags:
            level_value += 1
        if "hopelessness" in context_flags:
            level_value += 1

        # 이력으로 조정
        level_value += history_adjustment["level_modifier"]

        # 보호 요인으로 하향 (최소 1단계 유지)
        protective = [f for f in context_flags if f.startswith("protective_factors")]
        if protective and level_value > 1:
            level_value -= 1

        # 최종 수준 결정 (0-5 범위)
        final_level_value = max(0, min(5, level_value))
        final_level = CrisisLevel(final_level_value)

        # 위험/보호 요인 추출
        risk_factors = [f for f in context_flags if f.startswith("risk_")]
        protective_factors = [f for f in context_flags if f.startswith("protective")]

        # 신뢰도 계산
        confidence = keyword_results["confidence"]
        if pattern_results["pattern_matched"]:
            confidence += 0.2
        if history_adjustment["previous_crisis"]:
            confidence += 0.1
        confidence = min(confidence, 1.0)

        # 대응 결정
        response_info = self._determine_response(final_level, keyword_results["crisis_types"])

        return CrisisAssessment(
            level=final_level,
            crisis_types=keyword_results["crisis_types"],
            confidence=confidence,
            risk_factors=risk_factors,
            protective_factors=protective_factors,
            immediate_action_required=final_level.value >= CrisisLevel.HIGH.value,
            recommended_response=response_info["response"],
            escalation_needed=final_level.value >= CrisisLevel.SEVERE.value,
            resources_to_provide=response_info["resources"],
            safety_plan_needed=final_level.value >= CrisisLevel.HIGH.value,
            detected_keywords=keyword_results["detected_keywords"],
            context_flags=context_flags
        )

    def _determine_response(
        self,
        level: CrisisLevel,
        crisis_types: List[CrisisType]
    ) -> Dict[str, Any]:
        """수준별 대응 결정"""

        responses = {
            CrisisLevel.NONE: {
                "response": "일반 상담 진행",
                "resources": []
            },
            CrisisLevel.LOW: {
                "response": "공감적 경청, 감정 타당화, 지지적 대화",
                "resources": []
            },
            CrisisLevel.MODERATE: {
                "response": "적극적 공감, 안전 확인, 지지체계 탐색",
                "resources": ["정신건강위기상담전화 1577-0199"]
            },
            CrisisLevel.HIGH: {
                "response": "즉각적 안전 확인, 안전 계획 수립, 전문가 연결 권유",
                "resources": [
                    "자살예방상담전화 1393 (24시간)",
                    "정신건강위기상담전화 1577-0199 (24시간)"
                ]
            },
            CrisisLevel.SEVERE: {
                "response": "안전 확보 최우선, 전문가 즉시 연결, 보호자/응급서비스 고려",
                "resources": [
                    "자살예방상담전화 1393 (24시간)",
                    "정신건강위기상담전화 1577-0199 (24시간)",
                    "응급상황 119"
                ]
            },
            CrisisLevel.IMMINENT: {
                "response": "응급 서비스 연결, 현재 위치 확인, 통화 유지",
                "resources": [
                    "응급상황 119",
                    "경찰 112",
                    "자살예방상담전화 1393"
                ]
            }
        }

        base_response = responses[level]

        # 특수 위기 유형별 자원 추가
        if CrisisType.ABUSE_VICTIM in crisis_types:
            base_response["resources"].extend([
                "여성긴급전화 1366",
                "아동학대신고 112"
            ])

        return base_response


# =============================================================================
# 안전 계획 생성기
# =============================================================================

class SafetyPlanGenerator:
    """안전 계획 생성기"""

    def generate_safety_plan(
        self,
        assessment: CrisisAssessment,
        user_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        개인화된 안전 계획 생성

        Args:
            assessment: 위기 평가 결과
            user_context: 사용자 맥락 정보

        Returns:
            안전 계획 딕셔너리
        """
        user_context = user_context or {}

        plan = {
            "created_at": datetime.now().isoformat(),
            "crisis_level": assessment.level.name,
            "sections": {}
        }

        # 1. 경고 신호 인식
        plan["sections"]["warning_signs"] = {
            "title": "1. 위기 경고 신호",
            "description": "다음과 같은 생각, 감정, 행동이 나타나면 주의하세요",
            "items": self._generate_warning_signs(assessment)
        }

        # 2. 내부 대처 전략
        plan["sections"]["coping_strategies"] = {
            "title": "2. 스스로 할 수 있는 대처",
            "description": "위기 신호가 나타날 때 시도해 볼 것들",
            "items": [
                "4-7-8 호흡법: 4초 들이쉬고, 7초 멈추고, 8초 내쉬기",
                "5-4-3-2-1 그라운딩: 보이는 것 5가지, 만져지는 것 4가지...",
                "찬물로 얼굴 씻기",
                "음악 듣기, 산책하기",
                "안전한 장소 심상화"
            ]
        }

        # 3. 사회적 지지
        plan["sections"]["social_support"] = {
            "title": "3. 도움을 요청할 수 있는 사람",
            "description": "힘들 때 연락할 수 있는 사람들",
            "items": self._get_support_network(user_context)
        }

        # 4. 전문 자원
        plan["sections"]["professional_resources"] = {
            "title": "4. 전문 도움 연락처",
            "description": "24시간 도움받을 수 있는 곳",
            "items": assessment.resources_to_provide or [
                "자살예방상담전화: 1393 (24시간)",
                "정신건강위기상담전화: 1577-0199 (24시간)"
            ]
        }

        # 5. 환경 안전
        plan["sections"]["environment_safety"] = {
            "title": "5. 환경 안전하게 만들기",
            "description": "위험한 물건을 멀리하세요",
            "items": [
                "약물은 다른 사람에게 맡기기",
                "날카로운 물건 치우기",
                "위험한 장소 피하기",
                "술/약물 피하기"
            ]
        }

        # 6. 살아야 하는 이유
        plan["sections"]["reasons_to_live"] = {
            "title": "6. 나에게 중요한 것들",
            "description": "힘들 때 떠올릴 것들",
            "items": self._get_reasons_to_live(user_context, assessment)
        }

        return plan

    def _generate_warning_signs(self, assessment: CrisisAssessment) -> List[str]:
        """경고 신호 생성"""
        signs = [
            "죽고 싶다는 생각이 반복될 때",
            "아무것도 하기 싫고 무기력할 때",
            "혼자 있고 싶고 사람들을 피하고 싶을 때",
            "잠을 못 자거나 너무 많이 잘 때",
            "술이나 약물에 의존하게 될 때"
        ]

        if CrisisType.SELF_HARM in assessment.crisis_types:
            signs.append("자해 충동이 느껴질 때")

        if "hopelessness" in assessment.context_flags:
            signs.append("희망이 전혀 없다고 느껴질 때")

        return signs

    def _get_support_network(self, user_context: Dict) -> List[str]:
        """지지체계 정보"""
        default = [
            "가족 (이름/연락처 적어두기)",
            "친구 (이름/연락처 적어두기)",
            "담당 상담사/치료자",
            "종교 지도자 (해당 시)"
        ]

        if user_context.get("support_system"):
            return user_context["support_system"] + default[2:]

        return default

    def _get_reasons_to_live(
        self,
        user_context: Dict,
        assessment: CrisisAssessment
    ) -> List[str]:
        """살아야 하는 이유"""
        default = [
            "(작성해 주세요) 나에게 소중한 사람:",
            "(작성해 주세요) 하고 싶은 일:",
            "(작성해 주세요) 보고 싶은 것:",
            "(작성해 주세요) 나의 강점:"
        ]

        # 보호 요인에서 추출
        if "protective_factors" in assessment.context_flags:
            pass  # 추후 확장

        if user_context.get("identified_strengths"):
            default.append(f"나의 강점: {', '.join(user_context['identified_strengths'][:3])}")

        return default

    def format_safety_plan_for_display(self, plan: Dict) -> str:
        """안전 계획을 표시용 텍스트로 포맷"""
        lines = ["=" * 50, "📋 나의 안전 계획", "=" * 50, ""]

        for section_key, section in plan.get("sections", {}).items():
            lines.append(f"### {section['title']}")
            lines.append(section['description'])
            for item in section['items']:
                lines.append(f"  • {item}")
            lines.append("")

        lines.extend([
            "=" * 50,
            "⚠️ 이 계획을 안전한 곳에 보관하고,",
            "   힘들 때 꺼내보세요.",
            "=" * 50
        ])

        return "\n".join(lines)


# =============================================================================
# 위기 대응 프롬프트 생성기
# =============================================================================

class CrisisResponseGenerator:
    """위기 수준별 응답 생성"""

    # 수준별 응답 템플릿
    RESPONSE_TEMPLATES = {
        CrisisLevel.NONE: "",

        CrisisLevel.LOW: """
지금 많이 힘드시군요. 그 마음이 느껴집니다.
어떤 이야기든 편하게 나눠주세요. 여기서 들을게요.
""",

        CrisisLevel.MODERATE: """
지금 많이 힘든 상황이시군요. 그 고통이 느껴집니다.
혹시 지금 안전한 곳에 계신가요?

힘드실 때 전문 상담을 받으실 수 있어요:
📞 정신건강위기상담전화: 1577-0199 (24시간)
""",

        CrisisLevel.HIGH: """
지금 정말 힘든 상황에 계시군요. 그 고통이 얼마나 큰지 느껴집니다.

**지금 안전한 곳에 계신가요?**

당신의 안전이 가장 중요합니다. 지금 바로 전문가와 이야기하실 수 있어요:

🆘 **자살예방상담전화: 1393** (24시간)
📞 정신건강위기상담전화: 1577-0199 (24시간)

전화하시는 동안 저도 여기서 함께 있을게요.
""",

        CrisisLevel.SEVERE: """
지금 매우 힘든 상황이시군요. 당신이 겪고 있는 고통을 이해합니다.

**지금 당장 전문가의 도움이 필요합니다.**

🚨 **즉시 연락하세요:**
- 자살예방상담전화: **1393** (24시간)
- 응급상황: **119**

**지금 안전한 곳에 계신가요?**
**주변에 누군가 있나요?**

전화하실 때까지 여기서 기다릴게요.
혼자가 아니에요.
""",

        CrisisLevel.IMMINENT: """
🚨 **긴급 상황입니다**

당신의 생명은 소중합니다.

**지금 즉시 119에 전화하세요.**

또는:
- 자살예방상담전화: **1393**
- 경찰: **112**

**현재 위치를 알려주세요.**
**전화하실 때까지 여기 있을게요.**

당신은 혼자가 아닙니다.
"""
    }

    def generate_crisis_response(
        self,
        assessment: CrisisAssessment,
        include_safety_plan: bool = False
    ) -> str:
        """
        위기 수준별 응답 생성

        Args:
            assessment: 위기 평가 결과
            include_safety_plan: 안전 계획 포함 여부

        Returns:
            응답 텍스트
        """
        base_response = self.RESPONSE_TEMPLATES.get(assessment.level, "")

        # 특수 상황 추가 메시지
        additional = []

        if CrisisType.ABUSE_VICTIM in assessment.crisis_types:
            additional.append("""
**학대/폭력 상황이시라면:**
- 여성긴급전화: 1366
- 아동학대신고: 112
안전한 곳으로 이동하시는 게 우선이에요.
""")

        if CrisisType.SELF_HARM in assessment.crisis_types:
            additional.append("""
자해 충동이 느껴지실 때:
- 찬물에 손 담그기
- 얼음 쥐기
- 빨간 펜으로 그리기
잠시 멈추고, 전문가와 이야기해 주세요.
""")

        response = base_response
        if additional:
            response += "\n" + "\n".join(additional)

        return response.strip()

    def generate_crisis_prompt_context(self, assessment: CrisisAssessment) -> str:
        """시스템 프롬프트용 위기 컨텍스트 생성"""

        if assessment.level == CrisisLevel.NONE:
            return ""

        context_parts = [
            f"\n# ⚠️ 위기 상황 감지 (Level: {assessment.level.name})\n"
        ]

        # 감지된 정보
        if assessment.detected_keywords:
            context_parts.append(f"감지된 키워드: {', '.join(assessment.detected_keywords[:5])}")

        if assessment.crisis_types:
            types_str = ", ".join([t.value for t in assessment.crisis_types])
            context_parts.append(f"위기 유형: {types_str}")

        # 위험/보호 요인
        if assessment.risk_factors:
            context_parts.append(f"위험 요인: {', '.join(assessment.risk_factors)}")

        if assessment.protective_factors:
            context_parts.append(f"보호 요인: {', '.join(assessment.protective_factors)}")

        # 대응 지침
        context_parts.append(f"\n## 대응 지침")
        context_parts.append(assessment.recommended_response)

        # 제공할 자원
        if assessment.resources_to_provide:
            context_parts.append("\n## 제공할 자원")
            for resource in assessment.resources_to_provide:
                context_parts.append(f"- {resource}")

        # 금지 사항
        context_parts.append("""
## ⛔ 금지 사항
- 비밀 유지 약속 금지 (안전이 최우선)
- 판단이나 비난 금지
- 혼자 해결하려 하지 말 것
- "힘내세요" 등 피상적 위로 금지
""")

        return "\n".join(context_parts)


# =============================================================================
# 통합 위기 관리 시스템
# =============================================================================

class CrisisManagementSystem:
    """통합 위기 관리 시스템"""

    def __init__(self):
        self.detector = MultiLayerCrisisDetector()
        self.plan_generator = SafetyPlanGenerator()
        self.response_generator = CrisisResponseGenerator()

    def process_message(
        self,
        message: str,
        user_id: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None,
        user_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        메시지 처리 및 위기 대응

        Args:
            message: 사용자 메시지
            user_id: 사용자 ID
            conversation_history: 대화 이력
            user_context: 사용자 맥락

        Returns:
            처리 결과 딕셔너리
        """
        # 위기 평가
        assessment = self.detector.detect_crisis(
            message, user_id, conversation_history
        )

        result = {
            "assessment": assessment,
            "crisis_detected": assessment.level.value >= CrisisLevel.MODERATE.value,
            "crisis_level": assessment.level.name,
            "crisis_response": None,
            "safety_plan": None,
            "prompt_context": None,
            "action_required": assessment.immediate_action_required
        }

        # 위기 응답 생성
        if assessment.level.value >= CrisisLevel.MODERATE.value:
            result["crisis_response"] = self.response_generator.generate_crisis_response(
                assessment
            )
            result["prompt_context"] = self.response_generator.generate_crisis_prompt_context(
                assessment
            )

        # 안전 계획 생성 (HIGH 이상)
        if assessment.safety_plan_needed:
            result["safety_plan"] = self.plan_generator.generate_safety_plan(
                assessment, user_context
            )

        return result

    def get_crisis_history(self, user_id: str) -> List[Dict]:
        """사용자의 위기 이력 조회"""
        history = self.detector.user_crisis_history.get(user_id, [])
        return [
            {
                "timestamp": h.timestamp.isoformat(),
                "level": h.level.name,
                "types": [t.value for t in h.crisis_types],
                "confidence": h.confidence
            }
            for h in history
        ]


# =============================================================================
# 팩토리 함수
# =============================================================================

_crisis_system: Optional[CrisisManagementSystem] = None

def get_crisis_system() -> CrisisManagementSystem:
    """위기 관리 시스템 싱글톤"""
    global _crisis_system
    if _crisis_system is None:
        _crisis_system = CrisisManagementSystem()
    return _crisis_system


# =============================================================================
# 테스트
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("고도화된 위기 대응 시스템 테스트")
    print("=" * 60)

    system = get_crisis_system()

    test_messages = [
        "요즘 좀 힘들어요",
        "죽고 싶어요. 더 이상 못 견디겠어요",
        "자살 방법을 찾아봤어요",
        "지금 약을 모아뒀어요. 오늘 밤에 먹으려고요",
        "남편한테 매일 맞아요. 도망갈 수가 없어요",
    ]

    for msg in test_messages:
        print(f"\n[메시지] {msg}")
        print("-" * 40)

        result = system.process_message(msg, user_id="test_user")

        print(f"위기 수준: {result['crisis_level']}")
        print(f"위기 감지: {result['crisis_detected']}")
        print(f"즉각 조치: {result['action_required']}")

        if result['crisis_response']:
            print(f"\n[위기 응답]\n{result['crisis_response'][:300]}...")

        if result['safety_plan']:
            print("\n[안전 계획 생성됨]")
