#!/usr/bin/env python3
"""
음성 프로필 생성 스크립트
ElevenLabs 음성 파일을 사용하여 Zonos TTS용 음성 프로필 생성
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv()

import asyncio
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


async def create_voice_profile_from_file():
    """음성 파일로부터 음성 프로필 생성"""
    
    # 음성 파일 경로
    audio_file_path = PROJECT_ROOT / "data" / "ElevenLabs_2025-12-09T05_45_40_서윤쌤 1_gen_sp80_s50_sb75_v3.mp3"
    
    if not audio_file_path.exists():
        logger.error(f"음성 파일을 찾을 수 없습니다: {audio_file_path}")
        return
    
    logger.info(f"음성 파일 로드: {audio_file_path}")
    
    # ZonosTTS 인스턴스 생성 및 모델 로드
    from src.tts import ZonosTTS
    import torch
    
    # CUDA 사용 가능 여부 확인
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"사용할 디바이스: {device}")
    
    tts = ZonosTTS(device=device)
    logger.info("TTS 모델 로드 중...")
    tts.load_model()
    
    if tts.model is None:
        logger.error("TTS 모델을 로드할 수 없습니다.")
        return
    
    # 음성 프로필 생성
    profile_name = "seoyun_teacher"  # 프로필 이름
    description = "서윤쌤 목소리 (ElevenLabs 클론)"
    
    logger.info(f"음성 프로필 생성 중: {profile_name}...")
    
    try:
        profile = tts.create_voice_profile(
            name=profile_name,
            reference_audio=str(audio_file_path),
            description=description,
            sample_rate=44100  # MP3 파일의 샘플레이트 (일반적으로 44100)
        )
        
        logger.info(f"✓ 음성 프로필 생성 완료: {profile_name}")
        logger.info(f"  - Speaker embedding: {profile.speaker_embedding is not None}")
        logger.info(f"  - Reference audio: {profile.reference_audio_path}")
        
        # 프로필 저장
        profile_save_path = PROJECT_ROOT / "voice_profiles" / profile_name
        profile_save_path.parent.mkdir(exist_ok=True)
        
        tts.save_voice_profile(profile_name, str(profile_save_path))
        logger.info(f"✓ 음성 프로필 저장 완료: {profile_save_path}")
        
        # 기본 음성 프로필로 설정
        tts.default_voice = profile_name
        logger.info(f"✓ 기본 음성 프로필로 설정: {profile_name}")
        
        return profile
        
    except Exception as e:
        logger.error(f"음성 프로필 생성 실패: {e}", exc_info=True)
        return None


if __name__ == "__main__":
    asyncio.run(create_voice_profile_from_file())

