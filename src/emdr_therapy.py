"""
EMDR (Eye Movement Desensitization and Reprocessing) 치료 지원 시스템
안구운동 민감소실 및 재처리 요법의 디지털 적응 구현

이 모듈은 EMDR의 8단계 프로토콜을 텍스트 기반 상담에 맞게 적응하여 제공합니다.
- 양측성 자극 (Bilateral Stimulation) 가이드
- SUDS/VOC 척도 추적
- 트라우마 기억 처리 프로토콜
- 안전 자원 개발
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import json
import re

logger = logging.getLogger(__name__)


# ============================================================================
# Part 1: EMDR 기본 구조 및 데이터 모델
# ============================================================================

class EMDRPhase(Enum):
    """EMDR 8단계 프로토콜"""
    HISTORY_TAKING = "history_taking"           # 1단계: 병력 청취 및 치료 계획
    PREPARATION = "preparation"                  # 2단계: 준비
    ASSESSMENT = "assessment"                    # 3단계: 평가
    DESENSITIZATION = "desensitization"         # 4단계: 둔감화
    INSTALLATION = "installation"                # 5단계: 주입
    BODY_SCAN = "body_scan"                     # 6단계: 신체 스캔
    CLOSURE = "closure"                          # 7단계: 종결
    REEVALUATION = "reevaluation"               # 8단계: 재평가


class BilateralStimulationType(Enum):
    """양측성 자극 유형"""
    BUTTERFLY_HUG = "butterfly_hug"             # 나비 포옹 (자가 탭핑)
    AUDIO_TONES = "audio_tones"                 # 교대 음향
    VISUAL_GUIDANCE = "visual_guidance"         # 시각적 안내
    TACTILE_TAPPING = "tactile_tapping"         # 촉각 탭핑
    BREATHING_BILATERAL = "breathing_bilateral" # 양측성 호흡


class TargetType(Enum):
    """처리 대상 유형"""
    PAST_TRAUMA = "past_trauma"                 # 과거 트라우마
    PRESENT_TRIGGER = "present_trigger"         # 현재 트리거
    FUTURE_TEMPLATE = "future_template"         # 미래 템플릿
    RESOURCE = "resource"                        # 자원 개발


class ProcessingStatus(Enum):
    """처리 상태"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    NEEDS_REPROCESSING = "needs_reprocessing"


@dataclass
class SUDSRating:
    """SUDS (Subjective Units of Disturbance Scale) 평가"""
    rating: int  # 0-10 척도
    timestamp: datetime = field(default_factory=datetime.now)
    context: str = ""

    def __post_init__(self):
        if not 0 <= self.rating <= 10:
            raise ValueError("SUDS 평가는 0-10 범위여야 합니다")


@dataclass
class VOCRating:
    """VOC (Validity of Cognition) 평가"""
    rating: int  # 1-7 척도
    timestamp: datetime = field(default_factory=datetime.now)
    cognition: str = ""

    def __post_init__(self):
        if not 1 <= self.rating <= 7:
            raise ValueError("VOC 평가는 1-7 범위여야 합니다")


@dataclass
class TargetMemory:
    """처리 대상 기억"""
    target_id: str
    description: str
    image: str  # 가장 고통스러운 이미지/장면
    negative_cognition: str  # 부정적 인지 (예: "나는 무력하다")
    positive_cognition: str  # 긍정적 인지 (예: "나는 통제할 수 있다")
    emotion: str  # 주요 감정
    body_sensation: str  # 신체 감각 위치
    target_type: TargetType = TargetType.PAST_TRAUMA

    suds_history: List[SUDSRating] = field(default_factory=list)
    voc_history: List[VOCRating] = field(default_factory=list)

    processing_status: ProcessingStatus = ProcessingStatus.NOT_STARTED
    sets_completed: int = 0
    notes: List[str] = field(default_factory=list)

    created_at: datetime = field(default_factory=datetime.now)
    last_processed: Optional[datetime] = None

    @property
    def current_suds(self) -> Optional[int]:
        return self.suds_history[-1].rating if self.suds_history else None

    @property
    def current_voc(self) -> Optional[int]:
        return self.voc_history[-1].rating if self.voc_history else None

    @property
    def initial_suds(self) -> Optional[int]:
        return self.suds_history[0].rating if self.suds_history else None

    def is_processed(self) -> bool:
        """처리 완료 여부 (SUDS 0-1, VOC 6-7)"""
        if not self.suds_history or not self.voc_history:
            return False
        return self.current_suds <= 1 and self.current_voc >= 6


@dataclass
class SafePlace:
    """안전한 장소 자원"""
    name: str
    description: str
    sensory_details: Dict[str, str]  # 감각별 세부사항
    cue_word: str  # 신호 단어
    strength: int = 5  # 1-10 강도
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Container:
    """컨테이너 기법 자원"""
    name: str
    description: str
    lock_mechanism: str  # 잠금 방식
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class EMDRSession:
    """EMDR 세션"""
    session_id: str
    user_id: str

    current_phase: EMDRPhase = EMDRPhase.HISTORY_TAKING
    current_target: Optional[TargetMemory] = None

    targets: List[TargetMemory] = field(default_factory=list)
    safe_place: Optional[SafePlace] = None
    container: Optional[Container] = None

    bilateral_preference: BilateralStimulationType = BilateralStimulationType.BUTTERFLY_HUG

    session_notes: List[Dict[str, Any]] = field(default_factory=list)

    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None

    def add_note(self, note: str, phase: Optional[EMDRPhase] = None):
        self.session_notes.append({
            "timestamp": datetime.now().isoformat(),
            "phase": (phase or self.current_phase).value,
            "note": note
        })


# ============================================================================
# Part 2: 양측성 자극 가이드 시스템
# ============================================================================

