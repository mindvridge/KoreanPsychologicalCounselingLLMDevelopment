"""
Personalization API Usage Example
개인화 API 사용 예제

Demonstrates:
- User identification
- Personalized greetings
- Long-term memory
- Assessment tracking
- User profile management
"""

import requests
import json
from typing import Optional


class PersonalizedMentalHealthClient:
    """클라이언트 with personalization support"""

    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["X-API-Key"] = api_key

    def chat(self, message: str, user_id: Optional[str] = None,
             session_id: Optional[str] = None, consent: bool = True):
        """
        Send a chat message with personalization

        Args:
            message: User message
            user_id: User identifier (e.g., email hash) - enables personalization
            session_id: Session ID (optional)
            consent: Data storage consent
        """
        url = f"{self.base_url}/api/v1/chat"

        payload = {
            "message": message,
            "consent": consent
        }

        if user_id:
            payload["user_id"] = user_id

        if session_id:
            payload["session_id"] = session_id

        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def conduct_assessment(self, assessment_type: str, responses: list,
                          session_id: str, user_id: Optional[str] = None):
        """
        Conduct psychological assessment with user tracking

        Args:
            assessment_type: 'phq9', 'gad7', or 'k10'
            responses: List of response scores
            session_id: Session ID
            user_id: User identifier (saves to database if provided)
        """
        url = f"{self.base_url}/api/v1/assessment"

        payload = {
            "session_id": session_id,
            "assessment_type": assessment_type,
            "responses": responses
        }

        if user_id:
            payload["user_id"] = user_id

        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_user_profile(self, user_id: str):
        """Get user profile"""
        url = f"{self.base_url}/api/v1/user/{user_id}/profile"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_user_history(self, user_id: str, limit: int = 20):
        """Get conversation history"""
        url = f"{self.base_url}/api/v1/user/{user_id}/history"
        params = {"limit": limit}
        response = requests.get(url, params=params, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_user_assessments(self, user_id: str, assessment_type: Optional[str] = None):
        """Get assessment history and trends"""
        url = f"{self.base_url}/api/v1/user/{user_id}/assessments"
        params = {}
        if assessment_type:
            params["assessment_type"] = assessment_type
        response = requests.get(url, params=params, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_user_stats(self, user_id: str):
        """Get user statistics"""
        url = f"{self.base_url}/api/v1/user/{user_id}/stats"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def update_consent(self, user_id: str, consent_given: bool,
                      data_retention_days: Optional[int] = None):
        """Update user consent"""
        url = f"{self.base_url}/api/v1/user/{user_id}/consent"
        payload = {"consent_given": consent_given}
        if data_retention_days:
            payload["data_retention_days"] = data_retention_days
        response = requests.put(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def delete_user(self, user_id: str):
        """Delete user data (Right to be Forgotten)"""
        url = f"{self.base_url}/api/v1/user/{user_id}"
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()
        return response.json()


def example_1_personalized_conversation():
    """Example 1: Personalized conversation with name extraction"""
    print("="*70)
    print("Example 1: Personalized Conversation")
    print("="*70)

    client = PersonalizedMentalHealthClient()
    user_id = "user_example_1"  # In production, use hashed email or UUID

    # First conversation - introducing yourself
    print("\n1. First message (introducing name):")
    result = client.chat(
        message="안녕하세요. 제 이름은 김철수입니다. 나이는 28살이에요.",
        user_id=user_id
    )
    print(f"AI: {result['response']}")
    print(f"Session ID: {result['session_id']}")

    # Second message
    print("\n2. Second message:")
    result = client.chat(
        message="요즘 직장 스트레스 때문에 우울해요.",
        user_id=user_id,
        session_id=result['session_id']
    )
    print(f"AI: {result['response']}")

    # Get user profile (name should be extracted)
    print("\n3. User profile:")
    profile = client.get_user_profile(user_id)
    print(f"Preferred Name: {profile['preferred_name']}")
    print(f"Age Range: {profile['age_range']}")
    print(f"Main Concerns: {profile['main_concerns']}")
    print(f"Total Messages: {profile['total_messages']}")

    print("\n" + "="*70)


def example_2_returning_user():
    """Example 2: Returning user gets personalized greeting"""
    print("="*70)
    print("Example 2: Returning User")
    print("="*70)

    client = PersonalizedMentalHealthClient()
    user_id = "user_example_2"

    # First visit
    print("\n1. First visit:")
    result1 = client.chat(
        message="안녕하세요. 이영희라고 합니다.",
        user_id=user_id
    )
    print(f"AI: {result1['response']}")

    # Later visit (new session)
    print("\n2. Returning visit (new session):")
    result2 = client.chat(
        message="다시 찾아왔어요.",
        user_id=user_id
    )
    print(f"AI: {result2['response']}")  # Should include personalized greeting

    print("\n" + "="*70)


def example_3_assessment_tracking():
    """Example 3: Assessment tracking over time"""
    print("="*70)
    print("Example 3: Assessment Tracking")
    print("="*70)

    client = PersonalizedMentalHealthClient()
    user_id = "user_example_3"

    # First conversation
    print("\n1. Start conversation:")
    result = client.chat(
        message="안녕하세요. 우울증 검사를 받고 싶어요.",
        user_id=user_id
    )
    session_id = result['session_id']
    print(f"AI: {result['response']}")

    # Conduct PHQ-9 assessment
    print("\n2. Conducting PHQ-9 assessment:")
    phq9_responses = [2, 2, 1, 2, 1, 1, 2, 1, 0]  # Moderate depression
    assessment_result = client.conduct_assessment(
        assessment_type="phq9",
        responses=phq9_responses,
        session_id=session_id,
        user_id=user_id  # Save to database
    )
    print(f"Score: {assessment_result['score']}")
    print(f"Severity: {assessment_result['severity']}")
    print(f"Interpretation: {assessment_result['interpretation']}")

    # Get assessment history
    print("\n3. Get assessment history:")
    assessments = client.get_user_assessments(user_id, assessment_type="phq9")
    print(f"Total assessments: {len(assessments['assessments'])}")
    if assessments['trend']:
        print(f"Trend: {assessments['trend']}")

    print("\n" + "="*70)


def example_4_conversation_history():
    """Example 4: Retrieve conversation history"""
    print("="*70)
    print("Example 4: Conversation History")
    print("="*70)

    client = PersonalizedMentalHealthClient()
    user_id = "user_example_4"

    # Have multiple conversations
    print("\n1. Having conversations:")
    messages = [
        "안녕하세요. 박민수입니다.",
        "직장에서 스트레스를 많이 받아요.",
        "상사와의 관계가 힘들어요."
    ]

    session_id = None
    for msg in messages:
        result = client.chat(
            message=msg,
            user_id=user_id,
            session_id=session_id
        )
        session_id = result['session_id']
        print(f"User: {msg}")
        print(f"AI: {result['response'][:50]}...")

    # Get conversation history
    print("\n2. Retrieving conversation history:")
    history = client.get_user_history(user_id, limit=10)
    print(f"Total conversations: {history['total_count']}")
    for i, turn in enumerate(history['conversations'][:3]):
        print(f"  {i+1}. [{turn['role']}] {turn['content'][:40]}...")

    print("\n" + "="*70)


def example_5_user_stats():
    """Example 5: User statistics"""
    print("="*70)
    print("Example 5: User Statistics")
    print("="*70)

    client = PersonalizedMentalHealthClient()
    user_id = "user_example_1"  # Use existing user

    try:
        stats = client.get_user_stats(user_id)
        print("\nUser Statistics:")
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    except requests.exceptions.HTTPError as e:
        print(f"Error: {e}")
        print("Note: User might not exist yet. Run example_1 first.")

    print("\n" + "="*70)


def example_6_consent_management():
    """Example 6: Consent and data management (PIPA compliance)"""
    print("="*70)
    print("Example 6: Consent Management")
    print("="*70)

    client = PersonalizedMentalHealthClient()
    user_id = "user_consent_example"

    # Create user with conversation
    print("\n1. Create user:")
    result = client.chat(
        message="안녕하세요. 테스트입니다.",
        user_id=user_id,
        consent=True
    )
    print(f"User created: {user_id}")

    # Update consent
    print("\n2. Update consent (reduce retention to 30 days):")
    consent_result = client.update_consent(
        user_id=user_id,
        consent_given=True,
        data_retention_days=30
    )
    print(f"Consent updated: {consent_result}")

    # Withdraw consent
    print("\n3. Withdraw consent:")
    consent_result = client.update_consent(
        user_id=user_id,
        consent_given=False
    )
    print(f"Consent withdrawn: {consent_result}")

    # Delete user (Right to be Forgotten)
    print("\n4. Delete user data (Right to be Forgotten):")
    delete_result = client.delete_user(user_id)
    print(f"User deleted: {delete_result}")

    print("\n" + "="*70)


def main():
    """Run all examples"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*10 + "Personalization API Examples" + " "*30 + "║")
    print("║" + " "*10 + "개인화 API 사용 예제" + " "*37 + "║")
    print("╚" + "="*68 + "╝")
    print("\n")

    print("Make sure the API server is running on http://localhost:8000")
    print("Start server: python src/api.py")
    print("\n")

    try:
        # Run examples
        example_1_personalized_conversation()
        input("\nPress Enter to continue to Example 2...")

        example_2_returning_user()
        input("\nPress Enter to continue to Example 3...")

        example_3_assessment_tracking()
        input("\nPress Enter to continue to Example 4...")

        example_4_conversation_history()
        input("\nPress Enter to continue to Example 5...")

        example_5_user_stats()
        input("\nPress Enter to continue to Example 6...")

        example_6_consent_management()

        print("\n✓ All examples completed!")

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API server")
        print("Please start the server first: python src/api.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
