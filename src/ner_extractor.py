"""
Named Entity Recognition for Korean
한국어 개체명 인식 - 이름 및 개인정보 추출

프라이버시 주의: 추출된 정보는 암호화하여 저장해야 함
"""

import re
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class ExtractedInfo:
    """추출된 정보"""
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    concerns: List[str] = None

    def __post_init__(self):
        if self.concerns is None:
            self.concerns = []


class KoreanNERExtractor:
    """
    한국어 개체명 인식기

    주요 기능:
    - 이름 추출
    - 나이 추출
    - 성별 추출
    - 직업 추출
    - 주요 고민 추출
    """

    # 한국어 성씨 (빈도 높은 100개)
    KOREAN_SURNAMES = [
        "김", "이", "박", "최", "정", "강", "조", "윤", "장", "임",
        "한", "오", "서", "신", "권", "황", "안", "송", "류", "홍",
        "전", "고", "문", "손", "배", "조", "백", "허", "유", "남",
        "심", "노", "하", "곽", "성", "차", "주", "우", "구", "신",
        "라", "전", "민", "여", "추", "노", "지", "석", "선", "설"
    ]

    # 이름 패턴 (한국어)
    NAME_PATTERNS = [
        r"(?:제|내|저의|우리)\s*이름은\s*([가-힣]{2,4})(?:입니다|이에요|예요|야|에요)",
        r"([가-힣]{2,4})(?:이라고|라고)\s*(?:합니다|해요|불러요|불리)",
        r"(?:이름이|성함이)\s*([가-힣]{2,4})(?:입니다|이에요|예요)",
        r"저는\s*([가-힣]{2,4})(?:입니다|이에요|예요|야|라고)",
        r"([가-힣]{2,4})(?:이)\s*제\s*이름",
    ]

    # 나이 패턴
    AGE_PATTERNS = [
        r"(?:나이는|나이가)\s*(\d{1,2})(?:살|세|년생)",
        r"(\d{1,2})(?:살|세)\s*(?:입니다|이에요|예요)",
        r"올해\s*(\d{1,2})(?:살|세)",
        r"(\d{2})년생"
    ]

    # 성별 패턴
    GENDER_PATTERNS = [
        (r"남자|남성|아들|형|동생\(남\)|아버지|아빠", "male"),
        (r"여자|여성|딸|언니|누나|동생\(여\)|어머니|엄마", "female")
    ]

    # 직업 키워드
    OCCUPATION_KEYWORDS = [
        "학생", "대학생", "고등학생", "중학생",
        "회사원", "직장인", "사무직",
        "의사", "간호사", "선생님", "교사", "교수",
        "프로그래머", "개발자", "엔지니어",
        "주부", "전업주부",
        "자영업", "사업가", "대표",
        "공무원", "군인", "경찰",
        "무직", "백수", "취준생", "구직자"
    ]

    # 고민 키워드
    CONCERN_KEYWORDS = {
        "우울": ["우울", "슬픔", "무기력", "의욕 없"],
        "불안": ["불안", "걱정", "초조", "긴장"],
        "스트레스": ["스트레스", "압박", "부담"],
        "대인관계": ["친구", "관계", "사람", "외로", "고립"],
        "가족": ["부모", "가족", "엄마", "아빠", "형제"],
        "학업": ["공부", "시험", "성적", "학교", "수능"],
        "직장": ["회사", "직장", "상사", "동료", "업무"],
        "연애": ["연애", "이별", "사랑", "애인", "남자친구", "여자친구"],
        "진로": ["진로", "취업", "미래", "꿈"],
        "건강": ["건강", "몸", "아픔", "병"],
        "경제": ["돈", "경제", "빚", "생활비"],
        "자존감": ["자존감", "자신감", "열등감"]
    }

    def __init__(self):
        """초기화"""
        pass

    def extract_name(self, text: str) -> Optional[str]:
        """
        이름 추출

        Args:
            text: 입력 텍스트

        Returns:
            추출된 이름 (없으면 None)
        """
        # 패턴 매칭
        for pattern in self.NAME_PATTERNS:
            match = re.search(pattern, text)
            if match:
                name = match.group(1)

                # 성씨 검증 (첫 글자가 한국 성씨인지)
                if name[0] in self.KOREAN_SURNAMES:
                    # 이름 길이 검증 (2-4자)
                    if 2 <= len(name) <= 4:
                        return name

        return None

    def extract_age(self, text: str) -> Optional[int]:
        """
        나이 추출

        Args:
            text: 입력 텍스트

        Returns:
            추출된 나이 (없으면 None)
        """
        for pattern in self.AGE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                age_str = match.group(1)

                # 년생 패턴인 경우
                if "년생" in pattern:
                    birth_year = int(age_str)
                    # 00년대 vs 1900년대 구분
                    if birth_year < 30:
                        birth_year += 2000
                    else:
                        birth_year += 1900

                    from datetime import datetime
                    current_year = datetime.now().year
                    age = current_year - birth_year
                else:
                    age = int(age_str)

                # 나이 유효성 검증 (5-120)
                if 5 <= age <= 120:
                    return age

        return None

    def extract_gender(self, text: str) -> Optional[str]:
        """
        성별 추출

        Args:
            text: 입력 텍스트

        Returns:
            'male' or 'female' (없으면 None)
        """
        male_count = 0
        female_count = 0

        for pattern, gender in self.GENDER_PATTERNS:
            matches = re.findall(pattern, text)
            if gender == "male":
                male_count += len(matches)
            else:
                female_count += len(matches)

        # 더 많이 언급된 성별 반환
        if male_count > female_count:
            return "male"
        elif female_count > male_count:
            return "female"

        return None

    def extract_occupation(self, text: str) -> Optional[str]:
        """
        직업 추출

        Args:
            text: 입력 텍스트

        Returns:
            추출된 직업 (없으면 None)
        """
        text_lower = text.lower()

        for occupation in self.OCCUPATION_KEYWORDS:
            if occupation in text_lower:
                return occupation

        return None

    def extract_concerns(self, text: str, top_n: int = 3) -> List[str]:
        """
        주요 고민 추출

        Args:
            text: 입력 텍스트
            top_n: 상위 N개 반환

        Returns:
            고민 리스트
        """
        concern_scores = {}

        for concern, keywords in self.CONCERN_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                # 키워드 출현 횟수
                count = text.count(keyword)
                score += count

            if score > 0:
                concern_scores[concern] = score

        # 점수 순으로 정렬
        sorted_concerns = sorted(
            concern_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # 상위 N개 반환
        return [concern for concern, score in sorted_concerns[:top_n]]

    def extract_all(self, text: str) -> ExtractedInfo:
        """
        모든 정보 추출

        Args:
            text: 입력 텍스트

        Returns:
            ExtractedInfo 객체
        """
        return ExtractedInfo(
            name=self.extract_name(text),
            age=self.extract_age(text),
            gender=self.extract_gender(text),
            occupation=self.extract_occupation(text),
            concerns=self.extract_concerns(text)
        )

    def generate_preferred_name(self, extracted_name: Optional[str], gender: Optional[str] = None) -> str:
        """
        선호 호칭 생성

        Args:
            extracted_name: 추출된 이름
            gender: 성별

        Returns:
            선호 호칭 (예: "철수님", "손님")
        """
        if extracted_name:
            # 이름이 있으면 "이름 + 님"
            return f"{extracted_name}님"
        elif gender == "male":
            return "고객님"
        elif gender == "female":
            return "고객님"
        else:
            return "손님"


class ConversationAnalyzer:
    """
    대화 전체 분석

    여러 턴에 걸쳐 정보 수집 및 업데이트
    """

    def __init__(self):
        self.ner = KoreanNERExtractor()
        self.accumulated_info = ExtractedInfo()

    def update_from_message(self, message: str):
        """
        메시지에서 정보 추출 및 누적

        Args:
            message: 사용자 메시지
        """
        new_info = self.ner.extract_all(message)

        # 새로 추출된 정보로 업데이트 (기존 정보는 유지)
        if new_info.name and not self.accumulated_info.name:
            self.accumulated_info.name = new_info.name

        if new_info.age and not self.accumulated_info.age:
            self.accumulated_info.age = new_info.age

        if new_info.gender and not self.accumulated_info.gender:
            self.accumulated_info.gender = new_info.gender

        if new_info.occupation and not self.accumulated_info.occupation:
            self.accumulated_info.occupation = new_info.occupation

        # 고민은 누적
        for concern in new_info.concerns:
            if concern not in self.accumulated_info.concerns:
                self.accumulated_info.concerns.append(concern)

    def get_info(self) -> ExtractedInfo:
        """누적된 정보 반환"""
        return self.accumulated_info

    def get_preferred_name(self) -> str:
        """선호 호칭 반환"""
        return self.ner.generate_preferred_name(
            self.accumulated_info.name,
            self.accumulated_info.gender
        )


# ============================================================================
# Utility Functions
# ============================================================================

def extract_info_from_conversation(conversation_history: List[Dict[str, str]]) -> ExtractedInfo:
    """
    전체 대화에서 정보 추출

    Args:
        conversation_history: 대화 기록 [{"role": "user", "content": "..."}]

    Returns:
        ExtractedInfo 객체
    """
    analyzer = ConversationAnalyzer()

    for turn in conversation_history:
        if turn["role"] == "user":
            analyzer.update_from_message(turn["content"])

    return analyzer.get_info()


# ============================================================================
# Testing
# ============================================================================

if __name__ == "__main__":
    # 테스트
    ner = KoreanNERExtractor()

    test_texts = [
        "안녕하세요, 제 이름은 김철수입니다. 나이는 28살이에요.",
        "저는 이영희라고 해요. 올해 35세 여자입니다.",
        "박민수라고 합니다. 회사원이고 직장 스트레스가 심해요.",
        "대학생인데 우울하고 불안해요. 공부도 안 되고...",
    ]

    print("=" * 70)
    print("한국어 NER 테스트")
    print("=" * 70)

    for text in test_texts:
        print(f"\n입력: {text}")
        info = ner.extract_all(text)
        print(f"이름: {info.name}")
        print(f"나이: {info.age}")
        print(f"성별: {info.gender}")
        print(f"직업: {info.occupation}")
        print(f"고민: {info.concerns}")
        print(f"선호 호칭: {ner.generate_preferred_name(info.name, info.gender)}")
