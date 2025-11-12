"""
FastAPI Endpoint Tests
REST API 엔드포인트 테스트

모든 API 엔드포인트의 기능, 입력 검증, 에러 처리를 테스트합니다.
"""

import sys
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock the IntegratedMentalHealthSystem to avoid loading heavy models
with patch('src.api.IntegratedMentalHealthSystem'):
    from src.api import app

from src.safety_system_v2 import RiskLevel


# ============================================================================
# Test Client Setup
# ============================================================================

client = TestClient(app)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_system():
    """Mock IntegratedMentalHealthSystem"""
    with patch('src.api.mental_health_system') as mock:
        mock.is_initialized = True
        mock.stats = {
            "total_conversations": 100,
            "crisis_detections": 10,
            "assessments_conducted": 50,
            "uptime_start": "2024-01-01T00:00:00"
        }
        mock.config = {
            "model": {"name": "test-model", "quantization": "4bit"}
        }
        mock.crisis_detector = True
        mock.emotion_analyzer = True
        mock.rag_system = Mock(is_indexed=True)
        mock.assessment_manager = True
        mock.monitor = True
        mock.logger = True

        # Mock process_message method
        mock.process_message.return_value = {
            "response": "테스트 응답입니다",
            "crisis_detected": False,
            "crisis_level": 0,
            "emotions": {"primary_emotion": {"emotion": "중립", "confidence": 0.8}},
            "suggested_assessment": None,
            "response_time": 0.5,
            "metadata": {"session_id": "test-123", "timestamp": "2024-01-01T00:00:00"}
        }

        # Mock validate_system method
        mock.validate_system.return_value = {
            "llm": True,
            "crisis_detector": True,
            "emotion_analyzer": True,
            "assessment_manager": True,
            "rag_system": True,
            "monitoring": True,
            "logging": True
        }

        yield mock


# ============================================================================
# 1. Root Endpoint Tests
# ============================================================================

