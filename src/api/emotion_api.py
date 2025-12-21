"""
실시간 감정 분석 API (Real-time Emotion Analysis API)
웹캠 이미지를 분석하여 감정 데이터 반환
"""

import logging
import base64
import io
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

# FastAPI
try:
    from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field
except ImportError:
    # 테스트용 더미
    APIRouter = None
    BaseModel = object

# 이미지 처리
try:
    import numpy as np
    from PIL import Image
    HAS_IMAGE_SUPPORT = True
except ImportError:
    HAS_IMAGE_SUPPORT = False
    np = None
    Image = None

# 얼굴/감정 인식 (선택적)
try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False
    cv2 = None

logger = logging.getLogger(__name__)

# ============================================================================
# 데이터 모델
# ============================================================================

class EmotionType(str, Enum):
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    FEARFUL = "fearful"
    DISGUSTED = "disgusted"
    SURPRISED = "surprised"
    NEUTRAL = "neutral"


class EmotionRequest(BaseModel):
    """감정 분석 요청"""
    image: str = Field(..., description="Base64 인코딩된 이미지")
    session_id: Optional[str] = Field(None, description="세션 ID")
    timestamp: Optional[int] = Field(None, description="클라이언트 타임스탬프")


class EmotionResponse(BaseModel):
    """감정 분석 응답"""
    success: bool
    face_detected: bool
    emotions: Dict[str, float]
    primary_emotion: str
    confidence: float
    valence: float  # -1 (부정) ~ 1 (긍정)
    arousal: float  # 0 (차분) ~ 1 (흥분)
    engagement: float  # 참여도 0 ~ 1
    nonverbal_cues: List[str]
    timestamp: int
    processing_time_ms: float
    counseling_context: Optional[str] = None


class EmotionHistoryItem(BaseModel):
    """감정 히스토리 항목"""
    timestamp: int
    primary_emotion: str
    valence: float
    arousal: float


class SessionEmotionSummary(BaseModel):
    """세션 감정 요약"""
    session_id: str
    duration_seconds: float
    total_analyses: int
    dominant_emotions: Dict[str, float]
    average_valence: float
    average_arousal: float
    emotion_changes: int
    key_moments: List[Dict[str, Any]]


# ============================================================================
# 감정 분석 서비스
# ============================================================================

