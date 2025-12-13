"""
이미지 분석기 (Image Analyzer)
Vision AI 기반 그림 분석

기능:
- Vision AI (GPT-4V/Claude Vision) 연동
- 그림 요소 자동 감지
- 색상 분석
- 구도 분석
- 상징물 해석
"""

import logging
import base64
import json
import re
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class VisionProvider(Enum):
    """Vision AI 제공자"""
    OPENAI = "openai"        # GPT-4 Vision
    ANTHROPIC = "anthropic"  # Claude Vision
    LOCAL = "local"          # 로컬 분석 (Vision AI 없이)


@dataclass
class VisualElement:
    """시각적 요소"""
    element_type: str        # 요소 유형 (object, shape, line, etc.)
    description: str         # 설명
    position: str            # 위치 (center, top, bottom, left, right)
    size: str                # 크기 (small, medium, large)
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ColorInfo:
    """색상 정보"""
    color_name: str          # 색상명
    hex_code: Optional[str]  # HEX 코드
    coverage_percent: float  # 사용 비율
    psychological_meaning: str  # 심리학적 의미
    location: str            # 사용 위치


@dataclass
class ImageAnalysisResult:
    """이미지 분석 결과"""
    # 기본 정보
    image_id: str
    analysis_timestamp: datetime

    # 시각적 분석
    visual_elements: List[VisualElement]
    dominant_colors: List[ColorInfo]
    composition: Dict[str, Any]

    # 심리학적 해석
    overall_impression: str
    emotional_tone: str
    energy_level: str
    symbolic_elements: Dict[str, str]

    # 메타데이터
    confidence_score: float
    provider: VisionProvider
    raw_response: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "image_id": self.image_id,
            "timestamp": self.analysis_timestamp.isoformat(),
            "visual_elements": [
                {
                    "type": e.element_type,
                    "description": e.description,
                    "position": e.position,
                    "size": e.size
                }
                for e in self.visual_elements
            ],
            "dominant_colors": [
                {
                    "name": c.color_name,
                    "coverage": c.coverage_percent,
                    "meaning": c.psychological_meaning
                }
                for c in self.dominant_colors
            ],
            "composition": self.composition,
            "overall_impression": self.overall_impression,
            "emotional_tone": self.emotional_tone,
            "energy_level": self.energy_level,
            "symbolic_elements": self.symbolic_elements,
            "confidence": self.confidence_score
        }


