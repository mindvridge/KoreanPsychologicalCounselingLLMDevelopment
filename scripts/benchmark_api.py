#!/usr/bin/env python3
"""
API 성능 벤치마크 스크립트
API Performance Benchmark Script

API 엔드포인트의 응답 시간 및 처리량 측정
"""

import asyncio
import time
import statistics
import requests
import argparse
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed


class APIBenchmark:
    """API 성능 벤치마크"""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: str = None
    ):
        """
        초기화

        Args:
            base_url: API 기본 URL
            api_key: API 인증 키 (선택적)
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {}

        if api_key:
            self.headers["X-API-Key"] = api_key

    def health_check(self) -> Dict[str, Any]:
        """Health check 엔드포인트 테스트"""
        print("Health Check 테스트 중...")

        response_times = []

        for i in range(10):
            start = time.time()
            response = requests.get(f"{self.base_url}/api/v1/health", headers=self.headers)
            elapsed = (time.time() - start) * 1000  # ms

            response_times.append(elapsed)

            if response.status_code != 200:
                print(f"  ❌ 요청 실패: {response.status_code}")

        return {
            "endpoint": "/api/v1/health",
            "requests": len(response_times),
            "mean": statistics.mean(response_times),
            "median": statistics.median(response_times),
            "min": min(response_times),
            "max": max(response_times),
            "stdev": statistics.stdev(response_times) if len(response_times) > 1 else 0
        }

    def chat_benchmark(self, num_requests: int = 10) -> Dict[str, Any]:
        """Chat 엔드포인트 벤치마크"""
        print(f"Chat 엔드포인트 테스트 중 ({num_requests}개 요청)...")

        test_messages = [
            "안녕하세요",
            "요즘 기분이 좋지 않아요",
            "스트레스를 어떻게 관리하나요?",
            "우울한 감정이 계속돼요",
            "불안할 때 어떻게 해야 하나요?"
        ]

        response_times = []
        errors = 0

        for i in range(num_requests):
            message = test_messages[i % len(test_messages)]

            payload = {
                "session_id": f"benchmark_session_{i}",
                "user_message": message,
                "persona": "empathetic"
            }

            try:
                start = time.time()
                response = requests.post(
                    f"{self.base_url}/api/v1/chat",
                    json=payload,
                    headers=self.headers,
                    timeout=60
                )
                elapsed = (time.time() - start) * 1000  # ms

                if response.status_code == 200:
                    response_times.append(elapsed)
                else:
                    errors += 1
                    print(f"  ❌ 요청 {i+1} 실패: {response.status_code}")

            except Exception as e:
                errors += 1
                print(f"  ❌ 요청 {i+1} 오류: {e}")

        if not response_times:
            return {
                "endpoint": "/api/v1/chat",
                "error": "모든 요청 실패"
            }

        return {
            "endpoint": "/api/v1/chat",
            "requests": len(response_times),
            "errors": errors,
            "mean": statistics.mean(response_times),
            "median": statistics.median(response_times),
            "min": min(response_times),
            "max": max(response_times),
            "stdev": statistics.stdev(response_times) if len(response_times) > 1 else 0,
            "throughput": len(response_times) / (sum(response_times) / 1000)  # requests/second
        }

    def concurrent_benchmark(
        self,
        num_requests: int = 50,
        num_workers: int = 10
    ) -> Dict[str, Any]:
        """동시성 테스트 (여러 요청 동시 처리)"""
        print(f"동시성 테스트 중 ({num_requests}개 요청, {num_workers}개 워커)...")

        test_messages = [
            "안녕하세요",
            "오늘 기분이 어떤가요?",
            "스트레스 관리 방법을 알려주세요",
            "불안감을 느낄 때 어떻게 하나요?",
            "우울한 기분이 들어요"
        ]

        def make_request(request_id: int) -> float:
            """단일 요청 실행"""
            message = test_messages[request_id % len(test_messages)]

            payload = {
                "session_id": f"concurrent_session_{request_id}",
                "user_message": message,
                "persona": "empathetic"
            }

            try:
                start = time.time()
                response = requests.post(
                    f"{self.base_url}/api/v1/chat",
                    json=payload,
                    headers=self.headers,
                    timeout=60
                )
                elapsed = (time.time() - start) * 1000  # ms

                if response.status_code == 200:
                    return elapsed
                else:
                    return -1  # 에러

            except Exception:
                return -1  # 에러

        # 동시 요청 실행
        overall_start = time.time()
        response_times = []
        errors = 0

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(make_request, i) for i in range(num_requests)]

            for future in as_completed(futures):
                elapsed = future.result()

                if elapsed > 0:
                    response_times.append(elapsed)
                else:
                    errors += 1

        overall_elapsed = time.time() - overall_start

        if not response_times:
            return {
                "endpoint": "/api/v1/chat (concurrent)",
                "error": "모든 요청 실패"
            }

        return {
            "endpoint": "/api/v1/chat (concurrent)",
            "total_requests": num_requests,
            "successful_requests": len(response_times),
            "errors": errors,
            "workers": num_workers,
            "total_time": overall_elapsed,
            "mean_response_time": statistics.mean(response_times),
            "median_response_time": statistics.median(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "stdev_response_time": statistics.stdev(response_times) if len(response_times) > 1 else 0,
            "throughput": len(response_times) / overall_elapsed  # requests/second
        }

    def assessment_benchmark(self, num_requests: int = 10) -> Dict[str, Any]:
        """Assessment 엔드포인트 벤치마크"""
        print(f"Assessment 엔드포인트 테스트 중 ({num_requests}개 요청)...")

        # PHQ-9 샘플 응답
        phq9_responses = {
            1: 1, 2: 2, 3: 1, 4: 0,
            5: 1, 6: 2, 7: 1, 8: 0, 9: 0
        }

        response_times = []
        errors = 0

        for i in range(num_requests):
            payload = {
                "session_id": f"assessment_session_{i}",
                "assessment_type": "PHQ-9",
                "responses": phq9_responses
            }

            try:
                start = time.time()
                response = requests.post(
                    f"{self.base_url}/api/v1/assessment",
                    json=payload,
                    headers=self.headers,
                    timeout=30
                )
                elapsed = (time.time() - start) * 1000  # ms

                if response.status_code == 200:
                    response_times.append(elapsed)
                else:
                    errors += 1

            except Exception:
                errors += 1

        if not response_times:
            return {
                "endpoint": "/api/v1/assessment",
                "error": "모든 요청 실패"
            }

        return {
            "endpoint": "/api/v1/assessment",
            "requests": len(response_times),
            "errors": errors,
            "mean": statistics.mean(response_times),
            "median": statistics.median(response_times),
            "min": min(response_times),
            "max": max(response_times),
            "stdev": statistics.stdev(response_times) if len(response_times) > 1 else 0
        }

    def print_results(self, results: Dict[str, Any]):
        """결과 출력"""
        print("\n" + "="*70)
        print(f"📊 벤치마크 결과: {results['endpoint']}")
        print("="*70)

        if "error" in results:
            print(f"❌ 오류: {results['error']}")
            return

        # 기본 통계
        if "requests" in results:
            print(f"총 요청: {results['requests']}")

        if "errors" in results and results['errors'] > 0:
            print(f"❌ 실패: {results['errors']}")

        # 응답 시간 통계
        print(f"\n⏱️  응답 시간 (ms):")
        print(f"  평균:   {results.get('mean', 0):.2f}")
        print(f"  중앙값: {results.get('median', 0):.2f}")
        print(f"  최소:   {results.get('min', 0):.2f}")
        print(f"  최대:   {results.get('max', 0):.2f}")
        print(f"  표준편차: {results.get('stdev', 0):.2f}")

        # 처리량
        if "throughput" in results:
            print(f"\n🚀 처리량: {results['throughput']:.2f} requests/second")

        # 동시성 테스트 추가 정보
        if "workers" in results:
            print(f"\n⚙️  동시 워커: {results['workers']}")
            print(f"총 소요 시간: {results.get('total_time', 0):.2f}초")

        print("="*70 + "\n")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="API 성능 벤치마크")

    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="API 기본 URL (기본값: http://localhost:8000)"
    )

    parser.add_argument(
        "--api-key",
        default=None,
        help="API 인증 키"
    )

    parser.add_argument(
        "--chat-requests",
        type=int,
        default=10,
        help="Chat 엔드포인트 요청 수 (기본값: 10)"
    )

    parser.add_argument(
        "--concurrent-requests",
        type=int,
        default=50,
        help="동시성 테스트 요청 수 (기본값: 50)"
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=10,
        help="동시 워커 수 (기본값: 10)"
    )

    parser.add_argument(
        "--skip-health",
        action="store_true",
        help="Health check 테스트 건너뛰기"
    )

    parser.add_argument(
        "--skip-chat",
        action="store_true",
        help="Chat 테스트 건너뛰기"
    )

    parser.add_argument(
        "--skip-concurrent",
        action="store_true",
        help="동시성 테스트 건너뛰기"
    )

    parser.add_argument(
        "--skip-assessment",
        action="store_true",
        help="Assessment 테스트 건너뛰기"
    )

    args = parser.parse_args()

    # 벤치마크 실행
    benchmark = APIBenchmark(base_url=args.url, api_key=args.api_key)

    print("\n" + "="*70)
    print("🚀 API 성능 벤치마크 시작")
    print(f"   URL: {args.url}")
    print("="*70 + "\n")

    # Health Check
    if not args.skip_health:
        results = benchmark.health_check()
        benchmark.print_results(results)

    # Chat Endpoint
    if not args.skip_chat:
        results = benchmark.chat_benchmark(num_requests=args.chat_requests)
        benchmark.print_results(results)

    # Concurrent Test
    if not args.skip_concurrent:
        results = benchmark.concurrent_benchmark(
            num_requests=args.concurrent_requests,
            num_workers=args.workers
        )
        benchmark.print_results(results)

    # Assessment Endpoint
    if not args.skip_assessment:
        results = benchmark.assessment_benchmark()
        benchmark.print_results(results)

    print("✅ 벤치마크 완료!\n")


if __name__ == "__main__":
    main()
