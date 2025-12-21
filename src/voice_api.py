"""
음성 상담 API (Voice Counseling API)
FastAPI 기반 REST API 및 WebSocket 엔드포인트

기능:
- 채팅 상담 API (텍스트)
- 음성 상담 API (음성 파일)
- 실시간 음성 WebSocket
- Voice Cloning 관리
"""

import logging
import asyncio
import base64
from typing import Optional, List
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Pydantic Models
# =============================================================================

class ChatRequest(BaseModel):
    """채팅 요청"""
    message: str = Field(..., min_length=1, description="사용자 메시지")
    session_id: Optional[str] = Field(None, description="세션 ID (없으면 새로 생성)")
    include_audio: bool = Field(False, description="응답에 음성 포함 여부")
    voice_profile: Optional[str] = Field(None, description="음성 프로필")


class ChatResponse(BaseModel):
    """채팅 응답"""
    session_id: str
    user_message: str
    response: str
    audio_base64: Optional[str] = None
    audio_duration: Optional[float] = None
    timestamp: str


class VoiceRequest(BaseModel):
    """음성 요청 (Base64)"""
    audio_base64: str = Field(..., description="Base64 인코딩된 오디오")
    session_id: Optional[str] = Field(None, description="세션 ID")
    audio_format: str = Field("wav", description="오디오 포맷")


class VoiceResponse(BaseModel):
    """음성 응답"""
    session_id: str
    transcribed_text: str
    response_text: str
    response_audio_base64: str
    audio_duration: float
    timestamp: str


class VoiceProfileRequest(BaseModel):
    """음성 프로필 생성 요청"""
    name: str = Field(..., min_length=1, description="프로필 이름")
    description: str = Field("", description="설명")


class SessionInfo(BaseModel):
    """세션 정보"""
    session_id: str
    mode: str
    message_count: int
    created_at: str
    voice_profile: Optional[str] = None


class HealthResponse(BaseModel):
    """헬스체크 응답"""
    status: str
    stt_loaded: bool
    tts_loaded: bool
    llm_loaded: bool
    timestamp: str


# =============================================================================
# Global State
# =============================================================================

# 파이프라인 및 세션 관리
_pipeline = None
_sessions = {}


async def get_pipeline():
    """파이프라인 인스턴스 가져오기"""
    global _pipeline

    if _pipeline is None:
        try:
            logger.info("Initializing VoiceStreamingPipeline...")
            from .voice_streaming import VoiceStreamingPipeline
            _pipeline = VoiceStreamingPipeline()
            await _pipeline.initialize()
            logger.info("VoiceStreamingPipeline initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize pipeline: {e}", exc_info=True)
            raise

    return _pipeline


async def get_or_create_session(session_id: Optional[str], mode: str = "hybrid"):
    """세션 가져오기 또는 생성"""
    global _sessions

    if session_id and session_id in _sessions:
        return _sessions[session_id]

    from .voice_streaming import UnifiedCounselingSession, CounselingSessionConfig, VoiceCounselingMode

    config = CounselingSessionConfig(mode=VoiceCounselingMode(mode))
    session = UnifiedCounselingSession(config, await get_pipeline())
    await session.initialize()

    _sessions[session.session_id] = session
    return session


