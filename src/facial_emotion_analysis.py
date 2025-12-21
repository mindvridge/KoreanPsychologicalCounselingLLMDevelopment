"""
웹캠 기반 표정/감정 분석 시스템 (Facial Emotion Analysis System)
내담자의 얼굴 표정을 실시간으로 분석하여 심리상담에 활용

기능:
- 실시간 웹캠 영상 캡처
- 얼굴 감지 및 랜드마크 추출
- 표정 기반 감정 인식 (7가지 기본 감정)
- 미세 표정 분석 (Micro-expression)
- 비언어적 단서 감지 (시선, 고개 방향, 제스처)
- 상담 응답에 감정 정보 통합
- 감정 변화 추적 및 리포트
"""

import logging
import base64
import io
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


# =============================================================================
# Enums & Constants
# =============================================================================

class FacialEmotion(Enum):
    """얼굴 표정 기반 7가지 기본 감정"""
    HAPPY = "happy"             # 행복
    SAD = "sad"                 # 슬픔
    ANGRY = "angry"             # 분노
    FEARFUL = "fearful"         # 두려움
    DISGUSTED = "disgusted"     # 혐오
    SURPRISED = "surprised"     # 놀람
    NEUTRAL = "neutral"         # 중립


class NonverbalCue(Enum):
    """비언어적 단서"""
    EYE_CONTACT = "eye_contact"           # 눈 맞춤
    GAZE_AVOIDANCE = "gaze_avoidance"     # 시선 회피
    HEAD_DOWN = "head_down"               # 고개 숙임
    HEAD_TILT = "head_tilt"               # 고개 기울임
    FURROWED_BROW = "furrowed_brow"       # 미간 찌푸림
    TENSE_JAW = "tense_jaw"               # 턱 긴장
    LIP_BITING = "lip_biting"             # 입술 깨물기
    TEARS = "tears"                       # 눈물
    FORCED_SMILE = "forced_smile"         # 억지 미소
    MICRO_EXPRESSION = "micro_expression" # 미세 표정


class EngagementLevel(Enum):
    """상담 참여도"""
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    DISENGAGED = "disengaged"


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class EmotionDetection:
    """감정 감지 결과"""
    primary_emotion: FacialEmotion
    confidence: float  # 0-1
    all_emotions: Dict[str, float]  # 모든 감정 확률
    valence: float  # -1 (부정) ~ 1 (긍정)
    arousal: float  # 0 (차분) ~ 1 (흥분)
    timestamp: datetime


@dataclass
class FacialAnalysis:
    """얼굴 분석 결과"""
    face_detected: bool
    emotion: Optional[EmotionDetection]
    nonverbal_cues: List[NonverbalCue]
    engagement_level: EngagementLevel
    head_pose: Dict[str, float]  # pitch, yaw, roll
    eye_aspect_ratio: float  # 눈 깜빡임/졸림 감지
    mouth_aspect_ratio: float
    blink_rate: float  # 분당 깜빡임
    analysis_timestamp: datetime


@dataclass
class EmotionTimeline:
    """감정 타임라인"""
    session_id: str
    start_time: datetime
    emotion_history: List[EmotionDetection]
    dominant_emotions: Dict[str, float]  # 감정별 비율
    emotional_volatility: float  # 감정 변동성
    key_moments: List[Dict]  # 중요 순간 (급격한 변화)


@dataclass
class NonverbalInsight:
    """비언어적 인사이트"""
    cue: NonverbalCue
    frequency: int
    context: str
    clinical_meaning: str
    suggested_response: str


# =============================================================================
# Facial Landmark Detector (얼굴 랜드마크 감지)
# =============================================================================