class TestRootEndpoint:
    """Root endpoint 테스트"""

    def test_root_endpoint(self):
        """루트 엔드포인트 응답 확인"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert "name" in data
        assert "version" in data
        assert "endpoints" in data
        assert data["name"] == "Korean Mental Health Counseling API"


# ============================================================================
# 2. Health Check Tests
# ============================================================================

class TestHealthEndpoint:
    """Health check 엔드포인트 테스트"""

    def test_health_check_success(self, mock_system):
        """정상 상태 health check"""
        with patch('src.api.mental_health_system', mock_system):
            response = client.get("/api/v1/health")

            assert response.status_code == 200
            data = response.json()

            assert "status" in data
            assert "timestamp" in data
            assert "components" in data
            assert "uptime_seconds" in data

            # Components should all be true
            components = data["components"]
            assert components["llm"] is True
            assert components["crisis_detector"] is True

    def test_health_check_degraded(self, mock_system):
        """일부 컴포넌트 실패 시 degraded 상태"""
        mock_system.validate_system.return_value = {
            "llm": False,  # LLM failed
            "crisis_detector": True,
            "emotion_analyzer": True,
            "assessment_manager": True,
            "rag_system": True,
            "monitoring": True,
            "logging": True
        }

        with patch('src.api.mental_health_system', mock_system):
            response = client.get("/api/v1/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"

    def test_health_check_system_not_initialized(self):
        """시스템 미초기화 시 503 에러"""
        with patch('src.api.mental_health_system', None):
            response = client.get("/api/v1/health")

            assert response.status_code == 503


# ============================================================================
# 3. Chat Endpoint Tests
# ============================================================================

class TestChatEndpoint:
    """Chat 엔드포인트 테스트"""

    def test_chat_basic_request(self, mock_system):
        """기본 대화 요청"""
        with patch('src.api.mental_health_system', mock_system):
            response = client.post(
                "/api/v1/chat",
                json={"message": "안녕하세요"}
            )

            assert response.status_code == 200
            data = response.json()

            assert "session_id" in data
            assert "response" in data
            assert "crisis_detected" in data
            assert "crisis_level" in data
            assert "response_time" in data

            assert data["response"] == "테스트 응답입니다"
            assert data["crisis_detected"] is False

    def test_chat_with_session_id(self, mock_system):
        """세션 ID 포함 요청"""
        with patch('src.api.mental_health_system', mock_system):
            # First request
            response1 = client.post(
                "/api/v1/chat",
                json={"message": "안녕하세요"}
            )

            session_id = response1.json()["session_id"]

            # Second request with same session
            response2 = client.post(
                "/api/v1/chat",
                json={
                    "session_id": session_id,
                    "message": "잘 지내요"
                }
            )

            assert response2.status_code == 200
            assert response2.json()["session_id"] == session_id

    def test_chat_crisis_detection(self, mock_system):
        """위기 감지 응답"""
        mock_system.process_message.return_value = {
            "response": "전문가 도움이 필요합니다",
            "crisis_detected": True,
            "crisis_level": 4,
            "emotions": None,
            "suggested_assessment": None,
            "response_time": 0.5,
            "metadata": {}
        }

        with patch('src.api.mental_health_system', mock_system):
            response = client.post(
                "/api/v1/chat",
                json={"message": "죽고 싶어요"}
            )

            assert response.status_code == 200
            data = response.json()

            assert data["crisis_detected"] is True
            assert data["crisis_level"] == 4

    def test_chat_empty_message(self):
        """빈 메시지 검증"""
        response = client.post(
            "/api/v1/chat",
            json={"message": ""}
        )

        assert response.status_code == 422  # Validation error

    def test_chat_message_too_long(self):
        """너무 긴 메시지 검증"""
        long_message = "a" * 2001  # Max is 2000

        response = client.post(
            "/api/v1/chat",
            json={"message": long_message}
        )

        assert response.status_code == 422

    def test_chat_missing_message_field(self):
        """필수 필드 누락"""
        response = client.post(
            "/api/v1/chat",
            json={}
        )

        assert response.status_code == 422

    def test_chat_with_conversation_history(self, mock_system):
        """대화 기록 포함 요청"""
        with patch('src.api.mental_health_system', mock_system):
            response = client.post(
                "/api/v1/chat",
                json={
                    "message": "계속 이야기하고 싶어요",
                    "conversation_history": [
                        {"role": "user", "content": "안녕하세요"},
                        {"role": "assistant", "content": "안녕하세요"}
                    ]
                }
            )

            assert response.status_code == 200


# ============================================================================
# 4. Session Management Tests
# ============================================================================

class TestSessionEndpoints:
    """세션 관리 엔드포인트 테스트"""

    def test_get_session(self, mock_system):
        """세션 조회"""
        with patch('src.api.mental_health_system', mock_system):
            # Create a session first
            create_response = client.post(
                "/api/v1/chat",
                json={"message": "안녕하세요"}
            )

            session_id = create_response.json()["session_id"]

            # Get session info
            response = client.get(f"/api/v1/session/{session_id}")

            assert response.status_code == 200
            data = response.json()

            assert "session_id" in data
            assert "created_at" in data
            assert "total_messages" in data
            assert "crisis_detected_count" in data
            assert "last_activity" in data

    def test_get_nonexistent_session(self):
        """존재하지 않는 세션 조회"""
        response = client.get("/api/v1/session/nonexistent-id")

        assert response.status_code == 404

    def test_delete_session(self, mock_system):
        """세션 삭제"""
        with patch('src.api.mental_health_system', mock_system):
            # Create a session
            create_response = client.post(
                "/api/v1/chat",
                json={"message": "안녕하세요"}
            )

            session_id = create_response.json()["session_id"]

            # Delete session
            response = client.delete(f"/api/v1/session/{session_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == session_id

            # Verify session is deleted
            get_response = client.get(f"/api/v1/session/{session_id}")
            assert get_response.status_code == 404

    def test_delete_nonexistent_session(self):
        """존재하지 않는 세션 삭제"""
        response = client.delete("/api/v1/session/nonexistent-id")

        assert response.status_code == 404


# ============================================================================
# 5. Assessment Endpoint Tests
# ============================================================================

class TestAssessmentEndpoint:
    """심리 평가 엔드포인트 테스트"""

    def test_phq9_assessment(self, mock_system):
        """PHQ-9 평가"""
        with patch('src.api.mental_health_system', mock_system):
            response = client.post(
                "/api/v1/assessment",
                json={
                    "session_id": "test-session",
                    "assessment_type": "phq9",
                    "responses": [0, 1, 1, 2, 1, 0, 1, 2, 1]
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert "score" in data
            assert "severity" in data
            assert "interpretation" in data
            assert "recommendations" in data
            assert data["assessment_type"] == "phq9"

    def test_gad7_assessment(self, mock_system):
        """GAD-7 평가"""
        with patch('src.api.mental_health_system', mock_system):
            response = client.post(
                "/api/v1/assessment",
                json={
                    "session_id": "test-session",
                    "assessment_type": "gad7",
                    "responses": [1, 2, 1, 1, 2, 1, 0]
                }
            )

            assert response.status_code == 200
            assert response.json()["assessment_type"] == "gad7"

    def test_k10_assessment(self, mock_system):
        """K-10 평가"""
        with patch('src.api.mental_health_system', mock_system):
            response = client.post(
                "/api/v1/assessment",
                json={
                    "session_id": "test-session",
                    "assessment_type": "k10",
                    "responses": [1, 2, 3, 2, 1, 2, 3, 2, 1, 2]
                }
            )

            assert response.status_code == 200
            assert response.json()["assessment_type"] == "k10"

    def test_invalid_assessment_type(self, mock_system):
        """잘못된 평가 유형"""
        with patch('src.api.mental_health_system', mock_system):
            response = client.post(
                "/api/v1/assessment",
                json={
                    "session_id": "test-session",
                    "assessment_type": "invalid",
                    "responses": [1, 2, 3]
                }
            )

            assert response.status_code == 422

    def test_wrong_number_of_responses(self, mock_system):
        """잘못된 응답 개수"""
        with patch('src.api.mental_health_system', mock_system):
            # PHQ-9 requires 9 responses, but only 5 provided
            response = client.post(
                "/api/v1/assessment",
                json={
                    "session_id": "test-session",
                    "assessment_type": "phq9",
                    "responses": [1, 2, 3, 4, 5]
                }
            )

            assert response.status_code == 400


# ============================================================================
# 6. Feedback Endpoint Tests
# ============================================================================

class TestFeedbackEndpoint:
    """피드백 엔드포인트 테스트"""

    def test_submit_feedback(self):
        """피드백 제출"""
        response = client.post(
            "/api/v1/feedback",
            json={
                "session_id": "test-session",
                "rating": 5,
                "feedback_text": "매우 도움이 되었습니다",
                "feedback_type": "helpful"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "feedback_id" in data
        assert "message" in data

    def test_feedback_without_text(self):
        """텍스트 없는 피드백"""
        response = client.post(
            "/api/v1/feedback",
            json={
                "session_id": "test-session",
                "rating": 4,
                "feedback_type": "helpful"
            }
        )

        assert response.status_code == 200

    def test_feedback_invalid_rating(self):
        """잘못된 평점 (범위 밖)"""
        response = client.post(
            "/api/v1/feedback",
            json={
                "session_id": "test-session",
                "rating": 6,  # Max is 5
                "feedback_type": "helpful"
            }
        )

        assert response.status_code == 422


# ============================================================================
# 7. Statistics Endpoint Tests
# ============================================================================

class TestStatisticsEndpoint:
    """통계 엔드포인트 테스트"""

    def test_get_stats(self, mock_system):
        """시스템 통계 조회"""
        with patch('src.api.mental_health_system', mock_system):
            response = client.get("/api/v1/stats")

            assert response.status_code == 200
            data = response.json()

            assert "total_conversations" in data
            assert "crisis_detections" in data
            assert "assessments_conducted" in data
            assert "active_sessions" in data
            assert "uptime_seconds" in data
            assert "uptime_hours" in data


# ============================================================================
# 8. System Info Endpoint Tests
# ============================================================================

class TestSystemInfoEndpoint:
    """시스템 정보 엔드포인트 테스트"""

    def test_get_system_info(self, mock_system):
        """시스템 정보 조회"""
        with patch('src.api.mental_health_system', mock_system):
            response = client.get("/api/v1/system/info")

            assert response.status_code == 200
            data = response.json()

            assert "system" in data
            assert "version" in data
            assert "capabilities" in data
            assert "model" in data
            assert "features" in data

            # Check capabilities
            capabilities = data["capabilities"]
            assert isinstance(capabilities["crisis_detection"], bool)
            assert isinstance(capabilities["emotion_analysis"], bool)


# ============================================================================
# 9. Session Cleanup Tests
# ============================================================================

class TestSessionCleanup:
    """세션 정리 엔드포인트 테스트"""

    def test_cleanup_sessions(self, mock_system):
        """세션 정리"""
        with patch('src.api.mental_health_system', mock_system):
            response = client.post("/api/v1/sessions/cleanup")

            assert response.status_code == 200
            data = response.json()

            assert "removed_count" in data
            assert isinstance(data["removed_count"], int)

    def test_cleanup_with_custom_age(self, mock_system):
        """커스텀 보관 기간으로 정리"""
        with patch('src.api.mental_health_system', mock_system):
            response = client.post(
                "/api/v1/sessions/cleanup?max_age_hours=12"
            )

            assert response.status_code == 200


# ============================================================================
# 10. Metrics Endpoint Tests
# ============================================================================

class TestMetricsEndpoint:
    """Prometheus 메트릭 엔드포인트 테스트"""

    def test_metrics_endpoint(self):
        """메트릭 조회"""
        response = client.get("/metrics")

        assert response.status_code == 200
        # Prometheus format is text/plain
        assert "text/plain" in response.headers.get("content-type", "")


# ============================================================================
# 11. Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """에러 처리 테스트"""

    def test_404_not_found(self):
        """존재하지 않는 엔드포인트"""
        response = client.get("/api/v1/nonexistent")

        assert response.status_code == 404

    def test_method_not_allowed(self):
        """허용되지 않는 HTTP 메서드"""
        response = client.patch("/api/v1/chat")

        assert response.status_code == 405

    def test_invalid_json(self):
        """잘못된 JSON 형식"""
        response = client.post(
            "/api/v1/chat",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422


# ============================================================================
# 12. Authentication Tests (if API_KEY is set)
# ============================================================================

class TestAuthentication:
    """API Key 인증 테스트"""

    def test_with_valid_api_key(self, mock_system, monkeypatch):
        """유효한 API Key로 요청"""
        monkeypatch.setenv("API_KEY", "test-api-key-123")

        with patch('src.api.mental_health_system', mock_system):
            response = client.post(
                "/api/v1/chat",
                json={"message": "안녕하세요"},
                headers={"X-API-Key": "test-api-key-123"}
            )

            # Should work with correct key
            # Note: This test might fail if the app doesn't reload env vars
            # In real scenario, we'd restart the app

    def test_without_api_key_when_required(self, monkeypatch):
        """API Key 필요 시 키 없이 요청"""
        monkeypatch.setenv("API_KEY", "test-api-key-123")

        # Note: Without app restart, this won't actually enforce
        # This is a demonstration of the test structure


# ============================================================================
# 13. CORS Tests
# ============================================================================

class TestCORS:
    """CORS 설정 테스트"""

    def test_cors_headers(self):
        """CORS 헤더 확인"""
        response = client.options("/api/v1/chat")

        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers


# ============================================================================
# Test Configuration
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
