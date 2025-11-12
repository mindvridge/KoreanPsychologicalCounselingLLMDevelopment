"""
Phase 2 시스템 종합 테스트
Comprehensive Tests for Phase 2 Systems

다층 안전 시스템 및 한국어 감정 분석 시스템 테스트 (20+ 테스트 케이스)
"""

import sys
import os
import pytest
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.safety_system_v2 import (
    SafetySystem,
    KeywordDetector,
    SentimentAnalyzer,
    PatternRecognizer,
    LLMCrisisEvaluator,
    RiskLevel
)
from src.emotion_analyzer_v2 import KoreanEmotionAnalyzer


# ============================================================================
# 다층 안전 시스템 테스트
# ============================================================================

class TestKeywordDetector:
    """Layer 1: 키워드 감지기 테스트"""

    @pytest.fixture
    def detector(self):
        return KeywordDetector()

    def test_critical_direct_suicide(self, detector):
        """테스트 1: CRITICAL - 직접적 자살 표현"""
        text = "죽고 싶어요. 자살하고 싶어요."
        result = detector.detect(text)

        assert result["risk_level"] == RiskLevel.CRITICAL
        assert len(result["detected_keywords"]) >= 2
        assert result["confidence"] > 0.9

    def test_critical_suicide_plan(self, detector):
        """테스트 2: CRITICAL - 자살 계획"""
        text = "준비를 다 했어요. 오늘 중에 끝낼 거예요."
        result = detector.detect(text)

        assert result["risk_level"] == RiskLevel.CRITICAL
        assert "suicide_plan" in result["categories"] or "immediate_danger" in result["categories"]

    def test_critical_immediate_danger(self, detector):
        """테스트 3: CRITICAL - 즉각적 위험"""
        text = "지금 당장 약을 먹었어요."
        result = detector.detect(text)

        assert result["risk_level"] == RiskLevel.CRITICAL
        assert "immediate_danger" in result["categories"]

    def test_high_indirect_suicide(self, detector):
        """테스트 4: HIGH - 간접적 자살 표현"""
        text = "사라지고 싶어요. 없어지고 싶어요."
        result = detector.detect(text)

        assert result["risk_level"] in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert "indirect_suicide" in result["categories"]

    def test_high_self_harm(self, detector):
        """테스트 5: HIGH - 자해 관련"""
        text = "자해를 하고 싶어요. 칼로 긋고 싶어요."
        result = detector.detect(text)

        assert result["risk_level"] == RiskLevel.HIGH
        assert "self_harm" in result["categories"]

    def test_high_hopelessness(self, detector):
        """테스트 6: HIGH - 절망감"""
        text = "희망이 없어요. 아무것도 나아지지 않아요."
        result = detector.detect(text)

        assert result["risk_level"] in [RiskLevel.HIGH, RiskLevel.MEDIUM]
        assert "hopelessness" in result["categories"]

    def test_medium_burden_thoughts(self, detector):
        """테스트 7: MEDIUM - 부담감 (한국 문화적)"""
        text = "가족에게 폐만 끼치는 것 같아요. 짐이 되는 것 같아요."
        result = detector.detect(text)

        assert result["risk_level"] in [RiskLevel.MEDIUM, RiskLevel.HIGH]
        assert "burden_thoughts" in result["categories"]

    def test_medium_isolation(self, detector):
        """테스트 8: MEDIUM - 고립감"""
        text = "아무도 없어요. 혼자예요. 외로워요."
        result = detector.detect(text)

        assert result["risk_level"] == RiskLevel.MEDIUM
        assert "isolation" in result["categories"]

    def test_low_general_distress(self, detector):
        """테스트 9: LOW - 일반적 고통"""
        text = "힘들어요. 우울해요."
        result = detector.detect(text)

        assert result["risk_level"] == RiskLevel.LOW

    def test_none_normal_conversation(self, detector):
        """테스트 10: NONE - 정상 대화"""
        text = "오늘 날씨가 좋네요."
        result = detector.detect(text)

        assert result["risk_level"] == RiskLevel.NONE