class FacialLandmarkDetector:
    """얼굴 랜드마크 감지기"""

    def __init__(self):
        """
        실제 구현에서는 다음 라이브러리 중 하나 사용:
        - dlib + shape_predictor_68_face_landmarks
        - MediaPipe Face Mesh (468 landmarks)
        - OpenCV + DNN face detector
        """
        self.landmark_indices = {
            "left_eye": list(range(36, 42)),
            "right_eye": list(range(42, 48)),
            "nose": list(range(27, 36)),
            "mouth": list(range(48, 68)),
            "left_eyebrow": list(range(17, 22)),
            "right_eyebrow": list(range(22, 27)),
            "jaw": list(range(0, 17))
        }

        logger.info("얼굴 랜드마크 감지기 초기화")

    def detect_landmarks(self, image: np.ndarray) -> Optional[Dict]:
        """
        얼굴 랜드마크 감지

        Args:
            image: BGR 또는 RGB 이미지 (numpy array)

        Returns:
            랜드마크 좌표 딕셔너리 또는 None
        """
        # 실제 구현에서는 dlib 또는 MediaPipe 사용
        # 여기서는 인터페이스만 정의

        # Mock 반환 (실제 구현 시 교체)
        return {
            "landmarks_68": [],  # 68개 랜드마크 좌표
            "face_rect": (0, 0, 100, 100),  # x, y, w, h
            "confidence": 0.95
        }

    def calculate_eye_aspect_ratio(self, landmarks: Dict) -> float:
        """눈 종횡비 계산 (졸림/깜빡임 감지)"""
        # EAR = (|p2-p6| + |p3-p5|) / (2 * |p1-p4|)
        return 0.3  # Mock value

    def calculate_mouth_aspect_ratio(self, landmarks: Dict) -> float:
        """입 종횡비 계산"""
        return 0.5  # Mock value

    def estimate_head_pose(self, landmarks: Dict) -> Dict[str, float]:
        """머리 자세 추정"""
        return {
            "pitch": 0.0,  # 상하 (고개 끄덕임)
            "yaw": 0.0,    # 좌우 (고개 흔듦)
            "roll": 0.0    # 기울임
        }


# =============================================================================
# Emotion Classifier (감정 분류기)
# =============================================================================

class EmotionClassifier:
    """표정 기반 감정 분류기"""

    def __init__(self):
        """
        실제 구현에서는 다음 중 하나 사용:
        - FER (Facial Expression Recognition) 라이브러리
        - DeepFace
        - 커스텀 CNN 모델 (VGGFace, ResNet 등)
        """
        self.emotions = list(FacialEmotion)

        # 감정별 valence/arousal 매핑
        self.emotion_va_map = {
            FacialEmotion.HAPPY: (0.8, 0.6),
            FacialEmotion.SAD: (-0.7, 0.2),
            FacialEmotion.ANGRY: (-0.6, 0.8),
            FacialEmotion.FEARFUL: (-0.8, 0.7),
            FacialEmotion.DISGUSTED: (-0.5, 0.4),
            FacialEmotion.SURPRISED: (0.1, 0.9),
            FacialEmotion.NEUTRAL: (0.0, 0.3)
        }

        logger.info("감정 분류기 초기화")

    def classify(self, face_image: np.ndarray) -> EmotionDetection:
        """
        얼굴 이미지에서 감정 분류

        Args:
            face_image: 얼굴 영역 이미지

        Returns:
            EmotionDetection 결과
        """
        # 실제 구현에서는 딥러닝 모델 사용
        # Mock 구현

        all_emotions = {
            "happy": 0.1,
            "sad": 0.15,
            "angry": 0.05,
            "fearful": 0.1,
            "disgusted": 0.05,
            "surprised": 0.05,
            "neutral": 0.5
        }

        primary = max(all_emotions, key=all_emotions.get)
        primary_emotion = FacialEmotion(primary)
        confidence = all_emotions[primary]

        valence, arousal = self.emotion_va_map.get(
            primary_emotion, (0.0, 0.3)
        )

        return EmotionDetection(
            primary_emotion=primary_emotion,
            confidence=confidence,
            all_emotions=all_emotions,
            valence=valence,
            arousal=arousal,
            timestamp=datetime.now()
        )

    def detect_micro_expression(
        self,
        frame_sequence: List[np.ndarray],
        fps: int = 30
    ) -> Optional[Dict]:
        """
        미세 표정 감지 (0.04-0.2초 지속)

        Args:
            frame_sequence: 연속된 프레임들
            fps: 초당 프레임 수
        """
        # 미세 표정은 약 1-5 프레임 지속
        # 실제 구현에서는 optical flow 또는 시계열 분석

        return None


