"""
일관성 검증 시스템 (Consistency Checker System)

AI 응답의 일관성 유지를 위한 검증:
1. 사용자 정보 일관성 - 이름, 상황 등 정보 변경 감지
2. 조언 일관성 - 이전 조언과 상충되는 내용 감지
3. 감정 상태 일관성 - 급격한 감정 변화 확인
4. 상담 스타일 일관성 - 톤, 접근 방식 유지
5. 사실 일관성 - 언급된 사실들의 일관성
"""

from typing import Dict, List, Optional, Tuple, Any, Set
from enum import Enum
from dataclasses import dataclass, field
import logging
import re
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


# =============================================================================
# 일관성 유형 및 데이터 구조
# =============================================================================

class InconsistencyType(Enum):
    """불일관 유형"""
    USER_INFO = "user_info"                 # 사용자 정보
    ADVICE = "advice"                       # 조언
    EMOTION_STATE = "emotion_state"         # 감정 상태
    COUNSELING_STYLE = "counseling_style"   # 상담 스타일
    FACTS = "facts"                         # 사실
    CONTEXT = "context"                     # 맥락
    TIMELINE = "timeline"                   # 시간 순서


class Severity(Enum):
    """심각도"""
    HIGH = "high"       # 중대한 불일관
    MEDIUM = "medium"   # 주의 필요
    LOW = "low"         # 경미한 불일관


@dataclass
class InconsistencyIssue:
    """불일관 이슈"""
    inconsistency_type: InconsistencyType
    severity: Severity
    description: str
    previous_info: str
    current_info: str
    suggestion: str


@dataclass
class UserInfoRecord:
    """사용자 정보 기록"""
    name: Optional[str] = None
    age: Optional[str] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    family: Dict[str, str] = field(default_factory=dict)
    relationships: Dict[str, str] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    mentioned_facts: Dict[str, str] = field(default_factory=dict)


@dataclass
class ConsistencyResult:
    """일관성 검사 결과"""
    is_consistent: bool
    issues: List[InconsistencyIssue] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    confidence: float = 1.0


# =============================================================================
# 1. 사용자 정보 추적기
# =============================================================================

