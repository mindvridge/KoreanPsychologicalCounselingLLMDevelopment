"""
대화형 심리검사 모듈 (Conversational Assessment)
자연스러운 대화 흐름 속에서 PHQ-9, GAD-7 등 심리검사 수행

특징:
- 자연어 기반 질문 (딱딱하지 않은 표현)
- 단계적 질문 진행
- 맥락 기반 검사 제안
- 점수 계산 및 해석
- 검사 이력 관리
"""

import logging
import json
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import re

logger = logging.getLogger(__name__)


class AssessmentType(Enum):
    """심리검사 유형"""
    PHQ9 = "phq9"          # 우울증
    GAD7 = "gad7"          # 불안장애
    K10 = "k10"            # 심리적 고통
    PSS = "pss"            # 스트레스
    AUDIT = "audit"        # 알코올 사용


class AssessmentState(Enum):
    """검사 진행 상태"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DECLINED = "declined"


@dataclass
class AssessmentQuestion:
    """검사 질문"""
    id: int
    original_text: str      # 원본 임상 질문
    conversational_text: str  # 대화형 질문
    follow_up_prompts: List[str] = field(default_factory=list)  # 추가 프롬프트


@dataclass
class AssessmentResult:
    """검사 결과"""
    assessment_type: AssessmentType
    total_score: int
    max_score: int
    severity: str
    interpretation: str
    recommendations: List[str]
    answers: Dict[int, int]
    completed_at: datetime
    duration_minutes: float


class ConversationalAssessment:
    """
    대화형 심리검사 시스템

    자연스러운 대화 흐름 속에서 표준화된 심리검사 수행
    """

    def __init__(self):
        self.assessments = self._load_assessments()
        self.active_sessions: Dict[str, Dict] = {}

    def _load_assessments(self) -> Dict[AssessmentType, Dict]:
        """검사 데이터 로드"""
        return {
            AssessmentType.PHQ9: self._get_phq9(),
            AssessmentType.GAD7: self._get_gad7(),
        }

    def _get_phq9(self) -> Dict:
        """PHQ-9 우울증 검사"""
        return {
            "name": "PHQ-9",
            "full_name": "Patient Health Questionnaire-9",
            "description": "우울증 선별 검사",
            "intro": "최근 2주간 어떻게 지내셨는지 여쭤봐도 될까요? 몇 가지 질문을 통해 마음 상태를 함께 살펴보려고 해요.",
            "time_frame": "지난 2주간",
            "questions": [
                AssessmentQuestion(
                    id=1,
                    original_text="일 또는 여가 활동을 하는 데 흥미나 즐거움을 느끼지 못함",
                    conversational_text="요즘 평소에 즐기시던 활동이나 취미에 대한 흥미가 어떠세요? 예전만큼 즐거우신가요?",
                    follow_up_prompts=["그런 느낌이 얼마나 자주 드셨어요?", "언제부터 그러셨어요?"]
                ),
                AssessmentQuestion(
                    id=2,
                    original_text="기분이 가라앉거나, 우울하거나, 희망이 없음",
                    conversational_text="기분은 어떠세요? 혹시 가라앉거나 우울한 느낌이 드신 적 있으신가요?",
                    follow_up_prompts=["그런 기분이 하루 중 언제 주로 드세요?"]
                ),
                AssessmentQuestion(
                    id=3,
                    original_text="잠들기 어렵거나, 자주 깨거나, 너무 많이 잠",
                    conversational_text="수면은 어떠세요? 잠들기 어렵거나, 자주 깨시거나, 또는 너무 많이 주무시진 않으세요?",
                    follow_up_prompts=["하루에 보통 몇 시간 정도 주무세요?"]
                ),
                AssessmentQuestion(
                    id=4,
                    original_text="피곤하다고 느끼거나 기력이 거의 없음",
                    conversational_text="에너지는 어떠세요? 피곤하거나 기운이 없다고 느끼시는 경우가 있으신가요?",
                    follow_up_prompts=["쉬어도 피로가 풀리지 않으시나요?"]
                ),
                AssessmentQuestion(
                    id=5,
                    original_text="입맛이 없거나 과식을 함",
                    conversational_text="식사는 잘 하고 계세요? 입맛이 없거나, 반대로 많이 드시게 되진 않으세요?",
                    follow_up_prompts=["체중 변화가 있으셨나요?"]
                ),
                AssessmentQuestion(
                    id=6,
                    original_text="자신이 나쁜 사람이라고 느끼거나, 자신을 실패자라고 여기거나, 자신 또는 가족을 실망시켰다고 느낌",
                    conversational_text="자기 자신에 대해서는 어떻게 느끼세요? 혹시 스스로를 비난하거나 실망스럽다고 느끼신 적 있으세요?",
                    follow_up_prompts=["어떤 상황에서 그런 생각이 드세요?"]
                ),
                AssessmentQuestion(
                    id=7,
                    original_text="신문을 읽거나 텔레비전을 보는 것과 같은 일에 집중하기가 어려움",
                    conversational_text="집중력은 어떠세요? TV를 보거나 글을 읽을 때 집중하기 어려우신가요?",
                    follow_up_prompts=["일이나 공부할 때도 그러신가요?"]
                ),
                AssessmentQuestion(
                    id=8,
                    original_text="다른 사람들이 눈치 챌 정도로 거동이나 말이 느려짐, 또는 반대로 안절부절 못하거나 가만히 앉아 있을 수 없을 정도로 들뜸",
                    conversational_text="행동이나 말이 평소보다 느려졌다고 느끼시거나, 반대로 안절부절못하고 가만히 있기 힘드신가요?",
                    follow_up_prompts=["주변 분들이 뭐라고 하시던가요?"]
                ),
                AssessmentQuestion(
                    id=9,
                    original_text="자해하거나 차라리 죽는 것이 낫겠다는 생각",
                    conversational_text="혹시... 말씀드리기 조심스럽지만, 스스로를 해치고 싶거나 죽고 싶다는 생각이 드신 적 있으세요?",
                    follow_up_prompts=["그런 생각이 드실 때 누군가와 이야기하실 수 있으세요?"]
                ),
            ],
            "response_scale": {
                0: ["전혀", "없어요", "아니요", "없었어요", "전혀 없", "안 그래요"],
                1: ["며칠", "가끔", "조금", "약간", "때때로", "종종은 아니고"],
                2: ["절반 이상", "자주", "많이", "꽤", "반 이상", "일주일에 절반"],
                3: ["거의 매일", "매일", "항상", "늘", "계속", "하루도 빠짐없이"]
            },
            "scoring": {
                "ranges": [
                    (0, 4, "minimal", "정상 범위"),
                    (5, 9, "mild", "경미한 우울"),
                    (10, 14, "moderate", "중등도 우울"),
                    (15, 19, "moderately_severe", "중등도-심한 우울"),
                    (20, 27, "severe", "심한 우울")
                ],
                "crisis_threshold": 1,  # 9번 문항 1점 이상 시 위기
                "crisis_question": 9
            },
            "interpretations": {
                "minimal": "현재 우울 증상이 거의 없으신 것 같아요. 지금처럼 잘 지내고 계시네요.",
                "mild": "약간의 우울 증상이 있으신 것 같아요. 스트레스 관리와 자기 돌봄이 도움이 될 수 있어요.",
                "moderate": "중간 정도의 우울 증상이 있으신 것 같아요. 전문가와 상담하시면 도움이 될 수 있어요.",
                "moderately_severe": "상당한 우울 증상이 있으신 것 같아요. 전문적인 도움을 받으시길 권해드려요.",
                "severe": "심한 우울 증상이 있으신 것 같아요. 가능한 빨리 전문가의 도움을 받으시길 강력히 권해드려요."
            },
            "recommendations": {
                "minimal": ["현재 상태 유지", "규칙적인 생활 패턴", "스트레스 관리"],
                "mild": ["규칙적인 운동", "충분한 수면", "사회적 활동 유지", "스트레스 관리 기법 학습"],
                "moderate": ["전문 상담 고려", "생활 습관 개선", "지지 체계 강화"],
                "moderately_severe": ["정신건강 전문가 상담 권장", "정신건강의학과 방문 고려"],
                "severe": ["즉시 정신건강 전문가 상담 필요", "정신건강의학과 방문 권장"]
            }
        }

    def _get_gad7(self) -> Dict:
        """GAD-7 불안장애 검사"""
        return {
            "name": "GAD-7",
            "full_name": "Generalized Anxiety Disorder 7-item",
            "description": "범불안장애 선별 검사",
            "intro": "불안에 대해 조금 더 자세히 여쭤봐도 될까요? 최근 2주간의 경험을 함께 살펴보려고 해요.",
            "time_frame": "지난 2주간",
            "questions": [
                AssessmentQuestion(
                    id=1,
                    original_text="초조하거나 불안하거나 조마조마하게 느낀다",
                    conversational_text="요즘 마음이 불안하거나 초조하신 적이 있으세요? 조마조마한 느낌이 드시나요?",
                    follow_up_prompts=["어떤 상황에서 그런 느낌이 드세요?"]
                ),
                AssessmentQuestion(
                    id=2,
                    original_text="걱정하는 것을 멈추거나 조절할 수가 없다",
                    conversational_text="걱정이 시작되면 멈추기가 어려우신가요? 걱정을 조절하기 힘드세요?",
                    follow_up_prompts=["주로 어떤 걱정을 하시나요?"]
                ),
                AssessmentQuestion(
                    id=3,
                    original_text="여러 가지 것들에 대해 걱정을 너무 많이 한다",
                    conversational_text="이것저것 여러 가지 일에 대해 걱정이 많으신 편인가요?",
                    follow_up_prompts=["걱정이 생활에 영향을 주나요?"]
                ),
                AssessmentQuestion(
                    id=4,
                    original_text="편하게 있기가 어렵다",
                    conversational_text="편하게 쉬거나 긴장을 푸는 게 어려우신가요?",
                    follow_up_prompts=["쉴 때도 마음이 편치 않으신가요?"]
                ),
                AssessmentQuestion(
                    id=5,
                    original_text="너무 안절부절못해서 가만히 있기가 힘들다",
                    conversational_text="안절부절못하거나 가만히 있기 힘드신 적이 있으세요?",
                    follow_up_prompts=["몸이 계속 움직이고 싶으신가요?"]
                ),
                AssessmentQuestion(
                    id=6,
                    original_text="쉽게 짜증이 나거나 쉽게 성을 내게 된다",
                    conversational_text="요즘 짜증이 쉽게 나시거나 화가 나시는 편인가요?",
                    follow_up_prompts=["예전보다 더 예민해지셨나요?"]
                ),
                AssessmentQuestion(
                    id=7,
                    original_text="마치 끔찍한 일이 생길 것처럼 두렵게 느껴진다",
                    conversational_text="뭔가 안 좋은 일이 일어날 것 같은 두려움이 드신 적 있으세요?",
                    follow_up_prompts=["구체적으로 어떤 걱정이 드시나요?"]
                ),
            ],
            "response_scale": {
                0: ["전혀", "없어요", "아니요", "없었어요"],
                1: ["며칠", "가끔", "조금", "약간"],
                2: ["절반 이상", "자주", "많이", "꽤"],
                3: ["거의 매일", "매일", "항상", "늘"]
            },
            "scoring": {
                "ranges": [
                    (0, 4, "minimal", "정상 범위"),
                    (5, 9, "mild", "경미한 불안"),
                    (10, 14, "moderate", "중등도 불안"),
                    (15, 21, "severe", "심한 불안")
                ]
            },
            "interpretations": {
                "minimal": "현재 불안 증상이 거의 없으신 것 같아요.",
                "mild": "약간의 불안 증상이 있으신 것 같아요. 이완 기법이 도움이 될 수 있어요.",
                "moderate": "중간 정도의 불안 증상이 있으신 것 같아요. 전문가 상담을 고려해 보세요.",
                "severe": "상당한 불안 증상이 있으신 것 같아요. 전문가의 도움을 받으시길 권해드려요."
            },
            "recommendations": {
                "minimal": ["현재 상태 유지", "규칙적인 운동", "충분한 휴식"],
                "mild": ["이완 기법 연습 (호흡, 명상)", "규칙적인 운동", "카페인 줄이기"],
                "moderate": ["전문 상담 고려", "인지행동치료 고려", "생활 습관 개선"],
                "severe": ["정신건강 전문가 상담 권장", "정신건강의학과 방문 권장"]
            }
        }

    # =========================================================================
    # 검사 세션 관리
    # =========================================================================

    def start_assessment(
        self,
        session_id: str,
        assessment_type: AssessmentType,
        user_name: Optional[str] = None
    ) -> str:
        """검사 시작"""
        assessment = self.assessments.get(assessment_type)
        if not assessment:
            return "지원하지 않는 검사입니다."

        self.active_sessions[session_id] = {
            "type": assessment_type,
            "state": AssessmentState.IN_PROGRESS,
            "current_question": 0,
            "answers": {},
            "started_at": datetime.now(),
            "user_name": user_name
        }

        # 소개 메시지 생성
        intro = assessment["intro"]
        if user_name:
            intro = f"{user_name}님, " + intro

        first_question = assessment["questions"][0]

        return f"{intro}\n\n{first_question.conversational_text}"

    def process_response(
        self,
        session_id: str,
        user_response: str
    ) -> Tuple[str, Optional[AssessmentResult]]:
        """
        사용자 응답 처리

        Returns:
            (다음 질문 또는 결과 메시지, 완료 시 결과 객체)
        """
        if session_id not in self.active_sessions:
            return "진행 중인 검사가 없습니다.", None

        session = self.active_sessions[session_id]
        assessment = self.assessments[session["type"]]

        # 응답 거부 확인
        if self._is_decline_response(user_response):
            session["state"] = AssessmentState.DECLINED
            del self.active_sessions[session_id]
            return "알겠습니다. 준비가 되시면 언제든 말씀해 주세요. 다른 이야기를 나눠볼까요?", None

        # 점수 추출
        score = self._extract_score(user_response, assessment["response_scale"])

        if score is None:
            # 점수를 추출하지 못한 경우
            current_q = assessment["questions"][session["current_question"]]
            clarification = self._get_clarification_prompt(current_q)
            return clarification, None

        # 답변 저장
        current_q_id = session["current_question"] + 1
        session["answers"][current_q_id] = score

        # 다음 질문 또는 완료
        session["current_question"] += 1

        if session["current_question"] >= len(assessment["questions"]):
            # 검사 완료
            result = self._calculate_result(session, assessment)
            del self.active_sessions[session_id]

            response = self._format_result_message(result, assessment)
            return response, result
        else:
            # 다음 질문
            next_question = assessment["questions"][session["current_question"]]
            transition = self._get_transition_phrase()
            return f"{transition} {next_question.conversational_text}", None

    def _is_decline_response(self, response: str) -> bool:
        """거부 응답 확인"""
        decline_phrases = [
            "하기 싫", "안 할래", "그만", "중단", "멈춰", "싫어",
            "나중에", "다음에", "오늘은", "지금은 아니"
        ]
        return any(phrase in response for phrase in decline_phrases)

    def _extract_score(self, response: str, scale: Dict[int, List[str]]) -> Optional[int]:
        """응답에서 점수 추출"""
        response_lower = response.lower().strip()

        # 명시적 숫자 확인
        numbers = re.findall(r'\d+', response)
        if numbers:
            num = int(numbers[0])
            if 0 <= num <= 3:
                return num

        # 키워드 매칭
        for score, keywords in scale.items():
            for keyword in keywords:
                if keyword in response_lower:
                    return score

        # 자연어 분석 (간단한 휴리스틱)
        if any(word in response_lower for word in ["네", "맞아", "그래요", "있어요", "드려요"]):
            # 긍정적 응답 - 추가 문맥 필요
            if any(word in response_lower for word in ["많이", "자주", "항상", "계속"]):
                return 3
            elif any(word in response_lower for word in ["가끔", "때때로", "조금"]):
                return 1
            return 2

        if any(word in response_lower for word in ["아니", "없", "안"]):
            return 0

        return None

    def _get_clarification_prompt(self, question: AssessmentQuestion) -> str:
        """명확화 요청"""
        prompts = [
            "조금 더 구체적으로 말씀해 주시겠어요? 전혀 없으셨는지, 가끔 있으셨는지, 자주 있으셨는지, 거의 매일 있으셨는지 알려주시면 도움이 될 것 같아요.",
            "이해했어요. 그런 경험이 얼마나 자주 있으셨는지 여쭤봐도 될까요? 전혀 없음, 며칠, 7일 이상, 거의 매일 중에서요.",
            f"{question.follow_up_prompts[0] if question.follow_up_prompts else '얼마나 자주 그러셨어요?'}"
        ]
        import random
        return random.choice(prompts)

    def _get_transition_phrase(self) -> str:
        """전환 문구"""
        phrases = [
            "네, 알겠습니다.",
            "말씀 감사해요.",
            "이해했어요.",
            "네, 그러시군요.",
            "알려주셔서 감사해요.",
        ]
        import random
        return random.choice(phrases)

    def _calculate_result(self, session: Dict, assessment: Dict) -> AssessmentResult:
        """결과 계산"""
        total_score = sum(session["answers"].values())
        max_score = len(assessment["questions"]) * 3

        # 심각도 결정
        severity = "minimal"
        interpretation_key = "minimal"

        for min_score, max_s, sev, _ in assessment["scoring"]["ranges"]:
            if min_score <= total_score <= max_s:
                severity = sev
                interpretation_key = sev
                break

        # 위기 확인 (PHQ-9 9번 문항)
        crisis_detected = False
        if "crisis_question" in assessment["scoring"]:
            crisis_q = assessment["scoring"]["crisis_question"]
            crisis_threshold = assessment["scoring"]["crisis_threshold"]
            if session["answers"].get(crisis_q, 0) >= crisis_threshold:
                crisis_detected = True

        interpretation = assessment["interpretations"].get(interpretation_key, "")
        recommendations = assessment["recommendations"].get(interpretation_key, [])

        if crisis_detected:
            interpretation += "\n\n⚠️ 힘든 생각을 하고 계신 것 같아 걱정이 됩니다. 혼자 감당하지 마시고, 전문가의 도움을 받으시길 부탁드려요. 자살예방상담전화 1393은 24시간 운영됩니다."
            recommendations = ["즉시 전문가 상담 필요", "자살예방상담전화 1393"] + recommendations

        duration = (datetime.now() - session["started_at"]).total_seconds() / 60

        return AssessmentResult(
            assessment_type=session["type"],
            total_score=total_score,
            max_score=max_score,
            severity=severity,
            interpretation=interpretation,
            recommendations=recommendations,
            answers=session["answers"],
            completed_at=datetime.now(),
            duration_minutes=duration
        )

    def _format_result_message(self, result: AssessmentResult, assessment: Dict) -> str:
        """결과 메시지 포맷"""
        severity_labels = {
            "minimal": "정상",
            "mild": "경미",
            "moderate": "중등도",
            "moderately_severe": "중등도-심함",
            "severe": "심함"
        }

        severity_label = severity_labels.get(result.severity, result.severity)

        message = f"""
