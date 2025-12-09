"""
TTS 모듈 (Text-to-Speech)
Zonos를 사용한 음성 합성 및 Voice Cloning

기능:
- 텍스트를 음성으로 변환
- Voice Cloning (한국어 화자 복제)
- 감정 조절 (happiness, sadness, calmness)
- 실시간 스트리밍 지원
"""

import logging
import numpy as np
from typing import Optional, Dict, Any, Union, List
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import io
import threading

logger = logging.getLogger(__name__)


@dataclass
class VoiceProfile:
    """음성 프로필 (Voice Cloning용)"""
    name: str
    speaker_embedding: Optional[np.ndarray] = None
    reference_audio_path: Optional[str] = None
    description: str = ""
    language: str = "ko"
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "language": self.language,
            "has_embedding": self.speaker_embedding is not None,
            "reference_audio": self.reference_audio_path,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class SpeechConfig:
    """음성 생성 설정"""
    speaking_rate: float = 1.0  # 0.5 ~ 2.0
    pitch: float = 0.0  # -20 ~ 20
    volume_gain_db: float = 0.0
    sample_rate: int = 44100  # Zonos 기본 출력

    # 감정 설정 (Zonos 지원)
    emotion: str = "neutral"  # neutral, happy, sad, calm, angry
    emotion_intensity: float = 0.5  # 0.0 ~ 1.0


@dataclass
class SynthesisResult:
    """음성 합성 결과"""
    audio: np.ndarray
    sample_rate: int
    duration: float
    text: str
    voice_profile: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_bytes(self, format: str = "wav") -> bytes:
        """바이트로 변환"""
        import soundfile as sf

        buffer = io.BytesIO()
        sf.write(buffer, self.audio, self.sample_rate, format=format)
        buffer.seek(0)
        return buffer.read()

    def save(self, path: str) -> None:
        """파일로 저장"""
        import soundfile as sf
        sf.write(path, self.audio, self.sample_rate)


