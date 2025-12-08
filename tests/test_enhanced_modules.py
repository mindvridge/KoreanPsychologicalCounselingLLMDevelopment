"""
신규 모듈 테스트
Tests for Enhanced LLM Modules
"""

import pytest
from datetime import datetime
import sys
import os

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# =============================================================================
# Response Validator Tests
# =============================================================================

class TestResponseValidator:
    """응답 검증기 테스트"""

    def test_import(self):
        """모듈 임포트 테스트"""
        from src.response_validator import ResponseValidator, ValidationResult
        assert ResponseValidator is not None
        assert ValidationResult is not None

    def test_validator_initialization(self):
        """검증기 초기화 테스트"""
        from src.response_validator import ResponseValidator
        validator = ResponseValidator()
        assert validator is not None

    def test_valid_response(self):
        """유효한 응답 검증"""
        from src.response_validator import ResponseValidator
        validator = ResponseValidator()

        response = "많이 힘드시겠어요. 그런 감정이 드시는 건 자연스러운 거예요. 어떤 부분이 가장 힘드신가요?"
        context = {"crisis_level": 0, "emotion": "sadness"}

        result = validator.validate(response, context)

        assert result is not None
        assert result.overall_score >= 0.5

    def test_empathy_detection(self):
        """공감 표현 감지 테스트"""
        from src.response_validator import ResponseValidator
        validator = ResponseValidator()

        # 공감 표현이 있는 응답
        empathetic = "정말 힘드시겠어요. 그 마음 충분히 이해해요."
        result1 = validator.validate(empathetic, {})
        assert result1.check_results.get("empathy_present", False) == True

        # 공감 표현이 없는 응답
        non_empathetic = "네, 알겠습니다. 다음 단계로 넘어갈까요?"
        result2 = validator.validate(non_empathetic, {})
        # 공감 없이도 통과할 수 있지만 점수는 낮음

    def test_safety_check(self):
        """안전성 검사 테스트"""
        from src.response_validator import ResponseValidator
        validator = ResponseValidator()

        # 안전한 응답
        safe_response = "전문가와 상담해 보시는 것도 좋은 방법이에요."
        result1 = validator.validate(safe_response, {})
        assert result1.check_results.get("safety_language", True) == True

    def test_crisis_response_validation(self):
        """위기 상황 응답 검증"""
        from src.response_validator import ResponseValidator
        validator = ResponseValidator()

        # 위기 상황에서 적절한 응답 (상담전화 포함)
        crisis_response = "지금 많이 힘드시군요. 자살예방상담전화 1393이나 정신건강위기상담전화 1577-0199로 연락하실 수 있어요."
        context = {"crisis_level": 4}
        result = validator.validate(crisis_response, context)
        assert result.overall_score >= 0.6


# =============================================================================
# Conversation State Tests
# =============================================================================

class TestConversationState:
    """대화 상태 관리 테스트"""

    def test_import(self):
        """모듈 임포트 테스트"""
        from src.conversation_state import ConversationStateManager, ConversationState
        assert ConversationStateManager is not None
        assert ConversationState is not None

    def test_state_manager_initialization(self):
        """상태 관리자 초기화"""
        from src.conversation_state import ConversationStateManager
        manager = ConversationStateManager()
        state = manager.get_state()

        assert state is not None
        assert state.turn_count == 0

    def test_state_update(self):
        """상태 업데이트 테스트"""
        from src.conversation_state import ConversationStateManager
        manager = ConversationStateManager()

        manager.update_state(
            user_message="오늘 기분이 안 좋아요",
            emotion="sadness",
            emotion_intensity=0.7
        )

        state = manager.get_state()
        assert state.turn_count == 1
        assert len(state.emotion_trajectory) == 1

    def test_phase_progression(self):
        """대화 단계 진행 테스트"""
        from src.conversation_state import ConversationStateManager, ConversationPhase
        manager = ConversationStateManager()

        # 초기 단계는 OPENING
        assert manager.get_state().phase == ConversationPhase.OPENING

        # 여러 턴 진행 후 단계 변화
        for i in range(5):
            manager.update_state(
                user_message=f"메시지 {i}",
                emotion="neutral",
                emotion_intensity=0.5
            )

        # 턴이 진행되면 단계가 변경됨
        state = manager.get_state()
        assert state.turn_count == 5

    def test_reset(self):
        """상태 리셋 테스트"""
        from src.conversation_state import ConversationStateManager
        manager = ConversationStateManager()

        manager.update_state("테스트", "neutral", 0.5)
        manager.reset()

        state = manager.get_state()
        assert state.turn_count == 0
        assert len(state.emotion_trajectory) == 0


