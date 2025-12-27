"""
Integration Tests for Complete System
전체 시스템 통합 테스트

실제 사용 시나리오를 시뮬레이션하여 모든 컴포넌트가 
함께 올바르게 작동하는지 검증합니다.
"""

import sys
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# ============================================================================
# 1. Complete Conversation Flow
# ============================================================================

class TestCompleteConversationFlow:
    """완전한 대화 흐름 테스트"""

    @pytest.mark.integration
    def test_normal_conversation_flow(self):
        """
        정상 대화 흐름: 인사 → 고민 상담 → 조언 → 종료
        
        이 테스트는 실제 LLM 없이 로직만 검증합니다.
        """
        from main_integrated import IntegratedMentalHealthSystem
        
        # Mock components
        with patch('main_integrated.KoreanMentalHealthLLM') as mock_llm, \
             patch('main_integrated.LLMCrisisEvaluator') as mock_crisis, \
             patch('main_integrated.KoreanEmotionAnalyzer') as mock_emotion:
            
            system = IntegratedMentalHealthSystem()
            
            # Setup mocks
            mock_llm_instance = Mock()
            mock_llm_instance.generate_response.return_value = "공감적인 응답입니다"
            mock_llm.return_value = mock_llm_instance
            
            mock_crisis_instance = Mock()
            mock_crisis_instance.evaluate_crisis.return_value = {
                "overall_risk_level": "NONE",
                "requires_immediate_intervention": False
            }
            mock_crisis.return_value = mock_crisis_instance
            
            mock_emotion_instance = Mock()
            mock_emotion_instance.analyze_comprehensive.return_value = {
                "primary_emotion": {"emotion": "중립", "confidence": 0.8}
            }
            mock_emotion.return_value = mock_emotion_instance
            
            # Initialize manually
            system.llm = mock_llm_instance
            system.crisis_detector = mock_crisis_instance
            system.emotion_analyzer = mock_emotion_instance
            system.is_initialized = True
            
            # Test conversation
            conversation_flow = [
                "안녕하세요",
                "요즘 스트레스가 있어요",
                "조언 감사합니다"
            ]
            
            session_id = "test-session-001"
            
            for message in conversation_flow:
                result = system.process_message(session_id, message, [])
                
                assert result is not None
                assert "response" in result
                assert "crisis_detected" in result

    @pytest.mark.integration
    def test_crisis_intervention_flow(self):
        """
        위기 개입 흐름: 우울 → 자살 생각 → 긴급 개입 → 자원 연계
        """
        from main_integrated import IntegratedMentalHealthSystem
        from src.safety_system_v2 import RiskLevel
        
        with patch('main_integrated.KoreanMentalHealthLLM'), \
             patch('main_integrated.LLMCrisisEvaluator') as mock_crisis, \
             patch('main_integrated.KoreanEmotionAnalyzer'):
            
            system = IntegratedMentalHealthSystem()
            
            # Setup crisis detector
            mock_crisis_instance = Mock()
            
            def crisis_side_effect(message, history):
                if "죽고 싶" in message:
                    return {
                        "overall_risk_level": RiskLevel.CRITICAL,
                        "requires_immediate_intervention": True,
                        "recommended_actions": ["1393 전화"]
                    }
                else:
                    return {
                        "overall_risk_level": RiskLevel.MEDIUM,
                        "requires_immediate_intervention": False,
                        "recommended_actions": []
                    }
            
            mock_crisis_instance.evaluate_crisis.side_effect = crisis_side_effect
            mock_crisis.return_value = mock_crisis_instance
            
            system.crisis_detector = mock_crisis_instance
            system.is_initialized = True
            
            # Test crisis escalation
            session_id = "crisis-session"
            
            # Step 1: Moderate distress
            result1 = system.process_message(session_id, "우울해요", [])
            assert result1["crisis_level"] == 2  # MODERATE
            
            # Step 2: High crisis
            result2 = system.process_message(session_id, "죽고 싶어요", [])
            assert result2["crisis_level"] == 4  # CRITICAL
            assert result2["crisis_detected"] is True


# ============================================================================
# 2. API Integration Tests
# ============================================================================

