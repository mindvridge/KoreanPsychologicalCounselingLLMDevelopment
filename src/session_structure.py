"""
세션 구조 관리 시스템 (Session Structure Management System)

상담 세션의 단계별 구조화:
1. 시작 단계 (Opening) - 라포 형성, 안건 설정
2. 탐색 단계 (Exploration) - 문제 탐색, 감정 작업
3. 작업 단계 (Working/Intervention) - 기법 적용, 통찰 촉진
4. 마무리 단계 (Closing) - 요약, 과제 설정, 다음 세션 예고

세션 전환 관리 및 최적 타이밍 안내
"""

from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass, field
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# =============================================================================
# 세션 단계 및 데이터 구조
# =============================================================================

class SessionPhase(Enum):
    """세션 단계"""
    OPENING = "opening"              # 시작 (5-10분)
    EXPLORATION = "exploration"      # 탐색 (15-20분)
    WORKING = "working"              # 작업 (15-25분)
    CLOSING = "closing"              # 마무리 (5-10분)


class PhaseTask(Enum):
    """단계별 과제"""
    # Opening
    GREETING = "greeting"
    CHECK_IN = "check_in"
    AGENDA_SETTING = "agenda_setting"
    BRIDGE_PREVIOUS = "bridge_previous"

    # Exploration
    PROBLEM_EXPLORATION = "problem_exploration"
    EMOTION_EXPLORATION = "emotion_exploration"
    PATTERN_RECOGNITION = "pattern_recognition"
    CONTEXT_GATHERING = "context_gathering"

    # Working
    INTERVENTION = "intervention"
    INSIGHT_FACILITATION = "insight_facilitation"
    SKILL_BUILDING = "skill_building"
    COGNITIVE_WORK = "cognitive_work"

    # Closing
    SUMMARIZING = "summarizing"
    HOMEWORK_ASSIGNMENT = "homework_assignment"
    NEXT_SESSION_PREVIEW = "next_session_preview"
    FEEDBACK_COLLECTION = "feedback_collection"


@dataclass
class PhaseProgress:
    """단계 진행 상황"""
    phase: SessionPhase
    started_at: Optional[datetime] = None
    completed_tasks: List[PhaseTask] = field(default_factory=list)
    pending_tasks: List[PhaseTask] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    completion_percentage: float = 0.0


@dataclass
class SessionState:
    """세션 상태"""
    session_id: str = ""
    session_number: int = 1
    current_phase: SessionPhase = SessionPhase.OPENING
    turn_count: int = 0
    started_at: Optional[datetime] = None
    estimated_duration: int = 50  # 분
    phase_history: List[PhaseProgress] = field(default_factory=list)
    main_topics: List[str] = field(default_factory=list)
    key_emotions: List[str] = field(default_factory=list)
    insights_generated: List[str] = field(default_factory=list)
    homework_assigned: List[str] = field(default_factory=list)
    crisis_detected: bool = False


# =============================================================================
# 단계별 가이드
# =============================================================================