# =============================================================================
# Nonverbal Cue Analyzer (비언어적 단서 분석기)
# =============================================================================

class NonverbalCueAnalyzer:
    """비언어적 단서 분석기"""

    def __init__(self):
        self.cue_meanings = self._init_cue_meanings()

    def _init_cue_meanings(self) -> Dict[NonverbalCue, Dict]:
        """비언어적 단서의 임상적 의미"""
        return {
            NonverbalCue.EYE_CONTACT: {
                "meaning": "관심과 참여를 나타냄",
                "clinical": "적절한 눈 맞춤은 건강한 상호작용 표시",
                "response": "따뜻한 시선으로 반응하며 안전감 제공"
            },
            NonverbalCue.GAZE_AVOIDANCE: {
                "meaning": "불편함, 수치심, 또는 회피",
                "clinical": "민감한 주제에서 흔함. 과도하면 사회불안 가능성",
                "response": "압박하지 않고 편안한 분위기 유지. '천천히 말씀해 주셔도 괜찮아요'"
            },
            NonverbalCue.HEAD_DOWN: {
                "meaning": "우울, 수치심, 또는 위축",
                "clinical": "자존감 저하, 우울 증상과 연관",
                "response": "수용적 태도, 자기자비 강화. '많이 힘드셨군요'"
            },
            NonverbalCue.FURROWED_BROW: {
                "meaning": "혼란, 걱정, 또는 집중",
                "clinical": "불안, 걱정 반추와 관련",
                "response": "명확하게 설명, 걱정 탐색. '무엇이 가장 걱정되세요?'"
            },
            NonverbalCue.TENSE_JAW: {
                "meaning": "분노 억제, 스트레스",
                "clinical": "감정 억압, 신체화 가능성",
                "response": "감정 표현 격려. '지금 어떤 감정이 드세요?'"
            },
            NonverbalCue.LIP_BITING: {
                "meaning": "불안, 긴장, 또는 말하기 망설임",
                "clinical": "말하고 싶지만 억제하는 것일 수 있음",
                "response": "안전한 공간 제공. '말씀하고 싶은 게 있으신 것 같아요'"
            },
            NonverbalCue.TEARS: {
                "meaning": "슬픔, 해방감, 또는 감정 방출",
                "clinical": "감정 접촉의 중요한 순간",
                "response": "침묵과 공감. '울어도 괜찮아요. 여기 있을게요'"
            },
            NonverbalCue.FORCED_SMILE: {
                "meaning": "진짜 감정 숨김, 체면 유지",
                "clinical": "한국 문화에서 흔함. 진짜 감정 탐색 필요",
                "response": "부드럽게 탐색. '괜찮다고 하셨지만, 정말 괜찮으세요?'"
            },
            NonverbalCue.MICRO_EXPRESSION: {
                "meaning": "억압된 진짜 감정의 순간적 표출",
                "clinical": "말과 감정의 불일치 탐색 필요",
                "response": "관찰 결과 부드럽게 반영"
            }
        }

    def analyze(
        self,
        landmarks: Dict,
        head_pose: Dict[str, float],
        emotion: EmotionDetection,
        previous_frames: List[Dict] = None
    ) -> List[NonverbalCue]:
        """비언어적 단서 분석"""
        detected_cues = []

        # 시선 분석
        if head_pose.get("yaw", 0) > 20 or head_pose.get("yaw", 0) < -20:
            detected_cues.append(NonverbalCue.GAZE_AVOIDANCE)

        # 고개 숙임
        if head_pose.get("pitch", 0) < -15:
            detected_cues.append(NonverbalCue.HEAD_DOWN)

        # 억지 미소 감지 (행복 표정이지만 눈 주변 근육 비활성)
        if emotion.primary_emotion == FacialEmotion.HAPPY:
            if emotion.confidence < 0.6:  # 낮은 신뢰도
                detected_cues.append(NonverbalCue.FORCED_SMILE)

        return detected_cues

    def get_insight(self, cue: NonverbalCue) -> NonverbalInsight:
        """비언어적 단서에 대한 인사이트"""
        cue_info = self.cue_meanings.get(cue, {})

        return NonverbalInsight(
            cue=cue,
            frequency=1,
            context="상담 중",
            clinical_meaning=cue_info.get("clinical", ""),
            suggested_response=cue_info.get("response", "")
        )


