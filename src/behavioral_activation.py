# -*- coding: utf-8 -*-
"""
행동 활성화 모듈 (Behavioral Activation Module)

우울증과 무기력 상태에서 활동 일정, 즐거운 활동 계획,
성취감 있는 활동 추적을 통해 기분 개선을 돕습니다.

Author: MindVridge AI Team
Version: 1.0.0
"""

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple


class ActivityCategory(Enum):
    """활동 카테고리"""
    PLEASURE = "pleasure"               # 즐거운 활동
    MASTERY = "mastery"                 # 성취 활동
    SOCIAL = "social"                   # 사회적 활동
    PHYSICAL = "physical"               # 신체 활동
    SELF_CARE = "self_care"            # 자기 관리
    CREATIVE = "creative"               # 창의적 활동
    NATURE = "nature"                   # 자연/야외 활동
    RELAXATION = "relaxation"           # 이완 활동


class DifficultyLevel(Enum):
    """난이도 수준"""
    VERY_EASY = "very_easy"             # 매우 쉬움 (5분 이내)
    EASY = "easy"                       # 쉬움 (15분 이내)
    MODERATE = "moderate"               # 중간 (30분-1시간)
    CHALLENGING = "challenging"         # 도전적 (1시간 이상)


class MoodLevel(Enum):
    """기분 수준"""
    VERY_LOW = 1
    LOW = 2
    NEUTRAL = 3
    GOOD = 4
    VERY_GOOD = 5


@dataclass
class Activity:
    """활동 정의"""
    activity_id: str
    name: str
    category: ActivityCategory
    description: str
    difficulty: DifficultyLevel
    duration_minutes: int
    required_energy: int              # 1-5
    expected_pleasure: int            # 1-5
    expected_mastery: int             # 1-5
    tips: List[str]
    modifications_low_energy: List[str]  # 에너지 낮을 때 변형


@dataclass
class ActivityLog:
    """활동 기록"""
    log_id: str
    user_id: str
    activity_name: str
    timestamp: datetime
    planned_time: Optional[datetime] = None
    completed: bool = False
    mood_before: Optional[int] = None
    mood_after: Optional[int] = None
    pleasure_rating: Optional[int] = None  # 1-10
    mastery_rating: Optional[int] = None   # 1-10
    notes: str = ""


@dataclass
class WeeklyPlan:
    """주간 활동 계획"""
    user_id: str
    week_start: datetime
    planned_activities: List[Dict[str, Any]] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)


@dataclass
class BehavioralActivationSession:
    """행동 활성화 세션"""
    session_id: str
    user_id: str
    current_step: str = "assessment"
    mood_level: Optional[int] = None
    energy_level: Optional[int] = None
    identified_barriers: List[str] = field(default_factory=list)
    suggested_activities: List[Activity] = field(default_factory=list)
    chosen_activity: Optional[Activity] = None
    started_at: datetime = field(default_factory=datetime.now)


