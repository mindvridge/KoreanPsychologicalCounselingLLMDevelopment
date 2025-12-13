"""
그림 치료 시스템 (Art Therapy System)
그림을 통한 심리 분석 및 치료적 개입

기능:
- 그림 기반 심리 분석
- 투사 검사 해석 (HTP, KFD)
- 치료적 그리기 활동 제공
- 그림 진행 추적
- Vision AI 연동 분석
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
import json
import base64

logger = logging.getLogger(__name__)


class ArtActivityType(Enum):
    """그림 활동 유형"""
    FREE_DRAWING = "자유화"
    HTP = "HTP검사"              # House-Tree-Person
    KFD = "가족화"               # Kinetic Family Drawing
    MANDALA = "만다라"
    EMOTION_COLOR = "감정색칠"
    SAFE_PLACE = "안전한장소"
    WORRY_BOX = "걱정상자"
    FUTURE_SELF = "미래의나"
    BRIDGE = "다리그림"           # 현재-미래 연결
    ROAD = "길그림"               # 인생 여정


class TherapeuticGoal(Enum):
    """치료 목표"""
    EMOTIONAL_EXPRESSION = "감정표현"
    SELF_EXPLORATION = "자기탐색"
    STRESS_RELIEF = "스트레스해소"
    TRAUMA_PROCESSING = "트라우마처리"
    RELATIONSHIP_INSIGHT = "관계통찰"
    FUTURE_PLANNING = "미래설계"
    GROUNDING = "안정화"
    SELF_ESTEEM = "자존감향상"


@dataclass
class DrawingAnalysis:
    """그림 분석 결과"""
    activity_type: ArtActivityType
    visual_elements: Dict[str, Any]      # 시각적 요소
    color_analysis: Dict[str, Any]       # 색상 분석
    composition_analysis: Dict[str, Any] # 구도 분석
    symbolic_interpretation: Dict[str, Any]  # 상징 해석
    psychological_insights: List[str]    # 심리학적 통찰
    therapeutic_suggestions: List[str]   # 치료적 제안
    follow_up_questions: List[str]       # 후속 질문
    confidence_score: float              # 분석 신뢰도
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            "activity_type": self.activity_type.value,
            "visual_elements": self.visual_elements,
            "color_analysis": self.color_analysis,
            "composition_analysis": self.composition_analysis,
            "symbolic_interpretation": self.symbolic_interpretation,
            "psychological_insights": self.psychological_insights,
            "therapeutic_suggestions": self.therapeutic_suggestions,
            "follow_up_questions": self.follow_up_questions,
            "confidence_score": self.confidence_score,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class ArtTherapySession:
    """그림 치료 세션"""
    session_id: str
    user_id: Optional[str]
    activity_type: ArtActivityType
    therapeutic_goal: TherapeuticGoal
    drawings: List[Dict[str, Any]]       # 그림 데이터 목록
    analyses: List[DrawingAnalysis]      # 분석 결과 목록
    conversation_notes: List[str]        # 대화 기록
    progress_notes: str                  # 진행 노트
    created_at: datetime = field(default_factory=datetime.now)

    def add_drawing(self, image_data: str, analysis: DrawingAnalysis):
        """그림 및 분석 추가"""
        self.drawings.append({
            "image_data": image_data,
            "timestamp": datetime.now().isoformat()
        })
        self.analyses.append(analysis)


class ArtTherapyEngine:
    """
    그림 치료 엔진

    그림 치료 세션을 관리하고
    치료적 개입을 제공합니다.
    """

    def __init__(self, knowledge_base_path: Optional[str] = None):
        """
        초기화

        Args:
            knowledge_base_path: 지식 베이스 경로
        """
        self.sessions: Dict[str, ArtTherapySession] = {}
        self.knowledge_base_path = knowledge_base_path

        # 활동별 치료 목표 매핑
        self.activity_goals = {
            ArtActivityType.FREE_DRAWING: [
                TherapeuticGoal.EMOTIONAL_EXPRESSION,
                TherapeuticGoal.SELF_EXPLORATION
            ],
            ArtActivityType.HTP: [
                TherapeuticGoal.SELF_EXPLORATION,
                TherapeuticGoal.RELATIONSHIP_INSIGHT
            ],
            ArtActivityType.KFD: [
                TherapeuticGoal.RELATIONSHIP_INSIGHT,
                TherapeuticGoal.SELF_EXPLORATION
            ],
            ArtActivityType.MANDALA: [
                TherapeuticGoal.STRESS_RELIEF,
                TherapeuticGoal.GROUNDING
            ],
            ArtActivityType.EMOTION_COLOR: [
                TherapeuticGoal.EMOTIONAL_EXPRESSION,
                TherapeuticGoal.SELF_EXPLORATION
            ],
            ArtActivityType.SAFE_PLACE: [
                TherapeuticGoal.GROUNDING,
                TherapeuticGoal.TRAUMA_PROCESSING
            ],
            ArtActivityType.WORRY_BOX: [
                TherapeuticGoal.STRESS_RELIEF,
                TherapeuticGoal.EMOTIONAL_EXPRESSION
            ],
            ArtActivityType.FUTURE_SELF: [
                TherapeuticGoal.FUTURE_PLANNING,
                TherapeuticGoal.SELF_ESTEEM
            ],
            ArtActivityType.BRIDGE: [
                TherapeuticGoal.FUTURE_PLANNING,
                TherapeuticGoal.SELF_EXPLORATION
            ],
            ArtActivityType.ROAD: [
                TherapeuticGoal.SELF_EXPLORATION,
                TherapeuticGoal.FUTURE_PLANNING
            ]
        }

        # 활동별 지시문
        self.activity_instructions = self._load_activity_instructions()

        logger.info("ArtTherapyEngine initialized")

    def _load_activity_instructions(self) -> Dict[ArtActivityType, Dict[str, Any]]:
        """활동 지시문 로드"""
        return {
            ArtActivityType.FREE_DRAWING: {
                "title": "자유화 그리기",
                "instruction": "마음 가는 대로 자유롭게 그려보세요. 잘 그릴 필요 없어요. 지금 떠오르는 것, 느껴지는 것을 표현해 주세요.",
                "duration": "10-15분",
                "materials": ["종이", "색연필/크레파스", "물감(선택)"]
            },
            ArtActivityType.HTP: {
                "title": "집-나무-사람 그리기 (HTP)",
                "instruction": "세 가지를 차례로 그려주세요: 1) 집 2) 나무 3) 사람. 각각 다른 종이에 그려도 되고, 한 종이에 함께 그려도 됩니다.",
                "duration": "20-30분",
                "materials": ["종이 3장", "연필", "지우개", "색연필(선택)"],
                "sub_instructions": {
                    "house": "집을 그려주세요. 어떤 집이든 괜찮아요.",
                    "tree": "나무를 그려주세요. 어떤 나무든 괜찮아요.",
                    "person": "사람을 그려주세요. 막대사람 말고 전체 모습을 그려주세요."
                }
            },
            ArtActivityType.KFD: {
                "title": "동적 가족화 (KFD)",
                "instruction": "가족 모두가 무언가를 하고 있는 모습을 그려주세요. 자기 자신도 포함해서요. 가족들이 각각 무엇을 하고 있는지 그려주세요.",
                "duration": "20-30분",
                "materials": ["종이", "연필", "색연필"]
            },
            ArtActivityType.MANDALA: {
                "title": "만다라 색칠하기",
                "instruction": "원 안을 마음 가는 대로 색칠하거나 무늬를 그려보세요. 중심에서 시작해도 되고, 바깥에서 시작해도 됩니다. 천천히, 호흡하면서 그려보세요.",
                "duration": "15-20분",
                "materials": ["만다라 도안", "색연필/마커"]
            },
            ArtActivityType.EMOTION_COLOR: {
                "title": "감정 색으로 표현하기",
                "instruction": "지금 느끼는 감정을 색으로 표현해 보세요. 여러 감정이 있다면 여러 색을 사용해도 됩니다. 형태는 자유롭게요.",
                "duration": "10-15분",
                "materials": ["종이", "크레파스/물감"]
            },
            ArtActivityType.SAFE_PLACE: {
                "title": "안전한 장소 그리기",
                "instruction": "세상에서 가장 안전하고 편안하게 느껴지는 장소를 그려보세요. 실제 장소여도 되고, 상상의 장소여도 됩니다.",
                "duration": "15-20분",
                "materials": ["종이", "색연필/크레파스"]
            },
            ArtActivityType.WORRY_BOX: {
                "title": "걱정 상자 그리기",
                "instruction": "걱정을 담아둘 상자를 그려보세요. 그리고 지금 걱정되는 것들을 작게 그려서 상자 안에 넣어보세요.",
                "duration": "15-20분",
                "materials": ["종이", "색연필"]
            },
            ArtActivityType.FUTURE_SELF: {
                "title": "미래의 나 그리기",
                "instruction": "5년 후(또는 원하는 미래 시점의) 자신의 모습을 그려보세요. 어디서 무엇을 하고 있을까요?",
                "duration": "15-20분",
                "materials": ["종이", "색연필/마커"]
            },
            ArtActivityType.BRIDGE: {
                "title": "다리 그리기",
                "instruction": "현재의 나와 미래의 나를 연결하는 다리를 그려보세요. 다리 한쪽에는 지금의 나, 반대편에는 되고 싶은 나를 그려주세요.",
                "duration": "20-25분",
                "materials": ["종이", "색연필"]
            },
            ArtActivityType.ROAD: {
                "title": "인생 길 그리기",
                "instruction": "지금까지의 인생 여정을 길로 표현해 보세요. 시작점, 중요한 갈림길, 현재 위치, 그리고 앞으로의 길도 그려보세요.",
                "duration": "25-30분",
                "materials": ["큰 종이", "색연필/마커"]
            }
        }

    def create_session(
        self,
        session_id: str,
        activity_type: ArtActivityType,
        user_id: Optional[str] = None,
        therapeutic_goal: Optional[TherapeuticGoal] = None
    ) -> ArtTherapySession:
        """
        그림 치료 세션 생성

        Args:
            session_id: 세션 ID
            activity_type: 활동 유형
            user_id: 사용자 ID
            therapeutic_goal: 치료 목표

        Returns:
            ArtTherapySession: 생성된 세션
        """
        # 기본 치료 목표 설정
        if therapeutic_goal is None:
            goals = self.activity_goals.get(activity_type, [TherapeuticGoal.SELF_EXPLORATION])
            therapeutic_goal = goals[0] if goals else TherapeuticGoal.SELF_EXPLORATION

        session = ArtTherapySession(
            session_id=session_id,
            user_id=user_id,
            activity_type=activity_type,
            therapeutic_goal=therapeutic_goal,
            drawings=[],
            analyses=[],
            conversation_notes=[],
            progress_notes=""
        )

        self.sessions[session_id] = session
        logger.info(f"Created art therapy session: {session_id} ({activity_type.value})")

        return session

    def get_activity_prompt(self, activity_type: ArtActivityType) -> Dict[str, Any]:
        """
        활동 안내 프롬프트 가져오기

        Args:
            activity_type: 활동 유형

        Returns:
            Dict: 활동 안내 정보
        """
        instruction = self.activity_instructions.get(activity_type, {})

        return {
            "activity_type": activity_type.value,
            "title": instruction.get("title", activity_type.value),
            "instruction": instruction.get("instruction", ""),
            "duration": instruction.get("duration", "15-20분"),
            "materials": instruction.get("materials", []),
            "sub_instructions": instruction.get("sub_instructions", {}),
            "therapeutic_goals": [g.value for g in self.activity_goals.get(activity_type, [])]
        }

    def suggest_activity(
        self,
        emotional_state: str,
        therapeutic_goal: Optional[TherapeuticGoal] = None,
        previous_activities: Optional[List[ArtActivityType]] = None
    ) -> List[Dict[str, Any]]:
        """
        상황에 맞는 활동 추천

        Args:
            emotional_state: 현재 감정 상태
            therapeutic_goal: 원하는 치료 목표
            previous_activities: 이전에 수행한 활동들

        Returns:
            List[Dict]: 추천 활동 목록
        """
        # 감정 상태별 추천
        emotion_activity_map = {
            "불안": [ArtActivityType.MANDALA, ArtActivityType.SAFE_PLACE, ArtActivityType.WORRY_BOX],
            "우울": [ArtActivityType.EMOTION_COLOR, ArtActivityType.FUTURE_SELF, ArtActivityType.FREE_DRAWING],
            "분노": [ArtActivityType.FREE_DRAWING, ArtActivityType.EMOTION_COLOR],
            "슬픔": [ArtActivityType.EMOTION_COLOR, ArtActivityType.SAFE_PLACE],
            "스트레스": [ArtActivityType.MANDALA, ArtActivityType.WORRY_BOX],
            "혼란": [ArtActivityType.ROAD, ArtActivityType.BRIDGE],
            "외로움": [ArtActivityType.KFD, ArtActivityType.SAFE_PLACE],
            "자존감": [ArtActivityType.FUTURE_SELF, ArtActivityType.HTP]
        }

        # 추천 활동 수집
        recommendations = []

        # 감정 기반 추천
        for emotion_key, activities in emotion_activity_map.items():
            if emotion_key in emotional_state:
                for activity in activities:
                    if activity not in (previous_activities or []):
                        recommendations.append(activity)

        # 치료 목표 기반 추천
        if therapeutic_goal:
            for activity, goals in self.activity_goals.items():
                if therapeutic_goal in goals and activity not in recommendations:
                    recommendations.append(activity)

        # 기본 추천
        if not recommendations:
            recommendations = [ArtActivityType.FREE_DRAWING, ArtActivityType.EMOTION_COLOR]

        # 상위 3개만 반환
        return [self.get_activity_prompt(a) for a in recommendations[:3]]

    def generate_therapeutic_response(
        self,
        analysis: DrawingAnalysis,
        user_context: Optional[Dict] = None
    ) -> str:
        """
        분석 결과 기반 치료적 응답 생성

        Args:
            analysis: 그림 분석 결과
            user_context: 사용자 컨텍스트

        Returns:
            str: 치료적 응답
        """
        response_parts = []

        # 1. 그림에 대한 인정/수용
        response_parts.append("그림을 보여주셔서 감사해요.")

        # 2. 관찰된 내용 반영 (비판단적)
        if analysis.visual_elements:
            elements = analysis.visual_elements
            if elements.get("dominant_colors"):
                colors = elements["dominant_colors"]
                response_parts.append(f"{', '.join(colors[:2])} 색을 많이 사용하셨네요.")

        # 3. 열린 질문
        if analysis.follow_up_questions:
            response_parts.append("")
            response_parts.append(analysis.follow_up_questions[0])

        # 4. 통찰 제공 (조심스럽게)
        if analysis.psychological_insights and analysis.confidence_score > 0.7:
            response_parts.append("")
            response_parts.append("혹시... " + analysis.psychological_insights[0])

        return "\n".join(response_parts)

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """
        세션 요약 가져오기

        Args:
            session_id: 세션 ID

        Returns:
            Dict: 세션 요약
        """
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        return {
            "session_id": session.session_id,
            "activity_type": session.activity_type.value,
            "therapeutic_goal": session.therapeutic_goal.value,
            "drawings_count": len(session.drawings),
            "key_insights": [
                insight
                for analysis in session.analyses
                for insight in analysis.psychological_insights[:2]
            ],
            "duration": (datetime.now() - session.created_at).seconds // 60
        }


class ArtTherapyPromptGenerator:
    """
    그림 치료 프롬프트 생성기

    Vision AI에 전달할 분석 프롬프트를 생성합니다.
    """

    def __init__(self):
        self.base_guidelines = """
