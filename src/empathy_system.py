"""
공감 품질 고도화 시스템 (Advanced Empathy System)

다차원 공감 모델:
1. 인지적 공감 (Cognitive Empathy) - 생각/관점 이해
2. 정서적 공감 (Emotional Empathy) - 감정 공명
3. 행동적 공감 (Behavioral Empathy) - 행동 맥락 이해

반영 기술 고도화:
- 감정 반영 (Emotion Reflection)
- 내용 반영 (Content Reflection)
- 의미 반영 (Meaning Reflection)
- 숨은 욕구 반영 (Needs Reflection)
"""

from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass, field
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)


# =============================================================================
# 공감 유형 및 데이터 구조
# =============================================================================

class EmpathyDimension(Enum):
    """공감의 세 가지 차원"""
    COGNITIVE = "cognitive"      # 인지적 공감: 생각/관점 이해
    EMOTIONAL = "emotional"      # 정서적 공감: 감정 공명
    BEHAVIORAL = "behavioral"    # 행동적 공감: 행동 맥락 이해


class ReflectionType(Enum):
    """반영 기술 유형"""
    EMOTION = "emotion"          # 감정 반영
    CONTENT = "content"          # 내용 반영
    MEANING = "meaning"          # 의미 반영
    NEEDS = "needs"              # 숨은 욕구 반영
    VALUES = "values"            # 가치 반영
    AMBIVALENCE = "ambivalence"  # 양가감정 반영


class EmpathyDepth(Enum):
    """공감 깊이 수준"""
    SURFACE = 1      # 표면적 공감: 명시적 내용만
    MODERATE = 2     # 중간 공감: 암시된 감정 포함
    DEEP = 3         # 깊은 공감: 숨은 의미/욕구 포함
    PROFOUND = 4     # 심층 공감: 존재적 차원


@dataclass
class EmpathyResponse:
    """공감 반응 데이터"""
    dimension: EmpathyDimension
    reflection_type: ReflectionType
    depth: EmpathyDepth
    response: str
    detected_elements: Dict[str, Any]
    confidence: float = 0.8


@dataclass
class ClientState:
    """내담자 상태 분석"""
    primary_emotion: str = ""
    secondary_emotions: List[str] = field(default_factory=list)
    emotion_intensity: float = 0.5
    key_thoughts: List[str] = field(default_factory=list)
    behaviors_mentioned: List[str] = field(default_factory=list)
    implicit_needs: List[str] = field(default_factory=list)
    values_expressed: List[str] = field(default_factory=list)
    ambivalence_detected: bool = False
    ambivalence_poles: Tuple[str, str] = ("", "")


# =============================================================================
# 다차원 공감 분석기
# =============================================================================

