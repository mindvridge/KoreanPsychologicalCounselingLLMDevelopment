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
from sqlalchemy.pool import StaticPool, QueuePool, NullPool
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


class PersonaFeedback(Base):
    """
    페르소나 피드백 (사용자 만족도)

    추천 품질 개선을 위한 사용자 피드백 수집
    """
    __tablename__ = "persona_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(64), nullable=False, index=True)

    # 페르소나 정보
    persona_id = Column(String(50), nullable=False, index=True)

    # 피드백 정보
    rating = Column(Integer, nullable=False)  # 1-5 점
    helpful = Column(Boolean, default=True)  # 도움이 되었는가
    appropriate = Column(Boolean, default=True)  # 적절한 추천이었는가
    would_recommend_again = Column(Boolean, default=True)  # 다시 추천받고 싶은가

    # 상세 피드백
    concerns_addressed = Column(JSON)  # 해결된 고민 리스트
    feedback_text = Column(Text)  # 자유 형식 피드백
    user_age_range = Column(String(20))  # 사용자 나이대

    # 시간 정보
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationship
    user = relationship("User")

    def __repr__(self):
        return f"<PersonaFeedback(persona_id={self.persona_id}, rating={self.rating})>"


class PersonaPerformance(Base):
    """
    페르소나 성능 통계 (집계)

    각 페르소나의 전반적인 성능 메트릭
    """
    __tablename__ = "persona_performance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    persona_id = Column(String(50), unique=True, nullable=False, index=True)

    # 사용 통계
    total_sessions = Column(Integer, default=0)
    total_feedback_count = Column(Integer, default=0)

    # 만족도 메트릭
    average_rating = Column(Float, default=0.0)
    helpful_rate = Column(Float, default=0.0)  # 도움 비율 (0-1)
    appropriate_rate = Column(Float, default=0.0)  # 적절성 비율 (0-1)
    recommendation_rate = Column(Float, default=0.0)  # 재추천 의향 비율 (0-1)

    # 시간 정보
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<PersonaPerformance(persona_id={self.persona_id}, avg_rating={self.average_rating:.2f})>"


class PersonaWeightAdjustment(Base):
    """
    페르소나 가중치 조정 (학습)

    피드백 기반 추천 가중치 동적 조정
    """
    __tablename__ = "persona_weight_adjustments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    persona_id = Column(String(50), nullable=False, index=True)

    # 조정 컨텍스트
    concern = Column(String(50), nullable=False, index=True)  # 고민 유형
    age_range = Column(String(20), nullable=False, index=True)  # 나이대

    # 가중치 조정
    base_weight = Column(Float, default=0.0)  # 기본 가중치
    adjustment = Column(Float, default=0.0)  # 학습된 조정값
    final_weight = Column(Float, default=0.0)  # 최종 가중치

    # 학습 통계
    sample_count = Column(Integer, default=0)  # 학습 샘플 수
    success_rate = Column(Float, default=0.0)  # 성공률
    confidence = Column(Float, default=0.0)  # 신뢰도 (0-1)

    # 시간 정보
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<PersonaWeightAdjustment(persona={self.persona_id}, concern={self.concern}, weight={self.final_weight:.2f})>"


class UserPersonaPreference(Base):
    """
    사용자별 페르소나 선호도

    개인화된 추천을 위한 사용자별 페르소나 선호도 학습
    """
    __tablename__ = "user_persona_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    persona_id = Column(String(50), nullable=False, index=True)

    # 개인 선호도 메트릭
    total_sessions = Column(Integer, default=0)  # 총 상담 세션 수
    total_feedback_count = Column(Integer, default=0)  # 피드백 수
    average_rating = Column(Float, default=0.0)  # 평균 평점
    preference_score = Column(Float, default=0.0)  # 선호도 점수 (-1 to +1)

    # 성공 통계
    successful_sessions = Column(Integer, default=0)  # 성공 세션 (rating >= 4)
    success_rate = Column(Float, default=0.0)  # 성공률

    # 개인화 가중치
    personal_weight_adjustment = Column(Float, default=0.0)  # 개인 가중치 조정값
    confidence = Column(Float, default=0.0)  # 신뢰도 (0-1)

    # 시간 정보
    first_interaction = Column(DateTime, default=datetime.utcnow)
    last_interaction = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = relationship("User")

    def __repr__(self):
        return f"<UserPersonaPreference(user_id={self.user_id}, persona={self.persona_id}, score={self.preference_score:.2f})>"


