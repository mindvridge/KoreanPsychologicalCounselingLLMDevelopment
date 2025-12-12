"""
향상된 한국형 심리상담 LLM 메인 클래스
Enhanced Korean Mental Health Counseling LLM Main Class

신규 통합 모듈:
- 대화 상태 관리 (ConversationStateManager)
- 응답 검증 (ResponseValidator)
- 향상된 RAG (EnhancedRAGSystem)
- LLM 평가 시스템 (CounselingLLMEvaluator)
- A/B 테스트 (ExperimentManager)
- 모니터링 대시보드 (EnhancedMonitoringDashboard)
"""

import os
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    GenerationConfig
)

# 기존 모듈
from .emotion_analyzer import EmotionAnalyzer
from .safety_system import CrisisDetectionSystem
from .utils import (
    load_yaml,
    truncate_conversation_history,
    clean_text,
    check_gpu_availability,
    estimate_model_memory
)

# 신규 통합 모듈
from .prompts import PromptTemplate, ConversationPhase
from .conversation_state import ConversationStateManager, ConversationState
from .response_validator import ResponseValidator, ValidationResult
from .enhanced_rag import EnhancedRAGSystem
from .evaluation import CounselingLLMEvaluator, evaluate_response
from .experiments import ExperimentManager, get_experiment_manager
from .monitoring_dashboard import get_dashboard, EnhancedMonitoringDashboard

logger = logging.getLogger(__name__)


# =============================================================================
# 응답 결과 데이터 클래스
# =============================================================================

@dataclass
class EnhancedResponseResult:
    """향상된 응답 결과"""
    response: str
    emotion: Dict[str, Any]
    crisis: Optional[Dict[str, Any]]

    # 신규 메트릭
    validation: Optional[ValidationResult] = None
    evaluation_scores: Optional[Dict[str, float]] = None
    conversation_state: Optional[ConversationState] = None

    # RAG 정보
    rag_context_used: bool = False
    rag_sources: List[str] = None

    # 메타정보
    response_time_ms: float = 0.0
    is_intervention: bool = False
    intervention_message: Optional[str] = None
    experiment_variant: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        result = {
            "response": self.response,
            "emotion": self.emotion,
            "crisis": self.crisis,
            "validation": asdict(self.validation) if self.validation else None,
            "evaluation_scores": self.evaluation_scores,
            "rag_context_used": self.rag_context_used,
            "rag_sources": self.rag_sources,
            "response_time_ms": self.response_time_ms,
            "is_intervention": self.is_intervention,
            "intervention_message": self.intervention_message,
            "experiment_variant": self.experiment_variant,
            "error": self.error
        }
        return result


# =============================================================================
# 향상된 LLM 클래스
# =============================================================================