class ColorPsychologyAnalyzer:
    """
    색상 심리 분석기

    색상의 심리학적 의미를 분석합니다.
    """

    def __init__(self):
        # 색상별 심리학적 의미 (한국 문화 맥락 포함)
        self.color_meanings = {
            # 기본 색상
            "빨강": {
                "emotions": ["열정", "분노", "에너지", "사랑"],
                "energy": "high",
                "associations": ["생명력", "강렬함", "위험", "흥분"],
                "korean_context": "전통적으로 길한 색, 액막이"
            },
            "주황": {
                "emotions": ["활력", "따뜻함", "창의성", "열정"],
                "energy": "medium-high",
                "associations": ["낙관", "모험", "사교성"],
                "korean_context": "승려의 색, 생명력"
            },
            "노랑": {
                "emotions": ["기쁨", "낙관", "주의", "불안"],
                "energy": "high",
                "associations": ["지성", "명랑", "경고"],
                "korean_context": "왕실의 색, 중심"
            },
            "초록": {
                "emotions": ["평화", "성장", "안정", "질투"],
                "energy": "medium",
                "associations": ["자연", "건강", "균형", "새로움"],
                "korean_context": "생명과 희망"
            },
            "파랑": {
                "emotions": ["평온", "슬픔", "신뢰", "차가움"],
                "energy": "low-medium",
                "associations": ["안정", "깊이", "지혜", "우울"],
                "korean_context": "젊음, 희망, 서민의 색"
            },
            "남색": {
                "emotions": ["직관", "깊이", "내면"],
                "energy": "low",
                "associations": ["지혜", "성찰", "신비"],
                "korean_context": "선비의 색"
            },
            "보라": {
                "emotions": ["창의성", "신비", "영성", "슬픔"],
                "energy": "medium",
                "associations": ["고귀함", "상상력", "명상"],
                "korean_context": "고귀함, 특별함"
            },
            "분홍": {
                "emotions": ["사랑", "부드러움", "순수", "낭만"],
                "energy": "low-medium",
                "associations": ["돌봄", "여성성", "친밀감"],
                "korean_context": "어린아이, 사랑"
            },
            "갈색": {
                "emotions": ["안정", "편안함", "따뜻함"],
                "energy": "low",
                "associations": ["대지", "안전", "신뢰성"],
                "korean_context": "자연, 소박함"
            },
            "검정": {
                "emotions": ["힘", "슬픔", "신비", "억압"],
                "energy": "varies",
                "associations": ["권위", "우아함", "공허", "보호"],
                "korean_context": "북쪽, 음(陰), 상복"
            },
            "흰색": {
                "emotions": ["순수", "평화", "공허", "새로움"],
                "energy": "neutral",
                "associations": ["깨끗함", "시작", "단순함"],
                "korean_context": "백의민족, 순수, 상복"
            },
            "회색": {
                "emotions": ["중립", "우울", "불확실", "타협"],
                "energy": "low",
                "associations": ["균형", "실용성", "무관심"],
                "korean_context": "중립, 도시적"
            }
        }

        # 색상명 변환 (영어 → 한국어)
        self.color_name_map = {
            "red": "빨강", "orange": "주황", "yellow": "노랑",
            "green": "초록", "blue": "파랑", "indigo": "남색",
            "purple": "보라", "violet": "보라", "pink": "분홍",
            "brown": "갈색", "black": "검정", "white": "흰색",
            "gray": "회색", "grey": "회색"
        }

    def analyze_color(self, color_name: str) -> Dict[str, Any]:
        """
        색상 분석

        Args:
            color_name: 색상명 (한글 또는 영어)

        Returns:
            Dict: 색상 분석 결과
        """
        # 영어명을 한국어로 변환
        korean_name = self.color_name_map.get(color_name.lower(), color_name)

        # 색상 정보 가져오기
        info = self.color_meanings.get(korean_name, {
            "emotions": ["알 수 없음"],
            "energy": "unknown",
            "associations": [],
            "korean_context": ""
        })

        return {
            "color": korean_name,
            "primary_emotions": info["emotions"][:2],
            "energy_level": info["energy"],
            "associations": info["associations"],
            "cultural_context": info.get("korean_context", "")
        }

    def analyze_color_combination(
        self,
        colors: List[str]
    ) -> Dict[str, Any]:
        """
        색상 조합 분석

        Args:
            colors: 사용된 색상 목록

        Returns:
            Dict: 조합 분석 결과
        """
        if not colors:
            return {"interpretation": "색상 정보 없음"}

        # 각 색상 분석
        analyses = [self.analyze_color(c) for c in colors]

        # 전체 에너지 수준
        energy_map = {"high": 3, "medium-high": 2.5, "medium": 2, "low-medium": 1.5, "low": 1}
        energies = [energy_map.get(a["energy_level"], 2) for a in analyses]
        avg_energy = sum(energies) / len(energies)

        if avg_energy > 2.5:
            overall_energy = "높음 - 활발하고 강렬한 에너지"
        elif avg_energy > 1.5:
            overall_energy = "중간 - 균형 잡힌 에너지"
        else:
            overall_energy = "낮음 - 차분하거나 억눌린 에너지"

        # 색상 조화 분석
        warm_colors = ["빨강", "주황", "노랑", "분홍"]
        cool_colors = ["파랑", "초록", "보라", "남색"]

        warm_count = sum(1 for a in analyses if a["color"] in warm_colors)
        cool_count = sum(1 for a in analyses if a["color"] in cool_colors)

        if warm_count > cool_count * 2:
            harmony = "따뜻한 색상 중심 - 감정 표현적, 외향적"
        elif cool_count > warm_count * 2:
            harmony = "차가운 색상 중심 - 감정 억제적, 내향적"
        else:
            harmony = "균형 잡힌 색상 사용 - 정서적 균형"

        return {
            "colors_used": [a["color"] for a in analyses],
            "overall_energy": overall_energy,
            "color_harmony": harmony,
            "dominant_emotions": list(set(
                emotion
                for a in analyses
                for emotion in a["primary_emotions"]
            ))[:4],
            "interpretation": self._generate_color_interpretation(analyses)
        }

    def _generate_color_interpretation(self, analyses: List[Dict]) -> str:
        """색상 조합 해석 생성"""
        emotions = []
        for a in analyses:
            emotions.extend(a["primary_emotions"])

        emotion_counts = {}
        for e in emotions:
            emotion_counts[e] = emotion_counts.get(e, 0) + 1

        top_emotions = sorted(emotion_counts.items(), key=lambda x: -x[1])[:3]

        if top_emotions:
            return f"주요 정서: {', '.join(e[0] for e in top_emotions)}"
        return "다양한 정서가 표현됨"


