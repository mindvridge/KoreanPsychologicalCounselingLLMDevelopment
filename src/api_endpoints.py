"""
API 엔드포인트 모듈 (API Endpoints)
상담 시스템 REST API

기능:
- 대화 API
- 감정 추적 API
- 심리검사 API
- 세션 요약 API
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 내부 모듈
from src.conversational_assessment import (
    ConversationalAssessment,
    AssessmentType,
    AssessmentHistory
)
from src.emotion_tracking import (
    get_emotion_tracker,
    get_emotion_visualizer,
    EmotionTracker,
    EmotionVisualizer
)
from src.session_summary import (
    get_summary_manager,
    SessionSummaryManager
)

logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic 모델
# ============================================================================

class ChatRequest(BaseModel):
    """채팅 요청"""
    user_id: str
    session_id: str
    message: str
    include_emotion: bool = True


class ChatResponse(BaseModel):
    """채팅 응답"""
    response: str
    emotion: Optional[Dict[str, Any]] = None
    assessment_suggestion: Optional[Dict[str, str]] = None


class AssessmentStartRequest(BaseModel):
    """심리검사 시작 요청"""
    user_id: str
    session_id: str
    assessment_type: str  # "phq9" or "gad7"
    user_name: Optional[str] = None


class AssessmentResponseRequest(BaseModel):
    """심리검사 응답 요청"""
    session_id: str
    response: str


class EmotionChartRequest(BaseModel):
    """감정 차트 요청"""
    user_id: str
    days: int = 7


class SessionSummaryRequest(BaseModel):
    """세션 요약 요청"""
    session_id: str
    user_id: str
    conversation_history: List[Dict[str, Any]]


# ============================================================================
# FastAPI 앱
# ============================================================================

def create_app(
    llm_engine=None,
    data_storage_path: str = "./data"
) -> FastAPI:
    """
    FastAPI 앱 생성

    Args:
        llm_engine: LLM 엔진 (선택)
        data_storage_path: 데이터 저장 경로

    Returns:
        FastAPI 앱
    """
    app = FastAPI(
        title="Korean Psychological Counseling API",
        description="한국어 심리상담 AI API",
        version="1.0.0"
    )

    # CORS 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 서비스 초기화
    emotion_tracker = get_emotion_tracker(f"{data_storage_path}/emotions.json")
    emotion_visualizer = get_emotion_visualizer()
    summary_manager = get_summary_manager(llm_engine, f"{data_storage_path}/summaries.json")

    # 심리검사 세션 저장
    assessment_sessions: Dict[str, ConversationalAssessment] = {}
    assessment_history = AssessmentHistory()

    # ========================================================================
    # 헬스체크
    # ========================================================================

    @app.get("/health")
    async def health_check():
        """헬스체크"""
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}

    # ========================================================================
    # 채팅 API
    # ========================================================================

    @app.post("/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest):
        """일반 채팅"""
        try:
            # 감정 분석
            emotion_data = None
            if request.include_emotion:
                emotion_record = emotion_tracker.record_emotion(
                    user_id=request.user_id,
                    text=request.message,
                    session_id=request.session_id
                )
                emotion_data = {
                    "primary": emotion_record.primary_emotion.value,
                    "secondary": emotion_record.secondary_emotion.value if emotion_record.secondary_emotion else None,
                    "intensity": emotion_record.intensity,
                    "valence": emotion_record.valence
                }

            # LLM 응답 생성 (구현 시)
            if llm_engine:
                response_text = await llm_engine.generate_response(request.message)
            else:
                response_text = f"말씀해주신 내용을 잘 들었습니다: {request.message[:50]}..."

            # 심리검사 제안 확인
            assessment_suggestion = None
            temp_assessment = ConversationalAssessment()
            suggestion = temp_assessment.suggest_assessment([
                {"role": "user", "content": request.message}
            ])
            if suggestion:
                assessment_suggestion = {
                    "type": suggestion[0].value,
                    "reason": suggestion[1]
                }

            return ChatResponse(
                response=response_text,
                emotion=emotion_data,
                assessment_suggestion=assessment_suggestion
            )

        except Exception as e:
            logger.error(f"Chat error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ========================================================================
    # 심리검사 API
    # ========================================================================

    @app.post("/assessment/start")
    async def start_assessment(request: AssessmentStartRequest):
        """심리검사 시작"""
        try:
            assessment_type = AssessmentType(request.assessment_type)

            # 새 검사 세션 생성
            assessment = ConversationalAssessment()
            first_question = assessment.start_assessment(
                session_id=request.session_id,
                assessment_type=assessment_type,
                user_name=request.user_name
            )

            assessment_sessions[request.session_id] = assessment

            return {
                "status": "started",
                "session_id": request.session_id,
                "assessment_type": assessment_type.value,
                "question": first_question,
                "total_questions": 9 if assessment_type == AssessmentType.PHQ9 else 7
            }

        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid assessment type: {e}")
        except Exception as e:
            logger.error(f"Assessment start error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/assessment/respond")
    async def respond_assessment(request: AssessmentResponseRequest):
        """심리검사 응답 처리"""
        try:
            assessment = assessment_sessions.get(request.session_id)
            if not assessment:
                raise HTTPException(status_code=404, detail="Assessment session not found")

            next_message, result = assessment.process_response(
                session_id=request.session_id,
                user_response=request.response
            )

            response_data = {
                "message": next_message,
                "is_complete": result is not None
            }

            if result:
                # 검사 완료
                response_data["result"] = {
                    "assessment_type": result.assessment_type.value,
                    "total_score": result.total_score,
                    "severity": result.severity,
                    "interpretation": result.interpretation,
                    "recommendations": result.recommendations,
                    "professional_help_suggested": result.professional_help_suggested,
                    "question_scores": result.question_scores
                }

                # 히스토리에 저장
                assessment_history.add_result(
                    user_id=request.session_id.split("_")[0],  # session_id에서 user_id 추출
                    result=result
                )

                # 세션 정리
                del assessment_sessions[request.session_id]

            return response_data

        except Exception as e:
            logger.error(f"Assessment respond error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/assessment/history/{user_id}")
    async def get_assessment_history(user_id: str, assessment_type: Optional[str] = None):
        """심리검사 히스토리 조회"""
        try:
            history = assessment_history.get_history(
                user_id=user_id,
                assessment_type=AssessmentType(assessment_type) if assessment_type else None
            )

            return {
                "user_id": user_id,
                "count": len(history),
                "history": [
                    {
                        "assessment_type": h.assessment_type.value,
                        "total_score": h.total_score,
                        "severity": h.severity,
                        "completed_at": h.completed_at.isoformat()
                    }
                    for h in history
                ]
            }

        except Exception as e:
            logger.error(f"Assessment history error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ========================================================================
    # 감정 추적 API
    # ========================================================================

    @app.get("/emotion/chart")
    async def get_emotion_chart(user_id: str, days: int = 7):
        """감정 차트 데이터"""
        try:
            chart_data = emotion_visualizer.generate_emotion_chart_data(
                user_id=user_id,
                days=days
            )
            return chart_data

        except Exception as e:
            logger.error(f"Emotion chart error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/emotion/distribution")
    async def get_emotion_distribution(user_id: str, days: int = 7):
        """감정 분포 데이터"""
        try:
            pie_data = emotion_visualizer.generate_emotion_pie_data(
                user_id=user_id,
                days=days
            )
            return pie_data

        except Exception as e:
            logger.error(f"Emotion distribution error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/emotion/weekly-report")
    async def get_weekly_report(user_id: str):
        """주간 감정 리포트"""
        try:
            report = emotion_visualizer.generate_weekly_report(user_id=user_id)

            return {
                "start_date": report.start_date.isoformat(),
                "end_date": report.end_date.isoformat(),
                "overall_trend": report.overall_trend,
                "total_sessions": report.total_sessions,
                "dominant_emotions": [
                    (e.value, w) for e, w in report.dominant_emotions
                ],
                "insights": report.insights,
                "recommendations": report.recommendations
            }

        except Exception as e:
            logger.error(f"Weekly report error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/emotion/recent")
    async def get_recent_emotions(user_id: str, hours: int = 24):
        """최근 감정 기록"""
        try:
            records = emotion_tracker.get_recent_emotions(
                user_id=user_id,
                hours=hours
            )

            return [
                {
                    "primary_emotion": r.primary_emotion.value,
                    "intensity": r.intensity,
                    "valence": r.valence,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in records
            ]

        except Exception as e:
            logger.error(f"Recent emotions error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ========================================================================
    # 세션 요약 API
    # ========================================================================

    @app.post("/session/summary")
    async def create_session_summary(request: SessionSummaryRequest):
        """세션 요약 생성"""
        try:
            summary = await summary_manager.create_summary(
                session_id=request.session_id,
                user_id=request.user_id,
                conversation_history=request.conversation_history
            )

            return {
                "session_id": summary.session_id,
                "start_time": summary.start_time.isoformat(),
                "end_time": summary.end_time.isoformat(),
                "duration_minutes": summary.duration_minutes,
                "brief_summary": summary.brief_summary,
                "detailed_summary": summary.detailed_summary,
                "main_topics": [(t.value, w) for t, w in summary.main_topics],
                "key_points": summary.key_points,
                "dominant_emotion": summary.dominant_emotion,
                "emotional_shift": summary.emotional_shift,
                "emotional_journey": summary.emotional_journey,
                "insights": summary.insights,
                "homework": summary.homework,
                "next_session_suggestions": summary.next_session_suggestions
            }

        except Exception as e:
            logger.error(f"Session summary error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/session/history")
    async def get_session_history(user_id: str, limit: int = 10):
        """세션 히스토리"""
        try:
            summaries = summary_manager.get_user_summaries(
                user_id=user_id,
                limit=limit
            )

            return [
                {
                    "session_id": s.session_id,
                    "start_time": s.start_time.isoformat(),
                    "duration_minutes": s.duration_minutes,
                    "brief_summary": s.brief_summary,
                    "main_topics": [(t.value, w) for t, w in s.main_topics[:2]],
                    "dominant_emotion": s.dominant_emotion,
                    "emotional_shift": s.emotional_shift
                }
                for s in summaries
            ]

        except Exception as e:
            logger.error(f"Session history error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/session/progress")
    async def get_progress_report(user_id: str, days: int = 30):
        """진행 상황 리포트"""
        try:
            report = summary_manager.get_progress_report(
                user_id=user_id,
                days=days
            )
            return report

        except Exception as e:
            logger.error(f"Progress report error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return app


# ============================================================================
# 메인
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
