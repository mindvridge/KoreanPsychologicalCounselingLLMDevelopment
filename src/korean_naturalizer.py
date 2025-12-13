"""
한국어 자연스러움 향상 모듈 (Korean Naturalizer)
자연스러운 한국어 상담 응답을 위한 후처리 시스템

기능:
- 번역투 제거
- 문어체 → 구어체 변환
- 어미 다양화
- 자연스러운 추임새/감탄사 추가
- 문장 호흡 최적화
- 반복 표현 제거
"""

import re
import random
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class NaturalizationResult:
    """자연스러움 변환 결과"""
    original: str
    naturalized: str
    changes_made: List[str]
    naturalness_score: float  # 0-1


class KoreanNaturalizer:
    """
    한국어 자연스러움 향상기

    LLM 응답을 더 자연스러운 한국어 구어체로 변환합니다.
    """

    def __init__(self):
        # 번역투 → 자연스러운 표현
        self.translation_fixes = {
            # 과도한 수동태/번역투
            "그것은 ": "",
            "이것은 ": "",
            "그것이 ": "",
            "~인 것 같습니다": "~인 것 같아요",
            "~하는 것이 좋겠습니다": "~해보시는 건 어떨까요",
            "~할 수 있을 것입니다": "~하실 수 있을 거예요",
            "~해야 합니다": "~하시면 좋을 것 같아요",
            "~라고 생각됩니다": "~인 것 같아요",
            "~하시기 바랍니다": "~해 주세요",
            "당신은 ": "",
            "귀하는 ": "",
            "귀하의 ": "",

            # 문어체 → 구어체
            "~습니다만": "~지만요",
            "~이지만": "~인데",
            "~입니다만": "~인데요",
            "그러하므로": "그래서",
            "그러나": "하지만",
            "따라서": "그래서",
            "또한": "그리고",
            "매우": "정말",
            "매우 ": "정말 ",
            "대단히": "정말",
            "상당히": "꽤",
        }

        # 어미 다양화 (같은 어미 반복 방지)
        self.ending_variations = {
            "것 같아요": [
                "것 같아요", "듯해요", "것 같네요", "거예요", "느낌이에요"
            ],
            "군요": [
                "군요", "네요", "시네요", "구나요"
            ],
            "어요": [
                "어요", "죠", "네요", "요"
            ],
        }

        # 자연스러운 감탄사/추임새
        self.empathy_interjections = {
            "pain": ["아...", "아휴...", "에휴...", "음..."],
            "surprise": ["어머나...", "아...", "그랬군요..."],
            "understanding": ["네...", "음...", "그렇군요..."],
            "concern": ["아이고...", "에고...", "저런..."],
        }

        # 공감 강화 표현
        self.empathy_enhancers = {
            "힘드셨": ["정말 ", "많이 ", "얼마나 "],
            "걱정되": ["많이 ", "정말 "],
            "속상하": ["많이 ", "정말 "],
            "화가 나": ["정말 ", "많이 "],
        }

        # 문장 연결사 다양화
        self.connectors = {
            "그리고": ["그리고", "또", "게다가"],
            "그래서": ["그래서", "그러니까", "그러다 보니"],
            "하지만": ["하지만", "그런데", "다만"],
        }

        # 부자연스러운 반복 패턴
        self.repetition_patterns = [
            (r"(것 같아요\.?\s*){2,}", "것 같아요. "),
            (r"(네요\.?\s*){2,}", "네요. "),
            (r"(어요\.?\s*){2,}", "어요. "),
        ]

        logger.info("KoreanNaturalizer initialized")

    def naturalize(
        self,
        text: str,
        emotion_context: Optional[str] = None,
        add_interjection: bool = True
    ) -> NaturalizationResult:
        """
        텍스트 자연스러움 향상

        Args:
            text: 원본 텍스트
            emotion_context: 감정 맥락 (pain, surprise 등)
            add_interjection: 추임새 추가 여부

        Returns:
            NaturalizationResult: 변환 결과
        """
        original = text
        changes = []
        result = text

        # 1. 번역투 수정
        result, translation_changes = self._fix_translation_style(result)
        changes.extend(translation_changes)

        # 2. 어미 다양화
        result, ending_changes = self._diversify_endings(result)
        changes.extend(ending_changes)

        # 3. 반복 표현 제거
        result, repetition_changes = self._remove_repetitions(result)
        changes.extend(repetition_changes)

        # 4. 공감 표현 강화
        result, empathy_changes = self._enhance_empathy(result)
        changes.extend(empathy_changes)

        # 5. 감탄사 추가 (선택적)
        if add_interjection and emotion_context:
            result, interjection_changes = self._add_interjection(
                result, emotion_context
            )
            changes.extend(interjection_changes)

        # 6. 문장 호흡 최적화
        result, flow_changes = self._optimize_flow(result)
        changes.extend(flow_changes)

        # 자연스러움 점수 계산
        naturalness = self._calculate_naturalness(result)

        return NaturalizationResult(
            original=original,
            naturalized=result,
            changes_made=changes,
            naturalness_score=naturalness
        )

    def _fix_translation_style(self, text: str) -> Tuple[str, List[str]]:
        """번역투 수정"""
        changes = []
        result = text

        for old, new in self.translation_fixes.items():
            if old in result:
                result = result.replace(old, new)
                if new:
                    changes.append(f"번역투 수정: '{old}' → '{new}'")
                else:
                    changes.append(f"불필요 표현 제거: '{old}'")

        return result, changes

    def _diversify_endings(self, text: str) -> Tuple[str, List[str]]:
        """어미 다양화 (같은 어미 연속 사용 방지)"""
        changes = []
        sentences = re.split(r'(?<=[.!?])\s+', text)

        if len(sentences) < 2:
            return text, changes

        # 연속된 문장에서 같은 어미 패턴 감지
        for i in range(1, len(sentences)):
            prev_sentence = sentences[i - 1]
            curr_sentence = sentences[i]

            for ending, variations in self.ending_variations.items():
                if prev_sentence.rstrip('.!?').endswith(ending.rstrip('.')):
                    if curr_sentence.rstrip('.!?').endswith(ending.rstrip('.')):
                        # 같은 어미가 연속됨 → 변경
                        alt_endings = [v for v in variations if v != ending]
                        if alt_endings:
                            new_ending = random.choice(alt_endings)
                            # 문장 끝 어미 교체
                            old_ending = ending.rstrip('.')
                            new_end = new_ending.rstrip('.')
                            if curr_sentence.endswith(old_ending + "."):
                                sentences[i] = curr_sentence[:-len(old_ending)-1] + new_end + "."
                                changes.append(f"어미 다양화: '{old_ending}' → '{new_end}'")

        return ' '.join(sentences), changes

    def _remove_repetitions(self, text: str) -> Tuple[str, List[str]]:
        """반복 표현 제거"""
        changes = []
        result = text

        for pattern, replacement in self.repetition_patterns:
            if re.search(pattern, result):
                result = re.sub(pattern, replacement, result)
                changes.append(f"반복 표현 제거")

        return result, changes

    def _enhance_empathy(self, text: str) -> Tuple[str, List[str]]:
        """공감 표현 강화"""
        changes = []
        result = text

        for keyword, enhancers in self.empathy_enhancers.items():
            # 이미 강화 표현이 있으면 스킵
            if any(e + keyword in result for e in enhancers):
                continue

            if keyword in result:
                # 앞에 강화 표현이 없으면 추가
                pattern = rf'(?<![정말|많이|얼마나|너무]\s){keyword}'
                if re.search(pattern, result):
                    enhancer = random.choice(enhancers)
                    result = re.sub(pattern, enhancer + keyword, result, count=1)
                    changes.append(f"공감 강화: '{enhancer}{keyword}'")

        return result, changes

    def _add_interjection(
        self,
        text: str,
        emotion_context: str
    ) -> Tuple[str, List[str]]:
        """감탄사/추임새 추가"""
        changes = []

        # 이미 감탄사로 시작하면 스킵
        if text.startswith(("아", "어", "네", "음", "에", "저")):
            return text, changes

        # 감정 맥락에 맞는 감탄사 선택
        interjections = self.empathy_interjections.get(
            emotion_context,
            self.empathy_interjections["understanding"]
        )

        if interjections and random.random() > 0.3:  # 70% 확률로 추가
            interjection = random.choice(interjections)
            text = interjection + " " + text
            changes.append(f"감탄사 추가: '{interjection}'")

        return text, changes

    def _optimize_flow(self, text: str) -> Tuple[str, List[str]]:
        """문장 호흡 최적화"""
        changes = []

        # 너무 긴 문장 분리 (80자 이상)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        optimized = []

        for sentence in sentences:
            if len(sentence) > 80 and ", " in sentence:
                # 쉼표에서 문장 분리 시도
                parts = sentence.split(", ", 1)
                if len(parts) == 2 and len(parts[0]) > 20:
                    # 첫 부분에 적절한 어미 추가
                    first = parts[0].rstrip(',') + "."
                    second = parts[1]
                    # 두 번째 부분 시작 정리
                    if second and second[0].islower():
                        second = second[0].upper() + second[1:]
                    optimized.append(first)
                    optimized.append(second)
                    changes.append("긴 문장 분리")
                    continue

            optimized.append(sentence)

        return ' '.join(optimized), changes

    def _calculate_naturalness(self, text: str) -> float:
        """자연스러움 점수 계산"""
        score = 1.0

        # 번역투 표현 감점
        translation_patterns = [
            "그것은", "이것은", "당신은", "~입니다만",
            "~하시기 바랍니다", "~해야 합니다"
        ]
        for pattern in translation_patterns:
            if pattern in text:
                score -= 0.1

        # 같은 어미 반복 감점
        endings = re.findall(r'([요네죠])[.!?]', text)
        if endings and len(endings) >= 3:
            unique_ratio = len(set(endings)) / len(endings)
            if unique_ratio < 0.5:
                score -= 0.15

        # 문장 길이 적절성
        sentences = re.split(r'[.!?]', text)
        avg_length = sum(len(s) for s in sentences) / max(len(sentences), 1)
        if avg_length > 60:
            score -= 0.1
        elif avg_length < 10:
            score -= 0.05

        # 공감 표현 존재 가점
        empathy_markers = ["힘드", "걱정", "마음", "느끼", "이해"]
        for marker in empathy_markers:
            if marker in text:
                score += 0.03

        return max(0, min(1, score))