class UserInfoTracker:
    """
    사용자 정보 추적

    대화에서 언급된 사용자 정보를 추적하고 불일관 감지
    """

    # 이름 추출 패턴
    NAME_PATTERNS = [
        r"제?\s*이름은?\s*([가-힣]{2,4})(?:이에요|입니다|예요|야|이야)",
        r"([가-힣]{2,4})(?:라고\s*해요|라고\s*합니다|라고\s*불러)",
        r"저는?\s*([가-힣]{2,4})(?:이에요|입니다|예요)",
    ]

    # 나이 추출 패턴
    AGE_PATTERNS = [
        r"(\d{1,3})\s*(?:살|세)(?:이에요|입니다|예요|야)?",
        r"(\d{2})년생",
        r"(이십대|삼십대|사십대|오십대|십대)",
    ]

    # 직업 추출 패턴
    OCCUPATION_PATTERNS = [
        r"(학생|회사원|주부|프리랜서|자영업|공무원|의사|교사|간호사)(?:이에요|입니다|예요)?",
        r"(대학|고등학교|중학교).*?(?:다니|재학)",
    ]

    # 가족 관계 패턴
    FAMILY_PATTERNS = [
        r"(엄마|아빠|어머니|아버지|부모님).*?(계시|있|없|돌아가)",
        r"(형|오빠|누나|언니|동생|남동생|여동생).*?(있|없)",
        r"(배우자|남편|아내|와이프).*?(있|없|이혼)",
        r"(아이|자녀|아들|딸).*?(있|없|명)",
    ]

    def __init__(self):
        self.user_info = UserInfoRecord()
        self.info_history: List[Dict[str, Any]] = []
        logger.info("UserInfoTracker initialized")

    def extract_info(self, message: str, turn: int) -> Dict[str, Any]:
        """메시지에서 사용자 정보 추출"""
        extracted = {}

        # 이름 추출
        for pattern in self.NAME_PATTERNS:
            match = re.search(pattern, message)
            if match:
                extracted["name"] = match.group(1)
                break

        # 나이 추출
        for pattern in self.AGE_PATTERNS:
            match = re.search(pattern, message)
            if match:
                extracted["age"] = match.group(1)
                break

        # 직업 추출
        for pattern in self.OCCUPATION_PATTERNS:
            match = re.search(pattern, message)
            if match:
                extracted["occupation"] = match.group(1)
                break

        # 가족 관계 추출
        for pattern in self.FAMILY_PATTERNS:
            match = re.search(pattern, message)
            if match:
                relation = match.group(1)
                status = match.group(2)
                extracted[f"family_{relation}"] = status

        if extracted:
            self.info_history.append({
                "turn": turn,
                "extracted": extracted,
                "timestamp": datetime.now().isoformat()
            })

        return extracted

    def update_info(self, extracted: Dict[str, Any]) -> List[InconsistencyIssue]:
        """정보 업데이트 및 불일관 검사"""
        issues = []

        for key, value in extracted.items():
            if key == "name" and self.user_info.name:
                if self.user_info.name != value:
                    issues.append(InconsistencyIssue(
                        inconsistency_type=InconsistencyType.USER_INFO,
                        severity=Severity.HIGH,
                        description="사용자 이름이 변경됨",
                        previous_info=f"이전: {self.user_info.name}",
                        current_info=f"현재: {value}",
                        suggestion="이름 확인 필요: '이름이 ~이시라고 하셨는데, 맞나요?'"
                    ))
                else:
                    continue  # 같으면 업데이트 불필요

            elif key == "age" and self.user_info.age:
                if self.user_info.age != value:
                    issues.append(InconsistencyIssue(
                        inconsistency_type=InconsistencyType.USER_INFO,
                        severity=Severity.MEDIUM,
                        description="사용자 나이가 변경됨",
                        previous_info=f"이전: {self.user_info.age}",
                        current_info=f"현재: {value}",
                        suggestion="나이 정보 확인 필요"
                    ))

            # 정보 업데이트
            if key == "name":
                self.user_info.name = value
            elif key == "age":
                self.user_info.age = value
            elif key == "occupation":
                self.user_info.occupation = value
            elif key.startswith("family_"):
                relation = key.replace("family_", "")
                self.user_info.family[relation] = value

        return issues

    def check_response_consistency(self, response: str) -> List[InconsistencyIssue]:
        """응답에서 사용자 정보 언급 일관성 검사"""
        issues = []

        # 이름 언급 검사
        if self.user_info.name:
            name_mentions = re.findall(r'([가-힣]{2,4})님', response)
            for name in name_mentions:
                if name != self.user_info.name and len(name) >= 2:
                    issues.append(InconsistencyIssue(
                        inconsistency_type=InconsistencyType.USER_INFO,
                        severity=Severity.HIGH,
                        description="응답에서 잘못된 이름 사용",
                        previous_info=f"실제 이름: {self.user_info.name}",
                        current_info=f"응답에서 사용: {name}",
                        suggestion=f"'{self.user_info.name}'님으로 수정 필요"
                    ))

        return issues


# =============================================================================
# 2. 조언 일관성 추적기
# =============================================================================

