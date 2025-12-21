"""
가족/부부 치료 모듈 (Family & Couple Therapy Module)
Gottman 방법론과 정서중심치료(EFT) 기반

기능:
- Gottman 4가지 대화 패턴 분석 (묵시록의 4기수)
- 관계 평가 도구 (Relationship Assessment)
- 의사소통 기술 훈련
- 갈등 해결 전략
- 정서적 유대 강화 훈련
- 가족 역할/경계 분석
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import re

logger = logging.getLogger(__name__)


# =============================================================================
# Enums & Data Classes
# =============================================================================

class GottmanHorseman(Enum):
    """Gottman의 묵시록 4기수 (관계 파괴 패턴)"""
    CRITICISM = "criticism"           # 비난
    CONTEMPT = "contempt"             # 경멸
    DEFENSIVENESS = "defensiveness"   # 방어
    STONEWALLING = "stonewalling"     # 담쌓기/회피


class AttachmentStyle(Enum):
    """애착 유형"""
    SECURE = "secure"               # 안정형
    ANXIOUS = "anxious"             # 불안형
    AVOIDANT = "avoidant"           # 회피형
    DISORGANIZED = "disorganized"   # 혼란형


class ConflictStyle(Enum):
    """갈등 스타일"""
    VOLATILE = "volatile"           # 격정적 (감정적, 표현적)
    VALIDATING = "validating"       # 인정형 (상호 존중)
    AVOIDANT = "avoidant"           # 회피형 (최소화)
    HOSTILE = "hostile"             # 적대적 (파괴적)


class FamilyRole(Enum):
    """가족 내 역할"""
    HERO = "hero"                   # 영웅 (완벽주의, 성취)
    SCAPEGOAT = "scapegoat"         # 희생양 (문제아)
    LOST_CHILD = "lost_child"       # 잃어버린 아이 (투명인간)
    MASCOT = "mascot"               # 마스코트 (분위기 메이커)
    CARETAKER = "caretaker"         # 돌봄 제공자
    ENABLER = "enabler"             # 조력자/방조자


@dataclass
class HorsemanAnalysis:
    """4기수 분석 결과"""
    horseman: GottmanHorseman
    detected: bool
    examples: List[str]
    severity: int  # 1-10
    antidote: str
    practice_suggestion: str


@dataclass
class RelationshipAssessment:
    """관계 평가 결과"""
    assessment_id: str
    relationship_type: str  # couple, parent_child, siblings
    satisfaction_score: int  # 1-100
    horseman_scores: Dict[str, int]
    positive_sentiment_override: bool  # 긍정적 감정 우세 여부
    turning_toward_ratio: float  # 반응 비율 (5:1 이상 권장)
    friendship_score: int  # 1-10
    conflict_style: ConflictStyle
    attachment_styles: Dict[str, AttachmentStyle]
    strengths: List[str]
    growth_areas: List[str]
    recommendations: List[str]
    timestamp: datetime


@dataclass
class FamilySystemAnalysis:
    """가족 체계 분석"""
    family_id: str
    members: List[Dict]
    roles: Dict[str, FamilyRole]
    boundaries: str  # enmeshed, clear, rigid, disengaged
    communication_pattern: str
    power_structure: str
    triangles: List[Dict]  # 삼각관계
    intergenerational_patterns: List[str]
    strengths: List[str]
    concerns: List[str]


# =============================================================================
# Gottman Four Horsemen Detector
# =============================================================================

class GottmanHorsemanDetector:
    """Gottman 4기수 감지기"""

    def __init__(self):
        self.patterns = self._init_patterns()
        self.antidotes = self._init_antidotes()

    def _init_patterns(self) -> Dict[GottmanHorseman, Dict]:
        """4기수 패턴 정의"""
        return {
            GottmanHorseman.CRITICISM: {
                "name": "비난 (Criticism)",
                "description": "상대방의 성격이나 인격을 공격하는 것",
                "vs_complaint": "불만(특정 행동)과 구분: 비난은 '당신은 항상...'으로 인격을 공격",
                "keywords": [
                    "넌 항상", "넌 절대", "왜 맨날", "도대체 왜",
                    "넌 그런 사람", "넌 진짜", "문제가 있어",
                    "항상 그 모양", "절대 안 변해", "뭐가 문제야"
                ],
                "patterns": [
                    r"넌\s*(항상|맨날|언제나|늘)",
                    r"왜\s*맨날",
                    r"넌\s*그런\s*사람",
                    r"도대체\s*왜",
                    r"절대\s*(안|못)"
                ],
                "examples": [
                    "넌 항상 나한테 관심이 없어",
                    "넌 맨날 늦잖아, 나를 중요하게 생각 안 하지?",
                    "넌 그런 사람이야, 절대 안 변해"
                ]
            },
            GottmanHorseman.CONTEMPT: {
                "name": "경멸 (Contempt)",
                "description": "상대방을 낮추고 무시하는 것. 관계 파괴의 가장 강력한 예측 인자",
                "vs_criticism": "비난보다 더 심각. 우월한 위치에서 조롱/멸시",
                "keywords": [
                    "한심", "멍청", "바보", "찐따", "쓸모없",
                    "그것도 못해", "어휴", "역겹", "우습",
                    "비웃", "조롱", "무시", "그래서 뭐"
                ],
                "patterns": [
                    r"한심",
                    r"멍청|바보",
                    r"그것도\s*못",
                    r"어휴",
                    r"우습"
                ],
                "examples": [
                    "그것도 못하면서 뭘 한다고?",
                    "어휴, 한심해서... (눈 굴리기)",
                    "네가 뭘 알아? 웃기고 있네"
                ],
                "nonverbal": ["눈 굴리기", "비웃음", "조롱하는 어조", "무시하는 표정"]
            },
            GottmanHorseman.DEFENSIVENESS: {
                "name": "방어 (Defensiveness)",
                "description": "책임을 회피하고 자신을 정당화하는 것",
                "effect": "문제 해결 방해, 상대방 의견 무효화",
                "keywords": [
                    "내 잘못 아니", "근데 너도", "나는 안 그랬어",
                    "왜 나한테", "억울해", "오해야", "그런 뜻 아니",
                    "변명", "핑계", "네가 먼저"
                ],
                "patterns": [
                    r"내\s*잘못\s*(아니|이\s*아니)",
                    r"근데\s*너도",
                    r"왜\s*나한테",
                    r"네가\s*먼저"
                ],
                "examples": [
                    "내 잘못 아니야, 네가 먼저 그랬잖아",
                    "억울해, 나는 그런 뜻이 아니었어",
                    "왜 나한테만 그래? 너도 문제 있잖아"
                ],
                "forms": ["반격", "정당화", "피해자 행세", "책임 전가"]
            },
            GottmanHorseman.STONEWALLING: {
                "name": "담쌓기/회피 (Stonewalling)",
                "description": "대화를 차단하고 철수하는 것",
                "effect": "연결 단절, 문제 미해결, 상대방 좌절감 증가",
                "keywords": [
                    "말 안 해", "대화 안 해", "됐어", "나가",
                    "그만해", "알았어 알았어", "몰라", "상관없어",
                    "말해봤자", "포기", "무시"
                ],
                "patterns": [
                    r"말\s*(안|하기\s*싫)",
                    r"됐어",
                    r"그만\s*해",
                    r"몰라"
                ],
                "examples": [
                    "....(침묵, 반응 없음)",
                    "됐어, 말해봤자 뭐해",
                    "그만해, 더 이상 대화하기 싫어"
                ],
                "behaviors": ["침묵", "한숨", "딴 곳 보기", "자리 피하기", "핸드폰 보기"]
            }
        }

    def _init_antidotes(self) -> Dict[GottmanHorseman, Dict]:
        """4기수의 해독제"""
        return {
            GottmanHorseman.CRITICISM: {
                "name": "부드러운 시작 (Gentle Start-up)",
                "description": "인격 비난 대신 특정 행동에 대한 감정과 필요를 표현",
                "formula": "상황 + 감정 + 필요/요청",
                "examples": [
                    "'넌 맨날 늦어' → '오늘 약속에 30분 늦었을 때 (상황), 나는 중요하지 않다고 느껴졌어 (감정). 시간 약속을 지켜줬으면 해 (요청)'",
                    "'넌 관심이 없어' → '요즘 대화가 줄었는데 (상황), 외로워 (감정). 하루에 10분이라도 이야기 나눴으면 해 (요청)'"
                ],
                "practice": """