## 그림 분석 가이드라인

### 핵심 원칙
1. **비판단적 관찰**: 그림의 "좋고 나쁨"을 평가하지 않습니다.
2. **가설적 해석**: 모든 해석은 가설이며, 확정적 진단이 아닙니다.
3. **문화적 민감성**: 한국 문화적 맥락을 고려합니다.
4. **통합적 접근**: 개별 요소보다 전체적 인상을 중시합니다.

### 분석 영역
1. **형식적 요소**: 크기, 위치, 필압, 선의 특성
2. **색상**: 사용된 색상, 색의 강도, 색 조합
3. **내용**: 그려진 대상, 상징물, 생략된 요소
4. **공간 사용**: 전체 공간 활용, 요소 간 거리
5. **에너지**: 그림의 전반적 에너지와 분위기
"""

    def generate_analysis_prompt(
        self,
        activity_type: ArtActivityType,
        additional_context: Optional[str] = None
    ) -> str:
        """
        분석 프롬프트 생성

        Args:
            activity_type: 활동 유형
            additional_context: 추가 컨텍스트

        Returns:
            str: 분석 프롬프트
        """
        activity_specific = self._get_activity_specific_prompt(activity_type)

        prompt = f"""
{self.base_guidelines}

## 현재 활동: {activity_type.value}