class AdviceTracker:
    """
    조언 일관성 추적

    이전에 제공한 조언과 상충되는 조언 감지
    """

    # 조언 추출 패턴
    ADVICE_PATTERNS = [
        r"(~해\s*보시면|~해\s*보세요|~하시면|~하는\s*게).*?(좋|도움|효과)",
        r"(추천|권해|제안).*?(드려요|드립니다|해요)",
        r"(방법|전략|기법).*?(있|드릴)",
    ]

    # 상충 키워드 쌍
    CONTRADICTORY_PAIRS = [
        ("하세요", "하지 마세요"),
        ("좋아요", "좋지 않아요"),
        ("효과적", "효과 없"),
        ("도움", "도움 안"),
        ("추천", "추천 안"),
        ("표현하", "표현하지 마"),
        ("말씀하", "말씀하지 마"),
    ]

    def __init__(self):
        self.advice_history: List[Dict[str, Any]] = []
        self.topic_advice: Dict[str, List[str]] = defaultdict(list)
        logger.info("AdviceTracker initialized")

    def extract_advice(self, response: str, topic: str = "") -> List[str]:
        """응답에서 조언 추출"""
        advices = []

        for pattern in self.ADVICE_PATTERNS:
            matches = re.findall(pattern, response)
            for match in matches:
                advice = ''.join(match) if isinstance(match, tuple) else match
                advices.append(advice)

        if advices and topic:
            self.topic_advice[topic].extend(advices)

        return advices

    def check_contradiction(self, new_response: str, topic: str = "") -> List[InconsistencyIssue]:
        """이전 조언과 상충 검사"""
        issues = []

        # 이전 조언 수집
        previous_advices = []
        if topic and topic in self.topic_advice:
            previous_advices = self.topic_advice[topic]

        # 최근 조언들도 검사
        for record in self.advice_history[-10:]:
            previous_advices.extend(record.get("advices", []))

        # 상충 검사
        for prev_advice in previous_advices:
            for positive, negative in self.CONTRADICTORY_PAIRS:
                # 이전에 긍정적, 지금 부정적
                if positive in prev_advice and negative in new_response:
                    issues.append(InconsistencyIssue(
                        inconsistency_type=InconsistencyType.ADVICE,
                        severity=Severity.MEDIUM,
                        description="이전 조언과 상충되는 내용",
                        previous_info=f"이전: {prev_advice}",
                        current_info=f"현재: {negative} 포함",
                        suggestion="일관된 조언을 유지하거나, 변경 이유를 설명하세요"
                    ))
                # 이전에 부정적, 지금 긍정적
                elif negative in prev_advice and positive in new_response:
                    issues.append(InconsistencyIssue(
                        inconsistency_type=InconsistencyType.ADVICE,
                        severity=Severity.MEDIUM,
                        description="이전 조언과 상충되는 내용",
                        previous_info=f"이전: {prev_advice}",
                        current_info=f"현재: {positive} 포함",
                        suggestion="일관된 조언을 유지하거나, 변경 이유를 설명하세요"
                    ))

        return issues

    def record_advice(self, response: str, turn: int, topic: str = ""):
        """조언 기록"""
        advices = self.extract_advice(response, topic)
        if advices:
            self.advice_history.append({
                "turn": turn,
                "advices": advices,
                "topic": topic,
                "timestamp": datetime.now().isoformat()
            })


# =============================================================================
# 3. 감정 상태 추적기
# =============================================================================

class EmotionStateTracker:
    """
    감정 상태 일관성 추적

    급격한 감정 변화 감지
    """

    # 감정 카테고리
    EMOTION_KEYWORDS = {
        "positive": ["기쁨", "행복", "좋아", "감사", "희망", "편안", "안심"],
        "negative": ["슬픔", "우울", "불안", "화남", "두려움", "절망", "외로움"],
        "neutral": ["평온", "무덤덤", "그저 그래", "보통"],
    }

    # 감정 강도
    INTENSITY_MARKERS = {
        "high": ["매우", "정말", "너무", "극도로", "완전히"],
        "medium": ["꽤", "상당히", "어느 정도"],
        "low": ["조금", "약간", "살짝"],
    }

    def __init__(self):
        self.emotion_history: List[Dict[str, Any]] = []
        logger.info("EmotionStateTracker initialized")

    def analyze_emotion(self, message: str) -> Dict[str, Any]:
        """메시지에서 감정 분석"""
        detected_emotions = {
            "positive": [],
            "negative": [],
            "neutral": []
        }
        intensity = "medium"

        # 감정 키워드 검출
        for category, keywords in self.EMOTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in message:
                    detected_emotions[category].append(keyword)

        # 강도 검출
        for level, markers in self.INTENSITY_MARKERS.items():
            for marker in markers:
                if marker in message:
                    intensity = level
                    break

        # 주요 감정 카테고리 결정
        primary_category = "neutral"
        max_count = 0
        for category, emotions in detected_emotions.items():
            if len(emotions) > max_count:
                max_count = len(emotions)
                primary_category = category

        return {
            "primary_category": primary_category,
            "emotions": detected_emotions,
            "intensity": intensity,
            "all_emotions": sum(detected_emotions.values(), [])
        }

    def check_consistency(self, current_emotion: Dict[str, Any]) -> List[InconsistencyIssue]:
        """감정 상태 일관성 검사"""
        issues = []

        if not self.emotion_history:
            return issues

        last_emotion = self.emotion_history[-1]

        # 급격한 카테고리 변화 (positive ↔ negative)
        if (last_emotion["primary_category"] == "positive" and
            current_emotion["primary_category"] == "negative"):
            issues.append(InconsistencyIssue(
                inconsistency_type=InconsistencyType.EMOTION_STATE,
                severity=Severity.MEDIUM,
                description="급격한 감정 변화 감지 (긍정 → 부정)",
                previous_info=f"이전: {last_emotion['primary_category']}",
                current_info=f"현재: {current_emotion['primary_category']}",
                suggestion="감정 변화에 대해 확인해 보세요: '방금 전과 다르게 느껴지시나요?'"
            ))

        elif (last_emotion["primary_category"] == "negative" and
              current_emotion["primary_category"] == "positive"):
            issues.append(InconsistencyIssue(
                inconsistency_type=InconsistencyType.EMOTION_STATE,
                severity=Severity.LOW,
                description="급격한 감정 변화 감지 (부정 → 긍정)",
                previous_info=f"이전: {last_emotion['primary_category']}",
                current_info=f"현재: {current_emotion['primary_category']}",
                suggestion="긍정적 변화 확인: '기분이 나아지신 것 같아요. 어떤 변화가 있으셨나요?'"
            ))

        return issues

    def record_emotion(self, message: str, turn: int):
        """감정 기록"""
        emotion = self.analyze_emotion(message)
        emotion["turn"] = turn
        emotion["timestamp"] = datetime.now().isoformat()
        self.emotion_history.append(emotion)


