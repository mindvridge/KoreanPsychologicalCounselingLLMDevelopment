"""
윤리적 경계 시스템 (Ethical Boundaries System)

AI 상담 챗봇의 윤리적 경계 관리:
1. AI 정체성 명시 - AI임을 분명히 밝힘
2. 역할 한계 인식 - 상담 범위 판단
3. 전문가 연계 판단 - 연계 필요 시점 감지
4. 이중관계 방지 - 부적절한 관계 형성 차단
5. 비밀보장 한계 - 비밀보장 예외 상황 처리
6. 동의 및 자율성 - 내담자 권리 존중
"""

from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass, field
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)


# =============================================================================
# 윤리적 경계 유형 및 데이터 구조
# =============================================================================

class EthicalDomain(Enum):
    """윤리적 영역"""
    AI_IDENTITY = "ai_identity"                 # AI 정체성
    COMPETENCE_LIMITS = "competence_limits"     # 역량 한계
    REFERRAL_NEEDED = "referral_needed"         # 전문가 연계
    DUAL_RELATIONSHIP = "dual_relationship"     # 이중관계
    CONFIDENTIALITY = "confidentiality"         # 비밀보장
    INFORMED_CONSENT = "informed_consent"       # 동의
    CLIENT_AUTONOMY = "client_autonomy"         # 자율성
    SCOPE_OF_PRACTICE = "scope_of_practice"     # 업무 범위


class ReferralUrgency(Enum):
    """전문가 연계 긴급도"""
    IMMEDIATE = "immediate"     # 즉시 (위기 상황)
    URGENT = "urgent"           # 긴급 (24-48시간 내)
    RECOMMENDED = "recommended" # 권장 (가까운 시일 내)
    OPTIONAL = "optional"       # 선택적 (필요시)


@dataclass
class EthicalIssue:
    """윤리적 이슈"""
    domain: EthicalDomain
    description: str
    detected_text: str
    recommendation: str
    urgency: Optional[ReferralUrgency] = None


@dataclass
class EthicalAssessment:
    """윤리적 평가 결과"""
    issues: List[EthicalIssue] = field(default_factory=list)
    ai_disclosure_needed: bool = False
    referral_needed: bool = False
    referral_urgency: Optional[ReferralUrgency] = None
    referral_resources: List[str] = field(default_factory=list)
    boundary_alerts: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)


# =============================================================================
# 1. AI 정체성 관리
# =============================================================================

