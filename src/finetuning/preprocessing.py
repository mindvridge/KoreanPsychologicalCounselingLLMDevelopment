"""
데이터 전처리 및 품질 필터링
Data Preprocessing and Quality Filtering

기능:
- 텍스트 정규화 및 정제
- 품질 필터링
- 데이터 증강
- 개인정보 마스킹
"""

import re
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

from .dataset import (
    CounselingExample,
    ConversationTurn,
    CounselingDataset,
    DatasetConfig
)

logger = logging.getLogger(__name__)


# =============================================================================
# 텍스트 정제
# =============================================================================

class TextCleaner:
    """텍스트 정제 유틸리티"""

    # 정규화 패턴
    PATTERNS = {
        "multiple_spaces": (r"\s+", " "),
        "multiple_newlines": (r"\n{3,}", "\n\n"),
        "special_chars": (r"[^\w\s\.,!?\-\(\)\'\"가-힣ㄱ-ㅎㅏ-ㅣ]", ""),
        "url": (r"https?://\S+|www\.\S+", "[URL]"),
        "email": (r"[\w\.-]+@[\w\.-]+\.\w+", "[EMAIL]"),
    }

    # 개인정보 패턴
    PII_PATTERNS = {
        "phone": (r"\d{2,3}[-.\s]?\d{3,4}[-.\s]?\d{4}", "[전화번호]"),
        "resident_id": (r"\d{6}[-]?\d{7}", "[주민등록번호]"),
        "card_number": (r"\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}", "[카드번호]"),
        "account_number": (r"\d{3,6}[-]?\d{2,6}[-]?\d{2,6}", "[계좌번호]"),
        "name_pattern": (r"(제?\s?이름은?\s?)[가-힣]{2,4}(이에요|입니다|예요|이야)", r"\1[이름]\2"),
        "address": (r"(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)[시도]?\s*[가-힣]+[시군구]\s*[가-힣]+[동읍면로길]\s*\d*", "[주소]"),
    }

    @classmethod
    def clean_text(
        cls,
        text: str,
        normalize_whitespace: bool = True,
        remove_urls: bool = True,
        mask_pii: bool = True
    ) -> str:
        """텍스트 정제"""
        if not text:
            return ""

        result = text.strip()

        # URL 제거
        if remove_urls:
            result = re.sub(cls.PATTERNS["url"][0], cls.PATTERNS["url"][1], result)
            result = re.sub(cls.PATTERNS["email"][0], cls.PATTERNS["email"][1], result)

        # 개인정보 마스킹
        if mask_pii:
            for pattern_name, (pattern, replacement) in cls.PII_PATTERNS.items():
                result = re.sub(pattern, replacement, result)

        # 공백 정규화
        if normalize_whitespace:
            result = re.sub(cls.PATTERNS["multiple_spaces"][0], cls.PATTERNS["multiple_spaces"][1], result)
            result = re.sub(cls.PATTERNS["multiple_newlines"][0], cls.PATTERNS["multiple_newlines"][1], result)

        return result.strip()

    @classmethod
    def normalize_korean(cls, text: str) -> str:
        """한국어 정규화"""
        # 자음/모음 반복 줄이기 (예: ㅋㅋㅋㅋㅋ -> ㅋㅋ)
        result = re.sub(r"([ㄱ-ㅎㅏ-ㅣ])\1{2,}", r"\1\1", text)

        # 글자 반복 줄이기 (예: 감사합니다다다 -> 감사합니다)
        result = re.sub(r"(.)\1{3,}", r"\1\1", result)

        # 물음표/느낌표 반복 줄이기
        result = re.sub(r"[!]{2,}", "!", result)
        result = re.sub(r"[?]{2,}", "?", result)

        return result


# =============================================================================
# 품질 필터링
# =============================================================================

@dataclass
class QualityCheckResult:
    """품질 검사 결과"""
    passed: bool
    score: float
    issues: List[str]
    suggestions: List[str]


