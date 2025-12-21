"""
FastAPI REST API for Korean Mental Health Counseling System
Production-ready API with authentication, rate limiting, and comprehensive error handling
"""

import os
import sys
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

# .env 파일 로드 (가장 먼저 실행)
from dotenv import load_dotenv
load_dotenv()  # 프로젝트 루트의 .env 파일 로드

# Starlette Config가 .env 파일을 읽지 않도록 설정 (인코딩 문제 방지)
# python-dotenv로 이미 로드했으므로 Starlette가 다시 읽을 필요 없음
os.environ.setdefault("STARLETTE_ENV_FILE", "")

from fastapi import FastAPI, HTTPException, Depends, Header, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, validator
import uvicorn
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================================
# JSON 직렬화 헬퍼 함수
# ============================================================================

def convert_to_json_serializable(obj):
    """
    numpy 타입 및 기타 JSON 직렬화 불가능한 타입을 Python 기본 타입으로 변환
    
    Args:
        obj: 변환할 객체
        
    Returns:
        JSON 직렬화 가능한 객체
    """
    import numpy as np
    
    if isinstance(obj, (np.integer, np.floating)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_to_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_json_serializable(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        return convert_to_json_serializable(obj.__dict__)
    else:
        return obj

# 지연 임포트 (서버 시작 후 필요할 때 로드)
IntegratedMentalHealthSystem = None
RiskLevel = None
PersonalizationManager = None
PersonaManager = None
get_persona_manager = None
get_db = None
Session = None

# 모듈 임포트 시도 (실패해도 서버는 시작)
try:
    from main_integrated import IntegratedMentalHealthSystem
    from src.safety_system_v2 import RiskLevel
    from src.personalization import PersonalizationManager
    from src.persona_manager import PersonaManager, get_persona_manager
    from src.database import get_db
    from sqlalchemy.orm import Session
    logger.info("All modules imported successfully")
except Exception as e:
    logger.warning(f"Some modules failed to import: {e}")
    logger.warning("Server will start but some features may be unavailable")
    # 기본 타입만 임포트
    from enum import Enum
    class RiskLevel(Enum):
        NONE = "NONE"
        LOW = "LOW"
        MEDIUM = "MEDIUM"
        HIGH = "HIGH"
        CRITICAL = "CRITICAL"
    # get_db가 None일 때를 위한 더미 함수
    async def dummy_get_db():
        return None
    if get_db is None:
        get_db = dummy_get_db

# ============================================================================
# Configuration and Setup
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize rate limiter
# Starlette Config가 .env 파일을 읽을 때 인코딩 문제가 발생하므로
# Starlette Config의 _read_file 메서드를 패치하여 UTF-8 사용
try:
    from starlette.config import Config
    original_read_file = Config._read_file
    
    def patched_read_file(self, env_file):
        """UTF-8 인코딩을 사용하도록 패치된 _read_file 메서드"""
        if env_file is None or not Path(env_file).exists():
            return {}
        try:
            with open(env_file, 'r', encoding='utf-8') as input_file:
                return dict(
                    tuple(line.strip().split("=", 1))
                    for line in input_file
                    if line.strip() and not line.strip().startswith("#") and "=" in line
                )
        except Exception:
            return {}
    
    # 패치 적용
    Config._read_file = patched_read_file
    
    limiter = Limiter(
        key_func=get_remote_address, 
        default_limits=["1000/hour"]
    )
    logger.info("Rate limiter initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize rate limiter: {e}")
    logger.warning("Continuing without rate limiting")
    # Rate limiting 없이 진행
    limiter = None

# Create FastAPI app
app = FastAPI(
    title="Korean Mental Health Counseling API",
    description="AI-powered mental health counseling system with crisis detection and psychological assessments",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add rate limit exception handler (if limiter is available)
if limiter is not None:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
else:
    logger.warning("Rate limiting disabled (limiter not initialized)")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (Frontend)
# Mount frontend directory for serving HTML/CSS/JS
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
    logger.info(f"Frontend static files mounted at /static from {frontend_path}")
else:
    logger.warning(f"Frontend directory not found at {frontend_path}")

# Prometheus metrics
api_requests = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])
api_response_time = Histogram('api_response_time_seconds', 'API response time', ['endpoint'])
crisis_detections = Counter('crisis_detections_total', 'Total crisis detections')

# ============================================================================
# Pydantic Models (Request/Response Schemas)
# ============================================================================

class ChatRequest(BaseModel):
    """Chat message request"""
    session_id: Optional[str] = Field(None, description="Session ID (will be generated if not provided)")
    user_id: Optional[str] = Field(None, description="User identifier for personalization (optional)")
    persona_id: Optional[str] = Field(None, description="Counselor persona ID (e.g., 'warm_mother')")
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        None,
        description="Conversation history in format [{'role': 'user/assistant', 'content': '...'}]"
    )
    consent: bool = Field(default=True, description="Data storage consent for personalization")
    image_base64: Optional[str] = Field(None, description="Base64-encoded image (webcam capture) for emotion analysis")

    @validator('message')
    def message_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()


class ChatResponse(BaseModel):
    """Chat message response"""
    session_id: str = Field(..., description="Session ID")
    user_message: Optional[str] = Field(None, description="User message (echo)")
    response: str = Field(..., description="AI assistant response")
    crisis_detected: bool = Field(default=False, description="Whether crisis was detected")
    crisis_level: int = Field(default=0, description="Crisis level (0=none, 1-5=severity)")
    emotions: Optional[Dict[str, Any]] = Field(None, description="Detected emotions")
    suggested_assessment: Optional[str] = Field(None, description="Suggested psychological assessment")
    response_time: float = Field(default=0.0, description="Response time in seconds")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    audio_base64: Optional[str] = Field(None, description="TTS audio in base64 format (WAV)")
    audio_duration: Optional[float] = Field(None, description="Audio duration in seconds")


class SessionResponse(BaseModel):
    """Session information response"""
    session_id: str
    created_at: str
    total_messages: int
    crisis_detected_count: int
    last_activity: str


class AssessmentRequest(BaseModel):
    """Psychological assessment request"""
    session_id: str = Field(..., description="Session ID")
    user_id: Optional[str] = Field(None, description="User identifier for saving assessment history")
    assessment_type: str = Field(..., description="Assessment type: phq9, gad7, k10")
    responses: List[int] = Field(..., description="Assessment responses (0-3 or 0-4 depending on type)")

    @validator('assessment_type')
    def validate_type(cls, v):
        if v.lower() not in ['phq9', 'gad7', 'k10']:
            raise ValueError('Assessment type must be phq9, gad7, or k10')
        return v.lower()


class AssessmentResponse(BaseModel):
    """Assessment result response"""
    session_id: str
    assessment_type: str
    score: int
    severity: str
    interpretation: str
    recommendations: List[str]
    timestamp: str


class FeedbackRequest(BaseModel):
    """User feedback request"""
    session_id: str
    message_id: Optional[str] = None
    rating: int = Field(..., ge=1, le=5, description="Rating 1-5")
    feedback_text: Optional[str] = Field(None, max_length=1000)
    feedback_type: str = Field(..., description="Type: helpful, not_helpful, inappropriate, other")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    components: Dict[str, bool]
    uptime_seconds: float
    initialization_errors: List[Dict[str, str]] = Field(default_factory=list, description="초기화 오류 목록")


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    timestamp: str


class UserProfileResponse(BaseModel):
    """User profile response (with personalization)"""
    user_id: str = Field(..., description="Anonymous user ID")
    preferred_name: Optional[str] = Field(None, description="Preferred name (e.g., '철수님')")
    age_range: Optional[str] = Field(None, description="Age range (e.g., '20대')")
    main_concerns: List[str] = Field(default_factory=list, description="Main concerns")
    total_conversations: int = Field(..., description="Total conversation count")
    total_messages: int = Field(..., description="Total message count")
    crisis_count: int = Field(..., description="Number of crisis detections")
    created_at: str = Field(..., description="Account creation timestamp")
    last_active: str = Field(..., description="Last active timestamp")


class UserHistoryResponse(BaseModel):
    """User conversation history response"""
    user_id: str
    conversations: List[Dict[str, Any]] = Field(..., description="Conversation turns")
    total_count: int = Field(..., description="Total conversation count")


class UserAssessmentsResponse(BaseModel):
    """User assessment history response"""
    user_id: str
    assessments: List[Dict[str, Any]] = Field(..., description="Assessment history")
    trend: Optional[Dict[str, Any]] = Field(None, description="Trend analysis")


class UserConsentRequest(BaseModel):
    """User consent update request"""
    consent_given: bool = Field(..., description="Data collection consent")
    data_retention_days: Optional[int] = Field(None, description="Data retention period in days")


class PersonaRecommendRequest(BaseModel):
    """Persona recommendation request"""
    age_range: Optional[str] = Field(None, description="User age range (e.g., '20대')")
    concerns: Optional[List[str]] = Field(None, description="List of concerns (e.g., ['우울', '불안'])")
    top_k: int = Field(default=3, ge=1, le=10, description="Number of recommendations")
    user_id: Optional[str] = Field(None, description="User ID for personalized recommendations (optional)")


class PersonaResponse(BaseModel):
    """Persona information response"""
    id: str
    name: str
    display_name: str
    age_range: str
    gender: str
    personality_type: str
    specialties: List[str]
    counseling_style: Dict[str, str]
    intro: str


class PersonaListResponse(BaseModel):
    """Persona list response"""
    personas: List[Dict[str, Any]]
    total: int


