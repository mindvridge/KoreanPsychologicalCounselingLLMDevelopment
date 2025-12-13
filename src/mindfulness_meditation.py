# -*- coding: utf-8 -*-
"""
마음챙김/명상 모듈 (Mindfulness & Meditation Module)

다양한 마음챙김과 명상 기법을 채팅에 통합하여
현재 순간에 대한 인식과 수용을 높입니다.

Author: MindVridge AI Team
Version: 1.0.0
"""

import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any


class MeditationType(Enum):
    """명상 유형"""
    MINDFUL_BREATHING = "mindful_breathing"     # 마음챙김 호흡
    BODY_AWARENESS = "body_awareness"           # 신체 인식
    LOVING_KINDNESS = "loving_kindness"         # 자애 명상
    OBSERVING_THOUGHTS = "observing_thoughts"   # 생각 관찰
    WALKING = "walking"                         # 걷기 명상
    EATING = "eating"                           # 마음챙김 식사
    SOUND = "sound"                             # 소리 명상
    GRATITUDE = "gratitude"                     # 감사 명상
    SELF_COMPASSION = "self_compassion"         # 자기 연민
    PRESENT_MOMENT = "present_moment"           # 현재 순간 인식


class MindfulnessExerciseType(Enum):
    """마음챙김 운동 유형"""
    STOP = "stop"                               # STOP 기법
    RAIN = "rain"                               # RAIN 기법
    THREE_STEP = "three_step"                   # 3분 호흡공간
    MINDFUL_PAUSE = "mindful_pause"             # 마음챙김 멈춤
    NOTING = "noting"                           # 알아차리기(노팅)


@dataclass
class MeditationScript:
    """명상 스크립트"""
    meditation_type: MeditationType
    name: str
    duration_minutes: int
    introduction: str
    main_practice: List[str]
    closing: str
    suitable_for: List[str]
    benefits: List[str]


@dataclass
class MindfulnessExercise:
    """마음챙김 운동"""
    exercise_type: MindfulnessExerciseType
    name: str
    acronym_meaning: Optional[Dict[str, str]]  # 약어 설명
    steps: List[str]
    duration_minutes: int
    when_to_use: List[str]


@dataclass
class MeditationSession:
    """명상 세션"""
    session_id: str
    user_id: str
    meditation_type: MeditationType
    current_step: int = 0
    started_at: datetime = field(default_factory=datetime.now)
    paused: bool = False
    completed: bool = False


