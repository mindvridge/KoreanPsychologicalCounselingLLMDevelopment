"""
TTS 설정 초기화 스크립트
TTS 모델과 음성 프로필을 초기화하고 재로드합니다.
"""

import logging
import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def reset_tts():
    """TTS 설정 초기화"""
    try:
        from src.tts import ZonosTTS
        from src.streaming_tts import StreamingTTS, StreamingTTSConfig
        
        logger.info("=" * 60)
        logger.info("TTS 설정 초기화 시작...")
        logger.info("=" * 60)
        
        # 1. ZonosTTS 초기화
        logger.info("\n[1/3] ZonosTTS 모델 초기화 중...")
        try:
            # 전역 TTS 엔진이 있다면 초기화
            # API에서 사용하는 전역 변수 접근 시도
            import src.api as api_module
            if hasattr(api_module, '_tts_engine') and api_module._tts_engine is not None:
                logger.info("전역 TTS 엔진 발견, 초기화 중...")
                api_module._tts_engine.reset_model()
                api_module._tts_engine.load_model(force_reload=True)
                logger.info("✅ 전역 TTS 엔진 초기화 완료")
            else:
                # 직접 생성하여 초기화
                logger.info("새로운 TTS 엔진 생성 및 초기화 중...")
                tts = ZonosTTS(device="cuda")
                tts.reset_model()
                tts.load_model(force_reload=True)
                logger.info("✅ ZonosTTS 초기화 완료")
        except Exception as e:
            logger.error(f"❌ ZonosTTS 초기화 실패: {e}")
            logger.warning("계속 진행합니다...")
        
        # 2. StreamingTTS 초기화
        logger.info("\n[2/3] StreamingTTS 엔진 초기화 중...")
        try:
            if hasattr(api_module, 'streaming_tts') and api_module.streaming_tts is not None:
                logger.info("전역 StreamingTTS 발견, 초기화 중...")
                if hasattr(api_module.streaming_tts, 'engine') and api_module.streaming_tts.engine is not None:
                    api_module.streaming_tts.engine.reset_model()
                    api_module.streaming_tts.engine.load_model(force_reload=True)
                    logger.info("✅ 전역 StreamingTTS 엔진 초기화 완료")
                else:
                    logger.warning("StreamingTTS 엔진이 아직 로드되지 않았습니다.")
            else:
                logger.info("StreamingTTS는 나중에 자동으로 초기화됩니다.")
        except Exception as e:
            logger.error(f"❌ StreamingTTS 초기화 실패: {e}")
            logger.warning("계속 진행합니다...")
        
        # 3. 음성 프로필 재학습 안내
        logger.info("\n[3/3] 음성 프로필 상태 확인...")
        try:
            if hasattr(api_module, '_tts_engine') and api_module._tts_engine is not None:
                profiles = api_module._tts_engine.list_voice_profiles()
                if profiles:
                    logger.info(f"현재 등록된 음성 프로필: {len(profiles)}개")
                    for profile in profiles:
                        logger.info(f"  - {profile.get('name', 'unknown')}: {profile.get('description', '')}")
                    logger.info("\n음성 프로필을 재학습하려면:")
                    logger.info("  python -c \"from src.tts import ZonosTTS; tts = ZonosTTS(); tts.load_model(); tts.create_voice_profile('seoyun_teacher', 'path/to/audio.wav', force_relearn=True)\"")
                else:
                    logger.warning("등록된 음성 프로필이 없습니다.")
                    logger.info("음성 프로필을 생성하려면:")
                    logger.info("  python -c \"from src.tts import ZonosTTS; tts = ZonosTTS(); tts.load_model(); tts.create_voice_profile('seoyun_teacher', 'path/to/audio.wav')\"")
        except Exception as e:
            logger.warning(f"음성 프로필 확인 실패: {e}")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ TTS 설정 초기화 완료!")
        logger.info("=" * 60)
        logger.info("\n다음 단계:")
        logger.info("1. 서버를 재시작하면 새로운 설정이 적용됩니다.")
        logger.info("2. 음성 프로필을 재학습하려면 위의 명령어를 사용하세요.")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ TTS 초기화 중 오류 발생: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = reset_tts()
    sys.exit(0 if success else 1)