class PersonaRecommendationResponse(BaseModel):
    """Persona recommendation response"""
    recommendations: List[Dict[str, Any]]
    reason: Optional[str] = None


class PersonaFeedbackRequest(BaseModel):
    """Persona feedback submission request"""
    session_id: str = Field(..., description="Session ID")
    user_id: Optional[str] = Field(None, description="User ID (optional, anonymous allowed)")
    rating: int = Field(..., ge=1, le=5, description="Rating (1-5)")
    helpful: bool = Field(default=True, description="Was this persona helpful?")
    appropriate: bool = Field(default=True, description="Was this persona appropriate?")
    would_recommend_again: bool = Field(default=True, description="Would you use this persona again?")
    concerns_addressed: Optional[List[str]] = Field(None, description="List of concerns addressed")
    feedback_text: Optional[str] = Field(None, max_length=1000, description="Free-form feedback")
    user_age_range: Optional[str] = Field(None, description="User age range (e.g., '20대')")


class PersonaFeedbackResponse(BaseModel):
    """Persona feedback response"""
    success: bool
    message: str
    feedback_id: Optional[int] = None


class PersonaPerformanceResponse(BaseModel):
    """Persona performance statistics response"""
    persona_id: str
    total_feedback_count: int
    average_rating: float
    helpful_rate: float
    appropriate_rate: float
    recommendation_rate: float
    last_updated: Optional[str] = None


class PersonaAnalyticsResponse(BaseModel):
    """Persona analytics response"""
    personas: List[Dict[str, Any]]
    total_feedback_count: int
    overall_average_rating: float


# ============================================================================
# Global State and Session Management
# ============================================================================

# Global system instance (singleton)
mental_health_system: Optional[IntegratedMentalHealthSystem] = None

# Global personalization manager (for long-term memory)
personalization_manager: Optional[PersonalizationManager] = None

# Global persona manager (for counselor personas)
persona_manager: Optional[PersonaManager] = None

# In-memory session storage (use Redis in production)
sessions: Dict[str, Dict] = {}

# API Key authentication (basic security)
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: Optional[str] = Depends(API_KEY_HEADER)) -> bool:
    """
    Verify API key (if enabled)
    Set environment variable API_KEY to enable authentication
    """
    required_key = os.getenv("API_KEY")

    # If no API_KEY is set, authentication is disabled
    if not required_key:
        return True

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide X-API-Key header."
        )

    if api_key != required_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    return True


def get_or_create_session(session_id: Optional[str] = None) -> str:
    """Get existing session or create new one"""
    if session_id and session_id in sessions:
        # Update last activity
        sessions[session_id]["last_activity"] = datetime.now()
        return session_id

    # Create new session
    new_session_id = session_id or str(uuid.uuid4())
    sessions[new_session_id] = {
        "session_id": new_session_id,
        "created_at": datetime.now(),
        "last_activity": datetime.now(),
        "conversation_history": [],
        "crisis_detected_count": 0,
        "assessments": []
    }

    logger.info(f"Created new session: {new_session_id}")
    return new_session_id


def cleanup_old_sessions(max_age_hours: int = 24):
    """Remove sessions older than max_age_hours"""
    cutoff = datetime.now() - timedelta(hours=max_age_hours)
    to_remove = [
        sid for sid, data in sessions.items()
        if data["last_activity"] < cutoff
    ]

    for sid in to_remove:
        del sessions[sid]
        logger.info(f"Cleaned up old session: {sid}")

    return len(to_remove)


# ============================================================================
# Startup and Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup (non-blocking)"""
    global mental_health_system, personalization_manager, persona_manager
    
    import asyncio
    
    logger.info("="*70)
    logger.info("Starting Korean Mental Health Counseling API")
    logger.info("API server is starting... System initialization will happen in background.")
    logger.info("="*70)
    
    # 서버가 먼저 시작되도록 비동기로 초기화
    async def initialize_system():
        global mental_health_system, personalization_manager, persona_manager
        try:
            # IntegratedMentalHealthSystem이 임포트되었는지 확인
            if IntegratedMentalHealthSystem is None:
                error_msg = (
                    "IntegratedMentalHealthSystem 모듈을 임포트할 수 없습니다. "
                    "실행파일 빌드 시 main_integrated 모듈이 포함되지 않았을 수 있습니다. "
                    "build_exe.py의 hiddenimports에 'main_integrated'를 추가하세요."
                )
                logger.error(error_msg)
                raise ImportError(error_msg)
            
            # Initialize integrated system
            # .env 파일에서 CONFIG_PATH를 먼저 확인하고, 없으면 기본값 사용
            config_path = os.getenv("CONFIG_PATH")
            if not config_path:
                # .env 파일에서 직접 읽기 시도
                from dotenv import load_dotenv
                load_dotenv()
                config_path = os.getenv("CONFIG_PATH", "configs/config.yaml")
            logger.info(f"Initializing system with config: {config_path}")
            mental_health_system = IntegratedMentalHealthSystem(config_path=config_path)

            # Initialize all components (LLM 우선 초기화)
            logger.info("Starting component initialization...")
            success = mental_health_system.initialize_all_components()

            # LLM 초기화 상태 확인 (가장 중요)
            if mental_health_system.llm:
                logger.info(f"✅ LLM initialized: {type(mental_health_system.llm).__name__}")
                logger.info("✅ 시스템이 사용 가능한 상태입니다 (LLM 준비 완료)")
                print("="*70)
                print("✅ LLM 초기화 성공!")
                print(f"모델: {type(mental_health_system.llm).__name__}")
                print("="*70)
            else:
                logger.error("❌ LLM initialization failed!")
                print("="*70)
                print("❌ LLM 초기화 실패!")
                if mental_health_system.initialization_errors:
                    for component, error in mental_health_system.initialization_errors:
                        if component == "llm":
                            logger.error(f"LLM initialization error: {error}")
                            logger.error("시스템이 정상 작동하지 않을 수 있습니다.")
                            print(f"오류: {error}")
                            print("\n상세 오류 정보:")
                            import traceback
                            traceback.print_exc()
                else:
                    print("초기화 오류 정보가 없습니다.")
                print("="*70)
            
            # 다른 컴포넌트 초기화 상태
            if not success:
                logger.warning("⚠️ Some optional components failed to initialize")
                logger.warning("API will run in degraded mode (LLM만 사용)")
            else:
                logger.info("✅ All components initialized successfully")

            # Initialize personalization manager (long-term memory)
            if os.getenv("ENABLE_LONG_TERM_MEMORY", "true").lower() == "true":
                try:
                    if PersonalizationManager is not None:
                        personalization_manager = PersonalizationManager()
                        logger.info("✓ PersonalizationManager initialized (long-term memory enabled)")
                    else:
                        logger.warning("PersonalizationManager is not available (module import failed)")
                except Exception as e:
                    logger.error(f"Failed to initialize PersonalizationManager: {e}", exc_info=True)
                    logger.warning("Long-term memory features will be disabled")
            else:
                logger.info("Long-term memory disabled (ENABLE_LONG_TERM_MEMORY=false)")

            # Initialize persona manager (counselor personas)
            try:
                if PersonaManager is not None:
                    persona_manager = PersonaManager()
                    logger.info(f"✓ PersonaManager initialized ({len(persona_manager.personas)} personas loaded)")
                else:
                    logger.warning("PersonaManager is not available (module import failed)")
            except Exception as e:
                logger.error(f"Failed to initialize PersonaManager: {e}", exc_info=True)
                logger.warning("Persona features will be disabled")

            logger.info("API is ready to accept requests")
            logger.info("="*70)

        except ImportError as e:
            error_msg = str(e)
            logger.error(f"Failed to import required modules: {error_msg}", exc_info=True)
            logger.error("API will start but may not function correctly")
            # 콘솔에 오류 출력
            print("="*70)
            print("❌ 모듈 임포트 실패!")
            print(f"오류: {error_msg}")
            print("\n해결 방법:")
            print("1. 실행파일을 다시 빌드하세요: build_exe.bat")
            print("2. 또는 Python 환경에서 직접 실행하세요: python start_all.py")
            print("3. 필요한 모듈이 모두 설치되어 있는지 확인하세요")
            import traceback
            print("\n상세 오류:")
            traceback.print_exc()
            print("="*70)
            # 서버는 계속 실행되도록 함
            mental_health_system = None
            personalization_manager = None
            persona_manager = None
        except Exception as e:
            logger.error(f"Failed to initialize system: {e}", exc_info=True)
            logger.error("API will start but may not function correctly")
            # 콘솔에 오류 출력
            print("="*70)
            print("❌ 시스템 초기화 실패!")
            print(f"오류: {e}")
            import traceback
            print("\n상세 오류:")
            traceback.print_exc()
            print("="*70)
            # 서버는 계속 실행되도록 함
            mental_health_system = None
            personalization_manager = None
            persona_manager = None
    
    # 비동기 태스크로 실행 (서버 블로킹 방지)
    asyncio.create_task(initialize_system())


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down API...")

    # Save any pending data, cleanup resources, etc.
    if mental_health_system and mental_health_system.monitor:
        logger.info("Generating final metrics report...")
        # Could save metrics here

    logger.info("Shutdown complete")


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - Serve frontend application"""
    frontend_path = Path(__file__).parent.parent / "frontend" / "index.html"
    if frontend_path.exists():
        return FileResponse(str(frontend_path))
    else:
        # Fallback to API information if frontend not available
        return {
            "name": "Korean Mental Health Counseling API",
            "version": "1.0.0",
            "status": "running",
            "endpoints": {
                "docs": "/docs",
                "health": "/api/v1/health",
                "chat": "/api/v1/chat",
                "metrics": "/metrics",
                "frontend": "/static/index.html"
            }
        }


@app.get("/favicon.ico", tags=["Root"])
async def favicon():
    """Favicon endpoint - Return 204 No Content to prevent 404 errors"""
    from fastapi.responses import Response
    return Response(status_code=204)


@app.get("/api", tags=["Root"])
@app.get("/api/v1", tags=["Root"])
async def api_info():
    """API information endpoint"""
    return {
        "name": "Korean Mental Health Counseling API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "health": "/api/v1/health",
            "chat": "/api/v1/chat",
            "personas": "/api/v1/personas",
            "feedback": "/api/v1/personas/{persona_id}/feedback",
            "metrics": "/metrics",
            "frontend": "/"
        }
    }


@app.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint

    Returns system status and component health
    """
    if not mental_health_system:
        # Return degraded status instead of raising exception
        return HealthResponse(
            status="initializing",
            timestamp=datetime.now().isoformat(),
            components={
                "llm": False,
                "crisis_detector": False,
                "emotion_analyzer": False,
                "assessment_manager": False,
                "rag_system": False,
                "monitoring": False,
                "logging": False
            },
            uptime_seconds=0,
            initialization_errors=[]  # mental_health_system이 None이므로 오류 정보 없음
        )

    # Validate components (캐시 사용하여 중복 검증 방지)
    validation_results = mental_health_system.validate_system(use_cache=True)

    # Calculate uptime
    uptime = (datetime.now() - mental_health_system.stats["uptime_start"]).total_seconds()

    # Overall status
    all_critical_ok = validation_results.get("llm", False) and validation_results.get("crisis_detector", False)
    overall_status = "healthy" if all_critical_ok else "degraded"

    # 초기화 오류 정보 가져오기
    init_errors = []
    if hasattr(mental_health_system, 'initialization_errors') and mental_health_system.initialization_errors:
        init_errors = [
            {"component": component, "error": str(error)}
            for component, error in mental_health_system.initialization_errors
        ]
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now().isoformat(),
        components=validation_results,
        uptime_seconds=uptime,
        initialization_errors=init_errors
    )


