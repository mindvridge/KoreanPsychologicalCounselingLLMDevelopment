"""
Voice Interface Service for Korean Mental Health Counseling System
Provides Speech-to-Text (STT) and Text-to-Speech (TTS) capabilities
"""

import os
import io
import tempfile
import logging
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)

# Lazy imports to avoid loading heavy models at startup
_whisper_model = None
_gtts_available = False


def get_whisper_model():
    """Lazy load Whisper model"""
    global _whisper_model
    if _whisper_model is None:
        try:
            import whisper
            model_size = os.getenv("WHISPER_MODEL_SIZE", "base")
            logger.info(f"Loading Whisper model: {model_size}")
            _whisper_model = whisper.load_model(model_size)
            logger.info("Whisper model loaded successfully")
        except ImportError:
            logger.error("Whisper not installed. Run: pip install openai-whisper")
            raise
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
    return _whisper_model


class VoiceService:
    """
    Voice service providing Korean Speech-to-Text and Text-to-Speech

    Features:
    - Korean language optimized STT using OpenAI Whisper
    - Natural Korean TTS using gTTS
    - Audio preprocessing and validation
    - Emotion-aware speech synthesis (speed/pitch adjustment)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

        # Audio settings
        self.sample_rate = self.config.get("sample_rate", 16000)
        self.max_audio_duration = self.config.get("max_audio_duration", 300)  # 5 minutes
        self.max_file_size = self.config.get("max_file_size", 25 * 1024 * 1024)  # 25MB

        # TTS settings
        self.default_language = "ko"  # Korean
        self.tts_slow = self.config.get("tts_slow", False)

        # Cache directory for generated audio
        self.cache_dir = Path(self.config.get("cache_dir", "data/voice_cache"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Statistics
        self.stats = {
            "stt_requests": 0,
            "tts_requests": 0,
            "total_audio_processed_seconds": 0,
            "errors": 0
        }

        logger.info("VoiceService initialized")

    def transcribe_audio(
        self,
        audio_data: bytes,
        audio_format: str = "wav",
        language: str = "ko"
    ) -> Dict[str, Any]:
        """
        Convert speech audio to text using Whisper

        Args:
            audio_data: Raw audio bytes
            audio_format: Audio format (wav, mp3, m4a, webm)
            language: Target language code (default: ko for Korean)

        Returns:
            {
                "text": "transcribed text",
                "language": "ko",
                "confidence": 0.95,
                "duration": 5.2,
                "segments": [...]
            }
        """
        self.stats["stt_requests"] += 1

        try:
            # Validate audio size
            if len(audio_data) > self.max_file_size:
                raise ValueError(f"Audio file too large. Max size: {self.max_file_size / 1024 / 1024:.1f}MB")

            # Save to temporary file for Whisper processing
            with tempfile.NamedTemporaryFile(suffix=f".{audio_format}", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name

            try:
                # Load and transcribe using Whisper
                model = get_whisper_model()

                # Transcribe with Korean language hint
                result = model.transcribe(
                    temp_path,
                    language=language,
                    task="transcribe",
                    verbose=False
                )

                # Calculate audio duration
                try:
                    import librosa
                    audio, sr = librosa.load(temp_path, sr=None)
                    duration = len(audio) / sr
                except Exception:
                    duration = 0

                self.stats["total_audio_processed_seconds"] += duration

                # Extract segments with timestamps
                segments = []
                for seg in result.get("segments", []):
                    segments.append({
                        "start": seg["start"],
                        "end": seg["end"],
                        "text": seg["text"].strip()
                    })

                # Calculate confidence from segments
                avg_confidence = 0.0
                if segments:
                    # Use no_speech_prob as inverse confidence indicator
                    confidences = [1.0 - seg.get("no_speech_prob", 0) for seg in result.get("segments", [])]
                    if confidences:
                        avg_confidence = sum(confidences) / len(confidences)

                transcription_result = {
                    "text": result["text"].strip(),
                    "language": result.get("language", language),
                    "confidence": round(avg_confidence, 3),
                    "duration": round(duration, 2),
                    "segments": segments,
                    "timestamp": datetime.utcnow().isoformat()
                }

                logger.info(f"STT completed: {len(result['text'])} chars, {duration:.1f}s audio")
                return transcription_result

            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"STT error: {e}")
            raise

    def synthesize_speech(
        self,
        text: str,
        language: str = "ko",
        slow: bool = False,
        emotion: Optional[str] = None,
        output_format: str = "mp3"
    ) -> Dict[str, Any]:
        """
        Convert text to speech audio using gTTS

        Args:
            text: Text to convert to speech
            language: Language code (default: ko)
            slow: Speak slowly (for clarity)
            emotion: Optional emotion hint for speech adjustment
            output_format: Output audio format (mp3)

        Returns:
            {
                "audio_data": bytes,
                "format": "mp3",
                "text_length": 100,
                "duration_estimate": 5.0,
                "cached": False
            }
        """
        self.stats["tts_requests"] += 1

        try:
            if not text or not text.strip():
                raise ValueError("Text cannot be empty")

            # Limit text length for TTS
            max_text_length = 5000  # gTTS limit
            if len(text) > max_text_length:
                text = text[:max_text_length]
                logger.warning(f"Text truncated to {max_text_length} characters")

            # Check cache first
            cache_key = self._generate_cache_key(text, language, slow)
            cached_audio = self._get_cached_audio(cache_key)
            if cached_audio:
                logger.info("TTS cache hit")
                return {
                    "audio_data": cached_audio,
                    "format": output_format,
                    "text_length": len(text),
                    "duration_estimate": self._estimate_duration(text, language),
                    "cached": True
                }

            # Generate speech using gTTS
            from gtts import gTTS

            # Adjust speed based on emotion
            use_slow = slow
            if emotion in ["sadness", "calm", "anxiety"]:
                use_slow = True  # Speak slower for emotional content

            tts = gTTS(text=text, lang=language, slow=use_slow)

            # Save to bytes
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            audio_data = audio_buffer.read()

            # Cache the audio
            self._cache_audio(cache_key, audio_data)

            duration_estimate = self._estimate_duration(text, language)

            logger.info(f"TTS completed: {len(text)} chars, ~{duration_estimate:.1f}s audio")

            return {
                "audio_data": audio_data,
                "format": output_format,
                "text_length": len(text),
                "duration_estimate": round(duration_estimate, 2),
                "cached": False
            }

        except ImportError:
            self.stats["errors"] += 1
            logger.error("gTTS not installed. Run: pip install gtts")
            raise
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"TTS error: {e}")
            raise

    def _estimate_duration(self, text: str, language: str = "ko") -> float:
        """Estimate audio duration based on text length"""
        # Korean speech: approximately 3-4 characters per second
        if language == "ko":
            chars_per_second = 3.5
        else:
            # English: approximately 15 characters per second (including spaces)
            chars_per_second = 15.0

        return len(text) / chars_per_second

    def _generate_cache_key(self, text: str, language: str, slow: bool) -> str:
        """Generate cache key for TTS audio"""
        content = f"{text}:{language}:{slow}"
        return hashlib.md5(content.encode()).hexdigest()

    def _get_cached_audio(self, cache_key: str) -> Optional[bytes]:
        """Retrieve cached audio if exists"""
        cache_file = self.cache_dir / f"{cache_key}.mp3"
        if cache_file.exists():
            try:
                with open(cache_file, "rb") as f:
                    return f.read()
            except Exception:
                pass
        return None

    def _cache_audio(self, cache_key: str, audio_data: bytes) -> None:
        """Cache generated audio"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.mp3"
            with open(cache_file, "wb") as f:
                f.write(audio_data)
        except Exception as e:
            logger.warning(f"Failed to cache audio: {e}")

    def validate_audio_format(self, audio_data: bytes) -> Tuple[bool, str]:
        """
        Validate if audio data is in supported format

        Returns:
            (is_valid, format_or_error_message)
        """
        # Check file signatures
        if audio_data[:4] == b'RIFF':
            return True, "wav"
        elif audio_data[:3] == b'ID3' or audio_data[:2] == b'\xff\xfb':
            return True, "mp3"
        elif audio_data[:4] == b'fLaC':
            return True, "flac"
        elif audio_data[4:8] == b'ftyp':
            return True, "m4a"
        elif audio_data[:4] == b'\x1aE\xdf\xa3':
            return True, "webm"
        else:
            return False, "Unsupported audio format"

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            **self.stats,
            "cache_size_mb": self._get_cache_size(),
            "timestamp": datetime.utcnow().isoformat()
        }

    def _get_cache_size(self) -> float:
        """Get total cache size in MB"""
        total_size = 0
        for file in self.cache_dir.glob("*.mp3"):
            total_size += file.stat().st_size
        return round(total_size / (1024 * 1024), 2)

    def clear_cache(self) -> int:
        """Clear TTS cache, returns number of files deleted"""
        count = 0
        for file in self.cache_dir.glob("*.mp3"):
            try:
                file.unlink()
                count += 1
            except Exception:
                pass
        logger.info(f"Cleared {count} cached audio files")
        return count


