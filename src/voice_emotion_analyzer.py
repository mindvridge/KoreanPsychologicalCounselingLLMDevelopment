# -*- coding: utf-8 -*-
"""
음성 감정 분석 모듈 (Voice Emotion Analyzer)

음성의 음높이(pitch), 속도(tempo), 떨림(tremor), 에너지 등
음향학적 특성을 분석하여 감정 상태를 추론합니다.

Author: MindVridge AI Team
Version: 1.0.0
"""

import numpy as np
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
import warnings

# 음성 처리 라이브러리 (optional imports)
try:
    import librosa
    import librosa.display
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    warnings.warn("librosa not installed. Voice analysis features limited.")

try:
    import scipy.signal as signal
    from scipy.stats import skew, kurtosis
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    import parselmouth
    from parselmouth.praat import call
    PRAAT_AVAILABLE = True
except ImportError:
    PRAAT_AVAILABLE = False
    warnings.warn("parselmouth not installed. Advanced pitch analysis limited.")


class VoiceEmotion(Enum):
    """음성 감정 유형"""
    NEUTRAL = "neutral"
    ANXIETY = "anxiety"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    JOY = "joy"
    DISGUST = "disgust"
    SURPRISE = "surprise"
    DISTRESS = "distress"
    FATIGUE = "fatigue"


class EmotionalIntensity(Enum):
    """감정 강도"""
    VERY_LOW = 1
    LOW = 2
    MODERATE = 3
    HIGH = 4
    VERY_HIGH = 5


@dataclass
class PitchFeatures:
    """음높이 특성"""
    mean_pitch: float           # 평균 음높이 (Hz)
    pitch_std: float            # 음높이 표준편차
    pitch_range: float          # 음높이 범위
    pitch_contour: str          # 음높이 윤곽 (rising, falling, flat, varied)
    jitter: float               # 음높이 떨림 (%)
    pitch_breaks: int           # 음높이 끊김 횟수


@dataclass
class TempoFeatures:
    """속도 특성"""
    speech_rate: float          # 발화 속도 (음절/초)
    articulation_rate: float    # 조음 속도 (pause 제외)
    pause_ratio: float          # 휴지 비율 (%)
    pause_count: int            # 휴지 횟수
    mean_pause_duration: float  # 평균 휴지 시간 (초)
    rhythm_regularity: float    # 리듬 규칙성 (0-1)


@dataclass
class TremorFeatures:
    """떨림 특성"""
    shimmer: float              # 진폭 떨림 (%)
    tremor_intensity: float     # 떨림 강도 (0-1)
    tremor_frequency: float     # 떨림 주파수 (Hz)
    voice_breaks: int           # 음성 끊김 횟수
    harmonics_noise_ratio: float  # 조화음/잡음 비율


@dataclass
class EnergyFeatures:
    """에너지 특성"""
    mean_energy: float          # 평균 에너지 (dB)
    energy_std: float           # 에너지 표준편차
    energy_range: float         # 에너지 범위
    energy_contour: str         # 에너지 윤곽
    loudness_variability: float # 음량 변동성


@dataclass
class SpectralFeatures:
    """스펙트럼 특성"""
    spectral_centroid: float    # 스펙트럼 중심
    spectral_bandwidth: float   # 스펙트럼 대역폭
    spectral_rolloff: float     # 스펙트럼 롤오프
    mfcc_features: List[float]  # MFCC 계수들
    formants: List[float]       # 포먼트 주파수들


@dataclass
class VoiceEmotionResult:
    """음성 감정 분석 결과"""
    primary_emotion: VoiceEmotion
    emotion_probabilities: Dict[str, float]
    intensity: EmotionalIntensity
    confidence: float

    # 세부 특성
    pitch_features: PitchFeatures
    tempo_features: TempoFeatures
    tremor_features: TremorFeatures
    energy_features: EnergyFeatures
    spectral_features: Optional[SpectralFeatures]

    # 임상적 지표
    stress_index: float         # 스트레스 지수 (0-100)
    anxiety_markers: List[str]  # 불안 마커
    depression_markers: List[str]  # 우울 마커
    crisis_indicators: List[str]   # 위기 지표

    # 메타데이터
    analysis_timestamp: datetime = field(default_factory=datetime.now)
    audio_duration: float = 0.0
    sample_rate: int = 16000