class ConversationalStyleGuide:
    """
    대화체 스타일 가이드

    상담 맥락에 맞는 자연스러운 한국어 대화체 지침
    """

    def __init__(self):
        # 선호하는 어미 (구어체)
        self.preferred_endings = {
            "statements": [
                "~네요", "~군요", "~거든요", "~잖아요",
                "~더라고요", "~하더라고요"
            ],
            "questions": [
                "~세요?", "~실까요?", "~신가요?",
                "~어요?", "~죠?"
            ],
            "empathy": [
                "~셨군요", "~셨겠어요", "~시겠어요",
                "~하셨네요"
            ]
        }

        # 피해야 할 표현
        self.avoid_expressions = [
            # 권위적/지시적
            "~해야 합니다", "~하세요", "~하십시오",
            "반드시", "꼭", "무조건",

            # 판단적
            "잘못", "틀렸", "문제가 있",

            # 피상적 위로
            "힘내세요", "괜찮아질 거예요", "화이팅",

            # 번역투
            "그것은", "당신은", "귀하는"
        ]

        # 문장 시작 패턴
        self.good_starters = {
            "empathy": [
                "정말 ", "많이 ", "아, ", "네, ",
                "그러셨군요. ", "힘드셨겠어요. "
            ],
            "exploration": [
                "혹시 ", "그때 ", "어떤 ", "무엇이 "
            ],
            "support": [
                "조금이라도 ", "함께 ", "천천히 "
            ]
        }

    def get_style_prompt(self) -> str:
        """스타일 가이드 프롬프트 생성"""
        return """
## 한국어 대화체 스타일 가이드

### 선호하는 표현
- 어미: ~네요, ~군요, ~거든요, ~셨겠어요
- 시작: "정말", "많이", "아, ", "그러셨군요"
- 질문: ~세요?, ~실까요?, ~신가요?

### 피해야 할 표현
- 권위적: ~해야 합니다, ~하세요, 반드시
- 판단적: 잘못, 틀렸, 문제가 있
- 피상적: 힘내세요, 괜찮아질 거예요
- 번역투: 그것은, 당신은

### 예시
❌ "그것은 매우 힘든 상황입니다. 당신은 강해야 합니다."
✅ "정말 힘드셨겠어요. 지금 느끼시는 감정이 당연한 거예요."

❌ "걱정하지 마세요. 다 잘 될 것입니다."
✅ "많이 걱정되시죠. 그 마음이 충분히 이해돼요."
"""


