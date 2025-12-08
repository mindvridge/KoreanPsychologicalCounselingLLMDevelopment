"""
A/B 테스트 프레임워크 (Experiment Framework)
프롬프트, 모델 설정 등 다양한 변형을 실험하고 비교

기능:
- 실험 생성 및 관리
- 트래픽 분배 (해시 기반 일관된 할당)
- 메트릭 수집 및 분석
- 통계적 유의성 검정
- 실험 리포트 생성
"""

import logging
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import random
import math

logger = logging.getLogger(__name__)


class ExperimentStatus(Enum):
    """실험 상태"""
    DRAFT = "draft"       # 초안
    RUNNING = "running"   # 진행 중
    PAUSED = "paused"     # 일시정지
    COMPLETED = "completed"  # 완료
    ARCHIVED = "archived"    # 보관


@dataclass
class ExperimentVariant:
    """실험 변형"""
    name: str
    config: Dict[str, Any]
    traffic_percentage: float  # 0-1
    description: str = ""


@dataclass
class ExperimentMetrics:
    """실험 메트릭"""
    variant: str
    timestamp: datetime
    metric_type: str  # rating, completion, crisis_handling, etc.
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Experiment:
    """실험 정의"""
    experiment_id: str
    name: str
    description: str
    variants: List[ExperimentVariant]
    status: ExperimentStatus = ExperimentStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    metrics: List[ExperimentMetrics] = field(default_factory=list)
    target_sample_size: int = 100
    min_detectable_effect: float = 0.1  # 10% 효과 감지 목표

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "experiment_id": self.experiment_id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "variants": [
                {
                    "name": v.name,
                    "traffic_percentage": v.traffic_percentage,
                    "description": v.description
                }
                for v in self.variants
            ],
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "metrics_count": len(self.metrics),
            "sample_count": self._get_sample_counts()
        }

    def _get_sample_counts(self) -> Dict[str, int]:
        """변형별 샘플 수"""
        counts = defaultdict(int)
        for metric in self.metrics:
            counts[metric.variant] += 1
        return dict(counts)