{activity_specific}

## 분석 출력 형식

다음 형식으로 분석 결과를 제공해주세요:

### 1. 시각적 요소
- dominant_colors: [사용된 주요 색상]
- line_quality: 선의 특성 (굵기, 압력, 연속성)
- size: 그림 크기 (작음/중간/큼)
- position: 그림 위치 (중앙/상단/하단/좌/우)
- details: 세부 묘사 정도

### 2. 색상 분석
- 감정적 의미
- 에너지 수준
- 주목할 점

### 3. 구도 분석
- 공간 활용
- 요소 간 관계
- 균형/불균형

### 4. 상징적 해석
- 주요 상징물
- 생략된 요소
- 특이 요소

### 5. 심리학적 통찰 (가설적)
- 가능한 감정 상태
- 관계 패턴 (해당 시)
- 자기 인식

### 6. 치료적 제안
- 후속 활동 제안
- 탐색할 주제

### 7. 후속 질문 (3개)
- 그림에 대해 더 알아볼 열린 질문들

{f"### 추가 컨텍스트: {additional_context}" if additional_context else ""}
"""
        return prompt

    def _get_activity_specific_prompt(self, activity_type: ArtActivityType) -> str:
        """활동별 특화 프롬프트"""
        prompts = {
            ArtActivityType.HTP: """
