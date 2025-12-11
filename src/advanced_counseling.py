"""
고급 상담 기법 모듈 (Advanced Counseling Techniques)

효과적인 상담을 위한 핵심 요소:
1. 치료적 동맹 (Therapeutic Alliance) - 상담 관계의 질
2. 동기강화 면담 (Motivational Interviewing) - 변화 동기 강화
3. 변화 단계 모델 (Stages of Change) - 내담자 준비도 파악
"""

from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass, field
import logging
import re

logger = logging.getLogger(__name__)


# =============================================================================
# 1. 치료적 동맹 (Therapeutic Alliance)
# =============================================================================

class AllianceComponent(Enum):
    """치료적 동맹의 세 가지 구성요소 (Bordin, 1979)"""
    BOND = "bond"          # 정서적 유대 (감정적 연결)
    GOAL = "goal"          # 목표 합의 (상담 목표 공유)
    TASK = "task"          # 과제 합의 (방법 동의)


@dataclass
class AllianceIndicator:
    """동맹 지표"""
    component: AllianceComponent
    strength: float  # 0.0 ~ 1.0
    indicators: List[str]
    concerns: List[str]


@dataclass
class TherapeuticAlliance:
    """치료적 동맹 상태"""
    bond_score: float = 0.5
    goal_score: float = 0.5
    task_score: float = 0.5
    overall_score: float = 0.5
    rupture_detected: bool = False
    rupture_type: Optional[str] = None
    repair_strategies: List[str] = field(default_factory=list)