class PhaseGuide:
    """단계별 가이드 및 템플릿"""

    # 시작 단계 (Opening)
    OPENING_GUIDE = {
        "goals": [
            "편안한 분위기 조성",
            "내담자의 현재 상태 확인",
            "오늘 세션의 주제/안건 설정",
            "이전 세션과의 연결 (재방문 시)",
        ],
        "tasks": {
            PhaseTask.GREETING: {
                "description": "따뜻한 인사와 환영",
                "templates": [
                    "안녕하세요, 오늘도 찾아와 주셨네요.",
                    "반가워요, 어떻게 지내셨어요?",
                    "오늘 만나 뵙게 되어 기뻐요.",
                ],
                "new_client": [
                    "처음 오셨군요, 반갑습니다.",
                    "용기 내어 찾아와 주셔서 감사해요.",
                    "편하게 말씀해 주시면 돼요.",
                ]
            },
            PhaseTask.CHECK_IN: {
                "description": "현재 상태 확인",
                "templates": [
                    "오늘 기분은 어떠세요?",
                    "이번 주는 어떻게 지내셨어요?",
                    "지금 마음이 어떠세요?",
                    "몸 상태는 어떠신가요?",
                ]
            },
            PhaseTask.AGENDA_SETTING: {
                "description": "오늘 주제 설정",
                "templates": [
                    "오늘은 어떤 이야기를 나누고 싶으세요?",
                    "특별히 다루고 싶은 주제가 있으신가요?",
                    "오늘 대화에서 어떤 것이 도움이 되면 좋겠어요?",
                    "무엇에 대해 이야기하면 좋을까요?",
                ]
            },
            PhaseTask.BRIDGE_PREVIOUS: {
                "description": "이전 세션 연결",
                "templates": [
                    "지난번에 {topic}에 대해 이야기 나눴는데, 그 후로 어떠셨어요?",
                    "지난 세션 이후에 변화가 있으셨나요?",
                    "저번에 말씀하신 {homework}, 해보셨어요?",
                ]
            }
        },
        "transition_cues": [
            "안건이 설정됨",
            "주요 주제가 언급됨",
            "내담자가 구체적 이야기 시작",
        ],
        "typical_duration": (5, 10)  # 분
    }

    # 탐색 단계 (Exploration)
    EXPLORATION_GUIDE = {
        "goals": [
            "문제/상황에 대한 깊은 이해",
            "감정의 탐색과 표현 촉진",
            "패턴과 맥락 파악",
            "내담자의 관점 이해",
        ],
        "tasks": {
            PhaseTask.PROBLEM_EXPLORATION: {
                "description": "문제 상황 탐색",
                "templates": [
                    "조금 더 자세히 말씀해 주시겠어요?",
                    "어떤 상황이었나요?",
                    "그때 무슨 일이 있었나요?",
                    "언제부터 그런 일이 있었나요?",
                ]
            },
            PhaseTask.EMOTION_EXPLORATION: {
                "description": "감정 탐색",
                "templates": [
                    "그 순간 어떤 기분이 드셨어요?",
                    "그 감정을 좀 더 설명해 주실 수 있나요?",
                    "지금 이 이야기를 하면서 어떤 느낌이 드세요?",
                    "몸에서는 어떤 느낌이 있나요?",
                ]
            },
            PhaseTask.PATTERN_RECOGNITION: {
                "description": "패턴 탐색",
                "templates": [
                    "이런 일이 전에도 있었나요?",
                    "비슷한 상황이 반복되나요?",
                    "어떤 패턴이 보이시나요?",
                ]
            },
            PhaseTask.CONTEXT_GATHERING: {
                "description": "맥락 파악",
                "templates": [
                    "그 상황에서 주변 사람들은 어땠나요?",
                    "그 전에 어떤 일이 있었나요?",
                    "평소에는 어떠세요?",
                ]
            }
        },
        "transition_cues": [
            "핵심 문제가 명확해짐",
            "주요 감정이 표현됨",
            "패턴이 드러남",
            "내담자가 통찰을 보임",
        ],
        "typical_duration": (15, 20)
    }

    # 작업 단계 (Working)
    WORKING_GUIDE = {
        "goals": [
            "구체적 개입/기법 적용",
            "통찰 촉진 및 심화",
            "새로운 관점/행동 탐색",
            "변화 동기 강화",
        ],
        "tasks": {
            PhaseTask.INTERVENTION: {
                "description": "기법/개입 적용",
                "techniques": [
                    "인지 재구성",
                    "감정 조절 기법",
                    "행동 실험",
                    "역할극",
                    "이완 훈련",
                ]
            },
            PhaseTask.INSIGHT_FACILITATION: {
                "description": "통찰 촉진",
                "templates": [
                    "지금 하신 말씀에서 어떤 생각이 드세요?",
                    "그게 당신에게 어떤 의미인 것 같아요?",
                    "이 이야기들을 연결해 보면 어떤 그림이 그려지나요?",
                ]
            },
            PhaseTask.SKILL_BUILDING: {
                "description": "기술 습득",
                "templates": [
                    "이 상황에서 다르게 해볼 수 있는 것은 뭐가 있을까요?",
                    "새로운 방법을 한번 연습해 볼까요?",
                    "이 기법을 사용해 보시겠어요?",
                ]
            },
            PhaseTask.COGNITIVE_WORK: {
                "description": "인지 작업",
                "templates": [
                    "그 생각을 뒷받침하는 증거는 무엇인가요?",
                    "다르게 생각해 볼 수 있을까요?",
                    "가장 친한 친구라면 뭐라고 할까요?",
                ]
            }
        },
        "transition_cues": [
            "충분한 작업이 이루어짐",
            "내담자가 지침",
            "시간이 부족함",
            "자연스러운 마무리 지점",
        ],
        "typical_duration": (15, 25)
    }

    # 마무리 단계 (Closing)
    CLOSING_GUIDE = {
        "goals": [
            "세션 내용 정리 및 요약",
            "핵심 통찰 강화",
            "과제 설정 (필요시)",
            "다음 세션 예고",
            "긍정적 마무리",
        ],
        "tasks": {
            PhaseTask.SUMMARIZING: {
                "description": "세션 요약",
                "templates": [
                    "오늘 이야기 나눈 것을 정리해 보면...",
                    "오늘 세션에서 중요했던 점은...",
                    "오늘 나눈 대화 중에서 특히 기억에 남는 것이 있으신가요?",
                ]
            },
            PhaseTask.HOMEWORK_ASSIGNMENT: {
                "description": "과제 설정",
                "templates": [
                    "다음 세션까지 한 가지 해볼 수 있는 것이 있다면요?",
                    "이번 주에 {task}을 시도해 보시는 건 어떨까요?",
                    "오늘 이야기 나눈 것 중에서 일상에서 적용해 볼 수 있는 게 있을까요?",
                ],
                "homework_ideas": [
                    "감정 일기 쓰기",
                    "자동적 사고 기록하기",
                    "새로운 행동 시도하기",
                    "이완 연습하기",
                    "감사한 것 3가지 적기",
                ]
            },
            PhaseTask.NEXT_SESSION_PREVIEW: {
                "description": "다음 세션 예고",
                "templates": [
                    "다음에는 {topic}에 대해 더 이야기해 볼까요?",
                    "다음 세션에서 계속 다뤄보면 좋겠어요.",
                    "다음에 만나서 어떻게 되었는지 들려주세요.",
                ]
            },
            PhaseTask.FEEDBACK_COLLECTION: {
                "description": "피드백 수집",
                "templates": [
                    "오늘 대화가 어떠셨어요?",
                    "도움이 된 부분이 있었나요?",
                    "아쉬웠던 점이 있으시면 말씀해 주세요.",
                ]
            }
        },
        "transition_cues": [
            "요약 완료",
            "내담자가 마무리 준비됨",
            "시간 종료",
        ],
        "typical_duration": (5, 10)
    }

    @classmethod
    def get_guide(cls, phase: SessionPhase) -> Dict[str, Any]:
        """단계별 가이드 반환"""
        guides = {
            SessionPhase.OPENING: cls.OPENING_GUIDE,
            SessionPhase.EXPLORATION: cls.EXPLORATION_GUIDE,
            SessionPhase.WORKING: cls.WORKING_GUIDE,
            SessionPhase.CLOSING: cls.CLOSING_GUIDE,
        }
        return guides.get(phase, {})


