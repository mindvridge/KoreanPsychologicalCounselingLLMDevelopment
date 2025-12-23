"""
스트리밍 TTS 모듈 (Streaming Text-to-Speech)
문장 단위 실시간 음성 합성

특징:
- 문장 단위 즉시 합성 (First-byte latency 최소화)
- 청크 스트리밍 출력
- 감정 기반 음성 조절
- 음성 큐 관리
"""

import logging
import asyncio
import numpy as np
import re
from typing import Optional, AsyncGenerator, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
import threading
import queue
import io

logger = logging.getLogger(__name__)


@dataclass
class AudioChunk:
    """오디오 청크"""
    data: bytes
    sample_rate: int
    duration_ms: float
    text: str
    is_last: bool = False
    emotion: Optional[str] = None


@dataclass
class StreamingTTSConfig:
    """스트리밍 TTS 설정"""
    sample_rate: int = 24000
    chunk_size_ms: int = 100  # 출력 청크 크기
    sentence_pause_ms: int = 300  # 문장 사이 휴지
    voice_profile: str = "seoyun_counselor"
    default_emotion: str = "calm"
    speed: float = 1.0
    enable_ssml: bool = False


class SentenceSplitter:
    """한국어 문장 분리기"""

    # 문장 종결 패턴
    SENTENCE_END_PATTERN = re.compile(
        r'(?<=[.!?。！？])\s+|'  # 마침표 후 공백
        r'(?<=[요다죠])[.!?]?\s+|'  # 한국어 종결어미 후
        r'(?<=니다|세요|해요|군요|네요)[.!?]?\s*'  # 정중 종결
    )

    # 최소/최대 문장 길이
    MIN_SENTENCE_LENGTH = 5
    MAX_SENTENCE_LENGTH = 100

    @classmethod
    def split(cls, text: str) -> List[str]:
        """텍스트를 문장으로 분리"""
        if not text:
            return []

        # 기본 분리
        sentences = cls.SENTENCE_END_PATTERN.split(text)
        sentences = [s.strip() for s in sentences if s.strip()]

        # 너무 긴 문장 추가 분리
        result = []
        for sentence in sentences:
            if len(sentence) > cls.MAX_SENTENCE_LENGTH:
                # 쉼표나 접속사로 추가 분리
                parts = re.split(r'[,，、]|(?<=고\s)|(?<=며\s)|(?<=서\s)', sentence)
                parts = [p.strip() for p in parts if p.strip()]
                result.extend(parts)
            elif len(sentence) >= cls.MIN_SENTENCE_LENGTH:
                result.append(sentence)

        return result

    @classmethod
    async def stream_split(
        cls,
        text_stream: AsyncGenerator[str, None]
    ) -> AsyncGenerator[str, None]:
        """텍스트 스트림에서 문장 단위로 분리"""
        buffer = ""

        async for chunk in text_stream:
            buffer += chunk

            # 완성된 문장 추출
            while True:
                match = cls.SENTENCE_END_PATTERN.search(buffer)
                if match:
                    sentence = buffer[:match.end()].strip()
                    buffer = buffer[match.end():]

                    if len(sentence) >= cls.MIN_SENTENCE_LENGTH:
                        yield sentence
                else:
                    break

        # 남은 텍스트
        if buffer.strip() and len(buffer.strip()) >= cls.MIN_SENTENCE_LENGTH:
            yield buffer.strip()


