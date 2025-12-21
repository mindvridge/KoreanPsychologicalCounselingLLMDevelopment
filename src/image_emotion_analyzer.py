"""
이미지 기반 감정 분석 모듈
웹캠 캡처 이미지에서 얼굴 감지 및 감정 분석
"""

import base64
import io
import logging
from typing import Dict, Optional, Any
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV not available. Image emotion analysis will be limited.")

try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False
    logger.warning("DeepFace not available. Using basic image analysis.")


class ImageEmotionAnalyzer:
    """
    이미지에서 감정을 분석하는 클래스
    """
    
    def __init__(self):
        self.is_available = CV2_AVAILABLE or DEEPFACE_AVAILABLE
        if not self.is_available:
            logger.warning("Image emotion analysis is not fully available. Install opencv-python and deepface for full functionality.")
    
    def analyze(self, image_base64: str) -> Dict[str, Any]:
        """
        Base64 인코딩된 이미지에서 감정 분석
        
        Args:
            image_base64: Base64 인코딩된 이미지 문자열
            
        Returns:
            Dict: 분석 결과
                - primary_emotion: 주요 감정
                - emotions: 모든 감정 점수
                - confidence: 신뢰도
                - face_detected: 얼굴 감지 여부
        """
        if not image_base64:
            return self._empty_result()
        
        try:
            # Base64 디코딩
            image_data = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_data))
            
            # PIL Image를 numpy array로 변환
            img_array = np.array(image)
            
            # DeepFace를 사용한 감정 분석
            if DEEPFACE_AVAILABLE:
                try:
                    # DeepFace는 BGR 형식을 기대하므로 RGB를 BGR로 변환
                    if len(img_array.shape) == 3 and img_array.shape[2] == 3:
                        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                    else:
                        img_bgr = img_array
                    
                    # DeepFace로 감정 분석
                    result = DeepFace.analyze(
                        img_bgr,
                        actions=['emotion'],
                        enforce_detection=False,
                        silent=True
                    )
                    
                    # 결과 처리
                    if isinstance(result, list):
                        result = result[0]
                    
                    if 'emotion' in result:
                        emotions = result['emotion']
                        
                        # 주요 감정 찾기
                        primary_emotion = max(emotions.items(), key=lambda x: x[1])[0]
                        confidence = emotions[primary_emotion] / 100.0  # 0-1로 정규화
                        
                        # 한국어 감정 매핑
                        emotion_map = {
                            'angry': '분노',
                            'disgust': '혐오',
                            'fear': '두려움',
                            'happy': '기쁨',
                            'sad': '슬픔',
                            'surprise': '놀람',
                            'neutral': '중립'
                        }
                        
                        primary_emotion_kr = emotion_map.get(primary_emotion, primary_emotion)
                        
                        # 모든 감정을 한국어로 변환
                        emotions_kr = {
                            emotion_map.get(k, k): v / 100.0 
                            for k, v in emotions.items()
                        }
                        
                        return {
                            "primary_emotion": primary_emotion_kr,
                            "emotions": emotions_kr,
                            "confidence": confidence,
                            "face_detected": True,
                            "method": "deepface"
                        }
                    
                except Exception as e:
                    logger.warning(f"DeepFace analysis failed: {e}")
                    # Fallback to basic analysis
            
            # 기본 분석 (얼굴 감지만)
            if CV2_AVAILABLE:
                try:
                    # OpenCV로 얼굴 감지
                    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY) if len(img_array.shape) == 3 else img_array
                    
                    # Haar Cascade 얼굴 감지기 (기본 제공)
                    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                    
                    if len(faces) > 0:
                        return {
                            "primary_emotion": "중립",
                            "emotions": {"중립": 0.5},
                            "confidence": 0.5,
                            "face_detected": True,
                            "method": "basic",
                            "note": "얼굴은 감지되었지만 감정 분석은 DeepFace가 필요합니다."
                        }
                except Exception as e:
                    logger.warning(f"Basic face detection failed: {e}")
            
            return {
                "primary_emotion": "중립",
                "emotions": {},
                "confidence": 0.0,
                "face_detected": False,
                "method": "none",
                "note": "얼굴을 감지할 수 없습니다."
            }
            
        except Exception as e:
            logger.error(f"Error analyzing image: {e}", exc_info=True)
            return self._empty_result()
    
    def _empty_result(self) -> Dict[str, Any]:
        """빈 결과 반환"""
        return {
            "primary_emotion": "중립",
            "emotions": {},
            "confidence": 0.0,
            "face_detected": False,
            "method": "none"
        }


# 전역 인스턴스
_image_emotion_analyzer = None

def get_image_emotion_analyzer() -> ImageEmotionAnalyzer:
    """이미지 감정 분석기 싱글톤 인스턴스 반환"""
    global _image_emotion_analyzer
    if _image_emotion_analyzer is None:
        _image_emotion_analyzer = ImageEmotionAnalyzer()
    return _image_emotion_analyzer

