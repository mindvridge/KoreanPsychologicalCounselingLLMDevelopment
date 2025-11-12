"""
위기 감지 및 안전 시스템
Crisis Detection and Safety System

자살, 자해 등 위기 상황을 감지하고 적절히 대응합니다.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path

from .utils import load_json

logger = logging.getLogger(__name__)


class CrisisDetectionSystem:
    """
    위기 상황 감지 시스템

    자살, 자해, 폭력 등의 위기 상황을 실시간으로 감지하고
    적절한 개입 및 전문기관 연계를 제공합니다.
    """

    def __init__(self, keywords_file: Optional[str] = None):
        """
        초기화

        Args:
            keywords_file: 위기 키워드 파일 경로
        """
        self.keywords_file = keywords_file or "./data/crisis_keywords.json"
        self.crisis_data = self._load_crisis_keywords()
        self.detection_history = []

    def _load_crisis_keywords(self) -> Dict:
        """
        위기 키워드 데이터 로드

        Returns:
            Dict: 위기 키워드 및 설정
        """
        try:
            data = load_json(self.keywords_file)
            if not data:
                logger.warning("Crisis keywords file not found, using default")
                data = self._get_default_crisis_keywords()
            return data
        except Exception as e:
            logger.error(f"Error loading crisis keywords: {e}")
            return self._get_default_crisis_keywords()

    def _get_default_crisis_keywords(self) -> Dict:
        """
        기본 위기 키워드 반환

        Returns:
            Dict: 기본 위기 키워드
        """
        return {
            "crisis_categories": {
                "suicide": {
                    "severity": "critical",
                    "keywords": [
                        "죽고 싶", "자살", "목숨", "자해", "죽어버리",
                        "사라지고 싶", "끝내고 싶", "살 가치", "살아갈 이유",
                        "더 이상 못 살", "죽는 게 나을"
                    ],
                    "emergency_response": True,
                    "hotline": "1393"
                },
                "self_harm": {
                    "severity": "high",
                    "keywords": [
                        "자해", "칼로", "긋", "베", "상처", "피",
                        "팔뚝", "손목", "자상", "스스로 해치"
                    ],
                    "emergency_response": True,
                    "hotline": "1577-0199"
                }
            },
            "context_modifiers": {
                "negation": ["아니", "않", "없", "절대", "안 ", "못 "],
                "past_tense": ["했었", "였었", "던", "이었"],
                "hypothetical": ["만약", "가정", "만일", "~면"]
            }
        }

    def detect_crisis(self, text: str) -> Dict[str, any]:
        """
        위기 상황 감지

        Args:
            text: 분석할 텍스트

        Returns:
            Dict: 위기 감지 결과
                - is_crisis: 위기 여부
                - crisis_type: 위기 유형
                - severity: 심각도 (0-1)
                - confidence: 신뢰도 (0-1)
                - detected_keywords: 감지된 키워드
                - recommended_action: 권장 조치
                - emergency_contacts: 응급 연락처
        """
        if not text or not text.strip():
            return self._empty_result()

        # 텍스트 정제
        text = text.lower().strip()

        # 각 위기 카테고리별 점수 계산
        category_scores = self._calculate_category_scores(text)

        # 문맥 분석
        context_analysis = self._analyze_context(text)

        # 최종 위기 판단
        crisis_assessment = self._assess_crisis(
            category_scores,
            context_analysis
        )

        # 권장 조치 결정
        recommended_action = self._determine_action(crisis_assessment)

        # 결과 구성
        result = {
            "is_crisis": crisis_assessment["is_crisis"],
            "crisis_type": crisis_assessment["crisis_type"],
            "severity": round(crisis_assessment["severity"], 2),
            "confidence": round(crisis_assessment["confidence"], 2),
            "detected_keywords": crisis_assessment["detected_keywords"],
            "recommended_action": recommended_action,
            "emergency_contacts": self._get_emergency_contacts(
                crisis_assessment["crisis_type"]
            ),
            "details": {
                "category_scores": category_scores,
                "context_analysis": context_analysis
            }
        }

        # 히스토리 저장
        self.detection_history.append({
            "text": text[:100],  # 처음 100자만 저장
            "result": result
        })

        if result["is_crisis"]:
            logger.warning(
                f"Crisis detected: {result['crisis_type']} "
                f"(severity: {result['severity']:.2f})"
            )

        return result

    def _calculate_category_scores(self, text: str) -> Dict[str, float]:
        """
        카테고리별 점수 계산

        Args:
            text: 입력 텍스트

        Returns:
            Dict: 카테고리별 점수
        """
        scores = {}
        categories = self.crisis_data.get("crisis_categories", {})

        for category_name, category_data in categories.items():
            keywords = category_data.get("keywords", [])
            score = 0.0
            matched_keywords = []

            for keyword in keywords:
                if keyword in text:
                    # 키워드 매칭 시 점수 증가
                    score += 1.0
                    matched_keywords.append(keyword)

                    # 키워드가 반복되면 추가 점수
                    count = text.count(keyword)
                    if count > 1:
                        score += (count - 1) * 0.5

            scores[category_name] = {
                "score": score,
                "matched_keywords": matched_keywords,
                "severity": category_data.get("severity", "medium")
            }

        return scores

    def _analyze_context(self, text: str) -> Dict[str, any]:
        """
        문맥 분석

        Args:
            text: 입력 텍스트

        Returns:
            Dict: 문맥 분석 결과
        """
        modifiers = self.crisis_data.get("context_modifiers", {})

        # 부정 표현 확인
        has_negation = any(
            neg in text for neg in modifiers.get("negation", [])
        )

        # 과거형 확인
        is_past_tense = any(
            past in text for past in modifiers.get("past_tense", [])
        )

        # 가정형 확인
        is_hypothetical = any(
            hyp in text for hyp in modifiers.get("hypothetical", [])
        )

        # 질문형 확인
        is_question = "?" in text or "까요" in text or "ㄹ까" in text

        return {
            "has_negation": has_negation,
            "is_past_tense": is_past_tense,
            "is_hypothetical": is_hypothetical,
            "is_question": is_question,
            "urgency_indicators": self._check_urgency_indicators(text)
        }

    def _check_urgency_indicators(self, text: str) -> List[str]:
        """
        긴급성 지표 확인

        Args:
            text: 입력 텍스트

        Returns:
            List[str]: 감지된 긴급성 지표
        """
        indicators = []

        urgency_patterns = {
            "immediate": ["지금", "당장", "오늘", "이따가"],
            "plan": ["계획", "준비", "방법", "어떻게"],
            "isolation": ["혼자", "아무도", "외로", "고립"],
            "hopelessness": ["희망 없", "소용없", "의미 없", "무의미"],
            "finality": ["마지막", "끝", "종말", "더 이상"]
        }

        for indicator_type, patterns in urgency_patterns.items():
            for pattern in patterns:
                if pattern in text:
                    indicators.append(indicator_type)
                    break

        return list(set(indicators))  # 중복 제거

    def _assess_crisis(
        self,
        category_scores: Dict[str, any],
        context_analysis: Dict[str, any]
    ) -> Dict[str, any]:
        """
        위기 평가

        Args:
            category_scores: 카테고리별 점수
            context_analysis: 문맥 분석 결과

        Returns:
            Dict: 위기 평가 결과
        """
        # 가장 높은 점수의 카테고리
        max_category = None
        max_score = 0.0
        detected_keywords = []

        for category, data in category_scores.items():
            if data["score"] > max_score:
                max_score = data["score"]
                max_category = category
                detected_keywords = data["matched_keywords"]

        # 기본 심각도 계산
        base_severity = min(max_score / 5.0, 1.0)  # 5개 이상 키워드면 최고치

        # 문맥에 따른 조정
        severity_adjustment = 0.0

        # 부정 표현이 있으면 심각도 감소
        if context_analysis["has_negation"]:
            severity_adjustment -= 0.3

        # 과거형이면 심각도 감소
        if context_analysis["is_past_tense"]:
            severity_adjustment -= 0.2

        # 가정형이면 심각도 감소
        if context_analysis["is_hypothetical"]:
            severity_adjustment -= 0.2

        # 질문형이면 심각도 약간 감소
        if context_analysis["is_question"]:
            severity_adjustment -= 0.1

        # 긴급성 지표가 있으면 심각도 증가
        urgency_count = len(context_analysis["urgency_indicators"])
        severity_adjustment += urgency_count * 0.15

        # 최종 심각도 계산
        final_severity = max(0.0, min(1.0, base_severity + severity_adjustment))

        # 신뢰도 계산
        confidence = self._calculate_confidence(
            max_score,
            context_analysis
        )

        # 위기 여부 판단
        is_crisis = (
            final_severity >= 0.7 and
            confidence >= 0.6 and
            max_score > 0
        )

        return {
            "is_crisis": is_crisis,
            "crisis_type": max_category if max_category else "none",
            "severity": final_severity,
            "confidence": confidence,
            "detected_keywords": detected_keywords
        }

    def _calculate_confidence(
        self,
        keyword_score: float,
        context_analysis: Dict[str, any]
    ) -> float:
        """
        신뢰도 계산

        Args:
            keyword_score: 키워드 매칭 점수
            context_analysis: 문맥 분석 결과

        Returns:
            float: 신뢰도 (0-1)
        """
        # 기본 신뢰도는 키워드 점수에 비례
        base_confidence = min(keyword_score / 3.0, 1.0)

        # 문맥 모호성에 따른 조정
        ambiguity_penalty = 0.0

        if context_analysis["has_negation"]:
            ambiguity_penalty += 0.2
        if context_analysis["is_past_tense"]:
            ambiguity_penalty += 0.15
        if context_analysis["is_hypothetical"]:
            ambiguity_penalty += 0.2
        if context_analysis["is_question"]:
            ambiguity_penalty += 0.1

        # 긴급성 지표가 있으면 신뢰도 증가
        if context_analysis["urgency_indicators"]:
            ambiguity_penalty -= 0.1

        final_confidence = max(0.0, min(1.0, base_confidence - ambiguity_penalty))

        return final_confidence

    def _determine_action(self, crisis_assessment: Dict) -> str:
        """
        권장 조치 결정

        Args:
            crisis_assessment: 위기 평가 결과

        Returns:
            str: 권장 조치
        """
        if not crisis_assessment["is_crisis"]:
            return "continue_conversation"

        severity = crisis_assessment["severity"]

        if severity >= 0.9:
            return "immediate_emergency_intervention"
        elif severity >= 0.7:
            return "urgent_professional_referral"
        elif severity >= 0.5:
            return "professional_recommendation"
        else:
            return "supportive_monitoring"

    def _get_emergency_contacts(self, crisis_type: str) -> Dict[str, str]:
        """
        응급 연락처 가져오기

        Args:
            crisis_type: 위기 유형

        Returns:
            Dict: 연락처 정보
        """
        emergency_resources = self.crisis_data.get("emergency_resources", {})

        # 위기 유형별 주요 연락처
        primary_contacts = {
            "suicide": "suicide_prevention",
            "self_harm": "mental_health_hotline",
            "violence": "women_hotline",
            "domestic_violence": "women_hotline"
        }

        contacts = {}

        # 주요 연락처 추가
        primary_key = primary_contacts.get(crisis_type, "mental_health_hotline")
        if primary_key in emergency_resources:
            contacts["primary"] = emergency_resources[primary_key]

        # 일반 연락처 추가
        contacts["general"] = {
            "자살예방상담전화": "1393",
            "정신건강위기상담전화": "1577-0199",
            "응급": "119"
        }

        return contacts

    def _empty_result(self) -> Dict[str, any]:
        """
        빈 결과 반환

        Returns:
            Dict: 기본 결과
        """
        return {
            "is_crisis": False,
            "crisis_type": "none",
            "severity": 0.0,
            "confidence": 0.0,
            "detected_keywords": [],
            "recommended_action": "continue_conversation",
            "emergency_contacts": {},
            "details": {}
        }

    def get_intervention_message(self, crisis_result: Dict) -> str:
        """
        개입 메시지 생성

        Args:
            crisis_result: 위기 감지 결과

        Returns:
            str: 개입 메시지
        """
        if not crisis_result["is_crisis"]:
            return ""

        crisis_type = crisis_result["crisis_type"]
        severity = crisis_result["severity"]

        messages = {
            "suicide": """
