"""
감정 추적 및 시각화 모듈 (Emotion Tracking & Visualization)
사용자의 감정 변화를 추적하고 시각화

기능:
- 실시간 감정 분석 및 기록
- 감정 변화 그래프 생성
- 주간/월간 리포트
- 감정 트렌드 분석
- 감정 패턴 인사이트
"""

import logging
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import json
import statistics

logger = logging.getLogger(__name__)


class EmotionCategory(Enum):
    """감정 카테고리"""
    JOY = "기쁨"
    SADNESS = "슬픔"
    ANGER = "분노"
    FEAR = "두려움"
    ANXIETY = "불안"
    CALM = "평온"
    HOPE = "희망"
    LONELINESS = "외로움"
    STRESS = "스트레스"
    GRATITUDE = "감사"
    NEUTRAL = "중립"


@dataclass
class EmotionRecord:
    """감정 기록"""
    timestamp: datetime
    primary_emotion: EmotionCategory
    secondary_emotion: Optional[EmotionCategory] = None
    intensity: float = 0.5  # 0.0 ~ 1.0
    valence: float = 0.0    # -1.0 (부정) ~ 1.0 (긍정)
    arousal: float = 0.5    # 0.0 (낮음) ~ 1.0 (높음)
    context: Optional[str] = None  # 대화 맥락
    session_id: Optional[str] = None
    user_text: Optional[str] = None  # 사용자 발화 (분석용)


@dataclass
class DailyEmotionSummary:
    """일별 감정 요약"""
    date: datetime
    dominant_emotion: EmotionCategory
    average_valence: float
    average_arousal: float
    emotion_distribution: Dict[str, float]  # 감정별 비율
    record_count: int
    notable_moments: List[Dict]  # 주목할 만한 순간들


@dataclass
class WeeklyReport:
    """주간 리포트"""
    start_date: datetime
    end_date: datetime
    daily_summaries: List[DailyEmotionSummary]
    overall_trend: str  # "improving", "stable", "declining"
    dominant_emotions: List[Tuple[EmotionCategory, float]]  # Top 3
    valence_trend: List[float]  # 일별 평균 valence
    insights: List[str]
    recommendations: List[str]
    total_sessions: int


