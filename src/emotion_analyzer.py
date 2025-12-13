"""
감정 분석 모듈 v2.0 (Enhanced Emotion Analysis Module)
Emotion Analysis Module with ML Support

사용자의 텍스트에서 감정을 분석하고 분류합니다.

v2.0 기능:
- 키워드 기반 분석 (기존)
- ML 모델 기반 분석 (KoELECTRA) (NEW)
- 하이브리드 분석 (키워드 + ML 결합) (NEW)
- 복합 감정 인식 (NEW)
- 감정 추이 추적 (NEW)
- 간접 표현 해석 (NEW)
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
import os

logger = logging.getLogger(__name__)


# =============================================================================
# 데이터 클래스 및 Enum
# =============================================================================

class EmotionCategory(Enum):
    """감정 카테고리"""
    ANXIETY = "불안"
    DEPRESSION = "우울"
    ANGER = "분노"
    STRESS = "스트레스"
    JOY = "기쁨"
    SHAME = "수치심"
    NEUTRAL = "중립"
    FEAR = "공포"
    LONELINESS = "외로움"
    HOPELESSNESS = "절망"


@dataclass
class EmotionResult:
    """감정 분석 결과"""
    primary_emotion: str
    secondary_emotion: Optional[str]
    emotions: Dict[str, float]
    intensity: float
    confidence: float
    analysis_method: str  # "keyword", "ml", "hybrid"
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "primary_emotion": self.primary_emotion,
            "secondary_emotion": self.secondary_emotion,
            "emotions": self.emotions,
            "intensity": self.intensity,
            "confidence": self.confidence,
            "analysis_method": self.analysis_method,
            "details": self.details
        }


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


# =============================================================================
# NEW: ML 기반 감정 분석기 (KoELECTRA)
# =============================================================================

class MLEmotionAnalyzer:
    """
    ML 기반 감정 분석기 (NEW)

    KoELECTRA 모델을 사용하여 텍스트의 감정을 분류합니다.
    GPU가 없으면 CPU에서 실행됩니다.
    """

    def __init__(self, model_name: str = "beomi/KcELECTRA-base"):
        """
        초기화

        Args:
            model_name: HuggingFace 모델 이름
        """
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.device = "cpu"
        self.is_loaded = False

        # 감정 레이블 매핑 (모델에 따라 조정 필요)
        self.label_map = {
            0: "불안",
            1: "우울",
            2: "분노",
            3: "기쁨",
            4: "중립",
            5: "슬픔",
            6: "공포"
        }

        # 역방향 매핑
        self.reverse_label_map = {v: k for k, v in self.label_map.items()}

        logger.info(f"MLEmotionAnalyzer initialized with model: {model_name}")

    def load_model(self) -> bool:
        """
        모델 로드

        Returns:
            bool: 로드 성공 여부
        """
        try:
            import torch
            from transformers import AutoTokenizer, AutoModelForSequenceClassification

            # GPU 사용 가능 여부 확인
            if torch.cuda.is_available():
                self.device = "cuda"
                logger.info("Using GPU for ML emotion analysis")
            else:
                self.device = "cpu"
                logger.info("Using CPU for ML emotion analysis")

            # 토크나이저 및 모델 로드
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

            # 사전 학습된 감정 분류 모델 로드 시도
            # 실제 배포 시에는 파인튜닝된 모델 경로 사용
            try:
                self.model = AutoModelForSequenceClassification.from_pretrained(
                    self.model_name,
                    num_labels=len(self.label_map)
                )
            except Exception:
                # 기본 모델 로드
                self.model = AutoModelForSequenceClassification.from_pretrained(
                    self.model_name
                )

            self.model.to(self.device)
            self.model.eval()
            self.is_loaded = True

            logger.info("ML model loaded successfully")
            return True

        except ImportError as e:
            logger.warning(f"ML dependencies not installed: {e}")
            logger.warning("Install with: pip install torch transformers")
            return False

        except Exception as e:
            logger.error(f"Failed to load ML model: {e}")
            return False

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        ML 기반 감정 분석

        Args:
            text: 분석할 텍스트

        Returns:
            Dict: 분석 결과
        """
        if not self.is_loaded:
            if not self.load_model():
                return {"error": "Model not loaded", "emotions": {}}

        try:
            import torch
            import torch.nn.functional as F

            # 토큰화
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # 추론
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probabilities = F.softmax(logits, dim=-1)

            # 결과 처리
            probs = probabilities[0].cpu().numpy()

            # 감정별 확률
            emotions = {}
            for idx, prob in enumerate(probs):
                if idx in self.label_map:
                    emotions[self.label_map[idx]] = float(prob)

            # 상위 2개 감정
            sorted_emotions = sorted(emotions.items(), key=lambda x: x[1], reverse=True)
            primary_emotion = sorted_emotions[0][0] if sorted_emotions else "중립"
            secondary_emotion = sorted_emotions[1][0] if len(sorted_emotions) > 1 else None

            # 신뢰도
            confidence = sorted_emotions[0][1] if sorted_emotions else 0.0

            return {
                "primary_emotion": primary_emotion,
                "secondary_emotion": secondary_emotion,
                "emotions": emotions,
                "confidence": confidence,
                "method": "ml"
            }

        except Exception as e:
            logger.error(f"ML analysis failed: {e}")
            return {"error": str(e), "emotions": {}}