당신의 생명은 매우 소중합니다. 지금 느끼시는 고통이 얼마나 큰지 이해합니다.

하지만 혼자 감당하지 마시고, 지금 당장 전문가의 도움을 받으시는 것이 중요합니다.

🆘 자살예방상담전화: 1393 (24시간)
🆘 정신건강위기상담전화: 1577-0199 (24시간)
🆘 응급상황: 119

지금 이 순간이 힘들더라도, 도움을 받으시면 상황은 나아질 수 있습니다.
""",
            "self_harm": """
스스로를 해치고 싶은 충동이 느껴지신다니, 정말 힘든 상황이시군요.

지금 당장 안전한 곳으로 이동하시고, 전문가의 도움을 받으시는 것이 중요합니다.

📞 정신건강위기상담전화: 1577-0199 (24시간)
🆘 응급상황: 119

당신의 안전이 가장 중요합니다.
""",
            "violence": """
폭력이나 학대 상황에 있으시다면, 당신의 안전이 최우선입니다.

즉시 안전한 곳으로 피신하시고 도움을 요청하세요.

🆘 경찰: 112
📞 여성긴급전화: 1366 (24시간)
📞 아동학대신고: 112
"""
        }

        base_message = messages.get(crisis_type, messages["suicide"])

        if severity >= 0.9:
            base_message = "⚠️ 긴급 상황입니다.\n\n" + base_message

        return base_message.strip()


def test_crisis_detection():
    """위기 감지 시스템 테스트"""
    system = CrisisDetectionSystem()

    test_cases = [
        "죽고 싶어요. 더 이상 살 이유가 없어요.",
        "자살 생각이 자꾸 들어요. 힘들어요.",
        "만약 내가 죽으면 어떻게 될까요?",  # 가정형
        "예전에 죽고 싶었던 적이 있었어요.",  # 과거형
        "자해를 하고 싶어요. 손목을 긋고 싶어요.",
        "오늘 회사가 힘들었어요.",  # 일상적
        "불안하고 걱정돼요."  # 일상적
    ]

    print("=== 위기 감지 테스트 ===\n")
    for text in test_cases:
        result = system.detect_crisis(text)
        print(f"입력: {text}")
        print(f"위기 여부: {result['is_crisis']}")
        print(f"위기 유형: {result['crisis_type']}")
        print(f"심각도: {result['severity']:.2f}")
        print(f"신뢰도: {result['confidence']:.2f}")
        print(f"권장 조치: {result['recommended_action']}")

        if result["is_crisis"]:
            print("\n개입 메시지:")
            print(system.get_intervention_message(result))

        print("-" * 70)


if __name__ == "__main__":
    test_crisis_detection()
