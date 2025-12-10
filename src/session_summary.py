"""
세션 요약 모듈 (Session Summary)
AI 기반 상담 세션 요약 및 인사이트 생성

기능:
- 대화 내용 자동 요약
- 핵심 주제 추출
- 감정 변화 분석
- 상담 인사이트 생성
- 다음 세션 제안
"""

import logging
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import re
from collections import Counter

logger = logging.getLogger(__name__)


class TopicCategory(Enum):
    """상담 주제 카테고리"""
    RELATIONSHIP = "대인관계"
    WORK = "직장/학업"
    FAMILY = "가족"
    SELF_ESTEEM = "자존감"
    ANXIETY = "불안"
    DEPRESSION = "우울"
    STRESS = "스트레스"
    TRAUMA = "트라우마"
    LIFE_TRANSITION = "삶의 변화"
    EXISTENTIAL = "실존적 고민"
    HEALTH = "건강"
    FINANCIAL = "경제"
    OTHER = "기타"


@dataclass
class ConversationTurn:
    """대화 턴"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None
    emotion: Optional[str] = None
    importance: float = 0.5  # 0.0 ~ 1.0


@dataclass
class SessionSummary:
    """세션 요약"""
    session_id: str
    user_id: str
    start_time: datetime
    end_time: datetime
    duration_minutes: int

    # 요약
    brief_summary: str  # 2-3문장 요약
    detailed_summary: str  # 상세 요약

    # 주요 내용
    main_topics: List[Tuple[TopicCategory, float]]  # 주제 및 비중
    key_points: List[str]  # 핵심 포인트
    user_concerns: List[str]  # 사용자의 주요 고민
    counselor_suggestions: List[str]  # 상담사가 제안한 내용

    # 감정 분석
    emotional_journey: List[Dict]  # 시간별 감정 변화
    dominant_emotion: str
    emotional_shift: str  # "positive", "negative", "stable"

    # 인사이트
    insights: List[str]  # AI 생성 인사이트
    patterns_identified: List[str]  # 발견된 패턴

    # 다음 단계
    homework: List[str]  # 다음 세션까지 과제
    next_session_suggestions: List[str]  # 다음 세션 제안 주제

    # 메타데이터
    message_count: int
    user_message_count: int
    avg_response_time: Optional[float] = None


class KeywordExtractor:
    """키워드 추출기"""

    # 주제별 키워드 맵핑
    TOPIC_KEYWORDS = {
        TopicCategory.RELATIONSHIP: [
            "친구", "연인", "사람", "관계", "소통", "갈등", "다툼", "이별",
            "사랑", "외로움", "신뢰", "배신", "만남", "헤어짐"
        ],
        TopicCategory.WORK: [
            "회사", "직장", "업무", "일", "상사", "동료", "취업", "퇴사",
            "승진", "이직", "학교", "공부", "시험", "성적", "과제"
        ],
        TopicCategory.FAMILY: [
            "부모님", "어머니", "아버지", "형제", "자매", "남편", "아내",
            "자녀", "아이", "가족", "집", "결혼", "이혼"
        ],
        TopicCategory.SELF_ESTEEM: [
            "자신감", "자존감", "열등감", "비교", "못나", "못생겼", "무능",
            "가치", "존재", "인정", "칭찬", "비난"
        ],
        TopicCategory.ANXIETY: [
            "불안", "걱정", "초조", "긴장", "두려움", "공포", "무서움",
            "떨림", "심장", "식은땀", "패닉"
        ],
        TopicCategory.DEPRESSION: [
            "우울", "슬픔", "눈물", "무기력", "의욕", "흥미", "죽고 싶",
            "힘들", "지쳐", "피곤", "공허", "허무"
        ],
        TopicCategory.STRESS: [
            "스트레스", "압박", "부담", "지침", "번아웃", "과로", "피로",
            "쉬고 싶", "도망", "벗어나고"
        ],
        TopicCategory.TRAUMA: [
            "트라우마", "사고", "폭력", "학대", "왕따", "따돌림", "괴롭힘",
            "악몽", "플래시백", "공황"
        ],
        TopicCategory.LIFE_TRANSITION: [
            "변화", "전환", "새로운", "시작", "끝", "졸업", "입학",
            "출산", "은퇴", "이사"
        ],
        TopicCategory.EXISTENTIAL: [
            "의미", "목적", "왜 사는지", "인생", "삶", "죽음", "미래",
            "방향", "길", "선택"
        ],
        TopicCategory.HEALTH: [
            "건강", "아프", "병", "병원", "약", "수면", "잠", "불면",
            "식욕", "체중"
        ],
        TopicCategory.FINANCIAL: [
            "돈", "경제", "빚", "대출", "월급", "저축", "투자", "가난",
            "부자", "소비"
        ]
    }

    def extract_topics(
        self,
        conversation: List[ConversationTurn]
    ) -> List[Tuple[TopicCategory, float]]:
        """대화에서 주제 추출"""
        topic_scores = Counter()

        # 사용자 메시지만 분석
        user_messages = " ".join([
            turn.content for turn in conversation
            if turn.role == "user"
        ])

        # 키워드 매칭
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                count = user_messages.count(keyword)
                score += count

            if score > 0:
                topic_scores[topic] = score

        # 정규화 및 정렬
        total = sum(topic_scores.values()) or 1
        normalized = [
            (topic, score / total)
            for topic, score in topic_scores.most_common(5)
        ]

        # 최소 하나의 주제 보장
        if not normalized:
            normalized = [(TopicCategory.OTHER, 1.0)]

        return normalized


class SummaryGenerator:
    """요약 생성기"""

    def __init__(self, llm_engine=None):
        self.llm = llm_engine
        self.keyword_extractor = KeywordExtractor()

        # 요약 프롬프트 템플릿
        self.summary_prompt_template = """당신은 전문 심리상담사입니다. 다음 상담 세션을 분석하고 요약해주세요.

