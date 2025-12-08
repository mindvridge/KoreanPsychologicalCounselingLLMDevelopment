"""
Enhanced Monitoring Dashboard System
실시간 대시보드, 경보 시스템, 고급 분석 기능 제공

기능:
- 실시간 메트릭 대시보드
- 이상 탐지 및 경보
- LLM 품질 트렌드 분석
- 세션별 상세 분석
- 위기 개입 모니터링
"""

import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
from enum import Enum
import json
import statistics
import logging
import threading
from pathlib import Path

logger = logging.getLogger(__name__)


# =============================================================================
# Alert System
# =============================================================================

class AlertSeverity(Enum):
    """경보 심각도"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertType(Enum):
    """경보 유형"""
    HIGH_RESPONSE_TIME = "high_response_time"
    HIGH_CRISIS_RATE = "high_crisis_rate"
    LOW_SATISFACTION = "low_satisfaction"
    SYSTEM_OVERLOAD = "system_overload"
    LOW_EMPATHY_SCORE = "low_empathy_score"
    SAFETY_VIOLATION = "safety_violation"
    MODEL_DRIFT = "model_drift"
    SESSION_ANOMALY = "session_anomaly"


@dataclass
class Alert:
    """경보 데이터"""
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    timestamp: datetime
    metrics: Dict[str, Any]
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None


@dataclass
class AlertRule:
    """경보 규칙"""
    name: str
    alert_type: AlertType
    condition: Callable[[Dict[str, Any]], bool]
    severity: AlertSeverity
    cooldown_minutes: int = 5
    message_template: str = ""


class AlertManager:
    """경보 관리 시스템"""

    def __init__(self, max_alerts: int = 1000):
        self.alerts: deque = deque(maxlen=max_alerts)
        self.rules: List[AlertRule] = []
        self.last_alert_time: Dict[str, datetime] = {}
        self.alert_handlers: List[Callable[[Alert], None]] = []
        self._setup_default_rules()

    def _setup_default_rules(self):
        """기본 경보 규칙 설정"""

        # 응답 시간 경보
        self.add_rule(AlertRule(
            name="high_response_time",
            alert_type=AlertType.HIGH_RESPONSE_TIME,
            condition=lambda m: m.get("avg_response_time", 0) > 5.0,
            severity=AlertSeverity.WARNING,
            cooldown_minutes=5,
            message_template="평균 응답 시간이 {avg_response_time:.2f}초로 임계값(5초)을 초과했습니다."
        ))

        self.add_rule(AlertRule(
            name="critical_response_time",
            alert_type=AlertType.HIGH_RESPONSE_TIME,
            condition=lambda m: m.get("avg_response_time", 0) > 10.0,
            severity=AlertSeverity.CRITICAL,
            cooldown_minutes=2,
            message_template="평균 응답 시간이 {avg_response_time:.2f}초로 위험 수준입니다!"
        ))

        # 위기 상담 비율 경보
        self.add_rule(AlertRule(
            name="high_crisis_rate",
            alert_type=AlertType.HIGH_CRISIS_RATE,
            condition=lambda m: m.get("crisis_rate", 0) > 0.1,  # 10% 초과
            severity=AlertSeverity.WARNING,
            cooldown_minutes=10,
            message_template="위기 상담 비율이 {crisis_rate:.1%}로 높습니다. 추가 지원이 필요할 수 있습니다."
        ))

        self.add_rule(AlertRule(
            name="critical_crisis_rate",
            alert_type=AlertType.HIGH_CRISIS_RATE,
            condition=lambda m: m.get("crisis_rate", 0) > 0.2,  # 20% 초과
            severity=AlertSeverity.CRITICAL,
            cooldown_minutes=5,
            message_template="위기 상담 비율이 {crisis_rate:.1%}로 매우 높습니다! 즉시 확인이 필요합니다."
        ))

        # 사용자 만족도 경보
        self.add_rule(AlertRule(
            name="low_satisfaction",
            alert_type=AlertType.LOW_SATISFACTION,
            condition=lambda m: m.get("avg_satisfaction", 5) < 3.0,
            severity=AlertSeverity.WARNING,
            cooldown_minutes=15,
            message_template="평균 사용자 만족도가 {avg_satisfaction:.2f}로 낮습니다."
        ))

        # 시스템 부하 경보
        self.add_rule(AlertRule(
            name="system_overload",
            alert_type=AlertType.SYSTEM_OVERLOAD,
            condition=lambda m: m.get("cpu_percent", 0) > 90 or m.get("memory_percent", 0) > 90,
            severity=AlertSeverity.CRITICAL,
            cooldown_minutes=2,
            message_template="시스템 부하가 높습니다. CPU: {cpu_percent:.1f}%, 메모리: {memory_percent:.1f}%"
        ))

        # 공감 점수 경보
        self.add_rule(AlertRule(
            name="low_empathy",
            alert_type=AlertType.LOW_EMPATHY_SCORE,
            condition=lambda m: m.get("avg_empathy_score", 1) < 0.5,
            severity=AlertSeverity.WARNING,
            cooldown_minutes=15,
            message_template="평균 공감 점수가 {avg_empathy_score:.2f}로 낮습니다. 응답 품질 검토가 필요합니다."
        ))

        # 안전성 위반 경보
        self.add_rule(AlertRule(
            name="safety_violation",
            alert_type=AlertType.SAFETY_VIOLATION,
            condition=lambda m: m.get("safety_violations", 0) > 0,
            severity=AlertSeverity.EMERGENCY,
            cooldown_minutes=0,  # 즉시 알림
            message_template="안전성 위반이 {safety_violations}건 감지되었습니다! 즉시 검토가 필요합니다."
        ))

    def add_rule(self, rule: AlertRule):
        """경보 규칙 추가"""
        self.rules.append(rule)

    def add_handler(self, handler: Callable[[Alert], None]):
        """경보 핸들러 추가 (웹훅, 이메일 등)"""
        self.alert_handlers.append(handler)

    def check_rules(self, metrics: Dict[str, Any]) -> List[Alert]:
        """규칙 검사 및 경보 생성"""
        new_alerts = []

        for rule in self.rules:
            # 쿨다운 확인
            last_time = self.last_alert_time.get(rule.name)
            if last_time:
                cooldown_end = last_time + timedelta(minutes=rule.cooldown_minutes)
                if datetime.now() < cooldown_end:
                    continue

            # 조건 검사
            try:
                if rule.condition(metrics):
                    alert = self._create_alert(rule, metrics)
                    new_alerts.append(alert)
                    self.alerts.append(alert)
                    self.last_alert_time[rule.name] = datetime.now()

                    # 핸들러 호출
                    for handler in self.alert_handlers:
                        try:
                            handler(alert)
                        except Exception as e:
                            logger.error(f"Alert handler error: {e}")
            except Exception as e:
                logger.error(f"Error checking rule {rule.name}: {e}")

        return new_alerts

    def _create_alert(self, rule: AlertRule, metrics: Dict[str, Any]) -> Alert:
        """경보 생성"""
        alert_id = f"{rule.alert_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            message = rule.message_template.format(**metrics)
        except KeyError:
            message = f"Alert: {rule.name}"

        return Alert(
            alert_id=alert_id,
            alert_type=rule.alert_type,
            severity=rule.severity,
            message=message,
            timestamp=datetime.now(),
            metrics=metrics.copy()
        )

    def acknowledge_alert(self, alert_id: str, user: str) -> bool:
        """경보 확인"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                alert.acknowledged_by = user
                return True
        return False

    def resolve_alert(self, alert_id: str) -> bool:
        """경보 해결"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                return True
        return False

    def get_active_alerts(self) -> List[Alert]:
        """활성 경보 조회"""
        return [a for a in self.alerts if not a.resolved]

    def get_alerts_by_severity(self, severity: AlertSeverity) -> List[Alert]:
        """심각도별 경보 조회"""
        return [a for a in self.alerts if a.severity == severity and not a.resolved]


# =============================================================================
# Dashboard Metrics
# =============================================================================

@dataclass
class DashboardSnapshot:
    """대시보드 스냅샷"""
    timestamp: datetime

    # 실시간 메트릭
    active_sessions: int = 0
    conversations_last_hour: int = 0
    avg_response_time: float = 0.0
    p95_response_time: float = 0.0

    # 위기 상담
    crisis_detections_today: int = 0
    crisis_rate: float = 0.0
    high_risk_sessions: int = 0

    # 품질 메트릭
    avg_empathy_score: float = 0.0
    avg_safety_score: float = 0.0
    avg_satisfaction: float = 0.0

    # 시스템 상태
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    gpu_memory_gb: float = 0.0

    # 트렌드
    response_time_trend: str = "stable"  # up, down, stable
    satisfaction_trend: str = "stable"
    crisis_trend: str = "stable"


@dataclass
class SessionAnalytics:
    """세션 상세 분석"""
    session_id: str
    start_time: datetime
    duration_minutes: float
    turn_count: int

    # 감정 분석
    emotion_trajectory: List[Dict[str, Any]] = field(default_factory=list)
    dominant_emotion: str = ""
    emotion_change: float = 0.0  # -1 (악화) ~ 1 (개선)

    # 위기 정보
    crisis_events: List[Dict[str, Any]] = field(default_factory=list)
    max_crisis_level: int = 0

    # 품질 메트릭
    avg_response_time: float = 0.0
    avg_empathy_score: float = 0.0
    techniques_used: List[str] = field(default_factory=list)

    # 결과
    user_satisfaction: Optional[float] = None
    session_outcome: str = ""  # positive, neutral, negative, crisis_referred


@dataclass
class TrendAnalysis:
    """트렌드 분석"""
    metric_name: str
    period: str  # hourly, daily, weekly
    values: List[float] = field(default_factory=list)
    timestamps: List[datetime] = field(default_factory=list)

    # 통계
    current_value: float = 0.0
    previous_value: float = 0.0
    change_percent: float = 0.0
    trend_direction: str = "stable"  # up, down, stable

    # 예측
    predicted_next: Optional[float] = None
    confidence: float = 0.0


# =============================================================================
# Enhanced Dashboard
# =============================================================================

class EnhancedMonitoringDashboard:
    """강화된 모니터링 대시보드"""

    def __init__(
        self,
        update_interval_seconds: int = 30,
        history_retention_hours: int = 168  # 1주일
    ):
        self.update_interval = update_interval_seconds
        self.history_retention = history_retention_hours

        # 메트릭 히스토리
        self.snapshots: deque = deque(maxlen=history_retention_hours * 120)  # 30초 간격
        self.session_analytics: Dict[str, SessionAnalytics] = {}
        self.trend_cache: Dict[str, TrendAnalysis] = {}

        # 경보 관리자
        self.alert_manager = AlertManager()

        # 실시간 업데이트를 위한 콜백
        self.update_callbacks: List[Callable[[DashboardSnapshot], None]] = []

        # 백그라운드 업데이트 스레드
        self._running = False
        self._update_thread: Optional[threading.Thread] = None

        logger.info("EnhancedMonitoringDashboard initialized")

    def start_background_updates(self):
        """백그라운드 업데이트 시작"""
        if self._running:
            return

        self._running = True
        self._update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self._update_thread.start()
        logger.info("Background dashboard updates started")

    def stop_background_updates(self):
        """백그라운드 업데이트 중지"""
        self._running = False
        if self._update_thread:
            self._update_thread.join(timeout=5)
        logger.info("Background dashboard updates stopped")

    def _update_loop(self):
        """백그라운드 업데이트 루프"""
        while self._running:
            try:
                snapshot = self.collect_snapshot()
                self.snapshots.append(snapshot)

                # 경보 규칙 체크
                metrics = self._snapshot_to_metrics(snapshot)
                self.alert_manager.check_rules(metrics)

                # 콜백 호출
                for callback in self.update_callbacks:
                    try:
                        callback(snapshot)
                    except Exception as e:
                        logger.error(f"Dashboard callback error: {e}")

                time.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Dashboard update error: {e}")
                time.sleep(self.update_interval)

    def _snapshot_to_metrics(self, snapshot: DashboardSnapshot) -> Dict[str, Any]:
        """스냅샷을 메트릭 딕셔너리로 변환"""
        return asdict(snapshot)

    def collect_snapshot(self) -> DashboardSnapshot:
        """현재 스냅샷 수집"""
        import psutil
        import torch

        snapshot = DashboardSnapshot(timestamp=datetime.now())

        try:
            # 시스템 메트릭
            snapshot.cpu_percent = psutil.cpu_percent()
            snapshot.memory_percent = psutil.virtual_memory().percent

            if torch.cuda.is_available():
                snapshot.gpu_memory_gb = torch.cuda.memory_allocated() / 1024**3
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

        # 기타 메트릭은 외부에서 업데이트됨
        return snapshot

    def update_conversation_metrics(
        self,
        session_id: str,
        response_time: float,
        crisis_detected: bool,
        crisis_level: Optional[int],
        empathy_score: float,
        safety_score: float,
        emotion_data: Optional[Dict[str, Any]] = None,
        technique_used: Optional[str] = None
    ):
        """대화 메트릭 업데이트"""
        # 세션 분석 업데이트/생성
        if session_id not in self.session_analytics:
            self.session_analytics[session_id] = SessionAnalytics(
                session_id=session_id,
                start_time=datetime.now(),
                duration_minutes=0,
                turn_count=0
            )

        analytics = self.session_analytics[session_id]
        analytics.turn_count += 1
        analytics.duration_minutes = (datetime.now() - analytics.start_time).total_seconds() / 60

        # 응답 시간 업데이트
        if analytics.avg_response_time == 0:
            analytics.avg_response_time = response_time
        else:
            analytics.avg_response_time = (
                analytics.avg_response_time * (analytics.turn_count - 1) + response_time
            ) / analytics.turn_count

        # 공감 점수 업데이트
        if analytics.avg_empathy_score == 0:
            analytics.avg_empathy_score = empathy_score
        else:
            analytics.avg_empathy_score = (
                analytics.avg_empathy_score * (analytics.turn_count - 1) + empathy_score
            ) / analytics.turn_count

        # 위기 이벤트 기록
        if crisis_detected:
            analytics.crisis_events.append({
                "timestamp": datetime.now().isoformat(),
                "level": crisis_level
            })
            if crisis_level and crisis_level > analytics.max_crisis_level:
                analytics.max_crisis_level = crisis_level

        # 감정 궤적
        if emotion_data:
            analytics.emotion_trajectory.append({
                "timestamp": datetime.now().isoformat(),
                **emotion_data
            })

        # 사용 기법
        if technique_used and technique_used not in analytics.techniques_used:
            analytics.techniques_used.append(technique_used)

    def update_satisfaction(self, session_id: str, rating: float):
        """만족도 업데이트"""
        if session_id in self.session_analytics:
            self.session_analytics[session_id].user_satisfaction = rating

    def get_current_dashboard(self) -> Dict[str, Any]:
        """현재 대시보드 데이터 반환"""
        if not self.snapshots:
            snapshot = self.collect_snapshot()
        else:
            snapshot = self.snapshots[-1]

        # 활성 경보
        active_alerts = self.alert_manager.get_active_alerts()

        # 세션 요약
        active_sessions = [
            a for a in self.session_analytics.values()
            if (datetime.now() - a.start_time).total_seconds() < 3600  # 1시간 이내
        ]

        return {
            "timestamp": snapshot.timestamp.isoformat(),
            "realtime_metrics": asdict(snapshot),
            "alerts": {
                "active_count": len(active_alerts),
                "by_severity": {
                    "emergency": len([a for a in active_alerts if a.severity == AlertSeverity.EMERGENCY]),
                    "critical": len([a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]),
                    "warning": len([a for a in active_alerts if a.severity == AlertSeverity.WARNING]),
                    "info": len([a for a in active_alerts if a.severity == AlertSeverity.INFO])
                },
                "recent": [
                    {
                        "id": a.alert_id,
                        "type": a.alert_type.value,
                        "severity": a.severity.value,
                        "message": a.message,
                        "timestamp": a.timestamp.isoformat()
                    }
                    for a in list(active_alerts)[:5]
                ]
            },
            "sessions": {
                "active_count": len(active_sessions),
                "avg_duration_minutes": (
                    sum(s.duration_minutes for s in active_sessions) / len(active_sessions)
                    if active_sessions else 0
                ),
                "crisis_sessions": len([s for s in active_sessions if s.max_crisis_level >= 3]),
                "high_empathy_sessions": len([s for s in active_sessions if s.avg_empathy_score >= 0.7])
            }
        }

    def get_trend_analysis(
        self,
        metric_name: str,
        period: str = "hourly"
    ) -> TrendAnalysis:
        """트렌드 분석"""
        cache_key = f"{metric_name}_{period}"

        # 캐시 확인 (5분)
        if cache_key in self.trend_cache:
            cached = self.trend_cache[cache_key]
            cache_age = (datetime.now() - cached.timestamps[-1]).total_seconds() if cached.timestamps else float('inf')
            if cache_age < 300:
                return cached

        # 기간별 데이터 추출
        if period == "hourly":
            lookback = timedelta(hours=24)
            bucket_minutes = 60
        elif period == "daily":
            lookback = timedelta(days=7)
            bucket_minutes = 1440  # 24시간
        else:  # weekly
            lookback = timedelta(weeks=4)
            bucket_minutes = 10080  # 1주일

        cutoff = datetime.now() - lookback
        relevant_snapshots = [s for s in self.snapshots if s.timestamp > cutoff]

        if not relevant_snapshots:
            return TrendAnalysis(metric_name=metric_name, period=period)

        # 버킷별 집계
        buckets: Dict[str, List[float]] = defaultdict(list)

        for snapshot in relevant_snapshots:
            bucket_key = snapshot.timestamp.strftime("%Y-%m-%d %H:00" if period == "hourly" else "%Y-%m-%d")
            value = getattr(snapshot, metric_name, 0)
            if value is not None:
                buckets[bucket_key].append(value)

        # 평균 계산
        values = []
        timestamps = []
        for key in sorted(buckets.keys()):
            values.append(statistics.mean(buckets[key]))
            timestamps.append(datetime.strptime(key, "%Y-%m-%d %H:00" if period == "hourly" else "%Y-%m-%d"))

        if len(values) < 2:
            return TrendAnalysis(
                metric_name=metric_name,
                period=period,
                values=values,
                timestamps=timestamps,
                current_value=values[-1] if values else 0
            )

        # 트렌드 계산
        current_value = values[-1]
        previous_value = values[-2]
        change_percent = ((current_value - previous_value) / previous_value * 100) if previous_value != 0 else 0

        # 방향 판단
        if change_percent > 5:
            trend_direction = "up"
        elif change_percent < -5:
            trend_direction = "down"
        else:
            trend_direction = "stable"

        # 간단한 선형 예측
        predicted_next = None
        if len(values) >= 3:
            recent_changes = [values[i] - values[i-1] for i in range(1, len(values))]
            avg_change = statistics.mean(recent_changes[-3:])
            predicted_next = current_value + avg_change

        analysis = TrendAnalysis(
            metric_name=metric_name,
            period=period,
            values=values,
            timestamps=timestamps,
            current_value=current_value,
            previous_value=previous_value,
            change_percent=change_percent,
            trend_direction=trend_direction,
            predicted_next=predicted_next,
            confidence=0.7 if len(values) >= 5 else 0.4
        )

        self.trend_cache[cache_key] = analysis
        return analysis

    def get_session_detail(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 상세 정보"""
        if session_id not in self.session_analytics:
            return None

        analytics = self.session_analytics[session_id]

        # 감정 변화 계산
        emotion_change = 0.0
        if len(analytics.emotion_trajectory) >= 2:
            first_valence = analytics.emotion_trajectory[0].get("valence", 0)
            last_valence = analytics.emotion_trajectory[-1].get("valence", 0)
            emotion_change = last_valence - first_valence

        return {
            "session_id": analytics.session_id,
            "start_time": analytics.start_time.isoformat(),
            "duration_minutes": round(analytics.duration_minutes, 1),
            "turn_count": analytics.turn_count,
            "emotion": {
                "trajectory": analytics.emotion_trajectory,
                "change": emotion_change,
                "improved": emotion_change > 0.1
            },
            "crisis": {
                "events": analytics.crisis_events,
                "max_level": analytics.max_crisis_level,
                "count": len(analytics.crisis_events)
            },
            "quality": {
                "avg_response_time": round(analytics.avg_response_time, 2),
                "avg_empathy_score": round(analytics.avg_empathy_score, 2),
                "techniques_used": analytics.techniques_used
            },
            "outcome": {
                "satisfaction": analytics.user_satisfaction,
                "status": analytics.session_outcome
            }
        }

    def get_crisis_monitor(self) -> Dict[str, Any]:
        """위기 상담 모니터링"""
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # 오늘의 위기 세션
        crisis_sessions = [
            s for s in self.session_analytics.values()
            if s.start_time >= today_start and s.max_crisis_level > 0
        ]

        # 레벨별 분류
        by_level = defaultdict(list)
        for session in crisis_sessions:
            by_level[session.max_crisis_level].append(session)

        # 현재 진행 중인 고위험 세션
        active_high_risk = [
            s for s in crisis_sessions
            if s.max_crisis_level >= 3 and (now - s.start_time).total_seconds() < 3600
        ]

        return {
            "timestamp": now.isoformat(),
            "today_summary": {
                "total_crisis_sessions": len(crisis_sessions),
                "by_level": {
                    level: len(sessions) for level, sessions in sorted(by_level.items())
                },
                "active_high_risk_count": len(active_high_risk)
            },
            "active_high_risk_sessions": [
                {
                    "session_id": s.session_id,
                    "max_level": s.max_crisis_level,
                    "duration_minutes": round((now - s.start_time).total_seconds() / 60, 1),
                    "crisis_events_count": len(s.crisis_events)
                }
                for s in active_high_risk
            ],
            "recommendations": self._get_crisis_recommendations(crisis_sessions)
        }

    def _get_crisis_recommendations(self, crisis_sessions: List[SessionAnalytics]) -> List[str]:
        """위기 상담 관련 권장사항"""
        recommendations = []

        high_risk_count = len([s for s in crisis_sessions if s.max_crisis_level >= 4])
        if high_risk_count >= 3:
            recommendations.append("오늘 고위험 상담이 3건 이상입니다. 전문 상담사 대기를 권장합니다.")

        recent_crisis = len([
            s for s in crisis_sessions
            if (datetime.now() - s.start_time).total_seconds() < 1800  # 30분
        ])
        if recent_crisis >= 2:
            recommendations.append("최근 30분간 위기 상담이 집중되고 있습니다. 추가 리소스 배치를 고려하세요.")

        if not recommendations:
            recommendations.append("현재 위기 상담 상황은 정상 범위입니다.")

        return recommendations

    def generate_summary_report(self, period: str = "daily") -> Dict[str, Any]:
        """요약 리포트 생성"""
        now = datetime.now()

        if period == "daily":
            start = now - timedelta(days=1)
        elif period == "weekly":
            start = now - timedelta(weeks=1)
        else:
            start = now - timedelta(hours=1)

        # 관련 스냅샷
        snapshots = [s for s in self.snapshots if s.timestamp >= start]

        if not snapshots:
            return {"error": "No data available for the specified period"}

        # 관련 세션
        sessions = [
            s for s in self.session_analytics.values()
            if s.start_time >= start
        ]

        # 통계 계산
        response_times = [s.avg_response_time for s in snapshots if s.avg_response_time > 0]
        empathy_scores = [s.avg_empathy_score for s in snapshots if s.avg_empathy_score > 0]
        satisfaction_scores = [s.avg_satisfaction for s in snapshots if s.avg_satisfaction > 0]

        report = {
            "period": period,
            "start": start.isoformat(),
            "end": now.isoformat(),
            "overview": {
                "total_sessions": len(sessions),
                "total_turns": sum(s.turn_count for s in sessions),
                "total_crisis_sessions": len([s for s in sessions if s.max_crisis_level > 0]),
                "avg_session_duration_minutes": round(
                    statistics.mean([s.duration_minutes for s in sessions]) if sessions else 0, 1
                )
            },
            "performance": {
                "avg_response_time": round(statistics.mean(response_times) if response_times else 0, 2),
                "p95_response_time": round(
                    sorted(response_times)[int(len(response_times) * 0.95)] if len(response_times) >= 20 else 0, 2
                ),
                "max_response_time": round(max(response_times) if response_times else 0, 2)
            },
            "quality": {
                "avg_empathy_score": round(statistics.mean(empathy_scores) if empathy_scores else 0, 2),
                "avg_satisfaction": round(statistics.mean(satisfaction_scores) if satisfaction_scores else 0, 2),
                "satisfaction_response_rate": round(
                    len([s for s in sessions if s.user_satisfaction]) / len(sessions) * 100 if sessions else 0, 1
                )
            },
            "crisis": {
                "total_events": sum(len(s.crisis_events) for s in sessions),
                "high_risk_sessions": len([s for s in sessions if s.max_crisis_level >= 4]),
                "by_level": dict(sorted({
                    level: len([s for s in sessions if s.max_crisis_level == level])
                    for level in range(1, 6)
                }.items()))
            },
            "alerts": {
                "total_triggered": len([a for a in self.alert_manager.alerts if a.timestamp >= start]),
                "by_severity": {
                    sev.value: len([
                        a for a in self.alert_manager.alerts
                        if a.timestamp >= start and a.severity == sev
                    ])
                    for sev in AlertSeverity
                }
            },
            "trends": {
                "response_time": self.get_trend_analysis("avg_response_time", "hourly").trend_direction,
                "satisfaction": self.get_trend_analysis("avg_satisfaction", "hourly").trend_direction,
                "crisis_rate": self.get_trend_analysis("crisis_rate", "hourly").trend_direction
            }
        }

        return report

    def export_dashboard_data(self, filepath: Path, format: str = "json") -> None:
        """대시보드 데이터 내보내기"""
        data = {
            "exported_at": datetime.now().isoformat(),
            "snapshots": [asdict(s) for s in self.snapshots],
            "session_analytics": {
                sid: asdict(analytics)
                for sid, analytics in self.session_analytics.items()
            },
            "alerts": [asdict(a) for a in self.alert_manager.alerts],
            "summary": self.generate_summary_report("daily")
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"Dashboard data exported to {filepath}")


