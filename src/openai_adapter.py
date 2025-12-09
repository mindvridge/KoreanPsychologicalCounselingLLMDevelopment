"""
OpenAI API 어댑터 (ChatGPT API Adapter)
테스트 환경에서 로컬 LLM 대신 OpenAI API 사용

기능:
- GPT-4o / GPT-4o-mini 지원
- 로컬 LLM과 동일한 인터페이스
- 스트리밍 응답 지원
- 비용 추적
"""

import logging
import os
import asyncio
from typing import Optional, Dict, Any, List, Generator, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class OpenAIConfig:
    """OpenAI API 설정"""
    api_key: Optional[str] = None
    model: str = "gpt-4o-mini"  # gpt-4o, gpt-4o-mini, gpt-4-turbo
    temperature: float = 0.7
    max_tokens: int = 500
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0

    # 비용 추적
    track_cost: bool = True

    # 모델별 가격 (1K 토큰당 USD)
    pricing: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015}
    })


@dataclass
class UsageStats:
    """사용량 통계"""
    total_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    last_request_at: Optional[datetime] = None

    def update(self, input_tokens: int, output_tokens: int, model: str, pricing: dict):
        """통계 업데이트"""
        self.total_requests += 1
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.last_request_at = datetime.now()

        # 비용 계산
        if model in pricing:
            input_cost = (input_tokens / 1000) * pricing[model]["input"]
            output_cost = (output_tokens / 1000) * pricing[model]["output"]
            self.total_cost_usd += input_cost + output_cost

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_requests": self.total_requests,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "last_request_at": self.last_request_at.isoformat() if self.last_request_at else None
        }


# 한국어 심리상담 시스템 프롬프트
COUNSELOR_SYSTEM_PROMPT = """당신은 따뜻하고 공감적인 한국어 심리상담사 '마음이'입니다.

## 역할
- 내담자의 이야기를 경청하고 감정을 공감합니다
- 판단하지 않고 수용적인 태도를 유지합니다
- 적절한 상담 기법(경청, 반영, 명료화, 요약)을 사용합니다

## 상담 원칙
1. 공감적 경청: 내담자의 감정을 인정하고 반영합니다
2. 비판단적 태도: 어떤 상황에서도 판단하지 않습니다
3. 안전 우선: 위기 상황 시 전문 기관 연결을 안내합니다
4. 문화적 민감성: 한국 문화적 맥락을 이해하고 존중합니다

## 위기 대응
자살, 자해 관련 언급 시:
- 즉시 공감과 지지 표현
- 자살예방상담전화 1393
- 정신건강위기상담전화 1577-0199
- 전문 기관 연결 권유

## 응답 스타일
- 따뜻하고 부드러운 어조
- 짧고 명확한 문장
- 적절한 질문으로 대화 이끌기
- 한국어 존댓말 사용
"""