class EmotionAnalyzer:
    """
    감정 분석기
    텍스트에서 감정을 추출하고 분류
    """

    # 감정 키워드 사전 (한국어)
    EMOTION_KEYWORDS = {
        EmotionCategory.JOY: [
            "기쁘", "행복", "좋아", "즐거", "신나", "웃", "설레", "뿌듯",
            "감사", "다행", "최고", "짱", "대박", "사랑", "기분 좋"
        ],
        EmotionCategory.SADNESS: [
            "슬프", "우울", "눈물", "힘들", "서글프", "외롭", "쓸쓸",
            "허전", "아프", "마음이 아", "울고 싶", "지쳐", "무기력"
        ],
        EmotionCategory.ANGER: [
            "화가", "짜증", "분노", "열받", "빡치", "억울", "답답",
            "미치", "싫", "짜증나", "화나", "불공평", "원망"
        ],
        EmotionCategory.FEAR: [
            "무섭", "두렵", "공포", "떨리", "겁", "불안", "걱정",
            "초조", "조마조마", "긴장", "안절부절"
        ],
        EmotionCategory.ANXIETY: [
            "불안", "걱정", "초조", "긴장", "조급", "안절부절", "마음이 급",
            "불확실", "막막", "답답", "조바심", "스트레스"
        ],
        EmotionCategory.CALM: [
            "평온", "편안", "차분", "안정", "여유", "느긋", "고요",
            "평화", "잔잔", "릴렉스", "쉬", "휴식"
        ],
        EmotionCategory.HOPE: [
            "희망", "기대", "설레", "꿈", "목표", "할 수 있", "가능",
            "나아지", "좋아지", "믿", "노력", "긍정"
        ],
        EmotionCategory.LONELINESS: [
            "외롭", "혼자", "쓸쓸", "고독", "소외", "아무도",
            "혼밥", "혼술", "외로", "공허", "허전"
        ],
        EmotionCategory.STRESS: [
            "스트레스", "압박", "부담", "피곤", "지쳐", "버거",
            "힘들", "벅차", "과로", "번아웃", "지침"
        ],
        EmotionCategory.GRATITUDE: [
            "감사", "고맙", "다행", "덕분", "은혜", "복",
            "행운", "감동", "정말 좋", "너무 좋"
        ]
    }

    # 감정별 valence (긍정/부정)
    EMOTION_VALENCE = {
        EmotionCategory.JOY: 0.8,
        EmotionCategory.SADNESS: -0.7,
        EmotionCategory.ANGER: -0.6,
        EmotionCategory.FEAR: -0.5,
        EmotionCategory.ANXIETY: -0.4,
        EmotionCategory.CALM: 0.3,
        EmotionCategory.HOPE: 0.6,
        EmotionCategory.LONELINESS: -0.6,
        EmotionCategory.STRESS: -0.5,
        EmotionCategory.GRATITUDE: 0.7,
        EmotionCategory.NEUTRAL: 0.0
    }

    # 감정별 arousal (활성화 수준)
    EMOTION_AROUSAL = {
        EmotionCategory.JOY: 0.7,
        EmotionCategory.SADNESS: 0.3,
        EmotionCategory.ANGER: 0.8,
        EmotionCategory.FEAR: 0.8,
        EmotionCategory.ANXIETY: 0.7,
        EmotionCategory.CALM: 0.2,
        EmotionCategory.HOPE: 0.5,
        EmotionCategory.LONELINESS: 0.3,
        EmotionCategory.STRESS: 0.7,
        EmotionCategory.GRATITUDE: 0.5,
        EmotionCategory.NEUTRAL: 0.4
    }

    def __init__(self):
        self.intensity_modifiers = {
            "너무": 1.3,
            "정말": 1.2,
            "진짜": 1.2,
            "많이": 1.2,
            "아주": 1.2,
            "매우": 1.3,
            "엄청": 1.3,
            "되게": 1.1,
            "완전": 1.3,
            "약간": 0.7,
            "조금": 0.6,
            "살짝": 0.5,
            "좀": 0.7
        }

    def analyze(self, text: str) -> EmotionRecord:
        """
        텍스트에서 감정 분석

        Args:
            text: 분석할 텍스트

        Returns:
            감정 기록
        """
        emotion_scores = defaultdict(float)

        # 키워드 매칭
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    emotion_scores[emotion] += 1.0

        # 강도 수정자 확인
        intensity_modifier = 1.0
        for modifier, multiplier in self.intensity_modifiers.items():
            if modifier in text:
                intensity_modifier = max(intensity_modifier, multiplier)

        # 주요 감정 선택
        if emotion_scores:
            sorted_emotions = sorted(
                emotion_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )
            primary = sorted_emotions[0][0]
            secondary = sorted_emotions[1][0] if len(sorted_emotions) > 1 else None

            # 강도 계산 (0.3 ~ 1.0)
            max_score = sorted_emotions[0][1]
            base_intensity = min(0.3 + (max_score * 0.2), 0.9)
            intensity = min(base_intensity * intensity_modifier, 1.0)
        else:
            primary = EmotionCategory.NEUTRAL
            secondary = None
            intensity = 0.4

        return EmotionRecord(
            timestamp=datetime.now(),
            primary_emotion=primary,
            secondary_emotion=secondary,
            intensity=intensity,
            valence=self.EMOTION_VALENCE.get(primary, 0.0),
            arousal=self.EMOTION_AROUSAL.get(primary, 0.5),
            user_text=text[:200]  # 처음 200자만 저장
        )


