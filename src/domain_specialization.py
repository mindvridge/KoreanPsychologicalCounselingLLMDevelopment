"""
도메인별 전문화 시스템 (Domain Specialization System)
특정 상담 주제별 전문화

기능:
- 도메인 자동 감지
- 도메인별 전문 프롬프트 생성
- 전문 지식 베이스 연결
- 도메인별 응답 스타일 조정
- 도메인별 위기 대응 매핑
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class CounselingDomain(Enum):
    """상담 도메인"""
    DEPRESSION = "우울"
    ANXIETY = "불안"
    RELATIONSHIP = "관계"
    WORK_STRESS = "직장스트레스"
    FAMILY = "가족"
    SELF_ESTEEM = "자존감"
    TRAUMA = "트라우마"
    ADDICTION = "중독"
    GRIEF = "상실"
    LIFE_TRANSITION = "삶의전환"
    GENERAL = "일반"


@dataclass
class DomainConfig:
    """도메인 설정"""
    domain: CounselingDomain
    keywords: List[str]
    response_style: Dict[str, Any]
    therapeutic_approaches: List[str]
    key_techniques: List[str]
    warning_signs: List[str]
    resources: List[Dict[str, str]]
    prompt_additions: str


class DomainDetector:
    """
    도메인 감지기

    사용자 메시지에서 상담 도메인을 감지합니다.
    """

    def __init__(self):
        # 도메인별 키워드
        self.domain_keywords = {
            CounselingDomain.DEPRESSION: [
                "우울", "무기력", "의욕", "삶", "죽고 싶", "살기 싫",
                "슬프", "눈물", "아무것도", "희망", "절망", "무의미"
            ],
            CounselingDomain.ANXIETY: [
                "불안", "걱정", "두려", "무서", "공포", "공황",
                "심장", "떨리", "긴장", "초조", "예민"
            ],
            CounselingDomain.RELATIONSHIP: [
                "남자친구", "여자친구", "애인", "배우자", "남편", "아내",
                "이별", "헤어", "사랑", "연애", "결혼", "외도"
            ],
            CounselingDomain.WORK_STRESS: [
                "회사", "직장", "상사", "동료", "업무", "야근",
                "퇴사", "이직", "스트레스", "번아웃", "실업"
            ],
            CounselingDomain.FAMILY: [
                "부모", "엄마", "아빠", "형", "누나", "언니", "동생",
                "시댁", "시어머니", "고부", "가족"
            ],
            CounselingDomain.SELF_ESTEEM: [
                "자존", "자신감", "열등", "비교", "못나", "부족",
                "실패", "가치", "무능", "쓸모"
            ],
            CounselingDomain.TRAUMA: [
                "트라우마", "사고", "폭력", "학대", "성폭력", "가정폭력",
                "악몽", "플래시백", "충격"
            ],
            CounselingDomain.ADDICTION: [
                "술", "알코올", "게임", "도박", "중독", "담배",
                "끊고 싶", "조절"
            ],
            CounselingDomain.GRIEF: [
                "죽음", "사망", "돌아가", "상실", "이별", "떠나",
                "그리워", "보고 싶"
            ],
            CounselingDomain.LIFE_TRANSITION: [
                "진로", "취업", "졸업", "입시", "유학", "이사",
                "새로운", "변화", "미래"
            ]
        }

        # 가중치
        self.domain_weights: Dict[CounselingDomain, float] = {
            domain: 1.0 for domain in CounselingDomain
        }

        # 특수 키워드 (높은 가중치)
        self.high_priority_keywords = {
            "죽고 싶": (CounselingDomain.DEPRESSION, 3.0),
            "살기 싫": (CounselingDomain.DEPRESSION, 3.0),
            "공황발작": (CounselingDomain.ANXIETY, 2.5),
            "성폭력": (CounselingDomain.TRAUMA, 3.0),
            "학대": (CounselingDomain.TRAUMA, 2.5),
            "자해": (CounselingDomain.DEPRESSION, 3.0),
        }

    def detect(
        self,
        text: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> Tuple[CounselingDomain, float]:
        """
        도메인 감지

        Args:
            text: 사용자 메시지
            conversation_history: 대화 히스토리

        Returns:
            Tuple[CounselingDomain, float]: (도메인, 신뢰도)
        """
        scores: Dict[CounselingDomain, float] = {
            domain: 0.0 for domain in CounselingDomain
        }

        text_lower = text.lower()

        # 높은 우선순위 키워드 먼저 체크
        for keyword, (domain, weight) in self.high_priority_keywords.items():
            if keyword in text_lower:
                scores[domain] += weight

        # 일반 키워드 매칭
        for domain, keywords in self.domain_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    scores[domain] += 1.0 * self.domain_weights[domain]

        # 대화 히스토리 반영
        if conversation_history:
            for msg in conversation_history[-5:]:  # 최근 5개
                content = msg.get("content", "")
                for domain, keywords in self.domain_keywords.items():
                    for keyword in keywords:
                        if keyword in content.lower():
                            scores[domain] += 0.3  # 히스토리는 낮은 가중치

        # 최고 점수 도메인 선택
        max_domain = max(scores, key=scores.get)
        max_score = scores[max_domain]

        if max_score < 0.5:
            return CounselingDomain.GENERAL, 0.3

        # 정규화된 신뢰도
        total_score = sum(scores.values())
        confidence = max_score / total_score if total_score > 0 else 0.0

        return max_domain, confidence

    def get_all_scores(self, text: str) -> Dict[CounselingDomain, float]:
        """모든 도메인 점수 반환"""
        scores = {}
        for domain, keywords in self.domain_keywords.items():
            score = sum(1 for kw in keywords if kw in text.lower())
            if score > 0:
                scores[domain] = score
        return scores


class DomainSpecializer:
    """
    도메인 전문화 시스템

    도메인별 특화된 응답 전략을 제공합니다.
    """

    def __init__(self, knowledge_base_path: Optional[str] = None):
        """
        초기화

        Args:
            knowledge_base_path: 지식 베이스 경로
        """
        self.detector = DomainDetector()
        self.knowledge_base_path = knowledge_base_path
        self.domain_configs = self._init_domain_configs()
        self.cached_knowledge: Dict[str, Any] = {}

        logger.info("DomainSpecializer initialized")

    def _init_domain_configs(self) -> Dict[CounselingDomain, DomainConfig]:
        """도메인 설정 초기화"""
        configs = {
            CounselingDomain.DEPRESSION: DomainConfig(
                domain=CounselingDomain.DEPRESSION,
                keywords=["우울", "무기력", "희망없음"],
                response_style={
                    "tone": "따뜻하고 수용적",
                    "pace": "천천히",
                    "validation_level": "높음",
                    "question_style": "부드러운 탐색"
                },
                therapeutic_approaches=[
                    "행동활성화",
                    "인지재구조화",
                    "마음챙김"
                ],
                key_techniques=[
                    "작은 성취 경험 격려",
                    "긍정적 활동 탐색",
                    "자기비난 인식 및 완화"
                ],
                warning_signs=[
                    "자살 사고",
                    "자해",
                    "극심한 무기력"
                ],
                resources=[
                    {"name": "자살예방상담전화", "number": "1393"},
                    {"name": "정신건강위기상담전화", "number": "1577-0199"}
                ],
                prompt_additions="""
