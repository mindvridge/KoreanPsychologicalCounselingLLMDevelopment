"""
심리상담 파인튜닝 데이터셋 정의 및 관리
Korean Psychological Counseling Fine-tuning Dataset

데이터 형식:
- Instruction-Response 쌍
- 다중 턴 대화
- 메타데이터 (감정, 위기 레벨, 상담 기법 등)
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Iterator, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import random
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# 데이터 구조 정의
# =============================================================================

class CounselingCategory(Enum):
    """상담 카테고리"""
    DEPRESSION = "depression"           # 우울
    ANXIETY = "anxiety"                 # 불안
    RELATIONSHIP = "relationship"       # 대인관계
    FAMILY = "family"                   # 가족
    WORK_STRESS = "work_stress"        # 직장 스트레스
    ACADEMIC = "academic"               # 학업
    SELF_ESTEEM = "self_esteem"        # 자존감
    TRAUMA = "trauma"                   # 트라우마
    GRIEF = "grief"                     # 슬픔/상실
    LIFE_TRANSITION = "life_transition" # 인생 전환기
    GENERAL = "general"                 # 일반


class CounselingTechnique(Enum):
    """상담 기법"""
    CBT = "cbt"                         # 인지행동치료
    DBT = "dbt"                         # 변증법적 행동치료
    ACT = "act"                         # 수용전념치료
    MI = "mi"                           # 동기강화상담
    SOLUTION_FOCUSED = "solution_focused"  # 해결중심치료
    PERSON_CENTERED = "person_centered"    # 인간중심상담
    NARRATIVE = "narrative"             # 내러티브 치료
    MINDFULNESS = "mindfulness"         # 마음챙김 기반


class CrisisLevel(Enum):
    """위기 수준"""
    NONE = 0        # 위기 없음
    LOW = 1         # 낮은 위험
    MODERATE = 2    # 중간 위험
    HIGH = 3        # 높은 위험
    CRITICAL = 4    # 심각한 위기
    EMERGENCY = 5   # 응급 상황


@dataclass
class ConversationTurn:
    """대화 턴"""
    role: str                           # "user" or "assistant"
    content: str
    emotion: Optional[str] = None       # 감지된 감정
    emotion_intensity: float = 0.0      # 감정 강도 (0-1)
    crisis_level: int = 0               # 위기 수준
    technique_used: Optional[str] = None  # 사용된 상담 기법


@dataclass
class CounselingExample:
    """파인튜닝 예시 데이터"""
    example_id: str
    conversation: List[ConversationTurn]

    # 메타데이터
    category: str = "general"
    primary_emotion: str = ""
    crisis_level: int = 0
    techniques_used: List[str] = field(default_factory=list)

    # 품질 지표
    quality_score: float = 0.0          # 전체 품질 점수
    empathy_score: float = 0.0          # 공감 점수
    safety_score: float = 1.0           # 안전성 점수
    therapeutic_score: float = 0.0      # 치료적 적절성

    # 메타정보
    source: str = ""                    # 데이터 출처
    created_at: str = ""                # 생성 시간
    validated: bool = False             # 검증 여부
    validator: Optional[str] = None     # 검증자

    def to_instruction_format(self) -> Dict[str, str]:
        """Instruction 형식으로 변환"""
        if len(self.conversation) < 2:
            return {}

        # 시스템 프롬프트 + 대화 히스토리 구성
        instruction_parts = []

        # 이전 대화 컨텍스트
        for i, turn in enumerate(self.conversation[:-1]):
            if turn.role == "user":
                instruction_parts.append(f"내담자: {turn.content}")
            else:
                instruction_parts.append(f"상담사: {turn.content}")

        # 마지막 턴이 assistant인 경우
        if self.conversation[-1].role == "assistant":
            instruction = "\n".join(instruction_parts[:-1])
            response = self.conversation[-1].content
        else:
            instruction = "\n".join(instruction_parts)
            response = ""

        return {
            "instruction": instruction,
            "response": response,
            "category": self.category,
            "crisis_level": self.crisis_level
        }

    def to_chat_format(self) -> List[Dict[str, str]]:
        """Chat 형식으로 변환 (OpenAI/Hugging Face 호환)"""
        messages = []

        # 시스템 메시지
        system_msg = self._generate_system_message()
        messages.append({"role": "system", "content": system_msg})

        # 대화 턴
        for turn in self.conversation:
            messages.append({
                "role": turn.role,
                "content": turn.content
            })

        return messages

    def _generate_system_message(self) -> str:
        """시스템 메시지 생성"""
        return """당신은 전문 심리상담사입니다. 내담자의 이야기에 공감하며 따뜻하게 경청하고,