class LLMInterface(ABC):
    """LLM 인터페이스 (추상 클래스)"""

    @abstractmethod
    def generate_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        pass

    @abstractmethod
    async def generate_response_async(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        pass


class OpenAICounselor(LLMInterface):
    """
    OpenAI API 기반 상담사

    로컬 LLM과 동일한 인터페이스 제공
    """

    def __init__(self, config: Optional[OpenAIConfig] = None):
        self.config = config or OpenAIConfig()
        self.config.api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")

        if not self.config.api_key:
            raise ValueError("OPENAI_API_KEY 환경 변수를 설정하세요")

        self.client = None
        self.async_client = None
        self.stats = UsageStats()
        self.system_prompt = COUNSELOR_SYSTEM_PROMPT

        self._initialize_client()
        logger.info(f"OpenAICounselor initialized with model={self.config.model}")

    def _initialize_client(self):
        """클라이언트 초기화"""
        try:
            from openai import OpenAI, AsyncOpenAI

            self.client = OpenAI(api_key=self.config.api_key)
            self.async_client = AsyncOpenAI(api_key=self.config.api_key)

        except ImportError:
            raise ImportError("openai 패키지를 설치하세요: pip install openai")

    def generate_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """
        응답 생성 (동기)

        Args:
            user_message: 사용자 메시지
            conversation_history: 대화 기록

        Returns:
            상담사 응답
        """
        messages = self._build_messages(user_message, conversation_history)

        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                top_p=self.config.top_p,
                frequency_penalty=self.config.frequency_penalty,
                presence_penalty=self.config.presence_penalty
            )

            # 토큰 사용량 추적
            if self.config.track_cost and response.usage:
                self.stats.update(
                    input_tokens=response.usage.prompt_tokens,
                    output_tokens=response.usage.completion_tokens,
                    model=self.config.model,
                    pricing=self.config.pricing
                )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 말씀해 주세요."

    async def generate_response_async(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """응답 생성 (비동기)"""
        messages = self._build_messages(user_message, conversation_history)

        try:
            response = await self.async_client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                top_p=self.config.top_p
            )

            if self.config.track_cost and response.usage:
                self.stats.update(
                    input_tokens=response.usage.prompt_tokens,
                    output_tokens=response.usage.completion_tokens,
                    model=self.config.model,
                    pricing=self.config.pricing
                )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 말씀해 주세요."

    def generate_response_stream(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> Generator[str, None, None]:
        """스트리밍 응답 생성"""
        messages = self._build_messages(user_message, conversation_history)

        try:
            stream = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                stream=True
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            yield "죄송합니다. 오류가 발생했습니다."

    async def generate_response_stream_async(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> AsyncGenerator[str, None]:
        """비동기 스트리밍 응답 생성"""
        messages = self._build_messages(user_message, conversation_history)

        try:
            stream = await self.async_client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                stream=True
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            yield "죄송합니다. 오류가 발생했습니다."

    def _build_messages(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> List[Dict[str, str]]:
        """메시지 구성"""
        messages = [{"role": "system", "content": self.system_prompt}]

        # 대화 기록 추가 (최근 10개)
        if conversation_history:
            for msg in conversation_history[-10:]:
                role = "user" if msg.get("role") == "user" else "assistant"
                messages.append({"role": role, "content": msg.get("content", "")})

        # 현재 메시지
        messages.append({"role": "user", "content": user_message})

        return messages

    def set_system_prompt(self, prompt: str):
        """시스템 프롬프트 설정"""
        self.system_prompt = prompt

    def get_usage_stats(self) -> Dict[str, Any]:
        """사용량 통계 반환"""
        return self.stats.to_dict()

    def reset_stats(self):
        """통계 초기화"""
        self.stats = UsageStats()


class MockLLM(LLMInterface):
    """
    테스트용 Mock LLM

    API 호출 없이 테스트 가능
    """

    def __init__(self):
        self.response_templates = [
            "말씀해 주셔서 감사합니다. {emotion}시군요. 더 자세히 이야기해 주실 수 있을까요?",
            "그런 감정을 느끼시는 건 자연스러운 거예요. 어떤 상황에서 그런 느낌이 드셨나요?",
            "힘드셨겠네요. 제가 여기서 들어드릴게요. 편하게 말씀해 주세요.",
            "공감이 됩니다. 그 상황에서 많이 {emotion}셨을 것 같아요."
        ]
        self.call_count = 0
        logger.info("MockLLM initialized (for testing)")

    def generate_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        self.call_count += 1
        emotion = self._detect_emotion(user_message)
        template = self.response_templates[self.call_count % len(self.response_templates)]
        return template.format(emotion=emotion)

    async def generate_response_async(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        await asyncio.sleep(0.5)  # 시뮬레이션 지연
        return self.generate_response(user_message, conversation_history)

    def _detect_emotion(self, text: str) -> str:
        if any(word in text for word in ["슬프", "우울", "힘들"]):
            return "힘드"
        elif any(word in text for word in ["화나", "짜증", "열받"]):
            return "화나"
        elif any(word in text for word in ["불안", "걱정", "무서"]):
            return "불안하"
        else:
            return "그러"


# =============================================================================
# Factory Function
# =============================================================================

def get_llm(
    provider: str = "openai",
    **kwargs
) -> LLMInterface:
    """
    LLM 인스턴스 생성

    Args:
        provider: "openai", "local", "mock"
        **kwargs: 추가 설정

    Returns:
        LLMInterface 구현체
    """
    if provider == "openai":
        config = OpenAIConfig(**kwargs)
        return OpenAICounselor(config)

    elif provider == "mock":
        return MockLLM()

    elif provider == "local":
        # 로컬 LLM은 기존 main.py 사용
        try:
            from main import CounselingChatbot
            return CounselingChatbot()
        except ImportError:
            logger.warning("Local LLM not available, using mock")
            return MockLLM()

    else:
        raise ValueError(f"Unknown provider: {provider}")


# =============================================================================
# CLI Test
# =============================================================================

def main():
    """CLI 테스트"""
    import sys

    print("=" * 50)
    print("  한국어 심리상담 LLM 테스트 (OpenAI API)")
    print("=" * 50)

    # API 키 확인
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  OPENAI_API_KEY 환경 변수를 설정하세요")
        print("   export OPENAI_API_KEY=sk-...")
        sys.exit(1)

    # 모델 선택
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    print(f"\n모델: {model}")
    print("종료하려면 'quit' 또는 'q' 입력\n")

    # 상담사 초기화
    config = OpenAIConfig(model=model)
    counselor = OpenAICounselor(config)
    history = []

    while True:
        try:
            user_input = input("\n내담자: ").strip()

            if user_input.lower() in ["quit", "q", "종료"]:
                break

            if not user_input:
                continue

            # 응답 생성
            response = counselor.generate_response(user_input, history)
            print(f"\n상담사: {response}")

            # 대화 기록 저장
            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": response})

        except KeyboardInterrupt:
            break

    # 통계 출력
    stats = counselor.get_usage_stats()
    print("\n" + "=" * 50)
    print("세션 통계:")
    print(f"  총 요청: {stats['total_requests']}")
    print(f"  입력 토큰: {stats['total_input_tokens']}")
    print(f"  출력 토큰: {stats['total_output_tokens']}")
    print(f"  예상 비용: ${stats['total_cost_usd']:.4f}")
    print("=" * 50)


if __name__ == "__main__":
    main()