@app.post("/api/v1/chat", response_model=ChatResponse, tags=["Chat"])
@limiter.limit("100/minute")
async def chat(
    request: Request,
    chat_request: ChatRequest,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Process a chat message with personalization support

    - **session_id**: Optional session ID (will be generated if not provided)
    - **user_id**: Optional user identifier for personalization and long-term memory
    - **message**: User message (required)
    - **conversation_history**: Optional conversation history
    - **consent**: Data storage consent (default: true)

    Returns AI response with crisis detection and emotion analysis
    """
    start_time = datetime.now()

    # Check if system is initialized
    # LLM만 있으면 기본 응답 가능 (다른 컴포넌트는 선택적)
    if not mental_health_system:
        logger.warning("Chat request received but mental_health_system is None - using fallback response")
        # 기본 응답 반환
        return ChatResponse(
            session_id=chat_request.session_id or get_or_create_session(),
            user_message=chat_request.message,
            response="안녕하세요. 시스템이 아직 초기화 중입니다. 잠시만 기다려주시면 정상적으로 응답드리겠습니다.",
            crisis_detected=False,
            crisis_level=0,
            emotions=None,
            suggested_assessment=None,
            response_time=0.1,
            metadata={
                "status": "initializing",
                "message": "System is still initializing"
            }
        )
    
    # LLM이 초기화되었는지 확인 (가장 중요)
    # LLM이 없으면 초기화가 완료될 때까지 기다리거나 기본 응답 반환
    if not hasattr(mental_health_system, 'llm') or mental_health_system.llm is None:
        logger.warning("Chat request received but LLM is not initialized - checking initialization status...")
        
        # 초기화 오류 확인
        if hasattr(mental_health_system, 'initialization_errors'):
            for component, error in mental_health_system.initialization_errors:
                if component == "llm":
                    logger.error(f"LLM initialization error: {error}")
                    return ChatResponse(
                        session_id=chat_request.session_id or get_or_create_session(),
                        user_message=chat_request.message,
                        response=f"죄송합니다. AI 모델 초기화 중 오류가 발생했습니다: {str(error)[:100]}. 잠시 후 다시 시도해주세요.",
                        crisis_detected=False,
                        crisis_level=0,
                        emotions=None,
                        suggested_assessment=None,
                        response_time=0.1,
                        metadata={
                            "status": "error",
                            "message": f"LLM initialization failed: {error}"
                        }
                    )
        
        # 초기화 중이면 기본 응답 반환
        return ChatResponse(
            session_id=chat_request.session_id or get_or_create_session(),
            user_message=chat_request.message,
            response="안녕하세요. AI 모델이 아직 초기화 중입니다. 잠시만 기다려주시면 정상적으로 응답드리겠습니다.",
            crisis_detected=False,
            crisis_level=0,
            emotions=None,
            suggested_assessment=None,
            response_time=0.1,
            metadata={
                "status": "initializing",
                "message": "LLM is still initializing"
            }
        )
        # LLM이 없어도 process_message가 기본 응답을 반환하므로 계속 진행

    try:
        # Get or create session
        try:
            session_id = get_or_create_session(chat_request.session_id)
        except Exception as e:
            logger.error(f"Error creating/getting session: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create session: {str(e)}"
            )

        # Get session data
        if session_id not in sessions:
            logger.error(f"Session {session_id} not found in sessions dict")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Session creation failed"
            )
        session_data = sessions[session_id]

        # Personalization: Get or create user
        pm_user_id = None
        is_new_user = False
        personalized_greeting = None
        user_context = ""

        if personalization_manager and chat_request.user_id:
            try:
                pm_user_id, is_new_user = personalization_manager.get_or_create_user(
                    user_identifier=chat_request.user_id,
                    consent=chat_request.consent
                )

                # Generate personalized greeting for first message in session
                if len(session_data["conversation_history"]) == 0:
                    personalized_greeting = personalization_manager.get_personalized_greeting(
                        pm_user_id, is_new_user
                    )

                # Get user context for LLM
                user_context = personalization_manager.generate_personalized_context(pm_user_id)

            except Exception as e:
                logger.warning(f"Personalization error: {e}. Continuing without personalization.")

        # Use session history if not provided
        history = chat_request.conversation_history or session_data["conversation_history"]

        # 이미지 감정 분석 (이미지가 있는 경우)
        image_emotion_result = None
        if chat_request.image_base64:
            try:
                from src.image_emotion_analyzer import get_image_emotion_analyzer
                import asyncio
                image_analyzer = get_image_emotion_analyzer()
                image_emotion_result = await asyncio.to_thread(
                    image_analyzer.analyze,
                    chat_request.image_base64
                )
                logger.info(f"Image emotion analysis result: {image_emotion_result.get('primary_emotion', 'unknown')}")
            except Exception as e:
                logger.warning(f"Failed to analyze image emotion: {e}")

        # Add user context to message for personalized responses
        enhanced_message = chat_request.message
        
        # 이미지 감정 분석 결과를 메시지에 통합
        if image_emotion_result and image_emotion_result.get("face_detected"):
            image_emotion = image_emotion_result.get("primary_emotion", "중립")
            image_confidence = image_emotion_result.get("confidence", 0.0)
            image_emotions_detail = image_emotion_result.get("emotions", {})
            
            # 감정 상세 정보 문자열 생성
            emotion_details = ", ".join([
                f"{emotion}({score:.2f})" 
                for emotion, score in sorted(image_emotions_detail.items(), key=lambda x: x[1], reverse=True)[:3]
            ])
            
            image_context = f"\n\n[웹캠 이미지 분석 결과]\n- 주요 감정: {image_emotion} (신뢰도: {image_confidence:.1%})\n- 감정 분포: {emotion_details}\n- 얼굴 감지: 성공"
            enhanced_message = chat_request.message + image_context
        
        if user_context:
            # Prepend context for LLM (will be processed but not shown to user)
            enhanced_message = f"{user_context}\n\n[사용자 메시지]\n{enhanced_message}"

        # Process message through integrated system
        try:
            result = mental_health_system.process_message(
                session_id=session_id,
                user_message=enhanced_message,
                conversation_history=history
            )
            
            # Check if result is None or invalid
            if result is None:
                logger.error("process_message returned None")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="System returned invalid response"
                )
            
            # Check for errors
            if "error" in result:
                logger.error(f"process_message returned error: {result.get('error')}")
                api_requests.labels(method="POST", endpoint="/chat", status="500").inc()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result["error"]
                )
            
            # Check if response key exists
            if "response" not in result:
                logger.error(f"process_message result missing 'response' key: {result.keys()}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="System returned invalid response format"
                )
                
        except AttributeError as e:
            logger.error(f"AttributeError in process_message: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"System error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error in process_message: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process message: {str(e)}"
            )

        # Prepend personalized greeting if applicable
        response_text = result["response"]
        if personalized_greeting:
            response_text = f"{personalized_greeting}\n\n{response_text}"

        # Update session history
        session_data["conversation_history"].append({
            "role": "user",
            "content": chat_request.message
        })
        session_data["conversation_history"].append({
            "role": "assistant",
            "content": response_text
        })

        # Limit history length (keep last 20 messages)
        if len(session_data["conversation_history"]) > 40:  # 20 pairs
            session_data["conversation_history"] = session_data["conversation_history"][-40:]

        # Save to database (long-term memory)
        if personalization_manager and pm_user_id:
            try:
                # Save user message
                personalization_manager.save_conversation_turn(
                    user_id=pm_user_id,
                    session_id=session_id,
                    role="user",
                    content=chat_request.message,
                    detected_emotion=None,
                    crisis_detected=False,
                    crisis_level=0
                )

                # Save assistant response
                personalization_manager.save_conversation_turn(
                    user_id=pm_user_id,
                    session_id=session_id,
                    role="assistant",
                    content=response_text,
                    detected_emotion=result.get("emotions", {}).get("primary_emotion"),
                    crisis_detected=result.get("crisis_detected", False),
                    crisis_level=result.get("crisis_level", 0),
                    response_time=(datetime.now() - start_time).total_seconds()
                )
            except Exception as e:
                logger.error(f"Failed to save conversation to database: {e}")

        # Update crisis count
        if result.get("crisis_detected", False):
            session_data["crisis_detected_count"] += 1
            crisis_detections.inc()

        # Track metrics
        response_time = (datetime.now() - start_time).total_seconds()
        api_requests.labels(method="POST", endpoint="/chat", status="200").inc()
        api_response_time.labels(endpoint="/chat").observe(response_time)

        # Generate TTS audio using Zonos
        audio_base64 = None
        audio_duration = None
        try:
            # TTS 엔진 직접 사용
            from src.tts import ZonosTTS, CounselorVoice, SpeechConfig
            import asyncio
            import base64
            
            # TTS 인스턴스 가져오기 (전역 변수로 관리)
            global _tts_engine
            if '_tts_engine' not in globals():
                _tts_engine = None
            
            if _tts_engine is None:
                _tts_engine = ZonosTTS()
                await asyncio.to_thread(_tts_engine.load_model)
                
                # voice_profiles 폴더의 모든 프로필 자동 로드
                try:
                    voice_profiles_dir = Path(__file__).parent.parent / "voice_profiles"
                    if voice_profiles_dir.exists():
                        # profiles.json이 있으면 우선 확인
                        profiles_config = voice_profiles_dir / "profiles.json"
                        if profiles_config.exists():
                            import json
                            with open(profiles_config, 'r', encoding='utf-8') as f:
                                profiles_data = json.load(f)
                                # profiles.json에 정의된 프로필 로드
                                for profile_info in profiles_data.get('profiles', []):
                                    # profile_info가 dict인 경우 id 필드 사용, 아니면 문자열로 처리
                                    profile_id = profile_info.get('id') if isinstance(profile_info, dict) else profile_info
                                    profile_path = voice_profiles_dir / profile_id
                                    if profile_path.with_suffix('.json').exists():
                                        try:
                                            profile = await asyncio.to_thread(
                                                _tts_engine.load_voice_profile,
                                                str(profile_path)
                                            )
                                            logger.info(f"Loaded voice profile from profiles.json: {profile.name}")
                                            # 기본 프로필 설정
                                            if profiles_data.get('default_profile') == profile_id or not _tts_engine.default_voice:
                                                _tts_engine.default_voice = profile.name
                                        except Exception as e:
                                            logger.warning(f"Failed to load profile {profile_id}: {e}")
                        else:
                            # profiles.json이 없으면 폴더의 모든 .json 파일 찾기
                            profile_files = list(voice_profiles_dir.glob("*.json"))
                            for profile_file in profile_files:
                                # profiles.json은 제외
                                if profile_file.name == "profiles.json":
                                    continue
                                profile_name = profile_file.stem
                                try:
                                    profile = await asyncio.to_thread(
                                        _tts_engine.load_voice_profile,
                                        str(profile_file.with_suffix(''))  # 확장자 제거
                                    )
                                    logger.info(f"Loaded voice profile: {profile.name}")
                                    if not _tts_engine.default_voice:
                                        _tts_engine.default_voice = profile.name
                                except Exception as e:
                                    logger.warning(f"Failed to load profile {profile_name}: {e}")
                except Exception as e:
                    logger.warning(f"Failed to load voice profiles: {e}")
                    # 기본 음성 프로필 사용
            
            if _tts_engine and _tts_engine.model:
                logger.info("Generating TTS audio for chat response...")
                
                # 감정에 따른 음성 설정
                emotion = result.get("emotions", {}).get("primary_emotion", "neutral") if result.get("emotions") else "neutral"
                speech_config = CounselorVoice.get_config_for_context({
                    "emotion": emotion,
                    "response_type": "default"
                })
                
                # 클론된 음성 프로필 사용 (있으면)
                voice_profile_name = _tts_engine.default_voice or "default_counselor"
                if voice_profile_name not in _tts_engine.voice_profiles:
                    voice_profile_name = None
                
                # TTS 합성 (비동기)
                # 긴 텍스트의 경우 문장 단위로 분할하여 처리
                # Zonos는 긴 텍스트를 처리할 때 중간에 멈출 수 있으므로
                # 문장 단위로 나누어 합성 후 결합
                logger.info(f"TTS synthesis starting for text length: {len(response_text)} characters")
                
                synthesis_result = await asyncio.to_thread(
                    _tts_engine.synthesize,
                    response_text,
                    voice_profile_name,  # 클론된 음성 프로필 사용
                    speech_config
                )
                
                logger.info(f"TTS synthesis completed: duration={synthesis_result.duration:.2f}s, audio_length={len(synthesis_result.audio)}")
                
                # 오디오를 base64로 인코딩
                audio_bytes = synthesis_result.to_bytes(format="wav")
                audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                audio_duration = synthesis_result.duration
                
                logger.info(f"TTS audio generated: {audio_duration:.2f}s (voice: {voice_profile_name})")
        except Exception as e:
            logger.warning(f"Failed to generate TTS audio: {e}")
            # TTS 실패해도 텍스트 응답은 정상 반환
            audio_base64 = None
            audio_duration = None

        # Build response
        return ChatResponse(
            session_id=session_id,
            response=response_text,  # Use modified response with personalized greeting
            crisis_detected=result.get("crisis_detected", False),
            crisis_level=result.get("crisis_level", 0),
            emotions=result.get("emotions"),
            suggested_assessment=result.get("suggested_assessment"),
            response_time=response_time,
            metadata=result.get("metadata", {}),
            audio_base64=audio_base64,
            audio_duration=audio_duration
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        api_requests.labels(method="POST", endpoint="/chat", status="500").inc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@app.post("/api/v1/chat/stream", tags=["Chat"])
@limiter.limit("100/minute")
async def chat_stream(
    request: Request,
    chat_request: ChatRequest,
    authenticated: bool = Depends(verify_api_key)
):
    """
    스트리밍 채팅 엔드포인트
    
    LLM의 스트리밍 출력을 실시간으로 TTS로 변환하여 전송합니다.
    Server-Sent Events (SSE) 형식으로 응답을 스트리밍합니다.
    
    - **session_id**: Optional session ID (will be generated if not provided)
    - **user_id**: Optional user identifier for personalization
    - **message**: User message (required)
    - **conversation_history**: Optional conversation history
    - **consent**: Data storage consent (default: true)
    """
    import json
    import asyncio
    import base64
    from typing import AsyncGenerator
    
    # 시스템 초기화 확인
    if not mental_health_system:
        async def error_stream():
            yield f"data: {json.dumps({'type': 'error', 'message': '시스템이 아직 초기화 중입니다.'})}\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")
    
    if not hasattr(mental_health_system, 'llm') or mental_health_system.llm is None:
        async def error_stream():
            yield f"data: {json.dumps({'type': 'error', 'message': 'AI 모델이 아직 초기화 중입니다.'})}\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")
    
    async def generate_stream() -> AsyncGenerator[str, None]:
        """스트리밍 응답 생성"""
        # json과 asyncio를 명시적으로 참조 (스코프 문제 방지)
        import json as json_module
        import asyncio as asyncio_module
        
        session_id = None
        try:
            # 세션 관리
            session_id = get_or_create_session(chat_request.session_id)
            session_data = sessions.get(session_id, {
                "conversation_history": [],
                "crisis_detected_count": 0,
                "created_at": datetime.now()
            })
            
            # Personalization
            pm_user_id = None
            is_new_user = False
            personalized_greeting = None
            user_context = ""
            
            if personalization_manager and chat_request.user_id:
                try:
                    pm_user_id, is_new_user = personalization_manager.get_or_create_user(
                        user_identifier=chat_request.user_id,
                        consent=chat_request.consent
                    )
                    
                    if len(session_data["conversation_history"]) == 0:
                        personalized_greeting = personalization_manager.get_personalized_greeting(
                            pm_user_id, is_new_user
                        )
                    
                    user_context = personalization_manager.generate_personalized_context(pm_user_id)
                except Exception as e:
                    logger.warning(f"Personalization error: {e}")
            
            # 이미지 감정 분석 (이미지가 있는 경우)
            image_emotion_result = None
            if chat_request.image_base64:
                try:
                    from src.image_emotion_analyzer import get_image_emotion_analyzer
                    image_analyzer = get_image_emotion_analyzer()
                    image_emotion_result = await asyncio_module.to_thread(
                        image_analyzer.analyze,
                        chat_request.image_base64
                    )
                    logger.info(f"Image emotion analysis result: {image_emotion_result.get('primary_emotion', 'unknown')}")
                except Exception as e:
                    logger.warning(f"Failed to analyze image emotion: {e}")
            
            # 메시지 준비
            history = chat_request.conversation_history or session_data["conversation_history"]
            enhanced_message = chat_request.message
            
            # 이미지 감정 분석 결과를 메시지에 통합
            if image_emotion_result and image_emotion_result.get("face_detected"):
                image_emotion = image_emotion_result.get("primary_emotion", "중립")
                image_confidence = image_emotion_result.get("confidence", 0.0)
                image_emotions_detail = image_emotion_result.get("emotions", {})
                
                # 감정 상세 정보 문자열 생성
                emotion_details = ", ".join([
                    f"{emotion}({score:.2f})" 
                    for emotion, score in sorted(image_emotions_detail.items(), key=lambda x: x[1], reverse=True)[:3]
                ])
                
                image_context = f"\n\n[웹캠 이미지 분석 결과]\n- 주요 감정: {image_emotion} (신뢰도: {image_confidence:.1%})\n- 감정 분포: {emotion_details}\n- 얼굴 감지: 성공"
                enhanced_message = chat_request.message + image_context
            
            if user_context:
                enhanced_message = f"{user_context}\n\n[사용자 메시지]\n{enhanced_message}"
            
            # 세션 ID 전송
            yield f"data: {json_module.dumps({'type': 'session', 'session_id': session_id})}\n\n"
            
            # StreamingTTS 초기화
            from src.streaming_tts import StreamingTTS, StreamingTTSConfig
            from src.gpu_check import require_gpu
            
            # GPU 필수 - 감지 실패 시 상세 에러 로그와 함께 예외 발생
            device = require_gpu("cuda")
            tts_config = StreamingTTSConfig(
                voice_profile="seoyun_teacher",
                default_emotion="calm"
            )
            streaming_tts = StreamingTTS(config=tts_config, device=device)
            
            # 음성 프로필 로드 (StreamingTTS의 엔진이 ZonosTTS인 경우)
            # 음성 프로필 로드 (StreamingTTS의 엔진이 ZonosTTS인 경우)
            # _tts_engine과 동일한 방식으로 모든 프로필 로드
            if streaming_tts.engine and hasattr(streaming_tts.engine, 'load_voice_profile'):
                try:
                    voice_profiles_dir = Path(__file__).parent.parent / "voice_profiles"
                    if voice_profiles_dir.exists():
                        # profiles.json이 있으면 우선 확인
                        profiles_config = voice_profiles_dir / "profiles.json"
                        if profiles_config.exists():
                            import json
                            with open(profiles_config, 'r', encoding='utf-8') as f:
                                profiles_data = json.load(f)
                                # profiles.json에 정의된 프로필 로드
                                for profile_info in profiles_data.get('profiles', []):
                                    profile_id = profile_info.get('id') if isinstance(profile_info, dict) else profile_info
                                    profile_path = voice_profiles_dir / profile_id
                                    if profile_path.with_suffix('.json').exists():
                                        try:
                                            profile = await asyncio_module.to_thread(
                                                streaming_tts.engine.load_voice_profile,
                                                str(profile_path)
                                            )
                                            logger.info(f"Loaded voice profile for streaming from profiles.json: {profile.name}")
                                            if not streaming_tts.engine.default_voice:
                                                streaming_tts.engine.default_voice = profile.name
                                        except Exception as e:
                                            logger.warning(f"Failed to load streaming profile {profile_id}: {e}")
                        else:
                            # profiles.json이 없으면 폴더의 모든 .json 파일 찾기
                            profile_files = list(voice_profiles_dir.glob("*.json"))
                            for profile_file in profile_files:
                                # profiles.json은 제외
                                if profile_file.name == "profiles.json":
                                    continue
                                profile_name = profile_file.stem
                                try:
                                    profile = await asyncio_module.to_thread(
                                        streaming_tts.engine.load_voice_profile,
                                        str(profile_file.with_suffix(''))  # 확장자 제거
                                    )
                                    logger.info(f"Loaded voice profile for streaming: {profile.name}")
                                    if not streaming_tts.engine.default_voice:
                                        streaming_tts.engine.default_voice = profile.name
                                except Exception as e:
                                    logger.warning(f"Failed to load streaming profile {profile_name}: {e}")
                except Exception as e:
                    logger.warning(f"Failed to load voice profiles for streaming: {e}")
            
            # LLM 스트리밍 출력 생성
            response_text = ""
            full_response_text = ""
            
            # LLM 스트리밍이 지원되는지 확인
            if hasattr(mental_health_system.llm, 'generate_response_stream_async'):
                # 비동기 스트리밍 - 텍스트를 먼저 모은 후 TTS 생성 (깨짐 방지)
                try:
                    async for chunk in mental_health_system.llm.generate_response_stream_async(
                        enhanced_message,
                        history
                    ):
                        if chunk:  # 빈 청크는 무시
                            full_response_text += chunk
                            # 부분 텍스트 전송 (실시간 표시용)
                            yield f"data: {json_module.dumps({'type': 'text', 'text': full_response_text, 'is_partial': True})}\n\n"
                except Exception as stream_error:
                    logger.error(f"LLM streaming error: {stream_error}", exc_info=True)
                    # 스트리밍 오류 시 기본 응답 생성
                    if not full_response_text:
                        try:
                            full_response_text = await asyncio_module.to_thread(
                                mental_health_system.llm.generate_response,
                                enhanced_message,
                                history
                            )
                        except Exception as fallback_error:
                            logger.error(f"Fallback response generation failed: {fallback_error}")
                            full_response_text = "죄송합니다. 응답 생성 중 오류가 발생했습니다."
                    yield f"data: {json_module.dumps({'type': 'warning', 'message': '스트리밍 중 오류가 발생했습니다. 응답을 계속 진행합니다.'})}\n\n"
                
                # 최종 텍스트 전송
                yield f"data: {json_module.dumps({'type': 'text', 'text': full_response_text, 'is_partial': False})}\n\n"
                
                # 감정/위기 분석 (비동기로 수행, 응답 지연 최소화)
                try:
                    # 빠른 감정 분석만 수행
                    if mental_health_system.emotion_analyzer:
                        emotion_result = mental_health_system.emotion_analyzer.analyze(enhanced_message)
                        if emotion_result:
                            # numpy 타입을 Python 기본 타입으로 변환
                            emotion_result_serializable = convert_to_json_serializable(emotion_result)
                            yield f"data: {json_module.dumps({'type': 'emotion', 'data': emotion_result_serializable})}\n\n"
                    
                    # 위기 감지
                    if mental_health_system.safety_system:
                        safety_result = mental_health_system.safety_system.detect_crisis(
                            enhanced_message,
                            conversation_history=history
                        )
                        if safety_result.get("requires_intervention"):
                            from src.safety_system_v2 import RiskLevel
                            risk_level = safety_result.get("risk_level", RiskLevel.NONE)
                            crisis_level = mental_health_system._risk_level_to_int(risk_level)
                            crisis_data = {
                                'type': 'crisis',
                                'crisis_detected': True,
                                'crisis_level': crisis_level,
                                'crisis_details': convert_to_json_serializable(safety_result)
                            }
                            yield f"data: {json_module.dumps(crisis_data)}\n\n"
                except Exception as e:
                    logger.warning(f"Error in emotion/crisis analysis: {e}")
                
                # TTS - 전체 텍스트를 하나의 WAV로 변환 (깨짐 방지)
                try:
                    from src.tts import SpeechConfig
                    
                    # ZonosTTS 직접 사용하여 전체 텍스트 합성
                    tts_result = await asyncio_module.to_thread(
                        streaming_tts.engine.synthesize,
                        full_response_text,
                        streaming_tts.config.voice_profile,
                        SpeechConfig(emotion="calm", sample_rate=24000)
                    )
                    
                    if tts_result:
                        # 완성된 WAV 바이트로 변환
                        wav_bytes = tts_result.to_bytes(format="wav")
                        audio_base64 = base64.b64encode(wav_bytes).decode('utf-8')
                        
                        audio_data = {
                            'type': 'audio',
                            'audio_base64': audio_base64,
                            'sample_rate': 24000,
                            'duration_ms': tts_result.duration * 1000,
                            'text': full_response_text,
                            'is_last': True
                        }
                        yield f"data: {json_module.dumps(audio_data)}\n\n"
                        logger.info(f"TTS audio generated: {tts_result.duration:.2f}s for {len(full_response_text)} chars")
                except Exception as tts_error:
                    logger.error(f"TTS error: {tts_error}", exc_info=True)
                    # TTS 오류가 있어도 스트림은 계속 진행 (텍스트는 이미 전송됨)
                    yield f"data: {json_module.dumps({'type': 'warning', 'message': 'TTS 생성 중 오류가 발생했습니다. 텍스트 응답은 정상적으로 전송되었습니다.'})}\n\n"
                
            else:
                # 비스트리밍 LLM - 전체 응답 생성 후 TTS
                result = mental_health_system.process_message(
                    session_id=session_id,
                    user_message=enhanced_message,
                    conversation_history=history
                )
                
                if result and "response" in result:
                    full_response_text = result["response"]
                    if personalized_greeting:
                        full_response_text = f"{personalized_greeting}\n\n{full_response_text}"
                    
                    # 감정 데이터 전송
                    if result.get("emotions"):
                        emotions_serializable = convert_to_json_serializable(result['emotions'])
                        yield f"data: {json_module.dumps({'type': 'emotion', 'data': emotions_serializable})}\n\n"
                    
                    # 위기 감지 데이터 전송
                    if result.get("crisis_detected"):
                        crisis_data = {
                            'type': 'crisis',
                            'crisis_detected': result.get('crisis_detected', False),
                            'crisis_level': result.get('crisis_level', 0),
                            'crisis_details': convert_to_json_serializable(result.get('crisis_details'))
                        }
                        yield f"data: {json_module.dumps(crisis_data)}\n\n"
                    
                    # 치료 기법 데이터 전송 (있는 경우)
                    if result.get("metadata", {}).get("therapy_technique"):
                        therapy_data = {
                            'type': 'therapy',
                            'technique': result['metadata']['therapy_technique']
                        }
                        yield f"data: {json_module.dumps(therapy_data)}\n\n"
                    
                    # 텍스트 먼저 전송
                    yield f"data: {json_module.dumps({'type': 'text', 'text': full_response_text, 'is_partial': False})}\n\n"
                    
                    # TTS - 전체 텍스트를 하나의 WAV로 변환
                    try:
                        from src.tts import SpeechConfig
                        
                        tts_result = await asyncio.to_thread(
                            streaming_tts.engine.synthesize,
                            full_response_text,
                            streaming_tts.config.voice_profile,
                            SpeechConfig(emotion="calm", sample_rate=24000)
                        )
                        
                        if tts_result:
                            wav_bytes = tts_result.to_bytes(format="wav")
                            audio_base64 = base64.b64encode(wav_bytes).decode('utf-8')
                            
                            audio_data = {
                                'type': 'audio',
                                'audio_base64': audio_base64,
                                'sample_rate': 24000,
                                'duration_ms': tts_result.duration * 1000,
                                'text': full_response_text,
                                'is_last': True
                            }
                            yield f"data: {json_module.dumps(audio_data)}\n\n"
                    except Exception as tts_error:
                        logger.error(f"TTS error: {tts_error}")
                    
                    # TTS - 전체 텍스트를 하나의 WAV로 변환 (깨짐 방지)
                    try:
                        from src.tts import ZonosTTS, SpeechConfig
                        
                        # ZonosTTS 직접 사용하여 전체 텍스트 합성
                        tts_result = await asyncio.to_thread(
                            streaming_tts.engine.synthesize,
                            full_response_text,
                            streaming_tts.config.voice_profile,
                            SpeechConfig(emotion="calm", sample_rate=24000)
                        )
                        
                        if tts_result:
                            # 완성된 WAV 바이트로 변환
                            wav_bytes = tts_result.to_bytes(format="wav")
                            audio_base64 = base64.b64encode(wav_bytes).decode('utf-8')
                            
                            audio_data = {
                                'type': 'audio',
                                'audio_base64': audio_base64,
                                'sample_rate': 24000,
                                'duration_ms': tts_result.duration * 1000,
                                'text': full_response_text,
                                'is_last': True
                            }
                            yield f"data: {json_module.dumps(audio_data)}\n\n"
                    except Exception as tts_error:
                        logger.error(f"TTS error: {tts_error}")
            
            # 세션 히스토리 업데이트
            session_data["conversation_history"].append({
                "role": "user",
                "content": chat_request.message
            })
            session_data["conversation_history"].append({
                "role": "assistant",
                "content": full_response_text
            })
            
            if len(session_data["conversation_history"]) > 40:
                session_data["conversation_history"] = session_data["conversation_history"][-40:]
            
            # 완료 신호
            yield f"data: {json_module.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            # 오류 발생 시에도 스트림을 제대로 종료
            try:
                yield f"data: {json_module.dumps({'type': 'error', 'message': str(e)[:200]})}\n\n"
                yield f"data: {json_module.dumps({'type': 'done'})}\n\n"
            except Exception as final_error:
                logger.error(f"Error sending final error message: {final_error}")
        finally:
            # 스트림이 항상 완료되도록 보장
            try:
                # 이미 done 메시지를 보냈는지 확인하기 위해 빈 yield는 하지 않음
                # 대신 로깅만 수행
                logger.debug(f"Stream completed for session: {session_id}")
            except:
                pass
    
    return StreamingResponse(
        generate_stream(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # nginx 버퍼링 비활성화
        }
    )


@app.get("/api/v1/session/{session_id}", response_model=SessionResponse, tags=["Session"])
async def get_session(
    session_id: str,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Get session information

    Returns session details including message count and crisis detection count
    """
    if session_id not in sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )

    session_data = sessions[session_id]

    return SessionResponse(
        session_id=session_id,
        created_at=session_data["created_at"].isoformat(),
        total_messages=len(session_data["conversation_history"]) // 2,
        crisis_detected_count=session_data["crisis_detected_count"],
        last_activity=session_data["last_activity"].isoformat()
    )


