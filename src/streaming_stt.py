"""
스트리밍 STT 모듈 (Streaming Speech-to-Text)
실시간 음성 인식을 위한 청크 단위 처리

특징:
- 실시간 부분 인식 (Partial Recognition)
- VAD 기반 발화 구간 감지
- 적응형 버퍼링
- 낮은 지연시간
"""

import logging
import asyncio
import numpy as np
from typing import Optional, AsyncGenerator, Callable, List
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
import threading
import queue

logger = logging.getLogger(__name__)


@dataclass
class PartialTranscript:
    """부분 인식 결과"""
    text: str
    is_final: bool
    confidence: float
    start_time: float
    end_time: float
    words: List[dict] = field(default_factory=list)


@dataclass
class StreamingConfig:
    """스트리밍 설정"""
    sample_rate: int = 16000
    chunk_duration_ms: int = 100  # 청크 크기 (ms)
    vad_threshold: float = 0.01
    silence_duration_ms: int = 800  # 발화 종료 판단 침묵 시간
    max_speech_duration_s: float = 30.0  # 최대 발화 시간
    partial_results: bool = True  # 부분 결과 반환 여부
    language: str = "ko"


class StreamingSTT:
    """
    스트리밍 음성 인식

    실시간으로 오디오 청크를 받아 즉시 인식 결과를 반환
    """

    def __init__(
        self,
        model_name: str = "large-v3",
        config: Optional[StreamingConfig] = None,
        device: str = "cuda"
    ):
        self.model_name = model_name
        self.config = config or StreamingConfig()
        self.device = device

        # Whisper 모델 (지연 로딩)
        self._model = None
        self._model_lock = threading.Lock()

        # 오디오 버퍼
        self.audio_buffer = deque(maxlen=int(
            self.config.sample_rate * self.config.max_speech_duration_s
        ))

        # VAD 상태
        self.is_speaking = False
        self.silence_samples = 0
        self.speech_start_sample = 0

        # 청크 크기 계산
        self.chunk_samples = int(
            self.config.sample_rate * self.config.chunk_duration_ms / 1000
        )
        self.silence_samples_threshold = int(
            self.config.sample_rate * self.config.silence_duration_ms / 1000
        )

        # 부분 인식을 위한 상태
        self.pending_audio = np.array([], dtype=np.float32)
        self.last_partial_text = ""

    @property
    def model(self):
        """모델 지연 로딩"""
        if self._model is None:
            with self._model_lock:
                if self._model is None:
                    self._load_model()
        return self._model

    def _load_model(self):
        """Whisper 모델 로드"""
        try:
            from faster_whisper import WhisperModel

            compute_type = "float16" if self.device == "cuda" else "int8"

            self._model = WhisperModel(
                self.model_name,
                device=self.device,
                compute_type=compute_type
            )
            logger.info(f"Streaming STT 모델 로드 완료: {self.model_name}")

        except ImportError:
            logger.warning("faster-whisper not found, using openai-whisper")
            import whisper
            self._model = whisper.load_model(self.model_name, device=self.device)

    def reset(self):
        """상태 초기화"""
        self.audio_buffer.clear()
        self.is_speaking = False
        self.silence_samples = 0
        self.speech_start_sample = 0
        self.pending_audio = np.array([], dtype=np.float32)
        self.last_partial_text = ""

    def _detect_speech(self, audio_chunk: np.ndarray) -> bool:
        """음성 활동 감지 (VAD)"""
        energy = np.sqrt(np.mean(audio_chunk ** 2))
        return energy > self.config.vad_threshold

    async def process_chunk(
        self,
        audio_chunk: np.ndarray
    ) -> Optional[PartialTranscript]:
        """
        오디오 청크 처리

        Args:
            audio_chunk: 오디오 데이터 (float32, mono)

        Returns:
            부분 인식 결과 또는 None
        """
        # 버퍼에 추가
        self.audio_buffer.extend(audio_chunk)
        self.pending_audio = np.concatenate([self.pending_audio, audio_chunk])

        # VAD
        has_speech = self._detect_speech(audio_chunk)

        if has_speech:
            if not self.is_speaking:
                # 발화 시작
                self.is_speaking = True
                self.speech_start_sample = len(self.audio_buffer) - len(audio_chunk)
                logger.debug("발화 시작 감지")

            self.silence_samples = 0

        else:
            if self.is_speaking:
                self.silence_samples += len(audio_chunk)

                # 침묵이 임계값 초과 → 발화 종료
                if self.silence_samples >= self.silence_samples_threshold:
                    self.is_speaking = False

                    # 최종 인식 수행
                    result = await self._transcribe_final()
                    self.reset()
                    return result

        # 부분 인식 (발화 중일 때만)
        if self.is_speaking and self.config.partial_results:
            # 일정 길이 이상일 때만 부분 인식
            if len(self.pending_audio) >= self.config.sample_rate * 0.5:  # 0.5초
                return await self._transcribe_partial()

        return None

    async def _transcribe_partial(self) -> Optional[PartialTranscript]:
        """부분 인식 수행"""
        if len(self.pending_audio) < self.config.sample_rate * 0.3:
            return None

        try:
            # 비동기로 인식 실행
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._run_transcription,
                self.pending_audio.copy(),
                False  # is_final=False
            )

            if result and result.text != self.last_partial_text:
                self.last_partial_text = result.text
                return result

        except Exception as e:
            logger.error(f"부분 인식 오류: {e}")

        return None

    async def _transcribe_final(self) -> Optional[PartialTranscript]:
        """최종 인식 수행"""
        audio_data = np.array(list(self.audio_buffer), dtype=np.float32)

        if len(audio_data) < self.config.sample_rate * 0.1:  # 최소 0.1초
            return None

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._run_transcription,
                audio_data,
                True  # is_final=True
            )
            return result

        except Exception as e:
            logger.error(f"최종 인식 오류: {e}")
            return None

    def _run_transcription(
        self,
        audio: np.ndarray,
        is_final: bool
    ) -> Optional[PartialTranscript]:
        """실제 인식 수행 (동기)"""
        try:
            if hasattr(self.model, 'transcribe'):
                # faster-whisper
                segments, info = self.model.transcribe(
                    audio,
                    language=self.config.language,
                    beam_size=1 if not is_final else 5,
                    best_of=1 if not is_final else 5,
                    vad_filter=True,
                    word_timestamps=is_final
                )

                text_parts = []
                words = []

                for segment in segments:
                    text_parts.append(segment.text)
                    if is_final and hasattr(segment, 'words'):
                        for word in segment.words:
                            words.append({
                                "word": word.word,
                                "start": word.start,
                                "end": word.end,
                                "confidence": word.probability
                            })

                text = "".join(text_parts).strip()

                if text:
                    return PartialTranscript(
                        text=text,
                        is_final=is_final,
                        confidence=0.9 if is_final else 0.7,
                        start_time=0,
                        end_time=len(audio) / self.config.sample_rate,
                        words=words
                    )
            else:
                # openai-whisper
                result = self.model.transcribe(
                    audio,
                    language=self.config.language,
                    fp16=(self.device == "cuda")
                )

                text = result.get("text", "").strip()

                if text:
                    return PartialTranscript(
                        text=text,
                        is_final=is_final,
                        confidence=0.9 if is_final else 0.7,
                        start_time=0,
                        end_time=len(audio) / self.config.sample_rate,
                        words=[]
                    )

        except Exception as e:
            logger.error(f"Transcription error: {e}")

        return None

    async def stream_transcribe(
        self,
        audio_stream: AsyncGenerator[np.ndarray, None]
    ) -> AsyncGenerator[PartialTranscript, None]:
        """
        스트리밍 인식

        Args:
            audio_stream: 오디오 청크 스트림

        Yields:
            인식 결과
        """
        self.reset()

        async for chunk in audio_stream:
            result = await self.process_chunk(chunk)
            if result:
                yield result

        # 남은 오디오 처리
        if self.is_speaking and len(self.pending_audio) > 0:
            final_result = await self._transcribe_final()
            if final_result:
                yield final_result