class QualityFilter:
    """품질 필터"""

    def __init__(
        self,
        min_user_length: int = 5,
        min_assistant_length: int = 20,
        max_length: int = 2000,
        min_turns: int = 2,
        max_turns: int = 50
    ):
        self.min_user_length = min_user_length
        self.min_assistant_length = min_assistant_length
        self.max_length = max_length
        self.min_turns = min_turns
        self.max_turns = max_turns

        # 품질 저하 패턴
        self.low_quality_patterns = [
            r"^(네|예|아니요|응|어)$",  # 너무 짧은 응답
            r"^\?+$",  # 물음표만
            r"^\.+$",  # 점만
            r"(ㅋ|ㅎ|ㅠ|ㅜ){5,}",  # 과도한 자음 반복
        ]

        # 유해 콘텐츠 패턴
        self.harmful_patterns = [
            r"자살\s*방법",
            r"죽는\s*법",
            r"약물\s*과다",
            r"자해\s*방법",
        ]

        # 필수 공감 표현 (상담사 응답용)
        self.empathy_markers = [
            "힘드", "어려우", "고통", "이해", "공감", "느끼",
            "마음", "걱정", "힘이", "지치", "고생", "애쓰"
        ]

    def check_quality(self, example: CounselingExample) -> QualityCheckResult:
        """품질 검사"""
        issues = []
        suggestions = []
        score = 1.0

        # 1. 턴 수 검사
        turn_count = len(example.conversation)
        if turn_count < self.min_turns:
            issues.append(f"대화 턴이 너무 적음 ({turn_count} < {self.min_turns})")
            score -= 0.3
        elif turn_count > self.max_turns:
            issues.append(f"대화 턴이 너무 많음 ({turn_count} > {self.max_turns})")
            suggestions.append("대화를 여러 예시로 분할하세요")
            score -= 0.1

        # 2. 응답 길이 검사
        for turn in example.conversation:
            content_length = len(turn.content)

            if turn.role == "user" and content_length < self.min_user_length:
                issues.append(f"사용자 메시지가 너무 짧음: '{turn.content[:50]}...'")
                score -= 0.1

            if turn.role == "assistant":
                if content_length < self.min_assistant_length:
                    issues.append(f"상담사 응답이 너무 짧음: '{turn.content[:50]}...'")
                    score -= 0.2
                elif content_length > self.max_length:
                    issues.append(f"상담사 응답이 너무 김 ({content_length} > {self.max_length})")
                    suggestions.append("응답을 간결하게 수정하세요")
                    score -= 0.1

        # 3. 저품질 패턴 검사
        for turn in example.conversation:
            for pattern in self.low_quality_patterns:
                if re.match(pattern, turn.content):
                    issues.append(f"저품질 패턴 감지: '{turn.content[:30]}'")
                    score -= 0.15

        # 4. 유해 콘텐츠 검사
        full_text = " ".join(t.content for t in example.conversation)
        for pattern in self.harmful_patterns:
            if re.search(pattern, full_text):
                issues.append(f"유해 콘텐츠 패턴 감지")
                score = 0.0  # 즉시 실격
                break

        # 5. 공감 표현 검사 (상담사 응답)
        assistant_text = " ".join(
            t.content for t in example.conversation if t.role == "assistant"
        )
        empathy_count = sum(1 for marker in self.empathy_markers if marker in assistant_text)
        if empathy_count == 0:
            issues.append("공감 표현이 부족함")
            suggestions.append("공감적 언어를 추가하세요")
            score -= 0.2
        elif empathy_count >= 3:
            score = min(1.0, score + 0.1)  # 보너스

        # 6. 대화 흐름 검사
        if not self._check_conversation_flow(example):
            issues.append("대화 흐름이 자연스럽지 않음")
            score -= 0.15

        # 7. 위기 상담 시 안전 정보 검사
        if example.crisis_level >= 3:
            if not self._has_safety_info(assistant_text):
                issues.append("위기 상담에 안전 정보(상담 전화)가 누락됨")
                suggestions.append("1393, 1577-0199 등 상담 전화 안내를 추가하세요")
                score -= 0.3

        # 최종 점수 조정
        score = max(0.0, min(1.0, score))
        passed = score >= 0.6 and len([i for i in issues if "유해" in i]) == 0

        return QualityCheckResult(
            passed=passed,
            score=score,
            issues=issues,
            suggestions=suggestions
        )

    def _check_conversation_flow(self, example: CounselingExample) -> bool:
        """대화 흐름 검사"""
        turns = example.conversation

        # user/assistant 교대 확인
        for i in range(1, len(turns)):
            if turns[i].role == turns[i-1].role:
                # 같은 역할이 연속되면 비정상
                return False

        # 첫 턴이 user인지 확인
        if turns and turns[0].role != "user":
            return False

        return True

    def _has_safety_info(self, text: str) -> bool:
        """안전 정보 포함 여부"""
        safety_keywords = [
            "1393", "1577-0199", "자살예방", "정신건강",
            "상담전화", "위기상담", "전문가", "병원"
        ]
        return any(kw in text for kw in safety_keywords)

    def filter_dataset(
        self,
        dataset: CounselingDataset,
        min_score: float = 0.6
    ) -> Tuple[CounselingDataset, List[Tuple[CounselingExample, QualityCheckResult]]]:
        """데이터셋 필터링"""
        passed_config = DatasetConfig(
            name=f"{dataset.config.name}_filtered",
            min_quality_score=0.0  # 이미 필터링됨
        )
        passed_dataset = CounselingDataset(passed_config)
        rejected = []

        for example in dataset:
            result = self.check_quality(example)

            if result.passed and result.score >= min_score:
                example.quality_score = result.score
                passed_dataset.add_example(example)
            else:
                rejected.append((example, result))

        logger.info(f"Filtering complete: {len(passed_dataset)} passed, {len(rejected)} rejected")
        return passed_dataset, rejected


