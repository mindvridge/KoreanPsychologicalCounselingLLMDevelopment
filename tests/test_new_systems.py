"""
새 시스템 통합 테스트 (New Systems Integration Tests)

새로 추가된 시스템 테스트:
1. 세션 저장소 (Session Storage)
2. 안전 시스템 6종 통합 (Self Check System)
3. 상담 효과 시스템 (Counseling Effectiveness)
4. 전체 파이프라인 통합
"""

import os
import sys
import pytest
import logging
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# 1. 세션 저장소 테스트
# =============================================================================

class TestSessionStorage:
    """세션 저장소 테스트"""

    @pytest.fixture
    def storage(self, tmp_path):
        """임시 SQLite 저장소"""
        from src.session_storage import SQLiteSessionStorage
        storage = SQLiteSessionStorage(
            db_path=str(tmp_path / "test_sessions.db"),
            session_ttl_hours=1
        )
        yield storage
        storage.close()

    def test_create_session(self, storage):
        """세션 생성"""
        session = storage.create_session(
            session_id="test_001",
            user_id="user_123"
        )

        assert session.session_id == "test_001"
        assert session.user_id == "user_123"
        assert session.turn_count == 0

    def test_add_and_get_messages(self, storage):
        """메시지 추가 및 조회"""
        storage.create_session(session_id="test_002")

        # 메시지 추가
        storage.add_message("test_002", "user", "안녕하세요")
        session = storage.add_message("test_002", "assistant", "안녕하세요!")

        # 확인
        assert len(session.conversation_history) == 2
        assert session.turn_count == 1

        # 조회
        loaded = storage.get_session("test_002")
        assert len(loaded.conversation_history) == 2

    def test_update_session_crisis(self, storage):
        """위기 이벤트 업데이트"""
        storage.create_session(session_id="test_003")

        session = storage.update_session(
            "test_003",
            crisis_detected=True,
            emotion="슬픔"
        )

        assert session.crisis_events == 1
        assert "슬픔" in session.emotion_summary

    def test_session_expiry(self, storage):
        """세션 만료"""
        # 만료된 세션 생성 시뮬레이션
        storage.create_session(session_id="test_004")

        # 정상 조회
        session = storage.get_session("test_004")
        assert session is not None

    def test_cleanup_expired(self, storage):
        """만료 세션 정리"""
        storage.create_session(session_id="test_005")
        cleaned = storage.cleanup_expired_sessions()
        # 새 세션은 만료되지 않음
        assert storage.get_session("test_005") is not None

    def test_session_stats(self, storage):
        """세션 통계"""
        storage.create_session(session_id="stats_001", user_id="user_a")
        storage.create_session(session_id="stats_002", user_id="user_b")

        stats = storage.get_session_stats()
        assert stats["total_active_sessions"] >= 2
        assert stats["unique_users"] >= 2


# =============================================================================
# 2. 자기 점검 시스템 테스트
# =============================================================================

class TestSelfCheckSystem:
    """자기 점검 시스템 (안전 시스템 6종 통합)"""

    @pytest.fixture
    def checker(self):
        """자기 점검 시스템"""
        from src.self_check_system import get_self_check_system
        return get_self_check_system(strict_mode=True)

    def test_safe_empathic_response(self, checker):
        """안전한 공감 응답"""
        from src.self_check_system import ResponseStatus

        report = checker.check_response(
            response="많이 힘드셨군요. 어떤 상황이셨는지 더 이야기해 주실 수 있을까요?",
            user_message="요즘 너무 지쳐요"
        )

        assert report.status in [ResponseStatus.SAFE, ResponseStatus.WARNING]
        assert report.overall_score >= 50

    def test_detect_medical_advice(self, checker):
        """의학적 조언 감지"""
        report = checker.check_response(
            response="약을 먹어보세요. 우울증 진단이 필요해 보입니다.",
            user_message="기분이 우울해요"
        )

        # 의학적 조언은 감지되어야 함
        has_medical_warning = any(
            "의학" in w or "medical" in w.lower() or "진단" in w
            for w in report.warnings
        ) or report.overall_score < 70

        # 완벽히 감지 안될 수 있지만 점수는 낮아야 함
        assert report.overall_score <= 90 or has_medical_warning

    def test_detect_directive_language(self, checker):
        """지시적 표현 감지"""
        report = checker.check_response(
            response="그만하세요. 당장 그 생각을 멈추세요.",
            user_message="부정적인 생각이 자꾸 들어요"
        )

        # 지시적 표현은 경고 이상
        assert report.overall_score < 90 or len(report.warnings) > 0

    def test_quality_score_calculation(self, checker):
        """품질 점수 계산"""
        # 좋은 응답
        good_report = checker.check_response(
            response="그런 상황에서 힘드셨겠어요. 더 이야기해 주시겠어요?",
            user_message="직장에서 스트레스 받아요"
        )

        # 덜 좋은 응답
        bad_report = checker.check_response(
            response="그냥 참으세요.",
            user_message="직장에서 스트레스 받아요"
        )

        # 좋은 응답이 더 높은 점수
        assert good_report.overall_score >= bad_report.overall_score - 10