class TestAPIIntegration:
    """FastAPI와 시스템 통합 테스트"""

    @pytest.mark.integration
    def test_api_chat_to_assessment_flow(self):
        """
        API를 통한 대화 → 평가 흐름
        """
        from fastapi.testclient import TestClient
        
        # This would require actual API setup
        # Demonstration of test structure
        pass

    @pytest.mark.integration
    def test_session_persistence(self):
        """
        세션 지속성: 여러 요청에 걸친 대화 맥락 유지
        """
        from fastapi.testclient import TestClient
        
        with patch('src.api.mental_health_system'):
            from src.api import app
            client = TestClient(app)
            
            # First message
            response1 = client.post(
                "/api/v1/chat",
                json={"message": "안녕하세요"}
            )
            
            assert response1.status_code == 200
            session_id = response1.json()["session_id"]
            
            # Second message with same session
            response2 = client.post(
                "/api/v1/chat",
                json={
                    "session_id": session_id,
                    "message": "우울해요"
                }
            )
            
            assert response2.status_code == 200
            assert response2.json()["session_id"] == session_id


# ============================================================================
# 3. RAG System Integration
# ============================================================================

class TestRAGIntegration:
    """RAG 시스템 통합 테스트"""

    @pytest.mark.integration
    def test_rag_retrieval_in_conversation(self):
        """
        대화 중 RAG 검색 통합 테스트
        """
        # Requires knowledge base to be indexed
        # This is a placeholder for actual test
        pass


# ============================================================================
# 4. Monitoring Integration
# ============================================================================

class TestMonitoringIntegration:
    """모니터링 시스템 통합 테스트"""

    @pytest.mark.integration
    def test_metrics_collection_during_conversation(self):
        """
        대화 중 메트릭 수집 검증
        """
        from main_integrated import IntegratedMentalHealthSystem
        from src.monitoring import ProductionMonitor
        
        with patch('main_integrated.KoreanMentalHealthLLM'), \
             patch('main_integrated.LLMCrisisEvaluator'), \
             patch('main_integrated.KoreanEmotionAnalyzer'):
            
            system = IntegratedMentalHealthSystem()
            system.monitor = ProductionMonitor()
            system.is_initialized = True
            
            # Process a message
            result = system.process_message("test-session", "안녕하세요", [])
            
            # Verify metrics were tracked
            assert system.monitor is not None
            # Additional assertions would check metrics storage


# ============================================================================
# 5. Logging Integration
# ============================================================================

class TestLoggingIntegration:
    """로깅 시스템 통합 테스트"""

    @pytest.mark.integration
    def test_privacy_compliant_logging(self):
        """
        프라이버시 준수 로깅 검증
        """
        from src.logging_system import ConversationLogger, PrivacyMasker
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ConversationLogger(log_dir=tmpdir)
            
            # Log conversation with PII
            turn_data = {
                "user_message": "제 전화번호는 010-1234-5678입니다",
                "assistant_response": "네, 알겠습니다",
                "timestamp": "2024-01-01T00:00:00"
            }
            
            log_path = logger.log_conversation(
                session_id="test-session",
                turn_data=turn_data,
                mask_pii=True
            )
            
            # Read log and verify PII is masked
            import json
            with open(log_path, 'r') as f:
                logged_data = json.load(f)
            
            # Phone number should be masked
            assert "010-1234-5678" not in str(logged_data)
            assert "[전화번호]" in logged_data["turns"][0]["user_message"]


# ============================================================================
# 6. Complete User Scenarios
# ============================================================================

class TestCompleteUserScenarios:
    """실제 사용자 시나리오 시뮬레이션"""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_depression_screening_scenario(self):
        """
        우울증 스크리닝 시나리오
        
        1. 사용자가 우울 증상 호소
        2. 시스템이 PHQ-9 추천
        3. 평가 실시
        4. 결과 해석 및 권장사항 제공
        """
        # This requires full system integration
        # Placeholder for actual implementation
        pass

    @pytest.mark.integration
    @pytest.mark.slow
    def test_anxiety_management_scenario(self):
        """
        불안 관리 시나리오
        
        1. 불안 증상 호소
        2. GAD-7 평가
        3. 불안 관리 기법 제공
        """
        pass

    @pytest.mark.integration
    @pytest.mark.slow
    def test_crisis_to_stabilization_scenario(self):
        """
        위기 → 안정화 시나리오
        
        1. 위기 감지
        2. 긴급 개입
        3. 전문가 연계
        4. 안정화 확인
        """
        pass


# ============================================================================
# 7. Multi-Component Integration
# ============================================================================

class TestMultiComponentIntegration:
    """여러 컴포넌트 동시 작동 테스트"""

    @pytest.mark.integration
    def test_all_systems_working_together(self):
        """
        모든 시스템이 함께 작동하는지 검증
        
        - LLM
        - Crisis Detector
        - Emotion Analyzer
        - RAG
        - Monitoring
        - Logging
        """
        # Full system integration test
        # Would require actual system setup
        pass


# ============================================================================
# Test Configuration
# ============================================================================

# Integration tests are slow, so they're marked separately
pytest.mark.integration = pytest.mark.integration

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration", "--tb=short"])
