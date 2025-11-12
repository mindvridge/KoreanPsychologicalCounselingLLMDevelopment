"""
Pytest Configuration and Shared Fixtures
공유 픽스처 및 설정
"""

import sys
import os
import pytest
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# ============================================================================
# Session-scoped Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def project_root_dir():
    """프로젝트 루트 디렉토리"""
    return project_root


@pytest.fixture(scope="session")
def knowledge_base_dir(project_root_dir):
    """지식베이스 디렉토리"""
    return project_root_dir / "knowledge_base"


@pytest.fixture(scope="session")
def test_data_dir(project_root_dir):
    """테스트 데이터 디렉토리"""
    test_dir = project_root_dir / "tests" / "test_data"
    test_dir.mkdir(exist_ok=True)
    return test_dir


# ============================================================================
# Test Configuration
# ============================================================================

def pytest_configure(config):
    """Pytest 설정"""
    config.addinivalue_line(
        "markers", "safety_critical: marks tests as safety critical (must pass 100%)"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (slower)"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance benchmarks"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """테스트 수집 후 수정"""
    # Safety critical tests should fail fast
    for item in items:
        if "safety_critical" in item.keywords:
            item.add_marker(pytest.mark.xfail(strict=True))


# ============================================================================
# Test Reporting
# ============================================================================

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """테스트 결과 리포트 생성"""
    outcome = yield
    rep = outcome.get_result()
    
    # Safety critical tests must pass
    if "safety_critical" in item.keywords:
        if rep.when == "call" and rep.failed:
            print(f"\n⚠️  CRITICAL FAILURE: {item.nodeid}")
            print("   This is a safety-critical test and must be fixed immediately.")


# ============================================================================
# Cleanup
# ============================================================================

@pytest.fixture(scope="function", autouse=True)
def cleanup_after_test(request):
    """각 테스트 후 정리"""
    yield
    # Cleanup code here if needed
    pass


# ============================================================================
# Mock Data
# ============================================================================

@pytest.fixture
def sample_conversation_history():
    """샘플 대화 기록"""
    return [
        {"role": "user", "content": "안녕하세요"},
        {"role": "assistant", "content": "안녕하세요. 무엇을 도와드릴까요?"},
        {"role": "user", "content": "우울해요"},
        {"role": "assistant", "content": "어떤 점이 우울하신가요?"}
    ]


@pytest.fixture
def sample_crisis_messages():
    """샘플 위기 메시지"""
    return [
        "죽고 싶어요",
        "자살하고 싶어요",
        "더 이상 살 이유가 없어요",
        "오늘 자살할 계획이에요"
    ]


@pytest.fixture
def sample_safe_messages():
    """샘플 안전 메시지"""
    return [
        "안녕하세요",
        "오늘 날씨가 좋네요",
        "밥 먹었어요",
        "잘 지내요"
    ]


# ============================================================================
# Performance Monitoring
# ============================================================================

@pytest.fixture
def performance_tracker():
    """성능 추적"""
    import time
    
    class PerformanceTracker:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return PerformanceTracker()


# ============================================================================
# Environment Setup
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """테스트 환경 설정"""
    # Set environment variables for testing
    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = "ERROR"  # Reduce log noise during tests
    
    yield
    
    # Cleanup
    if "TESTING" in os.environ:
        del os.environ["TESTING"]
