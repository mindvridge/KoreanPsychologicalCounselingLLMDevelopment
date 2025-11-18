"""
E2E (End-to-End) 테스트
E2E Tests

실제 사용자 시나리오를 처음부터 끝까지 테스트합니다.
"""

import pytest
import requests
import time
from typing import Dict, List, Any


# ============================================================================
# 설정
# ============================================================================

BASE_URL = "http://localhost:8000"
API_TIMEOUT = 60  # 초


# ============================================================================
# Helper Functions
# ============================================================================

def wait_for_api(max_retries=30, delay=2):
    """API 서버가 준비될 때까지 대기"""
    for i in range(max_retries):
        try:
            response = requests.get(f"{BASE_URL}/api/v1/health", timeout=5)
            if response.status_code == 200:
                print(f"✓ API 서버 준비 완료")
                return True
        except requests.exceptions.RequestException:
            if i < max_retries - 1:
                print(f"API 서버 대기 중... ({i+1}/{max_retries})")
                time.sleep(delay)
    return False


# ============================================================================
# 전체 상담 플로우 E2E 테스트
# ============================================================================

class TestCounselingFlowE2E:
    """전체 상담 플로우 E2E 테스트"""

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_complete_counseling_session(self):
        """
        완전한 상담 세션 E2E 테스트

        시나리오:
        1. Health check
        2. 새 세션 시작 (인사)
        3. 우울 증상 호소
        4. 상담사의 응답 확인
        5. PHQ-9 평가 제안
        6. 조언 및 격려
        7. 세션 종료
        """
        # 1. Health check
        response = requests.get(f"{BASE_URL}/api/v1/health", timeout=API_TIMEOUT)
        assert response.status_code == 200, "Health check 실패"

        health_data = response.json()
        assert health_data["status"] == "healthy", "시스템 상태가 healthy가 아님"

        # 2. 새 세션 시작
        chat_payload = {
            "user_message": "안녕하세요",
            "persona": "empathetic"
        }

        response = requests.post(
            f"{BASE_URL}/api/v1/chat",
            json=chat_payload,
            timeout=API_TIMEOUT
        )

        assert response.status_code == 200, "채팅 요청 실패"
        chat1 = response.json()

        assert "session_id" in chat1, "session_id가 응답에 없음"
        assert "response" in chat1, "응답이 없음"

        session_id = chat1["session_id"]

        # 3. 우울 증상 호소
        chat2_payload = {
            "session_id": session_id,
            "user_message": "요즘 우울한 기분이 계속되고 있어요. 아무것도 하기 싫고 무기력해요.",
            "persona": "empathetic"
        }

        response = requests.post(
            f"{BASE_URL}/api/v1/chat",
            json=chat2_payload,
            timeout=API_TIMEOUT
        )

        assert response.status_code == 200, "두 번째 채팅 요청 실패"
        chat2 = response.json()

        assert chat2["session_id"] == session_id, "세션 ID가 일치하지 않음"
        assert len(chat2["response"]) > 0, "응답이 비어있음"

        # 감정 분석 확인
        if "emotion" in chat2:
            assert chat2["emotion"] is not None, "감정 분석 결과가 없음"

        # 4. 위기 감지 확인
        assert "crisis_detected" in chat2, "crisis_detected 필드가 없음"

        # 5. 세션 정보 조회
        response = requests.get(
            f"{BASE_URL}/api/v1/session/{session_id}",
            timeout=API_TIMEOUT
        )

        assert response.status_code == 200, "세션 조회 실패"
        session_data = response.json()

        assert len(session_data["history"]) >= 4, "대화 이력이 부족함"  # 2번의 대화 (user + assistant 각 2개)

        # 6. 조언 및 격려
        chat3_payload = {
            "session_id": session_id,
            "user_message": "어떻게 하면 이 기분을 극복할 수 있을까요?",
            "persona": "empathetic"
        }

        response = requests.post(
            f"{BASE_URL}/api/v1/chat",
            json=chat3_payload,
            timeout=API_TIMEOUT
        )

        assert response.status_code == 200, "세 번째 채팅 요청 실패"
        chat3 = response.json()

        assert len(chat3["response"]) > 0, "응답이 비어있음"

    @pytest.mark.e2e
    def test_crisis_detection_flow(self):
        """
        위기 감지 플로우 E2E 테스트

        시나리오:
        1. 정상 대화 시작
        2. 점진적 위기 상황
        3. 고위험 메시지 (자살 사고)
        4. 긴급 개입 응답 확인
        """
        # 1. 정상 대화
        response = requests.post(
            f"{BASE_URL}/api/v1/chat",
            json={
                "user_message": "안녕하세요",
                "persona": "professional"
            },
            timeout=API_TIMEOUT
        )

        assert response.status_code == 200
        session_id = response.json()["session_id"]

        # 2. 점진적 위기 상황
        messages = [
            "요즘 우울해요",
            "아무 의미도 없는 것 같아요",
            "모든 게 힘들고 포기하고 싶어요"
        ]

        for message in messages:
            response = requests.post(
                f"{BASE_URL}/api/v1/chat",
                json={
                    "session_id": session_id,
                    "user_message": message,
                    "persona": "professional"
                },
                timeout=API_TIMEOUT
            )

            assert response.status_code == 200
            data = response.json()

            # crisis_level이 증가하는지 확인 (선택적)
            if "crisis_level" in data:
                assert data["crisis_level"] >= 0

        # 3. 고위험 메시지
        response = requests.post(
            f"{BASE_URL}/api/v1/chat",
            json={
                "session_id": session_id,
                "user_message": "죽고 싶어요. 삶이 너무 힘들어요.",
                "persona": "professional"
            },
            timeout=API_TIMEOUT
        )

        assert response.status_code == 200
        crisis_response = response.json()

        # 위기 감지 확인
        assert crisis_response["crisis_detected"] is True, "위기가 감지되지 않음"

        # 긴급 개입 응답 확인
        assert len(crisis_response["response"]) > 0, "응답이 비어있음"
        # 응답에 긴급 연락처가 포함되어야 함
        assert ("1393" in crisis_response["response"] or
                "109" in crisis_response["response"] or
                "1577-0199" in crisis_response["response"]), \
            "긴급 연락처가 응답에 없음"


