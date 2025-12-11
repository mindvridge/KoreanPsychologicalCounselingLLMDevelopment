"""
장기기억-프롬프트 통합 모듈 (Memory-Prompt Integration)

장기기억 데이터를 프롬프트 시스템에 효과적으로 통합하는 모듈입니다.

기능:
1. 자동 세션 요약 생성
2. 개인화 컨텍스트 포맷팅
3. 세션 간 브릿지 생성
4. 기법 추천 시스템
5. 진행 상황 추적
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import Counter

logger = logging.getLogger(__name__)


# =============================================================================
# 세션 자동 요약 생성기
# =============================================================================

class SessionSummarizer:
    """
    대화 내용에서 자동으로 세션 요약 생성

    LLM을 사용하지 않고 규칙 기반으로 핵심 정보 추출
    """

    # 고민 카테고리 키워드
    CONCERN_KEYWORDS = {
        "직장/업무": ["회사", "직장", "상사", "동료", "업무", "야근", "이직", "퇴사", "번아웃", "승진"],
        "가족": ["가족", "부모", "엄마", "아빠", "형제", "자녀", "남편", "아내", "시댁", "처가"],
        "연애/결혼": ["연인", "남친", "여친", "결혼", "이별", "헤어", "사랑", "연애"],
        "대인관계": ["친구", "사람", "관계", "소통", "갈등", "왕따", "외로"],
        "학업/진로": ["공부", "시험", "성적", "진로", "취업", "대학", "학교"],
        "자존감": ["자존감", "자신감", "열등", "비교", "못나", "부족"],
        "불안": ["불안", "걱정", "초조", "두려움", "긴장", "공포"],
        "우울": ["우울", "무기력", "힘들", "슬프", "의욕없", "우울증"],
        "스트레스": ["스트레스", "압박", "부담", "피곤", "지쳐"],
        "건강": ["건강", "잠", "수면", "아프", "통증", "병원"],
        "트라우마": ["트라우마", "사건", "사고", "폭력", "학대"],
    }

    # 감정 키워드
    EMOTION_KEYWORDS = {
        "불안": ["불안", "걱정", "초조", "두렵", "긴장", "무섭"],
        "우울": ["우울", "슬프", "눈물", "무기력", "공허", "허무"],
        "분노": ["화나", "짜증", "답답", "억울", "분노", "열받"],
        "스트레스": ["스트레스", "피곤", "지쳐", "힘들", "부담"],
        "외로움": ["외롭", "혼자", "고립", "소외"],
        "두려움": ["두렵", "무섭", "공포", "겁나"],
        "죄책감": ["죄책", "미안", "잘못", "후회"],
        "수치심": ["창피", "부끄", "수치", "쪽팔"],
        "희망": ["희망", "나아", "좋아", "기대"],
    }

    # 기법 관련 키워드
    TECHNIQUE_KEYWORDS = {
        "호흡법": ["호흡", "숨", "4-7-8", "박스호흡"],
        "그라운딩": ["그라운딩", "5-4-3-2-1", "감각", "발바닥"],
        "인지재구성": ["생각", "인지", "해석", "관점"],
        "행동활성화": ["활동", "행동", "움직", "운동"],
        "마음챙김": ["마음챙김", "명상", "현재", "관찰"],
        "이완": ["이완", "긴장풀", "릴랙스", "근육"],
    }

    def generate_session_summary(
        self,
        conversation: List[Dict],
        session_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        대화에서 세션 요약 자동 생성

        Args:
            conversation: 대화 기록 [{"role": "user/assistant", "content": "..."}]
            session_id: 세션 ID
            user_id: 사용자 ID

        Returns:
            세션 요약 딕셔너리
        """
        # 사용자 메시지만 추출
        user_messages = [
            msg["content"] for msg in conversation
            if msg.get("role") == "user"
        ]
        all_user_text = " ".join(user_messages)

        # 어시스턴트 메시지
        assistant_messages = [
            msg["content"] for msg in conversation
            if msg.get("role") == "assistant"
        ]
        all_assistant_text = " ".join(assistant_messages)

        # 1. 주요 고민 추출
        main_concerns = self._extract_concerns(all_user_text)

        # 2. 감정 상태 분석
        emotional_state = self._analyze_emotion(all_user_text)

        # 3. 감정 변화 추정
        emotional_shift = self._estimate_emotional_shift(user_messages)

        # 4. 사용된 기법 추출
        techniques_used = self._extract_techniques(all_assistant_text)

        # 5. 과제 추출
        homework = self._extract_homework(all_assistant_text)

        # 6. 위기 이벤트 감지
        crisis_events, max_risk = self._detect_crisis(all_user_text)

        # 7. 핵심 인사이트 추출 (향후 LLM 연동 가능)
        key_insights = self._extract_insights(conversation)

        # 8. 다음 세션 초점
        next_focus = self._suggest_next_focus(main_concerns, emotional_state)

        return {
            "session_id": session_id,
            "user_id": user_id,
            "duration_minutes": len(conversation) * 2,  # 대략적 추정
            "main_concerns": main_concerns,
            "key_insights": key_insights,
            "emotional_state": emotional_state,
            "emotional_shift": emotional_shift,
            "techniques_used": techniques_used,
            "homework": homework,
            "crisis_events": crisis_events,
            "max_risk_level": max_risk,
            "next_session_focus": next_focus,
            "turn_count": len(conversation),
            "generated_at": datetime.now().isoformat()
        }

    def _extract_concerns(self, text: str) -> List[str]:
        """고민 카테고리 추출"""
        concerns = []
        for category, keywords in self.CONCERN_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                concerns.append(category)
        return concerns[:5]  # 최대 5개

    def _analyze_emotion(self, text: str) -> str:
        """주요 감정 분석"""
        emotion_counts = Counter()
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            count = sum(1 for kw in keywords if kw in text)
            if count > 0:
                emotion_counts[emotion] = count

        if emotion_counts:
            return emotion_counts.most_common(1)[0][0]
        return "중립"

    def _estimate_emotional_shift(self, messages: List[str]) -> str:
        """감정 변화 추정 (초반 vs 후반)"""
        if len(messages) < 4:
            return "stable"

        mid = len(messages) // 2
        early = " ".join(messages[:mid])
        late = " ".join(messages[mid:])

        # 부정 감정 키워드
        negative = ["힘들", "슬프", "불안", "화나", "우울", "지쳐"]
        # 긍정 신호
        positive = ["나아", "좋아", "감사", "도움", "편해"]

        early_neg = sum(1 for kw in negative if kw in early)
        late_neg = sum(1 for kw in negative if kw in late)
        late_pos = sum(1 for kw in positive if kw in late)

        if late_pos > 0 and late_neg < early_neg:
            return "positive"
        elif late_neg > early_neg:
            return "negative"
        return "stable"

    def _extract_techniques(self, assistant_text: str) -> List[str]:
        """사용된 기법 추출"""
        techniques = []
        for technique, keywords in self.TECHNIQUE_KEYWORDS.items():
            if any(kw in assistant_text for kw in keywords):
                techniques.append(technique)
        return techniques

    def _extract_homework(self, assistant_text: str) -> List[str]:
        """과제 추출"""
        homework = []
        homework_indicators = ["해보세요", "시도해 보세요", "연습해 보세요", "해 보시겠어요"]

        sentences = assistant_text.split(".")
        for sentence in sentences:
            if any(indicator in sentence for indicator in homework_indicators):
                # 간단히 정제
                clean = sentence.strip()
                if len(clean) > 10 and len(clean) < 100:
                    homework.append(clean)

        return homework[:3]  # 최대 3개

    def _detect_crisis(self, text: str) -> Tuple[int, int]:
        """위기 이벤트 감지"""
        crisis_keywords = ["자살", "죽고 싶", "자해", "끝내고 싶", "살고 싶지 않"]
        high_risk = ["죽고 싶", "자살", "끝내고 싶"]

        crisis_count = sum(1 for kw in crisis_keywords if kw in text)
        max_risk = 3 if any(kw in text for kw in high_risk) else (1 if crisis_count > 0 else 0)

        return crisis_count, max_risk

    def _extract_insights(self, conversation: List[Dict]) -> List[str]:
        """핵심 인사이트 추출 (간단 버전)"""
        insights = []

        # 사용자의 자기 인식 표현 찾기
        insight_phrases = ["깨달았", "알게 됐", "느꼈", "생각해 보니", "이제 보니"]

        for msg in conversation:
            if msg.get("role") == "user":
                content = msg["content"]
                if any(phrase in content for phrase in insight_phrases):
                    insights.append(content[:100])

        return insights[:3]

    def _suggest_next_focus(
        self,
        concerns: List[str],
        emotion: str
    ) -> List[str]:
        """다음 세션 초점 제안"""
        focus = []

        if "우울" in concerns or emotion == "우울":
            focus.append("행동 활성화 탐색")
        if "불안" in concerns or emotion == "불안":
            focus.append("불안 관리 기법 심화")
        if "직장/업무" in concerns:
            focus.append("직장 스트레스 대처 전략")
        if "가족" in concerns:
            focus.append("가족 관계 패턴 탐색")
        if "자존감" in concerns:
            focus.append("자기 인식 및 강점 탐색")

        return focus[:3] if focus else ["이전 진행 상황 확인"]


