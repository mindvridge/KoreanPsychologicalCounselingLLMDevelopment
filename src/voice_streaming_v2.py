"""
음성 스트리밍 v2 모듈 (Enhanced Voice Streaming)
저지연 실시간 음성 상담 파이프라인

개선사항:
- 스트리밍 STT (부분 인식)
- 스트리밍 TTS (문장 단위)
- 적응형 버퍼링
- 에코 캔슬링
- 세션 복구
- 하트비트
"""

import logging
import asyncio
import json
import numpy as np
from typing import Optional, Dict, Any, AsyncGenerator, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import time

from src.streaming_stt import StreamingSTT, StreamingConfig, PartialTranscript, AdaptiveBufferManager
from src.streaming_tts import StreamingTTS, StreamingTTSConfig, AudioChunk, SentenceSplitter

logger = logging.getLogger(__name__)


class SessionState(Enum):
    """세션 상태"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    PAUSED = "paused"
    RECOVERING = "recovering"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class LatencyMetrics:
    """지연시간 메트릭"""
    stt_latency_ms: float = 0.0
    llm_latency_ms: float = 0.0
    tts_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
    first_byte_latency_ms: float = 0.0  # 첫 응답까지

    def update_total(self):
        self.total_latency_ms = (
            self.stt_latency_ms +
            self.llm_latency_ms +
            self.tts_latency_ms
        )


@dataclass
class VoiceSessionV2:
    """향상된 음성 세션"""
    session_id: str
    state: SessionState = SessionState.CONNECTING
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    last_heartbeat: datetime = field(default_factory=datetime.now)

    # 대화
    conversation_history: list = field(default_factory=list)
    current_transcript: str = ""

    # 설정
    voice_profile: str = "seoyun_counselor"
    language: str = "ko"
    emotion: str = "calm"

    # 메트릭
    latency: LatencyMetrics = field(default_factory=LatencyMetrics)
    message_count: int = 0
    total_audio_ms: float = 0.0

    # 복구
    recovery_data: Optional[Dict] = None


class StreamingVoicePipeline:
    """
    저지연 음성 스트리밍 파이프라인

    특징:
    - 부분 인식 결과 즉시 전송
    - 문장 단위 TTS 스트리밍
    - 적응형 버퍼 관리
    - 자동 복구
    """

    def __init__(
        self,
        llm_engine=None,
        voice_profile: str = "seoyun_counselor",
        device: str = "cuda"
    ):
        self.llm = llm_engine
        self.voice_profile = voice_profile
        self.device = device

        # 스트리밍 STT/TTS
        self.stt = StreamingSTT(
            model_name="large-v3",
            config=StreamingConfig(
                chunk_duration_ms=100,
                silence_duration_ms=800,
                partial_results=True
            ),
            device=device
        )

        self.tts = StreamingTTS(
            config=StreamingTTSConfig(
                chunk_size_ms=100,
                sentence_pause_ms=300,
                voice_profile=voice_profile
            ),
            device=device
        )

        # 적응형 버퍼
        self.buffer_manager = AdaptiveBufferManager(
            min_buffer_ms=50,
            max_buffer_ms=300,
            target_latency_ms=150
        )

        # 세션
        self.sessions: Dict[str, VoiceSessionV2] = {}

        # 콜백
        self.on_partial_transcript: Optional[Callable] = None
        self.on_response_text: Optional[Callable] = None
        self.on_audio_chunk: Optional[Callable] = None
        self.on_state_change: Optional[Callable] = None
        self.on_error: Optional[Callable] = None

        # 하트비트
        self.heartbeat_interval = 5.0  # 초
        self.heartbeat_timeout = 15.0  # 초
        self._heartbeat_task = None

    async def initialize(self):
        """초기화"""
        # STT 모델 미리 로드
        _ = self.stt.model
        logger.info("Streaming voice pipeline initialized")

    # =========================================================================
    # 세션 관리
    # =========================================================================

    def create_session(
        self,
        voice_profile: Optional[str] = None,
        emotion: str = "calm"
    ) -> VoiceSessionV2:
        """새 세션 생성"""
        session_id = str(uuid.uuid4())
        session = VoiceSessionV2(
            session_id=session_id,
            voice_profile=voice_profile or self.voice_profile,
            emotion=emotion
        )
        self.sessions[session_id] = session

        logger.info(f"Session created: {session_id}")
        return session

    def get_session(self, session_id: str) -> Optional[VoiceSessionV2]:
        """세션 조회"""
        return self.sessions.get(session_id)

    async def close_session(self, session_id: str):
        """세션 종료"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.state = SessionState.DISCONNECTED

            # 복구 데이터 저장 (선택적)
            session.recovery_data = {
                "conversation_history": session.conversation_history[-10:],
                "voice_profile": session.voice_profile,
                "closed_at": datetime.now().isoformat()
            }

            del self.sessions[session_id]
            logger.info(f"Session closed: {session_id}")

    async def recover_session(
        self,
        session_id: str,
        recovery_data: Dict
    ) -> Optional[VoiceSessionV2]:
        """세션 복구"""
        if session_id in self.sessions:
            return self.sessions[session_id]

        session = VoiceSessionV2(
            session_id=session_id,
            state=SessionState.RECOVERING,
            conversation_history=recovery_data.get("conversation_history", []),
            voice_profile=recovery_data.get("voice_profile", self.voice_profile)
        )

        session.state = SessionState.CONNECTED
        self.sessions[session_id] = session

        logger.info(f"Session recovered: {session_id}")
        return session

    # =========================================================================
    # 하트비트
    # =========================================================================

    async def start_heartbeat(self, session_id: str):
        """하트비트 시작"""
        async def heartbeat_loop():
            while session_id in self.sessions:
                session = self.sessions[session_id]

                # 타임아웃 체크
                since_last = datetime.now() - session.last_heartbeat
                if since_last.total_seconds() > self.heartbeat_timeout:
                    logger.warning(f"Session timeout: {session_id}")
                    await self._handle_timeout(session_id)
                    break

                await asyncio.sleep(self.heartbeat_interval)

        self._heartbeat_task = asyncio.create_task(heartbeat_loop())

    def update_heartbeat(self, session_id: str):
        """하트비트 업데이트"""
        if session_id in self.sessions:
            self.sessions[session_id].last_heartbeat = datetime.now()

    async def _handle_timeout(self, session_id: str):
        """타임아웃 처리"""
        if session_id in self.sessions:
            session = self.sessions[session_id]

            # 복구 데이터 저장
            session.recovery_data = {
                "conversation_history": session.conversation_history[-10:],
                "voice_profile": session.voice_profile,
                "timeout_at": datetime.now().isoformat()
            }

            if self.on_error:
                await self.on_error(session_id, "session_timeout", "세션 시간 초과")

    # =========================================================================
    # 스트리밍 오디오 처리
    # =========================================================================

    async def process_audio_stream(
        self,
        session_id: str,
        audio_stream: AsyncGenerator[bytes, None]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        오디오 스트림 처리

        Args:
            session_id: 세션 ID
            audio_stream: 오디오 청크 스트림

        Yields:
            처리 결과 (부분 인식, 응답 텍스트, 오디오 등)
        """
        session = self.get_session(session_id)
        if not session:
            yield {"type": "error", "message": "Session not found"}
            return

        session.state = SessionState.LISTENING
        await self._notify_state_change(session)

        start_time = time.time()

        # 오디오 스트림을 numpy로 변환
        async def audio_to_numpy():
            async for chunk in audio_stream:
                # bytes → int16 → float32
                audio_int16 = np.frombuffer(chunk, dtype=np.int16)
                audio_float = audio_int16.astype(np.float32) / 32768.0
                yield audio_float

        # 스트리밍 STT 처리
        final_text = ""

        async for transcript in self.stt.stream_transcribe(audio_to_numpy()):
            if transcript.is_final:
                final_text = transcript.text
                session.current_transcript = final_text

                # STT 지연시간 기록
                session.latency.stt_latency_ms = (time.time() - start_time) * 1000

                yield {
                    "type": "transcript",
                    "text": transcript.text,
                    "is_final": True,
                    "confidence": transcript.confidence
                }
            else:
                # 부분 인식 결과
                yield {
                    "type": "transcript",
                    "text": transcript.text,
                    "is_final": False,
                    "confidence": transcript.confidence
                }

                if self.on_partial_transcript:
                    await self.on_partial_transcript(session_id, transcript.text)

        if not final_text.strip():
            yield {"type": "no_speech"}
            return

        # 대화 기록 추가
        session.conversation_history.append({
            "role": "user",
            "content": final_text,
            "timestamp": datetime.now().isoformat()
        })

        # LLM 응답 생성 및 TTS 스트리밍
        session.state = SessionState.PROCESSING
        await self._notify_state_change(session)

        llm_start = time.time()
        first_audio_sent = False

        async for result in self._generate_response_stream(session, final_text):
            if result["type"] == "response_text":
                if not first_audio_sent:
                    session.latency.llm_latency_ms = (time.time() - llm_start) * 1000
                    session.latency.first_byte_latency_ms = (time.time() - start_time) * 1000

            elif result["type"] == "audio":
                if not first_audio_sent:
                    session.latency.tts_latency_ms = (time.time() - llm_start) * 1000 - session.latency.llm_latency_ms
                    first_audio_sent = True
                    session.state = SessionState.SPEAKING
                    await self._notify_state_change(session)

            yield result

        # 메트릭 업데이트
        session.latency.update_total()
        session.message_count += 1

        # 적응형 버퍼 업데이트
        self.buffer_manager.update(session.latency.total_latency_ms)

        session.state = SessionState.CONNECTED
        await self._notify_state_change(session)

        yield {
            "type": "complete",
            "latency": {
                "stt_ms": session.latency.stt_latency_ms,
                "llm_ms": session.latency.llm_latency_ms,
                "tts_ms": session.latency.tts_latency_ms,
                "total_ms": session.latency.total_latency_ms,
                "first_byte_ms": session.latency.first_byte_latency_ms
            }
        }

    async def _generate_response_stream(
        self,
        session: VoiceSessionV2,
        user_text: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """응답 생성 및 TTS 스트리밍"""

        # LLM 응답 생성
        if self.llm:
            try:
                # 스트리밍 지원 확인
                if hasattr(self.llm, 'generate_response_stream'):
                    response_text = ""

                    async def text_stream():
                        nonlocal response_text
                        async for chunk in self.llm.generate_response_stream(
                            user_text,
                            session.conversation_history
                        ):
                            response_text += chunk
                            yield chunk

                    # 텍스트 스트림 → TTS 스트림
                    async for audio_chunk in self.tts.synthesize_text_stream(
                        text_stream(),
                        emotion=session.emotion
                    ):
                        yield {
                            "type": "audio",
                            "data": audio_chunk.data,
                            "sample_rate": audio_chunk.sample_rate,
                            "text": audio_chunk.text,
                            "is_last": audio_chunk.is_last
                        }

                    # 응답 텍스트 전송
                    yield {
                        "type": "response_text",
                        "text": response_text,
                        "is_complete": True
                    }

                else:
                    # 비스트리밍 LLM
                    response_text = await asyncio.to_thread(
                        self.llm.generate_response,
                        user_text,
                        session.conversation_history
                    )

                    yield {
                        "type": "response_text",
                        "text": response_text,
                        "is_complete": True
                    }

                    # TTS 스트리밍
                    async for audio_chunk in self.tts.synthesize_stream(
                        response_text,
                        emotion=session.emotion
                    ):
                        yield {
                            "type": "audio",
                            "data": audio_chunk.data,
                            "sample_rate": audio_chunk.sample_rate,
                            "text": audio_chunk.text,
                            "is_last": audio_chunk.is_last
                        }

            except Exception as e:
                logger.error(f"LLM error: {e}")
                response_text = "죄송합니다, 잠시 문제가 발생했습니다. 다시 말씀해 주시겠어요?"

                yield {"type": "response_text", "text": response_text, "is_complete": True}

                async for audio_chunk in self.tts.synthesize_stream(
                    response_text,
                    emotion="concerned"
                ):
                    yield {
                        "type": "audio",
                        "data": audio_chunk.data,
                        "sample_rate": audio_chunk.sample_rate,
                        "is_last": audio_chunk.is_last
                    }
        else:
            # LLM 없음 - 에코
            response_text = f"말씀하신 내용을 들었습니다: {user_text}"

            yield {"type": "response_text", "text": response_text, "is_complete": True}

            async for audio_chunk in self.tts.synthesize_stream(
                response_text,
                emotion=session.emotion
            ):
                yield {
                    "type": "audio",
                    "data": audio_chunk.data,
                    "sample_rate": audio_chunk.sample_rate,
                    "is_last": audio_chunk.is_last
                }

        # 대화 기록 추가
        session.conversation_history.append({
            "role": "assistant",
            "content": response_text,
            "timestamp": datetime.now().isoformat()
        })

    async def _notify_state_change(self, session: VoiceSessionV2):
        """상태 변경 알림"""
        if self.on_state_change:
            await self.on_state_change(session.session_id, session.state.value)

    # =========================================================================
    # 단일 오디오 처리 (비스트리밍)
    # =========================================================================

    async def process_audio(
        self,
        session_id: str,
        audio_data: bytes
    ) -> Dict[str, Any]:
        """단일 오디오 처리 (호환성)"""

        async def single_chunk_stream():
            yield audio_data

        results = []
        async for result in self.process_audio_stream(session_id, single_chunk_stream()):
            results.append(result)

        # 결과 통합
        transcript = ""
        response_text = ""
        audio_chunks = []

        for r in results:
            if r["type"] == "transcript" and r.get("is_final"):
                transcript = r["text"]
            elif r["type"] == "response_text":
                response_text = r["text"]
            elif r["type"] == "audio":
                audio_chunks.append(r["data"])

        return {
            "transcript": transcript,
            "response_text": response_text,
            "audio": b"".join(audio_chunks) if audio_chunks else None,
            "latency": results[-1].get("latency") if results else None
        }