# =============================================================================
# 세션 관리자
# =============================================================================

class SessionManager:
    """
    세션 관리자

    세션의 전체 흐름을 관리하고 단계 전환을 안내
    """

    # 단계 전환 기준 (턴 수 기반)
    PHASE_TURN_THRESHOLDS = {
        SessionPhase.OPENING: (1, 5),      # 1-5턴
        SessionPhase.EXPLORATION: (6, 15),  # 6-15턴
        SessionPhase.WORKING: (16, 30),     # 16-30턴
        SessionPhase.CLOSING: (31, 40),     # 31-40턴
    }

    def __init__(self, session_id: str = "", session_number: int = 1):
        self.state = SessionState(
            session_id=session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            session_number=session_number,
            started_at=datetime.now()
        )

        # 현재 단계 진행 초기화
        self._initialize_phase_progress(SessionPhase.OPENING)

        logger.info(f"SessionManager initialized: {self.state.session_id}")

    def _initialize_phase_progress(self, phase: SessionPhase):
        """단계 진행 초기화"""
        guide = PhaseGuide.get_guide(phase)
        tasks = list(guide.get("tasks", {}).keys())

        progress = PhaseProgress(
            phase=phase,
            started_at=datetime.now(),
            pending_tasks=tasks,
            completed_tasks=[]
        )

        self.state.phase_history.append(progress)

    def update_turn(self, user_message: str, assistant_response: str):
        """턴 업데이트"""
        self.state.turn_count += 1

        # 토픽 추출 (간단한 버전)
        self._extract_topics(user_message)

        # 단계 전환 체크
        suggested_phase = self._check_phase_transition()

        if suggested_phase and suggested_phase != self.state.current_phase:
            self._transition_to_phase(suggested_phase)

    def _extract_topics(self, message: str):
        """주요 토픽 추출"""
        # 간단한 키워드 기반 추출
        topic_keywords = {
            "가족": ["가족", "부모", "엄마", "아빠", "형제", "자녀"],
            "직장": ["직장", "회사", "상사", "동료", "업무", "일"],
            "관계": ["관계", "친구", "연인", "배우자", "사람들"],
            "감정": ["우울", "불안", "화", "슬픔", "두려움", "외로움"],
            "자존감": ["자존감", "자신감", "자격", "가치", "존재"],
            "스트레스": ["스트레스", "압박", "힘들", "지치", "번아웃"],
        }

        for topic, keywords in topic_keywords.items():
            for keyword in keywords:
                if keyword in message and topic not in self.state.main_topics:
                    self.state.main_topics.append(topic)
                    break

    def _check_phase_transition(self) -> Optional[SessionPhase]:
        """단계 전환 필요성 체크"""
        turn = self.state.turn_count

        for phase, (min_turn, max_turn) in self.PHASE_TURN_THRESHOLDS.items():
            if min_turn <= turn <= max_turn:
                return phase

        # 40턴 이후는 마무리
        if turn > 40:
            return SessionPhase.CLOSING

        return None

    def _transition_to_phase(self, new_phase: SessionPhase):
        """단계 전환 실행"""
        old_phase = self.state.current_phase

        # 현재 단계 완료 처리
        if self.state.phase_history:
            current_progress = self.state.phase_history[-1]
            current_progress.completion_percentage = 100.0

        # 새 단계 시작
        self.state.current_phase = new_phase
        self._initialize_phase_progress(new_phase)

        logger.info(f"Session phase transition: {old_phase.value} -> {new_phase.value}")

    def mark_task_complete(self, task: PhaseTask):
        """과제 완료 표시"""
        if self.state.phase_history:
            progress = self.state.phase_history[-1]
            if task in progress.pending_tasks:
                progress.pending_tasks.remove(task)
                progress.completed_tasks.append(task)

                # 완료율 업데이트
                total = len(progress.completed_tasks) + len(progress.pending_tasks)
                progress.completion_percentage = (len(progress.completed_tasks) / total) * 100 if total > 0 else 0

    def get_current_phase_guide(self) -> Dict[str, Any]:
        """현재 단계 가이드 반환"""
        return PhaseGuide.get_guide(self.state.current_phase)

    def get_session_status(self) -> Dict[str, Any]:
        """세션 상태 요약 반환"""
        elapsed = datetime.now() - self.state.started_at if self.state.started_at else timedelta()
        remaining = timedelta(minutes=self.state.estimated_duration) - elapsed

        current_progress = self.state.phase_history[-1] if self.state.phase_history else None

        return {
            "session_id": self.state.session_id,
            "session_number": self.state.session_number,
            "current_phase": self.state.current_phase.value,
            "turn_count": self.state.turn_count,
            "elapsed_minutes": elapsed.total_seconds() / 60,
            "remaining_minutes": max(0, remaining.total_seconds() / 60),
            "main_topics": self.state.main_topics,
            "key_emotions": self.state.key_emotions,
            "phase_progress": {
                "completed_tasks": [t.value for t in current_progress.completed_tasks] if current_progress else [],
                "pending_tasks": [t.value for t in current_progress.pending_tasks] if current_progress else [],
                "completion_percentage": current_progress.completion_percentage if current_progress else 0
            }
        }

    def suggest_next_action(self) -> Dict[str, Any]:
        """다음 행동 제안"""
        phase = self.state.current_phase
        guide = PhaseGuide.get_guide(phase)
        progress = self.state.phase_history[-1] if self.state.phase_history else None

        suggestion = {
            "phase": phase.value,
            "phase_goals": guide.get("goals", []),
            "suggested_task": None,
            "task_templates": [],
            "transition_ready": False,
            "transition_cues": guide.get("transition_cues", [])
        }

        # 다음 수행할 과제 제안
        if progress and progress.pending_tasks:
            next_task = progress.pending_tasks[0]
            suggestion["suggested_task"] = next_task.value

            task_info = guide.get("tasks", {}).get(next_task, {})
            suggestion["task_templates"] = task_info.get("templates", [])

        # 전환 준비도
        if progress:
            suggestion["transition_ready"] = progress.completion_percentage >= 70

        return suggestion

    def force_phase_transition(self, target_phase: SessionPhase):
        """강제 단계 전환"""
        self._transition_to_phase(target_phase)