@app.delete("/api/v1/session/{session_id}", tags=["Session"])
async def delete_session(
    session_id: str,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Delete a session

    Removes session data from memory
    """
    if session_id not in sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )

    del sessions[session_id]
    logger.info(f"Deleted session: {session_id}")

    return {"message": "Session deleted successfully", "session_id": session_id}


@app.post("/api/v1/assessment", response_model=AssessmentResponse, tags=["Assessment"])
@limiter.limit("20/minute")
async def conduct_assessment(
    request: Request,
    assessment_request: AssessmentRequest,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Conduct psychological assessment

    - **assessment_type**: phq9, gad7, or k10
    - **responses**: List of integer responses

    Returns assessment results with interpretation
    """
    if not mental_health_system or not mental_health_system.assessment_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Assessment system not available"
        )

    try:
        # Get appropriate assessment
        assessment_type = assessment_request.assessment_type.lower()

        if assessment_type == "phq9":
            from src.assessments import PHQ9Assessment
            assessment = PHQ9Assessment()
            if len(assessment_request.responses) != 9:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="PHQ-9 requires exactly 9 responses"
                )
        elif assessment_type == "gad7":
            from src.assessments import GAD7Assessment
            assessment = GAD7Assessment()
            if len(assessment_request.responses) != 7:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="GAD-7 requires exactly 7 responses"
                )
        elif assessment_type == "k10":
            from src.assessments import K10Assessment
            assessment = K10Assessment()
            if len(assessment_request.responses) != 10:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="K-10 requires exactly 10 responses"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid assessment type"
            )

        # Calculate results
        result = assessment.calculate_score(assessment_request.responses)

        # Store in session if exists
        if assessment_request.session_id in sessions:
            sessions[assessment_request.session_id]["assessments"].append({
                "type": assessment_type,
                "result": result,
                "timestamp": datetime.now()
            })

            # Update system stats
            mental_health_system.stats["assessments_conducted"] += 1

        # Save to database (long-term memory) if user_id provided
        if personalization_manager and assessment_request.user_id:
            try:
                # Get or create user
                pm_user_id, _ = personalization_manager.get_or_create_user(
                    user_identifier=assessment_request.user_id,
                    consent=True
                )

                # Save assessment result
                personalization_manager.save_assessment(
                    user_id=pm_user_id,
                    session_id=assessment_request.session_id,
                    assessment_type=assessment_type,
                    responses=assessment_request.responses,
                    score=result["score"],
                    severity=result["severity"],
                    interpretation=result["interpretation"],
                    recommendations=result.get("recommendations", [])
                )
                logger.info(f"Saved assessment to database for user {pm_user_id}")
            except Exception as e:
                logger.error(f"Failed to save assessment to database: {e}")

        return AssessmentResponse(
            session_id=assessment_request.session_id,
            assessment_type=assessment_type,
            score=result["score"],
            severity=result["severity"],
            interpretation=result["interpretation"],
            recommendations=result.get("recommendations", []),
            timestamp=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error conducting assessment: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Assessment error: {str(e)}"
        )


