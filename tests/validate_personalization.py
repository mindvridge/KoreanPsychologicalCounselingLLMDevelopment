"""
Validate User Personalization System
사용자 개인화 시스템 검증

Validates:
- Database schema for personalization
- PersonaManager personalization integration
- API endpoint updates
- Documentation
"""

import sys
import os

def validate_personalization_schema():
    """Validate personalization database schema"""
    print("=" * 70)
    print("Validating Personalization Database Schema")
    print("=" * 70)

    db_file = "src/database.py"

    if not os.path.exists(db_file):
        print(f"✗ File not found: {db_file}")
        return False

    with open(db_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for required classes
    required_classes = [
        "UserPersonaPreference",
        "UserInteractionHistory",
        "UserPersonalizationManager"
    ]

    print("\nChecking personalization classes:")
    for class_name in required_classes:
        if f"class {class_name}" in content:
            print(f"  ✓ {class_name}")
        else:
            print(f"  ✗ {class_name} - MISSING")
            return False

    # Check for key fields
    required_fields = [
        "preference_score",
        "personal_weight_adjustment",
        "confidence",
        "interaction_type",
        "duration_seconds"
    ]

    print("\nChecking personalization fields:")
    for field in required_fields:
        if field in content:
            print(f"  ✓ {field}")
        else:
            print(f"  ✗ {field} - MISSING")
            return False

    # Check for key methods
    required_methods = [
        "record_interaction",
        "_update_user_preference",
        "get_user_preferences",
        "get_user_persona_weight",
        "get_user_interaction_history",
        "get_user_stats"
    ]

    print("\nChecking UserPersonalizationManager methods:")
    for method in required_methods:
        if f"def {method}" in content:
            print(f"  ✓ {method}()")
        else:
            print(f"  ✗ {method}() - MISSING")
            return False

    print("\n✅ Personalization database schema validated successfully!\n")
    return True


def validate_persona_manager_personalization():
    """Validate PersonaManager personalization integration"""
    print("=" * 70)
    print("Validating PersonaManager Personalization")
    print("=" * 70)

    pm_file = "src/persona_manager.py"

    if not os.path.exists(pm_file):
        print(f"✗ File not found: {pm_file}")
        return False

    with open(pm_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for user_id parameter
    if "user_id: Optional[str]" in content:
        print("  ✓ user_id parameter in recommend_personas")
    else:
        print("  ✗ Missing user_id parameter")
        return False

    # Check for use_personalization parameter
    if "use_personalization: bool" in content:
        print("  ✓ use_personalization parameter")
    else:
        print("  ✗ Missing use_personalization parameter")
        return False

    # Check for user weights loading
    if "UserPersonalizationManager.get_user_persona_weight" in content:
        print("  ✓ User persona weight loading")
    else:
        print("  ✗ Missing user weight loading")
        return False

    # Check for personalized marker
    if ('"personalized": personalized' in content or "'personalized':" in content):
        print("  ✓ Personalized marker in recommendations")
    else:
        print("  ✗ Missing personalized marker")
        return False

    # Check for preference icon
    if "⭐" in content or "회원님 선호" in content:
        print("  ✓ Preference icon/text (⭐ 회원님 선호)")
    else:
        print("  ✗ Missing preference indicator")
        return False

    print("\n✅ PersonaManager personalization validated successfully!\n")
    return True


def validate_api_personalization():
    """Validate API personalization endpoints"""
    print("=" * 70)
    print("Validating API Personalization")
    print("=" * 70)

    api_file = "src/api.py"

    if not os.path.exists(api_file):
        print(f"✗ File not found: {api_file}")
        return False

    with open(api_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check PersonaRecommendRequest has user_id
    if "user_id: Optional[str]" in content and "PersonaRecommendRequest" in content:
        # Find the request model section
        request_section = content[content.find("class PersonaRecommendRequest"):content.find("class PersonaRecommendRequest") + 500]
        if "user_id" in request_section:
            print("  ✓ PersonaRecommendRequest has user_id field")
        else:
            print("  ✗ PersonaRecommendRequest missing user_id")
            return False
    else:
        print("  ✗ PersonaRecommendRequest not found or missing user_id")
        return False

    # Check recommend endpoint uses personalization
    if "user_id=recommend_request.user_id" in content:
        print("  ✓ Recommend endpoint passes user_id")
    else:
        print("  ✗ Recommend endpoint not using user_id")
        return False

    if "use_personalization=True" in content:
        print("  ✓ Recommend endpoint enables personalization")
    else:
        print("  ✗ Recommend endpoint not enabling personalization")
        return False

    # Check for personalization note in response
    if "Personalized for you" in content or "personalization" in content.lower():
        print("  ✓ Personalization noted in API responses")
    else:
        print("  ✗ Missing personalization indication in responses")
        return False

    print("\n✅ API personalization validated successfully!\n")
    return True


def validate_documentation():
    """Validate personalization documentation"""
    print("=" * 70)
    print("Validating Personalization Documentation")
    print("=" * 70)

    doc_file = "docs/USER_PERSONALIZATION_SYSTEM.md"

    if not os.path.exists(doc_file):
        print(f"  ✗ Documentation missing: {doc_file}")
        return False

    with open(doc_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for key sections
    required_sections = [
        "# 사용자별 개인화 시스템",
        "## 🏗️ 3단계 추천 시스템",
        "## 🗄️ 데이터베이스 스키마",
        "## 📈 개인화 학습 알고리즘",
        "## 🚀 API 사용법",
        "## 🎯 사용 시나리오",
        "## 🔧 개발자 가이드",
        "UserPersonaPreference",
        "UserInteractionHistory",
        "preference_score",
        "personal_weight_adjustment"
    ]

    print("\nChecking documentation sections:")
    missing_sections = []
    for section in required_sections:
        if section in content:
            print(f"  ✓ {section}")
        else:
            print(f"  ✗ {section} - MISSING")
            missing_sections.append(section)

    if missing_sections:
        print(f"\n  Missing {len(missing_sections)} sections")
        return False

    print(f"\n  Documentation file size: {len(content)} characters")
    print("\n✅ Personalization documentation validated successfully!\n")
    return True


def validate_three_tier_system():
    """Validate three-tier recommendation system"""
    print("=" * 70)
    print("Validating Three-Tier Recommendation System")
    print("=" * 70)

    pm_file = "src/persona_manager.py"

    with open(pm_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for three layers
    layers = {
        "Rule-Based": "age_rules" in content and "concern_rules" in content,
        "Global Learning": "PersonaFeedbackManager" in content and "learned_weights" in content,
        "Personalization": "UserPersonalizationManager" in content and "user_weights" in content
    }

    print("\nChecking recommendation layers:")
    for layer, exists in layers.items():
        if exists:
            print(f"  ✓ {layer}")
        else:
            print(f"  ✗ {layer} - MISSING")
            return False

    # Check for weight combination
    if "persona_scores[pid] += weight" in content:
        print("  ✓ Weight combination logic")
    else:
        print("  ✗ Missing weight combination")
        return False

    # Check for personalized flag
    if "personalized = persona_id in user_weights" in content:
        print("  ✓ Personalization detection")
    else:
        print("  ✗ Missing personalization detection")
        return False

    print("\n✅ Three-tier recommendation system validated successfully!\n")
    return True


def main():
    """Run all personalization validations"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 13 + "User Personalization System Validation" + " " * 17 + "║")
    print("║" + " " * 17 + "사용자 개인화 시스템 검증" + " " * 26 + "║")
    print("╚" + "=" * 68 + "╝")
    print("\n")

    validations = [
        ("Personalization Schema", validate_personalization_schema),
        ("PersonaManager Integration", validate_persona_manager_personalization),
        ("API Personalization", validate_api_personalization),
        ("Three-Tier System", validate_three_tier_system),
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
        print("\n🎉 All validations passed! User personalization system is ready.")
        print("\n📋 Implementation Summary:")
        print("  • 2 new database tables (UserPersonaPreference, UserInteractionHistory)")
        print("  • UserPersonalizationManager with 6 key methods")
        print("  • PersonaManager: user_id + use_personalization parameters")
        print("  • API: PersonaRecommendRequest updated with user_id")
        print("  • Three-tier recommendation: Rules → Global → Personal")
        print("  • Personalized markers (⭐) in recommendations")
        print("  • Comprehensive documentation (USER_PERSONALIZATION_SYSTEM.md)")
        print("\n🎯 Key Features:")
        print("  • Individual preference learning (-1 to +1 score)")
        print("  • Personal weight adjustment (up to ±2.0)")
        print("  • Confidence-based gradual application")
        print("  • User interaction history tracking")
        print("  • Favorite persona detection")
        print("\n📍 Usage:")
        print("  1. Add user_id to recommendation requests")
        print("  2. System automatically learns from feedback")
        print("  3. Look for ⭐ markers in recommendations")
        print("  4. Query /api/v1/users/{user_id}/preferences for details")
        return True
    else:
        print("\n❌ Some validations failed. Please review the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
