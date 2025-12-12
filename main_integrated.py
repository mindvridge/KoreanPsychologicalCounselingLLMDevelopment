"""
Integrated Korean Mental Health Counseling System
Combines all components into a production-ready system
"""

import os
import sys
import logging
from typing import Dict, Optional, List, Any
from pathlib import Path
import yaml
import torch
from datetime import datetime

# .env 파일 로드 (환경 변수 설정)
from dotenv import load_dotenv
load_dotenv()  # 프로젝트 루트의 .env 파일 로드

# Import all system components
from src.main import KoreanMentalHealthLLM
from src.safety_system_v2 import SafetySystem, LLMCrisisEvaluator, RiskLevel
from src.emotion_analyzer_v2 import KoreanEmotionAnalyzer
from src.assessments import AssessmentManager, PHQ9Assessment, GAD7Assessment, K10Assessment
from src.rag_system import MentalHealthRAG
from src.monitoring import ProductionMonitor, init_monitor
from src.logging_system import ConversationLogger, init_conversation_logger

# 안전 시스템 6종 통합
from src.self_check_system import (
    SelfCheckSystem, get_self_check_system,
    perform_self_check, ResponseStatus
)

# 세션 영속성
from src.session_storage import (
    SQLiteSessionStorage, SessionData,
    init_session_storage, get_session_storage
)

