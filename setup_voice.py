#!/usr/bin/env python3
"""
음성 기능 설치 스크립트
RTX 5060 Ti 최적화

필수 패키지 설치:
- faster-whisper (STT)
- TTS 관련 패키지
- 오디오 처리 패키지
"""

import subprocess
import sys
import os

# 컬러 출력
class Colors:
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def run_command(cmd, description):
    """명령어 실행"""
    print(f"  {description}...", end="", flush=True)
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f" {Colors.GREEN}✓{Colors.ENDC}")
            return True
        else:
            print(f" {Colors.FAIL}✗{Colors.ENDC}")
            if result.stderr:
                print(f"    오류: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f" {Colors.FAIL}✗{Colors.ENDC}")
        print(f"    오류: {e}")
        return False

def main():
    print(f"""
{Colors.BOLD}╔═══════════════════════════════════════════════════════════════╗
║   마음챗 음성 기능 설치 스크립트                              ║
║   RTX 5060 Ti 최적화                                          ║
╚═══════════════════════════════════════════════════════════════╝{Colors.ENDC}
""")

    # 1. 기본 패키지 업그레이드
    print(f"\n{Colors.BOLD}[1/5] pip 업그레이드{Colors.ENDC}")
    run_command(
        f"{sys.executable} -m pip install --upgrade pip",
        "pip 업그레이드"
    )

    # 2. PyTorch (CUDA 지원)
    print(f"\n{Colors.BOLD}[2/5] PyTorch 설치 (CUDA 12.1){Colors.ENDC}")
    run_command(
        f"{sys.executable} -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121",
        "PyTorch CUDA 12.1"
    )

    # 3. STT 패키지 (faster-whisper)
    print(f"\n{Colors.BOLD}[3/5] STT 패키지 설치{Colors.ENDC}")
    stt_packages = [
        ("faster-whisper", "faster-whisper (Whisper STT)"),
        ("webrtcvad", "webrtcvad (음성 활동 감지)"),
        ("sounddevice", "sounddevice (오디오 입력)"),
        ("soundfile", "soundfile (오디오 파일)"),
    ]
    for pkg, desc in stt_packages:
        run_command(f"{sys.executable} -m pip install {pkg}", desc)

    # 4. TTS 패키지
    print(f"\n{Colors.BOLD}[4/5] TTS 패키지 설치{Colors.ENDC}")
    tts_packages = [
        ("TTS", "Coqui TTS"),
        ("pyttsx3", "pyttsx3 (fallback TTS)"),
        ("edge-tts", "Edge TTS (Microsoft)"),
    ]
    for pkg, desc in tts_packages:
        run_command(f"{sys.executable} -m pip install {pkg}", desc)

    # 5. 오디오 처리 패키지
    print(f"\n{Colors.BOLD}[5/5] 오디오 처리 패키지 설치{Colors.ENDC}")
    audio_packages = [
        ("numpy", "numpy"),
        ("scipy", "scipy"),
        ("librosa", "librosa (오디오 분석)"),
        ("pydub", "pydub (오디오 변환)"),
        ("websockets", "websockets"),
    ]
    for pkg, desc in audio_packages:
        run_command(f"{sys.executable} -m pip install {pkg}", desc)

    # 완료 메시지
    print(f"""
{Colors.GREEN}{Colors.BOLD}
╔═══════════════════════════════════════════════════════════════╗
║   설치 완료!                                                  ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║   다음 명령으로 서버를 시작하세요:                            ║
║                                                               ║
║   Windows: start.bat                                          ║
║   Linux:   ./start.sh 또는 python start_all.py                ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
{Colors.ENDC}
""")

if __name__ == "__main__":
    main()