class TherapeuticAllianceManager:
    """
    치료적 동맹 관리자

    기능:
    - 동맹 강도 측정
    - 동맹 파열 감지
    - 동맹 회복 전략 제공
    """

    # 정서적 유대 강화 표현
    BOND_STRENGTHENING = {
        "validation": [
            "그런 마음이 드시는 게 당연해요",
            "그 상황에서 그렇게 느끼시는 건 자연스러운 거예요",
            "충분히 이해가 됩니다",
            "그 감정은 정말 중요한 거예요",
        ],
        "empathy": [
            "정말 힘드셨겠어요",
            "마음이 많이 아프셨겠어요",
            "얼마나 무거우셨을지 느껴져요",
            "그 고통이 느껴집니다",
        ],
        "presence": [
            "함께 이야기 나눌 수 있어서 좋아요",
            "여기 있어요, 편하게 말씀해 주세요",
            "당신의 이야기를 듣고 있어요",
            "오늘도 이렇게 찾아와 주셨네요",
        ],
        "non_judgment": [
            "어떤 이야기든 편하게 해 주세요",
            "여기서는 판단받지 않으셔도 돼요",
            "있는 그대로의 마음을 나눠주세요",
        ]
    }

    # 목표 합의 촉진 표현
    GOAL_ALIGNMENT = {
        "exploration": [
            "오늘 대화에서 어떤 것이 도움이 되면 좋겠어요?",
            "지금 가장 이야기하고 싶은 부분이 있으신가요?",
            "어떤 부분에 집중하면 좋을까요?",
        ],
        "clarification": [
            "제가 이해한 게 맞을까요?",
            "말씀하신 게 ~라는 의미일까요?",
            "혹시 다른 부분도 있으신가요?",
        ],
        "shared_goal": [
            "그러면 오늘은 ~에 대해 함께 이야기해 볼까요?",
            "~을 목표로 대화해 보는 건 어떨까요?",
            "이 부분을 함께 탐색해 보면 어떨까요?",
        ]
    }

    # 과제 합의 촉진 표현
    TASK_ALIGNMENT = {
        "collaboration": [
            "제가 어떻게 도와드리면 좋을까요?",
            "함께 방법을 찾아볼까요?",
            "어떤 방식이 편하실 것 같으세요?",
        ],
        "pacing": [
            "천천히 가도 괜찮아요",
            "편하신 속도로 진행하면 돼요",
            "무리하지 않으셔도 돼요",
        ],
        "choice": [
            "몇 가지 방법이 있는데, 어떤 게 끌리세요?",
            "선택은 전적으로 당신에게 있어요",
            "해보고 싶은 방법이 있으신가요?",
        ]
    }

    # 동맹 파열 신호
    RUPTURE_SIGNALS = {
        "withdrawal": {
            "keywords": ["모르겠어요", "상관없어요", "별로", "글쎄요", "아무거나"],
            "patterns": ["응답 짧아짐", "감정 표현 감소", "대화 회피"],
            "type": "철수 (Withdrawal)"
        },
        "confrontation": {
            "keywords": ["AI가 뭘 알아", "소용없어", "이해 못 해", "그만", "답답해"],
            "patterns": ["공격적 표현", "불만 표출", "저항"],
            "type": "대립 (Confrontation)"
        },
        "disconnect": {
            "keywords": ["네네", "알겠어요", "그렇군요"],
            "patterns": ["피상적 동의", "형식적 응답", "진정성 부족"],
            "type": "단절 (Disconnect)"
        }
    }

    # 동맹 회복 전략
    REPAIR_STRATEGIES = {
        "withdrawal": [
            "조금 멀어진 느낌이 드는데, 혹시 불편한 부분이 있으셨을까요?",
            "제가 놓친 부분이 있다면 말씀해 주세요",
            "지금 이 대화가 어떻게 느껴지세요?",
            "다른 방식으로 이야기해 볼까요?",
        ],
        "confrontation": [
            "제가 ~라고 말한 부분이 불편하셨던 것 같아요",
            "솔직하게 말씀해 주셔서 감사해요",
            "당신의 반응이 이해돼요. 제가 부족한 부분이 있었네요",
            "AI로서 한계가 있다는 점, 인정해요. 그래도 도움이 되고 싶어요",
        ],
        "disconnect": [
            "지금 이 대화가 도움이 되고 있는지 궁금해요",
            "혹시 다른 방향으로 가고 싶으신 부분이 있을까요?",
            "무엇이 지금 가장 필요하신가요?",
        ],
        "general": [
            "잠시 멈추고 확인해도 될까요?",
            "지금 기분이 어떠세요?",
            "이 대화에서 원하시는 게 있으신가요?",
        ]
    }

    def __init__(self):
        self.alliance_history = []

    def assess_alliance(
        self,
        conversation_history: List[Dict],
        current_message: str
    ) -> TherapeuticAlliance:
        """
        치료적 동맹 평가

        Args:
            conversation_history: 대화 기록
            current_message: 현재 사용자 메시지

        Returns:
            TherapeuticAlliance 객체
        """
        alliance = TherapeuticAlliance()

        # 정서적 유대 평가
        alliance.bond_score = self._assess_bond(conversation_history, current_message)

        # 목표 합의 평가
        alliance.goal_score = self._assess_goal_alignment(conversation_history)

        # 과제 합의 평가
        alliance.task_score = self._assess_task_alignment(conversation_history, current_message)

        # 종합 점수
        alliance.overall_score = (
            alliance.bond_score * 0.4 +
            alliance.goal_score * 0.3 +
            alliance.task_score * 0.3
        )

        # 파열 감지
        rupture_info = self._detect_rupture(current_message, conversation_history)
        alliance.rupture_detected = rupture_info["detected"]
        alliance.rupture_type = rupture_info.get("type")

        if alliance.rupture_detected:
            alliance.repair_strategies = self._get_repair_strategies(rupture_info["type"])

        return alliance

    def _assess_bond(
        self,
        history: List[Dict],
        current_message: str
    ) -> float:
        """정서적 유대 평가"""
        score = 0.5  # 기본 점수

        # 긍정적 신호
        positive_signals = [
            "감사", "고마워", "도움이", "좋아", "편해", "이해해",
            "말할 수 있어", "털어놓", "위로"
        ]
        for signal in positive_signals:
            if signal in current_message:
                score += 0.05

        # 대화 지속성 (더 많은 대화 = 더 강한 유대)
        if len(history) > 5:
            score += 0.1
        if len(history) > 10:
            score += 0.1

        # 자기 개방 정도 (메시지 길이로 추정)
        if len(current_message) > 100:
            score += 0.1
        if len(current_message) > 200:
            score += 0.05

        return min(1.0, max(0.0, score))

    def _assess_goal_alignment(self, history: List[Dict]) -> float:
        """목표 합의 평가"""
        score = 0.5

        # 목표 관련 키워드
        goal_keywords = ["해결", "나아지", "변화", "목표", "원해", "바라"]

        for msg in history[-5:]:  # 최근 5개 메시지
            content = msg.get("content", "")
            for keyword in goal_keywords:
                if keyword in content:
                    score += 0.05

        return min(1.0, score)

    def _assess_task_alignment(
        self,
        history: List[Dict],
        current_message: str
    ) -> float:
        """과제 합의 평가"""
        score = 0.5

        # 협력 신호
        collaboration_signals = [
            "해볼게", "시도해", "노력", "생각해볼게", "적용해", "실천"
        ]

        # 저항 신호
        resistance_signals = [
            "안 될", "못 해", "힘들어서", "귀찮", "싫어", "안 해"
        ]

        for signal in collaboration_signals:
            if signal in current_message:
                score += 0.1

        for signal in resistance_signals:
            if signal in current_message:
                score -= 0.1

        return min(1.0, max(0.0, score))

    def _detect_rupture(
        self,
        message: str,
        history: List[Dict]
    ) -> Dict[str, Any]:
        """동맹 파열 감지"""
        result = {"detected": False, "type": None, "severity": 0}

        for rupture_type, signals in self.RUPTURE_SIGNALS.items():
            keyword_count = sum(1 for kw in signals["keywords"] if kw in message)

            if keyword_count >= 2:
                result["detected"] = True
                result["type"] = rupture_type
                result["severity"] = min(1.0, keyword_count * 0.3)
                break

        # 메시지 길이 급감 감지 (철수 신호)
        if history and len(history) > 3:
            recent_lengths = [len(m.get("content", "")) for m in history[-3:] if m.get("role") == "user"]
            if recent_lengths and len(message) < sum(recent_lengths) / len(recent_lengths) * 0.3:
                result["detected"] = True
                result["type"] = "withdrawal"

        return result

    def _get_repair_strategies(self, rupture_type: str) -> List[str]:
        """파열 유형별 회복 전략"""
        strategies = self.REPAIR_STRATEGIES.get(rupture_type, [])
        if not strategies:
            strategies = self.REPAIR_STRATEGIES["general"]
        return strategies[:3]  # 상위 3개

    def get_alliance_enhancement_prompt(self, alliance: TherapeuticAlliance) -> str:
        """동맹 강화를 위한 프롬프트 추가 지침"""
        prompts = []

        if alliance.bond_score < 0.5:
            prompts.append("[유대 강화 필요] 더 많은 공감과 정서적 인정이 필요합니다.")
            prompts.append(f"권장 표현: {self.BOND_STRENGTHENING['validation'][0]}")

        if alliance.goal_score < 0.5:
            prompts.append("[목표 합의 필요] 상담 방향에 대한 확인이 필요합니다.")
            prompts.append(f"권장 표현: {self.GOAL_ALIGNMENT['exploration'][0]}")

        if alliance.task_score < 0.5:
            prompts.append("[과제 합의 필요] 방법에 대한 협의가 필요합니다.")
            prompts.append(f"권장 표현: {self.TASK_ALIGNMENT['collaboration'][0]}")

        if alliance.rupture_detected:
            prompts.append(f"[⚠️ 동맹 파열 감지: {alliance.rupture_type}]")
            prompts.append("우선 파열 회복에 집중하세요:")
            for strategy in alliance.repair_strategies:
                prompts.append(f"  - {strategy}")

        return "\n".join(prompts) if prompts else ""