# =============================================================================
# 데이터 증강
# =============================================================================

class DataAugmentor:
    """데이터 증강"""

    def __init__(self):
        # 동의어 사전
        self.synonyms = {
            "힘들어요": ["지쳐요", "고통스러워요", "버거워요", "어려워요"],
            "슬퍼요": ["우울해요", "눈물이 나요", "마음이 아파요"],
            "화나요": ["짜증나요", "분노해요", "열받아요"],
            "불안해요": ["걱정돼요", "두려워요", "초조해요"],
            "외로워요": ["쓸쓸해요", "고독해요", "혼자인 것 같아요"],
            "무기력해요": ["의욕이 없어요", "아무것도 하기 싫어요", "힘이 없어요"],
        }

        # 상담사 응답 변형 패턴
        self.response_variations = {
            "힘드시겠어요": ["많이 지치셨겠어요", "고통스러우시겠어요", "버거우시겠어요"],
            "이해해요": ["충분히 그러실 수 있어요", "그런 감정이 드시는 게 당연해요"],
            "말씀해 주셔서 감사해요": ["나눠주셔서 고마워요", "이야기해 주셔서 감사합니다"],
        }

        # 문장 끝 변형
        self.ending_variations = {
            "~네요": ["~군요", "~시네요"],
            "~을까요?": ["~실까요?", "~셨을까요?"],
            "~해요": ["~합니다", "~하시네요"],
        }

    def augment_example(
        self,
        example: CounselingExample,
        num_variations: int = 1
    ) -> List[CounselingExample]:
        """예시 증강"""
        augmented = []

        for i in range(num_variations):
            new_conversation = []

            for turn in example.conversation:
                new_content = turn.content

                # 동의어 치환
                if random.random() < 0.3:
                    new_content = self._apply_synonym_replacement(new_content)

                # 문장 끝 변형
                if random.random() < 0.2:
                    new_content = self._apply_ending_variation(new_content)

                # 상담사 응답 변형
                if turn.role == "assistant" and random.random() < 0.3:
                    new_content = self._apply_response_variation(new_content)

                new_turn = ConversationTurn(
                    role=turn.role,
                    content=new_content,
                    emotion=turn.emotion,
                    emotion_intensity=turn.emotion_intensity,
                    crisis_level=turn.crisis_level,
                    technique_used=turn.technique_used
                )
                new_conversation.append(new_turn)

            augmented_example = CounselingExample(
                example_id=f"{example.example_id}_aug{i+1}",
                conversation=new_conversation,
                category=example.category,
                primary_emotion=example.primary_emotion,
                crisis_level=example.crisis_level,
                techniques_used=example.techniques_used,
                quality_score=example.quality_score * 0.95,  # 약간 낮은 점수
                empathy_score=example.empathy_score,
                safety_score=example.safety_score,
                therapeutic_score=example.therapeutic_score,
                source=f"{example.source}_augmented",
                created_at=datetime.now().isoformat(),
                validated=False
            )
            augmented.append(augmented_example)

        return augmented

    def _apply_synonym_replacement(self, text: str) -> str:
        """동의어 치환"""
        result = text
        for word, synonyms in self.synonyms.items():
            if word in result:
                replacement = random.choice(synonyms)
                result = result.replace(word, replacement, 1)
                break
        return result

    def _apply_ending_variation(self, text: str) -> str:
        """문장 끝 변형"""
        result = text
        for ending, variations in self.ending_variations.items():
            if ending in result:
                replacement = random.choice(variations)
                result = result.replace(ending, replacement, 1)
                break
        return result

    def _apply_response_variation(self, text: str) -> str:
        """응답 변형"""
        result = text
        for phrase, variations in self.response_variations.items():
            if phrase in result:
                replacement = random.choice(variations)
                result = result.replace(phrase, replacement, 1)
                break
        return result

    def augment_dataset(
        self,
        dataset: CounselingDataset,
        augmentation_factor: float = 1.0,
        balance_categories: bool = True
    ) -> CounselingDataset:
        """데이터셋 증강"""
        augmented_config = DatasetConfig(
            name=f"{dataset.config.name}_augmented",
            min_quality_score=0.0
        )
        augmented_dataset = CounselingDataset(augmented_config)

        # 원본 데이터 추가
        for example in dataset:
            augmented_dataset.add_example(example)

        # 카테고리 균형 맞추기
        if balance_categories:
            category_counts = {}
            for example in dataset:
                cat = example.category
                category_counts[cat] = category_counts.get(cat, 0) + 1

            max_count = max(category_counts.values()) if category_counts else 0

            for example in dataset:
                cat = example.category
                if category_counts.get(cat, 0) < max_count:
                    # 부족한 카테고리 증강
                    needed = int((max_count - category_counts[cat]) * augmentation_factor)
                    needed = min(needed, 3)  # 최대 3개까지

                    augmented_examples = self.augment_example(example, needed)
                    for aug_ex in augmented_examples:
                        augmented_dataset.add_example(aug_ex)
        else:
            # 일반 증강
            for example in dataset:
                num_aug = int(augmentation_factor)
                augmented_examples = self.augment_example(example, num_aug)
                for aug_ex in augmented_examples:
                    augmented_dataset.add_example(aug_ex)

        logger.info(f"Augmentation complete: {len(dataset)} -> {len(augmented_dataset)} examples")
        return augmented_dataset