적절한 상담 기법을 활용하여 내담자가 자신의 감정과 생각을 탐색할 수 있도록 도와주세요.

핵심 원칙:
- 무조건적 긍정적 존중
- 공감적 이해
- 진실성
- 비판단적 태도

위기 상황 시 반드시 전문 기관(자살예방상담전화 1393, 정신건강위기상담전화 1577-0199)을 안내하세요."""

    def to_solar_format(self) -> str:
        """SOLAR 모델 형식으로 변환"""
        # SOLAR 모델의 instruction format
        template = """### System:
{system}

### User:
{user}

### Assistant:
{assistant}"""

        system_msg = self._generate_system_message()

        # 마지막 user 메시지와 assistant 응답 찾기
        user_msg = ""
        assistant_msg = ""

        for turn in reversed(self.conversation):
            if turn.role == "assistant" and not assistant_msg:
                assistant_msg = turn.content
            elif turn.role == "user" and not user_msg:
                user_msg = turn.content
                break

        # 이전 컨텍스트 추가
        context_parts = []
        for turn in self.conversation[:-2]:  # 마지막 2개 제외
            if turn.role == "user":
                context_parts.append(f"내담자: {turn.content}")
            else:
                context_parts.append(f"상담사: {turn.content}")

        if context_parts:
            user_msg = "\n".join(context_parts) + f"\n\n내담자: {user_msg}"

        return template.format(
            system=system_msg,
            user=user_msg,
            assistant=assistant_msg
        )


@dataclass
class DatasetConfig:
    """데이터셋 설정"""
    name: str
    version: str = "1.0.0"
    description: str = ""

    # 데이터 경로
    train_path: Optional[str] = None
    valid_path: Optional[str] = None
    test_path: Optional[str] = None

    # 분할 비율
    train_ratio: float = 0.8
    valid_ratio: float = 0.1
    test_ratio: float = 0.1

    # 필터링 기준
    min_quality_score: float = 0.6
    min_turns: int = 2
    max_turns: int = 20
    min_empathy_score: float = 0.5
    require_validation: bool = False

    # 증강 설정
    enable_augmentation: bool = False
    augmentation_factor: float = 1.0


# =============================================================================
# 데이터셋 클래스
# =============================================================================

class CounselingDataset:
    """심리상담 파인튜닝 데이터셋"""

    def __init__(self, config: DatasetConfig):
        self.config = config
        self.examples: List[CounselingExample] = []
        self.train_examples: List[CounselingExample] = []
        self.valid_examples: List[CounselingExample] = []
        self.test_examples: List[CounselingExample] = []

        self._stats: Dict[str, Any] = {}

    def __len__(self) -> int:
        return len(self.examples)

    def __iter__(self) -> Iterator[CounselingExample]:
        return iter(self.examples)

    def __getitem__(self, idx: int) -> CounselingExample:
        return self.examples[idx]

    def add_example(self, example: CounselingExample) -> bool:
        """예시 추가 (필터링 적용)"""
        if not self._passes_filter(example):
            return False

        self.examples.append(example)
        return True

    def _passes_filter(self, example: CounselingExample) -> bool:
        """필터 통과 여부 확인"""
        config = self.config

        # 품질 점수
        if example.quality_score < config.min_quality_score:
            return False

        # 공감 점수
        if example.empathy_score < config.min_empathy_score:
            return False

        # 턴 수
        turn_count = len(example.conversation)
        if turn_count < config.min_turns or turn_count > config.max_turns:
            return False

        # 검증 요구
        if config.require_validation and not example.validated:
            return False

        # 안전성
        if example.safety_score < 1.0:
            return False

        return True

    def load_from_jsonl(self, filepath: Union[str, Path]) -> int:
        """JSONL 파일에서 로드"""
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        loaded_count = 0
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    example = self._parse_example(data)
                    if self.add_example(example):
                        loaded_count += 1
                except Exception as e:
                    logger.warning(f"Error parsing line: {e}")

        logger.info(f"Loaded {loaded_count} examples from {filepath}")
        return loaded_count

    def _parse_example(self, data: Dict[str, Any]) -> CounselingExample:
        """JSON 데이터를 CounselingExample로 파싱"""
        # 대화 턴 파싱
        conversation = []
        for turn_data in data.get("conversation", []):
            turn = ConversationTurn(
                role=turn_data.get("role", "user"),
                content=turn_data.get("content", ""),
                emotion=turn_data.get("emotion"),
                emotion_intensity=turn_data.get("emotion_intensity", 0.0),
                crisis_level=turn_data.get("crisis_level", 0),
                technique_used=turn_data.get("technique_used")
            )
            conversation.append(turn)

        return CounselingExample(
            example_id=data.get("example_id", str(random.randint(10000, 99999))),
            conversation=conversation,
            category=data.get("category", "general"),
            primary_emotion=data.get("primary_emotion", ""),
            crisis_level=data.get("crisis_level", 0),
            techniques_used=data.get("techniques_used", []),
            quality_score=data.get("quality_score", 0.5),
            empathy_score=data.get("empathy_score", 0.5),
            safety_score=data.get("safety_score", 1.0),
            therapeutic_score=data.get("therapeutic_score", 0.5),
            source=data.get("source", ""),
            created_at=data.get("created_at", datetime.now().isoformat()),
            validated=data.get("validated", False),
            validator=data.get("validator")
        )

    def save_to_jsonl(self, filepath: Union[str, Path]) -> int:
        """JSONL 파일로 저장"""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        saved_count = 0
        with open(filepath, "w", encoding="utf-8") as f:
            for example in self.examples:
                data = self._example_to_dict(example)
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
                saved_count += 1

        logger.info(f"Saved {saved_count} examples to {filepath}")
        return saved_count

    def _example_to_dict(self, example: CounselingExample) -> Dict[str, Any]:
        """CounselingExample을 딕셔너리로 변환"""
        return {
            "example_id": example.example_id,
            "conversation": [
                {
                    "role": turn.role,
                    "content": turn.content,
                    "emotion": turn.emotion,
                    "emotion_intensity": turn.emotion_intensity,
                    "crisis_level": turn.crisis_level,
                    "technique_used": turn.technique_used
                }
                for turn in example.conversation
            ],
            "category": example.category,
            "primary_emotion": example.primary_emotion,
            "crisis_level": example.crisis_level,
            "techniques_used": example.techniques_used,
            "quality_score": example.quality_score,
            "empathy_score": example.empathy_score,
            "safety_score": example.safety_score,
            "therapeutic_score": example.therapeutic_score,
            "source": example.source,
            "created_at": example.created_at,
            "validated": example.validated,
            "validator": example.validator
        }

    def split_dataset(self, shuffle: bool = True, seed: int = 42) -> None:
        """데이터셋 분할"""
        if shuffle:
            random.seed(seed)
            examples = self.examples.copy()
            random.shuffle(examples)
        else:
            examples = self.examples

        total = len(examples)
        train_end = int(total * self.config.train_ratio)
        valid_end = train_end + int(total * self.config.valid_ratio)

        self.train_examples = examples[:train_end]
        self.valid_examples = examples[train_end:valid_end]
        self.test_examples = examples[valid_end:]

        logger.info(f"Dataset split: train={len(self.train_examples)}, "
                   f"valid={len(self.valid_examples)}, test={len(self.test_examples)}")

    def export_for_training(
        self,
        output_dir: Union[str, Path],
        format: str = "solar"
    ) -> Dict[str, str]:
        """학습용 형식으로 내보내기"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if not self.train_examples:
            self.split_dataset()

        output_paths = {}

        # 학습 데이터
        train_path = output_dir / f"train_{format}.jsonl"
        self._export_split(self.train_examples, train_path, format)
        output_paths["train"] = str(train_path)

        # 검증 데이터
        valid_path = output_dir / f"valid_{format}.jsonl"
        self._export_split(self.valid_examples, valid_path, format)
        output_paths["valid"] = str(valid_path)

        # 테스트 데이터
        test_path = output_dir / f"test_{format}.jsonl"
        self._export_split(self.test_examples, test_path, format)
        output_paths["test"] = str(test_path)

        return output_paths

    def _export_split(
        self,
        examples: List[CounselingExample],
        filepath: Path,
        format: str
    ) -> None:
        """분할 데이터 내보내기"""
        with open(filepath, "w", encoding="utf-8") as f:
            for example in examples:
                if format == "solar":
                    data = {"text": example.to_solar_format()}
                elif format == "chat":
                    data = {"messages": example.to_chat_format()}
                elif format == "instruction":
                    data = example.to_instruction_format()
                else:
                    data = self._example_to_dict(example)

                f.write(json.dumps(data, ensure_ascii=False) + "\n")

    def compute_statistics(self) -> Dict[str, Any]:
        """데이터셋 통계 계산"""
        if not self.examples:
            return {}

        stats = {
            "total_examples": len(self.examples),
            "total_turns": sum(len(e.conversation) for e in self.examples),
            "avg_turns_per_conversation": sum(len(e.conversation) for e in self.examples) / len(self.examples)
        }

        # 카테고리 분포
        category_counts = {}
        for example in self.examples:
            cat = example.category
            category_counts[cat] = category_counts.get(cat, 0) + 1
        stats["category_distribution"] = category_counts

        # 위기 레벨 분포
        crisis_counts = {}
        for example in self.examples:
            level = example.crisis_level
            crisis_counts[level] = crisis_counts.get(level, 0) + 1
        stats["crisis_level_distribution"] = crisis_counts

        # 품질 점수 통계
        quality_scores = [e.quality_score for e in self.examples]
        empathy_scores = [e.empathy_score for e in self.examples]

        stats["quality_scores"] = {
            "mean": sum(quality_scores) / len(quality_scores),
            "min": min(quality_scores),
            "max": max(quality_scores)
        }

        stats["empathy_scores"] = {
            "mean": sum(empathy_scores) / len(empathy_scores),
            "min": min(empathy_scores),
            "max": max(empathy_scores)
        }

        # 검증 상태
        validated_count = sum(1 for e in self.examples if e.validated)
        stats["validation"] = {
            "validated": validated_count,
            "unvalidated": len(self.examples) - validated_count,
            "validation_rate": validated_count / len(self.examples)
        }

        self._stats = stats
        return stats

    def get_stratified_sample(
        self,
        n: int,
        stratify_by: str = "category"
    ) -> List[CounselingExample]:
        """층화 샘플링"""
        if stratify_by == "category":
            groups = {}
            for example in self.examples:
                key = example.category
                if key not in groups:
                    groups[key] = []
                groups[key].append(example)
        elif stratify_by == "crisis_level":
            groups = {}
            for example in self.examples:
                key = example.crisis_level
                if key not in groups:
                    groups[key] = []
                groups[key].append(example)
        else:
            return random.sample(self.examples, min(n, len(self.examples)))

        # 비율 유지 샘플링
        sample = []
        total = len(self.examples)

        for key, examples in groups.items():
            group_ratio = len(examples) / total
            group_n = max(1, int(n * group_ratio))
            group_sample = random.sample(examples, min(group_n, len(examples)))
            sample.extend(group_sample)

        return sample[:n]


