"""
배치 처리 API v2 (Batch Processing API v2)
확장된 배치 처리 기능

새로운 기능:
- 웹훅 콜백
- 재시도 로직
- 우선순위 에스컬레이션
- 배치 취소
- 결과 만료
- 상세 메트릭
"""

import logging
import asyncio
import hashlib
import httpx
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import json

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl
import uuid

logger = logging.getLogger(__name__)


# ============================================================================
# 상수 및 설정
# ============================================================================

class BatchStatus(Enum):
    """배치 상태"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class Priority(Enum):
    """우선순위"""
    CRISIS = 0      # 위기 상황 - 즉시 처리
    REALTIME = 1    # 실시간 - 100ms 이내
    PREMIUM = 2     # 프리미엄 - 500ms 이내
    STANDARD = 3    # 표준 - 2초 이내
    BACKGROUND = 4  # 백그라운드 - 여유있게

    @classmethod
    def from_string(cls, value: str) -> "Priority":
        mapping = {
            "crisis": cls.CRISIS,
            "realtime": cls.REALTIME,
            "premium": cls.PREMIUM,
            "standard": cls.STANDARD,
            "background": cls.BACKGROUND
        }
        return mapping.get(value.lower(), cls.STANDARD)


@dataclass
class BatchConfig:
    """배치 처리 설정"""
    max_batch_size: int = 16
    max_wait_time_ms: int = 500
    max_retries: int = 3
    retry_delay_ms: int = 1000
    result_ttl_seconds: int = 3600  # 1시간
    webhook_timeout_seconds: int = 30
    escalation_threshold_ms: int = 5000


# ============================================================================
# 요청/응답 모델
# ============================================================================

class BatchRequest(BaseModel):
    """배치 요청"""
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    priority: str = Field("standard", description="우선순위")
    metadata: Optional[Dict[str, Any]] = None


class BatchWebhookRequest(BatchRequest):
    """웹훅 포함 배치 요청"""
    webhook_url: Optional[HttpUrl] = None
    webhook_headers: Optional[Dict[str, str]] = None


class BulkBatchRequest(BaseModel):
    """대량 배치 요청"""
    requests: List[BatchRequest]
    fail_fast: bool = Field(False, description="첫 오류시 중단")


class BatchResponse(BaseModel):
    """배치 응답"""
    request_id: str
    status: str
    response: Optional[str] = None
    error: Optional[str] = None
    priority: str
    queue_position: Optional[int] = None
    processing_time_ms: Optional[float] = None
    created_at: str
    completed_at: Optional[str] = None


class BatchStats(BaseModel):
    """배치 통계"""
    total_requests: int
    completed_requests: int
    failed_requests: int
    average_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    requests_per_minute: float
    queue_depth: int
    queue_by_priority: Dict[str, int]


# ============================================================================
# 배치 관리자
# ============================================================================

@dataclass
class BatchItem:
    """배치 항목"""
    request_id: str
    message: str
    session_id: Optional[str]
    priority: Priority
    status: BatchStatus = BatchStatus.QUEUED
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    retries: int = 0
    metadata: Dict = field(default_factory=dict)
    webhook_url: Optional[str] = None
    webhook_headers: Optional[Dict] = None


class EnhancedBatchProcessor:
    """
    향상된 배치 프로세서

    특징:
    - 우선순위 큐
    - 자동 에스컬레이션
    - 웹훅 콜백
    - 재시도 로직
    - 상세 메트릭
    """

    def __init__(self, config: BatchConfig = None, process_fn: Callable = None):
        self.config = config or BatchConfig()
        self.process_fn = process_fn

        # 우선순위별 큐
        self.queues: Dict[Priority, asyncio.Queue] = {
            p: asyncio.Queue() for p in Priority
        }

        # 요청 추적
        self.items: Dict[str, BatchItem] = {}

        # 메트릭
        self.latencies: List[float] = []
        self.request_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.start_time = datetime.now()

        # 상태
        self._running = False
        self._workers: List[asyncio.Task] = []

    async def start(self, num_workers: int = 4):
        """프로세서 시작"""
        if self._running:
            return

        self._running = True

        # 워커 시작
        for i in range(num_workers):
            worker = asyncio.create_task(self._worker(i))
            self._workers.append(worker)

        # 에스컬레이션 태스크
        asyncio.create_task(self._escalation_monitor())

        # 정리 태스크
        asyncio.create_task(self._cleanup_expired())

        logger.info(f"BatchProcessor started with {num_workers} workers")

    async def stop(self):
        """프로세서 중지"""
        self._running = False

        for worker in self._workers:
            worker.cancel()

        logger.info("BatchProcessor stopped")

    async def submit(
        self,
        message: str,
        session_id: Optional[str] = None,
        priority: str = "standard",
        metadata: Dict = None,
        webhook_url: str = None,
        webhook_headers: Dict = None
    ) -> str:
        """요청 제출"""
        request_id = str(uuid.uuid4())
        priority_enum = Priority.from_string(priority)

        # 위기 감지
        if self._detect_crisis(message):
            priority_enum = Priority.CRISIS
            logger.warning(f"Crisis detected, escalating priority: {request_id}")

        item = BatchItem(
            request_id=request_id,
            message=message,
            session_id=session_id,
            priority=priority_enum,
            metadata=metadata or {},
            webhook_url=webhook_url,
            webhook_headers=webhook_headers
        )

        self.items[request_id] = item
        await self.queues[priority_enum].put(item)

        self.request_count += 1

        return request_id

    async def get_result(
        self,
        request_id: str,
        wait: bool = False,
        timeout: float = 30.0
    ) -> BatchItem:
        """결과 조회"""
        if request_id not in self.items:
            raise KeyError(f"Request not found: {request_id}")

        item = self.items[request_id]

        if wait and item.status in [BatchStatus.QUEUED, BatchStatus.PROCESSING]:
            # 완료 대기
            start = datetime.now()
            while item.status in [BatchStatus.QUEUED, BatchStatus.PROCESSING]:
                await asyncio.sleep(0.1)
                if (datetime.now() - start).total_seconds() > timeout:
                    raise TimeoutError("Request timed out")

        return item

    async def cancel(self, request_id: str) -> bool:
        """요청 취소"""
        if request_id not in self.items:
            return False

        item = self.items[request_id]

        if item.status == BatchStatus.QUEUED:
            item.status = BatchStatus.CANCELLED
            item.completed_at = datetime.now()
            return True

        return False

    def _detect_crisis(self, message: str) -> bool:
        """위기 상황 감지"""
        crisis_keywords = [
            "자살", "죽고 싶", "죽을래", "자해", "목숨",
            "끝내고 싶", "살고 싶지 않", "사라지고 싶"
        ]
        return any(kw in message for kw in crisis_keywords)

    async def _worker(self, worker_id: int):
        """워커 태스크"""
        while self._running:
            try:
                # 우선순위 순서로 처리
                item = None
                for priority in Priority:
                    try:
                        item = self.queues[priority].get_nowait()
                        break
                    except asyncio.QueueEmpty:
                        continue

                if item is None:
                    await asyncio.sleep(0.01)
                    continue

                # 처리
                await self._process_item(item)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")

    async def _process_item(self, item: BatchItem):
        """항목 처리"""
        item.status = BatchStatus.PROCESSING
        start_time = datetime.now()

        try:
            # 실제 처리
            if self.process_fn:
                result = await self._call_with_retry(item)
            else:
                # 더미 응답
                result = f"[응답] {item.message[:50]}..."

            item.result = result
            item.status = BatchStatus.COMPLETED
            item.completed_at = datetime.now()
            self.success_count += 1

            # 지연시간 기록
            latency = (item.completed_at - item.created_at).total_seconds() * 1000
            self.latencies.append(latency)

            # 최근 1000개만 유지
            if len(self.latencies) > 1000:
                self.latencies = self.latencies[-1000:]

        except Exception as e:
            item.error = str(e)
            item.status = BatchStatus.FAILED
            item.completed_at = datetime.now()
            self.failure_count += 1
            logger.error(f"Processing failed: {item.request_id} - {e}")

        # 웹훅 콜백
        if item.webhook_url:
            asyncio.create_task(self._send_webhook(item))

    async def _call_with_retry(self, item: BatchItem) -> str:
        """재시도 로직"""
        last_error = None

        for attempt in range(self.config.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(self.process_fn):
                    return await self.process_fn(item.message, item.session_id)
                else:
                    return await asyncio.to_thread(
                        self.process_fn,
                        item.message,
                        item.session_id
                    )
            except Exception as e:
                last_error = e
                item.retries = attempt + 1

                if attempt < self.config.max_retries:
                    delay = self.config.retry_delay_ms / 1000 * (2 ** attempt)
                    await asyncio.sleep(delay)

        raise last_error

    async def _send_webhook(self, item: BatchItem):
        """웹훅 전송"""
        try:
            async with httpx.AsyncClient(timeout=self.config.webhook_timeout_seconds) as client:
                payload = {
                    "request_id": item.request_id,
                    "status": item.status.value,
                    "result": item.result,
                    "error": item.error,
                    "processing_time_ms": (
                        (item.completed_at - item.created_at).total_seconds() * 1000
                        if item.completed_at else None
                    )
                }

                headers = item.webhook_headers or {}
                headers["Content-Type"] = "application/json"

                await client.post(
                    item.webhook_url,
                    json=payload,
                    headers=headers
                )
                logger.info(f"Webhook sent for {item.request_id}")

        except Exception as e:
            logger.error(f"Webhook failed for {item.request_id}: {e}")

    async def _escalation_monitor(self):
        """우선순위 에스컬레이션 모니터"""
        while self._running:
            try:
                now = datetime.now()
                threshold = timedelta(milliseconds=self.config.escalation_threshold_ms)

                for item in self.items.values():
                    if item.status != BatchStatus.QUEUED:
                        continue

                    # 오래 대기한 요청 에스컬레이션
                    wait_time = now - item.created_at
                    if wait_time > threshold and item.priority.value > Priority.PREMIUM.value:
                        # 우선순위 상향
                        old_priority = item.priority
                        item.priority = Priority(max(0, item.priority.value - 1))
                        logger.info(
                            f"Escalated {item.request_id}: {old_priority.name} -> {item.priority.name}"
                        )

                await asyncio.sleep(1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Escalation monitor error: {e}")

    async def _cleanup_expired(self):
        """만료된 결과 정리"""
        while self._running:
            try:
                now = datetime.now()
                ttl = timedelta(seconds=self.config.result_ttl_seconds)

                expired = [
                    rid for rid, item in self.items.items()
                    if item.completed_at and (now - item.completed_at) > ttl
                ]

                for rid in expired:
                    del self.items[rid]

                if expired:
                    logger.info(f"Cleaned up {len(expired)} expired results")

                await asyncio.sleep(60)  # 1분마다 정리

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """통계 조회"""
        # 지연시간 계산
        if self.latencies:
            sorted_lat = sorted(self.latencies)
            avg_lat = sum(sorted_lat) / len(sorted_lat)
            p50 = sorted_lat[int(len(sorted_lat) * 0.50)]
            p95 = sorted_lat[int(len(sorted_lat) * 0.95)]
            p99 = sorted_lat[int(len(sorted_lat) * 0.99)]
        else:
            avg_lat = p50 = p95 = p99 = 0

        # RPM 계산
        elapsed = (datetime.now() - self.start_time).total_seconds() / 60
        rpm = self.request_count / elapsed if elapsed > 0 else 0

        # 큐 상태
        queue_by_priority = {
            p.name: self.queues[p].qsize() for p in Priority
        }
        total_queue = sum(queue_by_priority.values())

        return {
            "total_requests": self.request_count,
            "completed_requests": self.success_count,
            "failed_requests": self.failure_count,
            "average_latency_ms": round(avg_lat, 2),
            "p50_latency_ms": round(p50, 2),
            "p95_latency_ms": round(p95, 2),
            "p99_latency_ms": round(p99, 2),
            "requests_per_minute": round(rpm, 2),
            "queue_depth": total_queue,
            "queue_by_priority": queue_by_priority
        }


# ============================================================================
# FastAPI 앱
# ============================================================================

_processor: Optional[EnhancedBatchProcessor] = None


async def get_processor() -> EnhancedBatchProcessor:
    global _processor
    if _processor is None:
        _processor = EnhancedBatchProcessor()
        await _processor.start()
    return _processor


app = FastAPI(
    title="Batch Processing API v2",
    description="향상된 배치 처리 API - 웹훅, 재시도, 에스컬레이션 지원",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ============================================================================
# 엔드포인트
# ============================================================================

@app.post("/api/v2/batch/submit", response_model=BatchResponse, tags=["배치 처리"])
async def submit_batch(request: BatchWebhookRequest):
    """배치 요청 제출"""
    processor = await get_processor()

    request_id = await processor.submit(
        message=request.message,
        session_id=request.session_id,
        priority=request.priority,
        metadata=request.metadata,
        webhook_url=str(request.webhook_url) if request.webhook_url else None,
        webhook_headers=request.webhook_headers
    )

    item = processor.items[request_id]

    return BatchResponse(
        request_id=request_id,
        status=item.status.value,
        priority=item.priority.name,
        queue_position=processor.queues[item.priority].qsize(),
        created_at=item.created_at.isoformat()
    )


@app.post("/api/v2/batch/submit/sync", response_model=BatchResponse, tags=["배치 처리"])
async def submit_batch_sync(request: BatchRequest, timeout: float = Query(30.0)):
    """동기 배치 요청 (결과까지 대기)"""
    processor = await get_processor()

    request_id = await processor.submit(
        message=request.message,
        session_id=request.session_id,
        priority=request.priority,
        metadata=request.metadata
    )

    try:
        item = await processor.get_result(request_id, wait=True, timeout=timeout)
    except TimeoutError:
        raise HTTPException(status_code=504, detail="Request timed out")

    return BatchResponse(
        request_id=request_id,
        status=item.status.value,
        response=item.result,
        error=item.error,
        priority=item.priority.name,
        processing_time_ms=(
            (item.completed_at - item.created_at).total_seconds() * 1000
            if item.completed_at else None
        ),
        created_at=item.created_at.isoformat(),
        completed_at=item.completed_at.isoformat() if item.completed_at else None
    )


@app.post("/api/v2/batch/bulk", tags=["배치 처리"])
async def submit_bulk(request: BulkBatchRequest):
    """대량 배치 요청"""
    processor = await get_processor()
    results = []

    for req in request.requests:
        try:
            request_id = await processor.submit(
                message=req.message,
                session_id=req.session_id,
                priority=req.priority,
                metadata=req.metadata
            )
            results.append({
                "request_id": request_id,
                "status": "queued"
            })
        except Exception as e:
            results.append({
                "error": str(e),
                "status": "failed"
            })
            if request.fail_fast:
                break

    return {
        "total": len(request.requests),
        "submitted": sum(1 for r in results if r["status"] == "queued"),
        "results": results
    }


@app.get("/api/v2/batch/status/{request_id}", response_model=BatchResponse, tags=["조회"])
async def get_status(request_id: str):
    """요청 상태 조회"""
    processor = await get_processor()

    try:
        item = await processor.get_result(request_id, wait=False)
    except KeyError:
        raise HTTPException(status_code=404, detail="Request not found")

    return BatchResponse(
        request_id=request_id,
        status=item.status.value,
        response=item.result,
        error=item.error,
        priority=item.priority.name,
        processing_time_ms=(
            (item.completed_at - item.created_at).total_seconds() * 1000
            if item.completed_at else None
        ),
        created_at=item.created_at.isoformat(),
        completed_at=item.completed_at.isoformat() if item.completed_at else None
    )


@app.get("/api/v2/batch/result/{request_id}", tags=["조회"])
async def get_result(request_id: str, wait: bool = Query(False), timeout: float = Query(30.0)):
    """요청 결과 조회 (대기 옵션)"""
    processor = await get_processor()

    try:
        item = await processor.get_result(request_id, wait=wait, timeout=timeout)
    except KeyError:
        raise HTTPException(status_code=404, detail="Request not found")
    except TimeoutError:
        raise HTTPException(status_code=504, detail="Request timed out")

    if item.status == BatchStatus.FAILED:
        raise HTTPException(status_code=500, detail=item.error)

    return {
        "request_id": request_id,
        "status": item.status.value,
        "result": item.result,
        "processing_time_ms": (
            (item.completed_at - item.created_at).total_seconds() * 1000
            if item.completed_at else None
        )
    }


@app.delete("/api/v2/batch/{request_id}", tags=["관리"])
async def cancel_request(request_id: str):
    """요청 취소"""
    processor = await get_processor()

    success = await processor.cancel(request_id)

    if not success:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel: request not found or already processing"
        )

    return {"request_id": request_id, "status": "cancelled"}


@app.get("/api/v2/batch/stats", response_model=BatchStats, tags=["모니터링"])
async def get_stats():
    """배치 통계"""
    processor = await get_processor()
    return processor.get_stats()


@app.get("/api/v2/batch/health", tags=["모니터링"])
async def health_check():
    """헬스 체크"""
    processor = await get_processor()
    stats = processor.get_stats()

    status = "healthy"
    if stats["queue_depth"] > 100:
        status = "degraded"
    if stats["failed_requests"] > stats["completed_requests"] * 0.1:
        status = "unhealthy"

    return {
        "status": status,
        "queue_depth": stats["queue_depth"],
        "success_rate": (
            stats["completed_requests"] / max(stats["total_requests"], 1) * 100
        ),
        "avg_latency_ms": stats["average_latency_ms"]
    }


# ============================================================================
# 실행
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
