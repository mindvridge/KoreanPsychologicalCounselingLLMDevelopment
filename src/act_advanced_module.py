"""
ACT 심화 모듈 (Acceptance and Commitment Therapy Advanced Module)
수용전념치료 심화 기능 제공

기능:
- ACT 6가지 핵심 과정 (Hexaflex) 대화형 워크시트
- 가치 탐색 도구 (Values Clarification)
- 심리적 유연성 평가 (AAQ-II)
- 마음챙김 훈련 가이드
- 탈융합 기법 라이브러리
- 전념 행동 계획 수립
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger(__name__)


# =============================================================================
# Enums & Data Classes
# =============================================================================

class ACTProcess(Enum):
    """ACT 6가지 핵심 과정 (Hexaflex)"""
    ACCEPTANCE = "acceptance"           # 수용
    DEFUSION = "defusion"               # 인지적 탈융합
    PRESENT_MOMENT = "present_moment"   # 현재 순간 접촉
    SELF_AS_CONTEXT = "self_as_context" # 맥락으로서의 자기
    VALUES = "values"                   # 가치
    COMMITTED_ACTION = "committed_action"  # 전념 행동


class ValuesDomain(Enum):
    """가치 영역"""
    FAMILY = "family"               # 가족
    RELATIONSHIPS = "relationships" # 대인관계
    WORK_CAREER = "work_career"     # 직업/경력
    EDUCATION = "education"         # 교육/성장
    LEISURE = "leisure"             # 여가/취미
    SPIRITUALITY = "spirituality"   # 영성/의미
    HEALTH = "health"               # 건강
    COMMUNITY = "community"         # 지역사회/시민의식
    SELF_CARE = "self_care"         # 자기돌봄
    CREATIVITY = "creativity"       # 창의성/예술


@dataclass
class ValueAssessment:
    """가치 평가 결과"""
    domain: ValuesDomain
    importance: int          # 1-10 중요도
    current_living: int      # 1-10 현재 실천도
    gap: int                 # 중요도 - 실천도
    core_value: str          # 핵심 가치 문장
    barriers: List[str]      # 장벽
    committed_actions: List[str]  # 전념 행동


@dataclass
class ACTSessionProgress:
    """ACT 세션 진행 상태"""
    session_id: str
    user_id: str
    current_process: ACTProcess
    completed_processes: List[ACTProcess]
    values_assessment: List[ValueAssessment]
    defusion_techniques_used: List[str]
    mindfulness_exercises: List[str]
    committed_actions: List[Dict]
    aaq_ii_scores: List[Dict]  # 시간별 AAQ-II 점수
    created_at: datetime
    updated_at: datetime


@dataclass
class AAQIIResult:
    """AAQ-II (수용행동 질문지) 결과"""
    total_score: int          # 7-49
    interpretation: str
    flexibility_level: str    # high, moderate, low
    recommendations: List[str]
    item_scores: Dict[int, int]
    timestamp: datetime


# =============================================================================
# AAQ-II (Acceptance and Action Questionnaire-II)
# =============================================================================

class AAQII:
    """
    수용행동 질문지 II (AAQ-II)
    심리적 유연성/비유연성 측정

    7문항, 7점 척도 (1=전혀 그렇지 않다, 7=항상 그렇다)
    높은 점수 = 높은 심리적 비유연성 (경험 회피)
    """

    def __init__(self):
        self.questions = self._load_questions()

    def _load_questions(self) -> List[Dict]:
        """AAQ-II 문항 (한국어 버전)"""
        return [
            {
                "id": 1,
                "text": "나의 고통스러운 경험과 기억들이 내가 소중히 여기는 삶을 살기 어렵게 만든다.",
                "reverse": False
            },
            {
                "id": 2,
                "text": "나는 나의 감정이 두렵다.",
                "reverse": False
            },
            {
                "id": 3,
                "text": "나는 부정적인 감정이나 생각을 통제할 수 없는 것이 걱정된다.",
                "reverse": False
            },
            {
                "id": 4,
                "text": "나의 고통스러운 기억들이 내가 충만한 삶을 사는 것을 방해한다.",
                "reverse": False
            },
            {
                "id": 5,
                "text": "감정이 나의 삶에서 문제를 일으킨다.",
                "reverse": False
            },
            {
                "id": 6,
                "text": "대부분의 사람들이 나처럼 끔찍한 생각들을 가지고 있다면 그들의 삶이 더 나빠질 것 같다.",
                "reverse": False
            },
            {
                "id": 7,
                "text": "걱정이 내가 성공하는 것을 방해한다.",
                "reverse": False
            }
        ]

    def get_question(self, index: int) -> Optional[Dict]:
        """특정 문항 반환"""
        if 0 <= index < len(self.questions):
            return self.questions[index]
        return None

    def calculate_score(self, responses: Dict[int, int]) -> AAQIIResult:
        """
        점수 계산 및 해석

        Args:
            responses: {문항번호: 응답값(1-7)}

        Returns:
            AAQIIResult: 평가 결과
        """
        if len(responses) != 7:
            raise ValueError("모든 7개 문항에 응답해야 합니다.")

        total = sum(responses.values())

        # 해석
        if total <= 17:
            flexibility_level = "high"
            interpretation = "높은 심리적 유연성"
            recommendations = [
                "현재의 심리적 유연성을 유지하세요",
                "정기적인 마음챙김 연습을 계속하세요",
                "가치 기반 행동을 지속하세요"
            ]
        elif total <= 28:
            flexibility_level = "moderate"
            interpretation = "보통 수준의 심리적 유연성"
            recommendations = [
                "경험 회피 패턴을 인식해보세요",
                "수용 연습을 시작해보세요",
                "탈융합 기법을 배워보세요",
                "가치 명확화 작업이 도움이 될 수 있습니다"
            ]
        else:
            flexibility_level = "low"
            interpretation = "낮은 심리적 유연성 (높은 경험 회피)"
            recommendations = [
                "전문 상담사와 ACT 치료를 고려해보세요",
                "작은 것부터 수용 연습을 시작하세요",
                "마음챙김 명상으로 현재 순간에 머무는 연습을 해보세요",
                "생각과 거리두기 연습(탈융합)이 필요합니다",
                "가치 탐색을 통해 삶의 방향을 찾아보세요"
            ]

        return AAQIIResult(
            total_score=total,
            interpretation=interpretation,
            flexibility_level=flexibility_level,
            recommendations=recommendations,
            item_scores=responses,
            timestamp=datetime.now()
        )

    def get_conversational_question(self, index: int) -> str:
        """대화형 질문 형식으로 반환"""
        q = self.get_question(index)
        if not q:
            return ""

        return f"""다음 문장이 당신에게 얼마나 해당되나요?

