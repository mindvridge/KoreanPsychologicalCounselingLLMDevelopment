# -*- coding: utf-8 -*-
"""
개인화 AI 모듈 (Personalization AI Module)

사용자별 응답 스타일 학습, 강화학습 기반 최적 개입 선택,
위기 상황 사전 감지를 위한 예측 모델을 제공합니다.

Author: MindVridge AI Team
Version: 1.0.0
"""

import json
import random
import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
import numpy as np

try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


# ============================================================
# Part 1: 사용자별 응답 스타일 학습
# ============================================================

class ResponseStyleDimension(Enum):
    """응답 스타일 차원"""
    LENGTH = "length"                   # 응답 길이 선호
    FORMALITY = "formality"             # 격식체/비격식체
    DIRECTNESS = "directness"           # 직접적/간접적
    EMOTION_EXPRESSION = "emotion"      # 감정 표현 스타일
    DETAIL_LEVEL = "detail"             # 세부사항 수준
    METAPHOR_USE = "metaphor"           # 비유/은유 사용
    QUESTION_STYLE = "question"         # 질문 스타일
    PACE = "pace"                       # 대화 속도


@dataclass
class UserStyleProfile:
    """사용자 스타일 프로필"""
    user_id: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # 스타일 선호도 (0-1 스케일)
    preferred_length: float = 0.5       # 0: 짧은 응답, 1: 긴 응답
    preferred_formality: float = 0.5    # 0: 비격식, 1: 격식
    preferred_directness: float = 0.5   # 0: 간접적, 1: 직접적
    emotion_expressiveness: float = 0.5 # 0: 절제된, 1: 감정적
    detail_preference: float = 0.5      # 0: 간략, 1: 상세
    metaphor_receptivity: float = 0.5   # 0: 직설적, 1: 비유 선호
    question_tolerance: float = 0.5     # 0: 질문 적게, 1: 질문 많이
    conversation_pace: float = 0.5      # 0: 느린 페이스, 1: 빠른 페이스

    # 특정 개입 반응성
    intervention_receptivity: Dict[str, float] = field(default_factory=dict)

    # 통계
    total_interactions: int = 0
    positive_feedback_count: int = 0
    negative_feedback_count: int = 0

    # 학습 신뢰도
    confidence: float = 0.0             # 프로필 신뢰도 (0-1)


@dataclass
class InteractionFeedback:
    """상호작용 피드백"""
    interaction_id: str
    user_id: str
    timestamp: datetime
    response_style: Dict[str, float]    # 응답의 스타일 특성
    user_engagement: float              # 사용자 참여도 (0-1)
    explicit_feedback: Optional[int]    # 명시적 피드백 (1-5)
    implicit_signals: Dict[str, Any]    # 암묵적 신호


