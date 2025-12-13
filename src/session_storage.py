"""
세션 저장소 (Session Storage)

SQLite 기반 세션 영속성 관리:
1. 세션 생성/조회/업데이트/삭제
2. 대화 이력 저장 및 복원
3. 자동 만료 처리
4. 암호화 옵션 지원
"""

import os
import json
import sqlite3
import logging
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
from contextlib import contextmanager
import threading

logger = logging.getLogger(__name__)


# =============================================================================
# 데이터 클래스
# =============================================================================

@dataclass
class SessionData:
    """세션 데이터"""
    session_id: str
    user_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    conversation_history: List[Dict[str, Any]]
    metadata: Dict[str, Any]

    # 상태 정보
    turn_count: int = 0
    total_tokens: int = 0
    crisis_events: int = 0
    emotion_summary: Dict[str, int] = None

    def __post_init__(self):
        if self.emotion_summary is None:
            self.emotion_summary = {}

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "conversation_history": self.conversation_history,
            "metadata": self.metadata,
            "turn_count": self.turn_count,
            "total_tokens": self.total_tokens,
            "crisis_events": self.crisis_events,
            "emotion_summary": self.emotion_summary
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionData":
        """딕셔너리에서 생성"""
        return cls(
            session_id=data["session_id"],
            user_id=data.get("user_id"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            conversation_history=data.get("conversation_history", []),
            metadata=data.get("metadata", {}),
            turn_count=data.get("turn_count", 0),
            total_tokens=data.get("total_tokens", 0),
            crisis_events=data.get("crisis_events", 0),
            emotion_summary=data.get("emotion_summary", {})
        )


# =============================================================================
# SQLite 세션 저장소
# =============================================================================

class SQLiteSessionStorage:
    """
    SQLite 기반 세션 저장소

    Thread-safe하게 세션 데이터를 저장/조회/관리합니다.
    """

    def __init__(
        self,
        db_path: str = "./data/sessions.db",
        session_ttl_hours: int = 24,
        max_sessions_per_user: int = 5,
        enable_encryption: bool = False,
        encryption_key: Optional[str] = None
    ):
        """
        초기화

        Args:
            db_path: SQLite 데이터베이스 경로
            session_ttl_hours: 세션 유효 시간 (시간)
            max_sessions_per_user: 사용자당 최대 세션 수
            enable_encryption: 암호화 활성화
            encryption_key: 암호화 키
        """
        self.db_path = Path(db_path)
        self.session_ttl = timedelta(hours=session_ttl_hours)
        self.max_sessions_per_user = max_sessions_per_user
        self.enable_encryption = enable_encryption
        self.encryption_key = encryption_key

        # 스레드별 연결 관리
        self._local = threading.local()

        # 디렉토리 생성
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 테이블 초기화
        self._init_database()

        logger.info(f"SQLiteSessionStorage initialized: {self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """스레드별 DB 연결 반환"""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False
            )
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection

    @contextmanager
    def _get_cursor(self):
        """커서 컨텍스트 매니저"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()

    def _init_database(self):
        """데이터베이스 테이블 초기화"""
        with self._get_cursor() as cursor:
            # 세션 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    conversation_history TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    turn_count INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    crisis_events INTEGER DEFAULT 0,
                    emotion_summary TEXT DEFAULT '{}'
                )
            """)

            # 인덱스 생성
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_user_id
                ON sessions(user_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_expires_at
                ON sessions(expires_at)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_updated_at
                ON sessions(updated_at)
            """)

    def _encrypt(self, data: str) -> str:
        """데이터 암호화 (간단한 XOR 기반)"""
        if not self.enable_encryption or not self.encryption_key:
            return data

        key = hashlib.sha256(self.encryption_key.encode()).digest()
        encrypted = []
        for i, char in enumerate(data):
            encrypted.append(chr(ord(char) ^ key[i % len(key)]))
        return ''.join(encrypted)

    def _decrypt(self, data: str) -> str:
        """데이터 복호화"""
        # XOR은 대칭이므로 동일한 함수 사용
        return self._encrypt(data)

    # =========================================================================
    # CRUD 작업
    # =========================================================================

    def create_session(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SessionData:
        """
        새 세션 생성

        Args:
            session_id: 세션 ID
            user_id: 사용자 ID (선택)
            metadata: 추가 메타데이터

        Returns:
            SessionData: 생성된 세션 데이터
        """
        now = datetime.now()
        session = SessionData(
            session_id=session_id,
            user_id=user_id,
            created_at=now,
            updated_at=now,
            expires_at=now + self.session_ttl,
            conversation_history=[],
            metadata=metadata or {}
        )

        # 사용자당 세션 수 제한 확인
        if user_id:
            self._enforce_session_limit(user_id)

        with self._get_cursor() as cursor:
            cursor.execute("""
                INSERT OR REPLACE INTO sessions
                (session_id, user_id, created_at, updated_at, expires_at,
                 conversation_history, metadata, turn_count, total_tokens,
                 crisis_events, emotion_summary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session.session_id,
                session.user_id,
                session.created_at.isoformat(),
                session.updated_at.isoformat(),
                session.expires_at.isoformat(),
                self._encrypt(json.dumps(session.conversation_history, ensure_ascii=False)),
                json.dumps(session.metadata, ensure_ascii=False),
                session.turn_count,
                session.total_tokens,
                session.crisis_events,
                json.dumps(session.emotion_summary, ensure_ascii=False)
            ))

        logger.info(f"Session created: {session_id}")
        return session

    def get_session(self, session_id: str) -> Optional[SessionData]:
        """
        세션 조회

        Args:
            session_id: 세션 ID

        Returns:
            SessionData or None: 세션 데이터
        """
        with self._get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM sessions WHERE session_id = ?
            """, (session_id,))
            row = cursor.fetchone()

        if not row:
            return None

        # 만료 확인
        expires_at = datetime.fromisoformat(row["expires_at"])
        if datetime.now() > expires_at:
            self.delete_session(session_id)
            return None

        # 대화 이력 복호화
        conversation_history = json.loads(
            self._decrypt(row["conversation_history"])
        )

        return SessionData(
            session_id=row["session_id"],
            user_id=row["user_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            expires_at=expires_at,
            conversation_history=conversation_history,
            metadata=json.loads(row["metadata"]),
            turn_count=row["turn_count"],
            total_tokens=row["total_tokens"],
            crisis_events=row["crisis_events"],
            emotion_summary=json.loads(row["emotion_summary"])
        )

    def update_session(
        self,
        session_id: str,
        conversation_history: Optional[List[Dict]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        increment_turn: bool = False,
        add_tokens: int = 0,
        crisis_detected: bool = False,
        emotion: Optional[str] = None
    ) -> Optional[SessionData]:
        """
        세션 업데이트

        Args:
            session_id: 세션 ID
            conversation_history: 새 대화 이력 (전체 교체)
            metadata: 업데이트할 메타데이터
            increment_turn: 턴 카운트 증가
            add_tokens: 추가할 토큰 수
            crisis_detected: 위기 감지 여부
            emotion: 감지된 감정

        Returns:
            SessionData or None: 업데이트된 세션 데이터
        """
        session = self.get_session(session_id)
        if not session:
            return None

        # 업데이트
        session.updated_at = datetime.now()
        session.expires_at = session.updated_at + self.session_ttl

        if conversation_history is not None:
            session.conversation_history = conversation_history

        if metadata:
            session.metadata.update(metadata)

        if increment_turn:
            session.turn_count += 1

        if add_tokens > 0:
            session.total_tokens += add_tokens

        if crisis_detected:
            session.crisis_events += 1

        if emotion:
            session.emotion_summary[emotion] = session.emotion_summary.get(emotion, 0) + 1

        # DB 저장
        with self._get_cursor() as cursor:
            cursor.execute("""
                UPDATE sessions SET
                    updated_at = ?,
                    expires_at = ?,
                    conversation_history = ?,
                    metadata = ?,
                    turn_count = ?,
                    total_tokens = ?,
                    crisis_events = ?,
                    emotion_summary = ?
                WHERE session_id = ?
            """, (
                session.updated_at.isoformat(),
                session.expires_at.isoformat(),
                self._encrypt(json.dumps(session.conversation_history, ensure_ascii=False)),
                json.dumps(session.metadata, ensure_ascii=False),
                session.turn_count,
                session.total_tokens,
                session.crisis_events,
                json.dumps(session.emotion_summary, ensure_ascii=False),
                session_id
            ))

        return session

    def delete_session(self, session_id: str) -> bool:
        """
        세션 삭제

        Args:
            session_id: 세션 ID

        Returns:
            bool: 삭제 성공 여부
        """
        with self._get_cursor() as cursor:
            cursor.execute("""
                DELETE FROM sessions WHERE session_id = ?
            """, (session_id,))
            deleted = cursor.rowcount > 0

        if deleted:
            logger.info(f"Session deleted: {session_id}")

        return deleted

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[SessionData]:
        """
        세션에 메시지 추가

        Args:
            session_id: 세션 ID
            role: 역할 (user/assistant)
            content: 메시지 내용
            metadata: 메시지 메타데이터

        Returns:
            SessionData or None: 업데이트된 세션 데이터
        """
        session = self.get_session(session_id)
        if not session:
            return None

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        if metadata:
            message["metadata"] = metadata

        session.conversation_history.append(message)

        return self.update_session(
            session_id,
            conversation_history=session.conversation_history,
            increment_turn=(role == "assistant"),
            add_tokens=len(content.split())
        )

    # =========================================================================
    # 조회 및 관리
    # =========================================================================

    def get_user_sessions(self, user_id: str) -> List[SessionData]:
        """사용자의 모든 세션 조회"""
        with self._get_cursor() as cursor:
            cursor.execute("""
                SELECT session_id FROM sessions
                WHERE user_id = ?
                ORDER BY updated_at DESC
            """, (user_id,))
            rows = cursor.fetchall()

        sessions = []
        for row in rows:
            session = self.get_session(row["session_id"])
            if session:
                sessions.append(session)

        return sessions

    def _enforce_session_limit(self, user_id: str):
        """사용자당 세션 수 제한 적용"""
        sessions = self.get_user_sessions(user_id)

        if len(sessions) >= self.max_sessions_per_user:
            # 가장 오래된 세션들 삭제
            sessions_to_delete = sessions[self.max_sessions_per_user - 1:]
            for session in sessions_to_delete:
                self.delete_session(session.session_id)
                logger.info(f"Old session removed for user {user_id}: {session.session_id}")

    def cleanup_expired_sessions(self) -> int:
        """만료된 세션 정리"""
        now = datetime.now().isoformat()

        with self._get_cursor() as cursor:
            cursor.execute("""
                DELETE FROM sessions WHERE expires_at < ?
            """, (now,))
            deleted_count = cursor.rowcount

        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} expired sessions")

        return deleted_count

    def get_session_stats(self) -> Dict[str, Any]:
        """세션 통계 조회"""
        with self._get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    COUNT(*) as total_sessions,
                    COUNT(DISTINCT user_id) as unique_users,
                    SUM(turn_count) as total_turns,
                    SUM(total_tokens) as total_tokens,
                    SUM(crisis_events) as total_crisis_events,
                    AVG(turn_count) as avg_turns_per_session
                FROM sessions
                WHERE expires_at > ?
            """, (datetime.now().isoformat(),))
            row = cursor.fetchone()

        return {
            "total_active_sessions": row["total_sessions"] or 0,
            "unique_users": row["unique_users"] or 0,
            "total_turns": row["total_turns"] or 0,
            "total_tokens": row["total_tokens"] or 0,
            "total_crisis_events": row["total_crisis_events"] or 0,
            "avg_turns_per_session": round(row["avg_turns_per_session"] or 0, 2)
        }

    def close(self):
        """연결 종료"""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None


# =============================================================================
# 메모리 세션 저장소 (개발/테스트용)
# =============================================================================

class InMemorySessionStorage:
    """인메모리 세션 저장소 (개발/테스트용)"""

    def __init__(self, session_ttl_hours: int = 24):
        self.sessions: Dict[str, SessionData] = {}
        self.session_ttl = timedelta(hours=session_ttl_hours)
        self._lock = threading.Lock()

    def create_session(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SessionData:
        now = datetime.now()
        session = SessionData(
            session_id=session_id,
            user_id=user_id,
            created_at=now,
            updated_at=now,
            expires_at=now + self.session_ttl,
            conversation_history=[],
            metadata=metadata or {}
        )
        with self._lock:
            self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[SessionData]:
        with self._lock:
            session = self.sessions.get(session_id)
            if session and datetime.now() > session.expires_at:
                del self.sessions[session_id]
                return None
            return session

    def update_session(
        self,
        session_id: str,
        conversation_history: Optional[List[Dict]] = None,
        **kwargs
    ) -> Optional[SessionData]:
        session = self.get_session(session_id)
        if not session:
            return None

        session.updated_at = datetime.now()
        session.expires_at = session.updated_at + self.session_ttl

        if conversation_history is not None:
            session.conversation_history = conversation_history

        return session

    def delete_session(self, session_id: str) -> bool:
        with self._lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                return True
            return False

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[SessionData]:
        session = self.get_session(session_id)
        if not session:
            return None

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        if metadata:
            message["metadata"] = metadata

        session.conversation_history.append(message)
        session.updated_at = datetime.now()

        if role == "assistant":
            session.turn_count += 1

        return session

    def cleanup_expired_sessions(self) -> int:
        now = datetime.now()
        with self._lock:
            expired = [
                sid for sid, session in self.sessions.items()
                if now > session.expires_at
            ]
            for sid in expired:
                del self.sessions[sid]
            return len(expired)


# =============================================================================
# 호환성 Alias
# =============================================================================

# 일관된 네이밍을 위한 alias
SessionStorage = SQLiteSessionStorage


# =============================================================================
# 팩토리 및 편의 함수
# =============================================================================

_default_storage: Optional[SQLiteSessionStorage] = None


def get_session_storage(
    storage_type: str = "sqlite",
    **kwargs
) -> SQLiteSessionStorage:
    """
    세션 저장소 인스턴스 반환

    Args:
        storage_type: 저장소 유형 ("sqlite" 또는 "memory")
        **kwargs: 저장소 초기화 인자

    Returns:
        세션 저장소 인스턴스
    """
    global _default_storage

    if storage_type == "memory":
        return InMemorySessionStorage(**kwargs)

    if _default_storage is None:
        _default_storage = SQLiteSessionStorage(**kwargs)

    return _default_storage


def init_session_storage(
    db_path: str = "./data/sessions.db",
    session_ttl_hours: int = 24,
    max_sessions_per_user: int = 5,
    enable_encryption: bool = False,
    encryption_key: Optional[str] = None
) -> SQLiteSessionStorage:
    """
    세션 저장소 초기화

    Args:
        db_path: SQLite 데이터베이스 경로
        session_ttl_hours: 세션 유효 시간
        max_sessions_per_user: 사용자당 최대 세션 수
        enable_encryption: 암호화 활성화
        encryption_key: 암호화 키

    Returns:
        SQLiteSessionStorage: 초기화된 저장소
    """
    global _default_storage

    _default_storage = SQLiteSessionStorage(
        db_path=db_path,
        session_ttl_hours=session_ttl_hours,
        max_sessions_per_user=max_sessions_per_user,
        enable_encryption=enable_encryption,
        encryption_key=encryption_key
    )

    return _default_storage


if __name__ == "__main__":
    # 테스트
    logging.basicConfig(level=logging.INFO)

    storage = init_session_storage(db_path="./test_sessions.db")

    # 세션 생성
    session = storage.create_session(
        session_id="test_session_001",
        user_id="user_123",
        metadata={"source": "test"}
    )
    print(f"Created session: {session.session_id}")

    # 메시지 추가
    storage.add_message(
        session_id="test_session_001",
        role="user",
        content="안녕하세요, 요즘 기분이 우울해요."
    )
    storage.add_message(
        session_id="test_session_001",
        role="assistant",
        content="안녕하세요. 기분이 우울하시군요. 조금 더 이야기해 주실 수 있을까요?"
    )

    # 세션 조회
    session = storage.get_session("test_session_001")
    print(f"Session history: {len(session.conversation_history)} messages")
    print(f"Turn count: {session.turn_count}")

    # 통계
    stats = storage.get_session_stats()
    print(f"Stats: {stats}")

    # 정리
    storage.close()
    os.remove("./test_sessions.db")
    print("Test completed successfully!")