@app.post("/api/v1/feedback", tags=["Feedback"])
@limiter.limit("50/minute")
async def submit_feedback(
    request: Request,
    feedback_request: FeedbackRequest,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Submit user feedback

    Collects user feedback for quality improvement
    """
    # Store feedback (in production, save to database)
    feedback_data = {
        "session_id": feedback_request.session_id,
        "message_id": feedback_request.message_id,
        "rating": feedback_request.rating,
        "feedback_text": feedback_request.feedback_text,
        "feedback_type": feedback_request.feedback_type,
        "timestamp": datetime.now().isoformat()
    }

    # Log feedback
    logger.info(f"Feedback received: {feedback_data}")

    # In production: save to database or analytics system
    # feedback_db.insert(feedback_data)

    return {
        "message": "Feedback received successfully",
        "feedback_id": str(uuid.uuid4())
    }


@app.get("/api/v1/stats", tags=["Statistics"])
async def get_statistics(authenticated: bool = Depends(verify_api_key)):
    """
    Get system statistics

    Returns overall system statistics and metrics
    """
    if not mental_health_system:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System not initialized"
        )

    uptime = (datetime.now() - mental_health_system.stats["uptime_start"]).total_seconds()

    return {
        "total_conversations": mental_health_system.stats["total_conversations"],
        "crisis_detections": mental_health_system.stats["crisis_detections"],
        "assessments_conducted": mental_health_system.stats["assessments_conducted"],
        "active_sessions": len(sessions),
        "uptime_seconds": uptime,
        "uptime_hours": uptime / 3600,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v1/sessions/cleanup", tags=["Session"])
async def cleanup_sessions(
    max_age_hours: int = 24,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Cleanup old sessions

    Removes sessions older than max_age_hours (default: 24 hours)
    """
    removed_count = cleanup_old_sessions(max_age_hours)

    return {
        "message": f"Cleaned up {removed_count} old sessions",
        "removed_count": removed_count
    }


@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """
    Prometheus metrics endpoint

    Returns metrics in Prometheus format
    """
    from fastapi.responses import Response
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/v1/system/info", tags=["System"])
async def system_info():
    """
    Get system information

    Returns system configuration and capabilities (non-sensitive info only)
    """
    if not mental_health_system:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System not initialized"
        )

    return {
        "system": "Korean Mental Health Counseling AI",
        "version": "1.0.0",
        "capabilities": {
            "crisis_detection": mental_health_system.crisis_detector is not None,
            "emotion_analysis": mental_health_system.emotion_analyzer is not None,
            "rag_system": mental_health_system.rag_system is not None and mental_health_system.rag_system.is_indexed,
            "assessments": mental_health_system.assessment_manager is not None,
            "monitoring": mental_health_system.monitor is not None,
            "logging": mental_health_system.logger is not None
        },
        "model": {
            "name": mental_health_system.config.get("model", {}).get("name"),
            "quantization": mental_health_system.config.get("model", {}).get("quantization")
        },
        "features": [
            "Korean language support",
            "Multi-layered crisis detection",
            "Korean emotion analysis (han, jeong, etc.)",
            "Psychological assessments (PHQ-9, GAD-7, K-10)",
            "RAG-based knowledge retrieval",
            "Real-time monitoring",
            "PIPA-compliant logging",
            "Long-term memory & personalization" if personalization_manager else None
        ]
    }


