"""
LLM 평가 시스템 (Evaluation System)
심리상담 LLM의 응답 품질을 다각도로 평가

모듈:
- metrics: 평가 메트릭 정의
- evaluator: 종합 평가기
- benchmarks: 벤치마크 테스트 케이스
"""

from .metrics import (
    EmpathyMetric,
    SafetyMetric,
    TherapeuticAccuracyMetric,
    CulturalSensitivityMetric,
    CoherenceMetric
)

from .evaluator import (
    CounselingLLMEvaluator,
    EvaluationResult,
    evaluate_response,
    batch_evaluate
)

__all__ = [
    "EmpathyMetric",
    "SafetyMetric",
    "TherapeuticAccuracyMetric",
    "CulturalSensitivityMetric",
    "CoherenceMetric",
    "CounselingLLMEvaluator",
    "EvaluationResult",
    "evaluate_response",
    "batch_evaluate"
]