### HTP 검사 특화 분석

**집 (House) 분석 포인트:**
- 지붕: 환상/사고 영역
- 벽: 자아 강도
- 문: 외부와의 접촉
- 창문: 환경과의 상호작용
- 굴뚝/연기: 가정 내 따뜻함, 정서적 분위기
- 길: 접근성

**나무 (Tree) 분석 포인트:**
- 뿌리: 안정감, 현실 접촉
- 줄기: 자아 강도
- 가지: 환경과의 상호작용
- 잎/열매: 성취, 생산성
- 전체 크기: 자아상

**사람 (Person) 분석 포인트:**
- 머리: 지적 기능
- 얼굴 표정: 감정 상태
- 눈: 외부 세계와의 접촉
- 팔/손: 환경 조작 능력
- 다리/발: 안정감, 이동성
- 전체 비율: 신체상
""",
            ArtActivityType.KFD: """
### 동적 가족화 (KFD) 특화 분석

**분석 포인트:**
- 가족 구성원 배치: 거리, 위치 관계
- 각 인물의 활동: 상호작용 vs 개별 활동
- 크기 비율: 인지된 힘/중요성
- 얼굴 방향: 관계의 질
- 자기 자신의 위치: 가족 내 역할
- 생략된 가족원: 갈등 또는 거리감
- 장벽 요소: 가구, 벽 등으로 분리
- 전체적 분위기: 연결 vs 고립
""",
            ArtActivityType.MANDALA: """
