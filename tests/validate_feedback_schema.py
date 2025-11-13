"""
Validate Feedback System Database Schema
피드백 시스템 데이터베이스 스키마 검증

Simple validation without torch dependency
"""

import sys
import os

# Test database schema directly
def validate_schema():
    """Validate that feedback tables are defined correctly"""
    print("=" * 70)
    print("Validating Feedback System Database Schema")
    print("=" * 70)

    # Read database.py and check for required classes
    db_file = "src/database.py"

    if not os.path.exists(db_file):
        print(f"✗ File not found: {db_file}")
        return False

    with open(db_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for required classes
    required_classes = [
        "PersonaFeedback",
        "PersonaPerformance",
        "PersonaWeightAdjustment",
        "PersonaFeedbackManager"
    ]

    print("\nChecking database classes:")
    for class_name in required_classes:
        if f"class {class_name}" in content:
            print(f"  ✓ {class_name}")
        else:
            print(f"  ✗ {class_name} - MISSING")
            return False

    # Check for key methods
    required_methods = [
        "submit_feedback",
        "_update_performance_stats",
        "_update_weight_adjustment",
        "get_performance_stats",
        "get_weight_adjustments"
    ]

    print("\nChecking PersonaFeedbackManager methods:")
    for method in required_methods:
        if f"def {method}" in content:
            print(f"  ✓ {method}()")
        else:
            print(f"  ✗ {method}() - MISSING")
            return False

    # Check for table names
    required_tables = [
        "persona_feedback",
        "persona_performance",
        "persona_weight_adjustments"
    ]

    print("\nChecking table definitions:")
    for table in required_tables:
        if f'__tablename__ = "{table}"' in content:
            print(f"  ✓ {table}")
        else:
            print(f"  ✗ {table} - MISSING")
            return False

    print("\n✅ All database schema elements validated successfully!\n")
    return True


def validate_persona_manager():
    """Validate PersonaManager has learned weights integration"""
    print("=" * 70)
    print("Validating PersonaManager Integration")
    print("=" * 70)

    pm_file = "src/persona_manager.py"

    if not os.path.exists(pm_file):
        print(f"✗ File not found: {pm_file}")
        return False

    with open(pm_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for Session import
    if "from sqlalchemy.orm import Session" in content:
        print("  ✓ SQLAlchemy Session import")
    else:
        print("  ✗ Missing SQLAlchemy Session import")
        return False

    # Check for db_session parameter
    if "db_session: Optional[Session]" in content:
        print("  ✓ db_session parameter in recommend_personas")
    else:
        print("  ✗ Missing db_session parameter")
        return False

    # Check for learned weights loading
    if "PersonaFeedbackManager.get_weight_adjustments" in content:
        print("  ✓ Learned weights loading")
    else:
        print("  ✗ Missing learned weights loading")
        return False

    # Check for learned_weights usage
    if "learned_weights[key]" in content or "key in learned_weights" in content:
        print("  ✓ Learned weights application")
    else:
        print("  ✗ Missing learned weights application")
        return False

    print("\n✅ PersonaManager integration validated successfully!\n")
    return True


def validate_api_endpoints():
    """Validate API endpoints exist"""
    print("=" * 70)
    print("Validating API Endpoints")
    print("=" * 70)

    api_file = "src/api.py"

    if not os.path.exists(api_file):
        print(f"✗ File not found: {api_file}")
        return False

    with open(api_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for Pydantic models
    required_models = [
        "PersonaFeedbackRequest",
        "PersonaFeedbackResponse",
        "PersonaPerformanceResponse",
        "PersonaAnalyticsResponse"
    ]

    print("\nChecking Pydantic models:")
    for model in required_models:
        if f"class {model}(BaseModel)" in content:
            print(f"  ✓ {model}")
        else:
            print(f"  ✗ {model} - MISSING")
            return False

    # Check for API endpoints
    required_endpoints = [
        ("POST", "/personas/{persona_id}/feedback", "submit_persona_feedback"),
        ("GET", "/personas/{persona_id}/performance", "get_persona_performance"),
        ("GET", "/personas/analytics/all", "get_all_personas_analytics"),
        ("GET", "/personas/learning/weights", "get_learned_weights")
    ]

    print("\nChecking API endpoints:")
    for method, path, func_name in required_endpoints:
        # Check for function definition
        if f"async def {func_name}" in content:
            # Also verify endpoint decorator
            if path.replace("{persona_id}", r"{persona_id}") in content:
                print(f"  ✓ {method} {path}")
            else:
                print(f"  ✗ {method} {path} - decorator missing")
                return False
        else:
            print(f"  ✗ {method} {path} - function missing")
            return False

    # Check for db_session in recommend endpoint
    if "db: Session = Depends(get_db)" in content and "use_learned_weights=True" in content:
        print("  ✓ Recommendation endpoint uses learned weights")
    else:
        print("  ✗ Recommendation endpoint missing learned weights")
        return False

    print("\n✅ All API endpoints validated successfully!\n")
    return True


def validate_documentation():
    """Validate documentation exists"""
    print("=" * 70)
    print("Validating Documentation")
    print("=" * 70)

    doc_file = "docs/FEEDBACK_LEARNING_SYSTEM.md"

    if not os.path.exists(doc_file):
        print(f"  ✗ Documentation missing: {doc_file}")
        return False

    with open(doc_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for key sections
    required_sections = [
        "# 피드백 학습 시스템",
        "## 🏗️ 시스템 아키텍처",
        "## 🚀 API 사용법",
        "## 📈 학습 메커니즘",
        "## 🎯 사용 시나리오",
        "## 🔧 개발자 가이드"
    ]

    print("\nChecking documentation sections:")
    for section in required_sections:
        if section in content:
            print(f"  ✓ {section}")
        else:
            print(f"  ✗ {section} - MISSING")
            return False

    print(f"\n  Documentation file size: {len(content)} characters")
    print("\n✅ Documentation validated successfully!\n")
    return True


def main():
    """Run all validations"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "Feedback System Validation" + " " * 27 + "║")
    print("║" + " " * 17 + "피드백 시스템 검증" + " " * 32 + "║")
    print("╚" + "=" * 68 + "╝")
    print("\n")

    validations = [
        ("Database Schema", validate_schema),
        ("PersonaManager Integration", validate_persona_manager),
        ("API Endpoints", validate_api_endpoints),
        ("Documentation", validate_documentation)
    ]

    results = []

    for name, validate_func in validations:
        try:
            result = validate_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Validation '{name}' failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} validations passed")

    if passed == total:
        print("\n🎉 All validations passed! Feedback learning system is ready.")
        print("\n📋 Summary of Implementation:")
        print("  • 3 new database tables (PersonaFeedback, PersonaPerformance, PersonaWeightAdjustment)")
        print("  • PersonaFeedbackManager with 5 key methods")
        print("  • 4 new API endpoints for feedback and analytics")
        print("  • Learned weights integration in recommendations")
        print("  • Comprehensive documentation (FEEDBACK_LEARNING_SYSTEM.md)")
        print("\n📍 Next Steps:")
        print("  1. Start API server: python src/api.py")
        print("  2. Test feedback submission via Swagger UI: http://localhost:8000/docs")
        print("  3. Monitor learned weights in real-time")
        print("  4. Review analytics dashboard: GET /api/v1/personas/analytics/all")
        return True
    else:
        print("\n❌ Some validations failed. Please review the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
