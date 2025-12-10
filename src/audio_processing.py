"""
오디오 처리 모듈 (Audio Processing)
노이즈 제거, 에코 캔슬링, 오디오 품질 개선

특징:
- RNNoise 기반 노이즈 억제
- WebRTC AEC (Acoustic Echo Cancellation)
- AGC (Automatic Gain Control)
- 지터 버퍼
"""

import logging
import numpy as np
from typing import Optional, Tuple, List
from dataclasses import dataclass
from collections import deque
import threading

logger = logging.getLogger(__name__)


@dataclass
class AudioConfig:
    """오디오 설정"""
    sample_rate: int = 16000
    channels: int = 1
    frame_size_ms: int = 10  # WebRTC 표준
    enable_ns: bool = True  # Noise Suppression
    enable_aec: bool = True  # Echo Cancellation
    enable_agc: bool = True  # Automatic Gain Control
    enable_vad: bool = True  # Voice Activity Detection


class NoiseSupressor:
    """
    노이즈 억제 (Noise Suppression)

    RNNoise 또는 스펙트럼 감산 기반 노이즈 제거
    """

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self._rnnoise = None
        self._fallback_mode = False

        # 스펙트럼 노이즈 추정
        self.noise_estimate = None
        self.noise_frames = deque(maxlen=50)

        self._init_rnnoise()

    def _init_rnnoise(self):
        """RNNoise 초기화"""
        try:
            import rnnoise
            self._rnnoise = rnnoise.RNNoise()
            logger.info("RNNoise initialized")
        except ImportError:
            logger.warning("RNNoise not available, using spectral subtraction")
            self._fallback_mode = True

    def process(self, audio: np.ndarray) -> np.ndarray:
        """
        노이즈 제거

        Args:
            audio: 입력 오디오 (float32, mono)

        Returns:
            노이즈 제거된 오디오
        """
        if self._rnnoise and not self._fallback_mode:
            return self._process_rnnoise(audio)
        else:
            return self._process_spectral(audio)

    def _process_rnnoise(self, audio: np.ndarray) -> np.ndarray:
        """RNNoise 처리"""
        try:
            # RNNoise는 480 샘플 프레임 사용
            frame_size = 480
            output = np.zeros_like(audio)

            for i in range(0, len(audio), frame_size):
                frame = audio[i:i + frame_size]
                if len(frame) < frame_size:
                    frame = np.pad(frame, (0, frame_size - len(frame)))

                # float32 → int16 → rnnoise → float32
                frame_int16 = (frame * 32767).astype(np.int16)
                processed = self._rnnoise.process_frame(frame_int16)
                output[i:i + len(processed)] = np.array(processed) / 32767.0

            return output

        except Exception as e:
            logger.error(f"RNNoise error: {e}")
            return self._process_spectral(audio)

    def _process_spectral(self, audio: np.ndarray) -> np.ndarray:
        """스펙트럼 감산 기반 노이즈 제거"""
        # FFT
        n_fft = 512
        hop_length = n_fft // 4

        # STFT
        num_frames = 1 + (len(audio) - n_fft) // hop_length
        stft = np.zeros((n_fft // 2 + 1, num_frames), dtype=np.complex128)

        window = np.hanning(n_fft)

        for i in range(num_frames):
            start = i * hop_length
            frame = audio[start:start + n_fft] * window
            stft[:, i] = np.fft.rfft(frame)

        # 크기 스펙트럼
        magnitude = np.abs(stft)
        phase = np.angle(stft)

        # 노이즈 추정 (첫 몇 프레임 또는 저에너지 프레임)
        if self.noise_estimate is None:
            self.noise_estimate = np.mean(magnitude[:, :5], axis=1, keepdims=True)
        else:
            # 저에너지 프레임으로 노이즈 업데이트
            for i in range(num_frames):
                frame_energy = np.sum(magnitude[:, i] ** 2)
                if frame_energy < np.mean(self.noise_frames) * 0.5 if self.noise_frames else True:
                    self.noise_frames.append(frame_energy)
                    self.noise_estimate = 0.95 * self.noise_estimate + 0.05 * magnitude[:, i:i + 1]

        # 스펙트럼 감산
        alpha = 2.0  # 과감산 계수
        beta = 0.01  # 스펙트럼 플로어

        magnitude_clean = np.maximum(
            magnitude - alpha * self.noise_estimate,
            beta * magnitude
        )

        # ISTFT
        stft_clean = magnitude_clean * np.exp(1j * phase)
        output = np.zeros(len(audio))

        for i in range(num_frames):
            start = i * hop_length
            frame = np.fft.irfft(stft_clean[:, i]) * window
            output[start:start + n_fft] += frame

        # 정규화
        output = output / np.maximum(np.max(np.abs(output)), 1e-6)

        return output.astype(np.float32)


class EchoCanceller:
    """
    에코 캔슬러 (Acoustic Echo Cancellation)

    재생 중인 오디오가 마이크에 다시 수집되는 것을 방지
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        frame_size_ms: int = 10,
        filter_length_ms: int = 100
    ):
        self.sample_rate = sample_rate
        self.frame_size = int(sample_rate * frame_size_ms / 1000)
        self.filter_length = int(sample_rate * filter_length_ms / 1000)

        # 적응 필터 (NLMS)
        self.filter_coeffs = np.zeros(self.filter_length)
        self.mu = 0.1  # 학습률
        self.delta = 1e-6  # 정규화 상수

        # 참조 신호 버퍼
        self.ref_buffer = np.zeros(self.filter_length)

        # 상태
        self._webrtc_aec = None
        self._fallback_mode = False

        self._init_webrtc()

    def _init_webrtc(self):
        """WebRTC AEC 초기화"""
        try:
            import webrtcvad
            # webrtcvad는 VAD만 지원, AEC는 별도 라이브러리 필요
            # speexdsp 또는 자체 구현 사용
            logger.info("Using NLMS-based AEC")
        except ImportError:
            logger.warning("WebRTC not available")
            self._fallback_mode = True

    def set_reference(self, playback_audio: np.ndarray):
        """
        참조 신호 설정 (재생 중인 오디오)

        Args:
            playback_audio: 재생 중인 오디오
        """
        # 버퍼에 추가
        self.ref_buffer = np.concatenate([
            self.ref_buffer[len(playback_audio):],
            playback_audio
        ])[-self.filter_length:]

    def process(
        self,
        mic_audio: np.ndarray,
        playback_audio: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        에코 제거

        Args:
            mic_audio: 마이크 입력 오디오
            playback_audio: 재생 중인 오디오 (옵션)

        Returns:
            에코 제거된 오디오
        """
        if playback_audio is not None:
            self.set_reference(playback_audio)

        # NLMS 적응 필터
        output = np.zeros_like(mic_audio)

        for i in range(len(mic_audio)):
            # 참조 신호 벡터
            if i < self.filter_length:
                x = np.concatenate([
                    self.ref_buffer[-(self.filter_length - i):],
                    mic_audio[:i]
                ])
            else:
                x = mic_audio[i - self.filter_length:i]

            if len(x) < self.filter_length:
                x = np.pad(x, (self.filter_length - len(x), 0))

            # 에코 추정
            echo_estimate = np.dot(self.filter_coeffs, x)

            # 에코 제거
            error = mic_audio[i] - echo_estimate
            output[i] = error

            # 필터 업데이트 (NLMS)
            norm = np.dot(x, x) + self.delta
            self.filter_coeffs += (self.mu / norm) * error * x

        return output.astype(np.float32)


class AutomaticGainControl:
    """
    자동 이득 제어 (AGC)

    입력 신호의 볼륨을 일정하게 유지
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        target_level_db: float = -20.0,
        max_gain_db: float = 30.0,
        attack_time_ms: float = 5.0,
        release_time_ms: float = 100.0
    ):
        self.sample_rate = sample_rate
        self.target_level = 10 ** (target_level_db / 20)
        self.max_gain = 10 ** (max_gain_db / 20)

        # 시간 상수
        self.attack_coeff = np.exp(-1 / (sample_rate * attack_time_ms / 1000))
        self.release_coeff = np.exp(-1 / (sample_rate * release_time_ms / 1000))

        # 상태
        self.current_gain = 1.0
        self.envelope = 0.0

    def process(self, audio: np.ndarray) -> np.ndarray:
        """
        AGC 적용

        Args:
            audio: 입력 오디오

        Returns:
            볼륨 조정된 오디오
        """
        output = np.zeros_like(audio)

        for i in range(len(audio)):
            # 엔벨로프 추적
            abs_sample = np.abs(audio[i])

            if abs_sample > self.envelope:
                self.envelope = self.attack_coeff * self.envelope + (1 - self.attack_coeff) * abs_sample
            else:
                self.envelope = self.release_coeff * self.envelope + (1 - self.release_coeff) * abs_sample

            # 목표 이득 계산
            if self.envelope > 1e-6:
                target_gain = self.target_level / self.envelope
                target_gain = min(target_gain, self.max_gain)
            else:
                target_gain = self.max_gain

            # 부드러운 이득 변화
            self.current_gain = 0.99 * self.current_gain + 0.01 * target_gain

            # 적용
            output[i] = audio[i] * self.current_gain

        # 클리핑 방지
        output = np.clip(output, -1.0, 1.0)

        return output.astype(np.float32)


class JitterBuffer:
    """
    지터 버퍼 (Jitter Buffer)

    네트워크 지연 변동을 흡수하여 부드러운 재생 제공
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        target_delay_ms: int = 60,
        min_delay_ms: int = 20,
        max_delay_ms: int = 200
    ):
        self.sample_rate = sample_rate
        self.target_delay_samples = int(sample_rate * target_delay_ms / 1000)
        self.min_delay_samples = int(sample_rate * min_delay_ms / 1000)
        self.max_delay_samples = int(sample_rate * max_delay_ms / 1000)

        self.buffer = deque()
        self.total_samples = 0

        # 적응형 조절
        self.delay_history = deque(maxlen=100)
        self._lock = threading.Lock()

    def push(self, audio: np.ndarray, timestamp: Optional[float] = None):
        """오디오 청크 추가"""
        with self._lock:
            self.buffer.append({
                "audio": audio,
                "timestamp": timestamp,
                "length": len(audio)
            })
            self.total_samples += len(audio)

            # 최대 버퍼 초과 시 오래된 데이터 제거
            while self.total_samples > self.max_delay_samples:
                old = self.buffer.popleft()
                self.total_samples -= old["length"]
                logger.warning("Jitter buffer overflow, dropping packet")

    def pop(self, num_samples: int) -> Optional[np.ndarray]:
        """오디오 청크 추출"""
        with self._lock:
            # 최소 버퍼 미달 시 대기
            if self.total_samples < self.min_delay_samples:
                return None

            output = np.array([], dtype=np.float32)

            while len(output) < num_samples and self.buffer:
                chunk = self.buffer[0]

                remaining = num_samples - len(output)

                if chunk["length"] <= remaining:
                    # 전체 청크 사용
                    output = np.concatenate([output, chunk["audio"]])
                    self.buffer.popleft()
                    self.total_samples -= chunk["length"]
                else:
                    # 청크 일부만 사용
                    output = np.concatenate([output, chunk["audio"][:remaining]])
                    chunk["audio"] = chunk["audio"][remaining:]
                    chunk["length"] -= remaining
                    self.total_samples -= remaining

            return output if len(output) > 0 else None

    def clear(self):
        """버퍼 비우기"""
        with self._lock:
            self.buffer.clear()
            self.total_samples = 0

    @property
    def delay_ms(self) -> float:
        """현재 버퍼 지연 (ms)"""
        return self.total_samples / self.sample_rate * 1000


class AudioProcessor:
    """
    통합 오디오 프로세서

    노이즈 제거 + 에코 캔슬 + AGC + 지터 버퍼
    """

    def __init__(self, config: Optional[AudioConfig] = None):
        self.config = config or AudioConfig()

        # 컴포넌트 초기화
        self.noise_suppressor = NoiseSupressor(self.config.sample_rate) if self.config.enable_ns else None
        self.echo_canceller = EchoCanceller(self.config.sample_rate) if self.config.enable_aec else None
        self.agc = AutomaticGainControl(self.config.sample_rate) if self.config.enable_agc else None
        self.jitter_buffer = JitterBuffer(self.config.sample_rate)

        logger.info(f"AudioProcessor initialized: NS={self.config.enable_ns}, AEC={self.config.enable_aec}, AGC={self.config.enable_agc}")

    def process_input(
        self,
        mic_audio: np.ndarray,
        playback_audio: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        입력 오디오 처리 (마이크)

        Args:
            mic_audio: 마이크 입력
            playback_audio: 재생 중인 오디오 (에코 캔슬용)

        Returns:
            처리된 오디오
        """
        audio = mic_audio.astype(np.float32)

        # 1. 에코 캔슬링
        if self.echo_canceller and playback_audio is not None:
            audio = self.echo_canceller.process(audio, playback_audio)

        # 2. 노이즈 제거
        if self.noise_suppressor:
            audio = self.noise_suppressor.process(audio)

        # 3. AGC
        if self.agc:
            audio = self.agc.process(audio)

        return audio

    def process_output(self, audio: np.ndarray) -> np.ndarray:
        """
        출력 오디오 처리 (스피커)

        Args:
            audio: TTS 출력 오디오

        Returns:
            처리된 오디오
        """
        # 에코 캔슬러에 참조 신호 설정
        if self.echo_canceller:
            self.echo_canceller.set_reference(audio)

        return audio

    def buffer_output(self, audio: np.ndarray, timestamp: Optional[float] = None):
        """출력 오디오 버퍼링"""
        self.jitter_buffer.push(audio, timestamp)

    def get_buffered_output(self, num_samples: int) -> Optional[np.ndarray]:
        """버퍼된 출력 가져오기"""
        return self.jitter_buffer.pop(num_samples)