class AdaptiveBufferManager:
    """
    적응형 버퍼 관리자

    네트워크 상태에 따라 버퍼 크기 동적 조절
    """

    def __init__(
        self,
        min_buffer_ms: int = 50,
        max_buffer_ms: int = 500,
        target_latency_ms: int = 150
    ):
        self.min_buffer_ms = min_buffer_ms
        self.max_buffer_ms = max_buffer_ms
        self.target_latency_ms = target_latency_ms

        self.current_buffer_ms = target_latency_ms
        self.latency_history = deque(maxlen=10)
        self.jitter_history = deque(maxlen=10)

    def update(self, measured_latency_ms: float):
        """지연시간 측정값으로 버퍼 조절"""
        self.latency_history.append(measured_latency_ms)

        if len(self.latency_history) >= 2:
            # 지터 계산
            jitter = abs(measured_latency_ms - self.latency_history[-2])
            self.jitter_history.append(jitter)

        # 버퍼 크기 조절
        avg_latency = np.mean(list(self.latency_history))
        avg_jitter = np.mean(list(self.jitter_history)) if self.jitter_history else 0

        if avg_latency > self.target_latency_ms * 1.5:
            # 지연이 심함 → 버퍼 줄임
            self.current_buffer_ms = max(
                self.min_buffer_ms,
                self.current_buffer_ms - 20
            )
        elif avg_jitter > 50:
            # 지터가 큼 → 버퍼 늘림
            self.current_buffer_ms = min(
                self.max_buffer_ms,
                self.current_buffer_ms + 20
            )
        else:
            # 안정적 → 목표치로 수렴
            diff = self.target_latency_ms - self.current_buffer_ms
            self.current_buffer_ms += diff * 0.1

        return self.current_buffer_ms

    def get_buffer_size(self, sample_rate: int) -> int:
        """현재 버퍼 크기 (샘플 수)"""
        return int(sample_rate * self.current_buffer_ms / 1000)
