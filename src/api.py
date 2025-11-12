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
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field, validator
import uvicorn
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main_integrated import IntegratedMentalHealthSystem
from src.safety_system_v2 import RiskLevel

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
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        None,
        description="Conversation history in format [{'role': 'user/assistant', 'content': '...'}]"
    )

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


# ============================================================================
# Global State and Session Management
# ============================================================================

# Global system instance (singleton)
mental_health_system: Optional[IntegratedMentalHealthSystem] = None

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
    """Initialize system on startup"""
    global mental_health_system

    logger.info("="*70)
    logger.info("Starting Korean Mental Health Counseling API")
    logger.info("="*70)

    try:
        # Initialize integrated system
        config_path = os.getenv("CONFIG_PATH", "configs/config.yaml")
        mental_health_system = IntegratedMentalHealthSystem(config_path=config_path)

        # Initialize all components
        success = mental_health_system.initialize_all_components()

        if not success:
            logger.error("Failed to initialize some components")
            logger.warning("API will run in degraded mode")
        else:
            logger.info("All components initialized successfully")

        logger.info("API is ready to accept requests")
        logger.info("="*70)

    except Exception as e:
        logger.error(f"Failed to initialize system: {e}", exc_info=True)
        logger.error("API will start but may not function correctly")


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
    """Root endpoint - API information"""
    return {
        "name": "Korean Mental Health Counseling API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "health": "/api/v1/health",
            "chat": "/api/v1/chat",
            "metrics": "/metrics"
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
    Process a chat message

    - **session_id**: Optional session ID (will be generated if not provided)
    - **message**: User message (required)
    - **conversation_history**: Optional conversation history

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

        # Use session history if not provided
        history = chat_request.conversation_history or session_data["conversation_history"]

        # Process message through integrated system
        result = mental_health_system.process_message(
            session_id=session_id,
            user_message=chat_request.message,
            conversation_history=history
        )

        # Check for errors
        if "error" in result:
            api_requests.labels(method="POST", endpoint="/chat", status="500").inc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )

        # Update session history
        session_data["conversation_history"].append({
            "role": "user",
            "content": chat_request.message
        })
        session_data["conversation_history"].append({
            "role": "assistant",
            "content": result["response"]
        })

        # Limit history length (keep last 20 messages)
        if len(session_data["conversation_history"]) > 40:  # 20 pairs
            session_data["conversation_history"] = session_data["conversation_history"][-40:]

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
            response=result["response"],
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
            "PIPA-compliant logging"
        ]
    }


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
