"""
음성 스트리밍 모듈 (Voice Streaming)
WebSocket 기반 실시간 음성 상담

기능:
- 실시간 양방향 음성 스트리밍
- 음성→텍스트→LLM→텍스트→음성 파이프라인
- 세션 관리
- 에러 복구
"""

import logging
import asyncio
import json
import base64
from typing import Optional, Dict, Any, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class SessionState(Enum):
    """세션 상태"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    LISTENING = "listening"  # 사용자 음성 수신 중
    PROCESSING = "processing"  # LLM 처리 중
    SPEAKING = "speaking"  # TTS 출력 중
    PAUSED = "paused"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class VoiceMessage:
    """음성 메시지"""
    type: str  # audio, text, control
    data: Any
    timestamp: datetime = field(default_factory=datetime.now)
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


@dataclass
class VoiceSession:
    """음성 상담 세션"""
    session_id: str
    state: SessionState = SessionState.CONNECTING
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)

    # 대화 기록
    conversation_history: list = field(default_factory=list)

    # 설정
    voice_profile: Optional[str] = None
    language: str = "ko"

    # 메트릭
    total_audio_duration: float = 0.0
    message_count: int = 0


class VoiceStreamingPipeline:
    """
    음성 스트리밍 파이프라인

    Audio In → STT → LLM → TTS → Audio Out
    """

    def __init__(
        self,
        stt_engine=None,
        llm_engine=None,
        tts_engine=None,
        voice_profile: Optional[str] = None
    ):
        """
        초기화

        Args:
            stt_engine: STT 엔진 (WhisperSTT)
            llm_engine: LLM 엔진 (CounselingChatbot)
            tts_engine: TTS 엔진 (ZonosTTS)
            voice_profile: 사용할 음성 프로필
        """
        self.stt = stt_engine
        self.llm = llm_engine
        self.tts = tts_engine
        self.voice_profile = voice_profile

        self.sessions: Dict[str, VoiceSession] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """비동기 초기화"""
        if self._initialized:
            return

        # 모듈 로드
        if self.stt is None:
            from stt import WhisperSTT
            self.stt = WhisperSTT()
            await asyncio.to_thread(self.stt.load_model)

        if self.tts is None:
            from tts import ZonosTTS
            self.tts = ZonosTTS()
            await asyncio.to_thread(self.tts.load_model)

        # LLM은 선택적
        if self.llm is None:
            try:
                from main import CounselingChatbot
                self.llm = CounselingChatbot()
                await asyncio.to_thread(self.llm.load_model)
            except Exception as e:
                logger.warning(f"LLM not loaded: {e}")

        self._initialized = True
        logger.info("VoiceStreamingPipeline initialized")

    def create_session(
        self,
        voice_profile: Optional[str] = None
    ) -> VoiceSession:
        """새 세션 생성"""
        session_id = str(uuid.uuid4())
        session = VoiceSession(
            session_id=session_id,
            voice_profile=voice_profile or self.voice_profile
        )
        self.sessions[session_id] = session
        logger.info(f"Voice session created: {session_id}")
        return session

    def get_session(self, session_id: str) -> Optional[VoiceSession]:
        """세션 가져오기"""
        return self.sessions.get(session_id)

    def close_session(self, session_id: str) -> None:
        """세션 종료"""
        if session_id in self.sessions:
            self.sessions[session_id].state = SessionState.DISCONNECTED
            del self.sessions[session_id]
            logger.info(f"Voice session closed: {session_id}")

    async def process_audio(
        self,
        session_id: str,
        audio_data: bytes
    ) -> Dict[str, Any]:
        """
        오디오 처리 파이프라인

        Args:
            session_id: 세션 ID
            audio_data: 입력 오디오 (bytes)

        Returns:
            처리 결과 (텍스트, 응답 오디오 등)
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        try:
            session.state = SessionState.PROCESSING
            session.last_activity = datetime.now()

            # 1. STT: 음성 → 텍스트
            transcription = await asyncio.to_thread(
                self.stt.transcribe, audio_data
            )
            user_text = transcription.text

            if not user_text.strip():
                return {"status": "no_speech", "text": ""}

            logger.info(f"[{session_id}] User: {user_text}")

            # 2. LLM: 텍스트 → 응답
            if self.llm:
                response_text = await asyncio.to_thread(
                    self.llm.generate_response,
                    user_text,
                    session.conversation_history
                )
            else:
                # LLM 없으면 에코
                response_text = f"말씀하신 내용: {user_text}"

            logger.info(f"[{session_id}] Assistant: {response_text}")

            # 3. TTS: 텍스트 → 음성
            session.state = SessionState.SPEAKING

            # 컨텍스트 기반 음성 설정
            from tts import CounselorVoice, SpeechConfig
            speech_config = CounselorVoice.get_config_for_context({
                "emotion": "neutral",
                "response_type": "default"
            })

            synthesis_result = await asyncio.to_thread(
                self.tts.synthesize,
                response_text,
                session.voice_profile,
                speech_config
            )

            # 대화 기록 업데이트
            session.conversation_history.append({
                "role": "user",
                "content": user_text
            })
            session.conversation_history.append({
                "role": "assistant",
                "content": response_text
            })
            session.message_count += 1
            session.total_audio_duration += transcription.duration

            session.state = SessionState.CONNECTED

            return {
                "status": "success",
                "user_text": user_text,
                "response_text": response_text,
                "response_audio": base64.b64encode(synthesis_result.to_bytes()).decode(),
                "audio_duration": synthesis_result.duration
            }

        except Exception as e:
            logger.error(f"[{session_id}] Processing error: {e}")
            session.state = SessionState.ERROR
            return {
                "status": "error",
                "error": str(e)
            }


