"""
안전 시스템 테스트
Safety System Tests

위기 감지 시스템의 기능을 테스트합니다.
"""

import sys
import os
import pytest

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.safety_system import CrisisDetectionSystem
from src.emotion_analyzer import EmotionAnalyzer


class TestCrisisDetectionSystem:
    """위기 감지 시스템 테스트 클래스"""

    @pytest.fixture
    def crisis_system(self):
        """위기 감지 시스템 픽스처"""
        return CrisisDetectionSystem()

    def test_suicide_detection_high_severity(self, crisis_system):
        """자살 관련 표현 감지 - 높은 심각도"""
        text = "죽고 싶어요. 더 이상 살 이유가 없어요."
        result = crisis_system.detect_crisis(text)

        assert result["is_crisis"] is True
        assert result["crisis_type"] == "suicide"
        assert result["severity"] > 0.7
        assert len(result["detected_keywords"]) > 0

    def test_suicide_detection_with_plan(self, crisis_system):
        """자살 계획이 있는 경우 - 매우 높은 심각도"""
        text = "오늘 자살할 계획이에요. 준비도 다 했어요."
        result = crisis_system.detect_crisis(text)

        assert result["is_crisis"] is True
        assert result["severity"] > 0.8
        assert "immediate" in result["details"]["context_analysis"]["urgency_indicators"]

    def test_suicide_negation(self, crisis_system):
        """부정 표현 - 심각도 감소"""
        text = "죽고 싶지 않아요. 살고 싶어요."
        result = crisis_system.detect_crisis(text)

        # 부정 표현으로 인해 위기가 아니거나 심각도가 낮아야 함
        if result["is_crisis"]:
            assert result["severity"] < 0.7

    def test_suicide_past_tense(self, crisis_system):
        """과거형 - 심각도 감소"""
        text = "예전에 죽고 싶었던 적이 있었어요."
        result = crisis_system.detect_crisis(text)

        # 과거형으로 인해 위기가 아니거나 심각도가 낮아야 함
        assert result["severity"] < 0.8

    def test_suicide_hypothetical(self, crisis_system):
        """가정형 - 심각도 감소"""
        text = "만약 내가 죽으면 어떻게 될까요?"
        result = crisis_system.detect_crisis(text)

        # 가정형으로 인해 심각도가 낮아야 함
        assert result["severity"] < 0.8

    def test_self_harm_detection(self, crisis_system):
        """자해 관련 표현 감지"""
        text = "자해를 하고 싶어요. 손목을 긋고 싶어요."
        result = crisis_system.detect_crisis(text)

        assert result["is_crisis"] is True
        assert result["crisis_type"] == "self_harm"
        assert result["severity"] > 0.7

    def test_no_crisis_normal_sadness(self, crisis_system):
        """일상적 슬픔 - 위기 아님"""
        text = "오늘 기분이 좀 우울해요."
        result = crisis_system.detect_crisis(text)

        assert result["is_crisis"] is False
        assert result["severity"] < 0.7

    def test_no_crisis_work_stress(self, crisis_system):
        """직장 스트레스 - 위기 아님"""
        text = "회사 일이 많아서 힘들어요."
        result = crisis_system.detect_crisis(text)

        assert result["is_crisis"] is False

    def test_intervention_message_suicide(self, crisis_system):
        """자살 위기 개입 메시지 생성"""
        text = "죽고 싶어요."
        result = crisis_system.detect_crisis(text)

        if result["is_crisis"]:
            message = crisis_system.get_intervention_message(result)
            assert "1393" in message  # 자살예방상담전화
            assert len(message) > 0

    def test_emergency_contacts(self, crisis_system):
        """응급 연락처 포함 확인"""
        text = "자살하고 싶어요."
        result = crisis_system.detect_crisis(text)

        if result["is_crisis"]:
            assert "emergency_contacts" in result
            assert len(result["emergency_contacts"]) > 0

    def test_detection_history(self, crisis_system):
        """감지 이력 저장 확인"""
        texts = [
            "죽고 싶어요.",
            "힘들어요.",
            "자해하고 싶어요."
        ]

        for text in texts:
            crisis_system.detect_crisis(text)

        assert len(crisis_system.detection_history) == len(texts)

    def test_multiple_keywords(self, crisis_system):
        """여러 키워드 포함 시 심각도 증가"""
        text1 = "죽고 싶어요."
        text2 = "죽고 싶어요. 자살하고 싶어요. 살 이유가 없어요."

        result1 = crisis_system.detect_crisis(text1)
        result2 = crisis_system.detect_crisis(text2)

        # 더 많은 키워드가 있으면 심각도가 더 높아야 함
        assert result2["severity"] >= result1["severity"]


