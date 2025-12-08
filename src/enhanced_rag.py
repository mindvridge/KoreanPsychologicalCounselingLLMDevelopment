"""
강화된 RAG 시스템 (Enhanced RAG System)
심리상담 맥락에 최적화된 지식 검색 및 컨텍스트 증강

기능:
- 스마트 쿼리 재작성 (Query Rewriting)
- 감정/상황 기반 쿼리 확장
- 다중 쿼리 검색 및 결과 병합
- 관련성 필터링 및 재순위화
- 치료 기법 중심 컨텍스트 구성
- 위기 상황 우선 검색
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class QueryIntent(Enum):
    """쿼리 의도"""
    EMOTIONAL_SUPPORT = "emotional_support"     # 감정적 지지 필요
    COPING_STRATEGY = "coping_strategy"         # 대처 전략 필요
    CRISIS_RESPONSE = "crisis_response"         # 위기 대응
    PSYCHOEDUCATION = "psychoeducation"         # 심리교육 정보
    TECHNIQUE_GUIDANCE = "technique_guidance"   # 치료 기법 안내
    CULTURAL_CONTEXT = "cultural_context"       # 문화적 맥락
    GENERAL = "general"                         # 일반


@dataclass
class EnhancedSearchResult:
    """강화된 검색 결과"""
    content: str
    score: float
    relevance: str  # high, medium, low
    source: str
    therapy_type: Optional[str] = None
    category: Optional[str] = None
    query_matched: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryExpansion:
    """쿼리 확장 결과"""
    original_query: str
    expanded_queries: List[str]
    intent: QueryIntent
    emotion_context: Optional[str] = None
    keywords: List[str] = field(default_factory=list)


class QueryRewriter:
    """
    스마트 쿼리 재작성기

    사용자 메시지를 효과적인 검색 쿼리로 변환합니다.
    """

    def __init__(self):
        # 감정-치료기법 매핑
        self.emotion_therapy_map = {
            "우울": ["CBT 행동활성화", "인지 재구성", "우울 대처법"],
            "불안": ["불안 관리 기법", "호흡법", "점진적 근육 이완", "노출 치료"],
            "분노": ["분노 조절 기법", "DBT 고통감내", "마음챙김"],
            "스트레스": ["스트레스 관리", "이완 기법", "시간 관리"],
            "외로움": ["사회적 연결", "고립감 해소", "대인관계 기술"],
            "두려움": ["공포 대처", "체계적 둔감화", "인지 재구성"],
            "죄책감": ["자기연민", "인지 왜곡 수정", "수용"],
            "수치심": ["수치심 대처", "자기 수용", "체면 문화"],
            "무기력": ["행동 활성화", "작은 목표 설정", "동기 강화"],
        }

        # 상황-검색어 매핑
        self.situation_queries = {
            "직장": ["직장 스트레스", "번아웃", "상사 갈등", "워라밸"],
            "가족": ["가족 갈등", "부모 관계", "효도 문화", "세대 갈등"],
            "연애": ["연인 관계", "이별", "사랑", "관계 불안"],
            "학업": ["시험 불안", "학업 스트레스", "진로 고민"],
            "자존감": ["자존감 향상", "자기 효능감", "자기 비난"],
            "대인관계": ["대인관계 기술", "사회 불안", "거절 공포"],
        }

        # 위기 키워드
        self.crisis_keywords = [
            "죽고 싶", "자살", "자해", "살고 싶지 않",
            "사라지고 싶", "끝내고 싶", "희망이 없"
        ]

        # 한국어 동의어 사전
        self.synonyms = {
            "우울": ["우울증", "우울감", "침울", "기분저하", "무기력"],
            "불안": ["불안감", "초조", "긴장", "걱정", "두려움"],
            "스트레스": ["압박감", "부담", "긴장", "피로"],
            "CBT": ["인지행동치료", "인지치료", "행동치료"],
            "ACT": ["수용전념치료", "수용치료"],
            "DBT": ["변증법적행동치료", "변증법치료"],
            "마음챙김": ["명상", "mindfulness", "현재 집중"],
        }

        logger.info("QueryRewriter initialized")

    def rewrite(
        self,
        user_message: str,
        emotion: Optional[str] = None,
        conversation_context: Optional[List[Dict]] = None,
        crisis_detected: bool = False
    ) -> QueryExpansion:
        """
        쿼리 재작성 및 확장

        Args:
            user_message: 사용자 메시지
            emotion: 감지된 감정
            conversation_context: 대화 맥락
            crisis_detected: 위기 감지 여부

        Returns:
            QueryExpansion: 확장된 쿼리 정보
        """
        expanded_queries = []
        keywords = []

        # 1. 위기 상황 최우선 처리
        if crisis_detected or self._detect_crisis(user_message):
            return QueryExpansion(
                original_query=user_message,
                expanded_queries=[
                    "자살 위기 대응 프로토콜",
                    "위기 상담 기법",
                    "안전 계획",
                    "자살예방 상담"
                ],
                intent=QueryIntent.CRISIS_RESPONSE,
                emotion_context=emotion,
                keywords=["위기", "자살예방", "안전"]
            )

        # 2. 의도 파악
        intent = self._detect_intent(user_message, emotion)

        # 3. 원본 메시지에서 키워드 추출
        keywords = self._extract_keywords(user_message)
        expanded_queries.append(user_message)

        # 4. 감정 기반 쿼리 확장
        if emotion:
            emotion_queries = self.emotion_therapy_map.get(emotion, [])
            expanded_queries.extend(emotion_queries[:2])
            keywords.append(emotion)

        # 5. 상황 기반 쿼리 확장
        for situation, queries in self.situation_queries.items():
            if situation in user_message:
                expanded_queries.extend(queries[:2])
                keywords.append(situation)

        # 6. 동의어 확장
        for word in keywords[:3]:
            synonyms = self.synonyms.get(word, [])
            expanded_queries.extend(synonyms[:2])

        # 7. 대화 맥락 반영
        if conversation_context:
            context_queries = self._extract_context_queries(conversation_context)
            expanded_queries.extend(context_queries)

        # 중복 제거 및 제한
        expanded_queries = list(dict.fromkeys(expanded_queries))[:8]

        return QueryExpansion(
            original_query=user_message,
            expanded_queries=expanded_queries,
            intent=intent,
            emotion_context=emotion,
            keywords=keywords
        )

    def _detect_crisis(self, message: str) -> bool:
        """위기 상황 감지"""
        return any(keyword in message for keyword in self.crisis_keywords)

    def _detect_intent(self, message: str, emotion: Optional[str]) -> QueryIntent:
        """의도 파악"""
        message_lower = message.lower()

        # 위기 관련
        if self._detect_crisis(message):
            return QueryIntent.CRISIS_RESPONSE

        # 대처 전략 요청
        coping_markers = ["어떻게", "방법", "도움", "해결", "벗어나"]
        if any(marker in message_lower for marker in coping_markers):
            return QueryIntent.COPING_STRATEGY

        # 심리교육 요청
        edu_markers = ["뭔지", "무엇", "왜", "이유", "원인"]
        if any(marker in message_lower for marker in edu_markers):
            return QueryIntent.PSYCHOEDUCATION

        # 문화적 맥락
        cultural_markers = ["부모님", "체면", "기대", "효도"]
        if any(marker in message_lower for marker in cultural_markers):
            return QueryIntent.CULTURAL_CONTEXT

        # 기본: 감정적 지지
        return QueryIntent.EMOTIONAL_SUPPORT

    def _extract_keywords(self, message: str) -> List[str]:
        """메시지에서 키워드 추출"""
        keywords = []

        # 감정 키워드
        emotion_words = [
            "우울", "불안", "스트레스", "화", "분노", "슬프", "외롭",
            "무서", "두렵", "걱정", "힘들", "지쳐", "무기력"
        ]
        for word in emotion_words:
            if word in message:
                keywords.append(word)

        # 상황 키워드
        situation_words = [
            "직장", "회사", "상사", "가족", "부모", "연인", "친구",
            "학교", "시험", "취업", "이직"
        ]
        for word in situation_words:
            if word in message:
                keywords.append(word)

        return keywords[:5]

    def _extract_context_queries(
        self,
        conversation_context: List[Dict]
    ) -> List[str]:
        """대화 맥락에서 추가 쿼리 추출"""
        context_queries = []

        # 최근 3턴의 사용자 메시지에서 주제 추출
        user_messages = [
            turn["content"] for turn in conversation_context[-6:]
            if turn.get("role") == "user"
        ]

        # 반복되는 주제 찾기
        all_keywords = []
        for msg in user_messages:
            all_keywords.extend(self._extract_keywords(msg))

        # 빈도 높은 키워드를 쿼리로
        keyword_counts = defaultdict(int)
        for kw in all_keywords:
            keyword_counts[kw] += 1

        for kw, count in sorted(keyword_counts.items(), key=lambda x: -x[1])[:2]:
            if count >= 2:
                context_queries.append(f"{kw} 상담 기법")

        return context_queries


class RelevanceFilter:
    """
    관련성 필터 및 재순위화

    검색 결과의 관련성을 평가하고 재순위화합니다.
    """

    def __init__(self, min_score: float = 0.3):
        """
        초기화

        Args:
            min_score: 최소 관련성 점수
        """
        self.min_score = min_score

        # 치료 기법 우선순위 (상황별)
        self.therapy_priority = {
            QueryIntent.CRISIS_RESPONSE: ["crisis_protocols", "suicide_prevention"],
            QueryIntent.COPING_STRATEGY: ["CBT", "DBT", "ACT"],
            QueryIntent.EMOTIONAL_SUPPORT: ["counseling", "empathy"],
            QueryIntent.CULTURAL_CONTEXT: ["cultural_context", "korean"],
        }

    def filter_and_rank(
        self,
        results: List[EnhancedSearchResult],
        query_expansion: QueryExpansion,
        max_results: int = 5
    ) -> List[EnhancedSearchResult]:
        """
        필터링 및 재순위화

        Args:
            results: 검색 결과
            query_expansion: 쿼리 확장 정보
            max_results: 최대 결과 수

        Returns:
            List[EnhancedSearchResult]: 필터링된 결과
        """
        if not results:
            return []

        # 1. 최소 점수 필터링
        filtered = [r for r in results if r.score >= self.min_score]

        # 2. 의도 기반 가중치 적용
        intent = query_expansion.intent
        priority_categories = self.therapy_priority.get(intent, [])

        for result in filtered:
            # 우선 카테고리 보너스
            if result.category in priority_categories:
                result.score *= 1.3
            if result.therapy_type in priority_categories:
                result.score *= 1.2

            # 키워드 매칭 보너스
            content_lower = result.content.lower()
            keyword_matches = sum(
                1 for kw in query_expansion.keywords
                if kw in content_lower
            )
            result.score *= (1 + keyword_matches * 0.1)

        # 3. 중복 제거 (유사 컨텐츠)
        unique_results = self._remove_duplicates(filtered)

        # 4. 재순위화
        sorted_results = sorted(unique_results, key=lambda x: x.score, reverse=True)

        # 5. 다양성 보장 (같은 카테고리가 너무 많지 않도록)
        diverse_results = self._ensure_diversity(sorted_results, max_results)

        return diverse_results[:max_results]

    def _remove_duplicates(
        self,
        results: List[EnhancedSearchResult],
        similarity_threshold: float = 0.8
    ) -> List[EnhancedSearchResult]:
        """유사 컨텐츠 중복 제거"""
        unique = []
        seen_content = []

        for result in results:
            # 기존 컨텐츠와 비교
            is_duplicate = False
            for seen in seen_content:
                similarity = self._content_similarity(result.content, seen)
                if similarity > similarity_threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique.append(result)
                seen_content.append(result.content)

        return unique

    def _content_similarity(self, text1: str, text2: str) -> float:
        """컨텐츠 유사도 계산 (간단한 자카드 유사도)"""
        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _ensure_diversity(
        self,
        results: List[EnhancedSearchResult],
        max_results: int
    ) -> List[EnhancedSearchResult]:
        """다양성 보장"""
        if len(results) <= max_results:
            return results

        diverse = []
        category_counts = defaultdict(int)
        max_per_category = max(2, max_results // 3)

        for result in results:
            category = result.category or "general"
            if category_counts[category] < max_per_category:
                diverse.append(result)
                category_counts[category] += 1

            if len(diverse) >= max_results:
                break

        return diverse


class TherapyContextBuilder:
    """
    치료 컨텍스트 구성기

    검색 결과를 LLM 프롬프트용 컨텍스트로 구성합니다.
    """

    def __init__(self, max_context_length: int = 1500):
        """
        초기화

        Args:
            max_context_length: 최대 컨텍스트 길이 (문자)
        """
        self.max_context_length = max_context_length

    def build_context(
        self,
        results: List[EnhancedSearchResult],
        query_expansion: QueryExpansion
    ) -> str:
        """
        컨텍스트 구성

        Args:
            results: 검색 결과
            query_expansion: 쿼리 확장 정보

        Returns:
            str: 구성된 컨텍스트
        """
        if not results:
            return ""

        context_parts = []
        current_length = 0

        # 의도별 헤더
        intent_headers = {
            QueryIntent.CRISIS_RESPONSE: "## 위기 대응 프로토콜",
            QueryIntent.COPING_STRATEGY: "## 대처 전략 참고",
            QueryIntent.PSYCHOEDUCATION: "## 심리학적 이해",
            QueryIntent.TECHNIQUE_GUIDANCE: "## 치료 기법 가이드",
            QueryIntent.CULTURAL_CONTEXT: "## 한국 문화적 맥락",
            QueryIntent.EMOTIONAL_SUPPORT: "## 상담 참고 자료",
        }

        header = intent_headers.get(query_expansion.intent, "## 참고 자료")
        context_parts.append(header)
        current_length += len(header)

        # 결과 추가
        for i, result in enumerate(results, 1):
            # 출처 정보
            source_info = f"\n### 참고 {i}"
            if result.therapy_type:
                source_info += f" ({result.therapy_type})"
            source_info += f"\n관련도: {'높음' if result.relevance == 'high' else '중간'}\n"

            # 컨텐츠 (적절한 길이로 자르기)
            content = result.content
            remaining_length = self.max_context_length - current_length - len(source_info) - 100
            if remaining_length <= 0:
                break

            if len(content) > remaining_length:
                content = content[:remaining_length] + "..."

            entry = source_info + content + "\n"
            context_parts.append(entry)
            current_length += len(entry)

            if current_length >= self.max_context_length:
                break

        # 활용 가이드 추가
        usage_guide = self._get_usage_guide(query_expansion.intent)
        if current_length + len(usage_guide) < self.max_context_length:
            context_parts.append(usage_guide)

        return "\n".join(context_parts)

    def _get_usage_guide(self, intent: QueryIntent) -> str:
        """활용 가이드 생성"""
        guides = {
            QueryIntent.CRISIS_RESPONSE:
                "\n**활용 지침**: 위 프로토콜을 참고하되, 공감을 먼저 표현하고 "
                "안전 확인 후 전문 자원을 연결하세요.",
            QueryIntent.COPING_STRATEGY:
                "\n**활용 지침**: 내담자의 준비도에 맞춰 기법을 소개하세요. "
                "강요하지 말고 선택권을 제공하세요.",
            QueryIntent.CULTURAL_CONTEXT:
                "\n**활용 지침**: 문화적 맥락을 이해하되, 개인차를 존중하세요.",
        }
        return guides.get(intent, "")


class EnhancedRAGSystem:
    """
    강화된 RAG 시스템

    쿼리 재작성, 검색, 필터링, 컨텍스트 구성을 통합합니다.
    """

    def __init__(self, base_rag=None):
        """
        초기화

        Args:
            base_rag: 기본 RAG 시스템 (MentalHealthRAG 인스턴스)
        """
        self.base_rag = base_rag
        self.query_rewriter = QueryRewriter()
        self.relevance_filter = RelevanceFilter()
        self.context_builder = TherapyContextBuilder()

        logger.info("EnhancedRAGSystem initialized")

    def retrieve_and_augment(
        self,
        user_message: str,
        emotion: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None,
        crisis_detected: bool = False,
        max_results: int = 5
    ) -> Tuple[str, QueryExpansion]:
        """
        검색 및 컨텍스트 증강

        Args:
            user_message: 사용자 메시지
            emotion: 감지된 감정
            conversation_history: 대화 이력
            crisis_detected: 위기 감지 여부
            max_results: 최대 결과 수

        Returns:
            Tuple[str, QueryExpansion]: (증강된 컨텍스트, 쿼리 확장 정보)
        """
        # 1. 쿼리 재작성
        query_expansion = self.query_rewriter.rewrite(
            user_message=user_message,
            emotion=emotion,
            conversation_context=conversation_history,
            crisis_detected=crisis_detected
        )

        logger.debug(f"Query expanded: {query_expansion.expanded_queries}")

        # 2. 다중 쿼리 검색
        all_results = []
        if self.base_rag:
            for query in query_expansion.expanded_queries:
                try:
                    results = self.base_rag.retrieve(query, k=3)
                    for r in results:
                        enhanced_result = EnhancedSearchResult(
                            content=r.document.content,
                            score=r.score,
                            relevance=r.relevance,
                            source=r.document.metadata.get("source", ""),
                            therapy_type=r.document.metadata.get("therapy_type"),
                            category=r.document.metadata.get("category"),
                            query_matched=query
                        )
                        all_results.append(enhanced_result)
                except Exception as e:
                    logger.error(f"Search error for query '{query}': {e}")
        else:
            # base_rag가 없으면 시뮬레이션 결과 반환
            all_results = self._get_simulated_results(query_expansion)

        # 3. 필터링 및 재순위화
        filtered_results = self.relevance_filter.filter_and_rank(
            results=all_results,
            query_expansion=query_expansion,
            max_results=max_results
        )

        # 4. 컨텍스트 구성
        context = self.context_builder.build_context(
            results=filtered_results,
            query_expansion=query_expansion
        )

        return context, query_expansion

    def _get_simulated_results(
        self,
        query_expansion: QueryExpansion
    ) -> List[EnhancedSearchResult]:
        """시뮬레이션 결과 (base_rag 없을 때)"""
        # 의도별 기본 컨텐츠
        default_contents = {
            QueryIntent.CRISIS_RESPONSE: [
                EnhancedSearchResult(
                    content="자살 위기 대응 시 SAFE-T 프로토콜을 적용합니다. "
                           "1) 안전 확인 2) 공감 표현 3) 전문 자원 연결 (1393, 1577-0199) "
                           "4) 안전 계획 수립 5) 추후 관리",
                    score=0.95,
                    relevance="high",
                    source="crisis_protocols/suicide_prevention.txt",
                    category="crisis_protocols"
                )
            ],
            QueryIntent.COPING_STRATEGY: [
                EnhancedSearchResult(
                    content="CBT 인지재구성 기법: 부정적 자동적 사고를 인식하고, "
                           "그 사고의 증거를 검토하며, 대안적 사고를 개발합니다. "
                           "'생각 기록지'를 활용하면 효과적입니다.",
                    score=0.85,
                    relevance="high",
                    source="therapy_techniques/CBT_manual.txt",
                    therapy_type="CBT",
                    category="therapy_techniques"
                )
            ],
            QueryIntent.EMOTIONAL_SUPPORT: [
                EnhancedSearchResult(
                    content="공감적 경청의 핵심: 1) 판단 없이 듣기 2) 감정 반영하기 "
                           "3) 명료화 질문하기 4) 요약하기. "
                           "내담자의 감정을 있는 그대로 수용하는 것이 중요합니다.",
                    score=0.80,
                    relevance="high",
                    source="therapy_techniques/counseling_basics.txt",
                    category="therapy_techniques"
                )
            ],
        }

        return default_contents.get(query_expansion.intent, default_contents[QueryIntent.EMOTIONAL_SUPPORT])

    def get_therapy_suggestions(
        self,
        emotion: str,
        concern_categories: List[str]
    ) -> List[str]:
        """
        치료 기법 제안

        Args:
            emotion: 주요 감정
            concern_categories: 고민 카테고리들

        Returns:
            List[str]: 추천 치료 기법
        """
        suggestions = []

        # 감정별 기법
        emotion_techniques = {
            "우울": ["행동 활성화", "인지 재구성", "활동 계획"],
            "불안": ["호흡법", "점진적 근육 이완", "걱정 시간 설정"],
            "분노": ["STOP 기법", "마음챙김", "감정 조절 기술"],
            "스트레스": ["스트레스 관리", "시간 관리", "경계 설정"],
        }

        if emotion in emotion_techniques:
            suggestions.extend(emotion_techniques[emotion])

        # 상황별 기법
        situation_techniques = {
            "직장/업무": ["직장 스트레스 관리", "경계 설정", "자기주장"],
            "대인관계": ["의사소통 기술", "대인관계 효과성"],
            "가족": ["가족 의사소통", "경계 설정", "자기 돌봄"],
        }

        for category in concern_categories:
            if category in situation_techniques:
                suggestions.extend(situation_techniques[category])

        return list(set(suggestions))[:5]


# 편의 함수
def get_enhanced_context(
    user_message: str,
    emotion: Optional[str] = None,
    conversation_history: Optional[List[Dict]] = None,
    crisis_detected: bool = False,
    base_rag=None
) -> str:
    """
    강화된 컨텍스트 획득 편의 함수

    Args:
        user_message: 사용자 메시지
        emotion: 감지된 감정
        conversation_history: 대화 이력
        crisis_detected: 위기 감지 여부
        base_rag: 기본 RAG 시스템

    Returns:
        str: 증강된 컨텍스트
    """
    enhanced_rag = EnhancedRAGSystem(base_rag=base_rag)
    context, _ = enhanced_rag.retrieve_and_augment(
        user_message=user_message,
        emotion=emotion,
        conversation_history=conversation_history,
        crisis_detected=crisis_detected
    )
    return context


if __name__ == "__main__":
    # 테스트
    print("=== 강화된 RAG 시스템 테스트 ===\n")

    enhanced_rag = EnhancedRAGSystem()

    test_cases = [
        {
            "message": "요즘 직장에서 너무 스트레스받아요. 상사가 저한테만 일을 몰아줘요.",
            "emotion": "분노",
            "crisis": False
        },
        {
            "message": "더 이상 살고 싶지 않아요. 모든 게 힘들어요.",
            "emotion": "절망",
            "crisis": True
        },
        {
            "message": "불안해서 잠을 못 자요. 어떻게 해야 할까요?",
            "emotion": "불안",
            "crisis": False
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"### 테스트 {i}")
        print(f"메시지: {test['message']}")
        print(f"감정: {test['emotion']}")
        print(f"위기 감지: {test['crisis']}")

        context, expansion = enhanced_rag.retrieve_and_augment(
            user_message=test["message"],
            emotion=test["emotion"],
            crisis_detected=test["crisis"]
        )

        print(f"\n의도: {expansion.intent.value}")
        print(f"확장된 쿼리: {expansion.expanded_queries[:3]}")
        print(f"키워드: {expansion.keywords}")
        print(f"\n컨텍스트:\n{context[:500]}...")
        print("\n" + "="*60 + "\n")
