"""
위기 감지 및 안전 시스템 (Compatibility Layer)
Crisis Detection and Safety System

이 파일은 하위 호환성을 위한 래퍼입니다.
실제 구현은 safety_system_v2.py에 있습니다.

사용 권장:
    from src.safety_system_v2 import SafetySystem, RiskLevel
"""

import logging
from typing import Dict, List, Optional

# v2 모듈에서 실제 구현 import
from .safety_system_v2 import (
    SafetySystem,
    RiskLevel,
    KeywordDetector,
    SentimentAnalyzer,
    PatternRecognizer,
    LLMCrisisEvaluator,
    CrisisLog
)

logger = logging.getLogger(__name__)


class CrisisDetectionSystem:
    """
    위기 감지 시스템 호환성 클래스

    이 클래스는 하위 호환성을 위해 유지됩니다.
    새로운 코드에서는 SafetySystem을 직접 사용하세요.

    Example:
        # 권장 (새로운 코드)
        from src.safety_system_v2 import SafetySystem, RiskLevel
        safety = SafetySystem()

        # 레거시 지원 (기존 코드)
        from src.safety_system import CrisisDetectionSystem
        detector = CrisisDetectionSystem()
    """

    def __init__(self, keywords_file: Optional[str] = None):
        """
        초기화

        Args:
            keywords_file: 위기 키워드 파일 경로 (v2에서는 무시됨)
        """
        logger.info("CrisisDetectionSystem initialized (using SafetySystem v2)")
        self._safety_system = SafetySystem()
        self.detection_history = []

    def detect_crisis(self, text: str) -> Dict[str, any]:
        """
        위기 상황 감지

        Args:
            text: 분석할 텍스트

        Returns:
            Dict: 위기 감지 결과
                - is_crisis: 위기 여부
                - crisis_type: 위기 유형
                - severity: 심각도 (0-1)
                - confidence: 신뢰도 (0-1)
                - detected_keywords: 감지된 키워드
                - recommended_action: 권장 조치
                - emergency_contacts: 응급 연락처
        """
        if not text or not text.strip():
            return self._empty_result()

        # v2 check_safety 호출
        v2_result = self._safety_system.check_safety(text)

        # v1 형식으로 변환
        risk_level = v2_result.get("risk_level", RiskLevel.NONE)
        is_crisis = risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]

        # 심각도 변환 (RiskLevel → 0-1)
        severity_map = {
            RiskLevel.CRITICAL: 1.0,
            RiskLevel.HIGH: 0.8,
            RiskLevel.MEDIUM: 0.5,
            RiskLevel.LOW: 0.3,
            RiskLevel.NONE: 0.0
        }
        severity = severity_map.get(risk_level, 0.0)

        # 위기 유형 결정
        crisis_type = "none"
        if is_crisis:
            keywords = v2_result.get("detected_keywords", [])
            if any(k in str(keywords) for k in ["자살", "죽고", "목숨"]):
                crisis_type = "suicide"
            elif any(k in str(keywords) for k in ["자해", "손목", "긋"]):
                crisis_type = "self_harm"
            elif any(k in str(keywords) for k in ["폭력", "때리", "죽이"]):
                crisis_type = "violence"
            else:
                crisis_type = "emotional_distress"

        # 권장 조치 결정
        recommended_action = self._determine_action(severity)

        result = {
            "is_crisis": is_crisis,
            "crisis_type": crisis_type,
            "severity": round(severity, 2),
            "confidence": v2_result.get("confidence", 0.8),
            "detected_keywords": v2_result.get("detected_keywords", []),
            "recommended_action": recommended_action,
            "emergency_contacts": self._get_emergency_contacts(crisis_type),
            "details": {
                "risk_level": risk_level.value if hasattr(risk_level, 'value') else str(risk_level),
                "v2_result": v2_result
            }
        }

        # 히스토리 저장
        self.detection_history.append({
            "text": text[:100],
            "result": result
        })

        if result["is_crisis"]:
            logger.warning(
                f"Crisis detected: {result['crisis_type']} "
                f"(severity: {result['severity']:.2f})"
            )

        return result

    def _determine_action(self, severity: float) -> str:
        """권장 조치 결정"""
        if severity >= 0.9:
            return "immediate_emergency_intervention"
        elif severity >= 0.7:
            return "urgent_professional_referral"
        elif severity >= 0.5:
            return "professional_recommendation"
        elif severity >= 0.3:
            return "supportive_monitoring"
        else:
            return "continue_conversation"

    def _get_emergency_contacts(self, crisis_type: str) -> Dict[str, any]:
        """응급 연락처"""
        return {
            "general": {
                "자살예방상담전화": "1393",
                "정신건강위기상담전화": "1577-0199",
                "응급": "119"
            }
        }

    def _empty_result(self) -> Dict[str, any]:
        """빈 결과 반환"""
        return {
            "is_crisis": False,
            "crisis_type": "none",
            "severity": 0.0,
            "confidence": 0.0,
            "detected_keywords": [],
            "recommended_action": "continue_conversation",
            "emergency_contacts": {},
            "details": {}
        }

    def get_intervention_message(self, crisis_result: Dict) -> str:
        """
        개입 메시지 생성

        Args:
            crisis_result: 위기 감지 결과

        Returns:
            str: 개입 메시지
        """
        if not crisis_result.get("is_crisis", False):
            return ""

        crisis_type = crisis_result.get("crisis_type", "")
        severity = crisis_result.get("severity", 0)

        messages = {
            "suicide": """
당신의 생명은 매우 소중합니다. 지금 느끼시는 고통이 얼마나 큰지 이해합니다.

하지만 혼자 감당하지 마시고, 지금 당장 전문가의 도움을 받으시는 것이 중요합니다.

🆘 자살예방상담전화: 1393 (24시간)
🆘 정신건강위기상담전화: 1577-0199 (24시간)
🆘 응급상황: 119

지금 이 순간이 힘들더라도, 도움을 받으시면 상황은 나아질 수 있습니다.
""",
            "self_harm": """
스스로를 해치고 싶은 충동이 느껴지신다니, 정말 힘든 상황이시군요.

지금 당장 안전한 곳으로 이동하시고, 전문가의 도움을 받으시는 것이 중요합니다.

📞 정신건강위기상담전화: 1577-0199 (24시간)
🆘 응급상황: 119

당신의 안전이 가장 중요합니다.
""",
            "violence": """
폭력이나 학대 상황에 있으시다면, 당신의 안전이 최우선입니다.

즉시 안전한 곳으로 피신하시고 도움을 요청하세요.

🆘 경찰: 112
📞 여성긴급전화: 1366 (24시간)
📞 아동학대신고: 112
"""
        }

        base_message = messages.get(crisis_type, messages["suicide"])

        if severity >= 0.9:
            base_message = "⚠️ 긴급 상황입니다.\n\n" + base_message

        return base_message.strip()


# 하위 호환성을 위한 export
__all__ = [
    'CrisisDetectionSystem',
    'SafetySystem',
    'RiskLevel',
    'KeywordDetector',
    'SentimentAnalyzer',
    'PatternRecognizer',
    'LLMCrisisEvaluator',
    'CrisisLog'
]


if __name__ == "__main__":
    # 테스트
    print("=== CrisisDetectionSystem (v1 compatibility) 테스트 ===\n")

    system = CrisisDetectionSystem()

    test_cases = [
        "죽고 싶어요. 더 이상 살 이유가 없어요.",
        "자해를 하고 싶어요.",
        "오늘 회사가 힘들었어요.",
    ]

    for text in test_cases:
        result = system.detect_crisis(text)
        print(f"입력: {text}")
        print(f"위기 여부: {result['is_crisis']}")
        print(f"위기 유형: {result['crisis_type']}")
        print(f"심각도: {result['severity']:.2f}")
        print("-" * 50)