class ImageAnalyzer:
    """
    이미지 분석기

    Vision AI를 활용하여 그림을 분석합니다.
    """

    def __init__(
        self,
        provider: VisionProvider = VisionProvider.LOCAL,
        api_key: Optional[str] = None
    ):
        """
        초기화

        Args:
            provider: Vision AI 제공자
            api_key: API 키
        """
        self.provider = provider
        self.api_key = api_key
        self.color_analyzer = ColorPsychologyAnalyzer()

        # 분석 프롬프트 템플릿
        self.analysis_prompt = self._load_analysis_prompt()

        logger.info(f"ImageAnalyzer initialized with provider: {provider.value}")

    def _load_analysis_prompt(self) -> str:
        """분석 프롬프트 로드"""
        return """
이 그림을 심리상담 관점에서 분석해주세요.

## 분석 요청 항목

### 1. 시각적 요소
- 그림에 무엇이 있나요? (사물, 인물, 자연물 등)
- 각 요소의 위치와 크기는 어떠한가요?
- 선의 특성은 어떠한가요? (굵기, 압력, 연속성)

### 2. 색상
- 어떤 색상이 사용되었나요?
- 가장 많이 사용된 색상은?
- 색상의 강도와 배치는?

### 3. 구도와 공간
- 전체 공간 중 얼마나 사용되었나요?
- 요소들의 배치 패턴은?
- 빈 공간은 어디에 있나요?

### 4. 분위기
- 전체적인 분위기/느낌은?
- 에너지 수준은? (활발한/차분한/억눌린)

### 5. 특이점
- 눈에 띄는 특이한 요소가 있나요?
- 일반적이지 않은 표현이 있나요?

## 응답 형식 (JSON)

```json
{
    "visual_elements": [
        {"type": "요소유형", "description": "설명", "position": "위치", "size": "크기"}
    ],
    "colors": {
        "dominant": ["주요색상1", "주요색상2"],
        "accents": ["강조색상"],
        "overall_tone": "전체톤"
    },
    "composition": {
        "space_usage": "공간활용도",
        "balance": "균형상태",
        "focal_point": "초점"
    },
    "mood": {
        "overall": "전체분위기",
        "energy": "에너지수준",
        "emotional_tone": "정서톤"
    },
    "notable_features": ["특이점1", "특이점2"],
    "psychological_observations": ["관찰1", "관찰2"]
}
```

비판단적이고 객관적으로 분석해주세요.
"""

    async def analyze_image_async(
        self,
        image_data: Union[str, bytes],
        context: Optional[str] = None,
        activity_type: Optional[str] = None
    ) -> ImageAnalysisResult:
        """
        이미지 비동기 분석

        Args:
            image_data: 이미지 데이터 (base64 또는 bytes)
            context: 추가 컨텍스트
            activity_type: 활동 유형 (HTP, KFD 등)

        Returns:
            ImageAnalysisResult: 분석 결과
        """
        # 이미지 데이터 준비
        if isinstance(image_data, bytes):
            image_base64 = base64.b64encode(image_data).decode('utf-8')
        else:
            image_base64 = image_data

        # 프롬프트 구성
        prompt = self.analysis_prompt
        if activity_type:
            prompt += f"\n\n활동 유형: {activity_type}"
        if context:
            prompt += f"\n\n추가 컨텍스트: {context}"

        # 제공자별 분석
        if self.provider == VisionProvider.OPENAI:
            return await self._analyze_with_openai(image_base64, prompt)
        elif self.provider == VisionProvider.ANTHROPIC:
            return await self._analyze_with_anthropic(image_base64, prompt)
        else:
            return self._analyze_local(image_base64, prompt)

    def analyze_image(
        self,
        image_data: Union[str, bytes],
        context: Optional[str] = None,
        activity_type: Optional[str] = None
    ) -> ImageAnalysisResult:
        """
        이미지 동기 분석 (로컬 분석용)

        Args:
            image_data: 이미지 데이터
            context: 추가 컨텍스트
            activity_type: 활동 유형

        Returns:
            ImageAnalysisResult: 분석 결과
        """
        return self._analyze_local(image_data, context)

    async def _analyze_with_openai(
        self,
        image_base64: str,
        prompt: str
    ) -> ImageAnalysisResult:
        """OpenAI GPT-4 Vision으로 분석"""
        try:
            # OpenAI API 호출 (실제 구현 시 openai 라이브러리 사용)
            # 여기서는 인터페이스만 정의
            pass
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            return self._analyze_local(image_base64, prompt)

    async def _analyze_with_anthropic(
        self,
        image_base64: str,
        prompt: str
    ) -> ImageAnalysisResult:
        """Anthropic Claude Vision으로 분석"""
        try:
            # Anthropic API 호출 (실제 구현 시 anthropic 라이브러리 사용)
            # 여기서는 인터페이스만 정의
            pass
        except Exception as e:
            logger.error(f"Anthropic analysis failed: {e}")
            return self._analyze_local(image_base64, prompt)

    def _analyze_local(
        self,
        image_data: Union[str, bytes],
        context: Optional[str] = None
    ) -> ImageAnalysisResult:
        """
        로컬 분석 (Vision AI 없이)

        실제 Vision AI가 없을 때 사용하는 대체 분석
        사용자 설명 기반으로 분석합니다.
        """
        image_id = f"img_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 기본 분석 결과 생성 (사용자 설명 대기)
        return ImageAnalysisResult(
            image_id=image_id,
            analysis_timestamp=datetime.now(),
            visual_elements=[],
            dominant_colors=[],
            composition={
                "space_usage": "분석 대기",
                "balance": "분석 대기",
                "focal_point": "분석 대기"
            },
            overall_impression="그림을 받았습니다. 어떤 것을 그리셨는지 설명해 주시겠어요?",
            emotional_tone="탐색 중",
            energy_level="탐색 중",
            symbolic_elements={},
            confidence_score=0.3,
            provider=VisionProvider.LOCAL
        )

    def analyze_from_description(
        self,
        description: str,
        activity_type: Optional[str] = None
    ) -> ImageAnalysisResult:
        """
        사용자 설명 기반 분석

        Vision AI 없이 사용자의 그림 설명을 기반으로 분석

        Args:
            description: 사용자의 그림 설명
            activity_type: 활동 유형

        Returns:
            ImageAnalysisResult: 분석 결과
        """
        image_id = f"desc_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 색상 추출
        colors = self._extract_colors_from_text(description)
        color_analysis = self.color_analyzer.analyze_color_combination(colors)

        # 요소 추출
        elements = self._extract_elements_from_text(description, activity_type)

        # 분위기 추론
        mood = self._infer_mood(description, color_analysis)

        return ImageAnalysisResult(
            image_id=image_id,
            analysis_timestamp=datetime.now(),
            visual_elements=elements,
            dominant_colors=[
                ColorInfo(
                    color_name=c,
                    hex_code=None,
                    coverage_percent=0.0,
                    psychological_meaning=self.color_analyzer.analyze_color(c).get("primary_emotions", [""])[0],
                    location="전체"
                )
                for c in colors
            ],
            composition={
                "space_usage": self._infer_space_usage(description),
                "balance": "설명 기반 추론",
                "focal_point": self._infer_focal_point(description)
            },
            overall_impression=mood["overall"],
            emotional_tone=mood["emotional"],
            energy_level=color_analysis.get("overall_energy", "중간"),
            symbolic_elements=self._extract_symbols(description, activity_type),
            confidence_score=0.6,
            provider=VisionProvider.LOCAL
        )

    def _extract_colors_from_text(self, text: str) -> List[str]:
        """텍스트에서 색상 추출"""
        color_keywords = [
            "빨강", "빨간", "주황", "노랑", "노란", "초록", "녹색",
            "파랑", "파란", "남색", "보라", "분홍", "갈색", "검정",
            "검은", "흰색", "하얀", "회색"
        ]

        found_colors = []
        for color in color_keywords:
            if color in text:
                # 정규화
                normalized = color.replace("빨간", "빨강").replace("노란", "노랑")
                normalized = normalized.replace("파란", "파랑").replace("검은", "검정")
                normalized = normalized.replace("하얀", "흰색")
                if normalized not in found_colors:
                    found_colors.append(normalized)

        return found_colors

    def _extract_elements_from_text(
        self,
        text: str,
        activity_type: Optional[str]
    ) -> List[VisualElement]:
        """텍스트에서 시각적 요소 추출"""
        elements = []

        # HTP 관련 요소
        htp_elements = {
            "집": ["집", "지붕", "문", "창문", "굴뚝", "벽"],
            "나무": ["나무", "줄기", "가지", "잎", "뿌리", "열매"],
            "사람": ["사람", "얼굴", "눈", "코", "입", "팔", "다리", "손", "발", "머리"]
        }

        # 가족화 관련 요소
        family_elements = ["엄마", "아빠", "형", "누나", "동생", "가족", "나"]

        # 일반 요소
        general_elements = [
            "해", "달", "별", "구름", "하늘", "땅", "꽃", "산",
            "강", "바다", "길", "다리", "새", "동물"
        ]

        all_keywords = []
        if activity_type in ["HTP검사", "HTP"]:
            for category in htp_elements.values():
                all_keywords.extend(category)
        elif activity_type in ["가족화", "KFD"]:
            all_keywords.extend(family_elements)

        all_keywords.extend(general_elements)

        for keyword in all_keywords:
            if keyword in text:
                elements.append(VisualElement(
                    element_type="object",
                    description=keyword,
                    position="분석 필요",
                    size="분석 필요"
                ))

        return elements

    def _infer_mood(
        self,
        description: str,
        color_analysis: Dict
    ) -> Dict[str, str]:
        """분위기 추론"""
        # 긍정적 키워드
        positive = ["밝은", "행복", "웃는", "즐거운", "화창", "따뜻"]
        # 부정적 키워드
        negative = ["어두운", "슬픈", "우울", "비", "눈물", "차가운"]

        pos_count = sum(1 for p in positive if p in description)
        neg_count = sum(1 for n in negative if n in description)

        if pos_count > neg_count:
            overall = "밝고 긍정적인 분위기"
            emotional = "긍정적"
        elif neg_count > pos_count:
            overall = "어둡거나 침울한 분위기"
            emotional = "부정적"
        else:
            overall = "중립적인 분위기"
            emotional = "중립적"

        return {"overall": overall, "emotional": emotional}

    def _infer_space_usage(self, description: str) -> str:
        """공간 사용 추론"""
        if "작게" in description or "구석" in description:
            return "작은 공간 사용 - 위축된 자아상 가능"
        elif "크게" in description or "가득" in description:
            return "넓은 공간 사용 - 자신감 또는 통제욕구"
        return "보통의 공간 사용"

    def _infer_focal_point(self, description: str) -> str:
        """초점 추론"""
        focal_keywords = {
            "가운데": "중앙 - 자기 중심성",
            "위쪽": "상단 - 이상, 목표",
            "아래쪽": "하단 - 현실, 안정",
            "왼쪽": "좌측 - 과거, 내향성",
            "오른쪽": "우측 - 미래, 외향성"
        }

        for keyword, meaning in focal_keywords.items():
            if keyword in description:
                return meaning

        return "특정 초점 불명확"

    def _extract_symbols(
        self,
        description: str,
        activity_type: Optional[str]
    ) -> Dict[str, str]:
        """상징물 추출 및 해석"""
        symbols = {}

        symbol_meanings = {
            "해": "에너지, 따뜻함, 부성",
            "달": "여성성, 무의식, 변화",
            "별": "희망, 이상, 동경",
            "구름": "감정 상태, 불안정",
            "비": "슬픔, 정화, 감정 표출",
            "무지개": "희망, 조화, 통합",
            "꽃": "아름다움, 성장, 여성성",
            "새": "자유, 해방, 영적 측면",
            "나비": "변화, 변형, 자유",
            "길": "인생 여정, 선택",
            "다리": "연결, 전환, 과도기",
            "문": "기회, 경계, 새로운 시작",
            "창문": "외부 세계와의 연결",
            "물": "감정, 무의식",
            "불": "열정, 분노, 에너지",
            "산": "도전, 목표, 장애물"
        }

        for symbol, meaning in symbol_meanings.items():
            if symbol in description:
                symbols[symbol] = meaning

        return symbols