# =============================================================================
# 4. 상담 스타일 일관성 검사기
# =============================================================================

class CounselingStyleChecker:
    """
    상담 스타일 일관성 검사

    톤, 공손함 수준, 접근 방식의 일관성 유지
    """

    # 공손함 수준
    FORMALITY_MARKERS = {
        "formal": ["~습니다", "~입니다", "~세요", "~시겠어요"],
        "casual": ["~야", "~어", "~지", "~해"],
        "mixed": ["~요", "~네요", "~군요"],
    }

    # 상담 스타일
    STYLE_MARKERS = {
        "supportive": ["함께", "곁에", "응원", "지지", "편이에요"],
        "directive": ["해야", "하세요", "필요", "중요"],
        "exploratory": ["어떤", "무엇", "왜", "어떻게", "느끼"],
        "educational": ["보통", "일반적으로", "알려져", "연구"],
    }

    def __init__(self):
        self.style_history: List[Dict[str, Any]] = []
        self.established_formality: Optional[str] = None
        self.established_style: Optional[str] = None
        logger.info("CounselingStyleChecker initialized")

    def analyze_style(self, response: str) -> Dict[str, Any]:
        """응답 스타일 분석"""
        # 공손함 수준 분석
        formality_scores = {level: 0 for level in self.FORMALITY_MARKERS}
        for level, markers in self.FORMALITY_MARKERS.items():
            for marker in markers:
                formality_scores[level] += response.count(marker)

        formality = max(formality_scores, key=formality_scores.get)

        # 상담 스타일 분석
        style_scores = {style: 0 for style in self.STYLE_MARKERS}
        for style, markers in self.STYLE_MARKERS.items():
            for marker in markers:
                if marker in response:
                    style_scores[style] += 1

        primary_style = max(style_scores, key=style_scores.get)

        return {
            "formality": formality,
            "primary_style": primary_style,
            "style_scores": style_scores
        }

    def check_consistency(self, current_style: Dict[str, Any]) -> List[InconsistencyIssue]:
        """스타일 일관성 검사"""
        issues = []

        # 공손함 수준 일관성
        if self.established_formality:
            if current_style["formality"] != self.established_formality:
                # formal ↔ casual 변화만 검사 (mixed는 유연하게)
                if ((self.established_formality == "formal" and current_style["formality"] == "casual") or
                    (self.established_formality == "casual" and current_style["formality"] == "formal")):
                    issues.append(InconsistencyIssue(
                        inconsistency_type=InconsistencyType.COUNSELING_STYLE,
                        severity=Severity.LOW,
                        description="공손함 수준 변화 감지",
                        previous_info=f"기존: {self.established_formality}",
                        current_info=f"현재: {current_style['formality']}",
                        suggestion="일관된 말투를 유지하세요"
                    ))
        else:
            # 첫 번째 응답의 스타일을 기준으로 설정
            self.established_formality = current_style["formality"]

        # 상담 스타일 급변 검사
        if self.established_style:
            if (self.established_style == "supportive" and
                current_style["primary_style"] == "directive"):
                issues.append(InconsistencyIssue(
                    inconsistency_type=InconsistencyType.COUNSELING_STYLE,
                    severity=Severity.MEDIUM,
                    description="상담 스타일 급변 (지지적 → 지시적)",
                    previous_info=f"기존: {self.established_style}",
                    current_info=f"현재: {current_style['primary_style']}",
                    suggestion="지지적 접근을 유지하면서 필요시 점진적으로 전환하세요"
                ))
        else:
            self.established_style = current_style["primary_style"]

        return issues

    def record_style(self, response: str, turn: int):
        """스타일 기록"""
        style = self.analyze_style(response)
        style["turn"] = turn
        self.style_history.append(style)