1. 'I' 문장으로 시작하기 (나는 ~할 때 ~하게 느껴)
2. 특정 상황 묘사하기 (일반화 ×)
3. 자신의 감정 표현하기
4. 구체적인 요청하기 (긍정적으로)
                """
            },
            GottmanHorseman.CONTEMPT: {
                "name": "존중과 감사 문화 (Culture of Appreciation)",
                "description": "일상에서 존중과 감사를 표현하는 습관",
                "formula": "감사 + 존중 + 인정",
                "examples": [
                    "매일 감사한 것 3가지 말하기",
                    "'고마워' 자주 말하기",
                    "상대방의 노력 인정하기"
                ],
                "practice": """
1. 매일 감사 표현하기 (구체적으로)
2. 상대방의 좋은 점 찾아 말하기
3. 상대방 관점에서 생각해보기
4. 경멸적 생각이 들 때 잠시 멈추기
5. 상대방을 팀 동료로 보기
                """
            },
            GottmanHorseman.DEFENSIVENESS: {
                "name": "책임 인정 (Taking Responsibility)",
                "description": "작은 부분이라도 자신의 역할 인정하기",
                "formula": "인정 + 이해 + 개선 의지",
                "examples": [
                    "'네 말이 맞아, 내가 약속을 잊었어. 미안해.'",
                    "'그 부분은 내가 더 신경 썼어야 했어.'",
                    "'네가 그렇게 느꼈을 수 있겠다.'"
                ],
                "practice": """