"{q['text']}"

1 = 전혀 그렇지 않다
2 = 거의 그렇지 않다
3 = 약간 그렇지 않다
4 = 보통이다
5 = 약간 그렇다
6 = 거의 그렇다
7 = 항상 그렇다

1부터 7 사이의 숫자로 답해주세요."""


# =============================================================================
# Values Clarification (가치 명확화)
# =============================================================================

class ValuesExplorer:
    """가치 탐색 및 명확화 도구"""

    def __init__(self):
        self.domains = self._init_domains()
        self.value_questions = self._init_questions()

    def _init_domains(self) -> Dict[ValuesDomain, Dict]:
        """가치 영역 정의"""
        return {
            ValuesDomain.FAMILY: {
                "name": "가족",
                "description": "부모, 자녀, 형제자매, 확대가족과의 관계",
                "examples": ["사랑", "돌봄", "연결", "전통", "지지"]
            },
            ValuesDomain.RELATIONSHIPS: {
                "name": "대인관계/우정",
                "description": "친구, 동료, 이웃과의 관계",
                "examples": ["신뢰", "진정성", "친밀감", "재미", "충성"]
            },
            ValuesDomain.WORK_CAREER: {
                "name": "직업/경력",
                "description": "일, 직업, 경력 발전",
                "examples": ["성취", "기여", "전문성", "창의성", "안정"]
            },
            ValuesDomain.EDUCATION: {
                "name": "교육/학습/성장",
                "description": "배움, 자기개발, 지적 성장",
                "examples": ["호기심", "지혜", "성장", "숙달", "탐구"]
            },
            ValuesDomain.LEISURE: {
                "name": "여가/취미",
                "description": "재미, 휴식, 놀이, 취미 활동",
                "examples": ["즐거움", "모험", "휴식", "재충전", "열정"]
            },
            ValuesDomain.SPIRITUALITY: {
                "name": "영성/의미",
                "description": "종교, 영성, 삶의 의미와 목적",
                "examples": ["평화", "연결", "초월", "감사", "의미"]
            },
            ValuesDomain.HEALTH: {
                "name": "건강/웰빙",
                "description": "신체적, 정신적 건강 관리",
                "examples": ["활력", "균형", "자기돌봄", "강인함", "회복"]
            },
            ValuesDomain.COMMUNITY: {
                "name": "지역사회/시민의식",
                "description": "사회 참여, 봉사, 시민으로서의 역할",
                "examples": ["봉사", "정의", "기여", "환경", "연대"]
            },
            ValuesDomain.SELF_CARE: {
                "name": "자기돌봄/자기수용",
                "description": "자기 자신에 대한 친절과 수용",
                "examples": ["자비", "수용", "진정성", "용기", "정직"]
            },
            ValuesDomain.CREATIVITY: {
                "name": "창의성/예술",
                "description": "창작, 예술, 자기표현",
                "examples": ["표현", "아름다움", "혁신", "상상", "자유"]
            }
        }

    def _init_questions(self) -> List[Dict]:
        """가치 탐색 질문"""
        return [
            {
                "type": "imagine",
                "question": "만약 당신의 삶에서 모든 장애물이 사라진다면, 어떤 삶을 살고 싶으신가요?",
                "purpose": "이상적인 삶의 비전 탐색"
            },
            {
                "type": "eulogy",
                "question": "80세 생일 파티에서 가장 가까운 사람이 당신에 대해 어떤 말을 해주길 바라나요?",
                "purpose": "핵심 가치 발견"
            },
            {
                "type": "role_model",
                "question": "당신이 존경하는 사람은 누구인가요? 그 사람의 어떤 점을 존경하나요?",
                "purpose": "가치 투사 탐색"
            },
            {
                "type": "peak_experience",
                "question": "인생에서 가장 의미있고 충만했던 순간은 언제였나요? 그때 무엇이 그것을 특별하게 만들었나요?",
                "purpose": "가치 경험 발견"
            },
            {
                "type": "pain_point",
                "question": "가장 화가 나거나 실망스러운 상황은 어떤 것인가요? 어떤 가치가 위협받았을 때 그런 감정이 드나요?",
                "purpose": "역가치 탐색"
            },
            {
                "type": "legacy",
                "question": "세상에 어떤 흔적을 남기고 싶으신가요?",
                "purpose": "삶의 목적 탐색"
            }
        ]

    def get_domain_assessment_questions(self, domain: ValuesDomain) -> List[str]:
        """특정 영역에 대한 평가 질문"""
        domain_info = self.domains.get(domain, {})
        domain_name = domain_info.get("name", domain.value)

        return [
            f"{domain_name} 영역에서 당신에게 정말 중요한 것은 무엇인가요?",
            f"이 영역에서 어떤 사람이 되고 싶으신가요?",
            f"현재 이 영역에서 당신의 가치를 얼마나 실천하고 있나요? (1-10점)",
            f"이 영역에서 가치대로 살지 못하게 하는 장벽은 무엇인가요?",
            f"이 영역에서 가치에 맞는 작은 행동 한 가지를 한다면 무엇일까요?"
        ]

    def calculate_values_gap(self, importance: int, living: int) -> Dict:
        """가치 격차 분석"""
        gap = importance - living

        if gap <= 1:
            status = "aligned"
            message = "가치와 삶이 잘 일치하고 있습니다."
            priority = "low"
        elif gap <= 3:
            status = "moderate_gap"
            message = "약간의 격차가 있습니다. 작은 변화로 개선 가능합니다."
            priority = "medium"
        else:
            status = "significant_gap"
            message = "중요한 격차가 있습니다. 이 영역에 집중하면 삶의 만족도가 크게 향상될 수 있습니다."
            priority = "high"

        return {
            "gap": gap,
            "status": status,
            "message": message,
            "priority": priority
        }

    def generate_values_summary(self, assessments: List[ValueAssessment]) -> str:
        """가치 평가 요약 생성"""
        if not assessments:
            return "아직 가치 평가가 완료되지 않았습니다."

        # 우선순위별 정렬
        high_priority = [a for a in assessments if a.gap >= 4]
        medium_priority = [a for a in assessments if 2 <= a.gap < 4]
        aligned = [a for a in assessments if a.gap < 2]

        summary = "## 가치 탐색 결과\n\n"

        if high_priority:
            summary += "### 🔴 집중이 필요한 영역\n"
            for a in high_priority:
                summary += f"- **{a.domain.value}**: 중요도 {a.importance}/10, 실천도 {a.current_living}/10\n"
                summary += f"  - 핵심 가치: {a.core_value}\n"
                if a.barriers:
                    summary += f"  - 장벽: {', '.join(a.barriers)}\n"
            summary += "\n"

        if medium_priority:
            summary += "### 🟡 개선 가능한 영역\n"
            for a in medium_priority:
                summary += f"- **{a.domain.value}**: 중요도 {a.importance}/10, 실천도 {a.current_living}/10\n"
            summary += "\n"

        if aligned:
            summary += "### 🟢 잘 실천하고 있는 영역\n"
            for a in aligned:
                summary += f"- **{a.domain.value}**: 가치와 삶이 일치\n"
            summary += "\n"

        return summary


# =============================================================================
# Defusion Techniques (탈융합 기법)
# =============================================================================

class DefusionTechniques:
    """인지적 탈융합 기법 라이브러리"""

    def __init__(self):
        self.techniques = self._load_techniques()

    def _load_techniques(self) -> Dict[str, Dict]:
        """탈융합 기법 목록"""
        return {
            "leaves_on_stream": {
                "name": "시냇물 위 나뭇잎",
                "korean_name": "시냇물 위 나뭇잎",
                "description": "생각을 나뭇잎에 올려 시냇물에 흘려보내는 시각화 기법",
                "instructions": """
