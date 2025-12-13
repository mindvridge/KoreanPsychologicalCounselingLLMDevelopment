# -*- coding: utf-8 -*-
"""
음악 치료 모듈 (Music Therapy Module)

감정에 맞는 음악 추천, 음악 감상 가이드, 음악을 활용한
감정 표현 및 처리를 채팅에 통합합니다.

Author: MindVridge AI Team
Version: 1.0.0
"""

import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any


class MusicMood(Enum):
    """음악 분위기/감정"""
    CALMING = "calming"                 # 차분한
    UPLIFTING = "uplifting"             # 기분 좋은
    ENERGIZING = "energizing"           # 활기찬
    SAD = "sad"                         # 슬픈
    ANGRY = "angry"                     # 화난
    NOSTALGIC = "nostalgic"             # 향수어린
    HOPEFUL = "hopeful"                 # 희망적인
    PEACEFUL = "peaceful"               # 평화로운
    MELANCHOLIC = "melancholic"         # 우울한
    EMPOWERING = "empowering"           # 힘을 주는


class MusicGenre(Enum):
    """음악 장르"""
    CLASSICAL = "classical"
    JAZZ = "jazz"
    AMBIENT = "ambient"
    KPOP = "kpop"
    BALLAD = "ballad"
    FOLK = "folk"
    NATURE_SOUNDS = "nature_sounds"
    MEDITATION = "meditation"
    INSTRUMENTAL = "instrumental"
    ACOUSTIC = "acoustic"


class TherapeuticTechnique(Enum):
    """음악 치료 기법"""
    ISO_PRINCIPLE = "iso_principle"         # 아이소 원칙 (현재 감정 → 목표 감정)
    RECEPTIVE = "receptive"                 # 수용적 감상
    ACTIVE = "active"                       # 능동적 참여
    SONGWRITING = "songwriting"             # 노래 가사 쓰기
    LYRIC_ANALYSIS = "lyric_analysis"       # 가사 분석
    MUSICAL_REMINISCENCE = "reminiscence"   # 음악 회상


@dataclass
class MusicRecommendation:
    """음악 추천"""
    mood: MusicMood
    genre: MusicGenre
    title_suggestion: str
    korean_artists: List[str]
    international_artists: List[str]
    therapeutic_purpose: str
    listening_instructions: str


@dataclass
class IsoPlaylist:
    """아이소 원칙 플레이리스트"""
    current_mood: MusicMood
    target_mood: MusicMood
    stages: List[Dict[str, Any]]  # 단계별 음악 특성
    duration_minutes: int
    description: str


@dataclass
class MusicTherapySession:
    """음악 치료 세션"""
    session_id: str
    user_id: str
    technique: TherapeuticTechnique
    current_step: str = "intro"
    started_at: datetime = field(default_factory=datetime.now)
    user_responses: List[str] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)