## 대화 내용
{conversation}

## 요청 작업
1. **간략 요약** (2-3문장): 이 세션의 핵심 내용
2. **상세 요약** (5-7문장): 대화의 흐름과 주요 내용
3. **핵심 포인트** (3-5개): 가장 중요한 포인트들
4. **사용자 고민** (2-4개): 사용자가 표현한 주요 고민
5. **인사이트** (2-3개): 상담사 관점에서의 통찰
6. **다음 단계** (2-3개): 사용자에게 도움될 수 있는 과제나 제안

JSON 형식으로 응답해주세요:
{{
    "brief_summary": "...",
    "detailed_summary": "...",
    "key_points": ["...", "..."],
    "user_concerns": ["...", "..."],
    "insights": ["...", "..."],
    "homework": ["...", "..."]
}}"""

    async def generate_summary(
        self,
        session_id: str,
        user_id: str,
        conversation: List[ConversationTurn],
        emotional_data: Optional[List[Dict]] = None
    ) -> SessionSummary:
        """
        세션 요약 생성

        Args:
            session_id: 세션 ID
            user_id: 사용자 ID
            conversation: 대화 기록
            emotional_data: 감정 데이터 (선택)

        Returns:
            세션 요약
        """
        # 기본 정보 계산
        start_time = conversation[0].timestamp or datetime.now()
        end_time = conversation[-1].timestamp or datetime.now()
        duration = int((end_time - start_time).total_seconds() / 60)

        # 주제 추출
        main_topics = self.keyword_extractor.extract_topics(conversation)

        # LLM 기반 요약 또는 규칙 기반 요약
        if self.llm:
            summary_data = await self._generate_llm_summary(conversation)
        else:
            summary_data = self._generate_rule_based_summary(conversation)

        # 감정 분석
        emotional_journey, dominant_emotion, emotional_shift = self._analyze_emotions(
            conversation, emotional_data
        )

        # 다음 세션 제안 생성
        next_suggestions = self._generate_next_session_suggestions(
            main_topics, summary_data.get("user_concerns", [])
        )

        return SessionSummary(
            session_id=session_id,
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration,
            brief_summary=summary_data.get("brief_summary", ""),
            detailed_summary=summary_data.get("detailed_summary", ""),
            main_topics=main_topics,
            key_points=summary_data.get("key_points", []),
            user_concerns=summary_data.get("user_concerns", []),
            counselor_suggestions=summary_data.get("counselor_suggestions", []),
            emotional_journey=emotional_journey,
            dominant_emotion=dominant_emotion,
            emotional_shift=emotional_shift,
            insights=summary_data.get("insights", []),
            patterns_identified=summary_data.get("patterns", []),
            homework=summary_data.get("homework", []),
            next_session_suggestions=next_suggestions,
            message_count=len(conversation),
            user_message_count=len([t for t in conversation if t.role == "user"])
        )

    async def _generate_llm_summary(
        self,
        conversation: List[ConversationTurn]
    ) -> Dict:
        """LLM 기반 요약 생성"""
        try:
            # 대화 포맷팅
            conv_text = "\n".join([
                f"{'사용자' if t.role == 'user' else '상담사'}: {t.content}"
                for t in conversation
            ])

            prompt = self.summary_prompt_template.format(conversation=conv_text)

            # LLM 호출
            if hasattr(self.llm, 'generate_response_async'):
                response = await self.llm.generate_response_async(prompt)
            else:
                import asyncio
                response = await asyncio.to_thread(
                    self.llm.generate_response, prompt
                )

            # JSON 파싱
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())

            # 파싱 실패 시 규칙 기반 폴백
            return self._generate_rule_based_summary(conversation)

        except Exception as e:
            logger.error(f"LLM summary generation failed: {e}")
            return self._generate_rule_based_summary(conversation)

    def _generate_rule_based_summary(
        self,
        conversation: List[ConversationTurn]
    ) -> Dict:
        """규칙 기반 요약 생성"""
        user_messages = [t.content for t in conversation if t.role == "user"]
        assistant_messages = [t.content for t in conversation if t.role == "assistant"]

        # 첫 번째와 마지막 사용자 메시지를 기반으로 간략 요약
        if user_messages:
            first_msg = user_messages[0][:100]
            brief = f"사용자가 '{first_msg}...'에 대해 이야기했습니다. "

            if len(user_messages) > 1:
                brief += f"총 {len(user_messages)}개의 메시지가 교환되었습니다."
        else:
            brief = "대화 기록이 없습니다."

        # 핵심 포인트 추출 (사용자 메시지에서 질문/감정 표현)
        key_points = []
        question_patterns = ["?", "어떻게", "왜", "무엇", "어디", "언제"]
        emotion_patterns = ["힘들", "슬프", "기쁘", "화가", "불안", "걱정"]

        for msg in user_messages:
            for pattern in question_patterns + emotion_patterns:
                if pattern in msg:
                    key_points.append(msg[:80] + "..." if len(msg) > 80 else msg)
                    break

            if len(key_points) >= 5:
                break

        # 사용자 고민 추출
        concerns = []
        concern_markers = ["고민", "걱정", "힘들", "모르겠", "어떻게 해야"]

        for msg in user_messages:
            for marker in concern_markers:
                if marker in msg:
                    concerns.append(msg[:100] + "..." if len(msg) > 100 else msg)
                    break

            if len(concerns) >= 4:
                break

        # 상담사 제안 추출
        suggestions = []
        suggestion_markers = ["해보세요", "시도해", "생각해", "~면 좋겠", "어떨까요"]

        for msg in assistant_messages:
            for marker in suggestion_markers:
                if marker in msg:
                    # 해당 문장만 추출
                    sentences = re.split('[.!?]', msg)
                    for sent in sentences:
                        if marker in sent and len(sent) > 10:
                            suggestions.append(sent.strip() + ".")
                            break
                    break

            if len(suggestions) >= 3:
                break

        return {
            "brief_summary": brief,
            "detailed_summary": f"이 상담 세션에서는 {len(user_messages)}개의 사용자 메시지와 {len(assistant_messages)}개의 상담사 응답이 교환되었습니다. "
                              f"사용자는 주로 자신의 감정과 상황에 대해 이야기했으며, 상담사는 경청하고 지지적인 반응을 보였습니다.",
            "key_points": key_points[:5] if key_points else ["대화 내용에서 특별한 핵심 포인트가 추출되지 않았습니다."],
            "user_concerns": concerns[:4] if concerns else ["구체적인 고민이 표현되지 않았습니다."],
            "counselor_suggestions": suggestions[:3] if suggestions else [],
            "insights": self._generate_basic_insights(user_messages),
            "patterns": [],
            "homework": self._generate_basic_homework(concerns)
        }

    def _generate_basic_insights(self, user_messages: List[str]) -> List[str]:
        """기본 인사이트 생성"""
        insights = []

        all_text = " ".join(user_messages)

        # 메시지 빈도 기반 인사이트
        if len(user_messages) > 10:
            insights.append("활발한 대화를 나누셨습니다. 마음을 열고 이야기하는 것은 좋은 시작입니다.")
        elif len(user_messages) < 3:
            insights.append("짧은 대화였지만, 첫 걸음을 내딛으신 것만으로도 의미있습니다.")

        # 감정 표현 기반 인사이트
        negative_words = ["힘들", "슬프", "우울", "화가", "불안"]
        positive_words = ["기쁘", "좋", "감사", "행복", "희망"]

        neg_count = sum(1 for word in negative_words if word in all_text)
        pos_count = sum(1 for word in positive_words if word in all_text)

        if neg_count > pos_count:
            insights.append("어려운 감정들을 표현해주셨네요. 감정을 인식하고 표현하는 것은 회복의 첫 단계입니다.")
        elif pos_count > neg_count:
            insights.append("긍정적인 표현이 많았습니다. 좋은 에너지를 유지하고 계시네요.")

        # 질문 빈도 기반 인사이트
        question_count = all_text.count("?")
        if question_count > 5:
            insights.append("많은 질문을 하셨습니다. 자신에 대해 탐구하고 이해하려는 노력이 보입니다.")

        return insights if insights else ["대화를 통해 마음을 나눠주셨습니다."]

    def _generate_basic_homework(self, concerns: List[str]) -> List[str]:
        """기본 과제 생성"""
        homework = []

        all_concerns = " ".join(concerns)

        # 고민 기반 과제 제안
        if "불안" in all_concerns or "걱정" in all_concerns:
            homework.append("하루에 5분씩 깊은 호흡 연습을 해보세요.")
        if "우울" in all_concerns or "슬프" in all_concerns:
            homework.append("매일 감사한 일 3가지를 적어보세요.")
        if "스트레스" in all_concerns or "힘들" in all_concerns:
            homework.append("가벼운 산책이나 운동을 시도해보세요.")
        if "관계" in all_concerns or "사람" in all_concerns:
            homework.append("가까운 사람에게 솔직한 대화를 시도해보세요.")

        # 기본 과제
        if not homework:
            homework = [
                "오늘 대화에서 느낀 점을 일기로 정리해보세요.",
                "다음 세션 전까지 자신에게 하고 싶은 말을 생각해보세요."
            ]

        return homework[:3]

    def _analyze_emotions(
        self,
        conversation: List[ConversationTurn],
        emotional_data: Optional[List[Dict]]
    ) -> Tuple[List[Dict], str, str]:
        """감정 분석"""
        emotional_journey = []

        if emotional_data:
            emotional_journey = emotional_data
            emotions = [e.get("emotion", "중립") for e in emotional_data]
        else:
            # 대화에서 감정 추출
            emotion_keywords = {
                "기쁨": ["기쁘", "행복", "좋아", "신나", "웃"],
                "슬픔": ["슬프", "우울", "눈물", "힘들"],
                "분노": ["화가", "짜증", "열받"],
                "불안": ["불안", "걱정", "두려"],
                "평온": ["편안", "차분", "괜찮"]
            }

            emotions = []
            for i, turn in enumerate(conversation):
                if turn.role == "user":
                    detected = "중립"
                    for emotion, keywords in emotion_keywords.items():
                        if any(kw in turn.content for kw in keywords):
                            detected = emotion
                            break

                    emotions.append(detected)
                    emotional_journey.append({
                        "index": i,
                        "emotion": detected,
                        "timestamp": turn.timestamp.isoformat() if turn.timestamp else None
                    })

        # 지배적 감정
        if emotions:
            from collections import Counter
            emotion_counts = Counter(emotions)
            dominant_emotion = emotion_counts.most_common(1)[0][0]
        else:
            dominant_emotion = "중립"

        # 감정 변화 트렌드
        if len(emotions) >= 2:
            valence_map = {
                "기쁨": 1, "희망": 0.7, "평온": 0.3,
                "중립": 0, "불안": -0.4, "슬픔": -0.7, "분노": -0.6
            }

            first_half = emotions[:len(emotions)//2]
            second_half = emotions[len(emotions)//2:]

            first_avg = sum(valence_map.get(e, 0) for e in first_half) / len(first_half)
            second_avg = sum(valence_map.get(e, 0) for e in second_half) / len(second_half)

            if second_avg > first_avg + 0.2:
                emotional_shift = "positive"
            elif second_avg < first_avg - 0.2:
                emotional_shift = "negative"
            else:
                emotional_shift = "stable"
        else:
            emotional_shift = "stable"

        return emotional_journey, dominant_emotion, emotional_shift

    def _generate_next_session_suggestions(
        self,
        topics: List[Tuple[TopicCategory, float]],
        concerns: List[str]
    ) -> List[str]:
        """다음 세션 제안 생성"""
        suggestions = []

        # 주제별 제안
        for topic, _ in topics[:2]:
            if topic == TopicCategory.RELATIONSHIP:
                suggestions.append("대인관계에서의 소통 패턴에 대해 더 이야기해볼까요?")
            elif topic == TopicCategory.ANXIETY:
                suggestions.append("불안을 다루는 구체적인 기법을 배워보는 건 어떨까요?")
            elif topic == TopicCategory.DEPRESSION:
                suggestions.append("일상에서 작은 기쁨을 찾는 방법을 함께 탐색해볼까요?")
            elif topic == TopicCategory.SELF_ESTEEM:
                suggestions.append("자신의 강점과 가치를 발견하는 시간을 가져볼까요?")
            elif topic == TopicCategory.STRESS:
                suggestions.append("스트레스 관리 전략을 함께 세워볼까요?")
            elif topic == TopicCategory.FAMILY:
                suggestions.append("가족 관계에서의 기대와 현실에 대해 더 나눠볼까요?")

        if not suggestions:
            suggestions = [
                "오늘 대화에서 더 깊이 나누고 싶은 주제가 있으셨나요?",
                "다음 세션에서 특별히 다루고 싶은 내용이 있으면 알려주세요."
            ]

        return suggestions[:3]


class SessionSummaryManager:
    """세션 요약 관리자"""

    def __init__(
        self,
        llm_engine=None,
        storage_path: Optional[str] = None
    ):
        self.generator = SummaryGenerator(llm_engine)
        self.storage_path = storage_path
        self.summaries: Dict[str, SessionSummary] = {}

        if storage_path:
            self._load_summaries()

    async def create_summary(
        self,
        session_id: str,
        user_id: str,
        conversation_history: List[Dict],
        emotional_data: Optional[List[Dict]] = None
    ) -> SessionSummary:
        """
        세션 요약 생성

        Args:
            session_id: 세션 ID
            user_id: 사용자 ID
            conversation_history: 대화 기록 (dict 형태)
            emotional_data: 감정 데이터

        Returns:
            생성된 요약
        """
        # Dict → ConversationTurn 변환
        conversation = [
            ConversationTurn(
                role=msg.get("role", "user"),
                content=msg.get("content", ""),
                timestamp=datetime.fromisoformat(msg["timestamp"]) if msg.get("timestamp") else None,
                emotion=msg.get("emotion")
            )
            for msg in conversation_history
        ]

        # 요약 생성
        summary = await self.generator.generate_summary(
            session_id=session_id,
            user_id=user_id,
            conversation=conversation,
            emotional_data=emotional_data
        )

        # 저장
        self.summaries[session_id] = summary
        self._save_summaries()

        logger.info(f"Session summary created: {session_id}")
        return summary

    def get_summary(self, session_id: str) -> Optional[SessionSummary]:
        """요약 조회"""
        return self.summaries.get(session_id)

    def get_user_summaries(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[SessionSummary]:
        """사용자의 최근 요약들 조회"""
        user_summaries = [
            s for s in self.summaries.values()
            if s.user_id == user_id
        ]
        user_summaries.sort(key=lambda s: s.end_time, reverse=True)
        return user_summaries[:limit]

    def get_progress_report(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """진행 상황 리포트"""
        cutoff = datetime.now() - timedelta(days=days)
        recent_summaries = [
            s for s in self.summaries.values()
            if s.user_id == user_id and s.end_time > cutoff
        ]

        if not recent_summaries:
            return {"message": "최근 상담 기록이 없습니다."}

        # 통계
        total_sessions = len(recent_summaries)
        total_duration = sum(s.duration_minutes for s in recent_summaries)

        # 감정 변화 트렌드
        emotional_shifts = [s.emotional_shift for s in recent_summaries]
        positive_count = emotional_shifts.count("positive")
        negative_count = emotional_shifts.count("negative")

        # 주요 주제
        all_topics = []
        for s in recent_summaries:
            all_topics.extend([t[0].value for t in s.main_topics])
        topic_counts = Counter(all_topics)

        return {
            "period_days": days,
            "total_sessions": total_sessions,
            "total_duration_minutes": total_duration,
            "avg_session_duration": total_duration / total_sessions,
            "emotional_trend": {
                "positive_sessions": positive_count,
                "negative_sessions": negative_count,
                "stable_sessions": len(emotional_shifts) - positive_count - negative_count
            },
            "top_topics": topic_counts.most_common(5),
            "overall_progress": "개선" if positive_count > negative_count else (
                "유지" if positive_count == negative_count else "주의 필요"
            )
        }

    def format_summary_text(self, summary: SessionSummary) -> str:
        """요약 텍스트 포맷"""
        lines = []

        # 헤더
        lines.append(f"📋 세션 요약")
        lines.append(f"📅 {summary.start_time.strftime('%Y년 %m월 %d일 %H:%M')}")
        lines.append(f"⏱️ 상담 시간: {summary.duration_minutes}분")
        lines.append("")

        # 간략 요약
        lines.append("## 요약")
        lines.append(summary.brief_summary)
        lines.append("")

        # 주요 주제
        if summary.main_topics:
            lines.append("## 주요 주제")
            for topic, weight in summary.main_topics[:3]:
                lines.append(f"  • {topic.value} ({weight*100:.0f}%)")
            lines.append("")

        # 핵심 포인트
        if summary.key_points:
            lines.append("## 핵심 포인트")
            for point in summary.key_points[:4]:
                lines.append(f"  • {point}")
            lines.append("")

        # 감정 변화
        shift_emoji = {
            "positive": "📈 긍정적 변화",
            "negative": "📉 주의 필요",
            "stable": "➡️ 안정적"
        }
        lines.append("## 감정 분석")
        lines.append(f"  지배적 감정: {summary.dominant_emotion}")
        lines.append(f"  변화 추세: {shift_emoji.get(summary.emotional_shift, '❓')}")
        lines.append("")

        # 인사이트
        if summary.insights:
            lines.append("## 인사이트")
            for insight in summary.insights:
                lines.append(f"  💡 {insight}")
            lines.append("")

        # 다음 단계
        if summary.homework:
            lines.append("## 다음 세션까지")
            for hw in summary.homework:
                lines.append(f"  ✅ {hw}")

        return "\n".join(lines)

    def _load_summaries(self):
        """저장된 요약 로드"""
        try:
            import os
            if self.storage_path and os.path.exists(self.storage_path):
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for session_id, summary_data in data.items():
                        # 간단히 dict로 저장/로드 (실제로는 더 정교한 직렬화 필요)
                        pass  # TODO: 구현
                logger.info(f"Loaded {len(data)} session summaries")
        except Exception as e:
            logger.error(f"Failed to load summaries: {e}")

    def _save_summaries(self):
        """요약 저장"""
        try:
            if self.storage_path:
                # 최근 100개만 저장
                recent = list(self.summaries.items())[-100:]
                data = {}
                for session_id, summary in recent:
                    data[session_id] = {
                        "session_id": summary.session_id,
                        "user_id": summary.user_id,
                        "brief_summary": summary.brief_summary,
                        "start_time": summary.start_time.isoformat(),
                        "end_time": summary.end_time.isoformat(),
                        "duration_minutes": summary.duration_minutes,
                        "dominant_emotion": summary.dominant_emotion,
                        "emotional_shift": summary.emotional_shift
                    }

                with open(self.storage_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save summaries: {e}")


# 전역 인스턴스
_summary_manager: Optional[SessionSummaryManager] = None


def get_summary_manager(
    llm_engine=None,
    storage_path: Optional[str] = None
) -> SessionSummaryManager:
    """세션 요약 관리자 싱글톤"""
    global _summary_manager
    if _summary_manager is None:
        _summary_manager = SessionSummaryManager(llm_engine, storage_path)
    return _summary_manager