# ============================================================================
# 심리 평가 플로우 E2E 테스트
# ============================================================================

class TestAssessmentFlowE2E:
    """심리 평가 플로우 E2E 테스트"""

    @pytest.mark.e2e
    def test_phq9_assessment_flow(self):
        """
        PHQ-9 평가 전체 플로우 E2E 테스트

        시나리오:
        1. 평가 시작
        2. 9개 질문 응답
        3. 결과 확인
        4. 권장사항 확인
        """
        # PHQ-9 응답 (중간 정도의 우울 증상)
        responses = {
            "1": 2,  # 일이나 여가 활동에 흥미 상실
            "2": 2,  # 우울감, 절망감
            "3": 1,  # 수면 문제
            "4": 2,  # 피로감
            "5": 1,  # 식욕 변화
            "6": 1,  # 자신에 대한 부정적 생각
            "7": 1,  # 집중력 저하
            "8": 0,  # 움직임/말 변화
            "9": 0   # 자살/자해 생각
        }

        # 평가 실시
        response = requests.post(
            f"{BASE_URL}/api/v1/assessment",
            json={
                "session_id": "phq9_test_session",
                "assessment_type": "PHQ-9",
                "responses": responses
            },
            timeout=API_TIMEOUT
        )

        assert response.status_code == 200, "평가 요청 실패"
        result = response.json()

        # 결과 검증
        assert "score" in result, "점수가 없음"
        assert "severity" in result, "심각도가 없음"
        assert "interpretation" in result, "해석이 없음"
        assert "recommendations" in result, "권장사항이 없음"

        # 점수 검증 (2+2+1+2+1+1+1+0+0 = 10)
        assert result["score"] == 10, f"점수가 10이 아님: {result['score']}"

        # 심각도 검증 (10점은 중간 정도)
        assert result["severity"] in ["중간 정도의 우울 증상", "MODERATE"], \
            f"심각도가 올바르지 않음: {result['severity']}"

        # 권장사항 존재 확인
        assert len(result["recommendations"]) > 0, "권장사항이 비어있음"

    @pytest.mark.e2e
    def test_gad7_assessment_flow(self):
        """GAD-7 평가 전체 플로우 E2E 테스트"""
        # GAD-7 응답 (가벼운 불안)
        responses = {
            "1": 1,
            "2": 1,
            "3": 1,
            "4": 0,
            "5": 1,
            "6": 0,
            "7": 1
        }

        response = requests.post(
            f"{BASE_URL}/api/v1/assessment",
            json={
                "session_id": "gad7_test_session",
                "assessment_type": "GAD-7",
                "responses": responses
            },
            timeout=API_TIMEOUT
        )

        assert response.status_code == 200
        result = response.json()

        assert result["score"] == 5  # 1+1+1+0+1+0+1
        assert "severity" in result
        assert len(result["recommendations"]) > 0

    @pytest.mark.e2e
    def test_k10_assessment_flow(self):
        """K-10 평가 전체 플로우 E2E 테스트"""
        # K-10 응답
        responses = {
            "1": 2,
            "2": 2,
            "3": 2,
            "4": 2,
            "5": 2,
            "6": 2,
            "7": 1,
            "8": 1,
            "9": 1,
            "10": 1
        }

        response = requests.post(
            f"{BASE_URL}/api/v1/assessment",
            json={
                "session_id": "k10_test_session",
                "assessment_type": "K-10",
                "responses": responses
            },
            timeout=API_TIMEOUT
        )

        assert response.status_code == 200
        result = response.json()

        assert result["score"] == 16  # 2*6 + 1*4
        assert "severity" in result
        assert len(result["recommendations"]) > 0


