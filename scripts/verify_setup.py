#!/usr/bin/env python3
"""
로컬 테스트 환경 검증 스크립트
RTX 5060 Ti 16GB / Intel Ultra 5 245KF / 32GB RAM
"""

import sys
import os

# 색상 출력
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_status(name: str, status: bool, detail: str = ""):
    icon = f"{Colors.GREEN}✓{Colors.END}" if status else f"{Colors.RED}✗{Colors.END}"
    detail_str = f" ({detail})" if detail else ""
    print(f"  {icon} {name}{detail_str}")
    return status

def check_python():
    """Python 버전 확인"""
    version = sys.version_info
    ok = version.major == 3 and version.minor >= 10
    return print_status("Python 버전", ok, f"{version.major}.{version.minor}.{version.micro}")

def check_cuda():
    """CUDA 확인"""
    try:
        import torch
        available = torch.cuda.is_available()
        if available:
            gpu_name = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
            return print_status("CUDA/GPU", True, f"{gpu_name}, {vram:.1f}GB")
        else:
            return print_status("CUDA/GPU", False, "CUDA 사용 불가")
    except ImportError:
        return print_status("CUDA/GPU", False, "PyTorch 미설치")

def check_memory():
    """메모리 확인"""
    try:
        import psutil
        mem = psutil.virtual_memory()
        total_gb = mem.total / 1024**3
        ok = total_gb >= 16
        return print_status("시스템 메모리", ok, f"{total_gb:.1f}GB")
    except ImportError:
        return print_status("시스템 메모리", True, "psutil 미설치 (확인 불가)")

def check_package(name: str, import_name: str = None):
    """패키지 설치 확인"""
    import_name = import_name or name
    try:
        __import__(import_name)
        return print_status(name, True)
    except ImportError:
        return print_status(name, False, "미설치")

def check_transformers_model():
    """모델 로드 테스트"""
    try:
        from transformers import AutoTokenizer
        # 토크나이저만 테스트 (빠름)
        tokenizer = AutoTokenizer.from_pretrained(
            "beomi/KoAlpaca-Polyglot-5.8B",
            trust_remote_code=True
        )
        return print_status("HuggingFace 모델 접근", True)
    except Exception as e:
        return print_status("HuggingFace 모델 접근", False, str(e)[:50])

def check_whisper():
    """Whisper 확인"""
    try:
        from faster_whisper import WhisperModel
        return print_status("faster-whisper", True)
    except ImportError:
        try:
            import whisper
            return print_status("openai-whisper", True, "faster-whisper 권장")
        except ImportError:
            return print_status("Whisper STT", False, "미설치")

def check_tts():
    """TTS 확인"""
    try:
        from TTS.api import TTS
        return print_status("Coqui TTS", True)
    except ImportError:
        try:
            from gtts import gTTS
            return print_status("gTTS", True, "Coqui TTS 권장")
        except ImportError:
            return print_status("TTS", False, "미설치")

def check_directories():
    """디렉토리 확인"""
    dirs = ["logs", "outputs", "voice_profiles", "knowledge_base"]
    all_ok = True
    for d in dirs:
        exists = os.path.isdir(d)
        if not exists:
            all_ok = False
    return print_status("필수 디렉토리", all_ok, ", ".join(dirs))

def check_config():
    """설정 파일 확인"""
    config_files = [
        "configs/config.yaml",
        "configs/config.local-test.yaml",
        ".env"
    ]
    results = []
    for f in config_files:
        if os.path.isfile(f):
            results.append(f"{os.path.basename(f)}✓")
        else:
            results.append(f"{os.path.basename(f)}✗")
    all_ok = all("✓" in r for r in results)
    return print_status("설정 파일", all_ok, ", ".join(results))

def estimate_vram_usage():
    """VRAM 사용량 예상"""
    print(f"\n{Colors.BLUE}📊 예상 VRAM 사용량 (16GB 기준):{Colors.END}")
    print("  • KoAlpaca 5.8B (4bit): ~4GB")
    print("  • Whisper medium: ~2GB")
    print("  • Coqui TTS: ~2GB")
    print("  • 버퍼/오버헤드: ~2GB")
    print("  ─────────────────")
    print("  • 총 예상: ~10GB ✓ (여유 6GB)")

def main():
    print(f"\n{Colors.BLUE}{'='*50}{Colors.END}")
    print(f"{Colors.BLUE}  한국어 심리상담 LLM - 환경 검증{Colors.END}")
    print(f"{Colors.BLUE}{'='*50}{Colors.END}\n")

    results = []

    print(f"{Colors.YELLOW}[시스템 환경]{Colors.END}")
    results.append(check_python())
    results.append(check_cuda())
    results.append(check_memory())

    print(f"\n{Colors.YELLOW}[핵심 패키지]{Colors.END}")
    results.append(check_package("torch"))
    results.append(check_package("transformers"))
    results.append(check_package("accelerate"))
    results.append(check_package("bitsandbytes"))
    results.append(check_package("peft"))

    print(f"\n{Colors.YELLOW}[음성 처리]{Colors.END}")
    results.append(check_whisper())
    results.append(check_tts())
    results.append(check_package("soundfile"))
    results.append(check_package("librosa"))

    print(f"\n{Colors.YELLOW}[웹 프레임워크]{Colors.END}")
    results.append(check_package("fastapi"))
    results.append(check_package("uvicorn"))
    results.append(check_package("websockets"))

    print(f"\n{Colors.YELLOW}[파일 시스템]{Colors.END}")
    results.append(check_directories())
    results.append(check_config())

    print(f"\n{Colors.YELLOW}[모델 접근]{Colors.END}")
    results.append(check_transformers_model())

    estimate_vram_usage()

    # 결과 요약
    passed = sum(results)
    total = len(results)

    print(f"\n{Colors.BLUE}{'='*50}{Colors.END}")
    if passed == total:
        print(f"{Colors.GREEN}✓ 모든 검사 통과! ({passed}/{total}){Colors.END}")
        print(f"\n다음 명령으로 테스트를 시작하세요:")
        print(f"  python -m pytest tests/ -v")
    else:
        print(f"{Colors.YELLOW}⚠ 일부 항목 확인 필요 ({passed}/{total}){Colors.END}")
        print(f"\n누락된 패키지 설치:")
        print(f"  pip install -r requirements.txt")
    print(f"{Colors.BLUE}{'='*50}{Colors.END}\n")

    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