### 만다라 분석 포인트

- 중심에서 시작 vs 외곽에서 시작
- 대칭성: 균형 추구
- 색상 패턴: 감정의 흐름
- 빈 공간: 내적 여백
- 채움 정도: 에너지 수준
- 반복 패턴: 질서 추구
""",
            ArtActivityType.EMOTION_COLOR: """
### 감정 색칠 분석 포인트

- 선택한 색상: 감정과의 연결
- 색상 배치: 감정의 관계
- 색의 강도: 감정의 강도
- 혼합 여부: 감정의 복잡성
- 형태: 감정의 형상화
- 공간 활용: 감정의 크기/영향력
""",
            ArtActivityType.SAFE_PLACE: """
### 안전한 장소 분석 포인트

- 장소 유형: 실내/실외, 자연/인공
- 경계: 보호 요소 (벽, 울타리)
- 혼자/함께: 사회적 욕구
- 날씨/분위기: 정서적 톤
- 접근성: 쉽게 갈 수 있는지
- 세부 요소: 편안함의 원천
""",
            ArtActivityType.ROAD: """
### 인생 길 분석 포인트

- 길의 형태: 직선/곡선/갈림길
- 장애물: 인식된 어려움
- 현재 위치: 어디쯤인가
- 과거 표현: 중요 사건
- 미래 표현: 희망/불확실성
- 주변 환경: 지지 자원
- 길의 끝: 목표 또는 미지
"""
        }

        return prompts.get(activity_type, """