# =============================================================================
# 2. 동기강화 면담 (Motivational Interviewing)
# =============================================================================

class MISpirit(Enum):
    """MI의 정신 (Spirit of MI)"""
    PARTNERSHIP = "partnership"       # 파트너십 (협력)
    ACCEPTANCE = "acceptance"         # 수용 (무조건적 긍정)
    COMPASSION = "compassion"         # 연민 (공감)
    EVOCATION = "evocation"          # 유발 (내담자 내면의 자원 끌어내기)


class MIProcess(Enum):
    """MI 과정"""
    ENGAGING = "engaging"            # 관계 형성
    FOCUSING = "focusing"            # 초점 맞추기
    EVOKING = "evoking"             # 유발하기
    PLANNING = "planning"            # 계획하기


@dataclass
class ChangeStatement:
    """변화 대화 (Change Talk)"""
    type: str  # DARN-CAT
    content: str
    strength: float  # 0-1


class MotivationalInterviewing:
    """
    동기강화 면담 (MI) 관리자

    OARS 기술:
    - Open questions (개방형 질문)
    - Affirmations (인정)
    - Reflections (반영)
    - Summaries (요약)

    변화 대화 유형 (DARN-CAT):
    - Desire (욕구): "~하고 싶어요"
    - Ability (능력): "~할 수 있을 것 같아요"
    - Reasons (이유): "~하면 좋을 것 같아요"
    - Need (필요): "~해야 해요"
    - Commitment (다짐): "~할 거예요"
    - Activation (활성화): "~할 준비가 됐어요"
    - Taking steps (실행): "~하고 있어요"
    """

    # OARS 기술 예시
    OARS_TECHNIQUES = {
        "open_questions": {
            "exploring": [
                "그 상황에 대해 좀 더 말씀해 주시겠어요?",
                "어떤 생각이 드셨어요?",
                "그때 어떤 기분이셨어요?",
                "이 문제가 당신에게 어떤 영향을 미치고 있나요?",
            ],
            "change_oriented": [
                "변화가 생긴다면 어떤 모습일까요?",
                "이 상황이 달라지면 뭐가 좋아질까요?",
                "당신이 원하는 건 어떤 모습인가요?",
                "만약 변할 수 있다면, 가장 먼저 뭘 바꾸고 싶으세요?",
            ],
            "values": [
                "당신에게 가장 중요한 건 뭔가요?",
                "어떤 삶을 살고 싶으세요?",
                "무엇이 당신을 움직이게 하나요?",
            ]
        },
        "affirmations": {
            "strength": [
                "어려운 상황에서도 여기까지 오신 것 자체가 대단해요",
                "그런 용기를 가지고 계셨네요",
                "힘든 중에도 ~하신 게 인상적이에요",
                "그런 결정을 내리셨다니 대단해요",
            ],
            "effort": [
                "노력하고 계시는 게 느껴져요",
                "쉽지 않은 일인데 시도하고 계시네요",
                "포기하지 않으셨네요",
            ],
            "insight": [
                "스스로를 잘 알고 계시네요",
                "중요한 깨달음이에요",
                "그렇게 생각하신다니, 많이 고민하셨네요",
            ]
        },
        "reflections": {
            "simple": [
                "~하셨군요",
                "~이/가 힘드셨던 거네요",
                "~에 대한 마음이 있으시군요",
            ],
            "complex": [
                "한편으로는 ~하고 싶지만, 다른 한편으로는 ~도 있으시군요",
                "~라고 말씀하셨는데, 그 안에는 ~에 대한 마음도 있는 것 같아요",
                "겉으로는 ~해 보이지만, 속으로는 ~하신 것 같아요",
            ],
            "amplified": [  # 과장 반영 (양가감정 탐색용)
                "그러니까 전혀 바꿀 생각이 없으신 건가요?",
                "변화가 불가능하다고 느끼시는 거네요?",
            ]
        },
        "summaries": {
            "collecting": "지금까지 말씀하신 걸 정리하면...",
            "linking": "아까 말씀하신 ~와 연결해서 보면...",
            "transitional": "지금까지 이야기를 나눴는데, 여기서 한 걸음 더 나아가 볼까요?",
        }
    }

    # 변화 대화 키워드
    CHANGE_TALK_PATTERNS = {
        "desire": {
            "keywords": ["싶어", "원해", "바라", "되면 좋겠"],
            "strength": 0.3
        },
        "ability": {
            "keywords": ["할 수 있", "가능", "해낼", "됄 것 같"],
            "strength": 0.4
        },
        "reasons": {
            "keywords": ["좋을", "도움이 될", "해야 할 이유", "때문에"],
            "strength": 0.5
        },
        "need": {
            "keywords": ["해야", "필요", "안 하면 안", "달라져야"],
            "strength": 0.6
        },
        "commitment": {
            "keywords": ["할 거", "할게요", "결심", "다짐"],
            "strength": 0.8
        },
        "activation": {
            "keywords": ["준비", "시작할", "해볼", "도전"],
            "strength": 0.9
        },
        "taking_steps": {
            "keywords": ["하고 있", "시작했", "실천", "중이에요"],
            "strength": 1.0
        }
    }

    # 유지 대화 (Sustain Talk) - 변화 저항
    SUSTAIN_TALK_PATTERNS = {
        "keywords": [
            "못 해", "안 돼", "힘들어", "무리야", "소용없어",
            "바뀌지 않아", "이미 늦었", "안 될 거야", "포기"
        ],
        "responses": [
            "쉽지 않은 일이죠. 그래도 여기까지 오신 게 중요해요.",
            "그 마음도 이해가 돼요. 천천히 가도 괜찮아요.",
            "변화가 어렵게 느껴지시는 거죠. 어떤 부분이 가장 힘드세요?",
        ]
    }

    # 양가감정 탐색
    AMBIVALENCE_EXPLORATION = {
        "decisional_balance": [
            "변화하면 좋은 점은 뭐가 있을까요?",
            "그대로 유지하면 어떤 점이 좋으세요?",
            "변화하면 어려운 점은 뭐가 있을까요?",
            "현재 상태의 어려운 점은요?",
        ],
        "importance_confidence": [
            "변화가 얼마나 중요하다고 느끼세요? (0-10점으로)",
            "만약 변하기로 결심하면, 얼마나 자신이 있으세요? (0-10점으로)",
            "왜 0점이 아니라 그 점수인가요?",
            "그 점수에서 한 단계 올라가려면 뭐가 필요할까요?",
        ]
    }

    def __init__(self):
        self.change_talk_history = []

    def detect_change_talk(self, message: str) -> List[ChangeStatement]:
        """
        변화 대화 감지

        Args:
            message: 사용자 메시지

        Returns:
            감지된 변화 대화 리스트
        """
        statements = []

        for talk_type, patterns in self.CHANGE_TALK_PATTERNS.items():
            for keyword in patterns["keywords"]:
                if keyword in message:
                    statements.append(ChangeStatement(
                        type=talk_type,
                        content=message,
                        strength=patterns["strength"]
                    ))
                    break

        return statements

    def detect_sustain_talk(self, message: str) -> bool:
        """유지 대화 (저항) 감지"""
        for keyword in self.SUSTAIN_TALK_PATTERNS["keywords"]:
            if keyword in message:
                return True
        return False

    def get_oars_response(
        self,
        message: str,
        change_talk: List[ChangeStatement],
        has_sustain_talk: bool
    ) -> Dict[str, Any]:
        """
        OARS 기반 응답 전략 생성

        Args:
            message: 사용자 메시지
            change_talk: 감지된 변화 대화
            has_sustain_talk: 유지 대화 여부

        Returns:
            응답 전략
        """
        strategy = {
            "primary_technique": "",
            "suggested_responses": [],
            "rationale": ""
        }

        if change_talk:
            # 변화 대화가 있으면 반영 + 인정
            strongest = max(change_talk, key=lambda x: x.strength)

            if strongest.strength >= 0.8:  # Commitment 이상
                strategy["primary_technique"] = "affirmation"
                strategy["suggested_responses"] = self.OARS_TECHNIQUES["affirmations"]["effort"][:2]
                strategy["rationale"] = "높은 변화 동기 - 인정으로 강화"
            else:
                strategy["primary_technique"] = "reflection"
                strategy["suggested_responses"] = self._get_reflection_for_change_talk(strongest.type)
                strategy["rationale"] = "변화 대화 감지 - 반영으로 증폭"

        elif has_sustain_talk:
            # 유지 대화면 양가감정 탐색
            strategy["primary_technique"] = "exploration"
            strategy["suggested_responses"] = self.AMBIVALENCE_EXPLORATION["importance_confidence"][:2]
            strategy["rationale"] = "저항 감지 - 양가감정 탐색"

        else:
            # 기본 탐색
            strategy["primary_technique"] = "open_question"
            strategy["suggested_responses"] = self.OARS_TECHNIQUES["open_questions"]["change_oriented"][:2]
            strategy["rationale"] = "변화 동기 탐색 필요"

        return strategy

    def _get_reflection_for_change_talk(self, talk_type: str) -> List[str]:
        """변화 대화 유형별 반영 생성"""
        reflections = {
            "desire": ["~하고 싶은 마음이 있으시군요", "그런 바람이 있으셨네요"],
            "ability": ["할 수 있다는 느낌이 드시는군요", "가능성을 보고 계시네요"],
            "reasons": ["변화가 도움이 될 거라고 생각하시는군요"],
            "need": ["꼭 해야 한다고 느끼시는 거네요"],
            "commitment": ["결심하셨군요. 정말 중요한 결정이에요"],
            "activation": ["시작할 준비가 되셨네요"],
            "taking_steps": ["이미 실천하고 계시네요. 대단해요"],
        }
        return reflections.get(talk_type, ["그런 마음이 있으시군요"])

    def get_mi_prompt_addition(
        self,
        change_talk: List[ChangeStatement],
        has_sustain_talk: bool
    ) -> str:
        """MI 기반 프롬프트 추가"""
        prompts = ["[동기강화 면담 지침]"]

        if change_talk:
            prompts.append("✓ 변화 대화 감지됨 - 반영하고 강화하세요:")
            for ct in change_talk[:3]:
                prompts.append(f"  - {ct.type.upper()}: (강도 {ct.strength:.1f})")

        if has_sustain_talk:
            prompts.append("⚡ 유지 대화 감지 - 양가감정 인정하고 탐색하세요")
            prompts.append("  - 저항에 직면하지 말고 굴러가세요 (Roll with resistance)")
            prompts.append("  - 양가감정은 자연스러운 것임을 인정")

        prompts.append("\nOARS 원칙:")
        prompts.append("- Open questions: 변화 동기 탐색하는 개방형 질문")
        prompts.append("- Affirmations: 노력과 강점 인정")
        prompts.append("- Reflections: 변화 대화 반영 및 증폭")
        prompts.append("- Summaries: 변화 대화 위주로 요약")

        return "\n".join(prompts)