class WebSocketVoiceHandler:
    """
    WebSocket 음성 핸들러

    실시간 양방향 음성 통신 관리
    """

    def __init__(self, pipeline: VoiceStreamingPipeline):
        self.pipeline = pipeline
        self.connections: Dict[str, Any] = {}

    async def handle_connection(
        self,
        websocket,
        session_id: Optional[str] = None
    ) -> None:
        """
        WebSocket 연결 처리

        Args:
            websocket: WebSocket 연결
            session_id: 기존 세션 ID (재연결 시)
        """
        # 초기화 확인
        if not self.pipeline._initialized:
            await self.pipeline.initialize()

        # 세션 생성/가져오기
        if session_id and self.pipeline.get_session(session_id):
            session = self.pipeline.get_session(session_id)
        else:
            session = self.pipeline.create_session()

        session.state = SessionState.CONNECTED
        self.connections[session.session_id] = websocket

        # 연결 확인 메시지
        await self._send_message(websocket, VoiceMessage(
            type="connected",
            data={"session_id": session.session_id},
            session_id=session.session_id
        ))

        try:
            async for message in websocket:
                await self._handle_message(websocket, session, message)

        except Exception as e:
            logger.error(f"WebSocket error: {e}")

        finally:
            self._cleanup_connection(session.session_id)

    async def _handle_message(
        self,
        websocket,
        session: VoiceSession,
        message: Any
    ) -> None:
        """메시지 처리"""
        try:
            # JSON 메시지 파싱
            if isinstance(message, str):
                data = json.loads(message)
            elif isinstance(message, bytes):
                # 바이너리 오디오 데이터
                data = {"type": "audio", "data": base64.b64encode(message).decode()}
            else:
                data = message

            msg_type = data.get("type", "unknown")

            if msg_type == "audio":
                # 오디오 처리
                audio_data = base64.b64decode(data["data"])
                result = await self.pipeline.process_audio(session.session_id, audio_data)

                await self._send_message(websocket, VoiceMessage(
                    type="response",
                    data=result,
                    session_id=session.session_id
                ))

            elif msg_type == "text":
                # 텍스트 입력 (채팅 모드)
                result = await self._process_text(session, data.get("text", ""))

                await self._send_message(websocket, VoiceMessage(
                    type="response",
                    data=result,
                    session_id=session.session_id
                ))

            elif msg_type == "control":
                # 제어 명령
                await self._handle_control(websocket, session, data)

            elif msg_type == "ping":
                # 핑/퐁
                await self._send_message(websocket, VoiceMessage(
                    type="pong",
                    data={"timestamp": datetime.now().isoformat()},
                    session_id=session.session_id
                ))

        except json.JSONDecodeError:
            logger.warning("Invalid JSON message")
        except Exception as e:
            logger.error(f"Message handling error: {e}")
            await self._send_message(websocket, VoiceMessage(
                type="error",
                data={"error": str(e)},
                session_id=session.session_id
            ))

    async def _process_text(
        self,
        session: VoiceSession,
        text: str
    ) -> Dict[str, Any]:
        """텍스트 입력 처리 (채팅 모드)"""
        if not text.strip():
            return {"status": "empty", "text": ""}

        # LLM 응답 생성
        if self.pipeline.llm:
            response_text = await asyncio.to_thread(
                self.pipeline.llm.generate_response,
                text,
                session.conversation_history
            )
        else:
            response_text = f"받은 메시지: {text}"

        # 대화 기록 업데이트
        session.conversation_history.append({"role": "user", "content": text})
        session.conversation_history.append({"role": "assistant", "content": response_text})

        return {
            "status": "success",
            "user_text": text,
            "response_text": response_text
        }

    async def _handle_control(
        self,
        websocket,
        session: VoiceSession,
        data: Dict[str, Any]
    ) -> None:
        """제어 명령 처리"""
        command = data.get("command", "")

        if command == "set_voice":
            # 음성 프로필 변경
            session.voice_profile = data.get("voice_profile")
            await self._send_message(websocket, VoiceMessage(
                type="control_ack",
                data={"command": command, "status": "ok"},
                session_id=session.session_id
            ))

        elif command == "pause":
            session.state = SessionState.PAUSED
            await self._send_message(websocket, VoiceMessage(
                type="control_ack",
                data={"command": command, "status": "paused"},
                session_id=session.session_id
            ))

        elif command == "resume":
            session.state = SessionState.CONNECTED
            await self._send_message(websocket, VoiceMessage(
                type="control_ack",
                data={"command": command, "status": "resumed"},
                session_id=session.session_id
            ))

        elif command == "get_history":
            await self._send_message(websocket, VoiceMessage(
                type="history",
                data={"conversation": session.conversation_history},
                session_id=session.session_id
            ))

        elif command == "clear_history":
            session.conversation_history = []
            await self._send_message(websocket, VoiceMessage(
                type="control_ack",
                data={"command": command, "status": "cleared"},
                session_id=session.session_id
            ))

    async def _send_message(
        self,
        websocket,
        message: VoiceMessage
    ) -> None:
        """메시지 전송"""
        await websocket.send(message.to_json())

    def _cleanup_connection(self, session_id: str) -> None:
        """연결 정리"""
        if session_id in self.connections:
            del self.connections[session_id]

        session = self.pipeline.get_session(session_id)
        if session:
            session.state = SessionState.DISCONNECTED

        logger.info(f"Connection cleaned up: {session_id}")