## 우울 상담 가이드
- 무기력감과 절망감을 충분히 수용하세요
- 작은 변화도 인정하고 격려하세요
- "힘내세요" 등 피상적 격려는 피하세요
- 자살/자해 사고 여부를 주의 깊게 모니터링하세요
- 일상 속 작은 기쁨을 함께 찾아보세요
"""
            ),

            CounselingDomain.ANXIETY: DomainConfig(
                domain=CounselingDomain.ANXIETY,
                keywords=["불안", "걱정", "두려움"],
                response_style={
                    "tone": "안정적이고 차분함",
                    "pace": "안정적",
                    "validation_level": "높음",
                    "question_style": "구체화 질문"
                },
                therapeutic_approaches=[
                    "노출치료 원리",
                    "인지재구조화",
                    "이완훈련"
                ],
                key_techniques=[
                    "호흡법 (4-7-8)",
                    "그라운딩 (5-4-3-2-1)",
                    "걱정시간 설정"
                ],
                warning_signs=[
                    "공황발작",
                    "회피 행동 심화",
                    "일상 기능 저하"
                ],
                resources=[
                    {"name": "정신건강위기상담전화", "number": "1577-0199"}
                ],
                prompt_additions="""
## 불안 상담 가이드
- 불안은 자연스러운 반응임을 인정해주세요
- 구체적인 걱정 내용을 탐색하세요
- 현실적 vs 비현실적 걱정을 구분하도록 도와주세요
- 대처 가능한 부분에 초점을 맞추세요
- 필요시 호흡법이나 그라운딩 기법을 안내하세요
"""
            ),

            CounselingDomain.RELATIONSHIP: DomainConfig(
                domain=CounselingDomain.RELATIONSHIP,
                keywords=["연애", "이별", "관계"],
                response_style={
                    "tone": "공감적",
                    "pace": "적당히",
                    "validation_level": "중간",
                    "question_style": "관계 탐색"
                },
                therapeutic_approaches=[
                    "정서중심치료",
                    "애착이론",
                    "의사소통 훈련"
                ],
                key_techniques=[
                    "나-전달법",
                    "경청 기술",
                    "감정 표현"
                ],
                warning_signs=[
                    "데이트 폭력",
                    "정서적 학대",
                    "자해/자살 사고"
                ],
                resources=[
                    {"name": "여성긴급전화", "number": "1366"}
                ],
                prompt_additions="""
