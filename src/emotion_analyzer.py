"""
감정 분석 모듈 (Compatibility Layer)
Emotion Analysis Module

이 파일은 하위 호환성을 위한 래퍼입니다.
실제 구현은 emotion_analyzer_v2.py에 있습니다.

사용 권장:
    from src.emotion_analyzer_v2 import KoreanEmotionAnalyzer
"""

import logging
from typing import Dict, List, Optional

# v2 모듈에서 실제 구현 import
from .emotion_analyzer_v2 import KoreanEmotionAnalyzer, EmotionRecord

logger = logging.getLogger(__name__)


class EmotionAnalyzer:
    """
    감정 분석기 호환성 클래스

    이 클래스는 하위 호환성을 위해 유지됩니다.
    새로운 코드에서는 KoreanEmotionAnalyzer를 직접 사용하세요.

    Example:
        # 권장 (새로운 코드)
        from src.emotion_analyzer_v2 import KoreanEmotionAnalyzer
        analyzer = KoreanEmotionAnalyzer()

        # 레거시 지원 (기존 코드)
        from src.emotion_analyzer import EmotionAnalyzer
        analyzer = EmotionAnalyzer()
    """

    def __init__(self):
        """감정 분석기 초기화 - v2 래핑"""
        logger.info("EmotionAnalyzer initialized (using KoreanEmotionAnalyzer v2)")
        self._analyzer = KoreanEmotionAnalyzer()

    def analyze(self, text: str) -> Dict[str, any]:
        """
        텍스트 감정 분석

        Args:
            text: 분석할 텍스트

        Returns:
            Dict: 분석 결과
                - primary_emotion: 주요 감정
                - emotions: 감지된 감정과 점수
                - intensity: 감정 강도 (0-1)
                - details: 상세 정보
        """
        if not text or not text.strip():
            return self._empty_result()

        # v2 analyze 호출
        v2_result = self._analyzer.analyze(text)

        # v1 형식으로 변환
        return {
            "primary_emotion": v2_result.get("primary_emotion", "중립"),
            "emotions": v2_result.get("emotions", {}),
            "intensity": v2_result.get("intensity", 0) / 10,  # v2는 1-10, v1은 0-1
            "details": {
                "text_length": len(text),
                "contextual_clues": v2_result.get("implicit_cues", []),
                "detected_keywords": v2_result.get("keywords_found", []),
                "secondary_emotions": v2_result.get("secondary_emotions", []),
                "age_group": v2_result.get("age_group", None)
            }
        }

    def get_emotion_summary(self, text: str) -> str:
        """
        감정 분석 요약 텍스트

        Args:
            text: 분석할 텍스트

        Returns:
            str: 요약 문자열
        """
        result = self.analyze(text)

        primary = result["primary_emotion"]
        intensity = result["intensity"]

        intensity_label = "약함"
        if intensity > 0.7:
            intensity_label = "강함"
        elif intensity > 0.4:
            intensity_label = "중간"

        return f"{primary} (강도: {intensity_label})"

    def _empty_result(self) -> Dict[str, any]:
        """빈 결과 반환"""
        return {
            "primary_emotion": "중립",
            "emotions": {},
            "intensity": 0.0,
            "details": {}
        }


# 하위 호환성을 위한 export
__all__ = ['EmotionAnalyzer', 'KoreanEmotionAnalyzer', 'EmotionRecord']


if __name__ == "__main__":
    # 테스트
    print("=== EmotionAnalyzer (v1 compatibility) 테스트 ===\n")

    analyzer = EmotionAnalyzer()

    test_cases = [
        "너무 불안하고 걱정돼요. 잠도 못 자겠어요.",
        "회사가 정말 힘들어요. 스트레스가 너무 심해요.",
        "아무것도 하기 싫고 무기력해요. 우울해요.",
    ]

    for text in test_cases:
        result = analyzer.analyze(text)
        print(f"입력: {text}")
        print(f"주요 감정: {result['primary_emotion']}")
        print(f"강도: {result['intensity']:.2f}")
        print("-" * 50)
