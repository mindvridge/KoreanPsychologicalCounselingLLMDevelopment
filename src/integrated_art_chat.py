"""
통합 그림 치료 채팅 시스템 (Integrated Art Therapy Chat System)
채팅 중 자연스러운 그림 치료 통합

기능:
- 대화 중 그림 치료 필요성 자동 감지
- 맥락에 맞는 그림 활동 제안
- 그림 업로드 처리 및 분석
- 그림 기반 치료적 대화 생성
- 세션 내 그림-대화 통합 관리
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

# 내부 모듈 임포트
try:
    from art_therapy import (
        ArtTherapyEngine, ArtActivityType, TherapeuticGoal,
        ArtTherapySession, DrawingAnalysis
    )
    from image_analyzer import ImageAnalyzer, VisionProvider, ColorPsychologyAnalyzer
    from projective_tests import ProjectiveTestInterpreter, ProjectiveTestType
    ART_MODULES_AVAILABLE = True
except ImportError:
    ART_MODULES_AVAILABLE = False

logger = logging.getLogger(__name__)


class ArtTherapyTrigger(Enum):
    """그림 치료 트리거 유형"""
    VERBAL_DIFFICULTY = "verbal_difficulty"     # 말로 표현 어려움
    EMOTIONAL_OVERWHELM = "emotional_overwhelm" # 감정적 압도
    FAMILY_ISSUES = "family_issues"             # 가족 문제
    SELF_EXPLORATION = "self_exploration"       # 자기 탐색 필요
    ANXIETY_STRESS = "anxiety_stress"           # 불안/스트레스
    TRAUMA_HINTS = "trauma_hints"               # 트라우마 징후
    CHILD_ADOLESCENT = "child_adolescent"       # 아동/청소년
    GROUNDING_NEEDED = "grounding_needed"       # 안정화 필요
    FUTURE_PLANNING = "future_planning"         # 미래 설계
    RELATIONSHIP_ISSUES = "relationship_issues" # 관계 문제


class ArtSessionState(Enum):
    """그림 세션 상태"""
    NONE = "none"                    # 그림 활동 없음
    SUGGESTED = "suggested"          # 활동 제안됨
    ACCEPTED = "accepted"            # 사용자 수락
    IN_PROGRESS = "in_progress"      # 진행 중
    DRAWING_RECEIVED = "received"    # 그림 수신됨
    ANALYZING = "analyzing"          # 분석 중
    PROCESSING = "processing"        # 치료적 처리 중
    COMPLETED = "completed"          # 완료


@dataclass
class ArtChatContext:
    """그림 치료 채팅 컨텍스트"""
    session_state: ArtSessionState = ArtSessionState.NONE
    current_activity: Optional[ArtActivityType] = None
    trigger_reason: Optional[ArtTherapyTrigger] = None
    drawing_data: Optional[str] = None           # base64 이미지 또는 설명
    analysis_result: Optional[Dict] = None
    follow_up_questions: List[str] = field(default_factory=list)
    turn_count_in_activity: int = 0
    activity_started_at: Optional[datetime] = None


@dataclass
class IntegratedResponse:
    """통합 응답"""
    text: str                               # 응답 텍스트
    art_suggestion: Optional[Dict] = None   # 그림 활동 제안
    art_instruction: Optional[Dict] = None  # 그림 활동 지시
    analysis_feedback: Optional[Dict] = None # 분석 피드백
    show_upload_button: bool = False        # 업로드 버튼 표시
    show_canvas: bool = False               # 그리기 캔버스 표시
    suggested_colors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "text": self.text,
            "art_suggestion": self.art_suggestion,
            "art_instruction": self.art_instruction,
            "analysis_feedback": self.analysis_feedback,
            "show_upload_button": self.show_upload_button,
            "show_canvas": self.show_canvas,
            "suggested_colors": self.suggested_colors,
            "metadata": self.metadata
        }


class ArtTherapyTriggerDetector:
    """
    그림 치료 트리거 감지기

    대화에서 그림 치료가 도움이 될 상황을 감지합니다.
    """

    def __init__(self):
        # 트리거별 키워드 패턴
        self.trigger_patterns = {
            ArtTherapyTrigger.VERBAL_DIFFICULTY: [
                "말로 표현", "표현하기 힘", "표현이 안", "뭐라고 해야",
                "말이 안 나", "설명하기 어", "어떻게 말해", "말로는",
                "표현할 수가", "말문이", "말이 막", "언어로"
            ],
            ArtTherapyTrigger.EMOTIONAL_OVERWHELM: [
                "너무 복잡", "감정이 뒤죽박죽", "정리가 안", "혼란스러",
                "머릿속이 복잡", "감정 정리", "뭐가 뭔지", "뒤엉켜",
                "폭발할 것 같", "터질 것 같", "감당이 안"
            ],
            ArtTherapyTrigger.FAMILY_ISSUES: [
                "가족", "부모님", "엄마", "아빠", "형", "누나", "동생",
                "시댁", "시어머니", "고부", "남편", "아내", "자녀"
            ],
            ArtTherapyTrigger.SELF_EXPLORATION: [
                "나는 누구", "정체성", "나 자신", "내가 뭘 원하는지",
                "진짜 나", "알 수가 없", "나를 모르", "자아"
            ],
            ArtTherapyTrigger.ANXIETY_STRESS: [
                "불안", "걱정", "스트레스", "긴장", "초조", "두려",
                "무서", "공포", "떨리", "잠이 안"
            ],
            ArtTherapyTrigger.TRAUMA_HINTS: [
                "사고", "충격", "플래시백", "악몽", "잊을 수가",
                "계속 떠올", "트라우마", "그때 그 일"
            ],
            ArtTherapyTrigger.GROUNDING_NEEDED: [
                "붕 뜬", "현실감이 없", "멍하", "해리", "내가 아닌",
                "몸이 내 것 같지", "여기가 어딘지", "시간이 안 가"
            ],
            ArtTherapyTrigger.FUTURE_PLANNING: [
                "미래", "앞으로", "진로", "계획", "목표", "꿈",
                "어떻게 살", "방향", "결정"
            ],
            ArtTherapyTrigger.RELATIONSHIP_ISSUES: [
                "관계", "친구", "연인", "남자친구", "여자친구",
                "사람들이", "외로", "혼자", "이별"
            ]
        }

        # 트리거별 권장 활동
        self.trigger_activity_map = {
            ArtTherapyTrigger.VERBAL_DIFFICULTY: [
                ArtActivityType.EMOTION_COLOR,
                ArtActivityType.FREE_DRAWING
            ],
            ArtTherapyTrigger.EMOTIONAL_OVERWHELM: [
                ArtActivityType.EMOTION_COLOR,
                ArtActivityType.MANDALA,
                ArtActivityType.FREE_DRAWING
            ],
            ArtTherapyTrigger.FAMILY_ISSUES: [
                ArtActivityType.KFD,
                ArtActivityType.FREE_DRAWING
            ],
            ArtTherapyTrigger.SELF_EXPLORATION: [
                ArtActivityType.HTP,
                ArtActivityType.ROAD,
                ArtActivityType.FREE_DRAWING
            ],
            ArtTherapyTrigger.ANXIETY_STRESS: [
                ArtActivityType.MANDALA,
                ArtActivityType.WORRY_BOX,
                ArtActivityType.SAFE_PLACE
            ],
            ArtTherapyTrigger.TRAUMA_HINTS: [
                ArtActivityType.SAFE_PLACE,
                ArtActivityType.MANDALA
            ],
            ArtTherapyTrigger.GROUNDING_NEEDED: [
                ArtActivityType.MANDALA,
                ArtActivityType.SAFE_PLACE
            ],
            ArtTherapyTrigger.FUTURE_PLANNING: [
                ArtActivityType.FUTURE_SELF,
                ArtActivityType.BRIDGE,
                ArtActivityType.ROAD
            ],
            ArtTherapyTrigger.RELATIONSHIP_ISSUES: [
                ArtActivityType.KFD,
                ArtActivityType.FREE_DRAWING
            ]
        }

        # 트리거 쿨다운 (같은 세션에서 너무 자주 제안 방지)
        self.suggestion_cooldown_turns = 5

    def detect(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict]] = None,
        turns_since_last_suggestion: int = 999
    ) -> Tuple[Optional[ArtTherapyTrigger], float, List[ArtActivityType]]:
        """
        트리거 감지

        Args:
            user_message: 사용자 메시지
            conversation_history: 대화 히스토리
            turns_since_last_suggestion: 마지막 제안 이후 턴 수

        Returns:
            Tuple: (트리거, 신뢰도, 추천 활동 목록)
        """
        # 쿨다운 체크
        if turns_since_last_suggestion < self.suggestion_cooldown_turns:
            return None, 0.0, []

        # 트리거 점수 계산
        trigger_scores: Dict[ArtTherapyTrigger, float] = {}

        for trigger, patterns in self.trigger_patterns.items():
            score = 0.0
            for pattern in patterns:
                if pattern in user_message:
                    score += 1.0

            # 대화 히스토리에서도 확인 (낮은 가중치)
            if conversation_history:
                for msg in conversation_history[-3:]:
                    content = msg.get("content", "")
                    for pattern in patterns:
                        if pattern in content:
                            score += 0.3

            if score > 0:
                trigger_scores[trigger] = score

        if not trigger_scores:
            return None, 0.0, []

        # 최고 점수 트리거 선택
        best_trigger = max(trigger_scores, key=trigger_scores.get)
        best_score = trigger_scores[best_trigger]

        # 신뢰도 계산 (정규화)
        confidence = min(1.0, best_score / 3.0)

        # 추천 활동
        recommended_activities = self.trigger_activity_map.get(best_trigger, [])

        # 신뢰도가 낮으면 반환 안함
        if confidence < 0.3:
            return None, 0.0, []

        return best_trigger, confidence, recommended_activities


class IntegratedArtTherapyChat:
    """
    통합 그림 치료 채팅 시스템

    일반 상담 대화 중에 그림 치료를 자연스럽게 통합합니다.
    """

    def __init__(
        self,
        vision_provider: VisionProvider = VisionProvider.LOCAL,
        auto_suggest: bool = True,
        suggestion_threshold: float = 0.5
    ):
        """
        초기화

        Args:
            vision_provider: Vision AI 제공자
            auto_suggest: 자동 제안 활성화
            suggestion_threshold: 제안 임계값
        """
        self.trigger_detector = ArtTherapyTriggerDetector()
        self.art_engine = ArtTherapyEngine() if ART_MODULES_AVAILABLE else None
        self.image_analyzer = ImageAnalyzer(provider=vision_provider) if ART_MODULES_AVAILABLE else None
        self.projective_interpreter = ProjectiveTestInterpreter() if ART_MODULES_AVAILABLE else None
        self.color_analyzer = ColorPsychologyAnalyzer() if ART_MODULES_AVAILABLE else None

        self.auto_suggest = auto_suggest
        self.suggestion_threshold = suggestion_threshold

        # 세션별 컨텍스트
        self.session_contexts: Dict[str, ArtChatContext] = {}
        self.turns_since_suggestion: Dict[str, int] = {}

        logger.info("IntegratedArtTherapyChat initialized")

    def get_context(self, session_id: str) -> ArtChatContext:
        """세션 컨텍스트 가져오기"""
        if session_id not in self.session_contexts:
            self.session_contexts[session_id] = ArtChatContext()
            self.turns_since_suggestion[session_id] = 999
        return self.session_contexts[session_id]

    def process_message(
        self,
        session_id: str,
        user_message: str,
        conversation_history: Optional[List[Dict]] = None,
        image_data: Optional[str] = None,
        emotion_context: Optional[str] = None
    ) -> IntegratedResponse:
        """
        메시지 처리

        Args:
            session_id: 세션 ID
            user_message: 사용자 메시지
            conversation_history: 대화 히스토리
            image_data: 이미지 데이터 (base64 또는 설명)
            emotion_context: 감정 컨텍스트

        Returns:
            IntegratedResponse: 통합 응답
        """
        context = self.get_context(session_id)
        self.turns_since_suggestion[session_id] += 1

        # 이미지가 있으면 그림 처리
        if image_data:
            return self._handle_drawing_submission(
                session_id, context, image_data, user_message, emotion_context
            )

        # 현재 상태에 따른 처리
        if context.session_state == ArtSessionState.SUGGESTED:
            return self._handle_suggestion_response(
                session_id, context, user_message
            )
        elif context.session_state in [ArtSessionState.IN_PROGRESS, ArtSessionState.ACCEPTED]:
            return self._handle_in_progress(
                session_id, context, user_message
            )
        elif context.session_state == ArtSessionState.PROCESSING:
            return self._handle_processing(
                session_id, context, user_message
            )

        # 일반 상태: 트리거 감지
        if self.auto_suggest:
            trigger, confidence, activities = self.trigger_detector.detect(
                user_message,
                conversation_history,
                self.turns_since_suggestion.get(session_id, 999)
            )

            if trigger and confidence >= self.suggestion_threshold:
                return self._suggest_art_activity(
                    session_id, context, trigger, activities, user_message
                )

        # 그림 치료 제안 없이 일반 응답
        return IntegratedResponse(
            text="",  # 메인 LLM이 응답 생성
            metadata={"art_therapy_checked": True, "no_suggestion": True}
        )

    def _suggest_art_activity(
        self,
        session_id: str,
        context: ArtChatContext,
        trigger: ArtTherapyTrigger,
        activities: List[ArtActivityType],
        user_message: str
    ) -> IntegratedResponse:
        """그림 활동 제안"""
        if not activities:
            activities = [ArtActivityType.FREE_DRAWING]

        primary_activity = activities[0]
        activity_info = self.art_engine.get_activity_prompt(primary_activity) if self.art_engine else {}

        # 제안 메시지 생성
        suggestion_messages = {
            ArtTherapyTrigger.VERBAL_DIFFICULTY:
                "말로 표현하기 어려우시군요. 혹시 그림으로 표현해보시는 건 어떨까요?",
            ArtTherapyTrigger.EMOTIONAL_OVERWHELM:
                "감정이 복잡하시네요. 색으로 지금 느끼는 감정을 표현해보시겠어요?",
            ArtTherapyTrigger.FAMILY_ISSUES:
                "가족 이야기를 나누고 계시네요. 혹시 가족 그림을 그려보시겠어요?",
            ArtTherapyTrigger.ANXIETY_STRESS:
                "많이 불안하시네요. 마음을 진정시키는 만다라 색칠을 해보시는 건 어떨까요?",
            ArtTherapyTrigger.SELF_EXPLORATION:
                "자기 자신에 대해 탐색하고 계시네요. 나를 나무로 표현해보시겠어요?",
            ArtTherapyTrigger.TRAUMA_HINTS:
                "힘든 기억이 있으시네요. 안전한 장소를 그려보시는 건 어떨까요?",
            ArtTherapyTrigger.GROUNDING_NEEDED:
                "지금 마음이 많이 불안정하신 것 같아요. 천천히 만다라를 색칠해보실래요?",
            ArtTherapyTrigger.FUTURE_PLANNING:
                "미래에 대해 생각하고 계시네요. 미래의 나를 그려보시는 건 어떨까요?",
            ArtTherapyTrigger.RELATIONSHIP_ISSUES:
                "관계에 대한 고민이 있으시네요. 그림으로 표현해보시겠어요?"
        }

        suggestion_text = suggestion_messages.get(
            trigger,
            "혹시 그림으로 표현해보시겠어요?"
        )

        # 활동 설명 추가
        activity_desc = self._get_brief_activity_description(primary_activity)
        suggestion_text += f"\n\n{activity_desc}"

        # 컨텍스트 업데이트
        context.session_state = ArtSessionState.SUGGESTED
        context.current_activity = primary_activity
        context.trigger_reason = trigger
        self.turns_since_suggestion[session_id] = 0

        return IntegratedResponse(
            text=suggestion_text,
            art_suggestion={
                "activity_type": primary_activity.value,
                "activity_name": activity_info.get("title", primary_activity.value),
                "alternatives": [a.value for a in activities[1:3]],
                "trigger": trigger.value
            },
            show_upload_button=True,
            show_canvas=True,
            metadata={
                "suggestion_made": True,
                "trigger": trigger.value,
                "confidence": self.suggestion_threshold
            }
        )

    def _get_brief_activity_description(self, activity: ArtActivityType) -> str:
        """활동 간단 설명"""
        descriptions = {
            ArtActivityType.FREE_DRAWING:
                "마음 가는 대로 자유롭게 그려보세요. 잘 그릴 필요 없어요.",
            ArtActivityType.EMOTION_COLOR:
                "지금 느끼는 감정을 색으로 표현해보세요. 형태는 자유롭게요.",
            ArtActivityType.MANDALA:
                "원 안을 천천히 색칠해보세요. 호흡하면서 그려보세요.",
            ArtActivityType.KFD:
                "가족들이 무언가를 하고 있는 모습을 그려보세요. 자신도 포함해서요.",
            ArtActivityType.HTP:
                "집, 나무, 사람을 차례로 그려보세요.",
            ArtActivityType.SAFE_PLACE:
                "가장 안전하고 편안한 장소를 상상하며 그려보세요.",
            ArtActivityType.WORRY_BOX:
                "걱정을 담을 상자를 그리고, 걱정들을 넣어보세요.",
            ArtActivityType.FUTURE_SELF:
                "미래의 나는 어디서 무엇을 하고 있을지 그려보세요.",
            ArtActivityType.BRIDGE:
                "현재의 나와 미래의 나를 연결하는 다리를 그려보세요.",
            ArtActivityType.ROAD:
                "지금까지의 인생 여정을 길로 표현해보세요."
        }
        return descriptions.get(activity, "자유롭게 그려보세요.")

    def _handle_suggestion_response(
        self,
        session_id: str,
        context: ArtChatContext,
        user_message: str
    ) -> IntegratedResponse:
        """제안에 대한 응답 처리"""
        # 수락 패턴
        accept_patterns = ["네", "좋아", "할게", "해볼게", "그래", "응", "그럴게", "해보고 싶"]
        # 거절 패턴
        decline_patterns = ["아니", "싫", "안 할", "나중에", "됐어", "괜찮아"]

        message_lower = user_message.lower()

        # 수락
        if any(p in message_lower for p in accept_patterns):
            context.session_state = ArtSessionState.ACCEPTED
            context.activity_started_at = datetime.now()

            activity_info = self.art_engine.get_activity_prompt(
                context.current_activity
            ) if self.art_engine else {}

            instruction_text = activity_info.get("instruction", self._get_brief_activity_description(context.current_activity))

            return IntegratedResponse(
                text=f"좋아요! 그럼 시작해볼까요?\n\n{instruction_text}\n\n다 그리시면 사진을 찍어 올려주시거나, 어떻게 그렸는지 말씀해 주세요.",
                art_instruction={
                    "activity": context.current_activity.value,
                    "instruction": instruction_text,
                    "materials": activity_info.get("materials", []),
                    "duration": activity_info.get("duration", "15-20분")
                },
                show_upload_button=True,
                show_canvas=True,
                metadata={"activity_started": True}
            )

        # 거절
        elif any(p in message_lower for p in decline_patterns):
            context.session_state = ArtSessionState.NONE
            context.current_activity = None

            return IntegratedResponse(
                text="괜찮아요, 언제든 마음이 가실 때 말씀해 주세요. 계속 이야기 나눠볼까요?",
                metadata={"suggestion_declined": True}
            )

        # 모호한 응답
        else:
            return IntegratedResponse(
                text="그림으로 표현해보고 싶으신지, 아니면 그냥 대화를 계속 하고 싶으신지 말씀해 주시겠어요?",
                show_upload_button=True,
                metadata={"awaiting_clarification": True}
            )

    def _handle_in_progress(
        self,
        session_id: str,
        context: ArtChatContext,
        user_message: str
    ) -> IntegratedResponse:
        """진행 중 상태 처리"""
        context.turn_count_in_activity += 1

        # 완료 확인 패턴
        done_patterns = ["다 그렸", "완성", "끝났", "다 했", "그렸어"]

        if any(p in user_message for p in done_patterns):
            context.session_state = ArtSessionState.IN_PROGRESS

            return IntegratedResponse(
                text="다 그리셨군요! 그림을 보여주시겠어요? 사진을 찍어 올려주시거나, 어떻게 그리셨는지 설명해 주셔도 좋아요.",
                show_upload_button=True,
                metadata={"awaiting_drawing": True}
            )

        # 도움 요청
        help_patterns = ["어떻게", "모르겠", "뭘 그려", "막막"]

        if any(p in user_message for p in help_patterns):
            activity = context.current_activity
            help_text = self._get_activity_help(activity)

            return IntegratedResponse(
                text=help_text,
                metadata={"help_provided": True}
            )

        # 일반 응답
        return IntegratedResponse(
            text="천천히 그려보세요. 잘 그릴 필요 없어요. 마음 가는 대로 하시면 돼요.",
            metadata={"encouragement": True}
        )

    def _get_activity_help(self, activity: ArtActivityType) -> str:
        """활동별 도움말"""
        help_texts = {
            ArtActivityType.FREE_DRAWING:
                "뭘 그려야 할지 모르겠다면, 눈을 감고 지금 마음속에 떠오르는 이미지를 그려보세요. 선 하나, 점 하나로 시작해도 괜찮아요.",
            ArtActivityType.EMOTION_COLOR:
                "지금 느끼는 감정이 색이라면 무슨 색일까요? 그 색을 종이에 칠해보세요. 형태는 중요하지 않아요.",
            ArtActivityType.MANDALA:
                "중심에서 시작해도 되고, 바깥에서 시작해도 돼요. 마음 가는 대로 색을 칠해보세요. 호흡에 집중하면서요.",
            ArtActivityType.KFD:
                "가족들이 평소에 뭘 하는지 생각해보세요. 각자 하는 일을 그려도 되고, 함께 하는 일을 그려도 돼요.",
            ArtActivityType.HTP:
                "먼저 집을 그려보세요. 어떤 집이든 괜찮아요. 그 다음에 나무, 그 다음에 사람을 그려주세요.",
            ArtActivityType.SAFE_PLACE:
                "진짜 있는 곳이 아니어도 돼요. 상상 속 장소도 좋아요. 거기 있으면 편안할 것 같은 곳을 떠올려보세요."
        }
        return help_texts.get(activity, "마음 가는 대로 그려보세요. 정답은 없어요.")

    def _handle_drawing_submission(
        self,
        session_id: str,
        context: ArtChatContext,
        image_data: str,
        user_message: str,
        emotion_context: Optional[str]
    ) -> IntegratedResponse:
        """그림 제출 처리"""
        context.session_state = ArtSessionState.ANALYZING
        context.drawing_data = image_data

        # 이미지 분석 (Vision AI 또는 설명 기반)
        is_description = not image_data.startswith("data:") and not image_data.startswith("/9j/")

        if is_description or not self.image_analyzer:
            # 사용자 설명 기반 분석
            analysis_result = self._analyze_from_description(
                image_data if is_description else user_message,
                context.current_activity,
                emotion_context
            )
        else:
            # Vision AI 분석 (실제 구현 시)
            analysis_result = self._analyze_image(
                image_data,
                context.current_activity,
                emotion_context
            )

        context.analysis_result = analysis_result
        context.session_state = ArtSessionState.PROCESSING

        # 치료적 응답 생성
        therapeutic_response = self._generate_therapeutic_response(
            context, analysis_result, user_message
        )

        context.follow_up_questions = analysis_result.get("follow_up_questions", [])

        return IntegratedResponse(
            text=therapeutic_response,
            analysis_feedback={
                "received": True,
                "insights": analysis_result.get("insights", []),
                "emotional_tone": analysis_result.get("emotional_tone", "")
            },
            metadata={
                "drawing_analyzed": True,
                "activity": context.current_activity.value if context.current_activity else None
            }
        )

    def _analyze_from_description(
        self,
        description: str,
        activity: Optional[ArtActivityType],
        emotion_context: Optional[str]
    ) -> Dict[str, Any]:
        """설명 기반 분석"""
        if self.image_analyzer:
            result = self.image_analyzer.analyze_from_description(
                description,
                activity.value if activity else None
            )
            analysis = result.to_dict()
        else:
            analysis = {
                "visual_elements": [],
                "dominant_colors": [],
                "overall_impression": "그림을 받았습니다."
            }

        # 색상 분석
        if self.color_analyzer and description:
            colors = self._extract_colors_from_text(description)
            if colors:
                color_analysis = self.color_analyzer.analyze_color_combination(colors)
                analysis["color_interpretation"] = color_analysis

        # 투사 검사 해석 (해당하는 경우)
        if activity in [ArtActivityType.HTP, ArtActivityType.KFD] and self.projective_interpreter:
            # 설명에서 요소 추출하여 해석 (간단한 버전)
            analysis["projective_hints"] = self._extract_projective_hints(description, activity)

        # 후속 질문 생성
        analysis["follow_up_questions"] = self._generate_follow_up_questions(
            activity, analysis, description
        )

        # 통찰 생성
        analysis["insights"] = self._generate_insights(analysis, emotion_context)

        return analysis

    def _extract_colors_from_text(self, text: str) -> List[str]:
        """텍스트에서 색상 추출"""
        color_keywords = [
            "빨강", "빨간", "주황", "노랑", "노란", "초록", "녹색",
            "파랑", "파란", "남색", "보라", "분홍", "갈색", "검정",
            "검은", "흰색", "하얀", "회색", "밝은", "어두운"
        ]
        found = []
        for color in color_keywords:
            if color in text:
                normalized = color.replace("빨간", "빨강").replace("노란", "노랑")
                normalized = normalized.replace("파란", "파랑").replace("검은", "검정")
                normalized = normalized.replace("하얀", "흰색")
                if normalized not in found:
                    found.append(normalized)
        return found

    def _extract_projective_hints(
        self,
        description: str,
        activity: ArtActivityType
    ) -> Dict[str, Any]:
        """투사 검사 힌트 추출"""
        hints = {}

        if activity == ArtActivityType.HTP:
            # 집 관련
            if "집" in description:
                if "작" in description:
                    hints["house_size"] = "small"
                if "크" in description:
                    hints["house_size"] = "large"
                if "문" in description and "없" in description:
                    hints["door"] = "absent"
                if "창문" in description and "없" in description:
                    hints["windows"] = "absent"

            # 나무 관련
            if "나무" in description:
                if "가지" in description:
                    if "많" in description:
                        hints["branches"] = "many_reaching_up"
                if "뿌리" in description:
                    hints["roots"] = "visible"

            # 사람 관련
            if "사람" in description:
                if "웃" in description:
                    hints["expression"] = "happy"
                if "슬프" in description or "우울" in description:
                    hints["expression"] = "sad"

        elif activity == ArtActivityType.KFD:
            # 가족 관련
            if "멀리" in description or "떨어져" in description:
                hints["family_distance"] = "far"
            if "가까이" in description or "붙어" in description:
                hints["family_distance"] = "close"
            if "혼자" in description:
                hints["self_isolated"] = True

        return hints

    def _analyze_image(
        self,
        image_data: str,
        activity: Optional[ArtActivityType],
        emotion_context: Optional[str]
    ) -> Dict[str, Any]:
        """실제 이미지 분석 (Vision AI 사용 시)"""
        # Vision AI 분석 로직
        # 실제 구현에서는 GPT-4V 또는 Claude Vision API 호출
        return {
            "visual_elements": [],
            "dominant_colors": [],
            "overall_impression": "그림을 분석 중입니다.",
            "follow_up_questions": ["그림에 대해 더 이야기해 주시겠어요?"],
            "insights": []
        }

    def _generate_follow_up_questions(
        self,
        activity: Optional[ArtActivityType],
        analysis: Dict,
        description: str
    ) -> List[str]:
        """후속 질문 생성"""
        questions = [
            "그림을 그리면서 어떤 느낌이 드셨어요?"
        ]

        # 활동별 질문
        activity_questions = {
            ArtActivityType.FREE_DRAWING: [
                "이 그림에 제목을 붙인다면 뭐라고 하고 싶으세요?",
                "그림 속에서 가장 마음에 드는 부분은 어디예요?"
            ],
            ArtActivityType.EMOTION_COLOR: [
                "각 색은 어떤 감정을 나타내나요?",
                "이 감정들이 몸 어디에서 느껴지나요?"
            ],
            ArtActivityType.MANDALA: [
                "색칠하면서 마음이 어떻게 변했어요?",
                "어느 부분이 가장 마음에 드세요?"
            ],
            ArtActivityType.KFD: [
                "가족들이 뭘 하고 있는 건가요?",
                "본인은 어디에 있어요?",
                "가족 중 가장 가까운 사람은 누구예요?"
            ],
            ArtActivityType.HTP: [
                "이 집에는 누가 살고 있을까요?",
                "이 나무는 건강한 나무인가요?",
                "이 사람은 지금 기분이 어떨까요?"
            ],
            ArtActivityType.SAFE_PLACE: [
                "이곳에 있으면 어떤 느낌이 들어요?",
                "여기서 뭘 하고 싶으세요?"
            ],
            ArtActivityType.WORRY_BOX: [
                "상자 안에 어떤 걱정들을 넣었어요?",
                "상자에 넣고 나니 기분이 어때요?"
            ],
            ArtActivityType.FUTURE_SELF: [
                "미래의 나는 뭘 하고 있나요?",
                "미래의 내가 지금의 나에게 해주고 싶은 말이 있다면요?"
            ]
        }

        if activity and activity in activity_questions:
            questions.extend(activity_questions[activity][:2])

        # 색상 관련 질문
        colors = analysis.get("dominant_colors") or analysis.get("color_interpretation", {}).get("colors_used", [])
        if colors:
            questions.append("이 색들을 선택한 이유가 있으세요?")

        return questions[:4]

    def _generate_insights(
        self,
        analysis: Dict,
        emotion_context: Optional[str]
    ) -> List[str]:
        """통찰 생성"""
        insights = []

        # 색상 기반 통찰
        color_interp = analysis.get("color_interpretation", {})
        if color_interp:
            energy = color_interp.get("overall_energy", "")
            if "높음" in energy:
                insights.append("활발한 에너지가 느껴지는 그림이에요.")
            elif "낮음" in energy:
                insights.append("차분하거나 내면적인 에너지가 느껴져요.")

            emotions = color_interp.get("dominant_emotions", [])
            if emotions:
                insights.append(f"그림에서 {', '.join(emotions[:2])} 같은 감정이 표현된 것 같아요.")

        return insights

    def _generate_therapeutic_response(
        self,
        context: ArtChatContext,
        analysis: Dict,
        user_message: str
    ) -> str:
        """치료적 응답 생성"""
        response_parts = []

        # 1. 그림 수용
        response_parts.append("그림을 보여주셔서 고마워요.")

        # 2. 관찰 반영 (비판단적)
        if analysis.get("insights"):
            response_parts.append(analysis["insights"][0])

        # 3. 색상 언급
        color_interp = analysis.get("color_interpretation", {})
        colors_used = color_interp.get("colors_used", [])
        if colors_used:
            response_parts.append(f"{', '.join(colors_used[:2])} 색을 사용하셨네요.")

        # 4. 열린 질문
        if context.follow_up_questions:
            response_parts.append("")
            response_parts.append(context.follow_up_questions[0])

        return "\n".join(response_parts)

    def _handle_processing(
        self,
        session_id: str,
        context: ArtChatContext,
        user_message: str
    ) -> IntegratedResponse:
        """그림 처리 후 대화 처리"""
        context.turn_count_in_activity += 1

        # 후속 질문에 대한 응답 처리
        # 사용자가 그림에 대해 더 이야기함

        # 추가 질문 제공
        remaining_questions = context.follow_up_questions[1:] if len(context.follow_up_questions) > 1 else []

        if remaining_questions and context.turn_count_in_activity < 5:
            response_text = f"그렇군요... {remaining_questions[0]}"
            context.follow_up_questions = remaining_questions[1:]
        else:
            # 마무리
            response_text = "그림을 통해 많은 이야기를 나눴네요. 그림을 그리고 나니 기분이 어떠세요?"
            context.session_state = ArtSessionState.COMPLETED

        return IntegratedResponse(
            text=response_text,
            metadata={"processing_conversation": True}
        )

    def end_art_session(self, session_id: str) -> IntegratedResponse:
        """그림 세션 종료"""
        context = self.get_context(session_id)
        context.session_state = ArtSessionState.NONE
        context.current_activity = None
        context.turn_count_in_activity = 0

        return IntegratedResponse(
            text="그림 활동을 마쳤어요. 언제든 다시 그림으로 표현하고 싶으시면 말씀해 주세요.",
            metadata={"session_ended": True}
        )

    def get_art_session_summary(self, session_id: str) -> Dict[str, Any]:
        """그림 세션 요약"""
        context = self.get_context(session_id)

        return {
            "session_id": session_id,
            "current_state": context.session_state.value,
            "activity": context.current_activity.value if context.current_activity else None,
            "trigger": context.trigger_reason.value if context.trigger_reason else None,
            "turns_in_activity": context.turn_count_in_activity,
            "has_drawing": context.drawing_data is not None,
            "has_analysis": context.analysis_result is not None
        }


# =============================================================================
# 프롬프트 생성기 (LLM 연동용)
# =============================================================================

class ArtTherapyPromptEnhancer:
    """
    LLM 프롬프트 강화기

    그림 치료 맥락을 LLM 프롬프트에 통합합니다.
    """

    @staticmethod
    def get_system_prompt_addition(art_context: ArtChatContext) -> str:
        """시스템 프롬프트 추가 내용"""
        if art_context.session_state == ArtSessionState.NONE:
            return ""

        prompt_parts = ["\n## 그림 치료 맥락\n"]

        if art_context.current_activity:
            prompt_parts.append(f"현재 활동: {art_context.current_activity.value}")

        if art_context.session_state == ArtSessionState.PROCESSING:
            prompt_parts.append("\n### 대화 가이드")
            prompt_parts.append("- 그림에 대해 비판단적으로 대화하세요")
            prompt_parts.append("- '왜 그렇게 그렸어요?' 대신 '어떤 느낌이 드셨어요?' 형태로 질문")
            prompt_parts.append("- 해석을 강요하지 말고 내담자의 설명을 우선 경청")

        if art_context.analysis_result:
            insights = art_context.analysis_result.get("insights", [])
            if insights:
                prompt_parts.append(f"\n분석 힌트: {', '.join(insights[:2])}")

        if art_context.follow_up_questions:
            prompt_parts.append(f"\n제안 질문: {art_context.follow_up_questions[0]}")

        return "\n".join(prompt_parts)


# =============================================================================
# 테스트
# =============================================================================

def test_integrated_art_therapy():
    """통합 그림 치료 테스트"""
    print("=== 통합 그림 치료 채팅 테스트 ===\n")

    chat = IntegratedArtTherapyChat(auto_suggest=True, suggestion_threshold=0.3)

    # 시나리오 1: 감정 표현 어려움
    print("=== 시나리오 1: 감정 표현 어려움 ===")
    response1 = chat.process_message(
        session_id="test_001",
        user_message="말로 표현하기가 너무 힘들어요. 뭐라고 해야 할지 모르겠어요."
    )
    print(f"AI: {response1.text}")
    print(f"제안: {response1.art_suggestion}")

    # 사용자 수락
    response2 = chat.process_message(
        session_id="test_001",
        user_message="네, 해볼게요"
    )
    print(f"\nAI: {response2.text}")

    # 그림 설명 제출
    response3 = chat.process_message(
        session_id="test_001",
        user_message="그렸어요",
        image_data="파란색이랑 검은색을 많이 썼어요. 뭔가 소용돌이 같은 모양이에요."
    )
    print(f"\nAI: {response3.text}")

    print("\n" + "=" * 50)

    # 시나리오 2: 가족 문제
    print("\n=== 시나리오 2: 가족 문제 ===")
    response4 = chat.process_message(
        session_id="test_002",
        user_message="요즘 엄마랑 자꾸 싸워요. 아빠는 항상 바쁘시고..."
    )
    print(f"AI: {response4.text}")

    # 세션 요약
    print("\n=== 세션 요약 ===")
    summary = chat.get_art_session_summary("test_001")
    print(summary)


if __name__ == "__main__":
    test_integrated_art_therapy()
