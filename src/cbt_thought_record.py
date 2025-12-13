# -*- coding: utf-8 -*-
"""
CBT 사고 기록 모듈 (CBT Thought Record Module)

인지행동치료(CBT)의 핵심 기법인 사고 기록을 채팅에 통합합니다.
자동적 사고 식별, 인지 왜곡 탐지, 대안적 사고 생성을 지원합니다.

Author: MindVridge AI Team
Version: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
import re


class CognitiveDistortion(Enum):
    """인지 왜곡 유형"""
    ALL_OR_NOTHING = "all_or_nothing"           # 흑백 논리
    OVERGENERALIZATION = "overgeneralization"   # 과잉 일반화
    MENTAL_FILTER = "mental_filter"             # 정신적 여과
    DISQUALIFYING_POSITIVE = "disqualifying_positive"  # 긍정 격하
    JUMPING_TO_CONCLUSIONS = "jumping_to_conclusions"  # 성급한 결론
    MIND_READING = "mind_reading"               # 독심술
    FORTUNE_TELLING = "fortune_telling"         # 점쟁이 오류
    MAGNIFICATION = "magnification"             # 과대화
    MINIMIZATION = "minimization"               # 축소화
    EMOTIONAL_REASONING = "emotional_reasoning" # 감정적 추론
    SHOULD_STATEMENTS = "should_statements"     # 당위적 진술
    LABELING = "labeling"                       # 낙인찍기
    PERSONALIZATION = "personalization"         # 개인화
    CATASTROPHIZING = "catastrophizing"         # 파국화


@dataclass
class CognitiveDistortionInfo:
    """인지 왜곡 정보"""
    distortion_type: CognitiveDistortion
    korean_name: str
    description: str
    example: str
    challenging_questions: List[str]
    keywords: List[str]


@dataclass
class ThoughtRecord:
    """사고 기록"""
    record_id: str
    user_id: str
    timestamp: datetime

    # 상황
    situation: str = ""
    situation_when: str = ""
    situation_where: str = ""
    situation_who: str = ""
    situation_what: str = ""

    # 감정
    emotions: List[Dict[str, Any]] = field(default_factory=list)  # {name, intensity_before, intensity_after}

    # 자동적 사고
    automatic_thoughts: List[str] = field(default_factory=list)
    hot_thought: str = ""  # 가장 강렬한 사고

    # 인지 왜곡
    identified_distortions: List[CognitiveDistortion] = field(default_factory=list)

    # 증거
    evidence_for: List[str] = field(default_factory=list)      # 사고를 뒷받침하는 증거
    evidence_against: List[str] = field(default_factory=list)  # 사고에 반하는 증거

    # 대안적 사고
    alternative_thoughts: List[str] = field(default_factory=list)
    balanced_thought: str = ""

    # 결과
    new_emotion_ratings: List[Dict[str, Any]] = field(default_factory=list)
    action_plan: str = ""

    # 메타데이터
    completed: bool = False
    current_step: str = "situation"


class ThoughtRecordStep(Enum):
    """사고 기록 단계"""
    SITUATION = "situation"
    EMOTIONS = "emotions"
    AUTOMATIC_THOUGHTS = "automatic_thoughts"
    HOT_THOUGHT = "hot_thought"
    DISTORTIONS = "distortions"
    EVIDENCE_FOR = "evidence_for"
    EVIDENCE_AGAINST = "evidence_against"
    ALTERNATIVE_THOUGHT = "alternative_thought"
    BALANCED_THOUGHT = "balanced_thought"
    RE_RATE_EMOTIONS = "re_rate_emotions"
    ACTION_PLAN = "action_plan"
    COMPLETE = "complete"


class CognitiveDistortionDetector:
    """인지 왜곡 탐지기"""

    def __init__(self):
        self.distortion_info = self._initialize_distortion_info()

    def _initialize_distortion_info(self) -> Dict[CognitiveDistortion, CognitiveDistortionInfo]:
        """인지 왜곡 정보 초기화"""
        return {
            CognitiveDistortion.ALL_OR_NOTHING: CognitiveDistortionInfo(
                distortion_type=CognitiveDistortion.ALL_OR_NOTHING,
                korean_name="흑백 논리 (전부 아니면 전무)",
                description="상황을 극단적인 범주로만 봅니다. 중간 지대가 없습니다.",
                example="'실수를 했으니 완전히 실패한 거야'",
                challenging_questions=[
                    "중간 지점은 없을까요?",
                    "부분적인 성공은 인정할 수 있을까요?",
                    "회색 영역은 어떤 것이 있을까요?"
                ],
                keywords=["완전히", "전혀", "항상", "절대", "100%", "0%", "완벽", "최악"]
            ),

            CognitiveDistortion.OVERGENERALIZATION: CognitiveDistortionInfo(
                distortion_type=CognitiveDistortion.OVERGENERALIZATION,
                korean_name="과잉 일반화",
                description="한 번의 사건을 끝없는 패턴으로 확대합니다.",
                example="'이번에도 실패했어. 난 항상 실패해'",
                challenging_questions=[
                    "이것이 정말 '항상' 일어나는 일인가요?",
                    "예외적인 경우는 없었나요?",
                    "한 번의 사건으로 결론 내리는 것이 공정한가요?"
                ],
                keywords=["항상", "절대", "매번", "언제나", "아무도", "모든", "늘", "다"]
            ),

            CognitiveDistortion.MENTAL_FILTER: CognitiveDistortionInfo(
                distortion_type=CognitiveDistortion.MENTAL_FILTER,
                korean_name="정신적 여과",
                description="부정적인 세부 사항에만 집중하고 긍정적인 면은 걸러냅니다.",
                example="'칭찬도 받았지만 비판 한 마디가 계속 떠올라'",
                challenging_questions=[
                    "긍정적인 측면도 있지 않았나요?",
                    "전체 그림에서 무엇을 놓치고 있나요?",
                    "좋았던 부분은 어떤 것이 있었나요?"
                ],
                keywords=["그것만", "오직", "그 말이", "계속 떠올"]
            ),

            CognitiveDistortion.DISQUALIFYING_POSITIVE: CognitiveDistortionInfo(
                distortion_type=CognitiveDistortion.DISQUALIFYING_POSITIVE,
                korean_name="긍정 격하",
                description="긍정적인 경험을 인정하지 않고 무시하거나 평가절하합니다.",
                example="'운이 좋았을 뿐이야' '누구나 할 수 있는 거야'",
                challenging_questions=[
                    "왜 이 성공을 인정하기 어려운가요?",
                    "다른 사람이 같은 일을 했다면 어떻게 평가할까요?",
                    "노력한 부분은 없었나요?"
                ],
                keywords=["운이 좋", "누구나", "별거 아니", "그냥", "대단한 게"]
            ),

            CognitiveDistortion.JUMPING_TO_CONCLUSIONS: CognitiveDistortionInfo(
                distortion_type=CognitiveDistortion.JUMPING_TO_CONCLUSIONS,
                korean_name="성급한 결론",
                description="충분한 증거 없이 부정적인 결론에 뛰어듭니다.",
                example="'답장이 늦는 걸 보니 화가 났나 봐'",
                challenging_questions=[
                    "이 결론을 뒷받침하는 증거가 있나요?",
                    "다른 설명은 불가능한가요?",
                    "직접 확인해 본 적이 있나요?"
                ],
                keywords=["분명히", "틀림없이", "-나 봐", "아마", "확실히"]
            ),

            CognitiveDistortion.MIND_READING: CognitiveDistortionInfo(
                distortion_type=CognitiveDistortion.MIND_READING,
                korean_name="독심술",
                description="다른 사람의 생각을 확인 없이 안다고 가정합니다.",
                example="'다들 나를 이상하게 생각할 거야'",
                challenging_questions=[
                    "그 사람의 생각을 실제로 어떻게 알 수 있나요?",
                    "물어본 적이 있나요?",
                    "내 추측이 틀릴 가능성은요?"
                ],
                keywords=["생각할 거", "느낄 거", "알 거야", "볼 거야", "-겠지"]
            ),

            CognitiveDistortion.FORTUNE_TELLING: CognitiveDistortionInfo(
                distortion_type=CognitiveDistortion.FORTUNE_TELLING,
                korean_name="점쟁이 오류",
                description="부정적인 결과가 확실하게 일어날 것처럼 예측합니다.",
                example="'어차피 면접 망할 거야'",
                challenging_questions=[
                    "미래를 정확히 예측할 수 있나요?",
                    "과거에 예측이 틀린 적은 없었나요?",
                    "다른 결과도 가능하지 않을까요?"
                ],
                keywords=["될 거야", "어차피", "분명", "망할", "실패할", "안 될"]
            ),

            CognitiveDistortion.MAGNIFICATION: CognitiveDistortionInfo(
                distortion_type=CognitiveDistortion.MAGNIFICATION,
                korean_name="과대화 (확대)",
                description="부정적인 것의 중요성을 과장합니다.",
                example="'이 실수는 내 커리어를 끝장낼 거야'",
                challenging_questions=[
                    "이것이 정말 그렇게 큰 일인가요?",
                    "1년 후에도 이것이 중요할까요?",
                    "최악의 결과가 정말 일어날 확률은?"
                ],
                keywords=["끔찍", "최악", "재앙", "끝장", "엄청난", "파멸"]
            ),

            CognitiveDistortion.MINIMIZATION: CognitiveDistortionInfo(
                distortion_type=CognitiveDistortion.MINIMIZATION,
                korean_name="축소화",
                description="자신의 긍정적인 특성이나 성과를 축소합니다.",
                example="'별거 아니야, 누구나 할 수 있어'",
                challenging_questions=[
                    "이 성취를 왜 작게 보고 있나요?",
                    "남들도 쉽게 할 수 있는 일인가요?",
                    "친구가 같은 일을 했다면 뭐라고 할까요?"
                ],
                keywords=["별거 아니", "그냥", "누구나", "대단한 게 아니"]
            ),

            CognitiveDistortion.EMOTIONAL_REASONING: CognitiveDistortionInfo(
                distortion_type=CognitiveDistortion.EMOTIONAL_REASONING,
                korean_name="감정적 추론",
                description="감정을 사실의 증거로 사용합니다.",
                example="'불안하니까 분명 뭔가 잘못될 거야'",
                challenging_questions=[
                    "감정이 사실을 증명하나요?",
                    "불안한데도 잘된 적은 없었나요?",
                    "감정을 빼고 상황을 보면 어떤가요?"
                ],
                keywords=["느끼니까", "느껴지", "기분이", "그런 느낌"]
            ),

            CognitiveDistortion.SHOULD_STATEMENTS: CognitiveDistortionInfo(
                distortion_type=CognitiveDistortion.SHOULD_STATEMENTS,
                korean_name="당위적 진술 (~해야 해)",
                description="'해야 한다', '해서는 안 된다'라는 경직된 규칙을 적용합니다.",
                example="'나는 항상 완벽해야 해'",
                challenging_questions=[
                    "이 '해야 한다'는 어디서 왔나요?",
                    "정말 반드시 그래야 하나요?",
                    "'~하면 좋겠다'로 바꿔보면 어떨까요?"
                ],
                keywords=["해야", "해서는 안", "해야만", "당연히", "마땅히", "반드시"]
            ),

            CognitiveDistortion.LABELING: CognitiveDistortionInfo(
                distortion_type=CognitiveDistortion.LABELING,
                korean_name="낙인찍기",
                description="자신이나 타인에게 극단적인 라벨을 붙입니다.",
                example="'나는 루저야' '그 사람은 나쁜 사람이야'",
                challenging_questions=[
                    "한 가지 특성이 전체를 정의하나요?",
                    "이 라벨이 공정한가요?",
                    "행동과 사람을 구분할 수 있나요?"
                ],
                keywords=["나는 ~야", "걔는 ~야", "루저", "바보", "쓸모없", "무능"]
            ),

            CognitiveDistortion.PERSONALIZATION: CognitiveDistortionInfo(
                distortion_type=CognitiveDistortion.PERSONALIZATION,
                korean_name="개인화",
                description="자신과 관련 없는 일에 대해 책임을 느낍니다.",
                example="'팀이 실패한 건 내 탓이야'",
                challenging_questions=[
                    "이것이 전적으로 당신 책임인가요?",
                    "다른 요인들은 없었나요?",
                    "책임을 나눈다면 몇 %가 당신 몫인가요?"
                ],
                keywords=["내 탓", "내 잘못", "나 때문", "내가 ~해서"]
            ),

            CognitiveDistortion.CATASTROPHIZING: CognitiveDistortionInfo(
                distortion_type=CognitiveDistortion.CATASTROPHIZING,
                korean_name="파국화",
                description="최악의 시나리오만 생각합니다.",
                example="'직장에서 해고당하면 인생 끝이야'",
                challenging_questions=[
                    "최악의 시나리오가 실제로 일어날 확률은?",
                    "최악이 일어나도 대처할 방법은 없을까요?",
                    "가장 현실적인 결과는 무엇일까요?"
                ],
                keywords=["끝이야", "파멸", "최악", "재앙", "망했", "다 끝났"]
            )
        }

    def detect_distortions(self, thought: str) -> List[Tuple[CognitiveDistortion, float]]:
        """사고에서 인지 왜곡 탐지"""
        detected = []
        thought_lower = thought.lower()

        for distortion_type, info in self.distortion_info.items():
            confidence = 0.0
            matches = []

            for keyword in info.keywords:
                if keyword in thought_lower:
                    matches.append(keyword)
                    confidence += 0.2

            if matches:
                confidence = min(confidence, 0.9)
                detected.append((distortion_type, confidence))

        # 신뢰도순 정렬
        detected.sort(key=lambda x: x[1], reverse=True)
        return detected[:3]  # 상위 3개 반환

    def get_distortion_info(self, distortion_type: CognitiveDistortion) -> CognitiveDistortionInfo:
        """특정 인지 왜곡 정보 반환"""
        return self.distortion_info.get(distortion_type)


class CBTTriggerDetector:
    """CBT 사고 기록 필요 상황 감지"""

    def __init__(self):
        self.negative_thought_patterns = [
            r"나는\s*(바보|멍청이|쓸모없|실패자|루저)",
            r"항상\s*(실패|망|안\s*돼)",
            r"절대\s*(못|안\s*돼|안\s*될)",
            r"다\s*내\s*탓",
            r"아무도\s*(나를|날)",
            r"어차피",
            r"분명히?\s*(싫어|미워|무시)",
        ]

        self.emotional_intensity_keywords = [
            "너무", "정말", "진짜", "엄청", "완전", "미칠 것 같",
            "죽고 싶", "사라지고 싶", "힘들어서", "견딜 수 없"
        ]

        self.rumination_keywords = [
            "자꾸 생각", "계속 떠올", "머릿속에서", "잊을 수가 없",
            "계속 맴돌", "되새기", "반복"
        ]

    def detect(self, message: str, conversation_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """CBT 사고 기록 필요 상황 감지"""
        triggers = {
            "negative_thoughts": self._check_negative_thoughts(message),
            "emotional_intensity": self._check_emotional_intensity(message),
            "rumination": self._check_rumination(message)
        }

        # 대화 기록에서 반복되는 부정적 패턴 확인
        if conversation_history:
            triggers["recurring_pattern"] = self._check_recurring_pattern(
                message, conversation_history
            )
        else:
            triggers["recurring_pattern"] = {"detected": False}

        should_suggest = (
            triggers["negative_thoughts"]["detected"] or
            triggers["emotional_intensity"]["detected"] or
            triggers["rumination"]["detected"]
        )

        return {
            "should_suggest": should_suggest,
            "triggers": triggers,
            "primary_trigger": self._get_primary_trigger(triggers)
        }

    def _check_negative_thoughts(self, message: str) -> Dict[str, Any]:
        """부정적 사고 패턴 확인"""
        matches = []
        for pattern in self.negative_thought_patterns:
            if re.search(pattern, message):
                matches.append(pattern)

        return {
            "detected": len(matches) > 0,
            "match_count": len(matches),
            "confidence": min(len(matches) * 0.3, 0.9)
        }

    def _check_emotional_intensity(self, message: str) -> Dict[str, Any]:
        """감정 강도 확인"""
        matches = [kw for kw in self.emotional_intensity_keywords if kw in message]
        return {
            "detected": len(matches) >= 2,
            "matches": matches,
            "confidence": min(len(matches) * 0.2, 0.8)
        }

    def _check_rumination(self, message: str) -> Dict[str, Any]:
        """반추 패턴 확인"""
        matches = [kw for kw in self.rumination_keywords if kw in message]
        return {
            "detected": len(matches) > 0,
            "matches": matches,
            "confidence": min(len(matches) * 0.3, 0.8)
        }

    def _check_recurring_pattern(
        self,
        current_message: str,
        history: List[Dict]
    ) -> Dict[str, Any]:
        """반복되는 패턴 확인"""
        # 최근 5개 메시지에서 유사한 부정적 표현 확인
        recent_messages = [msg.get("content", "") for msg in history[-5:]]
        pattern_count = 0

        for pattern in self.negative_thought_patterns:
            if re.search(pattern, current_message):
                for hist_msg in recent_messages:
                    if re.search(pattern, hist_msg):
                        pattern_count += 1

        return {
            "detected": pattern_count >= 2,
            "recurring_count": pattern_count
        }

    def _get_primary_trigger(self, triggers: Dict) -> Optional[str]:
        """주요 트리거 식별"""
        max_confidence = 0
        primary = None

        for trigger_name, trigger_data in triggers.items():
            confidence = trigger_data.get("confidence", 0)
            if trigger_data["detected"] and confidence > max_confidence:
                max_confidence = confidence
                primary = trigger_name

        return primary


class IntegratedCBTChat:
    """채팅 통합형 CBT 사고 기록 시스템"""

    def __init__(self):
        self.trigger_detector = CBTTriggerDetector()
        self.distortion_detector = CognitiveDistortionDetector()
        self.active_records: Dict[str, ThoughtRecord] = {}
        self.record_counter = 0

    def process_message(
        self,
        session_id: str,
        user_message: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """사용자 메시지 처리 및 CBT 사고 기록 통합"""

        # 진행 중인 사고 기록이 있는지 확인
        if session_id in self.active_records:
            return self._handle_active_record(session_id, user_message)

        # CBT 사고 기록 필요 상황 감지
        trigger_result = self.trigger_detector.detect(user_message, conversation_history)

        if trigger_result["should_suggest"]:
            # 즉각적인 인지 왜곡 분석
            distortions = self.distortion_detector.detect_distortions(user_message)
            return self._suggest_thought_record(session_id, trigger_result, distortions)

        return {
            "cbt_suggested": False,
            "response": None,
            "continue_conversation": True
        }

    def _suggest_thought_record(
        self,
        session_id: str,
        trigger_result: Dict,
        distortions: List[Tuple[CognitiveDistortion, float]]
    ) -> Dict[str, Any]:
        """사고 기록 제안"""

        # 감지된 인지 왜곡 설명
        distortion_info = ""
        if distortions:
            top_distortion = distortions[0][0]
            info = self.distortion_detector.get_distortion_info(top_distortion)
            distortion_info = f"""