class MusicRecommendationLibrary:
    """음악 추천 라이브러리"""

    def __init__(self):
        self.recommendations = self._initialize_recommendations()
        self.iso_playlists = self._initialize_iso_playlists()

    def _initialize_recommendations(self) -> Dict[MusicMood, List[MusicRecommendation]]:
        """음악 추천 초기화"""
        return {
            MusicMood.CALMING: [
                MusicRecommendation(
                    mood=MusicMood.CALMING,
                    genre=MusicGenre.CLASSICAL,
                    title_suggestion="느린 템포의 피아노 곡",
                    korean_artists=["윤한", "이루마", "Yiruma"],
                    international_artists=["Ludovico Einaudi", "Max Richter", "Ólafur Arnalds"],
                    therapeutic_purpose="심신 이완, 스트레스 감소",
                    listening_instructions="눈을 감고 선율을 따라가 보세요. 호흡을 음악에 맞춰보세요."
                ),
                MusicRecommendation(
                    mood=MusicMood.CALMING,
                    genre=MusicGenre.NATURE_SOUNDS,
                    title_suggestion="비 소리, 파도 소리, 새소리",
                    korean_artists=["자연의 소리"],
                    international_artists=["Nature Sounds"],
                    therapeutic_purpose="자연과의 연결, 이완",
                    listening_instructions="자연 속에 있다고 상상해 보세요. 소리의 디테일에 집중해 보세요."
                ),
                MusicRecommendation(
                    mood=MusicMood.CALMING,
                    genre=MusicGenre.AMBIENT,
                    title_suggestion="앰비언트, 뉴에이지 음악",
                    korean_artists=["이적", "가을방학"],
                    international_artists=["Brian Eno", "Sigur Rós", "Tycho"],
                    therapeutic_purpose="명상적 상태, 깊은 이완",
                    listening_instructions="음악이 배경이 되게 하고, 생각이 흘러가게 두세요."
                )
            ],

            MusicMood.SAD: [
                MusicRecommendation(
                    mood=MusicMood.SAD,
                    genre=MusicGenre.BALLAD,
                    title_suggestion="슬픈 발라드",
                    korean_artists=["이문세", "김광석", "김동률", "성시경"],
                    international_artists=["Adele", "Sam Smith", "Billie Eilish"],
                    therapeutic_purpose="감정 인정과 수용, 카타르시스",
                    listening_instructions="울어도 괜찮아요. 음악과 함께 감정을 느껴보세요."
                ),
                MusicRecommendation(
                    mood=MusicMood.SAD,
                    genre=MusicGenre.CLASSICAL,
                    title_suggestion="슬픈 클래식 (바이올린, 첼로)",
                    korean_artists=["정경화"],
                    international_artists=["Yo-Yo Ma", "Jacqueline du Pré"],
                    therapeutic_purpose="감정의 깊이 탐색",
                    listening_instructions="선율이 당신의 감정을 대변해 줍니다. 그냥 느껴보세요."
                )
            ],

            MusicMood.UPLIFTING: [
                MusicRecommendation(
                    mood=MusicMood.UPLIFTING,
                    genre=MusicGenre.KPOP,
                    title_suggestion="밝고 경쾌한 K-pop",
                    korean_artists=["BTS", "아이유", "볼빨간사춘기", "악뮤"],
                    international_artists=["Pharrell Williams", "Bruno Mars"],
                    therapeutic_purpose="기분 전환, 에너지 충전",
                    listening_instructions="몸을 움직여 보세요. 리듬에 맞춰 고개를 끄덕여도 좋아요."
                ),
                MusicRecommendation(
                    mood=MusicMood.UPLIFTING,
                    genre=MusicGenre.ACOUSTIC,
                    title_suggestion="밝은 어쿠스틱",
                    korean_artists=["장범준", "정승환", "소란"],
                    international_artists=["Jason Mraz", "Jack Johnson"],
                    therapeutic_purpose="따뜻한 위로, 긍정적 감정",
                    listening_instructions="가사의 의미를 되새겨 보세요."
                )
            ],

            MusicMood.ENERGIZING: [
                MusicRecommendation(
                    mood=MusicMood.ENERGIZING,
                    genre=MusicGenre.KPOP,
                    title_suggestion="댄스, 힙합",
                    korean_artists=["BTS", "BLACKPINK", "세븐틴", "Stray Kids"],
                    international_artists=["Beyoncé", "Dua Lipa", "The Weeknd"],
                    therapeutic_purpose="에너지 발산, 활력 충전",
                    listening_instructions="춤을 춰보세요! 마음껏 몸을 움직여 보세요."
                )
            ],

            MusicMood.ANGRY: [
                MusicRecommendation(
                    mood=MusicMood.ANGRY,
                    genre=MusicGenre.KPOP,
                    title_suggestion="강렬한 록, 힙합",
                    korean_artists=["YB밴드", "자우림", "에픽하이"],
                    international_artists=["Linkin Park", "Eminem", "Rage Against the Machine"],
                    therapeutic_purpose="분노 표현과 해소",
                    listening_instructions="소리를 지르거나 쿠션을 치면서 들어도 좋아요. 감정을 밖으로 내보내세요."
                )
            ],

            MusicMood.PEACEFUL: [
                MusicRecommendation(
                    mood=MusicMood.PEACEFUL,
                    genre=MusicGenre.MEDITATION,
                    title_suggestion="명상 음악, 티벳 싱잉볼",
                    korean_artists=["명상음악"],
                    international_artists=["Deuter", "Karunesh"],
                    therapeutic_purpose="내면의 평화, 명상",
                    listening_instructions="호흡에 집중하며 들어보세요. 생각을 내려놓으세요."
                )
            ],

            MusicMood.HOPEFUL: [
                MusicRecommendation(
                    mood=MusicMood.HOPEFUL,
                    genre=MusicGenre.BALLAD,
                    title_suggestion="희망적인 가사의 노래",
                    korean_artists=["윤도현", "이승환", "김범수"],
                    international_artists=["Coldplay", "U2", "OneRepublic"],
                    therapeutic_purpose="희망 고취, 동기 부여",
                    listening_instructions="가사를 주의 깊게 들어보세요. 자신에게 해당되는 메시지를 찾아보세요."
                )
            ],

            MusicMood.NOSTALGIC: [
                MusicRecommendation(
                    mood=MusicMood.NOSTALGIC,
                    genre=MusicGenre.FOLK,
                    title_suggestion="추억의 노래, 포크",
                    korean_artists=["송창식", "윤수일", "김광석", "들국화"],
                    international_artists=["The Beatles", "Simon & Garfunkel"],
                    therapeutic_purpose="추억 회상, 감정 통합",
                    listening_instructions="그 시절의 기억을 떠올려 보세요. 어떤 느낌이 드나요?"
                )
            ],

            MusicMood.EMPOWERING: [
                MusicRecommendation(
                    mood=MusicMood.EMPOWERING,
                    genre=MusicGenre.KPOP,
                    title_suggestion="힘을 주는 응원가",
                    korean_artists=["방탄소년단", "에일리", "마마무"],
                    international_artists=["Rachel Platten", "Kelly Clarkson", "Sia"],
                    therapeutic_purpose="자신감 회복, 용기",
                    listening_instructions="가사를 따라 불러보세요. 자신에게 응원을 보내는 느낌으로."
                )
            ]
        }

    def _initialize_iso_playlists(self) -> Dict[str, IsoPlaylist]:
        """아이소 원칙 플레이리스트 초기화"""
        return {
            "sad_to_hopeful": IsoPlaylist(
                current_mood=MusicMood.SAD,
                target_mood=MusicMood.HOPEFUL,
                stages=[
                    {"stage": 1, "description": "슬픈 발라드 - 현재 감정 인정", "mood_level": 2, "duration": 10},
                    {"stage": 2, "description": "잔잔하지만 따뜻한 곡", "mood_level": 3, "duration": 8},
                    {"stage": 3, "description": "희망적인 가사의 미디엄 템포", "mood_level": 4, "duration": 8},
                    {"stage": 4, "description": "밝고 희망찬 노래", "mood_level": 5, "duration": 8}
                ],
                duration_minutes=34,
                description="슬픔에서 희망으로 점진적 전환"
            ),

            "angry_to_calm": IsoPlaylist(
                current_mood=MusicMood.ANGRY,
                target_mood=MusicMood.CALMING,
                stages=[
                    {"stage": 1, "description": "강렬한 록/힙합 - 분노 표출", "mood_level": 1, "duration": 8},
                    {"stage": 2, "description": "중간 강도의 곡", "mood_level": 2, "duration": 8},
                    {"stage": 3, "description": "잔잔한 어쿠스틱", "mood_level": 3, "duration": 8},
                    {"stage": 4, "description": "차분한 피아노/앰비언트", "mood_level": 4, "duration": 10}
                ],
                duration_minutes=34,
                description="분노에서 평온으로 점진적 전환"
            ),

            "anxious_to_peaceful": IsoPlaylist(
                current_mood=MusicMood.CALMING,  # 불안을 CALMING으로 대체
                target_mood=MusicMood.PEACEFUL,
                stages=[
                    {"stage": 1, "description": "빠른 템포의 클래식", "mood_level": 2, "duration": 6},
                    {"stage": 2, "description": "중간 템포 인스트루멘탈", "mood_level": 3, "duration": 8},
                    {"stage": 3, "description": "느린 피아노", "mood_level": 4, "duration": 8},
                    {"stage": 4, "description": "명상 음악/자연 소리", "mood_level": 5, "duration": 10}
                ],
                duration_minutes=32,
                description="불안에서 평화로 점진적 전환"
            ),

            "melancholic_to_uplifting": IsoPlaylist(
                current_mood=MusicMood.MELANCHOLIC,
                target_mood=MusicMood.UPLIFTING,
                stages=[
                    {"stage": 1, "description": "우울한 멜로디", "mood_level": 2, "duration": 8},
                    {"stage": 2, "description": "감성적이지만 따뜻한 곡", "mood_level": 3, "duration": 8},
                    {"stage": 3, "description": "밝아지는 템포", "mood_level": 4, "duration": 8},
                    {"stage": 4, "description": "경쾌하고 밝은 곡", "mood_level": 5, "duration": 8}
                ],
                duration_minutes=32,
                description="우울에서 밝음으로 점진적 전환"
            )
        }

    def get_recommendations(self, mood: MusicMood) -> List[MusicRecommendation]:
        """분위기에 맞는 음악 추천"""
        return self.recommendations.get(mood, [])

    def get_iso_playlist(self, playlist_key: str) -> IsoPlaylist:
        """아이소 플레이리스트 반환"""
        return self.iso_playlists.get(playlist_key)


