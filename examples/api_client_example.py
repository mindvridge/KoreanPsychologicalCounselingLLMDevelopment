"""
Korean Mental Health Counseling API - Client Example
FastAPI를 사용한 API 호출 예제
"""

import requests
import json
import time
from typing import Optional, Dict, List

class MentalHealthAPIClient:
    """
    한국형 심리상담 API 클라이언트
    """
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        """
        초기화
        
        Args:
            base_url: API 서버 주소
            api_key: API 인증 키 (선택사항)
        """
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json"
        }
        
        if api_key:
            self.headers["X-API-Key"] = api_key
    
    def health_check(self) -> Dict:
        """건강 체크"""
        response = requests.get(f"{self.base_url}/api/v1/health")
        response.raise_for_status()
        return response.json()
    
    def chat(
        self, 
        message: str, 
        session_id: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict:
        """
        대화 메시지 전송
        
        Args:
            message: 사용자 메시지
            session_id: 세션 ID (선택사항)
            conversation_history: 대화 기록 (선택사항)
        
        Returns:
            응답 딕셔너리
        """
        data = {"message": message}
        
        if session_id:
            data["session_id"] = session_id
        
        if conversation_history:
            data["conversation_history"] = conversation_history
        
        response = requests.post(
            f"{self.base_url}/api/v1/chat",
            json=data,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def conduct_assessment(
        self, 
        session_id: str,
        assessment_type: str,
        responses: List[int]
    ) -> Dict:
        """
        심리 평가 실시
        
        Args:
            session_id: 세션 ID
            assessment_type: 평가 유형 (phq9, gad7, k10)
            responses: 응답 리스트
        
        Returns:
            평가 결과
        """
        data = {
            "session_id": session_id,
            "assessment_type": assessment_type,
            "responses": responses
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/assessment",
            json=data,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_stats(self) -> Dict:
        """시스템 통계 조회"""
        response = requests.get(
            f"{self.base_url}/api/v1/stats",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()


def example_conversation():
    """
    예제: 완전한 대화 시나리오
    """
    print("="*70)
    print("한국형 심리상담 API 클라이언트 예제")
    print("="*70)
    
    # 클라이언트 초기화
    client = MentalHealthAPIClient()
    
    try:
        # 1. 건강 체크
        print("\n[1] 건강 체크...")
        health = client.health_check()
        print(f"   상태: {health['status']}")
        
        # 2. 대화 시작
        print("\n[2] 대화 시작...")
        response1 = client.chat(message="안녕하세요, 요즘 우울해서 힘들어요")
        
        session_id = response1['session_id']
        print(f"   세션 ID: {session_id}")
        print(f"   AI 응답: {response1['response'][:100]}...")
        print(f"   위기 감지: {response1['crisis_detected']}")
        
        # 3. PHQ-9 평가
        print("\n[3] PHQ-9 우울증 평가...")
        time.sleep(1)
        
        phq9_responses = [2, 2, 2, 1, 1, 0, 1, 2, 0]
        assessment = client.conduct_assessment(
            session_id=session_id,
            assessment_type="phq9",
            responses=phq9_responses
        )
        
        print(f"   점수: {assessment['score']}")
        print(f"   심각도: {assessment['severity']}")
        
        print("\n✓ 테스트 완료!")
        
    except requests.exceptions.ConnectionError:
        print("\n✗ 연결 오류: API 서버를 먼저 실행하세요")
        print("   실행 명령: python src/api.py")
    except Exception as e:
        print(f"\n✗ 에러: {e}")


if __name__ == "__main__":
    example_conversation()