# =============================================================================
# NEW: 하이브리드 감정 분석기 (Hybrid Analyzer)
# =============================================================================

class HybridEmotionAnalyzer:
    """
    하이브리드 감정 분석기 (NEW)

    키워드 기반과 ML 기반 분석을 결합하여
    더 정확한 감정 분석을 수행합니다.
    """

    def __init__(
        self,
        use_ml: bool = True,
        ml_weight: float = 0.6,
        keyword_weight: float = 0.4
    ):
        """
        초기화

        Args:
            use_ml: ML 분석 사용 여부
            ml_weight: ML 결과 가중치 (0-1)
            keyword_weight: 키워드 결과 가중치 (0-1)
        """
        self.keyword_analyzer = EmotionAnalyzer()
        self.ml_analyzer = MLEmotionAnalyzer() if use_ml else None
        self.use_ml = use_ml
        self.ml_weight = ml_weight
        self.keyword_weight = keyword_weight

        # 감정 추이 기록
        self.emotion_history: List[EmotionResult] = []
        self.max_history = 20

        # 간접 표현 해석 사전
        self.indirect_expression_map = {
            "그냥": {"hidden_emotion": "우울", "confidence_boost": 0.2},
            "별거 아닌데": {"hidden_emotion": "우울", "confidence_boost": 0.3},
            "괜찮아요": {"hidden_emotion": "불안", "confidence_boost": 0.2},
            "모르겠어요": {"hidden_emotion": "혼란", "confidence_boost": 0.2},
            "피곤해서": {"hidden_emotion": "우울", "confidence_boost": 0.2},
        }

        logger.info(f"HybridEmotionAnalyzer initialized (ML: {use_ml})")

    def analyze(self, text: str, include_history: bool = True) -> EmotionResult:
        """
        하이브리드 감정 분석

        Args:
            text: 분석할 텍스트
            include_history: 히스토리에 기록 여부

        Returns:
            EmotionResult: 분석 결과
        """
        if not text or not text.strip():
            return EmotionResult(
                primary_emotion="중립",
                secondary_emotion=None,
                emotions={},
                intensity=0.0,
                confidence=0.0,
                analysis_method="none"
            )

        # 1. 키워드 기반 분석
        keyword_result = self.keyword_analyzer.analyze(text)

        # 2. 간접 표현 분석
        indirect_result = self._analyze_indirect_expressions(text)

        # 3. ML 기반 분석 (사용 가능한 경우)
        ml_result = None
        if self.use_ml and self.ml_analyzer:
            ml_result = self.ml_analyzer.analyze(text)
            if "error" in ml_result:
                ml_result = None

        # 4. 결과 결합
        combined = self._combine_results(
            keyword_result, ml_result, indirect_result
        )

        # 5. 히스토리에 추가
        if include_history:
            self._add_to_history(combined)

        return combined

    def _analyze_indirect_expressions(self, text: str) -> Dict[str, Any]:
        """간접 표현 분석"""
        detected = []
        hidden_emotions = {}

        for expr, info in self.indirect_expression_map.items():
            if expr in text:
                detected.append(expr)
                emotion = info["hidden_emotion"]
                boost = info["confidence_boost"]

                if emotion in hidden_emotions:
                    hidden_emotions[emotion] = max(
                        hidden_emotions[emotion], boost
                    )
                else:
                    hidden_emotions[emotion] = boost

        return {
            "detected_expressions": detected,
            "hidden_emotions": hidden_emotions
        }

    def _combine_results(
        self,
        keyword_result: Dict,
        ml_result: Optional[Dict],
        indirect_result: Dict
    ) -> EmotionResult:
        """결과 결합"""
        combined_emotions = {}

        # 키워드 결과 반영
        for emotion, score in keyword_result.get("emotions", {}).items():
            combined_emotions[emotion] = score * self.keyword_weight

        # ML 결과 반영 (있는 경우)
        if ml_result:
            for emotion, score in ml_result.get("emotions", {}).items():
                if emotion in combined_emotions:
                    combined_emotions[emotion] += score * self.ml_weight
                else:
                    combined_emotions[emotion] = score * self.ml_weight
            analysis_method = "hybrid"
        else:
            analysis_method = "keyword"

        # 간접 표현 결과 반영
        for emotion, boost in indirect_result.get("hidden_emotions", {}).items():
            if emotion in combined_emotions:
                combined_emotions[emotion] += boost
            else:
                combined_emotions[emotion] = boost

        # 정규화
        max_score = max(combined_emotions.values()) if combined_emotions else 1
        normalized = {
            k: min(v / max_score, 1.0) if max_score > 0 else 0
            for k, v in combined_emotions.items()
        }

        # 주요 감정 결정
        sorted_emotions = sorted(
            normalized.items(), key=lambda x: x[1], reverse=True
        )

        primary = sorted_emotions[0][0] if sorted_emotions else "중립"
        secondary = sorted_emotions[1][0] if len(sorted_emotions) > 1 and sorted_emotions[1][1] > 0.3 else None

        # 강도 및 신뢰도 계산
        intensity = keyword_result.get("intensity", 0.5)
        confidence = sorted_emotions[0][1] if sorted_emotions else 0.0

        if ml_result and "confidence" in ml_result:
            confidence = (confidence + ml_result["confidence"]) / 2

        return EmotionResult(
            primary_emotion=primary,
            secondary_emotion=secondary,
            emotions=normalized,
            intensity=intensity,
            confidence=round(confidence, 2),
            analysis_method=analysis_method,
            details={
                "keyword_result": keyword_result.get("primary_emotion"),
                "ml_result": ml_result.get("primary_emotion") if ml_result else None,
                "indirect_expressions": indirect_result.get("detected_expressions", []),
                "contextual_clues": keyword_result.get("details", {}).get("contextual_clues", [])
            }
        )

    def _add_to_history(self, result: EmotionResult):
        """히스토리에 추가"""
        self.emotion_history.append(result)
        if len(self.emotion_history) > self.max_history:
            self.emotion_history = self.emotion_history[-self.max_history:]

    def get_emotion_trajectory(self) -> Dict[str, Any]:
        """
        감정 추이 분석

        Returns:
            Dict: 감정 추이 정보
        """
        if not self.emotion_history:
            return {"message": "No history"}

        # 감정별 출현 빈도
        emotion_counts = Counter(
            r.primary_emotion for r in self.emotion_history
        )

        # 강도 추이
        intensity_trend = [r.intensity for r in self.emotion_history]

        # 개선 여부 판단
        recent = intensity_trend[-5:] if len(intensity_trend) >= 5 else intensity_trend
        if len(recent) >= 2:
            trend = "improving" if recent[-1] < recent[0] else "worsening"
        else:
            trend = "stable"

        return {
            "total_analyses": len(self.emotion_history),
            "emotion_frequency": dict(emotion_counts.most_common()),
            "intensity_trend": intensity_trend,
            "average_intensity": sum(intensity_trend) / len(intensity_trend),
            "overall_trend": trend,
            "dominant_emotion": emotion_counts.most_common(1)[0][0] if emotion_counts else "중립"
        }

    def get_session_summary(self) -> str:
        """
        세션 요약 생성

        Returns:
            str: 세션 요약 텍스트
        """
        trajectory = self.get_emotion_trajectory()

        if trajectory.get("message") == "No history":
            return "분석된 대화가 없습니다."

        dominant = trajectory.get("dominant_emotion", "중립")
        avg_intensity = trajectory.get("average_intensity", 0)
        trend = trajectory.get("overall_trend", "stable")

        trend_text = {
            "improving": "호전되는",
            "worsening": "악화되는",
            "stable": "안정적인"
        }.get(trend, "안정적인")

        intensity_text = "높은" if avg_intensity > 0.6 else "중간" if avg_intensity > 0.3 else "낮은"

        return f"주요 감정: {dominant}, {trend_text} 추세, {intensity_text} 강도"