class BilateralStimulationGuide:
    """양측성 자극 안내 시스템"""

    def __init__(self):
        self.stimulation_scripts = self._load_stimulation_scripts()

    def _load_stimulation_scripts(self) -> Dict[BilateralStimulationType, Dict[str, Any]]:
        """자극 유형별 스크립트 로드"""
        return {
            BilateralStimulationType.BUTTERFLY_HUG: {
                "name": "나비 포옹",
                "korean_name": "나비 포옹 (Butterfly Hug)",
                "description": "자가 양측성 자극을 위한 나비 포옹 기법",
                "setup_instructions": [
                    "편안한 자세로 앉아주세요.",
                    "두 손을 가슴 위에 교차하여 올려놓으세요.",
                    "손가락 끝이 쇄골 아래에 닿도록 합니다.",
                    "마치 나비가 날개를 펴듯이 팔을 교차합니다."
                ],
                "execution_instructions": [
                    "이제 천천히 왼손, 오른손을 번갈아가며 가볍게 두드려주세요.",
                    "1... 2... 1... 2... 리듬을 유지하세요.",
                    "눈을 감아도 좋고, 편한 곳을 바라봐도 됩니다.",
                    "호흡은 자연스럽게 유지하세요."
                ],
                "set_duration": 25,  # 초
                "taps_per_set": 24,
                "tempo": "moderate"
            },

            BilateralStimulationType.TACTILE_TAPPING: {
                "name": "무릎 탭핑",
                "korean_name": "무릎 탭핑",
                "description": "무릎을 번갈아 두드리는 양측성 자극",
                "setup_instructions": [
                    "편안하게 앉아서 두 손을 무릎 위에 올려놓으세요.",
                    "어깨와 팔의 긴장을 풀어주세요."
                ],
                "execution_instructions": [
                    "왼쪽 무릎, 오른쪽 무릎을 번갈아 가볍게 두드려주세요.",
                    "일정한 리듬을 유지하세요.",
                    "너무 세게 두드리지 않아도 됩니다.",
                    "편안한 강도로 진행하세요."
                ],
                "set_duration": 25,
                "taps_per_set": 24,
                "tempo": "moderate"
            },

            BilateralStimulationType.BREATHING_BILATERAL: {
                "name": "양측성 호흡",
                "korean_name": "양측성 호흡",
                "description": "호흡과 결합한 양측성 자극",
                "setup_instructions": [
                    "편안한 자세를 취해주세요.",
                    "한 손은 가슴에, 다른 손은 배에 올려놓으세요."
                ],
                "execution_instructions": [
                    "숨을 들이쉴 때 왼쪽에 주의를 집중하세요.",
                    "숨을 내쉴 때 오른쪽에 주의를 집중하세요.",
                    "들이쉬기... 왼쪽... 내쉬기... 오른쪽...",
                    "천천히 반복합니다."
                ],
                "set_duration": 30,
                "breaths_per_set": 8,
                "tempo": "slow"
            },

            BilateralStimulationType.VISUAL_GUIDANCE: {
                "name": "시각 추적",
                "korean_name": "시각적 양측성 자극",
                "description": "눈 움직임을 통한 양측성 자극 (텍스트 가이드)",
                "setup_instructions": [
                    "머리는 고정한 채 눈만 움직여주세요.",
                    "편안하게 앉아 전방을 바라봅니다."
                ],
                "execution_instructions": [
                    "제가 안내하는 대로 눈을 움직여주세요.",
                    "왼쪽... 오른쪽... 왼쪽... 오른쪽...",
                    "머리는 움직이지 않고 눈만 움직입니다.",
                    "자연스러운 속도로 따라오세요."
                ],
                "set_duration": 25,
                "movements_per_set": 24,
                "tempo": "moderate"
            },

            BilateralStimulationType.AUDIO_TONES: {
                "name": "교대 음향",
                "korean_name": "양측성 청각 자극",
                "description": "이어폰을 통한 교대 음향 자극 (안내)",
                "setup_instructions": [
                    "이어폰이나 헤드폰을 착용해주세요.",
                    "양쪽 귀에서 소리가 잘 들리는지 확인합니다.",
                    "볼륨은 편안한 수준으로 조절하세요."
                ],
                "execution_instructions": [
                    "왼쪽, 오른쪽 귀에서 번갈아 소리가 들립니다.",
                    "소리를 따라가며 집중해주세요.",
                    "눈을 감고 진행해도 좋습니다."
                ],
                "set_duration": 25,
                "tones_per_set": 24,
                "tempo": "moderate"
            }
        }

    def get_setup_guide(self, stim_type: BilateralStimulationType) -> str:
        """자극 준비 안내 생성"""
        script = self.stimulation_scripts[stim_type]

        guide = f"## {script['korean_name']} 준비\n\n"
        guide += f"{script['description']}\n\n"
        guide += "### 준비 단계:\n"

        for i, instruction in enumerate(script['setup_instructions'], 1):
            guide += f"{i}. {instruction}\n"

        return guide

    def get_execution_guide(self, stim_type: BilateralStimulationType,
                           set_number: int = 1) -> str:
        """자극 실행 안내 생성"""
        script = self.stimulation_scripts[stim_type]

        guide = f"### 세트 {set_number} 시작\n\n"

        for instruction in script['execution_instructions']:
            guide += f"- {instruction}\n"

        guide += f"\n*약 {script['set_duration']}초간 진행합니다.*\n"
        guide += "\n준비되시면 시작하겠습니다. '시작'이라고 말씀해주세요."

        return guide

    def generate_bilateral_sequence(self, stim_type: BilateralStimulationType,
                                   duration_seconds: int = 25) -> List[str]:
        """양측성 자극 시퀀스 생성"""
        script = self.stimulation_scripts[stim_type]
        sequence = []

        if stim_type == BilateralStimulationType.BUTTERFLY_HUG:
            for i in range(script['taps_per_set']):
                side = "왼쪽" if i % 2 == 0 else "오른쪽"
                sequence.append(f"탭... {side}")

        elif stim_type == BilateralStimulationType.BREATHING_BILATERAL:
            for i in range(script['breaths_per_set']):
                sequence.append("들이쉬며... 왼쪽 집중...")
                sequence.append("내쉬며... 오른쪽 집중...")

        elif stim_type == BilateralStimulationType.VISUAL_GUIDANCE:
            for i in range(script['movements_per_set']):
                side = "◀ 왼쪽" if i % 2 == 0 else "오른쪽 ▶"
                sequence.append(side)

        return sequence

    def get_completion_message(self, set_number: int) -> str:
        """세트 완료 메시지"""
        return f"""
### 세트 {set_number} 완료

잠시 멈추고 심호흡을 해주세요.

지금 떠오르는 것이 있나요?
- 이미지, 생각, 감정, 신체 감각 무엇이든 말씀해주세요.
- 아무것도 떠오르지 않아도 괜찮습니다.

현재 느끼시는 것을 편하게 나눠주세요.
"""


# ============================================================================
# Part 3: EMDR 프로토콜 가이드
# ============================================================================