class UserInteractionHistory(Base):
    """
    사용자 상호작용 이력

    페르소나와의 상호작용 패턴 추적
    """
    __tablename__ = "user_interaction_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(String(64), nullable=False, index=True)
    persona_id = Column(String(50), nullable=False, index=True)

    # 상호작용 정보
    interaction_type = Column(String(20), nullable=False)  # chat, feedback, recommendation
    duration_seconds = Column(Integer)  # 세션 길이
    message_count = Column(Integer)  # 메시지 수

    # 결과
    rating = Column(Integer)  # 평점 (1-5)
    helpful = Column(Boolean)  # 도움이 되었는가
    completed = Column(Boolean, default=True)  # 완료 여부

    # 컨텍스트
    concerns = Column(JSON)  # 고민 리스트
    user_age_range = Column(String(20))  # 나이대

    # 시간 정보
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationship
    user = relationship("User")

    def __repr__(self):
        return f"<UserInteractionHistory(user_id={self.user_id}, persona={self.persona_id}, type={self.interaction_type})>"


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
            # PostgreSQL/MySQL 등 프로덕션 데이터베이스용 연결 풀링 설정
            pool_size = int(os.getenv("DB_POOL_SIZE", "10"))  # 기본 연결 풀 크기
            max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "20"))  # 최대 오버플로우 연결
            pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))  # 연결 대기 타임아웃 (초)
            pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "3600"))  # 연결 재활용 시간 (초)
            pool_pre_ping = os.getenv("DB_POOL_PRE_PING", "true").lower() == "true"  # 연결 확인

            self.engine = create_engine(
                database_url,
                echo=echo,
                poolclass=QueuePool,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_timeout=pool_timeout,
                pool_recycle=pool_recycle,
                pool_pre_ping=pool_pre_ping,  # 연결 전 상태 확인 (끊어진 연결 방지)
            )

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
# Persona Feedback Management
# ============================================================================