# =============================================================================
# NEW: 감정 인사이트 생성기
# =============================================================================

class EmotionInsightGenerator:
    """
    감정 분석 결과를 바탕으로 인사이트를 생성합니다. (NEW)
    """

    def __init__(self):
        # 감정-인사이트 매핑
        self.insights = {
            "불안": {
                "patterns": [
                    "미래에 대한 걱정이 많으신 것 같아요.",
                    "불확실한 상황에서 불안감을 느끼시는군요.",
                    "통제할 수 없는 것에 대한 두려움이 있으신 것 같아요."
                ],
                "techniques": ["호흡법", "그라운딩", "점진적 근육 이완"]
            },
            "우울": {
                "patterns": [
                    "에너지가 많이 떨어지신 것 같아요.",
                    "의욕이 없고 무기력하신 상태군요.",
                    "즐거움을 느끼기 어려우신 것 같아요."
                ],
                "techniques": ["행동활성화", "작은 성취 경험", "일상 루틴"]
            },
            "분노": {
                "patterns": [
                    "억울하고 답답한 마음이 크시군요.",
                    "참아온 감정이 많으신 것 같아요.",
                    "경계가 침범당한 느낌이 드시는군요."
                ],
                "techniques": ["STOP 기법", "분노 일기", "표현 연습"]
            },
            "스트레스": {
                "patterns": [
                    "감당해야 할 것이 많으시네요.",
                    "여유가 없이 바쁘게 지내고 계시군요.",
                    "쉴 틈이 없으신 것 같아요."
                ],
                "techniques": ["시간 관리", "우선순위 설정", "휴식 시간 확보"]
            }
        }

    def generate(self, result: EmotionResult) -> Dict[str, Any]:
        """
        감정 분석 결과를 바탕으로 인사이트 생성

        Args:
            result: 감정 분석 결과

        Returns:
            Dict: 인사이트 정보
        """
        primary = result.primary_emotion
        insight_data = self.insights.get(primary, {})

        patterns = insight_data.get("patterns", [])
        techniques = insight_data.get("techniques", [])

        # 랜덤 선택 대신 첫 번째 사용
        pattern_insight = patterns[0] if patterns else "지금 느끼시는 감정이 중요해요."
        suggested_techniques = techniques[:2] if techniques else []

        return {
            "primary_emotion": primary,
            "intensity": result.intensity,
            "insight": pattern_insight,
            "suggested_techniques": suggested_techniques,
            "secondary_emotion": result.secondary_emotion
        }