# =============================================================================
# 전처리 파이프라인
# =============================================================================

class DataPreprocessor:
    """데이터 전처리 파이프라인"""

    def __init__(
        self,
        clean_text: bool = True,
        mask_pii: bool = True,
        normalize_korean: bool = True,
        filter_quality: bool = True,
        augment: bool = False,
        augmentation_factor: float = 1.0
    ):
        self.clean_text = clean_text
        self.mask_pii = mask_pii
        self.normalize_korean = normalize_korean
        self.filter_quality = filter_quality
        self.augment = augment
        self.augmentation_factor = augmentation_factor

        self.quality_filter = QualityFilter()
        self.augmentor = DataAugmentor()

        self._stats = {
            "input_count": 0,
            "output_count": 0,
            "filtered_count": 0,
            "augmented_count": 0
        }

    def process(
        self,
        dataset: CounselingDataset,
        min_quality_score: float = 0.6
    ) -> CounselingDataset:
        """전처리 파이프라인 실행"""
        self._stats["input_count"] = len(dataset)

        # 1. 텍스트 정제
        if self.clean_text or self.mask_pii or self.normalize_korean:
            dataset = self._clean_dataset(dataset)

        # 2. 품질 필터링
        if self.filter_quality:
            dataset, rejected = self.quality_filter.filter_dataset(
                dataset, min_score=min_quality_score
            )
            self._stats["filtered_count"] = len(rejected)

        # 3. 데이터 증강
        if self.augment:
            original_count = len(dataset)
            dataset = self.augmentor.augment_dataset(
                dataset, self.augmentation_factor
            )
            self._stats["augmented_count"] = len(dataset) - original_count

        self._stats["output_count"] = len(dataset)
        return dataset

    def _clean_dataset(self, dataset: CounselingDataset) -> CounselingDataset:
        """데이터셋 텍스트 정제"""
        for example in dataset.examples:
            for turn in example.conversation:
                # 텍스트 정제
                if self.clean_text:
                    turn.content = TextCleaner.clean_text(
                        turn.content,
                        normalize_whitespace=True,
                        remove_urls=True,
                        mask_pii=self.mask_pii
                    )

                # 한국어 정규화
                if self.normalize_korean:
                    turn.content = TextCleaner.normalize_korean(turn.content)

        return dataset

    def get_stats(self) -> Dict[str, Any]:
        """전처리 통계 반환"""
        return self._stats.copy()