class AIIdentityManager:
    """
    AI 정체성 명시 관리

    AI가 자신의 정체성을 적절히 밝히도록 관리
    """

    # AI 정체성 관련 질문 패턴
    IDENTITY_QUESTION_PATTERNS = [
        r"(당신|너|선생님).*?(누구|뭐|사람|AI|인공지능|로봇)",
        r"(진짜|실제|정말).*?(사람|상담사|선생님)",
        r"(자격|면허|자격증).*?(있|가지)",
        r"(어디서|어떻게).*?(상담|공부|배)",
        r"(경험|경력).*?(얼마나|몇|많)",
        r"이름이\s*(뭐|무엇)",
    ]

    # AI 정체성 밝히는 표현
    AI_DISCLOSURE_STATEMENTS = {
        "basic": "저는 AI 상담 도우미예요. 전문 상담사는 아니지만, 함께 이야기 나눌 수 있어요.",
        "detailed": """저는 AI 기반의 심리상담 도우미입니다.
전문 상담사나 치료사는 아니지만, 심리상담 지식을 바탕으로 대화를 나눌 수 있어요.
깊은 상담이 필요하시면 전문 상담사 연결을 도와드릴 수 있습니다.""",
        "limitation": "AI로서 한계가 있지만, 말씀하시는 내용에 귀 기울이고 함께 생각해 볼 수 있어요.",
        "reassurance": "비록 AI이지만, 당신의 이야기를 진심으로 듣고 있어요."
    }

    # 인간인 척하는 표현 (금지)
    HUMAN_PRETENSE_PATTERNS = [
        r"저도\s*(사람|인간)으로서",
        r"제\s*(경험|경력)으로는",
        r"(수년간|오랫동안).*?상담.*?(해왔|해오)",
        r"(전문|임상).*?(자격|면허|경력)",
        r"(대학|대학원).*?(공부|전공)",
    ]

    def __init__(self):
        self.identity_patterns = [re.compile(p, re.IGNORECASE) for p in self.IDENTITY_QUESTION_PATTERNS]
        self.pretense_patterns = [re.compile(p, re.IGNORECASE) for p in self.HUMAN_PRETENSE_PATTERNS]
        logger.info("AIIdentityManager initialized")

    def check_identity_question(self, user_message: str) -> bool:
        """사용자가 AI 정체성에 대해 질문하는지 확인"""
        for pattern in self.identity_patterns:
            if pattern.search(user_message):
                return True
        return False

    def check_human_pretense(self, response: str) -> List[str]:
        """AI가 인간인 척하는 표현이 있는지 확인"""
        pretenses = []
        for pattern in self.pretense_patterns:
            matches = pattern.findall(response)
            pretenses.extend(matches)
        return pretenses

    def get_disclosure_statement(self, context: str = "basic") -> str:
        """적절한 AI 정체성 밝히기 문구 반환"""
        return self.AI_DISCLOSURE_STATEMENTS.get(context, self.AI_DISCLOSURE_STATEMENTS["basic"])

    def should_disclose_identity(self, conversation_turn: int, last_disclosure_turn: int) -> bool:
        """
        AI 정체성을 밝혀야 하는지 판단

        - 첫 번째 응답
        - 20턴마다 자연스럽게 상기
        - 직접 질문 시
        """
        if conversation_turn == 0:
            return True
        if conversation_turn - last_disclosure_turn >= 20:
            return True
        return False


# =============================================================================
# 2. 역량 한계 관리
# =============================================================================

class CompetenceLimitsManager:
    """
    AI 역량 한계 인식 및 관리

    AI가 다룰 수 있는 영역과 그렇지 않은 영역 구분
    """

    # AI가 다룰 수 있는 영역
    WITHIN_COMPETENCE = {
        "emotional_support": "감정적 지지 및 공감",
        "active_listening": "적극적 경청",
        "reflection": "감정/내용 반영",
        "general_coping": "일반적 대처 전략",
        "psychoeducation": "심리 교육 (일반 정보)",
        "resource_info": "자원 정보 제공",
        "grounding": "그라운딩 기법",
        "breathing": "호흡 기법",
        "journaling": "저널링 안내",
    }

    # AI 역량 밖 영역
    BEYOND_COMPETENCE = {
        "diagnosis": {
            "description": "정신건강 진단",
            "indicators": ["진단", "~증", "~장애", "병명"],
            "referral": "정신건강의학과 전문의"
        },
        "medication": {
            "description": "약물 치료",
            "indicators": ["약", "복용", "처방", "부작용"],
            "referral": "정신건강의학과 전문의 또는 약사"
        },
        "crisis": {
            "description": "위기 개입",
            "indicators": ["자살", "자해", "죽고 싶", "해치고 싶"],
            "referral": "자살예방상담전화 1393"
        },
        "trauma_processing": {
            "description": "트라우마 심층 처리",
            "indicators": ["트라우마", "PTSD", "플래시백", "학대 경험"],
            "referral": "트라우마 전문 상담사"
        },
        "legal": {
            "description": "법적 조언",
            "indicators": ["소송", "고소", "법적", "권리"],
            "referral": "법률 전문가 또는 법률구조공단(132)"
        },
        "financial": {
            "description": "재정 조언",
            "indicators": ["투자", "빚", "파산", "재정"],
            "referral": "재무 상담사 또는 신용회복위원회"
        },
        "medical": {
            "description": "의학적 조언",
            "indicators": ["증상", "치료", "수술", "검사"],
            "referral": "의료 전문가"
        },
        "substance": {
            "description": "물질 중독 치료",
            "indicators": ["중독", "금단", "알코올", "마약"],
            "referral": "중독관리통합지원센터"
        },
    }

    def __init__(self):
        logger.info("CompetenceLimitsManager initialized")

    def assess_competence(self, message: str, topic: str = "") -> Dict[str, Any]:
        """
        주제가 AI 역량 내인지 평가

        Returns:
            Dict: {
                "within_competence": bool,
                "area": str,
                "referral_needed": bool,
                "referral_to": str
            }
        """
        for area, info in self.BEYOND_COMPETENCE.items():
            for indicator in info["indicators"]:
                if indicator in message:
                    return {
                        "within_competence": False,
                        "area": area,
                        "description": info["description"],
                        "referral_needed": True,
                        "referral_to": info["referral"]
                    }

        return {
            "within_competence": True,
            "area": "general_support",
            "description": "일반적 지지 및 상담",
            "referral_needed": False,
            "referral_to": None
        }

    def get_limitation_statement(self, area: str) -> str:
        """역량 한계 설명 문구"""
        statements = {
            "diagnosis": "정확한 상태 파악은 전문가의 평가가 필요해요.",
            "medication": "약물에 관한 부분은 전문 의료인과 상담하시는 게 좋겠어요.",
            "crisis": "지금 상황이 걱정됩니다. 전문 상담원의 도움이 필요해 보여요.",
            "trauma_processing": "트라우마 관련 깊은 작업은 전문가와 함께하시는 게 안전해요.",
            "legal": "법적인 부분은 법률 전문가의 조언이 필요해요.",
            "financial": "재정 문제는 전문 상담사와 상담해 보시는 게 좋겠어요.",
            "medical": "건강 관련 부분은 의료 전문가와 상담하시길 권해드려요.",
            "substance": "중독 관련 전문적인 도움을 받으시면 좋겠어요.",
        }
        return statements.get(area, "이 부분은 전문가의 도움이 필요할 수 있어요.")