# =============================================================================
# 세션 흐름 안내자
# =============================================================================

class SessionFlowGuide:
    """
    세션 흐름 안내자

    실시간으로 세션 진행을 안내하고 제안 제공
    """

    def __init__(self, session_manager: SessionManager):
        self.manager = session_manager
        logger.info("SessionFlowGuide initialized")

    def analyze_message(self, message: str) -> Dict[str, Any]:
        """
        메시지 분석 및 흐름 관련 정보 반환
        """
        analysis = {
            "detected_topics": [],
            "detected_emotions": [],
            "phase_appropriate": True,
            "transition_signals": [],
            "recommendations": []
        }

        current_phase = self.manager.state.current_phase

        # 단계 적합성 체크
        if current_phase == SessionPhase.OPENING:
            # Opening에서 깊은 문제 탐색 감지
            deep_exploration_markers = ["힘들", "고통", "괴로", "죽고 싶", "우울"]
            if any(marker in message for marker in deep_exploration_markers):
                analysis["transition_signals"].append("깊은 감정 표현 - 탐색 단계로 전환 고려")

        elif current_phase == SessionPhase.EXPLORATION:
            # 통찰/변화 준비 신호
            insight_markers = ["알겠", "깨달", "이해가 되", "그래서", "그런 거구나"]
            if any(marker in message for marker in insight_markers):
                analysis["transition_signals"].append("통찰 신호 - 작업 단계로 전환 고려")

        elif current_phase == SessionPhase.WORKING:
            # 피로/종료 신호
            fatigue_markers = ["지쳤", "오늘은", "많이", "충분"]
            if any(marker in message for marker in fatigue_markers):
                analysis["transition_signals"].append("종료 신호 - 마무리 단계로 전환 고려")

        return analysis

    def get_phase_prompt_section(self) -> str:
        """프롬프트에 삽입할 세션 구조 가이드 섹션"""
        status = self.manager.get_session_status()
        suggestion = self.manager.suggest_next_action()
        guide = self.manager.get_current_phase_guide()

        section = f"""
## 세션 구조 가이드

### 현재 세션 상태
- 세션 번호: {status['session_number']}회기
- 현재 단계: {status['current_phase']}
- 진행 턴: {status['turn_count']}
- 경과 시간: {status['elapsed_minutes']:.0f}분 / {self.manager.state.estimated_duration}분
- 단계 진행률: {status['phase_progress']['completion_percentage']:.0f}%

### 현재 단계 목표 ({status['current_phase']})
"""
        for goal in guide.get("goals", [])[:3]:
            section += f"- {goal}\n"

        section += f"""
### 권장 행동
- 다음 과제: {suggestion.get('suggested_task', '자유 진행')}
"""

        if suggestion.get("task_templates"):
            section += "- 예시 표현:\n"
            for template in suggestion["task_templates"][:2]:
                section += f"  - \"{template}\"\n"

        if suggestion.get("transition_ready"):
            section += f"\n### 단계 전환 신호\n"
            for cue in suggestion.get("transition_cues", [])[:2]:
                section += f"- {cue}\n"

        # 주요 토픽/감정
        if status["main_topics"]:
            section += f"\n### 오늘 주요 주제\n"
            section += f"- {', '.join(status['main_topics'][:5])}\n"

        return section