1. 방어하기 전에 숨 쉬기
2. 상대방 말의 2%라도 맞는 부분 찾기
3. "네 말이 맞아, ~" 로 시작하기
4. 상대방 감정 먼저 인정하기
5. 변명 대신 사과하기
                """
            },
            GottmanHorseman.STONEWALLING: {
                "name": "자기 진정 (Self-Soothing)",
                "description": "휴식을 취한 후 대화로 돌아오기",
                "formula": "타임아웃 → 진정 → 복귀",
                "examples": [
                    "'지금 감정이 격해져서 20분 후에 다시 이야기하자'",
                    "'잠깐 밖에 나갔다 올게, 진정하고 올게'",
                    "'지금은 제대로 들을 수가 없어. 30분 후에 다시 하자'"
                ],
                "practice": """
1. 신체적 생리 반응 인식하기 (심박수 증가 등)
2. 휴식 요청하기 (최소 20분)
3. 휴식 중 진정 활동하기 (산책, 호흡 등)
4. 대화를 피하는 것이 아님을 명시하기
5. 약속한 시간에 반드시 돌아오기
                """
            }
        }

    def detect_horsemen(self, text: str) -> List[HorsemanAnalysis]:
        """텍스트에서 4기수 감지"""
        results = []
        text_lower = text.lower()

        for horseman, pattern_info in self.patterns.items():
            detected = False
            examples_found = []
            severity = 0

            # 키워드 매칭
            for keyword in pattern_info.get("keywords", []):
                if keyword in text_lower:
                    detected = True
                    examples_found.append(keyword)
                    severity += 2

            # 정규식 패턴 매칭
            for pattern in pattern_info.get("patterns", []):
                if re.search(pattern, text, re.IGNORECASE):
                    detected = True
                    severity += 3

            if detected:
                antidote_info = self.antidotes.get(horseman, {})
                results.append(HorsemanAnalysis(
                    horseman=horseman,
                    detected=True,
                    examples=examples_found[:3],
                    severity=min(severity, 10),
                    antidote=antidote_info.get("name", ""),
                    practice_suggestion=antidote_info.get("practice", "")
                ))

        return results

    def get_antidote_guidance(self, horseman: GottmanHorseman) -> Dict:
        """특정 기수의 해독제 안내"""
        return self.antidotes.get(horseman, {})

    def get_all_patterns(self) -> Dict:
        """모든 패턴 정보 반환"""
        return self.patterns


# =============================================================================
# Relationship Assessment Tool
# =============================================================================

class RelationshipAssessmentTool:
    """관계 평가 도구"""

    def __init__(self):
        self.questionnaire = self._init_questionnaire()

    def _init_questionnaire(self) -> Dict[str, List[Dict]]:
        """관계 평가 질문지"""
        return {
            "satisfaction": [
                {"id": 1, "text": "파트너와의 관계에 전반적으로 만족합니다.", "category": "satisfaction"},
                {"id": 2, "text": "파트너는 나의 최고의 친구입니다.", "category": "friendship"},
                {"id": 3, "text": "우리 관계의 미래가 밝다고 생각합니다.", "category": "future"},
            ],
            "communication": [
                {"id": 4, "text": "파트너에게 속마음을 편하게 이야기할 수 있습니다.", "category": "openness"},
                {"id": 5, "text": "의견이 다를 때도 서로 존중합니다.", "category": "respect"},
                {"id": 6, "text": "파트너가 나의 말을 경청한다고 느낍니다.", "category": "listening"},
            ],
            "conflict": [
                {"id": 7, "text": "갈등을 건설적으로 해결할 수 있습니다.", "category": "resolution"},
                {"id": 8, "text": "다툼 후에도 화해할 수 있습니다.", "category": "repair"},
                {"id": 9, "text": "갈등 중에도 상대방을 비난하지 않으려 합니다.", "category": "no_criticism"},
            ],
            "intimacy": [
                {"id": 10, "text": "파트너와 정서적으로 가깝다고 느낍니다.", "category": "emotional"},
                {"id": 11, "text": "파트너에게 지지받고 있다고 느낍니다.", "category": "support"},
                {"id": 12, "text": "서로의 꿈과 목표를 공유합니다.", "category": "shared_meaning"},
            ],
            "appreciation": [
                {"id": 13, "text": "파트너에게 감사를 자주 표현합니다.", "category": "expressing"},
                {"id": 14, "text": "파트너로부터 인정받는다고 느낍니다.", "category": "feeling"},
                {"id": 15, "text": "서로의 노력을 알아봅니다.", "category": "recognition"},
            ]
        }

    def get_questions(self, section: Optional[str] = None) -> List[Dict]:
        """질문 반환"""
        if section:
            return self.questionnaire.get(section, [])
        all_questions = []
        for questions in self.questionnaire.values():
            all_questions.extend(questions)
        return all_questions

    def calculate_scores(self, responses: Dict[int, int]) -> Dict:
        """점수 계산 (1-5점 척도 응답)"""
        category_scores = {}
        category_counts = {}

        all_questions = self.get_questions()
        for q in all_questions:
            qid = q["id"]
            category = q["category"]
            if qid in responses:
                if category not in category_scores:
                    category_scores[category] = 0
                    category_counts[category] = 0
                category_scores[category] += responses[qid]
                category_counts[category] += 1

        # 평균 계산
        averages = {}
        for cat, total in category_scores.items():
            count = category_counts.get(cat, 1)
            averages[cat] = round(total / count, 2)

        # 전체 점수 (100점 만점)
        total_score = sum(responses.values())
        max_possible = len(responses) * 5
        overall_percentage = round((total_score / max_possible) * 100)

        return {
            "overall_score": overall_percentage,
            "category_scores": averages,
            "interpretation": self._interpret_score(overall_percentage),
            "recommendations": self._get_recommendations(averages)
        }

    def _interpret_score(self, score: int) -> str:
        """점수 해석"""
        if score >= 80:
            return "매우 건강한 관계입니다. 강점을 유지하고 발전시켜 나가세요."
        elif score >= 60:
            return "전반적으로 좋은 관계입니다. 일부 개선 영역에 주의를 기울이면 더 좋아질 수 있습니다."
        elif score >= 40:
            return "관계에 어려움이 있습니다. 전문 상담을 고려해보세요."
        else:
            return "관계에 심각한 문제가 있습니다. 전문 부부상담사와 상담을 권합니다."

    def _get_recommendations(self, category_scores: Dict) -> List[str]:
        """점수별 추천"""
        recommendations = []

        for category, score in category_scores.items():
            if score < 3:
                if category == "openness":
                    recommendations.append("매일 10분 '대화 시간'을 정해 속마음을 나눠보세요")
                elif category == "respect":
                    recommendations.append("의견이 다를 때 '~라고 생각하는구나' 반영 연습을 해보세요")
                elif category == "listening":
                    recommendations.append("상대방이 말할 때 조언하기 전 요약해서 확인해보세요")
                elif category == "resolution":
                    recommendations.append("갈등 시 '부드러운 시작' 기법을 연습해보세요")
                elif category == "repair":
                    recommendations.append("다툼 후 화해 의식(사과, 포옹 등)을 만들어보세요")
                elif category == "emotional":
                    recommendations.append("하루에 한 번 진심 어린 신체 접촉을 해보세요")
                elif category == "support":
                    recommendations.append("파트너의 스트레스에 반응하고 공감해보세요")
                elif category in ["expressing", "recognition"]:
                    recommendations.append("매일 구체적인 감사 표현을 해보세요")

        return recommendations[:5]


# =============================================================================
# Communication Skills Training
# =============================================================================

class CommunicationSkillsTraining:
    """의사소통 기술 훈련"""

    def __init__(self):
        self.skills = self._init_skills()

    def _init_skills(self) -> Dict[str, Dict]:
        """의사소통 기술 목록"""
        return {
            "i_message": {
                "name": "I-메시지 (나-전달법)",
                "description": "상대방을 비난하지 않고 자신의 감정과 필요를 표현하는 방법",
                "formula": "[상황] + [감정] + [영향] + [요청]",
                "examples": [
                    {
                        "bad": "넌 맨날 늦어서 짜증나!",
                        "good": "약속 시간에 30분 늦으면 (상황), 나는 중요하지 않다는 느낌이 들어 (감정). 다음부터 시간을 지켜주면 좋겠어 (요청)."
                    },
                    {
                        "bad": "넌 나한테 관심도 없지!",
                        "good": "요즘 대화가 줄어든 것 같아서 (상황), 외롭고 서운해 (감정). 저녁에 10분이라도 이야기 나눴으면 해 (요청)."
                    }
                ],
                "practice_steps": [
                    "1. 상황을 객관적으로 묘사하기 (판단 없이)",
                    "2. 내 감정 명명하기",
                    "3. 그 상황이 나에게 미치는 영향 설명하기",
                    "4. 구체적인 요청하기 (긍정적으로)"
                ]
            },
            "active_listening": {
                "name": "적극적 경청",
                "description": "상대방의 말을 온전히 듣고 이해하려는 자세",
                "components": [
                    "눈 맞춤 유지하기",
                    "끄덕임, '음', '그렇구나' 등 반응하기",
                    "판단이나 조언 미루기",
                    "요약해서 확인하기",
                    "감정 반영하기"
                ],
                "examples": [
                    {
                        "partner_says": "오늘 정말 힘든 하루였어...",
                        "bad_response": "뭐, 나도 힘들었어. 근데 뭐 어쩌라고?",
                        "good_response": "오늘 힘들었구나... 무슨 일이 있었어?"
                    }
                ],
                "practice_steps": [
                    "1. 말을 끊지 않고 끝까지 듣기",
                    "2. 들은 내용 요약하기: '~라는 거지?'",
                    "3. 감정 반영하기: '~해서 ~했겠다'",
                    "4. 더 알고 싶다는 관심 표현하기"
                ]
            },
            "soft_startup": {
                "name": "부드러운 시작 (Soft Start-up)",
                "description": "대화를 비난이 아닌 부드러운 방식으로 시작하기",
                "gottman_principle": "대화의 처음 3분이 결과를 예측한다",
                "guidelines": [
                    "'나'로 시작하기 (너 대신)",
                    "불만이 아닌 바라는 것 말하기",
                    "과거가 아닌 현재 상황에 집중하기",
                    "감사와 인정으로 시작하기",
                    "부정적 특성이 아닌 특정 행동 말하기"
                ],
                "examples": [
                    {
                        "hard": "넌 집안일을 절대 안 해!",
                        "soft": "요즘 내가 집안일을 많이 하고 있는 것 같아. 분담을 다시 이야기해볼 수 있을까?"
                    }
                ]
            },
            "validation": {
                "name": "감정 인정 (Validation)",
                "description": "상대방의 감정을 인정하고 타당화하기",
                "levels": [
                    "1단계: 주의 기울이기 - 경청하고 있음을 보여주기",
                    "2단계: 반영하기 - 들은 것을 돌려주기",
                    "3단계: 마음 읽기 - 말하지 않은 감정 언급하기",
                    "4단계: 맥락 이해하기 - 그렇게 느끼는 이유 이해 표현",
                    "5단계: 정상화하기 - 누구나 그렇게 느낄 수 있음",
                    "6단계: 진심 인정 - 그 감정이 타당함을 인정"
                ],
                "examples": [
                    "그렇게 느끼는 거 당연해",
                    "그 상황에서 화가 날 수밖에 없지",
                    "네 감정이 이해가 돼"
                ],
                "what_not_to_say": [
                    "그렇게까지 화낼 일이야?",
                    "좀 오버하는 것 같은데",
                    "그냥 넘어가면 안 돼?"
                ]
            },
            "repair_attempt": {
                "name": "관계 회복 시도 (Repair Attempt)",
                "description": "갈등 중 긴장을 낮추고 연결을 회복하려는 시도",
                "examples": [
                    "잠깐 멈추자. 우리 방향이 잘못된 것 같아.",
                    "미안해, 내가 좀 심하게 말했어.",
                    "우리 지금 같은 편인 거 알지?",
                    "손잡자 (또는 포옹)",
                    "다시 해보자. 이번엔 좀 더 차분하게.",
                    "지금 얼굴 보니까 웃음이 나네 (유머)"
                ],
                "success_factors": [
                    "상대방이 회복 시도를 알아차리고 수용해야 함",
                    "건강한 관계일수록 수용률이 높음",
                    "긴장이 너무 높으면 먼저 진정 필요"
                ]
            }
        }

    def get_skill(self, skill_name: str) -> Optional[Dict]:
        """특정 기술 반환"""
        return self.skills.get(skill_name)

    def get_all_skills(self) -> Dict[str, Dict]:
        """모든 기술 반환"""
        return self.skills

    def practice_i_message(self, situation: str, emotion: str, request: str) -> str:
        """I-메시지 연습"""
        return f"{situation}할 때, 나는 {emotion}. {request}."

    def get_practice_prompts(self, skill_name: str) -> List[str]:
        """연습 프롬프트 반환"""
        prompts = {
            "i_message": [
                "최근 파트너에게 서운했던 상황을 I-메시지로 표현해보세요.",
                "파트너에게 바라는 것을 I-메시지로 표현해보세요."
            ],
            "active_listening": [
                "파트너의 말을 3분간 끊지 않고 들어보세요.",
                "파트너가 한 말을 요약해서 확인해보세요."
            ],
            "soft_startup": [
                "최근 불만을 '부드러운 시작'으로 다시 표현해보세요.",
                "대화 시작 전 감사한 점 한 가지를 먼저 말해보세요."
            ]
        }
        return prompts.get(skill_name, [])


# =============================================================================
# Family Systems Analysis
# =============================================================================

class FamilySystemsAnalyzer:
    """가족 체계 분석 도구"""

    def __init__(self):
        self.roles = self._init_roles()
        self.boundaries = self._init_boundaries()

    def _init_roles(self) -> Dict[FamilyRole, Dict]:
        """가족 역할 정의"""
        return {
            FamilyRole.HERO: {
                "name": "영웅 (Hero)",
                "description": "가족의 자랑이 되려고 완벽을 추구하는 역할",
                "characteristics": [
                    "성취 지향적",
                    "책임감 강함",
                    "완벽주의",
                    "통제하려 함",
                    "내면의 불안정"
                ],
                "impact": "가족 이미지를 좋게 만들지만, 자기 욕구 억압",
                "healing": ["자기 감정 인식하기", "완벽하지 않아도 된다는 허용"]
            },
            FamilyRole.SCAPEGOAT: {
                "name": "희생양 (Scapegoat)",
                "description": "가족 문제의 초점이 되어 주의를 분산시키는 역할",
                "characteristics": [
                    "반항적",
                    "문제 행동",
                    "분노 표출",
                    "외톨이",
                    "비난 받음"
                ],
                "impact": "가족의 진짜 문제에서 주의 분산",
                "healing": ["분노 아래 상처 인식", "건강한 정체성 형성"]
            },
            FamilyRole.LOST_CHILD: {
                "name": "잃어버린 아이 (Lost Child)",
                "description": "눈에 띄지 않게 조용히 지내는 역할",
                "characteristics": [
                    "조용함",
                    "혼자 있음 선호",
                    "존재감 없음",
                    "욕구 억압",
                    "회피적"
                ],
                "impact": "갈등 감소에 기여하지만 욕구 무시됨",
                "healing": ["자기 목소리 내기", "욕구 인식하고 표현하기"]
            },
            FamilyRole.MASCOT: {
                "name": "마스코트 (Mascot)",
                "description": "유머와 귀여움으로 긴장을 해소하는 역할",
                "characteristics": [
                    "유머러스",
                    "귀여움",
                    "관심 추구",
                    "감정 회피",
                    "미성숙해 보임"
                ],
                "impact": "가족 긴장 완화하지만 진지하게 여겨지지 않음",
                "healing": ["진지한 감정 표현하기", "자기 욕구 진지하게 다루기"]
            },
            FamilyRole.CARETAKER: {
                "name": "돌봄 제공자 (Caretaker)",
                "description": "다른 가족원을 돌보는 역할 (종종 아이가)",
                "characteristics": [
                    "과도한 책임감",
                    "타인 욕구 우선",
                    "자기 희생",
                    "공의존적",
                    "인정 욕구"
                ],
                "impact": "가족 기능에 기여하지만 자기 욕구 무시",
                "healing": ["자기 돌봄 배우기", "경계 설정하기"]
            },
            FamilyRole.ENABLER: {
                "name": "방조자 (Enabler)",
                "description": "문제 행동을 가능하게 하는 역할 (종종 배우자)",
                "characteristics": [
                    "문제 최소화",
                    "변명 제공",
                    "덮어줌",
                    "책임 대신 짐",
                    "갈등 회피"
                ],
                "impact": "단기적 평화 유지하지만 문제 지속",
                "healing": ["건강한 경계", "문제 직면하기"]
            }
        }

    def _init_boundaries(self) -> Dict[str, Dict]:
        """경계 유형 정의"""
        return {
            "enmeshed": {
                "name": "밀착형 (Enmeshed)",
                "description": "경계가 너무 흐려져 과도하게 가깝고 개인 공간이 없음",
                "signs": [
                    "개인 프라이버시 없음",
                    "한 사람의 감정이 모두에게 영향",
                    "과도한 간섭",
                    "개별화 어려움",
                    "'우리'가 '나'를 대체"
                ],
                "healthy_change": "개인 경계 설정, 개별성 존중"
            },
            "clear": {
                "name": "명확한 경계 (Clear)",
                "description": "건강한 경계 - 가까우면서도 개별성 존중",
                "signs": [
                    "적절한 프라이버시",
                    "서로 지지하면서 독립적",
                    "감정 공유하되 책임 분리",
                    "다양한 의견 허용",
                    "필요시 도움 요청 가능"
                ],
                "healthy_change": "유지하기"
            },
            "rigid": {
                "name": "경직된 경계 (Rigid)",
                "description": "경계가 너무 엄격하여 정서적 거리가 멂",
                "signs": [
                    "감정 공유 어려움",
                    "도움 요청 어려움",
                    "규칙 엄격",
                    "독립만 강조",
                    "친밀감 부족"
                ],
                "healthy_change": "취약성 표현 연습, 연결 시도"
            },
            "disengaged": {
                "name": "단절형 (Disengaged)",
                "description": "가족원 간 연결이 거의 없음",
                "signs": [
                    "각자 다른 삶",
                    "서로에 대해 모름",
                    "지지 없음",
                    "소통 부재",
                    "정서적 거리"
                ],
                "healthy_change": "정기적 연결 시간 만들기"
            }
        }

    def analyze_role(self, responses: Dict) -> FamilyRole:
        """역할 분석 (간단한 버전)"""
        # 실제 구현에서는 더 정교한 분석 필요
        return FamilyRole.HERO

    def get_role_info(self, role: FamilyRole) -> Dict:
        """역할 정보 반환"""
        return self.roles.get(role, {})

    def get_boundary_info(self, boundary_type: str) -> Dict:
        """경계 유형 정보 반환"""
        return self.boundaries.get(boundary_type, {})


# =============================================================================
# EFT (Emotionally Focused Therapy) 핵심 요소
# =============================================================================

class EFTCore:
    """정서중심치료(EFT) 핵심 요소"""

    def __init__(self):
        self.cycles = self._init_cycles()
        self.stages = self._init_stages()

    def _init_cycles(self) -> Dict[str, Dict]:
        """부정적 상호작용 사이클"""
        return {
            "pursue_withdraw": {
                "name": "추구자-철수자 패턴",
                "description": "한 사람은 연결을 추구하고, 다른 사람은 철수하는 패턴",
                "pursuer": {
                    "behavior": "비난, 요구, 쫓아다님",
                    "underlying_emotion": "두려움, 외로움, '나는 중요하지 않다'",
                    "attachment_need": "연결, 확인, 안심"
                },
                "withdrawer": {
                    "behavior": "침묵, 회피, 거리두기",
                    "underlying_emotion": "수치심, 실패감, '난 충분하지 않다'",
                    "attachment_need": "수용, 인정, 안전"
                },
                "cycle_example": """