# ============================================================================
# User Profile Endpoints (Personalization & Long-term Memory)
# ============================================================================

@app.get("/api/v1/user/{user_id}/profile", response_model=UserProfileResponse, tags=["User Profile"])
async def get_user_profile(
    user_id: str,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Get user profile with personalization data

    Returns user profile including preferred name, age range, concerns, and statistics
    """
    if not personalization_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Personalization system not available (ENABLE_LONG_TERM_MEMORY=false)"
        )

    try:
        # Get user context
        context = personalization_manager.get_user_context(user_id)

        if not context:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}"
            )

        # Get user from database for timestamps
        from src.database import get_db, UserManager
        db = next(get_db())
        try:
            user = UserManager.get_user(db, user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User not found: {user_id}"
                )

            return UserProfileResponse(
                user_id=user_id,
                preferred_name=context.get("preferred_name"),
                age_range=context.get("age_range"),
                main_concerns=context.get("main_concerns", []),
                total_conversations=context.get("total_conversations", 0),
                total_messages=context.get("total_messages", 0),
                crisis_count=context.get("crisis_count", 0),
                created_at=user.created_at.isoformat(),
                last_active=user.last_active.isoformat()
            )
        finally:
            db.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user profile: {str(e)}"
        )


@app.get("/api/v1/user/{user_id}/history", response_model=UserHistoryResponse, tags=["User Profile"])
async def get_user_history(
    user_id: str,
    session_id: Optional[str] = None,
    limit: int = 20,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Get user conversation history

    - **user_id**: User identifier
    - **session_id**: Optional session filter
    - **limit**: Maximum number of conversation turns (default: 20)

    Returns conversation history
    """
    if not personalization_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Personalization system not available"
        )

    try:
        conversations = personalization_manager.get_conversation_history(
            user_id=user_id,
            session_id=session_id,
            limit=limit
        )

        return UserHistoryResponse(
            user_id=user_id,
            conversations=conversations,
            total_count=len(conversations)
        )

    except Exception as e:
        logger.error(f"Error retrieving conversation history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving conversation history: {str(e)}"
        )