# =============================================================================
# 테스트 함수
# =============================================================================

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


def test_hybrid_analyzer():
    """하이브리드 분석기 테스트"""
    print("\n=== 하이브리드 감정 분석 테스트 ===\n")

    # ML 없이 테스트 (ML 모델 로드에 시간이 걸리므로)
    analyzer = HybridEmotionAnalyzer(use_ml=False)

    test_cases = [
        "너무 불안하고 걱정돼요. 잠도 못 자겠어요.",
        "그냥 그래요. 별거 아니에요.",  # 간접 표현
        "괜찮아요. 별일 아니에요.",  # 간접 표현
        "화가 나요. 너무 억울하고 짜증나요.",
        "요즘 너무 피곤해서 그래요."  # 간접 표현
    ]

    for text in test_cases:
        result = analyzer.analyze(text)
        print(f"입력: {text}")
        print(f"주요 감정: {result.primary_emotion}")
        print(f"보조 감정: {result.secondary_emotion}")
        print(f"강도: {result.intensity}")
        print(f"신뢰도: {result.confidence}")
        print(f"분석 방법: {result.analysis_method}")
        print(f"간접 표현: {result.details.get('indirect_expressions', [])}")
        print("-" * 50)

    # 감정 추이 확인
    print("\n=== 감정 추이 ===")
    trajectory = analyzer.get_emotion_trajectory()
    print(f"총 분석 횟수: {trajectory['total_analyses']}")
    print(f"감정 빈도: {trajectory['emotion_frequency']}")
    print(f"평균 강도: {trajectory['average_intensity']:.2f}")
    print(f"전체 추세: {trajectory['overall_trend']}")

    # 세션 요약
    print(f"\n세션 요약: {analyzer.get_session_summary()}")


if __name__ == "__main__":
    test_emotion_analyzer()
    test_hybrid_analyzer()
