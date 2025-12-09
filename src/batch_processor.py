"""
배치 처리 모듈 (Batch Processing Module)
다중 사용자 요청을 효율적으로 처리하기 위한 적응형 배치 시스템

기능:
- 적응형 배치 크기 조절
- 우선순위 기반 큐 관리
- 실시간 / 비실시간 요청 분리
- 위기 상담 우선 처리
- 배치 통계 및 모니터링
"""

import logging
import asyncio
import time
import uuid
from typing import Optional, Dict, Any, List, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
import threading
import queue
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Data Classes
# =============================================================================

class RequestPriority(Enum):
    """요청 우선순위"""
    CRISIS = 0      # 위기 상담 - 즉시 처리
    REALTIME = 1    # 실시간 음성 - 최소 배치
    PREMIUM = 2     # 프리미엄 사용자 - 소규모 배치
    STANDARD = 3    # 일반 사용자 - 일반 배치
    BACKGROUND = 4  # 백그라운드 작업 - 최대 배치


class BatchStrategy(Enum):
    """배치 전략"""
    DISABLED = "disabled"      # 배치 비활성화 (단일 처리)
    FIXED = "fixed"            # 고정 배치 크기
    ADAPTIVE = "adaptive"      # 적응형 배치
    PRIORITY = "priority"      # 우선순위 기반


@dataclass
class BatchRequest:
    """배치 요청"""
    request_id: str
    data: Any  # 입력 데이터 (텍스트, 오디오 등)
    priority: RequestPriority = RequestPriority.STANDARD
    session_id: Optional[str] = None
    request_type: str = "chat"  # chat, voice, stt, tts
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 결과 저장용
    result: Optional[Any] = None
    error: Optional[str] = None
    completed: bool = False
    completed_at: Optional[datetime] = None

    # 비동기 이벤트
    _event: asyncio.Event = field(default_factory=asyncio.Event, repr=False)

    def mark_completed(self, result: Any = None, error: str = None):
        """완료 표시"""
        self.result = result
        self.error = error
        self.completed = True
        self.completed_at = datetime.now()
        self._event.set()

    async def wait_for_result(self, timeout: float = 30.0) -> Any:
        """결과 대기"""
        try:
            await asyncio.wait_for(self._event.wait(), timeout=timeout)
            if self.error:
                raise Exception(self.error)
            return self.result
        except asyncio.TimeoutError:
            raise TimeoutError(f"Request {self.request_id} timed out")