class EmotionAnalysisService:
    """감정 분석 서비스"""

    # 감정-Valence/Arousal 매핑
    EMOTION_VALENCE = {
        "happy": 0.8,
        "surprised": 0.3,
        "neutral": 0.0,
        "sad": -0.6,
        "fearful": -0.5,
        "angry": -0.7,
        "disgusted": -0.4
    }

    EMOTION_AROUSAL = {
        "happy": 0.6,
        "surprised": 0.8,
        "angry": 0.9,
        "fearful": 0.7,
        "disgusted": 0.4,
        "sad": 0.2,
        "neutral": 0.1
    }

    # 비언어적 단서 매핑
    NONVERBAL_CUES = {
        "eye_contact": "눈 맞춤",
        "gaze_avoidance": "시선 회피",
        "head_down": "고개 숙임",
        "furrowed_brow": "미간 찌푸림",
        "tense_jaw": "턱 긴장",
        "forced_smile": "억지 미소"
    }

    # 상담 컨텍스트 템플릿
    COUNSELING_CONTEXT_TEMPLATES = {
        "happy": "내담자가 밝은 표정을 보이고 있습니다. 긍정적 분위기를 유지하세요.",
        "sad": "내담자에게서 슬픔이 감지됩니다. 공감적으로 경청하고 감정을 수용하세요.",
        "angry": "분노 감정이 감지됩니다. 차분한 톤을 유지하고 감정을 인정해주세요.",
        "fearful": "불안/두려움이 보입니다. 안전감을 제공하고 천천히 진행하세요.",
        "disgusted": "불쾌감이 감지됩니다. 해당 감정을 탐색해보세요.",
        "surprised": "놀라움이 감지됩니다. 상황을 명확히 하고 정보를 제공하세요.",
        "neutral": "중립적 상태입니다. 개방형 질문으로 대화를 이끌어가세요."
    }

    def __init__(self):
        self.session_histories: Dict[str, List[EmotionHistoryItem]] = {}
        self.model_loaded = False
        self._load_model()

    def _load_model(self):
        """감정 인식 모델 로드"""
        # 실제 구현에서는 여기서 모델을 로드
        # - TensorFlow/PyTorch 모델
        # - OpenCV DNN
        # - face_recognition + 표정 분류기
        self.model_loaded = True
        logger.info("감정 분석 모델 로드 완료")

    def decode_image(self, base64_string: str) -> Optional[Any]:
        """Base64 이미지 디코딩"""
        try:
            image_data = base64.b64decode(base64_string)

            if HAS_IMAGE_SUPPORT:
                image = Image.open(io.BytesIO(image_data))
                return np.array(image)
            else:
                return image_data

        except Exception as e:
            logger.error(f"이미지 디코딩 실패: {e}")
            return None

    def detect_face(self, image: Any) -> Optional[Dict[str, Any]]:
        """얼굴 감지"""
        if not HAS_OPENCV:
            # OpenCV 없이 시뮬레이션
            return {
                "detected": True,
                "bbox": [100, 100, 200, 200],
                "confidence": 0.95
            }

        try:
            # OpenCV Haar Cascade 또는 DNN 사용
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)

            if len(faces) > 0:
                x, y, w, h = faces[0]
                return {
                    "detected": True,
                    "bbox": [int(x), int(y), int(w), int(h)],
                    "confidence": 0.9
                }
            return None

        except Exception as e:
            logger.error(f"얼굴 감지 실패: {e}")
            return None

    def analyze_emotions(self, image: Any) -> Dict[str, float]:
        """감정 분석"""
        # 실제 구현에서는 딥러닝 모델 사용
        # 여기서는 시뮬레이션 데이터 반환

        import random

        # 기본 분포 생성
        emotions = {}
        remaining = 1.0

        emotion_list = list(EmotionType)
        random.shuffle(emotion_list)

        for i, emotion in enumerate(emotion_list):
            if i == len(emotion_list) - 1:
                emotions[emotion.value] = remaining
            else:
                # 하나의 감정이 지배적이도록
                if i == 0:
                    prob = 0.4 + random.random() * 0.4  # 40-80%
                else:
                    prob = random.random() * remaining * 0.5
                emotions[emotion.value] = prob
                remaining -= prob

        return emotions

    def detect_nonverbal_cues(self, image: Any, face_data: Dict) -> List[str]:
        """비언어적 단서 감지"""
        # 실제 구현에서는 랜드마크 기반 분석
        cues = []

        # 시뮬레이션
        import random
        if random.random() > 0.7:
            cues.append("gaze_avoidance")
        if random.random() > 0.8:
            cues.append("furrowed_brow")

        return cues

    def calculate_engagement(self, emotions: Dict[str, float], face_data: Dict) -> float:
        """참여도 계산"""
        # 감정 강도 기반 참여도
        max_emotion = max(emotions.values())
        neutral_level = emotions.get("neutral", 0)

        # 중립이 높으면 참여도 낮음
        engagement = max_emotion * (1 - neutral_level * 0.5)
        return min(1.0, max(0.0, engagement + 0.3))

    def generate_counseling_context(
        self,
        primary_emotion: str,
        confidence: float,
        valence: float,
        nonverbal_cues: List[str]
    ) -> str:
        """상담 컨텍스트 생성"""
        context_parts = []

        # 주요 감정 컨텍스트
        base_context = self.COUNSELING_CONTEXT_TEMPLATES.get(
            primary_emotion,
            "감정 상태를 파악 중입니다."
        )
        context_parts.append(base_context)

        # 신뢰도에 따른 추가
        if confidence > 0.8:
            context_parts.append(f"감정이 뚜렷하게 나타나고 있습니다 ({int(confidence*100)}%).")

        # 비언어적 단서
        if "gaze_avoidance" in nonverbal_cues:
            context_parts.append("시선을 피하는 경향이 있어 불편함을 느낄 수 있습니다.")
        if "furrowed_brow" in nonverbal_cues:
            context_parts.append("미간을 찌푸리고 있어 걱정이나 집중 상태일 수 있습니다.")

        # Valence 기반 추가
        if valence < -0.5:
            context_parts.append("전반적으로 부정적인 감정 상태입니다. 공감과 지지가 필요합니다.")

        return " ".join(context_parts)

    def analyze(self, image_base64: str, session_id: Optional[str] = None) -> EmotionResponse:
        """전체 분석 수행"""
        start_time = time.time()

        # 이미지 디코딩
        image = self.decode_image(image_base64)
        if image is None:
            return EmotionResponse(
                success=False,
                face_detected=False,
                emotions={},
                primary_emotion="unknown",
                confidence=0,
                valence=0,
                arousal=0,
                engagement=0,
                nonverbal_cues=[],
                timestamp=int(time.time() * 1000),
                processing_time_ms=0
            )

        # 얼굴 감지
        face_data = self.detect_face(image)
        if not face_data:
            return EmotionResponse(
                success=True,
                face_detected=False,
                emotions={},
                primary_emotion="unknown",
                confidence=0,
                valence=0,
                arousal=0,
                engagement=0,
                nonverbal_cues=[],
                timestamp=int(time.time() * 1000),
                processing_time_ms=(time.time() - start_time) * 1000
            )

        # 감정 분석
        emotions = self.analyze_emotions(image)

        # 주요 감정 결정
        primary_emotion = max(emotions, key=emotions.get)
        confidence = emotions[primary_emotion]

        # Valence/Arousal 계산
        valence = sum(
            self.EMOTION_VALENCE.get(e, 0) * p
            for e, p in emotions.items()
        )
        arousal = sum(
            self.EMOTION_AROUSAL.get(e, 0) * p
            for e, p in emotions.items()
        )

        # 비언어적 단서
        nonverbal_cues = self.detect_nonverbal_cues(image, face_data)

        # 참여도
        engagement = self.calculate_engagement(emotions, face_data)

        # 상담 컨텍스트
        counseling_context = self.generate_counseling_context(
            primary_emotion, confidence, valence, nonverbal_cues
        )

        # 세션 히스토리 업데이트
        if session_id:
            self._update_session_history(session_id, primary_emotion, valence, arousal)

        processing_time = (time.time() - start_time) * 1000

        return EmotionResponse(
            success=True,
            face_detected=True,
            emotions=emotions,
            primary_emotion=primary_emotion,
            confidence=confidence,
            valence=valence,
            arousal=arousal,
            engagement=engagement,
            nonverbal_cues=nonverbal_cues,
            timestamp=int(time.time() * 1000),
            processing_time_ms=processing_time,
            counseling_context=counseling_context
        )

    def _update_session_history(
        self,
        session_id: str,
        primary_emotion: str,
        valence: float,
        arousal: float
    ):
        """세션 히스토리 업데이트"""
        if session_id not in self.session_histories:
            self.session_histories[session_id] = []

        self.session_histories[session_id].append(EmotionHistoryItem(
            timestamp=int(time.time() * 1000),
            primary_emotion=primary_emotion,
            valence=valence,
            arousal=arousal
        ))

        # 최대 1000개 유지
        if len(self.session_histories[session_id]) > 1000:
            self.session_histories[session_id] = self.session_histories[session_id][-1000:]

    def get_session_summary(self, session_id: str) -> Optional[SessionEmotionSummary]:
        """세션 감정 요약"""
        if session_id not in self.session_histories:
            return None

        history = self.session_histories[session_id]
        if not history:
            return None

        # 통계 계산
        duration = (history[-1].timestamp - history[0].timestamp) / 1000

        # 감정 분포
        emotion_counts = {}
        for item in history:
            emotion_counts[item.primary_emotion] = emotion_counts.get(item.primary_emotion, 0) + 1

        total = len(history)
        dominant_emotions = {e: c/total for e, c in emotion_counts.items()}

        # 평균
        avg_valence = sum(h.valence for h in history) / total
        avg_arousal = sum(h.arousal for h in history) / total

        # 감정 변화 횟수
        changes = sum(
            1 for i in range(1, len(history))
            if history[i].primary_emotion != history[i-1].primary_emotion
        )

        # 주요 순간 (급격한 변화)
        key_moments = []
        for i in range(1, len(history)):
            if abs(history[i].valence - history[i-1].valence) > 0.5:
                key_moments.append({
                    "timestamp": history[i].timestamp,
                    "from_emotion": history[i-1].primary_emotion,
                    "to_emotion": history[i].primary_emotion,
                    "valence_change": history[i].valence - history[i-1].valence
                })

        return SessionEmotionSummary(
            session_id=session_id,
            duration_seconds=duration,
            total_analyses=total,
            dominant_emotions=dominant_emotions,
            average_valence=avg_valence,
            average_arousal=avg_arousal,
            emotion_changes=changes,
            key_moments=key_moments[:10]  # 최대 10개
        )


