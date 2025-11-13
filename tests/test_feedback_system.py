"""
Test Feedback Learning System
피드백 학습 시스템 테스트

Tests:
- Database models creation
- Feedback submission
- Performance statistics
- Weight adjustment learning
- Learned weights integration
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import (
    DatabaseManager,
    PersonaFeedback,
    PersonaPerformance,
    PersonaWeightAdjustment,
    PersonaFeedbackManager,
    UserManager
)
from src.persona_manager import PersonaManager
import tempfile


def test_database_models():
    """Test 1: Database models are created correctly"""
    print("=" * 70)
    print("Test 1: Database Models Creation")
    print("=" * 70)

    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        db_manager = DatabaseManager(f"sqlite:///{db_path}")
        db = db_manager.get_session()

        # Check tables exist
        from sqlalchemy import inspect
        inspector = inspect(db_manager.engine)
        tables = inspector.get_table_names()

        required_tables = [
            'persona_feedback',
            'persona_performance',
            'persona_weight_adjustments'
        ]

        for table in required_tables:
            if table in tables:
                print(f"✓ Table '{table}' exists")
            else:
                print(f"✗ Table '{table}' missing")
                return False

        db.close()
        print("\n✅ All database models created successfully\n")
        return True

    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.remove(db_path)


def test_feedback_submission():
    """Test 2: Submit feedback and verify storage"""
    print("=" * 70)
    print("Test 2: Feedback Submission")
    print("=" * 70)

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        db_manager = DatabaseManager(f"sqlite:///{db_path}")
        db = db_manager.get_session()

        # Submit feedback
        feedback = PersonaFeedbackManager.submit_feedback(
            db=db,
            user_id="test_user_123",
            session_id="test_session_456",
            persona_id="warm_mother",
            rating=5,
            helpful=True,
            appropriate=True,
            would_recommend_again=True,
            concerns_addressed=["우울", "불안"],
            feedback_text="매우 도움이 되었습니다",
            user_age_range="20대"
        )

        print(f"✓ Feedback submitted: ID={feedback.id}")
        print(f"  - Persona: {feedback.persona_id}")
        print(f"  - Rating: {feedback.rating}")
        print(f"  - Concerns: {feedback.concerns_addressed}")

        # Verify storage
        stored_feedback = db.query(PersonaFeedback).filter(
            PersonaFeedback.id == feedback.id
        ).first()

        if stored_feedback:
            print(f"✓ Feedback verified in database")
        else:
            print(f"✗ Feedback not found in database")
            return False

        db.close()
        print("\n✅ Feedback submission successful\n")
        return True

    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_performance_stats():
    """Test 3: Performance statistics calculation"""
    print("=" * 70)
    print("Test 3: Performance Statistics")
    print("=" * 70)

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        db_manager = DatabaseManager(f"sqlite:///{db_path}")
        db = db_manager.get_session()

        # Submit multiple feedback entries
        personas = ["warm_mother", "clinical_professional", "friendly_peer"]
        ratings = [5, 4, 5, 3, 5, 4, 5, 5, 4, 5]

        for i, rating in enumerate(ratings):
            PersonaFeedbackManager.submit_feedback(
                db=db,
                user_id=f"user_{i}",
                session_id=f"session_{i}",
                persona_id=personas[i % len(personas)],
                rating=rating,
                helpful=rating >= 4,
                appropriate=rating >= 4,
                would_recommend_again=rating >= 4,
                concerns_addressed=["우울"],
                user_age_range="20대"
            )

        # Get performance stats
        stats = PersonaFeedbackManager.get_performance_stats(db, "warm_mother")

        print(f"✓ Performance stats for 'warm_mother':")
        print(f"  - Total feedback: {stats['total_feedback_count']}")
        print(f"  - Average rating: {stats['average_rating']:.2f}")
        print(f"  - Helpful rate: {stats['helpful_rate']:.2f}")
        print(f"  - Appropriate rate: {stats['appropriate_rate']:.2f}")
        print(f"  - Recommendation rate: {stats['recommendation_rate']:.2f}")

        # Verify calculations
        if stats['total_feedback_count'] > 0 and stats['average_rating'] >= 4.0:
            print("✓ Statistics calculated correctly")
        else:
            print("✗ Statistics calculation error")
            return False

        db.close()
        print("\n✅ Performance statistics working correctly\n")
        return True

    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_weight_adjustment():
    """Test 4: Weight adjustment learning"""
    print("=" * 70)
    print("Test 4: Weight Adjustment Learning")
    print("=" * 70)

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        db_manager = DatabaseManager(f"sqlite:///{db_path}")
        db = db_manager.get_session()

        # Submit successful feedback (rating >= 4)
        persona_id = "trauma_specialist"
        concern = "트라우마"
        age_range = "20대"

        # Submit 25 high-rating feedback
        for i in range(25):
            PersonaFeedbackManager.submit_feedback(
                db=db,
                user_id=f"user_{i}",
                session_id=f"session_{i}",
                persona_id=persona_id,
                rating=5 if i < 23 else 3,  # 23/25 = 92% success
                helpful=True,
                appropriate=True,
                would_recommend_again=True,
                concerns_addressed=[concern],
                user_age_range=age_range
            )

        # Get weight adjustments
        adjustments = PersonaFeedbackManager.get_weight_adjustments(
            db,
            persona_id=persona_id,
            concern=concern,
            age_range=age_range
        )

        if adjustments:
            adj = adjustments[0]
            print(f"✓ Weight adjustment learned:")
            print(f"  - Persona: {adj['persona_id']}")
            print(f"  - Concern: {adj['concern']}")
            print(f"  - Age range: {adj['age_range']}")
            print(f"  - Base weight: {adj['base_weight']}")
            print(f"  - Adjustment: {adj['adjustment']:+.2f}")
            print(f"  - Final weight: {adj['final_weight']:.2f}")
            print(f"  - Sample count: {adj['sample_count']}")
            print(f"  - Success rate: {adj['success_rate']:.2%}")
            print(f"  - Confidence: {adj['confidence']:.2f}")

            # Verify learning
            if adj['sample_count'] == 25 and adj['success_rate'] >= 0.9:
                print("✓ Learning algorithm working correctly")
                print(f"  Expected: success_rate ~92%, confidence 1.0")
                print(f"  Got: success_rate {adj['success_rate']:.1%}, confidence {adj['confidence']}")
            else:
                print("✗ Learning algorithm error")
                return False
        else:
            print("✗ No weight adjustments found")
            return False

        db.close()
        print("\n✅ Weight adjustment learning successful\n")
        return True

    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_learned_recommendations():
    """Test 5: Learned weights integration with recommendations"""
    print("=" * 70)
    print("Test 5: Learned Weights in Recommendations")
    print("=" * 70)

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        db_manager = DatabaseManager(f"sqlite:///{db_path}")
        db = db_manager.get_session()

        # Initialize persona manager
        pm = PersonaManager()

        # Get baseline recommendations (no learning)
        baseline_recs = pm.recommend_personas(
            age_range="20대",
            concerns=["우울"],
            top_k=3,
            use_learned_weights=False
        )

        print("Baseline recommendations (rule-based only):")
        for i, rec in enumerate(baseline_recs, 1):
            print(f"  {i}. {rec['display_name']} (score: {rec['score']:.1f})")

        # Submit positive feedback for a specific persona
        target_persona = "clinical_professional"
        for i in range(25):
            PersonaFeedbackManager.submit_feedback(
                db=db,
                user_id=f"user_{i}",
                session_id=f"session_{i}",
                persona_id=target_persona,
                rating=5,
                helpful=True,
                appropriate=True,
                would_recommend_again=True,
                concerns_addressed=["우울"],
                user_age_range="20대"
            )

        # Get learned recommendations
        learned_recs = pm.recommend_personas(
            age_range="20대",
            concerns=["우울"],
            top_k=3,
            db_session=db,
            use_learned_weights=True
        )

        print("\nLearned recommendations (with feedback):")
        for i, rec in enumerate(learned_recs, 1):
            print(f"  {i}. {rec['display_name']} (score: {rec['score']:.1f})")

        # Verify target persona got boosted
        baseline_score = next(
            (r['score'] for r in baseline_recs if r['id'] == target_persona),
            0
        )
        learned_score = next(
            (r['score'] for r in learned_recs if r['id'] == target_persona),
            0
        )

        if learned_score > baseline_score:
            boost = learned_score - baseline_score
            print(f"\n✓ Learning effect detected:")
            print(f"  {target_persona} score: {baseline_score:.1f} → {learned_score:.1f} (+{boost:.1f})")
        else:
            print(f"\n✗ No learning effect detected")
            return False

        db.close()
        print("\n✅ Learned recommendations working correctly\n")
        return True

    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def run_all_tests():
    """Run all feedback system tests"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "Feedback Learning System Tests" + " " * 23 + "║")
    print("║" + " " * 17 + "피드백 학습 시스템 테스트" + " " * 24 + "║")
    print("╚" + "=" * 68 + "╝")
    print("\n")

    tests = [
        ("Database Models", test_database_models),
        ("Feedback Submission", test_feedback_submission),
        ("Performance Statistics", test_performance_stats),
        ("Weight Adjustment", test_weight_adjustment),
        ("Learned Recommendations", test_learned_recommendations)
    ]

    results = []

    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Test '{name}' failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Feedback learning system is working correctly.")
        return True
    else:
        print("\n❌ Some tests failed. Please review the errors above.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