# =============================================================================
# 3. 전문가 연계 판단
# =============================================================================

class ReferralDecisionSystem:
    """
    전문가 연계 필요성 판단 시스템
    """

    # 연계 기준
    REFERRAL_CRITERIA = {
        ReferralUrgency.IMMEDIATE: {
            "description": "즉시 전문가 연계 필요",
            "indicators": [
                "자살 계획", "자살 시도", "자해 중",
                "타인 해칠", "정신병적 증상", "현실 왜곡",
                "학대 진행 중", "급성 위기"
            ],
            "resources": [
                "자살예방상담전화: 1393",
                "정신건강위기상담전화: 1577-0199",
                "경찰: 112",
                "응급실"
            ]
        },
        ReferralUrgency.URGENT: {
            "description": "24-48시간 내 전문가 상담 권장",
            "indicators": [
                "자살 사고", "자해 충동", "심한 우울",
                "공황 증상", "심한 불안", "섭식 문제",
                "물질 사용 문제", "심각한 관계 문제"
            ],
            "resources": [
                "정신건강복지센터",
                "정신건강의학과",
                "위기상담센터"
            ]
        },
        ReferralUrgency.RECOMMENDED: {
            "description": "전문 상담 권장",
            "indicators": [
                "지속적 우울", "만성 불안", "트라우마",
                "관계 패턴 문제", "자존감 문제",
                "진로/직업 고민", "가족 갈등"
            ],
            "resources": [
                "심리상담센터",
                "대학상담센터",
                "청소년상담복지센터(1388)"
            ]
        },
        ReferralUrgency.OPTIONAL: {
            "description": "필요시 전문 상담 고려",
            "indicators": [
                "일시적 스트레스", "가벼운 고민",
                "정보 탐색", "자기 이해"
            ],
            "resources": [
                "지역 상담센터",
                "온라인 상담 서비스"
            ]
        }
    }

    # 한국 정신건강 자원
    KOREAN_RESOURCES = {
        "crisis": {
            "자살예방상담전화": {"number": "1393", "hours": "24시간"},
            "정신건강위기상담전화": {"number": "1577-0199", "hours": "24시간"},
            "생명의전화": {"number": "1588-9191", "hours": "24시간"},
        },
        "general": {
            "정신건강복지센터": {"description": "전국 지역별 센터 운영", "search": "정신건강복지센터 + 지역명"},
            "청소년상담복지센터": {"number": "1388", "target": "청소년/부모"},
            "여성긴급전화": {"number": "1366", "target": "여성 폭력 피해"},
        },
        "online": {
            "마인드온": {"url": "mind-on.kr", "description": "온라인 심리검사 및 상담"},
            "청소년사이버상담센터": {"url": "cyber1388.kr", "target": "청소년"},
        }
    }

    def __init__(self):
        logger.info("ReferralDecisionSystem initialized")

    def assess_referral_need(self, message: str, context: List[str] = None) -> Dict[str, Any]:
        """
        전문가 연계 필요성 평가

        Returns:
            Dict: 연계 평가 결과
        """
        for urgency, criteria in self.REFERRAL_CRITERIA.items():
            for indicator in criteria["indicators"]:
                if indicator in message:
                    return {
                        "referral_needed": True,
                        "urgency": urgency,
                        "description": criteria["description"],
                        "matched_indicator": indicator,
                        "resources": criteria["resources"]
                    }

        return {
            "referral_needed": False,
            "urgency": None,
            "description": "현재 전문가 연계 필요성 낮음",
            "resources": []
        }

    def get_referral_message(self, urgency: ReferralUrgency) -> str:
        """연계 안내 메시지 생성"""
        messages = {
            ReferralUrgency.IMMEDIATE: """
지금 상황이 많이 걱정됩니다.
지금 바로 전문 상담원과 이야기하시는 게 중요해요.

📞 자살예방상담전화: 1393 (24시간)
📞 정신건강위기상담전화: 1577-0199 (24시간)

전화하기 어려우시면, 가까운 응급실을 방문해 주세요.
""",
            ReferralUrgency.URGENT: """
지금 경험하고 계신 것이 힘드시겠어요.
가까운 시일 내에 전문가와 상담해 보시는 것을 권해드려요.

🏥 가까운 정신건강복지센터
🏥 정신건강의학과

예약이 어려우시면 정신건강위기상담전화(1577-0199)에서
상담 연계를 도와받으실 수 있어요.
""",
            ReferralUrgency.RECOMMENDED: """
말씀하신 부분은 전문 상담사와 더 깊이 이야기 나누시면
도움이 될 것 같아요.

심리상담센터나 정신건강복지센터에서 상담을 받아보시는 건 어떨까요?
비용이 부담되시면 지역 정신건강복지센터에서 무료/저렴한 상담을 받으실 수 있어요.
""",
            ReferralUrgency.OPTIONAL: """
필요하시면 전문 상담도 고려해 보실 수 있어요.
지역 상담센터나 온라인 상담 서비스도 있으니 참고해 주세요.
"""
        }
        return messages.get(urgency, "")

    def get_resources_for_issue(self, issue_type: str) -> List[Dict[str, str]]:
        """이슈 유형별 자원 반환"""
        if issue_type in ["자살", "자해", "위기"]:
            return [self.KOREAN_RESOURCES["crisis"]]
        elif issue_type in ["청소년", "학교"]:
            return [{"청소년상담복지센터": self.KOREAN_RESOURCES["general"]["청소년상담복지센터"]}]
        elif issue_type in ["여성", "폭력", "가정폭력"]:
            return [{"여성긴급전화": self.KOREAN_RESOURCES["general"]["여성긴급전화"]}]
        else:
            return [self.KOREAN_RESOURCES["general"]]