class UserStyleLearner:
    """사용자 스타일 학습기"""

    def __init__(self, learning_rate: float = 0.1, decay_factor: float = 0.95):
        self.learning_rate = learning_rate
        self.decay_factor = decay_factor
        self.user_profiles: Dict[str, UserStyleProfile] = {}
        self.interaction_history: Dict[str, List[InteractionFeedback]] = defaultdict(list)

    def get_or_create_profile(self, user_id: str) -> UserStyleProfile:
        """사용자 프로필 가져오기 또는 생성"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserStyleProfile(user_id=user_id)
        return self.user_profiles[user_id]

    def analyze_user_message(self, message: str) -> Dict[str, float]:
        """사용자 메시지에서 스타일 선호 추출"""
        features = {}

        # 메시지 길이로 선호 추정
        word_count = len(message.split())
        features['length_preference'] = min(word_count / 50, 1.0)

        # 격식체 사용 여부
        formal_endings = ['습니다', '합니다', '입니다', '니까', '시오']
        informal_endings = ['어', '야', '네', '지', '거든']
        formal_count = sum(1 for e in formal_endings if e in message)
        informal_count = sum(1 for e in informal_endings if e in message)
        if formal_count + informal_count > 0:
            features['formality'] = formal_count / (formal_count + informal_count)
        else:
            features['formality'] = 0.5

        # 감정 표현 정도
        emotion_words = ['정말', '너무', '진짜', '완전', '매우', '많이', '!']
        emotion_count = sum(1 for w in emotion_words if w in message)
        features['emotion_expression'] = min(emotion_count / 5, 1.0)

        # 세부사항 수준
        detail_indicators = [',', '그리고', '또한', '왜냐하면', '예를 들어']
        detail_count = sum(1 for d in detail_indicators if d in message)
        features['detail_level'] = min(detail_count / 3, 1.0)

        # 질문 사용
        question_count = message.count('?')
        features['question_style'] = min(question_count / 3, 1.0)

        return features

    def analyze_response_engagement(
        self,
        user_response: str,
        response_time_seconds: float,
        session_continued: bool
    ) -> float:
        """응답 참여도 분석"""
        engagement_score = 0.5

        # 응답 길이 기여
        word_count = len(user_response.split())
        if word_count > 20:
            engagement_score += 0.2
        elif word_count > 10:
            engagement_score += 0.1
        elif word_count < 3:
            engagement_score -= 0.1

        # 응답 시간 기여
        if response_time_seconds < 10:
            engagement_score += 0.1
        elif response_time_seconds > 60:
            engagement_score -= 0.1

        # 세션 지속 기여
        if session_continued:
            engagement_score += 0.15
        else:
            engagement_score -= 0.1

        # 부정적 표현 체크
        negative_indicators = ['네', '응', '그래', '음']  # 짧은 대답
        if user_response.strip() in negative_indicators:
            engagement_score -= 0.15

        return max(0, min(1, engagement_score))

    def update_profile(
        self,
        user_id: str,
        feedback: InteractionFeedback
    ):
        """피드백 기반 프로필 업데이트"""
        profile = self.get_or_create_profile(user_id)

        # 명시적 피드백 반영
        if feedback.explicit_feedback:
            feedback_weight = (feedback.explicit_feedback - 3) / 2  # -1 to 1
        else:
            feedback_weight = (feedback.user_engagement - 0.5) * 2  # -1 to 1

        # 각 차원 업데이트
        style = feedback.response_style

        if 'length' in style:
            profile.preferred_length = self._update_value(
                profile.preferred_length,
                style['length'],
                feedback_weight
            )

        if 'formality' in style:
            profile.preferred_formality = self._update_value(
                profile.preferred_formality,
                style['formality'],
                feedback_weight
            )

        if 'directness' in style:
            profile.preferred_directness = self._update_value(
                profile.preferred_directness,
                style['directness'],
                feedback_weight
            )

        if 'emotion' in style:
            profile.emotion_expressiveness = self._update_value(
                profile.emotion_expressiveness,
                style['emotion'],
                feedback_weight
            )

        # 통계 업데이트
        profile.total_interactions += 1
        if feedback_weight > 0:
            profile.positive_feedback_count += 1
        else:
            profile.negative_feedback_count += 1

        # 신뢰도 업데이트
        profile.confidence = min(profile.total_interactions / 50, 1.0)
        profile.updated_at = datetime.now()

        # 히스토리 저장
        self.interaction_history[user_id].append(feedback)

    def _update_value(
        self,
        current: float,
        observed: float,
        feedback_weight: float
    ) -> float:
        """값 업데이트 (가중 이동 평균)"""
        if feedback_weight > 0:
            # 긍정적 피드백: 관찰된 값 방향으로 이동
            delta = (observed - current) * self.learning_rate * feedback_weight
        else:
            # 부정적 피드백: 반대 방향으로 이동
            delta = (current - observed) * self.learning_rate * abs(feedback_weight) * 0.5

        new_value = current + delta
        return max(0, min(1, new_value))

    def generate_style_parameters(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """응답 생성을 위한 스타일 파라미터"""
        profile = self.get_or_create_profile(user_id)

        params = {
            'target_length': 'short' if profile.preferred_length < 0.3 else 'medium' if profile.preferred_length < 0.7 else 'long',
            'formality': 'informal' if profile.preferred_formality < 0.4 else 'neutral' if profile.preferred_formality < 0.7 else 'formal',
            'directness': 'indirect' if profile.preferred_directness < 0.4 else 'balanced' if profile.preferred_directness < 0.7 else 'direct',
            'emotion_level': 'reserved' if profile.emotion_expressiveness < 0.4 else 'moderate' if profile.emotion_expressiveness < 0.7 else 'expressive',
            'detail_level': 'brief' if profile.detail_preference < 0.4 else 'moderate' if profile.detail_preference < 0.7 else 'detailed',
            'use_metaphors': profile.metaphor_receptivity > 0.5,
            'question_frequency': 'low' if profile.question_tolerance < 0.3 else 'moderate' if profile.question_tolerance < 0.7 else 'high',
            'pace': 'slow' if profile.conversation_pace < 0.4 else 'moderate' if profile.conversation_pace < 0.7 else 'fast',
            'confidence': profile.confidence
        }

        return params


# ============================================================
# Part 2: 강화학습 기반 최적 개입 선택
# ============================================================

class InterventionType(Enum):
    """개입 유형"""
    BREATHING = "breathing"
    GROUNDING = "grounding"
    CBT = "cbt"
    JOURNALING = "journaling"
    MINDFULNESS = "mindfulness"
    BEHAVIORAL_ACTIVATION = "behavioral_activation"
    MUSIC = "music"
    ART = "art"
    VALIDATION = "validation"
    PSYCHOEDUCATION = "psychoeducation"
    PROBLEM_SOLVING = "problem_solving"
    SOCIAL_SUPPORT = "social_support"


@dataclass
class State:
    """환경 상태"""
    emotion_state: str          # 현재 감정 상태
    emotion_intensity: float    # 감정 강도 (0-1)
    stress_level: float         # 스트레스 수준 (0-1)
    session_duration: int       # 세션 시간 (분)
    turn_count: int             # 대화 턴 수
    recent_interventions: List[str]  # 최근 개입들
    time_of_day: str            # 시간대
    user_engagement: float      # 사용자 참여도


@dataclass
class ActionResult:
    """행동 결과"""
    intervention: InterventionType
    accepted: bool              # 사용자가 수용했는지
    completed: bool             # 완료했는지
    emotion_change: float       # 감정 변화 (-1 ~ 1)
    engagement_change: float    # 참여도 변화
    user_feedback: Optional[int]  # 명시적 피드백 (1-5)


class QLearningInterventionSelector:
    """Q-러닝 기반 개입 선택기"""

    def __init__(
        self,
        learning_rate: float = 0.1,
        discount_factor: float = 0.95,
        exploration_rate: float = 0.2,
        exploration_decay: float = 0.995
    ):
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exploration_rate = exploration_rate
        self.exploration_decay = exploration_decay
        self.min_exploration = 0.05

        # Q-테이블 초기화
        self.q_table: Dict[str, Dict[str, float]] = defaultdict(
            lambda: defaultdict(float)
        )

        # 행동 공간
        self.actions = list(InterventionType)

        # 학습 통계
        self.episode_count = 0
        self.total_reward = 0.0

    def _state_to_key(self, state: State) -> str:
        """상태를 키로 변환"""
        # 이산화된 상태 표현
        emotion_bucket = state.emotion_state
        intensity_bucket = 'low' if state.emotion_intensity < 0.3 else 'medium' if state.emotion_intensity < 0.7 else 'high'
        stress_bucket = 'low' if state.stress_level < 0.3 else 'medium' if state.stress_level < 0.7 else 'high'
        engagement_bucket = 'low' if state.user_engagement < 0.4 else 'high'

        return f"{emotion_bucket}_{intensity_bucket}_{stress_bucket}_{engagement_bucket}"

    def select_action(
        self,
        state: State,
        excluded_actions: Optional[List[InterventionType]] = None
    ) -> InterventionType:
        """
        ε-greedy 정책으로 행동 선택

        Args:
            state: 현재 상태
            excluded_actions: 제외할 행동들

        Returns:
            선택된 개입 유형
        """
        available_actions = [a for a in self.actions if a not in (excluded_actions or [])]

        if random.random() < self.exploration_rate:
            # 탐색: 랜덤 선택
            return random.choice(available_actions)
        else:
            # 활용: Q값이 가장 높은 행동 선택
            state_key = self._state_to_key(state)
            q_values = {a: self.q_table[state_key][a.value] for a in available_actions}

            # 최대 Q값을 가진 행동들 중 랜덤 선택 (타이 브레이킹)
            max_q = max(q_values.values())
            best_actions = [a for a, q in q_values.items() if q == max_q]

            return random.choice(best_actions)

    def calculate_reward(self, result: ActionResult) -> float:
        """보상 계산"""
        reward = 0.0

        # 수용 보상
        if result.accepted:
            reward += 0.3
        else:
            reward -= 0.2

        # 완료 보상
        if result.completed:
            reward += 0.4

        # 감정 변화 보상
        reward += result.emotion_change * 0.5

        # 참여도 변화 보상
        reward += result.engagement_change * 0.3

        # 명시적 피드백 보상
        if result.user_feedback:
            feedback_reward = (result.user_feedback - 3) / 2  # -1 to 1
            reward += feedback_reward * 0.5

        return reward

    def update(
        self,
        state: State,
        action: InterventionType,
        reward: float,
        next_state: State
    ):
        """Q-값 업데이트"""
        state_key = self._state_to_key(state)
        next_state_key = self._state_to_key(next_state)

        # 현재 Q값
        current_q = self.q_table[state_key][action.value]

        # 다음 상태의 최대 Q값
        next_max_q = max(
            self.q_table[next_state_key].values()
        ) if self.q_table[next_state_key] else 0

        # Q-러닝 업데이트
        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * next_max_q - current_q
        )

        self.q_table[state_key][action.value] = new_q

        # 탐색률 감소
        self.exploration_rate = max(
            self.min_exploration,
            self.exploration_rate * self.exploration_decay
        )

        self.episode_count += 1
        self.total_reward += reward

    def get_best_interventions(
        self,
        state: State,
        top_k: int = 3
    ) -> List[Tuple[InterventionType, float]]:
        """상위 k개 개입 추천"""
        state_key = self._state_to_key(state)
        q_values = [(a, self.q_table[state_key][a.value]) for a in self.actions]
        q_values.sort(key=lambda x: x[1], reverse=True)

        return q_values[:top_k]


class ContextualBanditSelector:
    """컨텍스트 밴딧 기반 개입 선택기"""

    def __init__(self, feature_dim: int = 10, n_arms: int = 12):
        self.feature_dim = feature_dim
        self.n_arms = n_arms
        self.arms = list(InterventionType)

        # UCB1 파라미터
        self.counts = np.zeros(n_arms)
        self.values = np.zeros(n_arms)

        # 컨텍스트별 가중치 (LinUCB)
        if SKLEARN_AVAILABLE:
            self.A = [np.eye(feature_dim) for _ in range(n_arms)]
            self.b = [np.zeros(feature_dim) for _ in range(n_arms)]
            self.alpha = 0.5  # 탐색 파라미터

    def _state_to_features(self, state: State) -> np.ndarray:
        """상태를 특성 벡터로 변환"""
        # 감정 상태 인코딩
        emotion_map = {
            'anxiety': [1, 0, 0, 0, 0],
            'depression': [0, 1, 0, 0, 0],
            'anger': [0, 0, 1, 0, 0],
            'sadness': [0, 0, 0, 1, 0],
            'neutral': [0, 0, 0, 0, 1]
        }
        emotion_vec = emotion_map.get(state.emotion_state, [0, 0, 0, 0, 1])

        features = np.array(
            emotion_vec +
            [
                state.emotion_intensity,
                state.stress_level,
                state.session_duration / 60,  # 정규화
                state.turn_count / 20,        # 정규화
                state.user_engagement
            ]
        )

        return features

    def select_action(self, state: State) -> InterventionType:
        """LinUCB로 행동 선택"""
        if not SKLEARN_AVAILABLE:
            return random.choice(self.arms)

        features = self._state_to_features(state)
        ucb_values = []

        for arm_idx in range(self.n_arms):
            A_inv = np.linalg.inv(self.A[arm_idx])
            theta = A_inv @ self.b[arm_idx]

            # UCB 값 계산
            mean = features @ theta
            uncertainty = self.alpha * np.sqrt(features @ A_inv @ features)
            ucb = mean + uncertainty

            ucb_values.append(ucb)

        best_arm_idx = np.argmax(ucb_values)
        return self.arms[best_arm_idx]

    def update(
        self,
        state: State,
        action: InterventionType,
        reward: float
    ):
        """LinUCB 파라미터 업데이트"""
        if not SKLEARN_AVAILABLE:
            return

        features = self._state_to_features(state)
        arm_idx = self.arms.index(action)

        self.A[arm_idx] += np.outer(features, features)
        self.b[arm_idx] += reward * features

        self.counts[arm_idx] += 1
        self.values[arm_idx] += (reward - self.values[arm_idx]) / self.counts[arm_idx]


# ============================================================
# Part 3: 위기 상황 사전 감지 예측 모델
# ============================================================

@dataclass
class CrisisRiskFeatures:
    """위기 위험 특성"""
    # 텍스트 특성
    suicidal_ideation_mentions: int
    hopelessness_score: float
    social_isolation_indicators: int
    sleep_disturbance_mentions: int
    substance_use_mentions: int

    # 행동 특성
    response_latency_change: float      # 응답 시간 변화
    message_length_change: float        # 메시지 길이 변화
    engagement_decline: float           # 참여도 하락
    session_frequency_change: float     # 세션 빈도 변화

    # 감정 특성
    emotion_volatility: float           # 감정 변동성
    negative_emotion_trend: float       # 부정 감정 추세
    anhedonia_indicators: int           # 무쾌감증 지표

    # 시간 특성
    time_since_last_session: float      # 마지막 세션 이후 시간
    unusual_session_time: bool          # 비정상 시간대

    # 이력 특성
    previous_crisis_history: bool
    days_since_last_crisis: Optional[int]


class CrisisRiskLevel(Enum):
    """위기 위험 수준"""
    LOW = 1
    MODERATE = 2
    HIGH = 3
    IMMINENT = 4


@dataclass
class CrisisPrediction:
    """위기 예측 결과"""
    risk_level: CrisisRiskLevel
    risk_score: float                   # 0-1
    confidence: float                   # 예측 신뢰도
    risk_factors: List[str]             # 주요 위험 요인
    protective_factors: List[str]       # 보호 요인
    recommended_actions: List[str]      # 권장 조치
    time_horizon: str                   # 위험 시간대


class CrisisPredictionModel:
    """위기 예측 모델"""

    def __init__(self):
        self.risk_keywords = {
            'suicidal': ['죽고 싶', '자살', '사라지고 싶', '없어지고 싶', '끝내고 싶',
                        '삶을 끝', '더 이상 못', '살고 싶지 않'],
            'hopelessness': ['희망이 없', '의미가 없', '미래가 없', '변하지 않',
                            '영원히', '절대 안 될', '불가능'],
            'isolation': ['혼자', '외로', '아무도', '고립', '관계 단절', '친구 없'],
            'sleep': ['잠이 안', '불면', '악몽', '새벽에 깨', '잠을 못'],
            'substance': ['술', '약', '마약', '담배', '취해', '끊을 수 없']
        }

        self.protective_keywords = [
            '가족', '친구', '희망', '목표', '계획', '좋아하는',
            '기대', '약속', '치료', '상담'
        ]

        # ML 모델 (있는 경우)
        self.ml_model = None
        self.scaler = None
        if SKLEARN_AVAILABLE:
            self.ml_model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                random_state=42
            )
            self.scaler = StandardScaler()

        self.is_trained = False

    def extract_features(
        self,
        current_message: str,
        conversation_history: List[Dict],
        user_profile: Optional[Dict] = None
    ) -> CrisisRiskFeatures:
        """위기 위험 특성 추출"""
        message_lower = current_message.lower()

        # 텍스트 특성
        suicidal_count = sum(
            1 for kw in self.risk_keywords['suicidal'] if kw in message_lower
        )
        hopelessness_score = sum(
            1 for kw in self.risk_keywords['hopelessness'] if kw in message_lower
        ) / len(self.risk_keywords['hopelessness'])
        isolation_count = sum(
            1 for kw in self.risk_keywords['isolation'] if kw in message_lower
        )
        sleep_count = sum(
            1 for kw in self.risk_keywords['sleep'] if kw in message_lower
        )
        substance_count = sum(
            1 for kw in self.risk_keywords['substance'] if kw in message_lower
        )

        # 행동 특성 분석
        if len(conversation_history) >= 3:
            recent_msgs = [h.get('content', '') for h in conversation_history[-5:] if h.get('role') == 'user']

            # 메시지 길이 변화
            lengths = [len(m) for m in recent_msgs]
            if len(lengths) >= 2:
                length_change = (lengths[-1] - np.mean(lengths[:-1])) / (np.mean(lengths[:-1]) + 1)
            else:
                length_change = 0.0

            # 부정적 감정 추세
            negative_words = ['힘들', '슬프', '우울', '불안', '화나', '지쳤']
            negative_counts = [
                sum(1 for w in negative_words if w in m.lower())
                for m in recent_msgs
            ]
            if len(negative_counts) >= 2:
                negative_trend = (negative_counts[-1] - np.mean(negative_counts[:-1])) / (np.mean(negative_counts[:-1]) + 1)
            else:
                negative_trend = 0.0

            # 감정 변동성
            emotion_volatility = np.std(negative_counts) if len(negative_counts) > 1 else 0.0
        else:
            length_change = 0.0
            negative_trend = 0.0
            emotion_volatility = 0.0

        # 시간 특성
        current_hour = datetime.now().hour
        unusual_time = current_hour >= 0 and current_hour <= 5  # 심야/새벽

        # 사용자 이력
        previous_crisis = False
        days_since_crisis = None
        if user_profile:
            previous_crisis = user_profile.get('previous_crisis', False)
            last_crisis = user_profile.get('last_crisis_date')
            if last_crisis:
                days_since_crisis = (datetime.now() - last_crisis).days

        return CrisisRiskFeatures(
            suicidal_ideation_mentions=suicidal_count,
            hopelessness_score=hopelessness_score,
            social_isolation_indicators=isolation_count,
            sleep_disturbance_mentions=sleep_count,
            substance_use_mentions=substance_count,
            response_latency_change=0.0,  # 실시간 분석 시 계산
            message_length_change=length_change,
            engagement_decline=0.0,  # 실시간 분석 시 계산
            session_frequency_change=0.0,  # 실시간 분석 시 계산
            emotion_volatility=emotion_volatility,
            negative_emotion_trend=negative_trend,
            anhedonia_indicators=0,  # 별도 분석 필요
            time_since_last_session=0.0,  # 실시간 분석 시 계산
            unusual_session_time=unusual_time,
            previous_crisis_history=previous_crisis,
            days_since_last_crisis=days_since_crisis
        )

    def predict(
        self,
        features: CrisisRiskFeatures
    ) -> CrisisPrediction:
        """위기 위험 예측"""
        # 규칙 기반 스코어링
        risk_score = 0.0
        risk_factors = []
        protective_factors = []

        # 자살 관련 언급 (높은 가중치)
        if features.suicidal_ideation_mentions > 0:
            risk_score += 0.4 * min(features.suicidal_ideation_mentions, 3)
            risk_factors.append(f"자살 관련 언급 {features.suicidal_ideation_mentions}회")

        # 절망감
        if features.hopelessness_score > 0.3:
            risk_score += 0.2 * features.hopelessness_score
            risk_factors.append("높은 절망감 표현")

        # 사회적 고립
        if features.social_isolation_indicators >= 2:
            risk_score += 0.15
            risk_factors.append("사회적 고립 징후")

        # 수면 문제
        if features.sleep_disturbance_mentions >= 2:
            risk_score += 0.1
            risk_factors.append("수면 장애 언급")

        # 물질 사용
        if features.substance_use_mentions >= 1:
            risk_score += 0.1
            risk_factors.append("물질 사용 언급")

        # 감정 악화 추세
        if features.negative_emotion_trend > 0.5:
            risk_score += 0.15
            risk_factors.append("부정적 감정 증가 추세")

        # 감정 변동성
        if features.emotion_volatility > 1.5:
            risk_score += 0.1
            risk_factors.append("높은 감정 변동성")

        # 비정상 시간대
        if features.unusual_session_time:
            risk_score += 0.05
            risk_factors.append("심야/새벽 시간대 접속")

        # 위기 이력
        if features.previous_crisis_history:
            risk_score += 0.1
            risk_factors.append("과거 위기 이력")
            if features.days_since_last_crisis and features.days_since_last_crisis < 30:
                risk_score += 0.1
                risk_factors.append("최근 위기 경험 (30일 이내)")

        # 정규화
        risk_score = min(risk_score, 1.0)

        # 위험 수준 결정
        if risk_score >= 0.7:
            risk_level = CrisisRiskLevel.IMMINENT
        elif risk_score >= 0.5:
            risk_level = CrisisRiskLevel.HIGH
        elif risk_score >= 0.3:
            risk_level = CrisisRiskLevel.MODERATE
        else:
            risk_level = CrisisRiskLevel.LOW

        # 권장 조치
        recommended_actions = self._get_recommendations(risk_level, risk_factors)

        # 시간대 예측
        if risk_level == CrisisRiskLevel.IMMINENT:
            time_horizon = "즉시 (24시간 이내)"
        elif risk_level == CrisisRiskLevel.HIGH:
            time_horizon = "단기 (1주일 이내)"
        elif risk_level == CrisisRiskLevel.MODERATE:
            time_horizon = "중기 (1개월 이내)"
        else:
            time_horizon = "장기적 모니터링"

        return CrisisPrediction(
            risk_level=risk_level,
            risk_score=risk_score,
            confidence=0.7 + 0.3 * (len(risk_factors) / 10),  # 더 많은 요인 = 더 높은 신뢰도
            risk_factors=risk_factors,
            protective_factors=protective_factors,
            recommended_actions=recommended_actions,
            time_horizon=time_horizon
        )

    def _get_recommendations(
        self,
        risk_level: CrisisRiskLevel,
        risk_factors: List[str]
    ) -> List[str]:
        """위험 수준별 권장 조치"""
        recommendations = []

        if risk_level == CrisisRiskLevel.IMMINENT:
            recommendations = [
                "🚨 즉각적인 위기 개입 필요",
                "자살예방상담전화 안내 (1393)",
                "안전 계약 시도",
                "긴급 연락처 확인",
                "전문가 즉시 연결 권고"
            ]
        elif risk_level == CrisisRiskLevel.HIGH:
            recommendations = [
                "⚠️ 높은 위험 - 집중 모니터링",
                "위기 대응 프로토콜 준비",
                "안전 계획 수립 권고",
                "지지 자원 연결 강화",
                "다음 세션 조기 예약 권고"
            ]
        elif risk_level == CrisisRiskLevel.MODERATE:
            recommendations = [
                "중간 위험 - 정기 모니터링",
                "대처 전략 강화",
                "사회적 지지 체계 확인",
                "자기 관리 기술 교육"
            ]
        else:
            recommendations = [
                "일반적인 상담 지속",
                "예방적 개입 고려",
                "보호 요인 강화"
            ]

        return recommendations


# ============================================================
# Part 4: 통합 개인화 시스템
# ============================================================

class IntegratedPersonalizationSystem:
    """통합 개인화 시스템"""

    def __init__(self):
        # 스타일 학습기
        self.style_learner = UserStyleLearner()

        # 개입 선택기들
        self.q_learner = QLearningInterventionSelector()
        self.bandit_selector = ContextualBanditSelector()

        # 위기 예측 모델
        self.crisis_predictor = CrisisPredictionModel()

        # 사용자별 설정
        self.user_configs: Dict[str, Dict] = {}

    def process_interaction(
        self,
        user_id: str,
        user_message: str,
        bot_response: str,
        conversation_history: List[Dict],
        explicit_feedback: Optional[int] = None,
        response_time: float = 0.0,
        session_continued: bool = True
    ) -> Dict[str, Any]:
        """상호작용 처리 및 학습"""
        # 스타일 분석
        user_style = self.style_learner.analyze_user_message(user_message)
        engagement = self.style_learner.analyze_response_engagement(
            user_message, response_time, session_continued
        )

        # 피드백 생성
        feedback = InteractionFeedback(
            interaction_id=f"{user_id}_{datetime.now().timestamp()}",
            user_id=user_id,
            timestamp=datetime.now(),
            response_style=user_style,
            user_engagement=engagement,
            explicit_feedback=explicit_feedback,
            implicit_signals={'response_time': response_time}
        )

        # 스타일 프로필 업데이트
        self.style_learner.update_profile(user_id, feedback)

        # 위기 위험 평가
        crisis_features = self.crisis_predictor.extract_features(
            user_message,
            conversation_history,
            self.user_configs.get(user_id)
        )
        crisis_prediction = self.crisis_predictor.predict(crisis_features)

        return {
            'style_profile': self.style_learner.get_or_create_profile(user_id),
            'engagement': engagement,
            'crisis_prediction': crisis_prediction
        }

    def get_personalized_response_params(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """개인화된 응답 파라미터"""
        return self.style_learner.generate_style_parameters(user_id)

    def select_optimal_intervention(
        self,
        user_id: str,
        emotional_state: str,
        emotion_intensity: float,
        stress_level: float,
        session_context: Dict
    ) -> Dict[str, Any]:
        """최적 개입 선택"""
        state = State(
            emotion_state=emotional_state,
            emotion_intensity=emotion_intensity,
            stress_level=stress_level,
            session_duration=session_context.get('duration', 0),
            turn_count=session_context.get('turn_count', 0),
            recent_interventions=session_context.get('recent_interventions', []),
            time_of_day=session_context.get('time_of_day', 'day'),
            user_engagement=session_context.get('engagement', 0.5)
        )

        # Q-러닝과 밴딧 앙상블
        q_recommendations = self.q_learner.get_best_interventions(state, top_k=3)
        bandit_selection = self.bandit_selector.select_action(state)

        # 최종 선택 (Q값 가중 투표)
        intervention_scores = defaultdict(float)
        for intervention, q_value in q_recommendations:
            intervention_scores[intervention] += q_value + 0.5

        intervention_scores[bandit_selection] += 0.5

        best_intervention = max(intervention_scores.items(), key=lambda x: x[1])[0]

        return {
            'recommended_intervention': best_intervention,
            'q_recommendations': q_recommendations,
            'bandit_selection': bandit_selection,
            'confidence': intervention_scores[best_intervention] / sum(intervention_scores.values())
        }

    def update_intervention_result(
        self,
        user_id: str,
        state: State,
        action: InterventionType,
        result: ActionResult,
        next_state: State
    ):
        """개입 결과 학습"""
        reward = self.q_learner.calculate_reward(result)

        # Q-러닝 업데이트
        self.q_learner.update(state, action, reward, next_state)

        # 밴딧 업데이트
        self.bandit_selector.update(state, action, reward)

    def get_crisis_assessment(
        self,
        user_id: str,
        message: str,
        history: List[Dict]
    ) -> CrisisPrediction:
        """위기 평가"""
        features = self.crisis_predictor.extract_features(
            message, history, self.user_configs.get(user_id)
        )
        return self.crisis_predictor.predict(features)


# 사용 예시
if __name__ == "__main__":
    system = IntegratedPersonalizationSystem()

    # 스타일 학습 예시
    style_params = system.get_personalized_response_params("user_001")
    print("=== 개인화 파라미터 ===")
    print(style_params)

    # 개입 선택 예시
    intervention = system.select_optimal_intervention(
        user_id="user_001",
        emotional_state="anxiety",
        emotion_intensity=0.7,
        stress_level=0.6,
        session_context={
            'duration': 15,
            'turn_count': 10,
            'engagement': 0.6
        }
    )
    print("\n=== 추천 개입 ===")
    print(f"추천: {intervention['recommended_intervention']}")
    print(f"신뢰도: {intervention['confidence']:.2f}")

    # 위기 예측 예시
    crisis = system.get_crisis_assessment(
        "user_001",
        "요즘 너무 힘들어요... 모든 게 의미없게 느껴지고 혼자인 것 같아요",
        []
    )
    print("\n=== 위기 평가 ===")
    print(f"위험 수준: {crisis.risk_level}")
    print(f"위험 점수: {crisis.risk_score:.2f}")
    print(f"위험 요인: {crisis.risk_factors}")
    print(f"권장 조치: {crisis.recommended_actions}")