@app.get("/api/v1/user/{user_id}/assessments", response_model=UserAssessmentsResponse, tags=["User Profile"])
async def get_user_assessments(
    user_id: str,
    assessment_type: Optional[str] = None,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Get user assessment history and trends

    - **user_id**: User identifier
    - **assessment_type**: Optional filter by type (phq9, gad7, k10)

    Returns assessment history with trend analysis
    """
    if not personalization_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Personalization system not available"
        )

    try:
        from src.database import get_db, AssessmentManager
        db = next(get_db())
        try:
            # Get assessment history
            assessments = AssessmentManager.get_assessment_history(
                db, user_id, assessment_type, limit=10
            )

            # Get trend data if assessment_type specified
            trend = None
            if assessment_type:
                trend = AssessmentManager.get_trend_data(db, user_id, assessment_type)

            return UserAssessmentsResponse(
                user_id=user_id,
                assessments=assessments,
                trend=trend
            )
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error retrieving assessments: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving assessments: {str(e)}"
        )


@app.get("/api/v1/user/{user_id}/stats", tags=["User Profile"])
async def get_user_stats(
    user_id: str,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Get user statistics

    Returns detailed statistics about user activity
    """
    if not personalization_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Personalization system not available"
        )

    try:
        stats = personalization_manager.get_user_stats(user_id)

        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}"
            )

        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user stats: {str(e)}"
        )


@app.put("/api/v1/user/{user_id}/consent", tags=["User Profile"])
async def update_user_consent(
    user_id: str,
    consent_request: UserConsentRequest,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Update user data consent settings

    - **consent_given**: Whether user consents to data storage
    - **data_retention_days**: Optional custom retention period

    Updates user consent preferences (PIPA compliance)
    """
    if not personalization_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Personalization system not available"
        )

    try:
        from src.database import get_db, UserManager
        db = next(get_db())
        try:
            user = UserManager.get_user(db, user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User not found: {user_id}"
                )

            # Update consent
            user.consent_given = consent_request.consent_given

            if consent_request.data_retention_days is not None:
                user.data_retention_days = consent_request.data_retention_days

            db.commit()

            return {
                "message": "Consent updated successfully",
                "user_id": user_id,
                "consent_given": user.consent_given,
                "data_retention_days": user.data_retention_days
            }

        finally:
            db.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating consent: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating consent: {str(e)}"
        )


@app.delete("/api/v1/user/{user_id}", tags=["User Profile"])
async def delete_user(
    user_id: str,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Delete user data (Right to be Forgotten - PIPA compliance)

    Permanently deletes all user data including:
    - User profile
    - Conversation history
    - Assessment results
    - Metadata

    WARNING: This action is irreversible!
    """
    if not personalization_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Personalization system not available"
        )

    try:
        from src.database import get_db, UserManager
        db = next(get_db())
        try:
            user = UserManager.get_user(db, user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User not found: {user_id}"
                )

            # Delete all user data
            UserManager.delete_user(db, user_id)

            logger.info(f"User deleted (Right to be Forgotten): {user_id}")

            return {
                "message": "User data deleted successfully",
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }

        finally:
            db.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting user: {str(e)}"
        )


# ============================================================================
# Persona Endpoints (Counselor Persona System)
# ============================================================================

@app.get("/api/v1/personas", response_model=PersonaListResponse, tags=["Personas"])
async def list_personas(
    include_details: bool = False,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Get list of available counselor personas

    - **include_details**: Include full details (default: false)

    Returns list of counselor personas with their characteristics
    """
    global persona_manager
    # persona_manager가 없으면 직접 초기화 시도
    if not persona_manager:
        try:
            if PersonaManager:
                persona_manager = PersonaManager()
                logger.info("PersonaManager initialized on-demand")
            else:
                # PersonaManager를 임포트할 수 없으면 기본 응답 반환
                logger.warning("PersonaManager not available, returning default personas")
                return PersonaListResponse(
                    personas=[
                        {
                            "id": "warm_mother",
                            "name": "박은희",
                            "display_name": "박은희 상담사",
                            "age_range": "40대",
                            "gender": "female",
                            "personality_type": "따뜻하고 포용적인",
                            "specialties": ["가족 관계", "우울", "불안"],
                            "intro": "따뜻하고 모성적인 상담사"
                        }
                    ],
                    total=1
                )
        except Exception as e:
            logger.error(f"Failed to initialize PersonaManager: {e}")
            # 기본 응답 반환
            return PersonaListResponse(
                personas=[
                    {
                        "id": "warm_mother",
                        "name": "박은희",
                        "display_name": "박은희 상담사",
                        "age_range": "40대",
                        "gender": "female",
                        "personality_type": "따뜻하고 포용적인",
                        "specialties": ["가족 관계", "우울", "불안"],
                        "intro": "따뜻하고 모성적인 상담사"
                    }
                ],
                total=1
            )

    try:
        personas = persona_manager.list_personas(include_details=include_details)

        return PersonaListResponse(
            personas=personas,
            total=len(personas)
        )

    except Exception as e:
        logger.error(f"Error listing personas: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing personas: {str(e)}"
        )


@app.get("/api/v1/personas/{persona_id}", response_model=PersonaResponse, tags=["Personas"])
async def get_persona(
    persona_id: str,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Get detailed information about a specific persona

    - **persona_id**: Persona identifier (e.g., 'warm_mother')

    Returns full persona profile including personality, specialties, and counseling style
    """
    if not persona_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Persona system not available"
        )

    try:
        persona = persona_manager.get_persona(persona_id)

        if not persona:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Persona not found: {persona_id}"
            )

        return PersonaResponse(
            id=persona.id,
            name=persona.name,
            display_name=persona.display_name,
            age_range=persona.age_range,
            gender=persona.gender,
            personality_type=persona.personality['type'],
            specialties=persona.specialties,
            counseling_style=persona.counseling_style,
            intro=persona.get_brief_intro()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting persona: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting persona: {str(e)}"
        )


