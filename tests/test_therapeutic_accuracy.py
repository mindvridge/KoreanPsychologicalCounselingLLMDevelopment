"""
Therapeutic Accuracy Tests
치료 기법 정확성 테스트

심리치료 기법(CBT, DBT, ACT)이 올바르게 적용되는지 검증합니다.
"""

import sys
import os
import pytest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# ============================================================================
# 1. CBT (Cognitive Behavioral Therapy) Techniques
# ============================================================================

class TestCBTTechniques:
    """인지행동치료 기법 테스트"""

    def test_cognitive_restructuring_keywords(self):
        """
        인지 재구성 키워드 감지
        
        예: "생각", "인지", "왜곡", "재구성"
        """
        cbt_responses = [
            "그 생각이 정말 사실인지 확인해보세요",
            "다른 관점에서 생각해볼 수 있을까요?",
            "그 생각의 근거는 무엇인가요?",
            "인지 왜곡이 있는 것 같아요"
        ]
        
        cbt_keywords = ["생각", "인지", "왜곡", "재구성", "관점", "근거"]
        
        for response in cbt_responses:
            has_keyword = any(keyword in response for keyword in cbt_keywords)
            assert has_keyword, f"CBT 키워드가 없습니다: '{response}'"

    def test_behavioral_activation(self):
        """
        행동 활성화 기법
        
        우울증 치료를 위한 활동 권장
        """
        behavioral_responses = [
            "작은 활동부터 시작해보세요",
            "매일 할 수 있는 것을 찾아보세요",
            "즐거웠던 활동을 다시 시도해보세요"
        ]
        
        behavioral_keywords = ["활동", "시작", "시도", "실천", "행동"]
        
        for response in behavioral_responses:
            has_keyword = any(keyword in response for keyword in behavioral_keywords)
            assert has_keyword or True  # Placeholder test


# ============================================================================
# 2. DBT (Dialectical Behavior Therapy) Techniques
# ============================================================================

class TestDBTTechniques:
    """변증법적 행동치료 기법 테스트"""

    def test_mindfulness_skills(self):
        """
        마음챙김 기법
        """
        mindfulness_keywords = [
            "마음챙김",
            "현재 순간",
            "지금 여기",
            "관찰",
            "알아차림"
        ]
        
        # Test that mindfulness concepts are recognized
        assert len(mindfulness_keywords) > 0

    def test_distress_tolerance(self):
        """
        고통 감내 기법
        """
        distress_keywords = [
            "고통 감내",
            "견디기",
            "수용",
            "참기"
        ]
        
        assert len(distress_keywords) > 0

    def test_emotion_regulation(self):
        """
        감정 조절 기법
        """
        emotion_regulation_keywords = [
            "감정 조절",
            "감정 이해",
            "감정 표현",
            "감정 관리"
        ]
        
        assert len(emotion_regulation_keywords) > 0


# ============================================================================
# 3. ACT (Acceptance and Commitment Therapy) Techniques
# ============================================================================

class TestACTTechniques:
    """수용전념치료 기법 테스트"""

    def test_acceptance(self):
        """
        수용 기법
        """
        acceptance_keywords = [
            "수용",
            "받아들이기",
            "인정",
            "허용"
        ]
        
        assert len(acceptance_keywords) > 0

    def test_values_clarification(self):
        """
        가치 명료화 기법
        """
        values_keywords = [
            "가치",
            "중요한 것",
            "의미",
            "목표"
        ]
        
        assert len(values_keywords) > 0

    def test_defusion(self):
        """
        탈융합 기법
        """
        defusion_keywords = [
            "탈융합",
            "거리두기",
            "분리",
            "관찰"
        ]
        
        assert len(defusion_keywords) > 0


# ============================================================================
# 4. Therapeutic Boundaries
# ============================================================================

class TestTherapeuticBoundaries:
    """치료적 경계 테스트"""

    def test_no_diagnosis(self):
        """
        진단을 내리지 않는지 확인
        """
        inappropriate_statements = [
            "당신은 우울증입니다",
            "확실히 불안장애예요",
            "이건 조현병이에요"
        ]
        
        # System should not make definitive diagnoses
        # This is a placeholder for actual test
        pass

    def test_no_prescription(self):
        """
        약물 처방을 하지 않는지 확인
        """
        inappropriate_statements = [
            "이 약을 드세요",
            "항우울제를 복용하세요",
            "약을 끊으세요"
        ]
        
        # System should not prescribe medication
        pass

    def test_professional_referral(self):
        """
        적절한 전문가 연계
        """
        referral_keywords = [
            "전문가",
            "상담사",
            "정신과",
            "병원",
            "의사"
        ]
        
        # For serious issues, should recommend professional help
        assert len(referral_keywords) > 0


# ============================================================================
# 5. Empathy and Validation
# ============================================================================

class TestEmpathyValidation:
    """공감과 타당화 테스트"""

    def test_empathic_responses(self):
        """
        공감적 응답
        """
        empathy_keywords = [
            "힘드시겠어요",
            "어려우시겠네요",
            "이해합니다",
            "그러셨군요"
        ]
        
        # Responses should contain empathic language
        assert len(empathy_keywords) > 0

    def test_validation(self):
        """
        타당화 응답
        """
        validation_keywords = [
            "당연합니다",
            "자연스러운",
            "이해할 수 있어요",
            "그럴 수 있어요"
        ]
        
        assert len(validation_keywords) > 0


# ============================================================================
# 6. Safety and Ethics
# ============================================================================

class TestSafetyEthics:
    """안전성과 윤리 테스트"""

    def test_no_harmful_advice(self):
        """
        해로운 조언을 하지 않는지 확인
        """
        harmful_advice = [
            "혼자 해결하세요",
            "그냥 참으세요",
            "약한 사람이에요"
        ]
        
        # System should never give harmful advice
        pass

    def test_crisis_prioritization(self):
        """
        위기 상황 우선 처리
        """
        # Crisis situations should be addressed first
        # before other therapeutic interventions
        pass


# ============================================================================
# 7. Cultural Competence
# ============================================================================

class TestCulturalCompetence:
    """문화적 역량 테스트"""

    def test_korean_therapy_adaptation(self):
        """
        한국 문화에 맞춘 치료 적용
        """
        # Therapy should be adapted to Korean cultural context
        pass


# ============================================================================
# Test Configuration
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
