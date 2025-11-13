"""
Persona Manager for Psychological Counseling System
심리상담 페르소나 관리 시스템

Features:
- Load and manage counselor personas
- Recommend personas based on user profile
- Generate persona-specific prompts
- Support multiple counseling styles
"""

import os
import yaml
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


@dataclass
class PersonaProfile:
    """페르소나 프로필 데이터 클래스"""
    id: str
    name: str
    display_name: str
    gender: str
    age_range: str
    personality: Dict[str, Any]
    specialties: List[str]
    counseling_style: Dict[str, str]
    speaking_style: Dict[str, Any]
    strengths: List[str]
    system_prompt: str

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "gender": self.gender,
            "age_range": self.age_range,
            "personality": self.personality,
            "specialties": self.specialties,
            "counseling_style": self.counseling_style,
            "speaking_style": self.speaking_style,
            "strengths": self.strengths,
            "system_prompt": self.system_prompt
        }

    def get_brief_intro(self) -> str:
        """간단한 소개 생성"""
        return (
            f"{self.display_name} ({self.age_range} {self.gender})\n"
            f"성격: {self.personality['type']}\n"
            f"전문 분야: {', '.join(self.specialties[:3])}\n"
            f"상담 스타일: {self.counseling_style['approach']}"
        )


class PersonaManager:
    """
    페르소나 관리 시스템

    Usage:
        pm = PersonaManager()
        persona = pm.get_persona("warm_mother")
        prompt = pm.generate_system_prompt("warm_mother", user_context)
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize PersonaManager

        Args:
            config_path: Path to personas.yaml (default: configs/personas.yaml)
        """
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "configs",
                "personas.yaml"
            )

        self.config_path = config_path
        self.personas: Dict[str, PersonaProfile] = {}
        self.default_persona_id: str = "warm_mother"
        self.recommendation_rules: Dict[str, Any] = {}

        self._load_personas()

    def _load_personas(self):
        """YAML 파일에서 페르소나 로드"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # 각 페르소나 로드
            personas_data = config.get('personas', {})
            for persona_id, persona_data in personas_data.items():
                self.personas[persona_id] = PersonaProfile(
                    id=persona_data['id'],
                    name=persona_data['name'],
                    display_name=persona_data['display_name'],
                    gender=persona_data['gender'],
                    age_range=persona_data['age_range'],
                    personality=persona_data['personality'],
                    specialties=persona_data['specialties'],
                    counseling_style=persona_data['counseling_style'],
                    speaking_style=persona_data['speaking_style'],
                    strengths=persona_data['strengths'],
                    system_prompt=persona_data['system_prompt']
                )

            # 기본 페르소나 설정
            self.default_persona_id = config.get('default_persona', 'warm_mother')

            # 추천 규칙 로드
            self.recommendation_rules = config.get('recommendation_rules', {})

            logger.info(f"Loaded {len(self.personas)} personas from {self.config_path}")

        except Exception as e:
            logger.error(f"Failed to load personas: {e}")
            raise

    def get_persona(self, persona_id: str) -> Optional[PersonaProfile]:
        """
        Get persona by ID

        Args:
            persona_id: Persona identifier

        Returns:
            PersonaProfile or None if not found
        """
        return self.personas.get(persona_id)

    def get_default_persona(self) -> PersonaProfile:
        """기본 페르소나 가져오기"""
        return self.personas[self.default_persona_id]

    def list_personas(self, include_details: bool = False) -> List[Dict[str, Any]]:
        """
        List all available personas

        Args:
            include_details: Include full details or just basic info

        Returns:
            List of persona information
        """
        if include_details:
            return [p.to_dict() for p in self.personas.values()]
        else:
            return [
                {
                    "id": p.id,
                    "name": p.name,
                    "display_name": p.display_name,
                    "age_range": p.age_range,
                    "gender": p.gender,
                    "personality_type": p.personality['type'],
                    "specialties": p.specialties[:3],
                    "intro": p.get_brief_intro()
                }
                for p in self.personas.values()
            ]

    def recommend_personas(
        self,
        age_range: Optional[str] = None,
        concerns: Optional[List[str]] = None,
        top_k: int = 3,
        db_session: Optional[Session] = None,
        use_learned_weights: bool = True,
        user_id: Optional[str] = None,
        use_personalization: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Recommend personas based on user profile with personalization

        Args:
            age_range: User age range (e.g., "20대")
            concerns: List of concerns (e.g., ["우울", "불안"])
            top_k: Number of recommendations
            db_session: Database session for learned weights (optional)
            use_learned_weights: Whether to use learned weights from feedback
            user_id: User ID for personalization (optional)
            use_personalization: Whether to apply user-specific personalization

        Returns:
            List of recommended personas with scores
        """
        persona_scores: Dict[str, float] = {pid: 0.0 for pid in self.personas.keys()}

        # Load learned weight adjustments if available (global learning)
        learned_weights = {}
        if use_learned_weights and db_session is not None and concerns and age_range:
            try:
                from src.database import PersonaFeedbackManager
                for concern in concerns:
                    adjustments = PersonaFeedbackManager.get_weight_adjustments(
                        db_session,
                        concern=concern,
                        age_range=age_range
                    )
                    for adj in adjustments:
                        key = (adj['persona_id'], concern, age_range)
                        learned_weights[key] = adj['final_weight']

                if learned_weights:
                    logger.info(f"Loaded {len(learned_weights)} learned weight adjustments")
            except Exception as e:
                logger.warning(f"Failed to load learned weights: {e}, using rule-based only")

        # Load user-specific preferences if available (personalization)
        user_weights = {}
        if use_personalization and user_id and db_session is not None:
            try:
                from src.database import UserPersonalizationManager
                for pid in self.personas.keys():
                    personal_weight = UserPersonalizationManager.get_user_persona_weight(
                        db_session,
                        user_id=user_id,
                        persona_id=pid
                    )
                    if personal_weight != 0.0:
                        user_weights[pid] = personal_weight

                if user_weights:
                    logger.info(f"Loaded {len(user_weights)} user-specific weight adjustments")
            except Exception as e:
                logger.warning(f"Failed to load user preferences: {e}, skipping personalization")

        # Age-based recommendation
        if age_range:
            age_rules = self.recommendation_rules.get('age_based', {})
            recommended_ids = age_rules.get(age_range, [])
            for pid in recommended_ids:
                if pid in persona_scores:
                    persona_scores[pid] += 2.0

        # Concern-based recommendation (with learned weights)
        if concerns:
            concern_rules = self.recommendation_rules.get('concern_based', {})
            for concern in concerns:
                recommended_ids = concern_rules.get(concern, [])
                for i, pid in enumerate(recommended_ids):
                    if pid in persona_scores:
                        # Check for learned weight
                        key = (pid, concern, age_range) if age_range else None
                        if key and key in learned_weights:
                            # Use learned weight from feedback
                            weight = learned_weights[key]
                            logger.debug(f"Using learned weight {weight:.2f} for {pid}/{concern}/{age_range}")
                        else:
                            # Use rule-based weight
                            weight = 3.0 - i * 0.5

                        persona_scores[pid] += weight

        # Apply user-specific personalization weights
        if user_weights:
            for pid, user_weight in user_weights.items():
                if pid in persona_scores:
                    persona_scores[pid] += user_weight
                    logger.debug(f"Applied user weight {user_weight:+.2f} for {pid}")

        # Sort by score
        sorted_personas = sorted(
            persona_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Get top K
        recommendations = []
        for persona_id, score in sorted_personas[:top_k]:
            persona = self.personas[persona_id]

            # Determine if this persona was boosted by personalization
            personalized = persona_id in user_weights

            recommendations.append({
                "id": persona.id,
                "name": persona.name,
                "display_name": persona.display_name,
                "score": score,
                "personality_type": persona.personality['type'],
                "specialties": persona.specialties,
                "intro": persona.get_brief_intro(),
                "reason": self._generate_recommendation_reason(
                    persona, age_range, concerns, personalized
                ),
                "personalized": personalized
            })

        return recommendations

    def _generate_recommendation_reason(
        self,
        persona: PersonaProfile,
        age_range: Optional[str],
        concerns: Optional[List[str]],
        personalized: bool = False
    ) -> str:
        """추천 이유 생성"""
        reasons = []

        # 개인화 표시
        if personalized:
            reasons.append("⭐ 회원님 선호")

        # 나이대 매칭
        if age_range:
            age_rules = self.recommendation_rules.get('age_based', {})
            if persona.id in age_rules.get(age_range, []):
                reasons.append(f"{age_range} 연령대에 적합")

        # 고민 매칭
        if concerns:
            concern_rules = self.recommendation_rules.get('concern_based', {})
            matching_concerns = []
            for concern in concerns:
                if persona.id in concern_rules.get(concern, []):
                    matching_concerns.append(concern)

            if matching_concerns:
                reasons.append(f"{', '.join(matching_concerns)} 전문")

        # 전문 분야
        if concerns:
            matching_specialties = [
                s for s in persona.specialties
                if any(c in s for c in concerns)
            ]
            if matching_specialties:
                reasons.append(f"{', '.join(matching_specialties[:2])} 특화")

        return " | ".join(reasons) if reasons else "추천 상담사"

    def search_personas(
        self,
        query: str = "",
        specialty: Optional[str] = None,
        gender: Optional[str] = None,
        personality_type: Optional[str] = None
    ) -> List[PersonaProfile]:
        """
        Search personas by various criteria

        Args:
            query: Search query (name, specialty, etc.)
            specialty: Filter by specialty
            gender: Filter by gender
            personality_type: Filter by personality type

        Returns:
            List of matching personas
        """
        results = []

        for persona in self.personas.values():
            # Check query
            if query:
                query_lower = query.lower()
                if not (
                    query_lower in persona.name.lower() or
                    query_lower in persona.display_name.lower() or
                    any(query_lower in s.lower() for s in persona.specialties) or
                    query_lower in persona.personality['type'].lower()
                ):
                    continue

            # Check specialty
            if specialty:
                if not any(specialty in s for s in persona.specialties):
                    continue

            # Check gender
            if gender and persona.gender != gender:
                continue

            # Check personality type
            if personality_type:
                if personality_type.lower() not in persona.personality['type'].lower():
                    continue

            results.append(persona)

        return results

    def generate_system_prompt(
        self,
        persona_id: str,
        user_context: Optional[str] = None,
        session_context: Optional[str] = None
    ) -> str:
        """
        Generate complete system prompt with persona

        Args:
            persona_id: Persona identifier
            user_context: User-specific context (name, age, concerns)
            session_context: Session-specific context

        Returns:
            Complete system prompt
        """
        persona = self.get_persona(persona_id)
        if not persona:
            logger.warning(f"Persona {persona_id} not found, using default")
            persona = self.get_default_persona()

        # Base persona prompt
        prompt = persona.system_prompt

        # Add user context
        if user_context:
            prompt += f"\n\n[내담자 정보]\n{user_context}"

        # Add session context
        if session_context:
            prompt += f"\n\n[세션 맥락]\n{session_context}"

        # Add general guidelines
        prompt += """

[상담 원칙]
- 항상 안전을 최우선으로 합니다
- 위기 상황(자살, 자해, 타해)은 즉시 감지하고 적절히 대응합니다
- 비밀보장 원칙을 지키되, 위험 상황에서는 예외를 설명합니다
- 진단이나 처방을 하지 않으며, 필요시 전문가 의뢰를 권장합니다
- 내담자의 자율성과 선택을 존중합니다
- 문화적 맥락(한국 문화)을 고려합니다

[응답 형식]
- 적절한 길이로 응답합니다 (너무 짧지도, 길지도 않게)
- 공감과 이해를 먼저 표현한 후, 탐색이나 개입을 합니다
- 한 번에 너무 많은 질문을 하지 않습니다
- 내담자의 페이스를 따라갑니다
"""

        return prompt

    def get_persona_greeting(self, persona_id: str, user_name: Optional[str] = None) -> str:
        """
        Get persona-specific greeting

        Args:
            persona_id: Persona identifier
            user_name: User name (if known)

        Returns:
            Personalized greeting
        """
        persona = self.get_persona(persona_id)
        if not persona:
            persona = self.get_default_persona()

        name_part = f"{user_name}님" if user_name else "손님"

        # Persona-specific greetings
        greetings = {
            "warm_mother": f"안녕하세요, {name_part}. 편안하게 이야기 나눠봐요.",
            "clinical_professional": f"안녕하세요, {name_part}. {persona.display_name}입니다. 무엇을 도와드릴까요?",
            "friendly_peer": f"안녕하세요, {name_part}! 편하게 얘기해주세요.",
            "calm_veteran": f"안녕하세요, {name_part}. 천천히 이야기 나눠보시죠.",
            "energetic_positive": f"안녕하세요, {name_part}! 만나서 반가워요. 함께 좋은 시간 만들어봐요!",
            "cbt_specialist": f"안녕하세요, {name_part}. 오늘은 어떤 것을 함께 살펴볼까요?",
            "teen_specialist": f"안녕, {name_part if user_name else '친구'}! 편하게 얘기해줘.",
            "workplace_specialist": f"안녕하세요, {name_part}. 직장 생활에서 어려운 점이 있으신가요?"
        }

        return greetings.get(persona_id, f"안녕하세요, {name_part}. 만나서 반갑습니다.")

    def get_statistics(self) -> Dict[str, Any]:
        """Get persona system statistics"""
        return {
            "total_personas": len(self.personas),
            "default_persona": self.default_persona_id,
            "personas_by_gender": {
                "male": sum(1 for p in self.personas.values() if p.gender == "male"),
                "female": sum(1 for p in self.personas.values() if p.gender == "female")
            },
            "personas_by_age": {
                age: sum(1 for p in self.personas.values() if p.age_range == age)
                for age in set(p.age_range for p in self.personas.values())
            },
            "available_specialties": list(set(
                specialty
                for p in self.personas.values()
                for specialty in p.specialties
            ))
        }


# Singleton instance
_persona_manager: Optional[PersonaManager] = None


def get_persona_manager() -> PersonaManager:
    """Get or create PersonaManager singleton"""
    global _persona_manager
    if _persona_manager is None:
        _persona_manager = PersonaManager()
    return _persona_manager


# Example usage
if __name__ == "__main__":
    # Initialize
    pm = PersonaManager()

    print("="*70)
    print("페르소나 관리 시스템 테스트")
    print("="*70)

    # List all personas
    print("\n1. 전체 페르소나 목록:")
    personas = pm.list_personas()
    for p in personas:
        print(f"\n{p['display_name']}")
        print(f"  ID: {p['id']}")
        print(f"  {p['intro']}")

    # Get specific persona
    print("\n\n2. 특정 페르소나 조회 (warm_mother):")
    persona = pm.get_persona("warm_mother")
    if persona:
        print(f"이름: {persona.display_name}")
        print(f"성격: {persona.personality['type']}")
        print(f"전문 분야: {', '.join(persona.specialties)}")
        print(f"상담 스타일: {persona.counseling_style['approach']}")

    # Recommend personas
    print("\n\n3. 페르소나 추천 (20대, 우울/불안):")
    recommendations = pm.recommend_personas(
        age_range="20대",
        concerns=["우울", "불안"],
        top_k=3
    )
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec['display_name']}")
        print(f"   추천 이유: {rec['reason']}")
        print(f"   점수: {rec['score']}")

    # Search personas
    print("\n\n4. 페르소나 검색 (전문 분야: 직장):")
    results = pm.search_personas(specialty="직장")
    for p in results:
        print(f"  - {p.display_name}: {', '.join(p.specialties[:3])}")

    # Generate system prompt
    print("\n\n5. 시스템 프롬프트 생성:")
    prompt = pm.generate_system_prompt(
        "warm_mother",
        user_context="이름: 철수님\n나이대: 20대\n주요 고민: 우울, 스트레스",
        session_context="3회차 상담"
    )
    print(prompt[:500] + "...")

    # Get greeting
    print("\n\n6. 페르소나별 인사말:")
    for pid in ["warm_mother", "friendly_peer", "clinical_professional"]:
        greeting = pm.get_persona_greeting(pid, "철수")
        print(f"  {pid}: {greeting}")

    # Statistics
    print("\n\n7. 통계:")
    stats = pm.get_statistics()
    print(f"  총 페르소나: {stats['total_personas']}개")
    print(f"  성별 분포: 남성 {stats['personas_by_gender']['male']}명, "
          f"여성 {stats['personas_by_gender']['female']}명")
    print(f"  전문 분야: {len(stats['available_specialties'])}개")

    print("\n" + "="*70)
