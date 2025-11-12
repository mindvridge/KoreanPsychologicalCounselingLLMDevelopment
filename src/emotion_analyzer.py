"""
감정 분석 모듈
Emotion Analysis Module

사용자의 텍스트에서 감정을 분석하고 분류합니다.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from collections import Counter

logger = logging.getLogger(__name__)


class EmotionAnalyzer:
    """
    한국어 텍스트 감정 분석 클래스

    키워드 기반과 문맥 기반 분석을 결합하여
    사용자의 감정 상태를 파악합니다.
    """

    def __init__(self):
        """감정 분석기 초기화"""
        self.emotion_keywords = self._load_emotion_keywords()
        self.intensity_modifiers = self._load_intensity_modifiers()

    def _load_emotion_keywords(self) -> Dict[str, List[str]]:
        """
        감정 키워드 사전 로드

        Returns:
            Dict: 감정별 키워드 딕셔너리
        """
        return {
            "불안": [
                "불안", "걱정", "두렵", "무섭", "초조", "떨리", "조마조마",
                "긴장", "불안정", "안절부절", "심란", "혼란",
                "패닉", "공황", "불안감", "공포", "겁", "두려움"
            ],
            "우울": [
                "우울", "슬프", "힘들", "외롭", "쓸쓸", "허전", "공허",
                "무기력", "의욕 없", "무의미", "희망 없", "절망",
                "침울", "울적", "암담", "좌절", "비참", "처량",
                "눈물", "울고", "울었", "울", "서러"
            ],
            "분노": [
                "화", "짜증", "짜증나", "열받", "빡치", "빡쳐",
                "분노", "분하", "억울", "답답", "답답하", "미치겠",
                "미워", "증오", "싫어", "싫증", "짜증남", "화남",
                "열이 받", "열받아", "빡침", "짜증"
            ],
            "스트레스": [
                "스트레스", "부담", "압박", "버거", "벅차", "과부하",
                "피곤", "지쳐", "지침", "힘듦", "고단", "녹초",
                "지치", "너무 많", "감당", "못 하겠", "한계"
            ],
            "기쁨": [
                "기쁘", "행복", "즐겁", "좋", "신나", "뿌듯",
                "만족", "감사", "고맙", "다행", "기분 좋",
                "웃음", "웃겼", "재밌", "재미있"
            ],
            "수치심": [
                "부끄럽", "창피", "수치", "죄책감", "미안",
                "죄송", "면목없", "부끄러움", "민망", "낯뜨거",
                "쪽팔", "자격 없"
            ],
            "무감정": [
                "무감각", "무덤덤", "아무 느낌", "무관심",
                "아무렇지 않", "그냥", "별로", "뭐"
            ]
        }

    def _load_intensity_modifiers(self) -> Dict[str, float]:
        """
        감정 강도 수정자 로드

        Returns:
            Dict: 강도 수정 단어와 가중치
        """
        return {
            # 강화
            "너무": 1.5,
            "정말": 1.4,
            "엄청": 1.5,
            "완전": 1.4,
            "매우": 1.3,
            "굉장히": 1.4,
            "심하게": 1.5,
            "극도로": 1.6,
            "극심한": 1.6,
            "극심하게": 1.6,

            # 약화
            "조금": 0.7,
            "약간": 0.7,
            "살짝": 0.6,
            "좀": 0.8,
            "약": 0.7,

            # 부정
            "안": -1.0,
            "않": -1.0,
            "없": -1.0,
            "못": -1.0
        }

    def analyze(self, text: str) -> Dict[str, any]:
        """
        텍스트 감정 분석

        Args:
            text: 분석할 텍스트

        Returns:
            Dict: 분석 결과
                - primary_emotion: 주요 감정
                - emotions: 모든 감지된 감정과 점수
                - intensity: 감정 강도 (0-1)
                - details: 상세 정보
        """
        if not text or not text.strip():
            return self._empty_result()

        # 텍스트 정제
        text = text.lower().strip()

        # 감정 키워드 매칭
        emotion_scores = self._calculate_emotion_scores(text)

        # 감정 강도 계산
        intensity = self._calculate_intensity(text, emotion_scores)

        # 주요 감정 결정
        primary_emotion = self._determine_primary_emotion(emotion_scores)

        # 문맥적 단서 추출
        contextual_clues = self._extract_contextual_clues(text)

        result = {
            "primary_emotion": primary_emotion,
            "emotions": emotion_scores,
            "intensity": round(intensity, 2),
            "details": {
                "text_length": len(text),
                "contextual_clues": contextual_clues,
                "detected_keywords": self._get_detected_keywords(text)
            }
        }

        logger.info(f"Emotion analysis: {primary_emotion} (intensity: {intensity:.2f})")

        return result

    def _calculate_emotion_scores(self, text: str) -> Dict[str, float]:
        """
        감정 점수 계산

        Args:
            text: 입력 텍스트

        Returns:
            Dict: 감정별 점수
        """
        scores = {emotion: 0.0 for emotion in self.emotion_keywords.keys()}

        for emotion, keywords in self.emotion_keywords.items():
            for keyword in keywords:
                # 키워드 출현 횟수
                count = text.count(keyword)

                if count > 0:
                    # 기본 점수
                    base_score = count * 1.0

                    # 강도 수정자 적용
                    for modifier, weight in self.intensity_modifiers.items():
                        if modifier in text:
                            # 키워드 근처에 수정자가 있는지 확인
                            pattern = f"{modifier}.*{keyword}|{keyword}.*{modifier}"
                            if re.search(pattern, text):
                                if weight < 0:  # 부정
                                    base_score *= 0.1
                                else:
                                    base_score *= weight

                    scores[emotion] += base_score

        # 정규화 (0-1 범위)
        max_score = max(scores.values()) if max(scores.values()) > 0 else 1
        normalized_scores = {
            emotion: round(score / max_score, 2)
            for emotion, score in scores.items()
        }

        return normalized_scores

    def _calculate_intensity(
        self,
        text: str,
        emotion_scores: Dict[str, float]
    ) -> float:
        """
        감정 강도 계산

        Args:
            text: 입력 텍스트
            emotion_scores: 감정 점수

        Returns:
            float: 감정 강도 (0-1)
        """
        # 기본 강도는 최고 감정 점수
        base_intensity = max(emotion_scores.values()) if emotion_scores else 0

        # 강도 증폭 요소
        intensity_boosters = 0

        # 느낌표, 물음표 반복
        intensity_boosters += len(re.findall(r'!+', text)) * 0.1
        intensity_boosters += len(re.findall(r'\?+', text)) * 0.05

        # 대문자 사용 (한국어에서는 덜 중요)
        # 반복 문자 (예: "진짜아아아아")
        intensity_boosters += len(re.findall(r'(.)\1{2,}', text)) * 0.1

        # 강도 수정자 체크
        for modifier in ["너무", "정말", "엄청", "완전"]:
            if modifier in text:
                intensity_boosters += 0.15

        # 최종 강도 계산 (최대 1.0)
        final_intensity = min(base_intensity + intensity_boosters, 1.0)

        return final_intensity

    def _determine_primary_emotion(
        self,
        emotion_scores: Dict[str, float]
    ) -> str:
        """
        주요 감정 결정

        Args:
            emotion_scores: 감정 점수

        Returns:
            str: 주요 감정
        """
        if not emotion_scores or max(emotion_scores.values()) == 0:
            return "중립"

        # 가장 높은 점수의 감정
        primary = max(emotion_scores.items(), key=lambda x: x[1])

        # 점수가 매우 낮으면 중립
        if primary[1] < 0.3:
            return "중립"

        return primary[0]

    def _extract_contextual_clues(self, text: str) -> List[str]:
        """
        문맥적 단서 추출

        Args:
            text: 입력 텍스트

        Returns:
            List[str]: 문맥 단서 리스트
        """
        clues = []

        # 간접 표현
        indirect_expressions = ["그냥", "별거 아니", "괜찮", "뭐"]
        for expr in indirect_expressions:
            if expr in text:
                clues.append(f"간접표현: {expr}")

        # 부정적 자기 언급
        negative_self = ["나는 안 돼", "못해", "할 수 없", "자격 없"]
        for expr in negative_self:
            if expr in text:
                clues.append("부정적_자기인식")
                break

        # 질문 형태
        if "?" in text or "까요" in text or "ㄹ까" in text:
            clues.append("질문형")

        # 과거형 (이미 지나간 일)
        if "었" in text or "였" in text or "던" in text:
            clues.append("과거형")

        return clues

    def _get_detected_keywords(self, text: str) -> List[str]:
        """
        감지된 키워드 추출

        Args:
            text: 입력 텍스트

        Returns:
            List[str]: 감지된 키워드 리스트
        """
        detected = []

        for emotion, keywords in self.emotion_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    detected.append(f"{emotion}:{keyword}")

        return detected[:10]  # 최대 10개

    def _empty_result(self) -> Dict[str, any]:
        """
        빈 결과 반환

        Returns:
            Dict: 기본 결과
        """
        return {
            "primary_emotion": "중립",
            "emotions": {},
            "intensity": 0.0,
            "details": {}
        }

    def get_emotion_summary(self, text: str) -> str:
        """
        감정 분석 요약 텍스트

        Args:
            text: 분석할 텍스트

        Returns:
            str: 요약 문자열
        """
        result = self.analyze(text)

        primary = result["primary_emotion"]
        intensity = result["intensity"]

        intensity_label = "약함"
        if intensity > 0.7:
            intensity_label = "강함"
        elif intensity > 0.4:
            intensity_label = "중간"

        return f"{primary} (강도: {intensity_label})"


def test_emotion_analyzer():
    """감정 분석기 테스트"""
    analyzer = EmotionAnalyzer()

    test_cases = [
        "너무 불안하고 걱정돼요. 잠도 못 자겠어요.",
        "회사가 정말 힘들어요. 스트레스가 너무 심해요.",
        "아무것도 하기 싫고 무기력해요. 우울해요.",
        "화가 나요. 너무 억울하고 짜증나요.",
        "오늘 좋은 일이 있어서 기분이 좋네요.",
        "그냥 그래요. 별거 아니에요."
    ]

    print("=== 감정 분석 테스트 ===\n")
    for text in test_cases:
        result = analyzer.analyze(text)
        print(f"입력: {text}")
        print(f"주요 감정: {result['primary_emotion']}")
        print(f"강도: {result['intensity']}")
        print(f"감정 점수: {result['emotions']}")
        print("-" * 50)


if __name__ == "__main__":
    test_emotion_analyzer()