# =============================================================================
# Engagement Tracker (참여도 추적기)
# =============================================================================

class EngagementTracker:
    """상담 참여도 추적기"""

    def __init__(self):
        self.blink_history = []
        self.gaze_history = []
        self.emotion_history = []

    def calculate_engagement(
        self,
        eye_aspect_ratio: float,
        head_pose: Dict[str, float],
        emotion: EmotionDetection,
        response_latency: float = None
    ) -> EngagementLevel:
        """참여도 계산"""
        score = 0.5  # 기본 점수

        # 눈 맞춤 (head pose 기반)
        yaw_abs = abs(head_pose.get("yaw", 0))
        if yaw_abs < 10:
            score += 0.2
        elif yaw_abs > 30:
            score -= 0.2

        # 감정 반응성
        if emotion.arousal > 0.5:
            score += 0.1

        # 졸림 감지 (EAR)
        if eye_aspect_ratio < 0.2:
            score -= 0.3

        # 점수 → 레벨
        if score >= 0.7:
            return EngagementLevel.HIGH
        elif score >= 0.5:
            return EngagementLevel.MODERATE
        elif score >= 0.3:
            return EngagementLevel.LOW
        else:
            return EngagementLevel.DISENGAGED


# =============================================================================
# Session Emotion Tracker (세션 감정 추적기)
# =============================================================================

