"""
다층 위기 감지 및 안전 시스템 (v2)
Multi-layered Crisis Detection and Safety System

4층 구조의 종합적 위기 감지 시스템:
1. KeywordDetector: 즉각적 위험 키워드 감지
2. SentimentAnalyzer: 감정 강도 및 누적 분석
3. PatternRecognizer: 대화 패턴 및 행동 패턴 분석
4. LLMCrisisEvaluator: 종합적 위기 평가
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum

from .utils import load_json

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """위험 수준 열거형"""
    CRITICAL = "CRITICAL"  # 즉각적 개입 필요
    HIGH = "HIGH"          # 긴급 전문가 상담 필요
    MEDIUM = "MEDIUM"      # 전문가 상담 권장
    LOW = "LOW"            # 모니터링 필요
    NONE = "NONE"          # 위험 없음


@dataclass
class CrisisLog:
    """위기 상황 로그"""
    timestamp: datetime
    user_id: Optional[str]
    severity: RiskLevel
    text: str
    detected_keywords: List[str]
    sentiment_score: float
    pattern_flags: List[str]
    intervention_message: str

    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "severity": self.severity.value,
            "text": self.text[:100],  # 개인정보 보호를 위해 축약
            "detected_keywords": self.detected_keywords,
            "sentiment_score": self.sentiment_score,
            "pattern_flags": self.pattern_flags,
            "intervention_message": self.intervention_message[:200]
        }


class KeywordDetector:
    """
    Layer 1: 즉각적 위험 키워드 감지기

    직접적이고 명확한 위험 키워드를 실시간으로 감지합니다.
    한국어 특유의 직접/간접 표현을 모두 포괄합니다.
    """

    def __init__(self):
        """초기화"""
        self.keywords_by_level = self._load_keywords()

    def _load_keywords(self) -> Dict[RiskLevel, Dict[str, List[str]]]:
        """
        위험도별 키워드 로드

        Returns:
            Dict: 위험도별 카테고리화된 키워드
        """
        return {
            RiskLevel.CRITICAL: {
                "direct_suicide": [
                    "죽고 싶다", "죽고싶다", "죽고 싶어", "죽을래",
                    "자살하고 싶", "자살할게", "자살할 거야",
                    "목숨을 끊", "생을 마감", "세상을 떠나",
                    "끝내버리고 싶", "오늘 죽을", "지금 죽을"
                ],
                "suicide_plan": [
                    "어떻게 죽을까", "죽는 방법", "자살 방법",
                    "유서", "유언", "마지막", "작별",
                    "준비했어", "계획을 세웠", "결심했"
                ],
                "immediate_danger": [
                    "지금 당장", "오늘 중에", "이따가",
                    "약을 먹었", "올라갔어", "뛰어내릴",
                    "손목을 긋", "목을 매"
                ]
            },
            RiskLevel.HIGH: {
                "indirect_suicide": [
                    "사라지고 싶", "없어지고 싶", "지워지고 싶",
                    "더 이상 살고 싶지 않", "살 이유가 없",
                    "존재할 필요가 없", "의미 없는 삶"
                ],
                "self_harm": [
                    "자해", "스스로 해치", "몸에 상처",
                    "칼로 긋", "베고 싶", "아프게 하고 싶",
                    "피가 나", "손목", "팔뚝"
                ],
                "hopelessness": [
                    "희망이 없", "절망적", "끝이 없",
                    "나아질 것 같지 않", "소용없",
                    "아무것도 바뀌지 않", "포기했"
                ]
            },
            RiskLevel.MEDIUM: {
                "burden_thoughts": [
                    "폐를 끼치고 싶지 않", "짐이 되는 것 같",
                    "없는 게 나을", "방해만 되",
                    "가족에게 미안", "부담 주고 싶지 않"
                ],
                "isolation": [
                    "아무도 없", "혼자야", "고립", "외로",
                    "연락할 사람이 없", "이해해주는 사람이 없"
                ],
                "severe_pain": [
                    "견딜 수 없", "너무 아파", "고통스러",
                    "괴로워", "힘들어 죽겠", "미치겠"
                ]
            },
            RiskLevel.LOW: {
                "general_distress": [
                    "힘들다", "지친다", "우울하다",
                    "불안하다", "걱정된다"
                ]
            }
        }

    def detect(self, text: str) -> Dict[str, any]:
        """
        키워드 기반 위험 감지

        Args:
            text: 분석할 텍스트

        Returns:
            Dict: 감지 결과
                - risk_level: 위험 수준
                - detected_keywords: 감지된 키워드
                - categories: 위험 카테고리
                - confidence: 신뢰도
        """
        text = text.lower().strip()

        detected = {
            "risk_level": RiskLevel.NONE,
            "detected_keywords": [],
            "categories": [],
            "confidence": 0.0,
            "details": {}
        }

        highest_risk = RiskLevel.NONE

        # 위험도별로 검사 (CRITICAL부터)
        for risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH,
                          RiskLevel.MEDIUM, RiskLevel.LOW]:

            if risk_level not in self.keywords_by_level:
                continue

            categories = self.keywords_by_level[risk_level]

            for category, keywords in categories.items():
                matched = []

                for keyword in keywords:
                    if keyword in text:
                        matched.append(keyword)

                if matched:
                    detected["detected_keywords"].extend(matched)
                    detected["categories"].append(category)

                    # 가장 높은 위험도 업데이트
                    if self._compare_risk(risk_level, highest_risk) > 0:
                        highest_risk = risk_level

                    detected["details"][category] = {
                        "risk_level": risk_level.value,
                        "keywords": matched,
                        "count": len(matched)
                    }

        detected["risk_level"] = highest_risk

        # 신뢰도 계산
        detected["confidence"] = self._calculate_confidence(
            highest_risk,
            len(detected["detected_keywords"])
        )

        return detected

    def _compare_risk(self, level1: RiskLevel, level2: RiskLevel) -> int:
        """
        위험도 비교

        Returns:
            int: level1이 더 높으면 1, 같으면 0, 낮으면 -1
        """
        order = [RiskLevel.NONE, RiskLevel.LOW, RiskLevel.MEDIUM,
                RiskLevel.HIGH, RiskLevel.CRITICAL]

        idx1 = order.index(level1)
        idx2 = order.index(level2)

        if idx1 > idx2:
            return 1
        elif idx1 == idx2:
            return 0
        else:
            return -1

    def _calculate_confidence(self, risk_level: RiskLevel, keyword_count: int) -> float:
        """
        신뢰도 계산

        Args:
            risk_level: 위험 수준
            keyword_count: 감지된 키워드 수

        Returns:
            float: 신뢰도 (0-1)
        """
        if risk_level == RiskLevel.NONE:
            return 0.0

        # 기본 신뢰도
        base_confidence = {
            RiskLevel.CRITICAL: 0.95,
            RiskLevel.HIGH: 0.85,
            RiskLevel.MEDIUM: 0.70,
            RiskLevel.LOW: 0.50
        }.get(risk_level, 0.0)

        # 키워드 수에 따른 보정
        keyword_boost = min(keyword_count * 0.05, 0.15)

        return min(base_confidence + keyword_boost, 1.0)


class SentimentAnalyzer:
    """
    Layer 2: 감정 강도 분석기

    감정의 강도를 0-10 척도로 측정하고,
    부정적 감정의 누적을 추적합니다.
    """

    def __init__(self, history_size: int = 10):
        """
        초기화

        Args:
            history_size: 추적할 감정 히스토리 크기
        """
        self.history = deque(maxlen=history_size)
        self.cumulative_negativity = 0.0

    def analyze(self, text: str, emotion_data: Optional[Dict] = None) -> Dict[str, any]:
        """
        감정 강도 분석

        Args:
            text: 분석할 텍스트
            emotion_data: 외부 감정 분석 결과 (옵션)

        Returns:
            Dict: 분석 결과
                - intensity: 감정 강도 (0-10)
                - negativity: 부정성 점수 (0-10)
                - cumulative_negativity: 누적 부정성
                - rapid_change: 급격한 변화 여부
        """
        # 감정 강도 계산
        intensity = self._calculate_intensity(text, emotion_data)

        # 부정성 점수
        negativity = self._calculate_negativity(text, emotion_data)

        # 히스토리에 추가
        self.history.append({
            "timestamp": datetime.now(),
            "intensity": intensity,
            "negativity": negativity
        })

        # 누적 부정성 업데이트
        self._update_cumulative_negativity(negativity)

        # 급격한 변화 감지
        rapid_change = self._detect_rapid_change()

        return {
            "intensity": round(intensity, 1),
            "negativity": round(negativity, 1),
            "cumulative_negativity": round(self.cumulative_negativity, 1),
            "rapid_change": rapid_change,
            "history_length": len(self.history),
            "trend": self._calculate_trend()
        }

    def _calculate_intensity(self, text: str, emotion_data: Optional[Dict]) -> float:
        """
        감정 강도 계산 (0-10)

        Args:
            text: 입력 텍스트
            emotion_data: 감정 분석 데이터

        Returns:
            float: 강도 (0-10)
        """
        intensity = 5.0  # 기본값

        # 외부 감정 데이터가 있으면 사용
        if emotion_data and "intensity" in emotion_data:
            intensity = emotion_data["intensity"] * 10

        # 텍스트 기반 강도 증폭 요소

        # 느낌표
        exclamation_count = text.count("!")
        intensity += min(exclamation_count * 0.5, 2.0)

        # 대문자 (한국어에서는 덜 중요)
        # upper_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        # intensity += upper_ratio * 2

        # 반복 표현
        if re.search(r'너무|정말|진짜|완전|엄청|심하게', text):
            intensity += 1.0

        if re.search(r'너무너무|정말정말|진짜진짜', text):
            intensity += 2.0

        # 연속 문장부호
        if re.search(r'\.\.\.+', text) or re.search(r'\?+|\!+', text):
            intensity += 0.5

        # 최대 10으로 제한
        return min(intensity, 10.0)

    def _calculate_negativity(self, text: str, emotion_data: Optional[Dict]) -> float:
        """
        부정성 점수 계산 (0-10)

        Args:
            text: 입력 텍스트
            emotion_data: 감정 분석 데이터

        Returns:
            float: 부정성 (0-10, 높을수록 부정적)
        """
        negativity = 0.0

        # 부정적 감정 키워드
        negative_keywords = {
            "극심한": 3.0,
            "견딜 수 없": 3.0,
            "최악": 2.5,
            "끔찍": 2.5,
            "절망": 2.5,
            "고통": 2.0,
            "괴로": 2.0,
            "힘들": 1.5,
            "우울": 1.5,
            "불안": 1.5,
            "슬프": 1.0,
            "걱정": 1.0
        }

        for keyword, score in negative_keywords.items():
            if keyword in text:
                negativity += score

        # 외부 감정 데이터 반영
        if emotion_data:
            primary = emotion_data.get("primary_emotion", "")

            negative_emotions = {
                "우울": 2.5,
                "절망": 3.0,
                "불안": 2.0,
                "분노": 1.5,
                "슬픔": 1.5,
                "스트레스": 1.5
            }

            if primary in negative_emotions:
                negativity += negative_emotions[primary]

                # 강도 반영
                intensity_mult = emotion_data.get("intensity", 0.5)
                negativity *= (0.5 + intensity_mult)

        return min(negativity, 10.0)

    def _update_cumulative_negativity(self, current_negativity: float):
        """
        누적 부정성 업데이트

        Args:
            current_negativity: 현재 부정성 점수
        """
        # 지수 가중 이동 평균
        alpha = 0.3  # 최근 값에 30% 가중치
        self.cumulative_negativity = (
            alpha * current_negativity +
            (1 - alpha) * self.cumulative_negativity
        )

    def _detect_rapid_change(self) -> bool:
        """
        급격한 감정 변화 감지

        Returns:
            bool: 급격한 변화 여부
        """
        if len(self.history) < 2:
            return False

        recent = list(self.history)[-2:]

        # 부정성의 급격한 증가
        negativity_change = recent[1]["negativity"] - recent[0]["negativity"]

        if negativity_change > 4.0:  # 4점 이상 급증
            return True

        # 강도의 급격한 증가
        intensity_change = recent[1]["intensity"] - recent[0]["intensity"]

        if intensity_change > 5.0:  # 5점 이상 급증
            return True

        return False

    def _calculate_trend(self) -> str:
        """
        감정 트렌드 계산

        Returns:
            str: "worsening", "stable", "improving"
        """
        if len(self.history) < 3:
            return "stable"

        recent = list(self.history)[-3:]
        negativity_scores = [h["negativity"] for h in recent]

        # 추세 계산
        if negativity_scores[2] > negativity_scores[1] > negativity_scores[0]:
            if negativity_scores[2] - negativity_scores[0] > 2.0:
                return "worsening"
        elif negativity_scores[2] < negativity_scores[1] < negativity_scores[0]:
            if negativity_scores[0] - negativity_scores[2] > 2.0:
                return "improving"

        return "stable"


class PatternRecognizer:
    """
    Layer 3: 대화 패턴 인식기

    위험 신호 패턴을 인식하고 시간대별 분석을 수행합니다.
    """

    def __init__(self):
        """초기화"""
        self.conversation_patterns = []

    def analyze_patterns(
        self,
        text: str,
        conversation_history: Optional[List[Dict]] = None,
        current_time: Optional[datetime] = None
    ) -> Dict[str, any]:
        """
        패턴 분석

        Args:
            text: 현재 텍스트
            conversation_history: 대화 이력
            current_time: 현재 시간

        Returns:
            Dict: 패턴 분석 결과
        """
        current_time = current_time or datetime.now()

        patterns = {
            "isolation_pattern": self._detect_isolation(text, conversation_history),
            "hopelessness_pattern": self._detect_hopelessness(text, conversation_history),
            "withdrawal_pattern": self._detect_withdrawal(conversation_history),
            "time_risk": self._analyze_time_risk(current_time),
            "repetitive_crisis_talk": self._detect_repetitive_crisis(conversation_history),
            "risk_flags": []
        }

        # 위험 플래그 수집
        if patterns["isolation_pattern"]["detected"]:
            patterns["risk_flags"].append("isolation")

        if patterns["hopelessness_pattern"]["detected"]:
            patterns["risk_flags"].append("hopelessness")

        if patterns["withdrawal_pattern"]["detected"]:
            patterns["risk_flags"].append("withdrawal")

        if patterns["time_risk"]["is_high_risk_time"]:
            patterns["risk_flags"].append("high_risk_time")

        if patterns["repetitive_crisis_talk"]["detected"]:
            patterns["risk_flags"].append("repetitive_crisis")

        # 전체 위험도 평가
        patterns["overall_risk_score"] = self._calculate_pattern_risk(patterns)

        return patterns

    def _detect_isolation(
        self,
        text: str,
        conversation_history: Optional[List[Dict]]
    ) -> Dict[str, any]:
        """
        고립 패턴 감지

        Args:
            text: 현재 텍스트
            conversation_history: 대화 이력

        Returns:
            Dict: 고립 패턴 정보
        """
        isolation_keywords = [
            "아무도", "혼자", "외로", "고립", "떨어져",
            "연락할 사람", "말할 사람", "이해해주는 사람",
            "나만", "혼자뿐", "버려"
        ]

        detected = False
        matched = []

        for keyword in isolation_keywords:
            if keyword in text:
                detected = True
                matched.append(keyword)

        # 대화 이력에서 반복 확인
        frequency = 0
        if conversation_history:
            for turn in conversation_history[-5:]:  # 최근 5턴
                content = turn.get("content", "")
                for keyword in isolation_keywords:
                    if keyword in content:
                        frequency += 1

        return {
            "detected": detected,
            "keywords": matched,
            "frequency": frequency,
            "severity": "high" if frequency >= 3 else ("medium" if detected else "low")
        }

    def _detect_hopelessness(
        self,
        text: str,
        conversation_history: Optional[List[Dict]]
    ) -> Dict[str, any]:
        """
        절망감 패턴 감지

        Args:
            text: 현재 텍스트
            conversation_history: 대화 이력

        Returns:
            Dict: 절망감 패턴 정보
        """
        hopelessness_keywords = [
            "희망", "소용없", "의미없", "아무것도",
            "바뀌지 않", "나아지지 않", "끝이 없",
            "포기", "그만", "더 이상"
        ]

        # 부정 표현과 함께 사용되는지 확인
        detected = False
        matched = []

        for keyword in hopelessness_keywords:
            # 부정 패턴과 함께 나오는지
            pattern = f"(없|않|못).*{keyword}|{keyword}.*(없|않|못)"
            if re.search(pattern, text) or keyword in text:
                detected = True
                matched.append(keyword)

        return {
            "detected": detected,
            "keywords": matched,
            "severity": "high" if len(matched) >= 2 else ("medium" if detected else "low")
        }

    def _detect_withdrawal(
        self,
        conversation_history: Optional[List[Dict]]
    ) -> Dict[str, any]:
        """
        철수/회피 패턴 감지

        Args:
            conversation_history: 대화 이력

        Returns:
            Dict: 철수 패턴 정보
        """
        if not conversation_history or len(conversation_history) < 3:
            return {"detected": False}

        # 응답 길이 감소 패턴
        recent_lengths = [
            len(turn.get("content", ""))
            for turn in conversation_history[-3:]
            if turn.get("role") == "user"
        ]

        if len(recent_lengths) >= 3:
            # 계속 짧아지는 패턴
            if recent_lengths[0] > recent_lengths[1] > recent_lengths[2]:
                if recent_lengths[2] < 20:  # 매우 짧은 응답
                    return {
                        "detected": True,
                        "pattern": "decreasing_engagement",
                        "severity": "medium"
                    }

        return {"detected": False}

    def _analyze_time_risk(self, current_time: datetime) -> Dict[str, any]:
        """
        시간대별 위험도 분석

        Args:
            current_time: 현재 시간

        Returns:
            Dict: 시간 위험도 정보
        """
        hour = current_time.hour

        # 새벽 시간대 (00:00 - 05:00) 고위험
        is_high_risk = 0 <= hour < 5

        # 늦은 밤 (22:00 - 24:00) 중위험
        is_medium_risk = 22 <= hour < 24

        risk_level = "high" if is_high_risk else ("medium" if is_medium_risk else "low")

        return {
            "current_hour": hour,
            "is_high_risk_time": is_high_risk,
            "risk_level": risk_level,
            "message": "새벽 시간대 대화는 위기 가능성이 높습니다" if is_high_risk else None
        }

    def _detect_repetitive_crisis(
        self,
        conversation_history: Optional[List[Dict]]
    ) -> Dict[str, any]:
        """
        반복적인 위기 언급 감지

        Args:
            conversation_history: 대화 이력

        Returns:
            Dict: 반복 패턴 정보
        """
        if not conversation_history:
            return {"detected": False}

        crisis_keywords = ["죽", "자살", "끝내", "사라지", "없어지"]

        crisis_mentions = 0
        for turn in conversation_history[-10:]:  # 최근 10턴
            if turn.get("role") == "user":
                content = turn.get("content", "")
                for keyword in crisis_keywords:
                    if keyword in content:
                        crisis_mentions += 1
                        break

        detected = crisis_mentions >= 2

        return {
            "detected": detected,
            "mention_count": crisis_mentions,
            "severity": "high" if crisis_mentions >= 3 else ("medium" if detected else "low")
        }

    def _calculate_pattern_risk(self, patterns: Dict) -> float:
        """
        패턴 기반 전체 위험도 계산

        Args:
            patterns: 패턴 분석 결과

        Returns:
            float: 위험도 점수 (0-10)
        """
        risk_score = 0.0

        # 각 패턴에 가중치 부여
        if patterns["isolation_pattern"]["detected"]:
            severity = patterns["isolation_pattern"]["severity"]
            risk_score += {"high": 3.0, "medium": 2.0, "low": 1.0}.get(severity, 0)

        if patterns["hopelessness_pattern"]["detected"]:
            severity = patterns["hopelessness_pattern"]["severity"]
            risk_score += {"high": 3.0, "medium": 2.0, "low": 1.0}.get(severity, 0)

        if patterns["withdrawal_pattern"]["detected"]:
            risk_score += 2.0

        if patterns["time_risk"]["is_high_risk_time"]:
            risk_score += 1.5

        if patterns["repetitive_crisis_talk"]["detected"]:
            severity = patterns["repetitive_crisis_talk"]["severity"]
            risk_score += {"high": 3.0, "medium": 2.0, "low": 1.0}.get(severity, 0)

        return min(risk_score, 10.0)


class LLMCrisisEvaluator:
    """
    Layer 4: 종합적 위기 평가기

    모든 레이어의 정보를 통합하여 최종 위기 수준을 판단합니다.
    """

    def __init__(self):
        """초기화"""
        pass

    def evaluate(
        self,
        text: str,
        keyword_result: Dict,
        sentiment_result: Dict,
        pattern_result: Dict,
        context: Optional[Dict] = None
    ) -> Dict[str, any]:
        """
        종합적 위기 평가

        Args:
            text: 입력 텍스트
            keyword_result: 키워드 감지 결과
            sentiment_result: 감정 분석 결과
            pattern_result: 패턴 분석 결과
            context: 추가 컨텍스트 정보

        Returns:
            Dict: 종합 평가 결과
        """
        # 1. 각 레이어의 위험도 점수화
        keyword_score = self._score_keyword_result(keyword_result)
        sentiment_score = self._score_sentiment_result(sentiment_result)
        pattern_score = pattern_result.get("overall_risk_score", 0.0)

        # 2. 가중 평균 계산
        # 키워드가 가장 중요 (50%), 감정 (30%), 패턴 (20%)
        weighted_score = (
            keyword_score * 0.5 +
            sentiment_score * 0.3 +
            pattern_score * 0.2
        )

        # 3. 최종 위험 수준 결정
        final_risk_level = self._determine_risk_level(
            weighted_score,
            keyword_result,
            sentiment_result,
            pattern_result
        )

        # 4. 신뢰도 계산
        confidence = self._calculate_confidence(
            keyword_result,
            sentiment_result,
            pattern_result
        )

        # 5. 개입 메시지 생성
        intervention = self._generate_intervention(final_risk_level, keyword_result)

        return {
            "risk_level": final_risk_level,
            "weighted_score": round(weighted_score, 2),
            "layer_scores": {
                "keyword": round(keyword_score, 2),
                "sentiment": round(sentiment_score, 2),
                "pattern": round(pattern_score, 2)
            },
            "confidence": round(confidence, 2),
            "requires_intervention": final_risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH],
            "intervention_message": intervention["message"],
            "recommended_resources": intervention["resources"],
            "action": intervention["action"],
            "details": {
                "keyword_details": keyword_result,
                "sentiment_details": sentiment_result,
                "pattern_details": pattern_result
            }
        }

    def _score_keyword_result(self, keyword_result: Dict) -> float:
        """
        키워드 결과를 0-10 점수로 변환

        Args:
            keyword_result: 키워드 감지 결과

        Returns:
            float: 점수 (0-10)
        """
        risk_level = keyword_result.get("risk_level", RiskLevel.NONE)

        score_map = {
            RiskLevel.CRITICAL: 10.0,
            RiskLevel.HIGH: 7.5,
            RiskLevel.MEDIUM: 5.0,
            RiskLevel.LOW: 2.5,
            RiskLevel.NONE: 0.0
        }

        base_score = score_map.get(risk_level, 0.0)

        # 키워드 수에 따른 보정
        keyword_count = len(keyword_result.get("detected_keywords", []))
        bonus = min(keyword_count * 0.3, 2.0)

        return min(base_score + bonus, 10.0)

    def _score_sentiment_result(self, sentiment_result: Dict) -> float:
        """
        감정 결과를 0-10 점수로 변환

        Args:
            sentiment_result: 감정 분석 결과

        Returns:
            float: 점수 (0-10)
        """
        negativity = sentiment_result.get("negativity", 0.0)
        cumulative = sentiment_result.get("cumulative_negativity", 0.0)
        rapid_change = sentiment_result.get("rapid_change", False)

        # 기본 점수는 부정성과 누적 부정성의 평균
        base_score = (negativity + cumulative) / 2

        # 급격한 변화가 있으면 가중
        if rapid_change:
            base_score *= 1.3

        return min(base_score, 10.0)

    def _determine_risk_level(
        self,
        weighted_score: float,
        keyword_result: Dict,
        sentiment_result: Dict,
        pattern_result: Dict
    ) -> RiskLevel:
        """
        최종 위험 수준 결정

        Args:
            weighted_score: 가중 점수
            keyword_result: 키워드 결과
            sentiment_result: 감정 결과
            pattern_result: 패턴 결과

        Returns:
            RiskLevel: 최종 위험 수준
        """
        # 키워드 기반 우선 판단
        keyword_risk = keyword_result.get("risk_level", RiskLevel.NONE)

        # CRITICAL 키워드가 감지되면 무조건 CRITICAL
        if keyword_risk == RiskLevel.CRITICAL:
            return RiskLevel.CRITICAL

        # 가중 점수 기반 판단
        if weighted_score >= 8.5:
            return RiskLevel.CRITICAL
        elif weighted_score >= 6.5:
            return RiskLevel.HIGH
        elif weighted_score >= 4.0:
            return RiskLevel.MEDIUM
        elif weighted_score >= 2.0:
            return RiskLevel.LOW
        else:
            return RiskLevel.NONE

    def _calculate_confidence(
        self,
        keyword_result: Dict,
        sentiment_result: Dict,
        pattern_result: Dict
    ) -> float:
        """
        신뢰도 계산

        Args:
            keyword_result: 키워드 결과
            sentiment_result: 감정 결과
            pattern_result: 패턴 결과

        Returns:
            float: 신뢰도 (0-1)
        """
        confidences = []

        # 키워드 신뢰도
        if "confidence" in keyword_result:
            confidences.append(keyword_result["confidence"])

        # 감정 신뢰도 (히스토리 길이 기반)
        history_length = sentiment_result.get("history_length", 0)
        sentiment_confidence = min(history_length / 10.0, 1.0)
        confidences.append(sentiment_confidence)

        # 패턴 신뢰도 (위험 플래그 수 기반)
        risk_flags = len(pattern_result.get("risk_flags", []))
        pattern_confidence = min(risk_flags / 3.0, 1.0)
        confidences.append(pattern_confidence)

        # 평균
        if confidences:
            return sum(confidences) / len(confidences)

        return 0.5

    def _generate_intervention(
        self,
        risk_level: RiskLevel,
        keyword_result: Dict
    ) -> Dict[str, any]:
        """
        개입 메시지 생성

        Args:
            risk_level: 위험 수준
            keyword_result: 키워드 결과

        Returns:
            Dict: 개입 정보
        """
        CRISIS_RESPONSES = {
            RiskLevel.CRITICAL: {
                "message": """⚠️ 긴급 상황입니다.