# =============================================================================
# 3. 변화 단계 모델 (Transtheoretical Model / Stages of Change)
# =============================================================================

class StageOfChange(Enum):
    """변화 단계"""
    PRECONTEMPLATION = "precontemplation"   # 숙고 전: 변화 의도 없음
    CONTEMPLATION = "contemplation"          # 숙고: 변화 고려 중
    PREPARATION = "preparation"              # 준비: 변화 계획 중
    ACTION = "action"                        # 행동: 변화 실행 중
    MAINTENANCE = "maintenance"              # 유지: 변화 유지 중
    RELAPSE = "relapse"                      # 재발: 이전 단계로 회귀


@dataclass
class StageAssessment:
    """변화 단계 평가"""
    stage: StageOfChange
    confidence: float  # 0-1
    indicators: List[str]
    recommended_approach: str
    suitable_techniques: List[str]


class StagesOfChangeManager:
    """
    변화 단계 모델 관리자

    각 단계별 맞춤 접근법 제공
    """

    # 단계별 키워드 및 지표
    STAGE_INDICATORS = {
        StageOfChange.PRECONTEMPLATION: {
            "keywords": [
                "문제없어", "괜찮아", "바꿀 필요 없", "다 그래",
                "상관없어", "남들도 다", "뭐가 문제야"
            ],
            "patterns": [
                "문제 인식 부재",
                "타인 탓",
                "방어적 태도",
                "변화 필요성 부정",
            ],
            "description": "문제를 인식하지 못하거나 변화 의도가 없는 상태"
        },
        StageOfChange.CONTEMPLATION: {
            "keywords": [
                "어쩌면", "생각해봐", "고민", "양가", "한편으로는",
                "변해야 하나", "이러면 안 되는데", "알긴 알아"
            ],
            "patterns": [
                "양가감정",
                "문제 인식은 있음",
                "변화 시기 불확실",
                "장단점 저울질",
            ],
            "description": "변화를 고려하고 있지만 아직 결정하지 못한 상태"
        },
        StageOfChange.PREPARATION: {
            "keywords": [
                "해봐야겠", "시작해볼까", "준비", "계획", "언제부터",
                "어떻게 하면", "방법을 찾고"
            ],
            "patterns": [
                "구체적 계획 언급",
                "실행 시기 설정",
                "방법 탐색",
                "작은 시도 시작",
            ],
            "description": "곧 변화를 시작하려는 구체적 계획이 있는 상태"
        },
        StageOfChange.ACTION: {
            "keywords": [
                "하고 있어", "시작했어", "요즘", "바꾸고 있",
                "노력 중", "실천하고", "변했어"
            ],
            "patterns": [
                "적극적 변화 행동",
                "새로운 행동 실천",
                "환경 변화",
                "도움 요청",
            ],
            "description": "적극적으로 변화를 실천하고 있는 상태"
        },
        StageOfChange.MAINTENANCE: {
            "keywords": [
                "유지하고", "계속", "꾸준히", "습관", "벌써 몇 달",
                "이제는", "자연스럽게"
            ],
            "patterns": [
                "변화 유지 6개월+",
                "재발 방지 전략",
                "새로운 정체성",
                "자기효능감 높음",
            ],
            "description": "변화를 6개월 이상 유지하고 있는 상태"
        },
        StageOfChange.RELAPSE: {
            "keywords": [
                "다시", "또", "못 지켰", "실패", "포기", "예전으로",
                "돌아갔", "안 되더라"
            ],
            "patterns": [
                "이전 행동 복귀",
                "실패감",
                "자기비난",
                "동기 저하",
            ],
            "description": "변화를 유지하다가 이전 행동으로 돌아간 상태"
        }
    }

    # 단계별 상담 접근법
    STAGE_APPROACHES = {
        StageOfChange.PRECONTEMPLATION: {
            "goal": "인식 제고 (Raise Awareness)",
            "approach": [
                "공감과 수용으로 관계 형성",
                "정보 제공 (요청 시에만)",
                "현재 상태의 결과 탐색 (비판 없이)",
                "자기탐색 격려",
            ],
            "avoid": [
                "변화 강요",
                "설득 시도",
                "문제 직면",
                "조언이나 충고",
            ],
            "techniques": [
                "개방형 질문",
                "반영적 경청",
                "정보 제공 (허락 후)",
            ],
            "sample_responses": [
                "그렇게 느끼시는군요. 좀 더 말씀해 주시겠어요?",
                "지금 상황이 어떤지 궁금해요. 일상이 어떠세요?",
                "변화에 대한 생각이 없으셔도 괜찮아요. 지금 이야기만 나눠도 좋아요.",
            ]
        },
        StageOfChange.CONTEMPLATION: {
            "goal": "양가감정 탐색 및 해결",
            "approach": [
                "양가감정 인정 및 탐색",
                "결정 저울 (장단점 분석)",
                "가치관과 목표 연결",
                "변화 대화 유발",
            ],
            "avoid": [
                "조급한 결정 강요",
                "한쪽만 강조",
                "판단적 태도",
            ],
            "techniques": [
                "결정 저울 (Decisional Balance)",
                "중요성-자신감 척도",
                "복합 반영",
                "가치 탐색",
            ],
            "sample_responses": [
                "한편으로는 ~하고 싶지만, 다른 한편으로는 걱정도 되시는 거죠?",
                "변화했을 때의 좋은 점과 어려운 점을 함께 생각해 볼까요?",
                "이 변화가 당신에게 왜 중요한가요?",
            ]
        },
        StageOfChange.PREPARATION: {
            "goal": "구체적 계획 수립 지원",
            "approach": [
                "구체적인 계획 수립 도움",
                "장애물 예측 및 대비",
                "지지체계 확인",
                "작은 첫 걸음 격려",
            ],
            "avoid": [
                "비현실적 목표",
                "너무 큰 변화",
                "지나친 계획",
            ],
            "techniques": [
                "SMART 목표 설정",
                "장애물 예측",
                "지지체계 매핑",
                "변화 실험",
            ],
            "sample_responses": [
                "어떤 것부터 시작하면 좋을까요?",
                "그걸 하다가 어려움이 생기면 어떻게 하실 계획이세요?",
                "도움을 줄 수 있는 사람이 주변에 있으신가요?",
            ]
        },
        StageOfChange.ACTION: {
            "goal": "변화 행동 강화 및 지지",
            "approach": [
                "노력 인정 및 격려",
                "성공 경험 확대",
                "문제 해결 지원",
                "재발 예방 교육",
            ],
            "avoid": [
                "과도한 기대",
                "완벽 요구",
                "조급함",
            ],
            "techniques": [
                "긍정 강화",
                "문제 해결 기술",
                "위험 상황 인식",
                "대처 전략 개발",
            ],
            "sample_responses": [
                "정말 노력하고 계시네요. 어떤 부분이 가장 도움이 됐나요?",
                "지금까지 잘 하고 계세요. 어려운 순간은 어떻게 넘기셨어요?",
                "힘든 상황이 오면 어떻게 대처하실 계획이세요?",
            ]
        },
        StageOfChange.MAINTENANCE: {
            "goal": "유지 강화 및 재발 예방",
            "approach": [
                "변화 유지 축하",
                "새로운 정체성 강화",
                "재발 위험 요인 모니터링",
                "지속적 성장 지원",
            ],
            "avoid": [
                "방심",
                "과거 집착",
                "지지 철수",
            ],
            "techniques": [
                "재발 예방 계획",
                "장기 목표 설정",
                "정체성 강화",
                "지지체계 유지",
            ],
            "sample_responses": [
                "오랜 기간 유지하고 계시네요, 정말 대단해요!",
                "어떤 것이 이렇게 오래 유지하는 데 도움이 됐나요?",
                "혹시 다시 힘들어질 것 같은 상황이 있을까요?",
            ]
        },
        StageOfChange.RELAPSE: {
            "goal": "재시작 지원 및 학습",
            "approach": [
                "비난 없이 수용",
                "실패가 아닌 학습으로 재프레이밍",
                "이전 성공 경험 상기",
                "재시작 동기 강화",
            ],
            "avoid": [
                "비난",
                "실패감 강화",
                "포기 암시",
            ],
            "techniques": [
                "자기자비",
                "재프레이밍",
                "이전 성공 분석",
                "장애물 분석",
            ],
            "sample_responses": [
                "다시 돌아가셨군요. 변화는 직선이 아니라 나선형이에요. 괜찮아요.",
                "이번에 뭘 배우셨나요? 그게 다음번에 도움이 될 거예요.",
                "전에는 ~까지 하셨잖아요. 그 힘이 아직 있어요.",
            ]
        }
    }

    def __init__(self):
        self.stage_history = []

    def assess_stage(
        self,
        message: str,
        conversation_history: List[Dict]
    ) -> StageAssessment:
        """
        변화 단계 평가

        Args:
            message: 현재 메시지
            conversation_history: 대화 기록

        Returns:
            StageAssessment 객체
        """
        scores = {}

        # 각 단계별 점수 계산
        for stage, indicators in self.STAGE_INDICATORS.items():
            score = 0
            found_indicators = []

            for keyword in indicators["keywords"]:
                if keyword in message:
                    score += 1
                    found_indicators.append(keyword)

            scores[stage] = {
                "score": score,
                "indicators": found_indicators
            }

        # 최고 점수 단계 선택
        best_stage = max(scores.items(), key=lambda x: x[1]["score"])

        # 기본값 설정 (점수가 0이면)
        if best_stage[1]["score"] == 0:
            # 대화 길이와 내용으로 추정
            if len(conversation_history) < 3:
                selected_stage = StageOfChange.CONTEMPLATION  # 기본
            else:
                selected_stage = StageOfChange.CONTEMPLATION
        else:
            selected_stage = best_stage[0]

        # 접근법 가져오기
        approach = self.STAGE_APPROACHES[selected_stage]

        return StageAssessment(
            stage=selected_stage,
            confidence=min(1.0, best_stage[1]["score"] * 0.3 + 0.3),
            indicators=best_stage[1]["indicators"],
            recommended_approach=approach["goal"],
            suitable_techniques=approach["techniques"]
        )

    def get_stage_prompt(self, assessment: StageAssessment) -> str:
        """단계별 프롬프트 지침 생성"""
        stage = assessment.stage
        approach = self.STAGE_APPROACHES[stage]

        prompt_parts = [
            f"[변화 단계: {stage.value.upper()}]",
            f"설명: {self.STAGE_INDICATORS[stage]['description']}",
            f"신뢰도: {assessment.confidence:.1%}",
            "",
            f"🎯 목표: {approach['goal']}",
            "",
            "✅ 권장 접근법:",
        ]

        for a in approach["approach"]:
            prompt_parts.append(f"  - {a}")

        prompt_parts.append("")
        prompt_parts.append("❌ 피해야 할 것:")

        for avoid in approach["avoid"]:
            prompt_parts.append(f"  - {avoid}")

        prompt_parts.append("")
        prompt_parts.append("💡 샘플 응답:")

        for sample in approach["sample_responses"][:2]:
            prompt_parts.append(f"  \"{sample}\"")

        return "\n".join(prompt_parts)

    def get_techniques_for_stage(self, stage: StageOfChange) -> List[str]:
        """단계에 적합한 기법 리스트"""
        return self.STAGE_APPROACHES[stage]["techniques"]