class MusicTherapyTriggerDetector:
    """음악 치료 필요 상황 감지"""

    def __init__(self):
        self.emotion_keywords = {
            "sad": ["슬퍼", "우울", "눈물", "울적", "서글", "외로", "허전"],
            "angry": ["화나", "짜증", "열받", "분노", "미치겠", "답답"],
            "anxious": ["불안", "긴장", "걱정", "두려", "무서", "초조"],
            "happy": ["좋아", "행복", "기뻐", "신나", "즐거"],
            "calm_need": ["진정", "차분", "평화", "쉬고 싶", "힐링"]
        }

        self.music_related_keywords = [
            "음악", "노래", "들을", "추천", "플레이리스트"
        ]

    def detect(self, message: str) -> Dict[str, Any]:
        """음악 치료 필요 상황 감지"""
        message_lower = message.lower()

        # 음악 관련 언급 확인
        music_mentioned = any(kw in message_lower for kw in self.music_related_keywords)

        # 감정 감지
        detected_emotions = {}
        for emotion, keywords in self.emotion_keywords.items():
            matches = [kw for kw in keywords if kw in message_lower]
            if matches:
                detected_emotions[emotion] = {
                    "detected": True,
                    "matches": matches,
                    "confidence": min(len(matches) * 0.3, 0.9)
                }

        # 주요 감정 결정
        primary_emotion = None
        max_confidence = 0
        for emotion, data in detected_emotions.items():
            if data["confidence"] > max_confidence:
                max_confidence = data["confidence"]
                primary_emotion = emotion

        # 음악 분위기 매핑
        emotion_to_mood = {
            "sad": MusicMood.SAD,
            "angry": MusicMood.ANGRY,
            "anxious": MusicMood.CALMING,
            "happy": MusicMood.UPLIFTING,
            "calm_need": MusicMood.PEACEFUL
        }

        recommended_mood = emotion_to_mood.get(primary_emotion) if primary_emotion else None

        return {
            "should_suggest": music_mentioned or bool(detected_emotions),
            "music_mentioned": music_mentioned,
            "detected_emotions": detected_emotions,
            "primary_emotion": primary_emotion,
            "recommended_mood": recommended_mood.value if recommended_mood else None
        }