당신의 생명은 매우 소중합니다. 지금 느끼시는 고통이 얼마나 큰지 이해합니다.

하지만 혼자 감당하지 마시고, 지금 즉시 전문가의 도움을 받으시는 것이 중요합니다.

🆘 자살예방상담전화: 1393 (24시간 무료)
🆘 정신건강위기상담전화: 1577-0199 (24시간)
🆘 카카오톡 상담: "카카오톡 플러스친구 상담톡109" 검색
🆘 응급상황: 119 또는 가까운 응급실

지금 이 순간이 힘들더라도, 도움을 받으시면 상황은 나아질 수 있습니다.""",
                "resources": [
                    {"name": "자살예방상담전화", "number": "1393", "available": "24시간"},
                    {"name": "정신건강위기상담전화", "number": "1577-0199", "available": "24시간"},
                    {"name": "응급상황", "number": "119", "available": "24시간"},
                    {"name": "카카오톡 상담", "id": "상담톡109", "available": "온라인"}
                ],
                "action": "IMMEDIATE_INTERVENTION"
            },
            RiskLevel.HIGH: {
                "message": """지금 정말 힘든 상황이시군요. 이런 고통을 느끼시는 것이 얼마나 어려운지 이해합니다.

혼자서 감당하기 어려운 상황입니다. 전문가의 도움을 받으시는 것을 강력히 권유드립니다.