1. 편안한 자세로 앉아 눈을 감습니다.
2. 부드럽게 흐르는 시냇물을 상상합니다.
3. 나뭇잎들이 물 위를 천천히 흘러가는 것을 봅니다.
4. 떠오르는 생각이나 감정이 있으면, 그것을 나뭇잎 위에 올려놓습니다.
5. 그 나뭇잎이 물을 따라 흘러가는 것을 지켜봅니다.
6. 생각을 붙잡거나 밀어내려 하지 말고, 그냥 흘러가게 합니다.
7. 새로운 생각이 떠오르면 다시 나뭇잎에 올려 흘려보냅니다.
                """,
                "duration_minutes": 5,
                "suitable_for": ["반복되는 부정적 생각", "걱정", "과거 후회"]
            },
            "thanking_mind": {
                "name": "마음에게 감사하기",
                "korean_name": "마음아 고마워",
                "description": "부정적 생각에 감사로 응답하여 거리 두기",
                "instructions": """
부정적인 생각이 떠오르면:

1. 그 생각을 알아차립니다.
2. "마음아, 그 생각 알려줘서 고마워"라고 말합니다.
3. 마음이 당신을 보호하려고 한다는 것을 인정합니다.
4. 생각과 싸우지 않고 그냥 둡니다.

