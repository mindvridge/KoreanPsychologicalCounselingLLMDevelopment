"""
한국형 심리상담 LLM 메인 클래스
Korean Mental Health Counseling LLM Main Class

SOLAR-Ko-10.7B 모델을 기반으로 한 심리상담 AI 시스템
"""

import os
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    GenerationConfig
)

from .emotion_analyzer import EmotionAnalyzer
from .safety_system import CrisisDetectionSystem
from .prompts import PromptTemplate
from .utils import (
    load_yaml,
    truncate_conversation_history,
    clean_text,
    check_gpu_availability,
    estimate_model_memory
)

logger = logging.getLogger(__name__)


class KoreanMentalHealthLLM:
    """
    한국형 심리상담 LLM 클래스

    beomi/OPEN-SOLAR-KO-10.7B 모델을 4비트 양자화로 로드하여
    한국어 심리상담 서비스를 제공합니다.

    주요 기능:
    - 공감적 대화 생성
    - 감정 분석
    - 위기 상황 감지 및 개입
    - 대화 이력 관리
    - 한국 문화 맥락 고려
    """

    def __init__(
        self,
        model_name: str = "beomi/OPEN-SOLAR-KO-10.7B",
        config_path: Optional[str] = None,
        load_in_4bit: bool = True,
        device: str = "auto"
    ):
        """
        초기화

        Args:
            model_name: 사용할 모델 이름
            config_path: 설정 파일 경로
            load_in_4bit: 4비트 양자화 사용 여부
            device: 사용할 디바이스 ("auto", "cuda", "cpu")
        """
        logger.info("Initializing Korean Mental Health LLM...")

        # 설정 로드
        self.config = self._load_config(config_path)

        # 모델 설정
        self.model_name = model_name
        self.load_in_4bit = load_in_4bit
        self.device = device

        # GPU 확인
        self.gpu_info = check_gpu_availability()
        logger.info(f"GPU Info: {self.gpu_info}")

        # 메모리 추정
        estimated_memory = estimate_model_memory(
            model_name,
            4 if load_in_4bit else 16
        )
        logger.info(f"Estimated model memory: {estimated_memory} GB")

        # 모델 및 토크나이저 초기화
        self.model = None
        self.tokenizer = None
        self._load_model()

        # 프롬프트 템플릿
        self.prompt_template = PromptTemplate(
            persona_name=self.config.get("persona", {}).get("name", "마음이")
        )

        # 감정 분석기
        self.emotion_analyzer = EmotionAnalyzer()

        # 위기 감지 시스템
        crisis_keywords_file = self.config.get("data_paths", {}).get(
            "crisis_keywords",
            "./data/crisis_keywords.json"
        )
        self.safety_system = CrisisDetectionSystem(crisis_keywords_file)

        # 대화 이력
        self.conversation_history: List[Dict[str, str]] = []
        self.max_turns = self.config.get("conversation", {}).get("max_turns", 10)

        # 생성 설정
        self.generation_config = self._create_generation_config()

        logger.info("Korean Mental Health LLM initialized successfully")

    def _load_config(self, config_path: Optional[str]) -> Dict:
        """
        설정 파일 로드

        Args:
            config_path: 설정 파일 경로

        Returns:
            Dict: 설정 딕셔너리
        """
        if config_path and os.path.exists(config_path):
            return load_yaml(config_path)

        default_config_path = "./configs/config.yaml"
        if os.path.exists(default_config_path):
            return load_yaml(default_config_path)

        logger.warning("Config file not found, using default settings")
        return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """
        기본 설정 반환

        Returns:
            Dict: 기본 설정
        """
        return {
            "model": {
                "name": "beomi/OPEN-SOLAR-KO-10.7B",
                "quantization": {"enabled": True, "bits": 4}
            },
            "generation": {
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 50,
                "max_new_tokens": 512,
                "repetition_penalty": 1.1
            },
            "conversation": {"max_turns": 10},
            "persona": {"name": "마음이"},
            "safety": {"enable_crisis_detection": True}
        }

    def _load_model(self):
        """모델 및 토크나이저 로드"""
        try:
            logger.info(f"Loading model: {self.model_name}")

            # 토크나이저 로드
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )

            # 패딩 토큰 설정
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            # 양자화 설정
            quantization_config = None
            if self.load_in_4bit:
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
                logger.info("Using 4-bit quantization")

            # 모델 로드
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                quantization_config=quantization_config,
                device_map=self.device if self.device != "auto" else "auto",
                trust_remote_code=True,
                torch_dtype=torch.float16 if not self.load_in_4bit else None
            )

            logger.info("Model loaded successfully")

        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise

    def _create_generation_config(self) -> GenerationConfig:
        """
        생성 설정 생성

        Returns:
            GenerationConfig: 생성 설정
        """
        gen_config = self.config.get("generation", {})

        return GenerationConfig(
            temperature=gen_config.get("temperature", 0.7),
            top_p=gen_config.get("top_p", 0.9),
            top_k=gen_config.get("top_k", 50),
            max_new_tokens=gen_config.get("max_new_tokens", 512),
            repetition_penalty=gen_config.get("repetition_penalty", 1.1),
            do_sample=gen_config.get("do_sample", True),
            pad_token_id=self.tokenizer.pad_token_id,
            eos_token_id=self.tokenizer.eos_token_id
        )

    def generate_response(
        self,
        user_input: str,
        skip_safety_check: bool = False
    ) -> Dict[str, any]:
        """
        사용자 입력에 대한 응답 생성

        Args:
            user_input: 사용자 입력 텍스트
            skip_safety_check: 안전 체크 건너뛰기 (테스트용)

        Returns:
            Dict: 응답 및 메타데이터
                - response: 생성된 응답
                - emotion: 감지된 감정
                - crisis: 위기 감지 결과
                - intervention_message: 개입 메시지 (위기 시)
        """
        try:
            logger.info(f"Generating response for input: {user_input[:50]}...")

            # 1. 감정 분석
            emotion_result = self.emotion_analyzer.analyze(user_input)
            logger.info(
                f"Emotion detected: {emotion_result['primary_emotion']} "
                f"(intensity: {emotion_result['intensity']:.2f})"
            )

            # 2. 위기 감지
            crisis_result = None
            intervention_message = None

            if not skip_safety_check:
                crisis_result = self.safety_system.detect_crisis(user_input)

                if crisis_result["is_crisis"]:
                    # 위기 상황 - 즉시 개입
                    logger.warning(
                        f"Crisis detected: {crisis_result['crisis_type']} "
                        f"(severity: {crisis_result['severity']:.2f})"
                    )

                    intervention_message = self.safety_system.get_intervention_message(
                        crisis_result
                    )

                    # 위기 상황에서는 개입 메시지를 우선 반환
                    return {
                        "response": intervention_message,
                        "emotion": emotion_result,
                        "crisis": crisis_result,
                        "intervention_message": intervention_message,
                        "is_intervention": True
                    }

            # 3. 시스템 프롬프트 구성
            context = {
                "emotion": emotion_result["primary_emotion"],
                "crisis_level": crisis_result["severity"] if crisis_result else 0
            }
            system_prompt = self.prompt_template.get_system_prompt(context)

            # 4. 대화 이력에 추가
            self.conversation_history.append({
                "role": "user",
                "content": user_input
            })

            # 5. 대화 이력 관리 (최대 턴 수 제한)
            self.conversation_history = truncate_conversation_history(
                self.conversation_history,
                self.max_turns
            )

            # 6. 프롬프트 구성
            prompt = self._build_prompt(system_prompt, user_input)

            # 7. 모델 추론
            response_text = self._generate(prompt)

            # 8. 응답 정제
            response_text = clean_text(response_text)

            # 9. 대화 이력에 응답 추가
            self.conversation_history.append({
                "role": "assistant",
                "content": response_text
            })

            logger.info(f"Response generated: {response_text[:100]}...")

            return {
                "response": response_text,
                "emotion": emotion_result,
                "crisis": crisis_result,
                "intervention_message": intervention_message,
                "is_intervention": False
            }

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "response": "죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해주세요.",
                "emotion": None,
                "crisis": None,
                "intervention_message": None,
                "is_intervention": False,
                "error": str(e)
            }

    def _build_prompt(self, system_prompt: str, user_input: str) -> str:
        """
        프롬프트 구성

        Args:
            system_prompt: 시스템 프롬프트
            user_input: 사용자 입력

        Returns:
            str: 구성된 프롬프트
        """
        # SOLAR 모델의 프롬프트 형식
        # <s>[INST] <<SYS>>시스템 프롬프트<</SYS>>사용자 입력[/INST]

        prompt = f"<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n"

        # 이전 대화 이력 추가 (마지막 제외)
        for turn in self.conversation_history[:-1]:
            if turn["role"] == "user":
                prompt += f"{turn['content']} [/INST] "
            elif turn["role"] == "assistant":
                prompt += f"{turn['content']} </s><s>[INST] "

        # 현재 사용자 입력
        prompt += f"{user_input} [/INST]"

        return prompt

    def _generate(self, prompt: str) -> str:
        """
        모델을 사용하여 텍스트 생성

        Args:
            prompt: 입력 프롬프트

        Returns:
            str: 생성된 텍스트
        """
        # 토크나이징
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=2048
        )

        # GPU로 이동
        if self.gpu_info["available"]:
            inputs = {k: v.to("cuda") for k, v in inputs.items()}

        # 생성
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                generation_config=self.generation_config
            )

        # 디코딩
        generated_text = self.tokenizer.decode(
            outputs[0],
            skip_special_tokens=True
        )

        # 프롬프트 부분 제거
        # [/INST] 이후의 텍스트만 추출
        if "[/INST]" in generated_text:
            parts = generated_text.split("[/INST]")
            response = parts[-1].strip()
        else:
            response = generated_text.strip()

        return response

    def reset_conversation(self):
        """대화 이력 초기화"""
        self.conversation_history = []
        logger.info("Conversation history reset")

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """
        대화 이력 반환

        Returns:
            List[Dict]: 대화 이력
        """
        return self.conversation_history.copy()

    def summarize_conversation(self) -> str:
        """
        대화 요약

        Returns:
            str: 대화 요약
        """
        if not self.conversation_history:
            return "대화 이력이 없습니다."

        summary = "대화 요약:\n\n"

        for i, turn in enumerate(self.conversation_history, 1):
            role = "내담자" if turn["role"] == "user" else "마음이"
            content = turn["content"][:100]  # 처음 100자만
            summary += f"{i}. {role}: {content}...\n"

        return summary

    def save_conversation(self, filepath: str) -> bool:
        """
        대화 저장

        Args:
            filepath: 저장할 파일 경로

        Returns:
            bool: 성공 여부
        """
        try:
            import json

            data = {
                "timestamp": datetime.now().isoformat(),
                "conversation": self.conversation_history
            }

            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"Conversation saved to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
            return False

    def get_greeting(self) -> str:
        """
        인사말 반환

        Returns:
            str: 인사말
        """
        return self.prompt_template.get_greeting_prompt()

    def get_closing(self) -> str:
        """
        종료 인사 반환

        Returns:
            str: 종료 인사
        """
        return self.prompt_template.get_closing_prompt()


def test_llm():
    """LLM 테스트"""
    logger.info("=== Testing Korean Mental Health LLM ===")

    # LLM 초기화
    llm = KoreanMentalHealthLLM()

    # 인사말
    print("\n" + llm.get_greeting())
    print("\n" + "="*70)

    # 테스트 케이스
    test_inputs = [
        "요즘 너무 불안하고 걱정이 많아요.",
        "직장에서 스트레스가 심해요. 상사와의 관계도 힘들고요.",
        "우울한 기분이 계속되고 아무것도 하기 싫어요."
    ]

    for user_input in test_inputs:
        print(f"\n[사용자]: {user_input}")
        print("-" * 70)

        result = llm.generate_response(user_input)

        print(f"[감정 분석]: {result['emotion']['primary_emotion']} "
              f"(강도: {result['emotion']['intensity']:.2f})")

        if result['crisis'] and result['crisis']['is_crisis']:
            print(f"[위기 감지]: {result['crisis']['crisis_type']} "
                  f"(심각도: {result['crisis']['severity']:.2f})")

        print(f"\n[마음이]: {result['response']}")
        print("\n" + "="*70)

    # 종료 인사
    print("\n" + llm.get_closing())


if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    test_llm()
