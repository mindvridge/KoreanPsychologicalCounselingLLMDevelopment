"""
SOLAR 모델 파인튜닝 트레이너
Fine-tuning Trainer for Korean Psychological Counseling LLM

지원 기법:
- Full Fine-tuning
- LoRA (Low-Rank Adaptation)
- QLoRA (Quantized LoRA)
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Optional imports for training
try:
    import torch
    from torch.utils.data import Dataset as TorchDataset, DataLoader
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available")

try:
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        TrainingArguments,
        Trainer,
        DataCollatorForLanguageModeling,
        BitsAndBytesConfig
    )
    from peft import (
        LoraConfig,
        get_peft_model,
        prepare_model_for_kbit_training,
        TaskType
    )
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers/PEFT not available for training")


# =============================================================================
# 설정 클래스
# =============================================================================

@dataclass
class ModelConfig:
    """모델 설정"""
    model_name: str = "upstage/SOLAR-10.7B-Instruct-v1.0"
    tokenizer_name: Optional[str] = None  # None이면 model_name 사용

    # 양자화 설정
    load_in_4bit: bool = True
    load_in_8bit: bool = False
    bnb_4bit_compute_dtype: str = "float16"
    bnb_4bit_quant_type: str = "nf4"
    bnb_4bit_use_double_quant: bool = True

    # 토크나이저 설정
    max_length: int = 2048
    padding_side: str = "right"
    truncation_side: str = "right"


@dataclass
class LoRAConfig:
    """LoRA 설정"""
    r: int = 16                          # LoRA rank
    lora_alpha: int = 32                 # LoRA alpha
    target_modules: List[str] = field(default_factory=lambda: [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj"
    ])
    lora_dropout: float = 0.05
    bias: str = "none"
    task_type: str = "CAUSAL_LM"


@dataclass
class TrainingConfig:
    """학습 설정"""
    output_dir: str = "./outputs"
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 2
    per_device_eval_batch_size: int = 2
    gradient_accumulation_steps: int = 8
    gradient_checkpointing: bool = True

    # 최적화
    learning_rate: float = 2e-4
    weight_decay: float = 0.01
    warmup_ratio: float = 0.03
    lr_scheduler_type: str = "cosine"
    optim: str = "paged_adamw_32bit"

    # 로깅
    logging_steps: int = 10
    save_steps: int = 100
    eval_steps: int = 100
    save_total_limit: int = 3

    # 기타
    fp16: bool = True
    bf16: bool = False
    max_grad_norm: float = 0.3
    group_by_length: bool = True
    report_to: str = "tensorboard"

    # 데이터
    max_seq_length: int = 2048
    packing: bool = False


@dataclass
class FineTuningConfig:
    """전체 파인튜닝 설정"""
    model: ModelConfig = field(default_factory=ModelConfig)
    lora: LoRAConfig = field(default_factory=LoRAConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)

    # 파인튜닝 방법
    method: str = "qlora"  # full, lora, qlora

    # 실험 정보
    experiment_name: str = "counseling_finetune"
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def save(self, filepath: Union[str, Path]) -> None:
        """설정 저장"""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> "FineTuningConfig":
        """설정 로드"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        return cls(
            model=ModelConfig(**data.get("model", {})),
            lora=LoRAConfig(**data.get("lora", {})),
            training=TrainingConfig(**data.get("training", {})),
            method=data.get("method", "qlora"),
            experiment_name=data.get("experiment_name", ""),
            description=data.get("description", ""),
            created_at=data.get("created_at", "")
        )


# =============================================================================
# 데이터셋 래퍼
# =============================================================================

if TORCH_AVAILABLE:
    class CounselingTrainDataset(TorchDataset):
        """파인튜닝용 데이터셋"""

        def __init__(
            self,
            data_path: Union[str, Path],
            tokenizer,
            max_length: int = 2048
        ):
            self.tokenizer = tokenizer
            self.max_length = max_length
            self.examples = []

            # 데이터 로드
            with open(data_path, "r", encoding="utf-8") as f:
                for line in f:
                    data = json.loads(line.strip())
                    self.examples.append(data)

            logger.info(f"Loaded {len(self.examples)} examples from {data_path}")

        def __len__(self) -> int:
            return len(self.examples)

        def __getitem__(self, idx: int) -> Dict[str, Any]:
            example = self.examples[idx]

            # SOLAR 형식 텍스트 가져오기
            text = example.get("text", "")

            # 토크나이즈
            encoding = self.tokenizer(
                text,
                truncation=True,
                max_length=self.max_length,
                padding="max_length",
                return_tensors="pt"
            )

            return {
                "input_ids": encoding["input_ids"].squeeze(),
                "attention_mask": encoding["attention_mask"].squeeze(),
                "labels": encoding["input_ids"].squeeze()
            }


