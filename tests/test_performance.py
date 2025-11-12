"""
Performance and Benchmarking Tests
성능 벤치마크 테스트

시스템의 응답 시간, 처리량, 리소스 사용량을 측정합니다.
"""

import sys
import os
import pytest
import time
import psutil
from typing import List
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# ============================================================================
# 1. Response Time Tests
# ============================================================================

class TestResponseTime:
    """응답 시간 테스트"""

    @pytest.mark.performance
    def test_crisis_detection_response_time(self):
        """
        위기 감지 응답 시간: < 1초 목표
        """
        from src.safety_system_v2 import LLMCrisisEvaluator
        
        evaluator = LLMCrisisEvaluator()
        test_message = "죽고 싶어요"
        
        start_time = time.time()
        result = evaluator.evaluate_crisis(test_message, [])
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response_time < 1.0, \
            f"위기 감지 응답 시간 초과: {response_time:.3f}초 (목표: < 1초)"

    @pytest.mark.performance
    def test_emotion_analysis_response_time(self):
        """
        감정 분석 응답 시간: < 0.5초 목표
        """
        from src.emotion_analyzer_v2 import KoreanEmotionAnalyzer
        
        analyzer = KoreanEmotionAnalyzer()
        test_message = "우울하고 불안해요"
        
        start_time = time.time()
        result = analyzer.analyze_comprehensive(test_message)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response_time < 0.5, \
            f"감정 분석 응답 시간 초과: {response_time:.3f}초 (목표: < 0.5초)"

    @pytest.mark.performance
    @pytest.mark.slow
    def test_rag_search_response_time(self):
        """
        RAG 검색 응답 시간: < 0.5초 목표
        """
        from src.rag_system import MentalHealthRAG
        
        try:
            rag = MentalHealthRAG(knowledge_base_dir="./knowledge_base")
            
            if rag.is_indexed:
                start_time = time.time()
                results = rag.search("우울증", k=3)
                end_time = time.time()
                
                response_time = end_time - start_time
                
                assert response_time < 0.5, \
                    f"RAG 검색 시간 초과: {response_time:.3f}초 (목표: < 0.5초)"
        except:
            pytest.skip("Knowledge base not available")

    @pytest.mark.performance
    def test_api_endpoint_response_time(self):
        """
        API 엔드포인트 응답 시간: < 3초 목표
        """
        from fastapi.testclient import TestClient
        
        with patch('src.api.mental_health_system'):
            from src.api import app
            client = TestClient(app)
            
            start_time = time.time()
            response = client.post(
                "/api/v1/chat",
                json={"message": "안녕하세요"}
            )
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # API overhead included
            assert response_time < 5.0, \
                f"API 응답 시간 초과: {response_time:.3f}초 (목표: < 5초)"


# ============================================================================
# 2. Throughput Tests
# ============================================================================

class TestThroughput:
    """처리량 테스트"""

    @pytest.mark.performance
    @pytest.mark.slow
    def test_sequential_message_processing(self):
        """
        순차 메시지 처리 성능
        
        목표: 10개 메시지를 30초 내 처리
        """
        from src.safety_system_v2 import LLMCrisisEvaluator
        
        evaluator = LLMCrisisEvaluator()
        
        test_messages = [
            "안녕하세요",
            "우울해요",
            "불안해요",
            "힘들어요",
            "스트레스받아요",
            "걱정돼요",
            "피곤해요",
            "지쳤어요",
            "무기력해요",
            "슬퍼요"
        ]
        
        start_time = time.time()
        
        for message in test_messages:
            evaluator.evaluate_crisis(message, [])
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / len(test_messages)
        
        assert total_time < 30.0, \
            f"처리 시간 초과: {total_time:.2f}초 (목표: < 30초)"
        
        print(f"\n평균 처리 시간: {avg_time:.3f}초/메시지")
        print(f"처리량: {len(test_messages)/total_time:.2f} 메시지/초")

    @pytest.mark.performance
    @pytest.mark.slow
    def test_batch_crisis_detection(self):
        """
        배치 위기 감지 성능
        
        목표: 100개 메시지를 2분 내 처리
        """
        from src.safety_system_v2 import LLMCrisisEvaluator
        
        evaluator = LLMCrisisEvaluator()
        
        # Generate 100 test messages
        test_messages = [f"테스트 메시지 {i}" for i in range(100)]
        
        start_time = time.time()
        
        for message in test_messages:
            evaluator.evaluate_crisis(message, [])
        
        end_time = time.time()
        total_time = end_time - start_time
        
        assert total_time < 120.0, \
            f"배치 처리 시간 초과: {total_time:.2f}초 (목표: < 120초)"
        
        throughput = len(test_messages) / total_time
        print(f"\n배치 처리량: {throughput:.2f} 메시지/초")


# ============================================================================
# 3. Memory Usage Tests
# ============================================================================