class EMDRProtocolGuide:
    """EMDR 8단계 프로토콜 가이드"""

    def __init__(self):
        self.phase_scripts = self._load_phase_scripts()
        self.negative_cognitions = self._load_negative_cognitions()
        self.positive_cognitions = self._load_positive_cognitions()

    def _load_phase_scripts(self) -> Dict[EMDRPhase, Dict[str, Any]]:
        """단계별 스크립트"""
        return {
            EMDRPhase.HISTORY_TAKING: {
                "name": "1단계: 병력 청취 및 치료 계획",
                "goals": [
                    "트라우마 경험 파악",
                    "현재 증상 평가",
                    "처리 대상 선정",
                    "자원 및 안정화 필요성 평가"
                ],
                "key_questions": [
                    "어떤 경험이 현재 가장 힘드시나요?",
                    "그 경험을 떠올릴 때 어떤 감정이 드시나요?",
                    "일상생활에 어떤 영향을 미치고 있나요?",
                    "이전에 비슷한 치료를 받아보신 적이 있으신가요?"
                ],
                "screening_questions": [
                    "현재 정신과 약물을 복용 중이신가요?",
                    "해리 증상(기억 공백, 비현실감)을 경험하시나요?",
                    "자해나 자살에 대한 생각이 있으신가요?",
                    "현재 안전한 생활환경에 계신가요?"
                ]
            },

            EMDRPhase.PREPARATION: {
                "name": "2단계: 준비",
                "goals": [
                    "EMDR 과정 설명",
                    "안전한 장소 개발",
                    "컨테이너 기법 학습",
                    "양측성 자극 연습"
                ],
                "explanation_script": """
EMDR(안구운동 민감소실 및 재처리)은 트라우마 기억을 처리하는 효과적인 치료법입니다.

이 과정에서는:
1. 힘든 기억을 떠올리면서
2. 양측성 자극(나비 포옹 등)을 함께 진행합니다
3. 이를 통해 기억이 자연스럽게 처리됩니다

처리 과정에서 다양한 생각, 감정, 이미지가 떠오를 수 있습니다.
이는 모두 정상적인 반응이며, 안전한 환경에서 진행됩니다.

언제든 멈추고 싶으시면 말씀해주세요.
""",
                "safe_place_script": """
### 안전한 장소 만들기

지금부터 마음속에 안전하고 평화로운 장소를 만들어볼 거예요.

1. 눈을 감고 편안한 호흡을 해주세요.
2. 당신이 완전히 안전하고 평화롭게 느껴지는 장소를 떠올려보세요.
   - 실제 장소여도 좋고, 상상의 장소여도 좋습니다.
   - 다른 사람이 없는 곳이어도 좋습니다.

3. 그 장소에서:
   - 무엇이 보이나요? (색깔, 모양, 빛)
   - 무슨 소리가 들리나요?
   - 어떤 냄새가 나나요?
   - 피부에 어떤 느낌이 드나요?
   - 기온은 어떤가요?

4. 이 장소에 어울리는 단어나 이름을 붙여주세요.

천천히 설명해주시겠어요?
"""
            },

            EMDRPhase.ASSESSMENT: {
                "name": "3단계: 평가",
                "goals": [
                    "처리 대상 기억 명확화",
                    "부정적 인지 파악",
                    "긍정적 인지 설정",
                    "SUDS/VOC 기준선 측정"
                ],
                "target_identification": """
### 처리 대상 기억 확인

처리하고자 하는 기억에 대해 구체적으로 살펴보겠습니다.

1. **이미지**: 그 경험에서 가장 힘든 장면이나 이미지는 무엇인가요?
   (한 장의 사진처럼 떠오르는 장면)

2. **부정적 생각**: 그 이미지를 볼 때, 자신에 대해 어떤 부정적인 생각이 드나요?
   예: "나는 무력하다", "나는 안전하지 않다", "내 잘못이다"

3. **원하는 생각**: 대신 자신에 대해 어떤 생각을 믿고 싶으신가요?
   예: "나는 통제할 수 있다", "나는 이제 안전하다", "나는 최선을 다했다"

4. **감정**: 그 이미지와 부정적 생각을 떠올릴 때 어떤 감정이 드나요?
   (불안, 슬픔, 분노, 수치심, 두려움 등)

5. **신체 감각**: 그 감정이 몸의 어디에서 느껴지나요?
   (가슴, 목, 배, 어깨 등)
""",
                "suds_instruction": """
### SUDS 척도 (주관적 고통 단위)

지금 그 이미지와 부정적 생각을 떠올릴 때,
얼마나 고통스러우신가요?

0 = 전혀 고통스럽지 않음
5 = 중간 정도
10 = 최고로 고통스러움

0부터 10 사이의 숫자로 말씀해주세요.
""",
                "voc_instruction": """
### VOC 척도 (인지의 타당성)

긍정적 생각 "{positive_cognition}"을(를) 떠올려보세요.

지금 그 이미지를 떠올릴 때,
이 긍정적 생각이 얼마나 진실되게 느껴지나요?

1 = 전혀 진실되게 느껴지지 않음
4 = 중간 정도
7 = 완전히 진실되게 느껴짐

1부터 7 사이의 숫자로 말씀해주세요.
"""
            },

            EMDRPhase.DESENSITIZATION: {
                "name": "4단계: 둔감화",
                "goals": [
                    "SUDS를 0-1까지 낮추기",
                    "양측성 자극으로 기억 처리",
                    "떠오르는 연결고리 따라가기"
                ],
                "start_script": """
### 둔감화 단계 시작

이제 본격적인 처리 단계를 시작합니다.

1. 처음에 말씀하신 이미지를 떠올려주세요.
2. 부정적 생각 "{negative_cognition}"을(를) 마음속으로 말해주세요.
3. 감정과 신체 감각에 주의를 기울여주세요.
4. 그 상태로 양측성 자극을 시작하겠습니다.

떠오르는 것이 무엇이든 그냥 지켜봐주세요.
기차 창밖 풍경을 보듯이, 지나가게 두세요.

준비되셨나요?
""",
                "set_transition": """
잘하셨습니다. 심호흡을 하시고,

지금 무엇이 떠오르나요?
(이미지, 생각, 감정, 신체 감각 무엇이든)
""",
                "return_to_target": """
처음 기억으로 돌아가 볼게요.

처음 이미지를 떠올릴 때,
지금 SUDS는 몇인가요? (0-10)
""",
                "blocked_processing": """
처리가 잠시 멈춘 것 같습니다.

다음 중 도움이 될 수 있는 방법을 시도해볼까요?
1. 다른 양측성 자극 방식 시도
2. 인지적 개입 추가
3. 잠시 안전한 장소로 가기
4. 신체 감각에 집중하기

어떤 것이 좋으실까요?
"""
            },

            EMDRPhase.INSTALLATION: {
                "name": "5단계: 주입",
                "goals": [
                    "긍정적 인지 강화",
                    "VOC를 6-7까지 높이기"
                ],
                "script": """
### 긍정적 인지 주입

SUDS가 충분히 낮아졌습니다. 잘하셨습니다.

이제 긍정적 생각을 강화할 거예요.

1. 원래 기억/이미지를 떠올려주세요.
2. 긍정적 생각 "{positive_cognition}"을(를) 함께 떠올려주세요.
3. 그 상태로 양측성 자극을 진행하겠습니다.

이 긍정적 생각이 점점 더 진실되게 느껴질 거예요.

준비되셨나요?
""",
                "voc_check": """
원래 이미지와 함께
"{positive_cognition}"을(를) 떠올릴 때,

지금 VOC는 몇인가요? (1-7)
얼마나 진실되게 느껴지나요?
"""
            },

            EMDRPhase.BODY_SCAN: {
                "name": "6단계: 신체 스캔",
                "goals": [
                    "잔여 신체 긴장 확인",
                    "불편감 처리"
                ],
                "script": """
### 신체 스캔

거의 다 왔습니다.

1. 눈을 감고 원래 기억을 떠올려주세요.
2. 긍정적 생각 "{positive_cognition}"을(를) 함께 생각해주세요.
3. 이제 머리부터 발끝까지 천천히 스캔해주세요.

몸에 불편하거나 긴장되는 부분이 있나요?
어떤 신체 감각이든 말씀해주세요.
""",
                "clean_scan": """
신체에 특별한 불편감이 없다면,
처리가 잘 완료된 것입니다.

다음 단계인 종결로 넘어가겠습니다.
""",
                "residual_tension": """
그 신체 감각에 집중하면서
양측성 자극을 한 세트 더 진행하겠습니다.
"""
            },

            EMDRPhase.CLOSURE: {
                "name": "7단계: 종결",
                "goals": [
                    "세션 안전하게 마무리",
                    "안정화",
                    "후속 안내"
                ],
                "complete_processing_script": """
### 세션 완료

오늘 정말 잘하셨습니다.
기억이 성공적으로 처리되었습니다.

**세션 후 안내:**

1. **처리가 계속될 수 있습니다**
   - 꿈, 새로운 기억, 감정이 떠오를 수 있습니다
   - 이는 자연스러운 치유 과정입니다

2. **자기 돌봄**
   - 충분한 휴식을 취하세요
   - 물을 많이 마시세요
   - 무리한 일정은 피하세요

3. **필요시**
   - 안전한 장소 기법을 사용하세요
   - 컨테이너에 불편한 것을 담아두세요
   - 다음 세션에서 나눠주세요

오늘 가장 도움이 된 것은 무엇이었나요?
""",
                "incomplete_processing_script": """
### 세션 종결

오늘 세션을 마무리하겠습니다.

처리가 아직 완료되지 않았지만, 괜찮습니다.
다음 세션에서 이어서 진행할 수 있습니다.

**마무리하기 전에:**

1. 안전한 장소를 떠올려보세요.
   "{safe_place_name}"

2. 남은 불편한 것들이 있다면,
   컨테이너에 담아두겠습니다.

3. 심호흡을 세 번 해주세요.

지금 기분이 어떠세요?
""",
                "container_usage": """
### 컨테이너 기법

오늘 처리하지 못한 것들을 안전하게 보관하겠습니다.

1. "{container_name}"을(를) 떠올려주세요.
2. 남은 불편한 이미지, 생각, 감정을 그 안에 넣어주세요.
3. 단단히 잠가주세요: {lock_mechanism}
4. 다음 세션 때까지 안전하게 보관됩니다.

준비되셨나요?
"""
            },

            EMDRPhase.REEVALUATION: {
                "name": "8단계: 재평가",
                "goals": [
                    "이전 세션 처리 결과 확인",
                    "새로운 기억/연결고리 파악",
                    "치료 계획 조정"
                ],
                "script": """
### 재평가

지난 세션 이후 어떠셨나요?

1. **지난 세션에서 다룬 기억**
   - 그 기억을 떠올릴 때 지금 SUDS는 몇인가요?
   - 새로운 측면이 떠오르셨나요?

2. **세션 사이 경험**
   - 관련된 꿈을 꾸셨나요?
   - 새로운 기억이 떠올랐나요?
   - 일상에서 변화를 느끼셨나요?

3. **현재 상태**
   - 오늘 컨디션은 어떠신가요?
   - 다루고 싶은 것이 있으신가요?

천천히 말씀해주세요.
"""
            }
        }

    def _load_negative_cognitions(self) -> Dict[str, List[str]]:
        """부정적 인지 목록"""
        return {
            "responsibility": [
                "내 잘못이다",
                "나는 뭔가 잘못했어야 했다",
                "나는 막을 수 있었다",
                "나는 책임이 있다"
            ],
            "safety": [
                "나는 안전하지 않다",
                "나는 위험에 처해 있다",
                "나는 보호받지 못한다",
                "세상은 위험하다"
            ],
            "control": [
                "나는 무력하다",
                "나는 통제할 수 없다",
                "나는 갇혀 있다",
                "나는 선택권이 없다"
            ],
            "self_worth": [
                "나는 충분하지 않다",
                "나는 부족하다",
                "나는 사랑받을 자격이 없다",
                "나는 결함이 있다"
            ],
            "shame": [
                "나는 수치스럽다",
                "나는 더럽다",
                "나는 나쁜 사람이다",
                "나는 약하다"
            ]
        }

    def _load_positive_cognitions(self) -> Dict[str, List[str]]:
        """긍정적 인지 목록"""
        return {
            "responsibility": [
                "나는 최선을 다했다",
                "나는 배우고 성장한다",
                "나는 책임을 적절히 진다",
                "나는 당시 할 수 있는 일을 했다"
            ],
            "safety": [
                "나는 이제 안전하다",
                "나는 스스로를 보호할 수 있다",
                "위험은 지나갔다",
                "나는 안전한 선택을 할 수 있다"
            ],
            "control": [
                "나는 선택할 수 있다",
                "나는 통제할 수 있다",
                "나는 도움을 요청할 수 있다",
                "나는 내 삶을 관리할 수 있다"
            ],
            "self_worth": [
                "나는 충분하다",
                "나는 가치 있다",
                "나는 사랑받을 자격이 있다",
                "나는 있는 그대로 괜찮다"
            ],
            "shame": [
                "나는 괜찮은 사람이다",
                "나는 존중받을 자격이 있다",
                "나는 용기 있는 사람이다",
                "나는 내 자신을 수용한다"
            ]
        }

    def get_phase_guide(self, phase: EMDRPhase) -> Dict[str, Any]:
        """단계별 가이드 반환"""
        return self.phase_scripts[phase]

    def get_cognition_suggestions(self, category: str,
                                  cognition_type: str = "negative") -> List[str]:
        """인지 제안 목록"""
        if cognition_type == "negative":
            return self.negative_cognitions.get(category, [])
        return self.positive_cognitions.get(category, [])

    def identify_cognition_category(self, cognition: str) -> Optional[str]:
        """인지 카테고리 식별"""
        keywords = {
            "responsibility": ["잘못", "책임", "막", "했어야"],
            "safety": ["안전", "위험", "보호", "두려"],
            "control": ["무력", "통제", "갇", "선택"],
            "self_worth": ["충분", "부족", "자격", "가치"],
            "shame": ["수치", "더럽", "나쁜", "약"]
        }

        for category, kw_list in keywords.items():
            for kw in kw_list:
                if kw in cognition:
                    return category
        return None


