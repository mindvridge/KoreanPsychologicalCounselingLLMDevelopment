"""
통합 프롬프트 시스템 (Integrated Prompt System v1.0)

세 가지 핵심 요소를 통합하여 최적의 상담 컨텍스트 생성:
1. 프롬프트 고도화 - 실시간 상황 적응
2. RAG 지식베이스 - 전문 지식 검색
3. 장기기억 활용 - 개인화된 맥락

이 모듈은 LLM에 전달되는 최종 시스템 프롬프트를 생성합니다.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# 컨텍스트 우선순위 설정
# =============================================================================

class ContextPriority(Enum):
    """컨텍스트 우선순위"""
    CRITICAL = 1    # 위기 상황 - 항상 최우선
    HIGH = 2        # 동맹 파열, 심각한 감정
    MEDIUM = 3      # 일반 상담 컨텍스트
    LOW = 4         # 배경 정보


@dataclass
class ContextBlock:
    """컨텍스트 블록"""
    content: str
    priority: ContextPriority
    category: str
    token_estimate: int = 0

    def __post_init__(self):
        # 대략적인 토큰 추정 (한글 기준)
        self.token_estimate = len(self.content) // 2


@dataclass
class IntegratedContext:
    """통합 컨텍스트"""
    blocks: List[ContextBlock] = field(default_factory=list)
    total_tokens: int = 0
    max_tokens: int = 4000  # 컨텍스트 토큰 제한

    def add_block(self, block: ContextBlock) -> bool:
        """블록 추가 (토큰 제한 확인)"""
        if self.total_tokens + block.token_estimate > self.max_tokens:
            return False
        self.blocks.append(block)
        self.total_tokens += block.token_estimate
        return True

    def get_sorted_content(self) -> str:
        """우선순위별 정렬된 컨텍스트"""
        sorted_blocks = sorted(self.blocks, key=lambda x: x.priority.value)
        return "\n\n".join([b.content for b in sorted_blocks])


# =============================================================================
# 실시간 상황 분석기
# =============================================================================

class RealTimeAnalyzer:
    """실시간 상황 분석"""

    # 위기 키워드 (확장)
    CRISIS_PATTERNS = {
        "suicide": {
            "keywords": ["자살", "죽고 싶", "죽을", "목숨", "끝내고 싶", "살고 싶지 않", "사라지고 싶"],
            "severity": "critical",
            "response_type": "immediate_safety"
        },
        "self_harm": {
            "keywords": ["자해", "손목", "피", "상처 내", "아프게 하고 싶"],
            "severity": "high",
            "response_type": "safety_assessment"
        },
        "violence": {
            "keywords": ["때리고 싶", "죽이고 싶", "해치고 싶", "복수"],
            "severity": "high",
            "response_type": "safety_assessment"
        },
        "abuse": {
            "keywords": ["맞았", "폭력", "학대", "성폭력", "강제로"],
            "severity": "high",
            "response_type": "protection_resources"
        }
    }

    # 감정 강도 키워드
    INTENSITY_MARKERS = {
        "extreme": ["너무", "정말", "진짜", "완전", "죽을 것 같", "미칠 것 같"],
        "high": ["많이", "굉장히", "심하게", "계속"],
        "moderate": ["좀", "약간", "조금"],
    }

    # 긴급 개입 신호
    URGENCY_SIGNALS = [
        "지금 당장", "오늘", "바로", "참을 수 없", "한계",
        "더 이상", "못 견디", "포기"
    ]

    def analyze_message(self, message: str, history: List[Dict]) -> Dict[str, Any]:
        """메시지 실시간 분석"""
        analysis = {
            "crisis_detected": False,
            "crisis_type": None,
            "crisis_severity": None,
            "emotion_intensity": "moderate",
            "urgency_level": 0,
            "requires_immediate_response": False,
            "detected_emotions": [],
            "key_concerns": [],
            "conversation_depth": len(history),
        }

        # 위기 감지
        for crisis_type, patterns in self.CRISIS_PATTERNS.items():
            for keyword in patterns["keywords"]:
                if keyword in message:
                    analysis["crisis_detected"] = True
                    analysis["crisis_type"] = crisis_type
                    analysis["crisis_severity"] = patterns["severity"]
                    analysis["requires_immediate_response"] = True
                    break
            if analysis["crisis_detected"]:
                break

        # 감정 강도 분석
        for intensity, markers in self.INTENSITY_MARKERS.items():
            if any(marker in message for marker in markers):
                analysis["emotion_intensity"] = intensity
                break

        # 긴급성 평가
        urgency_count = sum(1 for signal in self.URGENCY_SIGNALS if signal in message)
        analysis["urgency_level"] = min(urgency_count, 5)

        if analysis["urgency_level"] >= 2 or analysis["emotion_intensity"] == "extreme":
            analysis["requires_immediate_response"] = True

        return analysis


# =============================================================================
# RAG 컨텍스트 선택기
# =============================================================================

class RAGContextSelector:
    """RAG 컨텍스트 선택기"""

    # 상황별 필요한 지식 유형
    KNOWLEDGE_MAPPING = {
        "crisis": ["crisis_protocols", "emergency_response", "safety_resources"],
        "anxiety": ["CBT", "breathing_techniques", "grounding", "exposure"],
        "depression": ["behavioral_activation", "cognitive_restructuring", "self_compassion"],
        "anger": ["DBT", "emotion_regulation", "mindfulness"],
        "relationship": ["communication_skills", "boundary_setting", "interpersonal_effectiveness"],
        "trauma": ["trauma_informed_care", "grounding", "EMDR_basics", "safety"],
        "grief": ["grief_stages", "meaning_making", "continuing_bonds"],
        "stress": ["stress_management", "relaxation", "time_management"],
        "self_esteem": ["self_compassion", "cognitive_restructuring", "values_clarification"],
    }

    # 한국 문화 특화 상황
    KOREAN_CONTEXT_TRIGGERS = {
        "family_pressure": ["부모님", "기대", "효도", "집안", "명절"],
        "work_culture": ["야근", "상사", "눈치", "회식", "퇴사"],
        "social_comparison": ["남들", "비교", "SNS", "스펙", "결혼"],
        "generational": ["꼰대", "요즘 애들", "MZ", "세대"],
        "academic": ["수능", "공부", "학원", "입시", "취업"],
    }

    def select_knowledge_types(
        self,
        analysis: Dict[str, Any],
        message: str
    ) -> List[str]:
        """필요한 지식 유형 선택"""
        needed_knowledge = []

        # 위기 상황 최우선
        if analysis.get("crisis_detected"):
            needed_knowledge.extend(self.KNOWLEDGE_MAPPING["crisis"])
            return needed_knowledge

        # 감정/상황 기반 선택
        for situation, knowledge_types in self.KNOWLEDGE_MAPPING.items():
            if situation in message.lower():
                needed_knowledge.extend(knowledge_types)

        # 한국 문화 맥락 추가
        for context, triggers in self.KOREAN_CONTEXT_TRIGGERS.items():
            if any(trigger in message for trigger in triggers):
                needed_knowledge.append(f"korean_{context}")

        return list(set(needed_knowledge))[:5]  # 최대 5개

    def format_rag_context(
        self,
        retrieved_docs: List[Dict],
        max_chars: int = 2000
    ) -> str:
        """RAG 검색 결과 포맷팅"""
        if not retrieved_docs:
            return ""

        context_parts = ["# 참고 지식\n"]
        current_length = 0

        for doc in retrieved_docs:
            content = doc.get("content", "")
            source = doc.get("source", "unknown")

            if current_length + len(content) > max_chars:
                break

            context_parts.append(f"## [{source}]\n{content}\n")
            current_length += len(content)

        return "\n".join(context_parts)


# =============================================================================
# 장기기억 컨텍스트 생성기
# =============================================================================

class LongTermMemoryContextGenerator:
    """장기기억 기반 컨텍스트 생성"""

    def generate_personalized_context(
        self,
        user_profile: Optional[Dict],
        recent_sessions: Optional[List[Dict]],
        current_session_number: int
    ) -> str:
        """개인화된 컨텍스트 생성"""

        if not user_profile and not recent_sessions:
            return ""

        context_parts = ["# 사용자 맥락 (개인화)\n"]

        # 1. 기본 프로필 정보
        if user_profile:
            if user_profile.get("preferred_name"):
                context_parts.append(f"**호칭**: {user_profile['preferred_name']}")
            if user_profile.get("age_range"):
                context_parts.append(f"**나이대**: {user_profile['age_range']}")

        # 2. 반복되는 고민 패턴
        if user_profile and user_profile.get("recurring_concerns"):
            concerns = user_profile["recurring_concerns"]
            top_concerns = sorted(concerns.items(), key=lambda x: x[1], reverse=True)[:3]
            if top_concerns:
                concerns_str = ", ".join([f"{c[0]}({c[1]}회)" for c in top_concerns])
                context_parts.append(f"\n**반복 고민**: {concerns_str}")

        # 3. 효과적이었던 기법
        if user_profile and user_profile.get("effective_techniques"):
            techniques = user_profile["effective_techniques"]
            best_techniques = sorted(techniques.items(), key=lambda x: x[1], reverse=True)[:3]
            if best_techniques:
                tech_str = ", ".join([f"{t[0]}({t[1]:.0%})" for t in best_techniques])
                context_parts.append(f"**효과적 기법**: {tech_str}")

        # 4. 확인된 강점
        if user_profile and user_profile.get("identified_strengths"):
            strengths = user_profile["identified_strengths"][:3]
            context_parts.append(f"**확인된 강점**: {', '.join(strengths)}")

        # 5. 세션 브릿지 (이전 세션 연결)
        if recent_sessions and len(recent_sessions) > 0:
            last_session = recent_sessions[0]
            context_parts.append(f"\n## 이전 세션 요약 (#{current_session_number - 1})")

            if last_session.get("main_concerns"):
                context_parts.append(f"- 주요 고민: {', '.join(last_session['main_concerns'][:2])}")

            if last_session.get("emotional_shift"):
                shift = last_session["emotional_shift"]
                shift_text = {"positive": "호전", "negative": "악화", "stable": "유지"}
                context_parts.append(f"- 감정 변화: {shift_text.get(shift, shift)}")

            if last_session.get("homework_given"):
                context_parts.append(f"- 과제: {', '.join(last_session['homework_given'][:2])}")

            if last_session.get("next_session_focus"):
                context_parts.append(f"- 다음 초점: {', '.join(last_session['next_session_focus'][:2])}")

        # 6. 전체 진행 상황
        if user_profile:
            total_sessions = user_profile.get("total_sessions", 0)
            progress = user_profile.get("overall_progress", "unknown")

            if total_sessions > 1:
                progress_text = {
                    "improving": "전반적으로 호전 중",
                    "stable": "안정적 유지",
                    "declining": "주의 필요",
                    "unknown": ""
                }
                if progress_text.get(progress):
                    context_parts.append(f"\n**진행 상황** ({total_sessions}회 상담): {progress_text[progress]}")

        return "\n".join(context_parts)

    def generate_session_bridge(
        self,
        recent_sessions: List[Dict],
        current_session_number: int
    ) -> str:
        """자연스러운 세션 연결 문구 생성"""

        if not recent_sessions or current_session_number <= 1:
            return "첫 상담입니다. 편안하게 라포를 형성하세요."

        last_session = recent_sessions[0]

        bridge_parts = []

        # 이전 과제 확인
        if last_session.get("homework_given"):
            bridge_parts.append(
                f"지난 시간에 '{last_session['homework_given'][0]}' 과제를 드렸습니다. "
                "자연스럽게 과제 수행 여부를 확인해 보세요."
            )

        # 이전 감정 상태 연결
        if last_session.get("emotional_state"):
            bridge_parts.append(
                f"지난 상담 시 '{last_session['emotional_state']}' 감정이었습니다. "
                "오늘 기분 변화를 탐색해 보세요."
            )

        # 이전 초점 연결
        if last_session.get("next_session_focus"):
            focus = last_session["next_session_focus"][0]
            bridge_parts.append(
                f"지난 상담에서 '{focus}'에 집중하기로 했습니다."
            )

        return " ".join(bridge_parts) if bridge_parts else ""


# =============================================================================
# 동적 프롬프트 조정기
# =============================================================================

class DynamicPromptAdjuster:
    """동적 프롬프트 조정"""

    # 대화 단계별 지침
    PHASE_GUIDELINES = {
        "opening": {
            "turns": (0, 2),
            "focus": "라포 형성, 안전한 공간 조성",
            "avoid": "해결책 제시, 깊은 탐색",
            "techniques": ["개방형 질문", "따뜻한 환영"],
            "sample": "편안하게 어떤 이야기든 나눠주세요."
        },
        "exploration": {
            "turns": (3, 6),
            "focus": "문제 탐색, 감정 명명",
            "avoid": "조언, 해석",
            "techniques": ["반영", "구체화 질문", "감정 명명"],
            "sample": "그때 어떤 감정이 드셨어요?"
        },
        "understanding": {
            "turns": (7, 10),
            "focus": "깊은 이해, 패턴 인식",
            "avoid": "성급한 개입",
            "techniques": ["요약", "패턴 연결", "핵심 명료화"],
            "sample": "지금까지 말씀해 주신 걸 정리하면..."
        },
        "intervention": {
            "turns": (11, 15),
            "focus": "치료적 개입, 기법 제안",
            "avoid": "강요, 일방적 조언",
            "techniques": ["동의 구하기", "선택지 제공", "기법 안내"],
            "sample": "한 가지 방법이 있는데, 들어보시겠어요?"
        },
        "closing": {
            "turns": (16, float("inf")),
            "focus": "정리, 과제, 마무리",
            "avoid": "새로운 주제",
            "techniques": ["요약", "강점 강화", "다음 단계 안내"],
            "sample": "오늘 중요한 이야기 나눠주셔서 감사해요."
        }
    }

    def get_phase_context(self, turn_count: int) -> str:
        """대화 단계별 지침 생성"""
        current_phase = None

        for phase, config in self.PHASE_GUIDELINES.items():
            min_turn, max_turn = config["turns"]
            if min_turn <= turn_count <= max_turn:
                current_phase = (phase, config)
                break

        if not current_phase:
            current_phase = ("closing", self.PHASE_GUIDELINES["closing"])

        phase_name, config = current_phase

        return f"""## 현재 대화 단계: {phase_name.upper()} (턴 {turn_count})