검사를 완료해 주셔서 감사합니다. 결과를 알려드릴게요.

📊 **{assessment['name']} 결과**
- 총점: {result.total_score}점 / {result.max_score}점
- 수준: {severity_label}

💬 **해석**
{result.interpretation}

📋 **권장사항**
"""
        for i, rec in enumerate(result.recommendations[:3], 1):
            message += f"{i}. {rec}\n"

        message += "\n이 결과는 참고용이며, 정확한 진단은 전문가와 상담하시길 권해드려요. 더 이야기 나누고 싶으시면 말씀해 주세요."

        return message

    # =========================================================================
    # 검사 제안
    # =========================================================================

    def suggest_assessment(self, conversation_history: List[Dict]) -> Optional[Tuple[AssessmentType, str]]:
        """
        대화 내용 기반 검사 제안

        Returns:
            (검사 유형, 제안 메시지) 또는 None
        """
        if len(conversation_history) < 3:
            return None

        # 최근 대화 분석
        recent_text = " ".join([
            msg.get("content", "") for msg in conversation_history[-5:]
            if msg.get("role") == "user"
        ])

        # 우울 키워드
        depression_keywords = [
            "우울", "슬프", "눈물", "의욕", "무기력", "피곤", "힘들",
            "외롭", "희망", "죽", "살기", "포기", "끝"
        ]

        # 불안 키워드
        anxiety_keywords = [
            "불안", "걱정", "초조", "긴장", "두려", "무서",
            "잠이 안", "심장", "떨려", "안절부절"
        ]

        depression_count = sum(1 for kw in depression_keywords if kw in recent_text)
        anxiety_count = sum(1 for kw in anxiety_keywords if kw in recent_text)

        if depression_count >= 2:
            return (
                AssessmentType.PHQ9,
                "이야기를 들어보니, 마음이 많이 힘드신 것 같아요. 혹시 괜찮으시다면, 간단한 마음 체크를 해보는 건 어떨까요? 2-3분 정도면 되고, 지금 상태를 좀 더 객관적으로 이해하는 데 도움이 될 거예요."
            )

        if anxiety_count >= 2:
            return (
                AssessmentType.GAD7,
                "불안감이 많이 느껴지시는 것 같아요. 혹시 간단한 불안 체크를 해보시겠어요? 몇 분이면 되고, 지금 상태를 파악하는 데 도움이 될 거예요."
            )

        return None

    def is_assessment_in_progress(self, session_id: str) -> bool:
        """검사 진행 중 여부"""
        return session_id in self.active_sessions

    def get_current_progress(self, session_id: str) -> Optional[Dict]:
        """현재 진행 상황"""
        if session_id not in self.active_sessions:
            return None

        session = self.active_sessions[session_id]
        assessment = self.assessments[session["type"]]
        total_questions = len(assessment["questions"])

        return {
            "assessment_type": session["type"].value,
            "current_question": session["current_question"] + 1,
            "total_questions": total_questions,
            "progress_percent": (session["current_question"] / total_questions) * 100
        }


# ============================================================================
# 검사 이력 관리
# ============================================================================

class AssessmentHistory:
    """검사 이력 관리"""

    def __init__(self):
        self.history: Dict[str, List[AssessmentResult]] = {}

    def add_result(self, user_id: str, result: AssessmentResult):
        """결과 추가"""
        if user_id not in self.history:
            self.history[user_id] = []
        self.history[user_id].append(result)

    def get_history(
        self,
        user_id: str,
        assessment_type: Optional[AssessmentType] = None,
        limit: int = 10
    ) -> List[AssessmentResult]:
        """이력 조회"""
        results = self.history.get(user_id, [])

        if assessment_type:
            results = [r for r in results if r.assessment_type == assessment_type]

        return sorted(results, key=lambda x: x.completed_at, reverse=True)[:limit]

    def get_trend(self, user_id: str, assessment_type: AssessmentType) -> Dict:
        """추세 분석"""
        results = self.get_history(user_id, assessment_type, limit=5)

        if len(results) < 2:
            return {"trend": "insufficient_data", "message": "추세를 분석하기에 데이터가 부족합니다."}

        scores = [r.total_score for r in results]
        avg_change = (scores[0] - scores[-1]) / len(scores)

        if avg_change < -1:
            return {"trend": "improving", "message": "점차 좋아지고 있는 것 같아요!"}
        elif avg_change > 1:
            return {"trend": "worsening", "message": "최근 힘든 시간을 보내고 계신 것 같아요."}
        else:
            return {"trend": "stable", "message": "비교적 안정적인 상태를 유지하고 계세요."}


# Export
__all__ = [
    'ConversationalAssessment',
    'AssessmentHistory',
    'AssessmentType',
    'AssessmentResult'
]
