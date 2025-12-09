"""
배치 처리 API (Batch Processing API)
배치 처리를 지원하는 FastAPI 엔드포인트

기능:
- 배치 요청 제출
- 우선순위 지정
- 비동기 결과 조회
- 배치 통계 모니터링
"""

import logging
import asyncio
from typing import Optional, List
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from batch_processor import (
    BatchProcessor,
    AdaptiveBatchProcessor,
    BatchConfig,
    BatchStrategy,
    RequestPriority,
    BatchRequest,
    detect_crisis_priority,
    get_batch_processor,
    submit_request
)

logger = logging.getLogger(__name__)


# =============================================================================
# Pydantic Models
# =============================================================================

class BatchChatRequest(BaseModel):
    """배치 채팅 요청"""
    message: str = Field(..., min_length=1, description="사용자 메시지")
    session_id: Optional[str] = Field(None, description="세션 ID")
    priority: Optional[str] = Field("standard", description="우선순위 (crisis, realtime, premium, standard, background)")
    auto_detect_crisis: bool = Field(True, description="위기 상황 자동 감지")
    context: Optional[List[dict]] = Field(None, description="대화 컨텍스트")


class BatchChatResponse(BaseModel):
    """배치 채팅 응답"""
    request_id: str
    response: str
    priority_used: str
    wait_time_ms: float
    processing_time_ms: float
    timestamp: str


class AsyncBatchRequest(BaseModel):
    """비동기 배치 요청"""
    message: str
    session_id: Optional[str] = None
    priority: Optional[str] = "standard"
    callback_url: Optional[str] = None  # 완료 시 콜백


class AsyncBatchResponse(BaseModel):
    """비동기 배치 응답"""
    request_id: str
    status: str  # queued, processing, completed, error
    position_in_queue: Optional[int] = None


class BatchStatusResponse(BaseModel):
    """배치 상태 응답"""
    request_id: str
    status: str
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None


class BatchStatsResponse(BaseModel):
    """배치 통계 응답"""
    total_requests: int
    total_batches: int
    avg_batch_size: float
    avg_processing_time_ms: float
    requests_per_second: float
    queue_size: int
    queue_by_priority: dict
    config: dict


# =============================================================================
# Global State
# =============================================================================

_processor: Optional[BatchProcessor] = None
_pending_requests: dict = {}  # 비동기 요청 추적


async def get_processor() -> BatchProcessor:
    """배치 프로세서 인스턴스"""
    global _processor

    if _processor is None:
        config = BatchConfig(
            strategy=BatchStrategy.ADAPTIVE,
            min_batch_size=1,
            max_batch_size=8,
            max_wait_time_ms=500
        )
        _processor = AdaptiveBatchProcessor(config)
        await _processor.start()

    return _processor


def parse_priority(priority_str: str) -> RequestPriority:
    """문자열을 우선순위로 변환"""
    priority_map = {
        "crisis": RequestPriority.CRISIS,
        "realtime": RequestPriority.REALTIME,
        "premium": RequestPriority.PREMIUM,
        "standard": RequestPriority.STANDARD,
        "background": RequestPriority.BACKGROUND
    }
    return priority_map.get(priority_str.lower(), RequestPriority.STANDARD)


