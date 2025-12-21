"""
STT 모듈 (Speech-to-Text)
OpenAI Whisper large-v3를 사용한 한국어 음성 인식

기능:
- 실시간 음성 인식
- 파일 기반 음성 인식
- 스트리밍 지원
- 음성 활동 감지 (VAD)
"""

import logging
import numpy as np
from typing import Optional, Dict, Any, Generator, Union
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import io
import threading
import queue

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionResult:
    """음성 인식 결과"""
    text: str
    language: str
    confidence: float
    duration: float  # 오디오 길이 (초)
    segments: list = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "language": self.language,
            "confidence": self.confidence,
            "duration": self.duration,
            "segments": self.segments,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class VADConfig:
    """음성 활동 감지 설정"""
    sample_rate: int = 16000
    frame_duration_ms: int = 30  # 10, 20, 또는 30ms
    padding_duration_ms: int = 300
    aggressiveness: int = 3  # 0-3 (높을수록 엄격)


class WhisperSTT:
    """
    Whisper large-v3 기반 STT 엔진

    A100 GPU 최적화 설정 포함
    """

    def __init__(
        self,
        model_size: str = "large-v3",
        device: str = "cuda",
        compute_type: str = "float16",  # A100: float16 권장
        language: str = "ko",
        use_faster_whisper: bool = True,  # faster-whisper 사용 여부
        vad_config: Optional[VADConfig] = None
    ):
        """
        초기화

        Args:
            model_size: Whisper 모델 크기 (tiny, base, small, medium, large-v3)
            device: 디바이스 (cuda, cpu)
            compute_type: 연산 타입 (float16, int8, float32)
            language: 인식 언어 (ko: 한국어)
            use_faster_whisper: faster-whisper 사용 여부 (더 빠름)
            vad_config: 음성 활동 감지 설정
        """
        # GPU 필수 - 감지 실패 시 상세 에러 로그와 함께 예외 발생
        if device == "cuda":
            from src.gpu_check import require_gpu
            device = require_gpu("cuda")
        
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self.use_faster_whisper = use_faster_whisper
        self.vad_config = vad_config or VADConfig()

        self.model = None
        self.vad = None
        self._lock = threading.Lock()

        logger.info(f"WhisperSTT initializing with model={model_size}, device={device}")

    def load_model(self) -> None:
        """모델 로드"""
        with self._lock:
            if self.model is not None:
                return

            if self.use_faster_whisper:
                self._load_faster_whisper()
            else:
                self._load_openai_whisper()

            self._load_vad()

            logger.info("Whisper model loaded successfully")

    def _load_faster_whisper(self) -> None:
        """faster-whisper 모델 로드"""
        try:
            from faster_whisper import WhisperModel

            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )
            self._model_type = "faster_whisper"
            logger.info("faster-whisper model loaded")

        except ImportError:
            logger.warning("faster-whisper not installed, falling back to openai-whisper")
            self._load_openai_whisper()

    def _load_openai_whisper(self) -> None:
        """OpenAI Whisper 모델 로드"""
        try:
            import whisper

            self.model = whisper.load_model(self.model_size, device=self.device)
            self._model_type = "openai_whisper"
            logger.info("openai-whisper model loaded")

        except ImportError as e:
            error_msg = f"whisper not installed. Run: pip install openai-whisper. Original error: {e}"
            logger.error(error_msg)
            raise ImportError(error_msg)
        except Exception as e:
            error_msg = f"Failed to load whisper model: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def _load_vad(self) -> None:
        """VAD (Voice Activity Detection) 로드"""
        try:
            import webrtcvad
            self.vad = webrtcvad.Vad(self.vad_config.aggressiveness)
            logger.info("WebRTC VAD loaded")
        except ImportError:
            logger.warning("webrtcvad not installed, VAD disabled")
            self.vad = None

    def transcribe(
        self,
        audio: Union[str, bytes, np.ndarray],
        sample_rate: int = 16000
    ) -> TranscriptionResult:
        """
        음성을 텍스트로 변환

        Args:
            audio: 오디오 파일 경로, 바이트, 또는 numpy 배열
            sample_rate: 샘플레이트 (기본 16000Hz)

        Returns:
            TranscriptionResult: 인식 결과
        """
        if self.model is None:
            self.load_model()

        # 오디오 전처리
        audio_array = self._preprocess_audio(audio, sample_rate)
        duration = len(audio_array) / sample_rate

        # 인식 수행
        if self._model_type == "faster_whisper":
            result = self._transcribe_faster(audio_array)
        else:
            result = self._transcribe_openai(audio_array)

        result.duration = duration
        return result

    def _preprocess_audio(
        self,
        audio: Union[str, bytes, np.ndarray],
        sample_rate: int
    ) -> np.ndarray:
        """오디오 전처리"""
        import soundfile as sf

        if isinstance(audio, str):
            # 파일 경로
            audio_array, sr = sf.read(audio)
            if sr != sample_rate:
                audio_array = self._resample(audio_array, sr, sample_rate)
        elif isinstance(audio, bytes):
            # 바이트 데이터
            audio_array, sr = sf.read(io.BytesIO(audio))
            if sr != sample_rate:
                audio_array = self._resample(audio_array, sr, sample_rate)
        elif isinstance(audio, np.ndarray):
            audio_array = audio
        else:
            raise ValueError(f"Unsupported audio type: {type(audio)}")

        # 모노로 변환
        if len(audio_array.shape) > 1:
            audio_array = audio_array.mean(axis=1)

        # float32로 변환
        if audio_array.dtype != np.float32:
            audio_array = audio_array.astype(np.float32)

        # 정규화
        if np.abs(audio_array).max() > 1.0:
            audio_array = audio_array / np.abs(audio_array).max()

        return audio_array

    def _resample(
        self,
        audio: np.ndarray,
        orig_sr: int,
        target_sr: int
    ) -> np.ndarray:
        """리샘플링"""
        try:
            import librosa
            return librosa.resample(audio, orig_sr=orig_sr, target_sr=target_sr)
        except ImportError:
            # 간단한 리샘플링 (librosa 없을 때)
            ratio = target_sr / orig_sr
            new_length = int(len(audio) * ratio)
            indices = np.linspace(0, len(audio) - 1, new_length)
            return np.interp(indices, np.arange(len(audio)), audio)

    def _transcribe_faster(self, audio: np.ndarray) -> TranscriptionResult:
        """faster-whisper로 인식"""
        segments, info = self.model.transcribe(
            audio,
            language=self.language,
            beam_size=5,
            vad_filter=True,  # VAD 필터 활성화
            vad_parameters=dict(
                min_silence_duration_ms=500,
                speech_pad_ms=400
            )
        )

        # 세그먼트 수집
        segment_list = []
        full_text = []

        for segment in segments:
            segment_list.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            })
            full_text.append(segment.text.strip())

        return TranscriptionResult(
            text=" ".join(full_text),
            language=info.language,
            confidence=info.language_probability,
            duration=0,  # 나중에 설정
            segments=segment_list
        )

    def _transcribe_openai(self, audio: np.ndarray) -> TranscriptionResult:
        """OpenAI Whisper로 인식"""
        result = self.model.transcribe(
            audio,
            language=self.language,
            fp16=(self.device == "cuda")
        )

        segments = [
            {
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"].strip()
            }
            for seg in result.get("segments", [])
        ]

        return TranscriptionResult(
            text=result["text"].strip(),
            language=result.get("language", self.language),
            confidence=1.0,  # OpenAI Whisper는 confidence 미제공
            duration=0,
            segments=segments
        )

    def transcribe_stream(
        self,
        audio_stream: Generator[bytes, None, None],
        chunk_duration: float = 2.0,  # 청크 길이 (초)
        sample_rate: int = 16000
    ) -> Generator[TranscriptionResult, None, None]:
        """
        스트리밍 음성 인식

        Args:
            audio_stream: 오디오 바이트 스트림
            chunk_duration: 청크 길이 (초)
            sample_rate: 샘플레이트

        Yields:
            TranscriptionResult: 실시간 인식 결과
        """
        if self.model is None:
            self.load_model()

        chunk_size = int(chunk_duration * sample_rate * 2)  # 16-bit = 2 bytes
        buffer = b""

        for audio_chunk in audio_stream:
            buffer += audio_chunk

            while len(buffer) >= chunk_size:
                chunk = buffer[:chunk_size]
                buffer = buffer[chunk_size:]

                # VAD 체크
                if self.vad and not self._has_speech(chunk):
                    continue

                # 청크 인식
                result = self.transcribe(chunk, sample_rate)
                if result.text.strip():
                    yield result

    def _has_speech(self, audio_bytes: bytes) -> bool:
        """음성 활동 감지"""
        if self.vad is None:
            return True

        frame_size = int(
            self.vad_config.sample_rate *
            self.vad_config.frame_duration_ms / 1000 * 2
        )

        # 프레임별 VAD 체크
        speech_frames = 0
        total_frames = 0

        for i in range(0, len(audio_bytes) - frame_size, frame_size):
            frame = audio_bytes[i:i + frame_size]
            total_frames += 1
            if self.vad.is_speech(frame, self.vad_config.sample_rate):
                speech_frames += 1

        # 30% 이상 음성이면 True
        return total_frames > 0 and (speech_frames / total_frames) > 0.3

    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        return {
            "model_size": self.model_size,
            "device": self.device,
            "compute_type": self.compute_type,
            "language": self.language,
            "model_type": getattr(self, '_model_type', None),
            "loaded": self.model is not None,
            "vad_enabled": self.vad is not None
        }


