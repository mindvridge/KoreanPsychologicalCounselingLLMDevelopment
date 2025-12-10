"""
음성 처리 최적화 모듈 (Voice Processing Optimization)
지연시간 3초 이내 목표

최적화 전략:
1. 파이프라인 병렬화 - STT/LLM/TTS 동시 처리
2. 예측적 버퍼링 - 다음 청크 미리 준비
3. 모델 웜업 - 콜드 스타트 방지
4. 메모리 풀링 - GC 오버헤드 감소
5. 적응형 품질 - 네트워크 상태에 따른 품질 조절
"""

import logging
import asyncio
import numpy as np
from typing import Optional, Dict, Any, AsyncGenerator, List, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
import time
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


# ============================================================================
# 최적화 설정
# ============================================================================

@dataclass
class OptimizationConfig:
    """최적화 설정"""
    # 지연시간 목표 (밀리초)
    target_latency_ms: int = 3000
    max_latency_ms: int = 5000

    # STT 최적화
    stt_chunk_duration_ms: int = 100  # 더 작은 청크 = 빠른 응답
    stt_vad_threshold: float = 0.5
    stt_silence_timeout_ms: int = 500

    # TTS 최적화
    tts_sentence_buffer_size: int = 2  # 미리 준비할 문장 수
    tts_audio_sample_rate: int = 22050  # 낮은 샘플레이트 = 빠른 처리

    # 버퍼 설정
    audio_buffer_ms: int = 200
    prefetch_enabled: bool = True

    # 병렬 처리
    max_workers: int = 4

    # 적응형 품질
    adaptive_quality: bool = True
    min_quality: float = 0.5
    max_quality: float = 1.0


@dataclass
class LatencyStats:
    """지연시간 통계"""
    samples: deque = field(default_factory=lambda: deque(maxlen=100))

    def add_sample(self, latency_ms: float):
        self.samples.append(latency_ms)

    @property
    def average(self) -> float:
        return sum(self.samples) / len(self.samples) if self.samples else 0

    @property
    def p95(self) -> float:
        if not self.samples:
            return 0
        sorted_samples = sorted(self.samples)
        idx = int(len(sorted_samples) * 0.95)
        return sorted_samples[min(idx, len(sorted_samples) - 1)]

    @property
    def max(self) -> float:
        return max(self.samples) if self.samples else 0


# ============================================================================
# 메모리 풀
# ============================================================================

class AudioBufferPool:
    """
    오디오 버퍼 풀
    GC 오버헤드 감소를 위한 재사용 가능한 버퍼
    """

    def __init__(self, buffer_size: int = 4096, pool_size: int = 32):
        self.buffer_size = buffer_size
        self.pool: deque = deque()
        self.lock = threading.Lock()

        # 미리 버퍼 생성
        for _ in range(pool_size):
            self.pool.append(np.zeros(buffer_size, dtype=np.float32))

    def acquire(self) -> np.ndarray:
        """버퍼 획득"""
        with self.lock:
            if self.pool:
                return self.pool.popleft()
            return np.zeros(self.buffer_size, dtype=np.float32)

    def release(self, buffer: np.ndarray):
        """버퍼 반환"""
        with self.lock:
            buffer.fill(0)  # 초기화
            self.pool.append(buffer)


# ============================================================================
# 모델 웜업 관리자
# ============================================================================