class TestSentimentAnalyzer:
    """Layer 2: 감정 분석기 테스트"""

    @pytest.fixture
    def analyzer(self):
        return SentimentAnalyzer(history_size=10)

    def test_high_intensity_detection(self, analyzer):
        """테스트 11: 높은 감정 강도 감지"""
        text = "너무너무 힘들어요!!! 정말 견딜 수가 없어요!!!"
        result = analyzer.analyze(text)

        assert result["intensity"] >= 7.0
        assert result["negativity"] >= 5.0

    def test_cumulative_negativity(self, analyzer):
        """테스트 12: 누적 부정성 추적"""
        texts = [
            "조금 우울해요",
            "많이 힘들어요",
            "너무 괴로워요",
            "견딜 수 없어요"
        ]

        for text in texts:
            result = analyzer.analyze(text)

        # 누적 부정성이 증가해야 함
        assert result["cumulative_negativity"] > 5.0

    def test_rapid_change_detection(self, analyzer):
        """테스트 13: 급격한 감정 변화 감지"""
        # 처음엔 중립
        analyzer.analyze("괜찮아요.")

        # 갑자기 급격히 악화
        result = analyzer.analyze("극도로 괴롭고 견딜 수 없어요. 죽고 싶어요.")

        assert result["rapid_change"] is True

    def test_trend_worsening(self, analyzer):
        """테스트 14: 악화 추세 감지"""
        texts = [
            "조금 힘들어요",
            "많이 힘들어요",
            "너무 힘들어요"
        ]

        for text in texts:
            result = analyzer.analyze(text)

        assert result["trend"] in ["worsening", "stable"]


class TestPatternRecognizer:
    """Layer 3: 패턴 인식기 테스트"""

    @pytest.fixture
    def recognizer(self):
        return PatternRecognizer()

    def test_isolation_pattern(self, recognizer):
        """테스트 15: 고립 패턴 감지"""
        text = "아무도 없어요. 혼자예요. 외로워요."
        conversation_history = [
            {"role": "user", "content": "혼자 있어요"},
            {"role": "assistant", "content": "힘드시군요"},
            {"role": "user", "content": "아무도 연락할 사람이 없어요"},
            {"role": "assistant", "content": "이해합니다"},
            {"role": "user", "content": text}
        ]

        result = recognizer.analyze_patterns(text, conversation_history)

        assert result["isolation_pattern"]["detected"] is True
        assert result["isolation_pattern"]["frequency"] >= 3

    def test_hopelessness_pattern(self, recognizer):
        """테스트 16: 절망감 패턴 감지"""
        text = "희망이 없어요. 아무것도 바뀌지 않아요."
        result = recognizer.analyze_patterns(text)

        assert result["hopelessness_pattern"]["detected"] is True

    def test_high_risk_time(self, recognizer):
        """테스트 17: 고위험 시간대 (새벽) 감지"""
        # 새벽 2시 시뮬레이션
        late_night = datetime(2024, 1, 1, 2, 0, 0)
        result = recognizer.analyze_patterns("힘들어요", current_time=late_night)

        assert result["time_risk"]["is_high_risk_time"] is True
        assert result["time_risk"]["risk_level"] == "high"

    def test_repetitive_crisis(self, recognizer):
        """테스트 18: 반복적 위기 언급 감지"""
        conversation_history = [
            {"role": "user", "content": "죽고 싶어요"},
            {"role": "assistant", "content": "도와드리고 싶어요"},
            {"role": "user", "content": "자꾸 자살 생각이 나요"},
            {"role": "assistant", "content": "전문가 도움이 필요합니다"},
            {"role": "user", "content": "끝내고 싶어요"}
        ]

        result = recognizer.analyze_patterns("", conversation_history)

        assert result["repetitive_crisis_talk"]["detected"] is True
        assert result["repetitive_crisis_talk"]["mention_count"] >= 2