class SessionEmotionTracker:
    """세션 내 감정 변화 추적"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.start_time = datetime.now()
        self.emotion_history: List[EmotionDetection] = []
        self.key_moments: List[Dict] = []

    def add_detection(self, detection: EmotionDetection) -> None:
        """감정 감지 결과 추가"""
        self.emotion_history.append(detection)

        # 급격한 변화 감지
        if len(self.emotion_history) >= 2:
            prev = self.emotion_history[-2]
            curr = detection

            valence_change = abs(curr.valence - prev.valence)
            if valence_change > 0.5:
                self.key_moments.append({
                    "timestamp": curr.timestamp.isoformat(),
                    "type": "emotional_shift",
                    "from_emotion": prev.primary_emotion.value,
                    "to_emotion": curr.primary_emotion.value,
                    "valence_change": valence_change
                })

    def get_timeline(self) -> EmotionTimeline:
        """감정 타임라인 생성"""
        if not self.emotion_history:
            return EmotionTimeline(
                session_id=self.session_id,
                start_time=self.start_time,
                emotion_history=[],
                dominant_emotions={},
                emotional_volatility=0.0,
                key_moments=[]
            )

        # 감정별 비율 계산
        emotion_counts = {}
        for det in self.emotion_history:
            emotion = det.primary_emotion.value
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

        total = len(self.emotion_history)
        dominant_emotions = {
            k: round(v / total, 2)
            for k, v in emotion_counts.items()
        }

        # 감정 변동성 계산
        if len(self.emotion_history) > 1:
            valences = [d.valence for d in self.emotion_history]
            volatility = np.std(valences)
        else:
            volatility = 0.0

        return EmotionTimeline(
            session_id=self.session_id,
            start_time=self.start_time,
            emotion_history=self.emotion_history,
            dominant_emotions=dominant_emotions,
            emotional_volatility=float(volatility),
            key_moments=self.key_moments
        )


# =============================================================================
# Counseling Response Integrator (상담 응답 통합기)
# =============================================================================

class CounselingResponseIntegrator:
    """표정 분석 결과를 상담 응답에 통합"""

    def __init__(self):
        self.emotion_prompts = self._init_emotion_prompts()
        self.nonverbal_analyzer = NonverbalCueAnalyzer()

    def _init_emotion_prompts(self) -> Dict[FacialEmotion, Dict]:
        """감정별 상담 가이드"""
        return {
            FacialEmotion.HAPPY: {
                "observe": "밝은 표정이 보이네요",
                "validate": "좋은 일이 있으신 것 같아요",
                "explore": "무엇이 기분을 좋게 했나요?",
                "caution": "억지 미소 가능성 체크"
            },
            FacialEmotion.SAD: {
                "observe": "많이 힘드신 것 같아 보여요",
                "validate": "슬픔이 느껴지네요. 괜찮아요",
                "explore": "지금 어떤 마음이세요?",
                "technique": "감정 수용, 타당화"
            },
            FacialEmotion.ANGRY: {
                "observe": "화가 나신 것 같아요",
                "validate": "그런 상황에서 화가 나는 건 자연스러워요",
                "explore": "무엇이 가장 화가 나세요?",
                "technique": "감정 표현 격려, 1차 감정 탐색"
            },
            FacialEmotion.FEARFUL: {
                "observe": "불안해 보이세요",
                "validate": "두려움을 느끼고 계시군요",
                "explore": "지금 가장 걱정되는 게 뭔가요?",
                "technique": "안전감 제공, 그라운딩"
            },
            FacialEmotion.SURPRISED: {
                "observe": "놀라신 것 같네요",
                "validate": "예상치 못한 일이었군요",
                "explore": "무엇이 놀라우셨어요?",
                "technique": "탐색, 정보 처리 시간 제공"
            },
            FacialEmotion.NEUTRAL: {
                "observe": None,
                "validate": None,
                "explore": "지금 어떤 감정이 드세요?",
                "technique": "감정 탐색"
            }
        }

    def generate_context_prompt(
        self,
        analysis: FacialAnalysis,
        verbal_message: str = None
    ) -> str:
        """
        표정 분석 결과를 기반으로 상담사용 컨텍스트 생성

        이 정보는 LLM 시스템 프롬프트에 추가됨
        """
        if not analysis.face_detected or not analysis.emotion:
            return ""

        emotion = analysis.emotion.primary_emotion
        prompts = self.emotion_prompts.get(emotion, {})

        context_parts = ["\n# 비언어적 관찰 정보 (내담자 표정 분석)"]

        # 감정 정보
        context_parts.append(f"""
## 감지된 감정 상태
- 주요 감정: {emotion.value} (신뢰도: {analysis.emotion.confidence:.0%})
- 정서가 (Valence): {analysis.emotion.valence:.2f} (-1 부정 ~ +1 긍정)
- 각성도 (Arousal): {analysis.emotion.arousal:.2f} (0 차분 ~ 1 흥분)
""")

        # 비언어적 단서
        if analysis.nonverbal_cues:
            context_parts.append("## 비언어적 단서")
            for cue in analysis.nonverbal_cues:
                insight = self.nonverbal_analyzer.get_insight(cue)
                context_parts.append(f"- {cue.value}: {insight.clinical_meaning}")
                context_parts.append(f"  → 권장 반응: {insight.suggested_response}")

        # 참여도
        context_parts.append(f"\n## 참여도: {analysis.engagement_level.value}")
        if analysis.engagement_level == EngagementLevel.LOW:
            context_parts.append("→ 참여도가 낮아 보입니다. 흥미를 끌 수 있는 질문이나 휴식을 제안해보세요.")
        elif analysis.engagement_level == EngagementLevel.DISENGAGED:
            context_parts.append("→ 주의: 상담에 집중하지 못하는 것 같습니다. 지금 상태를 확인해주세요.")

        # 언어-비언어 불일치
        if verbal_message:
            if self._detect_incongruence(analysis.emotion, verbal_message):
                context_parts.append("""
