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
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
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

    def __init__(self, history_size: int = 20, llm_adapter: Optional[Any] = None, use_embedding: bool = True):
        """
        초기화

        Args:
            history_size: 추적할 감정 히스토리 크기
            llm_adapter: LLM 어댑터 (하이브리드 분석용, 선택적)
            use_embedding: 임베딩 모델 사용 여부 (기본: True)
        """
        self.emotion_expressions = self._load_emotion_expressions()
        self.korean_specific_emotions = self._load_korean_emotions()
        self.age_group_expressions = self._load_age_group_expressions()
        self.emotion_history = deque(maxlen=history_size)
        self.llm_adapter = llm_adapter  # LLM 어댑터 (하이브리드 분석용)
        self.use_llm = llm_adapter is not None
        self.use_embedding = use_embedding
        
        # 임베딩 모델 (lazy loading)
        self._embedding_model = None
        self._emotion_embeddings = None  # 감정 키워드 임베딩 캐시
        
        logger.info(f"KoreanEmotionAnalyzer initialized (LLM: {'enabled' if self.use_llm else 'disabled'}, Embedding: {'enabled' if self.use_embedding else 'disabled'})")

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
                "울화", "치밀", "약오르", "미치겠",
                "존나", "개", "ㅈ같", "개빡",  # 세대별 강조 표현
                # "답답"은 맥락에 따라 우울/불안일 수 있으므로 제거
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
                "회색", "암울", "어둡", "무겁", "가라앉",
                "심심", "심심해", "심심함",  # 세대별 표현
                "허탈", "허망", "절망적"
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
        context: Optional[Dict] = None,
        conversation_history: Optional[List[Dict]] = None
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

        # 1. 은유/비유 표현 처리 (Phase 3 - 우선 처리)
        metaphor_emotions = self._detect_metaphors(text)
        
        # 2. 맥락 기반 신체 증상 감지
        physical_symptoms = self._detect_physical_symptoms(text)
        
        # 3. 키워드 기반 1차 분석 (빠른 필터링)
        basic_emotions = self._analyze_basic_emotions(text)
        korean_emotions = self._analyze_korean_emotions(text)
        
        # 4. 부정문 처리 (키워드 매칭 결과 보정)
        basic_emotions = self._apply_negation_correction(text, basic_emotions)
        korean_emotions = self._apply_negation_correction(text, korean_emotions)

        # 5. 신체 증상이 있으면 불안/우울 점수 보정
        if physical_symptoms:
            if "답답" in text.lower() or "답답해" in text.lower():
                # 신체적 답답함은 불안/우울로 해석
                if "불안" not in korean_emotions:
                    korean_emotions["불안"] = 0.0
                korean_emotions["불안"] += 0.8
                if "우울" not in korean_emotions:
                    korean_emotions["우울"] = 0.0
                korean_emotions["우울"] += 0.6

        # 6. 모든 감정 통합
        all_emotions = {**basic_emotions, **korean_emotions}
        
        # 7. 은유/비유 표현 감정 추가 (Phase 3)
        for emotion, score in metaphor_emotions.items():
            if emotion not in all_emotions:
                all_emotions[emotion] = 0.0
            all_emotions[emotion] = max(all_emotions[emotion], score)
        
        # 8. 다중 모델 앙상블 (키워드 + LLM + 임베딩)
        model_results = {
            "keyword": all_emotions,
            "llm": {},
            "embedding": {}
        }
        
        # 6-1. LLM 기반 검증
        if self.use_llm and self.llm_adapter:
            try:
                llm_emotions = self._analyze_with_llm(text, all_emotions, conversation_history)
                if llm_emotions:
                    model_results["llm"] = llm_emotions
                    logger.debug("LLM analysis completed")
            except Exception as e:
                logger.warning(f"LLM analysis failed: {e}")
        
        # 6-2. 임베딩 기반 감정 분석
        if self.use_embedding:
            try:
                embedding_emotions = self._analyze_with_embedding(text)
                if embedding_emotions:
                    model_results["embedding"] = embedding_emotions
                    logger.debug("Embedding analysis completed")
            except Exception as e:
                logger.warning(f"Embedding analysis failed: {e}")
        
        # 6-3. 다중 모델 앙상블 (가중 평균)
        all_emotions = self._ensemble_models(model_results)
        
        # 6-4. 신뢰도 기반 후처리 (Phase 3)
        all_emotions = self._apply_confidence_filter(all_emotions, confidence_threshold=0.25)
        
        # 6-5. 감정 전이 패턴 적용 (Phase 3)
        if len(self.emotion_history) > 0:
            all_emotions = self._apply_emotion_transition(all_emotions)

        # 9. 주요 감정 결정
        primary_emotion = self._determine_primary_emotion(all_emotions)

        # 10. 감정 강도 측정 (1-10) - 고도화 버전
        intensity = self._measure_intensity(text, primary_emotion, all_emotions, conversation_history)

        # 11. 부가 감정 추출
        secondary_emotions = self._extract_secondary_emotions(
            all_emotions,
            primary_emotion
        )

        # 12. 연령대 추정
        age_group = self._estimate_age_group(text)

        # 13. 문화적 마커 감지
        cultural_markers = self._detect_cultural_markers(text)

        # 14. 신뢰도 계산
        confidence = self._calculate_confidence(
            all_emotions,
            text,
            age_group
        )

        # 15. 복합 감정 감지
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

    def _apply_negation_correction(self, text: str, emotions: Dict[str, float]) -> Dict[str, float]:
        """
        부정문/반어법 처리 - 키워드 매칭 결과 보정 (고도화)
        
        Args:
            text: 입력 텍스트
            emotions: 감정 점수 딕셔너리
            
        Returns:
            보정된 감정 점수
        """
        corrected = emotions.copy()
        
        # 부정 패턴 감지 (확장)
        negation_patterns = [
            r"(.+?)(지\s*않|아니|안\s*)(\w+)",  # "기쁘지 않아요", "슬프지 않아요"
            r"(.+?)(\s*아니|안\s*)(\w+)",  # "기쁘 아니에요"
            r"별로\s*(.+)",  # "별로 기쁘지 않아요"
            r"전혀\s*(.+)",  # "전혀 슬프지 않아요"
            r"하나도\s*(.+)",  # "하나도 기쁘지 않아요"
            r"전혀\s*(.+)",  # "전혀 좋지 않아요"
            r"결코\s*(.+)",  # "결코 행복하지 않아요"
        ]
        
        # 반어법 패턴 감지
        sarcasm_patterns = [
            r"좋아\s*죽겠",  # "좋아 죽겠네"
            r"행복하네요\s*정말",  # "행복하네요 정말" (비꼬는 톤)
            r"기쁘다\s*정말",  # "기쁘다 정말"
            r"(\w+)\s*죽겠",  # "~ 죽겠" (과장된 표현)
        ]
        
        # 이중 부정 패턴
        double_negation_patterns = [
            r"안\s*(.+?)\s*지\s*않",  # "안 좋지 않아요" → 긍정
        ]
        
        # 부정문 처리
        for emotion, score in emotions.items():
            if score > 0:
                emotion_keywords = []
                if emotion in self.emotion_expressions:
                    emotion_keywords = self.emotion_expressions[emotion]
                elif emotion in self.korean_specific_emotions:
                    emotion_keywords = self.korean_specific_emotions[emotion]
                
                for keyword in emotion_keywords:
                    if keyword in text:
                        # 이중 부정 확인 (긍정으로 전환)
                        is_double_negation = any(re.search(pattern, text, re.IGNORECASE) for pattern in double_negation_patterns)
                        if is_double_negation:
                            # 이중 부정은 긍정이므로 점수 유지 또는 증가
                            corrected[emotion] = min(1.0, score * 1.2)
                            logger.debug(f"Double negation detected for {emotion}: {score} -> {corrected[emotion]}")
                            continue
                        
                        # 반어법 확인 (분노/불만으로 전환)
                        is_sarcasm = any(re.search(pattern, text, re.IGNORECASE) for pattern in sarcasm_patterns)
                        if is_sarcasm and emotion in ["기쁨", "행복"]:
                            # 반어법이면 긍정 감정을 분노로 전환
                            if "분노" not in corrected:
                                corrected["분노"] = 0.0
                            corrected["분노"] += score * 0.8
                            corrected[emotion] = max(0.0, score * 0.1)  # 원래 감정 90% 감소
                            logger.debug(f"Sarcasm detected: {emotion} -> 분노")
                            continue
                        
                        # 일반 부정문 확인
                        is_negation = any(re.search(pattern, text, re.IGNORECASE) for pattern in negation_patterns)
                        if is_negation:
                            corrected[emotion] = max(0.0, score * 0.2)  # 80% 감소
                            logger.debug(f"Negation detected for {emotion}: {score} -> {corrected[emotion]}")
                            break
        
        return corrected

    def _calculate_dynamic_weights(
        self,
        text: str,
        keyword_emotions: Dict[str, float],
        llm_emotions: Dict[str, float]
    ) -> Tuple[float, float]:
        """
        문맥 기반 동적 가중치 계산
        
        Args:
            text: 입력 텍스트
            keyword_emotions: 키워드 매칭 결과
            llm_emotions: LLM 분석 결과
            
        Returns:
            (keyword_weight, llm_weight) 튜플
        """
        # 기본 가중치
        keyword_weight = 0.4
        llm_weight = 0.6
        
        # 텍스트 길이에 따른 조정
        text_length = len(text)
        if text_length < 10:
            # 짧은 텍스트는 키워드에 더 의존
            keyword_weight = 0.6
            llm_weight = 0.4
        elif text_length > 100:
            # 긴 텍스트는 LLM에 더 의존 (문맥 분석 중요)
            keyword_weight = 0.3
            llm_weight = 0.7
        
        # 키워드 매칭 신뢰도
        max_keyword_score = max(keyword_emotions.values()) if keyword_emotions else 0
        if max_keyword_score > 0.8:
            # 명확한 키워드 매칭이 있으면 키워드 가중치 증가
            keyword_weight += 0.1
            llm_weight -= 0.1
        elif max_keyword_score < 0.3:
            # 키워드 매칭이 약하면 LLM에 더 의존
            keyword_weight -= 0.1
            llm_weight += 0.1
        
        # LLM 결과 신뢰도 (LLM이 감정을 감지했는지)
        max_llm_score = max(llm_emotions.values()) if llm_emotions else 0
        if max_llm_score > 0.5:
            # LLM이 명확한 감정을 감지했으면 LLM 가중치 증가
            llm_weight += 0.1
            keyword_weight -= 0.1
        
        # 가중치 정규화 (0.2 ~ 0.8 범위)
        keyword_weight = max(0.2, min(0.8, keyword_weight))
        llm_weight = max(0.2, min(0.8, llm_weight))
        
        # 합이 1.0이 되도록 정규화
        total = keyword_weight + llm_weight
        keyword_weight /= total
        llm_weight /= total
        
        return keyword_weight, llm_weight

    def _load_embedding_model(self):
        """임베딩 모델 로드 (lazy loading)"""
        if self._embedding_model is None:
            try:
                import torch
                import os
                from sentence_transformers import SentenceTransformer
                
                # PyTorch 버전 확인
                torch_version = torch.__version__
                logger.info(f"PyTorch 버전: {torch_version}")
                
                # safetensors 사용 강제 (보안 취약점 방지)
                # 환경 변수 설정으로 safetensors 우선 사용
                os.environ.setdefault('SAFETENSORS_FAST_GPU', '1')
                os.environ.setdefault('HF_HUB_DISABLE_SYMLINKS_WARNING', '1')
                
                # transformers 라이브러리에서 safetensors 사용 강제
                try:
                    from transformers import AutoModel
                    # safetensors를 기본으로 사용하도록 설정
                    os.environ.setdefault('TRANSFORMERS_SAFE_LOADING', '1')
                except ImportError:
                    pass
                
                # 모델 로드 시도 (safetensors 우선 사용)
                try:
                    # PyTorch 버전 확인 및 경고
                    try:
                        import torch
                        torch_version = torch.__version__
                        version_parts = torch_version.split('+')[0].split('.')
                        major, minor = int(version_parts[0]), int(version_parts[1])
                        
                        if major < 2 or (major == 2 and minor < 6):
                            logger.warning(f"PyTorch 버전이 낮습니다: {torch_version} (권장: 2.6.0 이상)")
                            logger.warning("safetensors 형식 모델을 사용하거나 PyTorch를 업그레이드하세요.")
                    except:
                        pass
                    
                    # transformers 라이브러리에서 safetensors 사용 강제
                    os.environ['SAFETENSORS_FAST_GPU'] = '1'
                    
                    # SentenceTransformer는 내부적으로 safetensors를 지원
                    # 모델이 safetensors 형식이면 자동으로 사용
                    # trust_remote_code=False로 보안 강화
                    self._embedding_model = SentenceTransformer(
                        "jhgan/ko-sroberta-multitask",
                        device='cpu',  # CPU에서 먼저 로드 후 필요시 GPU로 이동
                        trust_remote_code=False
                    )
                    logger.info("감정 분석용 임베딩 모델 로드 완료: jhgan/ko-sroberta-multitask")
                except Exception as load_error:
                    error_msg = str(load_error)
                    logger.warning(f"기본 로드 방식 실패: {load_error}")
                    
                    # PyTorch 버전 문제인 경우 명확한 안내
                    if "torch.load" in error_msg or "CVE-2025-32434" in error_msg or "2.6" in error_msg:
                        logger.warning("=" * 60)
                        logger.warning("PyTorch 버전 문제가 감지되었습니다.")
                        logger.warning(f"현재 PyTorch 버전: {torch_version}")
                        logger.warning("필요한 버전: 2.6.0 이상")
                        logger.warning("")
                        logger.warning("해결 방법:")
                        logger.warning("1. PyTorch 업그레이드:")
                        logger.warning("   pip install --upgrade torch>=2.6.0")
                        logger.warning("")
                        logger.warning("2. 또는 CUDA 버전에 맞는 PyTorch 설치:")
                        logger.warning("   pip install torch>=2.6.0 --index-url https://download.pytorch.org/whl/cu121")
                        logger.warning("")
                        logger.warning("3. 또는 upgrade_torch.py 스크립트 실행:")
                        logger.warning("   python upgrade_torch.py")
                        logger.warning("")
                        logger.warning("참고: 대체 모델이 로드되어 시스템은 정상 작동합니다.")
                        logger.warning("=" * 60)
                    
                    logger.warning("대체 모델로 재시도 중...")
                    
                    # 대체 모델 시도
                    try:
                        # 더 작은 한국어 모델로 시도
                        self._embedding_model = SentenceTransformer(
                            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                            device='cpu'
                        )
                        logger.warning("대체 모델 로드 완료: paraphrase-multilingual-MiniLM-L12-v2")
                    except Exception as fallback_error:
                        logger.error(f"대체 모델 로드도 실패: {fallback_error}")
                        raise load_error  # 원래 오류를 다시 발생시킴
                    
            except ImportError as e:
                logger.error(f"필수 라이브러리 import 실패: {e}")
                logger.error("sentence-transformers를 설치해주세요: pip install sentence-transformers")
                self._embedding_model = None
                self.use_embedding = False
            except Exception as e:
                error_msg = str(e)
                logger.error(f"임베딩 모델 로드 실패: {error_msg}")
                
                # PyTorch 버전 관련 오류인지 확인
                if "torch.load" in error_msg or "CVE-2025-32434" in error_msg or "2.6" in error_msg:
                    logger.error("PyTorch 버전 문제가 감지되었습니다.")
                    logger.error("다음 명령어로 PyTorch를 업그레이드하세요:")
                    logger.error("  pip install --upgrade torch>=2.6.0")
                    logger.error("또는 safetensors 형식의 모델을 사용하세요.")
                
                logger.warning("임베딩 모델 없이 키워드 기반 분석만 사용합니다.")
                self._embedding_model = None
                self.use_embedding = False
        return self._embedding_model

    def _get_emotion_embeddings(self) -> Dict[str, np.ndarray]:
        """감정 키워드 임베딩 생성 및 캐싱"""
        if self._emotion_embeddings is None:
            embedding_model = self._load_embedding_model()
            if embedding_model is None:
                return {}
            
            # 모든 감정 키워드 수집
            emotion_texts = {}
            for emotion, keywords in self.emotion_expressions.items():
                # 각 감정의 대표 키워드 3-5개 선택
                representative_keywords = keywords[:5]
                emotion_texts[emotion] = f"{emotion} {' '.join(representative_keywords)}"
            
            for emotion, keywords in self.korean_specific_emotions.items():
                representative_keywords = keywords[:5]
                emotion_texts[emotion] = f"{emotion} {' '.join(representative_keywords)}"
            
            # 임베딩 생성
            emotion_names = list(emotion_texts.keys())
            emotion_sentences = list(emotion_texts.values())
            embeddings = embedding_model.encode(emotion_sentences, normalize_embeddings=True)
            
            # 딕셔너리로 변환
            self._emotion_embeddings = {
                emotion: embeddings[i] 
                for i, emotion in enumerate(emotion_names)
            }
            
            logger.debug(f"감정 키워드 임베딩 생성 완료: {len(self._emotion_embeddings)}개 감정")
        
        return self._emotion_embeddings

    def _analyze_with_embedding(self, text: str) -> Dict[str, float]:
        """
        임베딩 기반 감정 분석
        
        Args:
            text: 입력 텍스트
            
        Returns:
            임베딩 분석 결과 감정 점수
        """
        try:
            embedding_model = self._load_embedding_model()
            if embedding_model is None:
                return {}
            
            # 텍스트 임베딩
            text_embedding = embedding_model.encode([text], normalize_embeddings=True)[0]
            
            # 감정 키워드 임베딩
            emotion_embeddings = self._get_emotion_embeddings()
            if not emotion_embeddings:
                return {}
            
            # 코사인 유사도 계산
            emotion_scores = {}
            for emotion, emotion_embedding in emotion_embeddings.items():
                # 코사인 유사도 (이미 정규화되어 있으므로 내적만 계산)
                similarity = np.dot(text_embedding, emotion_embedding)
                # 0-1 범위로 정규화 (코사인 유사도는 -1~1이지만 정규화된 벡터는 0~1)
                emotion_scores[emotion] = max(0.0, similarity)
            
            # 정규화 (최고 점수를 1.0으로)
            max_score = max(emotion_scores.values()) if emotion_scores else 1.0
            if max_score > 0:
                emotion_scores = {k: v / max_score for k, v in emotion_scores.items()}
            
            logger.debug(f"Embedding analysis: top emotion = {max(emotion_scores.items(), key=lambda x: x[1]) if emotion_scores else 'N/A'}")
            return emotion_scores
            
        except Exception as e:
            logger.warning(f"Embedding analysis failed: {e}")
            return {}

    def _ensemble_models(self, model_results: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """
        다중 모델 앙상블 (키워드 + LLM + 임베딩)
        
        Args:
            model_results: 각 모델의 결과
                - keyword: 키워드 매칭 결과
                - llm: LLM 분석 결과
                - embedding: 임베딩 분석 결과
                
        Returns:
            앙상블된 감정 점수
        """
        keyword_emotions = model_results.get("keyword", {})
        llm_emotions = model_results.get("llm", {})
        embedding_emotions = model_results.get("embedding", {})
        
        # 사용 가능한 모델 수 확인
        available_models = []
        if keyword_emotions:
            available_models.append("keyword")
        if llm_emotions:
            available_models.append("llm")
        if embedding_emotions:
            available_models.append("embedding")
        
        if not available_models:
            return keyword_emotions  # fallback
        
        # 모델별 가중치 (동적 조정)
        weights = {
            "keyword": 0.3,
            "llm": 0.5,
            "embedding": 0.2
        }
        
        # 사용 가능한 모델만 정규화
        total_weight = sum(weights[model] for model in available_models)
        for model in available_models:
            weights[model] /= total_weight
        
        # 모든 감정 키 수집
        all_emotions = set()
        all_emotions.update(keyword_emotions.keys())
        all_emotions.update(llm_emotions.keys())
        all_emotions.update(embedding_emotions.keys())
        
        # 가중 평균 계산
        ensemble_emotions = {}
        for emotion in all_emotions:
            score = 0.0
            if emotion in keyword_emotions:
                score += keyword_emotions[emotion] * weights.get("keyword", 0)
            if emotion in llm_emotions:
                score += llm_emotions[emotion] * weights.get("llm", 0)
            if emotion in embedding_emotions:
                score += embedding_emotions[emotion] * weights.get("embedding", 0)
            
            ensemble_emotions[emotion] = score
        
        logger.debug(f"Ensemble: {len(available_models)} models ({', '.join(available_models)})")
        return ensemble_emotions

    def _detect_metaphors(self, text: str) -> Dict[str, float]:
        """
        은유/비유 표현 감지 (Phase 3)
        
        Args:
            text: 입력 텍스트
            
        Returns:
            은유 표현에서 추출한 감정 점수
        """
        metaphor_emotions = {}
        
        # 은유 패턴 사전
        metaphor_patterns = {
            # 신체 부위 기반 은유
            "마음이 무겁다": ("우울", 0.9),
            "마음이 가볍다": ("기쁨", 0.8),
            "마음이 차갑다": ("외로움", 0.7),
            "마음이 뜨겁다": ("분노", 0.6),
            "마음이 따뜻하다": ("기쁨", 0.8),
            "마음이 시리다": ("슬픔", 0.7),
            "마음이 아프다": ("슬픔", 0.8),
            "마음이 편하다": ("기쁨", 0.7),
            "마음이 불편하다": ("불안", 0.7),
            
            # 가슴 관련 은유
            "가슴이 답답하다": ("불안", 0.9),
            "가슴이 뻥 뚫렸다": ("기쁨", 0.8),
            "가슴이 메인다": ("슬픔", 0.8),
            "가슴이 시린다": ("슬픔", 0.7),
            "가슴이 아프다": ("슬픔", 0.8),
            
            # 무게/무겁다 관련
            "무겁다": ("우울", 0.6),
            "무게가 느껴진다": ("우울", 0.7),
            "짐이 무겁다": ("우울", 0.7),
            
            # 밝기/어둠 관련
            "어둡다": ("우울", 0.7),
            "밝다": ("기쁨", 0.7),
            "빛이 보인다": ("희망", 0.8),
            "터널 끝": ("희망", 0.7),
            
            # 날씨 관련 은유
            "비가 온다": ("슬픔", 0.6),
            "맑다": ("기쁨", 0.7),
            "흐리다": ("우울", 0.6),
            
            # 색깔 관련 은유
            "회색": ("우울", 0.7),
            "밝은 색": ("기쁨", 0.6),
            "어두운 색": ("우울", 0.6)
        }
        
        # 패턴 매칭
        for pattern, (emotion, score) in metaphor_patterns.items():
            if pattern in text:
                if emotion not in metaphor_emotions:
                    metaphor_emotions[emotion] = 0.0
                metaphor_emotions[emotion] = max(metaphor_emotions[emotion], score)
        
        return metaphor_emotions

    def _apply_confidence_filter(
        self, 
        emotions: Dict[str, float], 
        confidence_threshold: float = 0.25
    ) -> Dict[str, float]:
        """
        신뢰도 기반 후처리 (Phase 3)
        
        낮은 신뢰도의 감정을 필터링하고, 신뢰도 기반 가중치 재조정
        
        Args:
            emotions: 감정 점수 딕셔너리
            confidence_threshold: 최소 신뢰도 임계값
            
        Returns:
            필터링된 감정 점수
        """
        if not emotions:
            return emotions
        
        # 1. 임계값 이하 감정 제거
        filtered = {
            emotion: score 
            for emotion, score in emotions.items() 
            if score >= confidence_threshold
        }
        
        # 2. 최고 점수 기반 정규화 (신뢰도 향상)
        if filtered:
            max_score = max(filtered.values())
            if max_score > 0:
                # 최고 점수를 1.0으로 정규화하고 나머지도 비례 조정
                filtered = {
                    emotion: score / max_score 
                    for emotion, score in filtered.items()
                }
        
        return filtered

    def _apply_emotion_transition(self, emotions: Dict[str, float]) -> Dict[str, float]:
        """
        감정 전이 패턴 적용 (Phase 3)
        
        이전 감정에서 현재 감정으로의 전이 확률을 고려하여 점수 조정
        
        Args:
            emotions: 현재 감정 점수
            
        Returns:
            전이 패턴이 적용된 감정 점수
        """
        if not self.emotion_history or len(self.emotion_history) == 0:
            return emotions
        
        # 최근 감정 추출
        recent_emotions = []
        for record in list(self.emotion_history)[-3:]:  # 최근 3개
            if hasattr(record, 'primary_emotion'):
                recent_emotions.append(record.primary_emotion)
        
        if not recent_emotions:
            return emotions
        
        # 최근 주요 감정
        last_emotion = recent_emotions[-1]
        
        # 감정 전이 확률 매트릭스
        transition_matrix = {
            "우울": {
                "불안": 1.2,  # 우울 → 불안 (높은 확률)
                "외로움": 1.15,
                "슬픔": 1.1,
                "기쁨": 0.7,  # 우울 → 기쁨 (낮은 확률)
                "분노": 0.9
            },
            "불안": {
                "우울": 1.2,
                "스트레스": 1.15,
                "두려움": 1.1,
                "기쁨": 0.8,
                "분노": 1.05
            },
            "분노": {
                "후회": 1.15,
                "불안": 1.1,
                "우울": 1.05,
                "기쁨": 0.7,
                "슬픔": 1.0
            },
            "기쁨": {
                "만족": 1.1,
                "행복": 1.15,
                "우울": 0.6,  # 기쁨 → 우울 (낮은 확률)
                "슬픔": 0.7,
                "불안": 0.8
            },
            "슬픔": {
                "우울": 1.2,
                "외로움": 1.15,
                "아쉬움": 1.1,
                "기쁨": 0.7,
                "불안": 1.05
            }
        }
        
        # 전이 확률 적용
        adjusted_emotions = emotions.copy()
        if last_emotion in transition_matrix:
            transitions = transition_matrix[last_emotion]
            for emotion, score in adjusted_emotions.items():
                if emotion in transitions:
                    # 전이 확률에 따라 점수 조정
                    multiplier = transitions[emotion]
                    adjusted_emotions[emotion] = min(1.0, score * multiplier)
        
        return adjusted_emotions

    def _analyze_with_llm(
        self, 
        text: str, 
        keyword_emotions: Dict[str, float],
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, float]:
        """
        LLM을 사용한 감정 분석 (하이브리드 방식 - 고도화)
        
        Args:
            text: 입력 텍스트
            keyword_emotions: 키워드 매칭 결과 (참고용)
            conversation_history: 대화 히스토리 (컨텍스트용)
            
        Returns:
            LLM 분석 결과 감정 점수
        """
        try:
            # LLM 프롬프트 구성 (고도화: Few-shot + Chain-of-Thought)
            emotion_list = list(set(list(self.emotion_expressions.keys()) + list(self.korean_specific_emotions.keys())))
            emotion_list_str = ", ".join(emotion_list)
            
            # 대화 히스토리 컨텍스트 구성
            context_text = ""
            if conversation_history and len(conversation_history) > 0:
                recent_history = conversation_history[-5:]  # 최근 5턴
                context_text = "\n\n[대화 맥락]\n"
                for msg in recent_history:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")[:100]  # 최대 100자
                    context_text += f"{'사용자' if role == 'user' else '상담사'}: {content}\n"
            
            prompt = f"""당신은 한국어 감정 분석 전문가입니다. 다음 단계를 따라 정확하게 감정을 분석해주세요.

## 분석 단계 (Chain-of-Thought)

### 1단계: 부정문/반어법 감지
- 부정문: "기쁘지 않아요", "슬프지 않아요" → 해당 감정이 아님
- 반어법: "좋아 죽겠네", "행복하네요" (비꼬는 톤) → 분노/불만
- 이중 부정: "안 좋지 않아요" → 긍정

### 2단계: 문맥 분석
- 신체 증상: "가슴이 답답해요" → 불안/우울
- 상황 맥락: "답답하다" (상황에 대한) → 분노
- 은유 표현: "마음이 무겁다" → 우울, "마음이 가볍다" → 기쁨

### 3단계: 복합 감정 인식
- 여러 감정이 동시에 존재할 수 있음
- 주요 감정과 부가 감정 구분

## 예시 (Few-shot Learning)

예시 1:
텍스트: "요즘들어 가슴이 답답해요"
분석:
1. 부정문/반어법: 없음
2. 문맥: "가슴이 답답해요" → 신체 증상 → 불안/우울
3. 복합 감정: 불안(주요), 우울(부가)
결과: {{"primary_emotion": "불안", "intensity": 7, "secondary_emotions": ["우울"], "confidence": 0.9, "reasoning": "신체적 답답함은 불안/우울의 증상"}}

예시 2:
텍스트: "기쁘지 않아요"
분석:
1. 부정문: "기쁘지 않아요" → 기쁨이 아님
2. 문맥: 부정문이므로 기쁨 점수 0
3. 복합 감정: 중립 또는 다른 감정
결과: {{"primary_emotion": "중립", "intensity": 3, "secondary_emotions": [], "confidence": 0.8, "reasoning": "부정문으로 인해 기쁨이 아님"}}

예시 3:
텍스트: "좋아 죽겠네"
분석:
1. 반어법: "좋아 죽겠네" → 비꼬는 표현 → 분노/불만
2. 문맥: 반어법이므로 긍정이 아님
3. 복합 감정: 분노(주요), 불만(부가)
결과: {{"primary_emotion": "분노", "intensity": 6, "secondary_emotions": ["불만"], "confidence": 0.85, "reasoning": "반어법으로 분노 표현"}}

## 실제 분석 대상

텍스트: "{text}"
{context_text}
가능한 감정: {emotion_list_str}

위의 3단계 분석 과정을 거쳐 다음 형식으로 JSON 응답해주세요:
{{
    "primary_emotion": "주요 감정",
    "intensity": 1-10 사이의 숫자,
    "secondary_emotions": ["부가 감정1", "부가 감정2"],
    "confidence": 0.0-1.0 사이의 숫자,
    "reasoning": "분석 과정 요약 (1-2문장)"
}}

중요:
- 반드시 JSON 형식만 응답하세요 (추가 설명 없이)
- 부정문, 반어법, 은유를 정확히 인식하세요
- 대화 맥락을 고려하세요
"""
            
            # LLM 호출
            if hasattr(self.llm_adapter, 'generate_response'):
                response = self.llm_adapter.generate_response(prompt, [])
            elif hasattr(self.llm_adapter, 'chat'):
                response = self.llm_adapter.chat(prompt)
            else:
                logger.warning("LLM adapter does not support required methods")
                return {}
            
            # JSON 파싱 (개선: 중첩 JSON 지원)
            import json
            # 응답에서 JSON 추출 (중첩 객체 지원)
            # 여러 시도: 1) 전체 텍스트에서 JSON 찾기, 2) ```json 블록 찾기, 3) 첫 번째 { } 블록 찾기
            llm_result = None
            
            # 방법 1: ```json 코드 블록에서 추출
            json_block_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_block_match:
                try:
                    llm_result = json.loads(json_block_match.group(1))
                except json.JSONDecodeError:
                    pass
            
            # 방법 2: 첫 번째 완전한 JSON 객체 찾기 (중첩 지원)
            if not llm_result:
                brace_count = 0
                start_idx = response.find('{')
                if start_idx != -1:
                    for i in range(start_idx, len(response)):
                        if response[i] == '{':
                            brace_count += 1
                        elif response[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                json_str = response[start_idx:i+1]
                                try:
                                    llm_result = json.loads(json_str)
                                    break
                                except json.JSONDecodeError:
                                    pass
            
            if llm_result:
                
                # 감정 점수 딕셔너리로 변환
                llm_emotions = {}
                primary = llm_result.get("primary_emotion", "")
                intensity = llm_result.get("intensity", 5.0) / 10.0  # 1-10을 0-1로 정규화
                confidence = llm_result.get("confidence", 0.5)
                
                if primary:
                    llm_emotions[primary] = intensity * confidence
                
                # 부가 감정도 추가
                for sec_emotion in llm_result.get("secondary_emotions", []):
                    if sec_emotion not in llm_emotions:
                        llm_emotions[sec_emotion] = intensity * confidence * 0.5
                
                logger.debug(f"LLM emotion analysis: {llm_result.get('reasoning', 'N/A')}")
                return llm_emotions
            else:
                logger.warning("Failed to parse LLM response as JSON")
                return {}
                
        except Exception as e:
            logger.warning(f"LLM emotion analysis failed: {e}, falling back to keyword matching")
            return {}

    def _merge_emotion_scores(
        self, 
        keyword_emotions: Dict[str, float], 
        llm_emotions: Dict[str, float],
        keyword_weight: float = 0.4,
        llm_weight: float = 0.6
    ) -> Dict[str, float]:
        """
        키워드 매칭 결과와 LLM 결과를 결합
        
        Args:
            keyword_emotions: 키워드 매칭 결과
            llm_emotions: LLM 분석 결과
            keyword_weight: 키워드 결과 가중치
            llm_weight: LLM 결과 가중치
            
        Returns:
            결합된 감정 점수
        """
        merged = {}
        
        # 모든 감정 키 수집
        all_emotions = set(list(keyword_emotions.keys()) + list(llm_emotions.keys()))
        
        for emotion in all_emotions:
            keyword_score = keyword_emotions.get(emotion, 0.0)
            llm_score = llm_emotions.get(emotion, 0.0)
            
            # 가중 평균
            merged[emotion] = (keyword_score * keyword_weight) + (llm_score * llm_weight)
        
        return merged

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
        all_emotions: Dict[str, float],
        conversation_history: Optional[List[Dict]] = None
    ) -> float:
        """
        감정 강도 측정 (1-10 척도) - 고도화 버전
        
        문맥 기반 강도 조정 및 상대적 강도 비교 포함

        Args:
            text: 입력 텍스트
            primary_emotion: 주요 감정
            all_emotions: 모든 감정 점수
            conversation_history: 대화 히스토리 (상대적 강도 비교용)

        Returns:
            float: 강도 (1-10)

        예시:
            >>> analyzer._measure_intensity("너무너무 화나요!!!", "분노", {...})
            9.2
        """
        # 기본 강도 계산
        base_intensity = 5.0

        # 1. 주요 감정의 점수 반영 (개선: 비선형 변환)
        if primary_emotion in all_emotions:
            emotion_score = all_emotions[primary_emotion]
            # 비선형 변환: 낮은 점수는 약하게, 높은 점수는 강하게 반영
            if emotion_score < 0.5:
                intensity_boost = emotion_score * 2.0  # 최대 +1
            else:
                intensity_boost = 1.0 + (emotion_score - 0.5) * 4.0  # 0.5 이상은 강하게
            base_intensity += intensity_boost

        # 2. 텍스트 기반 증폭 요소 (확장)
        text_amplifiers = 0.0

        # 2-1. 강조 부사 (확장)
        emphasis_patterns = {
            "극도로|극심|극히|극렬": 2.5,
            "너무너무|정말정말|진짜진짜|완전완전": 2.0,
            "너무|정말|진짜|완전|엄청|대단히": 1.5,
            "매우|굉장히|심하게|몹시|아주": 1.0,
            "꽤|상당히|제법": 0.5,
            "조금|약간|살짝|좀": -0.8,
            "거의|대부분": 0.3
        }

        for pattern, boost in emphasis_patterns.items():
            if re.search(pattern, text):
                text_amplifiers += boost
                break  # 첫 번째 매칭만 사용

        # 2-2. 느낌표 (개선: 연속 사용 감지)
        exclamation_count = text.count("!")
        if exclamation_count >= 3:
            text_amplifiers += 2.5  # 강한 감정 표현
        elif exclamation_count >= 2:
            text_amplifiers += 1.5
        elif exclamation_count >= 1:
            text_amplifiers += 0.8

        # 2-3. 반복 문자 (개선: 반복 횟수에 따른 차등)
        repetition_match = re.search(r'(.)\1{3,}', text)  # 4회 이상 반복
        if repetition_match:
            text_amplifiers += 1.5
        elif re.search(r'(.)\1{2,}', text):  # 3회 반복
            text_amplifiers += 1.0

        # 2-4. 이모티콘/이모지 (개선: 감정별 차등)
        # 부정적 이모티콘
        negative_emoticons = r'ㅠㅠ|ㅜㅜ|ㅡㅡ|ㅠ|ㅜ'
        if re.search(negative_emoticons, text):
            text_amplifiers += 1.0
        
        # 긍정적 이모티콘
        positive_emoticons = r'ㅎㅎ|ㅋㅋ|하하|헤헤'
        if re.search(positive_emoticons, text):
            text_amplifiers += 0.5
        
        # 이모지 (감정별)
        sad_emojis = r'[😢😭😔😞😟]'
        happy_emojis = r'[😊😄😃😁]'
        angry_emojis = r'[😠😡🤬]'
        
        if re.search(sad_emojis, text):
            text_amplifiers += 1.2
        elif re.search(angry_emojis, text):
            text_amplifiers += 1.5
        elif re.search(happy_emojis, text):
            text_amplifiers += 0.8

        # 2-5. 부정 표현 (강도 증폭) - 확장
        negation_patterns = {
            "견딜 수 없|참을 수 없": 2.0,
            "도저히|도무지|절대": 1.5,
            "못 견디겠|버틸 수 없": 1.8,
            "한계|끝": 1.2
        }
        
        for pattern, boost in negation_patterns.items():
            if re.search(pattern, text):
                text_amplifiers += boost
                break

        # 2-6. 극단적 표현 (확장)
        extreme_patterns = {
            "죽겠|죽을 것 같": 2.0,
            "미치겠|미칠 것 같": 1.8,
            "터질 것 같|폭발": 1.5,
            "끝장|망했": 1.8,
            "살 수 없|생존 불가": 2.0
        }
        
        for pattern, boost in extreme_patterns.items():
            if re.search(pattern, text):
                text_amplifiers += boost
                break

        # 3. 문맥 기반 강도 조정 (신규)
        context_adjustment = 0.0
        
        # 3-1. 대화 히스토리 기반 상대적 강도
        if conversation_history and len(conversation_history) > 0:
            # 최근 대화의 감정 강도 추출
            recent_intensities = []
            for record in list(self.emotion_history)[-5:]:  # 최근 5개
                if hasattr(record, 'intensity'):
                    recent_intensities.append(record.intensity)
            
            if recent_intensities:
                avg_recent_intensity = sum(recent_intensities) / len(recent_intensities)
                # 현재 강도가 평균보다 높으면 추가 보정
                if base_intensity > avg_recent_intensity + 1.0:
                    context_adjustment += 0.5  # 급격한 변화 감지
                elif base_intensity < avg_recent_intensity - 1.0:
                    context_adjustment -= 0.3  # 급격한 감소

        # 3-2. 복합 감정 보정
        significant_emotions = [e for e, s in all_emotions.items() if s > 0.4]
        if len(significant_emotions) >= 3:
            # 여러 감정이 동시에 존재하면 강도 증가 (복잡한 감정 상태)
            context_adjustment += 0.5

        # 3-3. 감정 점수 분산 기반 조정
        if len(all_emotions) > 1:
            scores = [s for s in all_emotions.values() if s > 0]
            if scores:
                score_variance = np.var(scores) if len(scores) > 1 else 0
                # 분산이 크면 (감정이 혼재) 강도 약간 감소
                if score_variance > 0.1:
                    context_adjustment -= 0.3

        # 4. 최종 강도 계산
        final_intensity = base_intensity + text_amplifiers + context_adjustment

        # 5. 정규화 및 제한
        # 최소 1, 최대 10으로 제한
        final_intensity = max(1.0, min(final_intensity, 10.0))
        
        # 소수점 첫째 자리까지 반올림
        return round(final_intensity, 1)

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

    def _detect_physical_symptoms(self, text: str) -> Dict[str, bool]:
        """
        신체적 증상 감지 (맥락 기반 감정 분석 개선)
        
        Args:
            text: 입력 텍스트
            
        Returns:
            Dict: 감지된 신체 증상
        """
        symptoms = {
            "chest_tightness": False,  # 가슴 답답함
            "headache": False,  # 두통
            "stomach": False,  # 복통/소화불량
            "fatigue": False,  # 피로
            "sleep": False  # 수면 문제
        }
        
        # 가슴 관련 증상
        chest_patterns = [
            r"가슴.*답답", r"가슴.*아프", r"가슴.*조여", r"가슴.*묵직",
            r"답답.*가슴", r"답답해요", r"답답하", r"답답함"
        ]
        for pattern in chest_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                symptoms["chest_tightness"] = True
                break
        
        # 두통
        if re.search(r"머리.*아프|두통|머리가", text, re.IGNORECASE):
            symptoms["headache"] = True
        
        # 복통/소화
        if re.search(r"배.*아프|복통|소화|속.*안.*좋", text, re.IGNORECASE):
            symptoms["stomach"] = True
        
        # 피로
        if re.search(r"피곤|피로|지치|힘들|무기력", text, re.IGNORECASE):
            symptoms["fatigue"] = True
        
        # 수면
        if re.search(r"잠.*안.*와|불면|수면|잠.*못", text, re.IGNORECASE):
            symptoms["sleep"] = True
        
        return symptoms

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