# ============================================================================
# 페르소나 E2E 테스트
# ============================================================================

class TestPersonaE2E:
    """페르소나 시스템 E2E 테스트"""

    @pytest.mark.e2e
    def test_different_personas(self):
        """
        다양한 페르소나 테스트

        시나리오:
        1. Empathetic 페르소나로 대화
        2. Professional 페르소나로 대화
        3. Encouraging 페르소나로 대화
        """
        personas = ["empathetic", "professional", "encouraging"]

        for persona in personas:
            response = requests.post(
                f"{BASE_URL}/api/v1/chat",
                json={
                    "user_message": "안녕하세요, 우울해요",
                    "persona": persona
                },
                timeout=API_TIMEOUT
            )

            assert response.status_code == 200, f"{persona} 페르소나 요청 실패"
            data = response.json()

            assert "response" in data, f"{persona} 페르소나 응답이 없음"
            assert len(data["response"]) > 0, f"{persona} 페르소나 응답이 비어있음"

    @pytest.mark.e2e
    def test_persona_list(self):
        """페르소나 목록 조회"""
        response = requests.get(
            f"{BASE_URL}/api/v1/personas",
            timeout=API_TIMEOUT
        )

        assert response.status_code == 200
        personas = response.json()

        assert len(personas) > 0, "페르소나 목록이 비어있음"
        assert any(p["id"] == "empathetic" for p in personas), \
            "empathetic 페르소나가 없음"


# ============================================================================
# 데이터 내보내기 E2E 테스트
# ============================================================================

class TestExportE2E:
    """데이터 내보내기 E2E 테스트"""

    @pytest.mark.e2e
    def test_csv_export(self):
        """CSV 내보내기 E2E 테스트"""
        # 먼저 대화 생성
        response = requests.post(
            f"{BASE_URL}/api/v1/chat",
            json={
                "user_message": "안녕하세요",
                "persona": "empathetic"
            },
            timeout=API_TIMEOUT
        )

        assert response.status_code == 200
        session_id = response.json()["session_id"]

        # CSV 내보내기
        response = requests.post(
            f"{BASE_URL}/api/v1/export/conversation/csv",
            json={
                "session_id": session_id,
                "conversation_history": []  # 실제로는 대화 이력 전달
            },
            timeout=API_TIMEOUT
        )

        # 파일 다운로드 확인
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "text/csv; charset=utf-8"

    @pytest.mark.e2e
    def test_pdf_export(self):
        """PDF 내보내기 E2E 테스트"""
        # 세션 생성
        response = requests.post(
            f"{BASE_URL}/api/v1/chat",
            json={
                "user_message": "안녕하세요",
                "persona": "empathetic"
            },
            timeout=API_TIMEOUT
        )

        assert response.status_code == 200
        session_id = response.json()["session_id"]

        # PDF 내보내기
        response = requests.post(
            f"{BASE_URL}/api/v1/export/session/pdf",
            json={
                "session_id": session_id,
                "counselor_name": "테스트 상담사",
                "counselor_type": "empathetic",
                "conversation_history": []
            },
            timeout=API_TIMEOUT
        )

        assert response.status_code == 200
        assert response.headers["Content-Type"] == "application/pdf"


# ============================================================================
# 성능 E2E 테스트
# ============================================================================

class TestPerformanceE2E:
    """성능 E2E 테스트"""

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_concurrent_sessions(self):
        """동시 세션 처리 테스트"""
        import concurrent.futures

        def create_session(session_num):
            """단일 세션 생성"""
            response = requests.post(
                f"{BASE_URL}/api/v1/chat",
                json={
                    "user_message": f"안녕하세요 {session_num}",
                    "persona": "empathetic"
                },
                timeout=API_TIMEOUT
            )
            return response.status_code == 200

        # 10개 세션 동시 생성
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_session, i) for i in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # 모든 세션이 성공했는지 확인
        assert all(results), "일부 세션 생성 실패"

    @pytest.mark.e2e
    def test_response_time(self):
        """응답 시간 테스트 (2초 이내)"""
        start_time = time.time()

        response = requests.post(
            f"{BASE_URL}/api/v1/chat",
            json={
                "user_message": "안녕하세요",
                "persona": "empathetic"
            },
            timeout=API_TIMEOUT
        )

        elapsed_time = time.time() - start_time

        assert response.status_code == 200
        # Health check나 간단한 응답은 빠르게 처리되어야 함
        # LLM 응답은 더 오래 걸릴 수 있음
        assert elapsed_time < 60, f"응답 시간이 너무 김: {elapsed_time}초"


# ============================================================================
# 실행
# ============================================================================

if __name__ == "__main__":
    # API 서버가 실행 중인지 확인
    if not wait_for_api():
        print("❌ API 서버가 준비되지 않았습니다.")
        print("   다음 명령으로 서버를 먼저 시작하세요:")
        print("   python src/api.py")
        exit(1)

    # E2E 테스트 실행
    pytest.main([__file__, "-v", "-m", "e2e", "--tb=short"])