# =============================================================================
# 유틸리티 함수
# =============================================================================

def load_dataset(
    filepath: Union[str, Path],
    config: Optional[DatasetConfig] = None
) -> CounselingDataset:
    """데이터셋 로드"""
    if config is None:
        config = DatasetConfig(name="default")

    dataset = CounselingDataset(config)
    dataset.load_from_jsonl(filepath)
    return dataset


def create_dataset_from_conversations(
    conversations: List[Dict[str, Any]],
    config: Optional[DatasetConfig] = None,
    auto_score: bool = True
) -> CounselingDataset:
    """대화 데이터로부터 데이터셋 생성"""
    if config is None:
        config = DatasetConfig(name="generated")

    dataset = CounselingDataset(config)

    for i, conv_data in enumerate(conversations):
        example = CounselingExample(
            example_id=conv_data.get("id", f"conv_{i:05d}"),
            conversation=[
                ConversationTurn(
                    role=turn.get("role", "user"),
                    content=turn.get("content", ""),
                    emotion=turn.get("emotion"),
                    crisis_level=turn.get("crisis_level", 0)
                )
                for turn in conv_data.get("turns", [])
            ],
            category=conv_data.get("category", "general"),
            source=conv_data.get("source", "conversation_log")
        )

        if auto_score:
            # 간단한 자동 품질 점수 계산
            example.quality_score = _auto_quality_score(example)
            example.empathy_score = _auto_empathy_score(example)

        dataset.add_example(example)

    return dataset