class VoiceCounselingMode(Enum):
    """상담 모드"""
    CHAT = "chat"  # 텍스트 채팅만
    VOICE = "voice"  # 음성만
    HYBRID = "hybrid"  # 채팅 + 음성


@dataclass
class CounselingSessionConfig:
    """상담 세션 설정"""
    mode: VoiceCounselingMode = VoiceCounselingMode.HYBRID
    voice_profile: Optional[str] = None
    enable_emotion_analysis: bool = True
    enable_crisis_detection: bool = True
    language: str = "ko"


class UnifiedCounselingSession:
    """
    통합 상담 세션

    채팅과 음성을 모두 지원하는 통합 세션
    """

    def __init__(
        self,
        config: Optional[CounselingSessionConfig] = None,
        pipeline: Optional[VoiceStreamingPipeline] = None
    ):
        self.config = config or CounselingSessionConfig()
        self.pipeline = pipeline

        self.session_id = str(uuid.uuid4())
        self.mode = self.config.mode
        self.conversation_history: list = []
        self.created_at = datetime.now()

    async def initialize(self) -> None:
        """초기화"""
        if self.pipeline is None:
            self.pipeline = VoiceStreamingPipeline(
                voice_profile=self.config.voice_profile
            )

        if self.mode in [VoiceCounselingMode.VOICE, VoiceCounselingMode.HYBRID]:
            await self.pipeline.initialize()

    async def process_input(
        self,
        input_data: Union[str, bytes],
        input_type: str = "auto"
    ) -> Dict[str, Any]:
        """
        입력 처리 (텍스트 또는 음성)

        Args:
            input_data: 입력 데이터 (텍스트 또는 오디오 바이트)
            input_type: 입력 타입 (auto, text, audio)

        Returns:
            처리 결과
        """
        # 입력 타입 자동 감지
        if input_type == "auto":
            input_type = "text" if isinstance(input_data, str) else "audio"

        if input_type == "text":
            return await self._process_text_input(input_data)
        else:
            return await self._process_audio_input(input_data)

    async def _process_text_input(self, text: str) -> Dict[str, Any]:
        """텍스트 입력 처리"""
        # LLM 응답 생성
        if self.pipeline and self.pipeline.llm:
            response_text = await asyncio.to_thread(
                self.pipeline.llm.generate_response,
                text,
                self.conversation_history
            )
        else:
            response_text = "시스템이 아직 준비되지 않았습니다."

        # 대화 기록 업데이트
        self.conversation_history.append({"role": "user", "content": text})
        self.conversation_history.append({"role": "assistant", "content": response_text})

        result = {
            "status": "success",
            "mode": "chat",
            "user_text": text,
            "response_text": response_text
        }

        # 하이브리드 모드면 TTS도 생성
        if self.mode == VoiceCounselingMode.HYBRID and self.pipeline and self.pipeline.tts:
            synthesis = await asyncio.to_thread(
                self.pipeline.tts.synthesize,
                response_text,
                self.config.voice_profile
            )
            result["response_audio"] = base64.b64encode(synthesis.to_bytes()).decode()
            result["audio_duration"] = synthesis.duration

        return result

    async def _process_audio_input(self, audio_data: bytes) -> Dict[str, Any]:
        """음성 입력 처리"""
        if not self.pipeline:
            return {"status": "error", "error": "Pipeline not initialized"}

        # 음성 세션 생성/가져오기
        voice_session = self.pipeline.create_session(self.config.voice_profile)

        # 파이프라인 처리
        result = await self.pipeline.process_audio(voice_session.session_id, audio_data)

        # 대화 기록 동기화
        if result.get("status") == "success":
            self.conversation_history.append({
                "role": "user",
                "content": result.get("user_text", "")
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": result.get("response_text", "")
            })

        result["mode"] = "voice"
        return result

    def get_session_info(self) -> Dict[str, Any]:
        """세션 정보"""
        return {
            "session_id": self.session_id,
            "mode": self.mode.value,
            "message_count": len(self.conversation_history) // 2,
            "created_at": self.created_at.isoformat(),
            "voice_profile": self.config.voice_profile
        }


# 편의 함수
async def create_voice_session(
    mode: str = "hybrid",
    voice_profile: Optional[str] = None
) -> UnifiedCounselingSession:
    """음성 상담 세션 생성"""
    config = CounselingSessionConfig(
        mode=VoiceCounselingMode(mode),
        voice_profile=voice_profile
    )
    session = UnifiedCounselingSession(config)
    await session.initialize()
    return session