class MeditationLibrary:
    """명상 라이브러리"""

    def __init__(self):
        self.scripts = self._initialize_scripts()

    def _initialize_scripts(self) -> Dict[MeditationType, MeditationScript]:
        """명상 스크립트 초기화"""
        return {
            MeditationType.MINDFUL_BREATHING: MeditationScript(
                meditation_type=MeditationType.MINDFUL_BREATHING,
                name="마음챙김 호흡",
                duration_minutes=5,
                introduction="""편안한 자세를 취해주세요.
눈을 감거나 부드럽게 아래를 바라봐 주세요.
지금 이 순간, 호흡에 주의를 가져가 봅니다.""",
                main_practice=[
                    "자연스러운 호흡을 느껴보세요. 바꾸려 하지 마세요.",
                    "숨이 들어오는 것을 알아차리세요... 배가 부풀어 오릅니다.",
                    "숨이 나가는 것을 알아차리세요... 배가 가라앉습니다.",
                    "생각이 떠오르면, 그냥 알아차리고 다시 호흡으로 돌아오세요.",
                    "판단 없이, 있는 그대로 호흡을 관찰하세요.",
                    "들숨... 날숨... 지금 이 순간에 머물러 주세요.",
                    "호흡의 리듬을 느끼세요. 자연스러운 파도처럼...",
                    "마음이 떠돌아도 괜찮습니다. 부드럽게 돌아오면 됩니다."
                ],
                closing="""천천히 주변 소리를 알아차려 보세요.
몸의 감각을 느껴보세요.
준비가 되면 눈을 떠주세요.
이 평온함을 가지고 일상으로 돌아가세요.""",
                suitable_for=["스트레스", "불안", "집중력 부족", "일상"],
                benefits=["스트레스 감소", "집중력 향상", "감정 조절", "현재 인식"]
            ),

            MeditationType.BODY_AWARENESS: MeditationScript(
                meditation_type=MeditationType.BODY_AWARENESS,
                name="신체 인식 명상 (바디 스캔)",
                duration_minutes=10,
                introduction="""편안하게 누워주세요.
눈을 감고 몇 번 깊은 호흡을 합니다.
발끝부터 머리끝까지 천천히 여행할 거예요.""",
                main_practice=[
                    "발끝에 주의를 가져가세요. 어떤 감각이 느껴지나요?",
                    "발바닥... 발등... 발가락 하나하나를 느껴보세요.",
                    "천천히 발목으로, 종아리로 올라갑니다.",
                    "무릎... 허벅지... 긴장이 있다면 숨을 내쉬며 풀어주세요.",
                    "골반과 엉덩이... 이 부위에 머물러 보세요.",
                    "배... 숨을 쉴 때마다 부풀고 가라앉는 것을 느껴보세요.",
                    "가슴... 심장 박동을 느낄 수 있나요?",
                    "어깨... 많은 긴장이 쌓이는 곳입니다. 내려놓아 주세요.",
                    "팔... 손... 손가락 끝까지 알아차려 보세요.",
                    "목... 턱... 얼굴 근육을 풀어주세요.",
                    "이마... 정수리... 전신이 하나로 이완됩니다."
                ],
                closing="""전신의 감각을 한꺼번에 느껴보세요.
평화롭고 이완된 상태입니다.
천천히 손가락과 발가락을 움직여 보세요.
준비가 되면 부드럽게 눈을 떠주세요.""",
                suitable_for=["불면증", "신체 긴장", "만성 통증", "스트레스"],
                benefits=["신체 인식", "긴장 이완", "수면 개선", "통증 관리"]
            ),

            MeditationType.LOVING_KINDNESS: MeditationScript(
                meditation_type=MeditationType.LOVING_KINDNESS,
                name="자애 명상 (메타 명상)",
                duration_minutes=10,
                introduction="""편안한 자세로 앉아주세요.
눈을 감고 가슴 중앙에 손을 올려도 좋아요.
따뜻한 마음을 불러일으켜 봅니다.""",
                main_practice=[
                    "먼저, 자기 자신에게 사랑과 친절을 보내봅니다.",
                    "마음속으로 말해보세요: '내가 행복하기를...'",
                    "'내가 건강하기를...'",
                    "'내가 안전하기를...'",
                    "'내가 평화롭기를...'",
                    "이 따뜻한 마음을 느껴보세요.",
                    "이제 사랑하는 사람을 떠올려 보세요.",
                    "그 사람에게 같은 마음을 보냅니다: '당신이 행복하기를...'",
                    "'당신이 건강하기를...'",
                    "이제 이 마음을 모든 존재로 확장합니다.",
                    "'모든 존재가 행복하기를... 평화롭기를...'"
                ],
                closing="""가슴에서 퍼져나가는 따뜻함을 느껴보세요.
이 자애의 마음을 간직하세요.
천천히 현재로 돌아옵니다.
눈을 뜨고, 이 마음을 세상과 나누세요.""",
                suitable_for=["자기 비판", "분노", "외로움", "관계 문제"],
                benefits=["자기 연민", "타인 연민", "긍정 감정", "관계 개선"]
            ),

            MeditationType.OBSERVING_THOUGHTS: MeditationScript(
                meditation_type=MeditationType.OBSERVING_THOUGHTS,
                name="생각 관찰 명상",
                duration_minutes=7,
                introduction="""편안한 자세를 취해주세요.
호흡에 먼저 주의를 기울입니다.
이제 마음속에서 떠오르는 생각들을 관찰해 볼 거예요.""",
                main_practice=[
                    "생각이 떠오르면, 그것을 알아차리세요.",
                    "생각에 꼬리표를 붙여보세요: '계획', '걱정', '기억'...",
                    "구름이 하늘을 지나가듯, 생각도 지나가게 두세요.",
                    "생각을 따라가지 마세요. 그냥 관찰만 하세요.",
                    "생각이 사라지면, 다음 생각이 올 때까지 기다려보세요.",
                    "생각은 당신이 아닙니다. 그저 지나가는 정신 현상일 뿐.",
                    "생각에 빠져들었다면, 괜찮습니다. 다시 관찰자로 돌아오세요.",
                    "판단 없이, 호기심을 가지고 바라보세요."
                ],
                closing="""생각과 당신 사이에 공간이 있다는 것을 느끼셨나요?
이 관찰하는 마음을 기억하세요.
일상에서도 생각을 관찰할 수 있습니다.
천천히 눈을 떠주세요.""",
                suitable_for=["반추", "걱정", "불안", "생각 과다"],
                benefits=["생각과 거리두기", "반추 감소", "마음의 평화", "인지적 유연성"]
            ),

            MeditationType.SELF_COMPASSION: MeditationScript(
                meditation_type=MeditationType.SELF_COMPASSION,
                name="자기 연민 명상",
                duration_minutes=8,
                introduction="""편안한 자세로 앉아주세요.
힘들었던 순간을 떠올려도 좋아요.
자기 자신에게 따뜻한 마음을 보내봅니다.""",
                main_practice=[
                    "먼저 현재 느끼는 어려움을 인정해 주세요.",
                    "'지금 힘들구나...' 라고 자신에게 말해보세요.",
                    "모든 사람이 때때로 힘들다는 것을 기억하세요.",
                    "'나만 힘든 것이 아니야. 이것이 인간의 경험이야.'",
                    "가슴에 손을 올려보세요. 따뜻함을 느껴보세요.",
                    "'내가 스스로에게 친절하기를...'",
                    "'나 자신을 있는 그대로 받아들이기를...'",
                    "친구에게 하듯이, 자신에게 따뜻한 말을 건네보세요.",
                    "완벽하지 않아도 괜찮습니다. 당신은 충분합니다."
                ],
                closing="""이 자기 연민의 마음을 기억하세요.
힘들 때마다 이 연습을 할 수 있어요.
자신에게 친절하세요.
천천히 눈을 떠주세요.""",
                suitable_for=["자기 비판", "수치심", "실패감", "낮은 자존감"],
                benefits=["자기 수용", "자기 비판 감소", "정서적 회복력", "웰빙 증진"]
            ),

            MeditationType.PRESENT_MOMENT: MeditationScript(
                meditation_type=MeditationType.PRESENT_MOMENT,
                name="현재 순간 인식",
                duration_minutes=5,
                introduction="""잠시 멈추어 주세요.
지금 이 순간에 온전히 존재해 봅니다.
과거도 미래도 없이, 오직 지금.""",
                main_practice=[
                    "지금 무엇을 보고 있나요? 색깔, 모양, 빛을 알아차리세요.",
                    "지금 무엇을 듣고 있나요? 가까운 소리, 먼 소리...",
                    "몸에 닿는 감각을 느껴보세요. 옷의 촉감, 공기의 온도...",
                    "지금 어떤 냄새가 나나요?",
                    "입안에 어떤 맛이 느껴지나요?",
                    "이 모든 것이 '지금 여기'입니다.",
                    "생각이 과거나 미래로 가면, 부드럽게 현재로 돌아오세요.",
                    "지금 이 순간만이 진짜입니다."
                ],
                closing="""지금 이 순간에 완전히 존재하셨습니다.
이 느낌을 기억하세요.
언제든 현재로 돌아올 수 있습니다.
눈을 뜨고, 새로운 눈으로 세상을 바라보세요.""",
                suitable_for=["걱정", "미래 불안", "과거 집착", "일상"],
                benefits=["현재 인식", "걱정 감소", "삶의 질 향상", "감사함 증진"]
            ),

            MeditationType.GRATITUDE: MeditationScript(
                meditation_type=MeditationType.GRATITUDE,
                name="감사 명상",
                duration_minutes=7,
                introduction="""편안한 자세로 앉아주세요.
눈을 감고 호흡을 가다듬습니다.
감사의 마음을 불러일으켜 봅니다.""",
                main_practice=[
                    "오늘 아침 눈을 뜰 수 있었던 것에 감사해 보세요.",
                    "숨을 쉴 수 있는 것에 감사합니다.",
                    "당신을 지지해주는 사람을 떠올려 보세요. 감사합니다.",
                    "오늘 먹은 음식에 감사합니다. 그 음식을 만든 모든 사람에게.",
                    "편안한 잠자리에 감사합니다.",
                    "아픈 곳 없이 건강한 것에 감사합니다.",
                    "작은 행복의 순간들을 떠올려 보세요. 커피 한 잔, 따뜻한 햇살...",
                    "지금 이 순간 존재하는 것 자체에 감사합니다.",
                    "감사의 마음이 가슴에서 퍼져나가는 것을 느껴보세요."
                ],
                closing="""감사의 마음을 가득 안고 계시네요.
이 마음을 오늘 하루 간직하세요.
작은 것에도 감사할 수 있기를.
눈을 뜨고, 감사의 눈으로 세상을 바라보세요.""",
                suitable_for=["우울", "부정적 사고", "무기력", "불만"],
                benefits=["긍정 감정 증진", "웰빙 향상", "관계 개선", "삶의 만족"]
            )
        }

    def get_script(self, meditation_type: MeditationType) -> MeditationScript:
        """특정 명상 스크립트 반환"""
        return self.scripts.get(meditation_type)

    def get_suitable_meditation(self, emotion: str) -> List[MeditationScript]:
        """감정에 적합한 명상 목록"""
        suitable = []
        for script in self.scripts.values():
            if any(emotion.lower() in s.lower() for s in script.suitable_for):
                suitable.append(script)
        return suitable