class StreamingTTS:
    """
    스트리밍 텍스트-음성 변환

    텍스트를 문장 단위로 즉시 합성하여 스트리밍
    """

    def __init__(
        self,
        config: Optional[StreamingTTSConfig] = None,
        device: str = "cuda"
    ):
        self.config = config or StreamingTTSConfig()
        self.device = device

        # TTS 엔진 (지연 로딩)
        self._engine = None
        self._engine_lock = threading.Lock()

        # 음성 프로필 캐시
        self._voice_cache = {}

        # 합성 큐
        self.synthesis_queue = asyncio.Queue()
        self.output_queue = asyncio.Queue()

        # 상태
        self.is_synthesizing = False

    @property
    def engine(self):
        """TTS 엔진 지연 로딩"""
        if self._engine is None:
            with self._engine_lock:
                if self._engine is None:
                    self._load_engine()
        return self._engine

    def _load_engine(self):
        """TTS 엔진 로드"""
        # TTS 엔진 선택 (환경 변수 또는 설정에서)
        import os
        tts_engine_type = os.getenv("TTS_ENGINE", "zonos")  # 기본값: zonos
        
        if tts_engine_type == "elevenlabs":
            try:
                from src.elevenlabs_tts import ElevenLabsTTS, ElevenLabsConfig
                api_key = os.getenv("ELEVENLABS_API_KEY")
                if api_key:
                    config = ElevenLabsConfig(api_key=api_key)
                    self._engine = ElevenLabsTTS(config)
                    logger.info("ElevenLabs TTS 엔진 로드 완료 (스트리밍 지원)")
                else:
                    logger.warning("ElevenLabs API 키가 없어 Zonos TTS로 폴백")
                    tts_engine_type = "zonos"
            except Exception as e:
                logger.warning(f"ElevenLabs TTS 로드 실패, Zonos로 폴백: {e}")
                tts_engine_type = "zonos"
        
        if tts_engine_type == "zonos":
            try:
                # Zonos TTS 시도
                from src.tts import ZonosTTS
                self._engine = ZonosTTS(device=self.device)
                logger.info("Zonos TTS 엔진 로드 완료")

            except Exception as e:
                logger.warning(f"Zonos TTS 로드 실패, gTTS 사용: {e}")
                # Fallback to gTTS (online)
                self._engine = None

    async def synthesize_stream(
        self,
        text: str,
        emotion: Optional[str] = None
    ) -> AsyncGenerator[AudioChunk, None]:
        """
        텍스트 스트리밍 합성

        Args:
            text: 합성할 텍스트
            emotion: 감정 (calm, empathetic, encouraging, supportive)

        Yields:
            오디오 청크
        """
        emotion = emotion or self.config.default_emotion

        # 문장 분리
        sentences = SentenceSplitter.split(text)

        if not sentences:
            return

        for i, sentence in enumerate(sentences):
            is_last = (i == len(sentences) - 1)

            # 문장 합성
            audio_data = await self._synthesize_sentence(sentence, emotion)

            if audio_data is not None:
                # 청크로 분할하여 출력
                async for chunk in self._chunk_audio(
                    audio_data,
                    sentence,
                    is_last,
                    emotion
                ):
                    yield chunk

                # 문장 사이 휴지
                if not is_last:
                    pause_samples = int(
                        self.config.sample_rate *
                        self.config.sentence_pause_ms / 1000
                    )
                    pause_audio = np.zeros(pause_samples, dtype=np.float32)
                    yield AudioChunk(
                        data=pause_audio.tobytes(),
                        sample_rate=self.config.sample_rate,
                        duration_ms=self.config.sentence_pause_ms,
                        text="",
                        is_last=False,
                        emotion=emotion
                    )

    async def synthesize_text_stream(
        self,
        text_stream: AsyncGenerator[str, None],
        emotion: Optional[str] = None
    ) -> AsyncGenerator[AudioChunk, None]:
        """
        텍스트 스트림을 음성으로 변환

        LLM의 스트리밍 출력을 실시간으로 음성으로 변환

        Args:
            text_stream: 텍스트 스트림 (LLM 출력)
            emotion: 감정

        Yields:
            오디오 청크
        """
        emotion = emotion or self.config.default_emotion

        async for sentence in SentenceSplitter.stream_split(text_stream):
            audio_data = await self._synthesize_sentence(sentence, emotion)

            if audio_data is not None:
                async for chunk in self._chunk_audio(
                    audio_data,
                    sentence,
                    False,  # 스트림이므로 마지막 판단 어려움
                    emotion
                ):
                    yield chunk

    async def _synthesize_sentence(
        self,
        sentence: str,
        emotion: str
    ) -> Optional[np.ndarray]:
        """단일 문장 합성"""
        try:
            if self.engine is None:
                # Fallback: gTTS 사용
                return await self._synthesize_gtts(sentence)

            # ElevenLabs TTS인 경우 스트리밍 지원
            if hasattr(self.engine, 'synthesize_stream'):
                # ElevenLabs 스트리밍 사용
                loop = asyncio.get_event_loop()
                audio_chunks = []
                
                def collect_stream():
                    nonlocal audio_chunks
                    try:
                        for chunk in self.engine.synthesize_stream(sentence, emotion=emotion):
                            audio_chunks.append(chunk)
                    except Exception as e:
                        logger.error(f"ElevenLabs 스트리밍 오류: {e}")
                        raise
                
                await loop.run_in_executor(None, collect_stream)
                
                # 모든 청크를 합치기
                if audio_chunks:
                    import soundfile as sf
                    import librosa
                    all_audio = b''.join(audio_chunks)
                    audio_data, sample_rate = sf.read(io.BytesIO(all_audio))
                    
                    # 샘플 레이트 변환 (필요한 경우)
                    if sample_rate != 44100:
                        audio_data = librosa.resample(
                            audio_data,
                            orig_sr=sample_rate,
                            target_sr=44100
                        )
                    
                    return audio_data.astype(np.float32)
                return None

            # Zonos TTS 사용
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._run_synthesis,
                sentence,
                emotion
            )

            return result

        except Exception as e:
            logger.error(f"문장 합성 오류: {e}")
            return None

    def _run_synthesis(
        self,
        text: str,
        emotion: str
    ) -> Optional[np.ndarray]:
        """실제 합성 수행 (동기)"""
        try:
            # 음성 프로필 설정
            voice_settings = self._get_emotion_settings(emotion)

            result = self.engine.synthesize(
                text=text,
                voice_profile=self.config.voice_profile,
                speed=self.config.speed * voice_settings.get("speed_factor", 1.0),
                emotion=emotion
            )

            if result and hasattr(result, 'audio'):
                return result.audio

        except Exception as e:
            logger.error(f"Synthesis error: {e}")

        return None

    async def _synthesize_gtts(self, text: str) -> Optional[np.ndarray]:
        """gTTS를 사용한 폴백 합성"""
        try:
            from gtts import gTTS
            import tempfile
            import soundfile as sf

            loop = asyncio.get_event_loop()

            def _generate():
                tts = gTTS(text=text, lang='ko')
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                    tts.save(f.name)
                    return f.name

            mp3_path = await loop.run_in_executor(None, _generate)

            # MP3 → numpy
            audio, sr = sf.read(mp3_path)

            # 리샘플링 (필요시)
            if sr != self.config.sample_rate:
                import librosa
                audio = librosa.resample(
                    audio,
                    orig_sr=sr,
                    target_sr=self.config.sample_rate
                )

            return audio.astype(np.float32)

        except Exception as e:
            logger.error(f"gTTS error: {e}")
            return None

    def _get_emotion_settings(self, emotion: str) -> dict:
        """감정별 음성 설정"""
        settings = {
            "calm": {"speed_factor": 0.95, "pitch_shift": 0},
            "empathetic": {"speed_factor": 0.90, "pitch_shift": -0.5},
            "encouraging": {"speed_factor": 1.05, "pitch_shift": 0.5},
            "supportive": {"speed_factor": 0.95, "pitch_shift": 0},
            "concerned": {"speed_factor": 0.90, "pitch_shift": -0.3}
        }
        return settings.get(emotion, settings["calm"])

    async def _chunk_audio(
        self,
        audio: np.ndarray,
        text: str,
        is_last: bool,
        emotion: str
    ) -> AsyncGenerator[AudioChunk, None]:
        """오디오를 청크로 분할"""
        chunk_samples = int(
            self.config.sample_rate * self.config.chunk_size_ms / 1000
        )

        total_samples = len(audio)
        offset = 0

        while offset < total_samples:
            end = min(offset + chunk_samples, total_samples)
            chunk_data = audio[offset:end]

            chunk_is_last = is_last and (end >= total_samples)

            yield AudioChunk(
                data=chunk_data.astype(np.float32).tobytes(),
                sample_rate=self.config.sample_rate,
                duration_ms=len(chunk_data) / self.config.sample_rate * 1000,
                text=text if offset == 0 else "",
                is_last=chunk_is_last,
                emotion=emotion
            )

            offset = end

            # 다른 태스크에 양보
            await asyncio.sleep(0)