class EnhancedKoreanMentalHealthLLM:
    """
    향상된 한국형 심리상담 LLM

    기존 기능:
    - 공감적 대화 생성
    - 감정 분석
    - 위기 상황 감지 및 개입
    - 대화 이력 관리

    신규 기능:
    - 대화 상태 추적 및 단계별 대응
    - 응답 품질 검증
    - RAG 기반 지식 증강
    - 실시간 품질 평가
    - A/B 테스트 지원
    - 모니터링 대시보드 연동
    """

    def __init__(
        self,
        model_name: str = "beomi/OPEN-SOLAR-KO-10.7B",
        config_path: Optional[str] = None,
        load_in_4bit: bool = True,
        device: str = "auto",
        enable_rag: bool = True,
        enable_validation: bool = True,
        enable_evaluation: bool = True,
        enable_experiments: bool = True,
        enable_monitoring: bool = True
    ):
        """
        초기화

        Args:
            model_name: 사용할 모델 이름
            config_path: 설정 파일 경로
            load_in_4bit: 4비트 양자화 사용 여부
            device: 사용할 디바이스
            enable_rag: RAG 시스템 활성화
            enable_validation: 응답 검증 활성화
            enable_evaluation: 평가 시스템 활성화
            enable_experiments: A/B 테스트 활성화
            enable_monitoring: 모니터링 활성화
        """
        logger.info("Initializing Enhanced Korean Mental Health LLM...")

        # 설정
        self.config = self._load_config(config_path)
        self.model_name = model_name
        self.load_in_4bit = load_in_4bit
        self.device = device

        # 기능 플래그
        self.enable_rag = enable_rag
        self.enable_validation = enable_validation
        self.enable_evaluation = enable_evaluation
        self.enable_experiments = enable_experiments
        self.enable_monitoring = enable_monitoring

        # GPU 확인
        self.gpu_info = check_gpu_availability()
        logger.info(f"GPU Info: {self.gpu_info}")

        # 모델 로드
        self.model = None
        self.tokenizer = None
        self._load_model()

        # 기존 컴포넌트
        self.emotion_analyzer = EmotionAnalyzer()
        self.safety_system = CrisisDetectionSystem(
            self.config.get("data_paths", {}).get(
                "crisis_keywords", "./data/crisis_keywords.json"
            )
        )

        # 대화 관리
        self.conversation_history: List[Dict[str, str]] = []
        self.max_turns = self.config.get("conversation", {}).get("max_turns", 10)
        self.generation_config = self._create_generation_config()

        # 신규 컴포넌트 초기화
        self._init_enhanced_components()

        # 세션 정보
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.user_id: Optional[str] = None

        logger.info("Enhanced Korean Mental Health LLM initialized successfully")

    def _load_config(self, config_path: Optional[str]) -> Dict:
        """설정 파일 로드"""
        if config_path and os.path.exists(config_path):
            return load_yaml(config_path)

        default_config_path = "./configs/config.yaml"
        if os.path.exists(default_config_path):
            return load_yaml(default_config_path)

        return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """기본 설정"""
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

            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )

            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            quantization_config = None
            if self.load_in_4bit:
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )

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
        """생성 설정"""
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

    def _init_enhanced_components(self):
        """신규 컴포넌트 초기화"""

        # 프롬프트 템플릿
        persona_name = self.config.get("persona", {}).get("name", "마음이")
        self.prompt_template = PromptTemplate(persona_name)

        # 대화 상태 관리자
        self.state_manager = ConversationStateManager()

        # 응답 검증기
        self.validator = ResponseValidator() if self.enable_validation else None

        # RAG 시스템
        self.rag_system = None
        if self.enable_rag:
            try:
                from .rag_system import MentalHealthRAG
                base_rag = MentalHealthRAG()
                self.rag_system = EnhancedRAGSystem(base_rag)
                logger.info("RAG system initialized")
            except Exception as e:
                logger.warning(f"RAG system not available: {e}")
                self.rag_system = None

        # 평가 시스템
        self.evaluator = CounselingLLMEvaluator() if self.enable_evaluation else None

        # 실험 관리자
        self.experiment_manager = get_experiment_manager() if self.enable_experiments else None

        # 모니터링 대시보드
        self.dashboard = get_dashboard() if self.enable_monitoring else None

        logger.info("Enhanced components initialized")

    def set_user(self, user_id: str):
        """사용자 설정 (A/B 테스트용)"""
        self.user_id = user_id
        self.session_id = f"session_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def generate_response(
        self,
        user_input: str,
        skip_safety_check: bool = False,
        include_evaluation: bool = True
    ) -> EnhancedResponseResult:
        """
        향상된 응답 생성

        Args:
            user_input: 사용자 입력
            skip_safety_check: 안전 체크 건너뛰기
            include_evaluation: 평가 점수 포함 여부

        Returns:
            EnhancedResponseResult: 향상된 응답 결과
        """
        start_time = time.time()

        try:
            logger.info(f"Generating enhanced response for: {user_input[:50]}...")

            # 1. 감정 분석
            emotion_result = self.emotion_analyzer.analyze(user_input)

            # 2. 위기 감지
            crisis_result = None
            if not skip_safety_check:
                crisis_result = self.safety_system.detect_crisis(user_input)

                if crisis_result.get("is_crisis"):
                    intervention = self.safety_system.get_intervention_message(crisis_result)
                    response_time = (time.time() - start_time) * 1000

                    # 모니터링 기록
                    self._record_monitoring(
                        response_time=response_time,
                        crisis_detected=True,
                        crisis_level=crisis_result.get("severity", 0) * 5
                    )

                    return EnhancedResponseResult(
                        response=intervention,
                        emotion=emotion_result,
                        crisis=crisis_result,
                        response_time_ms=response_time,
                        is_intervention=True,
                        intervention_message=intervention
                    )

            # 3. 대화 상태 업데이트
            if self.state_manager:
                self.state_manager.update_state(
                    user_message=user_input,
                    emotion=emotion_result.get("primary_emotion", "neutral"),
                    emotion_intensity=emotion_result.get("intensity", 0.5),
                    crisis_detected=crisis_result.get("is_crisis", False) if crisis_result else False,
                    crisis_level=int(crisis_result.get("severity", 0) * 5) if crisis_result else 0
                )

            current_state = self.state_manager.get_state() if self.state_manager else None

            # 4. RAG 컨텍스트 검색
            rag_context = ""
            rag_sources = []
            if self.rag_system:
                try:
                    rag_context, query_expansion = self.rag_system.retrieve_and_augment(
                        user_message=user_input,
                        emotion=emotion_result.get("primary_emotion", "neutral"),
                        conversation_history=self.conversation_history,
                        crisis_detected=crisis_result.get("is_crisis", False) if crisis_result else False
                    )
                    # 소스 추출 (간략화)
                    if rag_context:
                        rag_sources = ["knowledge_base"]
                except Exception as e:
                    logger.warning(f"RAG retrieval failed: {e}")

            # 5. A/B 테스트 변형 확인
            experiment_variant = None
            if self.experiment_manager and self.user_id:
                # 활성 실험 확인
                for exp_id in self.experiment_manager.experiments:
                    variant = self.experiment_manager.assign_variant(exp_id, self.user_id)
                    if variant:
                        experiment_variant = variant.name
                        break

            # 6. 향상된 프롬프트 생성
            crisis_level = int(crisis_result.get("severity", 0) * 5) if crisis_result else 0
            prompt = self.prompt_template.get_enhanced_prompt(
                user_message=user_input,
                emotion_analysis={
                    "primary_emotion": emotion_result.get("primary_emotion", "neutral"),
                    "intensity": emotion_result.get("intensity", 5)
                },
                crisis_info={
                    "risk_score": crisis_level / 5.0  # 0-1 범위로 변환
                } if crisis_level > 0 else None,
                conversation_history=self.conversation_history[-6:],  # 최근 3턴
                rag_context=rag_context
            )

            # 7. 대화 이력 업데이트
            self.conversation_history.append({
                "role": "user",
                "content": user_input
            })
            self.conversation_history = truncate_conversation_history(
                self.conversation_history,
                self.max_turns
            )

            # 8. 응답 생성
            response_text = self._generate(prompt)
            response_text = clean_text(response_text)

            # 9. 응답 검증
            validation_result = None
            if self.validator:
                validation_context = {
                    "crisis_level": int(crisis_result.get("severity", 0) * 5) if crisis_result else 0,
                    "emotion": emotion_result.get("primary_emotion", "neutral"),
                    "conversation_history": self.conversation_history
                }
                validation_result = self.validator.validate(response_text, validation_context)

                # 검증 실패 시 재생성 시도
                if not validation_result.is_valid and validation_result.overall_score < 0.4:
                    logger.warning(f"Response validation failed, regenerating...")
                    # 프롬프트에 검증 피드백 추가
                    feedback_prompt = prompt + f"\n\n[검증 피드백: {', '.join(validation_result.issues)}]\n다시 응답해주세요:"
                    response_text = self._generate(feedback_prompt)
                    response_text = clean_text(response_text)
                    validation_result = self.validator.validate(response_text, validation_context)

            # 10. 응답 평가
            evaluation_scores = None
            if self.evaluator and include_evaluation:
                eval_result = self.evaluator.evaluate(response_text, {
                    "user_message": user_input,
                    "emotion": emotion_result.get("primary_emotion"),
                    "crisis_level": int(crisis_result.get("severity", 0) * 5) if crisis_result else 0,
                    "conversation_history": self.conversation_history
                })
                evaluation_scores = eval_result.metric_scores

            # 11. 대화 이력에 응답 추가
            self.conversation_history.append({
                "role": "assistant",
                "content": response_text
            })

            # 12. 상태 관리자에 사용 기법 기록
            if self.state_manager and evaluation_scores:
                technique = self._detect_technique(response_text)
                if technique:
                    self.state_manager.record_technique(
                        technique=technique,
                        effective=evaluation_scores.get("empathy", 0) > 0.6
                    )

            # 13. 응답 시간 계산
            response_time = (time.time() - start_time) * 1000

            # 14. 모니터링 기록
            self._record_monitoring(
                response_time=response_time,
                crisis_detected=crisis_result.get("is_crisis", False) if crisis_result else False,
                crisis_level=int(crisis_result.get("severity", 0) * 5) if crisis_result else 0,
                empathy_score=evaluation_scores.get("empathy", 0) if evaluation_scores else 0,
                safety_score=evaluation_scores.get("safety", 1.0) if evaluation_scores else 1.0,
                emotion_data=emotion_result
            )

            # 15. A/B 테스트 결과 기록
            if self.experiment_manager and experiment_variant:
                for exp_id in self.experiment_manager.experiments:
                    self.experiment_manager.record_result(
                        experiment_id=exp_id,
                        user_id=self.user_id,
                        metric_name="empathy_score",
                        value=evaluation_scores.get("empathy", 0) if evaluation_scores else 0
                    )

            logger.info(f"Enhanced response generated in {response_time:.0f}ms")

            return EnhancedResponseResult(
                response=response_text,
                emotion=emotion_result,
                crisis=crisis_result,
                validation=validation_result,
                evaluation_scores=evaluation_scores,
                conversation_state=current_state,
                rag_context_used=bool(rag_context),
                rag_sources=rag_sources,
                response_time_ms=response_time,
                is_intervention=False,
                experiment_variant=experiment_variant
            )

        except Exception as e:
            logger.error(f"Error generating enhanced response: {e}")
            response_time = (time.time() - start_time) * 1000

            return EnhancedResponseResult(
                response="죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해주세요.",
                emotion={},
                crisis=None,
                response_time_ms=response_time,
                error=str(e)
            )

    def _generate(self, prompt: str) -> str:
        """모델 추론"""
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=2048
        )

        if self.gpu_info["available"]:
            inputs = {k: v.to("cuda") for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                generation_config=self.generation_config
            )

        generated_text = self.tokenizer.decode(
            outputs[0],
            skip_special_tokens=True
        )

        # 응답 추출
        if "[/INST]" in generated_text:
            parts = generated_text.split("[/INST]")
            response = parts[-1].strip()
        elif "### Assistant:" in generated_text:
            parts = generated_text.split("### Assistant:")
            response = parts[-1].strip()
        else:
            response = generated_text.strip()

        return response

    def _detect_technique(self, response: str) -> Optional[str]:
        """응답에서 사용된 상담 기법 감지"""
        technique_markers = {
            "반영": ["~라고 느끼시", "~하셨군요", "~이셨군요"],
            "공감": ["힘드시겠", "어려우시겠", "고통스러우시겠"],
            "질문": ["어떠신가요?", "어떻게 느끼시", "말씀해 주실"],
            "정보제공": ["도움이 될 수 있는", "방법으로는", "연구에 따르면"],
            "재구조화": ["다른 관점에서", "생각해 보시면", "긍정적인 면"]
        }

        for technique, markers in technique_markers.items():
            if any(marker in response for marker in markers):
                return technique

        return None

    def _record_monitoring(
        self,
        response_time: float,
        crisis_detected: bool,
        crisis_level: int,
        empathy_score: float = 0,
        safety_score: float = 1.0,
        emotion_data: Optional[Dict] = None
    ):
        """모니터링 데이터 기록"""
        if not self.dashboard:
            return

        try:
            self.dashboard.update_conversation_metrics(
                session_id=self.session_id,
                response_time=response_time / 1000,  # ms -> seconds
                crisis_detected=crisis_detected,
                crisis_level=crisis_level,
                empathy_score=empathy_score,
                safety_score=safety_score,
                emotion_data=emotion_data
            )
        except Exception as e:
            logger.warning(f"Failed to record monitoring data: {e}")

    def get_conversation_state(self) -> Optional[Dict[str, Any]]:
        """현재 대화 상태 반환"""
        if not self.state_manager:
            return None

        state = self.state_manager.get_state()
        return {
            "phase": state.phase.value,
            "turn_count": state.turn_count,
            "emotion_trajectory": [
                {"emotion": e.emotion, "intensity": e.intensity}
                for e in state.emotion_trajectory[-5:]
            ],
            "identified_concerns": [c.description for c in state.identified_concerns],
            "techniques_used": [t.technique for t in state.techniques_used[-5:]]
        }

    def get_session_summary(self) -> Dict[str, Any]:
        """세션 요약"""
        state = self.state_manager.get_state() if self.state_manager else None

        summary = {
            "session_id": self.session_id,
            "turn_count": len(self.conversation_history) // 2,
            "conversation_phase": state.phase.value if state else "unknown"
        }

        # 감정 변화
        if state and state.emotion_trajectory:
            first_emotion = state.emotion_trajectory[0]
            last_emotion = state.emotion_trajectory[-1]
            summary["emotion_change"] = {
                "start": first_emotion.emotion,
                "end": last_emotion.emotion,
                "intensity_change": last_emotion.intensity - first_emotion.intensity
            }

        # 위기 이벤트
        if state:
            summary["crisis_events"] = len(state.crisis_flags)

        # 주요 관심사
        if state and state.identified_concerns:
            summary["main_concerns"] = [c.description for c in state.identified_concerns[:3]]

        return summary

    def reset_conversation(self):
        """대화 초기화"""
        self.conversation_history = []
        if self.state_manager:
            self.state_manager.reset()
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info("Conversation reset")

    def get_greeting(self) -> str:
        """인사말"""
        return (
            "안녕하세요, 저는 마음이입니다. 😊\n\n"
            "오늘 어떤 이야기를 나누고 싶으신가요?\n"
            "편하게 말씀해 주세요. 어떤 이야기든 함께 들을 준비가 되어 있습니다."
        )

    def get_closing(self) -> str:
        """종료 인사"""
        summary = self.get_session_summary()
        turn_count = summary.get("turn_count", 0)

        if turn_count > 5:
            return (
                "오늘 함께 이야기 나눠 주셔서 감사합니다.\n\n"
                "오늘 나눈 이야기들이 조금이나마 도움이 되었으면 좋겠어요.\n"
                "언제든 또 이야기하고 싶으실 때 찾아와 주세요.\n\n"
                "오늘 하루도 자신을 돌보는 시간 가지시길 바랍니다. 🌸"
            )
        else:
            return (
                "오늘 찾아와 주셔서 감사합니다.\n"
                "더 이야기하고 싶으실 때 언제든 다시 찾아와 주세요.\n"
                "오늘 하루도 따뜻하게 보내세요. 🌸"
            )