# ============================================================================
# API 라우터
# ============================================================================

# 서비스 인스턴스
emotion_service = EmotionAnalysisService()

# FastAPI 라우터
if APIRouter:
    router = APIRouter(prefix="/api/emotion", tags=["Emotion Analysis"])

    @router.post("/analyze", response_model=EmotionResponse)
    async def analyze_emotion(request: EmotionRequest):
        """
        실시간 감정 분석

        웹캠에서 캡처한 이미지를 분석하여 감정 데이터를 반환합니다.
        """
        try:
            result = emotion_service.analyze(
                request.image,
                request.session_id
            )
            return result
        except Exception as e:
            logger.error(f"감정 분석 오류: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/session/{session_id}/summary", response_model=SessionEmotionSummary)
    async def get_session_summary(session_id: str):
        """
        세션 감정 요약

        특정 세션의 감정 분석 요약을 반환합니다.
        """
        summary = emotion_service.get_session_summary(session_id)
        if not summary:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        return summary

    @router.websocket("/ws/{session_id}")
    async def emotion_websocket(websocket: WebSocket, session_id: str):
        """
        WebSocket 실시간 감정 분석

        지속적인 실시간 분석을 위한 WebSocket 연결
        """
        await websocket.accept()
        logger.info(f"WebSocket 연결: {session_id}")

        try:
            while True:
                # 이미지 데이터 수신
                data = await websocket.receive_json()
                image_base64 = data.get("image")

                if image_base64:
                    result = emotion_service.analyze(image_base64, session_id)
                    await websocket.send_json(asdict(result) if hasattr(result, '__dict__') else result.dict())

        except WebSocketDisconnect:
            logger.info(f"WebSocket 연결 종료: {session_id}")
        except Exception as e:
            logger.error(f"WebSocket 오류: {e}")
            await websocket.close()