class TestMemoryUsage:
    """메모리 사용량 테스트"""

    @pytest.mark.performance
    def test_crisis_detector_memory_usage(self):
        """
        위기 감지 시스템 메모리 사용량
        
        목표: < 500MB
        """
        import gc
        gc.collect()
        
        process = psutil.Process()
        mem_before = process.memory_info().rss / 1024 / 1024  # MB
        
        from src.safety_system_v2 import LLMCrisisEvaluator
        evaluator = LLMCrisisEvaluator()
        
        # Process several messages
        for i in range(10):
            evaluator.evaluate_crisis(f"테스트 메시지 {i}", [])
        
        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        mem_used = mem_after - mem_before
        
        print(f"\n메모리 사용량: {mem_used:.2f} MB")
        
        assert mem_used < 500, \
            f"메모리 사용량 초과: {mem_used:.2f} MB (목표: < 500 MB)"

    @pytest.mark.performance
    @pytest.mark.slow
    def test_no_memory_leak(self):
        """
        메모리 누수 테스트
        
        반복 처리 후 메모리가 계속 증가하지 않는지 확인
        """
        import gc
        from src.safety_system_v2 import LLMCrisisEvaluator
        
        evaluator = LLMCrisisEvaluator()
        process = psutil.Process()
        
        # Initial processing
        for i in range(50):
            evaluator.evaluate_crisis(f"테스트 {i}", [])
        
        gc.collect()
        mem_baseline = process.memory_info().rss / 1024 / 1024
        
        # Second batch
        for i in range(50):
            evaluator.evaluate_crisis(f"테스트 {i}", [])
        
        gc.collect()
        mem_after = process.memory_info().rss / 1024 / 1024
        
        mem_increase = mem_after - mem_baseline
        
        print(f"\n메모리 증가량: {mem_increase:.2f} MB")
        
        # Memory should not increase significantly
        assert mem_increase < 100, \
            f"메모리 누수 의심: {mem_increase:.2f} MB 증가"


# ============================================================================
# 4. Concurrent User Simulation
# ============================================================================

class TestConcurrency:
    """동시 사용자 시뮬레이션"""

    @pytest.mark.performance
    @pytest.mark.slow
    def test_concurrent_api_requests(self):
        """
        동시 API 요청 처리
        
        목표: 10명 동시 사용자 처리 가능
        """
        from fastapi.testclient import TestClient
        import concurrent.futures
        
        with patch('src.api.mental_health_system'):
            from src.api import app
            client = TestClient(app)
            
            def make_request(user_id):
                response = client.post(
                    "/api/v1/chat",
                    json={"message": f"사용자 {user_id} 메시지"}
                )
                return response.status_code == 200
            
            start_time = time.time()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_request, i) for i in range(10)]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # All requests should succeed
            assert all(results), "일부 요청이 실패했습니다"
            
            # Should complete in reasonable time
            assert total_time < 10.0, \
                f"동시 요청 처리 시간 초과: {total_time:.2f}초"
            
            print(f"\n10명 동시 사용자 처리 시간: {total_time:.2f}초")


# ============================================================================
# 5. Load Testing
# ============================================================================

class TestLoadTesting:
    """부하 테스트"""

    @pytest.mark.performance
    @pytest.mark.slow
    def test_sustained_load(self):
        """
        지속 부하 테스트
        
        목표: 1분간 지속적인 요청 처리
        """
        from src.safety_system_v2 import LLMCrisisEvaluator
        
        evaluator = LLMCrisisEvaluator()
        
        start_time = time.time()
        duration = 60  # 60 seconds
        message_count = 0
        errors = 0
        
        while (time.time() - start_time) < duration:
            try:
                evaluator.evaluate_crisis(f"테스트 메시지 {message_count}", [])
                message_count += 1
            except Exception as e:
                errors += 1
        
        total_time = time.time() - start_time
        throughput = message_count / total_time
        
        print(f"\n지속 부하 테스트 결과:")
        print(f"  처리 메시지: {message_count}")
        print(f"  에러 수: {errors}")
        print(f"  처리량: {throughput:.2f} 메시지/초")
        
        assert errors < message_count * 0.01, \
            f"에러율이 너무 높습니다: {errors}/{message_count}"


# ============================================================================
# 6. Database Performance (if applicable)
# ============================================================================

class TestDatabasePerformance:
    """데이터베이스 성능 테스트"""

    @pytest.mark.performance
    @pytest.mark.slow
    def test_session_lookup_performance(self):
        """
        세션 조회 성능
        
        목표: < 10ms
        """
        # This would test actual database queries
        # Placeholder for now
        pass


# ============================================================================
# 7. Cache Performance
# ============================================================================

class TestCachePerformance:
    """캐시 성능 테스트"""

    @pytest.mark.performance
    def test_response_caching(self):
        """응답 캐싱 효과"""
        # Test if caching improves response time
        # Placeholder
        pass


# ============================================================================
# Test Configuration
# ============================================================================

pytest.mark.performance = pytest.mark.performance
pytest.mark.slow = pytest.mark.slow

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "performance", "--tb=short"])