# =============================================================================
# Vision AI 분석 프롬프트 생성기
# =============================================================================

class VisionPromptGenerator:
    """
    Vision AI용 분석 프롬프트 생성기
    """

    @staticmethod
    def generate_htp_prompt() -> str:
        """HTP 검사용 프롬프트"""
        return """
이 그림은 HTP(House-Tree-Person) 심리검사 그림입니다.

다음 항목들을 분석해주세요:

## 집 (House) - 가정, 안전, 관계
- 지붕: 형태, 크기 (환상 영역)
- 벽: 두께, 선의 특성 (자아 강도)
- 문: 크기, 위치, 열림/닫힘 (대인관계)
- 창문: 개수, 크기, 커튼 유무 (외부와의 소통)
- 굴뚝: 유무, 연기 (가정의 따뜻함)
- 길: 유무, 형태 (접근성)

## 나무 (Tree) - 자아, 성장
- 줄기: 두께, 형태 (자아 강도)
- 가지: 형태, 방향 (환경과의 상호작용)
- 뿌리: 유무, 형태 (안정감, 현실감)
- 잎: 유무, 형태 (생명력)
- 전체 크기와 위치 (자아상)

## 사람 (Person) - 자기 이미지
- 크기와 위치 (자존감)
- 얼굴 표정 (감정 상태)
- 신체 비율 (신체상)
- 팔과 손 (환경 조작 능력)
- 다리와 발 (안정감)
- 옷과 장식 (사회적 자아)

JSON 형식으로 각 요소를 분석해주세요.
"""

    @staticmethod
    def generate_kfd_prompt() -> str:
        """동적 가족화용 프롬프트"""
        return """
이 그림은 동적 가족화(KFD) 심리검사 그림입니다.

다음 항목들을 분석해주세요:

## 가족 구성
- 그려진 가족 구성원 목록
- 각 인물의 크기 (인지된 힘/중요성)
- 배치와 거리 (심리적 거리)

## 활동 분석
- 각 인물의 활동 내용
- 상호작용 vs 개별 활동
- 협력적 vs 분리적 활동

## 관계 분석
- 인물 간 거리
- 얼굴 방향 (마주보기, 등지기)
- 신체적 접촉 유무
- 장벽 요소 (가구, 벽 등)

## 자기 표현
- 본인의 위치
- 본인의 크기
- 본인의 활동
- 다른 가족과의 관계

## 생략된 요소
- 생략된 가족 구성원
- 생략된 신체 부위

JSON 형식으로 분석해주세요.
"""