class ActivityLibrary:
    """활동 라이브러리"""

    def __init__(self):
        self.activities = self._initialize_activities()

    def _initialize_activities(self) -> List[Activity]:
        """활동 목록 초기화"""
        return [
            # 매우 쉬운 활동 (에너지 낮을 때도 가능)
            Activity(
                activity_id="act_001",
                name="창문 열고 바깥 공기 마시기",
                category=ActivityCategory.SELF_CARE,
                description="창문을 열고 2분간 신선한 공기를 들이마셔 보세요.",
                difficulty=DifficultyLevel.VERY_EASY,
                duration_minutes=2,
                required_energy=1,
                expected_pleasure=3,
                expected_mastery=2,
                tips=["눈을 감고 해보세요", "깊게 숨을 쉬어보세요"],
                modifications_low_energy=["침대에서 해도 괜찮아요"]
            ),
            Activity(
                activity_id="act_002",
                name="좋아하는 음악 한 곡 듣기",
                category=ActivityCategory.PLEASURE,
                description="마음에 드는 음악을 골라 집중해서 들어보세요.",
                difficulty=DifficultyLevel.VERY_EASY,
                duration_minutes=5,
                required_energy=1,
                expected_pleasure=4,
                expected_mastery=2,
                tips=["가사에 집중해보세요", "리듬에 맞춰 몸을 움직여봐도 좋아요"],
                modifications_low_energy=["누워서 이어폰으로 들어도 돼요"]
            ),
            Activity(
                activity_id="act_003",
                name="따뜻한 물로 손 씻기",
                category=ActivityCategory.SELF_CARE,
                description="따뜻한 물로 천천히 손을 씻으며 감각에 집중하세요.",
                difficulty=DifficultyLevel.VERY_EASY,
                duration_minutes=3,
                required_energy=1,
                expected_pleasure=3,
                expected_mastery=2,
                tips=["좋은 향의 비누를 사용해보세요", "물의 온도를 느껴보세요"],
                modifications_low_energy=["손 대신 얼굴만 씻어도 돼요"]
            ),
            Activity(
                activity_id="act_004",
                name="3분 스트레칭",
                category=ActivityCategory.PHYSICAL,
                description="간단한 스트레칭으로 몸을 풀어주세요.",
                difficulty=DifficultyLevel.VERY_EASY,
                duration_minutes=3,
                required_energy=2,
                expected_pleasure=3,
                expected_mastery=3,
                tips=["목, 어깨, 팔 순서로", "무리하지 마세요"],
                modifications_low_energy=["앉아서 목과 어깨만 돌려도 좋아요"]
            ),

            # 쉬운 활동
            Activity(
                activity_id="act_005",
                name="정리정돈하기 (책상 또는 작은 공간)",
                category=ActivityCategory.MASTERY,
                description="작은 공간 하나를 정리해 보세요.",
                difficulty=DifficultyLevel.EASY,
                duration_minutes=10,
                required_energy=2,
                expected_pleasure=3,
                expected_mastery=4,
                tips=["서랍 하나만 정리해도 충분해요", "불필요한 것은 과감히 버리세요"],
                modifications_low_energy=["핸드폰 사진만 정리해도 괜찮아요"]
            ),
            Activity(
                activity_id="act_006",
                name="친구/가족에게 메시지 보내기",
                category=ActivityCategory.SOCIAL,
                description="소중한 사람에게 짧은 안부 메시지를 보내세요.",
                difficulty=DifficultyLevel.EASY,
                duration_minutes=5,
                required_energy=2,
                expected_pleasure=4,
                expected_mastery=3,
                tips=["'오늘 뭐해?'처럼 간단하게 시작하세요", "이모티콘 하나도 좋아요"],
                modifications_low_energy=["짧은 이모티콘 하나만 보내도 충분해요"]
            ),
            Activity(
                activity_id="act_007",
                name="좋아하는 음료 만들어 마시기",
                category=ActivityCategory.PLEASURE,
                description="커피, 차, 또는 좋아하는 음료를 직접 만들어 마셔보세요.",
                difficulty=DifficultyLevel.EASY,
                duration_minutes=10,
                required_energy=2,
                expected_pleasure=4,
                expected_mastery=3,
                tips=["만드는 과정을 즐기세요", "특별한 컵을 사용해보세요"],
                modifications_low_energy=["물 한 잔이라도 괜찮아요"]
            ),
            Activity(
                activity_id="act_008",
                name="10분 산책",
                category=ActivityCategory.PHYSICAL,
                description="집 근처를 가볍게 걸어보세요.",
                difficulty=DifficultyLevel.EASY,
                duration_minutes=10,
                required_energy=2,
                expected_pleasure=4,
                expected_mastery=3,
                tips=["날씨를 느끼며 걸어보세요", "목적지 없이 걸어도 좋아요"],
                modifications_low_energy=["베란다나 복도만 걸어도 충분해요"]
            ),

            # 중간 활동
            Activity(
                activity_id="act_009",
                name="요리하기 (간단한 음식)",
                category=ActivityCategory.MASTERY,
                description="좋아하는 간단한 음식을 만들어 보세요.",
                difficulty=DifficultyLevel.MODERATE,
                duration_minutes=30,
                required_energy=3,
                expected_pleasure=4,
                expected_mastery=4,
                tips=["간단한 레시피부터 시작하세요", "만드는 과정을 즐기세요"],
                modifications_low_energy=["라면에 계란 하나 추가하는 것도 요리예요"]
            ),
            Activity(
                activity_id="act_010",
                name="영화/드라마 한 편 보기",
                category=ActivityCategory.PLEASURE,
                description="좋아하는 영화나 드라마를 집중해서 시청하세요.",
                difficulty=DifficultyLevel.MODERATE,
                duration_minutes=60,
                required_energy=2,
                expected_pleasure=5,
                expected_mastery=2,
                tips=["스마트폰을 멀리 두세요", "좋아하는 장르를 선택하세요"],
                modifications_low_energy=["짧은 유튜브 영상도 좋아요"]
            ),
            Activity(
                activity_id="act_011",
                name="친구와 통화하기",
                category=ActivityCategory.SOCIAL,
                description="친구나 가족과 전화 통화를 해보세요.",
                difficulty=DifficultyLevel.MODERATE,
                duration_minutes=20,
                required_energy=3,
                expected_pleasure=4,
                expected_mastery=3,
                tips=["부담 없이 안부만 물어도 좋아요", "듣는 것도 대화예요"],
                modifications_low_energy=["음성 메시지를 보내는 것도 좋아요"]
            ),
            Activity(
                activity_id="act_012",
                name="그림/색칠하기",
                category=ActivityCategory.CREATIVE,
                description="그림을 그리거나 색칠공부를 해보세요.",
                difficulty=DifficultyLevel.MODERATE,
                duration_minutes=30,
                required_energy=2,
                expected_pleasure=4,
                expected_mastery=3,
                tips=["잘 그리려고 하지 마세요", "색칠공부 앱도 있어요"],
                modifications_low_energy=["낙서도 창작이에요"]
            ),
            Activity(
                activity_id="act_013",
                name="공원 산책",
                category=ActivityCategory.NATURE,
                description="가까운 공원에서 자연을 느끼며 걸어보세요.",
                difficulty=DifficultyLevel.MODERATE,
                duration_minutes=30,
                required_energy=3,
                expected_pleasure=5,
                expected_mastery=3,
                tips=["벤치에 앉아 쉬어도 좋아요", "나무와 꽃을 관찰해보세요"],
                modifications_low_energy=["창문 근처 햇빛 쬐기도 좋아요"]
            ),

            # 도전적 활동
            Activity(
                activity_id="act_014",
                name="운동하기 (30분 이상)",
                category=ActivityCategory.PHYSICAL,
                description="조깅, 헬스, 수영 등 활발한 운동을 해보세요.",
                difficulty=DifficultyLevel.CHALLENGING,
                duration_minutes=45,
                required_energy=4,
                expected_pleasure=4,
                expected_mastery=5,
                tips=["무리하지 말고 본인 페이스로", "운동 후 성취감을 느껴보세요"],
                modifications_low_energy=["홈트레이닝 영상 따라하기로 시작"]
            ),
            Activity(
                activity_id="act_015",
                name="새로운 것 배우기",
                category=ActivityCategory.MASTERY,
                description="온라인 강의나 유튜브로 새로운 것을 배워보세요.",
                difficulty=DifficultyLevel.CHALLENGING,
                duration_minutes=60,
                required_energy=4,
                expected_pleasure=4,
                expected_mastery=5,
                tips=["관심 있던 분야를 선택하세요", "작은 목표부터 시작하세요"],
                modifications_low_energy=["5분짜리 영상 하나만 봐도 배움이에요"]
            ),
            Activity(
                activity_id="act_016",
                name="사람들 모임 참석하기",
                category=ActivityCategory.SOCIAL,
                description="동호회, 모임 등에 참석해 보세요.",
                difficulty=DifficultyLevel.CHALLENGING,
                duration_minutes=120,
                required_energy=4,
                expected_pleasure=4,
                expected_mastery=4,
                tips=["관심 있는 주제의 모임을 찾아보세요", "일찍 가서 먼저 도착한 사람과 대화해보세요"],
                modifications_low_energy=["온라인 모임도 좋은 시작이에요"]
            ),
            Activity(
                activity_id="act_017",
                name="자원봉사하기",
                category=ActivityCategory.MASTERY,
                description="지역사회 봉사 활동에 참여해 보세요.",
                difficulty=DifficultyLevel.CHALLENGING,
                duration_minutes=120,
                required_energy=4,
                expected_pleasure=4,
                expected_mastery=5,
                tips=["관심 있는 분야를 선택하세요", "작은 것부터 시작해도 좋아요"],
                modifications_low_energy=["온라인 멘토링도 봉사예요"]
            )
        ]

    def get_activities_by_energy(self, max_energy: int) -> List[Activity]:
        """에너지 수준에 맞는 활동들"""
        return [a for a in self.activities if a.required_energy <= max_energy]

    def get_activities_by_category(self, category: ActivityCategory) -> List[Activity]:
        """카테고리별 활동들"""
        return [a for a in self.activities if a.category == category]

    def get_activities_by_time(self, max_minutes: int) -> List[Activity]:
        """시간에 맞는 활동들"""
        return [a for a in self.activities if a.duration_minutes <= max_minutes]

    def get_very_easy_activities(self) -> List[Activity]:
        """매우 쉬운 활동들 (우울할 때 시작점)"""
        return [a for a in self.activities if a.difficulty == DifficultyLevel.VERY_EASY]