# =============================================================================
# FastAPI App
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 생명주기 관리"""
    logger.info("Voice API starting up...")
    yield
    logger.info("Voice API shutting down...")


app = FastAPI(
    title="Korean Psychological Counseling Voice API",
    description="한국어 심리상담 음성 API - 채팅 및 음성 상담 지원",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# REST Endpoints - 채팅 상담
# =============================================================================

@app.post("/api/v1/chat", response_model=ChatResponse, tags=["채팅 상담"])
async def chat_endpoint(request: ChatRequest):
    """
    채팅 상담 API

    텍스트 기반 상담 요청/응답
    """
    try:
        session = await get_or_create_session(request.session_id, "hybrid" if request.include_audio else "chat")

        result = await session.process_input(request.message, "text")

        response = ChatResponse(
            session_id=session.session_id,
            user_message=request.message,
            response=result.get("response_text", ""),
            timestamp=datetime.now().isoformat()
        )

        # 음성 포함 요청 시
        if request.include_audio and "response_audio" in result:
            response.audio_base64 = result["response_audio"]
            response.audio_duration = result.get("audio_duration")

        return response

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/chat/history/{session_id}", tags=["채팅 상담"])
async def get_chat_history(session_id: str):
    """채팅 기록 조회"""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _sessions[session_id]
    return {
        "session_id": session_id,
        "history": session.conversation_history
    }


# =============================================================================
# REST Endpoints - 음성 상담
# =============================================================================

@app.post("/api/v1/voice", response_model=VoiceResponse, tags=["음성 상담"])
async def voice_endpoint(request: VoiceRequest):
    """
    음성 상담 API

    음성 입력 → 텍스트 변환 → LLM 응답 → 음성 출력
    """
    try:
        session = await get_or_create_session(request.session_id, "voice")

        # Base64 디코딩
        audio_data = base64.b64decode(request.audio_base64)

        result = await session.process_input(audio_data, "audio")

        if result.get("status") != "success":
            raise HTTPException(status_code=400, detail=result.get("error", "Processing failed"))

        return VoiceResponse(
            session_id=session.session_id,
            transcribed_text=result.get("user_text", ""),
            response_text=result.get("response_text", ""),
            response_audio_base64=result.get("response_audio", ""),
            audio_duration=result.get("audio_duration", 0.0),
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"Voice error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/voice/upload", response_model=VoiceResponse, tags=["음성 상담"])
async def voice_upload_endpoint(
    audio_file: UploadFile = File(..., description="오디오 파일"),
    session_id: Optional[str] = Form(None)
):
    """
    음성 파일 업로드 상담

    음성 파일을 직접 업로드하여 상담
    """
    try:
        session = await get_or_create_session(session_id, "voice")

        # 파일 읽기
        audio_data = await audio_file.read()

        result = await session.process_input(audio_data, "audio")

        if result.get("status") != "success":
            raise HTTPException(status_code=400, detail=result.get("error", "Processing failed"))

        return VoiceResponse(
            session_id=session.session_id,
            transcribed_text=result.get("user_text", ""),
            response_text=result.get("response_text", ""),
            response_audio_base64=result.get("response_audio", ""),
            audio_duration=result.get("audio_duration", 0.0),
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"Voice upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/stt", tags=["음성 처리"])
async def stt_endpoint(
    audio_file: UploadFile = File(..., description="오디오 파일")
):
    """
    STT 전용 API

    음성을 텍스트로만 변환 (상담 없이)
    """
    try:
        pipeline = await get_pipeline()
        audio_data = await audio_file.read()

        result = await asyncio.to_thread(pipeline.stt.transcribe, audio_data)

        return {
            "text": result.text,
            "language": result.language,
            "confidence": result.confidence,
            "duration": result.duration,
            "segments": result.segments
        }

    except Exception as e:
        logger.error(f"STT error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/tts", tags=["음성 처리"])
async def tts_endpoint(
    text: str = Form(..., description="합성할 텍스트"),
    voice_profile: Optional[str] = Form(None, description="음성 프로필"),
    emotion: str = Form("calm", description="감정 (calm, empathetic, supportive)")
):
    """
    TTS 전용 API

    텍스트를 음성으로만 변환 (상담 없이)
    """
    try:
        pipeline = await get_pipeline()

        from tts import SpeechConfig
        config = SpeechConfig(emotion=emotion)

        result = await asyncio.to_thread(
            pipeline.tts.synthesize,
            text,
            voice_profile,
            config
        )

        return {
            "audio_base64": base64.b64encode(result.to_bytes()).decode(),
            "duration": result.duration,
            "sample_rate": result.sample_rate,
            "text": text
        }

    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Voice Profile Management
# =============================================================================

@app.post("/api/v1/voice-profiles", tags=["음성 프로필"])
async def create_voice_profile(
    name: str = Form(..., description="프로필 이름"),
    description: str = Form("", description="설명"),
    reference_audio: UploadFile = File(..., description="참조 음성 파일 (5-30초)")
):
    """
    음성 프로필 생성 (Voice Cloning)

    참조 음성으로 새 음성 프로필 생성
    """
    try:
        pipeline = await get_pipeline()
        audio_data = await reference_audio.read()

        profile = await asyncio.to_thread(
            pipeline.tts.create_voice_profile,
            name,
            audio_data,
            description
        )

        return {
            "status": "created",
            "profile": profile.to_dict()
        }

    except Exception as e:
        logger.error(f"Voice profile creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/voice-profiles", tags=["음성 프로필"])
async def list_voice_profiles():
    """음성 프로필 목록"""
    try:
        pipeline = await get_pipeline()
        profiles = pipeline.tts.list_voice_profiles()

        return {
            "profiles": profiles
        }

    except Exception as e:
        logger.error(f"List profiles error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# WebSocket - 실시간 음성 상담
# =============================================================================

@app.websocket("/ws/voice/{session_id}")
async def websocket_voice_endpoint(websocket: WebSocket, session_id: Optional[str] = None):
    """
    실시간 음성 상담 WebSocket

    양방향 실시간 음성 스트리밍
    """
    try:
        await websocket.accept()
        logger.info(f"WebSocket connection accepted: {session_id}")
    except Exception as e:
        logger.error(f"Failed to accept WebSocket connection: {e}", exc_info=True)
        return

    try:
        logger.info(f"Getting pipeline for session: {session_id}")
        pipeline = await get_pipeline()
        
        if pipeline is None:
            logger.error("Pipeline is None - cannot handle WebSocket connection")
            await websocket.close(code=1011, reason="Pipeline not initialized")
            return

        from .voice_streaming import WebSocketVoiceHandler
        handler = WebSocketVoiceHandler(pipeline)

        logger.info(f"Starting WebSocket handler for session: {session_id}")
        await handler.handle_connection(websocket, session_id)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            error_message = str(e)[:123]  # WebSocket close reason은 최대 123바이트
            await websocket.close(code=1011, reason=error_message)
        except Exception as close_error:
            logger.error(f"Failed to close WebSocket: {close_error}")


@app.websocket("/ws/chat/{session_id}")
async def websocket_chat_endpoint(websocket: WebSocket, session_id: Optional[str] = None):
    """
    실시간 채팅 상담 WebSocket

    텍스트 기반 실시간 상담
    """
    await websocket.accept()

    try:
        session = await get_or_create_session(session_id, "chat")

        await websocket.send_json({
            "type": "connected",
            "session_id": session.session_id
        })

        while True:
            data = await websocket.receive_json()

            if data.get("type") == "message":
                text = data.get("text", "")
                result = await session.process_input(text, "text")

                await websocket.send_json({
                    "type": "response",
                    "user_text": text,
                    "response_text": result.get("response_text", ""),
                    "timestamp": datetime.now().isoformat()
                })

            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info(f"Chat WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"Chat WebSocket error: {e}")


# =============================================================================
# Session Management
# =============================================================================

@app.get("/api/v1/sessions/{session_id}", response_model=SessionInfo, tags=["세션"])
async def get_session_info(session_id: str):
    """세션 정보 조회"""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _sessions[session_id]
    info = session.get_session_info()

    return SessionInfo(**info)


@app.delete("/api/v1/sessions/{session_id}", tags=["세션"])
async def delete_session(session_id: str):
    """세션 삭제"""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    del _sessions[session_id]

    return {"status": "deleted", "session_id": session_id}


@app.get("/api/v1/sessions", tags=["세션"])
async def list_sessions():
    """활성 세션 목록"""
    sessions = []
    for session_id, session in _sessions.items():
        sessions.append(session.get_session_info())

    return {"sessions": sessions, "count": len(sessions)}


# =============================================================================
# Health Check
# =============================================================================

@app.get("/health", response_model=HealthResponse, tags=["시스템"])
async def health_check():
    """헬스체크"""
    global _pipeline

    stt_loaded = False
    tts_loaded = False
    llm_loaded = False

    if _pipeline:
        stt_loaded = _pipeline.stt is not None and _pipeline.stt.model is not None
        tts_loaded = _pipeline.tts is not None and _pipeline.tts.model is not None
        llm_loaded = _pipeline.llm is not None

    return HealthResponse(
        status="healthy",
        stt_loaded=stt_loaded,
        tts_loaded=tts_loaded,
        llm_loaded=llm_loaded,
        timestamp=datetime.now().isoformat()
    )


@app.get("/api/v1/models/info", tags=["시스템"])
async def get_models_info():
    """로드된 모델 정보"""
    pipeline = await get_pipeline()

    return {
        "stt": pipeline.stt.get_model_info() if pipeline.stt else None,
        "tts": pipeline.tts.get_model_info() if pipeline.tts else None,
        "llm_available": pipeline.llm is not None
    }


# =============================================================================
# Run Server
# =============================================================================

def run_voice_api(host: str = "0.0.0.0", port: int = 8001):
    """음성 API 서버 실행"""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_voice_api()