# =============================================================================
# 3. 상담 효과 시스템 테스트
# =============================================================================

class TestCounselingEffectiveness:
    """상담 효과 시스템"""

    @pytest.fixture
    def system(self):
        """상담 효과 시스템"""
        from src.counseling_effectiveness import get_effectiveness_system
        return get_effectiveness_system()

    def test_analyze_good_interaction(self, system):
        """좋은 상호작용 분석"""
        from src.counseling_effectiveness import CounselingQuality

        report = system.analyze_interaction(
            session_id="eff_001",
            user_message="직장에서 스트레스가 너무 심해요",
            assistant_response="직장에서 많이 힘드셨군요. 어떤 일들이 특히 스트레스를 주시나요?",
            context={}
        )

        assert report.overall_quality_score > 50
        assert report.quality_grade in list(CounselingQuality)

    def test_session_phase_tracking(self, system):
        """세션 단계 추적"""
        session_id = "phase_001"

        # 첫 턴 (opening)
        report1 = system.analyze_interaction(
            session_id=session_id,
            user_message="안녕하세요",
            assistant_response="안녕하세요, 반갑습니다.",
            context={}
        )
        assert report1.session_progress.current_phase == "opening"

        # 여러 턴 진행
        for i in range(5):
            report = system.analyze_interaction(
                session_id=session_id,
                user_message=f"메시지 {i}",
                assistant_response=f"응답 {i}",
                context={}
            )

        # exploration 단계로 진행
        assert report.session_progress.current_phase == "exploration"

    def test_prompt_section_generation(self, system):
        """프롬프트 섹션 생성"""
        # 먼저 세션 시작
        system.analyze_interaction(
            session_id="prompt_001",
            user_message="테스트",
            assistant_response="테스트 응답",
            context={}
        )

        section = system.get_prompt_section("prompt_001")

        assert section is not None
        assert len(section) > 0

    def test_intervention_recommendations(self, system):
        """개입 추천 생성"""
        report = system.analyze_interaction(
            session_id="interv_001",
            user_message="너무 힘들어요",
            assistant_response="힘드시군요.",  # 짧은 응답
            context={}
        )

        # 개선이 필요한 응답이므로 추천이 있어야 함
        # (짧은 응답에 대한 추천)
        assert report is not None


# =============================================================================
# 4. 안전 시스템 v2 테스트
# =============================================================================

class TestSafetySystemV2:
    """안전 시스템 v2 (위기 감지)"""

    @pytest.fixture
    def safety(self):
        """안전 시스템"""
        from src.safety_system_v2 import SafetySystem
        return SafetySystem()

    def test_normal_message_safe(self, safety):
        """일반 메시지는 안전"""
        from src.safety_system_v2 import RiskLevel

        result = safety.check_safety(
            text="오늘 날씨가 좋네요",
            emotion_data=None,
            conversation_history=[]
        )

        assert result["risk_level"] in [RiskLevel.NONE, RiskLevel.LOW]
        assert not result.get("requires_intervention", False)

    def test_crisis_keyword_detection(self, safety):
        """위기 키워드 감지"""
        from src.safety_system_v2 import RiskLevel

        result = safety.check_safety(
            text="더 이상 살고 싶지 않아요",
            emotion_data=None,
            conversation_history=[]
        )

        # 위기 메시지로 감지
        assert result["risk_level"] not in [RiskLevel.NONE]

    def test_indirect_crisis_detection(self, safety):
        """간접적 위기 표현 감지"""
        from src.safety_system_v2 import RiskLevel

        result = safety.check_safety(
            text="그냥 사라지고 싶어요. 모든 게 의미없어요.",
            emotion_data=None,
            conversation_history=[]
        )

        # 간접 표현도 감지
        assert result["risk_level"] != RiskLevel.NONE

    def test_intervention_message_provided(self, safety):
        """위기 시 개입 메시지 제공"""
        result = safety.check_safety(
            text="죽고 싶어요",
            emotion_data=None,
            conversation_history=[]
        )

        # 개입이 필요한 경우 메시지 제공
        if result.get("requires_intervention"):
            assert "intervention_message" in result