# =============================================================================
# 트레이너 클래스
# =============================================================================

class CounselingFineTuner:
    """심리상담 LLM 파인튜너"""

    def __init__(self, config: FineTuningConfig):
        self.config = config
        self.model = None
        self.tokenizer = None
        self.trainer = None

        if not TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "transformers와 peft 라이브러리가 필요합니다. "
                "pip install transformers peft bitsandbytes 를 실행하세요."
            )

    def setup(self) -> None:
        """모델 및 토크나이저 설정"""
        logger.info(f"Setting up model: {self.config.model.model_name}")

        # 토크나이저 로드
        tokenizer_name = self.config.model.tokenizer_name or self.config.model.model_name
        self.tokenizer = AutoTokenizer.from_pretrained(
            tokenizer_name,
            trust_remote_code=True
        )

        # 패딩 토큰 설정
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.padding_side = self.config.model.padding_side

        # 양자화 설정
        if self.config.method == "qlora":
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=self.config.model.load_in_4bit,
                bnb_4bit_quant_type=self.config.model.bnb_4bit_quant_type,
                bnb_4bit_compute_dtype=getattr(
                    torch, self.config.model.bnb_4bit_compute_dtype
                ),
                bnb_4bit_use_double_quant=self.config.model.bnb_4bit_use_double_quant
            )
        elif self.config.method == "lora" and self.config.model.load_in_8bit:
            bnb_config = BitsAndBytesConfig(load_in_8bit=True)
        else:
            bnb_config = None

        # 모델 로드
        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.model.model_name,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
            torch_dtype=torch.float16 if self.config.training.fp16 else torch.float32
        )

        # LoRA 설정 (qlora 또는 lora인 경우)
        if self.config.method in ["qlora", "lora"]:
            if self.config.method == "qlora":
                self.model = prepare_model_for_kbit_training(self.model)

            lora_config = LoraConfig(
                r=self.config.lora.r,
                lora_alpha=self.config.lora.lora_alpha,
                target_modules=self.config.lora.target_modules,
                lora_dropout=self.config.lora.lora_dropout,
                bias=self.config.lora.bias,
                task_type=TaskType.CAUSAL_LM
            )

            self.model = get_peft_model(self.model, lora_config)
            self.model.print_trainable_parameters()

        logger.info("Model setup complete")

    def prepare_training(
        self,
        train_dataset_path: Union[str, Path],
        eval_dataset_path: Optional[Union[str, Path]] = None
    ) -> None:
        """학습 준비"""
        logger.info("Preparing training...")

        # 데이터셋 로드
        train_dataset = CounselingTrainDataset(
            train_dataset_path,
            self.tokenizer,
            self.config.training.max_seq_length
        )

        eval_dataset = None
        if eval_dataset_path:
            eval_dataset = CounselingTrainDataset(
                eval_dataset_path,
                self.tokenizer,
                self.config.training.max_seq_length
            )

        # 학습 인자 설정
        training_args = TrainingArguments(
            output_dir=self.config.training.output_dir,
            num_train_epochs=self.config.training.num_train_epochs,
            per_device_train_batch_size=self.config.training.per_device_train_batch_size,
            per_device_eval_batch_size=self.config.training.per_device_eval_batch_size,
            gradient_accumulation_steps=self.config.training.gradient_accumulation_steps,
            gradient_checkpointing=self.config.training.gradient_checkpointing,
            learning_rate=self.config.training.learning_rate,
            weight_decay=self.config.training.weight_decay,
            warmup_ratio=self.config.training.warmup_ratio,
            lr_scheduler_type=self.config.training.lr_scheduler_type,
            optim=self.config.training.optim,
            logging_steps=self.config.training.logging_steps,
            save_steps=self.config.training.save_steps,
            eval_steps=self.config.training.eval_steps if eval_dataset else None,
            evaluation_strategy="steps" if eval_dataset else "no",
            save_total_limit=self.config.training.save_total_limit,
            fp16=self.config.training.fp16,
            bf16=self.config.training.bf16,
            max_grad_norm=self.config.training.max_grad_norm,
            group_by_length=self.config.training.group_by_length,
            report_to=self.config.training.report_to,
            load_best_model_at_end=True if eval_dataset else False,
        )

        # Data Collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False
        )

        # Trainer 초기화
        self.trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=data_collator,
        )

        logger.info("Training preparation complete")

    def train(self) -> Dict[str, Any]:
        """학습 실행"""
        if self.trainer is None:
            raise RuntimeError("prepare_training()을 먼저 호출하세요")

        logger.info("Starting training...")

        # 학습
        train_result = self.trainer.train()

        # 결과 저장
        metrics = train_result.metrics
        self.trainer.log_metrics("train", metrics)
        self.trainer.save_metrics("train", metrics)

        # 모델 저장
        self.save_model()

        logger.info("Training complete")
        return metrics

    def save_model(self, output_dir: Optional[str] = None) -> str:
        """모델 저장"""
        output_dir = output_dir or self.config.training.output_dir
        final_dir = Path(output_dir) / "final_model"
        final_dir.mkdir(parents=True, exist_ok=True)

        # 모델 저장
        self.trainer.save_model(str(final_dir))

        # 토크나이저 저장
        self.tokenizer.save_pretrained(str(final_dir))

        # 설정 저장
        self.config.save(final_dir / "finetuning_config.json")

        logger.info(f"Model saved to {final_dir}")
        return str(final_dir)

    def evaluate(self, eval_dataset_path: Union[str, Path]) -> Dict[str, Any]:
        """평가"""
        if self.model is None:
            raise RuntimeError("setup()을 먼저 호출하세요")

        eval_dataset = CounselingTrainDataset(
            eval_dataset_path,
            self.tokenizer,
            self.config.training.max_seq_length
        )

        # 임시 Trainer 생성
        eval_args = TrainingArguments(
            output_dir=self.config.training.output_dir,
            per_device_eval_batch_size=self.config.training.per_device_eval_batch_size,
            fp16=self.config.training.fp16,
            report_to="none"
        )

        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False
        )

        eval_trainer = Trainer(
            model=self.model,
            args=eval_args,
            eval_dataset=eval_dataset,
            data_collator=data_collator
        )

        metrics = eval_trainer.evaluate()
        logger.info(f"Evaluation metrics: {metrics}")

        return metrics

    def generate_response(
        self,
        prompt: str,
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
        do_sample: bool = True
    ) -> str:
        """응답 생성 (테스트용)"""
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("setup()을 먼저 호출하세요")

        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=self.config.model.max_length
        )

        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=do_sample,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )

        response = self.tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:],
            skip_special_tokens=True
        )

        return response