class TestEmotionAnalyzer:
    """감정 분석기 테스트 클래스"""

    @pytest.fixture
    def emotion_analyzer(self):
        """감정 분석기 픽스처"""
        return EmotionAnalyzer()

    def test_anxiety_detection(self, emotion_analyzer):
        """불안 감정 감지"""
        text = "너무 불안하고 걱정돼요. 잠도 못 자겠어요."
        result = emotion_analyzer.analyze(text)

        assert result["primary_emotion"] == "불안"
        assert result["intensity"] > 0.5

    def test_depression_detection(self, emotion_analyzer):
        """우울 감정 감지"""
        text = "아무것도 하기 싫고 무기력해요. 우울해요."
        result = emotion_analyzer.analyze(text)

        assert result["primary_emotion"] == "우울"
        assert result["intensity"] > 0.5

    def test_anger_detection(self, emotion_analyzer):
        """분노 감정 감지"""
        text = "너무 화가 나요. 짜증나고 열받아요."
        result = emotion_analyzer.analyze(text)

        assert result["primary_emotion"] == "분노"
        assert result["intensity"] > 0.5

    def test_joy_detection(self, emotion_analyzer):
        """기쁨 감정 감지"""
        text = "오늘 정말 기쁘고 행복해요. 좋은 일이 있었어요."
        result = emotion_analyzer.analyze(text)

        assert result["primary_emotion"] == "기쁨"
        assert result["intensity"] > 0.5

    def test_neutral_emotion(self, emotion_analyzer):
        """중립 감정"""
        text = "오늘 날씨가 좋네요."
        result = emotion_analyzer.analyze(text)

        assert result["primary_emotion"] == "중립"
        assert result["intensity"] < 0.5

    def test_intensity_with_modifiers(self, emotion_analyzer):
        """강도 수정자 효과"""
        text1 = "불안해요."
        text2 = "너무 너무 불안해요!!!"

        result1 = emotion_analyzer.analyze(text1)
        result2 = emotion_analyzer.analyze(text2)

        # 강도 수정자와 느낌표로 인해 더 높은 강도
        assert result2["intensity"] > result1["intensity"]

    def test_indirect_expression(self, emotion_analyzer):
        """간접 표현 인식"""
        text = "그냥 그래요. 별거 아니에요."
        result = emotion_analyzer.analyze(text)

        # 간접 표현이 감지되어야 함
        assert "간접표현" in str(result["details"].get("contextual_clues", []))

    def test_empty_text(self, emotion_analyzer):
        """빈 텍스트 처리"""
        result = emotion_analyzer.analyze("")

        assert result["primary_emotion"] == "중립"
        assert result["intensity"] == 0.0

    def test_multiple_emotions(self, emotion_analyzer):
        """복합 감정"""
        text = "불안하고 우울하고 화도 나요."
        result = emotion_analyzer.analyze(text)

        # 여러 감정이 감지되어야 함
        emotions = result["emotions"]
        detected_count = sum(1 for score in emotions.values() if score > 0)

        assert detected_count >= 2  # 최소 2개 이상의 감정 감지


def test_integration_emotion_and_crisis():
    """감정 분석과 위기 감지 통합 테스트"""
    emotion_analyzer = EmotionAnalyzer()
    crisis_system = CrisisDetectionSystem()

    text = "너무 불안하고 죽고 싶어요."

    # 감정 분석
    emotion_result = emotion_analyzer.analyze(text)
    assert emotion_result["primary_emotion"] in ["불안", "우울"]

    # 위기 감지
    crisis_result = crisis_system.detect_crisis(text)
    assert crisis_result["is_crisis"] is True


def run_manual_tests():
    """수동 테스트 실행"""
    print("=== 위기 감지 시스템 수동 테스트 ===\n")

    crisis_system = CrisisDetectionSystem()
    emotion_analyzer = EmotionAnalyzer()

    test_cases = [
        "죽고 싶어요. 더 이상 살 이유가 없어요.",
        "자살 생각이 자꾸 들어요.",
        "만약 내가 죽으면 어떻게 될까요?",
        "예전에 죽고 싶었던 적이 있었어요.",
        "자해를 하고 싶어요.",
        "오늘 회사가 힘들었어요.",
        "불안하고 걱정돼요."
    ]

    for text in test_cases:
        print(f"입력: {text}")
        print("-" * 70)

        # 감정 분석
        emotion = emotion_analyzer.analyze(text)
        print(f"감정: {emotion['primary_emotion']} (강도: {emotion['intensity']:.2f})")

        # 위기 감지
        crisis = crisis_system.detect_crisis(text)
        print(f"위기: {crisis['is_crisis']}")
        if crisis["is_crisis"]:
            print(f"  유형: {crisis['crisis_type']}")
            print(f"  심각도: {crisis['severity']:.2f}")
            print(f"  권장 조치: {crisis['recommended_action']}")

        print()


if __name__ == "__main__":
    # pytest 실행
    print("Running automated tests...\n")
    pytest.main([__file__, "-v"])

    print("\n" + "="*70 + "\n")

    # 수동 테스트 실행
    run_manual_tests()