## ⚠️ 언어-비언어 불일치 감지
내담자의 말과 표정이 일치하지 않을 수 있습니다.
→ 부드럽게 탐색: "말씀은 괜찮다고 하셨지만, 표정에서 다른 감정이 느껴지는 것 같아요."
""")

        # 상담 가이드
        if prompts:
            context_parts.append("\n## 권장 상담 접근")
            if prompts.get("validate"):
                context_parts.append(f"- 타당화: \"{prompts['validate']}\"")
            if prompts.get("explore"):
                context_parts.append(f"- 탐색: \"{prompts['explore']}\"")
            if prompts.get("technique"):
                context_parts.append(f"- 기법: {prompts['technique']}")

        return "\n".join(context_parts)

    def _detect_incongruence(
        self,
        emotion: EmotionDetection,
        verbal_message: str
    ) -> bool:
        """언어-비언어 불일치 감지"""
        positive_words = ["괜찮", "좋", "행복", "감사", "기쁘"]
        negative_words = ["힘들", "슬프", "화", "불안", "걱정", "우울"]

        msg_lower = verbal_message.lower()

        # 긍정적 말 + 부정적 표정
        if any(w in msg_lower for w in positive_words):
            if emotion.primary_emotion in [
                FacialEmotion.SAD,
                FacialEmotion.ANGRY,
                FacialEmotion.FEARFUL
            ]:
                return True

        # 부정적 말 + 긍정적 표정
        if any(w in msg_lower for w in negative_words):
            if emotion.primary_emotion == FacialEmotion.HAPPY:
                if emotion.confidence > 0.7:  # 억지 미소 아닌 경우
                    return True

        return False


# =============================================================================
# Webcam Capture Handler (웹캠 캡처 핸들러)
# =============================================================================

class WebcamCaptureHandler:
    """웹캠 이미지 캡처 및 처리"""

    def __init__(self):
        self.supported_formats = ["jpeg", "png", "webp"]

    def decode_base64_image(self, base64_string: str) -> Optional[np.ndarray]:
        """Base64 인코딩된 이미지 디코딩"""
        try:
            # data:image/jpeg;base64,... 형식 처리
            if "base64," in base64_string:
                base64_string = base64_string.split("base64,")[1]

            image_bytes = base64.b64decode(base64_string)

            # 실제 구현에서는 cv2.imdecode 또는 PIL 사용
            # import cv2
            # nparr = np.frombuffer(image_bytes, np.uint8)
            # image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # Mock: 빈 이미지 반환
            image = np.zeros((480, 640, 3), dtype=np.uint8)

            return image

        except Exception as e:
            logger.error(f"이미지 디코딩 실패: {e}")
            return None

    def preprocess_for_analysis(
        self,
        image: np.ndarray,
        target_size: Tuple[int, int] = (224, 224)
    ) -> np.ndarray:
        """분석을 위한 전처리"""
        # 실제 구현: 리사이즈, 정규화 등
        return image


# =============================================================================
# Facial Emotion Analysis System (통합 시스템)
# =============================================================================

class FacialEmotionAnalysisSystem:
    """표정/감정 분석 통합 시스템"""

    def __init__(self):
        self.webcam_handler = WebcamCaptureHandler()
        self.landmark_detector = FacialLandmarkDetector()
        self.emotion_classifier = EmotionClassifier()
        self.nonverbal_analyzer = NonverbalCueAnalyzer()
        self.engagement_tracker = EngagementTracker()
        self.response_integrator = CounselingResponseIntegrator()

        # 세션별 트래커
        self.session_trackers: Dict[str, SessionEmotionTracker] = {}

        logger.info("표정/감정 분석 시스템 초기화 완료")

    def analyze_frame(
        self,
        image_base64: str,
        session_id: str = None
    ) -> FacialAnalysis:
        """
        단일 프레임 분석

        Args:
            image_base64: Base64 인코딩된 웹캠 이미지
            session_id: 세션 ID (추적용)

        Returns:
            FacialAnalysis 결과
        """
        # 이미지 디코딩
        image = self.webcam_handler.decode_base64_image(image_base64)

        if image is None:
            return FacialAnalysis(
                face_detected=False,
                emotion=None,
                nonverbal_cues=[],
                engagement_level=EngagementLevel.DISENGAGED,
                head_pose={},
                eye_aspect_ratio=0,
                mouth_aspect_ratio=0,
                blink_rate=0,
                analysis_timestamp=datetime.now()
            )

        # 얼굴 랜드마크 감지
        landmarks = self.landmark_detector.detect_landmarks(image)

        if not landmarks or landmarks.get("confidence", 0) < 0.5:
            return FacialAnalysis(
                face_detected=False,
                emotion=None,
                nonverbal_cues=[],
                engagement_level=EngagementLevel.DISENGAGED,
                head_pose={},
                eye_aspect_ratio=0,
                mouth_aspect_ratio=0,
                blink_rate=0,
                analysis_timestamp=datetime.now()
            )

        # 감정 분류
        emotion = self.emotion_classifier.classify(image)

        # 머리 자세 추정
        head_pose = self.landmark_detector.estimate_head_pose(landmarks)

        # 눈/입 종횡비
        ear = self.landmark_detector.calculate_eye_aspect_ratio(landmarks)
        mar = self.landmark_detector.calculate_mouth_aspect_ratio(landmarks)

        # 비언어적 단서 분석
        nonverbal_cues = self.nonverbal_analyzer.analyze(
            landmarks, head_pose, emotion
        )

        # 참여도 계산
        engagement = self.engagement_tracker.calculate_engagement(
            ear, head_pose, emotion
        )

        # 세션 추적
        if session_id:
            if session_id not in self.session_trackers:
                self.session_trackers[session_id] = SessionEmotionTracker(session_id)
            self.session_trackers[session_id].add_detection(emotion)

        return FacialAnalysis(
            face_detected=True,
            emotion=emotion,
            nonverbal_cues=nonverbal_cues,
            engagement_level=engagement,
            head_pose=head_pose,
            eye_aspect_ratio=ear,
            mouth_aspect_ratio=mar,
            blink_rate=15.0,  # 정상 범위: 15-20/분
            analysis_timestamp=datetime.now()
        )

    def get_counseling_context(
        self,
        analysis: FacialAnalysis,
        user_message: str = None
    ) -> str:
        """상담 LLM용 컨텍스트 생성"""
        return self.response_integrator.generate_context_prompt(
            analysis, user_message
        )

    def get_session_summary(self, session_id: str) -> Optional[Dict]:
        """세션 감정 요약"""
        tracker = self.session_trackers.get(session_id)
        if not tracker:
            return None

        timeline = tracker.get_timeline()

        return {
            "session_id": session_id,
            "duration_minutes": (
                datetime.now() - timeline.start_time
            ).total_seconds() / 60,
            "dominant_emotions": timeline.dominant_emotions,
            "emotional_volatility": timeline.emotional_volatility,
            "key_moments_count": len(timeline.key_moments),
            "key_moments": timeline.key_moments
        }

    def generate_session_report(self, session_id: str) -> str:
        """세션 감정 리포트 생성"""
        summary = self.get_session_summary(session_id)
        if not summary:
            return "세션 데이터가 없습니다."

        report = f"""