class MultiDimensionalEmpathyAnalyzer:
    """
    다차원 공감 분석기

    내담자의 메시지에서 인지적, 정서적, 행동적 요소를 분석
    """

    # 감정 어휘 (강도별)
    EMOTION_LEXICON = {
        # 슬픔 계열
        "슬픔": {
            "mild": ["서운", "아쉬", "허전", "쓸쓸"],
            "moderate": ["슬프", "우울", "눈물", "울적"],
            "intense": ["비참", "절망", "고통", "무너지", "산산조각"]
        },
        # 분노 계열
        "분노": {
            "mild": ["짜증", "귀찮", "불편"],
            "moderate": ["화나", "열받", "답답", "억울"],
            "intense": ["분노", "격분", "치밀", "폭발", "미치겠"]
        },
        # 두려움 계열
        "두려움": {
            "mild": ["걱정", "염려", "신경쓰"],
            "moderate": ["불안", "초조", "긴장", "두렵"],
            "intense": ["공포", "무섭", "겁나", "떨리", "패닉"]
        },
        # 수치심/죄책감 계열
        "수치심": {
            "mild": ["부끄럽", "민망", "쑥스럽"],
            "moderate": ["창피", "수치", "얼굴 들 수 없"],
            "intense": ["자격 없", "쓰레기 같", "존재 가치 없"]
        },
        # 외로움 계열
        "외로움": {
            "mild": ["혼자", "심심"],
            "moderate": ["외롭", "고독", "소외"],
            "intense": ["버림받", "아무도 없", "완전히 혼자"]
        },
        # 무력감 계열
        "무력감": {
            "mild": ["힘들", "지치"],
            "moderate": ["무기력", "의욕 없", "할 수 없"],
            "intense": ["절망", "아무것도 안 돼", "포기", "끝"]
        }
    }

    # 인지 패턴 (생각 표현)
    COGNITIVE_MARKERS = {
        "belief": ["생각", "느껴", "여겨", "같아", "보여"],
        "judgment": ["~해야", "~인 것 같", "틀림없", "분명"],
        "interpretation": ["의미", "뜻", "이유", "왜냐하면"],
        "expectation": ["기대", "바라", "원하", "희망"],
        "self_talk": ["나는", "내가", "저는", "제가"]
    }

    # 행동 패턴
    BEHAVIORAL_MARKERS = [
        "했", "갔", "봤", "만났", "말했", "들었",
        "시도", "노력", "포기", "피했", "도망",
        "싸웠", "참았", "견뎠", "버텼"
    ]

    # 숨은 욕구 키워드 매핑
    IMPLICIT_NEEDS_MAP = {
        "인정": ["무시", "인정 안", "존중 안", "하찮", "쓸모없"],
        "연결": ["외롭", "혼자", "아무도", "관심 없", "버림"],
        "안전": ["불안", "두렵", "위험", "걱정", "무섭"],
        "자율성": ["통제", "강요", "선택 없", "자유 없", "억압"],
        "의미": ["의미 없", "왜 사는지", "목적", "허무", "공허"],
        "유능감": ["못 해", "실패", "무능", "바보", "멍청"],
        "공정성": ["불공평", "억울", "왜 나만", "부당"],
        "이해": ["이해 못", "모른다", "왜 그런지", "알아주"]
    }

    # 가치 표현
    VALUES_MARKERS = {
        "가족": ["가족", "부모", "자녀", "아이", "배우자"],
        "성취": ["성공", "목표", "꿈", "성과", "결과"],
        "관계": ["친구", "사람", "관계", "사랑", "우정"],
        "자유": ["자유", "독립", "선택", "자율"],
        "안정": ["안정", "안전", "편안", "평화"],
        "성장": ["성장", "발전", "배움", "변화"],
        "정직": ["진실", "정직", "솔직", "거짓없"],
        "책임": ["책임", "의무", "역할", "맡"]
    }

    def __init__(self):
        logger.info("MultiDimensionalEmpathyAnalyzer initialized")

    def analyze(self, message: str, context: Optional[List[Dict]] = None) -> ClientState:
        """
        내담자 메시지 다차원 분석

        Args:
            message: 내담자 메시지
            context: 이전 대화 맥락 (선택)

        Returns:
            ClientState: 분석된 내담자 상태
        """
        state = ClientState()

        # 1. 감정 분석
        emotion_result = self._analyze_emotions(message)
        state.primary_emotion = emotion_result["primary"]
        state.secondary_emotions = emotion_result["secondary"]
        state.emotion_intensity = emotion_result["intensity"]

        # 2. 인지 분석 (생각/관점)
        state.key_thoughts = self._extract_thoughts(message)

        # 3. 행동 분석
        state.behaviors_mentioned = self._extract_behaviors(message)

        # 4. 숨은 욕구 추론
        state.implicit_needs = self._infer_needs(message, state.primary_emotion)

        # 5. 가치 탐색
        state.values_expressed = self._extract_values(message)

        # 6. 양가감정 탐지
        ambivalence = self._detect_ambivalence(message, context)
        state.ambivalence_detected = ambivalence["detected"]
        state.ambivalence_poles = ambivalence["poles"]

        logger.debug(f"Client state analyzed: primary_emotion={state.primary_emotion}, "
                    f"intensity={state.emotion_intensity:.2f}")

        return state

    def _analyze_emotions(self, message: str) -> Dict[str, Any]:
        """감정 분석"""
        detected = []

        for emotion, intensity_levels in self.EMOTION_LEXICON.items():
            for intensity, keywords in intensity_levels.items():
                for keyword in keywords:
                    if keyword in message:
                        intensity_score = {"mild": 0.3, "moderate": 0.6, "intense": 0.9}[intensity]
                        detected.append({
                            "emotion": emotion,
                            "keyword": keyword,
                            "intensity": intensity_score
                        })

        if not detected:
            return {"primary": "중립", "secondary": [], "intensity": 0.3}

        # 가장 강한 감정을 primary로
        detected.sort(key=lambda x: x["intensity"], reverse=True)
        primary = detected[0]["emotion"]
        intensity = detected[0]["intensity"]

        # 나머지를 secondary로
        secondary = list(set([d["emotion"] for d in detected[1:] if d["emotion"] != primary]))

        return {
            "primary": primary,
            "secondary": secondary[:3],  # 최대 3개
            "intensity": intensity
        }

    def _extract_thoughts(self, message: str) -> List[str]:
        """핵심 생각 추출"""
        thoughts = []

        # "~라고 생각해요", "~인 것 같아요" 패턴
        patterns = [
            r'(.{5,30})(라고 생각|라고 느껴|인 것 같|처럼 느껴)',
            r'(내가|제가|나는|저는)\s*(.{5,30})',
            r'(.{5,30})(해야 할|해야 한다|해야 돼)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, message)
            for match in matches:
                thought = ''.join(match).strip()
                if len(thought) > 5:
                    thoughts.append(thought)

        return thoughts[:5]  # 최대 5개

    def _extract_behaviors(self, message: str) -> List[str]:
        """언급된 행동 추출"""
        behaviors = []

        for marker in self.BEHAVIORAL_MARKERS:
            if marker in message:
                # 행동 맥락 추출 (앞뒤 10자)
                idx = message.find(marker)
                start = max(0, idx - 10)
                end = min(len(message), idx + len(marker) + 10)
                context = message[start:end].strip()
                behaviors.append(context)

        return behaviors[:5]

    def _infer_needs(self, message: str, primary_emotion: str) -> List[str]:
        """숨은 욕구 추론"""
        needs = []

        for need, keywords in self.IMPLICIT_NEEDS_MAP.items():
            for keyword in keywords:
                if keyword in message:
                    needs.append(need)
                    break

        # 감정에서 욕구 추론
        emotion_need_map = {
            "외로움": "연결",
            "분노": "공정성",
            "수치심": "인정",
            "두려움": "안전",
            "무력감": "유능감"
        }

        if primary_emotion in emotion_need_map:
            inferred_need = emotion_need_map[primary_emotion]
            if inferred_need not in needs:
                needs.append(inferred_need)

        return list(set(needs))

    def _extract_values(self, message: str) -> List[str]:
        """가치 추출"""
        values = []

        for value, keywords in self.VALUES_MARKERS.items():
            for keyword in keywords:
                if keyword in message:
                    values.append(value)
                    break

        return list(set(values))

    def _detect_ambivalence(self, message: str,
                           context: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """양가감정 탐지"""
        ambivalence_markers = [
            ("한편으로는", "다른 한편으로는"),
            ("~하고 싶지만", "~하기도 해"),
            ("좋은데", "싫어"),
            ("원하는데", "두려워"),
            ("사랑하지만", "미워"),
            ("~해야 하는데", "하기 싫"),
        ]

        # 접속사 기반 탐지
        contrast_markers = ["하지만", "그런데", "근데", "그래도", "반면", "동시에"]

        for marker in contrast_markers:
            if marker in message:
                # 양가감정 가능성 높음
                parts = message.split(marker)
                if len(parts) >= 2:
                    return {
                        "detected": True,
                        "poles": (parts[0].strip()[-20:], parts[1].strip()[:20])
                    }

        return {"detected": False, "poles": ("", "")}


# =============================================================================
# 공감 반응 생성기
# =============================================================================

class EmpathyResponseGenerator:
    """
    공감 반응 생성기

    내담자 상태에 맞는 다차원 공감 반응 생성
    """

    # 인지적 공감 템플릿
    COGNITIVE_TEMPLATES = {
        "understanding": [
            "{thought}라고 생각하셨군요",
            "그런 관점에서 보셨군요",
            "{thought}처럼 느껴지셨던 거군요",
            "그런 생각이 드셨군요",
            "{thought}라는 생각이 마음속에 있으셨네요",
        ],
        "perspective": [
            "그 상황을 그렇게 해석하셨군요",
            "{situation}가 그런 의미로 다가왔군요",
            "그 경험이 {thought}처럼 느껴지셨네요",
        ],
        "validation": [
            "그런 생각이 드시는 것도 이해가 돼요",
            "그 상황에서 그렇게 생각하시는 게 자연스러워요",
            "충분히 그렇게 느끼실 수 있어요",
        ]
    }

    # 정서적 공감 템플릿 (깊이별)
    EMOTIONAL_TEMPLATES = {
        EmpathyDepth.SURFACE: [
            "{emotion} 마음이 드셨군요",
            "{emotion} 느낌이 있으셨네요",
            "{emotion}하셨군요",
        ],
        EmpathyDepth.MODERATE: [
            "정말 {emotion}하셨겠어요",
            "{emotion} 마음이 크게 느껴지셨을 것 같아요",
            "그 {emotion}이 마음속에 깊이 있으셨네요",
            "얼마나 {emotion}하셨을지 느껴져요",
        ],
        EmpathyDepth.DEEP: [
            "그 {emotion}이 온몸으로 느껴지셨을 것 같아요",
            "마음 한가운데에서 {emotion}이 올라오셨군요",
            "{emotion} 속에서 버티고 계셨네요",
            "그 순간 얼마나 {emotion}하셨을지... 마음이 아파요",
        ],
        EmpathyDepth.PROFOUND: [
            "존재 전체가 {emotion}으로 가득 찼던 순간이었군요",
            "그 {emotion}이 당신의 전부를 흔들었겠어요",
            "삶 자체가 {emotion}으로 물들었던 시간이었네요",
        ]
    }

    # 행동적 공감 템플릿
    BEHAVIORAL_TEMPLATES = [
        "그래서 {behavior}하셨군요",
        "그 상황에서 {behavior}하신 거군요",
        "{behavior}하실 수밖에 없으셨겠어요",
        "그런 마음에 {behavior}하게 되셨네요",
        "{behavior}하시면서 버티고 계셨군요",
    ]

    # 욕구 반영 템플릿
    NEEDS_REFLECTION_TEMPLATES = {
        "인정": [
            "있는 그대로 인정받고 싶으셨던 거군요",
            "당신의 존재와 노력을 알아봐 주길 바라셨군요",
            "진정한 자신의 모습을 받아들여 주길 원하셨네요",
        ],
        "연결": [
            "누군가와 진심으로 연결되고 싶으셨군요",
            "혼자가 아니라고 느끼고 싶으셨던 거네요",
            "함께 있다는 느낌, 그게 필요하셨군요",
        ],
        "안전": [
            "안전하다고 느끼고 싶으셨군요",
            "마음 놓고 쉴 수 있는 곳이 필요하셨네요",
            "위협받지 않는다는 확신이 필요하셨던 거군요",
        ],
        "자율성": [
            "스스로 선택하고 결정할 수 있기를 원하셨군요",
            "당신의 삶을 당신이 이끌어가고 싶으셨네요",
            "누군가의 통제 없이 자유롭고 싶으셨던 거군요",
        ],
        "의미": [
            "삶의 의미를 찾고 싶으셨군요",
            "왜 살아가는지, 그 이유가 필요하셨네요",
            "의미 있는 존재로 느끼고 싶으셨던 거군요",
        ],
        "유능감": [
            "할 수 있다는 느낌이 필요하셨군요",
            "무언가를 해낼 수 있는 자신을 느끼고 싶으셨네요",
            "스스로에게 능력이 있다고 느끼고 싶으셨던 거군요",
        ],
        "공정성": [
            "공정하게 대우받고 싶으셨군요",
            "정당한 대우를 원하셨던 거네요",
            "불공평함이 마음을 아프게 했군요",
        ],
        "이해": [
            "이해받고 싶으셨군요",
            "당신의 마음을 누군가 알아주길 바라셨네요",
            "왜 그런지 설명하지 않아도 알아주는 사람이 필요하셨군요",
        ]
    }

    # 가치 반영 템플릿
    VALUES_REFLECTION_TEMPLATES = {
        "가족": "가족이 당신에게 정말 소중한 존재군요",
        "성취": "목표를 이루는 것이 당신에게 중요한 가치네요",
        "관계": "사람들과의 관계가 당신에게 큰 의미가 있군요",
        "자유": "자유롭게 살아가는 것이 당신에게 중요하네요",
        "안정": "안정된 삶이 당신에게 소중한 가치군요",
        "성장": "성장하고 발전하는 것이 당신에게 의미있네요",
        "정직": "진실되게 사는 것이 당신에게 중요하군요",
        "책임": "책임감 있게 행동하는 것이 당신의 가치네요",
    }

    # 양가감정 반영 템플릿
    AMBIVALENCE_TEMPLATES = [
        "한편으로는 {pole1} 하면서도, 다른 한편으로는 {pole2} 하시는군요",
        "두 마음이 공존하고 있네요. {pole1}와 {pole2} 사이에서...",
        "{pole1} 하고 싶으면서도 {pole2} 하시는 마음, 둘 다 진짜 마음이에요",
        "그 갈등이 느껴져요. {pole1}도 원하고, {pole2}도 원하시는...",
    ]

    def __init__(self):
        import random
        self.random = random
        logger.info("EmpathyResponseGenerator initialized")

    def generate(self, client_state: ClientState,
                 preferred_dimension: Optional[EmpathyDimension] = None,
                 target_depth: EmpathyDepth = EmpathyDepth.MODERATE) -> List[EmpathyResponse]:
        """
        공감 반응 생성

        Args:
            client_state: 분석된 내담자 상태
            preferred_dimension: 선호하는 공감 차원 (선택)
            target_depth: 목표 공감 깊이

        Returns:
            List[EmpathyResponse]: 생성된 공감 반응들
        """
        responses = []

        # 1. 정서적 공감 (항상 포함)
        emotional = self._generate_emotional_empathy(client_state, target_depth)
        if emotional:
            responses.append(emotional)

        # 2. 인지적 공감 (생각이 있을 때)
        if client_state.key_thoughts:
            cognitive = self._generate_cognitive_empathy(client_state)
            if cognitive:
                responses.append(cognitive)

        # 3. 행동적 공감 (행동이 언급됐을 때)
        if client_state.behaviors_mentioned:
            behavioral = self._generate_behavioral_empathy(client_state)
            if behavioral:
                responses.append(behavioral)

        # 4. 욕구 반영 (깊은 공감일 때)
        if target_depth.value >= EmpathyDepth.DEEP.value and client_state.implicit_needs:
            needs = self._generate_needs_reflection(client_state)
            if needs:
                responses.append(needs)

        # 5. 양가감정 반영 (감지됐을 때)
        if client_state.ambivalence_detected:
            ambivalence = self._generate_ambivalence_reflection(client_state)
            if ambivalence:
                responses.append(ambivalence)

        # 6. 가치 반영 (표현됐을 때)
        if client_state.values_expressed:
            values = self._generate_values_reflection(client_state)
            if values:
                responses.append(values)

        return responses

    def _generate_emotional_empathy(self, state: ClientState,
                                   depth: EmpathyDepth) -> Optional[EmpathyResponse]:
        """정서적 공감 생성"""
        if not state.primary_emotion or state.primary_emotion == "중립":
            return None

        templates = self.EMOTIONAL_TEMPLATES.get(depth,
                                                  self.EMOTIONAL_TEMPLATES[EmpathyDepth.MODERATE])
        template = self.random.choice(templates)

        # 감정 표현 매핑
        emotion_expressions = {
            "슬픔": ["슬프", "마음이 아프", "눈물이 나"],
            "분노": ["화가 나", "답답하", "억울하"],
            "두려움": ["두렵", "불안하", "걱정이 되"],
            "수치심": ["부끄럽", "창피하", "숨고 싶"],
            "외로움": ["외롭", "혼자인 것 같", "쓸쓸하"],
            "무력감": ["힘이 없", "무기력하", "지치"]
        }

        emotion_word = emotion_expressions.get(
            state.primary_emotion,
            [state.primary_emotion + "하"]
        )[0]

        response = template.format(emotion=emotion_word)

        return EmpathyResponse(
            dimension=EmpathyDimension.EMOTIONAL,
            reflection_type=ReflectionType.EMOTION,
            depth=depth,
            response=response,
            detected_elements={
                "primary_emotion": state.primary_emotion,
                "intensity": state.emotion_intensity
            },
            confidence=0.9 if state.emotion_intensity > 0.5 else 0.7
        )

    def _generate_cognitive_empathy(self, state: ClientState) -> Optional[EmpathyResponse]:
        """인지적 공감 생성"""
        if not state.key_thoughts:
            return None

        thought = state.key_thoughts[0]
        templates = self.COGNITIVE_TEMPLATES["understanding"]
        template = self.random.choice(templates)

        response = template.format(thought=thought)

        return EmpathyResponse(
            dimension=EmpathyDimension.COGNITIVE,
            reflection_type=ReflectionType.CONTENT,
            depth=EmpathyDepth.MODERATE,
            response=response,
            detected_elements={"thoughts": state.key_thoughts},
            confidence=0.8
        )

    def _generate_behavioral_empathy(self, state: ClientState) -> Optional[EmpathyResponse]:
        """행동적 공감 생성"""
        if not state.behaviors_mentioned:
            return None

        behavior = state.behaviors_mentioned[0]
        template = self.random.choice(self.BEHAVIORAL_TEMPLATES)
        response = template.format(behavior=behavior)

        return EmpathyResponse(
            dimension=EmpathyDimension.BEHAVIORAL,
            reflection_type=ReflectionType.CONTENT,
            depth=EmpathyDepth.MODERATE,
            response=response,
            detected_elements={"behaviors": state.behaviors_mentioned},
            confidence=0.75
        )

    def _generate_needs_reflection(self, state: ClientState) -> Optional[EmpathyResponse]:
        """욕구 반영 생성"""
        if not state.implicit_needs:
            return None

        need = state.implicit_needs[0]
        templates = self.NEEDS_REFLECTION_TEMPLATES.get(need)

        if not templates:
            return None

        response = self.random.choice(templates)

        return EmpathyResponse(
            dimension=EmpathyDimension.EMOTIONAL,
            reflection_type=ReflectionType.NEEDS,
            depth=EmpathyDepth.DEEP,
            response=response,
            detected_elements={"needs": state.implicit_needs},
            confidence=0.7
        )

    def _generate_ambivalence_reflection(self, state: ClientState) -> Optional[EmpathyResponse]:
        """양가감정 반영 생성"""
        if not state.ambivalence_detected:
            return None

        pole1, pole2 = state.ambivalence_poles
        if not pole1 or not pole2:
            return None

        template = self.random.choice(self.AMBIVALENCE_TEMPLATES)
        response = template.format(pole1=pole1, pole2=pole2)

        return EmpathyResponse(
            dimension=EmpathyDimension.EMOTIONAL,
            reflection_type=ReflectionType.AMBIVALENCE,
            depth=EmpathyDepth.DEEP,
            response=response,
            detected_elements={"ambivalence": state.ambivalence_poles},
            confidence=0.75
        )

    def _generate_values_reflection(self, state: ClientState) -> Optional[EmpathyResponse]:
        """가치 반영 생성"""
        if not state.values_expressed:
            return None

        value = state.values_expressed[0]
        response = self.VALUES_REFLECTION_TEMPLATES.get(value)

        if not response:
            return None

        return EmpathyResponse(
            dimension=EmpathyDimension.COGNITIVE,
            reflection_type=ReflectionType.VALUES,
            depth=EmpathyDepth.DEEP,
            response=response,
            detected_elements={"values": state.values_expressed},
            confidence=0.8
        )


# =============================================================================
# 공감 타이밍 최적화
# =============================================================================

class EmpathyTimingOptimizer:
    """
    공감 타이밍 최적화

    언제 어떤 깊이의 공감을 제공할지 결정
    """

    def __init__(self):
        self.turn_count = 0
        self.empathy_history = []
        self.emotion_trajectory = []
        logger.info("EmpathyTimingOptimizer initialized")

    def determine_optimal_response(
        self,
        client_state: ClientState,
        conversation_context: List[Dict],
        alliance_level: float = 0.5
    ) -> Dict[str, Any]:
        """
        최적 공감 반응 결정

        Args:
            client_state: 내담자 상태
            conversation_context: 대화 맥락
            alliance_level: 치료적 동맹 수준 (0-1)

        Returns:
            Dict: 권장 공감 설정
        """
        self.turn_count = len(conversation_context)

        # 감정 강도 추적
        self.emotion_trajectory.append(client_state.emotion_intensity)

        # 1. 공감 깊이 결정
        depth = self._determine_depth(client_state, alliance_level)

        # 2. 우선 차원 결정
        priority_dimension = self._determine_priority_dimension(client_state)

        # 3. 반영 유형 결정
        reflection_types = self._determine_reflection_types(client_state, depth)

        # 4. 공감 비율 결정 (탐색 vs 공감)
        empathy_ratio = self._calculate_empathy_ratio(client_state)

        return {
            "recommended_depth": depth,
            "priority_dimension": priority_dimension,
            "reflection_types": reflection_types,
            "empathy_ratio": empathy_ratio,
            "should_reflect_needs": depth.value >= EmpathyDepth.DEEP.value,
            "should_reflect_values": client_state.values_expressed and alliance_level > 0.6,
            "timing_notes": self._generate_timing_notes(client_state)
        }

    def _determine_depth(self, state: ClientState, alliance: float) -> EmpathyDepth:
        """공감 깊이 결정"""
        # 초기 세션에서는 표면~중간 수준
        if self.turn_count < 5:
            if state.emotion_intensity > 0.7:
                return EmpathyDepth.MODERATE
            return EmpathyDepth.SURFACE

        # 동맹이 낮으면 깊은 공감 자제
        if alliance < 0.4:
            return EmpathyDepth.SURFACE if state.emotion_intensity < 0.5 else EmpathyDepth.MODERATE

        # 감정 강도에 따른 깊이
        if state.emotion_intensity >= 0.8:
            return EmpathyDepth.PROFOUND if alliance > 0.7 else EmpathyDepth.DEEP
        elif state.emotion_intensity >= 0.6:
            return EmpathyDepth.DEEP if alliance > 0.6 else EmpathyDepth.MODERATE
        elif state.emotion_intensity >= 0.4:
            return EmpathyDepth.MODERATE
        else:
            return EmpathyDepth.SURFACE

    def _determine_priority_dimension(self, state: ClientState) -> EmpathyDimension:
        """우선 공감 차원 결정"""
        # 감정 강도가 높으면 정서적 공감 우선
        if state.emotion_intensity > 0.6:
            return EmpathyDimension.EMOTIONAL

        # 생각이 많이 표현되면 인지적 공감
        if len(state.key_thoughts) > 1:
            return EmpathyDimension.COGNITIVE

        # 행동이 언급되면 행동적 공감
        if state.behaviors_mentioned:
            return EmpathyDimension.BEHAVIORAL

        # 기본은 정서적 공감
        return EmpathyDimension.EMOTIONAL

    def _determine_reflection_types(self, state: ClientState,
                                   depth: EmpathyDepth) -> List[ReflectionType]:
        """반영 유형 결정"""
        types = [ReflectionType.EMOTION]  # 기본

        if state.key_thoughts:
            types.append(ReflectionType.CONTENT)

        if depth.value >= EmpathyDepth.DEEP.value:
            if state.implicit_needs:
                types.append(ReflectionType.NEEDS)
            if state.values_expressed:
                types.append(ReflectionType.VALUES)

        if state.ambivalence_detected:
            types.append(ReflectionType.AMBIVALENCE)

        return types

    def _calculate_empathy_ratio(self, state: ClientState) -> float:
        """
        공감 대 탐색 비율 계산

        Returns:
            float: 0.0 (순수 탐색) ~ 1.0 (순수 공감)
        """
        # 감정 강도가 높을수록 공감 비율 높임
        base_ratio = 0.5

        if state.emotion_intensity > 0.7:
            base_ratio = 0.8
        elif state.emotion_intensity > 0.5:
            base_ratio = 0.6
        elif state.emotion_intensity < 0.3:
            base_ratio = 0.3

        return base_ratio

    def _generate_timing_notes(self, state: ClientState) -> List[str]:
        """타이밍 관련 노트 생성"""
        notes = []

        # 감정 급상승 감지
        if len(self.emotion_trajectory) >= 2:
            if self.emotion_trajectory[-1] - self.emotion_trajectory[-2] > 0.3:
                notes.append("감정 급상승 - 깊은 공감 우선")

        # 양가감정 - 판단 보류
        if state.ambivalence_detected:
            notes.append("양가감정 - 양쪽 모두 인정")

        # 복합 감정 - 분리하여 반영
        if len(state.secondary_emotions) >= 2:
            notes.append("복합감정 - 단계적 반영 권장")

        return notes


# =============================================================================
# 통합 공감 시스템
# =============================================================================

class IntegratedEmpathySystem:
    """
    통합 공감 시스템

    분석, 생성, 타이밍 최적화를 통합
    """

    def __init__(self):
        self.analyzer = MultiDimensionalEmpathyAnalyzer()
        self.generator = EmpathyResponseGenerator()
        self.timing_optimizer = EmpathyTimingOptimizer()
        logger.info("IntegratedEmpathySystem initialized")

    def process(
        self,
        message: str,
        conversation_context: Optional[List[Dict]] = None,
        alliance_level: float = 0.5
    ) -> Dict[str, Any]:
        """
        메시지 처리 및 공감 반응 생성

        Args:
            message: 내담자 메시지
            conversation_context: 대화 맥락
            alliance_level: 치료적 동맹 수준

        Returns:
            Dict: 공감 분석 및 반응
        """
        context = conversation_context or []

        # 1. 내담자 상태 분석
        client_state = self.analyzer.analyze(message, context)

        # 2. 최적 타이밍/깊이 결정
        timing = self.timing_optimizer.determine_optimal_response(
            client_state, context, alliance_level
        )

        # 3. 공감 반응 생성
        responses = self.generator.generate(
            client_state,
            preferred_dimension=timing["priority_dimension"],
            target_depth=timing["recommended_depth"]
        )

        # 4. 통합 공감 메시지 구성
        integrated_response = self._compose_integrated_response(responses, timing)

        return {
            "client_state": {
                "primary_emotion": client_state.primary_emotion,
                "emotion_intensity": client_state.emotion_intensity,
                "secondary_emotions": client_state.secondary_emotions,
                "implicit_needs": client_state.implicit_needs,
                "values": client_state.values_expressed,
                "ambivalence": client_state.ambivalence_detected
            },
            "timing_recommendation": timing,
            "empathy_responses": [
                {
                    "dimension": r.dimension.value,
                    "type": r.reflection_type.value,
                    "depth": r.depth.value,
                    "response": r.response,
                    "confidence": r.confidence
                }
                for r in responses
            ],
            "integrated_response": integrated_response,
            "empathy_ratio": timing["empathy_ratio"]
        }

    def _compose_integrated_response(
        self,
        responses: List[EmpathyResponse],
        timing: Dict[str, Any]
    ) -> str:
        """
        통합 공감 응답 구성

        여러 공감 요소를 자연스럽게 결합
        """
        if not responses:
            return "말씀해 주셔서 감사해요."

        # 우선순위에 따라 정렬
        priority_order = {
            ReflectionType.EMOTION: 1,
            ReflectionType.AMBIVALENCE: 2,
            ReflectionType.CONTENT: 3,
            ReflectionType.NEEDS: 4,
            ReflectionType.VALUES: 5,
        }

        sorted_responses = sorted(
            responses,
            key=lambda r: priority_order.get(r.reflection_type, 10)
        )

        # 연결 구문
        connectors = [" ", " 그리고 ", " 동시에 "]

        # 최대 3개 반응 결합
        parts = []
        for i, response in enumerate(sorted_responses[:3]):
            if i == 0:
                parts.append(response.response)
            else:
                connector = connectors[min(i, len(connectors)-1)]
                parts.append(connector + response.response.lower())

        integrated = "".join(parts)

        # 마무리 구문 추가 (선택적)
        if timing["empathy_ratio"] > 0.7:
            integrated += " 그 마음, 충분히 이해해요."

        return integrated

    def get_empathy_prompt_section(
        self,
        message: str,
        conversation_context: Optional[List[Dict]] = None,
        alliance_level: float = 0.5
    ) -> str:
        """
        프롬프트에 삽입할 공감 가이드 섹션 생성

        Args:
            message: 내담자 메시지
            conversation_context: 대화 맥락
            alliance_level: 동맹 수준

        Returns:
            str: 프롬프트 섹션
        """
        result = self.process(message, conversation_context, alliance_level)

        state = result["client_state"]
        timing = result["timing_recommendation"]

        section = f"""
## 공감 가이드

### 내담자 현재 상태
- 주요 감정: {state['primary_emotion']} (강도: {state['emotion_intensity']:.1f})
- 부가 감정: {', '.join(state['secondary_emotions']) if state['secondary_emotions'] else '없음'}
- 숨은 욕구: {', '.join(state['implicit_needs']) if state['implicit_needs'] else '탐색 필요'}
- 양가감정: {'있음 - 양쪽 모두 인정하기' if state['ambivalence'] else '없음'}

### 권장 공감 접근
- 공감 깊이: {timing['recommended_depth'].name} ({timing['recommended_depth'].value}/4)
- 우선 차원: {timing['priority_dimension'].value}
- 반영 유형: {', '.join([t.value for t in timing['reflection_types']])}
- 공감/탐색 비율: {timing['empathy_ratio']:.0%} 공감

### 공감 예시
"""

        for r in result["empathy_responses"][:3]:
            section += f"- [{r['type']}] {r['response']}\n"

        if timing.get("timing_notes"):
            section += f"\n### 타이밍 노트\n"
            for note in timing["timing_notes"]:
                section += f"- {note}\n"

        return section


# =============================================================================
# 편의 함수
# =============================================================================

_empathy_system = None

def get_empathy_system() -> IntegratedEmpathySystem:
    """통합 공감 시스템 싱글톤 반환"""
    global _empathy_system
    if _empathy_system is None:
        _empathy_system = IntegratedEmpathySystem()
    return _empathy_system


def analyze_and_generate_empathy(
    message: str,
    context: Optional[List[Dict]] = None,
    alliance: float = 0.5
) -> Dict[str, Any]:
    """
    메시지 분석 및 공감 반응 생성

    Args:
        message: 내담자 메시지
        context: 대화 맥락
        alliance: 동맹 수준

    Returns:
        Dict: 분석 결과 및 공감 반응
    """
    system = get_empathy_system()
    return system.process(message, context, alliance)


def get_empathy_prompt_section(
    message: str,
    context: Optional[List[Dict]] = None,
    alliance: float = 0.5
) -> str:
    """
    프롬프트용 공감 가이드 섹션 생성

    Args:
        message: 내담자 메시지
        context: 대화 맥락
        alliance: 동맹 수준

    Returns:
        str: 프롬프트 섹션
    """
    system = get_empathy_system()
    return system.get_empathy_prompt_section(message, context, alliance)