💭 방금 말씀하신 내용에서 **'{info.korean_name}'** 패턴이 보여요.
{info.description}"""

        response = f"""지금 많이 힘든 생각이 드시는 것 같아요.{distortion_info}

📝 혹시 **사고 기록**을 함께 해보시겠어요?
생각을 정리하고 다른 관점을 찾아보는 데 도움이 될 수 있어요.

5-10분 정도 걸리고, 제가 하나씩 질문을 드릴게요.

해보시겠어요? (네/아니요)"""

        return {
            "cbt_suggested": True,
            "response": response,
            "detected_distortions": [(d[0].value, d[1]) for d in distortions],
            "trigger_type": trigger_result["primary_trigger"],
            "continue_conversation": True,
            "awaiting_acceptance": True
        }

    def start_thought_record(
        self,
        session_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """사고 기록 시작"""
        self.record_counter += 1
        record_id = f"TR_{user_id}_{self.record_counter}"

        self.active_records[session_id] = ThoughtRecord(
            record_id=record_id,
            user_id=user_id,
            timestamp=datetime.now(),
            current_step="situation"
        )

        response = """좋아요, 함께 생각을 정리해 볼게요. 📝

**[1단계: 상황]**

힘든 생각이 들었을 때의 상황을 알려주세요.
- **언제** 그런 생각이 들었나요?
- **어디서** 있었나요?
- **무슨 일**이 있었나요?