# ============================================================================
# Part 4: 안전 자원 개발 시스템
# ============================================================================

class ResourceDevelopmentSystem:
    """EMDR 안전 자원 개발 시스템"""

    def __init__(self):
        self.resource_scripts = self._load_resource_scripts()

    def _load_resource_scripts(self) -> Dict[str, Dict[str, Any]]:
        """자원 개발 스크립트"""
        return {
            "safe_place": {
                "name": "안전한 장소",
                "purpose": "정서적 안정과 안전감 제공",
                "development_steps": [
                    {
                        "step": "장소 선택",
                        "prompt": "당신이 완전히 안전하고 평화롭게 느껴지는 장소를 떠올려보세요. 실제 장소여도 좋고, 상상의 장소여도 좋습니다."
                    },
                    {
                        "step": "시각화",
                        "prompt": "그 장소에서 무엇이 보이나요? 색깔, 빛, 모양을 자세히 묘사해주세요."
                    },
                    {
                        "step": "청각",
                        "prompt": "그 장소에서 어떤 소리가 들리나요? 또는 고요한가요?"
                    },
                    {
                        "step": "촉각/온도",
                        "prompt": "피부에 어떤 느낌이 드나요? 온도는 어떤가요?"
                    },
                    {
                        "step": "후각",
                        "prompt": "어떤 향기가 나나요?"
                    },
                    {
                        "step": "신체 감각",
                        "prompt": "이 장소에서 몸이 어떻게 느껴지나요? 편안한 곳이 있나요?"
                    },
                    {
                        "step": "신호 단어",
                        "prompt": "이 장소를 나타내는 단어나 이름을 하나 정해주세요."
                    },
                    {
                        "step": "강화",
                        "prompt": "그 장소와 신호 단어를 떠올리며 양측성 자극을 진행합니다."
                    }
                ],
                "strengthening_protocol": """
안전한 장소 강화하기:

1. 눈을 감고 "{safe_place_name}"을(를) 떠올려주세요.
2. 모든 감각을 활성화해주세요.
3. 이 상태에서 나비 포옹을 4-6세트 진행합니다.
4. 매 세트마다 이미지가 더 선명해지고,
   안전한 느낌이 더 강해집니다.

준비되셨나요?
"""
            },

            "container": {
                "name": "컨테이너",
                "purpose": "불편한 감정/기억을 일시적으로 안전하게 보관",
                "development_steps": [
                    {
                        "step": "용기 선택",
                        "prompt": "불편한 것들을 담아둘 수 있는 튼튼한 용기를 상상해보세요. 금고, 상자, 창고, 동굴 등 어떤 것이든 괜찮습니다."
                    },
                    {
                        "step": "외관 설명",
                        "prompt": "그 용기는 어떻게 생겼나요? 크기, 색깔, 재질을 설명해주세요."
                    },
                    {
                        "step": "잠금 장치",
                        "prompt": "어떤 방식으로 잠기나요? 열쇠, 비밀번호, 마법 등"
                    },
                    {
                        "step": "위치",
                        "prompt": "이 용기는 어디에 있나요? 당신만 아는 곳인가요?"
                    },
                    {
                        "step": "연습",
                        "prompt": "가벼운 불편함 하나를 넣어보겠습니다. 잘 담기나요?"
                    }
                ],
                "usage_protocol": """
컨테이너 사용하기:

1. "{container_name}"을(를) 떠올려주세요.
2. 불편한 것(이미지, 감정, 생각)을 그 안에 넣어주세요.
3. "{lock_mechanism}"(으)로 단단히 잠가주세요.
4. 필요할 때까지 안전하게 보관됩니다.
5. 다음 세션에서 꺼내어 처리할 수 있습니다.

모든 것을 담으셨나요?
"""
            },

            "calm_place": {
                "name": "평화로운 장소",
                "purpose": "이완과 평온함 유도",
                "development_steps": [
                    {
                        "step": "장소 선택",
                        "prompt": "깊은 평화와 이완을 느끼는 장소를 떠올려보세요."
                    },
                    {
                        "step": "감각 상세화",
                        "prompt": "오감으로 그 장소를 느껴보세요."
                    },
                    {
                        "step": "신체 이완",
                        "prompt": "그 장소에서 몸이 어떻게 이완되나요?"
                    },
                    {
                        "step": "신호 단어",
                        "prompt": "평화를 나타내는 단어를 정해주세요."
                    }
                ]
            },

            "protective_figure": {
                "name": "보호자/지지자",
                "purpose": "보호와 지지를 받는 느낌 강화",
                "development_steps": [
                    {
                        "step": "인물 선택",
                        "prompt": "당신을 보호하고 지지해주는 인물을 떠올려보세요. 실제 인물, 상상의 인물, 영적 존재 모두 괜찮습니다."
                    },
                    {
                        "step": "모습 설명",
                        "prompt": "그 분은 어떻게 생겼나요?"
                    },
                    {
                        "step": "함께 있는 느낌",
                        "prompt": "그 분과 함께 있을 때 어떤 느낌이 드나요?"
                    },
                    {
                        "step": "지지의 말",
                        "prompt": "그 분이 당신에게 해주시는 말은 무엇인가요?"
                    },
                    {
                        "step": "연결 강화",
                        "prompt": "그 분의 존재를 느끼며 양측성 자극을 진행합니다."
                    }
                ]
            },

            "light_stream": {
                "name": "빛의 흐름",
                "purpose": "신체적 긴장과 불편감 해소",
                "protocol": """
빛의 흐름 기법:

1. 편안하게 앉아 눈을 감아주세요.
2. 불편한 신체 감각이 있는 곳에 주의를 기울여주세요.
3. 그 감각을 색깔, 모양, 크기로 표현해보세요.
4. 이제 머리 위에서 치유의 빛이 내려온다고 상상하세요.
5. 그 빛의 색깔을 선택하세요 - 가장 치유적인 색깔로.
6. 빛이 천천히 불편한 부분으로 흘러가요.
7. 빛이 닿는 곳마다 불편함이 녹아 없어집니다.
8. 불편함이 빛과 함께 몸 밖으로 빠져나갑니다.
9. 계속해서 빛이 그 부분을 채웁니다.

어떤 색깔의 빛이 좋으실까요?
"""
            }
        }

    def create_safe_place(self, user_responses: Dict[str, str]) -> SafePlace:
        """안전한 장소 생성"""
        return SafePlace(
            name=user_responses.get("cue_word", "나의 안전한 장소"),
            description=user_responses.get("description", ""),
            sensory_details={
                "visual": user_responses.get("visual", ""),
                "auditory": user_responses.get("auditory", ""),
                "tactile": user_responses.get("tactile", ""),
                "olfactory": user_responses.get("olfactory", ""),
                "body": user_responses.get("body", "")
            },
            cue_word=user_responses.get("cue_word", "안전"),
            strength=user_responses.get("strength", 5)
        )

    def create_container(self, user_responses: Dict[str, str]) -> Container:
        """컨테이너 생성"""
        return Container(
            name=user_responses.get("name", "나의 컨테이너"),
            description=user_responses.get("description", ""),
            lock_mechanism=user_responses.get("lock", "단단한 잠금장치")
        )

    def get_resource_development_guide(self, resource_type: str) -> Dict[str, Any]:
        """자원 개발 가이드"""
        return self.resource_scripts.get(resource_type, {})

    def strengthen_resource(self, resource_type: str,
                           resource_details: Dict[str, str]) -> str:
        """자원 강화 프로토콜 생성"""
        if resource_type == "safe_place":
            return self.resource_scripts["safe_place"]["strengthening_protocol"].format(
                safe_place_name=resource_details.get("name", "안전한 장소")
            )
        elif resource_type == "container":
            return self.resource_scripts["container"]["usage_protocol"].format(
                container_name=resource_details.get("name", "컨테이너"),
                lock_mechanism=resource_details.get("lock", "잠금장치")
            )
        return ""