class ResponsePolisher:
    """
    응답 다듬기 (Final Polish)

    최종 응답의 품질을 마무리하는 후처리기
    """

    def __init__(self):
        self.naturalizer = KoreanNaturalizer()
        self.style_guide = ConversationalStyleGuide()

    def polish(
        self,
        response: str,
        emotion: Optional[str] = None,
        turn_count: int = 0
    ) -> Dict[str, Any]:
        """
        응답 최종 다듬기

        Args:
            response: 원본 응답
            emotion: 감지된 감정
            turn_count: 대화 턴 수

        Returns:
            Dict: 다듬어진 응답과 메타데이터
        """
        # 감정 맥락 결정
        emotion_context = self._map_emotion_context(emotion)

        # 자연스러움 향상
        result = self.naturalizer.naturalize(
            response,
            emotion_context=emotion_context,
            add_interjection=(turn_count < 5)  # 초반에만 감탄사
        )

        # 최종 정리
        final = self._final_cleanup(result.naturalized)

        return {
            "response": final,
            "original": response,
            "naturalness_score": result.naturalness_score,
            "changes": result.changes_made,
            "emotion_context": emotion_context
        }

    def _map_emotion_context(self, emotion: Optional[str]) -> str:
        """감정을 맥락으로 매핑"""
        if not emotion:
            return "understanding"

        mapping = {
            "우울": "pain",
            "슬픔": "pain",
            "불안": "concern",
            "걱정": "concern",
            "분노": "understanding",
            "화": "understanding",
            "기쁨": "surprise",
            "스트레스": "concern",
        }

        return mapping.get(emotion, "understanding")

    def _final_cleanup(self, text: str) -> str:
        """최종 정리"""
        # 다중 공백 제거
        text = re.sub(r'\s+', ' ', text)

        # 문장 끝 정리
        text = re.sub(r'\s+([.!?])', r'\1', text)

        # 마침표 중복 제거
        text = re.sub(r'\.{2,}', '.', text)

        # 앞뒤 공백 제거
        text = text.strip()

        return text


