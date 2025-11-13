"""
Personalization Layer for Long-Term Memory
장기 기억 기반 개인화 레이어

사용자별 맞춤형 상담 경험 제공
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

logger = logging.getLogger(__name__)


class PersonalizationManager:
    """
    개인화 관리자

    기능:
    - 사용자 식별 및 프로필 관리
    - 대화 기록 저장 및 조회
    - 정보 추출 및 업데이트
    - 개인화된 인사말 생성
    """

    def __init__(self):
        self.ner = KoreanNERExtractor()
        self.privacy_masker = PrivacyMasker()

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