class MindfulnessExerciseLibrary:
    """마음챙김 운동 라이브러리"""

    def __init__(self):
        self.exercises = self._initialize_exercises()

    def _initialize_exercises(self) -> Dict[MindfulnessExerciseType, MindfulnessExercise]:
        """마음챙김 운동 초기화"""
        return {
            MindfulnessExerciseType.STOP: MindfulnessExercise(
                exercise_type=MindfulnessExerciseType.STOP,
                name="STOP 기법",
                acronym_meaning={
                    "S": "Stop (멈추기) - 하던 일을 잠시 멈추세요",
                    "T": "Take a breath (호흡하기) - 깊은 숨을 한번 쉬세요",
                    "O": "Observe (관찰하기) - 지금 무엇을 느끼는지 관찰하세요",
                    "P": "Proceed (진행하기) - 의식적으로 다음 행동을 선택하세요"
                },
                steps=[
                    "🛑 **S - 멈추기**: 지금 하던 것을 잠시 멈추세요.",
                    "🌬️ **T - 호흡**: 깊이 숨을 들이쉬고, 천천히 내쉬세요.",
                    "👁️ **O - 관찰**: 몸의 감각, 감정, 생각을 알아차리세요.",
                    "➡️ **P - 진행**: 지금 가장 필요한 것은 무엇인가요? 의식적으로 선택하세요."
                ],
                duration_minutes=1,
                when_to_use=["스트레스 순간", "감정적 반응 전", "결정이 필요할 때"]
            ),

            MindfulnessExerciseType.RAIN: MindfulnessExercise(
                exercise_type=MindfulnessExerciseType.RAIN,
                name="RAIN 기법",
                acronym_meaning={
                    "R": "Recognize (인식하기) - 무슨 일이 일어나고 있는지 인식",
                    "A": "Allow (허용하기) - 경험을 있는 그대로 허용",
                    "I": "Investigate (탐구하기) - 친절한 호기심으로 탐구",
                    "N": "Non-identification (동일시하지 않기) - 이것이 '나'가 아님을 인식"
                },
                steps=[
                    "🌧️ **R - 인식하기**: 지금 무엇을 경험하고 있나요? 감정, 생각, 신체 감각을 알아차리세요.",
                    "✨ **A - 허용하기**: 그 경험을 있는 그대로 허용하세요. 바꾸려 하지 마세요. '이것이 지금 있구나'",
                    "🔍 **I - 탐구하기**: 친절한 호기심을 가지고 탐구하세요. 이 감정이 몸에서 어떻게 느껴지나요? 무엇이 이것을 촉발했나요?",
                    "💜 **N - 동일시하지 않기**: 이 감정/생각은 '나'가 아닙니다. 지나가는 경험일 뿐이에요."
                ],
                duration_minutes=5,
                when_to_use=["강한 감정", "자기 비판", "어려운 경험"]
            ),

            MindfulnessExerciseType.THREE_STEP: MindfulnessExercise(
                exercise_type=MindfulnessExerciseType.THREE_STEP,
                name="3분 호흡 공간",
                acronym_meaning=None,
                steps=[
                    "**1분 - 알아차리기** 🔔\n지금 무엇을 경험하고 있나요?\n- 어떤 생각이 있나요?\n- 어떤 감정이 있나요?\n- 몸에서 무엇을 느끼나요?",
                    "**1분 - 집중하기** 🎯\n호흡에 주의를 집중하세요.\n숨이 들어오고 나가는 것을 느끼세요.\n배가 부풀고 가라앉는 것을 알아차리세요.",
                    "**1분 - 확장하기** 🌊\n호흡의 인식을 전신으로 확장하세요.\n몸 전체가 호흡하는 것을 느껴보세요.\n이 인식을 가지고 다음 활동으로 가세요."
                ],
                duration_minutes=3,
                when_to_use=["일상 중간", "스트레스 상황", "전환 시점"]
            ),

            MindfulnessExerciseType.MINDFUL_PAUSE: MindfulnessExercise(
                exercise_type=MindfulnessExerciseType.MINDFUL_PAUSE,
                name="마음챙김 멈춤",
                acronym_meaning=None,
                steps=[
                    "⏸️ 하던 일을 멈추세요.",
                    "🦶 발바닥이 바닥에 닿는 감각을 느껴보세요.",
                    "🫁 세 번 깊이 호흡하세요.",
                    "👀 주변을 천천히 둘러보세요.",
                    "💭 '지금 이 순간 나는 여기 있다'고 인식하세요."
                ],
                duration_minutes=1,
                when_to_use=["바쁜 일상", "자동조종 모드에서 벗어날 때", "현재로 돌아올 때"]
            ),

            MindfulnessExerciseType.NOTING: MindfulnessExercise(
                exercise_type=MindfulnessExerciseType.NOTING,
                name="알아차리기 (노팅)",
                acronym_meaning=None,
                steps=[
                    "생각이 떠오르면 '생각'이라고 속으로 이름 붙이세요.",
                    "감정이 느껴지면 '감정'이라고 이름 붙이세요.",
                    "몸의 감각이 있으면 '감각'이라고 이름 붙이세요.",
                    "더 구체적으로 '계획', '걱정', '판단', '슬픔', '따뜻함' 등으로 이름 붙일 수 있어요.",
                    "이름을 붙인 후, 다시 호흡으로 돌아오세요."
                ],
                duration_minutes=5,
                when_to_use=["명상 중", "생각이 많을 때", "감정 인식 연습"]
            )
        }

    def get_exercise(self, exercise_type: MindfulnessExerciseType) -> MindfulnessExercise:
        """특정 마음챙김 운동 반환"""
        return self.exercises.get(exercise_type)