class BehavioralActivationTriggerDetector:
    """행동 활성화 필요 상황 감지"""

    def __init__(self):
        self.depression_keywords = [
            "우울", "무기력", "아무것도 하기 싫", "의욕이 없",
            "귀찮", "힘들", "하루종일 누워", "아무것도 못",
            "재미가 없", "즐거운 게 없"
        ]

        self.avoidance_keywords = [
            "피하", "회피", "안 나가", "못 나가", "집에만",
            "사람 만나기 싫", "혼자", "고립", "숨고 싶"
        ]

        self.low_energy_keywords = [
            "기운이 없", "에너지가 없", "힘이 없", "지침",
            "피로", "기력", "몸이 무거", "일어나기 힘들"
        ]

    def detect(self, message: str, mood_history: Optional[List[int]] = None) -> Dict[str, Any]:
        """행동 활성화 필요 상황 감지"""
        message_lower = message.lower()

        triggers = {
            "depression_signs": self._check_keywords(message_lower, self.depression_keywords),
            "avoidance_patterns": self._check_keywords(message_lower, self.avoidance_keywords),
            "low_energy": self._check_keywords(message_lower, self.low_energy_keywords)
        }

        # 최근 기분 기록 확인
        if mood_history:
            avg_mood = sum(mood_history[-5:]) / min(len(mood_history), 5)
            triggers["chronic_low_mood"] = {"detected": avg_mood < 2.5, "average": avg_mood}
        else:
            triggers["chronic_low_mood"] = {"detected": False}

        should_suggest = any(t["detected"] for t in triggers.values())

        return {
            "should_suggest": should_suggest,
            "triggers": triggers,
            "severity": self._assess_severity(triggers),
            "recommended_approach": self._recommend_approach(triggers)
        }

    def _check_keywords(self, message: str, keywords: List[str]) -> Dict[str, Any]:
        """키워드 매칭"""
        matches = [kw for kw in keywords if kw in message]
        return {
            "detected": len(matches) > 0,
            "matches": matches,
            "confidence": min(len(matches) * 0.3, 0.9)
        }

    def _assess_severity(self, triggers: Dict) -> str:
        """심각도 평가"""
        detected_count = sum(1 for t in triggers.values() if t.get("detected", False))
        if detected_count >= 3:
            return "high"
        elif detected_count >= 2:
            return "moderate"
        elif detected_count >= 1:
            return "mild"
        return "none"

    def _recommend_approach(self, triggers: Dict) -> str:
        """접근 방식 추천"""
        if triggers["low_energy"]["detected"]:
            return "ultra_low"  # 매우 작은 활동부터
        elif triggers["depression_signs"]["detected"]:
            return "gentle"     # 부드러운 시작
        elif triggers["avoidance_patterns"]["detected"]:
            return "gradual"    # 점진적 노출
        return "standard"


