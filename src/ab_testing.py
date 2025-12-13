"""
A/B 테스트 프레임워크 (A/B Testing Framework)
응답 품질 비교 평가 시스템

기능:
- 다중 프롬프트/모델 변형 테스트
- 자동 품질 점수 비교
- 통계적 유의성 검정
- 실시간 결과 트래킹
- 자동 승자 선정
"""

import random
import logging
import hashlib
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
from enum import Enum
import json

logger = logging.getLogger(__name__)


class VariantType(Enum):
    """변형 유형"""
    PROMPT = "prompt"           # 프롬프트 변형
    MODEL = "model"             # 모델 변형
    TEMPERATURE = "temperature" # 온도 파라미터 변형
    SYSTEM = "system"           # 시스템 프롬프트 변형
    POST_PROCESS = "post"       # 후처리 변형


@dataclass
class Variant:
    """A/B 테스트 변형"""
    id: str
    name: str
    variant_type: VariantType
    config: Dict[str, Any]
    weight: float = 1.0  # 트래픽 배분 가중치
    is_control: bool = False  # 컨트롤 그룹 여부

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.variant_type.value,
            "config": self.config,
            "weight": self.weight,
            "is_control": self.is_control
        }


@dataclass
class ExperimentResult:
    """실험 결과"""
    variant_id: str
    quality_score: float
    naturalness_score: float
    response_length: int
    response_time_ms: float
    user_feedback: Optional[int] = None  # 1-5 점
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExperimentSummary:
    """실험 요약"""
    experiment_id: str
    total_samples: int
    variant_stats: Dict[str, Dict[str, float]]
    winner: Optional[str]
    confidence_level: float
    is_significant: bool
    recommendation: str


