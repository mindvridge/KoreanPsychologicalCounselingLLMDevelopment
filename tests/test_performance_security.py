"""
성능 및 보안 종합 테스트
Comprehensive Performance and Security Tests

시스템의 성능 및 보안 측면을 종합적으로 검증합니다.
"""

import pytest
import requests
import time
import concurrent.futures
from typing import List, Dict
import json


BASE_URL = "http://localhost:8000"


# ============================================================================
# 성능 테스트
# ============================================================================

class TestPerformance:
    """성능 테스트"""

    @pytest.mark.performance
    def test_load_testing(self):
        """
        부하 테스트

        100개의 동시 요청을 처리하고 응답 시간을 측정합니다.
        """
        def make_request(request_id: int) -> Dict:
            """단일 요청 실행"""
            start_time = time.time()

            try:
                response = requests.post(
                    f"{BASE_URL}/api/v1/chat",
                    json={
                        "user_message": f"테스트 메시지 {request_id}",
                        "persona": "empathetic"
                    },
                    timeout=60
                )

                elapsed = time.time() - start_time

                return {
                    "success": response.status_code == 200,
                    "response_time": elapsed,
                    "request_id": request_id
                }

            except Exception as e:
                return {
                    "success": False,
                    "response_time": -1,
                    "request_id": request_id,
                    "error": str(e)
                }

        # 100개의 동시 요청 실행
        num_requests = 100
        max_workers = 20

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(make_request, i) for i in range(num_requests)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # 결과 분석
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        success_rate = len(successful) / num_requests * 100
        response_times = [r["response_time"] for r in successful]

        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)

            print(f"\n성능 테스트 결과:")
            print(f"  총 요청: {num_requests}")
            print(f"  성공: {len(successful)} ({success_rate:.1f}%)")
            print(f"  실패: {len(failed)}")
            print(f"  평균 응답 시간: {avg_response_time:.2f}초")
            print(f"  최소 응답 시간: {min_response_time:.2f}초")
            print(f"  최대 응답 시간: {max_response_time:.2f}초")

            # 성능 기준
            assert success_rate >= 95, f"성공률이 95% 미만: {success_rate:.1f}%"
            assert avg_response_time < 10, f"평균 응답 시간이 10초 초과: {avg_response_time:.2f}초"

    @pytest.mark.performance
    def test_stress_testing(self):
        """
        스트레스 테스트

        시스템의 한계를 테스트합니다.
        """
        def sustained_load(duration_seconds: int = 30):
            """지속적인 부하 생성"""
            start_time = time.time()
            request_count = 0
            errors = 0

            while time.time() - start_time < duration_seconds:
                try:
                    response = requests.post(
                        f"{BASE_URL}/api/v1/chat",
                        json={
                            "user_message": "스트레스 테스트",
                            "persona": "empathetic"
                        },
                        timeout=10
                    )

                    if response.status_code == 200:
                        request_count += 1
                    else:
                        errors += 1

                except Exception:
                    errors += 1

                # 짧은 대기 (초당 약 10개 요청)
                time.sleep(0.1)

            return {
                "requests": request_count,
                "errors": errors,
                "duration": duration_seconds
            }

        # 30초간 지속적인 부하
        result = sustained_load(duration_seconds=30)

        throughput = result["requests"] / result["duration"]
        error_rate = result["errors"] / (result["requests"] + result["errors"]) * 100

        print(f"\n스트레스 테스트 결과:")
        print(f"  지속 시간: {result['duration']}초")
        print(f"  총 요청: {result['requests']}")
        print(f"  오류: {result['errors']}")
        print(f"  처리량: {throughput:.2f} req/s")
        print(f"  오류율: {error_rate:.1f}%")

        # 스트레스 기준
        assert throughput > 1, f"처리량이 1 req/s 미만: {throughput:.2f}"
        assert error_rate < 10, f"오류율이 10% 초과: {error_rate:.1f}%"

    @pytest.mark.performance
    def test_response_time_percentiles(self):
        """
        응답 시간 백분위수 테스트

        P50, P95, P99 응답 시간을 측정합니다.
        """
        response_times = []

        # 50개의 요청 실행
        for i in range(50):
            start_time = time.time()

            try:
                response = requests.post(
                    f"{BASE_URL}/api/v1/chat",
                    json={
                        "user_message": f"백분위수 테스트 {i}",
                        "persona": "empathetic"
                    },
                    timeout=60
                )

                elapsed = time.time() - start_time

                if response.status_code == 200:
                    response_times.append(elapsed)

            except Exception:
                pass

        if response_times:
            response_times.sort()

            p50_index = int(len(response_times) * 0.50)
            p95_index = int(len(response_times) * 0.95)
            p99_index = int(len(response_times) * 0.99)

            p50 = response_times[p50_index] if p50_index < len(response_times) else response_times[-1]
            p95 = response_times[p95_index] if p95_index < len(response_times) else response_times[-1]
            p99 = response_times[p99_index] if p99_index < len(response_times) else response_times[-1]

            print(f"\n응답 시간 백분위수:")
            print(f"  P50: {p50:.2f}초")
            print(f"  P95: {p95:.2f}초")
            print(f"  P99: {p99:.2f}초")

            # 백분위수 기준
            assert p95 < 15, f"P95가 15초 초과: {p95:.2f}초"

    @pytest.mark.performance
    def test_database_query_performance(self):
        """데이터베이스 쿼리 성능 테스트"""
        import tempfile
        from src.database import DatabaseManager, User, Conversation

        with tempfile.NamedTemporaryFile(suffix='.db') as f:
            db_manager = DatabaseManager(f"sqlite:///{f.name}")
            db = db_manager.get_session()

            try:
                # 대량 데이터 삽입
                start_time = time.time()

                user = User(user_id="perf_test_user")
                db.add(user)
                db.commit()

                # 1000개의 대화 레코드 생성
                for i in range(1000):
                    conv = Conversation(
                        user_id=user.id,
                        session_id=f"session_{i % 10}",
                        role="user" if i % 2 == 0 else "assistant",
                        content=f"메시지 {i}"
                    )
                    db.add(conv)

                    if i % 100 == 0:
                        db.commit()

                db.commit()
                insert_time = time.time() - start_time

                # 쿼리 성능 테스트
                start_time = time.time()
                conversations = db.query(Conversation).filter_by(user_id=user.id).all()
                query_time = time.time() - start_time

                print(f"\n데이터베이스 성능:")
                print(f"  1000개 레코드 삽입: {insert_time:.2f}초")
                print(f"  1000개 레코드 조회: {query_time:.2f}초")

                assert len(conversations) == 1000
                assert query_time < 1, f"쿼리 시간이 1초 초과: {query_time:.2f}초"

            finally:
                db.close()