# =============================================================================
# 4. 이중관계 방지
# =============================================================================

class DualRelationshipPrevention:
    """
    이중관계 형성 방지

    상담 관계 외 다른 관계 형성 시도 감지 및 차단
    """

    # 이중관계 시도 패턴
    DUAL_RELATIONSHIP_PATTERNS = {
        "personal_relationship": {
            "patterns": [
                r"(친구|연인|애인).*?(되|하|될)",
                r"(만나|데이트|밥).*?(먹|할|하)",
                r"(연락|카톡|문자).*?(해|할|주)",
                r"(번호|연락처|SNS|인스타).*?(알려|교환|가르쳐)",
            ],
            "response": "저는 AI 상담 도우미로서 여기서 대화를 나누는 역할을 해요. 상담 관계 안에서 도움을 드리고 싶어요."
        },
        "business_relationship": {
            "patterns": [
                r"(사업|비즈니스|일).*?(같이|함께)",
                r"(투자|돈).*?(같이|함께)",
                r"(홍보|광고).*?(해|해줘)",
            ],
            "response": "저는 심리상담 대화를 위한 AI예요. 다른 활동은 어려워요."
        },
        "excessive_dependency": {
            "patterns": [
                r"(당신|너)만.*?(믿|의지|기댈)",
                r"(항상|계속|평생).*?(함께|옆에)",
                r"(당신|너).*?없으면.*?(못|안)",
            ],
            "response": "마음을 나눠주셔서 감사해요. 다만 저는 AI이고, 실제 관계에서 지지를 받으시는 것도 중요해요."
        }
    }

    def __init__(self):
        self._compile_patterns()
        logger.info("DualRelationshipPrevention initialized")

    def _compile_patterns(self):
        self.compiled_patterns = {}
        for category, info in self.DUAL_RELATIONSHIP_PATTERNS.items():
            self.compiled_patterns[category] = {
                "patterns": [re.compile(p) for p in info["patterns"]],
                "response": info["response"]
            }

    def check_dual_relationship_attempt(self, message: str) -> Optional[Dict[str, str]]:
        """이중관계 시도 감지"""
        for category, info in self.compiled_patterns.items():
            for pattern in info["patterns"]:
                if pattern.search(message):
                    return {
                        "category": category,
                        "response": info["response"]
                    }
        return None

    def get_boundary_statement(self) -> str:
        """경계 설정 문구"""
        return """
저는 AI 상담 도우미로서, 이 공간에서 대화를 통해 도움을 드리는 역할을 해요.
상담 관계의 경계를 지키는 것은 당신을 위한 것이기도 해요.
여기서 편하게 이야기 나누시면 좋겠어요.
"""