예시:
- "넌 실패자야" → "마음아, 그 걱정 고마워. 하지만 지금은 괜찮아."
- "다 망칠 거야" → "마음아, 보호하려는 마음 고마워."
                """,
                "duration_minutes": 1,
                "suitable_for": ["자기비판", "불안한 예측", "부정적 자기대화"]
            },
            "silly_voice": {
                "name": "재미있는 목소리로 말하기",
                "korean_name": "우스꽝스러운 목소리",
                "description": "부정적 생각을 재미있는 목소리로 말해 거리 두기",
                "instructions": """
1. 반복되는 부정적 생각을 알아차립니다.
2. 그 생각을 소리 내어 말하거나 속으로 생각합니다.
3. 이번에는 만화 캐릭터 목소리로 그 생각을 말해봅니다.
4. 또는 노래 가사처럼 불러봅니다.
5. 생각의 내용은 같지만 힘이 줄어드는 것을 느껴봅니다.

예시 목소리:
- 도날드 덕 목소리
- 느린 슬로우 모션 목소리
- 로봇 목소리
- 오페라 가수처럼
                """,
                "duration_minutes": 2,
                "suitable_for": ["반복되는 자기비판", "강박적 생각"]
            },
            "naming_story": {
                "name": "이야기에 이름 붙이기",
                "korean_name": "그 이야기 또 나왔네",
                "description": "반복되는 생각 패턴에 이름 붙여 인식하기",
                "instructions": """
1. 자주 반복되는 생각 패턴을 파악합니다.
2. 그 패턴에 이름을 붙입니다.
3. 그 생각이 나타나면 "아, 'OO 이야기'가 또 나왔네"라고 말합니다.

예시:
- "난 충분하지 않아" → "부족함 이야기"
- "다들 날 싫어해" → "외톨이 이야기"
- "다 망할 거야" → "파멸 이야기"
- "내 잘못이야" → "죄책감 이야기"

이렇게 하면 생각과 거리를 두고 관찰자 위치에 설 수 있습니다.
                """,
                "duration_minutes": 1,
                "suitable_for": ["반복되는 걱정", "자기비판 패턴", "우울한 생각"]
            },
            "im_having_thought": {
                "name": "'나는 ~라는 생각을 하고 있다'",
                "korean_name": "생각 라벨링",
                "description": "생각에 '나는 ~라는 생각을 하고 있다'를 붙여 거리 두기",
                "instructions": """
1. 부정적 생각을 알아차립니다.
   예: "나는 실패자야"

2. 앞에 "나는 ~라는 생각을 하고 있다"를 붙입니다.
   → "나는 '나는 실패자야'라는 생각을 하고 있다"

3. 한 단계 더 나아가:
   → "나는 '나는 실패자야'라는 생각을 하고 있다는 것을 알아차리고 있다"

이렇게 하면 생각을 사실이 아닌 정신적 사건으로 볼 수 있습니다.
                """,
                "duration_minutes": 1,
                "suitable_for": ["생각과 동일시", "사실처럼 느껴지는 생각"]
            },
            "passengers_bus": {
                "name": "버스의 승객들",
                "korean_name": "버스 승객 비유",
                "description": "생각과 감정을 버스의 승객으로 보는 은유 기법",
                "instructions": """
당신은 버스 운전사이고, 생각과 감정은 승객입니다.

1. 당신이 인생이라는 버스를 운전하고 있다고 상상합니다.
2. 다양한 승객(생각, 감정)이 타고 있습니다.
   - "실패" 승객, "두려움" 승객, "분노" 승객 등
3. 어떤 승객은 시끄럽게 소리칩니다:
   "저쪽으로 가! 이 길로 가면 안 돼!"
4. 당신은 승객의 말을 들을 수 있지만,
   핸들을 잡고 가고 싶은 방향(가치)으로 운전합니다.
5. 승객을 버스에서 내리게 할 필요는 없습니다.
6. 그냥 가치의 방향으로 계속 운전합니다.