📞 정신건강위기상담전화: 1577-0199 (24시간)
📞 자살예방상담전화: 1393 (24시간)
📞 청소년전화: 1388 (24시간)
🏥 가까운 정신건강복지센터 방문

당신은 혼자가 아닙니다. 도움을 요청하는 것은 용기있는 행동입니다.""",
                "resources": [
                    {"name": "정신건강위기상담전화", "number": "1577-0199", "available": "24시간"},
                    {"name": "자살예방상담전화", "number": "1393", "available": "24시간"},
                    {"name": "청소년전화", "number": "1388", "available": "24시간"}
                ],
                "action": "URGENT_PROFESSIONAL_REFERRAL"
            },
            RiskLevel.MEDIUM: {
                "message": """많이 힘드신 것 같아요. 이런 어려움을 겪고 계시는 것이 느껴집니다.

전문가와 상담하시면 더 큰 도움을 받으실 수 있습니다.

💬 정신건강복지센터: 지역 보건소 또는 1577-0199
💬 온라인 상담: 한국상담심리학회, 한국임상심리학회
💬 대학 상담센터 (학생의 경우)

언제든 전문적인 도움을 받으시는 것을 고려해보세요.""",
                "resources": [
                    {"name": "정신건강복지센터", "number": "1577-0199", "available": "평일 9-18시"},
                    {"name": "온라인 상담", "website": "www.kacpt.or.kr", "available": "온라인"}
                ],
                "action": "PROFESSIONAL_RECOMMENDATION"
            },
            RiskLevel.LOW: {
                "message": """힘든 시간을 보내고 계시는군요. 함께 이야기 나눠봐요.