# =============================================================================
# 유틸리티 함수
# =============================================================================

def preprocess_conversation(
    conversation: List[Dict[str, str]],
    mask_pii: bool = True
) -> List[Dict[str, str]]:
    """단일 대화 전처리"""
    processed = []

    for turn in conversation:
        content = turn.get("content", "")

        # 텍스트 정제
        content = TextCleaner.clean_text(
            content,
            normalize_whitespace=True,
            mask_pii=mask_pii
        )
        content = TextCleaner.normalize_korean(content)

        processed.append({
            "role": turn.get("role", "user"),
            "content": content
        })

    return processed


def augment_data(
    examples: List[CounselingExample],
    num_variations: int = 1
) -> List[CounselingExample]:
    """데이터 증강"""
    augmentor = DataAugmentor()
    augmented = []

    for example in examples:
        augmented.extend(augmentor.augment_example(example, num_variations))

    return augmented


def validate_dataset_quality(dataset: CounselingDataset) -> Dict[str, Any]:
    """데이터셋 품질 검증"""
    quality_filter = QualityFilter()

    results = {
        "total": len(dataset),
        "passed": 0,
        "failed": 0,
        "avg_score": 0.0,
        "issues_summary": {},
        "score_distribution": {
            "excellent": 0,  # 0.9+
            "good": 0,       # 0.7-0.9
            "fair": 0,       # 0.6-0.7
            "poor": 0        # < 0.6
        }
    }

    scores = []
    all_issues = []

    for example in dataset:
        check_result = quality_filter.check_quality(example)
        scores.append(check_result.score)

        if check_result.passed:
            results["passed"] += 1
        else:
            results["failed"] += 1

        all_issues.extend(check_result.issues)

        # 점수 분포
        if check_result.score >= 0.9:
            results["score_distribution"]["excellent"] += 1
        elif check_result.score >= 0.7:
            results["score_distribution"]["good"] += 1
        elif check_result.score >= 0.6:
            results["score_distribution"]["fair"] += 1
        else:
            results["score_distribution"]["poor"] += 1

    results["avg_score"] = sum(scores) / len(scores) if scores else 0

    # 이슈 요약
    for issue in all_issues:
        key = issue.split(":")[0] if ":" in issue else issue
        results["issues_summary"][key] = results["issues_summary"].get(key, 0) + 1

    return results