편하게 말씀해 주세요."""

        return {
            "record_started": True,
            "response": response,
            "current_step": "situation",
            "continue_conversation": True
        }

    def _handle_active_record(
        self,
        session_id: str,
        user_message: str
    ) -> Dict[str, Any]:
        """진행 중인 사고 기록 처리"""
        record = self.active_records[session_id]
        message_lower = user_message.lower().strip()

        # 중단 요청 확인
        if any(word in message_lower for word in ["그만", "멈춰", "중단", "취소"]):
            return self._end_record(session_id, interrupted=True)

        # 단계별 처리
        step_handlers = {
            "situation": self._process_situation,
            "emotions": self._process_emotions,
            "automatic_thoughts": self._process_automatic_thoughts,
            "hot_thought": self._process_hot_thought,
            "distortions": self._process_distortions,
            "evidence_for": self._process_evidence_for,
            "evidence_against": self._process_evidence_against,
            "alternative_thought": self._process_alternative_thought,
            "balanced_thought": self._process_balanced_thought,
            "re_rate_emotions": self._process_re_rate_emotions,
            "action_plan": self._process_action_plan
        }

        handler = step_handlers.get(record.current_step)
        if handler:
            return handler(session_id, user_message)

        return {
            "response": "진행 중에 오류가 발생했어요. 다시 시작해 볼까요?",
            "continue_conversation": True
        }

    def _process_situation(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """상황 단계 처리"""
        record = self.active_records[session_id]
        record.situation = user_message
        record.current_step = "emotions"

        response = """네, 상황을 말씀해 주셨네요. 💙