### 일반 분석 포인트

- 전체적인 인상과 분위기
- 주요 시각적 요소
- 감정적 톤
- 특이하거나 주목할 요소
""")

    def generate_therapeutic_dialogue_prompt(
        self,
        analysis: DrawingAnalysis,
        conversation_history: Optional[List[str]] = None
    ) -> str:
        """
        치료적 대화 프롬프트 생성

        Args:
            analysis: 분석 결과
            conversation_history: 이전 대화

        Returns:
            str: 대화 프롬프트
        """
        return f"""
## 그림 치료 대화 가이드

### 분석 결과 요약
- 활동: {analysis.activity_type.value}
- 주요 통찰: {', '.join(analysis.psychological_insights[:2]) if analysis.psychological_insights else '탐색 중'}

### 대화 원칙
1. 그림에 대한 관찰을 공유하되, 해석을 강요하지 않기
2. "이것은 ~를 의미한다"가 아닌 "~처럼 보이는데, 어떻게 느끼세요?" 형태로
3. 내담자의 설명을 우선으로 듣기
4. 그림의 감정적 측면에 초점 맞추기
5. 비판단적이고 호기심 어린 태도 유지

### 제안된 후속 질문
{chr(10).join(f'- {q}' for q in analysis.follow_up_questions)}

### 피해야 할 표현
- "이건 ~를 나타내네요" (단정적)
- "왜 이렇게 그렸어요?" (방어 유발)
- "~가 없네요" (비판적)

### 권장 표현
- "이 부분에 대해 더 이야기해 주실 수 있을까요?"
- "그림을 그리면서 어떤 느낌이 드셨어요?"
- "여기 ~가 눈에 띄는데, 어떤 의미가 있을까요?"
"""


# =============================================================================
# 편의 함수
# =============================================================================

def create_art_therapy_session(
    session_id: str,
    activity_type: str = "자유화"
) -> Tuple[ArtTherapyEngine, ArtTherapySession]:
    """그림 치료 세션 빠른 생성"""
    engine = ArtTherapyEngine()

    # 문자열을 Enum으로 변환
    activity_map = {a.value: a for a in ArtActivityType}
    activity = activity_map.get(activity_type, ArtActivityType.FREE_DRAWING)

    session = engine.create_session(session_id, activity)
    return engine, session


def get_activity_recommendations(emotional_state: str) -> List[Dict]:
    """감정 상태 기반 활동 추천"""
    engine = ArtTherapyEngine()
    return engine.suggest_activity(emotional_state)


# =============================================================================
# 테스트
# =============================================================================

def test_art_therapy():
    """그림 치료 시스템 테스트"""
    print("=== 그림 치료 시스템 테스트 ===\n")

    engine = ArtTherapyEngine()

    # 1. 세션 생성
    session = engine.create_session(
        session_id="art_session_001",
        activity_type=ArtActivityType.HTP
    )
    print(f"세션 생성: {session.session_id} ({session.activity_type.value})")

    # 2. 활동 안내 가져오기
    prompt = engine.get_activity_prompt(ArtActivityType.HTP)
    print(f"\n활동 안내:")
    print(f"  제목: {prompt['title']}")
    print(f"  지시: {prompt['instruction'][:50]}...")
    print(f"  시간: {prompt['duration']}")

    # 3. 감정 기반 활동 추천
    print("\n감정 기반 활동 추천 (불안):")
    recommendations = engine.suggest_activity("불안하고 걱정이 많아요")
    for rec in recommendations:
        print(f"  - {rec['title']}: {rec['instruction'][:40]}...")

    # 4. 프롬프트 생성기 테스트
    prompt_gen = ArtTherapyPromptGenerator()
    analysis_prompt = prompt_gen.generate_analysis_prompt(ArtActivityType.HTP)
    print(f"\n분석 프롬프트 길이: {len(analysis_prompt)} 문자")


if __name__ == "__main__":
    test_art_therapy()