핵심: 생각이 시끄러워도 가치 있는 방향으로 행동할 수 있습니다.
                """,
                "duration_minutes": 5,
                "suitable_for": ["행동 회피", "생각에 지배당하는 느낌"]
            },
            "physicalizing": {
                "name": "생각 물리화하기",
                "korean_name": "생각 물체로 만들기",
                "description": "추상적 생각을 물리적 특성으로 상상하기",
                "instructions": """
1. 반복되는 생각을 떠올립니다.
2. 그 생각에 물리적 특성을 부여합니다:
   - 어떤 모양인가요?
   - 무슨 색깔인가요?
   - 크기는 어느 정도인가요?
   - 무게는 얼마나 되나요?
   - 질감은 어떤가요?
   - 온도는?
3. 그 물체를 손에 올려놓았다고 상상합니다.
4. 그것을 옆에 내려놓거나 주머니에 넣을 수 있습니다.
5. 그것이 있어도 가치 있는 행동을 할 수 있음을 느낍니다.
                """,
                "duration_minutes": 3,
                "suitable_for": ["불안", "압도감", "강한 감정"]
            }
        }

    def get_technique(self, name: str) -> Optional[Dict]:
        """특정 기법 반환"""
        return self.techniques.get(name)

    def get_all_techniques(self) -> Dict[str, Dict]:
        """모든 기법 반환"""
        return self.techniques

    def recommend_technique(self, situation: str) -> List[Dict]:
        """상황에 맞는 기법 추천"""
        situation_lower = situation.lower()
        recommended = []

        keywords_map = {
            "반복": ["leaves_on_stream", "naming_story"],
            "자기비판": ["thanking_mind", "silly_voice", "im_having_thought"],
            "걱정": ["leaves_on_stream", "thanking_mind", "naming_story"],
            "불안": ["physicalizing", "passengers_bus"],
            "우울": ["naming_story", "thanking_mind"],
            "생각에 빠": ["im_having_thought", "physicalizing"],
            "회피": ["passengers_bus"],
            "두려": ["passengers_bus", "physicalizing"]
        }

        for keyword, techniques in keywords_map.items():
            if keyword in situation_lower:
                for tech_name in techniques:
                    tech = self.techniques.get(tech_name)
                    if tech and tech not in recommended:
                        recommended.append(tech)

        # 기본 추천
        if not recommended:
            recommended = [
                self.techniques["im_having_thought"],
                self.techniques["thanking_mind"]
            ]

        return recommended[:3]  # 최대 3개


# =============================================================================
# Mindfulness Exercises (마음챙김 훈련)
# =============================================================================

class MindfulnessExercises:
    """마음챙김 훈련 가이드"""

    def __init__(self):
        self.exercises = self._load_exercises()

    def _load_exercises(self) -> Dict[str, Dict]:
        """마음챙김 훈련 목록"""
        return {
            "breath_anchor": {
                "name": "호흡 닻",
                "description": "호흡을 닻으로 현재 순간에 머무르기",
                "duration_minutes": 5,
                "instructions": """
1. 편안한 자세로 앉습니다.
2. 눈을 부드럽게 감거나 한 점을 응시합니다.
3. 호흡에 주의를 기울입니다.
4. 숨이 들어오고 나가는 것을 느낍니다.
5. 마음이 방황하면 부드럽게 호흡으로 돌아옵니다.
6. 방황했다고 자책하지 않습니다.
7. 매번 돌아오는 것이 훈련입니다.

"호흡은 현재 순간으로 돌아오는 닻입니다."
                """,
                "suitable_for": ["초보자", "일상", "스트레스"]
            },
            "five_senses": {
                "name": "5-4-3-2-1 감각 훈련",
                "description": "다섯 감각을 통해 현재에 접촉하기",
                "duration_minutes": 3,
                "instructions": """
지금 이 순간에 다음을 찾아보세요:

5가지 - 볼 수 있는 것
4가지 - 만질 수 있는 것 (또는 느낄 수 있는 촉감)
3가지 - 들을 수 있는 것
2가지 - 냄새 맡을 수 있는 것
1가지 - 맛볼 수 있는 것

천천히 각 감각에 주의를 기울이며 현재 순간에 머무릅니다.
                """,
                "suitable_for": ["불안", "해리", "그라운딩"]
            },
            "body_scan": {
                "name": "바디 스캔",
                "description": "몸 전체를 천천히 스캔하며 알아차리기",
                "duration_minutes": 10,
                "instructions": """
1. 누운 자세 또는 앉은 자세로 편안히 있습니다.
2. 발가락부터 시작합니다.
3. 각 부위의 감각을 알아차립니다:
   - 발가락 → 발 → 발목 → 종아리
   - 무릎 → 허벅지 → 골반
   - 복부 → 가슴 → 등
   - 손가락 → 손 → 팔
   - 어깨 → 목 → 얼굴 → 머리