class ModelWarmupManager:
    """
    모델 웜업 관리
    콜드 스타트 방지
    """

    def __init__(self):
        self.warmed_up = {
            "stt": False,
            "tts": False,
            "llm": False
        }
        self.warmup_times: Dict[str, float] = {}

    async def warmup_stt(self, stt_model):
        """STT 모델 웜업"""
        if self.warmed_up["stt"]:
            return

        start = time.time()
        try:
            # 더미 오디오로 웜업
            dummy_audio = np.zeros(16000, dtype=np.float32)  # 1초
            if hasattr(stt_model, 'transcribe'):
                await asyncio.to_thread(stt_model.transcribe, dummy_audio)
            self.warmed_up["stt"] = True
            self.warmup_times["stt"] = time.time() - start
            logger.info(f"STT warmup completed in {self.warmup_times['stt']:.2f}s")
        except Exception as e:
            logger.error(f"STT warmup failed: {e}")

    async def warmup_tts(self, tts_model):
        """TTS 모델 웜업"""
        if self.warmed_up["tts"]:
            return

        start = time.time()
        try:
            # 짧은 텍스트로 웜업
            if hasattr(tts_model, 'synthesize'):
                await asyncio.to_thread(tts_model.synthesize, "안녕하세요")
            self.warmed_up["tts"] = True
            self.warmup_times["tts"] = time.time() - start
            logger.info(f"TTS warmup completed in {self.warmup_times['tts']:.2f}s")
        except Exception as e:
            logger.error(f"TTS warmup failed: {e}")

    async def warmup_llm(self, llm_model):
        """LLM 모델 웜업"""
        if self.warmed_up["llm"]:
            return

        start = time.time()
        try:
            if hasattr(llm_model, 'generate'):
                await asyncio.to_thread(
                    llm_model.generate,
                    "안녕하세요",
                    max_new_tokens=10
                )
            self.warmed_up["llm"] = True
            self.warmup_times["llm"] = time.time() - start
            logger.info(f"LLM warmup completed in {self.warmup_times['llm']:.2f}s")
        except Exception as e:
            logger.error(f"LLM warmup failed: {e}")

    async def warmup_all(self, stt_model=None, tts_model=None, llm_model=None):
        """모든 모델 병렬 웜업"""
        tasks = []
        if stt_model:
            tasks.append(self.warmup_stt(stt_model))
        if tts_model:
            tasks.append(self.warmup_tts(tts_model))
        if llm_model:
            tasks.append(self.warmup_llm(llm_model))

        await asyncio.gather(*tasks)
        logger.info("All models warmed up")


# ============================================================================
# 병렬 파이프라인
# ============================================================================