class EmotionTracker:
    """
    감정 추적기
    사용자별 감정 기록 관리 및 추적
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path
        self.analyzer = EmotionAnalyzer()

        # 사용자별 감정 기록 {user_id: [EmotionRecord]}
        self.records: Dict[str, List[EmotionRecord]] = defaultdict(list)

        # 로드
        if storage_path:
            self._load_records()

    def record_emotion(
        self,
        user_id: str,
        text: str,
        session_id: Optional[str] = None,
        context: Optional[str] = None
    ) -> EmotionRecord:
        """
        감정 기록 추가

        Args:
            user_id: 사용자 ID
            text: 사용자 발화
            session_id: 세션 ID
            context: 대화 맥락

        Returns:
            생성된 감정 기록
        """
        record = self.analyzer.analyze(text)
        record.session_id = session_id
        record.context = context

        self.records[user_id].append(record)

        # 자동 저장 (선택적)
        if self.storage_path and len(self.records[user_id]) % 10 == 0:
            self._save_records()

        logger.debug(f"Emotion recorded for {user_id}: {record.primary_emotion.value}")
        return record

    def get_recent_emotions(
        self,
        user_id: str,
        hours: int = 24
    ) -> List[EmotionRecord]:
        """최근 감정 기록 조회"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [
            r for r in self.records.get(user_id, [])
            if r.timestamp > cutoff
        ]

    def get_emotion_by_date(
        self,
        user_id: str,
        target_date: datetime
    ) -> List[EmotionRecord]:
        """특정 날짜의 감정 기록"""
        start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)

        return [
            r for r in self.records.get(user_id, [])
            if start <= r.timestamp < end
        ]

    def get_daily_summary(
        self,
        user_id: str,
        target_date: datetime
    ) -> Optional[DailyEmotionSummary]:
        """일별 감정 요약 생성"""
        records = self.get_emotion_by_date(user_id, target_date)

        if not records:
            return None

        # 감정 분포 계산
        emotion_counts = defaultdict(int)
        for r in records:
            emotion_counts[r.primary_emotion.value] += 1

        total = len(records)
        emotion_distribution = {
            emotion: count / total
            for emotion, count in emotion_counts.items()
        }

        # 지배적 감정
        dominant = max(emotion_counts.items(), key=lambda x: x[1])[0]
        dominant_emotion = EmotionCategory(dominant)

        # 평균 valence/arousal
        avg_valence = statistics.mean(r.valence for r in records)
        avg_arousal = statistics.mean(r.arousal for r in records)

        # 주목할 만한 순간 (강도 높은 것들)
        notable = sorted(records, key=lambda r: r.intensity, reverse=True)[:3]
        notable_moments = [
            {
                "time": r.timestamp.strftime("%H:%M"),
                "emotion": r.primary_emotion.value,
                "intensity": r.intensity,
                "context": r.context
            }
            for r in notable
        ]

        return DailyEmotionSummary(
            date=target_date,
            dominant_emotion=dominant_emotion,
            average_valence=avg_valence,
            average_arousal=avg_arousal,
            emotion_distribution=emotion_distribution,
            record_count=total,
            notable_moments=notable_moments
        )

    def _load_records(self):
        """저장된 기록 로드"""
        try:
            import os
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for user_id, records_data in data.items():
                        for rd in records_data:
                            record = EmotionRecord(
                                timestamp=datetime.fromisoformat(rd['timestamp']),
                                primary_emotion=EmotionCategory(rd['primary_emotion']),
                                secondary_emotion=EmotionCategory(rd['secondary_emotion']) if rd.get('secondary_emotion') else None,
                                intensity=rd['intensity'],
                                valence=rd['valence'],
                                arousal=rd['arousal'],
                                context=rd.get('context'),
                                session_id=rd.get('session_id'),
                                user_text=rd.get('user_text')
                            )
                            self.records[user_id].append(record)
                logger.info(f"Loaded emotion records from {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to load emotion records: {e}")

    def _save_records(self):
        """기록 저장"""
        try:
            data = {}
            for user_id, records in self.records.items():
                data[user_id] = [
                    {
                        'timestamp': r.timestamp.isoformat(),
                        'primary_emotion': r.primary_emotion.value,
                        'secondary_emotion': r.secondary_emotion.value if r.secondary_emotion else None,
                        'intensity': r.intensity,
                        'valence': r.valence,
                        'arousal': r.arousal,
                        'context': r.context,
                        'session_id': r.session_id,
                        'user_text': r.user_text
                    }
                    for r in records[-500:]  # 최근 500개만 저장
                ]

            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save emotion records: {e}")