# =============================================================================
# 5. 비밀보장 관리
# =============================================================================

class ConfidentialityManager:
    """
    비밀보장 원칙 및 예외 관리
    """

    # 비밀보장 예외 상황
    CONFIDENTIALITY_EXCEPTIONS = {
        "self_harm_risk": {
            "description": "자해/자살 위험",
            "indicators": ["죽고 싶", "자살", "자해", "끝내고 싶"],
            "action": "안전을 위해 위기 개입 자원 연결"
        },
        "harm_to_others": {
            "description": "타인 위해 위험",
            "indicators": ["죽이고 싶", "해치고 싶", "복수", "폭행 계획"],
            "action": "타인 보호를 위한 조치 안내"
        },
        "child_abuse": {
            "description": "아동 학대",
            "indicators": ["아이를 때려", "아동 학대", "아이 방치"],
            "action": "아동보호전문기관 신고 안내 (112)"
        },
        "elder_abuse": {
            "description": "노인 학대",
            "indicators": ["노인 학대", "부모님 때려", "노인 방치"],
            "action": "노인보호전문기관 안내 (1577-1389)"
        },
        "ongoing_crime": {
            "description": "진행 중인 범죄",
            "indicators": ["지금 당하고", "갇혀 있", "폭행당하"],
            "action": "긴급 신고 안내 (112)"
        }
    }

    # 비밀보장 안내문
    CONFIDENTIALITY_STATEMENT = """
🔒 비밀보장 안내

대화 내용은 기본적으로 비밀이 보장됩니다.
다만, 다음의 경우에는 안전을 위해 예외가 적용될 수 있어요:

- 본인 또는 타인을 해칠 위험이 있는 경우
- 아동/노인 학대가 의심되는 경우
- 진행 중인 범죄 상황인 경우

이런 경우에는 안전을 위한 자원을 안내해 드려요.
"""

    def __init__(self):
        logger.info("ConfidentialityManager initialized")

    def check_confidentiality_exception(self, message: str) -> Optional[Dict[str, Any]]:
        """비밀보장 예외 상황 확인"""
        for exception_type, info in self.CONFIDENTIALITY_EXCEPTIONS.items():
            for indicator in info["indicators"]:
                if indicator in message:
                    return {
                        "exception_type": exception_type,
                        "description": info["description"],
                        "action": info["action"]
                    }
        return None

    def get_confidentiality_statement(self) -> str:
        """비밀보장 안내문 반환"""
        return self.CONFIDENTIALITY_STATEMENT

    def get_exception_response(self, exception_type: str) -> str:
        """예외 상황별 대응 문구"""
        responses = {
            "self_harm_risk": "당신의 안전이 가장 중요해요. 지금 전문 상담원과 이야기하시는 게 필요해 보여요. 1393으로 연락해 주세요.",
            "harm_to_others": "힘든 마음이 느껴져요. 하지만 안전을 위해 전문적인 도움이 필요해 보여요.",
            "child_abuse": "아이의 안전이 걱정됩니다. 아동보호전문기관(112)에서 도움을 받으실 수 있어요.",
            "elder_abuse": "어르신의 안전이 걱정됩니다. 노인보호전문기관(1577-1389)에서 도움을 받으실 수 있어요.",
            "ongoing_crime": "지금 상황이 위험해 보여요. 안전한 곳으로 이동하시고 112에 연락해 주세요."
        }
        return responses.get(exception_type, "")