**[2단계: 감정]**

그 상황에서 어떤 **감정**을 느끼셨나요?
감정의 **강도**를 0-100%로 표현해 주세요.

예시: "불안 80%, 슬픔 60%, 화남 40%"

여러 감정을 느끼셨을 수 있어요. 모두 말씀해 주세요."""

        return {
            "response": response,
            "current_step": "emotions",
            "continue_conversation": True
        }

    def _process_emotions(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """감정 단계 처리"""
        record = self.active_records[session_id]

        # 간단한 감정 파싱
        emotions = self._parse_emotions(user_message)
        record.emotions = emotions
        record.current_step = "automatic_thoughts"

        emotion_summary = ", ".join([f"{e['name']} {e['intensity']}%" for e in emotions]) if emotions else user_message

        response = f"""감정을 잘 인식하셨어요: {emotion_summary}

**[3단계: 자동적 사고]**

그때 **어떤 생각**이 스쳐 지나갔나요?
머릿속에 떠오른 생각을 그대로 적어주세요.

여러 가지 생각이 있을 수 있어요. 생각나는 대로 모두 말씀해 주세요.

예시: "나는 아무것도 제대로 못해", "다들 나를 무시할 거야" """

        return {
            "response": response,
            "current_step": "automatic_thoughts",
            "continue_conversation": True
        }

    def _process_automatic_thoughts(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """자동적 사고 단계 처리"""
        record = self.active_records[session_id]

        # 사고 파싱 및 저장
        thoughts = [t.strip() for t in user_message.replace(",", "\n").split("\n") if t.strip()]
        record.automatic_thoughts = thoughts
        record.current_step = "hot_thought"

        # 인지 왜곡 분석
        all_distortions = []
        for thought in thoughts:
            distortions = self.distortion_detector.detect_distortions(thought)
            all_distortions.extend(distortions)

        # 발견된 왜곡 저장
        record.identified_distortions = list(set([d[0] for d in all_distortions]))

        response = f"""생각을 잘 표현해 주셨어요. 총 {len(thoughts)}개의 생각을 말씀해 주셨네요.

