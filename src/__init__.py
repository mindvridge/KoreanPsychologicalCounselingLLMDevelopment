"""
한국형 심리상담 LLM 패키지
Korean Mental Health Counseling LLM Package

이 패키지는 한국 문화와 언어에 특화된 심리상담 AI 시스템을 제공합니다.
"""

__version__ = "0.2.0"
__author__ = "Korean Mental Health LLM Team"

# 메인 클래스 (torch 의존성 있음 - 지연 로딩)
try:
    from .main import KoreanMentalHealthLLM
except ImportError:
    KoreanMentalHealthLLM = None

# 안전 시스템 (v2 - 직접 import)
from .safety_system_v2 import SafetySystem, RiskLevel

# 감정 분석 (v2 - 직접 import)
from .emotion_analyzer_v2 import KoreanEmotionAnalyzer

__all__ = [
    "KoreanMentalHealthLLM",
    "SafetySystem",
    "RiskLevel",
    "KoreanEmotionAnalyzer",
]