# =============================================================================
# Evaluation Tests
# =============================================================================

class TestEvaluation:
    """평가 시스템 테스트"""

    def test_import(self):
        """모듈 임포트 테스트"""
        from src.evaluation import CounselingLLMEvaluator, evaluate_response
        assert CounselingLLMEvaluator is not None
        assert evaluate_response is not None

    def test_evaluator_initialization(self):
        """평가자 초기화"""
        from src.evaluation import CounselingLLMEvaluator
        evaluator = CounselingLLMEvaluator()
        assert evaluator is not None

    def test_response_evaluation(self):
        """응답 평가 테스트"""
        from src.evaluation import CounselingLLMEvaluator
        evaluator = CounselingLLMEvaluator()

        response = "많이 힘드시겠어요. 그 감정을 느끼시는 건 자연스러운 거예요. 더 이야기해 주실 수 있을까요?"
        context = {
            "user_message": "요즘 너무 우울해요",
            "emotion": "sadness",
            "crisis_level": 0
        }

        result = evaluator.evaluate(response, context)

        assert result is not None
        assert 0.0 <= result.overall_score <= 1.0
        assert "empathy" in result.metric_scores

    def test_quick_evaluate(self):
        """빠른 평가 함수 테스트"""
        from src.evaluation import evaluate_response

        response = "공감합니다. 힘드시죠."
        context = {"user_message": "힘들어요"}

        result = evaluate_response(response, context)
        assert "overall_score" in result


# =============================================================================
# Experiments Tests
# =============================================================================

class TestExperiments:
    """A/B 테스트 프레임워크 테스트"""

    def test_import(self):
        """모듈 임포트 테스트"""
        from src.experiments import ExperimentManager, get_experiment_manager
        assert ExperimentManager is not None
        assert get_experiment_manager is not None

    def test_create_experiment(self):
        """실험 생성 테스트"""
        from src.experiments import ExperimentManager, ExperimentVariant

        manager = ExperimentManager()

        variants = [
            ExperimentVariant(name="control", config={"prompt_version": "v1"}),
            ExperimentVariant(name="treatment", config={"prompt_version": "v2"})
        ]

        experiment = manager.create_experiment(
            name="prompt_test",
            description="프롬프트 버전 테스트",
            variants=variants,
            target_sample_size=100
        )

        assert experiment is not None
        assert experiment.name == "prompt_test"
        assert len(experiment.variants) == 2

    def test_variant_assignment(self):
        """변형 할당 테스트"""
        from src.experiments import ExperimentManager, ExperimentVariant

        manager = ExperimentManager()

        variants = [
            ExperimentVariant(name="A", config={}),
            ExperimentVariant(name="B", config={})
        ]

        experiment = manager.create_experiment(
            name="assignment_test",
            description="할당 테스트",
            variants=variants
        )

        # 동일 사용자는 항상 같은 변형 할당
        user_id = "test_user_123"
        variant1 = manager.assign_variant(experiment.experiment_id, user_id)
        variant2 = manager.assign_variant(experiment.experiment_id, user_id)

        assert variant1 == variant2  # 일관된 할당


# =============================================================================
# Monitoring Dashboard Tests
# =============================================================================

class TestMonitoringDashboard:
    """모니터링 대시보드 테스트"""

    def test_import(self):
        """모듈 임포트 테스트"""
        from src.monitoring_dashboard import EnhancedMonitoringDashboard, get_dashboard
        assert EnhancedMonitoringDashboard is not None
        assert get_dashboard is not None

    def test_dashboard_initialization(self):
        """대시보드 초기화"""
        from src.monitoring_dashboard import EnhancedMonitoringDashboard
        dashboard = EnhancedMonitoringDashboard()
        assert dashboard is not None

    def test_collect_snapshot(self):
        """스냅샷 수집 테스트"""
        from src.monitoring_dashboard import EnhancedMonitoringDashboard
        dashboard = EnhancedMonitoringDashboard()

        snapshot = dashboard.collect_snapshot()
        assert snapshot is not None
        assert hasattr(snapshot, 'timestamp')
        assert hasattr(snapshot, 'cpu_percent')

    def test_alert_manager(self):
        """경보 관리자 테스트"""
        from src.monitoring_dashboard import EnhancedMonitoringDashboard
        dashboard = EnhancedMonitoringDashboard()

        # 경보 규칙 확인
        assert len(dashboard.alert_manager.rules) > 0

        # 높은 응답 시간으로 경보 트리거
        metrics = {"avg_response_time": 15.0}  # 임계값 초과
        alerts = dashboard.alert_manager.check_rules(metrics)

        # 경보가 생성되었는지 확인
        assert len(alerts) > 0


