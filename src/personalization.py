"""
Personalization Layer for Long-Term Memory
장기 기억 기반 개인화 레이어

사용자별 맞춤형 상담 경험 제공
Enhanced with Cross-Session Context and Pattern Analysis
"""

from typing import Optional, Dict, List, Any
from datetime import datetime
import logging

from src.database import (
    get_db,
    UserManager,
    ConversationManager,
    AssessmentManager as DBAssessmentManager,
    User,
    UserMetadata
)
from src.ner_extractor import KoreanNERExtractor, ConversationAnalyzer, ExtractedInfo
from src.logging_system import PrivacyMasker
from src.long_term_memory import (
    LongTermMemoryManager,
    get_memory_manager,
    SessionMemory,
    UserLongTermProfile
)

logger = logging.getLogger(__name__)


class PersonalizationManager:
    """
    개인화 관리자

    기능:
    - 사용자 식별 및 프로필 관리
    - 대화 기록 저장 및 조회
    - 정보 추출 및 업데이트
    - 개인화된 인사말 생성
    - [신규] 교차 세션 맥락 연결
    - [신규] 장기 패턴 분석
    - [신규] 치료 효과 추적
    """

    def __init__(self, memory_storage_path: Optional[str] = None):
        self.ner = KoreanNERExtractor()
        self.privacy_masker = PrivacyMasker()

        # 장기 기억 관리자 초기화
        storage_path = memory_storage_path or "./data/long_term_memory.json"
        self.memory_manager = get_memory_manager(storage_path)

    def get_or_create_user(
        self,
        user_identifier: Optional[str] = None,
        consent: bool = True
    ) -> tuple[str, bool]:
        """
        사용자 조회 또는 생성

        Args:
            user_identifier: 사용자 식별자 (선택사항, 익명 가능)
            consent: 데이터 저장 동의

        Returns:
            (user_id, is_new_user)
        """
        db = next(get_db())
        try:
            if user_identifier:
                # 기존 사용자 확인
                user_id = UserManager.generate_user_id(user_identifier)
                user = UserManager.get_user(db, user_id)

                if user:
                    UserManager.update_last_active(db, user_id)
                    return user_id, False
                else:
                    # 새 사용자 생성
                    user = UserManager.create_user(db, user_id, consent)
                    return user.user_id, True
            else:
                # 완전 익명 사용자
                user = UserManager.create_user(db, consent=consent)
                return user.user_id, True

        finally:
            db.close()

    def save_conversation_turn(
        self,
        user_id: str,
        session_id: str,
        role: str,
        content: str,
        detected_emotion: Optional[str] = None,
        crisis_detected: bool = False,
        crisis_level: int = 0,
        response_time: Optional[float] = None
    ):
        """
        대화 턴 저장

        Args:
            user_id: 사용자 ID
            session_id: 세션 ID
            role: 역할 ('user' or 'assistant')
            content: 내용
            detected_emotion: 감지된 감정
            crisis_detected: 위기 감지 여부
            crisis_level: 위기 수준
            response_time: 응답 시간
        """
        db = next(get_db())
        try:
            # PII 마스킹
            masked_content = self.privacy_masker.mask_pii(content)

            # 저장
            ConversationManager.save_conversation(
                db=db,
                user_id=user_id,
                session_id=session_id,
                role=role,
                content=masked_content,
                detected_emotion=detected_emotion,
                crisis_detected=crisis_detected,
                crisis_level=crisis_level,
                response_time=response_time
            )

            # 사용자 메시지인 경우 정보 추출
            if role == "user":
                self._extract_and_update_user_info(db, user_id, content)

        finally:
            db.close()

    def _extract_and_update_user_info(self, db, user_id: str, message: str):
        """
        메시지에서 정보 추출 및 사용자 프로필 업데이트

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            message: 사용자 메시지
        """
        try:
            # 정보 추출
            extracted = self.ner.extract_all(message)

            # 사용자 조회
            user = UserManager.get_user(db, user_id)
            if not user or not user.metadata:
                return

            metadata = user.metadata
            updated = False

            # 이름 업데이트
            if extracted.name and not metadata.extracted_name:
                metadata.extracted_name = extracted.name
                metadata.preferred_name = self.ner.generate_preferred_name(
                    extracted.name,
                    extracted.gender
                )
                updated = True
                logger.info(f"Extracted name for user {user_id}: {extracted.name}")

            # 나이 업데이트
            if extracted.age and not metadata.age_range:
                age_range = self._get_age_range(extracted.age)
                metadata.age_range = age_range
                updated = True

            # 고민 누적
            if extracted.concerns:
                current_concerns = metadata.main_concerns or []
                for concern in extracted.concerns:
                    if concern not in current_concerns:
                        current_concerns.append(concern)
                metadata.main_concerns = current_concerns
                updated = True

            if updated:
                db.commit()

        except Exception as e:
            logger.error(f"Error extracting user info: {e}")
            db.rollback()

    def _get_age_range(self, age: int) -> str:
        """나이대 계산"""
        if age < 20:
            return "10대"
        elif age < 30:
            return "20대"
        elif age < 40:
            return "30대"
        elif age < 50:
            return "40대"
        elif age < 60:
            return "50대"
        else:
            return "60대 이상"

    def get_conversation_history(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        대화 기록 조회

        Args:
            user_id: 사용자 ID
            session_id: 세션 ID (선택사항)
            limit: 최대 개수

        Returns:
            대화 기록 리스트
        """
        db = next(get_db())
        try:
            return ConversationManager.get_conversation_history(
                db, user_id, session_id, limit
            )
        finally:
            db.close()

    def get_personalized_greeting(self, user_id: str, is_new_user: bool = False) -> str:
        """
        개인화된 인사말 생성

        Args:
            user_id: 사용자 ID
            is_new_user: 신규 사용자 여부

        Returns:
            개인화된 인사말
        """
        db = next(get_db())
        try:
            user = UserManager.get_user(db, user_id)

            if not user or not user.metadata:
                return "안녕하세요. 무엇을 도와드릴까요?"

            metadata = user.metadata
            preferred_name = metadata.preferred_name or "손님"

            if is_new_user:
                return f"안녕하세요, {preferred_name}! 반갑습니다. 편안하게 이야기 나눠봐요."
            else:
                # 재방문 사용자
                last_active = user.last_active
                now = datetime.utcnow()
                time_diff = now - last_active

                if time_diff.days == 0:
                    # 오늘 이미 대화
                    return f"다시 만나서 반갑습니다, {preferred_name}!"
                elif time_diff.days == 1:
                    return f"어제 이후 처음이시네요, {preferred_name}! 오늘은 어떠신가요?"
                elif time_diff.days <= 7:
                    return f"며칠 만이시네요, {preferred_name}! 그동안 어떻게 지내셨어요?"
                else:
                    return f"오랜만입니다, {preferred_name}! 잘 지내셨나요?"

        finally:
            db.close()

    def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """
        사용자 맥락 정보 조회

        Args:
            user_id: 사용자 ID

        Returns:
            사용자 맥락 정보
        """
        db = next(get_db())
        try:
            user = UserManager.get_user(db, user_id)

            if not user:
                return {}

            metadata = user.metadata if user.metadata else None

            # 최근 평가 결과
            recent_assessments = DBAssessmentManager.get_assessment_history(
                db, user_id, limit=3
            )

            # 주요 고민
            main_concerns = metadata.main_concerns if metadata else []

            return {
                "preferred_name": metadata.preferred_name if metadata else None,
                "age_range": metadata.age_range if metadata else None,
                "main_concerns": main_concerns,
                "recent_assessments": recent_assessments,
                "total_conversations": user.total_conversations,
                "total_messages": user.total_messages,
                "crisis_count": user.crisis_count
            }

        finally:
            db.close()

    def save_assessment(
        self,
        user_id: str,
        session_id: str,
        assessment_type: str,
        responses: List[int],
        score: int,
        severity: str,
        interpretation: str,
        recommendations: List[str]
    ):
        """
        평가 결과 저장

        Args:
            user_id: 사용자 ID
            session_id: 세션 ID
            assessment_type: 평가 유형
            responses: 응답 배열
            score: 점수
            severity: 심각도
            interpretation: 해석
            recommendations: 권장사항
        """
        db = next(get_db())
        try:
            DBAssessmentManager.save_assessment(
                db=db,
                user_id=user_id,
                session_id=session_id,
                assessment_type=assessment_type,
                responses=responses,
                score=score,
                severity=severity,
                interpretation=interpretation,
                recommendations=recommendations
            )
        finally:
            db.close()

    def get_assessment_trend(self, user_id: str, assessment_type: str) -> Dict[str, Any]:
        """
        평가 결과 추이 조회

        Args:
            user_id: 사용자 ID
            assessment_type: 평가 유형

        Returns:
            추이 정보
        """
        db = next(get_db())
        try:
            return DBAssessmentManager.get_trend_data(db, user_id, assessment_type)
        finally:
            db.close()

    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """
        사용자 통계 조회

        Args:
            user_id: 사용자 ID

        Returns:
            통계 정보
        """
        db = next(get_db())
        try:
            return UserManager.get_user_stats(db, user_id)
        finally:
            db.close()

    def generate_personalized_context(self, user_id: str) -> str:
        """
        개인화된 시스템 컨텍스트 생성

        LLM에게 사용자 맥락을 제공하여 개인화된 응답 생성

        Args:
            user_id: 사용자 ID

        Returns:
            시스템 컨텍스트 문자열
        """
        context = self.get_user_context(user_id)

        context_parts = []

        # 선호 호칭
        if context.get("preferred_name"):
            context_parts.append(f"사용자 호칭: {context['preferred_name']}")

        # 나이대
        if context.get("age_range"):
            context_parts.append(f"나이대: {context['age_range']}")

        # 주요 고민
        if context.get("main_concerns"):
            concerns_str = ", ".join(context["main_concerns"][:3])
            context_parts.append(f"주요 고민: {concerns_str}")

        # 최근 평가
        if context.get("recent_assessments"):
            latest = context["recent_assessments"][0]
            context_parts.append(
                f"최근 평가: {latest['type']} (점수: {latest['score']}, {latest['severity']})"
            )

        # 위기 이력
        if context.get("crisis_count", 0) > 0:
            context_parts.append(f"위기 감지 이력: {context['crisis_count']}회")
            context_parts.append("주의: 위기 징후에 민감하게 대응하세요.")

        if context_parts:
            return "\n".join(["[사용자 맥락]"] + context_parts)
        else:
            return ""

    # =========================================================================
    # 장기 기억 통합 메서드 (신규)
    # =========================================================================

    def generate_enhanced_context(
        self,
        user_id: str,
        session_id: str,
        include_cross_session: bool = True,
        include_patterns: bool = True
    ) -> str:
        """
        강화된 개인화 컨텍스트 생성 (장기 기억 포함)

        Args:
            user_id: 사용자 ID
            session_id: 현재 세션 ID
            include_cross_session: 교차 세션 컨텍스트 포함
            include_patterns: 장기 패턴 분석 포함

        Returns:
            통합 컨텍스트 문자열
        """
        context_parts = []

        # 1. 기존 개인화 컨텍스트
        basic_context = self.generate_personalized_context(user_id)
        if basic_context:
            context_parts.append(basic_context)

        # 2. 장기 기억 컨텍스트
        memory_context = self.memory_manager.generate_personalized_context(
            user_id,
            include_patterns=include_patterns,
            include_bridge=include_cross_session
        )
        if memory_context:
            context_parts.append(memory_context)

        return "\n\n".join(context_parts)

    def end_session_with_memory(
        self,
        user_id: str,
        session_id: str,
        session_summary: Dict[str, Any]
    ):
        """
        세션 종료 시 장기 기억에 저장

        Args:
            user_id: 사용자 ID
            session_id: 세션 ID
            session_summary: 세션 요약 데이터
        """
        self.memory_manager.create_session_memory(
            session_id=session_id,
            user_id=user_id,
            session_data=session_summary
        )
        logger.info(f"Session memory saved for user {user_id}")

    def record_technique_with_effect(
        self,
        user_id: str,
        technique: str,
        concern: str,
        effectiveness: float
    ):
        """
        치료 기법 사용 및 효과 기록

        Args:
            user_id: 사용자 ID
            technique: 사용된 기법
            concern: 관련 고민
            effectiveness: 효과 점수 (-1 to 1)
        """
        self.memory_manager.record_technique_usage(
            user_id=user_id,
            technique=technique,
            context={"concern": concern},
            effectiveness_score=effectiveness
        )

    def get_recommended_techniques_for_user(
        self,
        user_id: str,
        current_concern: Optional[str] = None,
        current_emotion: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        사용자 맞춤 기법 추천

        Args:
            user_id: 사용자 ID
            current_concern: 현재 고민
            current_emotion: 현재 감정

        Returns:
            추천 기법 리스트
        """
        recommendations = self.memory_manager.get_recommended_techniques(
            user_id=user_id,
            current_concern=current_concern,
            current_emotion=current_emotion
        )

        return [
            {"technique": name, "confidence": round(score, 2)}
            for name, score in recommendations
        ]

    def get_user_progress_report(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        사용자 진행 상황 리포트

        Args:
            user_id: 사용자 ID
            days: 분석 기간

        Returns:
            진행 리포트
        """
        return self.memory_manager.generate_progress_report(user_id, days)

    def add_user_strength(self, user_id: str, strength: str):
        """사용자 강점 추가"""
        self.memory_manager.add_identified_strength(user_id, strength)

    def add_user_coping_strategy(self, user_id: str, strategy: str):
        """효과적인 대처 전략 추가"""
        self.memory_manager.add_coping_strategy(user_id, strategy)

    def update_homework_completion(
        self,
        user_id: str,
        session_id: str,
        completed: List[str]
    ):
        """과제 완료 상태 업데이트"""
        self.memory_manager.update_homework_status(user_id, session_id, completed)

    def get_session_bridge_context(self, user_id: str) -> str:
        """
        이전 세션과의 브릿지 컨텍스트만 가져오기

        Returns:
            브릿지 컨텍스트 문자열
        """
        profile = self.memory_manager.get_or_create_profile(user_id)
        sessions = self.memory_manager.get_recent_sessions(user_id, limit=3)

        return self.memory_manager.context_manager.generate_session_bridge(
            profile, sessions, profile.total_sessions + 1
        )

    def get_long_term_patterns(self, user_id: str) -> Dict[str, Any]:
        """
        장기 패턴 분석 결과 조회

        Returns:
            패턴 분석 결과
        """
        profile = self.memory_manager.get_or_create_profile(user_id)

        return {
            "recurring_concerns": profile.recurring_concerns,
            "trigger_patterns": profile.trigger_patterns,
            "effective_techniques": profile.effective_techniques,
            "coping_strategies": profile.coping_strategies,
            "identified_strengths": profile.identified_strengths,
            "overall_progress": profile.overall_progress,
            "total_sessions": profile.total_sessions
        }


# ============================================================================
# Utility Functions
# ============================================================================

def create_personalization_manager() -> PersonalizationManager:
    """PersonalizationManager 싱글톤 생성"""
    return PersonalizationManager()


# 전역 인스턴스 (선택사항)
_personalization_manager: Optional[PersonalizationManager] = None

def get_personalization_manager() -> PersonalizationManager:
    """PersonalizationManager 싱글톤 가져오기"""
    global _personalization_manager
    if _personalization_manager is None:
        _personalization_manager = PersonalizationManager()
    return _personalization_manager