# =============================================================================
# 5. 사실 일관성 추적기
# =============================================================================

class FactTracker:
    """
    언급된 사실의 일관성 추적

    대화에서 언급된 사실들이 일관되게 유지되는지 확인
    """

    # 시간 관련 패턴
    TIME_PATTERNS = [
        (r"(\d+)\s*(년|개월|달|주|일)\s*전", "time_ago"),
        (r"(\d+)\s*(살|세)\s*(때|부터)", "age_at"),
        (r"(작년|올해|내년|지난\s*주|이번\s*주)", "relative_time"),
    ]

    # 숫자 관련 패턴
    NUMBER_PATTERNS = [
        (r"(\d+)\s*번", "count"),
        (r"(\d+)\s*명", "people_count"),
        (r"(\d+)\s*시간", "duration"),
    ]

    def __init__(self):
        self.facts: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        logger.info("FactTracker initialized")

    def extract_facts(self, message: str, turn: int) -> Dict[str, Any]:
        """사실 추출"""
        extracted = {}

        # 시간 관련 사실
        for pattern, fact_type in self.TIME_PATTERNS:
            matches = re.findall(pattern, message)
            for match in matches:
                key = f"{fact_type}_{match[0] if isinstance(match, tuple) else match}"
                extracted[key] = match

        # 숫자 관련 사실
        for pattern, fact_type in self.NUMBER_PATTERNS:
            matches = re.findall(pattern, message)
            for match in matches:
                key = f"{fact_type}_{match}"
                extracted[key] = match

        # 기록
        for key, value in extracted.items():
            self.facts[key].append({
                "value": value,
                "turn": turn,
                "context": message[:100]
            })

        return extracted

    def check_consistency(self, message: str, turn: int) -> List[InconsistencyIssue]:
        """사실 일관성 검사"""
        issues = []
        current_facts = self.extract_facts(message, turn)

        for key, value in current_facts.items():
            if key in self.facts and len(self.facts[key]) > 1:
                # 이전 값과 비교
                previous = self.facts[key][0]  # 첫 번째 언급
                if previous["value"] != value:
                    issues.append(InconsistencyIssue(
                        inconsistency_type=InconsistencyType.FACTS,
                        severity=Severity.MEDIUM,
                        description=f"사실 불일관: {key}",
                        previous_info=f"이전 언급: {previous['value']} (턴 {previous['turn']})",
                        current_info=f"현재 언급: {value}",
                        suggestion="사실 관계 확인이 필요할 수 있습니다"
                    ))

        return issues


# =============================================================================
# 통합 일관성 검사 시스템
# =============================================================================