# ============================================================================
# Part 5: 통합 EMDR 치료 시스템
# ============================================================================

class IntegratedEMDRTherapySystem:
    """통합 EMDR 치료 시스템"""

    def __init__(self):
        self.bilateral_guide = BilateralStimulationGuide()
        self.protocol_guide = EMDRProtocolGuide()
        self.resource_system = ResourceDevelopmentSystem()

        self.active_sessions: Dict[str, EMDRSession] = {}
        self.completed_sessions: List[EMDRSession] = []

    def create_session(self, user_id: str, session_id: Optional[str] = None) -> EMDRSession:
        """새 EMDR 세션 생성"""
        if session_id is None:
            session_id = f"emdr_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        session = EMDRSession(
            session_id=session_id,
            user_id=user_id
        )

        self.active_sessions[session_id] = session
        logger.info(f"EMDR 세션 생성: {session_id}")

        return session

    def get_session(self, session_id: str) -> Optional[EMDRSession]:
        """세션 조회"""
        return self.active_sessions.get(session_id)

    def advance_phase(self, session_id: str) -> Tuple[EMDRPhase, str]:
        """다음 단계로 진행"""
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"세션을 찾을 수 없습니다: {session_id}")

        phase_order = list(EMDRPhase)
        current_index = phase_order.index(session.current_phase)

        if current_index < len(phase_order) - 1:
            session.current_phase = phase_order[current_index + 1]
            session.add_note(f"단계 진행: {session.current_phase.value}")

        guide = self.protocol_guide.get_phase_guide(session.current_phase)
        return session.current_phase, guide["name"]

    def set_phase(self, session_id: str, phase: EMDRPhase) -> Dict[str, Any]:
        """특정 단계로 설정"""
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"세션을 찾을 수 없습니다: {session_id}")

        session.current_phase = phase
        session.add_note(f"단계 설정: {phase.value}")

        return self.protocol_guide.get_phase_guide(phase)

    def create_target(self, session_id: str, target_data: Dict[str, Any]) -> TargetMemory:
        """처리 대상 생성"""
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"세션을 찾을 수 없습니다: {session_id}")

        target = TargetMemory(
            target_id=f"target_{len(session.targets) + 1}",
            description=target_data.get("description", ""),
            image=target_data.get("image", ""),
            negative_cognition=target_data.get("negative_cognition", ""),
            positive_cognition=target_data.get("positive_cognition", ""),
            emotion=target_data.get("emotion", ""),
            body_sensation=target_data.get("body_sensation", ""),
            target_type=target_data.get("target_type", TargetType.PAST_TRAUMA)
        )

        session.targets.append(target)
        session.current_target = target
        session.add_note(f"대상 생성: {target.target_id}")

        return target

    def record_suds(self, session_id: str, rating: int,
                   context: str = "") -> SUDSRating:
        """SUDS 기록"""
        session = self.active_sessions.get(session_id)
        if not session or not session.current_target:
            raise ValueError("활성 세션 또는 대상이 없습니다")

        suds = SUDSRating(rating=rating, context=context)
        session.current_target.suds_history.append(suds)
        session.add_note(f"SUDS 기록: {rating}")

        return suds

    def record_voc(self, session_id: str, rating: int) -> VOCRating:
        """VOC 기록"""
        session = self.active_sessions.get(session_id)
        if not session or not session.current_target:
            raise ValueError("활성 세션 또는 대상이 없습니다")

        target = session.current_target
        voc = VOCRating(rating=rating, cognition=target.positive_cognition)
        target.voc_history.append(voc)
        session.add_note(f"VOC 기록: {rating}")

        return voc

    def run_bilateral_set(self, session_id: str, set_number: int = 1) -> Dict[str, Any]:
        """양측성 자극 세트 실행"""
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"세션을 찾을 수 없습니다: {session_id}")

        stim_type = session.bilateral_preference

        result = {
            "set_number": set_number,
            "stimulation_type": stim_type.value,
            "setup_guide": self.bilateral_guide.get_setup_guide(stim_type) if set_number == 1 else None,
            "execution_guide": self.bilateral_guide.get_execution_guide(stim_type, set_number),
            "sequence": self.bilateral_guide.generate_bilateral_sequence(stim_type),
            "completion_message": self.bilateral_guide.get_completion_message(set_number)
        }

        if session.current_target:
            session.current_target.sets_completed += 1
            session.current_target.last_processed = datetime.now()

        session.add_note(f"양측성 자극 세트 {set_number} 완료")

        return result

    def setup_safe_place(self, session_id: str,
                        responses: Dict[str, str]) -> SafePlace:
        """안전한 장소 설정"""
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"세션을 찾을 수 없습니다: {session_id}")

        safe_place = self.resource_system.create_safe_place(responses)
        session.safe_place = safe_place
        session.add_note(f"안전한 장소 생성: {safe_place.name}")

        return safe_place

    def setup_container(self, session_id: str,
                       responses: Dict[str, str]) -> Container:
        """컨테이너 설정"""
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"세션을 찾을 수 없습니다: {session_id}")

        container = self.resource_system.create_container(responses)
        session.container = container
        session.add_note(f"컨테이너 생성: {container.name}")

        return container

    def check_processing_status(self, session_id: str) -> Dict[str, Any]:
        """처리 상태 확인"""
        session = self.active_sessions.get(session_id)
        if not session or not session.current_target:
            return {"status": "no_active_target"}

        target = session.current_target

        status = {
            "target_id": target.target_id,
            "current_suds": target.current_suds,
            "initial_suds": target.initial_suds,
            "current_voc": target.current_voc,
            "sets_completed": target.sets_completed,
            "is_processed": target.is_processed(),
            "suds_reduction": (target.initial_suds - target.current_suds) if target.initial_suds and target.current_suds else 0
        }

        # 처리 완료 여부 판단
        if target.current_suds is not None and target.current_suds <= 1:
            if target.current_voc is not None and target.current_voc >= 6:
                status["recommendation"] = "processing_complete"
                status["next_phase"] = EMDRPhase.BODY_SCAN.value
            else:
                status["recommendation"] = "proceed_to_installation"
                status["next_phase"] = EMDRPhase.INSTALLATION.value
        elif target.sets_completed > 0 and target.sets_completed % 3 == 0:
            status["recommendation"] = "check_suds"
        else:
            status["recommendation"] = "continue_processing"

        return status

    def generate_phase_response(self, session_id: str,
                               user_input: str) -> Dict[str, Any]:
        """현재 단계에 맞는 응답 생성"""
        session = self.active_sessions.get(session_id)
        if not session:
            return {"error": "세션을 찾을 수 없습니다"}

        phase = session.current_phase
        guide = self.protocol_guide.get_phase_guide(phase)

        response = {
            "phase": phase.value,
            "phase_name": guide["name"],
            "goals": guide["goals"]
        }

        # 단계별 특수 처리
        if phase == EMDRPhase.HISTORY_TAKING:
            response["questions"] = guide.get("key_questions", [])
            response["screening"] = guide.get("screening_questions", [])

        elif phase == EMDRPhase.PREPARATION:
            response["explanation"] = guide.get("explanation_script", "")
            response["safe_place_guide"] = guide.get("safe_place_script", "")

        elif phase == EMDRPhase.ASSESSMENT:
            response["target_identification"] = guide.get("target_identification", "")
            response["suds_instruction"] = guide.get("suds_instruction", "")
            if session.current_target:
                response["voc_instruction"] = guide.get("voc_instruction", "").format(
                    positive_cognition=session.current_target.positive_cognition
                )

        elif phase == EMDRPhase.DESENSITIZATION:
            if session.current_target:
                response["start_script"] = guide.get("start_script", "").format(
                    negative_cognition=session.current_target.negative_cognition
                )
            response["set_transition"] = guide.get("set_transition", "")
            response["return_to_target"] = guide.get("return_to_target", "")

        elif phase == EMDRPhase.INSTALLATION:
            if session.current_target:
                response["script"] = guide.get("script", "").format(
                    positive_cognition=session.current_target.positive_cognition
                )
                response["voc_check"] = guide.get("voc_check", "").format(
                    positive_cognition=session.current_target.positive_cognition
                )

        elif phase == EMDRPhase.BODY_SCAN:
            if session.current_target:
                response["script"] = guide.get("script", "").format(
                    positive_cognition=session.current_target.positive_cognition
                )
            response["clean_scan"] = guide.get("clean_scan", "")
            response["residual_tension"] = guide.get("residual_tension", "")

        elif phase == EMDRPhase.CLOSURE:
            processing_status = self.check_processing_status(session_id)
            if processing_status.get("is_processed"):
                response["script"] = guide.get("complete_processing_script", "")
            else:
                script = guide.get("incomplete_processing_script", "")
                if session.safe_place:
                    script = script.format(safe_place_name=session.safe_place.name)
                response["script"] = script

                if session.container:
                    response["container_usage"] = guide.get("container_usage", "").format(
                        container_name=session.container.name,
                        lock_mechanism=session.container.lock_mechanism
                    )

        elif phase == EMDRPhase.REEVALUATION:
            response["script"] = guide.get("script", "")

        return response

    def close_session(self, session_id: str,
                     complete: bool = True) -> Dict[str, Any]:
        """세션 종료"""
        session = self.active_sessions.get(session_id)
        if not session:
            return {"error": "세션을 찾을 수 없습니다"}

        session.ended_at = datetime.now()

        # 세션 요약 생성
        summary = {
            "session_id": session_id,
            "user_id": session.user_id,
            "duration_minutes": (session.ended_at - session.started_at).seconds // 60,
            "phases_completed": session.current_phase.value,
            "targets_processed": len(session.targets),
            "completed_targets": sum(1 for t in session.targets if t.is_processed()),
            "total_sets": sum(t.sets_completed for t in session.targets),
            "final_phase": session.current_phase.value
        }

        if session.current_target:
            summary["last_target"] = {
                "target_id": session.current_target.target_id,
                "final_suds": session.current_target.current_suds,
                "final_voc": session.current_target.current_voc,
                "is_processed": session.current_target.is_processed()
            }

        # 세션 이동
        self.completed_sessions.append(session)
        del self.active_sessions[session_id]

        logger.info(f"EMDR 세션 종료: {session_id}")

        return summary

    def get_session_report(self, session_id: str) -> Dict[str, Any]:
        """세션 보고서 생성"""
        # 활성 세션 또는 완료된 세션에서 검색
        session = self.active_sessions.get(session_id)
        if not session:
            for s in self.completed_sessions:
                if s.session_id == session_id:
                    session = s
                    break

        if not session:
            return {"error": "세션을 찾을 수 없습니다"}

        report = {
            "session_info": {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "started_at": session.started_at.isoformat(),
                "ended_at": session.ended_at.isoformat() if session.ended_at else None,
                "current_phase": session.current_phase.value
            },
            "targets": [],
            "resources": {
                "safe_place": session.safe_place.name if session.safe_place else None,
                "container": session.container.name if session.container else None
            },
            "session_notes": session.session_notes
        }

        for target in session.targets:
            target_report = {
                "target_id": target.target_id,
                "description": target.description,
                "negative_cognition": target.negative_cognition,
                "positive_cognition": target.positive_cognition,
                "emotion": target.emotion,
                "body_sensation": target.body_sensation,
                "suds_progression": [
                    {"rating": s.rating, "timestamp": s.timestamp.isoformat()}
                    for s in target.suds_history
                ],
                "voc_progression": [
                    {"rating": v.rating, "timestamp": v.timestamp.isoformat()}
                    for v in target.voc_history
                ],
                "sets_completed": target.sets_completed,
                "is_processed": target.is_processed(),
                "processing_status": target.processing_status.value
            }
            report["targets"].append(target_report)

        return report