# =============================================================================
# CLI 스크립트용 함수
# =============================================================================

def create_default_config() -> FineTuningConfig:
    """기본 설정 생성"""
    return FineTuningConfig(
        model=ModelConfig(
            model_name="upstage/SOLAR-10.7B-Instruct-v1.0",
            load_in_4bit=True,
            max_length=2048
        ),
        lora=LoRAConfig(
            r=16,
            lora_alpha=32,
            lora_dropout=0.05
        ),
        training=TrainingConfig(
            output_dir="./outputs/counseling_solar",
            num_train_epochs=3,
            per_device_train_batch_size=2,
            gradient_accumulation_steps=8,
            learning_rate=2e-4
        ),
        method="qlora",
        experiment_name="korean_counseling_finetune",
        description="Korean psychological counseling LLM fine-tuning with QLoRA"
    )


def run_finetuning(
    config_path: Optional[str] = None,
    train_data_path: str = None,
    eval_data_path: Optional[str] = None
) -> Dict[str, Any]:
    """파인튜닝 실행"""
    # 설정 로드
    if config_path:
        config = FineTuningConfig.load(config_path)
    else:
        config = create_default_config()

    # 트레이너 생성 및 실행
    finetuner = CounselingFineTuner(config)
    finetuner.setup()
    finetuner.prepare_training(train_data_path, eval_data_path)
    metrics = finetuner.train()

    return {
        "status": "success",
        "metrics": metrics,
        "model_path": finetuner.config.training.output_dir
    }


def load_finetuned_model(
    model_path: str,
    config_path: Optional[str] = None
) -> CounselingFineTuner:
    """파인튜닝된 모델 로드"""
    # 설정 로드
    if config_path:
        config = FineTuningConfig.load(config_path)
    else:
        config_file = Path(model_path) / "finetuning_config.json"
        if config_file.exists():
            config = FineTuningConfig.load(config_file)
        else:
            config = create_default_config()
            config.model.model_name = model_path

    finetuner = CounselingFineTuner(config)
    finetuner.setup()

    return finetuner
