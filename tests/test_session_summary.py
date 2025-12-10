"""
Session Summary Module Tests
세션 요약 모듈 테스트

테스트 대상:
- KeywordExtractor: 키워드/주제 추출
- SummaryGenerator: 요약 생성
- SessionSummaryManager: 요약 관리
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.session_summary import (
    TopicCategory,
    ConversationTurn,
    SessionSummary,
    KeywordExtractor,
    SummaryGenerator,
    SessionSummaryManager,
    get_summary_manager
)


# ============================================================================
# TopicCategory Tests
# ============================================================================

class TestTopicCategory:
    """주제 카테고리 테스트"""

    def test_topic_categories_exist(self):
        """모든 주제 카테고리 존재 확인"""
        expected_topics = [
            "대인관계", "직장/학업", "가족", "자존감", "불안",
            "우울", "스트레스", "트라우마", "삶의 변화",
            "실존적 고민", "건강", "경제", "기타"
        ]

        actual_values = [t.value for t in TopicCategory]

        for topic in expected_topics:
            assert topic in actual_values


# ============================================================================
# ConversationTurn Tests
# ============================================================================

class TestConversationTurn:
    """대화 턴 테스트"""

    def test_create_conversation_turn(self):
        """대화 턴 생성"""
        turn = ConversationTurn(
            role="user",
            content="안녕하세요",
            timestamp=datetime.now()
        )

        assert turn.role == "user"
        assert turn.content == "안녕하세요"

    def test_default_values(self):
        """기본값 확인"""
        turn = ConversationTurn(role="user", content="테스트")

        assert turn.timestamp is None
        assert turn.emotion is None
        assert turn.importance == 0.5


# ============================================================================
# KeywordExtractor Tests
# ============================================================================

class TestKeywordExtractor:
    """키워드 추출기 테스트"""

    @pytest.fixture
    def extractor(self):
        return KeywordExtractor()

    def test_extract_relationship_topic(self, extractor):
        """대인관계 주제 추출"""
        conversation = [
            ConversationTurn(role="user", content="친구와 다퉜어요. 관계가 힘들어요.")
        ]

        topics = extractor.extract_topics(conversation)

        assert len(topics) > 0
        topic_values = [t[0] for t in topics]
        assert TopicCategory.RELATIONSHIP in topic_values

    def test_extract_work_topic(self, extractor):
        """직장 주제 추출"""
        conversation = [
            ConversationTurn(role="user", content="회사에서 상사한테 혼났어요. 업무가 너무 힘들어요.")
        ]

        topics = extractor.extract_topics(conversation)

        topic_values = [t[0] for t in topics]
        assert TopicCategory.WORK in topic_values

    def test_extract_family_topic(self, extractor):
        """가족 주제 추출"""
        conversation = [
            ConversationTurn(role="user", content="부모님과 갈등이 있어요. 아버지가 화를 내셨어요.")
        ]

        topics = extractor.extract_topics(conversation)

        topic_values = [t[0] for t in topics]
        assert TopicCategory.FAMILY in topic_values

    def test_extract_anxiety_topic(self, extractor):
        """불안 주제 추출"""
        conversation = [
            ConversationTurn(role="user", content="불안하고 걱정돼요. 무서워요.")
        ]

        topics = extractor.extract_topics(conversation)

        topic_values = [t[0] for t in topics]
        assert TopicCategory.ANXIETY in topic_values

    def test_extract_depression_topic(self, extractor):
        """우울 주제 추출"""
        conversation = [
            ConversationTurn(role="user", content="우울하고 슬퍼요. 무기력해요.")
        ]

        topics = extractor.extract_topics(conversation)

        topic_values = [t[0] for t in topics]
        assert TopicCategory.DEPRESSION in topic_values

    def test_multiple_topics(self, extractor):
        """복합 주제 추출"""
        conversation = [
            ConversationTurn(role="user", content="회사 스트레스로 가족과 다퉜어요. 너무 우울해요.")
        ]

        topics = extractor.extract_topics(conversation)

        assert len(topics) >= 2

    def test_topic_normalization(self, extractor):
        """주제 정규화 (합계 1.0)"""
        conversation = [
            ConversationTurn(role="user", content="친구, 가족, 직장 문제가 있어요.")
        ]

        topics = extractor.extract_topics(conversation)

        total_weight = sum(t[1] for t in topics)
        assert abs(total_weight - 1.0) < 0.01

    def test_empty_conversation(self, extractor):
        """빈 대화"""
        topics = extractor.extract_topics([])

        assert len(topics) == 1
        assert topics[0][0] == TopicCategory.OTHER

    def test_only_assistant_messages(self, extractor):
        """상담사 메시지만 있는 경우"""
        conversation = [
            ConversationTurn(role="assistant", content="무엇을 도와드릴까요?")
        ]

        topics = extractor.extract_topics(conversation)

        assert topics[0][0] == TopicCategory.OTHER


# ============================================================================
# SummaryGenerator Tests
# ============================================================================

class TestSummaryGenerator:
    """요약 생성기 테스트"""

    @pytest.fixture
    def generator(self):
        return SummaryGenerator(llm_engine=None)  # 규칙 기반

    @pytest.fixture
    def sample_conversation(self):
        return [
            ConversationTurn(
                role="user",
                content="요즘 회사에서 스트레스를 많이 받아요.",
                timestamp=datetime.now() - timedelta(minutes=30)
            ),
            ConversationTurn(
                role="assistant",
                content="회사에서 어떤 일이 있으셨나요?",
                timestamp=datetime.now() - timedelta(minutes=28)
            ),
            ConversationTurn(
                role="user",
                content="상사가 계속 잔소리를 해요. 힘들어요.",
                timestamp=datetime.now() - timedelta(minutes=25)
            ),
            ConversationTurn(
                role="assistant",
                content="많이 힘드시겠네요. 깊은 호흡을 해보시는 건 어떨까요?",
                timestamp=datetime.now() - timedelta(minutes=23)
            ),
            ConversationTurn(
                role="user",
                content="네, 그래볼게요. 감사합니다.",
                timestamp=datetime.now()
            )
        ]

    @pytest.mark.asyncio
    async def test_generate_summary(self, generator, sample_conversation):
        """요약 생성"""
        summary = await generator.generate_summary(
            session_id="test-session",
            user_id="user1",
            conversation=sample_conversation
        )

        assert summary is not None
        assert summary.session_id == "test-session"
        assert summary.user_id == "user1"

    @pytest.mark.asyncio
    async def test_summary_has_required_fields(self, generator, sample_conversation):
        """필수 필드 확인"""
        summary = await generator.generate_summary(
            session_id="test",
            user_id="user1",
            conversation=sample_conversation
        )

        assert summary.brief_summary != ""
        assert len(summary.main_topics) > 0
        assert summary.dominant_emotion is not None

    @pytest.mark.asyncio
    async def test_emotional_shift_detection(self, generator):
        """감정 변화 감지"""
        conversation = [
            ConversationTurn(role="user", content="너무 슬퍼요", timestamp=datetime.now() - timedelta(minutes=30)),
            ConversationTurn(role="user", content="조금 나아졌어요", timestamp=datetime.now() - timedelta(minutes=15)),
            ConversationTurn(role="user", content="기분이 좋아요", timestamp=datetime.now())
        ]

        summary = await generator.generate_summary(
            session_id="test",
            user_id="user1",
            conversation=conversation
        )

        assert summary.emotional_shift in ["positive", "negative", "stable"]

    @pytest.mark.asyncio
    async def test_insights_generation(self, generator, sample_conversation):
        """인사이트 생성"""
        summary = await generator.generate_summary(
            session_id="test",
            user_id="user1",
            conversation=sample_conversation
        )

        assert len(summary.insights) > 0

    @pytest.mark.asyncio
    async def test_homework_generation(self, generator, sample_conversation):
        """과제 생성"""
        summary = await generator.generate_summary(
            session_id="test",
            user_id="user1",
            conversation=sample_conversation
        )

        # 과제는 있거나 없을 수 있음
        assert isinstance(summary.homework, list)


# ============================================================================
# SessionSummaryManager Tests
# ============================================================================

class TestSessionSummaryManager:
    """세션 요약 관리자 테스트"""

    @pytest.fixture
    def manager(self):
        return SessionSummaryManager(llm_engine=None)

    @pytest.fixture
    def sample_history(self):
        return [
            {"role": "user", "content": "안녕하세요", "timestamp": datetime.now().isoformat()},
            {"role": "assistant", "content": "안녕하세요!", "timestamp": datetime.now().isoformat()},
            {"role": "user", "content": "오늘 기분이 안 좋아요", "timestamp": datetime.now().isoformat()},
        ]

    @pytest.mark.asyncio
    async def test_create_summary(self, manager, sample_history):
        """요약 생성"""
        summary = await manager.create_summary(
            session_id="session1",
            user_id="user1",
            conversation_history=sample_history
        )

        assert summary is not None
        assert summary.session_id == "session1"

    @pytest.mark.asyncio
    async def test_get_summary(self, manager, sample_history):
        """요약 조회"""
        await manager.create_summary(
            session_id="session1",
            user_id="user1",
            conversation_history=sample_history
        )

        summary = manager.get_summary("session1")
        assert summary is not None

    @pytest.mark.asyncio
    async def test_get_user_summaries(self, manager, sample_history):
        """사용자 요약 목록 조회"""
        await manager.create_summary("session1", "user1", sample_history)
        await manager.create_summary("session2", "user1", sample_history)

        summaries = manager.get_user_summaries("user1")
        assert len(summaries) == 2

    @pytest.mark.asyncio
    async def test_get_progress_report(self, manager, sample_history):
        """진행 리포트 조회"""
        await manager.create_summary("session1", "user1", sample_history)

        report = manager.get_progress_report("user1", days=30)
        assert report is not None

    def test_format_summary_text(self, manager):
        """요약 텍스트 포맷"""
        # 더미 요약 생성
        summary = SessionSummary(
            session_id="test",
            user_id="user1",
            start_time=datetime.now() - timedelta(hours=1),
            end_time=datetime.now(),
            duration_minutes=60,
            brief_summary="테스트 요약입니다.",
            detailed_summary="상세 요약입니다.",
            main_topics=[(TopicCategory.STRESS, 0.5)],
            key_points=["포인트1"],
            user_concerns=["고민1"],
            counselor_suggestions=["제안1"],
            emotional_journey=[],
            dominant_emotion="스트레스",
            emotional_shift="stable",
            insights=["인사이트1"],
            patterns_identified=[],
            homework=["과제1"],
            next_session_suggestions=["제안1"],
            message_count=10,
            user_message_count=5
        )

        text = manager.format_summary_text(summary)

        assert "세션 요약" in text
        assert "테스트 요약입니다" in text


# ============================================================================
# Integration Tests
# ============================================================================

class TestSessionSummaryIntegration:
    """통합 테스트"""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """전체 워크플로우"""
        manager = SessionSummaryManager()

        history = [
            {"role": "user", "content": "스트레스 받아요", "timestamp": datetime.now().isoformat()},
            {"role": "assistant", "content": "어떤 일이 있으셨나요?", "timestamp": datetime.now().isoformat()},
            {"role": "user", "content": "직장 문제에요", "timestamp": datetime.now().isoformat()},
        ]

        # 요약 생성
        summary = await manager.create_summary("s1", "u1", history)
        assert summary is not None

        # 요약 조회
        retrieved = manager.get_summary("s1")
        assert retrieved is not None

        # 텍스트 포맷
        text = manager.format_summary_text(summary)
        assert len(text) > 0


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    """엣지 케이스 테스트"""

    @pytest.mark.asyncio
    async def test_empty_conversation(self):
        """빈 대화"""
        manager = SessionSummaryManager()

        with pytest.raises(Exception):
            await manager.create_summary("s1", "u1", [])

    @pytest.mark.asyncio
    async def test_single_message(self):
        """단일 메시지"""
        manager = SessionSummaryManager()

        history = [
            {"role": "user", "content": "안녕", "timestamp": datetime.now().isoformat()}
        ]

        summary = await manager.create_summary("s1", "u1", history)
        assert summary is not None

    @pytest.mark.asyncio
    async def test_very_long_conversation(self):
        """매우 긴 대화"""
        manager = SessionSummaryManager()

        history = [
            {"role": "user" if i % 2 == 0 else "assistant",
             "content": f"메시지 {i}",
             "timestamp": datetime.now().isoformat()}
            for i in range(100)
        ]

        summary = await manager.create_summary("s1", "u1", history)
        assert summary is not None
        assert summary.message_count == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