@dataclass
class Batch:
    """배치"""
    batch_id: str
    requests: List[BatchRequest]
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @property
    def size(self) -> int:
        return len(self.requests)

    @property
    def priority(self) -> RequestPriority:
        """배치의 최고 우선순위"""
        if not self.requests:
            return RequestPriority.STANDARD
        return min(r.priority for r in self.requests)

    @property
    def processing_time(self) -> Optional[float]:
        """처리 시간 (초)"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


@dataclass
class BatchConfig:
    """배치 설정"""
    strategy: BatchStrategy = BatchStrategy.ADAPTIVE
    min_batch_size: int = 1
    max_batch_size: int = 8
    max_wait_time_ms: int = 500  # 최대 대기 시간 (ms)

    # 우선순위별 최대 배치 크기
    priority_max_batch: Dict[RequestPriority, int] = field(default_factory=lambda: {
        RequestPriority.CRISIS: 1,
        RequestPriority.REALTIME: 2,
        RequestPriority.PREMIUM: 4,
        RequestPriority.STANDARD: 8,
        RequestPriority.BACKGROUND: 16
    })

    # 우선순위별 최대 대기 시간 (ms)
    priority_max_wait: Dict[RequestPriority, int] = field(default_factory=lambda: {
        RequestPriority.CRISIS: 0,
        RequestPriority.REALTIME: 100,
        RequestPriority.PREMIUM: 300,
        RequestPriority.STANDARD: 500,
        RequestPriority.BACKGROUND: 2000
    })


@dataclass
class BatchStats:
    """배치 통계"""
    total_requests: int = 0
    total_batches: int = 0
    total_processing_time: float = 0.0
    avg_batch_size: float = 0.0
    avg_wait_time_ms: float = 0.0
    avg_processing_time_ms: float = 0.0
    requests_per_second: float = 0.0

    # 우선순위별 통계
    priority_counts: Dict[RequestPriority, int] = field(default_factory=lambda: defaultdict(int))

    def update(self, batch: Batch):
        """통계 업데이트"""
        self.total_batches += 1
        self.total_requests += batch.size

        if batch.processing_time:
            self.total_processing_time += batch.processing_time

        # 평균 계산
        if self.total_batches > 0:
            self.avg_batch_size = self.total_requests / self.total_batches
            if self.total_processing_time > 0:
                self.avg_processing_time_ms = (self.total_processing_time / self.total_batches) * 1000
                self.requests_per_second = self.total_requests / self.total_processing_time

        # 우선순위별 카운트
        for req in batch.requests:
            self.priority_counts[req.priority] += 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_requests": self.total_requests,
            "total_batches": self.total_batches,
            "avg_batch_size": round(self.avg_batch_size, 2),
            "avg_processing_time_ms": round(self.avg_processing_time_ms, 2),
            "requests_per_second": round(self.requests_per_second, 2),
            "priority_distribution": {p.name: c for p, c in self.priority_counts.items()}
        }


# =============================================================================
# Priority Queue
# =============================================================================

class PriorityRequestQueue:
    """우선순위 기반 요청 큐"""

    def __init__(self):
        self._queues: Dict[RequestPriority, asyncio.Queue] = {
            priority: asyncio.Queue() for priority in RequestPriority
        }
        self._lock = asyncio.Lock()
        self._total_size = 0

    async def put(self, request: BatchRequest):
        """요청 추가"""
        await self._queues[request.priority].put(request)
        self._total_size += 1

    async def get(self, timeout: float = 0.1) -> Optional[BatchRequest]:
        """우선순위 순으로 요청 가져오기"""
        for priority in RequestPriority:
            queue = self._queues[priority]
            if not queue.empty():
                try:
                    request = queue.get_nowait()
                    self._total_size -= 1
                    return request
                except asyncio.QueueEmpty:
                    continue
        return None

    async def get_batch(
        self,
        max_size: int,
        max_wait_ms: int,
        priority_limits: Dict[RequestPriority, int]
    ) -> List[BatchRequest]:
        """배치 가져오기"""
        batch = []
        start_time = time.time()
        max_wait_sec = max_wait_ms / 1000.0

        while len(batch) < max_size:
            # 타임아웃 체크
            elapsed = time.time() - start_time
            if elapsed >= max_wait_sec and len(batch) > 0:
                break

            # 우선순위 순으로 요청 수집
            request = await self.get(timeout=0.05)
            if request:
                # 우선순위별 배치 크기 제한 확인
                priority_count = sum(1 for r in batch if r.priority == request.priority)
                if priority_count < priority_limits.get(request.priority, max_size):
                    batch.append(request)
                else:
                    # 다시 큐에 넣기
                    await self.put(request)
            else:
                # 큐가 비어있으면 잠시 대기
                if len(batch) > 0:
                    await asyncio.sleep(0.01)
                else:
                    await asyncio.sleep(0.05)

            # 위기 상담 요청이 있으면 즉시 반환
            if any(r.priority == RequestPriority.CRISIS for r in batch):
                break

        return batch

    def size(self) -> int:
        return self._total_size

    def size_by_priority(self) -> Dict[RequestPriority, int]:
        return {p: q.qsize() for p, q in self._queues.items()}


# =============================================================================
# Batch Processor
# =============================================================================

class BatchInferenceEngine(ABC):
    """배치 추론 엔진 인터페이스"""

    @abstractmethod
    async def process_batch(self, requests: List[BatchRequest]) -> List[Any]:
        """배치 처리"""
        pass


class LLMBatchEngine(BatchInferenceEngine):
    """LLM 배치 추론 엔진"""

    def __init__(self, model=None, tokenizer=None):
        self.model = model
        self.tokenizer = tokenizer
        self._initialized = False

    async def initialize(self):
        """모델 초기화"""
        if self._initialized:
            return

        if self.model is None:
            try:
                # 실제 모델 로드 (main.py에서 가져오기)
                from main import CounselingChatbot
                chatbot = CounselingChatbot()
                await asyncio.to_thread(chatbot.load_model)
                self.model = chatbot.model
                self.tokenizer = chatbot.tokenizer
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                raise

        self._initialized = True
        logger.info("LLMBatchEngine initialized")

    async def process_batch(self, requests: List[BatchRequest]) -> List[Any]:
        """배치 처리"""
        if not self._initialized:
            await self.initialize()

        # 입력 텍스트 수집
        texts = [req.data for req in requests]
        contexts = [req.metadata.get("context", []) for req in requests]

        # 배치 토큰화
        results = await self._batch_generate(texts, contexts)

        return results

    async def _batch_generate(
        self,
        texts: List[str],
        contexts: List[List[Dict]]
    ) -> List[str]:
        """배치 생성"""
        import torch

        # 프롬프트 생성
        prompts = []
        for text, context in zip(texts, contexts):
            prompt = self._build_prompt(text, context)
            prompts.append(prompt)

        # 배치 토큰화
        inputs = self.tokenizer(
            prompts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=2048
        ).to(self.model.device)

        # 배치 생성
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=300,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )

        # 디코딩
        results = []
        for i, output in enumerate(outputs):
            # 입력 부분 제외
            input_len = inputs.input_ids[i].shape[0]
            generated = output[input_len:]
            text = self.tokenizer.decode(generated, skip_special_tokens=True)
            results.append(text.strip())

        return results

    def _build_prompt(self, text: str, context: List[Dict]) -> str:
        """프롬프트 생성"""
        prompt = """당신은 따뜻하고 공감적인 한국어 심리상담사입니다.