## 관계 상담 가이드
- 양측의 입장을 균형있게 탐색하세요
- 감정 뒤에 있는 욕구를 탐색하세요
- 건강한 관계의 특성을 자연스럽게 나누세요
- 한쪽 편을 들지 마세요
- 폭력이나 학대 징후가 있으면 안전을 우선하세요
"""
            ),

            CounselingDomain.WORK_STRESS: DomainConfig(
                domain=CounselingDomain.WORK_STRESS,
                keywords=["직장", "업무", "스트레스"],
                response_style={
                    "tone": "현실적이고 지지적",
                    "pace": "적당히",
                    "validation_level": "중간",
                    "question_style": "상황 구체화"
                },
                therapeutic_approaches=[
                    "문제해결치료",
                    "스트레스 관리",
                    "경계 설정"
                ],
                key_techniques=[
                    "우선순위 설정",
                    "시간 관리",
                    "경계 설정"
                ],
                warning_signs=[
                    "번아웃",
                    "직장 내 괴롭힘",
                    "우울증 전환"
                ],
                resources=[
                    {"name": "근로자건강센터", "number": "1588-6497"},
                    {"name": "고용노동부", "number": "1350"}
                ],
                prompt_additions="""
## 직장 스트레스 상담 가이드
- 구체적인 상황과 대인관계를 파악하세요
- 업무량, 관계, 환경 등 다양한 원인을 탐색하세요
- 바꿀 수 있는 것과 없는 것을 구분하도록 도와주세요
- 자기 돌봄의 중요성을 강조하세요
- 직장 내 괴롭힘 시 관련 자원을 안내하세요
"""
            ),

            CounselingDomain.FAMILY: DomainConfig(
                domain=CounselingDomain.FAMILY,
                keywords=["가족", "부모", "고부갈등"],
                response_style={
                    "tone": "중립적이고 수용적",
                    "pace": "천천히",
                    "validation_level": "높음",
                    "question_style": "가족 역동 탐색"
                },
                therapeutic_approaches=[
                    "가족체계이론",
                    "경계 설정",
                    "세대 간 패턴"
                ],
                key_techniques=[
                    "가족 역할 인식",
                    "건강한 경계",
                    "효과적 의사소통"
                ],
                warning_signs=[
                    "가정폭력",
                    "학대",
                    "방임"
                ],
                resources=[
                    {"name": "가정폭력상담전화", "number": "1366"},
                    {"name": "아동학대신고", "number": "112"}
                ],
                prompt_additions="""
