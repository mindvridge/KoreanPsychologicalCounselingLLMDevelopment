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
import sys
import os
import subprocess
import shutil
import ctypes.util

logger = logging.getLogger(__name__)

# Windows에서 espeak-ng 경로 확인 및 패치 적용 (모듈 로드 전)
if sys.platform == 'win32':
    espeak_paths = [
        r"C:\Program Files\eSpeak NG",
        r"C:\Program Files (x86)\eSpeak NG",
    ]
    espeak_path = None
    for path in espeak_paths:
        if os.path.exists(path):
            espeak_path = path
            # PATH에 추가
            current_path = os.environ.get('PATH', '')
            if path not in current_path:
                os.environ['PATH'] = f"{path};{current_path}"
            
            # 환경 변수 설정
            os.environ['PHONEMIZER_ESPEAK_PATH'] = path
            os.environ['ESPEAK_PATH'] = path
            
            # PHONEMIZER_ESPEAK_LIBRARY 환경 변수 설정 (phonemizer가 직접 사용, DLL 우선)
            libespeak_ng_dll = os.path.join(path, "libespeak-ng.dll")
            libespeak_dll = os.path.join(path, "libespeak.dll")
            if os.path.exists(libespeak_ng_dll):
                os.environ['PHONEMIZER_ESPEAK_LIBRARY'] = str(libespeak_ng_dll)
            elif os.path.exists(libespeak_dll):
                os.environ['PHONEMIZER_ESPEAK_LIBRARY'] = str(libespeak_dll)
            else:
                # DLL이 없으면 실행 파일 경로 사용
                espeak_exe_path = os.path.join(path, "espeak.exe")
                espeak_ng_exe_path = os.path.join(path, "espeak-ng.exe")
                if os.path.exists(espeak_exe_path):
                    os.environ['PHONEMIZER_ESPEAK_LIBRARY'] = str(espeak_exe_path)
                elif os.path.exists(espeak_ng_exe_path):
                    os.environ['PHONEMIZER_ESPEAK_LIBRARY'] = str(espeak_ng_exe_path)
            
            # subprocess.run 패치
            original_subprocess_run = subprocess.run
            
            def patched_subprocess_run(*args, **kwargs):
                """subprocess.run을 패치하여 espeak 호출 시 경로를 명시적으로 지정"""
                if args and isinstance(args[0], (list, tuple)) and len(args[0]) > 0:
                    cmd = args[0][0]
                    cmd_lower = cmd.lower() if isinstance(cmd, str) else str(cmd).lower()
                    if cmd_lower in ['espeak', 'espeak-ng', 'espeak.exe', 'espeak-ng.exe']:
                        if not os.path.isabs(cmd):
                            espeak_exe_path = os.path.join(path, "espeak.exe")
                            espeak_ng_exe_path = os.path.join(path, "espeak-ng.exe")
                            if os.path.exists(espeak_exe_path):
                                new_args = [espeak_exe_path] + list(args[0][1:])
                                args = (new_args,) + args[1:]
                            elif os.path.exists(espeak_ng_exe_path):
                                new_args = [espeak_ng_exe_path] + list(args[0][1:])
                                args = (new_args,) + args[1:]
                return original_subprocess_run(*args, **kwargs)
            
            subprocess.run = patched_subprocess_run
            
            # shutil.which 패치
            original_shutil_which = shutil.which
            
            def patched_shutil_which(cmd, mode=os.F_OK | os.X_OK, path=None):
                """shutil.which를 패치하여 espeak을 찾을 때 우리가 지정한 경로를 반환"""
                cmd_lower = cmd.lower() if isinstance(cmd, str) else str(cmd).lower()
                if cmd_lower in ['espeak', 'espeak-ng', 'espeak.exe', 'espeak-ng.exe']:
                    espeak_exe_path = os.path.join(path, "espeak.exe")
                    espeak_ng_exe_path = os.path.join(path, "espeak-ng.exe")
                    if os.path.exists(espeak_exe_path):
                        return espeak_exe_path
                    elif os.path.exists(espeak_ng_exe_path):
                        return espeak_ng_exe_path
                return original_shutil_which(cmd, mode, path)
            
            shutil.which = patched_shutil_which
            
            # ctypes.util.find_library 패치 (phonemizer가 espeak 라이브러리를 찾을 때 사용)
            original_find_library = ctypes.util.find_library
            
            def patched_find_library(name):
                """ctypes.util.find_library를 패치하여 espeak을 찾을 때 우리가 지정한 경로를 반환"""
                name_lower = name.lower() if isinstance(name, str) else str(name).lower()
                if name_lower in ['espeak', 'espeak-ng', 'libespeak-ng', 'libespeak']:
                    # Windows에서 espeak-ng DLL 경로 반환
                    libespeak_ng_dll = os.path.join(path, "libespeak-ng.dll")
                    libespeak_dll = os.path.join(path, "libespeak.dll")
                    if os.path.exists(libespeak_ng_dll):
                        return str(libespeak_ng_dll)
                    elif os.path.exists(libespeak_dll):
                        return str(libespeak_dll)
                    # DLL이 없으면 실행 파일 경로 반환 (fallback)
                    espeak_exe_path = os.path.join(path, "espeak.exe")
                    espeak_ng_exe_path = os.path.join(path, "espeak-ng.exe")
                    if os.path.exists(espeak_exe_path):
                        return str(espeak_exe_path)
                    elif os.path.exists(espeak_ng_exe_path):
                        return str(espeak_ng_exe_path)
                return original_find_library(name)
            
            ctypes.util.find_library = patched_find_library
            
            # phonemizer의 EspeakWrapper.library() 메서드 패치
            # phonemizer가 로드되기 전에 패치를 적용하기 위해 지연 로딩
            def patch_phonemizer_wrapper():
                try:
                    from phonemizer.backend.espeak.wrapper import EspeakWrapper
                    original_library = EspeakWrapper.library
                    
                    @classmethod
                    def patched_library(cls):
                        """EspeakWrapper.library()를 패치하여 espeak 경로를 명시적으로 반환"""
                        # 환경 변수 확인
                        if 'PHONEMIZER_ESPEAK_LIBRARY' in os.environ:
                            library = os.environ['PHONEMIZER_ESPEAK_LIBRARY']
                            if os.path.exists(library):
                                return library
                        
                        # espeak.exe 경로 반환 (Windows에서는 실행 파일을 직접 사용)
                        espeak_exe_path = os.path.join(path, "espeak.exe")
                        espeak_ng_exe_path = os.path.join(path, "espeak-ng.exe")
                        if os.path.exists(espeak_exe_path):
                            return str(espeak_exe_path)
                        elif os.path.exists(espeak_ng_exe_path):
                            return str(espeak_ng_exe_path)
                        
                        # 원래 메서드 호출 (fallback)
                        return original_library()
                    
                    EspeakWrapper.library = patched_library
                    logger.info(f"Patched EspeakWrapper.library() for espeak path: {path}")
                except ImportError:
                    # phonemizer가 아직 로드되지 않은 경우, 나중에 패치
                    pass
            
            # phonemizer 패치를 지연 실행 (phonemizer가 로드된 후)
            import atexit
            atexit.register(patch_phonemizer_wrapper)
            
            # 즉시 시도 (phonemizer가 이미 로드된 경우)
            patch_phonemizer_wrapper()
            
            logger.info(f"Patched subprocess.run, shutil.which, ctypes.util.find_library at module level for espeak path: {path}")
            break


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
    sample_rate: int = 24000  # Zonos 기본 출력 (24000Hz)

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
        """바이트로 변환 (Zonos 공식 방식 - 최소한의 후처리)"""
        import struct
        
        # 원본 오디오 복사 (변경 방지)
        audio_to_save = self.audio.copy()
        target_sample_rate = self.sample_rate
        
        # Zonos는 이미 [-1.0, 1.0] 범위의 float32 오디오를 반환
        # 추가 정규화는 최소화 (원본 품질 유지)
        
        # 오디오 범위 확인
        max_val = np.abs(audio_to_save).max()
        min_val = audio_to_save.min()
        max_abs = audio_to_save.max()
        
        logger.debug(f"to_bytes: audio range=[{min_val:.4f}, {max_abs:.4f}], abs_max={max_val:.4f}")
        
        # 비정상적인 경우만 처리
        # 1. NaN/Inf 값 제거
        if np.any(np.isnan(audio_to_save)) or np.any(np.isinf(audio_to_save)):
            logger.warning("Audio contains NaN/Inf, replacing with zeros")
            audio_to_save = np.nan_to_num(audio_to_save, nan=0.0, posinf=1.0, neginf=-1.0)
        
        # 2. 비정상적으로 큰 값만 정규화 (1.5를 넘는 경우)
        if max_val > 1.5:
            logger.warning(f"Audio exceeds normal range (max={max_val:.4f}), normalizing")
            audio_to_save = audio_to_save / max_val * 0.95
        
        # 3. float32 (-1.0 ~ 1.0)을 int16으로 변환
        # int16 범위: -32768 ~ 32767
        # 정확한 변환: [-1.0, 1.0] -> [-32768, 32767]
        # 스케일링: audio * 32767.0 (최대값 32767 사용, 클리핑 방지)
        audio_clipped = np.clip(audio_to_save, -1.0, 1.0)
        
        # int16 변환 (32767 스케일 사용 - 표준 WAV 포맷)
        # -1.0 -> -32768, 0.0 -> 0, 1.0 -> 32767
        # 32767을 사용하여 대칭적인 범위 유지
        audio_int16 = (audio_clipped * 32767.0).astype(np.int16)
        # 클리핑은 astype이 자동으로 처리하므로 별도 클리핑 불필요
        pcm_data = audio_int16.tobytes()
        
        # WAV 헤더 생성
        num_channels = 1
        bits_per_sample = 16
        byte_rate = target_sample_rate * num_channels * bits_per_sample // 8
        block_align = num_channels * bits_per_sample // 8
        data_size = len(pcm_data)
        file_size = 36 + data_size
        
        # WAV 헤더 작성
        wav_header = struct.pack(
            '<4sI4s4sIHHIIHH4sI',
            b'RIFF',
            file_size,
            b'WAVE',
            b'fmt ',
            16,  # fmt 청크 크기
            1,   # PCM 포맷
            num_channels,
            target_sample_rate,
            byte_rate,
            block_align,
            bits_per_sample,
            b'data',
            data_size
        )
        
        # WAV 파일 = 헤더 + PCM 데이터
        wav_data = wav_header + pcm_data
        
        logger.debug(f"WAV created: {target_sample_rate}Hz, 16-bit, {len(audio_to_save)} samples (original quality preserved, no normalization)")
        
        return wav_data

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
        # GPU 필수 - 감지 실패 시 상세 에러 로그와 함께 예외 발생
        if device == "cuda":
            from src.gpu_check import require_gpu
            device = require_gpu("cuda")
        
        self.model_name = model_name
        self.device = device
        self.default_voice = default_voice

        self.model = None
        self.voice_profiles: Dict[str, VoiceProfile] = {}
        self._lock = threading.Lock()

        logger.info(f"ZonosTTS initializing with model={model_name}, device={device}")

    def reset_model(self) -> None:
        """모델 초기화 (재학습을 위한 리셋)"""
        with self._lock:
            logger.info("Resetting TTS model and voice profiles...")
            self.model = None
            self.voice_profiles.clear()
            # 캐시된 모델 정보도 초기화
            if hasattr(self, 'default_speaker_embedding'):
                self.default_speaker_embedding = None
            logger.info("TTS model reset complete. Call load_model() to reload.")

    def load_model(self, force_reload: bool = False) -> None:
        """모델 로드
        
        Args:
            force_reload: True이면 기존 모델을 무시하고 재로드
        """
        with self._lock:
            if self.model is not None and not force_reload:
                return
            
            if force_reload:
                logger.info("Force reloading TTS model...")
                self.model = None

            try:
                import torch
                import torchaudio
                from zonos.model import Zonos
                from zonos.conditioning import make_cond_dict
                from zonos.utils import DEFAULT_DEVICE
                import os
                
                # Windows에서 C++ 컴파일러가 없을 때 torch.compile 오류 억제
                # eager mode로 fallback하도록 설정
                try:
                    import torch._dynamo
                    torch._dynamo.config.suppress_errors = True
                    # torch.compile 완전 비활성화 (속도 개선)
                    torch._dynamo.config.disable = True
                    logger.info("Disabled torch.compile for better performance (using eager mode)")
                except (ImportError, AttributeError):
                    pass
                
                # phonemizer의 EspeakWrapper.library() 패치 (Zonos가 phonemizer를 사용하기 전에)
                if sys.platform == 'win32':
                    try:
                        from phonemizer.backend.espeak.wrapper import EspeakWrapper
                        original_library = EspeakWrapper.library
                        
                        @classmethod
                        def patched_library(cls):
                            """EspeakWrapper.library()를 패치하여 espeak 경로를 명시적으로 반환"""
                            # 환경 변수 확인
                            if 'PHONEMIZER_ESPEAK_LIBRARY' in os.environ:
                                library = os.environ['PHONEMIZER_ESPEAK_LIBRARY']
                                if os.path.exists(library):
                                    return library
                            
                            # espeak 경로 찾기 (DLL 우선)
                            espeak_paths = [
                                r"C:\Program Files\eSpeak NG",
                                r"C:\Program Files (x86)\eSpeak NG",
                            ]
                            for espeak_path in espeak_paths:
                                if os.path.exists(espeak_path):
                                    # DLL 우선 확인
                                    libespeak_ng_dll = os.path.join(espeak_path, "libespeak-ng.dll")
                                    libespeak_dll = os.path.join(espeak_path, "libespeak.dll")
                                    if os.path.exists(libespeak_ng_dll):
                                        return str(libespeak_ng_dll)
                                    elif os.path.exists(libespeak_dll):
                                        return str(libespeak_dll)
                                    # DLL이 없으면 실행 파일 경로 반환
                                    espeak_exe_path = os.path.join(espeak_path, "espeak.exe")
                                    espeak_ng_exe_path = os.path.join(espeak_path, "espeak-ng.exe")
                                    if os.path.exists(espeak_exe_path):
                                        return str(espeak_exe_path)
                                    elif os.path.exists(espeak_ng_exe_path):
                                        return str(espeak_ng_exe_path)
                            
                            # 원래 메서드 호출 (fallback)
                            return original_library()
                        
                        EspeakWrapper.library = patched_library
                        logger.info("Patched EspeakWrapper.library() in load_model()")
                    except ImportError:
                        pass
                
                # Windows에서 espeak-ng 경로 확인 (모듈 레벨에서 이미 패치가 적용됨)
                if sys.platform == 'win32':
                    espeak_paths = [
                        r"C:\Program Files\eSpeak NG",
                        r"C:\Program Files (x86)\eSpeak NG",
                    ]
                    for espeak_path in espeak_paths:
                        if os.path.exists(espeak_path):
                            # espeak.exe 확인
                            espeak_exe = os.path.join(espeak_path, "espeak.exe")
                            espeak_ng_exe = os.path.join(espeak_path, "espeak-ng.exe")
                            
                            if not os.path.exists(espeak_exe) and os.path.exists(espeak_ng_exe):
                                logger.warning(f"espeak.exe not found. Please create it manually:")
                                logger.warning(f"  Copy-Item '{espeak_ng_exe}' '{espeak_exe}' -Force")
                            elif os.path.exists(espeak_exe):
                                logger.info(f"espeak.exe found: {espeak_exe}")
                            
                            break

                # Zonos 모델 로드 (공식 문서 방식)
                self.model = Zonos.from_pretrained(self.model_name, device=self.device)
                self.model.eval()

                self._make_cond_dict = make_cond_dict
                self._torch = torch
                self._torchaudio = torchaudio
                self._default_device = DEFAULT_DEVICE

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
        sample_rate: int = 16000,
        force_relearn: bool = False
    ) -> VoiceProfile:
        """
        Voice Cloning용 음성 프로필 생성 (재학습 지원)

        Args:
            name: 프로필 이름
            reference_audio: 참조 오디오 (5-30초 권장)
            description: 설명
            sample_rate: 참조 오디오 샘플레이트
            force_relearn: True이면 기존 프로필을 삭제하고 재학습

        Returns:
            VoiceProfile: 생성된 프로필
        """
        if self.model is None:
            self.load_model()

        # 재학습 모드인 경우 기존 프로필 삭제
        if force_relearn and name in self.voice_profiles:
            logger.info(f"Removing existing voice profile '{name}' for relearning...")
            del self.voice_profiles[name]

        # 오디오 로드
        audio_array = self._load_audio(reference_audio, sample_rate)
        
        # 오디오 품질 검증
        audio_duration = len(audio_array) / sample_rate
        if audio_duration < 3.0:
            logger.warning(f"Reference audio is too short ({audio_duration:.2f}s). Recommended: 5-30 seconds.")
        elif audio_duration > 30.0:
            logger.warning(f"Reference audio is too long ({audio_duration:.2f}s). Using first 30 seconds.")
            max_samples = int(sample_rate * 30.0)
            audio_array = audio_array[:max_samples]

        # Speaker Embedding 추출 (재학습)
        with self._lock:
            logger.info(f"Extracting speaker embedding for '{name}'...")
            speaker_embedding = self._extract_speaker_embedding(audio_array, sample_rate)
            logger.info(f"Speaker embedding extracted: shape={speaker_embedding.shape if hasattr(speaker_embedding, 'shape') else 'unknown'}")

        # 프로필 생성
        profile = VoiceProfile(
            name=name,
            speaker_embedding=speaker_embedding,
            reference_audio_path=reference_audio if isinstance(reference_audio, str) else None,
            description=description,
            language="ko"
        )

        self.voice_profiles[name] = profile
        logger.info(f"Voice profile created/relearned: {name}")

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

    def _extract_speaker_embedding(self, audio: np.ndarray, sample_rate: int = 44100) -> np.ndarray:
        """Speaker Embedding 추출"""
        if hasattr(self, '_torch') and hasattr(self, '_torchaudio') and self.model is not None:
            # Zonos의 speaker embedding 추출 (공식 문서 방식)
            with self._torch.no_grad():
                # numpy 배열을 torch tensor로 변환
                audio_tensor = self._torch.tensor(audio, dtype=self._torch.float32)
                
                # Zonos는 (batch, samples) 형태를 기대
                if audio_tensor.ndim == 1:
                    audio_tensor = audio_tensor.unsqueeze(0)
                
                # make_speaker_embedding 호출 (공식 문서: make_speaker_embedding(wav, sampling_rate))
                embedding = self.model.make_speaker_embedding(audio_tensor, sample_rate)
                
                # embedding이 tensor인 경우 numpy로 변환
                if isinstance(embedding, self._torch.Tensor):
                    # BFloat16 등 지원되지 않는 타입을 float32로 변환
                    if embedding.dtype == self._torch.bfloat16:
                        embedding = embedding.float()
                    return embedding.cpu().numpy()
                else:
                    return np.array(embedding)
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

        # 긴 텍스트의 경우 문장 단위로 분할하여 처리
        # Zonos는 긴 텍스트를 처리할 때 중간에 멈출 수 있으므로
        # 문장 단위로 나누어 합성 후 결합
        # 속도 최적화: 더 작은 청크로 빠른 첫 응답
        max_chunk_length = 80  # 최대 청크 길이 (문자 수) - 100에서 80으로 축소하여 더 빠른 처리
        
        if len(text) > max_chunk_length:
            logger.info(f"Text is long ({len(text)} chars), splitting into chunks...")
            # 문장 단위로 분할 (마침표, 물음표, 느낌표 기준)
            import re
            sentences = re.split(r'([.!?。！？]\s*)', text)
            chunks = []
            current_chunk = ""
            
            for i in range(0, len(sentences), 2):
                sentence = sentences[i] + (sentences[i+1] if i+1 < len(sentences) else "")
                if len(current_chunk) + len(sentence) > max_chunk_length and current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    current_chunk += sentence
            
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            
            logger.info(f"Split text into {len(chunks)} chunks")
            
            # 각 청크를 합성하고 결합
            audio_chunks = []
            with self._lock:
                for i, chunk in enumerate(chunks):
                    logger.info(f"Synthesizing chunk {i+1}/{len(chunks)}: {chunk[:50]}...")
                    chunk_audio = self._synthesize_impl(chunk, profile, config)
                    audio_chunks.append(chunk_audio)
                    # 청크 사이에 짧은 무음 추가 (0.2초)
                    silence = np.zeros(int(config.sample_rate * 0.2), dtype=np.float32)
                    audio_chunks.append(silence)
            
            # 모든 청크 결합
            audio = np.concatenate(audio_chunks) if audio_chunks else np.array([], dtype=np.float32)
        else:
            # 짧은 텍스트는 그대로 처리
            with self._lock:
                audio = self._synthesize_impl(text, profile, config)

        # Zonos는 24000Hz 샘플레이트 사용
        actual_sample_rate = 24000
        duration = len(audio) / actual_sample_rate
        logger.info(f"Final audio: length={len(audio)}, duration={duration:.2f}s, text_length={len(text)}")

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
            # Conditioning 설정 (공식 문서 방식)
            # Zonos의 emotion은 list[float] 형식 (8개 값)을 기대함
            emotion_dict = self._map_emotion(config.emotion)
            
            # 딕셔너리를 리스트로 변환 (Zonos 형식: [happiness, sadness, anger, fear, ...])
            # 기본값: [0.3077, 0.0256, 0.0256, 0.0256, 0.0256, 0.0256, 0.2564, 0.3077]
            emotion_list = [
                emotion_dict.get("happiness", 0.0),
                emotion_dict.get("sadness", 0.0),
                emotion_dict.get("anger", 0.0),
                emotion_dict.get("fear", 0.0),
                0.0,  # 추가 감정 1
                0.0,  # 추가 감정 2
                0.0,  # 추가 감정 3
                0.0   # 추가 감정 4
            ]
            
            # 언어 설정: phonemizer가 한국어를 올바르게 처리하도록 명시적 지정
            # espeak-ng는 한국어를 지원하지만, 언어 코드가 정확해야 함
            # "ko" 또는 "kor" 사용 가능, "ko"가 더 일반적
            language_code = "ko"
            
            cond_kwargs = {
                "text": text,
                "language": language_code,  # 한국어 명시적 지정
                "emotion": emotion_list,
                "speaking_rate": config.speaking_rate
            }
            
            logger.debug(f"TTS synthesis: text={text[:50]}..., language={language_code}, emotion={emotion_list[:3]}...")
            
            # speaker embedding이 있는 경우에만 추가
            speaker_embedding = None
            # 모델의 dtype 확인 (bfloat16 또는 float32)
            model_dtype = next(self.model.parameters()).dtype if hasattr(self.model, 'parameters') and next(self.model.parameters(), None) is not None else self._torch.bfloat16
            
            if profile and profile.speaker_embedding is not None:
                # numpy 배열을 torch tensor로 변환 (모델의 dtype으로)
                if isinstance(profile.speaker_embedding, np.ndarray):
                    speaker_embedding = self._torch.tensor(profile.speaker_embedding, dtype=model_dtype)
                    if speaker_embedding.ndim == 1:
                        speaker_embedding = speaker_embedding.unsqueeze(0)
                else:
                    speaker_embedding = profile.speaker_embedding
                    # 이미 tensor인 경우 dtype 변환
                    if isinstance(speaker_embedding, self._torch.Tensor) and speaker_embedding.dtype != model_dtype:
                        speaker_embedding = speaker_embedding.to(dtype=model_dtype)
                cond_kwargs["speaker"] = speaker_embedding
            elif hasattr(self, 'default_speaker_embedding') and self.default_speaker_embedding is not None:
                if isinstance(self.default_speaker_embedding, np.ndarray):
                    speaker_embedding = self._torch.tensor(self.default_speaker_embedding, dtype=model_dtype)
                    if speaker_embedding.ndim == 1:
                        speaker_embedding = speaker_embedding.unsqueeze(0)
                else:
                    speaker_embedding = self.default_speaker_embedding
                    # 이미 tensor인 경우 dtype 변환
                    if isinstance(speaker_embedding, self._torch.Tensor) and speaker_embedding.dtype != model_dtype:
                        speaker_embedding = speaker_embedding.to(dtype=model_dtype)
                cond_kwargs["speaker"] = speaker_embedding
            
            # phonemizer가 espeak을 찾을 수 있도록 환경 변수 재설정 (make_cond_dict 호출 전)
            if sys.platform == 'win32':
                espeak_paths = [
                    r"C:\Program Files\eSpeak NG",
                    r"C:\Program Files (x86)\eSpeak NG",
                ]
                for espeak_path in espeak_paths:
                    if os.path.exists(espeak_path):
                        current_path = os.environ.get('PATH', '')
                        if espeak_path not in current_path:
                            os.environ['PATH'] = f"{espeak_path};{current_path}"
                        os.environ['PHONEMIZER_ESPEAK_PATH'] = espeak_path
                        os.environ['ESPEAK_PATH'] = espeak_path
                        break
            
            # make_cond_dict 호출 전에 언어 설정 확인
            # phonemizer가 한국어를 올바르게 처리하도록 보장
            try:
                cond_dict = self._make_cond_dict(**cond_kwargs)
            except Exception as e:
                # 언어 관련 오류인 경우 로깅
                if "language" in str(e).lower() or "phonemizer" in str(e).lower():
                    logger.warning(f"Language processing error: {e}, retrying with explicit Korean language setting")
                    # 언어를 명시적으로 다시 설정하고 재시도
                    cond_kwargs["language"] = "ko"
                    cond_dict = self._make_cond_dict(**cond_kwargs)
                else:
                    raise e
            
            # cond_dict의 텐서 dtype 변환 (정수형은 유지, float형만 모델 dtype으로 변환)
            model_dtype = next(self.model.parameters()).dtype if hasattr(self.model, 'parameters') and next(self.model.parameters(), None) is not None else self._torch.bfloat16
            
            # 정수형 dtype (인덱스, 토큰 ID 등은 정수형이어야 함)
            integer_dtypes = [self._torch.int8, self._torch.int16, self._torch.int32, self._torch.int64,
                            self._torch.uint8, self._torch.uint16, self._torch.uint32, self._torch.uint64,
                            self._torch.long, self._torch.int]
            
            for key, value in cond_dict.items():
                if isinstance(value, self._torch.Tensor):
                    # 정수형 텐서는 그대로 유지
                    if value.dtype in integer_dtypes:
                        continue
                    # float형 텐서만 모델 dtype으로 변환
                    elif value.dtype.is_floating_point and value.dtype != model_dtype:
                        cond_dict[key] = value.to(dtype=model_dtype)
            
            # Conditioning 준비 (공식 문서 방식)
            conditioning = self.model.prepare_conditioning(cond_dict)

            # 합성 (공식 문서 방식)
            # torch.compile 오류를 억제하고 eager mode로 fallback
            logger.info(f"Starting TTS generation for text: {text[:100]}... (length: {len(text)} chars)")
            
            # CUDA 최적화 제거 - 기본 설정 사용
            
            with self._torch.no_grad():
                try:
                    # Zonos generate 호출
                    # 기본 설정 사용 - max_length 제한 제거 (원본 품질 유지)
                    # Zonos 기본 설정으로 생성
                    
                    # 기본 generate 호출 (최적화 파라미터 없음)
                    import time
                    gen_start_time = time.time()
                    codes = self.model.generate(conditioning)
                    gen_time = time.time() - gen_start_time
                    logger.info(f"TTS generation completed in {gen_time:.2f}s (text_length={len(text)})")
                    logger.debug(f"TTS codes generated: shape={codes.shape if hasattr(codes, 'shape') else 'unknown'}")
                except (RuntimeError, Exception) as e:
                    error_str = str(e)
                    if "Compiler: cl is not found" in error_str or "Compiler:" in error_str or "BackendCompilerFailed" in error_str:
                        # C++ 컴파일러 오류인 경우, torch._dynamo를 비활성화하고 재시도
                        logger.warning("C++ compiler not found, disabling torch.compile and retrying...")
                        try:
                            import torch._dynamo
                            torch._dynamo.config.suppress_errors = True
                            # 재시도 (최적화 파라미터 없이)
                            codes = self.model.generate(conditioning)
                        except Exception as e2:
                            logger.error(f"Failed to generate even with compile disabled: {e2}")
                            raise e
                    else:
                        raise e
                
                # 오디오 디코딩 (Zonos 공식 방식)
                logger.debug("Decoding audio from codes...")
                # Zonos autoencoder.decode()는 텐서를 직접 반환
                # with torch.no_grad() 컨텍스트 내에서 디코딩
                result = self.model.autoencoder.decode(codes)
                
                # GPU에서 CPU로 이동
                if isinstance(result, self._torch.Tensor):
                    audio = result.cpu()
                else:
                    audio = result
                
                # 텐서를 numpy 배열로 변환
                if isinstance(audio, self._torch.Tensor):
                    audio = audio.numpy()
                else:
                    audio = np.array(audio)
                
                # 차원 처리: (batch, samples) 또는 (samples,) 형태
                if audio.ndim > 1:
                    # 배치 차원 제거 (첫 번째 샘플 사용)
                    audio = audio.squeeze()
                    # 여전히 다차원이면 flatten
                    if audio.ndim > 1:
                        audio = audio.flatten()
                
                # 1D 배열 보장
                if audio.ndim == 0:
                    audio = np.array([audio])
                elif audio.ndim > 1:
                    audio = audio.flatten()
                
                # Zonos는 이미 [-1, 1] 범위의 float32 오디오를 반환
                # 추가 정규화는 필요 없지만, 범위 검증은 수행
                max_val = np.abs(audio).max()
                min_val = audio.min()
                max_abs = audio.max()
                
                logger.debug(f"Audio decoded: shape={audio.shape}, dtype={audio.dtype}, range=[{min_val:.4f}, {max_abs:.4f}], abs_max={max_val:.4f}")
                
                # 오디오 길이 확인 및 로깅
                actual_sample_rate = 24000  # Zonos 모델의 실제 샘플레이트
                expected_duration = len(text) * 0.1  # 대략적인 예상 길이 (초당 10자)
                actual_duration = len(audio) / actual_sample_rate
                logger.info(f"Audio decoded: length={len(audio)}, duration={actual_duration:.2f}s, expected~{expected_duration:.2f}s, text_length={len(text)}")
                
                # 오디오가 너무 짧으면 경고
                if actual_duration < expected_duration * 0.5:
                    logger.warning(f"Audio duration ({actual_duration:.2f}s) is much shorter than expected ({expected_duration:.2f}s). Text may have been truncated during generation.")
                
                # NaN 또는 Inf 값 확인 및 제거 (안전성)
                if np.any(np.isnan(audio)) or np.any(np.isinf(audio)):
                    logger.error("Audio contains NaN or Inf values, replacing with zeros")
                    audio = np.nan_to_num(audio, nan=0.0, posinf=1.0, neginf=-1.0)
                
                # Zonos는 이미 정규화된 오디오를 반환하므로 추가 정규화 최소화
                # 다만, 비정상적으로 큰 값만 제한 (클리핑 방지)
                # 정규화 임계값을 높여서 원본 품질 유지
                if max_val > 2.0:  # 2.0을 넘는 경우에만 정규화 (비정상적인 경우)
                    logger.warning(f"Audio exceeds expected range (max={max_val:.4f}), normalizing to prevent clipping")
                    audio = audio / max_val * 0.98  # 98%로 정규화 (더 보수적)
                elif max_val < 0.001:  # 거의 무음인 경우
                    logger.warning(f"Audio too quiet (max={max_val:.4f}), may be silent")
                # 정상 범위 (0.001 ~ 2.0)는 원본 그대로 유지
                
                # float32로 보장
                audio = audio.astype(np.float32)
                
                logger.debug(f"Final audio: shape={audio.shape}, dtype={audio.dtype}, range=[{audio.min():.4f}, {audio.max():.4f}]")
                
                return audio

        except RuntimeError as e:
            if "espeak not installed" in str(e):
                logger.error(f"Zonos synthesis error: {e}")
                logger.error("espeak-ng가 설치되지 않았습니다. Windows에서 설치 방법:")
                logger.error("1. 관리자 권한으로 PowerShell 열기")
                logger.error("2. choco install espeak-ng -y 실행")
                logger.error("또는 https://github.com/espeak-ng/espeak-ng/releases 에서 수동 설치")
            else:
                logger.error(f"Zonos synthesis error: {e}", exc_info=True)
            # 대체 합성 시도
            return self._synthesize_fallback(text)
        except Exception as e:
            logger.error(f"Zonos synthesis error: {e}", exc_info=True)
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