@app.post("/api/v1/personas/recommend", response_model=PersonaRecommendationResponse, tags=["Personas"])
async def recommend_personas(
    recommend_request: PersonaRecommendRequest,
    authenticated: bool = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Get persona recommendations based on user profile with personalization

    Uses machine learning from user feedback AND user-specific preferences
    to deliver highly personalized recommendations.

    - **age_range**: User age range (e.g., '20대', '30대')
    - **concerns**: List of concerns (e.g., ['우울', '불안', '직장'])
    - **top_k**: Number of recommendations (default: 3)
    - **user_id**: User ID for personalized recommendations (optional but recommended)

    Returns recommended personas ranked by suitability with personalization markers (⭐)
    """
    global persona_manager
    # persona_manager가 없으면 직접 초기화 시도
    if not persona_manager:
        try:
            if PersonaManager:
                persona_manager = PersonaManager()
                logger.info("PersonaManager initialized on-demand")
            else:
                # PersonaManager를 임포트할 수 없으면 기본 응답 반환
                logger.warning("PersonaManager not available, returning default recommendations")
                return PersonaRecommendationResponse(
                    recommendations=[
                        {
                            "id": "warm_mother",
                            "name": "박은희",
                            "display_name": "박은희 상담사",
                            "match_score": 0.8,
                            "reason": "기본 추천 상담사",
                            "specialties": ["우울", "불안", "가족 관계"]
                        }
                    ],
                    reason="System initializing, showing default recommendation"
                )
        except Exception as e:
            logger.error(f"Failed to initialize PersonaManager: {e}")
            # 기본 응답 반환
            return PersonaRecommendationResponse(
                recommendations=[
                    {
                        "id": "warm_mother",
                        "name": "박은희",
                        "display_name": "박은희 상담사",
                        "match_score": 0.8,
                        "reason": "기본 추천 상담사",
                        "specialties": ["우울", "불안", "가족 관계"]
                    }
                ],
                reason="System initializing, showing default recommendation"
            )

    try:
        # Use learned weights + personalization
        recommendations = persona_manager.recommend_personas(
            age_range=recommend_request.age_range,
            concerns=recommend_request.concerns,
            top_k=recommend_request.top_k,
            db_session=db,
            use_learned_weights=True,
            user_id=recommend_request.user_id,
            use_personalization=True
        )

        # Add note about learning and personalization
        learning_note = " (AI-enhanced)"
        if recommend_request.user_id:
            learning_note += " + Personalized for you"

        return PersonaRecommendationResponse(
            recommendations=recommendations,
            reason=f"Based on age: {recommend_request.age_range}, concerns: {recommend_request.concerns}{learning_note}"
        )

    except Exception as e:
        logger.error(f"Error recommending personas: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error recommending personas: {str(e)}"
        )


@app.get("/api/v1/personas/search", tags=["Personas"])
async def search_personas(
    query: str = "",
    specialty: Optional[str] = None,
    gender: Optional[str] = None,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Search personas by various criteria

    - **query**: Search query (name, specialty, personality)
    - **specialty**: Filter by specialty
    - **gender**: Filter by gender

    Returns list of matching personas
    """
    if not persona_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Persona system not available"
        )

    try:
        results = persona_manager.search_personas(
            query=query,
            specialty=specialty,
            gender=gender
        )

        personas_data = [
            {
                "id": p.id,
                "name": p.name,
                "display_name": p.display_name,
                "age_range": p.age_range,
                "gender": p.gender,
                "personality_type": p.personality['type'],
                "specialties": p.specialties,
                "intro": p.get_brief_intro()
            }
            for p in results
        ]

        return {
            "results": personas_data,
            "total": len(personas_data),
            "query": query
        }

    except Exception as e:
        logger.error(f"Error searching personas: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching personas: {str(e)}"
        )


@app.get("/api/v1/personas/stats", tags=["Personas"])
async def get_persona_statistics(authenticated: bool = Depends(verify_api_key)):
    """
    Get persona system statistics

    Returns statistics about available personas
    """
    if not persona_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Persona system not available"
        )

    try:
        stats = persona_manager.get_statistics()
        return stats

    except Exception as e:
        logger.error(f"Error getting persona statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting persona statistics: {str(e)}"
        )


@app.post("/api/v1/personas/{persona_id}/feedback", response_model=PersonaFeedbackResponse, tags=["Persona Feedback"])
async def submit_persona_feedback(
    persona_id: str,
    feedback: PersonaFeedbackRequest,
    db: Session = Depends(get_db),
    authenticated: bool = Depends(verify_api_key)
):
    """
    Submit feedback for a persona

    Collects user feedback to improve persona recommendations through machine learning.

    - **persona_id**: ID of the persona being rated
    - **rating**: 1-5 star rating
    - **helpful**: Whether the persona was helpful
    - **appropriate**: Whether the persona was appropriate for the user's needs
    - **would_recommend_again**: Whether user would use this persona again
    - **concerns_addressed**: List of concerns that were addressed
    - **feedback_text**: Optional free-form feedback
    - **user_age_range**: User's age range for better learning
    """
    if not persona_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Persona system not available"
        )

    # Verify persona exists
    persona = persona_manager.get_persona(persona_id)
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona '{persona_id}' not found"
        )

    try:
        from src.database import PersonaFeedbackManager, UserManager

        # Generate anonymous user ID if not provided
        user_id = feedback.user_id
        if not user_id:
            user_id = UserManager.generate_user_id()

        # Submit feedback
        feedback_record = PersonaFeedbackManager.submit_feedback(
            db=db,
            user_id=user_id,
            session_id=feedback.session_id,
            persona_id=persona_id,
            rating=feedback.rating,
            helpful=feedback.helpful,
            appropriate=feedback.appropriate,
            would_recommend_again=feedback.would_recommend_again,
            concerns_addressed=feedback.concerns_addressed,
            feedback_text=feedback.feedback_text,
            user_age_range=feedback.user_age_range
        )

        logger.info(f"Feedback submitted for persona {persona_id}: rating={feedback.rating}")

        return PersonaFeedbackResponse(
            success=True,
            message="Feedback submitted successfully. Thank you for helping us improve!",
            feedback_id=feedback_record.id
        )

    except Exception as e:
        logger.error(f"Error submitting feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting feedback: {str(e)}"
        )


@app.get("/api/v1/personas/{persona_id}/performance", response_model=PersonaPerformanceResponse, tags=["Persona Feedback"])
async def get_persona_performance(
    persona_id: str,
    db: Session = Depends(get_db),
    authenticated: bool = Depends(verify_api_key)
):
    """
    Get performance statistics for a specific persona

    Returns aggregated performance metrics based on user feedback.
    """
    if not persona_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Persona system not available"
        )

    # Verify persona exists
    persona = persona_manager.get_persona(persona_id)
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona '{persona_id}' not found"
        )

    try:
        from src.database import PersonaFeedbackManager

        stats = PersonaFeedbackManager.get_performance_stats(db, persona_id)

        if not stats:
            # Return default stats if no feedback yet
            return PersonaPerformanceResponse(
                persona_id=persona_id,
                total_feedback_count=0,
                average_rating=0.0,
                helpful_rate=0.0,
                appropriate_rate=0.0,
                recommendation_rate=0.0,
                last_updated=None
            )

        return PersonaPerformanceResponse(**stats)

    except Exception as e:
        logger.error(f"Error getting persona performance: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting persona performance: {str(e)}"
        )


@app.get("/api/v1/personas/analytics/all", response_model=PersonaAnalyticsResponse, tags=["Persona Feedback"])
async def get_all_personas_analytics(
    db: Session = Depends(get_db),
    authenticated: bool = Depends(verify_api_key)
):
    """
    Get analytics for all personas

    Returns performance metrics for all personas, sorted by rating.
    Useful for understanding which personas perform best overall.
    """
    if not persona_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Persona system not available"
        )

    try:
        from src.database import PersonaFeedbackManager

        all_stats = PersonaFeedbackManager.get_all_performance_stats(db)

        # Calculate overall metrics
        total_feedback = sum(s['total_feedback_count'] for s in all_stats)

        if total_feedback > 0:
            # Weighted average rating
            weighted_rating = sum(
                s['average_rating'] * s['total_feedback_count']
                for s in all_stats
            ) / total_feedback
        else:
            weighted_rating = 0.0

        # Enrich with persona display names
        enriched_stats = []
        for stat in all_stats:
            persona = persona_manager.get_persona(stat['persona_id'])
            if persona:
                enriched_stat = {
                    **stat,
                    'display_name': persona.display_name,
                    'personality_type': persona.personality['type']
                }
                enriched_stats.append(enriched_stat)

        return PersonaAnalyticsResponse(
            personas=enriched_stats,
            total_feedback_count=total_feedback,
            overall_average_rating=round(weighted_rating, 2)
        )

    except Exception as e:
        logger.error(f"Error getting persona analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting persona analytics: {str(e)}"
        )


@app.get("/api/v1/personas/learning/weights", tags=["Persona Feedback"])
async def get_learned_weights(
    persona_id: Optional[str] = None,
    concern: Optional[str] = None,
    age_range: Optional[str] = None,
    db: Session = Depends(get_db),
    authenticated: bool = Depends(verify_api_key)
):
    """
    Get learned weight adjustments

    Returns the weight adjustments learned from user feedback.
    These weights are used to improve persona recommendations over time.

    - **persona_id**: Filter by persona (optional)
    - **concern**: Filter by concern type (optional)
    - **age_range**: Filter by age range (optional)
    """
    try:
        from src.database import PersonaFeedbackManager

        adjustments = PersonaFeedbackManager.get_weight_adjustments(
            db,
            persona_id=persona_id,
            concern=concern,
            age_range=age_range
        )

        return {
            "adjustments": adjustments,
            "total": len(adjustments),
            "description": "Learned weight adjustments from user feedback"
        }

    except Exception as e:
        logger.error(f"Error getting learned weights: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting learned weights: {str(e)}"
        )


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )


# ============================================================================
# Main entry point
# ============================================================================

def main():
    """Run API server"""
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))

    logger.info(f"Starting API server on {host}:{port}")

    uvicorn.run(
        "src.api:app",
        host=host,
        port=port,
        reload=os.getenv("RELOAD", "false").lower() == "true",
        log_level="info"
    )


if __name__ == "__main__":
    main()
