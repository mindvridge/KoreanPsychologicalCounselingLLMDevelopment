"""
Database Models and Connection for Long-Term Memory
장기 기억을 위한 데이터베이스 모델 및 연결

PIPA 준수 프라이버시 우선 설계
"""

import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.pool import StaticPool
import hashlib
import uuid

Base = declarative_base()


# ============================================================================
# Models
# ============================================================================

class User(Base):
    """
    사용자 프로필 (익명화)

    프라이버시 보호:
    - 실제 이름 대신 익명 ID 사용
    - 추출된 정보는 암호화하여 별도 저장
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), unique=True, nullable=False, index=True)  # 익명 해시 ID
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)

    # 프라이버시 보호 설정
    consent_given = Column(Boolean, default=False)  # 데이터 저장 동의
    data_retention_days = Column(Integer, default=90)  # 보관 기간

    # 통계 (개인정보 아님)
    total_conversations = Column(Integer, default=0)
    total_messages = Column(Integer, default=0)
    crisis_count = Column(Integer, default=0)

    # Relationships
    metadata = relationship("UserMetadata", back_populates="user", uselist=False, cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(user_id={self.user_id}, created={self.created_at})>"


class UserMetadata(Base):
    """
    사용자 메타데이터 (추출된 개인정보)

    주의: 민감 정보는 암호화하여 저장
    """
    __tablename__ = "user_metadata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 추출된 정보 (암호화 권장)
    preferred_name = Column(String(100))  # 선호 호칭 (예: "철수님", "손님")
    extracted_name = Column(String(100))  # 추출된 이름 (암호화 필요)
    age_range = Column(String(20))  # 예: "20-29", "30-39"

    # 관심사 및 주제
    main_concerns = Column(JSON)  # ["우울", "불안", "직장 스트레스"]
    conversation_style = Column(String(20), default="formal")  # formal/casual

    # 선호 설정
    preferred_language = Column(String(10), default="ko")
    timezone = Column(String(50), default="Asia/Seoul")

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="metadata")

    def __repr__(self):
        return f"<UserMetadata(user_id={self.user_id}, name={self.preferred_name})>"


class Conversation(Base):
    """
    대화 기록 (영구 저장)

    프라이버시:
    - 민감 정보는 마스킹하여 저장
    - 보관 기간 후 자동 삭제
    """
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(64), nullable=False, index=True)

    # 대화 내용
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)  # PII 마스킹된 내용
    original_content_hash = Column(String(64))  # 원본 해시 (무결성 검증)

    # 메타데이터
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    response_time = Column(Float)  # 응답 시간 (초)

    # 분석 결과
    detected_emotion = Column(String(50))
    crisis_detected = Column(Boolean, default=False)
    crisis_level = Column(Integer, default=0)

    # Relationship
    user = relationship("User", back_populates="conversations")

    def __repr__(self):
        return f"<Conversation(user_id={self.user_id}, role={self.role}, time={self.timestamp})>"


class Assessment(Base):
    """
    심리 평가 결과 (PHQ-9, GAD-7, K-10)

    장기 추적으로 증상 변화 모니터링
    """
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(64), nullable=False)

    # 평가 정보
    assessment_type = Column(String(20), nullable=False)  # phq9, gad7, k10
    responses = Column(JSON, nullable=False)  # 응답 배열
    score = Column(Integer, nullable=False)
    severity = Column(String(50), nullable=False)

    # 해석 및 권장사항
    interpretation = Column(Text)
    recommendations = Column(JSON)

    # 시간 정보
    conducted_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationship
    user = relationship("User", back_populates="assessments")

    def __repr__(self):
        return f"<Assessment(user_id={self.user_id}, type={self.assessment_type}, score={self.score})>"


# ============================================================================
# Database Connection
# ============================================================================

class DatabaseManager:
    """데이터베이스 연결 및 세션 관리"""

    def __init__(self, database_url: Optional[str] = None, echo: bool = False):
        """
        초기화

        Args:
            database_url: 데이터베이스 URL (기본값: SQLite)
            echo: SQL 로그 출력 여부
        """
        if database_url is None:
            # 기본값: SQLite (로컬 파일)
            db_path = os.getenv("DATABASE_PATH", "./data/mental_health.db")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            database_url = f"sqlite:///{db_path}"

        # SQLite의 경우 특별 설정
        if database_url.startswith("sqlite"):
            self.engine = create_engine(
                database_url,
                echo=echo,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool
            )
        else:
            self.engine = create_engine(database_url, echo=echo)

        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # 테이블 생성
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        """새 데이터베이스 세션 생성"""
        return self.SessionLocal()

    def close(self):
        """데이터베이스 연결 종료"""
        self.engine.dispose()


# ============================================================================
# User Management
# ============================================================================

class UserManager:
    """사용자 관리"""

    @staticmethod
    def generate_user_id(identifier: Optional[str] = None) -> str:
        """
        익명 사용자 ID 생성

        Args:
            identifier: 식별자 (이메일, 전화번호 등, 선택사항)

        Returns:
            익명 해시 ID
        """
        if identifier:
            # 식별자가 있으면 일관된 해시 생성
            return hashlib.sha256(identifier.encode()).hexdigest()
        else:
            # 완전 익명: UUID 사용
            return str(uuid.uuid4())

    @staticmethod
    def create_user(db: Session, user_id: Optional[str] = None, consent: bool = True) -> User:
        """
        새 사용자 생성

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID (없으면 자동 생성)
            consent: 데이터 저장 동의

        Returns:
            User 객체
        """
        if user_id is None:
            user_id = UserManager.generate_user_id()

        # 기존 사용자 확인
        existing_user = db.query(User).filter(User.user_id == user_id).first()
        if existing_user:
            return existing_user

        # 새 사용자 생성
        user = User(
            user_id=user_id,
            consent_given=consent,
            created_at=datetime.utcnow(),
            last_active=datetime.utcnow()
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        # 메타데이터 생성
        metadata = UserMetadata(user_id=user.id)
        db.add(metadata)
        db.commit()

        return user

    @staticmethod
    def get_user(db: Session, user_id: str) -> Optional[User]:
        """사용자 조회"""
        return db.query(User).filter(User.user_id == user_id).first()

    @staticmethod
    def update_last_active(db: Session, user_id: str):
        """마지막 활동 시간 업데이트"""
        user = UserManager.get_user(db, user_id)
        if user:
            user.last_active = datetime.utcnow()
            db.commit()

    @staticmethod
    def get_user_stats(db: Session, user_id: str) -> Dict[str, Any]:
        """사용자 통계 조회"""
        user = UserManager.get_user(db, user_id)
        if not user:
            return {}

        return {
            "total_conversations": user.total_conversations,
            "total_messages": user.total_messages,
            "crisis_count": user.crisis_count,
            "member_since": user.created_at.isoformat(),
            "last_active": user.last_active.isoformat()
        }


# ============================================================================
# Conversation Management
# ============================================================================

class ConversationManager:
    """대화 기록 관리"""

    @staticmethod
    def save_conversation(
        db: Session,
        user_id: str,
        session_id: str,
        role: str,
        content: str,
        detected_emotion: Optional[str] = None,
        crisis_detected: bool = False,
        crisis_level: int = 0,
        response_time: Optional[float] = None
    ) -> Conversation:
        """
        대화 저장

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            session_id: 세션 ID
            role: 역할 ('user' or 'assistant')
            content: 내용 (PII 마스킹된)
            detected_emotion: 감지된 감정
            crisis_detected: 위기 감지 여부
            crisis_level: 위기 수준
            response_time: 응답 시간

        Returns:
            Conversation 객체
        """
        user = UserManager.get_user(db, user_id)
        if not user:
            user = UserManager.create_user(db, user_id)

        # 원본 해시 생성
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        conversation = Conversation(
            user_id=user.id,
            session_id=session_id,
            role=role,
            content=content,
            original_content_hash=content_hash,
            detected_emotion=detected_emotion,
            crisis_detected=crisis_detected,
            crisis_level=crisis_level,
            response_time=response_time,
            timestamp=datetime.utcnow()
        )

        db.add(conversation)

        # 사용자 통계 업데이트
        user.total_messages += 1
        if crisis_detected:
            user.crisis_count += 1

        db.commit()
        db.refresh(conversation)

        return conversation

    @staticmethod
    def get_conversation_history(
        db: Session,
        user_id: str,
        session_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        대화 기록 조회

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            session_id: 세션 ID (선택사항)
            limit: 최대 개수

        Returns:
            대화 기록 리스트
        """
        user = UserManager.get_user(db, user_id)
        if not user:
            return []

        query = db.query(Conversation).filter(Conversation.user_id == user.id)

        if session_id:
            query = query.filter(Conversation.session_id == session_id)

        conversations = query.order_by(Conversation.timestamp.desc()).limit(limit).all()

        # 시간순 정렬 (오래된 것부터)
        conversations.reverse()

        return [
            {
                "role": conv.role,
                "content": conv.content,
                "timestamp": conv.timestamp.isoformat(),
                "detected_emotion": conv.detected_emotion,
                "crisis_detected": conv.crisis_detected
            }
            for conv in conversations
        ]

    @staticmethod
    def get_recent_sessions(db: Session, user_id: str, limit: int = 10) -> List[str]:
        """최근 세션 ID 목록"""
        user = UserManager.get_user(db, user_id)
        if not user:
            return []

        sessions = db.query(Conversation.session_id).filter(
            Conversation.user_id == user.id
        ).distinct().order_by(Conversation.timestamp.desc()).limit(limit).all()

        return [session[0] for session in sessions]