**[4단계: 핵심 사고 (Hot Thought)]**

이 생각들 중에서 **가장 강렬하게** 느껴지거나,
**감정을 가장 많이 자극**하는 생각은 무엇인가요?

하나만 선택해 주세요."""

        return {
            "response": response,
            "current_step": "hot_thought",
            "automatic_thoughts": thoughts,
            "continue_conversation": True
        }

    def _process_hot_thought(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """핵심 사고 단계 처리"""
        record = self.active_records[session_id]
        record.hot_thought = user_message
        record.current_step = "distortions"

        # 핵심 사고에 대한 인지 왜곡 분석
        distortions = self.distortion_detector.detect_distortions(user_message)

        distortion_text = ""
        if distortions:
            distortion_text = "\n\n이 생각에서 발견된 사고 패턴:\n"
            for distortion, confidence in distortions[:2]:
                info = self.distortion_detector.get_distortion_info(distortion)
                distortion_text += f"• **{info.korean_name}**: {info.description}\n"

        response = f"""핵심 사고: "{user_message}"{distortion_text}

**[5단계: 인지 왜곡 확인]**

위의 사고 패턴이 맞는 것 같으신가요?
혹시 다른 패턴도 느껴지시나요?

(맞으면 '네', 다른 의견이 있으면 말씀해 주세요)"""

        return {
            "response": response,
            "current_step": "distortions",
            "detected_distortions": [(d[0].value, d[1]) for d in distortions],
            "continue_conversation": True
        }

    def _process_distortions(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """인지 왜곡 확인 단계 처리"""
        record = self.active_records[session_id]
        record.current_step = "evidence_for"

        response = f"""좋아요, 이제 이 생각을 함께 검토해 볼게요.