# ============================================================================
# Part 6: EMDR 안전 프로토콜
# ============================================================================

class EMDRSafetyProtocol:
    """EMDR 안전 프로토콜"""

    def __init__(self):
        self.contraindications = self._load_contraindications()
        self.stabilization_techniques = self._load_stabilization_techniques()

    def _load_contraindications(self) -> Dict[str, Any]:
        """금기사항 목록"""
        return {
            "absolute": [
                {
                    "condition": "급성 정신증",
                    "description": "현재 정신증적 증상이 있는 경우",
                    "action": "EMDR 진행 불가, 정신과 연계 필요"
                },
                {
                    "condition": "심한 해리 장애",
                    "description": "심각한 해리 증상이나 다중인격 의심",
                    "action": "전문가 평가 후 결정"
                },
                {
                    "condition": "불안정한 환경",
                    "description": "현재 학대나 위험 상황에 있는 경우",
                    "action": "안전 확보 우선"
                },
                {
                    "condition": "급성 자살 위험",
                    "description": "현재 자살 계획이 있는 경우",
                    "action": "위기 개입 우선"
                }
            ],
            "relative": [
                {
                    "condition": "심한 우울증",
                    "description": "심각한 우울 상태",
                    "action": "안정화 및 약물 치료 병행 고려"
                },
                {
                    "condition": "물질 사용 장애",
                    "description": "활성 중독 상태",
                    "action": "해독 후 진행 또는 병행 치료"
                },
                {
                    "condition": "의료적 불안정",
                    "description": "간질, 심장질환 등",
                    "action": "의료진 협의 필요"
                },
                {
                    "condition": "임신",
                    "description": "특히 고위험 임신",
                    "action": "산부인과 협의, 주의해서 진행"
                }
            ],
            "caution": [
                {
                    "condition": "최근 트라우마",
                    "description": "최근 1개월 이내 트라우마 경험",
                    "action": "안정화 기간 필요할 수 있음"
                },
                {
                    "condition": "복잡 트라우마",
                    "description": "어린 시절 만성적 트라우마",
                    "action": "충분한 준비 단계 필요"
                },
                {
                    "condition": "약한 지지체계",
                    "description": "사회적 지지가 부족한 경우",
                    "action": "세션 간 지지체계 구축 필요"
                }
            ]
        }

    def _load_stabilization_techniques(self) -> Dict[str, str]:
        """안정화 기법"""
        return {
            "grounding_5_4_3_2_1": """
### 5-4-3-2-1 그라운딩

지금 이 순간으로 돌아오겠습니다.

주변에서:
- 5가지 보이는 것을 말해주세요
- 4가지 만질 수 있는 것
- 3가지 들리는 것
- 2가지 냄새 맡을 수 있는 것
- 1가지 맛볼 수 있는 것

천천히 하나씩 말씀해주세요.
""",
            "breathing_4_7_8": """
### 4-7-8 호흡

함께 호흡하겠습니다.

1. 코로 4초간 들이쉽니다... 1, 2, 3, 4
2. 7초간 숨을 참습니다... 1, 2, 3, 4, 5, 6, 7
3. 입으로 8초간 내쉽니다... 1, 2, 3, 4, 5, 6, 7, 8

다시 한번 해볼까요?
""",
            "safe_place_activation": """
### 안전한 장소로

잠시 안전한 장소로 가겠습니다.

눈을 감고, 당신의 안전한 장소를 떠올려주세요.
모든 감각을 활성화하세요.
여기는 완전히 안전합니다.
필요한 만큼 머물러 계세요.

준비되면 말씀해주세요.
""",
            "butterfly_hug_calming": """
### 나비 포옹 진정

나비 포옹 자세를 취해주세요.
아주 천천히, 부드럽게 탭핑합니다.
숨을 들이쉬며... 왼쪽...
숨을 내쉬며... 오른쪽...
마음이 진정될 때까지 계속합니다.
""",
            "orientation_to_present": """
### 현재로 돌아오기

지금 이 순간으로 돌아오겠습니다.

- 오늘은 {date}입니다
- 지금 당신은 안전한 곳에 있습니다
- 그 일은 과거의 일입니다
- 지금 여기서 당신은 안전합니다

발이 바닥에 닿는 느낌을 느껴보세요.
의자가 몸을 지지하는 느낌을 느껴보세요.
"""
        }

    def screen_for_contraindications(self,
                                     screening_responses: Dict[str, bool]) -> Dict[str, Any]:
        """금기사항 스크리닝"""
        result = {
            "can_proceed": True,
            "warnings": [],
            "recommendations": []
        }

        # 절대 금기사항 체크
        if screening_responses.get("acute_psychosis"):
            result["can_proceed"] = False
            result["warnings"].append("급성 정신증 - EMDR 진행 불가")
            result["recommendations"].append("정신과 전문의 연계가 필요합니다")

        if screening_responses.get("severe_dissociation"):
            result["can_proceed"] = False
            result["warnings"].append("심한 해리 증상 - 전문가 평가 필요")
            result["recommendations"].append("해리 장애 전문가 평가를 권장합니다")

        if screening_responses.get("active_danger"):
            result["can_proceed"] = False
            result["warnings"].append("현재 위험 상황 - 안전 확보 우선")
            result["recommendations"].append("안전한 환경 확보가 우선입니다")

        if screening_responses.get("acute_suicidal"):
            result["can_proceed"] = False
            result["warnings"].append("급성 자살 위험 - 위기 개입 필요")
            result["recommendations"].append("즉각적인 위기 개입이 필요합니다")

        # 상대 금기사항 체크
        if screening_responses.get("severe_depression"):
            result["warnings"].append("심한 우울증 - 주의 필요")
            result["recommendations"].append("안정화 및 약물 치료 병행을 고려하세요")

        if screening_responses.get("substance_use"):
            result["warnings"].append("물질 사용 - 주의 필요")
            result["recommendations"].append("물질 사용 상태 안정화 후 진행을 권장합니다")

        if screening_responses.get("medical_conditions"):
            result["warnings"].append("의료적 상태 - 확인 필요")
            result["recommendations"].append("담당 의료진과 협의하세요")

        # 주의사항 체크
        if screening_responses.get("recent_trauma"):
            result["recommendations"].append("최근 트라우마 - 충분한 안정화 기간을 가지세요")

        if screening_responses.get("complex_trauma"):
            result["recommendations"].append("복잡 트라우마 - 준비 단계를 충분히 진행하세요")

        return result

    def get_stabilization_technique(self, technique_name: str) -> str:
        """안정화 기법 가져오기"""
        return self.stabilization_techniques.get(technique_name, "")

    def handle_abreaction(self) -> str:
        """감정 폭발(abreaction) 대응"""
        return """
### 강한 감정 반응 대응

지금 강한 감정이 올라오고 있군요. 괜찮습니다.

1. **안전합니다**
   - 지금 여기는 안전한 곳입니다
   - 이것은 기억입니다
   - 당신은 그때가 아닌 지금 여기에 있습니다

2. **함께 있습니다**
   - 저는 여기 있습니다
   - 당신은 혼자가 아닙니다

3. **선택할 수 있습니다**
   - 계속 진행할 수 있습니다
   - 잠시 멈출 수 있습니다
   - 안전한 장소로 갈 수 있습니다

어떻게 하고 싶으신가요?
"""

    def emergency_stop_protocol(self, session_id: str) -> str:
        """긴급 중단 프로토콜"""
        return """
### 세션 긴급 중단

세션을 안전하게 중단하겠습니다.

1. **현재로 돌아오기**
   - 눈을 뜨세요
   - 방 안을 둘러보세요
   - 발이 바닥에 닿는 것을 느끼세요

2. **호흡 안정**
   - 천천히 깊게 숨을 쉬세요
   - 들이쉬고... 내쉬고...

3. **그라운딩**
   - 주변에서 5가지 보이는 것을 말해주세요

4. **안전 확인**
   - 지금 괜찮으신가요?
   - 필요한 것이 있으신가요?

다음에 편안할 때 다시 이야기 나눌 수 있습니다.
오늘은 여기까지 하겠습니다.
"""