class ZonosTTS:
    """
    Zonos 기반 TTS 엔진

    Voice Cloning을 통한 한국어 지원
    """

    def __init__(
        self,
        model_name: str = "Zyphra/Zonos-v0.1-transformer",
        device: str = "cuda",
        default_voice: Optional[str] = None
    ):
        """
        초기화

        Args:
            model_name: Zonos 모델 이름
            device: 디바이스 (cuda, cpu)
            default_voice: 기본 음성 프로필 이름
        """
        self.model_name = model_name
        self.device = device
        self.default_voice = default_voice

        self.model = None
        self.voice_profiles: Dict[str, VoiceProfile] = {}
        self._lock = threading.Lock()

        logger.info(f"ZonosTTS initializing with model={model_name}, device={device}")

    def load_model(self) -> None:
        """모델 로드"""
        with self._lock:
            if self.model is not None:
                return

            try:
                import torch
                from zonos.model import Zonos
                from zonos.conditioning import make_cond_dict

                self.model = Zonos.from_pretrained(self.model_name)
                self.model = self.model.to(self.device)
                self.model.eval()

                self._make_cond_dict = make_cond_dict
                self._torch = torch

                logger.info("Zonos model loaded successfully")

            except ImportError as e:
                logger.error(f"Zonos import error: {e}")
                logger.info("Attempting to use fallback TTS...")
                self._load_fallback_tts()

    def _load_fallback_tts(self) -> None:
        """대체 TTS 로드 (Zonos 사용 불가시)"""
        try:
            from TTS.api import TTS

            # Coqui TTS (VITS) 사용
            self.model = TTS(model_name="tts_models/multilingual/multi-dataset/your_tts")
            self._model_type = "coqui"
            logger.info("Fallback to Coqui TTS")

        except ImportError:
            logger.warning("No TTS engine available")
            self.model = None
            self._model_type = None

    def create_voice_profile(
        self,
        name: str,
        reference_audio: Union[str, bytes, np.ndarray],
        description: str = "",
        sample_rate: int = 16000
    ) -> VoiceProfile:
        """
        Voice Cloning용 음성 프로필 생성

        Args:
            name: 프로필 이름
            reference_audio: 참조 오디오 (5-30초 권장)
            description: 설명
            sample_rate: 참조 오디오 샘플레이트

        Returns:
            VoiceProfile: 생성된 프로필
        """
        if self.model is None:
            self.load_model()

        # 오디오 로드
        audio_array = self._load_audio(reference_audio, sample_rate)

        # Speaker Embedding 추출
        with self._lock:
            speaker_embedding = self._extract_speaker_embedding(audio_array)

        # 프로필 생성
        profile = VoiceProfile(
            name=name,
            speaker_embedding=speaker_embedding,
            reference_audio_path=reference_audio if isinstance(reference_audio, str) else None,
            description=description,
            language="ko"
        )

        self.voice_profiles[name] = profile
        logger.info(f"Voice profile created: {name}")

        return profile

    def _load_audio(
        self,
        audio: Union[str, bytes, np.ndarray],
        sample_rate: int
    ) -> np.ndarray:
        """오디오 로드"""
        import soundfile as sf

        if isinstance(audio, str):
            audio_array, sr = sf.read(audio)
        elif isinstance(audio, bytes):
            audio_array, sr = sf.read(io.BytesIO(audio))
        elif isinstance(audio, np.ndarray):
            return audio.astype(np.float32)
        else:
            raise ValueError(f"Unsupported audio type: {type(audio)}")

        # 리샘플링 (필요시)
        if sr != sample_rate:
            try:
                import librosa
                audio_array = librosa.resample(audio_array, orig_sr=sr, target_sr=sample_rate)
            except ImportError:
                pass

        return audio_array.astype(np.float32)

    def _extract_speaker_embedding(self, audio: np.ndarray) -> np.ndarray:
        """Speaker Embedding 추출"""
        if hasattr(self, '_torch') and self.model is not None:
            # Zonos의 speaker embedding 추출
            with self._torch.no_grad():
                audio_tensor = self._torch.tensor(audio).unsqueeze(0).to(self.device)
                embedding = self.model.make_speaker_embedding(audio_tensor)
                return embedding.cpu().numpy()
        else:
            # 더미 임베딩 반환
            return np.zeros(256, dtype=np.float32)

    def synthesize(
        self,
        text: str,
        voice_profile: Optional[str] = None,
        config: Optional[SpeechConfig] = None
    ) -> SynthesisResult:
        """
        텍스트를 음성으로 합성

        Args:
            text: 합성할 텍스트
            voice_profile: 사용할 음성 프로필
            config: 음성 설정

        Returns:
            SynthesisResult: 합성 결과
        """
        if self.model is None:
            self.load_model()

        config = config or SpeechConfig()
        profile_name = voice_profile or self.default_voice

        # 프로필 가져오기
        profile = self.voice_profiles.get(profile_name) if profile_name else None

        with self._lock:
            audio = self._synthesize_impl(text, profile, config)

        duration = len(audio) / config.sample_rate

        return SynthesisResult(
            audio=audio,
            sample_rate=config.sample_rate,
            duration=duration,
            text=text,
            voice_profile=profile_name
        )

    def _synthesize_impl(
        self,
        text: str,
        profile: Optional[VoiceProfile],
        config: SpeechConfig
    ) -> np.ndarray:
        """실제 합성 구현"""
        if hasattr(self, '_model_type') and self._model_type == "coqui":
            return self._synthesize_coqui(text, profile, config)

        if self.model is None:
            raise RuntimeError("No TTS model loaded")

        # Zonos 합성
        try:
            # Conditioning 설정
            cond_dict = self._make_cond_dict(
                text=text,
                speaker=profile.speaker_embedding if profile else None,
                language="ko",
                emotion=self._map_emotion(config.emotion),
                speaking_rate=config.speaking_rate
            )

            # 합성
            with self._torch.no_grad():
                audio = self.model.generate(**cond_dict)
                audio = audio.cpu().numpy().squeeze()

            # 볼륨 조절
            if config.volume_gain_db != 0:
                gain = 10 ** (config.volume_gain_db / 20)
                audio = audio * gain

            return audio

        except Exception as e:
            logger.error(f"Zonos synthesis error: {e}")
            # 대체 합성 시도
            return self._synthesize_fallback(text)

    def _synthesize_coqui(
        self,
        text: str,
        profile: Optional[VoiceProfile],
        config: SpeechConfig
    ) -> np.ndarray:
        """Coqui TTS 합성"""
        audio = self.model.tts(
            text=text,
            speaker_wav=profile.reference_audio_path if profile else None,
            language="ko"
        )
        return np.array(audio, dtype=np.float32)

    def _synthesize_fallback(self, text: str) -> np.ndarray:
        """대체 합성 (gTTS 등)"""
        try:
            from gtts import gTTS
            import tempfile
            import soundfile as sf

            tts = gTTS(text=text, lang='ko')
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                tts.save(f.name)
                audio, sr = sf.read(f.name)

            return audio.astype(np.float32)

        except Exception as e:
            logger.error(f"Fallback synthesis failed: {e}")
            # 무음 반환
            return np.zeros(44100, dtype=np.float32)

    def _map_emotion(self, emotion: str) -> Dict[str, float]:
        """감정 매핑"""
        emotion_map = {
            "neutral": {"happiness": 0.0, "sadness": 0.0, "anger": 0.0, "fear": 0.0},
            "happy": {"happiness": 0.8, "sadness": 0.0, "anger": 0.0, "fear": 0.0},
            "sad": {"happiness": 0.0, "sadness": 0.7, "anger": 0.0, "fear": 0.0},
            "calm": {"happiness": 0.2, "sadness": 0.0, "anger": 0.0, "fear": 0.0},
            "angry": {"happiness": 0.0, "sadness": 0.0, "anger": 0.8, "fear": 0.0},
            # 상담용 감정
            "empathetic": {"happiness": 0.3, "sadness": 0.2, "anger": 0.0, "fear": 0.0},
            "supportive": {"happiness": 0.4, "sadness": 0.0, "anger": 0.0, "fear": 0.0},
            "concerned": {"happiness": 0.0, "sadness": 0.3, "anger": 0.0, "fear": 0.1}
        }
        return emotion_map.get(emotion, emotion_map["neutral"])

    def synthesize_stream(
        self,
        text: str,
        voice_profile: Optional[str] = None,
        config: Optional[SpeechConfig] = None,
        chunk_size: int = 8192
    ):
        """
        스트리밍 합성

        Args:
            text: 합성할 텍스트
            voice_profile: 음성 프로필
            config: 음성 설정
            chunk_size: 청크 크기

        Yields:
            bytes: 오디오 청크
        """
        result = self.synthesize(text, voice_profile, config)
        audio_bytes = result.to_bytes()

        for i in range(0, len(audio_bytes), chunk_size):
            yield audio_bytes[i:i + chunk_size]

    def list_voice_profiles(self) -> List[Dict[str, Any]]:
        """등록된 음성 프로필 목록"""
        return [p.to_dict() for p in self.voice_profiles.values()]

    def save_voice_profile(self, name: str, path: str) -> None:
        """음성 프로필 저장"""
        import json

        profile = self.voice_profiles.get(name)
        if not profile:
            raise ValueError(f"Voice profile not found: {name}")

        data = {
            "name": profile.name,
            "description": profile.description,
            "language": profile.language,
            "reference_audio_path": profile.reference_audio_path
        }

        # 임베딩 저장
        if profile.speaker_embedding is not None:
            np.save(f"{path}.embedding.npy", profile.speaker_embedding)
            data["embedding_path"] = f"{path}.embedding.npy"

        with open(f"{path}.json", 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Voice profile saved: {path}")

    def load_voice_profile(self, path: str) -> VoiceProfile:
        """음성 프로필 로드"""
        import json

        with open(f"{path}.json", 'r', encoding='utf-8') as f:
            data = json.load(f)

        embedding = None
        if "embedding_path" in data:
            embedding = np.load(data["embedding_path"])

        profile = VoiceProfile(
            name=data["name"],
            speaker_embedding=embedding,
            reference_audio_path=data.get("reference_audio_path"),
            description=data.get("description", ""),
            language=data.get("language", "ko")
        )

        self.voice_profiles[profile.name] = profile
        return profile

    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보"""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "loaded": self.model is not None,
            "model_type": getattr(self, '_model_type', 'zonos'),
            "voice_profiles": list(self.voice_profiles.keys()),
            "default_voice": self.default_voice
        }


class CounselorVoice:
    """
    심리상담사 음성 설정

    차분하고 공감적인 상담사 음성을 위한 프리셋
    """

    # 기본 상담사 음성 설정
    DEFAULT_CONFIG = SpeechConfig(
        speaking_rate=0.9,  # 약간 느리게
        pitch=-2.0,  # 약간 낮게
        emotion="calm",
        emotion_intensity=0.6
    )

    # 공감 표현 시 설정
    EMPATHETIC_CONFIG = SpeechConfig(
        speaking_rate=0.85,
        pitch=-1.0,
        emotion="empathetic",
        emotion_intensity=0.7
    )

    # 지지/격려 시 설정
    SUPPORTIVE_CONFIG = SpeechConfig(
        speaking_rate=0.95,
        pitch=0.0,
        emotion="supportive",
        emotion_intensity=0.6
    )

    # 위기 상황 시 설정 (차분하고 안정적)
    CRISIS_CONFIG = SpeechConfig(
        speaking_rate=0.8,
        pitch=-3.0,
        emotion="calm",
        emotion_intensity=0.8
    )

    @classmethod
    def get_config_for_context(cls, context: Dict[str, Any]) -> SpeechConfig:
        """컨텍스트에 맞는 음성 설정 반환"""
        crisis_level = context.get("crisis_level", 0)
        emotion = context.get("emotion", "neutral")
        response_type = context.get("response_type", "default")

        if crisis_level > 0.7:
            return cls.CRISIS_CONFIG
        elif response_type == "empathy" or emotion in ["sadness", "fear"]:
            return cls.EMPATHETIC_CONFIG
        elif response_type == "encouragement":
            return cls.SUPPORTIVE_CONFIG
        else:
            return cls.DEFAULT_CONFIG


# 편의 함수
_default_tts: Optional[ZonosTTS] = None


def get_tts(device: str = "cuda") -> ZonosTTS:
    """기본 TTS 인스턴스 반환"""
    global _default_tts

    if _default_tts is None:
        _default_tts = ZonosTTS(device=device)
        _default_tts.load_model()

    return _default_tts


def synthesize(
    text: str,
    voice_profile: Optional[str] = None,
    emotion: str = "calm"
) -> bytes:
    """간단한 음성 합성 함수"""
    tts = get_tts()
    config = SpeechConfig(emotion=emotion)
    result = tts.synthesize(text, voice_profile, config)
    return result.to_bytes()