# =============================================================================
# 테스트
# =============================================================================

def test_image_analyzer():
    """이미지 분석기 테스트"""
    print("=== 이미지 분석기 테스트 ===\n")

    analyzer = ImageAnalyzer(provider=VisionProvider.LOCAL)

    # 사용자 설명 기반 분석 테스트
    description = """
    큰 나무를 그렸어요. 줄기가 굵고 가지가 많아요.
    잎은 초록색으로 많이 그렸고, 나무 아래에 작은 꽃들이 있어요.
    하늘에는 해가 밝게 떠 있고, 새 두 마리가 날고 있어요.
    """

    result = analyzer.analyze_from_description(description, "HTP검사")

    print("분석 결과:")
    print(f"  전체 인상: {result.overall_impression}")
    print(f"  감정 톤: {result.emotional_tone}")
    print(f"  에너지: {result.energy_level}")
    print(f"  시각 요소: {[e.description for e in result.visual_elements]}")
    print(f"  상징물: {result.symbolic_elements}")

    # 색상 분석 테스트
    print("\n=== 색상 분석 테스트 ===")
    color_analyzer = ColorPsychologyAnalyzer()

    colors = ["빨강", "파랑", "노랑"]
    color_result = color_analyzer.analyze_color_combination(colors)

    print(f"사용 색상: {color_result['colors_used']}")
    print(f"전체 에너지: {color_result['overall_energy']}")
    print(f"색상 조화: {color_result['color_harmony']}")
    print(f"주요 정서: {color_result['dominant_emotions']}")


if __name__ == "__main__":
    test_image_analyzer()
