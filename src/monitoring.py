"""
Production Monitoring System
Tracks system metrics, conversation quality, and generates reports
"""

import time
import psutil
import torch
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ConversationMetrics:
    """Metrics for a single conversation"""
    session_id: str
    timestamp: datetime
    response_time: float
    tokens_generated: int
    crisis_detected: bool
    crisis_level: Optional[int]
    user_satisfaction: Optional[float]
    therapy_technique_used: Optional[str]
    model_confidence: float


@dataclass
class SystemMetrics:
    """System resource metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    gpu_memory_used: Optional[float]
    gpu_utilization: Optional[float]
    active_sessions: int


class ProductionMonitor:
    """
    Comprehensive monitoring system for production deployment

    Tracks:
    - Response times and latency
    - Crisis detections
    - User satisfaction
    - Model performance
    - System resources
    - Conversation quality
    """

    def __init__(self, retention_days: int = 30):
        """
        Args:
            retention_days: Days to retain metrics before archiving
        """
        self.retention_days = retention_days

        # Metrics storage (in-memory, backed by database)
        self.conversation_metrics: deque = deque(maxlen=10000)
        self.system_metrics: deque = deque(maxlen=1000)

        # Aggregated metrics
        self.hourly_stats = defaultdict(lambda: {
            "response_times": [],
            "crisis_count": 0,
            "total_conversations": 0,
            "avg_satisfaction": []
        })

        # Performance tracking
        self.response_times: deque = deque(maxlen=1000)
        self.crisis_detections: List[Dict] = []
        self.user_satisfaction: deque = deque(maxlen=1000)
        self.model_performance: deque = deque(maxlen=1000)

        # Check GPU availability
        self.has_gpu = torch.cuda.is_available()

        logger.info(f"ProductionMonitor initialized (GPU: {self.has_gpu})")

    def track_conversation(
        self,
        session_id: str,
        response_time: float,
        tokens_generated: int,
        crisis_detected: bool,
        crisis_level: Optional[int] = None,
        therapy_technique: Optional[str] = None,
        model_confidence: float = 0.0
    ) -> None:
        """
        Track metrics for a single conversation turn

        Args:
            session_id: Unique session identifier
            response_time: Time taken to generate response (seconds)
            tokens_generated: Number of tokens in response
            crisis_detected: Whether crisis was detected
            crisis_level: Crisis severity (1-5 if detected)
            therapy_technique: CBT/DBT/ACT technique used
            model_confidence: Model's confidence in response (0-1)
        """
        metrics = ConversationMetrics(
            session_id=session_id,
            timestamp=datetime.now(),
            response_time=response_time,
            tokens_generated=tokens_generated,
            crisis_detected=crisis_detected,
            crisis_level=crisis_level,
            user_satisfaction=None,  # Set later via feedback
            therapy_technique_used=therapy_technique,
            model_confidence=model_confidence
        )

        self.conversation_metrics.append(metrics)
        self.response_times.append(response_time)

        if crisis_detected:
            self.crisis_detections.append({
                "session_id": session_id,
                "timestamp": datetime.now(),
                "level": crisis_level
            })
            logger.warning(f"Crisis detected in session {session_id}, level {crisis_level}")

        # Update hourly stats
        hour_key = datetime.now().strftime("%Y-%m-%d %H:00")
        self.hourly_stats[hour_key]["response_times"].append(response_time)
        self.hourly_stats[hour_key]["total_conversations"] += 1
        if crisis_detected:
            self.hourly_stats[hour_key]["crisis_count"] += 1

    def track_user_satisfaction(
        self,
        session_id: str,
        rating: float
    ) -> None:
        """
        Track user satisfaction rating

        Args:
            session_id: Session identifier
            rating: Satisfaction score (1-5)
        """
        self.user_satisfaction.append(rating)

        # Update corresponding conversation metric
        for metric in reversed(self.conversation_metrics):
            if metric.session_id == session_id:
                metric.user_satisfaction = rating
                break

        # Update hourly stats
        hour_key = datetime.now().strftime("%Y-%m-%d %H:00")
        self.hourly_stats[hour_key]["avg_satisfaction"].append(rating)

    def track_system_resources(self) -> SystemMetrics:
        """
        Track current system resource usage

        Returns:
            SystemMetrics object
        """
        # CPU and Memory
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent

        # GPU metrics (if available)
        gpu_memory_used = None
        gpu_utilization = None

        if self.has_gpu:
            try:
                gpu_memory_used = torch.cuda.memory_allocated() / 1024**3  # GB
                # GPU utilization would need nvidia-smi or similar
            except Exception as e:
                logger.error(f"Error getting GPU metrics: {e}")

        metrics = SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            gpu_memory_used=gpu_memory_used,
            gpu_utilization=gpu_utilization,
            active_sessions=len(set(m.session_id for m in self.conversation_metrics))
        )

        self.system_metrics.append(metrics)
        return metrics

    def track_conversation_quality(
        self,
        response: str,
        context: str,
        reference: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Track conversation quality metrics

        Measures:
        - Response relevance
        - Empathy score
        - Safety check
        - Therapeutic appropriateness

        Args:
            response: Generated response
            context: Conversation context
            reference: Reference response (if available)

        Returns:
            Dictionary of quality metrics
        """
        quality_metrics = {}

        # 1. Relevance (simple keyword overlap as baseline)
        context_words = set(context.lower().split())
        response_words = set(response.lower().split())
        if context_words:
            relevance = len(context_words & response_words) / len(context_words)
            quality_metrics["relevance"] = min(relevance, 1.0)

        # 2. Empathy indicators (Korean)
        empathy_keywords = [
            "힘드", "어려우", "고통", "이해",
            "공감", "함께", "지지", "괜찮"
        ]
        empathy_score = sum(1 for kw in empathy_keywords if kw in response)
        quality_metrics["empathy_score"] = min(empathy_score / 3, 1.0)

        # 3. Safety check (no harmful advice)
        unsafe_patterns = [
            "약 먹지 마", "치료 필요없",
            "혼자 해결", "참아"
        ]
        safety_violations = sum(1 for pattern in unsafe_patterns if pattern in response)
        quality_metrics["safety_score"] = 1.0 if safety_violations == 0 else 0.0

        # 4. Professional boundary check
        medical_advice_patterns = [
            "mg 드세요", "약을 중단",
            "진단하면", "병이"
        ]
        boundary_violations = sum(1 for pattern in medical_advice_patterns if pattern in response)
        quality_metrics["professional_boundary"] = 1.0 if boundary_violations == 0 else 0.0

        return quality_metrics

    def get_realtime_stats(self) -> Dict[str, Any]:
        """
        Get real-time statistics

        Returns:
            Dictionary of current metrics
        """
        now = datetime.now()
        last_hour = now - timedelta(hours=1)

        # Filter recent metrics
        recent_conversations = [
            m for m in self.conversation_metrics
            if m.timestamp > last_hour
        ]

        recent_crises = [
            c for c in self.crisis_detections
            if c["timestamp"] > last_hour
        ]

        stats = {
            "timestamp": now.isoformat(),
            "last_hour": {
                "total_conversations": len(recent_conversations),
                "avg_response_time": (
                    sum(m.response_time for m in recent_conversations) / len(recent_conversations)
                    if recent_conversations else 0
                ),
                "crisis_detections": len(recent_crises),
                "avg_satisfaction": (
                    sum(m.user_satisfaction for m in recent_conversations if m.user_satisfaction)
                    / len([m for m in recent_conversations if m.user_satisfaction])
                    if any(m.user_satisfaction for m in recent_conversations) else None
                )
            },
            "system": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "active_sessions": len(set(m.session_id for m in recent_conversations))
            }
        }

        # GPU stats
        if self.has_gpu:
            stats["system"]["gpu_memory_gb"] = torch.cuda.memory_allocated() / 1024**3

        return stats

    def generate_daily_report(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Generate comprehensive daily operational report

        Args:
            date: Date for report (default: yesterday)

        Returns:
            Daily report dictionary
        """
        if date is None:
            date = datetime.now() - timedelta(days=1)

        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        # Filter metrics for the day
        daily_conversations = [
            m for m in self.conversation_metrics
            if start_of_day <= m.timestamp < end_of_day
        ]

        daily_crises = [
            c for c in self.crisis_detections
            if start_of_day <= c["timestamp"] < end_of_day
        ]

        if not daily_conversations:
            return {
                "date": date.strftime("%Y-%m-%d"),
                "error": "No data for this date"
            }

        # Calculate statistics
        total_conversations = len(daily_conversations)
        unique_users = len(set(m.session_id for m in daily_conversations))
        avg_response_time = sum(m.response_time for m in daily_conversations) / total_conversations
        total_tokens = sum(m.tokens_generated for m in daily_conversations)

        # Satisfaction
        ratings = [m.user_satisfaction for m in daily_conversations if m.user_satisfaction]
        avg_satisfaction = sum(ratings) / len(ratings) if ratings else None

        # Crisis breakdown
        crisis_by_level = defaultdict(int)
        for crisis in daily_crises:
            crisis_by_level[crisis["level"]] += 1

        # Therapy techniques used
        techniques = [m.therapy_technique_used for m in daily_conversations if m.therapy_technique_used]
        technique_counts = defaultdict(int)
        for tech in techniques:
            technique_counts[tech] += 1

        report = {
            "date": date.strftime("%Y-%m-%d"),
            "overview": {
                "total_conversations": total_conversations,
                "unique_users": unique_users,
                "avg_conversation_length": total_conversations / unique_users if unique_users > 0 else 0,
                "total_tokens_generated": total_tokens
            },
            "performance": {
                "avg_response_time_seconds": round(avg_response_time, 3),
                "p95_response_time": round(sorted([m.response_time for m in daily_conversations])[int(len(daily_conversations) * 0.95)], 3) if daily_conversations else 0,
                "p99_response_time": round(sorted([m.response_time for m in daily_conversations])[int(len(daily_conversations) * 0.99)], 3) if daily_conversations else 0
            },
            "safety": {
                "total_crisis_detections": len(daily_crises),
                "crisis_by_level": dict(crisis_by_level),
                "crisis_rate_percent": round(len(daily_crises) / total_conversations * 100, 2)
            },
            "quality": {
                "avg_user_satisfaction": round(avg_satisfaction, 2) if avg_satisfaction else None,
                "satisfaction_responses": len(ratings),
                "response_rate_percent": round(len(ratings) / total_conversations * 100, 2)
            },
            "therapy": {
                "techniques_used": dict(technique_counts),
                "most_common_technique": max(technique_counts.items(), key=lambda x: x[1])[0] if technique_counts else None
            }
        }

        return report

    def generate_weekly_report(self) -> Dict[str, Any]:
        """
        Generate weekly report

        Returns:
            Weekly aggregated report
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        weekly_conversations = [
            m for m in self.conversation_metrics
            if start_date <= m.timestamp < end_date
        ]

        if not weekly_conversations:
            return {"error": "No data for the past week"}

        # Daily breakdown
        daily_counts = defaultdict(int)
        for m in weekly_conversations:
            day_key = m.timestamp.strftime("%Y-%m-%d")
            daily_counts[day_key] += 1

        report = {
            "period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            "total_conversations": len(weekly_conversations),
            "daily_breakdown": dict(daily_counts),
            "avg_daily_conversations": len(weekly_conversations) / 7,
            "crisis_detections": len([m for m in weekly_conversations if m.crisis_detected]),
            "avg_response_time": sum(m.response_time for m in weekly_conversations) / len(weekly_conversations)
        }

        return report

    def export_metrics(self, filepath: Path, format: str = "json") -> None:
        """
        Export metrics to file

        Args:
            filepath: Output file path
            format: Export format (json, csv)
        """
        if format == "json":
            data = {
                "exported_at": datetime.now().isoformat(),
                "conversation_metrics": [
                    asdict(m) for m in self.conversation_metrics
                ],
                "system_metrics": [
                    asdict(m) for m in self.system_metrics
                ],
                "hourly_stats": dict(self.hourly_stats)
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"Metrics exported to {filepath}")

        else:
            raise ValueError(f"Unsupported format: {format}")

    def get_prometheus_metrics(self) -> str:
        """
        Generate Prometheus-compatible metrics

        Returns:
            Metrics in Prometheus text format
        """
        stats = self.get_realtime_stats()

        metrics = []

        # Response time
        if self.response_times:
            metrics.append(f"llm_response_time_seconds {sum(self.response_times) / len(self.response_times)}")

        # Crisis detections
        recent_crises = len([c for c in self.crisis_detections if c["timestamp"] > datetime.now() - timedelta(hours=1)])
        metrics.append(f"llm_crisis_detections_total {len(self.crisis_detections)}")
        metrics.append(f"llm_crisis_detections_last_hour {recent_crises}")

        # System metrics
        metrics.append(f"llm_cpu_percent {stats['system']['cpu_percent']}")
        metrics.append(f"llm_memory_percent {stats['system']['memory_percent']}")
        metrics.append(f"llm_active_sessions {stats['system']['active_sessions']}")

        if self.has_gpu:
            metrics.append(f"llm_gpu_memory_gb {stats['system'].get('gpu_memory_gb', 0)}")

        # User satisfaction
        if self.user_satisfaction:
            metrics.append(f"llm_user_satisfaction_avg {sum(self.user_satisfaction) / len(self.user_satisfaction)}")

        return "\n".join(metrics)


# Global monitor instance
_monitor: Optional[ProductionMonitor] = None


def get_monitor() -> ProductionMonitor:
    """Get or create global monitor instance"""
    global _monitor
    if _monitor is None:
        _monitor = ProductionMonitor()
    return _monitor


def init_monitor(retention_days: int = 30) -> ProductionMonitor:
    """
    Initialize global monitor

    Args:
        retention_days: Days to retain metrics

    Returns:
        ProductionMonitor instance
    """
    global _monitor
    _monitor = ProductionMonitor(retention_days=retention_days)
    return _monitor