# =============================================================================
# 6. 동의 및 자율성 관리
# =============================================================================

class ConsentAutonomyManager:
    """
    동의 획득 및 내담자 자율성 존중 관리
    """

    # 초기 동의 안내
    INITIAL_CONSENT_STATEMENT = """
안녕하세요, AI 심리상담 도우미입니다.

📋 시작하기 전에 안내드려요:

1. **AI 상담 도우미**: 저는 AI로, 전문 상담사를 대체하지 않아요.
2. **비밀보장**: 대화 내용은 기본적으로 비밀이 보장되지만,
   안전 위험 시 예외가 있을 수 있어요.
3. **전문가 연계**: 필요시 전문 상담 자원을 안내해 드려요.
4. **자유로운 종료**: 언제든 대화를 멈추실 수 있어요.

편하게 이야기 나눠요. 오늘 어떤 마음으로 오셨나요?
"""

    # 자율성 침해 표현 (피해야 할 표현)
    AUTONOMY_VIOLATION_PATTERNS = [
        r"(반드시|꼭|무조건).*?(해야|하세요)",
        r"제\s*말대로",
        r"다른\s*방법.*?없",
        r"선택의\s*여지.*?없",
    ]

    # 자율성 존중 표현
    AUTONOMY_RESPECTING_PHRASES = [
        "선택은 당신의 것이에요.",
        "어떻게 하실지는 당신이 결정하시는 거예요.",
        "여러 가지 방법이 있을 수 있어요.",
        "당신이 원하시는 방향으로 가시면 돼요.",
        "무엇이 맞는지는 당신이 가장 잘 아실 거예요.",
    ]

    def __init__(self):
        self.violation_patterns = [re.compile(p) for p in self.AUTONOMY_VIOLATION_PATTERNS]
        logger.info("ConsentAutonomyManager initialized")

    def get_initial_consent(self) -> str:
        """초기 동의 안내문"""
        return self.INITIAL_CONSENT_STATEMENT

    def check_autonomy_violation(self, response: str) -> List[str]:
        """자율성 침해 표현 검사"""
        violations = []
        for pattern in self.violation_patterns:
            matches = pattern.findall(response)
            violations.extend(matches)
        return violations

    def get_autonomy_phrase(self) -> str:
        """자율성 존중 문구 반환"""
        import random
        return random.choice(self.AUTONOMY_RESPECTING_PHRASES)