def _auto_quality_score(example: CounselingExample) -> float:
    """자동 품질 점수 계산"""
    score = 0.5  # 기본 점수

    # 대화 길이 보너스
    turn_count = len(example.conversation)
    if 4 <= turn_count <= 10:
        score += 0.2
    elif turn_count > 10:
        score += 0.1

    # 응답 길이 체크
    assistant_turns = [t for t in example.conversation if t.role == "assistant"]
    if assistant_turns:
        avg_length = sum(len(t.content) for t in assistant_turns) / len(assistant_turns)
        if 50 <= avg_length <= 300:
            score += 0.2
        elif avg_length > 300:
            score += 0.1

    return min(1.0, score)


def _auto_empathy_score(example: CounselingExample) -> float:
    """자동 공감 점수 계산"""
    empathy_keywords = [
        "힘드시", "어려우시", "고통", "이해", "공감",
        "함께", "지지", "괜찮", "느끼시", "마음이",
        "힘이 드", "걱정이 되", "안쓰럽", "응원"
    ]

    score = 0.3  # 기본 점수
    assistant_content = " ".join(
        t.content for t in example.conversation if t.role == "assistant"
    )

    # 공감 키워드 점수
    keyword_count = sum(1 for kw in empathy_keywords if kw in assistant_content)
    score += min(0.5, keyword_count * 0.1)

    # 질문 사용 점수
    question_count = assistant_content.count("?")
    if 1 <= question_count <= 3:
        score += 0.2

    return min(1.0, score)