class TestLLMCrisisEvaluator:
    """Layer 4: 종합 위기 평가기 테스트"""

    @pytest.fixture
    def evaluator(self):
        return LLMCrisisEvaluator()

    @pytest.fixture
    def sample_results(self):
        """샘플 레이어 결과"""
        keyword_result = {
            "risk_level": RiskLevel.HIGH,
            "detected_keywords": ["죽고 싶", "사라지고 싶"],
            "confidence": 0.85
        }

        sentiment_result = {
            "intensity": 8.5,
            "negativity": 9.0,
            "cumulative_negativity": 7.5,
            "rapid_change": True,
            "history_length": 5
        }

        pattern_result = {
            "isolation_pattern": {"detected": True},
            "hopelessness_pattern": {"detected": True},
            "overall_risk_score": 7.0,
            "risk_flags": ["isolation", "hopelessness"]
        }

        return keyword_result, sentiment_result, pattern_result

    def test_evaluation_high_risk(self, evaluator, sample_results):
        """테스트 19: HIGH 위험도 종합 평가"""
        keyword_result, sentiment_result, pattern_result = sample_results

        result = evaluator.evaluate(
            "죽고 싶어요. 사라지고 싶어요.",
            keyword_result,
            sentiment_result,
            pattern_result
        )

        assert result["risk_level"] in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert result["requires_intervention"] is True
        assert len(result["recommended_resources"]) > 0

    def test_intervention_message_critical(self, evaluator):
        """테스트 20: CRITICAL 개입 메시지 생성"""
        keyword_result = {
            "risk_level": RiskLevel.CRITICAL,
            "detected_keywords": ["죽고 싶", "오늘", "준비"],
            "confidence": 0.95
        }

        sentiment_result = {
            "intensity": 10.0,
            "negativity": 10.0,
            "cumulative_negativity": 9.0,
            "rapid_change": True
        }

        pattern_result = {
            "overall_risk_score": 9.0,
            "risk_flags": ["immediate", "plan"]
        }

        result = evaluator.evaluate(
            "오늘 죽을 거예요. 준비 다 했어요.",
            keyword_result,
            sentiment_result,
            pattern_result
        )

        assert result["risk_level"] == RiskLevel.CRITICAL
        assert "1393" in result["intervention_message"]  # 자살예방상담전화
        assert result["action"] == "IMMEDIATE_INTERVENTION"


class TestSafetySystemIntegration:
    """통합 안전 시스템 테스트"""

    @pytest.fixture
    def safety_system(self):
        return SafetySystem(user_id="test_user")

    def test_integrated_critical_detection(self, safety_system):
        """테스트 21: 통합 CRITICAL 감지"""
        text = "죽고 싶어요. 오늘 중에 끝낼 거예요."
        result = safety_system.check_safety(text)

        assert result["risk_level"] == RiskLevel.CRITICAL
        assert result["requires_intervention"] is True
        assert len(safety_system.crisis_logs) > 0

    def test_phq9_screening(self, safety_system):
        """테스트 22: PHQ-9 Item 9 스크리닝"""
        # 거의 매일
        text1 = "매일 죽고 싶다는 생각이 들어요. 끊임없이 생각나요."
        result1 = safety_system.phq9_item9_screening(text1)

        assert result1["score"] == 3  # 거의 매일
        assert result1["risk_present"] is True

        # 며칠
        text2 = "가끔 죽고 싶다는 생각이 들어요."
        result2 = safety_system.phq9_item9_screening(text2)

        assert result2["score"] in [1, 2]
        assert result2["risk_present"] is True

    def test_crisis_logging(self, safety_system):
        """테스트 23: 위기 로깅 기능"""
        texts = [
            "죽고 싶어요",
            "자해하고 싶어요",
            "사라지고 싶어요"
        ]

        for text in texts:
            safety_system.check_safety(text)

        crisis_history = safety_system.get_crisis_history()

        assert len(crisis_history) >= 3
        assert all("timestamp" in log for log in crisis_history)

    def test_risk_trend_analysis(self, safety_system):
        """테스트 24: 위험도 추세 분석"""
        # 점점 악화되는 시퀀스
        texts = [
            "조금 힘들어요",
            "많이 힘들어요",
            "죽고 싶어요"
        ]

        for text in texts:
            safety_system.check_safety(text)

        trend = safety_system.get_risk_trend()

        assert trend["trend"] in ["escalating", "stable"]


# ============================================================================
# 한국어 감정 분석 시스템 테스트
# ============================================================================