class AudioOutputBuffer:
    """
    오디오 출력 버퍼

    지터 보상 및 부드러운 재생을 위한 버퍼 관리
    """

    def __init__(
        self,
        sample_rate: int = 24000,
        buffer_duration_ms: int = 200,
        min_buffer_ms: int = 100
    ):
        self.sample_rate = sample_rate
        self.buffer_duration_ms = buffer_duration_ms
        self.min_buffer_ms = min_buffer_ms

        self.buffer = deque()
        self.total_samples = 0
        self.is_playing = False

        self._lock = threading.Lock()

    def add(self, audio_chunk: AudioChunk):
        """오디오 청크 추가"""
        with self._lock:
            self.buffer.append(audio_chunk)
            self.total_samples += len(audio_chunk.data) // 4  # float32 = 4 bytes

    def get_playable(self) -> Optional[bytes]:
        """재생 가능한 오디오 가져오기"""
        with self._lock:
            if not self.buffer:
                return None

            # 최소 버퍼 확인
            min_samples = int(self.sample_rate * self.min_buffer_ms / 1000)

            if not self.is_playing and self.total_samples < min_samples:
                return None

            self.is_playing = True

            # 청크 추출
            chunk = self.buffer.popleft()
            self.total_samples -= len(chunk.data) // 4

            return chunk.data

    def clear(self):
        """버퍼 비우기"""
        with self._lock:
            self.buffer.clear()
            self.total_samples = 0
            self.is_playing = False

    @property
    def buffered_duration_ms(self) -> float:
        """버퍼된 오디오 시간 (ms)"""
        return self.total_samples / self.sample_rate * 1000