**[6단계: 사고를 뒷받침하는 증거]**

"{record.hot_thought}"

이 생각이 **사실이라는 증거**는 무엇인가요?
실제로 일어난 일, 관찰 가능한 사실만 말씀해 주세요.

(해석이나 추측이 아닌 객관적 사실로요)"""

        return {
            "response": response,
            "current_step": "evidence_for",
            "continue_conversation": True
        }

    def _process_evidence_for(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """뒷받침 증거 단계 처리"""
        record = self.active_records[session_id]
        evidence = [e.strip() for e in user_message.split(",") if e.strip()]
        record.evidence_for = evidence if evidence else [user_message]
        record.current_step = "evidence_against"

        response = f"""증거를 정리해 주셨어요.

**[7단계: 사고에 반하는 증거]**

"{record.hot_thought}"

이 생각이 **사실이 아닐 수 있는 증거**는 무엇인가요?
- 예외적인 경우는 없었나요?
- 다른 설명은 불가능할까요?
- 놓치고 있는 정보는 없을까요?

천천히 생각해 보세요."""

        return {
            "response": response,
            "current_step": "evidence_against",
            "continue_conversation": True
        }

    def _process_evidence_against(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """반대 증거 단계 처리"""
        record = self.active_records[session_id]
        evidence = [e.strip() for e in user_message.split(",") if e.strip()]
        record.evidence_against = evidence if evidence else [user_message]
        record.current_step = "alternative_thought"

        # 인지 왜곡에 맞는 질문 제시
        challenging_questions = []
        for distortion in record.identified_distortions[:2]:
            info = self.distortion_detector.get_distortion_info(distortion)
            challenging_questions.extend(info.challenging_questions[:1])

        question_text = ""
        if challenging_questions:
            question_text = "\n\n도움이 될 수 있는 질문:\n"
            for q in challenging_questions[:3]:
                question_text += f"• {q}\n"

        response = f"""양쪽 증거를 모두 살펴봤어요.{question_text}

