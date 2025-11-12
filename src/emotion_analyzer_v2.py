"""
한국어 특화 감정 분석 시스템 (v2)
Korean Emotion Analysis System

6대 기본 감정 + 한국 특유 감정 분석
감정 강도 측정 (1-10 척도)
연령대별 표현 차이 인식
복합 감정 처리
감정 변화 추적
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from collections import deque
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EmotionRecord:
    """감정 기록"""
    timestamp: datetime
    primary_emotion: str
    intensity: float
    secondary_emotions: List[str]
    age_group: Optional[str]


class KoreanEmotionAnalyzer:
    """
    한국어 특화 감정 분석기

    특징:
    - 6대 기본 감정 + 한국 특유 감정
    - 1-10 척도 감정 강도 측정
    - 연령대별 표현 인식
    - 복합 감정 처리
    - 감정 변화 추적
    """

    def __init__(self, history_size: int = 20):
        """
        초기화

        Args:
            history_size: 추적할 감정 히스토리 크기
        """
        self.emotion_expressions = self._load_emotion_expressions()
        self.korean_specific_emotions = self._load_korean_emotions()
        self.age_group_expressions = self._load_age_group_expressions()
        self.emotion_history = deque(maxlen=history_size)

        logger.info("KoreanEmotionAnalyzer initialized")

    def _load_emotion_expressions(self) -> Dict[str, List[str]]:
        """
        6대 기본 감정 표현 로드

        Returns:
            Dict: 감정별 표현 리스트
        """
        return {
            # 1. 기쁨 (Joy)
            "기쁨": [
                "기쁘", "행복", "즐겁", "좋", "신나", "뿌듯",
                "만족", "감사", "고맙", "다행", "기분 좋",
                "웃음", "웃겼", "재밌", "재미있", "유쾌",
                "흐뭇", "상쾌", "통쾌", "짜릿", "신남"
            ],

            # 2. 슬픔 (Sadness)
            "슬픔": [
                "슬프", "슬퍼", "눈물", "울", "울고", "울었",
                "서러", "서글", "비참", "비애", "애달",
                "처량", "쓸쓸", "허전", "허무", "공허",
                "상실", "잃", "그리", "아쉽", "안타깝"
            ],

            # 3. 분노 (Anger)
            "분노": [
                "화", "짜증", "열받", "빡치", "빡쳐", "열나",
                "분하", "억울", "미워", "증오", "싫", "싫어",
                "짜증나", "화나", "분노", "격분", "격노",
                "울화", "치밀", "약오르", "미치겠", "답답"
            ],

            # 4. 두려움 (Fear)
            "두려움": [
                "무섭", "두렵", "겁", "공포", "무서워",
                "두려워", "떨리", "조마조마", "불안", "초조",
                "긴장", "겁나", "무시무시", "오싹", "섬뜩",
                "소름", "위협", "위험", "위기", "걱정"
            ],

            # 5. 놀람 (Surprise)
            "놀람": [
                "놀랐", "놀라", "깜짝", "어머", "헉", "와",
                "대박", "충격", "당황", "어안이벙벙", "아연실색",
                "예상 못", "뜻밖", "의외", "신기", "새롭"
            ],

            # 6. 역겨움/혐오 (Disgust)
            "역겨움": [
                "역겹", "징그럽", "더럽", "추하", "혐오",
                "구역질", "메스껍", "토할", "불쾌", "끔찍",
                "소름", "진저리", "치사", "비열", "추잡"
            ]
        }

    def _load_korean_emotions(self) -> Dict[str, List[str]]:
        """
        한국 특유의 감정 표현 로드

        Returns:
            Dict: 한국 특유 감정 표현
        """
        return {
            # 한 (恨) - 억울하고 원통한 감정의 응어리
            "한": [
                "한", "원한", "원망", "한맺힌", "서러운",
                "원통", "한스럽", "맺힌", "사무치", "응어리"
            ],

            # 정 (情) - 사람 사이의 따뜻한 인간적 유대감
            "정": [
                "정", "정들", "정이 가", "정이 많", "정겨",
                "정스럽", "애정", "인정", "의리", "따뜻"
            ],

            # 아쉬움 - 만족스럽지 못하거나 충분하지 않아 안타까운 마음
            "아쉬움": [
                "아쉽", "미련", "아깝", "안타깝", "섭섭",
                "못내", "여한", "미진", "부족", "모자라"
            ],

            # 서러움 - 억울하고 슬픈 마음
            "서러움": [
                "서러", "서럽", "서글", "설움", "눈물겹",
                "비참", "애달", "가엾", "불쌍", "한스러"
            ],

            # 우울 (한국적 맥락에서의 우울)
            "우울": [
                "우울", "울적", "침울", "음울", "답답",
                "무기력", "의욕 없", "무감각", "공허", "허무",
                "회색", "암울", "어둡", "무겁", "가라앉"
            ],

            # 불안 (한국적 표현)
            "불안": [
                "불안", "걱정", "초조", "조마조마", "안절부절",
                "마음 졸", "심란", "불안정", "혼란", "혼돈",
                "마음 편치 않", "찜찜", "께름칙", "불편"
            ],

            # 수치심
            "수치심": [
                "부끄럽", "창피", "쪽팔", "민망", "낯뜨거",
                "수치", "창피스럽", "면목없", "부끄러워",
                "체면", "염치", "얼굴 들"
            ],

            # 죄책감
            "죄책감": [
                "미안", "죄송", "죄책감", "잘못", "용서",
                "미안해", "죄스럽", "죄송스럽", "송구",
                "뉘우치", "회개", "참회", "반성"
            ],

            # 외로움
            "외로움": [
                "외롭", "외로워", "쓸쓸", "고독", "고립",
                "혼자", "홀로", "따로", "떨어져", "소외",
                "고독하", "쓸쓸하", "쓸쓸함", "적막"
            ]
        }

    def _load_age_group_expressions(self) -> Dict[str, Dict[str, List[str]]]:
        """
        연령대별 감정 표현 특성 로드

        Returns:
            Dict: 연령대별 표현 패턴
        """
        return {
            # 10대 (10-19세)
            "10대": {
                "markers": [
                    "ㅋㅋ", "ㅠㅠ", "ㅜㅜ", "ㄷㄷ", "ㅇㅈ", "ㄹㅇ",
                    "헐", "대박", "쩐다", "짱", "쩔어",
                    "개", "존나", "ㅈㄴ", "레알", "리얼",
                    "엄마", "아빠", "학교", "공부", "시험",
                    "학원", "친구들", "애들", "쌤", "선생님"
                ],
                "emotions": {
                    "짜증": ["짜증", "짜증나", "개짜증", "존짜"],
                    "빡침": ["빡쳐", "빡침", "개빡", "열받"],
                    "우울": ["우울해", "우울", "멘붕", "ㅈ됐어"],
                    "기쁨": ["좋아", "조아", "좋당", "굿굿", "굿"]
                }
            },

            # 20-30대 (20-39세)
            "20-30대": {
                "markers": [
                    "회사", "직장", "상사", "동료", "팀장",
                    "야근", "업무", "퇴사", "이직", "취업",
                    "연애", "결혼", "부모님", "엄마", "아빠",
                    "친구", "지인", "선배", "후배",
                    "요즘", "최근", "오늘", "내일"
                ],
                "emotions": {
                    "스트레스": ["스트레스", "압박", "부담"],
                    "번아웃": ["번아웃", "탈진", "한계"],
                    "불안": ["불안해", "걱정돼", "무서워"],
                    "우울": ["우울해", "힘들어", "지쳐"]
                }
            },

            # 40대 이상 (40+)
            "40대이상": {
                "markers": [
                    "자식", "아들", "딸", "아이", "애",
                    "남편", "아내", "배우자", "가족",
                    "부모", "자녀", "사위", "며느리",
                    "건강", "병원", "질병", "치료",
                    "노후", "은퇴", "퇴직"
                ],
                "emotions": {
                    "걱정": ["걱정이", "근심", "염려"],
                    "한": ["한이", "원망", "서러움"],
                    "서글픔": ["서글픈", "쓸쓸한", "외로운"],
                    "아쉬움": ["아쉬운", "미련", "안타까운"]
                }
            }
        }

    def analyze(
        self,
        text: str,
        context: Optional[Dict] = None
    ) -> Dict[str, any]:
        """
        종합적 감정 분석

        Args:
            text: 분석할 텍스트
            context: 추가 컨텍스트 (이전 대화 등)

        Returns:
            Dict: 분석 결과
                - primary_emotion: 주요 감정
                - intensity: 강도 (1-10)
                - secondary_emotions: 부가 감정들
                - confidence: 신뢰도 (0-1)
                - cultural_markers: 문화적 특징
                - age_group_estimated: 추정 연령대
                - emotion_details: 상세 정보
        """
        text = text.strip()

        if not text:
            return self._empty_result()

        # 1. 기본 6대 감정 분석
        basic_emotions = self._analyze_basic_emotions(text)

        # 2. 한국 특유 감정 분석
        korean_emotions = self._analyze_korean_emotions(text)

        # 3. 모든 감정 통합
        all_emotions = {**basic_emotions, **korean_emotions}

        # 4. 주요 감정 결정
        primary_emotion = self._determine_primary_emotion(all_emotions)

        # 5. 감정 강도 측정 (1-10)
        intensity = self._measure_intensity(text, primary_emotion, all_emotions)

        # 6. 부가 감정 추출
        secondary_emotions = self._extract_secondary_emotions(
            all_emotions,
            primary_emotion
        )

        # 7. 연령대 추정
        age_group = self._estimate_age_group(text)

        # 8. 문화적 마커 감지
        cultural_markers = self._detect_cultural_markers(text)

        # 9. 신뢰도 계산
        confidence = self._calculate_confidence(
            all_emotions,
            text,
            age_group
        )

        # 10. 복합 감정 감지
        complex_emotions = self._detect_complex_emotions(all_emotions)

        result = {
            "primary_emotion": primary_emotion,
            "intensity": round(intensity, 1),
            "secondary_emotions": secondary_emotions,
            "confidence": round(confidence, 2),
            "cultural_markers": cultural_markers,
            "age_group_estimated": age_group,
            "emotion_details": {
                "basic_emotions": basic_emotions,
                "korean_emotions": korean_emotions,
                "complex_emotions": complex_emotions,
                "all_scores": all_emotions
            },
            "text_features": {
                "length": len(text),
                "has_emoticons": self._has_emoticons(text),
                "has_repetition": self._has_repetition(text),
                "formality": self._assess_formality(text)
            }
        }

        # 히스토리에 기록
        self._record_emotion(result)

        return result

    def _analyze_basic_emotions(self, text: str) -> Dict[str, float]:
        """
        6대 기본 감정 분석

        Args:
            text: 입력 텍스트

        Returns:
            Dict: 감정별 점수 (0-1)

        예시:
            >>> analyzer._analyze_basic_emotions("정말 기쁘고 행복해요!")
            {'기쁨': 0.85, '슬픔': 0.0, '분노': 0.0, ...}
        """
        scores = {}

        for emotion, keywords in self.emotion_expressions.items():
            score = 0.0

            for keyword in keywords:
                if keyword in text:
                    score += 1.0

            scores[emotion] = score

        # 정규화 (0-1)
        max_score = max(scores.values()) if max(scores.values()) > 0 else 1.0

        normalized = {
            emotion: round(score / max_score, 2)
            for emotion, score in scores.items()
        }

        return normalized

    def _analyze_korean_emotions(self, text: str) -> Dict[str, float]:
        """
        한국 특유 감정 분석

        Args:
            text: 입력 텍스트

        Returns:
            Dict: 한국 감정별 점수

        예시:
            >>> analyzer._analyze_korean_emotions("정말 한스럽고 서러워요")
            {'한': 0.9, '서러움': 0.8, ...}
        """
        scores = {}

        for emotion, keywords in self.korean_specific_emotions.items():
            score = 0.0

            for keyword in keywords:
                if keyword in text:
                    score += 1.0

            scores[emotion] = score

        # 정규화
        max_score = max(scores.values()) if max(scores.values()) > 0 else 1.0

        normalized = {
            emotion: round(score / max_score, 2)
            for emotion, score in scores.items()
        }

        return normalized

    def _determine_primary_emotion(self, all_emotions: Dict[str, float]) -> str:
        """
        주요 감정 결정

        Args:
            all_emotions: 모든 감정 점수

        Returns:
            str: 주요 감정
        """
        if not all_emotions or max(all_emotions.values()) == 0:
            return "중립"

        # 가장 높은 점수의 감정
        primary = max(all_emotions.items(), key=lambda x: x[1])

        # 점수가 너무 낮으면 중립
        if primary[1] < 0.3:
            return "중립"

        return primary[0]

    def _measure_intensity(
        self,
        text: str,
        primary_emotion: str,
        all_emotions: Dict[str, float]
    ) -> float:
        """
        감정 강도 측정 (1-10 척도)

        Args:
            text: 입력 텍스트
            primary_emotion: 주요 감정
            all_emotions: 모든 감정 점수

        Returns:
            float: 강도 (1-10)

        예시:
            >>> analyzer._measure_intensity("너무너무 화나요!!!", "분노", {...})
            9.2
        """
        # 기본 강도 (5.0)
        intensity = 5.0

        # 주요 감정의 점수 반영
        if primary_emotion in all_emotions:
            emotion_score = all_emotions[primary_emotion]
            intensity += emotion_score * 3.0  # 최대 +3

        # 텍스트 기반 증폭 요소

        # 1. 강조 부사
        emphasis_patterns = {
            "극도로|극심|극히": 2.0,
            "너무너무|정말정말|진짜진짜": 1.8,
            "너무|정말|진짜|완전|엄청": 1.2,
            "매우|굉장히|심하게|몹시": 1.0,
            "조금|약간|살짝": -0.5
        }

        for pattern, boost in emphasis_patterns.items():
            if re.search(pattern, text):
                intensity += boost

        # 2. 느낌표
        exclamation_count = text.count("!")
        intensity += min(exclamation_count * 0.5, 2.0)

        # 3. 반복 문자 (예: "아아아", "ㅠㅠㅠ")
        if re.search(r'(.)\1{2,}', text):
            intensity += 1.0

        # 4. 이모티콘/이모지
        emoticon_patterns = [
            r'ㅠㅠ|ㅜㅜ|ㅡㅡ|ㅎㅎ|ㅋㅋ',
            r'[😀-🙏]'  # 이모지 범위
        ]

        for pattern in emoticon_patterns:
            if re.search(pattern, text):
                intensity += 0.5

        # 5. 부정 표현 (강도 증폭)
        negation_patterns = ["견딜 수 없", "참을 수 없", "도저히", "도무지"]
        for pattern in negation_patterns:
            if pattern in text:
                intensity += 1.5

        # 6. 극단적 표현
        extreme_patterns = ["죽겠", "미치겠", "터질 것 같", "폭발"]
        for pattern in extreme_patterns:
            if pattern in text:
                intensity += 1.0

        # 최소 1, 최대 10으로 제한
        return max(1.0, min(intensity, 10.0))

    def _extract_secondary_emotions(
        self,
        all_emotions: Dict[str, float],
        primary_emotion: str
    ) -> List[str]:
        """
        부가 감정 추출

        Args:
            all_emotions: 모든 감정 점수
            primary_emotion: 주요 감정

        Returns:
            List[str]: 부가 감정 리스트 (최대 3개)
        """
        # 주요 감정을 제외한 감정들
        secondary = {
            emotion: score
            for emotion, score in all_emotions.items()
            if emotion != primary_emotion and score > 0.3
        }

        # 점수 순으로 정렬하여 상위 3개
        sorted_emotions = sorted(
            secondary.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [emotion for emotion, score in sorted_emotions[:3]]

    def _estimate_age_group(self, text: str) -> Optional[str]:
        """
        연령대 추정

        Args:
            text: 입력 텍스트

        Returns:
            Optional[str]: 추정 연령대 (10대, 20-30대, 40대이상, None)

        예시:
            >>> analyzer._estimate_age_group("학교에서 친구들이랑 짱나는 일이 있었어 ㅠㅠ")
            "10대"
        """
        age_scores = {}

        for age_group, data in self.age_group_expressions.items():
            score = 0

            # 마커 체크
            for marker in data["markers"]:
                if marker in text:
                    score += 1

            # 감정 표현 체크
            for emotion_type, expressions in data["emotions"].items():
                for expr in expressions:
                    if expr in text:
                        score += 0.5

            age_scores[age_group] = score

        # 가장 높은 점수의 연령대
        if max(age_scores.values()) >= 2.0:  # 최소 임계값
            return max(age_scores.items(), key=lambda x: x[1])[0]

        return None

    def _detect_cultural_markers(self, text: str) -> List[str]:
        """
        한국 문화적 마커 감지

        Args:
            text: 입력 텍스트

        Returns:
            List[str]: 문화적 마커 리스트
        """
        markers = []

        # 간접 표현
        indirect_phrases = ["그냥", "별거 아니", "괜찮아", "뭐", "글쎄"]
        if any(phrase in text for phrase in indirect_phrases):
            markers.append("간접표현")

        # 체면 관련
        face_phrases = ["창피", "부끄럽", "쪽팔", "면목", "체면"]
        if any(phrase in text for phrase in face_phrases):
            markers.append("체면중시")

        # 집단주의
        collective_phrases = [
            "남들", "다른 사람", "주변", "가족", "부모님",
            "실망", "기대", "눈치"
        ]
        if any(phrase in text for phrase in collective_phrases):
            markers.append("집단주의")

        # 위계질서
        hierarchy_phrases = [
            "상사", "선배", "윗사람", "아랫사람", "손윗",
            "연장자", "어른"
        ]
        if any(phrase in text for phrase in hierarchy_phrases):
            markers.append("위계의식")

        # 효 문화
        filial_phrases = ["부모", "효도", "봉양", "모시", "자식"]
        if any(phrase in text for phrase in filial_phrases):
            markers.append("효문화")

        # 정서적 억압
        suppression_phrases = [
            "참", "견디", "억지로", "숨기", "표현 못",
            "말 못", "드러내지"
        ]
        if any(phrase in text for phrase in suppression_phrases):
            markers.append("정서억압")

        return markers

    def _calculate_confidence(
        self,
        all_emotions: Dict[str, float],
        text: str,
        age_group: Optional[str]
    ) -> float:
        """
        분석 신뢰도 계산

        Args:
            all_emotions: 모든 감정 점수
            text: 입력 텍스트
            age_group: 연령대

        Returns:
            float: 신뢰도 (0-1)
        """
        confidence = 0.5  # 기본값

        # 최고 감정 점수가 높을수록 신뢰도 증가
        max_score = max(all_emotions.values()) if all_emotions else 0
        confidence += max_score * 0.3

        # 텍스트 길이 (너무 짧으면 신뢰도 감소)
        text_length = len(text)
        if text_length < 10:
            confidence -= 0.2
        elif text_length > 50:
            confidence += 0.1

        # 연령대 추정 성공 시 신뢰도 증가
        if age_group:
            confidence += 0.1

        # 명확한 감정 키워드가 있으면 신뢰도 증가
        clear_keywords = ["느껴", "감정", "기분", "마음"]
        if any(keyword in text for keyword in clear_keywords):
            confidence += 0.1

        return max(0.0, min(confidence, 1.0))

    def _detect_complex_emotions(self, all_emotions: Dict[str, float]) -> Dict[str, any]:
        """
        복합 감정 감지

        Args:
            all_emotions: 모든 감정 점수

        Returns:
            Dict: 복합 감정 정보
        """
        # 0.4 이상인 감정들
        significant_emotions = {
            emotion: score
            for emotion, score in all_emotions.items()
            if score >= 0.4
        }

        is_complex = len(significant_emotions) >= 2

        # 모순된 감정 체크 (예: 기쁨+슬픔)
        contradictory_pairs = [
            ("기쁨", "슬픔"),
            ("기쁨", "분노"),
            ("기쁨", "두려움")
        ]

        contradictions = []
        for emotion1, emotion2 in contradictory_pairs:
            if (emotion1 in significant_emotions and
                emotion2 in significant_emotions):
                contradictions.append((emotion1, emotion2))

        return {
            "is_complex": is_complex,
            "significant_emotions": list(significant_emotions.keys()),
            "emotion_count": len(significant_emotions),
            "contradictions": contradictions
        }

    def _has_emoticons(self, text: str) -> bool:
        """이모티콘 존재 여부"""
        patterns = [
            r'ㅋㅋ|ㅎㅎ|ㅠㅠ|ㅜㅜ|ㅡㅡ',
            r':\)|:\(|:D|:P',
            r'[😀-🙏🌀-🗿]'
        ]

        return any(re.search(pattern, text) for pattern in patterns)

    def _has_repetition(self, text: str) -> bool:
        """반복 표현 존재 여부"""
        return bool(re.search(r'(.{2,})\1+', text))

    def _assess_formality(self, text: str) -> str:
        """
        격식 수준 평가

        Returns:
            str: "formal", "informal", "casual"
        """
        # 존댓말 마커
        formal_markers = ["습니다", "입니다", "ㅂ니다", "요", "니다"]

        # 반말 마커
        informal_markers = ["야", "해", "어", "지", "거든"]

        # 격식없는 표현
        casual_markers = ["ㅋㅋ", "ㅎㅎ", "ㅇㅇ", "ㄴㄴ", "ㅈㄴ"]

        formal_count = sum(1 for marker in formal_markers if marker in text)
        informal_count = sum(1 for marker in informal_markers if marker in text)
        casual_count = sum(1 for marker in casual_markers if marker in text)

        if casual_count >= 2:
            return "casual"
        elif formal_count >= 2:
            return "formal"
        else:
            return "informal"

    def _record_emotion(self, result: Dict):
        """
        감정 히스토리에 기록

        Args:
            result: 분석 결과
        """
        record = EmotionRecord(
            timestamp=datetime.now(),
            primary_emotion=result["primary_emotion"],
            intensity=result["intensity"],
            secondary_emotions=result["secondary_emotions"],
            age_group=result.get("age_group_estimated")
        )

        self.emotion_history.append(record)

    def get_emotion_trend(self) -> Dict[str, any]:
        """
        감정 변화 추세 분석

        Returns:
            Dict: 추세 정보
        """
        if len(self.emotion_history) < 2:
            return {"trend": "insufficient_data"}

        recent = list(self.emotion_history)[-5:]

        # 강도 추세
        intensities = [record.intensity for record in recent]

        if len(intensities) >= 3:
            if intensities[-1] > intensities[-2] > intensities[-3]:
                intensity_trend = "increasing"
            elif intensities[-1] < intensities[-2] < intensities[-3]:
                intensity_trend = "decreasing"
            else:
                intensity_trend = "stable"
        else:
            intensity_trend = "stable"

        # 주요 감정 변화
        emotions = [record.primary_emotion for record in recent]
        emotion_changes = len(set(emotions))

        # 감정 전환점 (dramatic shift)
        transition_points = []
        for i in range(1, len(recent)):
            if recent[i].primary_emotion != recent[i-1].primary_emotion:
                transition_points.append({
                    "from": recent[i-1].primary_emotion,
                    "to": recent[i].primary_emotion,
                    "timestamp": recent[i].timestamp.isoformat()
                })

        return {
            "intensity_trend": intensity_trend,
            "recent_intensities": intensities,
            "average_intensity": sum(intensities) / len(intensities),
            "emotion_stability": "unstable" if emotion_changes >= 4 else "stable",
            "transition_points": transition_points,
            "dominant_emotion": max(set(emotions), key=emotions.count)
        }

    def _empty_result(self) -> Dict[str, any]:
        """빈 결과 반환"""
        return {
            "primary_emotion": "중립",
            "intensity": 5.0,
            "secondary_emotions": [],
            "confidence": 0.0,
            "cultural_markers": [],
            "age_group_estimated": None,
            "emotion_details": {},
            "text_features": {}
        }


if __name__ == "__main__":
    # 테스트
    print("=== 한국어 감정 분석 시스템 테스트 ===\n")

    analyzer = KoreanEmotionAnalyzer()

    test_cases = [
        ("너무너무 기쁘고 행복해요!!! 정말 최고예요 ㅋㅋㅋ", "기쁨"),
        ("학교에서 친구들이랑 싸워서 진짜 빡쳐 ㅡㅡ", "분노 + 10대"),
        ("회사 상사가 너무 스트레스예요. 이직하고 싶어요.", "스트레스 + 20-30대"),
        ("한스럽고 서러워요. 원망스럽기까지 해요.", "한 + 서러움"),
        ("그냥 그래요. 별거 아니에요.", "간접 표현"),
        ("부모님 실망시킬까 봐 두렵고 창피해요.", "두려움 + 체면"),
        ("아이가 걱정돼요. 건강이 좋지 않아서요.", "걱정 + 40대이상"),
    ]

    for i, (text, expected) in enumerate(test_cases, 1):
        print(f"테스트 {i}: {text}")
        print(f"예상: {expected}")
        print("-" * 70)

        result = analyzer.analyze(text)

        print(f"주요 감정: {result['primary_emotion']}")
        print(f"강도: {result['intensity']}/10")
        print(f"부가 감정: {', '.join(result['secondary_emotions']) if result['secondary_emotions'] else '없음'}")
        print(f"연령대: {result['age_group_estimated'] or '미추정'}")
        print(f"문화적 마커: {', '.join(result['cultural_markers']) if result['cultural_markers'] else '없음'}")
        print(f"신뢰도: {result['confidence']:.2f}")

        if result['emotion_details']['complex_emotions']['is_complex']:
            print(f"복합 감정: {result['emotion_details']['complex_emotions']['significant_emotions']}")

        print("\n" + "=" * 70 + "\n")

    # 감정 추세 확인
    print("감정 추세 분석:")
    trend = analyzer.get_emotion_trend()
    print(f"강도 추세: {trend.get('intensity_trend', 'N/A')}")
    print(f"평균 강도: {trend.get('average_intensity', 0):.1f}")
    print(f"주된 감정: {trend.get('dominant_emotion', 'N/A')}")