class ConsistencyCheckSystem:
    """
    통합 일관성 검사 시스템

    모든 일관성 검사를 통합
    """

    def __init__(self):
        self.user_info_tracker = UserInfoTracker()
        self.advice_tracker = AdviceTracker()
        self.emotion_tracker = EmotionStateTracker()
        self.style_checker = CounselingStyleChecker()
        self.fact_tracker = FactTracker()

        self.turn_count = 0
        logger.info("ConsistencyCheckSystem initialized")

    def check_user_message(self, message: str) -> ConsistencyResult:
        """
        사용자 메시지 일관성 검사

        사용자가 제공한 정보의 일관성 확인
        """
        self.turn_count += 1
        issues = []

        # 사용자 정보 추출 및 검사
        extracted = self.user_info_tracker.extract_info(message, self.turn_count)
        if extracted:
            user_issues = self.user_info_tracker.update_info(extracted)
            issues.extend(user_issues)

        # 감정 상태 추적
        emotion = self.emotion_tracker.analyze_emotion(message)
        emotion_issues = self.emotion_tracker.check_consistency(emotion)
        issues.extend(emotion_issues)
        self.emotion_tracker.record_emotion(message, self.turn_count)

        # 사실 일관성 검사
        fact_issues = self.fact_tracker.check_consistency(message, self.turn_count)
        issues.extend(fact_issues)

        # 결과 생성
        is_consistent = len([i for i in issues if i.severity == Severity.HIGH]) == 0
        warnings = [i.description for i in issues if i.severity == Severity.MEDIUM]

        return ConsistencyResult(
            is_consistent=is_consistent,
            issues=issues,
            warnings=warnings,
            confidence=1.0 - (len(issues) * 0.1)
        )

    def check_response(self, response: str, topic: str = "") -> ConsistencyResult:
        """
        AI 응답 일관성 검사

        AI 응답이 이전 대화와 일관되는지 확인
        """
        issues = []

        # 사용자 정보 언급 일관성
        user_issues = self.user_info_tracker.check_response_consistency(response)
        issues.extend(user_issues)

        # 조언 일관성
        advice_issues = self.advice_tracker.check_contradiction(response, topic)
        issues.extend(advice_issues)
        self.advice_tracker.record_advice(response, self.turn_count, topic)

        # 상담 스타일 일관성
        style = self.style_checker.analyze_style(response)
        style_issues = self.style_checker.check_consistency(style)
        issues.extend(style_issues)
        self.style_checker.record_style(response, self.turn_count)

        # 결과 생성
        is_consistent = len([i for i in issues if i.severity == Severity.HIGH]) == 0
        warnings = [i.description for i in issues if i.severity == Severity.MEDIUM]

        return ConsistencyResult(
            is_consistent=is_consistent,
            issues=issues,
            warnings=warnings,
            confidence=1.0 - (len(issues) * 0.1)
        )

    def get_user_info_summary(self) -> Dict[str, Any]:
        """현재까지 파악된 사용자 정보 요약"""
        info = self.user_info_tracker.user_info
        return {
            "name": info.name,
            "age": info.age,
            "occupation": info.occupation,
            "family": info.family,
            "issues": info.issues
        }

    def get_prompt_section(self) -> str:
        """프롬프트에 삽입할 일관성 가이드"""
        user_info = self.get_user_info_summary()

        section = """
## 일관성 유지 가이드

### 파악된 사용자 정보
"""
        if user_info["name"]:
            section += f"- 이름: {user_info['name']}\n"
        if user_info["age"]:
            section += f"- 나이: {user_info['age']}\n"
        if user_info["occupation"]:
            section += f"- 직업: {user_info['occupation']}\n"
        if user_info["family"]:
            section += f"- 가족: {user_info['family']}\n"

        section += """
### 일관성 유지 원칙
1. **사용자 정보**: 파악된 정보와 일치하게 응답하기
2. **조언 일관성**: 이전에 한 조언과 상충되지 않게 하기
3. **상담 스타일**: 처음 설정한 톤과 스타일 유지하기
4. **사실 확인**: 불확실한 정보는 확인 질문하기

### 불일관 발견 시
- "제가 기억하기로는 ~라고 하셨는데, 맞나요?"
- "앞서 말씀하신 것과 조금 다른 것 같은데, 확인해 볼까요?"
"""
        return section


# =============================================================================
# 편의 함수
# =============================================================================

_consistency_system: Optional[ConsistencyCheckSystem] = None


def get_consistency_system() -> ConsistencyCheckSystem:
    """일관성 검사 시스템 싱글톤 반환"""
    global _consistency_system
    if _consistency_system is None:
        _consistency_system = ConsistencyCheckSystem()
    return _consistency_system


def check_message_consistency(message: str) -> ConsistencyResult:
    """사용자 메시지 일관성 빠른 검사"""
    system = get_consistency_system()
    return system.check_user_message(message)


def check_response_consistency(response: str, topic: str = "") -> ConsistencyResult:
    """AI 응답 일관성 빠른 검사"""
    system = get_consistency_system()
    return system.check_response(response, topic)


def get_consistency_prompt_section() -> str:
    """프롬프트용 일관성 섹션"""
    system = get_consistency_system()
    return system.get_prompt_section()