class PersonaFeedbackManager:
    """페르소나 피드백 관리"""

    @staticmethod
    def submit_feedback(
        db: Session,
        user_id: str,
        session_id: str,
        persona_id: str,
        rating: int,
        helpful: bool = True,
        appropriate: bool = True,
        would_recommend_again: bool = True,
        concerns_addressed: Optional[List[str]] = None,
        feedback_text: Optional[str] = None,
        user_age_range: Optional[str] = None
    ) -> PersonaFeedback:
        """
        페르소나 피드백 제출

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            session_id: 세션 ID
            persona_id: 페르소나 ID
            rating: 만족도 (1-5)
            helpful: 도움이 되었는가
            appropriate: 적절한 추천이었는가
            would_recommend_again: 다시 추천받고 싶은가
            concerns_addressed: 해결된 고민 리스트
            feedback_text: 자유 형식 피드백
            user_age_range: 사용자 나이대

        Returns:
            PersonaFeedback 객체
        """
        user = UserManager.get_user(db, user_id)
        if not user:
            user = UserManager.create_user(db, user_id)

        # 피드백 생성
        feedback = PersonaFeedback(
            user_id=user.id,
            session_id=session_id,
            persona_id=persona_id,
            rating=rating,
            helpful=helpful,
            appropriate=appropriate,
            would_recommend_again=would_recommend_again,
            concerns_addressed=concerns_addressed or [],
            feedback_text=feedback_text,
            user_age_range=user_age_range,
            created_at=datetime.utcnow()
        )

        db.add(feedback)
        db.commit()
        db.refresh(feedback)

        # 성능 통계 업데이트
        PersonaFeedbackManager._update_performance_stats(db, persona_id)

        # 가중치 조정 학습
        if concerns_addressed and user_age_range:
            for concern in concerns_addressed:
                PersonaFeedbackManager._update_weight_adjustment(
                    db, persona_id, concern, user_age_range, rating >= 4
                )

        return feedback

    @staticmethod
    def _update_performance_stats(db: Session, persona_id: str):
        """페르소나 성능 통계 업데이트"""
        # 기존 성능 레코드 조회 또는 생성
        performance = db.query(PersonaPerformance).filter(
            PersonaPerformance.persona_id == persona_id
        ).first()

        if not performance:
            performance = PersonaPerformance(persona_id=persona_id)
            db.add(performance)

        # 모든 피드백 조회
        feedbacks = db.query(PersonaFeedback).filter(
            PersonaFeedback.persona_id == persona_id
        ).all()

        if not feedbacks:
            db.commit()
            return

        # 통계 계산
        total_count = len(feedbacks)
        total_rating = sum(f.rating for f in feedbacks)
        helpful_count = sum(1 for f in feedbacks if f.helpful)
        appropriate_count = sum(1 for f in feedbacks if f.appropriate)
        recommend_count = sum(1 for f in feedbacks if f.would_recommend_again)

        # 업데이트
        performance.total_feedback_count = total_count
        performance.average_rating = total_rating / total_count if total_count > 0 else 0.0
        performance.helpful_rate = helpful_count / total_count if total_count > 0 else 0.0
        performance.appropriate_rate = appropriate_count / total_count if total_count > 0 else 0.0
        performance.recommendation_rate = recommend_count / total_count if total_count > 0 else 0.0
        performance.last_updated = datetime.utcnow()

        db.commit()

    @staticmethod
    def _update_weight_adjustment(
        db: Session,
        persona_id: str,
        concern: str,
        age_range: str,
        success: bool
    ):
        """
        가중치 조정 학습

        Args:
            db: 데이터베이스 세션
            persona_id: 페르소나 ID
            concern: 고민 유형
            age_range: 나이대
            success: 성공 여부 (rating >= 4)
        """
        # 기존 레코드 조회 또는 생성
        adjustment = db.query(PersonaWeightAdjustment).filter(
            PersonaWeightAdjustment.persona_id == persona_id,
            PersonaWeightAdjustment.concern == concern,
            PersonaWeightAdjustment.age_range == age_range
        ).first()

        if not adjustment:
            # 새 레코드 생성
            adjustment = PersonaWeightAdjustment(
                persona_id=persona_id,
                concern=concern,
                age_range=age_range,
                base_weight=3.0,  # 기본 가중치
                adjustment=0.0,
                final_weight=3.0,
                sample_count=0,
                success_rate=0.0,
                confidence=0.0
            )
            db.add(adjustment)

        # 통계 업데이트 (이동 평균)
        adjustment.sample_count += 1
        old_success_rate = adjustment.success_rate
        adjustment.success_rate = (
            (old_success_rate * (adjustment.sample_count - 1) + (1.0 if success else 0.0))
            / adjustment.sample_count
        )

        # 신뢰도 계산 (샘플 수가 많을수록 높음, 최대 1.0)
        adjustment.confidence = min(1.0, adjustment.sample_count / 20.0)

        # 가중치 조정 계산
        # 성공률이 높으면 가중치 증가, 낮으면 감소
        # 신뢰도가 높을수록 조정폭 증가
        success_delta = adjustment.success_rate - 0.7  # 70%를 기준으로
        adjustment.adjustment = success_delta * 2.0 * adjustment.confidence

        # 최종 가중치 (기본 + 조정)
        adjustment.final_weight = max(0.5, adjustment.base_weight + adjustment.adjustment)

        adjustment.last_updated = datetime.utcnow()

        db.commit()

    @staticmethod
    def get_persona_feedback(
        db: Session,
        persona_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """페르소나 피드백 조회"""
        feedbacks = db.query(PersonaFeedback).filter(
            PersonaFeedback.persona_id == persona_id
        ).order_by(PersonaFeedback.created_at.desc()).limit(limit).all()

        return [
            {
                "rating": fb.rating,
                "helpful": fb.helpful,
                "appropriate": fb.appropriate,
                "would_recommend_again": fb.would_recommend_again,
                "concerns_addressed": fb.concerns_addressed,
                "feedback_text": fb.feedback_text,
                "user_age_range": fb.user_age_range,
                "created_at": fb.created_at.isoformat()
            }
            for fb in feedbacks
        ]

    @staticmethod
    def get_performance_stats(db: Session, persona_id: str) -> Optional[Dict[str, Any]]:
        """페르소나 성능 통계 조회"""
        performance = db.query(PersonaPerformance).filter(
            PersonaPerformance.persona_id == persona_id
        ).first()

        if not performance:
            return None

        return {
            "persona_id": performance.persona_id,
            "total_sessions": performance.total_sessions,
            "total_feedback_count": performance.total_feedback_count,
            "average_rating": round(performance.average_rating, 2),
            "helpful_rate": round(performance.helpful_rate, 2),
            "appropriate_rate": round(performance.appropriate_rate, 2),
            "recommendation_rate": round(performance.recommendation_rate, 2),
            "last_updated": performance.last_updated.isoformat()
        }

    @staticmethod
    def get_all_performance_stats(db: Session) -> List[Dict[str, Any]]:
        """전체 페르소나 성능 통계"""
        performances = db.query(PersonaPerformance).order_by(
            PersonaPerformance.average_rating.desc()
        ).all()

        return [
            {
                "persona_id": p.persona_id,
                "total_feedback_count": p.total_feedback_count,
                "average_rating": round(p.average_rating, 2),
                "helpful_rate": round(p.helpful_rate, 2),
                "appropriate_rate": round(p.appropriate_rate, 2),
                "recommendation_rate": round(p.recommendation_rate, 2)
            }
            for p in performances
        ]

    @staticmethod
    def get_weight_adjustments(
        db: Session,
        persona_id: Optional[str] = None,
        concern: Optional[str] = None,
        age_range: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """가중치 조정 조회"""
        query = db.query(PersonaWeightAdjustment)

        if persona_id:
            query = query.filter(PersonaWeightAdjustment.persona_id == persona_id)
        if concern:
            query = query.filter(PersonaWeightAdjustment.concern == concern)
        if age_range:
            query = query.filter(PersonaWeightAdjustment.age_range == age_range)

        adjustments = query.order_by(
            PersonaWeightAdjustment.final_weight.desc()
        ).all()

        return [
            {
                "persona_id": adj.persona_id,
                "concern": adj.concern,
                "age_range": adj.age_range,
                "base_weight": adj.base_weight,
                "adjustment": round(adj.adjustment, 2),
                "final_weight": round(adj.final_weight, 2),
                "sample_count": adj.sample_count,
                "success_rate": round(adj.success_rate, 2),
                "confidence": round(adj.confidence, 2)
            }
            for adj in adjustments
        ]


# ============================================================================
# User Personalization Management
# ============================================================================

class UserPersonalizationManager:
    """사용자별 개인화 관리"""

    @staticmethod
    def record_interaction(
        db: Session,
        user_id: str,
        session_id: str,
        persona_id: str,
        interaction_type: str,
        rating: Optional[int] = None,
        helpful: Optional[bool] = None,
        duration_seconds: Optional[int] = None,
        message_count: Optional[int] = None,
        concerns: Optional[List[str]] = None,
        user_age_range: Optional[str] = None,
        completed: bool = True
    ) -> UserInteractionHistory:
        """
        사용자 상호작용 기록

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            session_id: 세션 ID
            persona_id: 페르소나 ID
            interaction_type: 상호작용 유형 (chat, feedback, recommendation)
            rating: 평점 (1-5, optional)
            helpful: 도움이 되었는가 (optional)
            duration_seconds: 세션 길이 (초)
            message_count: 메시지 수
            concerns: 고민 리스트
            user_age_range: 사용자 나이대
            completed: 완료 여부

        Returns:
            UserInteractionHistory 객체
        """
        user = UserManager.get_user(db, user_id)
        if not user:
            user = UserManager.create_user(db, user_id)

        # 상호작용 기록
        interaction = UserInteractionHistory(
            user_id=user.id,
            session_id=session_id,
            persona_id=persona_id,
            interaction_type=interaction_type,
            rating=rating,
            helpful=helpful,
            duration_seconds=duration_seconds,
            message_count=message_count,
            concerns=concerns,
            user_age_range=user_age_range,
            completed=completed,
            created_at=datetime.utcnow()
        )

        db.add(interaction)
        db.commit()
        db.refresh(interaction)

        # 선호도 업데이트 (평점이 있는 경우)
        if rating is not None:
            UserPersonalizationManager._update_user_preference(
                db, user.id, persona_id, rating, helpful
            )

        return interaction

    @staticmethod
    def _update_user_preference(
        db: Session,
        user_internal_id: int,
        persona_id: str,
        rating: int,
        helpful: Optional[bool]
    ):
        """
        사용자 선호도 업데이트

        Args:
            db: 데이터베이스 세션
            user_internal_id: 내부 사용자 ID
            persona_id: 페르소나 ID
            rating: 평점
            helpful: 도움이 되었는가
        """
        # 기존 선호도 레코드 조회 또는 생성
        preference = db.query(UserPersonaPreference).filter(
            UserPersonaPreference.user_id == user_internal_id,
            UserPersonaPreference.persona_id == persona_id
        ).first()

        if not preference:
            preference = UserPersonaPreference(
                user_id=user_internal_id,
                persona_id=persona_id,
                total_sessions=0,
                total_feedback_count=0,
                average_rating=0.0,
                preference_score=0.0,
                successful_sessions=0,
                success_rate=0.0,
                personal_weight_adjustment=0.0,
                confidence=0.0,
                first_interaction=datetime.utcnow()
            )
            db.add(preference)

        # 통계 업데이트
        preference.total_feedback_count += 1
        old_average = preference.average_rating
        preference.average_rating = (
            (old_average * (preference.total_feedback_count - 1) + rating)
            / preference.total_feedback_count
        )

        # 성공 세션 카운트 (rating >= 4)
        if rating >= 4:
            preference.successful_sessions += 1

        preference.success_rate = (
            preference.successful_sessions / preference.total_feedback_count
            if preference.total_feedback_count > 0 else 0.0
        )

        # 선호도 점수 계산 (-1 to +1)
        # 평균 평점 4를 기준으로 정규화
        normalized_rating = (preference.average_rating - 3.0) / 2.0  # -1 to +1
        preference.preference_score = max(-1.0, min(1.0, normalized_rating))

        # 신뢰도 계산 (최소 5개 피드백 필요)
        preference.confidence = min(1.0, preference.total_feedback_count / 10.0)

        # 개인 가중치 조정 계산
        # 선호도 점수와 신뢰도에 기반
        preference.personal_weight_adjustment = (
            preference.preference_score * 2.0 * preference.confidence
        )

        preference.last_interaction = datetime.utcnow()

        db.commit()

    @staticmethod
    def get_user_preferences(
        db: Session,
        user_id: str,
        min_confidence: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        사용자 선호도 조회

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            min_confidence: 최소 신뢰도 필터

        Returns:
            선호도 리스트
        """
        user = UserManager.get_user(db, user_id)
        if not user:
            return []

        preferences = db.query(UserPersonaPreference).filter(
            UserPersonaPreference.user_id == user.id,
            UserPersonaPreference.confidence >= min_confidence
        ).order_by(UserPersonaPreference.preference_score.desc()).all()

        return [
            {
                "persona_id": pref.persona_id,
                "preference_score": round(pref.preference_score, 2),
                "average_rating": round(pref.average_rating, 2),
                "total_feedback_count": pref.total_feedback_count,
                "success_rate": round(pref.success_rate, 2),
                "personal_weight_adjustment": round(pref.personal_weight_adjustment, 2),
                "confidence": round(pref.confidence, 2),
                "first_interaction": pref.first_interaction.isoformat(),
                "last_interaction": pref.last_interaction.isoformat()
            }
            for pref in preferences
        ]

    @staticmethod
    def get_user_persona_weight(
        db: Session,
        user_id: str,
        persona_id: str
    ) -> float:
        """
        사용자별 페르소나 가중치 조회

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            persona_id: 페르소나 ID

        Returns:
            개인 가중치 조정값 (0.0 if not found)
        """
        user = UserManager.get_user(db, user_id)
        if not user:
            return 0.0

        preference = db.query(UserPersonaPreference).filter(
            UserPersonaPreference.user_id == user.id,
            UserPersonaPreference.persona_id == persona_id
        ).first()

        if not preference:
            return 0.0

        return preference.personal_weight_adjustment

    @staticmethod
    def get_user_interaction_history(
        db: Session,
        user_id: str,
        persona_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        사용자 상호작용 이력 조회

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            persona_id: 페르소나 ID 필터 (optional)
            limit: 최대 개수

        Returns:
            상호작용 이력 리스트
        """
        user = UserManager.get_user(db, user_id)
        if not user:
            return []

        query = db.query(UserInteractionHistory).filter(
            UserInteractionHistory.user_id == user.id
        )

        if persona_id:
            query = query.filter(UserInteractionHistory.persona_id == persona_id)

        interactions = query.order_by(
            UserInteractionHistory.created_at.desc()
        ).limit(limit).all()

        return [
            {
                "session_id": inter.session_id,
                "persona_id": inter.persona_id,
                "interaction_type": inter.interaction_type,
                "rating": inter.rating,
                "helpful": inter.helpful,
                "duration_seconds": inter.duration_seconds,
                "message_count": inter.message_count,
                "concerns": inter.concerns,
                "completed": inter.completed,
                "created_at": inter.created_at.isoformat()
            }
            for inter in interactions
        ]

    @staticmethod
    def get_user_stats(db: Session, user_id: str) -> Dict[str, Any]:
        """
        사용자 개인화 통계

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID

        Returns:
            통계 딕셔너리
        """
        user = UserManager.get_user(db, user_id)
        if not user:
            return {}

        # 선호도 통계
        preferences = db.query(UserPersonaPreference).filter(
            UserPersonaPreference.user_id == user.id
        ).all()

        total_feedback = sum(p.total_feedback_count for p in preferences)
        avg_rating = (
            sum(p.average_rating * p.total_feedback_count for p in preferences) / total_feedback
            if total_feedback > 0 else 0.0
        )

        # 상호작용 통계
        interactions = db.query(UserInteractionHistory).filter(
            UserInteractionHistory.user_id == user.id
        ).all()

        total_interactions = len(interactions)
        completed_count = sum(1 for i in interactions if i.completed)

        # 가장 선호하는 페르소나
        favorite_persona = None
        if preferences:
            top_pref = max(preferences, key=lambda p: p.preference_score)
            favorite_persona = {
                "persona_id": top_pref.persona_id,
                "preference_score": round(top_pref.preference_score, 2),
                "interaction_count": top_pref.total_feedback_count
            }

        return {
            "user_id": user.user_id,
            "total_personas_tried": len(preferences),
            "total_feedback_count": total_feedback,
            "overall_average_rating": round(avg_rating, 2),
            "total_interactions": total_interactions,
            "completed_interactions": completed_count,
            "completion_rate": round(completed_count / total_interactions, 2) if total_interactions > 0 else 0.0,
            "favorite_persona": favorite_persona,
            "personalization_active": len(preferences) >= 3  # 최소 3개 페르소나 경험 필요
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