내담자의 이야기를 경청하고, 감정을 이해하며, 적절한 상담 기법을 사용하세요.

"""
        # 대화 기록 추가
        for msg in context[-5:]:  # 최근 5개
            role = "내담자" if msg.get("role") == "user" else "상담사"
            prompt += f"{role}: {msg.get('content', '')}\n"

        prompt += f"내담자: {text}\n상담사: "
        return prompt


class BatchProcessor:
    """
    배치 프로세서

    다중 요청을 효율적으로 처리하는 메인 클래스
    """

    def __init__(
        self,
        config: Optional[BatchConfig] = None,
        engine: Optional[BatchInferenceEngine] = None
    ):
        self.config = config or BatchConfig()
        self.engine = engine

        self._queue = PriorityRequestQueue()
        self._stats = BatchStats()
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

        logger.info(f"BatchProcessor initialized with strategy={self.config.strategy.value}")

    async def start(self):
        """배치 처리 시작"""
        if self._running:
            return

        self._running = True

        # 엔진 초기화
        if self.engine is None:
            self.engine = LLMBatchEngine()
        await self.engine.initialize()

        # 워커 시작
        self._worker_task = asyncio.create_task(self._worker_loop())
        logger.info("BatchProcessor started")

    async def stop(self):
        """배치 처리 중지"""
        self._running = False

        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

        logger.info("BatchProcessor stopped")

    async def submit(
        self,
        data: Any,
        priority: RequestPriority = RequestPriority.STANDARD,
        session_id: Optional[str] = None,
        request_type: str = "chat",
        metadata: Optional[Dict] = None
    ) -> BatchRequest:
        """요청 제출"""
        request = BatchRequest(
            request_id=str(uuid.uuid4()),
            data=data,
            priority=priority,
            session_id=session_id,
            request_type=request_type,
            metadata=metadata or {}
        )

        await self._queue.put(request)
        logger.debug(f"Request submitted: {request.request_id}, priority={priority.name}")

        return request

    async def submit_and_wait(
        self,
        data: Any,
        priority: RequestPriority = RequestPriority.STANDARD,
        timeout: float = 30.0,
        **kwargs
    ) -> Any:
        """요청 제출 및 결과 대기"""
        request = await self.submit(data, priority, **kwargs)
        return await request.wait_for_result(timeout=timeout)

    async def _worker_loop(self):
        """워커 루프"""
        while self._running:
            try:
                # 배치 수집
                batch_requests = await self._collect_batch()

                if not batch_requests:
                    await asyncio.sleep(0.01)
                    continue

                # 배치 생성
                batch = Batch(
                    batch_id=str(uuid.uuid4()),
                    requests=batch_requests
                )

                # 배치 처리
                await self._process_batch(batch)

                # 통계 업데이트
                self._stats.update(batch)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                await asyncio.sleep(0.1)

    async def _collect_batch(self) -> List[BatchRequest]:
        """배치 수집"""
        if self.config.strategy == BatchStrategy.DISABLED:
            # 단일 처리
            request = await self._queue.get()
            return [request] if request else []

        elif self.config.strategy == BatchStrategy.FIXED:
            # 고정 크기 배치
            return await self._queue.get_batch(
                max_size=self.config.max_batch_size,
                max_wait_ms=self.config.max_wait_time_ms,
                priority_limits=self.config.priority_max_batch
            )

        elif self.config.strategy in [BatchStrategy.ADAPTIVE, BatchStrategy.PRIORITY]:
            # 적응형 / 우선순위 배치
            return await self._queue.get_batch(
                max_size=self.config.max_batch_size,
                max_wait_ms=self.config.max_wait_time_ms,
                priority_limits=self.config.priority_max_batch
            )

        return []

    async def _process_batch(self, batch: Batch):
        """배치 처리"""
        batch.started_at = datetime.now()

        try:
            # 엔진으로 배치 처리
            results = await self.engine.process_batch(batch.requests)

            # 결과 매핑
            for request, result in zip(batch.requests, results):
                request.mark_completed(result=result)

        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            # 모든 요청에 에러 표시
            for request in batch.requests:
                request.mark_completed(error=str(e))

        finally:
            batch.completed_at = datetime.now()
            logger.debug(
                f"Batch {batch.batch_id} completed: "
                f"size={batch.size}, time={batch.processing_time:.2f}s"
            )

    def get_stats(self) -> Dict[str, Any]:
        """통계 반환"""
        return {
            **self._stats.to_dict(),
            "queue_size": self._queue.size(),
            "queue_by_priority": {
                p.name: c for p, c in self._queue.size_by_priority().items()
            },
            "config": {
                "strategy": self.config.strategy.value,
                "max_batch_size": self.config.max_batch_size,
                "max_wait_time_ms": self.config.max_wait_time_ms
            }
        }

    def get_queue_status(self) -> Dict[str, Any]:
        """큐 상태"""
        return {
            "total": self._queue.size(),
            "by_priority": {
                p.name: c for p, c in self._queue.size_by_priority().items()
            }
        }


# =============================================================================
# Adaptive Batch Processor (고급)
# =============================================================================

class AdaptiveBatchProcessor(BatchProcessor):
    """
    적응형 배치 프로세서

    부하에 따라 동적으로 배치 크기 조절
    """

    def __init__(self, config: Optional[BatchConfig] = None, **kwargs):
        super().__init__(config, **kwargs)

        # 적응형 설정
        self._target_latency_ms = 2000  # 목표 지연 시간
        self._current_batch_size = self.config.min_batch_size
        self._latency_history: List[float] = []
        self._adjustment_interval = 10  # 배치 N개마다 조절

    async def _collect_batch(self) -> List[BatchRequest]:
        """적응형 배치 수집"""
        # 현재 최적 배치 크기 계산
        optimal_size = self._calculate_optimal_batch_size()

        return await self._queue.get_batch(
            max_size=optimal_size,
            max_wait_ms=self._calculate_optimal_wait_time(),
            priority_limits=self.config.priority_max_batch
        )

    def _calculate_optimal_batch_size(self) -> int:
        """최적 배치 크기 계산"""
        if len(self._latency_history) < 5:
            return self._current_batch_size

        # 평균 지연 시간 계산
        avg_latency = sum(self._latency_history[-10:]) / len(self._latency_history[-10:])

        # 목표 대비 조절
        if avg_latency > self._target_latency_ms * 1.2:
            # 지연이 높으면 배치 크기 감소
            self._current_batch_size = max(
                self.config.min_batch_size,
                self._current_batch_size - 1
            )
        elif avg_latency < self._target_latency_ms * 0.8:
            # 여유가 있으면 배치 크기 증가
            self._current_batch_size = min(
                self.config.max_batch_size,
                self._current_batch_size + 1
            )

        return self._current_batch_size

    def _calculate_optimal_wait_time(self) -> int:
        """최적 대기 시간 계산"""
        # 큐 크기에 따라 대기 시간 조절
        queue_size = self._queue.size()

        if queue_size > self.config.max_batch_size * 2:
            # 큐가 많으면 대기 시간 감소 (빨리 처리)
            return max(100, self.config.max_wait_time_ms // 2)
        elif queue_size < self.config.min_batch_size:
            # 큐가 적으면 대기 시간 증가 (배치 모으기)
            return min(1000, self.config.max_wait_time_ms * 2)

        return self.config.max_wait_time_ms

    async def _process_batch(self, batch: Batch):
        """배치 처리 (지연 시간 기록 추가)"""
        await super()._process_batch(batch)

        # 지연 시간 기록
        if batch.processing_time:
            latency_ms = batch.processing_time * 1000
            self._latency_history.append(latency_ms)

            # 히스토리 제한
            if len(self._latency_history) > 100:
                self._latency_history = self._latency_history[-100:]


# =============================================================================
# Crisis Detection Integration
# =============================================================================

def detect_crisis_priority(text: str) -> RequestPriority:
    """위기 상황 감지하여 우선순위 결정"""
    crisis_keywords = [
        "자살", "죽고 싶", "죽을", "목숨", "끝내고 싶",
        "자해", "손목", "약 먹", "뛰어내리",
        "살고 싶지 않", "사라지고 싶", "없어지고 싶"
    ]

    text_lower = text.lower()

    for keyword in crisis_keywords:
        if keyword in text_lower:
            logger.warning(f"Crisis detected in text: {keyword}")
            return RequestPriority.CRISIS

    return RequestPriority.STANDARD


# =============================================================================
# Global Instance
# =============================================================================

_batch_processor: Optional[BatchProcessor] = None


async def get_batch_processor(
    config: Optional[BatchConfig] = None,
    adaptive: bool = True
) -> BatchProcessor:
    """글로벌 배치 프로세서 인스턴스"""
    global _batch_processor

    if _batch_processor is None:
        if adaptive:
            _batch_processor = AdaptiveBatchProcessor(config)
        else:
            _batch_processor = BatchProcessor(config)
        await _batch_processor.start()

    return _batch_processor


async def submit_request(
    data: Any,
    priority: Optional[RequestPriority] = None,
    auto_detect_crisis: bool = True,
    **kwargs
) -> Any:
    """편의 함수: 요청 제출 및 결과 대기"""
    processor = await get_batch_processor()

    # 위기 상황 자동 감지
    if auto_detect_crisis and isinstance(data, str):
        detected_priority = detect_crisis_priority(data)
        priority = detected_priority if detected_priority == RequestPriority.CRISIS else priority

    priority = priority or RequestPriority.STANDARD

    return await processor.submit_and_wait(data, priority, **kwargs)
