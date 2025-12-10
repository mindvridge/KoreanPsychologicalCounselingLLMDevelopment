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

from fastapi import FastAPI, HTTPException, Depends, Header, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
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
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="Korean Mental Health Counseling API",
    description="AI-powered mental health counseling system with crisis detection and psychological assessments",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add rate limit exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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

    @validator('message')
    def message_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()


class ChatResponse(BaseModel):
    """Chat message response"""
    session_id: str = Field(..., description="Session ID")
    response: str = Field(..., description="AI assistant response")
    crisis_detected: bool = Field(..., description="Whether crisis was detected")
    crisis_level: int = Field(..., description="Crisis level (0=none, 1-5=severity)")
    emotions: Optional[Dict[str, Any]] = Field(None, description="Detected emotions")
    suggested_assessment: Optional[str] = Field(None, description="Suggested psychological assessment")
    response_time: float = Field(..., description="Response time in seconds")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata")


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
        try:
            # Initialize integrated system
            config_path = os.getenv("CONFIG_PATH", "configs/config.yaml")
            logger.info(f"Initializing system with config: {config_path}")
            mental_health_system = IntegratedMentalHealthSystem(config_path=config_path)

            # Initialize all components
            success = mental_health_system.initialize_all_components()

            if not success:
                logger.error("Failed to initialize some components")
                logger.warning("API will run in degraded mode")
            else:
                logger.info("All components initialized successfully")

            # Initialize personalization manager (long-term memory)
            if os.getenv("ENABLE_LONG_TERM_MEMORY", "true").lower() == "true":
                try:
                    personalization_manager = PersonalizationManager()
                    logger.info("✓ PersonalizationManager initialized (long-term memory enabled)")
                except Exception as e:
                    logger.error(f"Failed to initialize PersonalizationManager: {e}")
                    logger.warning("Long-term memory features will be disabled")
            else:
                logger.info("Long-term memory disabled (ENABLE_LONG_TERM_MEMORY=false)")

            # Initialize persona manager (counselor personas)
            try:
                persona_manager = PersonaManager()
                logger.info(f"✓ PersonaManager initialized ({len(persona_manager.personas)} personas loaded)")
            except Exception as e:
                logger.error(f"Failed to initialize PersonaManager: {e}")
                logger.warning("Persona features will be disabled")

            logger.info("API is ready to accept requests")
            logger.info("="*70)

        except Exception as e:
            logger.error(f"Failed to initialize system: {e}", exc_info=True)
            logger.error("API will start but may not function correctly")
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
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System not initialized"
        )

    # Validate components
    validation_results = mental_health_system.validate_system()

    # Calculate uptime
    uptime = (datetime.now() - mental_health_system.stats["uptime_start"]).total_seconds()

    # Overall status
    all_critical_ok = validation_results.get("llm", False) and validation_results.get("crisis_detector", False)
    overall_status = "healthy" if all_critical_ok else "degraded"

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now().isoformat(),
        components=validation_results,
        uptime_seconds=uptime
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

    if not mental_health_system or not mental_health_system.is_initialized:
        api_requests.labels(method="POST", endpoint="/chat", status="503").inc()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System not initialized. Please try again later."
        )

    try:
        # Get or create session
        session_id = get_or_create_session(chat_request.session_id)

        # Get session data
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

        # Add user context to message for personalized responses
        enhanced_message = chat_request.message
        if user_context:
            # Prepend context for LLM (will be processed but not shown to user)
            enhanced_message = f"{user_context}\n\n[사용자 메시지]\n{chat_request.message}"

        # Process message through integrated system
        result = mental_health_system.process_message(
            session_id=session_id,
            user_message=enhanced_message,
            conversation_history=history
        )

        # Check for errors
        if "error" in result:
            api_requests.labels(method="POST", endpoint="/chat", status="500").inc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
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

        # Build response
        return ChatResponse(
            session_id=session_id,
            response=response_text,  # Use modified response with personalized greeting
            crisis_detected=result.get("crisis_detected", False),
            crisis_level=result.get("crisis_level", 0),
            emotions=result.get("emotions"),
            suggested_assessment=result.get("suggested_assessment"),
            response_time=response_time,
            metadata=result.get("metadata", {})
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
    if not persona_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Persona system not available"
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
    if not persona_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Persona system not available"
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