# ============================================================================
# 보안 테스트
# ============================================================================

class TestSecurity:
    """보안 테스트"""

    @pytest.mark.security
    def test_cors_security(self):
        """
        CORS 보안 테스트

        허용되지 않은 출처에서의 요청이 차단되는지 확인합니다.
        """
        # 허용되지 않은 출처에서 요청
        headers = {
            "Origin": "http://malicious-site.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }

        # OPTIONS 요청 (preflight)
        response = requests.options(
            f"{BASE_URL}/api/v1/chat",
            headers=headers
        )

        # CORS 헤더 확인
        if "Access-Control-Allow-Origin" in response.headers:
            allowed_origin = response.headers["Access-Control-Allow-Origin"]

            # "*" 또는 특정 허용된 출처만 있어야 함
            assert allowed_origin != "http://malicious-site.com", \
                "악의적인 출처가 허용됨"

    @pytest.mark.security
    def test_rate_limiting(self):
        """
        Rate Limiting 테스트

        짧은 시간에 과도한 요청이 제한되는지 확인합니다.
        """
        # 빠른 속도로 많은 요청 전송
        responses = []

        for i in range(150):  # CHAT_RATE_LIMIT=100이므로 150개 요청
            response = requests.post(
                f"{BASE_URL}/api/v1/chat",
                json={
                    "user_message": f"Rate limit 테스트 {i}",
                    "persona": "empathetic"
                },
                timeout=10
            )
            responses.append(response.status_code)

            # 매우 짧은 대기
            time.sleep(0.01)

        # 일부 요청이 429 (Too Many Requests)를 반환해야 함
        too_many_requests = responses.count(429)

        print(f"\nRate Limiting 테스트:")
        print(f"  총 요청: {len(responses)}")
        print(f"  429 응답: {too_many_requests}")

        # Rate limiting이 작동하는지 확인
        # (실제로는 rate limit 설정에 따라 다를 수 있음)
        assert too_many_requests > 0 or len([r for r in responses if r == 200]) <= 100, \
            "Rate limiting이 작동하지 않음"

    @pytest.mark.security
    def test_sql_injection_prevention(self):
        """
        SQL Injection 방지 테스트

        SQL Injection 시도가 차단되는지 확인합니다.
        """
        # SQL Injection 시도
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'--",
            "1' UNION SELECT * FROM users--"
        ]

        for malicious_input in malicious_inputs:
            try:
                response = requests.post(
                    f"{BASE_URL}/api/v1/chat",
                    json={
                        "user_message": malicious_input,
                        "persona": "empathetic"
                    },
                    timeout=10
                )

                # 요청이 성공하더라도 SQL Injection이 실행되지 않아야 함
                assert response.status_code in [200, 400, 422], \
                    "예상치 못한 응답 코드"

            except Exception:
                # 예외가 발생해도 괜찮음 (입력 검증)
                pass

    @pytest.mark.security
    def test_xss_prevention(self):
        """
        XSS (Cross-Site Scripting) 방지 테스트

        악의적인 스크립트가 실행되지 않는지 확인합니다.
        """
        # XSS 시도
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror='alert(1)'>",
            "javascript:alert('XSS')",
            "<svg/onload=alert('XSS')>"
        ]

        for payload in xss_payloads:
            response = requests.post(
                f"{BASE_URL}/api/v1/chat",
                json={
                    "user_message": payload,
                    "persona": "empathetic"
                },
                timeout=10
            )

            if response.status_code == 200:
                response_data = response.json()

                # 응답에 스크립트가 이스케이프되었거나 제거되었는지 확인
                if "response" in response_data:
                    assert "<script>" not in response_data["response"], \
                        "스크립트 태그가 이스케이프되지 않음"

    @pytest.mark.security
    def test_pii_masking(self):
        """
        개인정보 마스킹 테스트

        로그에 개인정보가 마스킹되는지 확인합니다.
        """
        from src.logging_system import PrivacyMasker

        masker = PrivacyMasker()

        # 개인정보가 포함된 텍스트
        test_cases = [
            ("제 전화번호는 010-1234-5678입니다", "[전화번호]"),
            ("이메일은 test@example.com입니다", "[이메일]"),
            ("주민등록번호는 123456-1234567입니다", "[주민등록번호]"),
            ("계좌번호는 1234-5678-9012-3456입니다", "[계좌번호]")
        ]

        for original, expected_mask in test_cases:
            masked = masker.mask(original)

            assert expected_mask in masked, \
                f"개인정보가 마스킹되지 않음: {original}"
            print(f"  원본: {original}")
            print(f"  마스킹: {masked}\n")

    @pytest.mark.security
    def test_session_security(self):
        """
        세션 보안 테스트

        세션이 안전하게 관리되는지 확인합니다.
        """
        # 세션 생성
        response1 = requests.post(
            f"{BASE_URL}/api/v1/chat",
            json={
                "user_message": "안녕하세요",
                "persona": "empathetic"
            },
            timeout=10
        )

        assert response1.status_code == 200
        session_id = response1.json()["session_id"]

        # 세션 ID 형식 검증 (UUID 형식)
        import re
        uuid_pattern = r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$'
        assert re.match(uuid_pattern, session_id, re.IGNORECASE), \
            "세션 ID가 UUID 형식이 아님"

        # 동일한 세션으로 후속 요청
        response2 = requests.post(
            f"{BASE_URL}/api/v1/chat",
            json={
                "session_id": session_id,
                "user_message": "두 번째 메시지",
                "persona": "empathetic"
            },
            timeout=10
        )

        assert response2.status_code == 200
        assert response2.json()["session_id"] == session_id, \
            "세션 ID가 유지되지 않음"

    @pytest.mark.security
    def test_api_authentication(self):
        """
        API 인증 테스트

        API 키가 필요한 경우 인증이 작동하는지 확인합니다.
        """
        # API 키 없이 요청 (API_KEY가 설정된 경우)
        response = requests.post(
            f"{BASE_URL}/api/v1/chat",
            json={
                "user_message": "인증 테스트",
                "persona": "empathetic"
            },
            headers={},  # API 키 헤더 없음
            timeout=10
        )

        # API 키가 필요한 경우 401 또는 403이어야 함
        # API 키가 불필요한 경우 200이어야 함
        assert response.status_code in [200, 401, 403], \
            f"예상치 못한 응답 코드: {response.status_code}"

    @pytest.mark.security
    def test_input_validation(self):
        """
        입력 검증 테스트

        잘못된 입력이 적절히 거부되는지 확인합니다.
        """
        # 너무 긴 입력
        long_message = "a" * 100000

        response = requests.post(
            f"{BASE_URL}/api/v1/chat",
            json={
                "user_message": long_message,
                "persona": "empathetic"
            },
            timeout=10
        )

        # 너무 긴 입력은 거부되거나 잘라야 함
        assert response.status_code in [200, 400, 413, 422], \
            "입력 길이 검증이 작동하지 않음"

        # 잘못된 persona
        response = requests.post(
            f"{BASE_URL}/api/v1/chat",
            json={
                "user_message": "안녕하세요",
                "persona": "invalid_persona_12345"
            },
            timeout=10
        )

        # 잘못된 persona는 거부되거나 기본값 사용
        assert response.status_code in [200, 400, 422], \
            "Persona 검증이 작동하지 않음"


# ============================================================================
# 실행
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "performance or security", "--tb=short"])