4. 긴장이 있으면 알아차리고, 그냥 둡니다.
5. 바꾸려 하지 말고 있는 그대로 관찰합니다.
                """,
                "suitable_for": ["긴장", "스트레스", "수면 전"]
            },
            "mindful_walking": {
                "name": "마음챙김 걷기",
                "description": "걷는 동작에 온전히 주의를 기울이기",
                "duration_minutes": 10,
                "instructions": """
1. 천천히 걷기 시작합니다.
2. 발이 땅에 닿는 감각에 주의를 기울입니다.
3. 뒤꿈치 → 발바닥 → 발가락의 움직임을 느낍니다.
4. 다리 근육의 움직임을 알아차립니다.
5. 팔의 흔들림을 느낍니다.
6. 주변 환경을 열린 마음으로 인식합니다.
7. 마음이 방황하면 부드럽게 걷기로 돌아옵니다.

일상에서 출퇴근길, 집 안에서도 연습할 수 있습니다.
                """,
                "suitable_for": ["일상 통합", "움직임 선호", "야외"]
            },
            "dropping_anchor": {
                "name": "닻 내리기 (ACE)",
                "description": "강한 감정에서 현재로 돌아오기",
                "duration_minutes": 3,
                "instructions": """
강한 감정의 폭풍 속에서 닻을 내리세요:

A - Acknowledge (알아차리기)
"지금 나에게 OO 감정이 있구나"
생각과 감정을 알아차리고 이름 붙입니다.

C - Connect (연결하기)
몸과 연결합니다:
- 발이 바닥에 닿는 느낌
- 등이 의자에 닿는 느낌
- 손을 천천히 쥐었다 펴기
- 천천히 숨쉬기

E - Engage (참여하기)
현재 활동에 다시 참여합니다.
지금 여기서 할 수 있는 가치 있는 행동은?

이것은 감정을 없애는 것이 아니라,
폭풍 속에서 닻을 내려 안정을 찾는 것입니다.
                """,
                "suitable_for": ["위기", "강한 감정", "패닉"]
            }
        }

    def get_exercise(self, name: str) -> Optional[Dict]:
        """특정 훈련 반환"""
        return self.exercises.get(name)

    def get_exercise_for_situation(self, situation: str) -> Optional[Dict]:
        """상황에 맞는 훈련 반환"""
        situation_lower = situation.lower()

        if any(word in situation_lower for word in ["불안", "공황", "패닉"]):
            return self.exercises["dropping_anchor"]
        elif any(word in situation_lower for word in ["긴장", "스트레스"]):
            return self.exercises["body_scan"]
        elif any(word in situation_lower for word in ["산만", "집중"]):
            return self.exercises["breath_anchor"]
        elif any(word in situation_lower for word in ["해리", "비현실"]):
            return self.exercises["five_senses"]
        else:
            return self.exercises["breath_anchor"]


# =============================================================================
# Committed Action Planner (전념 행동 계획)
# =============================================================================

class CommittedActionPlanner:
    """전념 행동 계획 수립 도구"""

    def __init__(self):
        self.smart_criteria = {
            "S": "구체적 (Specific) - 정확히 무엇을 할 것인가?",
            "M": "측정가능 (Measurable) - 어떻게 완료를 알 수 있나?",
            "A": "행동중심 (Action-oriented) - 어떤 행동을 취할 것인가?",
            "R": "현실적 (Realistic) - 실제로 할 수 있는가?",
            "T": "시간제한 (Time-bound) - 언제까지 할 것인가?"
        }

    def create_action_plan(
        self,
        value: str,
        goal: str,
        barriers: List[str],
        willing_discomfort: str
    ) -> Dict:
        """전념 행동 계획 생성"""

        plan = {
            "value": value,
            "goal": goal,
            "barriers": barriers,
            "willing_discomfort": willing_discomfort,
            "action_steps": [],
            "if_then_plans": [],
            "commitment_statement": "",
            "review_date": None,
            "created_at": datetime.now().isoformat()
        }

        # 헌신 선언문 생성
        plan["commitment_statement"] = f"""
나는 {value}(이)라는 가치를 향해 나아가기 위해
{goal}을(를) 하겠습니다.

이 과정에서 {', '.join(barriers)}과(와) 같은 어려움이 있을 수 있지만,
나는 {willing_discomfort}을(를) 기꺼이 경험할 것입니다.