# =============================================================================
# 통합 윤리적 경계 시스템
# =============================================================================

class EthicalBoundarySystem:
    """
    통합 윤리적 경계 시스템

    모든 윤리적 영역을 통합하여 관리
    """

    def __init__(self):
        self.identity = AIIdentityManager()
        self.competence = CompetenceLimitsManager()
        self.referral = ReferralDecisionSystem()
        self.dual_relationship = DualRelationshipPrevention()
        self.confidentiality = ConfidentialityManager()
        self.consent = ConsentAutonomyManager()

        self.last_identity_disclosure = -1
        self.turn_count = 0

        logger.info("EthicalBoundarySystem initialized")

    def assess_ethical_issues(
        self,
        user_message: str,
        assistant_response: str = "",
        turn: int = 0
    ) -> EthicalAssessment:
        """
        윤리적 이슈 종합 평가

        Args:
            user_message: 사용자 메시지
            assistant_response: AI 응답 (검토용)
            turn: 현재 턴 번호

        Returns:
            EthicalAssessment: 평가 결과
        """
        self.turn_count = turn
        assessment = EthicalAssessment()

        # 1. AI 정체성 공개 필요성
        if self.identity.check_identity_question(user_message):
            assessment.ai_disclosure_needed = True
            assessment.issues.append(EthicalIssue(
                domain=EthicalDomain.AI_IDENTITY,
                description="사용자가 AI 정체성에 대해 질문함",
                detected_text=user_message,
                recommendation=self.identity.get_disclosure_statement("detailed")
            ))

        # 응답에서 인간인 척하는 표현 검사
        if assistant_response:
            pretenses = self.identity.check_human_pretense(assistant_response)
            if pretenses:
                assessment.issues.append(EthicalIssue(
                    domain=EthicalDomain.AI_IDENTITY,
                    description="AI가 인간인 척하는 표현 감지",
                    detected_text=str(pretenses),
                    recommendation="AI임을 명확히 밝히는 표현으로 수정"
                ))

        # 2. 역량 한계 평가
        competence_result = self.competence.assess_competence(user_message)
        if not competence_result["within_competence"]:
            assessment.issues.append(EthicalIssue(
                domain=EthicalDomain.COMPETENCE_LIMITS,
                description=f"AI 역량 밖 영역: {competence_result['description']}",
                detected_text=user_message,
                recommendation=self.competence.get_limitation_statement(competence_result["area"])
            ))
            assessment.referral_needed = True
            assessment.referral_resources.append(competence_result["referral_to"])

        # 3. 전문가 연계 필요성
        referral_result = self.referral.assess_referral_need(user_message)
        if referral_result["referral_needed"]:
            assessment.referral_needed = True
            assessment.referral_urgency = referral_result["urgency"]
            assessment.referral_resources.extend(referral_result["resources"])
            assessment.issues.append(EthicalIssue(
                domain=EthicalDomain.REFERRAL_NEEDED,
                description=referral_result["description"],
                detected_text=referral_result.get("matched_indicator", ""),
                recommendation=self.referral.get_referral_message(referral_result["urgency"]),
                urgency=referral_result["urgency"]
            ))

        # 4. 이중관계 시도 감지
        dual_check = self.dual_relationship.check_dual_relationship_attempt(user_message)
        if dual_check:
            assessment.boundary_alerts.append(f"이중관계 시도: {dual_check['category']}")
            assessment.issues.append(EthicalIssue(
                domain=EthicalDomain.DUAL_RELATIONSHIP,
                description=f"이중관계 형성 시도: {dual_check['category']}",
                detected_text=user_message,
                recommendation=dual_check["response"]
            ))

        # 5. 비밀보장 예외 확인
        confidentiality_check = self.confidentiality.check_confidentiality_exception(user_message)
        if confidentiality_check:
            assessment.issues.append(EthicalIssue(
                domain=EthicalDomain.CONFIDENTIALITY,
                description=f"비밀보장 예외: {confidentiality_check['description']}",
                detected_text=user_message,
                recommendation=self.confidentiality.get_exception_response(
                    confidentiality_check["exception_type"]
                )
            ))

        # 6. 자율성 침해 검사 (응답에서)
        if assistant_response:
            autonomy_violations = self.consent.check_autonomy_violation(assistant_response)
            if autonomy_violations:
                assessment.issues.append(EthicalIssue(
                    domain=EthicalDomain.CLIENT_AUTONOMY,
                    description="자율성 침해 표현 감지",
                    detected_text=str(autonomy_violations),
                    recommendation=self.consent.get_autonomy_phrase()
                ))

        # 권장 조치 생성
        assessment.recommended_actions = self._generate_recommendations(assessment)

        return assessment

    def _generate_recommendations(self, assessment: EthicalAssessment) -> List[str]:
        """권장 조치 생성"""
        actions = []

        if assessment.ai_disclosure_needed:
            actions.append("AI 정체성 명확히 밝히기")

        if assessment.referral_needed:
            if assessment.referral_urgency == ReferralUrgency.IMMEDIATE:
                actions.append("즉시 위기 자원 연결")
            elif assessment.referral_urgency == ReferralUrgency.URGENT:
                actions.append("긴급 전문가 연계 권유")
            else:
                actions.append("전문 상담 권유")

        for issue in assessment.issues:
            if issue.domain == EthicalDomain.DUAL_RELATIONSHIP:
                actions.append("경계 설정 및 상담 관계 재확인")
            elif issue.domain == EthicalDomain.CLIENT_AUTONOMY:
                actions.append("자율성 존중 표현으로 수정")

        return actions

    def get_prompt_section(self) -> str:
        """프롬프트에 삽입할 윤리적 경계 가이드"""
        return """
## 윤리적 경계 가이드 - 반드시 준수

### AI 정체성
- AI임을 명확히 밝히기 (특히 직접 질문 시)
- 인간/전문가인 척하지 않기
- "저는 AI 상담 도우미예요"

### 역량 한계 인식
- 진단/처방 하지 않기
- 법적/재정적 조언 하지 않기
- 한계 인정: "이 부분은 전문가와 상담하시는 게 좋겠어요"

### 전문가 연계
- 위기 상황: 즉시 1393/1577-0199 안내
- 심각한 증상: 정신건강의학과 권유
- 지속적 문제: 전문 상담 권유

### 경계 유지
- 상담 외 관계 형성 거절
- 개인정보 교환 거절
- 과도한 의존 부드럽게 다루기

### 비밀보장
- 기본 비밀보장 유지
- 예외: 자해/타해 위험, 학대, 범죄
- 예외 시 안전 자원 연결

### 자율성 존중
- "~해야 해요" → "~해보시면 어떨까요?"
- "선택은 당신의 것이에요"
- 결정 강요하지 않기
"""


# =============================================================================
# 편의 함수
# =============================================================================

_ethical_system: Optional[EthicalBoundarySystem] = None


def get_ethical_system() -> EthicalBoundarySystem:
    """윤리적 경계 시스템 싱글톤 반환"""
    global _ethical_system
    if _ethical_system is None:
        _ethical_system = EthicalBoundarySystem()
    return _ethical_system


def assess_ethical_boundaries(
    user_message: str,
    assistant_response: str = "",
    turn: int = 0
) -> EthicalAssessment:
    """윤리적 경계 빠른 평가"""
    system = get_ethical_system()
    return system.assess_ethical_issues(user_message, assistant_response, turn)


def get_ethical_prompt_section() -> str:
    """프롬프트용 윤리적 경계 섹션"""
    system = get_ethical_system()
    return system.get_prompt_section()


def get_initial_consent_message() -> str:
    """초기 동의 메시지"""
    system = get_ethical_system()
    return system.consent.get_initial_consent()