**[8단계: 대안적 사고]**

증거를 고려했을 때, **다른 방식**으로 이 상황을 볼 수 있을까요?
좀 더 **균형 잡힌 생각**은 어떤 것이 있을까요?

친한 친구가 같은 상황에 있다면 뭐라고 말해줄 것 같나요?"""

        return {
            "response": response,
            "current_step": "alternative_thought",
            "continue_conversation": True
        }

    def _process_alternative_thought(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """대안적 사고 단계 처리"""
        record = self.active_records[session_id]
        record.alternative_thoughts.append(user_message)
        record.current_step = "balanced_thought"

        response = f"""좋은 대안적 사고예요! 💡

**[9단계: 균형 잡힌 사고]**

원래 생각: "{record.hot_thought}"
대안적 사고: "{user_message}"

이 두 가지를 고려해서, 지금 상황에 대한
**균형 잡힌 한 문장**을 만들어 볼까요?

예시: "실수를 했지만, 그것이 나 전체를 정의하지는 않아.
다음에는 더 잘할 수 있어." """

        return {
            "response": response,
            "current_step": "balanced_thought",
            "continue_conversation": True
        }

    def _process_balanced_thought(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """균형 잡힌 사고 단계 처리"""
        record = self.active_records[session_id]
        record.balanced_thought = user_message
        record.current_step = "re_rate_emotions"

        emotion_names = [e.get("name", "감정") for e in record.emotions]
        emotion_list = ", ".join(emotion_names) if emotion_names else "처음에 느꼈던 감정"

        response = f"""훌륭한 균형 잡힌 사고예요! ✨

"{user_message}"

**[10단계: 감정 재평가]**

이 균형 잡힌 사고로 바라봤을 때,
처음에 느꼈던 감정({emotion_list})의 강도는 어떻게 변했나요?

다시 0-100%로 표현해 주세요."""

        return {
            "response": response,
            "current_step": "re_rate_emotions",
            "continue_conversation": True
        }

    def _process_re_rate_emotions(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """감정 재평가 단계 처리"""
        record = self.active_records[session_id]
        record.new_emotion_ratings = self._parse_emotions(user_message)
        record.current_step = "action_plan"

        response = """감정의 변화가 있으셨군요! 💙

**[11단계: 행동 계획]**

마지막으로, 앞으로 비슷한 상황에서
**어떻게 대처**하면 좋을까요?

혹은 지금 **작은 한 가지**를 할 수 있다면
무엇을 하고 싶으신가요?"""

        return {
            "response": response,
            "current_step": "action_plan",
            "continue_conversation": True
        }

    def _process_action_plan(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """행동 계획 단계 처리 및 완료"""
        record = self.active_records[session_id]
        record.action_plan = user_message
        record.completed = True

        # 요약 생성
        summary = self._generate_summary(record)

        # 세션 정리
        del self.active_records[session_id]

        response = f"""🎉 **사고 기록 완료!**

정말 잘 하셨어요. 자신의 생각을 이렇게 살펴보는 것은 쉽지 않은 일이에요.

{summary}

📌 **기억하세요:**
"{record.balanced_thought}"

힘든 생각이 들 때 이 균형 잡힌 사고를 떠올려 보세요.
언제든 다시 사고 기록을 해보고 싶으시면 말씀해 주세요. 💙"""

        return {
            "response": response,
            "record_completed": True,
            "summary": summary,
            "balanced_thought": record.balanced_thought,
            "continue_conversation": True
        }

    def _generate_summary(self, record: ThoughtRecord) -> str:
        """사고 기록 요약 생성"""
        # 감정 변화 계산
        emotion_change = ""
        if record.emotions and record.new_emotion_ratings:
            before = record.emotions[0].get("intensity", 0)
            after = record.new_emotion_ratings[0].get("intensity", 0) if record.new_emotion_ratings else before

            if isinstance(before, (int, float)) and isinstance(after, (int, float)):
                change = before - after
                if change > 0:
                    emotion_change = f"감정 강도가 {change}% 감소했어요."

        summary = f"""---
**📋 요약**

**상황**: {record.situation[:100]}...
**원래 생각**: {record.hot_thought}
**균형 잡힌 사고**: {record.balanced_thought}
**행동 계획**: {record.action_plan}
{emotion_change}
---"""

        return summary

    def _parse_emotions(self, text: str) -> List[Dict[str, Any]]:
        """감정 텍스트 파싱"""
        emotions = []

        # 패턴: "불안 80%" 또는 "불안(80%)" 또는 "불안 80"
        pattern = r"(\w+)\s*[:(]?\s*(\d+)\s*%?\)?"
        matches = re.findall(pattern, text)

        for name, intensity in matches:
            emotions.append({
                "name": name,
                "intensity": int(intensity)
            })

        # 패턴 매칭 실패 시 텍스트 그대로 저장
        if not emotions and text.strip():
            emotions.append({
                "name": text.strip(),
                "intensity": 50  # 기본값
            })

        return emotions

    def _end_record(self, session_id: str, interrupted: bool = False) -> Dict[str, Any]:
        """사고 기록 종료"""
        if session_id in self.active_records:
            del self.active_records[session_id]

        if interrupted:
            response = """괜찮아요, 나중에 다시 해볼 수 있어요.

지금은 그냥 이야기를 나눠볼까요?
어떤 것이든 편하게 말씀해 주세요. 💙"""
        else:
            response = "사고 기록을 마쳤습니다. 계속 이야기를 나눠볼까요?"

        return {
            "response": response,
            "record_ended": True,
            "interrupted": interrupted,
            "continue_conversation": True
        }

    def get_distortion_info_for_user(self, distortion_type: str) -> str:
        """사용자에게 인지 왜곡 설명"""
        try:
            dt = CognitiveDistortion(distortion_type)
            info = self.distortion_detector.get_distortion_info(dt)

            return f"""💭 **{info.korean_name}**

{info.description}

**예시**: {info.example}

**스스로에게 물어볼 질문**:
{chr(10).join(['• ' + q for q in info.challenging_questions])}"""

        except ValueError:
            return "해당 인지 왜곡 정보를 찾을 수 없습니다."


# 사용 예시
if __name__ == "__main__":
    system = IntegratedCBTChat()

    # 부정적 사고 감지 테스트
    result = system.process_message(
        "session_1",
        "나는 항상 실패해... 이번 프로젝트도 망할 거야. 다들 나를 무능하다고 생각할 거야."
    )
    print("=== CBT 제안 ===")
    print(result["response"])

    # 인지 왜곡 정보
    print("\n=== 인지 왜곡 정보 ===")
    print(system.get_distortion_info_for_user("overgeneralization"))