왜냐하면 이것이 내가 되고 싶은 사람에게 가까워지는 길이기 때문입니다.
        """

        return plan

    def add_if_then_plan(
        self,
        trigger: str,
        action: str
    ) -> Dict:
        """IF-THEN 계획 생성 (장애물 대비)"""
        return {
            "if": trigger,
            "then": action,
            "purpose": "장애물 발생 시 자동 대응"
        }

    def generate_action_prompts(self, value_domain: str) -> List[str]:
        """가치 영역별 행동 질문"""
        return [
            f"이번 주에 {value_domain} 가치를 위해 할 수 있는 작은 행동 하나는?",
            f"{value_domain}에서 되고 싶은 사람처럼 행동한다면 내일 뭘 할까요?",
            f"지금 당장 5분 안에 {value_domain}을 위해 할 수 있는 것은?",
            f"어려움이 있어도 기꺼이 하고 싶은 {value_domain} 관련 행동은?",
            f"100세 노인이 된 당신이 지금의 당신에게 {value_domain}에 대해 조언한다면?"
        ]


# =============================================================================
# ACT Advanced Module (통합 클래스)
# =============================================================================

class ACTAdvancedModule:
    """ACT 심화 모듈 통합 클래스"""

    def __init__(self):
        self.aaq_ii = AAQII()
        self.values_explorer = ValuesExplorer()
        self.defusion = DefusionTechniques()
        self.mindfulness = MindfulnessExercises()
        self.action_planner = CommittedActionPlanner()
        self.sessions: Dict[str, ACTSessionProgress] = {}

        logger.info("ACT 심화 모듈 초기화 완료")

    def start_session(self, session_id: str, user_id: str) -> ACTSessionProgress:
        """새 ACT 세션 시작"""
        session = ACTSessionProgress(
            session_id=session_id,
            user_id=user_id,
            current_process=ACTProcess.VALUES,
            completed_processes=[],
            values_assessment=[],
            defusion_techniques_used=[],
            mindfulness_exercises=[],
            committed_actions=[],
            aaq_ii_scores=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[ACTSessionProgress]:
        """세션 조회"""
        return self.sessions.get(session_id)

    def get_hexaflex_guidance(self, process: ACTProcess) -> Dict:
        """Hexaflex 과정별 가이드"""
        guidance = {
            ACTProcess.ACCEPTANCE: {
                "name": "수용 (Acceptance)",
                "description": "경험을 피하거나 싸우지 않고 기꺼이 경험하기",
                "key_questions": [
                    "지금 피하고 있는 감정이나 생각이 있나요?",
                    "그것을 밀어내려고 얼마나 많은 에너지를 쓰고 있나요?",
                    "만약 그것과 싸우지 않는다면 어떨까요?"
                ],
                "exercises": ["dropping_anchor", "breath_anchor"],
                "metaphors": ["파도 타기 - 파도와 싸우지 않고 타기", "손님 맞이하기"]
            },
            ACTProcess.DEFUSION: {
                "name": "인지적 탈융합 (Defusion)",
                "description": "생각과 거리를 두고 관찰하기",
                "key_questions": [
                    "자주 나타나는 생각 패턴이 있나요?",
                    "그 생각이 100% 사실인가요?",
                    "생각과 자신을 분리할 수 있나요?"
                ],
                "exercises": list(self.defusion.get_all_techniques().keys()),
                "metaphors": ["버스 승객", "시냇물 위 나뭇잎"]
            },
            ACTProcess.PRESENT_MOMENT: {
                "name": "현재 순간 접촉 (Present Moment)",
                "description": "지금 여기에 온전히 존재하기",
                "key_questions": [
                    "지금 이 순간 무엇을 경험하고 있나요?",
                    "과거나 미래에 빠져있진 않나요?",
                    "지금 여기서 무엇을 감각하나요?"
                ],
                "exercises": ["five_senses", "breath_anchor", "mindful_walking"],
                "metaphors": ["현재는 유일하게 살 수 있는 순간"]
            },
            ACTProcess.SELF_AS_CONTEXT: {
                "name": "맥락으로서의 자기 (Self as Context)",
                "description": "변하는 경험을 관찰하는 불변의 관찰자",
                "key_questions": [
                    "5년 전의 당신과 지금의 당신의 공통점은?",
                    "모든 생각과 감정이 변해도 변하지 않는 당신은?",
                    "당신은 생각인가요, 생각을 인식하는 자인가요?"
                ],
                "exercises": ["observer_self"],
                "metaphors": ["하늘과 날씨", "무대와 배우"]
            },
            ACTProcess.VALUES: {
                "name": "가치 (Values)",
                "description": "삶의 방향을 안내하는 나침반",
                "key_questions": [
                    "당신에게 정말 중요한 것은 무엇인가요?",
                    "어떤 사람이 되고 싶은가요?",
                    "무엇이 당신의 삶에 의미를 주나요?"
                ],
                "exercises": ["values_card_sort", "eulogy_exercise"],
                "metaphors": ["나침반 - 목적지가 아닌 방향"]
            },
            ACTProcess.COMMITTED_ACTION: {
                "name": "전념 행동 (Committed Action)",
                "description": "가치에 따라 효과적으로 행동하기",
                "key_questions": [
                    "가치를 향해 오늘 할 수 있는 작은 행동은?",
                    "어려움이 있어도 기꺼이 할 행동은?",
                    "5년 후의 당신이 오늘의 당신에게 바라는 것은?"
                ],
                "exercises": ["smart_goals", "if_then_planning"],
                "metaphors": ["여행 - 한 걸음씩"]
            }
        }
        return guidance.get(process, {})

    def process_message(
        self,
        session_id: str,
        user_message: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """메시지 처리 및 ACT 기반 응답 생성"""
        session = self.get_session(session_id)
        if not session:
            session = self.start_session(session_id, context.get("user_id", "unknown"))

        response = {
            "process": session.current_process.value,
            "guidance": self.get_hexaflex_guidance(session.current_process),
            "techniques": [],
            "exercises": [],
            "next_steps": []
        }

        # 위기 키워드 확인
        crisis_keywords = ["죽고 싶", "자살", "자해", "죽을"]
        if any(kw in user_message for kw in crisis_keywords):
            response["crisis_detected"] = True
            response["immediate_action"] = self.mindfulness.get_exercise("dropping_anchor")
            response["resources"] = {
                "hotline": "자살예방상담전화 1393 (24시간)",
                "crisis_line": "정신건강위기상담전화 1577-0199"
            }
            return response

        # 상황에 맞는 탈융합 기법 추천
        if any(word in user_message for word in ["생각", "반복", "머릿속", "떠나질 않"]):
            response["techniques"] = self.defusion.recommend_technique(user_message)

        # 상황에 맞는 마음챙김 훈련 추천
        if any(word in user_message for word in ["불안", "긴장", "스트레스", "힘들"]):
            exercise = self.mindfulness.get_exercise_for_situation(user_message)
            if exercise:
                response["exercises"].append(exercise)

        session.updated_at = datetime.now()
        return response

    def get_values_assessment_flow(self, domain: ValuesDomain) -> Dict:
        """가치 평가 플로우"""
        questions = self.values_explorer.get_domain_assessment_questions(domain)
        domain_info = self.values_explorer.domains.get(domain, {})

        return {
            "domain": domain.value,
            "domain_name": domain_info.get("name", ""),
            "description": domain_info.get("description", ""),
            "examples": domain_info.get("examples", []),
            "questions": questions,
            "rating_scales": {
                "importance": "이 영역이 당신에게 얼마나 중요한가요? (1-10)",
                "living": "현재 이 가치를 얼마나 실천하고 있나요? (1-10)"
            }
        }

    def complete_aaq_ii(self, responses: Dict[int, int]) -> AAQIIResult:
        """AAQ-II 완료 및 결과 반환"""
        return self.aaq_ii.calculate_score(responses)

    def get_module_summary(self) -> Dict:
        """모듈 요약 정보"""
        return {
            "name": "ACT 심화 모듈",
            "version": "1.0.0",
            "components": {
                "aaq_ii": "수용행동 질문지 (심리적 유연성 측정)",
                "values_explorer": "가치 탐색 도구 (10개 영역)",
                "defusion_techniques": f"탈융합 기법 ({len(self.defusion.techniques)}개)",
                "mindfulness_exercises": f"마음챙김 훈련 ({len(self.mindfulness.exercises)}개)",
                "action_planner": "전념 행동 계획 수립"
            },
            "hexaflex_processes": [p.value for p in ACTProcess]
        }


# =============================================================================
# Factory & Test
# =============================================================================

def get_act_module() -> ACTAdvancedModule:
    """ACT 모듈 인스턴스 생성"""
    return ACTAdvancedModule()


if __name__ == "__main__":
    # 테스트
    module = get_act_module()

    print("=" * 60)
    print("ACT 심화 모듈 테스트")
    print("=" * 60)

    # 모듈 요약
    summary = module.get_module_summary()
    print(f"\n모듈: {summary['name']} v{summary['version']}")
    print("\n구성요소:")
    for key, value in summary['components'].items():
        print(f"  - {key}: {value}")

    # AAQ-II 테스트
    print("\n\n--- AAQ-II 테스트 ---")
    test_responses = {1: 4, 2: 3, 3: 5, 4: 4, 5: 3, 6: 4, 7: 5}
    result = module.complete_aaq_ii(test_responses)
    print(f"총점: {result.total_score}")
    print(f"해석: {result.interpretation}")
    print(f"유연성 수준: {result.flexibility_level}")

    # 탈융합 기법 테스트
    print("\n\n--- 탈융합 기법 추천 테스트 ---")
    techniques = module.defusion.recommend_technique("자기비판적 생각이 반복돼요")
    for tech in techniques:
        print(f"  - {tech['korean_name']}: {tech['description']}")

    # 마음챙김 테스트
    print("\n\n--- 마음챙김 훈련 테스트 ---")
    exercise = module.mindfulness.get_exercise_for_situation("불안해요")
    print(f"추천 훈련: {exercise['name']}")

    # 가치 평가 테스트
    print("\n\n--- 가치 평가 플로우 테스트 ---")
    flow = module.get_values_assessment_flow(ValuesDomain.FAMILY)
    print(f"영역: {flow['domain_name']}")
    print(f"설명: {flow['description']}")
    print(f"질문 수: {len(flow['questions'])}")

    print("\n\n테스트 완료!")