# 세션 감정 분석 리포트

## 세션 정보
- 세션 ID: {summary['session_id']}
- 진행 시간: {summary['duration_minutes']:.1f}분

## 감정 분포
"""
        for emotion, ratio in sorted(
            summary['dominant_emotions'].items(),
            key=lambda x: x[1],
            reverse=True
        ):
            bar = "█" * int(ratio * 20)
            report += f"- {emotion}: {bar} {ratio:.0%}\n"

        report += f"""
## 감정 변동성
- 점수: {summary['emotional_volatility']:.2f}
- 해석: {'감정 변화가 큼' if summary['emotional_volatility'] > 0.3 else '비교적 안정적'}

## 주요 순간
- 감정 변화 횟수: {summary['key_moments_count']}회
"""

        for moment in summary['key_moments'][:5]:
            report += f"- {moment.get('from_emotion', '')} → {moment.get('to_emotion', '')}\n"

        return report

    def get_module_summary(self) -> Dict:
        """모듈 요약"""
        return {
            "name": "웹캠 기반 표정/감정 분석 시스템",
            "version": "1.0.0",
            "components": {
                "webcam_handler": "Base64 이미지 처리",
                "landmark_detector": "68개 얼굴 랜드마크 감지",
                "emotion_classifier": "7가지 기본 감정 분류",
                "nonverbal_analyzer": "비언어적 단서 분석 (10종)",
                "engagement_tracker": "상담 참여도 추적",
                "session_tracker": "세션별 감정 변화 추적",
                "response_integrator": "상담 응답 통합"
            },
            "emotions": [e.value for e in FacialEmotion],
            "nonverbal_cues": [c.value for c in NonverbalCue],
            "features": [
                "실시간 표정 분석",
                "감정 변화 추적",
                "언어-비언어 불일치 감지",
                "상담 컨텍스트 자동 생성",
                "세션 감정 리포트"
            ]
        }


# =============================================================================
# Factory & Test
# =============================================================================

def get_facial_analysis_system() -> FacialEmotionAnalysisSystem:
    """표정 분석 시스템 인스턴스 생성"""
    return FacialEmotionAnalysisSystem()


if __name__ == "__main__":
    # 테스트
    system = get_facial_analysis_system()

    print("=" * 60)
    print("웹캠 기반 표정/감정 분석 시스템 테스트")
    print("=" * 60)

    # 모듈 요약
    summary = system.get_module_summary()
    print(f"\n모듈: {summary['name']} v{summary['version']}")
    print("\n구성요소:")
    for key, value in summary['components'].items():
        print(f"  - {key}: {value}")

    print(f"\n감지 가능 감정: {summary['emotions']}")
    print(f"비언어적 단서: {summary['nonverbal_cues']}")

    # Mock 분석 테스트
    print("\n\n--- 분석 테스트 (Mock) ---")

    # 가짜 Base64 이미지 (실제 테스트시 실제 이미지 사용)
    mock_image = base64.b64encode(b"fake_image_data").decode()

    analysis = system.analyze_frame(mock_image, session_id="test_session")
    print(f"얼굴 감지: {analysis.face_detected}")

    if analysis.emotion:
        print(f"감정: {analysis.emotion.primary_emotion.value}")
        print(f"신뢰도: {analysis.emotion.confidence:.0%}")

    print(f"참여도: {analysis.engagement_level.value}")

    # 상담 컨텍스트 생성
    print("\n\n--- 상담 컨텍스트 생성 ---")
    context = system.get_counseling_context(analysis, "저 괜찮아요")
    print(context[:500] if context else "컨텍스트 없음")

    print("\n\n테스트 완료!")
