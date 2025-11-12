"""
한국형 심리상담 LLM 패키지
Korean Mental Health Counseling LLM Package

이 패키지는 한국 문화와 언어에 특화된 심리상담 AI 시스템을 제공합니다.
"""

__version__ = "0.1.0"
__author__ = "Korean Mental Health LLM Team"

from .main import KoreanMentalHealthLLM
from .safety_system import CrisisDetectionSystem
from .emotion_analyzer import EmotionAnalyzer

__all__ = [
    "KoreanMentalHealthLLM",
    "CrisisDetectionSystem",
    "EmotionAnalyzer",
]