# =============================================================================
# 세션 요약 생성기
# =============================================================================

class SessionSummaryGenerator:
    """
    세션 요약 생성기

    세션 종료 시 요약 및 기록 생성
    """

    def __init__(self, session_manager: SessionManager):
        self.manager = session_manager
        logger.info("SessionSummaryGenerator initialized")

    def generate_summary(
        self,
        conversation_history: List[Dict],
        insights: List[str] = None,
        homework: List[str] = None
    ) -> Dict[str, Any]:
        """
        세션 요약 생성

        Args:
            conversation_history: 대화 기록
            insights: 도출된 통찰
            homework: 할당된 과제

        Returns:
            Dict: 세션 요약
        """
        status = self.manager.get_session_status()

        summary = {
            "session_info": {
                "session_id": status["session_id"],
                "session_number": status["session_number"],
                "date": datetime.now().isoformat(),
                "duration_minutes": status["elapsed_minutes"],
                "turn_count": status["turn_count"]
            },
            "content": {
                "main_topics": status["main_topics"],
                "key_emotions": status["key_emotions"],
                "presenting_issues": self._extract_presenting_issues(conversation_history),
                "insights": insights or self.manager.state.insights_generated,
                "techniques_used": self._identify_techniques_used(conversation_history)
            },
            "outcomes": {
                "goals_addressed": self._assess_goals_addressed(),
                "progress_made": self._assess_progress(),
                "homework_assigned": homework or self.manager.state.homework_assigned
            },
            "next_session": {
                "suggested_topics": self._suggest_next_topics(),
                "follow_up_items": self._identify_follow_up_items()
            },
            "clinical_notes": self._generate_clinical_notes()
        }

        return summary

    def _extract_presenting_issues(self, history: List[Dict]) -> List[str]:
        """주요 호소 문제 추출"""
        issues = []

        issue_markers = [
            ("고민", "고민 사항"),
            ("힘들", "어려움"),
            ("문제", "문제 상황"),
            ("걱정", "걱정거리"),
            ("스트레스", "스트레스 원인"),
        ]

        for turn in history[:10]:  # 초반 대화에서 추출
            content = turn.get("content", "")
            for marker, label in issue_markers:
                if marker in content and label not in issues:
                    issues.append(label)

        return issues[:5]

    def _identify_techniques_used(self, history: List[Dict]) -> List[str]:
        """사용된 기법 식별"""
        techniques = []

        technique_markers = {
            "인지 재구성": ["다르게 생각", "증거", "다른 가능성"],
            "감정 탐색": ["어떤 기분", "감정", "느낌"],
            "기적 질문": ["기적", "내일 아침", "변화"],
            "척도 질문": ["0점", "10점", "몇 점"],
            "공감적 반영": ["그러셨군요", "힘드셨", "마음이"],
        }

        full_text = " ".join([t.get("content", "") for t in history])

        for technique, markers in technique_markers.items():
            if any(marker in full_text for marker in markers):
                techniques.append(technique)

        return techniques

    def _assess_goals_addressed(self) -> Dict[str, bool]:
        """목표 달성 여부 평가"""
        progress = self.manager.state.phase_history

        return {
            "rapport_established": any(
                PhaseTask.GREETING in p.completed_tasks or PhaseTask.CHECK_IN in p.completed_tasks
                for p in progress
            ),
            "exploration_done": any(
                PhaseTask.PROBLEM_EXPLORATION in p.completed_tasks or
                PhaseTask.EMOTION_EXPLORATION in p.completed_tasks
                for p in progress
            ),
            "intervention_applied": any(
                PhaseTask.INTERVENTION in p.completed_tasks or
                PhaseTask.COGNITIVE_WORK in p.completed_tasks
                for p in progress
            ),
            "proper_closure": any(
                PhaseTask.SUMMARIZING in p.completed_tasks
                for p in progress
            )
        }

    def _assess_progress(self) -> str:
        """진행 상황 평가"""
        status = self.manager.get_session_status()
        topics = len(status["main_topics"])
        turns = status["turn_count"]

        if topics >= 3 and turns >= 20:
            return "충분한 탐색과 작업이 이루어짐"
        elif topics >= 2 and turns >= 10:
            return "적절한 진행"
        else:
            return "추가 탐색 필요"

    def _suggest_next_topics(self) -> List[str]:
        """다음 세션 주제 제안"""
        current_topics = self.manager.state.main_topics
        suggestions = []

        topic_follow_ups = {
            "가족": "가족 관계의 패턴 탐색",
            "직장": "직장 스트레스 대처 전략",
            "관계": "대인관계 패턴 검토",
            "감정": "감정 조절 기술 연습",
            "자존감": "자기 가치감 강화",
        }

        for topic in current_topics[:3]:
            if topic in topic_follow_ups:
                suggestions.append(topic_follow_ups[topic])

        return suggestions or ["이전 세션 내용 점검"]

    def _identify_follow_up_items(self) -> List[str]:
        """후속 조치 항목"""
        items = []

        if self.manager.state.homework_assigned:
            items.append("과제 수행 여부 확인")

        if self.manager.state.crisis_detected:
            items.append("위기 상태 재평가")

        items.append("전반적 상태 변화 확인")

        return items

    def _generate_clinical_notes(self) -> str:
        """임상 노트 생성"""
        status = self.manager.get_session_status()

        notes = f"""
세션 #{status['session_number']} 임상 노트
날짜: {datetime.now().strftime('%Y-%m-%d')}
기간: {status['elapsed_minutes']:.0f}분

주요 주제: {', '.join(status['main_topics']) if status['main_topics'] else '탐색 중'}

세션 진행:
- 시작 단계에서 현재 상태 확인
- 탐색 단계에서 주요 문제 논의
- 작업 단계에서 개입 시도
- 마무리 단계에서 요약 및 과제 설정

다음 세션 계획:
- 과제 점검
- 지속적인 주제 탐색
"""
        return notes.strip()

    def generate_client_summary(self) -> str:
        """내담자용 세션 요약 생성"""
        status = self.manager.get_session_status()

        summary = f"""
오늘 상담 요약

오늘 나눈 이야기:
"""
        for topic in status["main_topics"][:3]:
            summary += f"- {topic}에 대해 이야기 나눴어요\n"

        if self.manager.state.homework_assigned:
            summary += "\n다음 세션까지 해볼 것:\n"
            for hw in self.manager.state.homework_assigned[:3]:
                summary += f"- {hw}\n"

        summary += "\n다음에 만나서 이야기해요. 수고하셨습니다."

        return summary.strip()


