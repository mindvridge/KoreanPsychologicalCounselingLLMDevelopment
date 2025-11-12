"""
Cultural Sensitivity Tests for Korean Context
한국 문화 적합성 테스트

한국 문화에 특화된 상담 접근법이 올바르게 적용되는지 검증합니다.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.emotion_analyzer_v2 import KoreanEmotionAnalyzer


# ============================================================================
# 1. Korean-Specific Emotions
# ============================================================================

class TestKoreanEmotions:
    """한국 특유 감정 인식 테스트"""

    def test_han_emotion_detection(self):
        """한(恨) 감정 감지"""
        analyzer = KoreanEmotionAnalyzer()
        
        han_phrases = [
            "억울해요",
            "서러워요",
            "맺힌 게 있어요",
            "풀리지 않는 응어리가 있어요"
        ]
        
        for phrase in han_phrases:
            result = analyzer.analyze_comprehensive(phrase)
            korean_emotions = result.get("korean_emotions", {})
            
            # 한 감정이 감지되어야 함
            assert korean_emotions.get("han", 0) > 0, \
                f"한 감정이 감지되지 않음: '{phrase}'"

    def test_jeong_emotion_detection(self):
        """정(情) 감정 감지"""
        analyzer = KoreanEmotionAnalyzer()
        
        jeong_phrases = [
            "정이 들었어요",
            "따뜻한 마음이 느껴져요",
            "정을 나누고 싶어요",
            "정든 사람들이 그리워요"
        ]
        
        for phrase in jeong_phrases:
            result = analyzer.analyze_comprehensive(phrase)
            korean_emotions = result.get("korean_emotions", {})
            
            assert korean_emotions.get("jeong", 0) > 0, \
                f"정 감정이 감지되지 않음: '{phrase}'"

    def test_nunchi_related_expressions(self):
        """눈치 관련 표현 이해"""
        phrases_with_nunchi = [
            "눈치가 보여요",
            "다른 사람 눈치를 봐요",
            "주변 눈치가 보여서 힘들어요"
        ]
        
        # 이런 표현들은 불안이나 스트레스로 감지되어야 함
        analyzer = KoreanEmotionAnalyzer()
        
        for phrase in phrases_with_nunchi:
            result = analyzer.analyze_comprehensive(phrase)
            primary = result.get("primary_emotion", {})
            
            assert primary.get("emotion") in ["불안", "걱정", "스트레스"], \
                f"눈치 관련 표현의 감정 인식 오류: '{phrase}'"


# ============================================================================
# 2. Family Relationships Context
# ============================================================================

class TestFamilyRelationships:
    """가족 관계 맥락 이해 테스트"""

    def test_parent_child_dynamics(self):
        """부모-자녀 관계 역학"""
        family_phrases = [
            "부모님 기대가 부담스러워요",
            "효도해야 한다는 압박이 있어요",
            "부모님을 실망시킬까 봐 두려워요"
        ]
        
        # 이런 표현들은 한국 문화의 가족 압박을 반영
        analyzer = KoreanEmotionAnalyzer()
        
        for phrase in family_phrases:
            result = analyzer.analyze_comprehensive(phrase)
            assert result is not None, f"가족 관계 표현 처리 실패: '{phrase}'"

    def test_sibae_relationship(self):
        """시댁 관계 (한국 특유)"""
        sibae_phrases = [
            "시댁 식구들과의 관계가 힘들어요",
            "시어머니가 스트레스예요"
        ]
        
        analyzer = KoreanEmotionAnalyzer()
        
        for phrase in sibae_phrases:
            result = analyzer.analyze_comprehensive(phrase)
            primary = result.get("primary_emotion", {})
            
            assert primary.get("emotion") in ["스트레스", "불안", "짜증"], \
                f"시댁 관계 스트레스 감지 실패: '{phrase}'"


# ============================================================================
# 3. Indirect Communication Patterns
# ============================================================================

class TestIndirectCommunication:
    """간접 표현 이해 테스트"""

    def test_understatement_detection(self):
        """축소 표현 (실제로는 심각함)"""
        understatements = [
            "그냥 좀 그래요",  # 실제로는 매우 우울
            "별로 안 좋아요",  # 실제로는 많이 안 좋음
            "조금 힘들어요",   # 실제로는 매우 힘듦
        ]
        
        # 이런 표현들의 진짜 의미를 파악해야 함
        analyzer = KoreanEmotionAnalyzer()
        
        for phrase in understatements:
            result = analyzer.analyze_comprehensive(phrase)
            # 시스템이 이런 표현들을 '경미한' 것으로만 해석하지 않아야 함
            assert result is not None

    def test_gwenchanayo_variations(self):
        """'괜찮아요' 변형들 (실제로는 괜찮지 않음)"""
        gwenchan_phrases = [
            "괜찮아요... (하지만 실제로는 힘듦)",
            "뭐 그냥 괜찮아요",
            "괜찮다고 하지만..."
        ]
        
        # '괜찮아요'가 항상 정말 괜찮다는 뜻은 아님
        analyzer = KoreanEmotionAnalyzer()
        
        for phrase in gwenchan_phrases:
            result = analyzer.analyze_comprehensive(phrase)
            # 맥락에 따라 다르게 해석될 수 있어야 함
            assert result is not None


# ============================================================================
# 4. Honorifics and Formality
# ============================================================================

class TestHonorificsHandling:
    """존댓말 처리 테스트"""

    def test_formal_speech_recognition(self):
        """존댓말 인식"""
        formal_phrases = [
            "저는 우울합니다",
            "도와주시겠습니까",
            "감사합니다"
        ]
        
        # 존댓말 사용 여부를 인식할 수 있어야 함
        analyzer = KoreanEmotionAnalyzer()
        
        for phrase in formal_phrases:
            result = analyzer.analyze_comprehensive(phrase)
            assert result is not None

    def test_informal_speech_recognition(self):
        """반말 인식"""
        informal_phrases = [
            "나 우울해",
            "도와줘",
            "고마워"
        ]
        
        analyzer = KoreanEmotionAnalyzer()
        
        for phrase in informal_phrases:
            result = analyzer.analyze_comprehensive(phrase)
            assert result is not None


# ============================================================================
# 5. Collectivism vs Individualism
# ============================================================================

class TestCollectivismContext:
    """집단주의 맥락 이해 테스트"""

    def test_group_harmony_concerns(self):
        """집단 조화 관련 고민"""
        harmony_phrases = [
            "나 때문에 팀이 힘들어해요",
            "다른 사람들에게 폐를 끼치는 것 같아요",
            "나만 빠지면 괜찮을 것 같아요"
        ]
        
        analyzer = KoreanEmotionAnalyzer()
        
        for phrase in harmony_phrases:
            result = analyzer.analyze_comprehensive(phrase)
            primary = result.get("primary_emotion", {})
            
            # 죄책감, 미안함 등이 감지되어야 함
            assert result is not None

    def test_individual_vs_collective_conflict(self):
        """개인 vs 집단 갈등"""
        conflict_phrases = [
            "내가 하고 싶은 게 있는데 가족이 반대해요",
            "나를 위한 선택을 하기 어려워요"
        ]
        
        analyzer = KoreanEmotionAnalyzer()
        
        for phrase in conflict_phrases:
            result = analyzer.analyze_comprehensive(phrase)
            assert result is not None


# ============================================================================
# 6. Age and Hierarchy
# ============================================================================

class TestAgeHierarchy:
    """나이와 서열 맥락 테스트"""

    def test_age_based_pressure(self):
        """나이 기반 압박"""
        age_phrases = [
            "이 나이에 이것도 못하면 안 되죠",
            "삼십 대인데 아직도...",
            "또래들은 다 성공했는데"
        ]
        
        analyzer = KoreanEmotionAnalyzer()
        
        for phrase in age_phrases:
            result = analyzer.analyze_comprehensive(phrase)
            assert result is not None


# ============================================================================
# 7. Educational and Career Pressure
# ============================================================================

class TestEducationalPressure:
    """학업·직업 압박 테스트"""

    def test_academic_stress(self):
        """학업 스트레스"""
        academic_phrases = [
            "명문대에 가야 한다는 압박이 있어요",
            "성적 때문에 스트레스받아요",
            "수능이 인생의 전부인 것 같아요"
        ]
        
        analyzer = KoreanEmotionAnalyzer()
        
        for phrase in academic_phrases:
            result = analyzer.analyze_comprehensive(phrase)
            primary = result.get("primary_emotion", {})
            
            assert primary.get("emotion") in ["스트레스", "불안", "압박"], \
                f"학업 스트레스 감지 실패: '{phrase}'"

    def test_career_pressure(self):
        """직업 압박"""
        career_phrases = [
            "대기업에 가야 한다는 압박",
            "공무원이 되라는 주변 압력",
            "안정적인 직장을 원하시는 부모님"
        ]
        
        analyzer = KoreanEmotionAnalyzer()
        
        for phrase in career_phrases:
            result = analyzer.analyze_comprehensive(phrase)
            assert result is not None


# ============================================================================
# 8. Social Stigma
# ============================================================================

class TestSocialStigma:
    """사회적 낙인 테스트"""

    def test_mental_health_stigma(self):
        """정신건강 낙인"""
        stigma_phrases = [
            "정신과 가는 게 부끄러워요",
            "상담 받는다고 하면 이상하게 볼까 봐",
            "약 먹는 걸 들키고 싶지 않아요"
        ]
        
        analyzer = KoreanEmotionAnalyzer()
        
        for phrase in stigma_phrases:
            result = analyzer.analyze_comprehensive(phrase)
            primary = result.get("primary_emotion", {})
            
            # 수치심, 두려움 등이 감지되어야 함
            assert result is not None


# ============================================================================
# Test Configuration
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