# =============================================================================
# 테스트 함수
# =============================================================================

def test_enhanced_llm():
    """향상된 LLM 테스트"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger.info("=== Testing Enhanced Korean Mental Health LLM ===")

    # LLM 초기화 (테스트 모드)
    llm = EnhancedKoreanMentalHealthLLM(
        enable_rag=False,  # RAG 비활성화 (테스트)
        enable_experiments=False,  # 실험 비활성화
        enable_monitoring=False  # 모니터링 비활성화
    )

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

        print(f"[감정]: {result.emotion.get('primary_emotion', 'N/A')}")
        print(f"[응답 시간]: {result.response_time_ms:.0f}ms")

        if result.validation:
            print(f"[검증 점수]: {result.validation.overall_score:.2f}")

        if result.evaluation_scores:
            print(f"[평가 점수]: 공감={result.evaluation_scores.get('empathy', 0):.2f}")

        print(f"\n[마음이]: {result.response}")

        # 대화 상태
        state = llm.get_conversation_state()
        if state:
            print(f"\n[대화 단계]: {state['phase']}, 턴: {state['turn_count']}")

        print("\n" + "="*70)

    # 세션 요약
    print("\n[세션 요약]")
    summary = llm.get_session_summary()
    print(f"  - 총 턴 수: {summary.get('turn_count', 0)}")
    print(f"  - 대화 단계: {summary.get('conversation_phase', 'N/A')}")
    if 'main_concerns' in summary:
        print(f"  - 주요 관심사: {', '.join(summary['main_concerns'])}")

    # 종료 인사
    print("\n" + llm.get_closing())


if __name__ == "__main__":
    test_enhanced_llm()