# =============================================================================
# Finetuning Dataset Tests
# =============================================================================

class TestFinetuningDataset:
    """파인튜닝 데이터셋 테스트"""

    def test_import(self):
        """모듈 임포트 테스트"""
        from src.finetuning import CounselingDataset, DatasetConfig
        assert CounselingDataset is not None
        assert DatasetConfig is not None

    def test_sample_dataset_generation(self):
        """샘플 데이터셋 생성 테스트"""
        from src.finetuning.dataset import generate_sample_dataset

        dataset = generate_sample_dataset(n=5)
        assert len(dataset) == 5

    def test_example_format_conversion(self):
        """예시 형식 변환 테스트"""
        from src.finetuning.dataset import generate_sample_dataset

        dataset = generate_sample_dataset(n=1)
        example = dataset[0]

        # Instruction 형식
        instruction_format = example.to_instruction_format()
        assert "instruction" in instruction_format
        assert "response" in instruction_format

        # Chat 형식
        chat_format = example.to_chat_format()
        assert len(chat_format) >= 2  # system + conversation

        # SOLAR 형식
        solar_format = example.to_solar_format()
        assert "### System:" in solar_format
        assert "### User:" in solar_format


# =============================================================================
# Preprocessing Tests
# =============================================================================

class TestPreprocessing:
    """전처리 테스트"""

    def test_import(self):
        """모듈 임포트 테스트"""
        from src.finetuning.preprocessing import DataPreprocessor, QualityFilter
        assert DataPreprocessor is not None
        assert QualityFilter is not None

    def test_text_cleaner(self):
        """텍스트 정제 테스트"""
        from src.finetuning.preprocessing import TextCleaner

        # 공백 정규화
        text = "너무   많은   공백"
        cleaned = TextCleaner.clean_text(text)
        assert "   " not in cleaned

        # 개인정보 마스킹
        text_with_phone = "전화번호는 010-1234-5678이에요"
        cleaned = TextCleaner.clean_text(text_with_phone, mask_pii=True)
        assert "010-1234-5678" not in cleaned

    def test_quality_filter(self):
        """품질 필터 테스트"""
        from src.finetuning.preprocessing import QualityFilter
        from src.finetuning.dataset import CounselingExample, ConversationTurn

        quality_filter = QualityFilter()

        # 유효한 예시
        valid_example = CounselingExample(
            example_id="test_001",
            conversation=[
                ConversationTurn(role="user", content="오늘 기분이 안 좋아요."),
                ConversationTurn(role="assistant", content="기분이 안 좋으시군요. 많이 힘드시겠어요. 어떤 일이 있으셨나요?")
            ]
        )

        result = quality_filter.check_quality(valid_example)
        assert result.passed == True
        assert result.score >= 0.6


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """통합 테스트"""

    def test_full_pipeline_mock(self):
        """전체 파이프라인 목 테스트"""
        from src.conversation_state import ConversationStateManager
        from src.response_validator import ResponseValidator
        from src.evaluation import CounselingLLMEvaluator

        # 컴포넌트 초기화
        state_manager = ConversationStateManager()
        validator = ResponseValidator()
        evaluator = CounselingLLMEvaluator()

        # 시뮬레이션: 사용자 입력
        user_input = "요즘 너무 스트레스 받아요"

        # 1. 상태 업데이트
        state_manager.update_state(
            user_message=user_input,
            emotion="stress",
            emotion_intensity=0.7
        )

        # 2. 응답 생성 (목)
        mock_response = "많이 힘드시겠어요. 스트레스를 받고 계시다니 정말 지치셨을 것 같아요. 어떤 부분에서 스트레스를 느끼시나요?"

        # 3. 응답 검증
        validation_result = validator.validate(mock_response, {
            "crisis_level": 0,
            "emotion": "stress"
        })

        # 4. 응답 평가
        eval_result = evaluator.evaluate(mock_response, {
            "user_message": user_input,
            "emotion": "stress",
            "crisis_level": 0
        })

        # 검증
        assert state_manager.get_state().turn_count == 1
        assert validation_result.is_valid
        assert eval_result.overall_score >= 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