# 상담 효과 시스템
from src.counseling_effectiveness import (
    CounselingEffectivenessSystem, get_effectiveness_system,
    analyze_counseling_effectiveness, CounselingQuality
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class IntegratedMentalHealthSystem:
    """
    Complete integrated mental health counseling system

    Features:
    - Korean LLM (SOLAR-Ko-10.7B) with 4-bit quantization
    - Multi-layered crisis detection
    - Korean emotion analysis
    - Psychological assessments (PHQ-9, GAD-7, K-10)
    - RAG system with therapy knowledge base
    - Real-time monitoring
    - Privacy-compliant logging
    """

    def __init__(self, config_path: str = "configs/config.yaml"):
        """
        Initialize integrated system

        Args:
            config_path: Path to configuration file
        """
        logger.info("="*70)
        logger.info("Initializing Korean Mental Health Counseling System")
        logger.info("="*70)

        # Load configuration
        self.config = self._load_config(config_path)

        # Initialize components
        self.llm: Optional[KoreanMentalHealthLLM] = None
        self.crisis_detector: Optional[LLMCrisisEvaluator] = None
        self.safety_system: Optional[SafetySystem] = None  # 통합 안전 시스템
        self.response_checker: Optional[SelfCheckSystem] = None  # 응답 안전 검사 시스템
        self.emotion_analyzer: Optional[KoreanEmotionAnalyzer] = None
        self.assessment_manager: Optional[AssessmentManager] = None
        self.rag_system: Optional[MentalHealthRAG] = None
        self.monitor: Optional[ProductionMonitor] = None
        self.logger: Optional[ConversationLogger] = None
        self.session_storage: Optional[SQLiteSessionStorage] = None  # 세션 영속성
        self.counseling_system: Optional[CounselingEffectivenessSystem] = None  # 상담 효과 시스템

        # System state
        self.is_initialized = False
        self.initialization_errors = []

        # Statistics
        self.stats = {
            "total_conversations": 0,
            "crisis_detections": 0,
            "assessments_conducted": 0,
            "uptime_start": datetime.now()
        }

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            "model": {
                "name": "beomi/OPEN-SOLAR-KO-10.7B",
                "quantization": "4bit",
                "max_memory": "40GB",
                "device_map": "auto"
            },
            "safety": {
                "crisis_detection_threshold": 0.7,
                "auto_alert_professionals": False,
                "log_all_conversations": True,
                "require_acknowledgment": True
            },
            "cultural": {
                "default_honorific_level": "polite",
                "age_estimation": True,
                "cultural_adaptation": True
            },
            "rag": {
                "knowledge_base_dir": "./knowledge_base",
                "chunk_size": 500,
                "chunk_overlap": 50,
                "embedding_model": "jhgan/ko-sroberta-multitask",
                "max_results": 3
            },
            "monitoring": {
                "enabled": True,
                "retention_days": 30
            },
            "logging": {
                "log_dir": "./logs",
                "retention_days": 90,
                "enable_encryption": True,
                "mask_pii": True
            },
            "api": {
                "rate_limit": 100,
                "timeout": 30,
                "max_conversation_length": 20
            }
        }

    def initialize_all_components(self) -> bool:
        """
        Initialize all system components

        Returns:
            True if successful, False otherwise
        """
        logger.info("Initializing components...")

        success = True

        # 1. Initialize monitoring (first, to track initialization)
        try:
            logger.info("1/7 Initializing monitoring system...")
            self.monitor = init_monitor(
                retention_days=self.config.get("monitoring", {}).get("retention_days", 30)
            )
            logger.info("✓ Monitoring system initialized")
        except Exception as e:
            logger.error(f"✗ Monitoring initialization failed: {e}")
            self.initialization_errors.append(("monitoring", str(e)))
            success = False

        # 2. Initialize logging
        try:
            logger.info("2/7 Initializing conversation logging...")
            self.logger = init_conversation_logger(
                log_dir=Path(self.config.get("logging", {}).get("log_dir", "./logs")),
                retention_days=self.config.get("logging", {}).get("retention_days", 90),
                enable_encryption=self.config.get("logging", {}).get("enable_encryption", True)
            )
            logger.info("✓ Conversation logging initialized")
        except Exception as e:
            logger.error(f"✗ Logging initialization failed: {e}")
            self.initialization_errors.append(("logging", str(e)))
            success = False

        # 2.5. Initialize session storage
        try:
            logger.info("   Initializing session storage...")
            session_config = self.config.get("session", {})
            self.session_storage = init_session_storage(
                db_path=session_config.get("db_path", "./data/sessions.db"),
                session_ttl_hours=session_config.get("ttl_hours", 24),
                max_sessions_per_user=session_config.get("max_per_user", 5),
                enable_encryption=session_config.get("enable_encryption", False)
            )
            # 만료된 세션 정리
            cleaned = self.session_storage.cleanup_expired_sessions()
            if cleaned > 0:
                logger.info(f"   Cleaned up {cleaned} expired sessions")
            logger.info("✓ Session storage initialized")
        except Exception as e:
            logger.error(f"✗ Session storage initialization failed: {e}")
            self.initialization_errors.append(("session_storage", str(e)))
            # 세션 저장소 없이도 동작 가능 (메모리 폴백)
            self.session_storage = None

        # 3. Initialize RAG system
        try:
            logger.info("3/7 Initializing RAG system...")
            rag_config = self.config.get("rag", {})
            self.rag_system = MentalHealthRAG(
                knowledge_base_dir=rag_config.get("knowledge_base_dir", "./knowledge_base"),
                chunk_size=rag_config.get("chunk_size", 500),
                chunk_overlap=rag_config.get("chunk_overlap", 50),
                embedding_model=rag_config.get("embedding_model", "jhgan/ko-sroberta-multitask")
            )
            logger.info("   Indexing knowledge base...")
            self.rag_system.index_documents()
            logger.info(f"✓ RAG system initialized with {len(self.rag_system.doc_processor.documents)} documents")
        except Exception as e:
            logger.error(f"✗ RAG initialization failed: {e}")
            self.initialization_errors.append(("rag", str(e)))
            # RAG is optional, continue without it
            self.rag_system = None

        # 4. Initialize emotion analyzer
        try:
            logger.info("4/7 Initializing emotion analyzer...")
            self.emotion_analyzer = KoreanEmotionAnalyzer()
            logger.info("✓ Emotion analyzer initialized")
        except Exception as e:
            logger.error(f"✗ Emotion analyzer initialization failed: {e}")
            self.initialization_errors.append(("emotion_analyzer", str(e)))
            success = False

        # 5. Initialize crisis detector and safety system
        try:
            logger.info("5/7 Initializing crisis detection system...")
            self.crisis_detector = LLMCrisisEvaluator()
            self.safety_system = SafetySystem()  # 통합 안전 시스템 초기화
            self.response_checker = get_self_check_system(strict_mode=True)  # 응답 안전 검사
            logger.info("✓ Crisis detection & response safety system initialized")
        except Exception as e:
            logger.error(f"✗ Crisis detector initialization failed: {e}")
            self.initialization_errors.append(("crisis_detector", str(e)))
            success = False

        # 5.5. Initialize counseling effectiveness system
        try:
            logger.info("   Initializing counseling effectiveness system...")
            self.counseling_system = get_effectiveness_system()
            logger.info("✓ Counseling effectiveness system initialized")
        except Exception as e:
            logger.error(f"✗ Counseling effectiveness system failed: {e}")
            self.initialization_errors.append(("counseling_system", str(e)))
            # 상담 효과 시스템 없이도 동작 가능

        # 6. Initialize assessment manager
        try:
            logger.info("6/7 Initializing assessment manager...")
            self.assessment_manager = AssessmentManager()
            logger.info("✓ Assessment manager initialized")
        except Exception as e:
            logger.error(f"✗ Assessment manager initialization failed: {e}")
            self.initialization_errors.append(("assessment_manager", str(e)))
            # Assessments are optional
            self.assessment_manager = None

        # 7. Initialize LLM (last, most memory-intensive)
        try:
            logger.info("7/7 Initializing LLM...")
            model_config = self.config.get("model", {})
            provider = model_config.get("provider", "local")

            if provider == "openai":
                # OpenAI API 사용
                logger.info("   Using OpenAI API provider")
                from src.openai_adapter import OpenAICounselor, OpenAIConfig
                
                # .env 파일을 다시 로드하여 환경 변수 확인
                # (Uvicorn reload 모드에서 환경 변수가 손실될 수 있음)
                from dotenv import load_dotenv
                env_path = Path(__file__).parent / ".env"
                if env_path.exists():
                    load_dotenv(env_path, override=True)
                    logger.info(f"   Loaded .env file from {env_path}")
                else:
                    # 프로젝트 루트에서 찾기
                    load_dotenv(override=True)
                
                # API 키 확인
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다. .env 파일을 확인하세요.")
                
                openai_config = model_config.get("openai", {})
                config = OpenAIConfig(
                    api_key=api_key,  # 명시적으로 API 키 전달
                    model=model_config.get("name", "gpt-4o-mini"),
                    temperature=openai_config.get("temperature", 0.7),
                    max_tokens=openai_config.get("max_tokens", 500),
                    top_p=openai_config.get("top_p", 0.9),
                    frequency_penalty=openai_config.get("frequency_penalty", 0.0),
                    presence_penalty=openai_config.get("presence_penalty", 0.0),
                    track_cost=openai_config.get("track_cost", True)
                )
                self.llm = OpenAICounselor(config)
                logger.info(f"✓ OpenAI LLM initialized (model: {config.model})")
                
            elif provider == "mock":
                # Mock LLM 사용 (테스트용)
                logger.info("   Using Mock LLM provider")
                from src.openai_adapter import MockLLM
                self.llm = MockLLM()
                logger.info("✓ Mock LLM initialized")
                
            else:
                # 로컬 LLM 사용 (기본값)
                logger.info("   Using local LLM provider")
                # Check GPU availability
                if torch.cuda.is_available():
                    logger.info(f"   GPU detected: {torch.cuda.get_device_name(0)}")
                    logger.info(f"   GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
                else:
                    logger.warning("   No GPU detected, using CPU (will be slow)")

                self.llm = KoreanMentalHealthLLM(
                    model_name=model_config.get("name", "beomi/OPEN-SOLAR-KO-10.7B"),
                    load_in_4bit=model_config.get("quantization") == "4bit"
                )
                logger.info("✓ Local LLM initialized successfully")
                
        except Exception as e:
            logger.error(f"✗ LLM initialization failed: {e}")
            self.initialization_errors.append(("llm", str(e)))
            # LLM 초기화 실패해도 서버는 실행 가능 (degraded mode)
            self.llm = None
            logger.warning("API will run in degraded mode without LLM")
                
        # 초기화 실패해도 서버는 실행 가능 (degraded mode)
        # LLM이 없어도 다른 기능들은 작동 가능
        self.is_initialized = True  # 항상 True로 설정하여 서버 실행 허용

        if success:
            logger.info("="*70)
            logger.info("✓ All components initialized successfully!")
            logger.info("="*70)
        else:
            logger.warning("="*70)
            logger.warning("⚠ Some components failed to initialize (degraded mode):")
            for component, error in self.initialization_errors:
                logger.warning(f"   - {component}: {error}")
            logger.warning("API will run in degraded mode")
            logger.warning("="*70)

        return True  # 항상 True 반환하여 서버 실행 허용

    def validate_system(self) -> Dict[str, bool]:
        """
        Validate all system components

        Returns:
            Dictionary of component validation results
        """
        logger.info("Validating system...")

        results = {
            "llm": False,
            "crisis_detector": False,
            "emotion_analyzer": False,
            "assessment_manager": False,
            "rag_system": False,
            "monitoring": False,
            "logging": False
        }

        # Validate LLM
        if self.llm:
            try:
                # OpenAI API는 max_length 파라미터가 없으므로 제거
                if hasattr(self.llm, 'generate_response'):
                    # OpenAI API 또는 Mock LLM
                    test_response = self.llm.generate_response("안녕하세요", conversation_history=[])
                else:
                    # 로컬 LLM
                    test_response = self.llm.generate_response("안녕하세요", max_length=50)
                
                if isinstance(test_response, str):
                    results["llm"] = len(test_response) > 0
                elif isinstance(test_response, dict):
                    results["llm"] = "response" in test_response and len(test_response.get("response", "")) > 0
                else:
                    results["llm"] = False
                    
                logger.info(f"✓ LLM validation: {'PASS' if results['llm'] else 'FAIL'}")
            except Exception as e:
                logger.error(f"✗ LLM validation failed: {e}", exc_info=True)
                results["llm"] = False
        else:
            # LLM이 None이면 False
            results["llm"] = False
            logger.warning("LLM is None, validation skipped")

        # Validate crisis detector and safety system
        if self.safety_system:
            try:
                # SafetySystem 검증 - 간단한 테스트 메시지로 확인
                test_result = self.safety_system.check_safety(
                    text="테스트 메시지입니다",
                    emotion_data=None,
                    conversation_history=[]
                )
                results["crisis_detector"] = test_result is not None and "risk_level" in test_result
                logger.info(f"✓ Safety system validation: {'PASS' if results['crisis_detector'] else 'FAIL'}")
            except Exception as e:
                logger.error(f"✗ Safety system validation failed: {e}")
        elif self.crisis_detector:
            results["crisis_detector"] = True
            logger.info("✓ Crisis detector validation: PASS (legacy mode)")

        # Validate emotion analyzer
        if self.emotion_analyzer:
            try:
                test_result = self.emotion_analyzer.analyze("기쁩니다")
                results["emotion_analyzer"] = test_result is not None
                logger.info(f"✓ Emotion analyzer validation: {'PASS' if results['emotion_analyzer'] else 'FAIL'}")
            except Exception as e:
                logger.error(f"✗ Emotion analyzer validation failed: {e}")

        # Validate assessment manager
        if self.assessment_manager:
            results["assessment_manager"] = True
            logger.info("✓ Assessment manager validation: PASS")

        # Validate RAG system
        if self.rag_system and self.rag_system.is_indexed:
            try:
                test_results = self.rag_system.search("우울증", k=1)
                results["rag_system"] = len(test_results) > 0
                logger.info(f"✓ RAG system validation: {'PASS' if results['rag_system'] else 'FAIL'}")
            except Exception as e:
                logger.error(f"✗ RAG system validation failed: {e}")

        # Validate monitoring
        if self.monitor:
            results["monitoring"] = True
            logger.info("✓ Monitoring validation: PASS")

        # Validate logging
        if self.logger:
            results["logging"] = True
            logger.info("✓ Logging validation: PASS")

        return results

    def process_message(
        self,
        session_id: str,
        user_message: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Process a user message through the complete pipeline

        Args:
            session_id: Session identifier
            user_message: User's message
            conversation_history: Previous conversation turns

        Returns:
            Response dictionary containing:
            - response: AI response text
            - crisis_detected: bool
            - crisis_level: int (1-5)
            - emotions: emotion analysis results
            - suggested_assessment: optional assessment recommendation
            - metadata: additional information
        """
        start_time = datetime.now()

        if not self.is_initialized:
            return {
                "error": "System not initialized",
                "response": "죄송합니다. 시스템 초기화 중입니다. 잠시 후 다시 시도해주세요."
            }

        try:
            # 0. Load or create session from storage
            session_data = None
            if self.session_storage:
                session_data = self.session_storage.get_session(session_id)
                if session_data:
                    # 세션 존재: 대화 이력 로드
                    if conversation_history is None:
                        conversation_history = session_data.conversation_history
                    logger.debug(f"Session loaded: {session_id}, turns: {session_data.turn_count}")
                else:
                    # 세션 없음: 새로 생성
                    session_data = self.session_storage.create_session(
                        session_id=session_id,
                        metadata={"created_by": "process_message"}
                    )
                    logger.debug(f"New session created: {session_id}")

            # 1. Emotion analysis
            emotion_result = None
            if self.emotion_analyzer:
                try:
                    emotion_result = self.emotion_analyzer.analyze(user_message)
                except Exception as e:
                    logger.warning(f"Emotion analysis failed: {e}")
                    emotion_result = None

            # 2. Crisis detection
            crisis_result = None
            crisis_detected = False
            crisis_level = 0

            if self.safety_system:
                try:
                    history = conversation_history or []
                    # SafetySystem을 사용한 종합 위기 감지
                    crisis_result = self.safety_system.check_safety(
                        text=user_message,
                        emotion_data=emotion_result,
                        conversation_history=history
                    )

                    # 결과 파싱
                    risk_level = crisis_result.get("risk_level", RiskLevel.NONE)
                    crisis_detected = crisis_result.get("requires_intervention", False)
                    crisis_level = self._risk_level_to_int(risk_level)

                    if crisis_detected:
                        logger.warning(f"위기 감지됨: level={crisis_level}, risk={risk_level.value}")
                except Exception as e:
                    logger.warning(f"Crisis detection failed: {e}")
                    crisis_result = None

            # 3. RAG context retrieval (if not crisis)
            rag_context = ""
            if self.rag_system and not crisis_detected:
                try:
                    rag_context = self.rag_system.get_augmented_context(
                        user_message,
                        max_results=self.config.get("rag", {}).get("max_results", 3)
                    )
                except Exception as e:
                    logger.warning(f"RAG retrieval failed: {e}")

            # 4. Generate response
            if crisis_detected and crisis_level >= 4 and crisis_result:
                # High crisis: Use predefined emergency response
                response = self._get_crisis_response(crisis_result)
            else:
                # Normal: Generate with LLM
                if not self.llm:
                    # LLM이 없으면 기본 응답
                    response = "죄송합니다. 시스템 초기화 중입니다. 잠시 후 다시 시도해주세요."
                else:
                    system_context = self._build_system_context(
                        emotion_result=emotion_result,
                        crisis_result=crisis_result,
                        rag_context=rag_context
                    )

                    # OpenAI API는 다른 인터페이스를 사용
                    if hasattr(self.llm, 'generate_response_async'):
                        # OpenAI API (비동기)
                        import asyncio
                        try:
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                # 이미 실행 중인 루프가 있으면 동기 메서드 사용
                                response = self.llm.generate_response(
                                    user_message,
                                    conversation_history=conversation_history
                                )
                            else:
                                response = loop.run_until_complete(
                                    self.llm.generate_response_async(
                                        user_message,
                                        conversation_history=conversation_history
                                    )
                                )
                        except:
                            response = self.llm.generate_response(
                                user_message,
                                conversation_history=conversation_history
                            )
                    elif hasattr(self.llm, 'generate_response'):
                        # 로컬 LLM 또는 Mock LLM
                        if isinstance(self.llm, KoreanMentalHealthLLM):
                            # 로컬 LLM은 context와 conversation_history를 받음
                            response = self.llm.generate_response(
                                user_message,
                                skip_safety_check=False
                            )
                            if isinstance(response, dict):
                                response = response.get("response", "응답 생성 실패")
                        else:
                            # OpenAI API 동기 메서드
                            response = self.llm.generate_response(
                                user_message,
                                conversation_history=conversation_history
                            )
                    else:
                        response = "죄송합니다. LLM이 올바르게 초기화되지 않았습니다."

            # 5. Response safety check (6종 안전 시스템 통합 검사)
            safety_check_result = None
            if self.response_checker and response:
                try:
                    safety_check_result = self.response_checker.check_response(
                        response=response,
                        user_message=user_message,
                        context={
                            "emotion": emotion_result,
                            "crisis_detected": crisis_detected,
                            "conversation_history": conversation_history
                        }
                    )

                    # 응답 상태에 따른 처리
                    if safety_check_result.status == ResponseStatus.BLOCKED:
                        # 차단된 경우: 안전한 대체 응답 사용
                        logger.warning(f"응답 차단됨: {safety_check_result.critical_issues}")
                        response = self._get_safe_fallback_response(
                            safety_check_result.critical_issues
                        )
                    elif safety_check_result.status == ResponseStatus.NEEDS_REVISION:
                        # 수정 필요: 수정된 응답 사용 또는 재생성
                        if safety_check_result.corrected_response:
                            response = safety_check_result.corrected_response
                            logger.info("응답이 자동 수정되었습니다")
                        else:
                            logger.warning(f"응답 수정 필요: {safety_check_result.warnings[:3]}")
                    elif safety_check_result.status == ResponseStatus.WARNING:
                        # 경고: 로그만 기록
                        logger.info(f"응답 경고: {safety_check_result.warnings[:2]}")

                except Exception as e:
                    logger.warning(f"Response safety check failed: {e}")

            # 6. Counseling effectiveness analysis
            counseling_analysis = None
            if self.counseling_system and response:
                try:
                    counseling_analysis = self.counseling_system.analyze_interaction(
                        session_id=session_id,
                        user_message=user_message,
                        assistant_response=response,
                        context={
                            "emotion": emotion_result.get("primary_emotion") if emotion_result else None,
                            "crisis_detected": crisis_detected,
                            "conversation_history": conversation_history
                        }
                    )
                    logger.debug(
                        f"Counseling quality: {counseling_analysis.quality_grade.value}, "
                        f"score: {counseling_analysis.overall_quality_score:.1f}"
                    )
                except Exception as e:
                    logger.warning(f"Counseling effectiveness analysis failed: {e}")

            # 7. Assessment recommendation
            suggested_assessment = None
            if self.assessment_manager and emotion_result:
                suggested_assessment = self.assessment_manager.smart_selection({
                    "emotions": emotion_result,
                    "crisis": crisis_detected
                })

            # 6. Calculate response time
            response_time = (datetime.now() - start_time).total_seconds()

            # 7. Track metrics
            if self.monitor:
                therapy_technique = self._detect_therapy_technique(response)
                self.monitor.track_conversation(
                    session_id=session_id,
                    response_time=response_time,
                    tokens_generated=len(response.split()),
                    crisis_detected=crisis_detected,
                    crisis_level=crisis_level,
                    therapy_technique=therapy_technique,
                    model_confidence=0.85  # Placeholder
                )

            # 8. Log conversation (privacy-compliant)
            if self.logger and self.config.get("safety", {}).get("log_all_conversations", True):
                try:
                    # emotion_result에서 primary_emotion 안전하게 추출
                    emotion_for_log = None
                    if emotion_result and isinstance(emotion_result, dict):
                        primary_emotion = emotion_result.get("primary_emotion")
                        if primary_emotion:
                            if isinstance(primary_emotion, dict):
                                emotion_for_log = primary_emotion.get("emotion")
                            else:
                                emotion_for_log = str(primary_emotion)
                    
                    self.logger.log_conversation(
                        session_id=session_id,
                        turn_data={
                            "user_message": user_message,
                            "assistant_response": response,
                            "timestamp": datetime.now(),
                            "crisis_detected": crisis_detected,
                            "crisis_level": crisis_level,
                            "metadata": {
                                "response_time": response_time,
                                "emotions": emotion_for_log
                            }
                        },
                        mask_pii=self.config.get("logging", {}).get("mask_pii", True)
                    )
                except Exception as e:
                    logger.warning(f"Failed to log conversation: {e}")

            # 9. Update statistics
            self.stats["total_conversations"] += 1
            if crisis_detected:
                self.stats["crisis_detections"] += 1

            # 9.5. Save to session storage
            if self.session_storage:
                try:
                    # 사용자 메시지 저장
                    self.session_storage.add_message(
                        session_id=session_id,
                        role="user",
                        content=user_message,
                        metadata={"emotion": emotion_result.get("primary_emotion") if emotion_result else None}
                    )
                    # 어시스턴트 응답 저장
                    primary_emotion = None
                    if emotion_result and isinstance(emotion_result, dict):
                        pe = emotion_result.get("primary_emotion")
                        primary_emotion = pe.get("emotion") if isinstance(pe, dict) else str(pe) if pe else None

                    self.session_storage.add_message(
                        session_id=session_id,
                        role="assistant",
                        content=response,
                        metadata={
                            "crisis_detected": crisis_detected,
                            "safety_status": safety_check_result.status.value if safety_check_result else None
                        }
                    )
                    # 세션 메타데이터 업데이트
                    self.session_storage.update_session(
                        session_id=session_id,
                        crisis_detected=crisis_detected,
                        emotion=primary_emotion
                    )
                except Exception as e:
                    logger.warning(f"Failed to save to session storage: {e}")

            # 10. Build response
            return {
                "response": response,
                "crisis_detected": crisis_detected,
                "crisis_level": crisis_level,
                "crisis_details": crisis_result if crisis_detected else None,
                "emotions": emotion_result,
                "suggested_assessment": suggested_assessment,
                "response_time": response_time,
                "safety_check": {
                    "status": safety_check_result.status.value if safety_check_result else "unchecked",
                    "score": safety_check_result.overall_score if safety_check_result else None,
                    "warnings": safety_check_result.warnings[:3] if safety_check_result else [],
                    "passed": safety_check_result.status in [ResponseStatus.SAFE, ResponseStatus.WARNING] if safety_check_result else True
                },
                "counseling_quality": {
                    "score": counseling_analysis.overall_quality_score if counseling_analysis else None,
                    "grade": counseling_analysis.quality_grade.value if counseling_analysis else None,
                    "interventions": counseling_analysis.recommended_interventions[:3] if counseling_analysis else [],
                    "session_phase": counseling_analysis.session_progress.current_phase if counseling_analysis and counseling_analysis.session_progress else None
                },
                "metadata": {
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "rag_used": bool(rag_context)
                }
            }

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return {
                "error": str(e),
                "response": "죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해주세요."
            }

    def _risk_level_to_int(self, risk_level: RiskLevel) -> int:
        """Convert RiskLevel enum to integer"""
        mapping = {
            RiskLevel.NONE: 0,
            RiskLevel.LOW: 1,
            RiskLevel.MODERATE: 2,
            RiskLevel.HIGH: 3,
            RiskLevel.CRITICAL: 4
        }
        return mapping.get(risk_level, 0)

    def _build_system_context(
        self,
        emotion_result: Optional[Dict],
        crisis_result: Optional[Dict],
        rag_context: str
    ) -> str:
        """Build system context for LLM"""
        context_parts = [
            "당신은 한국 정신건강 상담 AI입니다.",
            "공감적이고 전문적으로 응답하세요.",
            "의료 진단이나 처방은 하지 마세요."
        ]

        if emotion_result and isinstance(emotion_result, dict):
            try:
                primary_emotion = emotion_result.get("primary_emotion")
                if primary_emotion:
                    if isinstance(primary_emotion, dict):
                        emotion_name = primary_emotion.get("emotion")
                    else:
                        emotion_name = str(primary_emotion)
                    if emotion_name:
                        context_parts.append(f"내담자의 주 감정: {emotion_name}")
            except Exception as e:
                logger.warning(f"Error extracting emotion from result: {e}")

        if crisis_result and isinstance(crisis_result, dict):
            try:
                risk_level = crisis_result.get("overall_risk_level")
                if risk_level in [RiskLevel.MODERATE, RiskLevel.HIGH]:
                    context_parts.append("주의: 위기 징후 감지됨. 신중하게 대응하세요.")
            except Exception as e:
                logger.warning(f"Error extracting crisis level: {e}")

        if rag_context:
            context_parts.append("\n--- 참고 자료 ---")
            context_parts.append(rag_context)

        return "\n".join(context_parts)

    def _get_crisis_response(self, crisis_result: Dict) -> str:
        """Get emergency response for high crisis situations"""
        return """
지금 매우 힘든 시간을 보내고 계신 것 같아 걱정됩니다.

**즉시 전문가의 도움을 받으시길 강력히 권장합니다:**

📞 자살예방상담전화: 1393 (24시간, 무료)
📞 정신건강위기상담: 1577-0199 (24시간)
📞 청소년전화: 1388
🚨 응급상황: 119

당신의 생명은 소중합니다.
혼자서 감당하지 마시고, 지금 바로 위 번호로 전화해주세요.
전문가들이 24시간 기다리고 있습니다.

제가 계속 함께 있겠습니다. 어떻게 도와드릴까요?
"""

    def _get_safe_fallback_response(self, issues: List[str]) -> str:
        """
        안전 문제로 차단된 경우 대체 응답 생성

        Args:
            issues: 감지된 문제 목록

        Returns:
            str: 안전한 대체 응답
        """
        # 문제 유형에 따른 대체 응답
        if any("의학" in issue or "medical" in issue.lower() for issue in issues):
            return (
                "의료적인 부분에 대해서는 제가 정확한 정보를 드리기 어렵습니다. "
                "전문 의료인과 상담하시는 것을 권장드립니다. "
                "그 외에 마음이 힘드신 부분이 있으시다면 함께 이야기 나눠보아요."
            )
        elif any("법" in issue or "legal" in issue.lower() for issue in issues):
            return (
                "법적인 문제에 대해서는 제가 조언을 드리기 어렵습니다. "
                "전문 법률 상담을 받으시는 것이 좋을 것 같아요. "
                "혹시 이 상황 때문에 마음이 힘드신 건 아닌지 여쭤봐도 될까요?"
            )
        elif any("진단" in issue or "diagnosis" in issue.lower() for issue in issues):
            return (
                "정확한 진단은 전문가의 평가가 필요한 영역입니다. "
                "지금 느끼시는 어려움에 대해 조금 더 이야기해 주시겠어요? "
                "함께 어떤 도움이 필요한지 생각해볼 수 있을 것 같아요."
            )
        else:
            # 일반적인 안전 대체 응답
            return (
                "말씀해 주신 내용을 잘 들었습니다. "
                "지금 어떤 마음이 드시는지, 조금 더 이야기해 주실 수 있을까요? "
                "함께 이야기 나누면서 도움이 될 수 있는 방법을 찾아보겠습니다."
            )

    def _detect_therapy_technique(self, response: str) -> Optional[str]:
        """Detect which therapy technique was used in response"""
        cbt_keywords = ["생각", "인지", "왜곡", "재구성"]
        dbt_keywords = ["마음챙김", "수용", "감정조절", "고통감내"]
        act_keywords = ["가치", "전념", "수용", "탈융합"]

        if any(kw in response for kw in cbt_keywords):
            return "CBT"
        elif any(kw in response for kw in dbt_keywords):
            return "DBT"
        elif any(kw in response for kw in act_keywords):
            return "ACT"
        return None

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        status = {
            "initialized": self.is_initialized,
            "uptime": str(datetime.now() - self.stats["uptime_start"]),
            "statistics": self.stats.copy(),
            "components": {
                "llm": self.llm is not None,
                "crisis_detector": self.crisis_detector is not None,
                "safety_system": self.safety_system is not None,
                "response_checker": self.response_checker is not None,
                "emotion_analyzer": self.emotion_analyzer is not None,
                "assessment_manager": self.assessment_manager is not None,
                "rag_system": self.rag_system is not None and self.rag_system.is_indexed,
                "monitoring": self.monitor is not None,
                "logging": self.logger is not None,
                "session_storage": self.session_storage is not None,
                "counseling_system": self.counseling_system is not None
            }
        }

        # Add session stats if available
        if self.session_storage:
            try:
                status["session_stats"] = self.session_storage.get_session_stats()
            except Exception:
                pass

        # Add monitoring stats if available
        if self.monitor:
            status["metrics"] = self.monitor.get_realtime_stats()

        return status

    def shutdown(self) -> None:
        """Gracefully shutdown the system"""
        logger.info("Shutting down system...")

        # Save metrics
        if self.monitor:
            try:
                self.monitor.export_metrics(
                    Path("logs/metrics_final.json"),
                    format="json"
                )
                logger.info("✓ Metrics exported")
            except Exception as e:
                logger.error(f"Error exporting metrics: {e}")

        # Cleanup old logs
        if self.logger:
            try:
                deleted = self.logger.cleanup_old_logs(dry_run=False)
                logger.info(f"✓ Cleaned up {deleted} old log files")
            except Exception as e:
                logger.error(f"Error cleaning logs: {e}")

        logger.info("✓ System shutdown complete")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Korean Mental Health Counseling System")
    parser.add_argument("--config", default="configs/config.yaml", help="Config file path")
    parser.add_argument("--validate-only", action="store_true", help="Only validate, don't start")
    args = parser.parse_args()

    # Initialize system
    system = IntegratedMentalHealthSystem(config_path=args.config)

    # Initialize all components
    if not system.initialize_all_components():
        logger.error("Failed to initialize system")
        sys.exit(1)

    # Validate
    validation_results = system.validate_system()

    all_valid = all(validation_results.values())
    if not all_valid:
        logger.warning("Some components failed validation")
        for component, valid in validation_results.items():
            if not valid:
                logger.warning(f"  - {component}: FAILED")

    if args.validate_only:
        sys.exit(0 if all_valid else 1)

    # Print status
    status = system.get_system_status()
    logger.info("\n" + "="*70)
    logger.info("System Status:")
    logger.info(f"  Initialized: {status['initialized']}")
    logger.info(f"  Uptime: {status['uptime']}")
    logger.info(f"  Total Conversations: {status['statistics']['total_conversations']}")
    logger.info("="*70)

    # Interactive mode (if not running as service)
    logger.info("\nSystem ready! Use API or Gradio interface to interact.")
    logger.info("Press Ctrl+C to shutdown")

    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\nShutdown signal received")
        system.shutdown()


if __name__ == "__main__":
    main()