class MindfulnessTriggerDetector:
    """마음챙김/명상 필요 상황 감지"""

    def __init__(self):
        self.overwhelm_keywords = [
            "머리가 복잡", "생각이 많", "정신없", "너무 바빠",
            "휘몰아", "감당이 안", "멈출 수가 없"
        ]

        self.stress_keywords = [
            "스트레스", "지쳤", "피곤", "지침", "힘들",
            "쉬고 싶", "여유가 없"
        ]

        self.racing_thoughts_keywords = [
            "생각이 멈추지 않", "머릿속이 시끄러", "계속 돌아",
            "잠이 안", "걱정이 멈추지"
        ]

        self.disconnection_keywords = [
            "현실감이", "몸이 내 것 같지", "멍하", "무감각",
            "느껴지지 않"
        ]

    def detect(self, message: str, emotion_context: Optional[Dict] = None) -> Dict[str, Any]:
        """마음챙김/명상 필요 상황 감지"""
        message_lower = message.lower()

        triggers = {
            "overwhelm": self._check_keywords(message_lower, self.overwhelm_keywords),
            "stress": self._check_keywords(message_lower, self.stress_keywords),
            "racing_thoughts": self._check_keywords(message_lower, self.racing_thoughts_keywords),
            "disconnection": self._check_keywords(message_lower, self.disconnection_keywords)
        }

        # 추천 결정
        recommended = self._recommend_practice(triggers)

        return {
            "should_suggest": any(t["detected"] for t in triggers.values()),
            "triggers": triggers,
            "recommended_type": recommended["type"],
            "recommended_exercise": recommended["exercise"],
            "urgency": self._assess_urgency(triggers)
        }

    def _check_keywords(self, message: str, keywords: List[str]) -> Dict[str, Any]:
        """키워드 매칭"""
        matches = [kw for kw in keywords if kw in message]
        return {
            "detected": len(matches) > 0,
            "matches": matches,
            "confidence": min(len(matches) * 0.3, 0.9)
        }

    def _recommend_practice(self, triggers: Dict) -> Dict[str, Any]:
        """연습 추천"""
        if triggers["disconnection"]["detected"]:
            return {
                "type": MeditationType.BODY_AWARENESS,
                "exercise": MindfulnessExerciseType.STOP
            }
        elif triggers["racing_thoughts"]["detected"]:
            return {
                "type": MeditationType.OBSERVING_THOUGHTS,
                "exercise": MindfulnessExerciseType.RAIN
            }
        elif triggers["overwhelm"]["detected"]:
            return {
                "type": MeditationType.MINDFUL_BREATHING,
                "exercise": MindfulnessExerciseType.THREE_STEP
            }
        elif triggers["stress"]["detected"]:
            return {
                "type": MeditationType.PRESENT_MOMENT,
                "exercise": MindfulnessExerciseType.MINDFUL_PAUSE
            }

        return {
            "type": MeditationType.MINDFUL_BREATHING,
            "exercise": MindfulnessExerciseType.STOP
        }

    def _assess_urgency(self, triggers: Dict) -> str:
        """긴급도 평가"""
        detected_count = sum(1 for t in triggers.values() if t["detected"])
        if detected_count >= 2:
            return "high"
        elif detected_count == 1:
            return "medium"
        return "low"


