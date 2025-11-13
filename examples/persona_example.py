"""
Counselor Persona System Examples
상담사 페르소나 시스템 사용 예제

Demonstrates:
- Listing available personas
- Getting persona details
- Persona recommendations
- Searching personas
- Using personas in chat
"""

import requests
import json
from typing import Optional, List


class PersonaAPIClient:
    """페르소나 API 클라이언트"""

    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["X-API-Key"] = api_key

    def list_personas(self, include_details: bool = False):
        """Get list of all personas"""
        url = f"{self.base_url}/api/v1/personas"
        params = {"include_details": include_details}
        response = requests.get(url, params=params, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_persona(self, persona_id: str):
        """Get detailed persona information"""
        url = f"{self.base_url}/api/v1/personas/{persona_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def recommend_personas(self, age_range: Optional[str] = None,
                          concerns: Optional[List[str]] = None, top_k: int = 3):
        """Get persona recommendations"""
        url = f"{self.base_url}/api/v1/personas/recommend"
        payload = {"top_k": top_k}
        if age_range:
            payload["age_range"] = age_range
        if concerns:
            payload["concerns"] = concerns
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def search_personas(self, query: str = "", specialty: Optional[str] = None,
                       gender: Optional[str] = None):
        """Search personas"""
        url = f"{self.base_url}/api/v1/personas/search"
        params = {}
        if query:
            params["query"] = query
        if specialty:
            params["specialty"] = specialty
        if gender:
            params["gender"] = gender
        response = requests.get(url, params=params, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_persona_stats(self):
        """Get persona system statistics"""
        url = f"{self.base_url}/api/v1/personas/stats"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def chat(self, message: str, persona_id: Optional[str] = None,
             session_id: Optional[str] = None, user_id: Optional[str] = None):
        """Send chat message with persona"""
        url = f"{self.base_url}/api/v1/chat"
        payload = {"message": message}
        if persona_id:
            payload["persona_id"] = persona_id
        if session_id:
            payload["session_id"] = session_id
        if user_id:
            payload["user_id"] = user_id
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()


def example_1_list_personas():
    """Example 1: List all available personas"""
    print("="*70)
    print("Example 1: 전체 페르소나 목록")
    print("="*70)

    client = PersonaAPIClient()

    # Get persona list
    result = client.list_personas(include_details=False)

    print(f"\n총 {result['total']}명의 상담사가 있습니다.\n")

    for i, persona in enumerate(result['personas'], 1):
        print(f"{i}. {persona['display_name']}")
        print(f"   성격: {persona['personality_type']}")
        print(f"   전문 분야: {', '.join(persona['specialties'][:3])}")
        print()

    print("="*70)


def example_2_persona_details():
    """Example 2: Get detailed persona information"""
    print("\n" + "="*70)
    print("Example 2: 상담사 상세 정보")
    print("="*70)

    client = PersonaAPIClient()

    # Get specific persona
    persona_id = "warm_mother"
    result = client.get_persona(persona_id)

    print(f"\n이름: {result['display_name']}")
    print(f"성별/나이: {result['age_range']} {result['gender']}")
    print(f"성격: {result['personality_type']}")
    print(f"\n전문 분야:")
    for specialty in result['specialties']:
        print(f"  - {specialty}")
    print(f"\n상담 접근법: {result['counseling_style']['approach']}")
    print(f"어조: {result['counseling_style']['tone']}")

    print("\n" + "="*70)


def example_3_recommend_personas():
    """Example 3: Get persona recommendations"""
    print("\n" + "="*70)
    print("Example 3: 페르소나 추천")
    print("="*70)

    client = PersonaAPIClient()

    # Case 1: 20대, 우울/불안
    print("\n[사례 1] 20대, 우울과 불안으로 고민 중")
    result = client.recommend_personas(
        age_range="20대",
        concerns=["우울", "불안"],
        top_k=3
    )

    for i, rec in enumerate(result['recommendations'], 1):
        print(f"\n{i}. {rec['display_name']}")
        print(f"   추천 이유: {rec['reason']}")
        print(f"   성격: {rec['personality_type']}")
        print(f"   전문 분야: {', '.join(rec['specialties'][:3])}")

    # Case 2: 40대, 직장 스트레스
    print("\n\n[사례 2] 40대, 직장 스트레스와 번아웃")
    result = client.recommend_personas(
        age_range="40대",
        concerns=["직장", "번아웃"],
        top_k=3
    )

    for i, rec in enumerate(result['recommendations'], 1):
        print(f"\n{i}. {rec['display_name']}")
        print(f"   추천 이유: {rec['reason']}")

    # Case 3: 청소년, 학업 스트레스
    print("\n\n[사례 3] 10대, 학업 스트레스와 친구 관계")
    result = client.recommend_personas(
        age_range="10대",
        concerns=["학업", "대인관계"],
        top_k=3
    )

    for i, rec in enumerate(result['recommendations'], 1):
        print(f"\n{i}. {rec['display_name']}")
        print(f"   추천 이유: {rec['reason']}")

    print("\n" + "="*70)


def example_4_search_personas():
    """Example 4: Search personas"""
    print("\n" + "="*70)
    print("Example 4: 페르소나 검색")
    print("="*70)

    client = PersonaAPIClient()

    # Search by specialty
    print("\n[검색 1] 전문 분야: 우울증")
    result = client.search_personas(specialty="우울")

    print(f"검색 결과: {result['total']}명")
    for persona in result['results']:
        print(f"  - {persona['display_name']}: {', '.join(persona['specialties'][:3])}")

    # Search by gender
    print("\n[검색 2] 성별: 여성 상담사")
    result = client.search_personas(gender="female")

    print(f"검색 결과: {result['total']}명")
    for persona in result['results']:
        print(f"  - {persona['display_name']} ({persona['age_range']})")

    # Search by query
    print("\n[검색 3] 키워드: '긍정적'")
    result = client.search_personas(query="긍정")

    print(f"검색 결과: {result['total']}명")
    for persona in result['results']:
        print(f"  - {persona['display_name']}: {persona['personality_type']}")

    print("\n" + "="*70)


def example_5_persona_stats():
    """Example 5: Get persona statistics"""
    print("\n" + "="*70)
    print("Example 5: 페르소나 시스템 통계")
    print("="*70)

    client = PersonaAPIClient()

    stats = client.get_persona_stats()

    print(f"\n총 페르소나: {stats['total_personas']}명")
    print(f"기본 페르소나: {stats['default_persona']}")

    print("\n성별 분포:")
    for gender, count in stats['personas_by_gender'].items():
        gender_kr = "남성" if gender == "male" else "여성"
        print(f"  {gender_kr}: {count}명")

    print("\n연령대 분포:")
    for age, count in stats['personas_by_age'].items():
        print(f"  {age}: {count}명")

    print(f"\n전문 분야: {len(stats['available_specialties'])}개")
    print("주요 전문 분야:")
    for specialty in list(stats['available_specialties'])[:10]:
        print(f"  - {specialty}")

    print("\n" + "="*70)


def example_6_chat_with_persona():
    """Example 6: Chat with different personas"""
    print("\n" + "="*70)
    print("Example 6: 페르소나별 대화 체험")
    print("="*70)

    client = PersonaAPIClient()
    message = "안녕하세요. 요즘 직장 스트레스 때문에 힘들어요."

    personas_to_try = [
        "warm_mother",
        "clinical_professional",
        "friendly_peer",
        "workplace_specialist"
    ]

    for persona_id in personas_to_try:
        # Get persona info
        persona = client.get_persona(persona_id)

        print(f"\n{'='*70}")
        print(f"상담사: {persona['display_name']}")
        print(f"성격: {persona['personality_type']}")
        print(f"{'='*70}")

        print(f"\n사용자: {message}")

        try:
            # Note: This requires the chat endpoint to support persona_id
            # For now, it will use the default persona
            response = client.chat(message, persona_id=persona_id)
            print(f"\n{persona['display_name']}: {response['response'][:200]}...")
        except Exception as e:
            print(f"\n[주의] 페르소나 기능은 아직 채팅 엔드포인트에 완전히 통합되지 않았습니다.")
            print(f"현재는 페르소나 정보 조회만 가능합니다.")
            break

    print("\n" + "="*70)


def example_7_persona_matching():
    """Example 7: Find best matching persona"""
    print("\n" + "="*70)
    print("Example 7: 최적 페르소나 매칭")
    print("="*70)

    client = PersonaAPIClient()

    # Scenario
    print("\n[상황]")
    print("이름: 김민지")
    print("나이: 28세 (20대)")
    print("고민: 회사에서의 우울감, 상사와의 갈등, 번아웃")

    # Get recommendations
    result = client.recommend_personas(
        age_range="20대",
        concerns=["우울", "직장", "번아웃"],
        top_k=3
    )

    print("\n[추천 상담사]")
    for i, rec in enumerate(result['recommendations'], 1):
        score = rec.get('score', 0)
        print(f"\n{i}위. {rec['display_name']} (점수: {score:.1f})")
        print(f"     {rec['reason']}")
        print(f"     전문 분야: {', '.join(rec['specialties'][:3])}")

    # Get detailed info for top recommendation
    if result['recommendations']:
        top_rec = result['recommendations'][0]
        print(f"\n[추천 1위 상담사 상세 정보]")
        persona = client.get_persona(top_rec['id'])
        print(f"이름: {persona['display_name']}")
        print(f"상담 접근법: {persona['counseling_style']['approach']}")
        print(f"어조: {persona['counseling_style']['tone']}")
        print(f"\n강점:")
        # Note: strengths are not in the response model yet
        print("  - 전문적이고 체계적인 접근")
        print("  - 실질적인 해결 방안 제시")

    print("\n" + "="*70)


def main():
    """Run all examples"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "Counselor Persona System" + " "*29 + "║")
    print("║" + " "*17 + "상담사 페르소나 시스템" + " "*30 + "║")
    print("╚" + "="*68 + "╝")
    print("\n")

    print("이 예제는 다양한 상담사 페르소나 시스템을 시연합니다.")
    print("API 서버가 http://localhost:8000에서 실행 중이어야 합니다.")
    print("\n")

    try:
        # Run examples
        example_1_list_personas()
        input("\nPress Enter to continue to Example 2...")

        example_2_persona_details()
        input("\nPress Enter to continue to Example 3...")

        example_3_recommend_personas()
        input("\nPress Enter to continue to Example 4...")

        example_4_search_personas()
        input("\nPress Enter to continue to Example 5...")

        example_5_persona_stats()
        input("\nPress Enter to continue to Example 6...")

        example_6_chat_with_persona()
        input("\nPress Enter to continue to Example 7...")

        example_7_persona_matching()

        print("\n✓ All examples completed!")
        print("\n[다음 단계]")
        print("1. Swagger UI에서 API 탐색: http://localhost:8000/docs")
        print("2. 페르소나 추천 API를 사용하여 맞춤형 상담사 찾기")
        print("3. 사용자 프로필과 페르소나를 결합하여 개인화된 상담 경험 제공")

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API server")
        print("Please start the server first: python src/api.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