class RealtimeSTT:
    """
    실시간 마이크 입력 STT

    마이크에서 실시간으로 음성을 캡처하여 텍스트로 변환
    """

    def __init__(
        self,
        whisper_stt: Optional[WhisperSTT] = None,
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_duration: float = 2.0
    ):
        self.stt = whisper_stt or WhisperSTT()
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_duration = chunk_duration

        self._running = False
        self._audio_queue = queue.Queue()
        self._result_queue = queue.Queue()

    def start(self) -> None:
        """실시간 인식 시작"""
        import sounddevice as sd

        self._running = True

        # 오디오 캡처 스레드
        def audio_callback(indata, frames, time, status):
            if status:
                logger.warning(f"Audio status: {status}")
            self._audio_queue.put(indata.copy())

        # 스트림 시작
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype='float32',
            callback=audio_callback,
            blocksize=int(self.sample_rate * self.chunk_duration)
        )
        self._stream.start()

        # 인식 스레드
        self._recognition_thread = threading.Thread(target=self._recognition_loop)
        self._recognition_thread.start()

        logger.info("RealtimeSTT started")

    def stop(self) -> None:
        """실시간 인식 중지"""
        self._running = False

        if hasattr(self, '_stream'):
            self._stream.stop()
            self._stream.close()

        if hasattr(self, '_recognition_thread'):
            self._recognition_thread.join(timeout=2.0)

        logger.info("RealtimeSTT stopped")

    def _recognition_loop(self) -> None:
        """인식 루프"""
        buffer = []

        while self._running:
            try:
                audio_chunk = self._audio_queue.get(timeout=0.5)
                buffer.append(audio_chunk)

                # 충분한 오디오가 모이면 인식
                total_samples = sum(len(c) for c in buffer)
                if total_samples >= self.sample_rate * self.chunk_duration:
                    audio = np.concatenate(buffer)
                    buffer = []

                    result = self.stt.transcribe(audio, self.sample_rate)
                    if result.text.strip():
                        self._result_queue.put(result)

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Recognition error: {e}")

    def get_result(self, timeout: float = 1.0) -> Optional[TranscriptionResult]:
        """인식 결과 가져오기"""
        try:
            return self._result_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


# 편의 함수
_default_stt: Optional[WhisperSTT] = None


def get_stt(
    model_size: str = "large-v3",
    device: str = "cuda"
) -> WhisperSTT:
    """기본 STT 인스턴스 반환"""
    global _default_stt

    if _default_stt is None:
        _default_stt = WhisperSTT(model_size=model_size, device=device)
        _default_stt.load_model()

    return _default_stt


def transcribe(
    audio: Union[str, bytes, np.ndarray],
    language: str = "ko"
) -> str:
    """간단한 음성 인식 함수"""
    stt = get_stt()
    result = stt.transcribe(audio)
    return result.text
