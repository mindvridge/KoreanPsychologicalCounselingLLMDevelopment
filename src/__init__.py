"""
한국형 심리상담 LLM 패키지
Korean Mental Health Counseling LLM Package

이 패키지는 한국 문화와 언어에 특화된 심리상담 AI 시스템을 제공합니다.
"""

__version__ = "0.2.0"
__author__ = "Korean Mental Health LLM Team"

# 메인 클래스
from .main import KoreanMentalHealthLLM

# 안전 시스템 (v2 권장)
from .safety_system import CrisisDetectionSystem  # 레거시 호환
from .safety_system_v2 import SafetySystem, RiskLevel  # v2 권장

# 감정 분석 (v2 권장)
from .emotion_analyzer import EmotionAnalyzer  # 레거시 호환
from .emotion_analyzer_v2 import KoreanEmotionAnalyzer  # v2 권장

__all__ = [
    # 메인
    "KoreanMentalHealthLLM",
    # 안전 시스템
    "CrisisDetectionSystem",  # 레거시
    "SafetySystem",  # v2 권장
    "RiskLevel",
    # 감정 분석
    "EmotionAnalyzer",  # 레거시
    "KoreanEmotionAnalyzer",  # v2 권장
]