class TestKoreanEmotionAnalyzer:
    """한국어 감정 분석기 테스트"""

    @pytest.fixture
    def analyzer(self):
        return KoreanEmotionAnalyzer()

    def test_basic_joy(self, analyzer):
        """테스트 25: 기쁨 감정 감지"""
        text = "너무 기쁘고 행복해요! 정말 좋아요!"
        result = analyzer.analyze(text)

        assert result["primary_emotion"] == "기쁨"
        assert result["intensity"] >= 7.0

    def test_basic_sadness(self, analyzer):
        """테스트 26: 슬픔 감정 감지"""
        text = "너무 슬프고 눈물이 나요. 울고 싶어요."
        result = analyzer.analyze(text)

        assert result["primary_emotion"] == "슬픔"
        assert result["intensity"] >= 6.0

    def test_basic_anger(self, analyzer):
        """테스트 27: 분노 감정 감지"""
        text = "정말 화나요. 짜증나고 열받아요."
        result = analyzer.analyze(text)

        assert result["primary_emotion"] == "분노"
        assert result["intensity"] >= 6.0

    def test_basic_fear(self, analyzer):
        """테스트 28: 두려움 감정 감지"""
        text = "너무 무서워요. 두렵고 떨려요."
        result = analyzer.analyze(text)

        assert result["primary_emotion"] == "두려움"
        assert result["intensity"] >= 6.0

    def test_korean_han(self, analyzer):
        """테스트 29: 한(恨) 감정 감지"""
        text = "한스럽고 원망스러워요. 맺힌 게 많아요."
        result = analyzer.analyze(text)

        assert result["primary_emotion"] == "한"
        assert "한" in result["emotion_details"]["korean_emotions"]

    def test_korean_jung(self, analyzer):
        """테스트 30: 정(情) 감정 감지"""
        text = "정이 많이 들었어요. 정겨운 사람이에요."
        result = analyzer.analyze(text)

        assert result["primary_emotion"] == "정"

    def test_korean_seoroom(self, analyzer):
        """테스트 31: 서러움 감정 감지"""
        text = "서럽고 눈물겨워요. 너무 서글퍼요."
        result = analyzer.analyze(text)

        assert result["primary_emotion"] == "서러움"

    def test_intensity_maximum(self, analyzer):
        """테스트 32: 최대 강도 (10) 측정"""
        text = "극도로 괴롭고 견딜 수 없어요!!! 정말정말 힘들어요!!!"
        result = analyzer.analyze(text)

        assert result["intensity"] >= 9.0

    def test_intensity_minimum(self, analyzer):
        """테스트 33: 최소 강도 측정"""
        text = "약간 힘들어요."
        result = analyzer.analyze(text)

        assert result["intensity"] <= 6.0

    def test_age_group_teenager(self, analyzer):
        """테스트 34: 10대 표현 인식"""
        text = "학교에서 친구들이랑 짱나는 일이 있었어 ㅠㅠ 개짜증"
        result = analyzer.analyze(text)

        assert result["age_group_estimated"] == "10대"

    def test_age_group_twenties_thirties(self, analyzer):
        """테스트 35: 20-30대 표현 인식"""
        text = "회사 상사가 너무 스트레스예요. 야근 많고 번아웃 왔어요."
        result = analyzer.analyze(text)

        assert result["age_group_estimated"] == "20-30대"

    def test_age_group_forties_plus(self, analyzer):
        """테스트 36: 40대 이상 표현 인식"""
        text = "자식 걱정에 잠을 못 자요. 건강도 안 좋고요."
        result = analyzer.analyze(text)

        assert result["age_group_estimated"] == "40대이상"

    def test_cultural_marker_indirect(self, analyzer):
        """테스트 37: 간접 표현 마커"""
        text = "그냥 그래요. 별거 아니에요."
        result = analyzer.analyze(text)

        assert "간접표현" in result["cultural_markers"]

    def test_cultural_marker_face(self, analyzer):
        """테스트 38: 체면 중시 마커"""
        text = "창피하고 부끄러워요. 체면이 말이 아니에요."
        result = analyzer.analyze(text)

        assert "체면중시" in result["cultural_markers"]

    def test_cultural_marker_collective(self, analyzer):
        """테스트 39: 집단주의 마커"""
        text = "가족들이 실망할까 봐 걱정돼요. 주변 눈치가 보여요."
        result = analyzer.analyze(text)

        assert "집단주의" in result["cultural_markers"]

    def test_complex_emotions(self, analyzer):
        """테스트 40: 복합 감정 감지"""
        text = "기쁘기도 하고 슬프기도 해요. 복잡한 마음이에요."
        result = analyzer.analyze(text)

        assert result["emotion_details"]["complex_emotions"]["is_complex"] is True
        assert len(result["secondary_emotions"]) >= 1

    def test_emotion_trend(self, analyzer):
        """테스트 41: 감정 변화 추세"""
        texts = [
            "조금 우울해요",
            "많이 우울해요",
            "너무 우울해요"
        ]

        for text in texts:
            analyzer.analyze(text)

        trend = analyzer.get_emotion_trend()

        assert trend["intensity_trend"] in ["increasing", "stable"]

    def test_formality_assessment(self, analyzer):
        """테스트 42: 격식 수준 평가"""
        # Formal
        text1 = "정말 힘듭니다. 도와주시겠습니까?"
        result1 = analyzer.analyze(text1)
        assert result1["text_features"]["formality"] == "formal"

        # Casual
        text2 = "ㅋㅋㅋ 진짜 대박 ㅇㅇ"
        result2 = analyzer.analyze(text2)
        assert result2["text_features"]["formality"] == "casual"