# =============================================================================
# 프롬프트 자연스러움 지시문 생성기
# =============================================================================

def get_naturalness_instruction() -> str:
    """자연스러움 향상을 위한 시스템 프롬프트 지시문"""
    return """
## 한국어 자연스러움 지침

### 필수 규칙
1. **번역투 금지**: "그것은", "당신은", "~입니다만" 등 번역체 표현 사용하지 않기
2. **구어체 사용**: 문어체보다 자연스러운 구어체 선호
   - ❌ "~하는 것이 좋겠습니다" → ✅ "~해보시는 건 어떨까요"
   - ❌ "~해야 합니다" → ✅ "~하시면 좋을 것 같아요"

3. **어미 다양화**: 같은 어미 연속 사용 피하기
   - ~요, ~죠, ~네요, ~거든요 등 다양하게

4. **공감 표현 강화**:
   - "힘드셨겠어요" 보다 "정말 많이 힘드셨겠어요"
   - 앞에 "정말", "많이", "얼마나" 등 강조어 사용

5. **자연스러운 흐름**:
   - 짧은 문장 선호 (50자 내외)
   - 적절한 호흡과 쉼표 사용
   - 때때로 "아..." "네..." 같은 추임새 사용 가능

### 피해야 할 표현
- 권위적: "~해야 합니다", "반드시", "꼭"
- 판단적: "잘못", "틀렸다", "문제"
- 피상적 위로: "힘내세요", "괜찮아질 거예요", "화이팅"
- 진단적: "~증상", "~장애", "치료가 필요"

### 예시
❌ "당신의 감정은 이해됩니다. 그것은 자연스러운 반응입니다. 힘내세요."
✅ "정말 많이 힘드셨겠어요. 그런 상황에서 그렇게 느끼시는 건 당연한 거예요."
"""


# =============================================================================
# 테스트 함수
# =============================================================================

def test_naturalizer():
    """자연스러움 변환 테스트"""
    naturalizer = KoreanNaturalizer()
    polisher = ResponsePolisher()

    test_cases = [
        {
            "text": "그것은 매우 힘든 상황입니다. 당신은 힘드셨을 것입니다. 힘내세요.",
            "emotion": "우울"
        },
        {
            "text": "걱정하지 마세요. 다 잘 될 것입니다. 당신은 강합니다.",
            "emotion": "불안"
        },
        {
            "text": "힘드셨군요. 힘드셨군요. 정말 힘드셨겠어요.",
            "emotion": "우울"
        },
        {
            "text": "그러하므로 당신은 휴식을 취하는 것이 좋겠습니다.",
            "emotion": None
        }
    ]

    print("=== 한국어 자연스러움 변환 테스트 ===\n")

    for case in test_cases:
        print(f"원본: {case['text']}")

        result = polisher.polish(
            case["text"],
            emotion=case["emotion"],
            turn_count=1
        )

        print(f"변환: {result['response']}")
        print(f"점수: {result['naturalness_score']:.2f}")
        print(f"변경: {result['changes']}")
        print("-" * 60)


if __name__ == "__main__":
    test_naturalizer()