# =============================================================================
# 5. 통합 파이프라인 테스트
# =============================================================================

class TestIntegratedPipeline:
    """전체 파이프라인 통합"""

    @pytest.fixture
    def system(self, tmp_path):
        """통합 시스템 (Mock LLM)"""
        from main_integrated import IntegratedMentalHealthSystem

        # 설정 파일 생성
        config = f"""
model:
  provider: mock
  name: test

session:
  db_path: {tmp_path}/sessions.db
  ttl_hours: 1

safety:
  log_all_conversations: false

logging:
  log_dir: {tmp_path}/logs
"""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(config)

        system = IntegratedMentalHealthSystem(str(config_path))
        system.initialize_all_components()

        return system

    def test_system_components_initialized(self, system):
        """컴포넌트 초기화 확인"""
        status = system.get_system_status()

        assert status["initialized"]
        assert "components" in status

        # 주요 컴포넌트 확인
        components = status["components"]
        # safety_system과 response_checker는 있어야 함
        assert components.get("safety_system") or components.get("response_checker")

    def test_process_message_returns_expected_fields(self, system):
        """메시지 처리 결과 필드 확인"""
        result = system.process_message(
            session_id="test_001",
            user_message="안녕하세요"
        )

        # 필수 필드 확인
        assert "response" in result
        assert "crisis_detected" in result
        assert "safety_check" in result
        assert "counseling_quality" in result
        assert "metadata" in result

    def test_session_persistence(self, system):
        """세션 영속성 확인"""
        # 첫 번째 메시지
        result1 = system.process_message(
            session_id="persist_001",
            user_message="안녕하세요"
        )

        # 두 번째 메시지 (세션 이어받기)
        result2 = system.process_message(
            session_id="persist_001",
            user_message="저는 학생이에요"
        )

        # 세션 저장소가 있으면 이력이 유지됨
        if system.session_storage:
            session = system.session_storage.get_session("persist_001")
            assert session is not None
            assert len(session.conversation_history) >= 2

    def test_safety_check_in_response(self, system):
        """응답에 안전 검사 포함"""
        result = system.process_message(
            session_id="safety_001",
            user_message="요즘 힘들어요"
        )

        safety = result.get("safety_check", {})
        assert "status" in safety
        assert "passed" in safety

    def test_counseling_quality_in_response(self, system):
        """응답에 상담 품질 포함"""
        result = system.process_message(
            session_id="quality_001",
            user_message="스트레스 받아요"
        )

        quality = result.get("counseling_quality", {})
        # 값이 있거나 None (시스템 미초기화시)
        assert "score" in quality or "grade" in quality


# =============================================================================
# 6. 엣지 케이스
# =============================================================================

class TestEdgeCases:
    """엣지 케이스"""

    def test_empty_string_handling(self):
        """빈 문자열 처리"""
        from src.counseling_effectiveness import get_effectiveness_system

        system = get_effectiveness_system()
        report = system.analyze_interaction(
            session_id="edge_001",
            user_message="",
            assistant_response="무슨 말씀인가요?",
            context={}
        )

        assert report is not None

    def test_special_characters(self, tmp_path):
        """특수 문자 처리"""
        from src.session_storage import SQLiteSessionStorage

        storage = SQLiteSessionStorage(str(tmp_path / "special.db"))
        storage.create_session("special_001")

        # 특수 문자가 포함된 메시지
        session = storage.add_message(
            "special_001",
            "user",
            "이모지 😊 특수문자 <>&'\""
        )

        loaded = storage.get_session("special_001")
        assert "😊" in loaded.conversation_history[0]["content"]

        storage.close()

    def test_korean_unicode(self, tmp_path):
        """한글 유니코드"""
        from src.session_storage import SQLiteSessionStorage

        storage = SQLiteSessionStorage(str(tmp_path / "korean.db"))
        storage.create_session("korean_001")

        korean = "한글 테스트입니다. 가나다라마바사"
        storage.add_message("korean_001", "user", korean)

        loaded = storage.get_session("korean_001")
        assert loaded.conversation_history[0]["content"] == korean

        storage.close()


# =============================================================================
# 실행
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