# ============================================================================
# Assessment Management
# ============================================================================

class AssessmentManager:
    """평가 결과 관리"""

    @staticmethod
    def save_assessment(
        db: Session,
        user_id: str,
        session_id: str,
        assessment_type: str,
        responses: List[int],
        score: int,
        severity: str,
        interpretation: str,
        recommendations: List[str]
    ) -> Assessment:
        """평가 결과 저장"""
        user = UserManager.get_user(db, user_id)
        if not user:
            user = UserManager.create_user(db, user_id)

        assessment = Assessment(
            user_id=user.id,
            session_id=session_id,
            assessment_type=assessment_type,
            responses=responses,
            score=score,
            severity=severity,
            interpretation=interpretation,
            recommendations=recommendations,
            conducted_at=datetime.utcnow()
        )

        db.add(assessment)
        db.commit()
        db.refresh(assessment)

        return assessment

    @staticmethod
    def get_assessment_history(
        db: Session,
        user_id: str,
        assessment_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """평가 이력 조회"""
        user = UserManager.get_user(db, user_id)
        if not user:
            return []

        query = db.query(Assessment).filter(Assessment.user_id == user.id)

        if assessment_type:
            query = query.filter(Assessment.assessment_type == assessment_type)

        assessments = query.order_by(Assessment.conducted_at.desc()).limit(limit).all()

        return [
            {
                "type": assess.assessment_type,
                "score": assess.score,
                "severity": assess.severity,
                "date": assess.conducted_at.isoformat()
            }
            for assess in assessments
        ]

    @staticmethod
    def get_trend_data(db: Session, user_id: str, assessment_type: str) -> Dict[str, Any]:
        """증상 변화 추이"""
        assessments = AssessmentManager.get_assessment_history(
            db, user_id, assessment_type, limit=20
        )

        if not assessments:
            return {"trend": "no_data", "assessments": []}

        # 점수 추이 분석
        scores = [a["score"] for a in assessments]

        if len(scores) >= 2:
            recent = scores[:3]
            older = scores[-3:]

            recent_avg = sum(recent) / len(recent)
            older_avg = sum(older) / len(older)

            if recent_avg < older_avg - 3:
                trend = "improving"
            elif recent_avg > older_avg + 3:
                trend = "worsening"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        return {
            "trend": trend,
            "assessments": assessments,
            "latest_score": assessments[0]["score"] if assessments else None
        }


# ============================================================================
# Data Cleanup
# ============================================================================

def cleanup_old_data(db: Session, retention_days: int = 90):
    """오래된 데이터 삭제 (PIPA 준수)"""
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

    # 오래된 대화 삭제
    deleted_conversations = db.query(Conversation).filter(
        Conversation.timestamp < cutoff_date
    ).delete()

    # 동의 철회한 사용자 데이터 삭제
    users_to_delete = db.query(User).filter(
        User.consent_given == False,
        User.last_active < cutoff_date
    ).all()

    for user in users_to_delete:
        db.delete(user)

    db.commit()

    return {
        "deleted_conversations": deleted_conversations,
        "deleted_users": len(users_to_delete)
    }


# ============================================================================
# Initialization
# ============================================================================

# 전역 데이터베이스 매니저 (싱글톤)
_db_manager: Optional[DatabaseManager] = None

def get_db_manager() -> DatabaseManager:
    """데이터베이스 매니저 싱글톤"""
    global _db_manager
    if _db_manager is None:
        database_url = os.getenv("DATABASE_URL")
        _db_manager = DatabaseManager(database_url)
    return _db_manager

def get_db() -> Session:
    """데이터베이스 세션 가져오기"""
    db_manager = get_db_manager()
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()