## 가족 상담 가이드
- 가족 구성원 각각의 입장을 균형있게 탐색하세요
- 오랜 패턴과 역할을 이해하려고 노력하세요
- 효도와 자기 돌봄 사이의 균형을 탐색하세요
- 건강한 경계 설정의 중요성을 나누세요
- 폭력이나 학대 시 안전을 최우선하세요
"""
            ),

            CounselingDomain.TRAUMA: DomainConfig(
                domain=CounselingDomain.TRAUMA,
                keywords=["트라우마", "학대", "폭력"],
                response_style={
                    "tone": "안전하고 수용적",
                    "pace": "매우 천천히",
                    "validation_level": "매우 높음",
                    "question_style": "조심스러운 탐색"
                },
                therapeutic_approaches=[
                    "트라우마 정보 접근",
                    "안정화",
                    "EMDR 원리"
                ],
                key_techniques=[
                    "안전한 공간 만들기",
                    "그라운딩",
                    "자기조절"
                ],
                warning_signs=[
                    "심한 플래시백",
                    "해리",
                    "자해/자살"
                ],
                resources=[
                    {"name": "성폭력상담전화", "number": "1366"},
                    {"name": "범죄피해자지원", "number": "1577-1295"}
                ],
                prompt_additions="""
## 트라우마 상담 가이드
⚠️ 트라우마 내용을 강제로 탐색하지 마세요
- 안전감 확립이 최우선입니다
- 내담자의 페이스를 존중하세요
- 그라운딩 기법을 준비해두세요
- 전문 치료 의뢰를 권유하세요
- 재외상화를 예방하세요
"""
            ),

            CounselingDomain.ADDICTION: DomainConfig(
                domain=CounselingDomain.ADDICTION,
                keywords=["중독", "술", "게임", "도박"],
                response_style={
                    "tone": "비판단적",
                    "pace": "적당히",
                    "validation_level": "중간",
                    "question_style": "동기강화"
                },
                therapeutic_approaches=[
                    "동기강화상담",
                    "해해감소",
                    "재발방지"
                ],
                key_techniques=[
                    "양가감정 탐색",
                    "변화 동기 강화",
                    "대안 행동"
                ],
                warning_signs=[
                    "금단 증상",
                    "재정/법적 문제",
                    "신체 건강 악화"
                ],
                resources=[
                    {"name": "중독관리통합지원센터", "number": "1577-0199"},
                    {"name": "도박문제관리센터", "number": "1336"}
                ],
                prompt_additions="""
## 중독 상담 가이드
- 비판하지 말고 현재 상태를 이해하려고 하세요
- 변화에 대한 양가감정을 탐색하세요
- 작은 변화도 인정하세요
- 중독 이면의 욕구를 탐색하세요
- 전문 치료 기관 연결을 권유하세요
"""
            ),

            CounselingDomain.SELF_ESTEEM: DomainConfig(
                domain=CounselingDomain.SELF_ESTEEM,
                keywords=["자존감", "열등감", "자신감"],
                response_style={
                    "tone": "따뜻하고 지지적",
                    "pace": "천천히",
                    "validation_level": "높음",
                    "question_style": "강점 탐색"
                },
                therapeutic_approaches=[
                    "인지재구조화",
                    "자기수용",
                    "강점 기반 접근"
                ],
                key_techniques=[
                    "자기비난 인식",
                    "강점 발견",
                    "자기 수용"
                ],
                warning_signs=[
                    "극심한 자기혐오",
                    "자해",
                    "사회적 철수"
                ],
                resources=[],
                prompt_additions="""
## 자존감 상담 가이드
- 자기비판적 생각을 알아차리도록 도와주세요
- 강점과 긍정적 자질을 함께 탐색하세요
- 비교의 해로움을 나누세요
- 자기 수용과 자기 개선의 균형을 탐색하세요
- 작은 성취를 인정하도록 격려하세요
"""
            ),

            CounselingDomain.GENERAL: DomainConfig(
                domain=CounselingDomain.GENERAL,
                keywords=[],
                response_style={
                    "tone": "따뜻하고 열린",
                    "pace": "적당히",
                    "validation_level": "중간",
                    "question_style": "열린 탐색"
                },
                therapeutic_approaches=[
                    "인간중심치료",
                    "경청",
                    "공감"
                ],
                key_techniques=[
                    "반영적 경청",
                    "열린 질문",
                    "감정 명명"
                ],
                warning_signs=[],
                resources=[
                    {"name": "정신건강위기상담전화", "number": "1577-0199"}
                ],
                prompt_additions="""