class ParallelVoicePipeline:
    """
    병렬 처리 음성 파이프라인

    처리 흐름:
    Audio In → [STT] → [LLM] → [TTS] → Audio Out
                ↓        ↓        ↓
           [부분결과] [스트림] [청크출력]

    병렬화:
    - STT: 청크 단위 병렬 처리
    - LLM: 토큰 스트리밍
    - TTS: 문장 단위 병렬 합성
    """

    def __init__(
        self,
        config: OptimizationConfig = None,
        stt_model=None,
        tts_model=None,
        llm_model=None
    ):
        self.config = config or OptimizationConfig()
        self.stt = stt_model
        self.tts = tts_model
        self.llm = llm_model

        # 메모리 풀
        self.buffer_pool = AudioBufferPool()

        # 웜업 관리자
        self.warmup_manager = ModelWarmupManager()

        # 스레드 풀
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_workers)

        # 통계
        self.latency_stats = LatencyStats()

        # 상태
        self.is_processing = False
        self.current_quality = 1.0

    async def initialize(self):
        """파이프라인 초기화 (웜업 포함)"""
        await self.warmup_manager.warmup_all(
            self.stt, self.tts, self.llm
        )

    async def process_audio_optimized(
        self,
        audio_stream: AsyncGenerator[bytes, None],
        on_partial_transcript: Optional[Callable] = None,
        on_response_start: Optional[Callable] = None,
        on_audio_chunk: Optional[Callable] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        최적화된 오디오 처리

        Args:
            audio_stream: 입력 오디오 스트림
            on_partial_transcript: 부분 인식 콜백
            on_response_start: 응답 시작 콜백
            on_audio_chunk: 오디오 청크 콜백

        Yields:
            처리 결과
        """
        self.is_processing = True
        start_time = time.time()
        first_response_time = None

        try:
            # 1. STT 처리 (부분 결과 스트리밍)
            transcript_parts = []

            async for audio_chunk in audio_stream:
                if not self.is_processing:
                    break

                # STT 처리
                stt_start = time.time()
                partial_result = await self._process_stt_chunk(audio_chunk)
                stt_latency = (time.time() - stt_start) * 1000

                if partial_result:
                    transcript_parts.append(partial_result)

                    if on_partial_transcript:
                        await on_partial_transcript(partial_result)

                    yield {
                        "type": "partial_transcript",
                        "text": partial_result,
                        "latency_ms": stt_latency
                    }

            # 전체 트랜스크립트
            full_transcript = " ".join(transcript_parts)

            if not full_transcript.strip():
                return

            # 2. LLM 처리 (토큰 스트리밍)
            llm_start = time.time()
            response_text = ""

            if on_response_start:
                await on_response_start()

            async for token in self._stream_llm_response(full_transcript):
                response_text += token

                if first_response_time is None:
                    first_response_time = time.time()
                    first_byte_latency = (first_response_time - start_time) * 1000
                    yield {
                        "type": "first_byte",
                        "latency_ms": first_byte_latency
                    }

                yield {
                    "type": "token",
                    "text": token
                }

            llm_latency = (time.time() - llm_start) * 1000

            # 3. TTS 처리 (문장 병렬 합성)
            tts_start = time.time()

            async for audio_chunk in self._stream_tts_parallel(response_text):
                if on_audio_chunk:
                    await on_audio_chunk(audio_chunk)

                yield {
                    "type": "audio",
                    "data": audio_chunk,
                    "sample_rate": self.config.tts_audio_sample_rate
                }

            tts_latency = (time.time() - tts_start) * 1000

            # 총 지연시간
            total_latency = (time.time() - start_time) * 1000
            self.latency_stats.add_sample(total_latency)

            # 적응형 품질 조절
            if self.config.adaptive_quality:
                self._adjust_quality(total_latency)

            yield {
                "type": "complete",
                "transcript": full_transcript,
                "response": response_text,
                "latency": {
                    "stt_ms": stt_latency,
                    "llm_ms": llm_latency,
                    "tts_ms": tts_latency,
                    "total_ms": total_latency,
                    "first_byte_ms": first_byte_latency if first_response_time else None
                }
            }

        finally:
            self.is_processing = False

    async def _process_stt_chunk(self, audio_chunk: bytes) -> Optional[str]:
        """STT 청크 처리"""
        if not self.stt:
            return None

        try:
            # 바이트 → numpy 변환
            audio_array = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32)
            audio_array /= 32768.0  # 정규화

            # STT 처리
            result = await asyncio.to_thread(
                self.stt.transcribe,
                audio_array
            )

            if hasattr(result, 'text'):
                return result.text
            return str(result) if result else None

        except Exception as e:
            logger.error(f"STT processing error: {e}")
            return None

    async def _stream_llm_response(
        self,
        text: str
    ) -> AsyncGenerator[str, None]:
        """LLM 응답 스트리밍"""
        if not self.llm:
            yield f"[응답] {text}"
            return

        try:
            # 스트리밍 생성
            if hasattr(self.llm, 'generate_stream'):
                async for token in self.llm.generate_stream(text):
                    yield token
            elif hasattr(self.llm, 'generate'):
                result = await asyncio.to_thread(self.llm.generate, text)
                yield result
            else:
                yield f"[응답] {text}"

        except Exception as e:
            logger.error(f"LLM processing error: {e}")
            yield f"죄송합니다. 잠시 후 다시 시도해주세요."

    async def _stream_tts_parallel(
        self,
        text: str
    ) -> AsyncGenerator[bytes, None]:
        """TTS 병렬 스트리밍"""
        if not self.tts:
            return

        try:
            # 문장 분리
            sentences = self._split_sentences(text)

            # 문장 큐
            sentence_queue = asyncio.Queue()
            for sentence in sentences:
                await sentence_queue.put(sentence)

            # 병렬 합성 작업
            async def synthesize_sentence(sentence: str) -> bytes:
                return await asyncio.to_thread(
                    self.tts.synthesize,
                    sentence,
                    sample_rate=self.config.tts_audio_sample_rate
                )

            # 첫 문장 즉시 처리
            while not sentence_queue.empty():
                sentence = await sentence_queue.get()

                if not sentence.strip():
                    continue

                # 다음 문장 미리 준비 (prefetch)
                next_sentence_task = None
                if self.config.prefetch_enabled and not sentence_queue.empty():
                    next_sentence = await sentence_queue.get()
                    next_sentence_task = asyncio.create_task(
                        synthesize_sentence(next_sentence)
                    )
                    await sentence_queue.put(next_sentence)  # 다시 넣기

                # 현재 문장 합성
                audio = await synthesize_sentence(sentence)

                if audio:
                    yield audio

        except Exception as e:
            logger.error(f"TTS processing error: {e}")

    def _split_sentences(self, text: str) -> List[str]:
        """문장 분리"""
        import re

        # 한국어 문장 분리
        sentences = re.split(r'(?<=[.!?])\s+|(?<=[요다]\.)\s*', text)
        return [s.strip() for s in sentences if s.strip()]

    def _adjust_quality(self, current_latency_ms: float):
        """적응형 품질 조절"""
        target = self.config.target_latency_ms
        max_lat = self.config.max_latency_ms

        if current_latency_ms > max_lat:
            # 품질 낮추기
            self.current_quality = max(
                self.config.min_quality,
                self.current_quality - 0.1
            )
            logger.info(f"Quality reduced to {self.current_quality:.1f}")

        elif current_latency_ms < target * 0.7:
            # 품질 올리기
            self.current_quality = min(
                self.config.max_quality,
                self.current_quality + 0.05
            )

    def get_stats(self) -> Dict[str, Any]:
        """통계 조회"""
        return {
            "average_latency_ms": self.latency_stats.average,
            "p95_latency_ms": self.latency_stats.p95,
            "max_latency_ms": self.latency_stats.max,
            "current_quality": self.current_quality,
            "samples_count": len(self.latency_stats.samples)
        }

    def shutdown(self):
        """정리"""
        self.is_processing = False
        self.executor.shutdown(wait=False)


# ============================================================================
# 빠른 응답 캐시
# ============================================================================

class ResponseCache:
    """
    응답 캐시
    자주 사용되는 응답 캐싱
    """

    def __init__(self, max_size: int = 100):
        self.cache: Dict[str, Tuple[str, bytes]] = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0

    def _normalize_key(self, text: str) -> str:
        """키 정규화"""
        return text.lower().strip()[:100]

    def get(self, text: str) -> Optional[Tuple[str, bytes]]:
        """캐시 조회"""
        key = self._normalize_key(text)
        result = self.cache.get(key)

        if result:
            self.hits += 1
        else:
            self.misses += 1

        return result

    def set(self, text: str, response: str, audio: bytes):
        """캐시 저장"""
        if len(self.cache) >= self.max_size:
            # LRU: 가장 오래된 항목 제거
            oldest = next(iter(self.cache))
            del self.cache[oldest]

        key = self._normalize_key(text)
        self.cache[key] = (response, audio)

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0


# ============================================================================
# 최적화된 음성 서비스
# ============================================================================

class OptimizedVoiceService:
    """
    최적화된 음성 상담 서비스

    목표: 3초 이내 첫 응답
    """

    def __init__(
        self,
        config: OptimizationConfig = None,
        stt_model=None,
        tts_model=None,
        llm_model=None
    ):
        self.config = config or OptimizationConfig()

        # 파이프라인
        self.pipeline = ParallelVoicePipeline(
            config=self.config,
            stt_model=stt_model,
            tts_model=tts_model,
            llm_model=llm_model
        )

        # 캐시
        self.cache = ResponseCache()

        # 버퍼 풀
        self.buffer_pool = AudioBufferPool()

        # 초기화 상태
        self.initialized = False

    async def initialize(self):
        """서비스 초기화"""
        if self.initialized:
            return

        await self.pipeline.initialize()
        self.initialized = True
        logger.info("OptimizedVoiceService initialized")

    async def process_voice(
        self,
        audio_stream: AsyncGenerator[bytes, None],
        session_id: str = None,
        callbacks: Dict[str, Callable] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        음성 처리

        Args:
            audio_stream: 오디오 스트림
            session_id: 세션 ID
            callbacks: 콜백 함수들

        Yields:
            처리 결과
        """
        if not self.initialized:
            await self.initialize()

        callbacks = callbacks or {}

        async for result in self.pipeline.process_audio_optimized(
            audio_stream,
            on_partial_transcript=callbacks.get("on_partial"),
            on_response_start=callbacks.get("on_response_start"),
            on_audio_chunk=callbacks.get("on_audio")
        ):
            yield result

    def get_performance_report(self) -> Dict[str, Any]:
        """성능 리포트"""
        stats = self.pipeline.get_stats()

        return {
            "latency": stats,
            "cache": {
                "hit_rate": f"{self.cache.hit_rate:.1%}",
                "hits": self.cache.hits,
                "misses": self.cache.misses
            },
            "quality": {
                "current": self.pipeline.current_quality,
                "target_latency_ms": self.config.target_latency_ms
            },
            "status": {
                "initialized": self.initialized,
                "target_met": stats["average_latency_ms"] < self.config.target_latency_ms
            }
        }

    async def shutdown(self):
        """서비스 종료"""
        self.pipeline.shutdown()
        logger.info("OptimizedVoiceService shutdown")


# ============================================================================
# 유틸리티
# ============================================================================

def create_optimized_voice_service(
    target_latency_ms: int = 3000,
    stt_model=None,
    tts_model=None,
    llm_model=None
) -> OptimizedVoiceService:
    """최적화된 음성 서비스 생성"""
    config = OptimizationConfig(target_latency_ms=target_latency_ms)
    return OptimizedVoiceService(
        config=config,
        stt_model=stt_model,
        tts_model=tts_model,
        llm_model=llm_model
    )