# =============================================================================
# API 연동용 함수들
# =============================================================================

_dashboard: Optional[EnhancedMonitoringDashboard] = None


def get_dashboard() -> EnhancedMonitoringDashboard:
    """글로벌 대시보드 인스턴스 반환"""
    global _dashboard
    if _dashboard is None:
        _dashboard = EnhancedMonitoringDashboard()
    return _dashboard


def init_dashboard(
    update_interval_seconds: int = 30,
    history_retention_hours: int = 168,
    start_updates: bool = True
) -> EnhancedMonitoringDashboard:
    """대시보드 초기화"""
    global _dashboard
    _dashboard = EnhancedMonitoringDashboard(
        update_interval_seconds=update_interval_seconds,
        history_retention_hours=history_retention_hours
    )

    if start_updates:
        _dashboard.start_background_updates()

    return _dashboard


# =============================================================================
# FastAPI 라우터 (선택적)
# =============================================================================

def create_dashboard_router():
    """FastAPI 라우터 생성"""
    try:
        from fastapi import APIRouter, HTTPException
        from fastapi.responses import JSONResponse
    except ImportError:
        logger.warning("FastAPI not installed, dashboard router not available")
        return None

    router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

    @router.get("/")
    async def get_dashboard_data():
        """현재 대시보드 데이터"""
        dashboard = get_dashboard()
        return dashboard.get_current_dashboard()

    @router.get("/trends/{metric_name}")
    async def get_metric_trend(metric_name: str, period: str = "hourly"):
        """메트릭 트렌드"""
        dashboard = get_dashboard()
        trend = dashboard.get_trend_analysis(metric_name, period)
        return asdict(trend)

    @router.get("/sessions/{session_id}")
    async def get_session_details(session_id: str):
        """세션 상세"""
        dashboard = get_dashboard()
        detail = dashboard.get_session_detail(session_id)
        if not detail:
            raise HTTPException(status_code=404, detail="Session not found")
        return detail

    @router.get("/crisis")
    async def get_crisis_monitor():
        """위기 모니터링"""
        dashboard = get_dashboard()
        return dashboard.get_crisis_monitor()

    @router.get("/alerts")
    async def get_alerts(resolved: bool = False):
        """경보 목록"""
        dashboard = get_dashboard()
        if resolved:
            alerts = list(dashboard.alert_manager.alerts)
        else:
            alerts = dashboard.alert_manager.get_active_alerts()
        return {"alerts": [asdict(a) for a in alerts]}

    @router.post("/alerts/{alert_id}/acknowledge")
    async def acknowledge_alert(alert_id: str, user: str = "admin"):
        """경보 확인"""
        dashboard = get_dashboard()
        success = dashboard.alert_manager.acknowledge_alert(alert_id, user)
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        return {"status": "acknowledged"}

    @router.post("/alerts/{alert_id}/resolve")
    async def resolve_alert(alert_id: str):
        """경보 해결"""
        dashboard = get_dashboard()
        success = dashboard.alert_manager.resolve_alert(alert_id)
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        return {"status": "resolved"}

    @router.get("/report/{period}")
    async def get_report(period: str = "daily"):
        """리포트 생성"""
        if period not in ["hourly", "daily", "weekly"]:
            raise HTTPException(status_code=400, detail="Invalid period")
        dashboard = get_dashboard()
        return dashboard.generate_summary_report(period)

    return router