# =============================================================================
# 통합 세션 구조 시스템
# =============================================================================

class SessionStructureSystem:
    """
    통합 세션 구조 시스템

    세션 관리, 흐름 안내, 요약 생성을 통합
    """

    def __init__(self, session_id: str = "", session_number: int = 1):
        self.manager = SessionManager(session_id, session_number)
        self.flow_guide = SessionFlowGuide(self.manager)
        self.summary_generator = SessionSummaryGenerator(self.manager)

        logger.info("SessionStructureSystem initialized")

    def process_turn(
        self,
        user_message: str,
        assistant_response: str
    ) -> Dict[str, Any]:
        """
        턴 처리 및 상태 업데이트

        Returns:
            Dict: 업데이트된 상태 및 제안
        """
        # 메시지 분석
        analysis = self.flow_guide.analyze_message(user_message)

        # 턴 업데이트
        self.manager.update_turn(user_message, assistant_response)

        # 상태 및 제안 반환
        return {
            "status": self.manager.get_session_status(),
            "message_analysis": analysis,
            "next_action": self.manager.suggest_next_action()
        }

    def get_prompt_section(self) -> str:
        """프롬프트용 세션 구조 섹션"""
        return self.flow_guide.get_phase_prompt_section()

    def end_session(
        self,
        conversation_history: List[Dict],
        insights: List[str] = None,
        homework: List[str] = None
    ) -> Dict[str, Any]:
        """세션 종료 및 요약 생성"""
        return self.summary_generator.generate_summary(
            conversation_history, insights, homework
        )

    def get_client_summary(self) -> str:
        """내담자용 요약"""
        return self.summary_generator.generate_client_summary()

    def transition_phase(self, target: SessionPhase):
        """수동 단계 전환"""
        self.manager.force_phase_transition(target)


# =============================================================================
# 편의 함수
# =============================================================================

_session_system: Optional[SessionStructureSystem] = None


def get_session_system(
    session_id: str = "",
    session_number: int = 1,
    reset: bool = False
) -> SessionStructureSystem:
    """세션 구조 시스템 싱글톤 반환"""
    global _session_system

    if _session_system is None or reset:
        _session_system = SessionStructureSystem(session_id, session_number)

    return _session_system


def get_session_structure_prompt_section(
    session_id: str = "",
    session_number: int = 1
) -> str:
    """프롬프트용 세션 구조 섹션"""
    system = get_session_system(session_id, session_number)
    return system.get_prompt_section()


def process_session_turn(
    user_message: str,
    assistant_response: str,
    session_id: str = "",
    session_number: int = 1
) -> Dict[str, Any]:
    """세션 턴 처리"""
    system = get_session_system(session_id, session_number)
    return system.process_turn(user_message, assistant_response)


def end_counseling_session(
    conversation_history: List[Dict],
    insights: List[str] = None,
    homework: List[str] = None
) -> Dict[str, Any]:
    """상담 세션 종료"""
    system = get_session_system()
    return system.end_session(conversation_history, insights, homework)