class IntegratedBehavioralActivation:
    """채팅 통합형 행동 활성화 시스템"""

    def __init__(self):
        self.trigger_detector = BehavioralActivationTriggerDetector()
        self.activity_library = ActivityLibrary()
        self.active_sessions: Dict[str, BehavioralActivationSession] = {}
        self.user_logs: Dict[str, List[ActivityLog]] = {}

    def process_message(
        self,
        session_id: str,
        user_message: str,
        mood_history: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """사용자 메시지 처리"""

        # 진행 중인 세션 확인
        if session_id in self.active_sessions:
            return self._handle_active_session(session_id, user_message)

        # 행동 활성화 필요 상황 감지
        trigger_result = self.trigger_detector.detect(user_message, mood_history)

        if trigger_result["should_suggest"]:
            return self._suggest_behavioral_activation(session_id, trigger_result)

        return {
            "ba_suggested": False,
            "response": None,
            "continue_conversation": True
        }

    def _suggest_behavioral_activation(
        self,
        session_id: str,
        trigger_result: Dict
    ) -> Dict[str, Any]:
        """행동 활성화 제안"""
        severity = trigger_result["severity"]
        approach = trigger_result["recommended_approach"]

        # 심각도에 따른 공감 메시지
        if severity == "high":
            empathy = "정말 힘드시겠어요. 아무것도 하고 싶지 않은 마음, 충분히 이해해요."
        elif severity == "moderate":
            empathy = "의욕이 없고 무기력한 느낌이 드시는군요."
        else:
            empathy = "좀 처지는 기분이시네요."

        # 접근 방식에 따른 제안
        if approach == "ultra_low":
            activity_hint = "아주 작은 것부터 시작해 볼까요? 창문 열기 같은 2분짜리 활동도 있어요."
        else:
            activity_hint = "기분이 조금이라도 나아질 수 있는 활동을 함께 찾아볼까요?"

        response = f"""{empathy}

🌱 **행동 활성화**라는 방법이 있어요.
우울할 때는 아무것도 하기 싫지만,
아주 작은 활동이라도 하면 기분이 조금씩 나아질 수 있어요.

{activity_hint}

함께 해보시겠어요? (네/아니요)"""

        return {
            "ba_suggested": True,
            "approach": approach,
            "severity": severity,
            "response": response,
            "continue_conversation": True,
            "awaiting_acceptance": True
        }

    def start_session(
        self,
        session_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """행동 활성화 세션 시작"""
        self.active_sessions[session_id] = BehavioralActivationSession(
            session_id=session_id,
            user_id=user_id,
            current_step="energy_check"
        )

        response = """좋아요, 함께 해볼게요! 🌱

먼저 지금 상태를 확인해 볼게요.

**지금 에너지 수준은 어떠세요?**
1️⃣ 매우 낮음 (움직이기 힘들어요)
2️⃣ 낮음 (귀찮지만 조금은 할 수 있어요)
3️⃣ 보통 (무난해요)
4️⃣ 괜찮음 (활동적이에요)
5️⃣ 높음 (에너지가 넘쳐요)

숫자로 답해주세요."""

        return {
            "session_started": True,
            "response": response,
            "current_step": "energy_check",
            "continue_conversation": True
        }

    def _handle_active_session(
        self,
        session_id: str,
        user_message: str
    ) -> Dict[str, Any]:
        """진행 중인 세션 처리"""
        session = self.active_sessions[session_id]
        message_lower = user_message.lower().strip()

        # 중단 요청
        if any(word in message_lower for word in ["그만", "취소", "안 할래"]):
            return self._end_session(session_id, interrupted=True)

        # 단계별 처리
        step_handlers = {
            "energy_check": self._process_energy_check,
            "mood_check": self._process_mood_check,
            "time_check": self._process_time_check,
            "activity_suggestion": self._process_activity_choice,
            "commitment": self._process_commitment,
            "after_activity": self._process_after_activity
        }

        handler = step_handlers.get(session.current_step)
        if handler:
            return handler(session_id, user_message)

        return {
            "response": "어떤 활동을 해보고 싶으신가요?",
            "continue_conversation": True
        }

    def _process_energy_check(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """에너지 체크"""
        session = self.active_sessions[session_id]

        # 숫자 파싱
        try:
            energy = int(''.join(filter(str.isdigit, user_message)))
            energy = max(1, min(5, energy))
        except:
            energy = 2  # 기본값

        session.energy_level = energy
        session.current_step = "mood_check"

        energy_messages = {
            1: "많이 힘드시군요. 아주 작은 것부터 시작할게요.",
            2: "조금 지치셨네요. 부담 없는 활동을 찾아볼게요.",
            3: "보통이시군요. 적당한 활동을 추천해 드릴게요.",
            4: "에너지가 괜찮으시네요! 좋은 활동들이 있어요.",
            5: "에너지가 넘치시네요! 도전적인 활동도 가능할 것 같아요."
        }

        response = f"""{energy_messages.get(energy, '')}

**지금 기분은 어떠세요?**
1️⃣ 매우 안 좋음
2️⃣ 안 좋음
3️⃣ 보통
4️⃣ 좋음
5️⃣ 매우 좋음

숫자로 답해주세요."""

        return {
            "response": response,
            "energy_level": energy,
            "continue_conversation": True
        }

    def _process_mood_check(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """기분 체크"""
        session = self.active_sessions[session_id]

        try:
            mood = int(''.join(filter(str.isdigit, user_message)))
            mood = max(1, min(5, mood))
        except:
            mood = 2

        session.mood_level = mood
        session.current_step = "time_check"

        response = """알겠어요.

**지금 활동에 쓸 수 있는 시간은 얼마나 되세요?**
1️⃣ 5분 이내
2️⃣ 15분 정도
3️⃣ 30분 정도
4️⃣ 1시간 정도
5️⃣ 시간 여유 있어요

숫자로 답해주세요."""

        return {
            "response": response,
            "mood_level": mood,
            "continue_conversation": True
        }

    def _process_time_check(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """시간 체크 및 활동 추천"""
        session = self.active_sessions[session_id]

        time_map = {1: 5, 2: 15, 3: 30, 4: 60, 5: 120}
        try:
            time_choice = int(''.join(filter(str.isdigit, user_message)))
            available_minutes = time_map.get(time_choice, 15)
        except:
            available_minutes = 15

        # 에너지와 시간에 맞는 활동 필터링
        energy = session.energy_level or 2
        activities = self.activity_library.get_activities_by_energy(energy)
        activities = [a for a in activities if a.duration_minutes <= available_minutes]

        # 상위 3개 추천
        if energy <= 2:
            # 에너지 낮을 때는 매우 쉬운 것 우선
            activities.sort(key=lambda a: a.required_energy)
        else:
            # 즐거움과 성취감 균형
            activities.sort(key=lambda a: a.expected_pleasure + a.expected_mastery, reverse=True)

        suggested = activities[:3]
        session.suggested_activities = suggested
        session.current_step = "activity_suggestion"

        if not suggested:
            suggested = self.activity_library.get_very_easy_activities()[:3]
            session.suggested_activities = suggested

        activity_list = ""
        for i, act in enumerate(suggested, 1):
            category_emoji = {
                ActivityCategory.PLEASURE: "😊",
                ActivityCategory.MASTERY: "🏆",
                ActivityCategory.SOCIAL: "👥",
                ActivityCategory.PHYSICAL: "🏃",
                ActivityCategory.SELF_CARE: "💆",
                ActivityCategory.CREATIVE: "🎨",
                ActivityCategory.NATURE: "🌿",
                ActivityCategory.RELAXATION: "😌"
            }
            emoji = category_emoji.get(act.category, "✨")
            activity_list += f"\n{i}️⃣ {emoji} **{act.name}** ({act.duration_minutes}분)\n   {act.description}\n"

        response = f"""좋아요, 맞춤 활동을 찾았어요! 🌟

{activity_list}

어떤 활동을 해보시겠어요? (1, 2, 3 중 선택)
또는 '다른 거'라고 하시면 다른 활동을 보여드릴게요."""

        return {
            "response": response,
            "suggested_activities": [a.name for a in suggested],
            "continue_conversation": True
        }

    def _process_activity_choice(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """활동 선택"""
        session = self.active_sessions[session_id]
        message_lower = user_message.lower()

        # 다른 활동 요청
        if "다른" in message_lower:
            # 현재 추천 제외하고 다시 추천
            current_ids = [a.activity_id for a in session.suggested_activities]
            all_activities = self.activity_library.get_activities_by_energy(session.energy_level or 2)
            other_activities = [a for a in all_activities if a.activity_id not in current_ids]

            if other_activities:
                session.suggested_activities = other_activities[:3]
                return self._format_activity_suggestions(session_id)

        # 숫자 선택
        try:
            choice = int(''.join(filter(str.isdigit, user_message)))
            if 1 <= choice <= len(session.suggested_activities):
                chosen = session.suggested_activities[choice - 1]
                session.chosen_activity = chosen
                session.current_step = "commitment"

                tips_text = "\n".join([f"• {tip}" for tip in chosen.tips[:2]])

                response = f"""좋은 선택이에요! 👍

**{chosen.name}**

{chosen.description}

💡 **팁:**
{tips_text}

지금 바로 해보시겠어요?
(네/나중에)"""

                return {
                    "response": response,
                    "chosen_activity": chosen.name,
                    "continue_conversation": True
                }
        except:
            pass

        return {
            "response": "1, 2, 3 중에서 선택해 주세요. 또는 '다른 거'라고 해주세요.",
            "continue_conversation": True
        }

    def _format_activity_suggestions(self, session_id: str) -> Dict[str, Any]:
        """활동 추천 포맷팅"""
        session = self.active_sessions[session_id]

        activity_list = ""
        for i, act in enumerate(session.suggested_activities, 1):
            activity_list += f"\n{i}️⃣ **{act.name}** ({act.duration_minutes}분)\n   {act.description}\n"

        return {
            "response": f"다른 활동을 찾았어요!\n{activity_list}\n어떤 활동을 해보시겠어요?",
            "continue_conversation": True
        }

    def _process_commitment(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """활동 약속"""
        session = self.active_sessions[session_id]
        message_lower = user_message.lower()

        if any(word in message_lower for word in ["네", "응", "할게", "좋아", "지금"]):
            session.current_step = "after_activity"

            activity = session.chosen_activity
            low_energy_tip = ""
            if session.energy_level and session.energy_level <= 2:
                if activity.modifications_low_energy:
                    low_energy_tip = f"\n\n💜 **에너지가 낮을 때:** {activity.modifications_low_energy[0]}"

            response = f"""좋아요! 👏

{activity.name}을 시작해 보세요.

{activity.description}{low_energy_tip}

끝나면 '다 했어요' 또는 '끝'이라고 말씀해 주세요.

작은 시작도 큰 의미가 있어요. 화이팅! 🌟"""

            return {
                "response": response,
                "activity_started": True,
                "continue_conversation": True
            }

        elif any(word in message_lower for word in ["나중", "다음", "못"]):
            response = """괜찮아요, 나중에 해도 충분해요.

기억해 두셨다가 마음이 동할 때 해보세요.
작은 한 발짝도 소중한 시작이에요. 💙

다른 이야기를 나눠볼까요?"""

            del self.active_sessions[session_id]

            return {
                "response": response,
                "session_ended": True,
                "continue_conversation": True
            }

        return {
            "response": "지금 해보시겠어요? '네' 또는 '나중에'로 답해주세요.",
            "continue_conversation": True
        }

    def _process_after_activity(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """활동 후 체크"""
        session = self.active_sessions[session_id]
        message_lower = user_message.lower()

        if any(word in message_lower for word in ["끝", "했어", "완료", "다 했"]):
            response = f"""🎉 해내셨어요! 정말 잘하셨어요!

**{session.chosen_activity.name}**을 완료하셨네요.

지금 기분이 어떠세요?
아까보다 조금이라도 나아지셨나요?

1️⃣ 많이 좋아졌어요
2️⃣ 조금 나아졌어요
3️⃣ 비슷해요
4️⃣ 더 안 좋아졌어요

숫자로 답해주세요."""

            session.current_step = "feedback"

            return {
                "response": response,
                "activity_completed": True,
                "continue_conversation": True
            }

        # 피드백 단계
        if session.current_step == "feedback":
            try:
                feedback = int(''.join(filter(str.isdigit, user_message)))
            except:
                feedback = 2

            # 세션 종료 및 로그 저장
            del self.active_sessions[session_id]

            if feedback <= 2:
                response = """좋아지셨다니 정말 다행이에요! 💙

작은 활동이 기분에 변화를 줄 수 있다는 것을 경험하셨네요.
내일도 작은 것 하나 해보시는 건 어떨까요?

잘 하셨어요! 🌟"""
            else:
                response = """활동을 완료하셨다는 것 자체가 대단한 거예요. 💙

기분이 바로 나아지지 않을 수도 있어요.
하지만 작은 활동들이 쌓이면 점점 변화가 생길 거예요.

오늘 자신을 위해 한 걸음 내디딘 것, 기억해 주세요. 🌱"""

            return {
                "response": response,
                "session_completed": True,
                "continue_conversation": True
            }

        return {
            "response": "활동을 마치시면 '다 했어요'라고 말씀해 주세요.",
            "continue_conversation": True
        }

    def _end_session(self, session_id: str, interrupted: bool = False) -> Dict[str, Any]:
        """세션 종료"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

        if interrupted:
            response = """괜찮아요, 언제든 다시 할 수 있어요.
작은 활동이라도 해보고 싶을 때 말씀해 주세요. 💙"""
        else:
            response = "활동 계획을 마쳤습니다. 다른 이야기를 나눠볼까요?"

        return {
            "response": response,
            "session_ended": True,
            "interrupted": interrupted,
            "continue_conversation": True
        }

    def get_quick_activity_for_energy(self, energy_level: int) -> Activity:
        """에너지 수준에 맞는 빠른 활동 추천"""
        activities = self.activity_library.get_activities_by_energy(energy_level)
        # 가장 짧고 쉬운 것
        activities.sort(key=lambda a: (a.duration_minutes, a.required_energy))
        return activities[0] if activities else None

    def get_activity_menu(self) -> Dict[str, List[Dict]]:
        """활동 메뉴"""
        menu = {}
        for category in ActivityCategory:
            activities = self.activity_library.get_activities_by_category(category)
            menu[category.value] = [
                {
                    "name": a.name,
                    "duration": a.duration_minutes,
                    "energy_required": a.required_energy,
                    "description": a.description
                }
                for a in activities
            ]
        return menu


# 사용 예시
if __name__ == "__main__":
    system = IntegratedBehavioralActivation()

    # 감지 테스트
    result = system.process_message(
        "session_1",
        "아무것도 하기 싫어요... 하루종일 누워만 있고 의욕이 없어요"
    )
    print("=== 행동 활성화 제안 ===")
    print(result["response"])

    # 빠른 활동 추천
    print("\n=== 에너지 낮을 때 추천 활동 ===")
    quick = system.get_quick_activity_for_energy(1)
    if quick:
        print(f"- {quick.name} ({quick.duration_minutes}분)")
        print(f"  {quick.description}")

    # 활동 메뉴
    print("\n=== 활동 카테고리 ===")
    menu = system.get_activity_menu()
    for category, activities in menu.items():
        print(f"\n{category}:")
        for act in activities[:2]:
            print(f"  - {act['name']} ({act['duration']}분)")
