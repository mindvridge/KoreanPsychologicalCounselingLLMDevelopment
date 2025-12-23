"""
ElevenLabs TTS 모듈
ElevenLabs API를 사용한 고품질 음성 합성
"""

import logging
import base64
import io
import numpy as np
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from elevenlabs import ElevenLabs, VoiceSettings
    HAS_ELEVENLABS = True
except ImportError:
    HAS_ELEVENLABS = False
    logger.warning("ElevenLabs 패키지가 설치되지 않았습니다. pip install elevenlabs로 설치하세요.")


@dataclass
class ElevenLabsConfig:
    """ElevenLabs 설정"""
    api_key: Optional[str] = None
    voice_id: str = "zsAH1WNcfG4gUQ2NIDnd"  # 기본 음성 (사용자 지정)
    model_id: str = "eleven_multilingual_v2"  # 다국어 모델
    stability: float = 0.5  # 0.0 ~ 1.0
    similarity_boost: float = 0.75  # 0.0 ~ 1.0
    style: float = 0.0  # 0.0 ~ 1.0
    use_speaker_boost: bool = True
    sample_rate: int = 44100


class ElevenLabsTTS:
    """
    ElevenLabs TTS 엔진
    
    고품질 음성 합성을 위한 ElevenLabs API 사용
    """
    
    def __init__(self, config: Optional[ElevenLabsConfig] = None):
        """
        초기화
        
        Args:
            config: ElevenLabs 설정
        """
        if not HAS_ELEVENLABS:
            raise ImportError("ElevenLabs 패키지가 설치되지 않았습니다.")
        
        self.config = config or ElevenLabsConfig()
        
        # API 키 설정
        import os
        api_key = self.config.api_key or os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            logger.warning("ElevenLabs API 키가 설정되지 않았습니다. 환경 변수 ELEVENLABS_API_KEY를 설정하세요.")
        
        # ElevenLabs 클라이언트 초기화
        self.client = ElevenLabs(api_key=api_key) if api_key else None
        if api_key:
            self.config.api_key = api_key
    
    def synthesize(
        self,
        text: str,
        voice_id: Optional[str] = None,
        emotion: Optional[str] = None
    ) -> np.ndarray:
        """
        텍스트를 음성으로 변환
        
        Args:
            text: 합성할 텍스트
            voice_id: 음성 ID (기본값: 설정된 음성)
            emotion: 감정 (calm, empathetic, supportive 등)
        
        Returns:
            오디오 데이터 (numpy array)
        """
        if not HAS_ELEVENLABS:
            raise RuntimeError("ElevenLabs가 설치되지 않았습니다.")
        
        try:
            # 음성 ID 설정
            selected_voice_id = voice_id or self.config.voice_id
            
            # 감정에 따른 설정 조정 (기본값)
            stability = self.config.stability
            style = self.config.style
            
            # 감정에 따른 미세 조정
            if emotion == "calm":
                stability = 0.6
                style = 0.2
            elif emotion == "empathetic":
                stability = 0.5
                style = 0.4
            elif emotion == "supportive":
                stability = 0.55
                style = 0.3
            
            # VoiceSettings 객체 생성 (frozen이므로 생성 시 모든 값을 설정)
            voice_settings = VoiceSettings(
                stability=stability,
                similarity_boost=self.config.similarity_boost,
                style=style,
                use_speaker_boost=self.config.use_speaker_boost
            )
            
            # 음성 생성 (비스트리밍) - ElevenLabs 2.x API
            if not self.client:
                raise RuntimeError("ElevenLabs 클라이언트가 초기화되지 않았습니다. API 키를 설정하세요.")
            
            response = self.client.text_to_speech.convert(
                voice_id=selected_voice_id,
                text=text,
                model_id=self.config.model_id,
                voice_settings=voice_settings
            )
            
            # 응답에서 오디오 바이트 추출
            audio_bytes = b""
            for chunk in response:
                if hasattr(chunk, 'audio'):
                    audio_bytes += chunk.audio
                elif isinstance(chunk, bytes):
                    audio_bytes += chunk
                else:
                    # 응답이 다른 형식일 수 있음
                    audio_bytes = bytes(chunk) if chunk else b""
            
            # 바이트를 numpy array로 변환
            import soundfile as sf
            audio_data, sample_rate = sf.read(io.BytesIO(audio_bytes))
            
            # 샘플 레이트 변환 (필요한 경우)
            if sample_rate != self.config.sample_rate:
                import librosa
                audio_data = librosa.resample(
                    audio_data,
                    orig_sr=sample_rate,
                    target_sr=self.config.sample_rate
                )
            
            return audio_data.astype(np.float32)
            
        except Exception as e:
            logger.error(f"ElevenLabs 합성 오류: {e}", exc_info=True)
            import traceback
            logger.error(f"ElevenLabs 합성 오류 상세:\n{traceback.format_exc()}")
            raise
    
    def get_available_voices(self) -> list:
        """
        사용 가능한 음성 목록 가져오기
        
        Returns:
            음성 목록
        """
        if not HAS_ELEVENLABS:
            return []
        
        try:
            voices_list = voices()
            return [
                {
                    "voice_id": voice.voice_id,
                    "name": voice.name,
                    "category": voice.category,
                    "description": getattr(voice, 'description', '')
                }
                for voice in voices_list
            ]
        except Exception as e:
            logger.error(f"음성 목록 가져오기 오류: {e}")
            return []
    
    def synthesize_stream(
        self,
        text: str,
        voice_id: Optional[str] = None,
        emotion: Optional[str] = None
    ):
        """
        텍스트를 음성으로 스트리밍 변환
        
        Args:
            text: 합성할 텍스트
            voice_id: 음성 ID (기본값: 설정된 음성)
            emotion: 감정 (calm, empathetic, supportive 등)
        
        Yields:
            오디오 청크 (bytes)
        """
        if not HAS_ELEVENLABS:
            raise RuntimeError("ElevenLabs가 설치되지 않았습니다.")
        
        try:
            # 음성 ID 설정
            selected_voice_id = voice_id or self.config.voice_id
            
            # 감정에 따른 설정 조정 (기본값)
            stability = self.config.stability
            style = self.config.style
            
            # 감정에 따른 미세 조정
            if emotion == "calm":
                stability = 0.6
                style = 0.2
            elif emotion == "empathetic":
                stability = 0.5
                style = 0.4
            elif emotion == "supportive":
                stability = 0.55
                style = 0.3
            
            # VoiceSettings 객체 생성 (frozen이므로 생성 시 모든 값을 설정)
            voice_settings = VoiceSettings(
                stability=stability,
                similarity_boost=self.config.similarity_boost,
                style=style,
                use_speaker_boost=self.config.use_speaker_boost
            )
            
            # 스트리밍 음성 생성 - ElevenLabs 2.x API
            if not self.client:
                raise RuntimeError("ElevenLabs 클라이언트가 초기화되지 않았습니다. API 키를 설정하세요.")
            
            response = self.client.text_to_speech.convert_stream(
                voice_id=selected_voice_id,
                text=text,
                model_id=self.config.model_id,
                voice_settings=voice_settings
            )
            
            # 스트림에서 오디오 청크 반환
            for chunk in response:
                if hasattr(chunk, 'audio'):
                    yield chunk.audio
                elif isinstance(chunk, bytes):
                    yield chunk
                else:
                    # 응답이 다른 형식일 수 있음
                    yield bytes(chunk) if chunk else b""
            
        except Exception as e:
            logger.error(f"ElevenLabs 스트리밍 합성 오류: {e}")
            raise
    
    def is_available(self) -> bool:
        """ElevenLabs 사용 가능 여부"""
        return HAS_ELEVENLABS and self.config.api_key is not None