1. 철수자가 거리를 두면
2. 추구자는 버림받는다고 느끼고 더 쫓아가고
3. 철수자는 비난받는다고 느끼고 더 철수하고
4. 추구자는 더 불안해지고...
(반복)
                """,
                "breaking_cycle": [
                    "사이클 인식하기 (둘 다 피해자)",
                    "1차 감정 (두려움, 외로움) 표현하기",
                    "2차 감정 (분노, 냉담) 아래 욕구 말하기",
                    "상대방의 두려움 이해하기",
                    "새로운 상호작용 시도하기"
                ]
            },
            "mutual_withdraw": {
                "name": "상호 철수 패턴",
                "description": "둘 다 철수하여 정서적으로 단절된 상태",
                "dynamic": "둘 다 상처받을까봐 거리를 둠",
                "result": "외로움, 공허함, '우리 사이에 뭔가 없어졌다'",
                "breaking_cycle": [
                    "연결 욕구 인정하기",
                    "작은 연결 시도하기",
                    "취약성 표현 연습하기"
                ]
            },
            "mutual_attack": {
                "name": "상호 공격 패턴",
                "description": "둘 다 비난하고 방어하는 격렬한 싸움",
                "dynamic": "상처를 주고받으며 에스컬레이션",
                "result": "깊은 상처, 신뢰 손상",
                "breaking_cycle": [
                    "타임아웃 사용하기",
                    "분노 아래 상처 인식하기",
                    "방어 아래 두려움 인정하기"
                ]
            }
        }

    def _init_stages(self) -> List[Dict]:
        """EFT 3단계"""
        return [
            {
                "stage": 1,
                "name": "사이클 인식과 비에스컬레이션",
                "goals": [
                    "부정적 상호작용 패턴 파악",
                    "사이클을 '공동의 적'으로 보기",
                    "1차 감정 (두려움, 슬픔) 접촉",
                    "갈등 강도 낮추기"
                ],
                "key_interventions": [
                    "반영(Reflection)",
                    "타당화(Validation)",
                    "공감적 추측(Empathic Conjecture)"
                ]
            },
            {
                "stage": 2,
                "name": "상호작용 패턴 변화",
                "goals": [
                    "취약한 감정 표현하기",
                    "애착 욕구 공개하기",
                    "파트너의 욕구에 반응하기",
                    "새로운 상호작용 경험"
                ],
                "key_interventions": [
                    "접근-소프닝(Softening)",
                    "재참여(Re-engagement)",
                    "유대 사건(Bonding Events)"
                ]
            },
            {
                "stage": 3,
                "name": "공고화와 통합",
                "goals": [
                    "새로운 패턴 강화",
                    "문제를 새로운 방식으로 해결",
                    "새로운 이야기 만들기",
                    "안전 기지 강화"
                ],
                "key_interventions": [
                    "변화 요약",
                    "미래 대비",
                    "안전한 연결 경험"
                ]
            }
        ]

    def get_cycle_info(self, cycle_type: str) -> Dict:
        """사이클 정보 반환"""
        return self.cycles.get(cycle_type, {})

    def get_stage_info(self, stage: int) -> Optional[Dict]:
        """단계 정보 반환"""
        for s in self.stages:
            if s["stage"] == stage:
                return s
        return None

    def identify_primary_emotion(self, secondary_emotion: str) -> Dict:
        """2차 감정 아래 1차 감정 탐색"""
        emotion_mapping = {
            "분노": {
                "primary": ["두려움", "상처", "무력감"],
                "question": "분노 아래 어떤 두려움이나 상처가 있나요?"
            },
            "짜증": {
                "primary": ["피로", "좌절", "무시당함"],
                "question": "짜증 뒤에는 어떤 좌절감이 있을까요?"
            },
            "냉담": {
                "primary": ["수치심", "실패감", "거부 두려움"],
                "question": "거리를 두는 것은 어떤 것을 피하기 위해서인가요?"
            },
            "비난": {
                "primary": ["외로움", "연결 욕구", "버림받는 두려움"],
                "question": "비난하게 되는 건 어떤 욕구가 충족되지 않아서인가요?"
            }
        }
        return emotion_mapping.get(secondary_emotion, {
            "primary": ["미확인"],
            "question": "그 감정 아래 더 깊은 감정이 있다면 무엇일까요?"
        })


# =============================================================================
# Family Couple Therapy Module (통합 클래스)
# =============================================================================

class FamilyCoupleTherapyModule:
    """가족/부부 치료 모듈 통합 클래스"""

    def __init__(self):
        self.horseman_detector = GottmanHorsemanDetector()
        self.relationship_assessment = RelationshipAssessmentTool()
        self.communication_skills = CommunicationSkillsTraining()
        self.family_systems = FamilySystemsAnalyzer()
        self.eft_core = EFTCore()

        logger.info("가족/부부 치료 모듈 초기화 완료")

    def analyze_conversation(self, text: str) -> Dict:
        """대화 패턴 분석"""
        horsemen = self.horseman_detector.detect_horsemen(text)

        return {
            "horsemen_detected": [
                {
                    "type": h.horseman.value,
                    "severity": h.severity,
                    "examples": h.examples,
                    "antidote": h.antidote
                }
                for h in horsemen
            ],
            "healthy_patterns": len(horsemen) == 0,
            "recommendations": self._get_conversation_recommendations(horsemen)
        }

    def _get_conversation_recommendations(self, horsemen: List[HorsemanAnalysis]) -> List[str]:
        """대화 패턴에 따른 추천"""
        recommendations = []

        for h in horsemen:
            antidote = self.horseman_detector.get_antidote_guidance(h.horseman)
            if antidote:
                recommendations.append(f"{h.horseman.value}에 대한 해독제: {antidote.get('name', '')}")

        if not recommendations:
            recommendations.append("건강한 대화 패턴을 유지하고 있습니다!")

        return recommendations

    def get_skill_training(self, skill_name: str) -> Dict:
        """기술 훈련 자료 반환"""
        return self.communication_skills.get_skill(skill_name) or {}

    def get_relationship_questionnaire(self) -> List[Dict]:
        """관계 평가 질문지 반환"""
        return self.relationship_assessment.get_questions()

    def evaluate_relationship(self, responses: Dict[int, int]) -> Dict:
        """관계 평가"""
        return self.relationship_assessment.calculate_scores(responses)

    def get_eft_cycle_info(self, cycle_type: str = "pursue_withdraw") -> Dict:
        """EFT 사이클 정보 반환"""
        return self.eft_core.get_cycle_info(cycle_type)

    def explore_primary_emotion(self, secondary_emotion: str) -> Dict:
        """1차 감정 탐색"""
        return self.eft_core.identify_primary_emotion(secondary_emotion)

    def get_family_role_info(self, role: FamilyRole) -> Dict:
        """가족 역할 정보"""
        return self.family_systems.get_role_info(role)

    def get_module_summary(self) -> Dict:
        """모듈 요약"""
        return {
            "name": "가족/부부 치료 모듈",
            "version": "1.0.0",
            "components": {
                "gottman_horseman": "4기수 감지 및 해독제",
                "relationship_assessment": "관계 평가 도구 (15문항)",
                "communication_skills": f"의사소통 기술 ({len(self.communication_skills.skills)}개)",
                "family_systems": "가족 체계 분석 (역할, 경계)",
                "eft_core": "정서중심치료 핵심 (사이클, 3단계)"
            },
            "theoretical_basis": [
                "Gottman Method Couples Therapy",
                "Emotionally Focused Therapy (EFT)",
                "Family Systems Theory"
            ]
        }


# =============================================================================
# Factory & Test
# =============================================================================

def get_family_couple_module() -> FamilyCoupleTherapyModule:
    """가족/부부 치료 모듈 인스턴스 생성"""
    return FamilyCoupleTherapyModule()


if __name__ == "__main__":
    # 테스트
    module = get_family_couple_module()

    print("=" * 60)
    print("가족/부부 치료 모듈 테스트")
    print("=" * 60)

    # 모듈 요약
    summary = module.get_module_summary()
    print(f"\n모듈: {summary['name']} v{summary['version']}")
    print("\n구성요소:")
    for key, value in summary['components'].items():
        print(f"  - {key}: {value}")

    # 4기수 감지 테스트
    print("\n\n--- 4기수 감지 테스트 ---")
    test_text = "넌 항상 그 모양이야. 맨날 늦고, 정말 한심해."
    analysis = module.analyze_conversation(test_text)
    print(f"테스트 문장: '{test_text}'")
    print("감지된 패턴:")
    for h in analysis['horsemen_detected']:
        print(f"  - {h['type']}: 심각도 {h['severity']}")
        print(f"    해독제: {h['antidote']}")

    # 의사소통 기술 테스트
    print("\n\n--- 의사소통 기술 테스트 ---")
    skill = module.get_skill_training("i_message")
    print(f"기술: {skill.get('name', '')}")
    print(f"설명: {skill.get('description', '')}")

    # EFT 사이클 테스트
    print("\n\n--- EFT 사이클 테스트 ---")
    cycle = module.get_eft_cycle_info("pursue_withdraw")
    print(f"패턴: {cycle.get('name', '')}")
    print(f"설명: {cycle.get('description', '')}")

    # 1차 감정 탐색 테스트
    print("\n\n--- 1차 감정 탐색 테스트 ---")
    primary = module.explore_primary_emotion("분노")
    print(f"2차 감정: 분노")
    print(f"1차 감정: {primary.get('primary', [])}")
    print(f"탐색 질문: {primary.get('question', '')}")

    print("\n\n테스트 완료!")
