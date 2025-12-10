"""
Conversational Assessment Module Tests
대화형 심리검사 모듈 테스트

테스트 대상:
- ConversationalAssessment: 대화형 심리검사
- AssessmentHistory: 검사 기록
- 자연어 응답 파싱
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.conversational_assessment import (
    AssessmentType,
    AssessmentResult,
    ConversationalAssessment,
    AssessmentHistory
)


# ============================================================================
# AssessmentType Tests
# ============================================================================

class TestAssessmentType:
    """검사 유형 테스트"""

    def test_phq9_type(self):
        """PHQ-9 유형"""
        assert AssessmentType.PHQ9.value == "phq9"

    def test_gad7_type(self):
        """GAD-7 유형"""
        assert AssessmentType.GAD7.value == "gad7"


# ============================================================================
# ConversationalAssessment Tests
# ============================================================================

class TestConversationalAssessment:
    """대화형 심리검사 테스트"""

    @pytest.fixture
    def assessment(self):
        return ConversationalAssessment()

    # -------------------------------------------------------------------------
    # PHQ-9 Tests
    # -------------------------------------------------------------------------

    def test_start_phq9_assessment(self, assessment):
        """PHQ-9 검사 시작"""
        first_question = assessment.start_assessment(
            session_id="test-session",
            assessment_type=AssessmentType.PHQ9,
            user_name="테스트"
        )

        assert first_question is not None
        assert len(first_question) > 0

    def test_phq9_full_flow(self, assessment):
        """PHQ-9 전체 흐름"""
        assessment.start_assessment("s1", AssessmentType.PHQ9)

        responses = [
            "전혀 없었어요",
            "거의 매일 그랬어요",
            "일주일에 며칠 그랬어요",
            "전혀 없었어요",
            "절반 이상 그랬어요",
            "전혀 없었어요",
            "며칠 그랬어요",
            "전혀 없었어요",
            "전혀 없었어요"  # 9번 문항 - 자해 관련
        ]

        result = None
        for response in responses:
            next_msg, result = assessment.process_response("s1", response)

        assert result is not None
        assert result.assessment_type == AssessmentType.PHQ9
        assert result.total_score >= 0
        assert result.severity is not None

    def test_phq9_score_calculation(self, assessment):
        """PHQ-9 점수 계산"""
        assessment.start_assessment("s1", AssessmentType.PHQ9)

        # 모든 응답을 "전혀 없었어요" (0점)
        for _ in range(9):
            _, result = assessment.process_response("s1", "전혀 없었어요")

        assert result is not None
        assert result.total_score == 0
        assert result.severity == "minimal"

    def test_phq9_severity_levels(self, assessment):
        """PHQ-9 심각도 수준"""
        # Minimal: 0-4
        # Mild: 5-9
        # Moderate: 10-14
        # Moderately Severe: 15-19
        # Severe: 20-27

        assessment.start_assessment("s1", AssessmentType.PHQ9)

        # 높은 점수 응답
        for _ in range(9):
            _, result = assessment.process_response("s1", "거의 매일 그랬어요")

        assert result is not None
        assert result.total_score == 27  # 9 * 3
        assert result.severity == "severe"

    # -------------------------------------------------------------------------
    # GAD-7 Tests
    # -------------------------------------------------------------------------

    def test_start_gad7_assessment(self, assessment):
        """GAD-7 검사 시작"""
        first_question = assessment.start_assessment(
            session_id="test-session",
            assessment_type=AssessmentType.GAD7
        )

        assert first_question is not None

    def test_gad7_full_flow(self, assessment):
        """GAD-7 전체 흐름"""
        assessment.start_assessment("s1", AssessmentType.GAD7)

        responses = [
            "전혀 없었어요",
            "며칠 그랬어요",
            "절반 이상",
            "전혀 없었어요",
            "며칠",
            "전혀 없었어요",
            "전혀 없었어요"
        ]

        result = None
        for response in responses:
            _, result = assessment.process_response("s1", response)

        assert result is not None
        assert result.assessment_type == AssessmentType.GAD7

    def test_gad7_severity_levels(self, assessment):
        """GAD-7 심각도 수준"""
        assessment.start_assessment("s1", AssessmentType.GAD7)

        # 모든 응답 최대 (3점)
        for _ in range(7):
            _, result = assessment.process_response("s1", "거의 매일")

        assert result.total_score == 21  # 7 * 3
        assert result.severity == "severe"

    # -------------------------------------------------------------------------
    # Response Parsing Tests
    # -------------------------------------------------------------------------

    def test_parse_response_none(self, assessment):
        """'전혀 없었어요' 응답 파싱"""
        assessment.start_assessment("s1", AssessmentType.PHQ9)
        _, _ = assessment.process_response("s1", "전혀 없었어요")

        session = assessment.active_sessions.get("s1")
        if session:
            assert 0 in session["scores"]

    def test_parse_response_several(self, assessment):
        """'며칠' 응답 파싱"""
        assessment.start_assessment("s1", AssessmentType.PHQ9)
        _, _ = assessment.process_response("s1", "며칠 그랬어요")

        session = assessment.active_sessions.get("s1")
        if session:
            assert 1 in session["scores"]

    def test_parse_response_more_than_half(self, assessment):
        """'절반 이상' 응답 파싱"""
        assessment.start_assessment("s1", AssessmentType.PHQ9)
        _, _ = assessment.process_response("s1", "절반 이상이요")

        session = assessment.active_sessions.get("s1")
        if session:
            assert 2 in session["scores"]

    def test_parse_response_nearly_everyday(self, assessment):
        """'거의 매일' 응답 파싱"""
        assessment.start_assessment("s1", AssessmentType.PHQ9)
        _, _ = assessment.process_response("s1", "거의 매일 그래요")

        session = assessment.active_sessions.get("s1")
        if session:
            assert 3 in session["scores"]

    def test_parse_ambiguous_response(self, assessment):
        """애매한 응답 처리"""
        assessment.start_assessment("s1", AssessmentType.PHQ9)
        next_msg, _ = assessment.process_response("s1", "글쎄요...")

        # 다시 질문해야 함
        assert next_msg is not None

    # -------------------------------------------------------------------------
    # Crisis Detection Tests
    # -------------------------------------------------------------------------

    def test_phq9_crisis_detection(self, assessment):
        """PHQ-9 위기 감지 (9번 문항)"""
        assessment.start_assessment("s1", AssessmentType.PHQ9)

        # 8개 문항 응답
        for _ in range(8):
            assessment.process_response("s1", "전혀 없었어요")

        # 9번 문항 (자해 관련) - 높은 점수
        next_msg, result = assessment.process_response("s1", "거의 매일 그런 생각이 들어요")

        assert result is not None
        assert result.professional_help_suggested == True

    # -------------------------------------------------------------------------
    # Assessment Suggestion Tests
    # -------------------------------------------------------------------------

    def test_suggest_depression_assessment(self, assessment):
        """우울 키워드로 PHQ-9 추천"""
        history = [
            {"role": "user", "content": "요즘 너무 우울해요"},
            {"role": "user", "content": "아무것도 하기 싫어요"}
        ]

        suggestion = assessment.suggest_assessment(history)

        assert suggestion is not None
        assert suggestion[0] == AssessmentType.PHQ9

    def test_suggest_anxiety_assessment(self, assessment):
        """불안 키워드로 GAD-7 추천"""
        history = [
            {"role": "user", "content": "너무 불안해요"},
            {"role": "user", "content": "걱정이 많아요"}
        ]

        suggestion = assessment.suggest_assessment(history)

        assert suggestion is not None
        assert suggestion[0] == AssessmentType.GAD7

    def test_no_suggestion_for_neutral(self, assessment):
        """중립 대화에서 추천 없음"""
        history = [
            {"role": "user", "content": "안녕하세요"},
            {"role": "user", "content": "날씨가 좋네요"}
        ]

        suggestion = assessment.suggest_assessment(history)

        assert suggestion is None


# ============================================================================
# AssessmentHistory Tests
# ============================================================================

class TestAssessmentHistory:
    """검사 기록 테스트"""

    @pytest.fixture
    def history(self):
        return AssessmentHistory()

    @pytest.fixture
    def sample_result(self):
        return AssessmentResult(
            assessment_type=AssessmentType.PHQ9,
            total_score=10,
            severity="moderate",
            interpretation="중등도 우울 증상",
            recommendations=["전문가 상담 권장"],
            question_scores={1: 1, 2: 2, 3: 1},
            completed_at=datetime.now(),
            professional_help_suggested=False
        )

    def test_add_result(self, history, sample_result):
        """결과 추가"""
        history.add_result("user1", sample_result)

        results = history.get_history("user1")
        assert len(results) == 1

    def test_get_history(self, history, sample_result):
        """기록 조회"""
        history.add_result("user1", sample_result)
        history.add_result("user1", sample_result)

        results = history.get_history("user1")
        assert len(results) == 2

    def test_get_history_by_type(self, history):
        """유형별 기록 조회"""
        phq9_result = AssessmentResult(
            assessment_type=AssessmentType.PHQ9,
            total_score=5, severity="mild", interpretation="",
            recommendations=[], question_scores={},
            completed_at=datetime.now(), professional_help_suggested=False
        )
        gad7_result = AssessmentResult(
            assessment_type=AssessmentType.GAD7,
            total_score=5, severity="mild", interpretation="",
            recommendations=[], question_scores={},
            completed_at=datetime.now(), professional_help_suggested=False
        )

        history.add_result("user1", phq9_result)
        history.add_result("user1", gad7_result)

        phq9_only = history.get_history("user1", AssessmentType.PHQ9)
        assert len(phq9_only) == 1
        assert phq9_only[0].assessment_type == AssessmentType.PHQ9

    def test_get_trend(self, history):
        """트렌드 분석"""
        for score in [15, 12, 10, 8, 5]:  # 개선 추세
            result = AssessmentResult(
                assessment_type=AssessmentType.PHQ9,
                total_score=score, severity="moderate",
                interpretation="", recommendations=[],
                question_scores={}, completed_at=datetime.now(),
                professional_help_suggested=False
            )
            history.add_result("user1", result)

        trend = history.get_trend("user1", AssessmentType.PHQ9)

        assert trend is not None
        # 점수가 낮아지는 추세 = 개선


# ============================================================================
# Integration Tests
# ============================================================================

class TestConversationalAssessmentIntegration:
    """통합 테스트"""

    def test_complete_assessment_workflow(self):
        """완전한 검사 워크플로우"""
        assessment = ConversationalAssessment()
        history = AssessmentHistory()

        # 1. 검사 시작
        first_q = assessment.start_assessment("s1", AssessmentType.PHQ9, "홍길동")
        assert "홍길동" in first_q

        # 2. 모든 질문 응답
        for _ in range(9):
            next_msg, result = assessment.process_response("s1", "전혀 없었어요")

        # 3. 결과 확인
        assert result is not None
        assert result.total_score == 0

        # 4. 기록 저장
        history.add_result("user1", result)

        # 5. 기록 조회
        saved = history.get_history("user1")
        assert len(saved) == 1


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    """엣지 케이스 테스트"""

    def test_invalid_session(self):
        """잘못된 세션"""
        assessment = ConversationalAssessment()

        with pytest.raises(KeyError):
            assessment.process_response("nonexistent", "응답")

    def test_response_after_completion(self):
        """완료 후 응답"""
        assessment = ConversationalAssessment()
        assessment.start_assessment("s1", AssessmentType.PHQ9)

        # 모든 질문 완료
        for _ in range(9):
            assessment.process_response("s1", "전혀 없었어요")

        # 추가 응답 시도
        with pytest.raises(KeyError):
            assessment.process_response("s1", "추가 응답")

    def test_special_characters_in_response(self):
        """특수문자 응답"""
        assessment = ConversationalAssessment()
        assessment.start_assessment("s1", AssessmentType.PHQ9)

        # 이모지 포함
        next_msg, _ = assessment.process_response("s1", "전혀 없었어요 😊")
        assert next_msg is not None

    def test_empty_response(self):
        """빈 응답"""
        assessment = ConversationalAssessment()
        assessment.start_assessment("s1", AssessmentType.PHQ9)

        next_msg, _ = assessment.process_response("s1", "")
        # 다시 질문해야 함
        assert next_msg is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