class VoiceFeatureExtractor:
    """음성 특성 추출기"""

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.frame_length = int(0.025 * sample_rate)  # 25ms
        self.hop_length = int(0.010 * sample_rate)    # 10ms

    def extract_all_features(
        self,
        audio_data: np.ndarray,
        sample_rate: Optional[int] = None
    ) -> Dict[str, Any]:
        """모든 음성 특성 추출"""
        if sample_rate is None:
            sample_rate = self.sample_rate

        features = {}

        # 음높이 특성
        features['pitch'] = self.extract_pitch_features(audio_data, sample_rate)

        # 속도 특성
        features['tempo'] = self.extract_tempo_features(audio_data, sample_rate)

        # 떨림 특성
        features['tremor'] = self.extract_tremor_features(audio_data, sample_rate)

        # 에너지 특성
        features['energy'] = self.extract_energy_features(audio_data, sample_rate)

        # 스펙트럼 특성
        if LIBROSA_AVAILABLE:
            features['spectral'] = self.extract_spectral_features(audio_data, sample_rate)

        return features

    def extract_pitch_features(
        self,
        audio_data: np.ndarray,
        sample_rate: int
    ) -> PitchFeatures:
        """음높이 특성 추출"""
        if PRAAT_AVAILABLE:
            return self._extract_pitch_praat(audio_data, sample_rate)
        elif LIBROSA_AVAILABLE:
            return self._extract_pitch_librosa(audio_data, sample_rate)
        else:
            return self._extract_pitch_basic(audio_data, sample_rate)

    def _extract_pitch_praat(
        self,
        audio_data: np.ndarray,
        sample_rate: int
    ) -> PitchFeatures:
        """Praat을 사용한 정밀 음높이 분석"""
        # numpy array를 Praat Sound 객체로 변환
        sound = parselmouth.Sound(audio_data, sampling_frequency=sample_rate)

        # Pitch 추출
        pitch = call(sound, "To Pitch", 0.0, 75, 600)

        # 기본 통계
        mean_pitch = call(pitch, "Get mean", 0, 0, "Hertz")
        pitch_std = call(pitch, "Get standard deviation", 0, 0, "Hertz")
        min_pitch = call(pitch, "Get minimum", 0, 0, "Hertz", "Parabolic")
        max_pitch = call(pitch, "Get maximum", 0, 0, "Hertz", "Parabolic")

        # NaN 처리
        mean_pitch = mean_pitch if not np.isnan(mean_pitch) else 0.0
        pitch_std = pitch_std if not np.isnan(pitch_std) else 0.0
        pitch_range = (max_pitch - min_pitch) if not (np.isnan(max_pitch) or np.isnan(min_pitch)) else 0.0

        # Jitter (음높이 떨림)
        point_process = call(sound, "To PointProcess (periodic, cc)", 75, 600)
        jitter = call(point_process, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
        jitter = jitter * 100 if not np.isnan(jitter) else 0.0

        # 음높이 윤곽 분석
        pitch_values = pitch.selected_array['frequency']
        pitch_values = pitch_values[pitch_values > 0]  # 유성음만
        contour = self._analyze_contour(pitch_values)

        # 음높이 끊김
        pitch_breaks = self._count_pitch_breaks(pitch_values)

        return PitchFeatures(
            mean_pitch=mean_pitch,
            pitch_std=pitch_std,
            pitch_range=pitch_range,
            pitch_contour=contour,
            jitter=jitter,
            pitch_breaks=pitch_breaks
        )

    def _extract_pitch_librosa(
        self,
        audio_data: np.ndarray,
        sample_rate: int
    ) -> PitchFeatures:
        """Librosa를 사용한 음높이 분석"""
        # F0 추출
        f0, voiced_flag, voiced_probs = librosa.pyin(
            audio_data,
            fmin=librosa.note_to_hz('C2'),
            fmax=librosa.note_to_hz('C7'),
            sr=sample_rate
        )

        # 유성음 부분만 추출
        f0_voiced = f0[voiced_flag]

        if len(f0_voiced) > 0:
            mean_pitch = np.nanmean(f0_voiced)
            pitch_std = np.nanstd(f0_voiced)
            pitch_range = np.nanmax(f0_voiced) - np.nanmin(f0_voiced)
        else:
            mean_pitch = 0.0
            pitch_std = 0.0
            pitch_range = 0.0

        # 윤곽 분석
        contour = self._analyze_contour(f0_voiced)

        # 간단한 jitter 계산
        if len(f0_voiced) > 1:
            jitter = np.mean(np.abs(np.diff(f0_voiced))) / mean_pitch * 100 if mean_pitch > 0 else 0
        else:
            jitter = 0.0

        pitch_breaks = self._count_pitch_breaks(f0_voiced)

        return PitchFeatures(
            mean_pitch=mean_pitch,
            pitch_std=pitch_std,
            pitch_range=pitch_range,
            pitch_contour=contour,
            jitter=jitter,
            pitch_breaks=pitch_breaks
        )

    def _extract_pitch_basic(
        self,
        audio_data: np.ndarray,
        sample_rate: int
    ) -> PitchFeatures:
        """기본 음높이 분석 (라이브러리 없이)"""
        # Zero-crossing rate 기반 대략적 추정
        zcr = np.sum(np.abs(np.diff(np.sign(audio_data)))) / (2 * len(audio_data))
        estimated_pitch = zcr * sample_rate / 2

        return PitchFeatures(
            mean_pitch=estimated_pitch,
            pitch_std=0.0,
            pitch_range=0.0,
            pitch_contour="unknown",
            jitter=0.0,
            pitch_breaks=0
        )

    def _analyze_contour(self, pitch_values: np.ndarray) -> str:
        """음높이 윤곽 분석"""
        if len(pitch_values) < 3:
            return "flat"

        # 선형 회귀로 전체 추세 파악
        x = np.arange(len(pitch_values))
        slope = np.polyfit(x, pitch_values, 1)[0]

        # 변동성 계산
        variability = np.std(pitch_values) / np.mean(pitch_values) if np.mean(pitch_values) > 0 else 0

        if variability > 0.3:
            return "varied"
        elif slope > 0.5:
            return "rising"
        elif slope < -0.5:
            return "falling"
        else:
            return "flat"

    def _count_pitch_breaks(self, pitch_values: np.ndarray) -> int:
        """음높이 끊김 횟수 계산"""
        if len(pitch_values) < 2:
            return 0

        # 급격한 변화 감지
        diff = np.abs(np.diff(pitch_values))
        threshold = np.mean(diff) + 2 * np.std(diff)
        breaks = np.sum(diff > threshold)

        return int(breaks)

    def extract_tempo_features(
        self,
        audio_data: np.ndarray,
        sample_rate: int
    ) -> TempoFeatures:
        """속도 특성 추출"""
        # 에너지 기반 음성/비음성 구간 분리
        frame_length = int(0.025 * sample_rate)
        hop_length = int(0.010 * sample_rate)

        # RMS 에너지 계산
        if LIBROSA_AVAILABLE:
            rms = librosa.feature.rms(y=audio_data, frame_length=frame_length, hop_length=hop_length)[0]
        else:
            # 간단한 RMS 계산
            frames = len(audio_data) // hop_length
            rms = np.array([
                np.sqrt(np.mean(audio_data[i*hop_length:i*hop_length+frame_length]**2))
                for i in range(frames)
            ])

        # 음성/비음성 구간 분리
        threshold = np.mean(rms) * 0.5
        is_speech = rms > threshold

        # 휴지(pause) 분석
        pause_frames = ~is_speech
        pause_regions = self._find_regions(pause_frames)

        total_duration = len(audio_data) / sample_rate
        speech_duration = np.sum(is_speech) * hop_length / sample_rate
        pause_duration = total_duration - speech_duration

        # 발화 속도 추정 (음절/초)
        # 대략적으로 한국어 평균 4-5음절/초
        # 에너지 피크 수를 음절 수로 추정
        if SCIPY_AVAILABLE:
            peaks, _ = signal.find_peaks(rms, distance=int(0.1 * sample_rate / hop_length))
            syllable_count = len(peaks)
        else:
            # 간단한 피크 카운팅
            syllable_count = np.sum(np.diff(np.sign(np.diff(rms))) < 0)

        speech_rate = syllable_count / total_duration if total_duration > 0 else 0
        articulation_rate = syllable_count / speech_duration if speech_duration > 0 else 0

        # 휴지 통계
        pause_count = len(pause_regions)
        if pause_count > 0:
            pause_durations = [(end - start) * hop_length / sample_rate
                            for start, end in pause_regions]
            mean_pause_duration = np.mean(pause_durations)
        else:
            mean_pause_duration = 0.0

        # 리듬 규칙성
        if len(rms) > 1:
            rhythm_regularity = 1.0 - min(np.std(np.diff(rms)) / np.mean(rms), 1.0) if np.mean(rms) > 0 else 0
        else:
            rhythm_regularity = 0.0

        return TempoFeatures(
            speech_rate=speech_rate,
            articulation_rate=articulation_rate,
            pause_ratio=pause_duration / total_duration * 100 if total_duration > 0 else 0,
            pause_count=pause_count,
            mean_pause_duration=mean_pause_duration,
            rhythm_regularity=rhythm_regularity
        )

    def _find_regions(self, binary_array: np.ndarray) -> List[Tuple[int, int]]:
        """연속 구간 찾기"""
        regions = []
        in_region = False
        start = 0

        for i, val in enumerate(binary_array):
            if val and not in_region:
                start = i
                in_region = True
            elif not val and in_region:
                if i - start > 3:  # 최소 30ms
                    regions.append((start, i))
                in_region = False

        if in_region:
            regions.append((start, len(binary_array)))

        return regions

    def extract_tremor_features(
        self,
        audio_data: np.ndarray,
        sample_rate: int
    ) -> TremorFeatures:
        """떨림 특성 추출"""
        if PRAAT_AVAILABLE:
            return self._extract_tremor_praat(audio_data, sample_rate)
        else:
            return self._extract_tremor_basic(audio_data, sample_rate)

    def _extract_tremor_praat(
        self,
        audio_data: np.ndarray,
        sample_rate: int
    ) -> TremorFeatures:
        """Praat을 사용한 떨림 분석"""
        sound = parselmouth.Sound(audio_data, sampling_frequency=sample_rate)

        # Point process 생성
        point_process = call(sound, "To PointProcess (periodic, cc)", 75, 600)

        # Shimmer (진폭 떨림)
        shimmer = call([sound, point_process], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
        shimmer = shimmer * 100 if not np.isnan(shimmer) else 0.0

        # HNR (Harmonics-to-Noise Ratio)
        harmonicity = call(sound, "To Harmonicity (cc)", 0.01, 75, 0.1, 1.0)
        hnr = call(harmonicity, "Get mean", 0, 0)
        hnr = hnr if not np.isnan(hnr) else 0.0

        # Voice breaks
        voice_breaks = call([sound, point_process], "Get number of voice breaks", 0, 0)

        # 떨림 강도 추정 (shimmer와 jitter 기반)
        tremor_intensity = min(shimmer / 10, 1.0)  # 정규화

        # 떨림 주파수 추정 (대략 4-8Hz가 일반적)
        tremor_frequency = self._estimate_tremor_frequency(audio_data, sample_rate)

        return TremorFeatures(
            shimmer=shimmer,
            tremor_intensity=tremor_intensity,
            tremor_frequency=tremor_frequency,
            voice_breaks=int(voice_breaks),
            harmonics_noise_ratio=hnr
        )

    def _extract_tremor_basic(
        self,
        audio_data: np.ndarray,
        sample_rate: int
    ) -> TremorFeatures:
        """기본 떨림 분석"""
        # 간단한 진폭 변동 분석
        frame_length = int(0.025 * sample_rate)
        hop_length = int(0.010 * sample_rate)

        # 프레임별 진폭
        frames = len(audio_data) // hop_length
        amplitudes = np.array([
            np.max(np.abs(audio_data[i*hop_length:i*hop_length+frame_length]))
            for i in range(frames)
        ])

        # Shimmer 추정
        if len(amplitudes) > 1:
            shimmer = np.mean(np.abs(np.diff(amplitudes))) / np.mean(amplitudes) * 100 if np.mean(amplitudes) > 0 else 0
        else:
            shimmer = 0.0

        tremor_intensity = min(shimmer / 10, 1.0)
        tremor_frequency = self._estimate_tremor_frequency(audio_data, sample_rate)

        return TremorFeatures(
            shimmer=shimmer,
            tremor_intensity=tremor_intensity,
            tremor_frequency=tremor_frequency,
            voice_breaks=0,
            harmonics_noise_ratio=0.0
        )

    def _estimate_tremor_frequency(
        self,
        audio_data: np.ndarray,
        sample_rate: int
    ) -> float:
        """떨림 주파수 추정"""
        # 저주파 대역 (1-15Hz)의 진폭 변조 분석
        if not SCIPY_AVAILABLE:
            return 5.0  # 기본값

        # 힐버트 변환으로 envelope 추출
        analytic_signal = signal.hilbert(audio_data)
        amplitude_envelope = np.abs(analytic_signal)

        # 저주파 필터링
        nyquist = sample_rate / 2
        low_freq = 1 / nyquist
        high_freq = 15 / nyquist

        if high_freq < 1:
            b, a = signal.butter(4, [low_freq, high_freq], btype='band')
            filtered_envelope = signal.filtfilt(b, a, amplitude_envelope)

            # FFT로 주파수 분석
            fft = np.fft.fft(filtered_envelope)
            freqs = np.fft.fftfreq(len(filtered_envelope), 1/sample_rate)

            # 양의 주파수만
            positive_freqs = freqs[:len(freqs)//2]
            positive_fft = np.abs(fft[:len(fft)//2])

            # 1-15Hz 범위에서 최대 피크
            mask = (positive_freqs >= 1) & (positive_freqs <= 15)
            if np.any(mask):
                tremor_freq_idx = np.argmax(positive_fft[mask])
                tremor_frequency = positive_freqs[mask][tremor_freq_idx]
                return float(tremor_frequency)

        return 5.0  # 기본값

    def extract_energy_features(
        self,
        audio_data: np.ndarray,
        sample_rate: int
    ) -> EnergyFeatures:
        """에너지 특성 추출"""
        frame_length = int(0.025 * sample_rate)
        hop_length = int(0.010 * sample_rate)

        # RMS 에너지 계산
        if LIBROSA_AVAILABLE:
            rms = librosa.feature.rms(y=audio_data, frame_length=frame_length, hop_length=hop_length)[0]
        else:
            frames = len(audio_data) // hop_length
            rms = np.array([
                np.sqrt(np.mean(audio_data[i*hop_length:i*hop_length+frame_length]**2))
                for i in range(frames)
            ])

        # dB 변환
        rms_db = 20 * np.log10(rms + 1e-10)

        mean_energy = np.mean(rms_db)
        energy_std = np.std(rms_db)
        energy_range = np.max(rms_db) - np.min(rms_db)

        # 에너지 윤곽
        contour = self._analyze_contour(rms_db)

        # 음량 변동성
        loudness_variability = energy_std / abs(mean_energy) if abs(mean_energy) > 0 else 0

        return EnergyFeatures(
            mean_energy=mean_energy,
            energy_std=energy_std,
            energy_range=energy_range,
            energy_contour=contour,
            loudness_variability=loudness_variability
        )

    def extract_spectral_features(
        self,
        audio_data: np.ndarray,
        sample_rate: int
    ) -> SpectralFeatures:
        """스펙트럼 특성 추출"""
        if not LIBROSA_AVAILABLE:
            return SpectralFeatures(
                spectral_centroid=0.0,
                spectral_bandwidth=0.0,
                spectral_rolloff=0.0,
                mfcc_features=[],
                formants=[]
            )

        # Spectral centroid
        centroid = librosa.feature.spectral_centroid(y=audio_data, sr=sample_rate)[0]

        # Spectral bandwidth
        bandwidth = librosa.feature.spectral_bandwidth(y=audio_data, sr=sample_rate)[0]

        # Spectral rolloff
        rolloff = librosa.feature.spectral_rolloff(y=audio_data, sr=sample_rate)[0]

        # MFCC
        mfccs = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=13)
        mfcc_means = np.mean(mfccs, axis=1).tolist()

        # Formants (LPC 기반 추정)
        formants = self._estimate_formants(audio_data, sample_rate)

        return SpectralFeatures(
            spectral_centroid=np.mean(centroid),
            spectral_bandwidth=np.mean(bandwidth),
            spectral_rolloff=np.mean(rolloff),
            mfcc_features=mfcc_means,
            formants=formants
        )

    def _estimate_formants(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        num_formants: int = 4
    ) -> List[float]:
        """포먼트 주파수 추정"""
        if PRAAT_AVAILABLE:
            sound = parselmouth.Sound(audio_data, sampling_frequency=sample_rate)
            formant = call(sound, "To Formant (burg)", 0.0, 5, 5500, 0.025, 50)

            formants = []
            for i in range(1, num_formants + 1):
                f = call(formant, "Get mean", i, 0, 0, "Hertz")
                formants.append(f if not np.isnan(f) else 0.0)

            return formants

        return [0.0] * num_formants


class VoiceEmotionClassifier:
    """음성 감정 분류기"""

    def __init__(self):
        # 감정별 특성 프로파일 (연구 기반 임계값)
        self.emotion_profiles = {
            VoiceEmotion.ANXIETY: {
                'pitch': {'mean': 'high', 'std': 'high', 'jitter': 'high'},
                'tempo': {'rate': 'fast', 'pause_ratio': 'low'},
                'tremor': {'shimmer': 'high', 'intensity': 'high'},
                'energy': {'mean': 'high', 'variability': 'high'}
            },
            VoiceEmotion.SADNESS: {
                'pitch': {'mean': 'low', 'std': 'low', 'contour': 'falling'},
                'tempo': {'rate': 'slow', 'pause_ratio': 'high'},
                'tremor': {'shimmer': 'moderate'},
                'energy': {'mean': 'low', 'variability': 'low'}
            },
            VoiceEmotion.ANGER: {
                'pitch': {'mean': 'high', 'std': 'high', 'range': 'wide'},
                'tempo': {'rate': 'fast'},
                'tremor': {'shimmer': 'moderate'},
                'energy': {'mean': 'high', 'variability': 'high'}
            },
            VoiceEmotion.FEAR: {
                'pitch': {'mean': 'high', 'jitter': 'high'},
                'tempo': {'rate': 'fast', 'rhythm': 'irregular'},
                'tremor': {'shimmer': 'high', 'intensity': 'high'},
                'energy': {'variability': 'high'}
            },
            VoiceEmotion.JOY: {
                'pitch': {'mean': 'high', 'std': 'high', 'contour': 'varied'},
                'tempo': {'rate': 'fast', 'rhythm': 'regular'},
                'tremor': {'shimmer': 'low'},
                'energy': {'mean': 'high'}
            },
            VoiceEmotion.FATIGUE: {
                'pitch': {'mean': 'low', 'std': 'low'},
                'tempo': {'rate': 'slow', 'pause_ratio': 'high'},
                'tremor': {'shimmer': 'moderate'},
                'energy': {'mean': 'low'}
            },
            VoiceEmotion.DISTRESS: {
                'pitch': {'mean': 'high', 'jitter': 'very_high', 'breaks': 'many'},
                'tempo': {'rate': 'irregular'},
                'tremor': {'shimmer': 'high', 'voice_breaks': 'many'},
                'energy': {'variability': 'very_high'}
            }
        }

        # 기준값 (한국어 성인 평균)
        self.reference_values = {
            'pitch_mean_male': 120,      # Hz
            'pitch_mean_female': 220,    # Hz
            'speech_rate_normal': 4.5,   # 음절/초
            'jitter_normal': 1.0,        # %
            'shimmer_normal': 3.0,       # %
            'hnr_normal': 20.0           # dB
        }

    def classify(
        self,
        features: Dict[str, Any],
        gender: str = 'unknown'
    ) -> Tuple[VoiceEmotion, Dict[str, float], float]:
        """
        음성 특성으로 감정 분류

        Returns:
            Tuple of (primary_emotion, probability_dict, confidence)
        """
        probabilities = {}

        for emotion in VoiceEmotion:
            if emotion in self.emotion_profiles:
                prob = self._calculate_emotion_probability(
                    features, emotion, gender
                )
            else:
                prob = 0.1  # 기본 확률
            probabilities[emotion.value] = prob

        # 정규화
        total = sum(probabilities.values())
        if total > 0:
            probabilities = {k: v/total for k, v in probabilities.items()}

        # 최고 확률 감정
        primary_emotion = VoiceEmotion(max(probabilities, key=probabilities.get))
        confidence = max(probabilities.values())

        return primary_emotion, probabilities, confidence

    def _calculate_emotion_probability(
        self,
        features: Dict[str, Any],
        emotion: VoiceEmotion,
        gender: str
    ) -> float:
        """특정 감정의 확률 계산"""
        profile = self.emotion_profiles.get(emotion, {})
        score = 0.0
        weights = 0.0

        pitch = features.get('pitch')
        tempo = features.get('tempo')
        tremor = features.get('tremor')
        energy = features.get('energy')

        # 음높이 점수
        if pitch and 'pitch' in profile:
            pitch_score = self._score_pitch(pitch, profile['pitch'], gender)
            score += pitch_score * 0.3
            weights += 0.3

        # 속도 점수
        if tempo and 'tempo' in profile:
            tempo_score = self._score_tempo(tempo, profile['tempo'])
            score += tempo_score * 0.25
            weights += 0.25

        # 떨림 점수
        if tremor and 'tremor' in profile:
            tremor_score = self._score_tremor(tremor, profile['tremor'])
            score += tremor_score * 0.25
            weights += 0.25

        # 에너지 점수
        if energy and 'energy' in profile:
            energy_score = self._score_energy(energy, profile['energy'])
            score += energy_score * 0.2
            weights += 0.2

        return score / weights if weights > 0 else 0.1

    def _score_pitch(
        self,
        pitch: PitchFeatures,
        profile: Dict,
        gender: str
    ) -> float:
        """음높이 프로파일 매칭 점수"""
        score = 0.0
        count = 0

        # 기준 음높이
        if gender == 'male':
            ref_pitch = self.reference_values['pitch_mean_male']
        elif gender == 'female':
            ref_pitch = self.reference_values['pitch_mean_female']
        else:
            ref_pitch = 170  # 중간값

        # 평균 음높이
        if 'mean' in profile:
            if profile['mean'] == 'high' and pitch.mean_pitch > ref_pitch * 1.1:
                score += 1.0
            elif profile['mean'] == 'low' and pitch.mean_pitch < ref_pitch * 0.9:
                score += 1.0
            elif profile['mean'] == 'normal':
                if 0.9 * ref_pitch <= pitch.mean_pitch <= 1.1 * ref_pitch:
                    score += 1.0
            count += 1

        # 음높이 변동
        if 'std' in profile:
            high_threshold = ref_pitch * 0.15
            if profile['std'] == 'high' and pitch.pitch_std > high_threshold:
                score += 1.0
            elif profile['std'] == 'low' and pitch.pitch_std < high_threshold * 0.5:
                score += 1.0
            count += 1

        # Jitter
        if 'jitter' in profile:
            if profile['jitter'] == 'high' and pitch.jitter > 2.0:
                score += 1.0
            elif profile['jitter'] == 'very_high' and pitch.jitter > 4.0:
                score += 1.0
            elif profile['jitter'] == 'low' and pitch.jitter < 1.0:
                score += 1.0
            count += 1

        return score / count if count > 0 else 0.5

    def _score_tempo(self, tempo: TempoFeatures, profile: Dict) -> float:
        """속도 프로파일 매칭 점수"""
        score = 0.0
        count = 0

        ref_rate = self.reference_values['speech_rate_normal']

        if 'rate' in profile:
            if profile['rate'] == 'fast' and tempo.speech_rate > ref_rate * 1.2:
                score += 1.0
            elif profile['rate'] == 'slow' and tempo.speech_rate < ref_rate * 0.8:
                score += 1.0
            elif profile['rate'] == 'irregular':
                if tempo.rhythm_regularity < 0.5:
                    score += 1.0
            count += 1

        if 'pause_ratio' in profile:
            if profile['pause_ratio'] == 'high' and tempo.pause_ratio > 30:
                score += 1.0
            elif profile['pause_ratio'] == 'low' and tempo.pause_ratio < 15:
                score += 1.0
            count += 1

        if 'rhythm' in profile:
            if profile['rhythm'] == 'regular' and tempo.rhythm_regularity > 0.7:
                score += 1.0
            elif profile['rhythm'] == 'irregular' and tempo.rhythm_regularity < 0.5:
                score += 1.0
            count += 1

        return score / count if count > 0 else 0.5

    def _score_tremor(self, tremor: TremorFeatures, profile: Dict) -> float:
        """떨림 프로파일 매칭 점수"""
        score = 0.0
        count = 0

        ref_shimmer = self.reference_values['shimmer_normal']

        if 'shimmer' in profile:
            if profile['shimmer'] == 'high' and tremor.shimmer > ref_shimmer * 1.5:
                score += 1.0
            elif profile['shimmer'] == 'low' and tremor.shimmer < ref_shimmer * 0.7:
                score += 1.0
            elif profile['shimmer'] == 'moderate':
                if 0.8 * ref_shimmer <= tremor.shimmer <= 1.3 * ref_shimmer:
                    score += 1.0
            count += 1

        if 'intensity' in profile:
            if profile['intensity'] == 'high' and tremor.tremor_intensity > 0.5:
                score += 1.0
            count += 1

        if 'voice_breaks' in profile:
            if profile['voice_breaks'] == 'many' and tremor.voice_breaks > 3:
                score += 1.0
            count += 1

        return score / count if count > 0 else 0.5

    def _score_energy(self, energy: EnergyFeatures, profile: Dict) -> float:
        """에너지 프로파일 매칭 점수"""
        score = 0.0
        count = 0

        if 'mean' in profile:
            if profile['mean'] == 'high' and energy.mean_energy > -20:
                score += 1.0
            elif profile['mean'] == 'low' and energy.mean_energy < -35:
                score += 1.0
            count += 1

        if 'variability' in profile:
            if profile['variability'] == 'high' and energy.loudness_variability > 0.3:
                score += 1.0
            elif profile['variability'] == 'very_high' and energy.loudness_variability > 0.5:
                score += 1.0
            elif profile['variability'] == 'low' and energy.loudness_variability < 0.15:
                score += 1.0
            count += 1

        return score / count if count > 0 else 0.5


class ClinicalVoiceIndicators:
    """임상적 음성 지표 분석"""

    def __init__(self):
        # 임상적 임계값
        self.clinical_thresholds = {
            'anxiety': {
                'pitch_increase': 1.15,      # 15% 이상 증가
                'jitter_high': 2.5,          # %
                'speech_rate_fast': 5.5,     # 음절/초
                'tremor_intensity': 0.4
            },
            'depression': {
                'pitch_decrease': 0.85,      # 15% 이상 감소
                'speech_rate_slow': 3.5,     # 음절/초
                'pause_ratio_high': 35,      # %
                'energy_low': -40            # dB
            },
            'crisis': {
                'jitter_critical': 5.0,      # %
                'shimmer_critical': 8.0,     # %
                'voice_breaks': 5,
                'extreme_energy_var': 0.6
            }
        }

    def analyze_clinical_indicators(
        self,
        features: Dict[str, Any],
        baseline: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """임상적 지표 분석"""
        pitch = features.get('pitch')
        tempo = features.get('tempo')
        tremor = features.get('tremor')
        energy = features.get('energy')

        result = {
            'stress_index': 0.0,
            'anxiety_markers': [],
            'depression_markers': [],
            'crisis_indicators': []
        }

        # 불안 마커
        anxiety_score = 0
        if pitch and pitch.jitter > self.clinical_thresholds['anxiety']['jitter_high']:
            result['anxiety_markers'].append('높은 음높이 떨림 (jitter)')
            anxiety_score += 20

        if tempo and tempo.speech_rate > self.clinical_thresholds['anxiety']['speech_rate_fast']:
            result['anxiety_markers'].append('빠른 발화 속도')
            anxiety_score += 15

        if tremor and tremor.tremor_intensity > self.clinical_thresholds['anxiety']['tremor_intensity']:
            result['anxiety_markers'].append('음성 떨림 감지')
            anxiety_score += 25

        # 우울 마커
        depression_score = 0
        if tempo and tempo.speech_rate < self.clinical_thresholds['depression']['speech_rate_slow']:
            result['depression_markers'].append('느린 발화 속도')
            depression_score += 15

        if tempo and tempo.pause_ratio > self.clinical_thresholds['depression']['pause_ratio_high']:
            result['depression_markers'].append('긴 휴지 시간')
            depression_score += 20

        if energy and energy.mean_energy < self.clinical_thresholds['depression']['energy_low']:
            result['depression_markers'].append('낮은 음성 에너지')
            depression_score += 15

        # 위기 지표
        crisis_score = 0
        if pitch and pitch.jitter > self.clinical_thresholds['crisis']['jitter_critical']:
            result['crisis_indicators'].append('극심한 음높이 불안정')
            crisis_score += 30

        if tremor and tremor.shimmer > self.clinical_thresholds['crisis']['shimmer_critical']:
            result['crisis_indicators'].append('극심한 진폭 변동')
            crisis_score += 30

        if tremor and tremor.voice_breaks >= self.clinical_thresholds['crisis']['voice_breaks']:
            result['crisis_indicators'].append('잦은 음성 끊김')
            crisis_score += 25

        if energy and energy.loudness_variability > self.clinical_thresholds['crisis']['extreme_energy_var']:
            result['crisis_indicators'].append('극심한 음량 변동')
            crisis_score += 15

        # 스트레스 지수 계산
        result['stress_index'] = min(anxiety_score + depression_score * 0.5 + crisis_score, 100)

        return result


class IntegratedVoiceEmotionAnalyzer:
    """통합 음성 감정 분석기"""

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.feature_extractor = VoiceFeatureExtractor(sample_rate)
        self.emotion_classifier = VoiceEmotionClassifier()
        self.clinical_analyzer = ClinicalVoiceIndicators()

        # 사용자별 기준선 저장
        self.user_baselines: Dict[str, Dict] = {}

    def analyze(
        self,
        audio_data: np.ndarray,
        sample_rate: Optional[int] = None,
        user_id: Optional[str] = None,
        gender: str = 'unknown'
    ) -> VoiceEmotionResult:
        """
        음성 감정 종합 분석

        Args:
            audio_data: 오디오 데이터 (numpy array)
            sample_rate: 샘플링 레이트
            user_id: 사용자 ID (기준선 비교용)
            gender: 성별 ('male', 'female', 'unknown')

        Returns:
            VoiceEmotionResult: 종합 분석 결과
        """
        if sample_rate is None:
            sample_rate = self.sample_rate

        # 특성 추출
        features = self.feature_extractor.extract_all_features(audio_data, sample_rate)

        # 기준선 가져오기
        baseline = self.user_baselines.get(user_id) if user_id else None

        # 감정 분류
        primary_emotion, probabilities, confidence = self.emotion_classifier.classify(
            features, gender
        )

        # 임상적 지표 분석
        clinical_result = self.clinical_analyzer.analyze_clinical_indicators(
            features, baseline
        )

        # 감정 강도 결정
        intensity = self._determine_intensity(
            probabilities[primary_emotion.value],
            clinical_result['stress_index']
        )

        # 결과 구성
        result = VoiceEmotionResult(
            primary_emotion=primary_emotion,
            emotion_probabilities=probabilities,
            intensity=intensity,
            confidence=confidence,
            pitch_features=features['pitch'],
            tempo_features=features['tempo'],
            tremor_features=features['tremor'],
            energy_features=features['energy'],
            spectral_features=features.get('spectral'),
            stress_index=clinical_result['stress_index'],
            anxiety_markers=clinical_result['anxiety_markers'],
            depression_markers=clinical_result['depression_markers'],
            crisis_indicators=clinical_result['crisis_indicators'],
            audio_duration=len(audio_data) / sample_rate,
            sample_rate=sample_rate
        )

        return result

    def _determine_intensity(
        self,
        emotion_probability: float,
        stress_index: float
    ) -> EmotionalIntensity:
        """감정 강도 결정"""
        combined_score = emotion_probability * 50 + stress_index * 0.5

        if combined_score >= 80:
            return EmotionalIntensity.VERY_HIGH
        elif combined_score >= 60:
            return EmotionalIntensity.HIGH
        elif combined_score >= 40:
            return EmotionalIntensity.MODERATE
        elif combined_score >= 20:
            return EmotionalIntensity.LOW
        else:
            return EmotionalIntensity.VERY_LOW

    def update_baseline(
        self,
        user_id: str,
        audio_data: np.ndarray,
        sample_rate: Optional[int] = None
    ):
        """사용자 기준선 업데이트"""
        if sample_rate is None:
            sample_rate = self.sample_rate

        features = self.feature_extractor.extract_all_features(audio_data, sample_rate)

        if user_id not in self.user_baselines:
            self.user_baselines[user_id] = features
        else:
            # 이동 평균으로 업데이트
            existing = self.user_baselines[user_id]
            for key in features:
                if key in existing:
                    # DataClass 필드들 평균
                    pass  # 실제 구현에서는 필드별 평균 계산

    def get_emotion_summary(self, result: VoiceEmotionResult) -> str:
        """감정 분석 요약 텍스트 생성"""
        emotion_korean = {
            VoiceEmotion.NEUTRAL: "중립",
            VoiceEmotion.ANXIETY: "불안",
            VoiceEmotion.SADNESS: "슬픔",
            VoiceEmotion.ANGER: "분노",
            VoiceEmotion.FEAR: "두려움",
            VoiceEmotion.JOY: "기쁨",
            VoiceEmotion.DISTRESS: "고통",
            VoiceEmotion.FATIGUE: "피로"
        }

        intensity_korean = {
            EmotionalIntensity.VERY_LOW: "매우 낮음",
            EmotionalIntensity.LOW: "낮음",
            EmotionalIntensity.MODERATE: "보통",
            EmotionalIntensity.HIGH: "높음",
            EmotionalIntensity.VERY_HIGH: "매우 높음"
        }

        summary = f"""📊 **음성 감정 분석 결과**

**주요 감정**: {emotion_korean.get(result.primary_emotion, result.primary_emotion.value)}
**강도**: {intensity_korean.get(result.intensity, '보통')}
**신뢰도**: {result.confidence * 100:.1f}%
**스트레스 지수**: {result.stress_index:.0f}/100

**음성 특성**:
• 음높이: 평균 {result.pitch_features.mean_pitch:.1f}Hz (변동: {result.pitch_features.pitch_std:.1f})
• 발화 속도: {result.tempo_features.speech_rate:.1f}음절/초
• 휴지 비율: {result.tempo_features.pause_ratio:.1f}%
• 음성 떨림: {result.tremor_features.shimmer:.2f}%"""

        if result.anxiety_markers:
            summary += f"\n\n⚠️ **불안 지표**: {', '.join(result.anxiety_markers)}"

        if result.depression_markers:
            summary += f"\n\n💙 **우울 지표**: {', '.join(result.depression_markers)}"

        if result.crisis_indicators:
            summary += f"\n\n🚨 **위기 지표**: {', '.join(result.crisis_indicators)}"

        return summary


# 사용 예시
if __name__ == "__main__":
    analyzer = IntegratedVoiceEmotionAnalyzer(sample_rate=16000)

    # 테스트용 더미 오디오
    duration = 5.0
    sample_rate = 16000
    t = np.linspace(0, duration, int(duration * sample_rate))

    # 떨리는 목소리 시뮬레이션
    base_freq = 200
    tremor = 5  # Hz
    audio_data = np.sin(2 * np.pi * base_freq * t) * (1 + 0.3 * np.sin(2 * np.pi * tremor * t))
    audio_data = audio_data.astype(np.float32)

    # 분석
    result = analyzer.analyze(audio_data, sample_rate, gender='female')

    print(analyzer.get_emotion_summary(result))