# =============================================================================
# FastAPI App
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 생명주기"""
    logger.info("Batch API starting up...")
    await get_processor()  # 프로세서 초기화
    yield
    logger.info("Batch API shutting down...")
    if _processor:
        await _processor.stop()


app = FastAPI(
    title="Batch Processing API",
    description="한국어 심리상담 배치 처리 API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Endpoints - 동기 배치 처리
# =============================================================================

@app.post("/api/v1/batch/chat", response_model=BatchChatResponse, tags=["배치 처리"])
async def batch_chat(request: BatchChatRequest):
    """
    배치 채팅 요청 (동기)

    요청을 배치 큐에 넣고 결과를 기다림
    """
    processor = await get_processor()
    start_time = datetime.now()

    # 우선순위 결정
    priority = parse_priority(request.priority)

    # 위기 상황 자동 감지
    if request.auto_detect_crisis:
        detected = detect_crisis_priority(request.message)
        if detected == RequestPriority.CRISIS:
            priority = RequestPriority.CRISIS
            logger.warning(f"Crisis detected, priority elevated")

    try:
        # 요청 제출 및 대기
        submit_time = datetime.now()
        result = await processor.submit_and_wait(
            data=request.message,
            priority=priority,
            session_id=request.session_id,
            request_type="chat",
            metadata={"context": request.context or []},
            timeout=30.0
        )
        end_time = datetime.now()

        # 시간 계산
        wait_time = (submit_time - start_time).total_seconds() * 1000
        processing_time = (end_time - submit_time).total_seconds() * 1000

        return BatchChatResponse(
            request_id=str(id(request)),
            response=result,
            priority_used=priority.name,
            wait_time_ms=round(wait_time, 2),
            processing_time_ms=round(processing_time, 2),
            timestamp=datetime.now().isoformat()
        )

    except TimeoutError:
        raise HTTPException(status_code=504, detail="Request timed out")
    except Exception as e:
        logger.error(f"Batch chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/batch/chat/bulk", tags=["배치 처리"])
async def batch_chat_bulk(requests: List[BatchChatRequest]):
    """
    대량 배치 요청

    여러 요청을 한 번에 제출
    """
    processor = await get_processor()
    results = []

    # 모든 요청 제출
    batch_requests = []
    for req in requests:
        priority = parse_priority(req.priority)

        if req.auto_detect_crisis:
            detected = detect_crisis_priority(req.message)
            if detected == RequestPriority.CRISIS:
                priority = RequestPriority.CRISIS

        batch_req = await processor.submit(
            data=req.message,
            priority=priority,
            session_id=req.session_id,
            request_type="chat",
            metadata={"context": req.context or []}
        )
        batch_requests.append(batch_req)

    # 모든 결과 대기
    for batch_req in batch_requests:
        try:
            result = await batch_req.wait_for_result(timeout=60.0)
            results.append({
                "request_id": batch_req.request_id,
                "status": "success",
                "response": result
            })
        except Exception as e:
            results.append({
                "request_id": batch_req.request_id,
                "status": "error",
                "error": str(e)
            })

    return {
        "total": len(requests),
        "success": sum(1 for r in results if r["status"] == "success"),
        "results": results
    }


# =============================================================================
# Endpoints - 비동기 배치 처리
# =============================================================================

@app.post("/api/v1/batch/async/submit", response_model=AsyncBatchResponse, tags=["비동기 배치"])
async def async_submit(request: AsyncBatchRequest, background_tasks: BackgroundTasks):
    """
    비동기 배치 요청 제출

    요청만 제출하고 즉시 반환, 나중에 결과 조회
    """
    processor = await get_processor()

    priority = parse_priority(request.priority)
    detected = detect_crisis_priority(request.message)
    if detected == RequestPriority.CRISIS:
        priority = RequestPriority.CRISIS

    # 요청 제출
    batch_req = await processor.submit(
        data=request.message,
        priority=priority,
        session_id=request.session_id,
        request_type="chat"
    )

    # 추적용 저장
    _pending_requests[batch_req.request_id] = batch_req

    # 콜백 설정 (선택)
    if request.callback_url:
        background_tasks.add_task(
            _wait_and_callback,
            batch_req,
            request.callback_url
        )

    # 큐 위치 계산
    queue_status = processor.get_queue_status()
    position = queue_status.get("total", 0)

    return AsyncBatchResponse(
        request_id=batch_req.request_id,
        status="queued",
        position_in_queue=position
    )


@app.get("/api/v1/batch/async/status/{request_id}", response_model=BatchStatusResponse, tags=["비동기 배치"])
async def async_status(request_id: str):
    """
    비동기 요청 상태 조회
    """
    if request_id not in _pending_requests:
        raise HTTPException(status_code=404, detail="Request not found")

    batch_req = _pending_requests[request_id]

    status = "processing"
    if batch_req.completed:
        status = "completed" if not batch_req.error else "error"

    return BatchStatusResponse(
        request_id=request_id,
        status=status,
        result=batch_req.result if batch_req.completed else None,
        error=batch_req.error,
        created_at=batch_req.created_at.isoformat(),
        completed_at=batch_req.completed_at.isoformat() if batch_req.completed_at else None
    )


@app.get("/api/v1/batch/async/result/{request_id}", tags=["비동기 배치"])
async def async_result(request_id: str, wait: bool = False, timeout: float = 30.0):
    """
    비동기 요청 결과 조회

    wait=True면 완료까지 대기
    """
    if request_id not in _pending_requests:
        raise HTTPException(status_code=404, detail="Request not found")

    batch_req = _pending_requests[request_id]

    if wait and not batch_req.completed:
        try:
            await batch_req.wait_for_result(timeout=timeout)
        except TimeoutError:
            raise HTTPException(status_code=504, detail="Request timed out")

    if not batch_req.completed:
        return {
            "request_id": request_id,
            "status": "processing",
            "message": "Request still processing"
        }

    # 완료된 요청 정리
    del _pending_requests[request_id]

    if batch_req.error:
        raise HTTPException(status_code=500, detail=batch_req.error)

    return {
        "request_id": request_id,
        "status": "completed",
        "result": batch_req.result,
        "processing_time_ms": (
            (batch_req.completed_at - batch_req.created_at).total_seconds() * 1000
            if batch_req.completed_at else None
        )
    }


async def _wait_and_callback(batch_req: BatchRequest, callback_url: str):
    """결과 대기 후 콜백"""
    import httpx

    try:
        await batch_req.wait_for_result(timeout=60.0)

        async with httpx.AsyncClient() as client:
            await client.post(callback_url, json={
                "request_id": batch_req.request_id,
                "status": "completed" if not batch_req.error else "error",
                "result": batch_req.result,
                "error": batch_req.error
            })
    except Exception as e:
        logger.error(f"Callback failed: {e}")


# =============================================================================
# Endpoints - 모니터링
# =============================================================================

@app.get("/api/v1/batch/stats", response_model=BatchStatsResponse, tags=["모니터링"])
async def get_batch_stats():
    """배치 처리 통계"""
    processor = await get_processor()
    stats = processor.get_stats()

    return BatchStatsResponse(**stats)


@app.get("/api/v1/batch/queue", tags=["모니터링"])
async def get_queue_status():
    """큐 상태"""
    processor = await get_processor()
    return processor.get_queue_status()


@app.get("/api/v1/batch/health", tags=["모니터링"])
async def batch_health():
    """배치 프로세서 헬스체크"""
    processor = await get_processor()
    stats = processor.get_stats()

    return {
        "status": "healthy",
        "processor_running": processor._running,
        "queue_size": stats["queue_size"],
        "total_processed": stats["total_requests"],
        "avg_latency_ms": stats["avg_processing_time_ms"]
    }


# =============================================================================
# Endpoints - 설정
# =============================================================================

@app.post("/api/v1/batch/config", tags=["설정"])
async def update_batch_config(
    strategy: Optional[str] = None,
    max_batch_size: Optional[int] = None,
    max_wait_time_ms: Optional[int] = None
):
    """배치 설정 업데이트 (런타임)"""
    processor = await get_processor()

    if strategy:
        try:
            processor.config.strategy = BatchStrategy(strategy)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid strategy: {strategy}")

    if max_batch_size:
        processor.config.max_batch_size = max_batch_size

    if max_wait_time_ms:
        processor.config.max_wait_time_ms = max_wait_time_ms

    return {
        "status": "updated",
        "config": {
            "strategy": processor.config.strategy.value,
            "max_batch_size": processor.config.max_batch_size,
            "max_wait_time_ms": processor.config.max_wait_time_ms
        }
    }


# =============================================================================
# Run Server
# =============================================================================

def run_batch_api(host: str = "0.0.0.0", port: int = 8002):
    """배치 API 서버 실행"""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_batch_api()