## 일반 상담 가이드
- 열린 마음으로 경청하세요
- 사용자의 관심사와 감정을 탐색하세요
- 주제가 명확해지면 해당 도메인 전략을 적용하세요
"""
            )
        }

        return configs

    def get_domain_config(self, domain: CounselingDomain) -> DomainConfig:
        """도메인 설정 가져오기"""
        return self.domain_configs.get(domain, self.domain_configs[CounselingDomain.GENERAL])

    def detect_and_specialize(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        도메인 감지 및 전문화 정보 반환

        Args:
            user_message: 사용자 메시지
            conversation_history: 대화 히스토리

        Returns:
            Dict: 전문화 정보
        """
        domain, confidence = self.detector.detect(user_message, conversation_history)
        config = self.get_domain_config(domain)

        # 지식 베이스 로드
        knowledge = self._load_domain_knowledge(domain)

        return {
            "domain": domain.value,
            "confidence": confidence,
            "response_style": config.response_style,
            "therapeutic_approaches": config.therapeutic_approaches,
            "key_techniques": config.key_techniques,
            "warning_signs": config.warning_signs,
            "resources": config.resources,
            "prompt_additions": config.prompt_additions,
            "knowledge": knowledge
        }

    def _load_domain_knowledge(self, domain: CounselingDomain) -> Optional[Dict]:
        """도메인 지식 로드"""
        if not self.knowledge_base_path:
            return None

        # 캐시 확인
        cache_key = domain.value
        if cache_key in self.cached_knowledge:
            return self.cached_knowledge[cache_key]

        # 도메인-파일 매핑
        file_map = {
            CounselingDomain.TRAUMA: "trauma_ptsd.json",
            CounselingDomain.ADDICTION: "addiction.json",
            CounselingDomain.RELATIONSHIP: "relationship_issues.json",
            CounselingDomain.ANXIETY: "psychosomatic.json"  # 공황장애 포함
        }

        filename = file_map.get(domain)
        if not filename:
            return None

        filepath = Path(self.knowledge_base_path) / "specialized" / filename
        if not filepath.exists():
            return None

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                knowledge = json.load(f)
                self.cached_knowledge[cache_key] = knowledge
                return knowledge
        except Exception as e:
            logger.error(f"Failed to load knowledge: {e}")
            return None

    def generate_specialized_prompt(
        self,
        domain: CounselingDomain,
        include_techniques: bool = True
    ) -> str:
        """
        전문화된 프롬프트 생성

        Args:
            domain: 상담 도메인
            include_techniques: 기법 포함 여부

        Returns:
            str: 전문화 프롬프트
        """
        config = self.get_domain_config(domain)

        parts = [config.prompt_additions]

        if include_techniques and config.key_techniques:
            parts.append("\n### 활용 가능한 기법:")
            for tech in config.key_techniques:
                parts.append(f"- {tech}")

        if config.warning_signs:
            parts.append("\n### 주의 징후:")
            for sign in config.warning_signs:
                parts.append(f"- {sign}")

        if config.resources:
            parts.append("\n### 연결 가능한 자원:")
            for res in config.resources:
                parts.append(f"- {res['name']}: {res['number']}")

        return "\n".join(parts)


# =============================================================================
# 테스트
# =============================================================================

def test_domain_specialization():
    """도메인 전문화 테스트"""
    print("=== 도메인 전문화 시스템 테스트 ===\n")

    specializer = DomainSpecializer()

    test_cases = [
        "요즘 너무 우울해요. 아무것도 하기 싫고 눈물만 나요.",
        "회사에서 너무 스트레스 받아요. 상사가 너무 싫어요.",
        "남자친구랑 헤어졌어요. 너무 힘들어요.",
        "어릴 때 학대를 받았어요. 아직도 악몽을 꿔요.",
        "술을 끊고 싶은데 자꾸 마시게 돼요.",
        "저는 정말 못난 사람 같아요. 자신감이 없어요."
    ]

    for text in test_cases:
        result = specializer.detect_and_specialize(text)
        print(f"입력: {text}")
        print(f"도메인: {result['domain']} (신뢰도: {result['confidence']:.2f})")
        print(f"응답 스타일: {result['response_style']['tone']}")
        print(f"접근법: {', '.join(result['therapeutic_approaches'][:2])}")
        print("-" * 60)

    # 전문화 프롬프트 생성
    print("\n=== 우울 도메인 전문화 프롬프트 ===")
    prompt = specializer.generate_specialized_prompt(CounselingDomain.DEPRESSION)
    print(prompt)


if __name__ == "__main__":
    test_domain_specialization()