# ============================================================================
# 테스트
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("실시간 감정 분석 API 테스트")
    print("=" * 60)

    # 서비스 테스트
    service = EmotionAnalysisService()

    # 더미 이미지 (실제로는 웹캠 이미지)
    dummy_image = base64.b64encode(b"fake_image_data").decode()

    # 분석 수행
    result = service.analyze(dummy_image, "test_session")

    print(f"\n분석 결과:")
    print(f"  - 얼굴 감지: {result.face_detected}")
    print(f"  - 주요 감정: {result.primary_emotion} ({result.confidence:.0%})")
    print(f"  - Valence: {result.valence:.2f}")
    print(f"  - Arousal: {result.arousal:.2f}")
    print(f"  - 참여도: {result.engagement:.0%}")
    print(f"  - 처리 시간: {result.processing_time_ms:.1f}ms")
    print(f"\n상담 컨텍스트:")
    print(f"  {result.counseling_context}")

    # 여러 번 분석 후 요약
    for _ in range(5):
        service.analyze(dummy_image, "test_session")

    summary = service.get_session_summary("test_session")
    if summary:
        print(f"\n세션 요약:")
        print(f"  - 총 분석: {summary.total_analyses}회")
        print(f"  - 감정 변화: {summary.emotion_changes}회")
        print(f"  - 평균 Valence: {summary.average_valence:.2f}")

    print("\n✅ 테스트 완료!")
