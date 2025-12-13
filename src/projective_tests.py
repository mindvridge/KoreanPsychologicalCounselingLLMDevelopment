"""
투사 검사 해석기 (Projective Tests Interpreter)
HTP, KFD 등 투사 검사 전문 해석

기능:
- HTP (집-나무-사람) 검사 해석
- KFD (동적 가족화) 검사 해석
- 상징물 의미 해석
- 통합적 심리학적 분석
- 치료적 질문 생성
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ProjectiveTestType(Enum):
    """투사 검사 유형"""
    HTP = "HTP"                      # House-Tree-Person
    KFD = "KFD"                      # Kinetic Family Drawing
    DAP = "DAP"                      # Draw-A-Person
    TREE = "TREE"                    # 나무 그림 검사
    FREE = "FREE"                    # 자유화


@dataclass
class HTPElement:
    """HTP 요소"""
    category: str          # house, tree, person
    element: str           # specific element
    present: bool          # 존재 여부
    characteristics: Dict[str, Any]  # 특성
    interpretation: str    # 해석


@dataclass
class FamilyMember:
    """가족 구성원"""
    role: str              # 역할 (아빠, 엄마, 본인 등)
    size: str              # 크기 (large, medium, small)
    position: str          # 위치
    activity: str          # 활동
    facing: str            # 방향 (toward_family, away, forward)
    distance_from_self: str  # 본인과의 거리


@dataclass
class ProjectiveTestResult:
    """투사 검사 결과"""
    test_type: ProjectiveTestType
    elements: List[Any]              # HTPElement 또는 FamilyMember
    overall_interpretation: str
    psychological_themes: List[str]
    emotional_indicators: List[str]
    relationship_patterns: List[str]
    strengths_identified: List[str]
    areas_of_concern: List[str]
    therapeutic_questions: List[str]
    confidence_level: float
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            "test_type": self.test_type.value,
            "overall_interpretation": self.overall_interpretation,
            "themes": self.psychological_themes,
            "emotions": self.emotional_indicators,
            "relationships": self.relationship_patterns,
            "strengths": self.strengths_identified,
            "concerns": self.areas_of_concern,
            "questions": self.therapeutic_questions,
            "confidence": self.confidence_level
        }


class HTPInterpreter:
    """
    HTP 검사 해석기

    집-나무-사람 그림 검사를 해석합니다.
    """

    def __init__(self):
        # 집 해석 가이드
        self.house_guide = {
            "roof": {
                "large": "환상/사고 영역의 과도한 강조, 지적 방어",
                "small": "환상 영역의 제한, 정서적 위축",
                "absent": "환상 능력 결핍, 현실에만 집착",
                "peaked": "높은 이상, 야망",
                "flat": "실용적, 현실적"
            },
            "walls": {
                "thick": "강한 자아 경계, 방어적",
                "thin": "취약한 자아 경계",
                "transparent": "경계 문제, 침습 경험 가능"
            },
            "door": {
                "large": "의존성, 대인관계 욕구",
                "small": "대인관계 회피, 폐쇄성",
                "absent": "심한 대인관계 철수",
                "open": "개방성, 환영",
                "closed": "방어적, 폐쇄적",
                "locked": "강한 방어, 불신"
            },
            "windows": {
                "many": "환경과의 상호작용 욕구",
                "few": "제한된 환경 접촉",
                "curtains": "방어적, 은폐 욕구",
                "absent": "심한 철수, 고립"
            },
            "chimney": {
                "present_with_smoke": "따뜻한 가정, 정서적 만족",
                "present_no_smoke": "정서적 냉담",
                "absent": "가정 내 따뜻함 부재 인식",
                "excessive_smoke": "내적 긴장, 갈등"
            },
            "path": {
                "present": "접근성, 환영",
                "absent": "접근 어려움",
                "winding": "방어적 접근",
                "straight": "직접적 접근"
            }
        }

        # 나무 해석 가이드
        self.tree_guide = {
            "trunk": {
                "thick": "강한 자아, 안정감",
                "thin": "취약한 자아",
                "damaged": "트라우마, 상처",
                "hollow": "공허감, 정서적 결핍"
            },
            "branches": {
                "many_reaching_up": "환경과의 상호작용 욕구, 성장 지향",
                "few": "제한된 환경 접촉",
                "drooping": "무기력, 우울",
                "broken": "트라우마, 상실 경험",
                "sharp": "공격성, 방어"
            },
            "roots": {
                "visible": "현실감, 안정 욕구",
                "absent": "불안정감, 뿌리 없는 느낌",
                "exaggerated": "과도한 안정 욕구"
            },
            "leaves": {
                "present": "생명력, 성장",
                "absent": "공허, 상실감",
                "falling": "상실, 우울"
            },
            "size": {
                "large": "강한 자아, 과대평가 가능",
                "small": "위축된 자아, 낮은 자존감",
                "medium": "적절한 자아상"
            },
            "location": {
                "center": "안정감, 자기 중심성",
                "left": "과거 지향, 내향성",
                "right": "미래 지향, 외향성",
                "top": "환상, 이상",
                "bottom": "현실, 우울 가능"
            }
        }

        # 사람 해석 가이드
        self.person_guide = {
            "size": {
                "large": "과대한 자아, 보상적 자존감",
                "small": "낮은 자존감, 열등감",
                "medium": "적절한 자존감"
            },
            "head": {
                "large": "지적 야망, 환상 강조",
                "small": "지적 부적절감"
            },
            "eyes": {
                "large": "경계, 편집증적 경향",
                "small": "내적 초점, 자기 몰두",
                "closed": "외부 세계 차단",
                "absent": "관계 회피"
            },
            "mouth": {
                "large": "의존성, 구강기적 욕구",
                "small": "감정 억제",
                "absent": "소통 문제"
            },
            "arms": {
                "extended": "환경과의 상호작용 욕구",
                "hidden": "죄책감, 부적절감",
                "absent": "무력감",
                "crossed": "방어적, 적대적"
            },
            "hands": {
                "large": "공격성 또는 보상적 힘",
                "small": "부적절감",
                "absent": "무력감, 죄책감",
                "hidden": "죄책감"
            },
            "legs_feet": {
                "large": "안정 욕구",
                "small": "의존성",
                "absent": "불안정감",
                "spread": "공격성, 반항"
            },
            "expression": {
                "happy": "긍정적 자아상",
                "sad": "우울, 부정적 자아상",
                "angry": "공격성, 분노",
                "blank": "감정 억제, 해리"
            }
        }

        logger.info("HTPInterpreter initialized")

    def interpret(
        self,
        elements_data: Dict[str, Any],
        context: Optional[str] = None
    ) -> ProjectiveTestResult:
        """
        HTP 검사 해석

        Args:
            elements_data: 그림 요소 데이터
            context: 추가 맥락

        Returns:
            ProjectiveTestResult: 해석 결과
        """
        elements = []
        psychological_themes = []
        emotional_indicators = []
        relationship_patterns = []
        strengths = []
        concerns = []

        # 집 해석
        if "house" in elements_data:
            house_result = self._interpret_house(elements_data["house"])
            elements.extend(house_result["elements"])
            psychological_themes.extend(house_result["themes"])
            emotional_indicators.extend(house_result["emotions"])

        # 나무 해석
        if "tree" in elements_data:
            tree_result = self._interpret_tree(elements_data["tree"])
            elements.extend(tree_result["elements"])
            psychological_themes.extend(tree_result["themes"])
            emotional_indicators.extend(tree_result["emotions"])

        # 사람 해석
        if "person" in elements_data:
            person_result = self._interpret_person(elements_data["person"])
            elements.extend(person_result["elements"])
            psychological_themes.extend(person_result["themes"])
            emotional_indicators.extend(person_result["emotions"])
            relationship_patterns.extend(person_result["relationships"])

        # 통합 해석
        overall = self._generate_overall_interpretation(
            psychological_themes, emotional_indicators
        )

        # 강점과 관심 영역 분류
        strengths, concerns = self._categorize_findings(
            psychological_themes, emotional_indicators
        )

        # 치료적 질문 생성
        questions = self._generate_therapeutic_questions(
            psychological_themes, concerns
        )

        return ProjectiveTestResult(
            test_type=ProjectiveTestType.HTP,
            elements=elements,
            overall_interpretation=overall,
            psychological_themes=list(set(psychological_themes)),
            emotional_indicators=list(set(emotional_indicators)),
            relationship_patterns=list(set(relationship_patterns)),
            strengths_identified=strengths,
            areas_of_concern=concerns,
            therapeutic_questions=questions,
            confidence_level=self._calculate_confidence(elements_data)
        )

    def _interpret_house(self, house_data: Dict) -> Dict[str, List]:
        """집 해석"""
        result = {"elements": [], "themes": [], "emotions": []}

        for element, guide in self.house_guide.items():
            if element in house_data:
                value = house_data[element]
                if value in guide:
                    interpretation = guide[value]
                    result["elements"].append(HTPElement(
                        category="house",
                        element=element,
                        present=True,
                        characteristics={"value": value},
                        interpretation=interpretation
                    ))
                    result["themes"].append(interpretation)

        # 집 전체적 해석
        if house_data.get("overall_impression"):
            result["emotions"].append(house_data["overall_impression"])

        return result

    def _interpret_tree(self, tree_data: Dict) -> Dict[str, List]:
        """나무 해석"""
        result = {"elements": [], "themes": [], "emotions": []}

        for element, guide in self.tree_guide.items():
            if element in tree_data:
                value = tree_data[element]
                if value in guide:
                    interpretation = guide[value]
                    result["elements"].append(HTPElement(
                        category="tree",
                        element=element,
                        present=True,
                        characteristics={"value": value},
                        interpretation=interpretation
                    ))
                    result["themes"].append(interpretation)

        return result

    def _interpret_person(self, person_data: Dict) -> Dict[str, List]:
        """사람 해석"""
        result = {"elements": [], "themes": [], "emotions": [], "relationships": []}

        for element, guide in self.person_guide.items():
            if element in person_data:
                value = person_data[element]
                if value in guide:
                    interpretation = guide[value]
                    result["elements"].append(HTPElement(
                        category="person",
                        element=element,
                        present=True,
                        characteristics={"value": value},
                        interpretation=interpretation
                    ))
                    result["themes"].append(interpretation)

        # 대인관계 패턴
        if person_data.get("arms") in ["extended", "hidden"]:
            result["relationships"].append(
                "환경과의 상호작용 패턴" if person_data.get("arms") == "extended"
                else "대인관계 회피 경향"
            )

        return result

    def _generate_overall_interpretation(
        self,
        themes: List[str],
        emotions: List[str]
    ) -> str:
        """통합 해석 생성"""
        if not themes:
            return "추가 정보가 필요합니다."

        # 주요 테마 추출
        positive_indicators = [
            "강한 자아", "안정감", "성장", "긍정적", "환경과의 상호작용"
        ]
        negative_indicators = [
            "위축", "불안", "우울", "회피", "무력감", "취약"
        ]

        pos_count = sum(1 for t in themes if any(p in t for p in positive_indicators))
        neg_count = sum(1 for t in themes if any(n in t for n in negative_indicators))

        if pos_count > neg_count:
            overall_tone = "전반적으로 긍정적인 자아상과 적응력이 관찰됩니다."
        elif neg_count > pos_count:
            overall_tone = "몇 가지 정서적 어려움을 나타내는 요소들이 관찰됩니다."
        else:
            overall_tone = "긍정적 요소와 탐색이 필요한 요소가 혼재되어 있습니다."

        return f"{overall_tone} 주요 테마: {', '.join(themes[:3])}"

    def _categorize_findings(
        self,
        themes: List[str],
        emotions: List[str]
    ) -> Tuple[List[str], List[str]]:
        """강점과 관심 영역 분류"""
        strengths = []
        concerns = []

        strength_keywords = ["강한", "안정", "성장", "긍정", "생명력", "개방"]
        concern_keywords = ["위축", "불안", "우울", "회피", "무력", "취약", "결핍"]

        for theme in themes:
            if any(k in theme for k in strength_keywords):
                strengths.append(theme)
            elif any(k in theme for k in concern_keywords):
                concerns.append(theme)

        return strengths[:5], concerns[:5]

    def _generate_therapeutic_questions(
        self,
        themes: List[str],
        concerns: List[str]
    ) -> List[str]:
        """치료적 질문 생성"""
        questions = [
            "이 그림에서 가장 마음에 드는 부분은 어디인가요?",
            "그림을 그리면서 어떤 느낌이 드셨어요?"
        ]

        if any("집" in t or "가정" in t for t in themes + concerns):
            questions.append("그림 속 집에 누가 살고 있을까요?")
            questions.append("이 집에서의 생활은 어떨 것 같아요?")

        if any("자아" in t or "자존감" in t for t in themes + concerns):
            questions.append("그림 속 사람은 지금 어떤 기분일까요?")
            questions.append("이 사람에게 해주고 싶은 말이 있다면요?")

        if any("관계" in t or "대인" in t for t in themes + concerns):
            questions.append("이 사람 주변에 다른 사람들이 있다면 어디에 있을까요?")

        return questions[:5]

    def _calculate_confidence(self, data: Dict) -> float:
        """신뢰도 계산"""
        # 데이터 완성도 기반
        total_categories = 3  # house, tree, person
        present_categories = sum(1 for k in ["house", "tree", "person"] if k in data)

        base_confidence = present_categories / total_categories

        # 각 카테고리 내 요소 수에 따라 조정
        element_count = sum(len(v) if isinstance(v, dict) else 1 for v in data.values())
        element_bonus = min(0.2, element_count * 0.02)

        return min(0.95, base_confidence * 0.8 + element_bonus)


class KFDInterpreter:
    """
    KFD (동적 가족화) 검사 해석기

    동적 가족화 그림을 해석합니다.
    """

    def __init__(self):
        # 거리 해석
        self.distance_meanings = {
            "very_close": "친밀함, 의존성",
            "close": "긍정적 관계",
            "moderate": "적절한 거리",
            "far": "심리적 거리감",
            "very_far": "소외, 단절"
        }

        # 크기 해석
        self.size_meanings = {
            "very_large": "인지된 힘/영향력이 큼, 위협적으로 경험될 수 있음",
            "large": "중요한 인물, 영향력 있음",
            "medium": "적절한 중요성",
            "small": "낮은 영향력, 무시당함",
            "very_small": "무력하게 인식, 회피 대상"
        }

        # 활동 유형 해석
        self.activity_meanings = {
            "together": "가족 응집력, 협력",
            "separate": "개별화, 분리",
            "nurturing": "돌봄 관계",
            "conflict": "갈등 상황",
            "work": "역할 수행, 책임",
            "play": "즐거움, 친밀감",
            "isolated": "고립, 소외"
        }

        # 방향 해석
        self.facing_meanings = {
            "toward_family": "관계 지향, 연결 욕구",
            "toward_self": "본인에게 관심",
            "away": "회피, 거리두기",
            "forward": "외부 지향",
            "backward": "과거 지향, 퇴행"
        }

        logger.info("KFDInterpreter initialized")

    def interpret(
        self,
        family_data: Dict[str, Any],
        context: Optional[str] = None
    ) -> ProjectiveTestResult:
        """
        KFD 검사 해석

        Args:
            family_data: 가족화 데이터
            context: 추가 맥락

        Returns:
            ProjectiveTestResult: 해석 결과
        """
        members = []
        relationship_patterns = []
        emotional_indicators = []
        psychological_themes = []

        # 가족 구성원 분석
        for member_data in family_data.get("members", []):
            member = self._analyze_member(member_data)
            members.append(member)

        # 관계 패턴 분석
        relationship_patterns = self._analyze_relationships(members)

        # 자기 위치 분석
        self_analysis = self._analyze_self_position(family_data)
        psychological_themes.extend(self_analysis["themes"])
        emotional_indicators.extend(self_analysis["emotions"])

        # 생략된 구성원 분석
        omission_analysis = self._analyze_omissions(family_data)
        if omission_analysis:
            psychological_themes.extend(omission_analysis)

        # 활동 분석
        activity_analysis = self._analyze_activities(members)
        psychological_themes.extend(activity_analysis["themes"])

        # 통합 해석
        overall = self._generate_overall_interpretation(
            relationship_patterns, psychological_themes
        )

        # 강점과 관심 영역
        strengths, concerns = self._categorize_findings(
            relationship_patterns, psychological_themes
        )

        # 치료적 질문
        questions = self._generate_therapeutic_questions(
            relationship_patterns, concerns
        )

        return ProjectiveTestResult(
            test_type=ProjectiveTestType.KFD,
            elements=members,
            overall_interpretation=overall,
            psychological_themes=list(set(psychological_themes)),
            emotional_indicators=list(set(emotional_indicators)),
            relationship_patterns=list(set(relationship_patterns)),
            strengths_identified=strengths,
            areas_of_concern=concerns,
            therapeutic_questions=questions,
            confidence_level=self._calculate_confidence(family_data)
        )

    def _analyze_member(self, member_data: Dict) -> FamilyMember:
        """개별 가족 구성원 분석"""
        return FamilyMember(
            role=member_data.get("role", "unknown"),
            size=member_data.get("size", "medium"),
            position=member_data.get("position", "unknown"),
            activity=member_data.get("activity", "unknown"),
            facing=member_data.get("facing", "forward"),
            distance_from_self=member_data.get("distance_from_self", "moderate")
        )

    def _analyze_relationships(self, members: List[FamilyMember]) -> List[str]:
        """관계 패턴 분석"""
        patterns = []

        for member in members:
            # 거리 기반 해석
            distance_meaning = self.distance_meanings.get(
                member.distance_from_self, "알 수 없음"
            )
            patterns.append(f"{member.role}와(과)의 관계: {distance_meaning}")

            # 크기 기반 해석
            if member.size in ["very_large", "large"]:
                patterns.append(f"{member.role}이(가) 영향력 있는 인물로 인식됨")
            elif member.size in ["small", "very_small"]:
                patterns.append(f"{member.role}이(가) 약한 영향력으로 인식됨")

            # 방향 기반 해석
            facing_meaning = self.facing_meanings.get(member.facing, "")
            if facing_meaning:
                patterns.append(f"{member.role}의 방향: {facing_meaning}")

        return patterns

    def _analyze_self_position(self, family_data: Dict) -> Dict[str, List[str]]:
        """자기 위치 분석"""
        result = {"themes": [], "emotions": []}

        self_data = family_data.get("self", {})

        if not self_data:
            result["themes"].append("자신이 그림에서 생략됨 - 가족 내 소속감 문제 가능")
            return result

        # 위치 분석
        position = self_data.get("position", "")
        if "center" in position:
            result["themes"].append("가족의 중심에 위치 - 중요성 인식")
        elif "edge" in position or "corner" in position:
            result["themes"].append("가족의 주변부에 위치 - 소외감 가능")

        # 크기 분석
        size = self_data.get("size", "medium")
        if size in ["very_small", "small"]:
            result["emotions"].append("자신을 작게 표현 - 낮은 자존감 가능")
        elif size in ["very_large", "large"]:
            result["themes"].append("자신을 크게 표현 - 과대평가 또는 자기 주장")

        # 활동 분석
        activity = self_data.get("activity", "")
        if "alone" in activity or "isolated" in activity:
            result["emotions"].append("혼자 있는 활동 - 고립감")
        elif "with" in activity:
            result["themes"].append("가족과 함께하는 활동 - 소속감")

        return result

    def _analyze_omissions(self, family_data: Dict) -> List[str]:
        """생략된 구성원 분석"""
        themes = []

        omitted = family_data.get("omitted_members", [])
        for member in omitted:
            themes.append(f"{member}이(가) 생략됨 - 갈등, 거리감, 또는 부인 가능")

        return themes

    def _analyze_activities(self, members: List[FamilyMember]) -> Dict[str, List[str]]:
        """활동 분석"""
        result = {"themes": []}

        activities = [m.activity for m in members]

        # 공동 활동 여부
        if len(set(activities)) == 1 and activities[0] not in ["isolated", "unknown"]:
            result["themes"].append("가족이 함께하는 활동 - 응집력")
        elif all(a == "isolated" or "alone" in a for a in activities):
            result["themes"].append("각자 개별 활동 - 분리된 가족 구조")

        # 활동 유형별 해석
        for activity in set(activities):
            meaning = self.activity_meanings.get(activity)
            if meaning:
                result["themes"].append(meaning)

        return result

    def _generate_overall_interpretation(
        self,
        relationships: List[str],
        themes: List[str]
    ) -> str:
        """통합 해석 생성"""
        # 긍정적/부정적 지표 카운트
        positive_keywords = ["친밀", "협력", "중요", "연결", "소속"]
        negative_keywords = ["거리", "소외", "갈등", "고립", "분리"]

        all_text = " ".join(relationships + themes)

        pos = sum(1 for k in positive_keywords if k in all_text)
        neg = sum(1 for k in negative_keywords if k in all_text)

        if pos > neg:
            tone = "전반적으로 긍정적인 가족 관계가 표현되었습니다."
        elif neg > pos:
            tone = "가족 관계에서 일부 어려움이 표현되었습니다."
        else:
            tone = "가족 관계에 대한 다양한 측면이 표현되었습니다."

        return tone

    def _categorize_findings(
        self,
        relationships: List[str],
        themes: List[str]
    ) -> Tuple[List[str], List[str]]:
        """강점과 관심 영역 분류"""
        strengths = []
        concerns = []

        for item in relationships + themes:
            if any(k in item for k in ["친밀", "협력", "연결", "응집", "긍정"]):
                strengths.append(item)
            elif any(k in item for k in ["거리", "소외", "갈등", "생략", "고립"]):
                concerns.append(item)

        return strengths[:5], concerns[:5]

    def _generate_therapeutic_questions(
        self,
        relationships: List[str],
        concerns: List[str]
    ) -> List[str]:
        """치료적 질문 생성"""
        questions = [
            "이 그림에서 가족들이 무엇을 하고 있나요?",
            "그림 속에서 본인은 어디에 있나요?",
            "가족 중 가장 가까운 사람은 누구인가요?"
        ]

        if any("거리" in c or "소외" in c for c in concerns):
            questions.append("가족 중 조금 멀게 느껴지는 분이 있나요?")

        if any("갈등" in c for c in concerns):
            questions.append("가족 안에서 불편한 관계가 있나요?")

        if any("생략" in c for c in concerns):
            questions.append("그림에 포함하지 않은 가족이 있다면, 어떤 이유가 있을까요?")

        return questions[:5]

    def _calculate_confidence(self, data: Dict) -> float:
        """신뢰도 계산"""
        members = data.get("members", [])
        has_self = "self" in data

        base = 0.5 if has_self else 0.3
        member_bonus = min(0.3, len(members) * 0.06)

        return min(0.9, base + member_bonus)


# =============================================================================
# 통합 해석기
# =============================================================================

class ProjectiveTestInterpreter:
    """
    통합 투사 검사 해석기

    다양한 투사 검사를 해석합니다.
    """

    def __init__(self):
        self.htp_interpreter = HTPInterpreter()
        self.kfd_interpreter = KFDInterpreter()

        logger.info("ProjectiveTestInterpreter initialized")

    def interpret(
        self,
        test_type: ProjectiveTestType,
        data: Dict[str, Any],
        context: Optional[str] = None
    ) -> ProjectiveTestResult:
        """
        투사 검사 해석

        Args:
            test_type: 검사 유형
            data: 검사 데이터
            context: 추가 맥락

        Returns:
            ProjectiveTestResult: 해석 결과
        """
        if test_type == ProjectiveTestType.HTP:
            return self.htp_interpreter.interpret(data, context)
        elif test_type == ProjectiveTestType.KFD:
            return self.kfd_interpreter.interpret(data, context)
        else:
            # 기본 해석
            return self._basic_interpretation(test_type, data)

    def _basic_interpretation(
        self,
        test_type: ProjectiveTestType,
        data: Dict
    ) -> ProjectiveTestResult:
        """기본 해석"""
        return ProjectiveTestResult(
            test_type=test_type,
            elements=[],
            overall_interpretation="추가 분석이 필요합니다.",
            psychological_themes=[],
            emotional_indicators=[],
            relationship_patterns=[],
            strengths_identified=[],
            areas_of_concern=[],
            therapeutic_questions=[
                "이 그림에 대해 더 이야기해 주시겠어요?",
                "그림을 그리면서 어떤 느낌이 드셨나요?"
            ],
            confidence_level=0.3
        )

    def generate_feedback_prompt(
        self,
        result: ProjectiveTestResult
    ) -> str:
        """
        치료적 피드백 프롬프트 생성

        Args:
            result: 해석 결과

        Returns:
            str: 피드백 프롬프트
        """
        prompt_parts = [
            "## 투사 검사 피드백 가이드\n",
            f"검사 유형: {result.test_type.value}\n"
        ]

        if result.strengths_identified:
            prompt_parts.append("### 관찰된 강점:")
            for s in result.strengths_identified[:3]:
                prompt_parts.append(f"- {s}")
            prompt_parts.append("")

        if result.areas_of_concern:
            prompt_parts.append("### 탐색할 영역:")
            for c in result.areas_of_concern[:3]:
                prompt_parts.append(f"- {c}")
            prompt_parts.append("")

        prompt_parts.append("### 권장 질문:")
        for q in result.therapeutic_questions[:3]:
            prompt_parts.append(f"- {q}")

        prompt_parts.append("\n### 피드백 원칙:")
        prompt_parts.append("- 해석을 단정적으로 전달하지 마세요")
        prompt_parts.append("- '~처럼 보이는데, 어떻게 느끼세요?' 형태로 질문하세요")
        prompt_parts.append("- 내담자의 설명을 우선적으로 경청하세요")

        return "\n".join(prompt_parts)


# =============================================================================
# 테스트
# =============================================================================

def test_projective_tests():
    """투사 검사 해석기 테스트"""
    print("=== 투사 검사 해석기 테스트 ===\n")

    interpreter = ProjectiveTestInterpreter()

    # HTP 테스트
    print("=== HTP 검사 해석 ===")
    htp_data = {
        "house": {
            "roof": "large",
            "door": "small",
            "windows": "few",
            "chimney": "absent"
        },
        "tree": {
            "trunk": "thick",
            "branches": "many_reaching_up",
            "roots": "visible",
            "size": "large"
        },
        "person": {
            "size": "medium",
            "expression": "happy",
            "arms": "extended"
        }
    }

    htp_result = interpreter.interpret(ProjectiveTestType.HTP, htp_data)
    print(f"전체 해석: {htp_result.overall_interpretation}")
    print(f"강점: {htp_result.strengths_identified}")
    print(f"관심 영역: {htp_result.areas_of_concern}")
    print(f"치료적 질문: {htp_result.therapeutic_questions[:2]}")

    # KFD 테스트
    print("\n=== KFD 검사 해석 ===")
    kfd_data = {
        "members": [
            {"role": "아빠", "size": "large", "activity": "work", "facing": "away", "distance_from_self": "far"},
            {"role": "엄마", "size": "medium", "activity": "nurturing", "facing": "toward_self", "distance_from_self": "close"},
            {"role": "동생", "size": "small", "activity": "play", "facing": "toward_family", "distance_from_self": "close"}
        ],
        "self": {
            "position": "center",
            "size": "medium",
            "activity": "with_mom"
        },
        "omitted_members": []
    }

    kfd_result = interpreter.interpret(ProjectiveTestType.KFD, kfd_data)
    print(f"전체 해석: {kfd_result.overall_interpretation}")
    print(f"관계 패턴: {kfd_result.relationship_patterns[:3]}")
    print(f"치료적 질문: {kfd_result.therapeutic_questions[:2]}")

    # 피드백 프롬프트
    print("\n=== 피드백 프롬프트 ===")
    prompt = interpreter.generate_feedback_prompt(kfd_result)
    print(prompt[:500] + "...")


if __name__ == "__main__":
    test_projective_tests()