# =============================================================================
# 개인화 컨텍스트 포맷터
# =============================================================================

class PersonalizationFormatter:
    """
    장기기억 데이터를 프롬프트용 텍스트로 포맷팅
    """

    def format_user_profile_context(
        self,
        profile: Dict[str, Any],
        max_length: int = 800
    ) -> str:
        """
        사용자 프로필을 프롬프트 컨텍스트로 포맷

        Args:
            profile: 사용자 장기 프로필 딕셔너리
            max_length: 최대 문자 수

        Returns:
            포맷된 컨텍스트 문자열
        """
        if not profile:
            return ""

        sections = []

        # 기본 정보
        header = "# 사용자 개인화 정보"
        sections.append(header)

        if profile.get("preferred_name"):
            sections.append(f"- 호칭: {profile['preferred_name']}")

        if profile.get("age_range"):
            sections.append(f"- 나이대: {profile['age_range']}")

        # 상담 이력
        total_sessions = profile.get("total_sessions", 0)
        if total_sessions > 0:
            sections.append(f"\n## 상담 이력 ({total_sessions}회)")

            # 반복 고민
            recurring = profile.get("recurring_concerns", {})
            if recurring:
                top_concerns = sorted(recurring.items(), key=lambda x: x[1], reverse=True)[:3]
                concerns_text = ", ".join([f"{c[0]}({c[1]}회)" for c in top_concerns])
                sections.append(f"- 반복 고민: {concerns_text}")

            # 효과적 기법
            techniques = profile.get("effective_techniques", {})
            if techniques:
                top_tech = sorted(techniques.items(), key=lambda x: x[1], reverse=True)[:3]
                tech_text = ", ".join([f"{t[0]}({t[1]:.0%})" for t in top_tech])
                sections.append(f"- 효과적 기법: {tech_text}")

        # 강점
        strengths = profile.get("identified_strengths", [])
        if strengths:
            sections.append(f"- 확인된 강점: {', '.join(strengths[:3])}")

        # 대처 전략
        coping = profile.get("coping_strategies", [])
        if coping:
            sections.append(f"- 효과적 대처법: {', '.join(coping[:3])}")

        # 트리거
        triggers = profile.get("trigger_patterns", [])
        if triggers:
            sections.append(f"- 주의 필요 트리거: {', '.join(triggers[:3])}")

        # 진행 상황
        progress = profile.get("overall_progress", "unknown")
        if progress != "unknown":
            progress_text = {
                "improving": "호전 중",
                "stable": "안정적",
                "declining": "주의 필요"
            }
            sections.append(f"\n**전반적 진행**: {progress_text.get(progress, progress)}")

        result = "\n".join(sections)

        # 길이 제한
        if len(result) > max_length:
            result = result[:max_length] + "..."

        return result

    def format_session_history_context(
        self,
        recent_sessions: List[Dict],
        max_sessions: int = 3
    ) -> str:
        """
        최근 세션 이력을 컨텍스트로 포맷

        Args:
            recent_sessions: 최근 세션 리스트 (최신순)
            max_sessions: 포함할 최대 세션 수

        Returns:
            포맷된 세션 이력 문자열
        """
        if not recent_sessions:
            return ""

        sections = ["# 최근 상담 이력"]

        for i, session in enumerate(recent_sessions[:max_sessions]):
            session_num = len(recent_sessions) - i
            sections.append(f"\n## 세션 #{session_num}")

            if session.get("main_concerns"):
                sections.append(f"- 고민: {', '.join(session['main_concerns'][:2])}")

            if session.get("emotional_state"):
                sections.append(f"- 감정: {session['emotional_state']}")

            if session.get("emotional_shift"):
                shift_text = {"positive": "호전", "negative": "악화", "stable": "유지"}
                sections.append(f"- 변화: {shift_text.get(session['emotional_shift'], session['emotional_shift'])}")

            if session.get("techniques_used"):
                sections.append(f"- 사용 기법: {', '.join(session['techniques_used'][:2])}")

            if session.get("homework_given"):
                sections.append(f"- 과제: {session['homework_given'][0]}")

            if session.get("key_insights"):
                sections.append(f"- 인사이트: {session['key_insights'][0][:50]}...")

        return "\n".join(sections)

    def format_session_bridge(
        self,
        last_session: Dict,
        current_session_number: int
    ) -> str:
        """
        자연스러운 세션 연결 문구 생성

        Args:
            last_session: 직전 세션 정보
            current_session_number: 현재 세션 번호

        Returns:
            세션 브릿지 안내 문자열
        """
        if not last_session:
            return "첫 상담입니다. 편안한 라포 형성에 집중하세요."

        bridge_parts = [f"# 세션 #{current_session_number} 연결 가이드\n"]

        # 이전 과제 확인
        if last_session.get("homework_given"):
            homework = last_session["homework_given"][0]
            bridge_parts.append(
                f"**과제 확인**: 지난 시간 '{homework}' 과제를 드렸습니다.\n"
                "→ \"지난번에 드린 과제는 해보셨어요?\""
            )

        # 이전 감정 상태 연결
        if last_session.get("emotional_state"):
            emotion = last_session["emotional_state"]
            bridge_parts.append(
                f"\n**이전 감정**: '{emotion}' 상태였습니다.\n"
                "→ \"지난번에 ~한 마음이셨는데, 오늘은 어떠세요?\""
            )

        # 다음 초점 연결
        if last_session.get("next_session_focus"):
            focus = last_session["next_session_focus"][0]
            bridge_parts.append(
                f"\n**계획된 초점**: '{focus}'\n"
                "→ 자연스럽게 이 주제로 연결하세요"
            )

        # 감정 변화 추적
        if last_session.get("emotional_shift"):
            shift = last_session["emotional_shift"]
            if shift == "positive":
                bridge_parts.append("\n✓ 지난 세션에서 긍정적 변화가 있었습니다. 이를 강화하세요.")
            elif shift == "negative":
                bridge_parts.append("\n⚠️ 지난 세션에서 악화 신호가 있었습니다. 주의깊게 확인하세요.")

        return "\n".join(bridge_parts)