class IntegratedMusicTherapyChat:
    """채팅 통합형 음악 치료 시스템"""

    def __init__(self):
        self.trigger_detector = MusicTherapyTriggerDetector()
        self.recommendation_library = MusicRecommendationLibrary()
        self.active_sessions: Dict[str, MusicTherapySession] = {}

    def process_message(
        self,
        session_id: str,
        user_message: str,
        emotion_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """사용자 메시지 처리"""

        # 진행 중인 세션 확인
        if session_id in self.active_sessions:
            return self._handle_active_session(session_id, user_message)

        # 음악 치료 필요 상황 감지
        trigger_result = self.trigger_detector.detect(user_message)

        if trigger_result["should_suggest"]:
            return self._suggest_music_therapy(session_id, trigger_result)

        return {
            "music_suggested": False,
            "response": None,
            "continue_conversation": True
        }

    def _suggest_music_therapy(
        self,
        session_id: str,
        trigger_result: Dict
    ) -> Dict[str, Any]:
        """음악 치료 제안"""
        primary_emotion = trigger_result["primary_emotion"]
        recommended_mood = trigger_result["recommended_mood"]

        # 감정별 공감 메시지
        empathy_messages = {
            "sad": "슬픈 마음이 느껴지시네요.",
            "angry": "화가 많이 나셨군요.",
            "anxious": "불안하고 마음이 편치 않으시군요.",
            "happy": "기분이 좋으신 것 같네요!",
            "calm_need": "마음의 평화가 필요하시군요."
        }

        empathy = empathy_messages.get(primary_emotion, "")

        response = f"""{empathy}

🎵 **음악**이 도움이 될 수 있어요.

음악을 통해 감정을 표현하고 처리하는 방법이 있어요.

어떤 것을 해보시겠어요?
1️⃣ 지금 기분에 맞는 음악 추천받기
2️⃣ 기분 전환 플레이리스트 (아이소 원칙)
3️⃣ 노래 가사로 마음 표현하기
4️⃣ 추억의 노래 떠올리기

숫자로 선택해 주세요."""

        return {
            "music_suggested": True,
            "primary_emotion": primary_emotion,
            "recommended_mood": recommended_mood,
            "response": response,
            "continue_conversation": True,
            "awaiting_choice": True
        }

    def get_mood_recommendation(
        self,
        mood: MusicMood
    ) -> Dict[str, Any]:
        """분위기에 맞는 음악 추천"""
        recommendations = self.recommendation_library.get_recommendations(mood)

        if not recommendations:
            return {
                "error": True,
                "response": "해당 분위기의 음악 추천을 찾지 못했어요."
            }

        rec = random.choice(recommendations)

        korean_artists = ", ".join(rec.korean_artists[:3])
        intl_artists = ", ".join(rec.international_artists[:2])

        response = f"""🎵 **{rec.title_suggestion}** 추천드려요!

**추천 아티스트:**
🇰🇷 한국: {korean_artists}
🌍 해외: {intl_artists}

**치료적 효과:** {rec.therapeutic_purpose}

**💡 감상 가이드:**
{rec.listening_instructions}

---

음악을 들으신 후 어떤 느낌이 드셨는지 말씀해 주세요. 💙"""

        return {
            "response": response,
            "recommendation": {
                "genre": rec.genre.value,
                "mood": rec.mood.value,
                "artists": rec.korean_artists + rec.international_artists
            },
            "continue_conversation": True
        }

    def get_iso_playlist(
        self,
        current_emotion: str
    ) -> Dict[str, Any]:
        """아이소 원칙 플레이리스트"""
        playlist_map = {
            "sad": "sad_to_hopeful",
            "angry": "angry_to_calm",
            "anxious": "anxious_to_peaceful",
            "melancholic": "melancholic_to_uplifting"
        }

        playlist_key = playlist_map.get(current_emotion, "sad_to_hopeful")
        playlist = self.recommendation_library.get_iso_playlist(playlist_key)

        if not playlist:
            return {"error": True, "response": "플레이리스트를 찾지 못했어요."}

        stages_text = ""
        for stage in playlist.stages:
            stages_text += f"""
**{stage['stage']}단계** ({stage['duration']}분)
{stage['description']}
"""

        response = f"""🎼 **아이소 원칙 플레이리스트**

{playlist.description}

**원리:** 현재 감정의 음악부터 시작해서 점진적으로 목표 감정으로 이동합니다.

**총 시간:** 약 {playlist.duration_minutes}분

{stages_text}

---

💡 **사용법:**
1. 1단계 음악부터 순서대로 들어주세요
2. 각 단계에서 충분히 머무르세요
3. 감정이 자연스럽게 변화하는 것을 느껴보세요

어떤 플랫폼에서 음악을 들으시나요? (유튜브, 스포티파이, 멜론 등)
검색어를 알려드릴게요."""

        return {
            "response": response,
            "playlist": playlist_key,
            "duration": playlist.duration_minutes,
            "continue_conversation": True
        }

    def start_lyric_analysis(
        self,
        session_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """가사 분석 세션 시작"""
        self.active_sessions[session_id] = MusicTherapySession(
            session_id=session_id,
            user_id=user_id,
            technique=TherapeuticTechnique.LYRIC_ANALYSIS,
            current_step="song_selection"
        )

        response = """🎤 **노래 가사로 마음 표현하기**

좋아하는 노래나 최근 마음에 와닿는 노래가 있으신가요?

그 노래의 제목이나 가사 일부를 알려주세요.
함께 그 노래가 왜 마음에 와닿는지 이야기해 볼게요.

(노래 제목이나 가사를 입력해 주세요)"""

        return {
            "session_started": True,
            "response": response,
            "continue_conversation": True
        }

    def start_reminiscence(
        self,
        session_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """음악 회상 세션 시작"""
        self.active_sessions[session_id] = MusicTherapySession(
            session_id=session_id,
            user_id=user_id,
            technique=TherapeuticTechnique.MUSICAL_REMINISCENCE,
            current_step="memory_exploration"
        )

        response = """🎶 **추억의 노래 떠올리기**

음악은 강력한 기억을 불러일으킬 수 있어요.

특별한 추억이 담긴 노래가 있으신가요?
- 어린 시절 자주 들었던 노래
- 특별한 순간에 들었던 노래
- 누군가를 떠올리게 하는 노래

떠오르는 노래가 있으면 말씀해 주세요.
그 노래와 연결된 이야기를 나눠볼게요."""

        return {
            "session_started": True,
            "response": response,
            "continue_conversation": True
        }

    def _handle_active_session(
        self,
        session_id: str,
        user_message: str
    ) -> Dict[str, Any]:
        """진행 중인 세션 처리"""
        session = self.active_sessions[session_id]
        message_lower = user_message.lower()

        # 중단 요청
        if any(word in message_lower for word in ["그만", "취소", "끝"]):
            return self._end_session(session_id, interrupted=True)

        # 기법별 처리
        if session.technique == TherapeuticTechnique.LYRIC_ANALYSIS:
            return self._process_lyric_analysis(session_id, user_message)
        elif session.technique == TherapeuticTechnique.MUSICAL_REMINISCENCE:
            return self._process_reminiscence(session_id, user_message)

        return {
            "response": "계속 이야기해 주세요.",
            "continue_conversation": True
        }

    def _process_lyric_analysis(
        self,
        session_id: str,
        user_message: str
    ) -> Dict[str, Any]:
        """가사 분석 처리"""
        session = self.active_sessions[session_id]
        session.user_responses.append(user_message)

        if session.current_step == "song_selection":
            session.current_step = "exploration"

            response = f"""'{user_message}'

이 노래를 선택하셨군요.

몇 가지 질문을 드릴게요:

1️⃣ 이 노래가 특별히 마음에 와닿는 이유가 뭘까요?
2️⃣ 가사 중에 특히 공감되는 부분이 있나요?

하나씩 편하게 말씀해 주세요."""

            return {
                "response": response,
                "continue_conversation": True
            }

        elif session.current_step == "exploration":
            if len(session.user_responses) < 3:
                questions = [
                    "그 부분이 당신의 어떤 경험이나 감정과 연결되나요?",
                    "이 노래를 들을 때 주로 어떤 기분이 드시나요?",
                    "이 노래가 당신에게 해주는 말이 있다면 무엇일까요?"
                ]
                question = questions[len(session.user_responses) - 1] if len(session.user_responses) <= len(questions) else None

                if question:
                    return {
                        "response": f"네, 그렇군요. 💙\n\n{question}",
                        "continue_conversation": True
                    }

            # 마무리
            return self._complete_lyric_analysis(session_id)

        return {
            "response": "더 이야기해 주세요.",
            "continue_conversation": True
        }

    def _complete_lyric_analysis(self, session_id: str) -> Dict[str, Any]:
        """가사 분석 완료"""
        session = self.active_sessions[session_id]

        response = """🎵 **정리해 볼게요**

노래를 통해 자신의 감정을 표현하고 이해하는 시간이었어요.

때로는 직접 말하기 어려운 감정을
음악이 대신 표현해 줄 수 있죠.

💡 **팁:** 힘들 때 이 노래를 들으며
자신의 감정을 인정하고 위로받아 보세요.

오늘 나눈 이야기가 도움이 되셨나요?"""

        del self.active_sessions[session_id]

        return {
            "response": response,
            "session_completed": True,
            "continue_conversation": True
        }

    def _process_reminiscence(
        self,
        session_id: str,
        user_message: str
    ) -> Dict[str, Any]:
        """음악 회상 처리"""
        session = self.active_sessions[session_id]
        session.user_responses.append(user_message)

        if len(session.user_responses) == 1:
            response = f"""'{user_message}'

좋은 노래를 떠올리셨네요.

이 노래와 관련된 **추억**이 있으신가요?
언제, 어디서, 누구와 함께 이 노래를 들으셨나요?"""

            return {
                "response": response,
                "continue_conversation": True
            }

        elif len(session.user_responses) == 2:
            response = """소중한 추억을 나눠주셨네요. 💙

그 때의 기분은 어땠나요?
지금 그 기억을 떠올리니 어떤 감정이 드시나요?"""

            return {
                "response": response,
                "continue_conversation": True
            }

        elif len(session.user_responses) == 3:
            # 마무리
            response = """🎶 **음악 회상을 마치며**

음악은 과거의 감정과 기억을 생생하게 불러일으키는 힘이 있어요.

오늘 떠올린 추억이 당신에게 어떤 의미가 있는지,
그리고 그 감정이 지금의 당신에게 무엇을 말해주는지
생각해 보셔도 좋을 것 같아요.

좋은 추억은 힘들 때 우리에게 힘이 되어줍니다.
이 노래를 다시 들으며 그 따뜻함을 느껴보세요. 💙"""

            del self.active_sessions[session_id]

            return {
                "response": response,
                "session_completed": True,
                "continue_conversation": True
            }

        return {
            "response": "더 이야기해 주세요.",
            "continue_conversation": True
        }

    def _end_session(self, session_id: str, interrupted: bool = False) -> Dict[str, Any]:
        """세션 종료"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

        response = """괜찮아요, 나중에 다시 해볼 수 있어요.
음악이 필요하실 때 언제든 말씀해 주세요. 🎵"""

        return {
            "response": response,
            "session_ended": True,
            "interrupted": interrupted,
            "continue_conversation": True
        }

    def get_quick_music_for_mood(self, mood: str) -> str:
        """빠른 분위기별 음악 제안"""
        mood_map = {
            "슬플 때": "잔잔한 피아노 음악 (이루마, Yiruma)",
            "화날 때": "락 음악으로 감정 분출하고, 점차 잔잔한 곡으로",
            "불안할 때": "자연 소리 (빗소리, 파도 소리) + 느린 템포 클래식",
            "우울할 때": "슬픈 발라드로 감정 인정 후, 밝은 곡으로 전환",
            "기운 없을 때": "밝은 K-pop, 신나는 댄스 음악",
            "잠이 안 올 때": "느린 피아노, 앰비언트, 자연 소리"
        }

        result = "🎵 **분위기별 음악 추천**\n\n"
        for situation, music in mood_map.items():
            result += f"• **{situation}**: {music}\n"

        return result


# 사용 예시
if __name__ == "__main__":
    system = IntegratedMusicTherapyChat()

    # 감지 테스트
    result = system.process_message(
        "session_1",
        "너무 슬퍼서 울고 싶어요... 음악이라도 들을까"
    )
    print("=== 음악 치료 제안 ===")
    print(result["response"])

    # 분위기별 추천
    print("\n=== 슬플 때 음악 추천 ===")
    rec = system.get_mood_recommendation(MusicMood.SAD)
    print(rec["response"])

    # 아이소 플레이리스트
    print("\n=== 아이소 플레이리스트 ===")
    playlist = system.get_iso_playlist("sad")
    print(playlist["response"])

    # 빠른 추천
    print("\n=== 빠른 분위기별 추천 ===")
    print(system.get_quick_music_for_mood("all"))