class ExperimentManager:
    """
    실험 관리자

    A/B 테스트 실험을 생성, 관리, 분석합니다.
    """

    def __init__(self):
        """초기화"""
        self.experiments: Dict[str, Experiment] = {}
        self.user_assignments: Dict[str, Dict[str, str]] = {}  # user_id -> {exp_id: variant}

        logger.info("ExperimentManager initialized")

    def create_experiment(
        self,
        name: str,
        description: str,
        variants: List[Dict[str, Any]],
        target_sample_size: int = 100
    ) -> Experiment:
        """
        실험 생성

        Args:
            name: 실험 이름
            description: 설명
            variants: 변형 목록 [{"name": str, "config": dict, "traffic": float}, ...]
            target_sample_size: 목표 샘플 수

        Returns:
            Experiment: 생성된 실험
        """
        # 트래픽 합계 검증
        total_traffic = sum(v.get("traffic", 0.5) for v in variants)
        if abs(total_traffic - 1.0) > 0.01:
            raise ValueError(f"Traffic percentages must sum to 1.0, got {total_traffic}")

        experiment_id = f"exp_{name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        variant_objects = [
            ExperimentVariant(
                name=v["name"],
                config=v.get("config", {}),
                traffic_percentage=v.get("traffic", 1.0 / len(variants)),
                description=v.get("description", "")
            )
            for v in variants
        ]

        experiment = Experiment(
            experiment_id=experiment_id,
            name=name,
            description=description,
            variants=variant_objects,
            target_sample_size=target_sample_size
        )

        self.experiments[experiment_id] = experiment
        logger.info(f"Experiment created: {experiment_id}")

        return experiment

    def start_experiment(self, experiment_id: str) -> bool:
        """실험 시작"""
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return False

        experiment.status = ExperimentStatus.RUNNING
        experiment.started_at = datetime.now()
        logger.info(f"Experiment started: {experiment_id}")
        return True

    def stop_experiment(self, experiment_id: str) -> bool:
        """실험 종료"""
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return False

        experiment.status = ExperimentStatus.COMPLETED
        experiment.ended_at = datetime.now()
        logger.info(f"Experiment stopped: {experiment_id}")
        return True

    def assign_variant(
        self,
        experiment_id: str,
        user_id: str
    ) -> Optional[ExperimentVariant]:
        """
        사용자에게 변형 할당

        해시 기반으로 일관된 할당을 보장합니다.

        Args:
            experiment_id: 실험 ID
            user_id: 사용자 ID

        Returns:
            ExperimentVariant: 할당된 변형 (또는 None)
        """
        experiment = self.experiments.get(experiment_id)
        if not experiment or experiment.status != ExperimentStatus.RUNNING:
            return None

        # 캐시된 할당 확인
        if user_id in self.user_assignments:
            if experiment_id in self.user_assignments[user_id]:
                variant_name = self.user_assignments[user_id][experiment_id]
                return next(
                    (v for v in experiment.variants if v.name == variant_name),
                    None
                )

        # 해시 기반 할당 (일관성 보장)
        hash_input = f"{user_id}_{experiment_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        bucket = (hash_value % 10000) / 10000  # 0-1 범위

        cumulative = 0.0
        assigned_variant = experiment.variants[0]

        for variant in experiment.variants:
            cumulative += variant.traffic_percentage
            if bucket < cumulative:
                assigned_variant = variant
                break

        # 할당 저장
        if user_id not in self.user_assignments:
            self.user_assignments[user_id] = {}
        self.user_assignments[user_id][experiment_id] = assigned_variant.name

        logger.debug(
            f"User {user_id} assigned to variant '{assigned_variant.name}' "
            f"in experiment {experiment_id}"
        )

        return assigned_variant

    def record_metric(
        self,
        experiment_id: str,
        user_id: str,
        metric_type: str,
        value: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        메트릭 기록

        Args:
            experiment_id: 실험 ID
            user_id: 사용자 ID
            metric_type: 메트릭 유형 (rating, completion, empathy_score, etc.)
            value: 값
            metadata: 추가 메타데이터

        Returns:
            bool: 성공 여부
        """
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return False

        # 사용자의 변형 확인
        variant_name = self.user_assignments.get(user_id, {}).get(experiment_id)
        if not variant_name:
            return False

        metric = ExperimentMetrics(
            variant=variant_name,
            timestamp=datetime.now(),
            metric_type=metric_type,
            value=value,
            metadata=metadata or {}
        )

        experiment.metrics.append(metric)
        return True

    def analyze_experiment(
        self,
        experiment_id: str
    ) -> Dict[str, Any]:
        """
        실험 분석

        Args:
            experiment_id: 실험 ID

        Returns:
            Dict: 분석 결과
        """
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return {"error": "Experiment not found"}

        # 변형별 메트릭 그룹화
        variant_metrics = defaultdict(lambda: defaultdict(list))
        for metric in experiment.metrics:
            variant_metrics[metric.variant][metric.metric_type].append(metric.value)

        # 통계 계산
        results = {
            "experiment_id": experiment_id,
            "name": experiment.name,
            "status": experiment.status.value,
            "duration_hours": self._calculate_duration(experiment),
            "variants": {}
        }

        for variant in experiment.variants:
            variant_data = variant_metrics[variant.name]
            variant_stats = {
                "sample_size": sum(len(v) for v in variant_data.values()),
                "traffic_percentage": variant.traffic_percentage,
                "metrics": {}
            }

            for metric_type, values in variant_data.items():
                if values:
                    variant_stats["metrics"][metric_type] = {
                        "mean": sum(values) / len(values),
                        "std": self._std_dev(values),
                        "min": min(values),
                        "max": max(values),
                        "count": len(values)
                    }

            results["variants"][variant.name] = variant_stats

        # 유의성 검정 (A vs B 비교)
        if len(experiment.variants) == 2:
            results["comparison"] = self._compare_variants(
                experiment,
                variant_metrics
            )

        # 우승 변형 결정
        results["winner"] = self._determine_winner(results)

        return results

    def _calculate_duration(self, experiment: Experiment) -> float:
        """실험 지속 시간 (시간)"""
        if not experiment.started_at:
            return 0
        end = experiment.ended_at or datetime.now()
        return (end - experiment.started_at).total_seconds() / 3600

    def _std_dev(self, values: List[float]) -> float:
        """표준편차 계산"""
        if len(values) < 2:
            return 0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)

    def _compare_variants(
        self,
        experiment: Experiment,
        variant_metrics: Dict
    ) -> Dict[str, Any]:
        """두 변형 비교 (t-test 근사)"""
        if len(experiment.variants) != 2:
            return {}

        v1_name = experiment.variants[0].name
        v2_name = experiment.variants[1].name

        comparisons = {}

        # 각 메트릭 타입에 대해 비교
        all_metric_types = set()
        for metrics in variant_metrics.values():
            all_metric_types.update(metrics.keys())

        for metric_type in all_metric_types:
            v1_values = variant_metrics[v1_name][metric_type]
            v2_values = variant_metrics[v2_name][metric_type]

            if len(v1_values) >= 5 and len(v2_values) >= 5:
                # 평균 및 표준편차
                mean1 = sum(v1_values) / len(v1_values)
                mean2 = sum(v2_values) / len(v2_values)
                std1 = self._std_dev(v1_values)
                std2 = self._std_dev(v2_values)

                # 효과 크기 (Cohen's d 근사)
                pooled_std = math.sqrt((std1**2 + std2**2) / 2)
                effect_size = (mean2 - mean1) / pooled_std if pooled_std > 0 else 0

                # 간단한 유의성 추정 (샘플 크기 기반)
                n = min(len(v1_values), len(v2_values))
                is_significant = abs(effect_size) > 0.2 and n >= 30

                comparisons[metric_type] = {
                    f"{v1_name}_mean": round(mean1, 3),
                    f"{v2_name}_mean": round(mean2, 3),
                    "difference": round(mean2 - mean1, 3),
                    "relative_change": round((mean2 - mean1) / mean1 * 100, 1) if mean1 != 0 else 0,
                    "effect_size": round(effect_size, 3),
                    "is_significant": is_significant,
                    "better_variant": v2_name if mean2 > mean1 else v1_name
                }

        return comparisons

    def _determine_winner(self, results: Dict[str, Any]) -> Optional[str]:
        """우승 변형 결정"""
        comparison = results.get("comparison", {})
        if not comparison:
            return None

        # 주요 메트릭 우선순위
        priority_metrics = ["rating", "empathy_score", "completion_rate"]

        for metric in priority_metrics:
            if metric in comparison:
                comp = comparison[metric]
                if comp.get("is_significant"):
                    return comp.get("better_variant")

        return None

    def generate_report(self, experiment_id: str) -> str:
        """
        실험 리포트 생성

        Args:
            experiment_id: 실험 ID

        Returns:
            str: 마크다운 리포트
        """
        analysis = self.analyze_experiment(experiment_id)
        if "error" in analysis:
            return f"# Error\n{analysis['error']}"

        report = [
            f"# A/B 테스트 리포트: {analysis['name']}",
            f"\n**실험 ID**: {analysis['experiment_id']}",
            f"**상태**: {analysis['status']}",
            f"**진행 시간**: {analysis['duration_hours']:.1f} 시간",
            "",
            "## 변형별 결과"
        ]

        for variant_name, data in analysis["variants"].items():
            report.append(f"\n### {variant_name}")
            report.append(f"- 샘플 수: {data['sample_size']}")
            report.append(f"- 트래픽 비율: {data['traffic_percentage']*100:.0f}%")

            if data["metrics"]:
                report.append("\n**메트릭**:")
                for metric_name, stats in data["metrics"].items():
                    report.append(
                        f"- {metric_name}: 평균 {stats['mean']:.3f} "
                        f"(± {stats['std']:.3f}), n={stats['count']}"
                    )

        if analysis.get("comparison"):
            report.append("\n## 변형 비교")
            for metric_name, comp in analysis["comparison"].items():
                report.append(f"\n### {metric_name}")
                for k, v in comp.items():
                    report.append(f"- {k}: {v}")

        if analysis.get("winner"):
            report.append(f"\n## 결론")
            report.append(f"**우승 변형**: {analysis['winner']}")
        else:
            report.append("\n## 결론")
            report.append("아직 통계적으로 유의미한 차이가 감지되지 않았습니다.")

        return "\n".join(report)


class PromptExperiment:
    """
    프롬프트 A/B 테스트

    다양한 시스템 프롬프트를 비교 테스트합니다.
    """

    def __init__(self, experiment_manager: ExperimentManager):
        """
        초기화

        Args:
            experiment_manager: 실험 관리자
        """
        self.manager = experiment_manager

    def create_prompt_experiment(
        self,
        name: str,
        prompt_variants: Dict[str, str],
        traffic_split: Optional[Dict[str, float]] = None
    ) -> Experiment:
        """
        프롬프트 실험 생성

        Args:
            name: 실험 이름
            prompt_variants: {"variant_name": "prompt_text", ...}
            traffic_split: {"variant_name": 0.5, ...}

        Returns:
            Experiment: 생성된 실험
        """
        if traffic_split is None:
            # 균등 분배
            n = len(prompt_variants)
            traffic_split = {k: 1.0/n for k in prompt_variants.keys()}

        variants = [
            {
                "name": name,
                "config": {"prompt": prompt},
                "traffic": traffic_split.get(name, 0.5),
                "description": f"프롬프트 변형: {name}"
            }
            for name, prompt in prompt_variants.items()
        ]

        return self.manager.create_experiment(
            name=name,
            description=f"프롬프트 A/B 테스트: {', '.join(prompt_variants.keys())}",
            variants=variants
        )

    def get_prompt_for_user(
        self,
        experiment_id: str,
        user_id: str
    ) -> Optional[str]:
        """
        사용자에게 할당된 프롬프트 반환

        Args:
            experiment_id: 실험 ID
            user_id: 사용자 ID

        Returns:
            str: 할당된 프롬프트 (또는 None)
        """
        variant = self.manager.assign_variant(experiment_id, user_id)
        if variant:
            return variant.config.get("prompt")
        return None


# 전역 실험 관리자
_experiment_manager: Optional[ExperimentManager] = None


def get_experiment_manager() -> ExperimentManager:
    """실험 관리자 싱글톤"""
    global _experiment_manager
    if _experiment_manager is None:
        _experiment_manager = ExperimentManager()
    return _experiment_manager


if __name__ == "__main__":
    # 테스트
    print("=== A/B 테스트 프레임워크 테스트 ===\n")

    manager = ExperimentManager()

    # 실험 생성
    experiment = manager.create_experiment(
        name="프롬프트 테스트",
        description="공감 표현 강화 프롬프트 vs 기본 프롬프트",
        variants=[
            {
                "name": "control",
                "config": {"prompt": "기본 프롬프트"},
                "traffic": 0.5,
                "description": "기존 프롬프트"
            },
            {
                "name": "enhanced",
                "config": {"prompt": "강화된 공감 프롬프트"},
                "traffic": 0.5,
                "description": "공감 표현 강화"
            }
        ]
    )

    print(f"실험 생성: {experiment.experiment_id}")

    # 실험 시작
    manager.start_experiment(experiment.experiment_id)

    # 시뮬레이션: 사용자 할당 및 메트릭 기록
    import random

    for i in range(50):
        user_id = f"user_{i:03d}"

        # 변형 할당
        variant = manager.assign_variant(experiment.experiment_id, user_id)
        if variant:
            # 메트릭 기록 (시뮬레이션)
            # enhanced 변형이 약간 더 좋은 성능
            base_rating = 3.5 if variant.name == "control" else 3.8
            rating = base_rating + random.uniform(-0.5, 0.5)

            manager.record_metric(
                experiment.experiment_id,
                user_id,
                "rating",
                rating
            )

            empathy_score = 0.6 if variant.name == "control" else 0.7
            empathy_score += random.uniform(-0.1, 0.1)

            manager.record_metric(
                experiment.experiment_id,
                user_id,
                "empathy_score",
                empathy_score
            )

    # 분석
    print("\n### 분석 결과")
    analysis = manager.analyze_experiment(experiment.experiment_id)
    print(json.dumps(analysis, ensure_ascii=False, indent=2, default=str))

    # 리포트
    print("\n### 리포트")
    report = manager.generate_report(experiment.experiment_id)
    print(report)