# ============================================================================
# 통합 테스트
# ============================================================================

def test_safety_emotion_integration():
    """테스트 43: 안전 시스템 + 감정 분석 통합"""
    safety_system = SafetySystem(user_id="integration_test")
    emotion_analyzer = KoreanEmotionAnalyzer()

    text = "너무 우울하고 죽고 싶어요. 견딜 수가 없어요."

    # 감정 분석
    emotion_result = emotion_analyzer.analyze(text)

    # 안전 체크 (감정 데이터 포함)
    safety_result = safety_system.check_safety(text, emotion_data=emotion_result)

    # 감정은 우울
    assert emotion_result["primary_emotion"] in ["우울", "슬픔"]

    # 안전은 HIGH 또는 CRITICAL
    assert safety_result["risk_level"] in [RiskLevel.HIGH, RiskLevel.CRITICAL]

    # 개입 필요
    assert safety_result["requires_intervention"] is True


def run_manual_tests():
    """수동 테스트 실행"""
    print("\n" + "=" * 80)
    print("Phase 2 시스템 수동 테스트")
    print("=" * 80 + "\n")

    # 안전 시스템 테스트
    print("1. 다층 안전 시스템 테스트\n")

    safety_system = SafetySystem(user_id="manual_test")

    test_cases_safety = [
        ("죽고 싶어요. 오늘 중에 끝낼 거예요.", "CRITICAL 예상"),
        ("사라지고 싶어요. 자해하고 싶어요.", "HIGH 예상"),
        ("가족에게 폐만 끼치는 것 같아요.", "MEDIUM 예상 - 한국 문화"),
        ("힘들어요. 우울해요.", "LOW 예상"),
    ]

    for text, expected in test_cases_safety:
        result = safety_system.check_safety(text)
        print(f"입력: {text}")
        print(f"예상: {expected}")
        print(f"결과: {result['risk_level'].value}")
        print(f"가중 점수: {result['weighted_score']}/10")
        print(f"개입 필요: {result['requires_intervention']}")
        print("-" * 80 + "\n")

    # 감정 분석 테스트
    print("\n2. 한국어 감정 분석 시스템 테스트\n")

    emotion_analyzer = KoreanEmotionAnalyzer()

    test_cases_emotion = [
        ("너무너무 기쁘고 행복해요!!!", "기쁨 + 높은 강도"),
        ("학교에서 친구들이랑 싸워서 빡쳐 ㅠㅠ", "분노 + 10대"),
        ("회사 상사가 스트레스예요. 번아웃 왔어요.", "스트레스 + 20-30대"),
        ("한스럽고 서러워요. 원망스러워요.", "한 + 서러움"),
        ("그냥 그래요. 별거 아니에요.", "간접 표현"),
    ]

    for text, expected in test_cases_emotion:
        result = emotion_analyzer.analyze(text)
        print(f"입력: {text}")
        print(f"예상: {expected}")
        print(f"주요 감정: {result['primary_emotion']}")
        print(f"강도: {result['intensity']}/10")
        print(f"연령대: {result['age_group_estimated'] or '미추정'}")
        print(f"문화적 마커: {', '.join(result['cultural_markers']) or '없음'}")
        print("-" * 80 + "\n")


if __name__ == "__main__":
    # pytest 실행
    print("=" * 80)
    print("자동화 테스트 실행 (pytest)")
    print("=" * 80)

    pytest.main([__file__, "-v", "--tb=short"])

    # 수동 테스트 실행
    run_manual_tests()

    print("\n" + "=" * 80)
    print(f"총 43개 테스트 완료")
    print("=" * 80)