# ============================================================================
# 메인 인터페이스
# ============================================================================

def create_emdr_system() -> IntegratedEMDRTherapySystem:
    """EMDR 치료 시스템 생성"""
    return IntegratedEMDRTherapySystem()


def create_safety_protocol() -> EMDRSafetyProtocol:
    """안전 프로토콜 생성"""
    return EMDRSafetyProtocol()


# 사용 예시
if __name__ == "__main__":
    # 시스템 초기화
    emdr_system = create_emdr_system()
    safety_protocol = create_safety_protocol()

    # 새 세션 생성
    session = emdr_system.create_session("user_123")
    print(f"세션 생성: {session.session_id}")

    # 1단계 가이드 가져오기
    phase_response = emdr_system.generate_phase_response(session.session_id, "")
    print(f"\n현재 단계: {phase_response['phase_name']}")
    print(f"목표: {phase_response['goals']}")

    # 양측성 자극 가이드
    bilateral_guide = emdr_system.bilateral_guide
    setup = bilateral_guide.get_setup_guide(BilateralStimulationType.BUTTERFLY_HUG)
    print(f"\n{setup}")

    # 안전 스크리닝
    screening = safety_protocol.screen_for_contraindications({
        "acute_psychosis": False,
        "severe_dissociation": False,
        "recent_trauma": True
    })
    print(f"\n진행 가능: {screening['can_proceed']}")
    print(f"권장사항: {screening['recommendations']}")
