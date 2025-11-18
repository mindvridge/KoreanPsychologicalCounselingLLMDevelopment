"""
Database Integration Tests
Tests for database persistence, conversation saving, and user management
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import (
    Base, get_engine, get_session,
    User, UserMetadata, Conversation, Assessment,
    PersonaFeedback, PersonaPerformance, UserPersonaPreference
)


@pytest.fixture
def test_engine():
    """Create in-memory SQLite database for testing"""
    from sqlalchemy import create_engine
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def test_session(test_engine):
    """Create database session for testing"""
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session
    session.close()


class TestDatabaseModels:
    """Test database models creation and relationships"""

    def test_create_user(self, test_session):
        """Test creating a user"""
        user = User(
            user_id="test_user_123",
            consent_given=True,
            data_retention_days=90
        )
        test_session.add(user)
        test_session.commit()

        # Retrieve user
        retrieved = test_session.query(User).filter_by(user_id="test_user_123").first()
        assert retrieved is not None
        assert retrieved.user_id == "test_user_123"
        assert retrieved.consent_given == True
        assert retrieved.total_conversations == 0

    def test_user_metadata_relationship(self, test_session):
        """Test user-metadata relationship"""
        user = User(user_id="test_user_456")
        test_session.add(user)
        test_session.flush()

        metadata = UserMetadata(
            user_id=user.id,
            preferred_name="철수님",
            age_range="20대",
            main_concerns=["우울", "불안"]
        )
        test_session.add(metadata)
        test_session.commit()

        # Verify relationship
        assert user.metadata is not None
        assert user.metadata.preferred_name == "철수님"
        assert user.metadata.age_range == "20대"

    def test_conversation_save(self, test_session):
        """Test saving conversation turns"""
        user = User(user_id="test_user_789")
        test_session.add(user)
        test_session.flush()

        # Save user message
        conv1 = Conversation(
            user_id=user.id,
            session_id="session_001",
            persona_id="warm_mother",
            message_role="user",
            message_content="안녕하세요",
            timestamp=datetime.utcnow()
        )

        # Save assistant response
        conv2 = Conversation(
            user_id=user.id,
            session_id="session_001",
            persona_id="warm_mother",
            message_role="assistant",
            message_content="안녕하세요! 무엇을 도와드릴까요?",
            timestamp=datetime.utcnow()
        )

        test_session.add_all([conv1, conv2])
        test_session.commit()

        # Retrieve conversation history
        history = test_session.query(Conversation).filter_by(
            user_id=user.id,
            session_id="session_001"
        ).order_by(Conversation.timestamp).all()

        assert len(history) == 2
        assert history[0].message_role == "user"
        assert history[1].message_role == "assistant"
        assert "안녕하세요" in history[0].message_content

    def test_assessment_save(self, test_session):
        """Test saving assessment results"""
        user = User(user_id="test_user_assessment")
        test_session.add(user)
        test_session.flush()

        assessment = Assessment(
            user_id=user.id,
            assessment_type="PHQ-9",
            score=12,
            severity="moderate",
            responses=[1, 2, 1, 2, 1, 2, 1, 2, 0],
            recommendations=["전문가 상담 권장"],
            timestamp=datetime.utcnow()
        )
        test_session.add(assessment)
        test_session.commit()

        # Retrieve assessment
        saved = test_session.query(Assessment).filter_by(
            user_id=user.id,
            assessment_type="PHQ-9"
        ).first()

        assert saved is not None
        assert saved.score == 12
        assert saved.severity == "moderate"
        assert len(saved.responses) == 9

    def test_persona_feedback(self, test_session):
        """Test saving persona feedback"""
        feedback = PersonaFeedback(
            persona_id="warm_mother",
            session_id="session_feedback_001",
            user_id="user_feedback_test",
            rating=5,
            helpful=True,
            appropriate=True,
            would_recommend=True,
            feedback_text="매우 도움이 되었습니다",
            concern="우울",
            age_range="30대",
            timestamp=datetime.utcnow()
        )
        test_session.add(feedback)
        test_session.commit()

        # Retrieve feedback
        saved = test_session.query(PersonaFeedback).filter_by(
            persona_id="warm_mother"
        ).first()

        assert saved is not None
        assert saved.rating == 5
        assert saved.helpful == True
        assert saved.feedback_text == "매우 도움이 되었습니다"

    def test_cascade_delete(self, test_session):
        """Test cascade delete (user deletion removes all related data)"""
        user = User(user_id="test_cascade")
        test_session.add(user)
        test_session.flush()

        # Add related data
        metadata = UserMetadata(user_id=user.id, preferred_name="테스트")
        conv = Conversation(user_id=user.id, session_id="s1", message_role="user", message_content="test")
        assessment = Assessment(user_id=user.id, assessment_type="PHQ-9", score=10)

        test_session.add_all([metadata, conv, assessment])
        test_session.commit()

        # Delete user
        test_session.delete(user)
        test_session.commit()

        # Verify all related data is deleted
        assert test_session.query(UserMetadata).count() == 0
        assert test_session.query(Conversation).filter_by(session_id="s1").count() == 0
        assert test_session.query(Assessment).filter_by(score=10).count() == 0


class TestDatabasePersistence:
    """Test database persistence across sessions"""

    def test_data_survives_session(self, test_engine):
        """Test that data persists across different database sessions"""
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=test_engine)

        # Session 1: Create user
        session1 = Session()
        user = User(user_id="persistent_user")
        session1.add(user)
        session1.commit()
        session1.close()

        # Session 2: Retrieve user
        session2 = Session()
        retrieved = session2.query(User).filter_by(user_id="persistent_user").first()
        assert retrieved is not None
        assert retrieved.user_id == "persistent_user"
        session2.close()


class TestDatabaseQueries:
    """Test complex database queries"""

    def test_conversation_history_query(self, test_session):
        """Test retrieving conversation history for a session"""
        user = User(user_id="query_test_user")
        test_session.add(user)
        test_session.flush()

        # Add multiple conversations
        for i in range(5):
            conv = Conversation(
                user_id=user.id,
                session_id="query_session",
                message_role="user" if i % 2 == 0 else "assistant",
                message_content=f"Message {i}",
                timestamp=datetime.utcnow()
            )
            test_session.add(conv)

        test_session.commit()

        # Query conversation history
        history = test_session.query(Conversation).filter_by(
            session_id="query_session"
        ).order_by(Conversation.timestamp).all()

        assert len(history) == 5
        assert history[0].message_content == "Message 0"
        assert history[-1].message_content == "Message 4"

    def test_user_statistics(self, test_session):
        """Test calculating user statistics"""
        user = User(
            user_id="stats_user",
            total_conversations=10,
            total_messages=50,
            crisis_count=2
        )
        test_session.add(user)
        test_session.commit()

        # Query statistics
        stats = test_session.query(User).filter_by(user_id="stats_user").first()
        assert stats.total_conversations == 10
        assert stats.total_messages == 50
        assert stats.crisis_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