class IntegratedMindfulnessChat:
    """채팅 통합형 마음챙김/명상 시스템"""

    def __init__(self):
        self.trigger_detector = MindfulnessTriggerDetector()
        self.meditation_library = MeditationLibrary()
        self.exercise_library = MindfulnessExerciseLibrary()
        self.active_sessions: Dict[str, MeditationSession] = {}

    def process_message(
        self,
        session_id: str,
        user_message: str,
        emotion_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """사용자 메시지 처리"""

        # 진행 중인 세션 확인
        if session_id in self.active_sessions:
            return self._handle_active_session(session_id, user_message)

        # 마음챙김/명상 필요 상황 감지
        trigger_result = self.trigger_detector.detect(user_message, emotion_context)

        if trigger_result["should_suggest"]:
            return self._suggest_mindfulness(session_id, trigger_result)

        return {
            "mindfulness_suggested": False,
            "response": None,
            "continue_conversation": True
        }

    def _suggest_mindfulness(
        self,
        session_id: str,
        trigger_result: Dict
    ) -> Dict[str, Any]:
        """마음챙김/명상 제안"""
        meditation_type = trigger_result["recommended_type"]
        exercise_type = trigger_result["recommended_exercise"]

        script = self.meditation_library.get_script(meditation_type)
        exercise = self.exercise_library.get_exercise(exercise_type)

        response = f"""마음이 많이 분주하시군요. 💭

🧘 잠시 **마음챙김**을 해보시는 건 어떨까요?

**빠른 방법** (1분):
{exercise.name} - {exercise.steps[0][:50]}...

**깊은 방법** ({script.duration_minutes}분):
{script.name} - {script.introduction[:50]}...

어떤 것을 해보시겠어요?
('빠른', '깊은', 또는 '아니요'로 답해주세요)"""

        return {
            "mindfulness_suggested": True,
            "meditation_type": meditation_type.value,
            "exercise_type": exercise_type.value,
            "response": response,
            "continue_conversation": True,
            "awaiting_choice": True
        }

    def start_quick_exercise(
        self,
        session_id: str,
        user_id: str,
        exercise_type: MindfulnessExerciseType
    ) -> Dict[str, Any]:
        """빠른 마음챙김 운동 시작"""
        exercise = self.exercise_library.get_exercise(exercise_type)

        if not exercise:
            return {"error": "운동을 찾을 수 없습니다."}

        # 약어 설명 포함
        acronym_text = ""
        if exercise.acronym_meaning:
            acronym_text = "\n\n**" + exercise.name + " 의미:**\n"
            for letter, meaning in exercise.acronym_meaning.items():
                acronym_text += f"• **{letter}**: {meaning}\n"

        steps_text = "\n\n".join(exercise.steps)

        response = f"""🧘 **{exercise.name}** 시작합니다!

⏱️ 약 {exercise.duration_minutes}분 소요
{acronym_text}
---

{steps_text}

---

어떠셨나요? 마음이 조금 가라앉으셨나요? 💙"""

        return {
            "exercise_completed": True,
            "exercise_type": exercise_type.value,
            "response": response,
            "continue_conversation": True
        }

    def start_meditation(
        self,
        session_id: str,
        user_id: str,
        meditation_type: MeditationType
    ) -> Dict[str, Any]:
        """명상 세션 시작"""
        script = self.meditation_library.get_script(meditation_type)

        if not script:
            return {"error": "명상 스크립트를 찾을 수 없습니다."}

        # 세션 생성
        self.active_sessions[session_id] = MeditationSession(
            session_id=session_id,
            user_id=user_id,
            meditation_type=meditation_type
        )

        response = f"""🧘 **{script.name}** 시작합니다.

⏱️ 약 {script.duration_minutes}분 소요

**준비하기:**
{script.introduction}

준비가 되시면 '시작'이라고 말씀해 주세요.
(언제든 '멈춤' 또는 '종료'라고 하시면 중단할 수 있어요)"""

        return {
            "session_started": True,
            "meditation_type": meditation_type.value,
            "duration": script.duration_minutes,
            "response": response,
            "continue_conversation": True
        }

    def _handle_active_session(
        self,
        session_id: str,
        user_message: str
    ) -> Dict[str, Any]:
        """진행 중인 세션 처리"""
        session = self.active_sessions[session_id]
        message_lower = user_message.lower().strip()

        # 중단/종료
        if any(word in message_lower for word in ["종료", "그만", "stop", "멈춤"]):
            return self._end_session(session_id, interrupted=True)

        # 일시정지
        if "멈춤" in message_lower or "pause" in message_lower:
            session.paused = True
            return {
                "response": "잠시 멈추었습니다. 계속하시려면 '계속'이라고 말씀해 주세요.",
                "paused": True,
                "continue_conversation": True
            }

        # 계속
        if session.paused and any(word in message_lower for word in ["계속", "continue"]):
            session.paused = False
            return self._get_next_instruction(session_id)

        # 시작 또는 다음 단계
        if any(word in message_lower for word in ["시작", "네", "다음", "응"]):
            return self._get_next_instruction(session_id)

        return {
            "response": "천천히 진행하세요. 준비되시면 말씀해 주세요.",
            "continue_conversation": True
        }

    def _get_next_instruction(self, session_id: str) -> Dict[str, Any]:
        """다음 명상 안내"""
        session = self.active_sessions[session_id]
        script = self.meditation_library.get_script(session.meditation_type)

        # 모든 단계 완료 확인
        if session.current_step >= len(script.main_practice):
            return self._complete_session(session_id)

        # 현재 단계 안내
        instruction = script.main_practice[session.current_step]
        session.current_step += 1

        progress = f"[{session.current_step}/{len(script.main_practice)}]"

        response = f"""**{progress}**

{instruction}

...(잠시 머물러 주세요)...

준비되시면 '다음'이라고 말씀해 주세요."""

        return {
            "response": response,
            "current_step": session.current_step,
            "total_steps": len(script.main_practice),
            "continue_conversation": True
        }

    def _complete_session(self, session_id: str) -> Dict[str, Any]:
        """세션 완료"""
        session = self.active_sessions[session_id]
        script = self.meditation_library.get_script(session.meditation_type)

        response = f"""**마무리**

{script.closing}

🎉 **{script.name}**을 완료하셨습니다!

**이 명상의 효과:**
{chr(10).join(['• ' + b for b in script.benefits])}

어떠셨나요? 지금 기분을 말씀해 주세요. 💙"""

        # 세션 정리
        del self.active_sessions[session_id]

        return {
            "response": response,
            "session_completed": True,
            "meditation_type": session.meditation_type.value,
            "continue_conversation": True
        }

    def _end_session(self, session_id: str, interrupted: bool = False) -> Dict[str, Any]:
        """세션 종료"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

        if interrupted:
            response = """괜찮아요, 언제든 다시 할 수 있어요.
짧은 시간이라도 마음을 돌보셨다는 게 중요해요. 💙

계속 이야기를 나눠볼까요?"""
        else:
            response = "명상을 마쳤습니다. 이야기를 계속해 볼까요?"

        return {
            "response": response,
            "session_ended": True,
            "interrupted": interrupted,
            "continue_conversation": True
        }

    def get_daily_mindfulness_tip(self) -> str:
        """오늘의 마음챙김 팁"""
        tips = [
            "☕ 커피나 차를 마실 때, 첫 모금의 맛과 온기에 온전히 집중해 보세요.",
            "🚶 걸을 때 발바닥이 땅에 닿는 감각을 느껴보세요.",
            "🌅 아침에 눈을 뜨면, 3번 깊은 호흡을 하고 하루를 시작해 보세요.",
            "🍽️ 식사 첫 세 입을 천천히, 맛에 집중하며 먹어보세요.",
            "📱 핸드폰을 보기 전에, 한 번 깊이 숨을 쉬어보세요.",
            "🔔 알람이나 전화가 올 때, 바로 반응하지 말고 한 번 숨을 쉬어보세요.",
            "🧼 손을 씻을 때, 물의 온도와 비누 거품의 감각에 집중해 보세요.",
            "🌳 창밖을 바라보며 30초 동안 자연을 관찰해 보세요.",
            "😊 하루에 세 번, '지금 여기'라고 속으로 말하며 현재를 인식해 보세요.",
            "🛏️ 잠자리에 들 때, 오늘 감사한 것 세 가지를 떠올려 보세요."
        ]
        return random.choice(tips)

    def list_meditations(self) -> List[Dict]:
        """사용 가능한 명상 목록"""
        meditations = []
        for med_type, script in self.meditation_library.scripts.items():
            meditations.append({
                "type": med_type.value,
                "name": script.name,
                "duration": script.duration_minutes,
                "suitable_for": script.suitable_for,
                "benefits": script.benefits
            })
        return meditations

    def list_quick_exercises(self) -> List[Dict]:
        """빠른 마음챙김 운동 목록"""
        exercises = []
        for ex_type, exercise in self.exercise_library.exercises.items():
            exercises.append({
                "type": ex_type.value,
                "name": exercise.name,
                "duration": exercise.duration_minutes,
                "when_to_use": exercise.when_to_use
            })
        return exercises


# 사용 예시
if __name__ == "__main__":
    system = IntegratedMindfulnessChat()

    # 감지 테스트
    result = system.process_message(
        "session_1",
        "머릿속이 너무 시끄러워요. 생각이 멈추지 않아서 잠도 못 자겠어요."
    )
    print("=== 마음챙김 제안 ===")
    print(result["response"])

    # 빠른 운동
    print("\n=== STOP 기법 ===")
    quick = system.start_quick_exercise(
        "session_1",
        "user_1",
        MindfulnessExerciseType.STOP
    )
    print(quick["response"])

    # 오늘의 팁
    print("\n=== 오늘의 마음챙김 팁 ===")
    print(system.get_daily_mindfulness_tip())

    # 명상 목록
    print("\n=== 사용 가능한 명상 ===")
    for med in system.list_meditations():
        print(f"- {med['name']} ({med['duration']}분)")