# =============================================================================
# 기법 추천 시스템
# =============================================================================

class TechniqueRecommender:
    """
    사용자 이력 기반 기법 추천
    """

    # 상황별 기본 기법 매핑
    DEFAULT_TECHNIQUES = {
        "불안": ["호흡법", "그라운딩", "점진적 근육 이완"],
        "우울": ["행동 활성화", "인지 재구성", "자기 자비"],
        "분노": ["STOP 기법", "감정 명명", "타임아웃"],
        "스트레스": ["이완 훈련", "시간 관리", "경계 설정"],
        "트라우마": ["그라운딩", "안전한 장소", "페이싱"],
        "외로움": ["사회적 연결", "자기 돌봄", "의미 찾기"],
    }

    def recommend_techniques(
        self,
        current_emotion: str,
        current_concern: str,
        user_history: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        기법 추천

        Args:
            current_emotion: 현재 감정
            current_concern: 현재 고민
            user_history: 사용자 이력 (효과적 기법, 사용 기록)

        Returns:
            추천 기법 리스트
        """
        recommendations = []

        # 1. 기본 추천 (상황 기반)
        base_techniques = self.DEFAULT_TECHNIQUES.get(current_emotion, [])
        for tech in base_techniques[:2]:
            recommendations.append({
                "technique": tech,
                "reason": f"{current_emotion} 상태에 효과적",
                "confidence": 0.7
            })

        # 2. 개인화 추천 (이력 기반)
        if user_history:
            effective = user_history.get("effective_techniques", {})
            for tech, score in sorted(effective.items(), key=lambda x: x[1], reverse=True)[:2]:
                if score > 0.5:  # 효과 점수가 높은 것만
                    recommendations.append({
                        "technique": tech,
                        "reason": f"이전에 {score:.0%} 효과 (개인화)",
                        "confidence": min(score + 0.1, 1.0)
                    })

        # 중복 제거 및 정렬
        seen = set()
        unique_recs = []
        for rec in recommendations:
            if rec["technique"] not in seen:
                seen.add(rec["technique"])
                unique_recs.append(rec)

        return sorted(unique_recs, key=lambda x: x["confidence"], reverse=True)[:4]

    def format_recommendations_for_prompt(
        self,
        recommendations: List[Dict]
    ) -> str:
        """추천 결과를 프롬프트용 텍스트로 포맷"""
        if not recommendations:
            return ""

        lines = ["## 권장 기법"]
        for rec in recommendations:
            lines.append(f"- **{rec['technique']}**: {rec['reason']} (신뢰도: {rec['confidence']:.0%})")

        return "\n".join(lines)


# =============================================================================
# 통합 인터페이스
# =============================================================================

class MemoryPromptIntegrator:
    """
    장기기억과 프롬프트 시스템 통합 인터페이스
    """

    def __init__(self):
        self.summarizer = SessionSummarizer()
        self.formatter = PersonalizationFormatter()
        self.recommender = TechniqueRecommender()

    def generate_full_context(
        self,
        user_profile: Optional[Dict],
        recent_sessions: Optional[List[Dict]],
        current_message: str,
        current_emotion: Optional[str] = None
    ) -> str:
        """
        전체 개인화 컨텍스트 생성

        Args:
            user_profile: 사용자 장기 프로필
            recent_sessions: 최근 세션 리스트
            current_message: 현재 메시지
            current_emotion: 현재 감지된 감정

        Returns:
            통합된 컨텍스트 문자열
        """
        context_parts = []

        # 1. 사용자 프로필 컨텍스트
        if user_profile:
            profile_context = self.formatter.format_user_profile_context(user_profile)
            if profile_context:
                context_parts.append(profile_context)

        # 2. 세션 브릿지
        if recent_sessions:
            session_num = (user_profile.get("total_sessions", 0) + 1) if user_profile else 1
            bridge = self.formatter.format_session_bridge(recent_sessions[0], session_num)
            if bridge:
                context_parts.append(bridge)

        # 3. 기법 추천
        if current_emotion or (user_profile and user_profile.get("recurring_concerns")):
            emotion = current_emotion or "스트레스"
            concern = ""
            if user_profile and user_profile.get("recurring_concerns"):
                concern = list(user_profile["recurring_concerns"].keys())[0]

            recommendations = self.recommender.recommend_techniques(
                emotion, concern, user_profile
            )
            if recommendations:
                rec_text = self.recommender.format_recommendations_for_prompt(recommendations)
                context_parts.append(rec_text)

        return "\n\n".join(context_parts)

    def create_session_summary(
        self,
        conversation: List[Dict],
        session_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """세션 요약 생성 (대화 종료 시 호출)"""
        return self.summarizer.generate_session_summary(
            conversation, session_id, user_id
        )


# =============================================================================
# 팩토리 함수
# =============================================================================

_integrator: Optional[MemoryPromptIntegrator] = None

def get_memory_prompt_integrator() -> MemoryPromptIntegrator:
    """싱글톤 인스턴스"""
    global _integrator
    if _integrator is None:
        _integrator = MemoryPromptIntegrator()
    return _integrator


# =============================================================================
# 테스트
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("장기기억-프롬프트 통합 모듈 테스트")
    print("=" * 60)

    integrator = get_memory_prompt_integrator()

    # 테스트 데이터
    test_profile = {
        "preferred_name": "민수",
        "age_range": "30대",
        "total_sessions": 5,
        "recurring_concerns": {"직장/업무": 4, "불안": 3, "수면": 2},
        "effective_techniques": {"호흡법": 0.8, "그라운딩": 0.7, "인지재구성": 0.6},
        "identified_strengths": ["끈기", "분석력", "공감 능력"],
        "coping_strategies": ["운동", "일기 쓰기"],
        "trigger_patterns": ["야근", "상사 피드백"],
        "overall_progress": "improving"
    }

    test_sessions = [
        {
            "main_concerns": ["직장 스트레스", "수면 문제"],
            "emotional_state": "불안",
            "emotional_shift": "positive",
            "techniques_used": ["호흡법", "그라운딩"],
            "homework_given": ["4-7-8 호흡법 매일 연습"],
            "next_session_focus": ["수면 위생 개선"],
            "key_insights": ["야근 후 특히 불안이 심해짐"]
        }
    ]

    # 전체 컨텍스트 생성
    context = integrator.generate_full_context(
        user_profile=test_profile,
        recent_sessions=test_sessions,
        current_message="오늘도 야근했는데 잠이 안 와요",
        current_emotion="불안"
    )

    print("\n[생성된 컨텍스트]")
    print(context)

    # 세션 요약 테스트
    print("\n" + "=" * 60)
    print("세션 요약 테스트")

    test_conversation = [
        {"role": "user", "content": "요즘 회사에서 너무 힘들어요"},
        {"role": "assistant", "content": "많이 힘드시겠어요. 어떤 부분이 가장 힘드세요?"},
        {"role": "user", "content": "상사가 계속 야근을 시키는데 거절을 못 하겠어요"},
        {"role": "assistant", "content": "거절하기 어려운 상황이시군요. 그때 어떤 감정이 드세요?"},
        {"role": "user", "content": "화도 나고 불안하기도 해요"},
        {"role": "assistant", "content": "호흡법을 한번 시도해 보시겠어요? 4초 들이쉬고 7초 멈추고 8초 내쉬는 거예요"},
        {"role": "user", "content": "네, 해볼게요. 이야기하니까 좀 나아진 것 같아요"},
    ]

    summary = integrator.create_session_summary(
        test_conversation, "session_test_001", "user_test_001"
    )

    print("\n[세션 요약]")
    for key, value in summary.items():
        print(f"  {key}: {value}")
