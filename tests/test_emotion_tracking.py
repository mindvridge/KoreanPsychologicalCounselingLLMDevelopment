"""
Emotion Tracking Module Tests
감정 추적 모듈 테스트

테스트 대상:
- EmotionAnalyzer: 감정 분석
- EmotionTracker: 감정 기록 및 추적
- EmotionVisualizer: 시각화 데이터 생성
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.emotion_tracking import (
    EmotionCategory,
    EmotionRecord,
    EmotionAnalyzer,
    EmotionTracker,
    EmotionVisualizer,
    DailyEmotionSummary,
    WeeklyReport,
    get_emotion_tracker,
    get_emotion_visualizer
)


# ============================================================================
# EmotionCategory Tests
# ============================================================================

class TestEmotionCategory:
    """감정 카테고리 테스트"""

    def test_emotion_categories_exist(self):
        """모든 감정 카테고리 존재 확인"""
        expected_emotions = [
            "기쁨", "슬픔", "분노", "두려움", "불안",
            "평온", "희망", "외로움", "스트레스", "감사", "중립"
        ]

        actual_values = [e.value for e in EmotionCategory]

        for emotion in expected_emotions:
            assert emotion in actual_values

    def test_emotion_category_values(self):
        """감정 카테고리 값 확인"""
        assert EmotionCategory.JOY.value == "기쁨"
        assert EmotionCategory.SADNESS.value == "슬픔"
        assert EmotionCategory.ANXIETY.value == "불안"
        assert EmotionCategory.NEUTRAL.value == "중립"


# ============================================================================
# EmotionAnalyzer Tests
# ============================================================================

class TestEmotionAnalyzer:
    """감정 분석기 테스트"""

    @pytest.fixture
    def analyzer(self):
        return EmotionAnalyzer()

    def test_analyze_joy(self, analyzer):
        """기쁨 감정 분석"""
        text = "오늘 정말 행복해요! 기분이 너무 좋아요."
        result = analyzer.analyze(text)

        assert result.primary_emotion == EmotionCategory.JOY
        assert result.valence > 0  # 긍정

    def test_analyze_sadness(self, analyzer):
        """슬픔 감정 분석"""
        text = "너무 슬프고 우울해요. 눈물이 나요."
        result = analyzer.analyze(text)

        assert result.primary_emotion == EmotionCategory.SADNESS
        assert result.valence < 0  # 부정

    def test_analyze_anger(self, analyzer):
        """분노 감정 분석"""
        text = "정말 화가 나요! 너무 짜증나요."
        result = analyzer.analyze(text)

        assert result.primary_emotion == EmotionCategory.ANGER
        assert result.arousal > 0.5  # 높은 활성화

    def test_analyze_anxiety(self, analyzer):
        """불안 감정 분석"""
        text = "불안하고 걱정돼요. 초조해요."
        result = analyzer.analyze(text)

        assert result.primary_emotion == EmotionCategory.ANXIETY

    def test_analyze_calm(self, analyzer):
        """평온 감정 분석"""
        text = "마음이 편안하고 차분해요. 여유로워요."
        result = analyzer.analyze(text)

        assert result.primary_emotion == EmotionCategory.CALM
        assert result.arousal < 0.5  # 낮은 활성화

    def test_analyze_neutral(self, analyzer):
        """중립 감정 분석"""
        text = "네, 알겠습니다."
        result = analyzer.analyze(text)

        assert result.primary_emotion == EmotionCategory.NEUTRAL

    def test_analyze_with_intensity_modifier(self, analyzer):
        """강도 수정자 적용"""
        text_normal = "슬퍼요"
        text_intense = "너무 너무 슬퍼요"

        result_normal = analyzer.analyze(text_normal)
        result_intense = analyzer.analyze(text_intense)

        assert result_intense.intensity >= result_normal.intensity

    def test_analyze_loneliness(self, analyzer):
        """외로움 감정 분석"""
        text = "너무 외로워요. 혼자인 것 같아요."
        result = analyzer.analyze(text)

        assert result.primary_emotion == EmotionCategory.LONELINESS

    def test_analyze_stress(self, analyzer):
        """스트레스 감정 분석"""
        text = "스트레스 받아요. 너무 지쳐요."
        result = analyzer.analyze(text)

        assert result.primary_emotion == EmotionCategory.STRESS

    def test_analyze_hope(self, analyzer):
        """희망 감정 분석"""
        text = "희망이 생겨요. 할 수 있을 것 같아요."
        result = analyzer.analyze(text)

        assert result.primary_emotion == EmotionCategory.HOPE
        assert result.valence > 0

    def test_emotion_record_has_timestamp(self, analyzer):
        """감정 기록에 타임스탬프 존재"""
        result = analyzer.analyze("테스트 메시지")

        assert result.timestamp is not None
        assert isinstance(result.timestamp, datetime)

    def test_valence_arousal_ranges(self, analyzer):
        """valence/arousal 값 범위 확인"""
        texts = [
            "기뻐요", "슬퍼요", "화나요", "불안해요",
            "평온해요", "희망적이에요", "스트레스 받아요"
        ]

        for text in texts:
            result = analyzer.analyze(text)
            assert -1.0 <= result.valence <= 1.0
            assert 0.0 <= result.arousal <= 1.0
            assert 0.0 <= result.intensity <= 1.0


# ============================================================================
# EmotionTracker Tests
# ============================================================================

class TestEmotionTracker:
    """감정 추적기 테스트"""

    @pytest.fixture
    def tracker(self):
        return EmotionTracker()

    def test_record_emotion(self, tracker):
        """감정 기록"""
        record = tracker.record_emotion(
            user_id="user1",
            text="오늘 기분이 좋아요",
            session_id="session1"
        )

        assert record is not None
        assert record.session_id == "session1"

    def test_multiple_records(self, tracker):
        """다중 기록"""
        tracker.record_emotion("user1", "기뻐요")
        tracker.record_emotion("user1", "슬퍼요")
        tracker.record_emotion("user1", "화나요")

        records = tracker.get_recent_emotions("user1", hours=24)
        assert len(records) == 3

    def test_get_recent_emotions(self, tracker):
        """최근 감정 조회"""
        tracker.record_emotion("user1", "테스트1")
        tracker.record_emotion("user1", "테스트2")

        records = tracker.get_recent_emotions("user1", hours=1)
        assert len(records) >= 2

    def test_user_isolation(self, tracker):
        """사용자별 격리"""
        tracker.record_emotion("user1", "기뻐요")
        tracker.record_emotion("user2", "슬퍼요")

        user1_records = tracker.get_recent_emotions("user1")
        user2_records = tracker.get_recent_emotions("user2")

        assert len(user1_records) == 1
        assert len(user2_records) == 1

    def test_get_emotion_by_date(self, tracker):
        """날짜별 감정 조회"""
        tracker.record_emotion("user1", "오늘의 감정")

        today = datetime.now()
        records = tracker.get_emotion_by_date("user1", today)

        assert len(records) >= 1

    def test_daily_summary(self, tracker):
        """일별 요약 생성"""
        # 여러 감정 기록
        tracker.record_emotion("user1", "기뻐요")
        tracker.record_emotion("user1", "슬퍼요")
        tracker.record_emotion("user1", "기뻐요")

        summary = tracker.get_daily_summary("user1", datetime.now())

        assert summary is not None
        assert summary.record_count >= 3
        assert summary.emotion_distribution is not None

    def test_empty_daily_summary(self, tracker):
        """기록 없는 날 요약"""
        yesterday = datetime.now() - timedelta(days=1)
        summary = tracker.get_daily_summary("nonexistent", yesterday)

        assert summary is None


# ============================================================================
# EmotionVisualizer Tests
# ============================================================================

class TestEmotionVisualizer:
    """감정 시각화 테스트"""

    @pytest.fixture
    def visualizer(self):
        tracker = EmotionTracker()
        # 테스트 데이터 추가
        for i in range(7):
            tracker.record_emotion("user1", "기분이 좋아요")
            tracker.record_emotion("user1", "조금 불안해요")
        return EmotionVisualizer(tracker)

    def test_generate_chart_data(self, visualizer):
        """차트 데이터 생성"""
        data = visualizer.generate_emotion_chart_data("user1", days=7)

        assert data is not None
        assert "labels" in data
        assert "datasets" in data
        assert len(data["labels"]) == 7

    def test_generate_pie_data(self, visualizer):
        """파이 차트 데이터 생성"""
        data = visualizer.generate_emotion_pie_data("user1", days=7)

        assert data is not None
        assert "labels" in data
        assert "datasets" in data

    def test_weekly_report(self, visualizer):
        """주간 리포트 생성"""
        report = visualizer.generate_weekly_report("user1")

        assert report is not None
        assert hasattr(report, "overall_trend")
        assert hasattr(report, "insights")
        assert hasattr(report, "recommendations")

    def test_weekly_report_text_format(self, visualizer):
        """주간 리포트 텍스트 포맷"""
        report = visualizer.generate_weekly_report("user1")
        text = visualizer.format_weekly_report_text(report)

        assert "주간 감정 리포트" in text
        assert len(text) > 100


# ============================================================================
# Integration Tests
# ============================================================================

class TestEmotionTrackingIntegration:
    """통합 테스트"""

    def test_full_workflow(self):
        """전체 워크플로우"""
        tracker = EmotionTracker()
        visualizer = EmotionVisualizer(tracker)

        # 1. 감정 기록
        for emotion_text in ["기뻐요", "슬퍼요", "화나요", "평온해요"]:
            tracker.record_emotion("user1", emotion_text)

        # 2. 차트 데이터 생성
        chart_data = visualizer.generate_emotion_chart_data("user1")
        assert chart_data is not None

        # 3. 주간 리포트 생성
        report = visualizer.generate_weekly_report("user1")
        assert report is not None

    def test_singleton_pattern(self):
        """싱글톤 패턴 확인"""
        tracker1 = get_emotion_tracker()
        tracker2 = get_emotion_tracker()

        # 같은 인스턴스여야 함
        assert tracker1 is tracker2


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    """엣지 케이스 테스트"""

    def test_empty_text(self):
        """빈 텍스트 분석"""
        analyzer = EmotionAnalyzer()
        result = analyzer.analyze("")

        assert result.primary_emotion == EmotionCategory.NEUTRAL

    def test_very_long_text(self):
        """매우 긴 텍스트"""
        analyzer = EmotionAnalyzer()
        long_text = "기뻐요 " * 1000
        result = analyzer.analyze(long_text)

        assert result is not None
        assert len(result.user_text) <= 200  # 200자로 잘림

    def test_special_characters(self):
        """특수문자 처리"""
        analyzer = EmotionAnalyzer()
        text = "기뻐요!!! ^^;; ㅠㅠ 😊"
        result = analyzer.analyze(text)

        assert result is not None

    def test_mixed_emotions(self):
        """복합 감정"""
        analyzer = EmotionAnalyzer()
        text = "기쁘기도 하고 슬프기도 해요"
        result = analyzer.analyze(text)

        # 주 감정과 부 감정 모두 있을 수 있음
        assert result.primary_emotion is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
