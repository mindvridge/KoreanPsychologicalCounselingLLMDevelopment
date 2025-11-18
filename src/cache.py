"""
Redis 캐싱 유틸리티
Redis Caching Utilities for Performance Optimization

성능 향상을 위한 캐싱 전략:
- 세션 데이터 캐싱
- LLM 응답 캐싱 (동일한 질문에 대한 빠른 응답)
- RAG 검색 결과 캐싱
- 사용자 프로필 캐싱
"""

import os
import json
import hashlib
import logging
from typing import Optional, Any, Dict, List
from datetime import timedelta
from functools import wraps

logger = logging.getLogger(__name__)

# Redis 클라이언트 (선택적)
try:
    import redis
    from redis import Redis, ConnectionPool
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis 패키지가 설치되지 않았습니다. 캐싱 기능이 비활성화됩니다.")


class CacheManager:
    """
    Redis 캐시 관리자

    주요 기능:
    - 키-값 캐싱
    - TTL (Time-To-Live) 지원
    - 세션 데이터 관리
    - LLM 응답 캐싱 (cost 절감)
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        default_ttl: int = 3600,
        enabled: bool = True
    ):
        """
        초기화

        Args:
            redis_url: Redis 연결 URL (예: redis://localhost:6379/0)
            default_ttl: 기본 TTL (초)
            enabled: 캐싱 활성화 여부
        """
        self.enabled = enabled and REDIS_AVAILABLE
        self.default_ttl = default_ttl
        self.client: Optional[Redis] = None

        if not self.enabled:
            logger.info("캐싱이 비활성화되었습니다")
            return

        # Redis URL 설정
        if redis_url is None:
            redis_url = os.getenv("REDIS_URL", "")

        if not redis_url:
            logger.warning("REDIS_URL이 설정되지 않았습니다. 캐싱이 비활성화됩니다.")
            self.enabled = False
            return

        try:
            # Connection pool 생성
            pool = ConnectionPool.from_url(
                redis_url,
                max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "50")),
                socket_keepalive=os.getenv("REDIS_SOCKET_KEEPALIVE", "true").lower() == "true",
                socket_timeout=int(os.getenv("REDIS_SOCKET_TIMEOUT", "5")),
                decode_responses=True  # 자동 UTF-8 디코딩
            )

            self.client = Redis(connection_pool=pool)

            # 연결 테스트
            self.client.ping()

            logger.info("✓ Redis 캐시 연결 성공")

        except Exception as e:
            logger.error(f"Redis 연결 실패: {e}")
            logger.warning("캐싱이 비활성화됩니다")
            self.enabled = False

    def is_available(self) -> bool:
        """캐시 사용 가능 여부"""
        return self.enabled and self.client is not None

    def get(self, key: str) -> Optional[Any]:
        """
        캐시에서 값 가져오기

        Args:
            key: 캐시 키

        Returns:
            Optional[Any]: 캐시된 값 (없으면 None)
        """
        if not self.is_available():
            return None

        try:
            value = self.client.get(key)

            if value is None:
                return None

            # JSON 역직렬화 시도
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # JSON이 아닌 경우 문자열 그대로 반환
                return value

        except Exception as e:
            logger.error(f"캐시 조회 실패 ({key}): {e}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        캐시에 값 저장

        Args:
            key: 캐시 키
            value: 저장할 값
            ttl: TTL (초), None이면 기본값 사용

        Returns:
            bool: 성공 여부
        """
        if not self.is_available():
            return False

        try:
            # 값을 JSON으로 직렬화
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, ensure_ascii=False)
            else:
                serialized_value = str(value)

            # TTL 설정
            if ttl is None:
                ttl = self.default_ttl

            # Redis에 저장
            self.client.setex(key, ttl, serialized_value)

            return True

        except Exception as e:
            logger.error(f"캐시 저장 실패 ({key}): {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        캐시에서 값 삭제

        Args:
            key: 캐시 키

        Returns:
            bool: 성공 여부
        """
        if not self.is_available():
            return False

        try:
            self.client.delete(key)
            return True

        except Exception as e:
            logger.error(f"캐시 삭제 실패 ({key}): {e}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """
        패턴과 일치하는 모든 키 삭제

        Args:
            pattern: 키 패턴 (예: "session:*")

        Returns:
            int: 삭제된 키 개수
        """
        if not self.is_available():
            return 0

        try:
            keys = list(self.client.scan_iter(pattern))

            if keys:
                return self.client.delete(*keys)

            return 0

        except Exception as e:
            logger.error(f"패턴 삭제 실패 ({pattern}): {e}")
            return 0

    def hash_key(self, *args: Any) -> str:
        """
        인자들을 해시하여 캐시 키 생성

        Args:
            *args: 해시할 값들

        Returns:
            str: 해시된 키
        """
        # 인자를 문자열로 변환
        key_string = ":".join(str(arg) for arg in args)

        # SHA256 해시
        return hashlib.sha256(key_string.encode()).hexdigest()[:16]


# ============================================================================
# 캐싱 데코레이터
# ============================================================================

def cached(
    cache_manager: CacheManager,
    key_prefix: str,
    ttl: int = 3600,
    key_generator=None
):
    """
    함수 결과를 캐싱하는 데코레이터

    Args:
        cache_manager: CacheManager 인스턴스
        key_prefix: 캐시 키 접두사
        ttl: TTL (초)
        key_generator: 캐시 키 생성 함수 (None이면 기본 해시 사용)

    Example:
        @cached(cache_manager, key_prefix="llm_response", ttl=1800)
        def generate_response(user_message: str) -> str:
            return llm.generate(user_message)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 캐시 사용 불가능한 경우 원래 함수 실행
            if not cache_manager.is_available():
                return func(*args, **kwargs)

            # 캐시 키 생성
            if key_generator:
                cache_key = f"{key_prefix}:{key_generator(*args, **kwargs)}"
            else:
                # 기본: 인자들을 해시
                key_hash = cache_manager.hash_key(*args, *kwargs.values())
                cache_key = f"{key_prefix}:{key_hash}"

            # 캐시 조회
            cached_value = cache_manager.get(cache_key)

            if cached_value is not None:
                logger.debug(f"캐시 히트: {cache_key}")
                return cached_value

            # 캐시 미스 - 원래 함수 실행
            logger.debug(f"캐시 미스: {cache_key}")
            result = func(*args, **kwargs)

            # 결과를 캐시에 저장
            cache_manager.set(cache_key, result, ttl=ttl)

            return result

        return wrapper
    return decorator


# ============================================================================
# 세션 캐시
# ============================================================================

class SessionCache:
    """
    세션 데이터 캐싱

    사용자 세션 정보를 Redis에 캐싱하여 빠른 조회 지원
    """

    def __init__(self, cache_manager: CacheManager):
        """
        초기화

        Args:
            cache_manager: CacheManager 인스턴스
        """
        self.cache = cache_manager
        self.prefix = "session"

    def get_session(self, session_id: str) -> Optional[Dict]:
        """세션 데이터 가져오기"""
        return self.cache.get(f"{self.prefix}:{session_id}")

    def set_session(
        self,
        session_id: str,
        session_data: Dict,
        ttl: int = 7200  # 2시간
    ) -> bool:
        """세션 데이터 저장"""
        return self.cache.set(f"{self.prefix}:{session_id}", session_data, ttl=ttl)

    def delete_session(self, session_id: str) -> bool:
        """세션 삭제"""
        return self.cache.delete(f"{self.prefix}:{session_id}")

    def clear_user_sessions(self, user_id: str) -> int:
        """특정 사용자의 모든 세션 삭제"""
        return self.cache.clear_pattern(f"{self.prefix}:*:{user_id}:*")


# ============================================================================
# LLM 응답 캐시
# ============================================================================

class LLMResponseCache:
    """
    LLM 응답 캐싱

    동일한 질문에 대해 캐시된 응답 반환 (비용 절감)
    """

    def __init__(self, cache_manager: CacheManager):
        """
        초기화

        Args:
            cache_manager: CacheManager 인스턴스
        """
        self.cache = cache_manager
        self.prefix = "llm_response"

    def get_response(
        self,
        user_message: str,
        context: Optional[str] = None
    ) -> Optional[str]:
        """
        캐시된 LLM 응답 가져오기

        Args:
            user_message: 사용자 메시지
            context: 컨텍스트 (선택적)

        Returns:
            Optional[str]: 캐시된 응답 (없으면 None)
        """
        # 캐시 키 생성 (메시지 + 컨텍스트 해시)
        key_components = [user_message]
        if context:
            key_components.append(context)

        key_hash = self.cache.hash_key(*key_components)
        cache_key = f"{self.prefix}:{key_hash}"

        return self.cache.get(cache_key)

    def set_response(
        self,
        user_message: str,
        response: str,
        context: Optional[str] = None,
        ttl: int = 1800  # 30분
    ) -> bool:
        """
        LLM 응답 캐싱

        Args:
            user_message: 사용자 메시지
            response: LLM 응답
            context: 컨텍스트 (선택적)
            ttl: TTL (초)

        Returns:
            bool: 성공 여부
        """
        # 캐시 키 생성
        key_components = [user_message]
        if context:
            key_components.append(context)

        key_hash = self.cache.hash_key(*key_components)
        cache_key = f"{self.prefix}:{key_hash}"

        return self.cache.set(cache_key, response, ttl=ttl)


# ============================================================================
# 싱글톤 인스턴스
# ============================================================================

_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """캐시 매니저 싱글톤"""
    global _cache_manager

    if _cache_manager is None:
        redis_url = os.getenv("REDIS_URL")
        enabled = os.getenv("ENABLE_REDIS_CACHE", "true").lower() == "true"

        _cache_manager = CacheManager(
            redis_url=redis_url,
            enabled=enabled and bool(redis_url)
        )

    return _cache_manager


# ============================================================================
# 사용 예시
# ============================================================================

if __name__ == "__main__":
    # 캐시 매니저 초기화
    cache = get_cache_manager()

    # 값 저장
    cache.set("test_key", {"data": "test"}, ttl=60)

    # 값 조회
    value = cache.get("test_key")
    print(f"캐시된 값: {value}")

    # 세션 캐시
    session_cache = SessionCache(cache)
    session_cache.set_session("session123", {"user_id": "user1", "messages": []})

    # LLM 응답 캐시
    llm_cache = LLMResponseCache(cache)
    llm_cache.set_response("안녕하세요", "안녕하세요! 무엇을 도와드릴까요?")

    # 캐시 조회
    cached_response = llm_cache.get_response("안녕하세요")
    print(f"캐시된 응답: {cached_response}")