**집중**: {config['focus']}
**피할 것**: {config['avoid']}
**권장 기법**: {', '.join(config['techniques'])}
**예시**: "{config['sample']}"
"""

    def adjust_for_emotion_intensity(
        self,
        intensity: str,
        crisis_detected: bool
    ) -> str:
        """감정 강도에 따른 조정"""

        if crisis_detected:
            return """⚠️ **위기 상황 감지**
- 안전 확인 최우선
- 공감 후 자원 연결
- 자살예방상담전화 1393 안내
- 단독 대응 금지
"""

        adjustments = {
            "extreme": """⚡ **강한 감정 상태**
- 즉각적 공감과 타당화 필요
- 그라운딩/호흡법 우선 고려
- 천천히, 현재에 머무르기
- 문제 해결보다 감정 수용
""",
            "high": """**높은 감정 강도**
- 충분한 공감 제공
- 감정 명명 도움
- 조급하게 해결책 제시 않기
""",
            "moderate": """**보통 감정 강도**
- 균형 잡힌 탐색과 공감
- 필요시 기법 제안 가능
"""
        }

        return adjustments.get(intensity, "")


# =============================================================================
# 통합 프롬프트 생성기
# =============================================================================

class IntegratedPromptGenerator:
    """
    통합 프롬프트 생성기

    모든 컨텍스트 소스를 통합하여 최적의 시스템 프롬프트 생성
    """

    def __init__(self, max_context_tokens: int = 4000):
        self.analyzer = RealTimeAnalyzer()
        self.rag_selector = RAGContextSelector()
        self.memory_generator = LongTermMemoryContextGenerator()
        self.prompt_adjuster = DynamicPromptAdjuster()
        self.max_tokens = max_context_tokens

    def generate_integrated_prompt(
        self,
        base_prompt: str,
        current_message: str,
        conversation_history: List[Dict],
        user_profile: Optional[Dict] = None,
        recent_sessions: Optional[List[Dict]] = None,
        retrieved_docs: Optional[List[Dict]] = None,
        advanced_analysis: Optional[Dict] = None
    ) -> str:
        """
        통합 시스템 프롬프트 생성

        Args:
            base_prompt: 기본 시스템 프롬프트
            current_message: 현재 사용자 메시지
            conversation_history: 대화 기록
            user_profile: 사용자 장기 프로필
            recent_sessions: 최근 세션 기록
            retrieved_docs: RAG 검색 결과
            advanced_analysis: 고급 상담 분석 결과 (동맹, MI, 변화단계)

        Returns:
            통합된 시스템 프롬프트
        """
        context = IntegratedContext(max_tokens=self.max_tokens)

        # 1. 실시간 분석
        analysis = self.analyzer.analyze_message(current_message, conversation_history)

        # 2. 위기 상황 (최우선)
        if analysis["crisis_detected"]:
            crisis_context = self._generate_crisis_context(analysis)
            context.add_block(ContextBlock(
                content=crisis_context,
                priority=ContextPriority.CRITICAL,
                category="crisis"
            ))

        # 3. 고급 상담 분석 (동맹, MI, 변화단계)
        if advanced_analysis:
            advanced_context = self._format_advanced_analysis(advanced_analysis)
            priority = ContextPriority.HIGH if advanced_analysis.get("alliance", {}).get("rupture_detected") else ContextPriority.MEDIUM
            context.add_block(ContextBlock(
                content=advanced_context,
                priority=priority,
                category="advanced_counseling"
            ))

        # 4. 대화 단계 지침
        turn_count = len(conversation_history)
        phase_context = self.prompt_adjuster.get_phase_context(turn_count)
        context.add_block(ContextBlock(
            content=phase_context,
            priority=ContextPriority.MEDIUM,
            category="phase"
        ))

        # 5. 감정 강도 조정
        intensity_context = self.prompt_adjuster.adjust_for_emotion_intensity(
            analysis["emotion_intensity"],
            analysis["crisis_detected"]
        )
        if intensity_context:
            context.add_block(ContextBlock(
                content=intensity_context,
                priority=ContextPriority.MEDIUM,
                category="emotion_adjustment"
            ))

        # 6. 장기기억 컨텍스트
        if user_profile or recent_sessions:
            session_number = user_profile.get("total_sessions", 0) + 1 if user_profile else 1
            memory_context = self.memory_generator.generate_personalized_context(
                user_profile, recent_sessions, session_number
            )
            if memory_context:
                context.add_block(ContextBlock(
                    content=memory_context,
                    priority=ContextPriority.MEDIUM,
                    category="long_term_memory"
                ))

            # 세션 브릿지
            bridge = self.memory_generator.generate_session_bridge(
                recent_sessions or [], session_number
            )
            if bridge:
                context.add_block(ContextBlock(
                    content=f"## 세션 연결 지침\n{bridge}",
                    priority=ContextPriority.MEDIUM,
                    category="session_bridge"
                ))

        # 7. RAG 컨텍스트
        if retrieved_docs:
            rag_context = self.rag_selector.format_rag_context(retrieved_docs)
            if rag_context:
                context.add_block(ContextBlock(
                    content=rag_context,
                    priority=ContextPriority.LOW,
                    category="rag"
                ))

        # 최종 프롬프트 조합
        final_prompt = base_prompt + "\n\n" + context.get_sorted_content()

        return final_prompt

    def _generate_crisis_context(self, analysis: Dict) -> str:
        """위기 상황 컨텍스트 생성"""
        crisis_type = analysis.get("crisis_type", "unknown")

        return f"""