# =============================================================================
# 샘플 데이터 생성
# =============================================================================

def generate_sample_dataset(n: int = 10) -> CounselingDataset:
    """샘플 데이터셋 생성 (개발/테스트용)"""

    sample_conversations = [
        {
            "category": "depression",
            "turns": [
                {"role": "user", "content": "요즘 아무것도 하고 싶지 않아요. 매일 피곤하고 무기력해요."},
                {"role": "assistant", "content": "많이 힘드시겠어요. 아무것도 하고 싶지 않고 매일 피곤하고 무기력한 감정이 드신다니, 정말 지치셨을 것 같아요. 이런 감정이 언제부터 시작되었는지 여쭤봐도 될까요?"},
                {"role": "user", "content": "한 달 정도 된 것 같아요. 회사에서 일이 많아지면서부터요."},
                {"role": "assistant", "content": "한 달 동안 그런 감정을 느끼고 계셨군요. 회사 일이 많아지면서 시작되었다고 하셨는데, 그동안 정말 많이 애쓰셨을 것 같아요. 업무량이 늘어나면서 어떤 부분이 가장 힘드셨나요?"}
            ],
            "crisis_level": 1,
            "techniques_used": ["person_centered", "active_listening"]
        },
        {
            "category": "anxiety",
            "turns": [
                {"role": "user", "content": "발표만 생각하면 심장이 두근거리고 손에 땀이 나요."},
                {"role": "assistant", "content": "발표 상황을 떠올리기만 해도 심장이 두근거리고 손에 땀이 나시는군요. 그런 신체 반응이 나타나면 정말 불안하고 걱정되실 것 같아요. 발표에 대한 불안이 언제부터 있으셨나요?"},
                {"role": "user", "content": "어릴 때부터요. 학교에서 발표할 때마다 창피당한 기억이 있어서요."},
                {"role": "assistant", "content": "어린 시절부터 발표 상황에서 창피했던 경험들이 있으셨군요. 그런 기억들이 지금까지 영향을 주고 있다니, 오랫동안 마음고생을 하셨겠어요. 그때 어떤 일이 있었는지 편하게 이야기해 주실 수 있을까요?"}
            ],
            "crisis_level": 0,
            "techniques_used": ["cbt", "exploration"]
        },
        {
            "category": "relationship",
            "turns": [
                {"role": "user", "content": "친구들이 저를 싫어하는 것 같아요. 다들 저한테만 차갑게 대해요."},
                {"role": "assistant", "content": "친구들이 나에게만 차갑게 대한다고 느끼시는군요. 그런 생각이 드시면 정말 외롭고 서운하실 것 같아요. 어떤 상황에서 그런 느낌을 받으셨는지 이야기해 주실 수 있을까요?"},
                {"role": "user", "content": "단톡방에서 제 말에는 반응이 없는데 다른 사람 말에는 다들 답을 해요."},
                {"role": "assistant", "content": "단톡방에서 자신의 말에만 반응이 없는 것 같다고 느끼셨군요. 그런 상황이 반복되면 소외감을 느끼실 수 있어요. 혹시 그런 상황이 자주 있었나요, 아니면 특정 상황에서 그랬나요?"}
            ],
            "crisis_level": 0,
            "techniques_used": ["cbt", "cognitive_restructuring"]
        },
        {
            "category": "family",
            "turns": [
                {"role": "user", "content": "부모님이 항상 저한테 기대가 너무 높아요. 뭘 해도 만족을 못하세요."},
                {"role": "assistant", "content": "부모님의 높은 기대 속에서 뭘 해도 만족시키기 어렵다고 느끼시는군요. 그런 상황이 계속되면 정말 지치고 힘드실 것 같아요. 부모님의 기대 때문에 어떤 감정이 드시나요?"},
                {"role": "user", "content": "화가 나기도 하고, 저 자신이 부족한 것 같아서 자책도 해요."},
                {"role": "assistant", "content": "화도 나고 자책도 하시는군요. 두 가지 감정이 동시에 느껴지면 더 혼란스러우실 것 같아요. 분노와 자책, 어떤 감정이 더 크게 느껴지시나요?"}
            ],
            "crisis_level": 0,
            "techniques_used": ["person_centered", "emotion_exploration"]
        },
        {
            "category": "work_stress",
            "turns": [
                {"role": "user", "content": "상사가 저한테만 일을 많이 시켜요. 불공평해요."},
                {"role": "assistant", "content": "상사분이 유독 본인에게만 일을 많이 맡긴다고 느끼시는군요. 불공평하다는 생각이 드시면 답답하고 억울하실 것 같아요. 구체적으로 어떤 상황들이 있었는지 이야기해 주실 수 있을까요?"},
                {"role": "user", "content": "다른 동료들은 정시 퇴근하는데 저만 매일 야근해요."},
                {"role": "assistant", "content": "혼자만 매일 야근을 하시는 상황이 반복되고 계시는군요. 다른 동료들은 정시 퇴근하는 걸 보면서 더 불공평하다고 느끼실 것 같아요. 이런 상황에 대해 상사분께 말씀드려 보신 적이 있으신가요?"}
            ],
            "crisis_level": 0,
            "techniques_used": ["solution_focused", "assertiveness"]
        }
    ]

    # 위기 상담 예시 추가
    sample_conversations.append({
        "category": "trauma",
        "turns": [
            {"role": "user", "content": "가끔 죽고 싶다는 생각이 들어요..."},
            {"role": "assistant", "content": "죽고 싶다는 생각이 드신다고 말씀해 주셔서 감사합니다. 그런 생각을 하고 계시다니 정말 많이 힘드시겠어요. 혼자서 그런 무거운 감정을 안고 계셨을 것 같아 마음이 아프네요. 지금 안전하신 상태인가요?"},
            {"role": "user", "content": "네, 그냥 생각만 해요. 실제로 하려고 한 건 아니에요."},
            {"role": "assistant", "content": "실제로 행동으로 옮기려 한 건 아니라고 하셨네요. 솔직하게 말씀해 주셔서 감사해요. 그런 생각이 드실 때 특히 힘든 상황이 있으신가요? 그리고 만약 그런 생각이 더 강해지면, 자살예방상담전화 1393이나 정신건강위기상담전화 1577-0199로 연락해 주세요. 24시간 상담 가능합니다."}
        ],
        "crisis_level": 3,
        "techniques_used": ["crisis_intervention", "safety_planning"]
    })

    config = DatasetConfig(
        name="sample_dataset",
        min_quality_score=0.0,  # 샘플이므로 필터 완화
        min_empathy_score=0.0
    )

    dataset = CounselingDataset(config)

    for i, conv_data in enumerate(sample_conversations[:n]):
        example = CounselingExample(
            example_id=f"sample_{i:03d}",
            conversation=[
                ConversationTurn(
                    role=turn["role"],
                    content=turn["content"]
                )
                for turn in conv_data["turns"]
            ],
            category=conv_data["category"],
            crisis_level=conv_data.get("crisis_level", 0),
            techniques_used=conv_data.get("techniques_used", []),
            quality_score=0.8,
            empathy_score=0.7,
            safety_score=1.0,
            source="sample_generator",
            created_at=datetime.now().isoformat()
        )
        dataset.add_example(example)

    return dataset