# =============================================================================
# 통합 상담 강화 시스템
# =============================================================================

class AdvancedCounselingSystem:
    """
    고급 상담 시스템 통합

    세 가지 핵심 요소 통합:
    1. 치료적 동맹 관리
    2. 동기강화 면담 (MI)
    3. 변화 단계 모델
    """

    def __init__(self):
        self.alliance_manager = TherapeuticAllianceManager()
        self.mi_manager = MotivationalInterviewing()
        self.stage_manager = StagesOfChangeManager()

    def analyze_and_enhance(
        self,
        current_message: str,
        conversation_history: List[Dict]
    ) -> Dict[str, Any]:
        """
        종합 분석 및 응답 강화 지침 생성

        Args:
            current_message: 현재 사용자 메시지
            conversation_history: 대화 기록

        Returns:
            통합 분석 결과 및 지침
        """
        # 1. 치료적 동맹 평가
        alliance = self.alliance_manager.assess_alliance(
            conversation_history, current_message
        )

        # 2. MI 분석
        change_talk = self.mi_manager.detect_change_talk(current_message)
        sustain_talk = self.mi_manager.detect_sustain_talk(current_message)
        mi_strategy = self.mi_manager.get_oars_response(
            current_message, change_talk, sustain_talk
        )

        # 3. 변화 단계 평가
        stage_assessment = self.stage_manager.assess_stage(
            current_message, conversation_history
        )

        # 통합 결과
        result = {
            "alliance": {
                "overall_score": alliance.overall_score,
                "bond": alliance.bond_score,
                "goal": alliance.goal_score,
                "task": alliance.task_score,
                "rupture_detected": alliance.rupture_detected,
                "rupture_type": alliance.rupture_type,
            },
            "mi": {
                "change_talk_count": len(change_talk),
                "change_talk_types": [ct.type for ct in change_talk],
                "has_sustain_talk": sustain_talk,
                "recommended_technique": mi_strategy["primary_technique"],
            },
            "stage": {
                "current_stage": stage_assessment.stage.value,
                "confidence": stage_assessment.confidence,
                "recommended_approach": stage_assessment.recommended_approach,
            },
            "integrated_prompt": self._generate_integrated_prompt(
                alliance, change_talk, sustain_talk, stage_assessment
            )
        }

        return result

    def _generate_integrated_prompt(
        self,
        alliance: TherapeuticAlliance,
        change_talk: List[ChangeStatement],
        sustain_talk: bool,
        stage: StageAssessment
    ) -> str:
        """통합 프롬프트 생성"""
        sections = []

        # 최우선: 동맹 파열 시
        if alliance.rupture_detected:
            sections.append("=" * 50)
            sections.append("⚠️ [우선순위 1: 동맹 회복]")
            sections.append(self.alliance_manager.get_alliance_enhancement_prompt(alliance))
            sections.append("=" * 50)

        # 변화 단계 맥락
        sections.append(self.stage_manager.get_stage_prompt(stage))
        sections.append("")

        # MI 지침
        sections.append(self.mi_manager.get_mi_prompt_addition(change_talk, sustain_talk))

        # 동맹 강화 (파열이 아닌 경우도)
        if not alliance.rupture_detected and alliance.overall_score < 0.7:
            sections.append("")
            sections.append(self.alliance_manager.get_alliance_enhancement_prompt(alliance))

        return "\n".join(sections)

    def get_priority_guidance(
        self,
        alliance: TherapeuticAlliance,
        stage: StageAssessment
    ) -> str:
        """우선순위 지침"""

        # 1순위: 동맹 파열
        if alliance.rupture_detected:
            return "동맹 회복에 집중하세요. 내용보다 관계가 우선입니다."

        # 2순위: 동맹 약함
        if alliance.overall_score < 0.5:
            return "관계 형성에 집중하세요. 공감과 수용이 우선입니다."

        # 3순위: 숙고 전 단계
        if stage.stage == StageOfChange.PRECONTEMPLATION:
            return "변화를 강요하지 마세요. 경청과 공감에 집중하세요."

        # 4순위: 재발
        if stage.stage == StageOfChange.RELAPSE:
            return "비난 없이 수용하세요. 실패가 아닌 학습으로 재프레이밍하세요."

        return "단계에 맞는 접근법을 사용하세요."