필요하시다면 언제든 전문가의 도움을 받으실 수 있습니다.""",
                "resources": [],
                "action": "SUPPORTIVE_CONVERSATION"
            },
            RiskLevel.NONE: {
                "message": "",
                "resources": [],
                "action": "CONTINUE_CONVERSATION"
            }
        }

        return CRISIS_RESPONSES.get(risk_level, CRISIS_RESPONSES[RiskLevel.NONE])


class SafetySystem:
    """
    통합 안전 시스템

    4개 레이어를 통합하여 종합적인 위기 감지 및 대응을 제공합니다.
    """

    def __init__(self, user_id: Optional[str] = None):
        """
        초기화

        Args:
            user_id: 사용자 ID (로깅용)
        """
        self.user_id = user_id

        # 4개 레이어 초기화
        self.keyword_detector = KeywordDetector()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.pattern_recognizer = PatternRecognizer()
        self.crisis_evaluator = LLMCrisisEvaluator()

        # 위기 로그
        self.crisis_logs: List[CrisisLog] = []

        logger.info("SafetySystem initialized")

    def check_safety(
        self,
        text: str,
        emotion_data: Optional[Dict] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, any]:
        """
        종합 안전 체크

        Args:
            text: 분석할 텍스트
            emotion_data: 감정 분석 데이터
            conversation_history: 대화 이력

        Returns:
            Dict: 종합 안전 체크 결과
        """
        logger.info(f"Safety check for text: {text[:50]}...")

        # Layer 1: 키워드 감지
        keyword_result = self.keyword_detector.detect(text)

        # Layer 2: 감정 분석
        sentiment_result = self.sentiment_analyzer.analyze(text, emotion_data)

        # Layer 3: 패턴 인식
        pattern_result = self.pattern_recognizer.analyze_patterns(
            text,
            conversation_history
        )

        # Layer 4: 종합 평가
        evaluation = self.crisis_evaluator.evaluate(
            text,
            keyword_result,
            sentiment_result,
            pattern_result
        )

        # 위기 로깅
        if evaluation["requires_intervention"]:
            self._log_crisis(text, evaluation, keyword_result, sentiment_result, pattern_result)

        return evaluation

    def phq9_item9_screening(self, text: str) -> Dict[str, any]:
        """
        PHQ-9 Item 9 기반 자살 사고 스크리닝

        PHQ-9 Item 9: "자신을 해치거나 차라리 죽는 것이 낫겠다는 생각"

        Args:
            text: 분석할 텍스트

        Returns:
            Dict: 스크리닝 결과
                - score: 0-3 (0=전혀, 1=며칠, 2=7일 이상, 3=거의 매일)
                - risk_present: 위험 존재 여부
                - recommendation: 권장 사항
        """
        # 빈도 관련 키워드
        frequency_patterns = {
            3: ["매일", "항상", "계속", "끊임없이", "하루종일"],
            2: ["자주", "많이", "일주일", "7일"],
            1: ["가끔", "때때로", "며칠", "종종"],
            0: ["없", "안", "전혀"]
        }

        # 자살 사고 관련 키워드
        suicidal_ideation = [
            "죽고 싶", "자살", "자해", "사라지고 싶",
            "끝내고 싶", "차라리 죽는 게"
        ]

        # 자살 사고 존재 확인
        has_ideation = any(keyword in text for keyword in suicidal_ideation)

        if not has_ideation:
            return {
                "score": 0,
                "risk_present": False,
                "frequency": "없음",
                "recommendation": "모니터링 계속"
            }

        # 빈도 평가
        detected_score = 1  # 기본값: 며칠

        for score, patterns in sorted(frequency_patterns.items(), reverse=True):
            if any(pattern in text for pattern in patterns):
                detected_score = score
                break

        frequency_labels = {
            0: "전혀 없음",
            1: "며칠 동안",
            2: "7일 이상",
            3: "거의 매일"
        }

        recommendations = {
            0: "모니터링 계속",
            1: "주의 깊은 모니터링 필요",
            2: "전문가 상담 강력 권장",
            3: "즉각적인 전문가 개입 필요"
        }

        return {
            "score": detected_score,
            "risk_present": True,
            "frequency": frequency_labels[detected_score],
            "recommendation": recommendations[detected_score],
            "severity": "high" if detected_score >= 2 else "medium"
        }

    def _log_crisis(
        self,
        text: str,
        evaluation: Dict,
        keyword_result: Dict,
        sentiment_result: Dict,
        pattern_result: Dict
    ):
        """
        위기 상황 로깅

        Args:
            text: 입력 텍스트
            evaluation: 평가 결과
            keyword_result: 키워드 결과
            sentiment_result: 감정 결과
            pattern_result: 패턴 결과
        """
        crisis_log = CrisisLog(
            timestamp=datetime.now(),
            user_id=self.user_id,
            severity=evaluation["risk_level"],
            text=text,
            detected_keywords=keyword_result.get("detected_keywords", []),
            sentiment_score=sentiment_result.get("negativity", 0.0),
            pattern_flags=pattern_result.get("risk_flags", []),
            intervention_message=evaluation["intervention_message"]
        )

        self.crisis_logs.append(crisis_log)

        logger.warning(
            f"Crisis logged: {evaluation['risk_level'].value} - "
            f"User: {self.user_id} - Time: {crisis_log.timestamp}"
        )

    def get_crisis_history(self, limit: int = 10) -> List[Dict]:
        """
        위기 이력 조회

        Args:
            limit: 조회할 최대 개수

        Returns:
            List[Dict]: 위기 로그 리스트
        """
        recent_logs = self.crisis_logs[-limit:] if self.crisis_logs else []
        return [log.to_dict() for log in recent_logs]

    def get_risk_trend(self) -> Dict[str, any]:
        """
        위험도 추세 분석

        Returns:
            Dict: 추세 정보
        """
        if len(self.crisis_logs) < 2:
            return {"trend": "insufficient_data"}

        recent = self.crisis_logs[-5:]

        severity_scores = []
        for log in recent:
            score_map = {
                RiskLevel.CRITICAL: 4,
                RiskLevel.HIGH: 3,
                RiskLevel.MEDIUM: 2,
                RiskLevel.LOW: 1,
                RiskLevel.NONE: 0
            }
            severity_scores.append(score_map.get(log.severity, 0))

        # 추세 계산
        if len(severity_scores) >= 3:
            if severity_scores[-1] > severity_scores[-2] > severity_scores[-3]:
                trend = "escalating"
            elif severity_scores[-1] < severity_scores[-2] < severity_scores[-3]:
                trend = "improving"
            else:
                trend = "stable"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "recent_severity_scores": severity_scores,
            "average_severity": sum(severity_scores) / len(severity_scores) if severity_scores else 0,
            "highest_severity": max(severity_scores) if severity_scores else 0
        }


# 하위 호환성을 위한 별칭
CrisisDetectionSystem = SafetySystem


if __name__ == "__main__":
    # 테스트 코드
    print("=== 다층 안전 시스템 테스트 ===\n")

    safety_system = SafetySystem(user_id="test_user")

    test_cases = [
        "죽고 싶어요. 오늘 중에 끝내버릴 거예요.",
        "너무 외롭고 고립된 것 같아요. 아무도 없어요.",
        "회사가 힘들어요. 스트레스 받아요.",
        "요즘 계속 죽고 싶다는 생각이 들어요."
    ]

    for i, text in enumerate(test_cases, 1):
        print(f"테스트 {i}: {text}")
        print("-" * 70)

        result = safety_system.check_safety(text)

        print(f"위험 수준: {result['risk_level'].value}")
        print(f"가중 점수: {result['weighted_score']}/10")
        print(f"신뢰도: {result['confidence']:.2f}")
        print(f"개입 필요: {result['requires_intervention']}")

        if result['requires_intervention']:
            print(f"\n개입 메시지:")
            print(result['intervention_message'])

        # PHQ-9 스크리닝
        phq9 = safety_system.phq9_item9_screening(text)
        if phq9['risk_present']:
            print(f"\nPHQ-9 Item 9 점수: {phq9['score']}/3")
            print(f"빈도: {phq9['frequency']}")
            print(f"권장사항: {phq9['recommendation']}")

        print("\n" + "=" * 70 + "\n")