class EmotionVisualizer:
    """
    감정 시각화 생성기
    차트 데이터 및 리포트 생성
    """

    def __init__(self, tracker: EmotionTracker):
        self.tracker = tracker

    def generate_emotion_chart_data(
        self,
        user_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        감정 변화 차트 데이터 생성

        Args:
            user_id: 사용자 ID
            days: 조회 기간 (일)

        Returns:
            차트 데이터 (JSON 형식)
        """
        labels = []
        valence_data = []
        arousal_data = []
        emotion_distribution_data = []

        for i in range(days - 1, -1, -1):
            target_date = datetime.now() - timedelta(days=i)
            summary = self.tracker.get_daily_summary(user_id, target_date)

            labels.append(target_date.strftime("%m/%d"))

            if summary:
                valence_data.append(round(summary.average_valence, 2))
                arousal_data.append(round(summary.average_arousal, 2))
                emotion_distribution_data.append(summary.emotion_distribution)
            else:
                valence_data.append(None)
                arousal_data.append(None)
                emotion_distribution_data.append({})

        return {
            "type": "emotion_timeline",
            "labels": labels,
            "datasets": [
                {
                    "label": "감정 상태 (긍정/부정)",
                    "data": valence_data,
                    "borderColor": "#4CAF50",
                    "backgroundColor": "rgba(76, 175, 80, 0.2)",
                    "fill": True
                },
                {
                    "label": "활성화 수준",
                    "data": arousal_data,
                    "borderColor": "#FF9800",
                    "backgroundColor": "rgba(255, 152, 0, 0.2)",
                    "fill": True
                }
            ],
            "emotion_distribution": emotion_distribution_data
        }

    def generate_emotion_pie_data(
        self,
        user_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        감정 분포 파이 차트 데이터
        """
        emotion_counts = defaultdict(int)

        for i in range(days):
            target_date = datetime.now() - timedelta(days=i)
            records = self.tracker.get_emotion_by_date(user_id, target_date)

            for record in records:
                emotion_counts[record.primary_emotion.value] += 1

        # 상위 6개만 표시
        sorted_emotions = sorted(
            emotion_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:6]

        colors = {
            "기쁨": "#FFD700",
            "슬픔": "#4169E1",
            "분노": "#DC143C",
            "두려움": "#800080",
            "불안": "#FFA500",
            "평온": "#90EE90",
            "희망": "#00CED1",
            "외로움": "#708090",
            "스트레스": "#FF6347",
            "감사": "#FFB6C1",
            "중립": "#C0C0C0"
        }

        return {
            "type": "emotion_distribution",
            "labels": [e[0] for e in sorted_emotions],
            "datasets": [{
                "data": [e[1] for e in sorted_emotions],
                "backgroundColor": [
                    colors.get(e[0], "#808080")
                    for e in sorted_emotions
                ]
            }]
        }

    def generate_weekly_report(
        self,
        user_id: str,
        start_date: Optional[datetime] = None
    ) -> WeeklyReport:
        """
        주간 리포트 생성

        Args:
            user_id: 사용자 ID
            start_date: 시작 날짜 (기본: 지난 주 월요일)

        Returns:
            주간 리포트
        """
        if start_date is None:
            today = datetime.now()
            start_date = today - timedelta(days=today.weekday() + 7)

        end_date = start_date + timedelta(days=6)

        # 일별 요약 수집
        daily_summaries = []
        valence_trend = []
        all_emotions = defaultdict(int)
        total_sessions = set()

        for i in range(7):
            target_date = start_date + timedelta(days=i)
            summary = self.tracker.get_daily_summary(user_id, target_date)

            if summary:
                daily_summaries.append(summary)
                valence_trend.append(summary.average_valence)

                for emotion, ratio in summary.emotion_distribution.items():
                    all_emotions[emotion] += ratio
            else:
                valence_trend.append(None)

        # 세션 수 계산
        for i in range(7):
            target_date = start_date + timedelta(days=i)
            records = self.tracker.get_emotion_by_date(user_id, target_date)
            for r in records:
                if r.session_id:
                    total_sessions.add(r.session_id)

        # 전체 트렌드 분석
        valid_valence = [v for v in valence_trend if v is not None]
        if len(valid_valence) >= 2:
            first_half = statistics.mean(valid_valence[:len(valid_valence)//2])
            second_half = statistics.mean(valid_valence[len(valid_valence)//2:])

            if second_half > first_half + 0.1:
                overall_trend = "improving"
            elif second_half < first_half - 0.1:
                overall_trend = "declining"
            else:
                overall_trend = "stable"
        else:
            overall_trend = "insufficient_data"

        # 지배적 감정 Top 3
        dominant_emotions = sorted(
            [(EmotionCategory(e), c) for e, c in all_emotions.items()],
            key=lambda x: x[1],
            reverse=True
        )[:3]

        # 인사이트 생성
        insights = self._generate_insights(
            daily_summaries,
            dominant_emotions,
            overall_trend
        )

        # 추천 생성
        recommendations = self._generate_recommendations(
            dominant_emotions,
            overall_trend,
            valid_valence
        )

        return WeeklyReport(
            start_date=start_date,
            end_date=end_date,
            daily_summaries=daily_summaries,
            overall_trend=overall_trend,
            dominant_emotions=dominant_emotions,
            valence_trend=valence_trend,
            insights=insights,
            recommendations=recommendations,
            total_sessions=len(total_sessions)
        )

    def _generate_insights(
        self,
        daily_summaries: List[DailyEmotionSummary],
        dominant_emotions: List[Tuple[EmotionCategory, float]],
        trend: str
    ) -> List[str]:
        """인사이트 생성"""
        insights = []

        if not daily_summaries:
            return ["이번 주 감정 기록이 충분하지 않습니다."]

        # 트렌드 기반 인사이트
        if trend == "improving":
            insights.append("📈 이번 주 감정 상태가 점점 좋아지고 있어요!")
        elif trend == "declining":
            insights.append("📉 이번 주 감정 상태가 조금 힘들어 보여요. 괜찮으세요?")
        elif trend == "stable":
            insights.append("➡️ 이번 주 감정 상태가 안정적으로 유지되고 있어요.")

        # 지배적 감정 기반 인사이트
        if dominant_emotions:
            top_emotion = dominant_emotions[0][0]

            if top_emotion == EmotionCategory.JOY:
                insights.append("😊 기쁨이 가장 많이 나타났어요. 좋은 일이 많았나 봐요!")
            elif top_emotion == EmotionCategory.SADNESS:
                insights.append("😢 슬픔을 많이 느끼셨네요. 힘든 일이 있으셨나요?")
            elif top_emotion == EmotionCategory.ANXIETY:
                insights.append("😰 불안감이 높았어요. 걱정되는 일이 있으신가요?")
            elif top_emotion == EmotionCategory.STRESS:
                insights.append("😫 스트레스가 많았던 한 주였네요. 충분한 휴식이 필요해요.")
            elif top_emotion == EmotionCategory.CALM:
                insights.append("😌 평온한 시간이 많았어요. 좋은 흐름이에요!")

        # 기록 빈도 기반 인사이트
        total_records = sum(s.record_count for s in daily_summaries)
        avg_daily = total_records / len(daily_summaries)

        if avg_daily >= 5:
            insights.append(f"💬 하루 평균 {avg_daily:.1f}회 대화하셨어요. 꾸준히 마음을 나누고 계시네요!")
        elif avg_daily >= 2:
            insights.append(f"💬 하루 평균 {avg_daily:.1f}회 대화하셨어요.")
        else:
            insights.append("💬 대화가 조금 적었어요. 더 자주 이야기 나눠봐요!")

        return insights

    def _generate_recommendations(
        self,
        dominant_emotions: List[Tuple[EmotionCategory, float]],
        trend: str,
        valence_values: List[float]
    ) -> List[str]:
        """추천 생성"""
        recommendations = []

        if not dominant_emotions:
            return ["정기적으로 감정을 기록하면 더 정확한 분석이 가능해요."]

        top_emotion = dominant_emotions[0][0]
        avg_valence = statistics.mean(valence_values) if valence_values else 0

        # 부정적 감정이 많은 경우
        if avg_valence < -0.3:
            recommendations.append("🌿 가벼운 산책이나 스트레칭으로 기분 전환을 해보세요.")
            recommendations.append("📝 감사 일기를 써보는 건 어떨까요? 작은 것부터 시작해요.")

        # 감정별 추천
        if top_emotion == EmotionCategory.ANXIETY:
            recommendations.append("🧘 깊은 호흡 운동을 해보세요. 4초 들이쉬고, 4초 내쉬기를 반복해요.")
            recommendations.append("📵 SNS 사용을 줄이고 현재에 집중하는 시간을 가져보세요.")
        elif top_emotion == EmotionCategory.SADNESS:
            recommendations.append("🤗 가까운 사람과 대화를 나눠보세요. 혼자 품지 마세요.")
            recommendations.append("🎵 좋아하는 음악을 들으며 감정을 표현해보세요.")
        elif top_emotion == EmotionCategory.STRESS:
            recommendations.append("⏰ 충분한 수면을 취하세요. 7-8시간이 권장됩니다.")
            recommendations.append("🚫 할 일 목록을 정리하고 우선순위를 정해보세요.")
        elif top_emotion == EmotionCategory.LONELINESS:
            recommendations.append("👥 작은 모임이나 동호회 활동을 시작해보세요.")
            recommendations.append("📞 오랜만에 친구에게 연락해보는 건 어떨까요?")
        elif top_emotion in [EmotionCategory.JOY, EmotionCategory.CALM]:
            recommendations.append("✨ 지금의 좋은 에너지를 유지하세요!")
            recommendations.append("📔 이 좋은 순간들을 기록으로 남겨두세요.")

        # 트렌드 기반 추천
        if trend == "declining":
            recommendations.append("💡 전문 상담사와의 상담도 고려해보세요. 도움을 받는 것은 용기 있는 선택이에요.")

        return recommendations[:4]  # 최대 4개

    def format_weekly_report_text(self, report: WeeklyReport) -> str:
        """주간 리포트 텍스트 포맷"""
        lines = []

        # 헤더
        lines.append(f"📊 주간 감정 리포트")
        lines.append(f"📅 {report.start_date.strftime('%Y.%m.%d')} - {report.end_date.strftime('%Y.%m.%d')}")
        lines.append("")

        # 전체 트렌드
        trend_emoji = {
            "improving": "📈 개선",
            "stable": "➡️ 안정",
            "declining": "📉 주의",
            "insufficient_data": "❓ 데이터 부족"
        }
        lines.append(f"전체 트렌드: {trend_emoji.get(report.overall_trend, '❓')}")
        lines.append(f"총 상담 세션: {report.total_sessions}회")
        lines.append("")

        # 주요 감정
        if report.dominant_emotions:
            lines.append("🎭 주요 감정:")
            for i, (emotion, _) in enumerate(report.dominant_emotions, 1):
                lines.append(f"  {i}. {emotion.value}")
            lines.append("")

        # 인사이트
        if report.insights:
            lines.append("💡 인사이트:")
            for insight in report.insights:
                lines.append(f"  • {insight}")
            lines.append("")

        # 추천
        if report.recommendations:
            lines.append("✨ 추천:")
            for rec in report.recommendations:
                lines.append(f"  • {rec}")

        return "\n".join(lines)


# 전역 인스턴스 (싱글톤)
_emotion_tracker: Optional[EmotionTracker] = None
_emotion_visualizer: Optional[EmotionVisualizer] = None


def get_emotion_tracker(storage_path: Optional[str] = None) -> EmotionTracker:
    """감정 추적기 싱글톤"""
    global _emotion_tracker
    if _emotion_tracker is None:
        _emotion_tracker = EmotionTracker(storage_path)
    return _emotion_tracker


def get_emotion_visualizer() -> EmotionVisualizer:
    """감정 시각화 싱글톤"""
    global _emotion_visualizer
    if _emotion_visualizer is None:
        _emotion_visualizer = EmotionVisualizer(get_emotion_tracker())
    return _emotion_visualizer