# =============================================================================
# 유틸리티 함수
# =============================================================================

def create_advanced_counseling_system() -> AdvancedCounselingSystem:
    """고급 상담 시스템 생성"""
    return AdvancedCounselingSystem()


# 싱글톤
_advanced_system: Optional[AdvancedCounselingSystem] = None

def get_advanced_counseling_system() -> AdvancedCounselingSystem:
    """싱글톤 인스턴스 가져오기"""
    global _advanced_system
    if _advanced_system is None:
        _advanced_system = AdvancedCounselingSystem()
    return _advanced_system


# =============================================================================
# 테스트
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("고급 상담 기법 모듈 테스트")
    print("=" * 60)

    system = create_advanced_counseling_system()

    # 테스트 시나리오
    test_cases = [
        {
            "message": "변화하고 싶은데... 잘 안 돼요. AI가 뭘 알겠어요.",
            "history": [{"role": "user", "content": "힘들어요"}]
        },
        {
            "message": "이번에는 정말 담배 끊어볼 거예요. 준비하고 있어요.",
            "history": [{"role": "user", "content": "건강이 걱정돼요"}]
        },
        {
            "message": "바꿔야 하는 건 알아요. 근데 지금은 아닌 것 같아요.",
            "history": [{"role": "user", "content": "고민이 있어요"}]
        },
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"\n[테스트 {i}]")
        print(f"메시지: {case['message']}")
        print("-" * 40)

        result = system.analyze_and_enhance(case["message"], case["history"])

        print(f"동맹 점수: {result['alliance']['overall_score']:.2f}")
        print(f"파열 감지: {result['alliance']['rupture_detected']}")
        print(f"변화 단계: {result['stage']['current_stage']}")
        print(f"변화 대화: {result['mi']['change_talk_types']}")
        print(f"유지 대화: {result['mi']['has_sustain_talk']}")
        print("-" * 40)
        print("통합 프롬프트 (일부):")
        print(result["integrated_prompt"][:500] + "...")