class ABTestingFramework:
    """
    A/B 테스트 프레임워크

    다양한 응답 생성 전략을 비교하고
    최적의 설정을 찾습니다.
    """

    def __init__(self, min_samples_per_variant: int = 30):
        """
        초기화

        Args:
            min_samples_per_variant: 통계적 유의성을 위한 최소 샘플 수
        """
        self.experiments: Dict[str, Dict[str, Any]] = {}
        self.results: Dict[str, List[ExperimentResult]] = defaultdict(list)
        self.min_samples = min_samples_per_variant

        # 사전 정의된 변형 세트
        self.predefined_variants = self._load_predefined_variants()

        logger.info(f"ABTestingFramework initialized (min_samples={min_samples_per_variant})")

    def _load_predefined_variants(self) -> Dict[str, List[Variant]]:
        """사전 정의된 변형 세트 로드"""
        return {
            "empathy_style": [
                Variant(
                    id="empathy_direct",
                    name="직접적 공감",
                    variant_type=VariantType.PROMPT,
                    config={
                        "style": "direct",
                        "instruction": "사용자의 감정을 직접적으로 명명하고 공감하세요."
                    },
                    is_control=True
                ),
                Variant(
                    id="empathy_reflective",
                    name="반영적 공감",
                    variant_type=VariantType.PROMPT,
                    config={
                        "style": "reflective",
                        "instruction": "사용자의 말을 반영하며 감정을 탐색하세요."
                    }
                ),
                Variant(
                    id="empathy_exploratory",
                    name="탐색적 공감",
                    variant_type=VariantType.PROMPT,
                    config={
                        "style": "exploratory",
                        "instruction": "질문을 통해 사용자의 감정을 함께 탐색하세요."
                    }
                )
            ],
            "response_length": [
                Variant(
                    id="length_short",
                    name="간결 응답",
                    variant_type=VariantType.PROMPT,
                    config={
                        "max_length": 100,
                        "instruction": "1-2문장으로 간결하게 응답하세요."
                    }
                ),
                Variant(
                    id="length_medium",
                    name="중간 응답",
                    variant_type=VariantType.PROMPT,
                    config={
                        "max_length": 200,
                        "instruction": "2-3문장으로 적절히 응답하세요."
                    },
                    is_control=True
                ),
                Variant(
                    id="length_detailed",
                    name="상세 응답",
                    variant_type=VariantType.PROMPT,
                    config={
                        "max_length": 350,
                        "instruction": "3-4문장으로 충분히 공감하고 탐색하세요."
                    }
                )
            ],
            "question_strategy": [
                Variant(
                    id="question_none",
                    name="질문 없음",
                    variant_type=VariantType.PROMPT,
                    config={
                        "questions": 0,
                        "instruction": "질문 없이 공감과 반영만 하세요."
                    }
                ),
                Variant(
                    id="question_one",
                    name="질문 1개",
                    variant_type=VariantType.PROMPT,
                    config={
                        "questions": 1,
                        "instruction": "응답 끝에 열린 질문 1개를 포함하세요."
                    },
                    is_control=True
                ),
                Variant(
                    id="question_optional",
                    name="선택적 질문",
                    variant_type=VariantType.PROMPT,
                    config={
                        "questions": "optional",
                        "instruction": "필요할 때만 질문하세요."
                    }
                )
            ],
            "temperature": [
                Variant(
                    id="temp_low",
                    name="낮은 온도 (0.3)",
                    variant_type=VariantType.TEMPERATURE,
                    config={"temperature": 0.3}
                ),
                Variant(
                    id="temp_medium",
                    name="중간 온도 (0.7)",
                    variant_type=VariantType.TEMPERATURE,
                    config={"temperature": 0.7},
                    is_control=True
                ),
                Variant(
                    id="temp_high",
                    name="높은 온도 (0.9)",
                    variant_type=VariantType.TEMPERATURE,
                    config={"temperature": 0.9}
                )
            ]
        }

    def create_experiment(
        self,
        experiment_id: str,
        name: str,
        variants: List[Variant],
        description: str = ""
    ) -> Dict[str, Any]:
        """
        새 실험 생성

        Args:
            experiment_id: 실험 ID
            name: 실험 이름
            variants: 테스트할 변형 목록
            description: 실험 설명

        Returns:
            Dict: 생성된 실험 정보
        """
        if experiment_id in self.experiments:
            logger.warning(f"Experiment {experiment_id} already exists, overwriting")

        # 가중치 정규화
        total_weight = sum(v.weight for v in variants)
        for v in variants:
            v.weight = v.weight / total_weight

        experiment = {
            "id": experiment_id,
            "name": name,
            "description": description,
            "variants": {v.id: v for v in variants},
            "variant_ids": [v.id for v in variants],
            "created_at": datetime.now().isoformat(),
            "status": "running",
            "total_samples": 0
        }

        self.experiments[experiment_id] = experiment
        logger.info(f"Created experiment: {name} with {len(variants)} variants")

        return experiment

    def create_from_predefined(
        self,
        experiment_id: str,
        preset_name: str,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        사전 정의된 변형 세트로 실험 생성

        Args:
            experiment_id: 실험 ID
            preset_name: 사전 정의 세트 이름 (empathy_style, response_length 등)
            description: 실험 설명

        Returns:
            Dict: 생성된 실험 정보
        """
        if preset_name not in self.predefined_variants:
            available = list(self.predefined_variants.keys())
            raise ValueError(f"Unknown preset: {preset_name}. Available: {available}")

        variants = self.predefined_variants[preset_name]
        return self.create_experiment(
            experiment_id=experiment_id,
            name=f"{preset_name} 테스트",
            variants=variants,
            description=description or f"{preset_name} 변형 비교 실험"
        )

    def assign_variant(
        self,
        experiment_id: str,
        user_id: Optional[str] = None
    ) -> Variant:
        """
        사용자에게 변형 할당

        동일 사용자는 항상 같은 변형을 받도록 해싱 사용

        Args:
            experiment_id: 실험 ID
            user_id: 사용자 ID (없으면 랜덤)

        Returns:
            Variant: 할당된 변형
        """
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment not found: {experiment_id}")

        experiment = self.experiments[experiment_id]
        variants = experiment["variants"]
        variant_ids = experiment["variant_ids"]

        if user_id:
            # 해시 기반 일관된 할당
            hash_input = f"{experiment_id}:{user_id}"
            hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
            normalized = (hash_value % 10000) / 10000.0

            cumulative = 0.0
            for vid in variant_ids:
                variant = variants[vid]
                cumulative += variant.weight
                if normalized < cumulative:
                    return variant

        # 가중치 기반 랜덤 선택
        weights = [variants[vid].weight for vid in variant_ids]
        chosen_id = random.choices(variant_ids, weights=weights, k=1)[0]
        return variants[chosen_id]

    def record_result(
        self,
        experiment_id: str,
        variant_id: str,
        quality_score: float,
        naturalness_score: float = 0.0,
        response_length: int = 0,
        response_time_ms: float = 0.0,
        user_feedback: Optional[int] = None,
        metadata: Optional[Dict] = None
    ):
        """
        실험 결과 기록

        Args:
            experiment_id: 실험 ID
            variant_id: 변형 ID
            quality_score: 품질 점수 (0-100)
            naturalness_score: 자연스러움 점수 (0-1)
            response_length: 응답 길이
            response_time_ms: 응답 시간
            user_feedback: 사용자 피드백 (1-5)
            metadata: 추가 메타데이터
        """
        result = ExperimentResult(
            variant_id=variant_id,
            quality_score=quality_score,
            naturalness_score=naturalness_score,
            response_length=response_length,
            response_time_ms=response_time_ms,
            user_feedback=user_feedback,
            metadata=metadata or {}
        )

        self.results[experiment_id].append(result)

        # 실험 통계 업데이트
        if experiment_id in self.experiments:
            self.experiments[experiment_id]["total_samples"] += 1

    def get_experiment_stats(self, experiment_id: str) -> Dict[str, Any]:
        """
        실험 통계 조회

        Args:
            experiment_id: 실험 ID

        Returns:
            Dict: 변형별 통계
        """
        if experiment_id not in self.experiments:
            return {"error": "Experiment not found"}

        experiment = self.experiments[experiment_id]
        results = self.results[experiment_id]

        if not results:
            return {"message": "No results yet"}

        # 변형별 결과 분류
        variant_results: Dict[str, List[ExperimentResult]] = defaultdict(list)
        for r in results:
            variant_results[r.variant_id].append(r)

        stats = {}
        for variant_id, var_results in variant_results.items():
            quality_scores = [r.quality_score for r in var_results]
            naturalness_scores = [r.naturalness_score for r in var_results if r.naturalness_score]
            feedbacks = [r.user_feedback for r in var_results if r.user_feedback]
            response_times = [r.response_time_ms for r in var_results if r.response_time_ms]

            stats[variant_id] = {
                "sample_count": len(var_results),
                "quality": {
                    "mean": sum(quality_scores) / len(quality_scores),
                    "std": self._std(quality_scores),
                    "min": min(quality_scores),
                    "max": max(quality_scores)
                },
                "naturalness": {
                    "mean": sum(naturalness_scores) / len(naturalness_scores) if naturalness_scores else 0,
                    "std": self._std(naturalness_scores) if naturalness_scores else 0
                },
                "user_feedback": {
                    "mean": sum(feedbacks) / len(feedbacks) if feedbacks else 0,
                    "count": len(feedbacks)
                },
                "response_time_ms": {
                    "mean": sum(response_times) / len(response_times) if response_times else 0
                }
            }

        return {
            "experiment_id": experiment_id,
            "experiment_name": experiment["name"],
            "total_samples": len(results),
            "variants": stats
        }

    def determine_winner(
        self,
        experiment_id: str,
        metric: str = "quality",
        confidence_threshold: float = 0.95
    ) -> ExperimentSummary:
        """
        승자 결정

        Args:
            experiment_id: 실험 ID
            metric: 비교 기준 (quality, naturalness, user_feedback)
            confidence_threshold: 신뢰도 임계값

        Returns:
            ExperimentSummary: 실험 요약
        """
        stats = self.get_experiment_stats(experiment_id)

        if "error" in stats or "message" in stats:
            return ExperimentSummary(
                experiment_id=experiment_id,
                total_samples=0,
                variant_stats={},
                winner=None,
                confidence_level=0.0,
                is_significant=False,
                recommendation="데이터가 충분하지 않습니다."
            )

        variant_stats = stats["variants"]

        # 각 변형의 해당 메트릭 점수 추출
        variant_scores = {}
        for vid, vstat in variant_stats.items():
            if metric in vstat:
                variant_scores[vid] = vstat[metric]["mean"]
            elif metric == "quality":
                variant_scores[vid] = vstat.get("quality", {}).get("mean", 0)

        if not variant_scores:
            return ExperimentSummary(
                experiment_id=experiment_id,
                total_samples=stats["total_samples"],
                variant_stats=variant_stats,
                winner=None,
                confidence_level=0.0,
                is_significant=False,
                recommendation="메트릭을 계산할 수 없습니다."
            )

        # 최고 점수 변형 찾기
        sorted_variants = sorted(variant_scores.items(), key=lambda x: x[1], reverse=True)
        best_variant = sorted_variants[0][0]
        best_score = sorted_variants[0][1]

        # 통계적 유의성 검정 (간단한 방법)
        is_significant = False
        confidence = 0.0

        if len(sorted_variants) >= 2:
            second_score = sorted_variants[1][1]
            sample_count = variant_stats[best_variant]["sample_count"]

            # 샘플 수가 충분하고 차이가 의미있으면 유의함으로 판단
            if sample_count >= self.min_samples:
                score_diff = best_score - second_score
                # 5% 이상 차이나면 유의함으로 간주 (단순화)
                if metric == "quality":
                    is_significant = score_diff >= 5
                else:
                    is_significant = score_diff >= 0.05

                # 신뢰도 추정 (단순화)
                confidence = min(0.99, 0.5 + (sample_count / self.min_samples) * 0.25 + (score_diff / 20) * 0.25)

        # 권장사항 생성
        if is_significant and confidence >= confidence_threshold:
            recommendation = f"'{best_variant}' 변형이 {metric} 기준으로 우수합니다. 배포를 권장합니다."
        elif stats["total_samples"] < self.min_samples * len(variant_stats):
            recommendation = f"더 많은 샘플이 필요합니다. (현재: {stats['total_samples']}, 권장: {self.min_samples * len(variant_stats)})"
        else:
            recommendation = "변형 간 유의미한 차이가 없습니다. 추가 테스트가 필요합니다."

        return ExperimentSummary(
            experiment_id=experiment_id,
            total_samples=stats["total_samples"],
            variant_stats=variant_stats,
            winner=best_variant if is_significant else None,
            confidence_level=confidence,
            is_significant=is_significant,
            recommendation=recommendation
        )

    def _std(self, values: List[float]) -> float:
        """표준편차 계산"""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5

    def get_all_experiments(self) -> List[Dict[str, Any]]:
        """모든 실험 목록"""
        experiments_list = []
        for exp_id, exp in self.experiments.items():
            summary = self.determine_winner(exp_id)
            experiments_list.append({
                "id": exp_id,
                "name": exp["name"],
                "status": exp["status"],
                "total_samples": exp["total_samples"],
                "winner": summary.winner,
                "is_significant": summary.is_significant
            })
        return experiments_list

    def stop_experiment(self, experiment_id: str):
        """실험 중지"""
        if experiment_id in self.experiments:
            self.experiments[experiment_id]["status"] = "stopped"
            logger.info(f"Experiment stopped: {experiment_id}")

    def export_results(self, experiment_id: str) -> str:
        """결과 JSON 내보내기"""
        stats = self.get_experiment_stats(experiment_id)
        summary = self.determine_winner(experiment_id)

        export_data = {
            "experiment": self.experiments.get(experiment_id, {}),
            "statistics": stats,
            "summary": {
                "winner": summary.winner,
                "confidence": summary.confidence_level,
                "is_significant": summary.is_significant,
                "recommendation": summary.recommendation
            },
            "exported_at": datetime.now().isoformat()
        }

        return json.dumps(export_data, ensure_ascii=False, indent=2, default=str)


# =============================================================================
# 실험 편의 함수
# =============================================================================

def create_empathy_experiment(framework: ABTestingFramework) -> str:
    """공감 스타일 실험 생성"""
    framework.create_from_predefined(
        experiment_id="empathy_style_exp",
        preset_name="empathy_style",
        description="직접적 vs 반영적 vs 탐색적 공감 스타일 비교"
    )
    return "empathy_style_exp"


def create_response_length_experiment(framework: ABTestingFramework) -> str:
    """응답 길이 실험 생성"""
    framework.create_from_predefined(
        experiment_id="response_length_exp",
        preset_name="response_length",
        description="간결 vs 중간 vs 상세 응답 길이 비교"
    )
    return "response_length_exp"


# =============================================================================
# 테스트
# =============================================================================

def test_ab_framework():
    """A/B 테스트 프레임워크 테스트"""
    print("=== A/B 테스트 프레임워크 테스트 ===\n")

    framework = ABTestingFramework(min_samples_per_variant=10)

    # 실험 생성
    exp_id = create_empathy_experiment(framework)
    print(f"실험 생성됨: {exp_id}")

    # 시뮬레이션: 가상 결과 기록
    import random
    random.seed(42)

    for i in range(50):
        variant = framework.assign_variant(exp_id, user_id=f"user_{i}")

        # 변형에 따라 다른 품질 점수 시뮬레이션
        base_score = {
            "empathy_direct": 72,
            "empathy_reflective": 78,
            "empathy_exploratory": 75
        }.get(variant.id, 70)

        quality_score = base_score + random.uniform(-10, 10)
        naturalness = 0.7 + random.uniform(-0.15, 0.15)

        framework.record_result(
            experiment_id=exp_id,
            variant_id=variant.id,
            quality_score=quality_score,
            naturalness_score=naturalness,
            response_length=random.randint(100, 300),
            response_time_ms=random.uniform(200, 800)
        )

    # 결과 조회
    stats = framework.get_experiment_stats(exp_id)
    print(f"\n총 샘플: {stats['total_samples']}")
    print("\n변형별 통계:")
    for vid, vstat in stats["variants"].items():
        print(f"  {vid}: 품질={vstat['quality']['mean']:.1f}, 샘플={vstat['sample_count']}")

    # 승자 결정
    summary = framework.determine_winner(exp_id)
    print(f"\n승자: {summary.winner}")
    print(f"유의성: {summary.is_significant}")
    print(f"신뢰도: {summary.confidence_level:.2f}")
    print(f"권장: {summary.recommendation}")


if __name__ == "__main__":
    test_ab_framework()