class EmotionAwareVoiceService(VoiceService):
    """
    Extended voice service with emotion-aware speech synthesis
    Adjusts TTS parameters based on detected emotions
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)

        # Emotion to speech mapping
        self.emotion_speech_params = {
            "sadness": {"slow": True, "pause_ratio": 1.2},
            "happiness": {"slow": False, "pause_ratio": 0.9},
            "anger": {"slow": False, "pause_ratio": 0.8},
            "anxiety": {"slow": True, "pause_ratio": 1.3},
            "fear": {"slow": True, "pause_ratio": 1.4},
            "calm": {"slow": True, "pause_ratio": 1.1},
            "neutral": {"slow": False, "pause_ratio": 1.0}
        }

    def synthesize_empathetic_response(
        self,
        text: str,
        user_emotion: str = "neutral",
        language: str = "ko"
    ) -> Dict[str, Any]:
        """
        Generate speech with empathetic adjustments based on user's emotion

        Args:
            text: Response text
            user_emotion: Detected user emotion
            language: Language code

        Returns:
            TTS result with emotion-aware parameters
        """
        # Get speech parameters for emotion
        params = self.emotion_speech_params.get(user_emotion, self.emotion_speech_params["neutral"])

        # Add empathetic pauses for certain emotions
        if user_emotion in ["sadness", "anxiety", "fear"]:
            # Add slight pauses after periods for more empathetic delivery
            text = text.replace(". ", ".  ")  # Extra space creates pause
            text = text.replace("요. ", "요.  ")

        result = self.synthesize_speech(
            text=text,
            language=language,
            slow=params["slow"],
            emotion=user_emotion
        )

        result["emotion_adjusted"] = True
        result["user_emotion"] = user_emotion
        result["speech_params"] = params

        return result


# Singleton instance
_voice_service = None


def get_voice_service() -> VoiceService:
    """Get singleton voice service instance"""
    global _voice_service
    if _voice_service is None:
        _voice_service = EmotionAwareVoiceService()
    return _voice_service