# ⚠️ 위기 상황 프로토콜 활성화

**감지된 위험**: {crisis_type}
**심각도**: {analysis.get('crisis_severity', 'unknown')}

## 즉각 대응 단계:
1. **공감 표현**: "지금 정말 힘든 상황에 계시군요"
2. **안전 확인**: "지금 안전한 곳에 계신가요?"
3. **자원 연결**:
   - 자살예방상담전화: 1393 (24시간)
   - 정신건강위기상담: 1577-0199 (24시간)
4. **연결 유지**: "전화하시는 동안 저도 여기 있을게요"

⛔ 금지 사항:
- 혼자 해결하려 하지 마세요
- 비밀 유지 약속하지 마세요
- 조언이나 설교하지 마세요
"""

    def _format_advanced_analysis(self, analysis: Dict) -> str:
        """고급 분석 결과 포맷팅"""
        parts = ["# 상담 역동 분석\n"]

        # 치료적 동맹
        if "alliance" in analysis:
            alliance = analysis["alliance"]
            parts.append(f"## 치료적 동맹: {alliance.get('overall_score', 0):.0%}")

            if alliance.get("rupture_detected"):
                parts.append(f"⚠️ **동맹 파열**: {alliance.get('rupture_type')}")
                parts.append("→ 내용보다 관계 회복에 집중하세요")

        # 변화 단계
        if "stage" in analysis:
            stage = analysis["stage"]
            parts.append(f"\n## 변화 단계: {stage.get('current_stage', 'unknown').upper()}")
            parts.append(f"목표: {stage.get('recommended_approach', '')}")

        # MI 분석
        if "mi" in analysis:
            mi = analysis["mi"]
            if mi.get("change_talk_count", 0) > 0:
                parts.append(f"\n## 변화 대화 감지")
                parts.append("→ 반영하고 강화하세요")

            if mi.get("has_sustain_talk"):
                parts.append("\n## 저항 감지")
                parts.append("→ 굴러가기 (Roll with resistance)")

        return "\n".join(parts)


# =============================================================================
# 팩토리 함수
# =============================================================================

_integrated_generator: Optional[IntegratedPromptGenerator] = None

def get_integrated_prompt_generator() -> IntegratedPromptGenerator:
    """통합 프롬프트 생성기 싱글톤"""
    global _integrated_generator
    if _integrated_generator is None:
        _integrated_generator = IntegratedPromptGenerator()
    return _integrated_generator


def generate_counseling_prompt(
    current_message: str,
    conversation_history: List[Dict],
    user_id: Optional[str] = None,
    **kwargs
) -> str:
    """
    편의 함수: 상담 프롬프트 생성

    Args:
        current_message: 현재 메시지
        conversation_history: 대화 기록
        user_id: 사용자 ID (장기기억 조회용)
        **kwargs: 추가 옵션

    Returns:
        완성된 시스템 프롬프트
    """
    generator = get_integrated_prompt_generator()

    # 기본 프롬프트 가져오기
    try:
        from src.prompts_enhanced import get_enhanced_template
        template = get_enhanced_template()
        base_prompt = template.get_system_prompt({"turn_count": len(conversation_history)})
    except ImportError:
        base_prompt = "당신은 한국어 심리상담 AI 도우미입니다."

    # 장기기억 조회
    user_profile = None
    recent_sessions = None

    if user_id:
        try:
            from src.personalization import get_personalization_manager
            pm = get_personalization_manager()
            user_profile = pm.get_long_term_patterns(user_id)
            # recent_sessions = pm.get_recent_sessions(user_id)  # 필요시 구현
        except ImportError:
            pass

    # 고급 상담 분석
    advanced_analysis = None
    try:
        from src.advanced_counseling import get_advanced_counseling_system
        system = get_advanced_counseling_system()
        advanced_analysis = system.analyze_and_enhance(current_message, conversation_history)
    except ImportError:
        pass

    return generator.generate_integrated_prompt(
        base_prompt=base_prompt,
        current_message=current_message,
        conversation_history=conversation_history,
        user_profile=user_profile,
        recent_sessions=recent_sessions,
        advanced_analysis=advanced_analysis,
        **kwargs
    )


# =============================================================================
# 테스트
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("통합 프롬프트 시스템 테스트")
    print("=" * 60)

    generator = get_integrated_prompt_generator()

    # 테스트 케이스
    test_cases = [
        {
            "message": "요즘 너무 힘들어요. 아무것도 하기 싫어요.",
            "history": [{"role": "user", "content": "안녕하세요"}],
            "profile": {"preferred_name": "민수", "recurring_concerns": {"직장": 3, "우울": 2}}
        },
        {
            "message": "죽고 싶어요. 더 이상 못 견디겠어요.",
            "history": [],
            "profile": None
        },
        {
            "message": "지난번에 알려주신 호흡법 해봤는데 좀 나았어요.",
            "history": [{"role": "user", "content": "불안해요"}] * 5,
            "profile": {"effective_techniques": {"호흡법": 0.8}}
        }
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"\n[테스트 {i}]")
        print(f"메시지: {case['message'][:50]}...")
        print("-" * 40)

        prompt = generator.generate_integrated_prompt(
            base_prompt="당신은 마음이, 한국어 심리상담 AI입니다.",
            current_message=case["message"],
            conversation_history=case["history"],
            user_profile=case["profile"]
        )

        print(f"프롬프트 길이: {len(prompt)} 문자")
        print(f"프롬프트 (처음 500자):\n{prompt[:500]}...")
