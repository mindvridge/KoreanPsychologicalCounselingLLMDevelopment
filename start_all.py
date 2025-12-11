#!/usr/bin/env python3
"""
마음챗 통합 서버 실행 스크립트
RTX 5060 Ti 최적화 버전

모든 서비스를 한 번에 실행:
- 메인 API 서버 (포트 8000)
- 음성 API 서버 (포트 8001)
- STT/TTS 모델 자동 로드
"""

import os
import sys
import time
import signal
import subprocess
import threading
from pathlib import Path

# Windows 인코딩 문제 해결
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# 프로젝트 루트 설정
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv()

# 컬러 출력
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_banner():
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   {Colors.GREEN}마음챗 - 한국어 심리상담 AI 시스템{Colors.CYAN}                        ║
║   Korean Psychological Counseling LLM                         ║
║                                                               ║
║   {Colors.WARNING}RTX 5060 Ti 최적화 버전{Colors.CYAN}                                ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
{Colors.ENDC}
"""
    print(banner)

def check_requirements():
    """필수 요구사항 확인"""
    print(f"{Colors.BLUE}[1/5] 필수 요구사항 확인 중...{Colors.ENDC}")

    errors = []
    warnings = []

    # Python 버전 확인
    if sys.version_info < (3, 9):
        errors.append(f"Python 3.9+ 필요 (현재: {sys.version})")
    else:
        print(f"  {Colors.GREEN}✓{Colors.ENDC} Python {sys.version_info.major}.{sys.version_info.minor}")

    # OpenAI API 키 확인
    if os.getenv('OPENAI_API_KEY'):
        print(f"  {Colors.GREEN}✓{Colors.ENDC} OpenAI API 키 설정됨")
    else:
        errors.append("OPENAI_API_KEY 환경변수가 설정되지 않음")

    # 설정 파일 확인
    config_path = PROJECT_ROOT / "configs" / "config.yaml"
    if config_path.exists():
        print(f"  {Colors.GREEN}✓{Colors.ENDC} 설정 파일 존재")
    else:
        errors.append(f"설정 파일 없음: {config_path}")

    # GPU 확인
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print(f"  {Colors.GREEN}✓{Colors.ENDC} GPU: {gpu_name} ({gpu_memory:.1f}GB)")
        else:
            warnings.append("CUDA GPU를 찾을 수 없음 (CPU 모드로 실행)")
    except ImportError:
        warnings.append("PyTorch가 설치되지 않음")

    # 필수 패키지 확인
    required_packages = ['fastapi', 'uvicorn', 'yaml', 'openai']
    for pkg in required_packages:
        try:
            __import__(pkg)
            print(f"  {Colors.GREEN}✓{Colors.ENDC} {pkg}")
        except ImportError:
            errors.append(f"패키지 없음: {pkg}")

    # 결과 출력
    if warnings:
        for w in warnings:
            print(f"  {Colors.WARNING}⚠{Colors.ENDC} {w}")

    if errors:
        print(f"\n{Colors.FAIL}오류 발견:{Colors.ENDC}")
        for e in errors:
            print(f"  {Colors.FAIL}✗{Colors.ENDC} {e}")
        return False

    print(f"  {Colors.GREEN}모든 요구사항 충족{Colors.ENDC}\n")
    return True

def check_gpu_memory():
    """GPU 메모리 상태 확인"""
    print(f"{Colors.BLUE}[2/5] GPU 메모리 확인 중...{Colors.ENDC}")

    try:
        import torch
        if torch.cuda.is_available():
            gpu_memory_total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            gpu_memory_reserved = torch.cuda.memory_reserved(0) / (1024**3)
            gpu_memory_free = gpu_memory_total - gpu_memory_reserved

            print(f"  총 VRAM: {gpu_memory_total:.1f}GB")
            print(f"  사용 가능: {gpu_memory_free:.1f}GB")

            # RTX 5060 Ti 최적화 설정
            if gpu_memory_total >= 16:
                print(f"  {Colors.GREEN}✓{Colors.ENDC} 16GB+ VRAM - 고품질 모드 사용 가능")
                return "high"
            elif gpu_memory_total >= 8:
                print(f"  {Colors.GREEN}✓{Colors.ENDC} 8GB+ VRAM - 표준 모드 사용")
                return "standard"
            else:
                print(f"  {Colors.WARNING}⚠{Colors.ENDC} VRAM 부족 - 경량 모드 사용")
                return "light"
        else:
            print(f"  {Colors.WARNING}⚠{Colors.ENDC} GPU 없음 - CPU 모드")
            return "cpu"
    except Exception as e:
        print(f"  {Colors.WARNING}⚠{Colors.ENDC} GPU 확인 실패: {e}")
        return "cpu"

def setup_environment(gpu_mode):
    """환경 설정"""
    print(f"\n{Colors.BLUE}[3/5] 환경 설정 중...{Colors.ENDC}")

    # 환경 변수 설정
    os.environ['CONFIG_PATH'] = str(PROJECT_ROOT / "configs" / "config.yaml")
    os.environ['PYTHONPATH'] = str(PROJECT_ROOT)

    # GPU 모드별 설정
    if gpu_mode == "high":
        os.environ['WHISPER_MODEL'] = 'large-v3'
        os.environ['TTS_QUALITY'] = 'high'
        print(f"  {Colors.GREEN}✓{Colors.ENDC} 고품질 모드 (Whisper large-v3)")
    elif gpu_mode == "standard":
        os.environ['WHISPER_MODEL'] = 'medium'
        os.environ['TTS_QUALITY'] = 'standard'
        print(f"  {Colors.GREEN}✓{Colors.ENDC} 표준 모드 (Whisper medium)")
    elif gpu_mode == "light":
        os.environ['WHISPER_MODEL'] = 'small'
        os.environ['TTS_QUALITY'] = 'light'
        print(f"  {Colors.GREEN}✓{Colors.ENDC} 경량 모드 (Whisper small)")
    else:
        os.environ['WHISPER_MODEL'] = 'tiny'
        os.environ['TTS_QUALITY'] = 'cpu'
        print(f"  {Colors.WARNING}⚠{Colors.ENDC} CPU 모드 (Whisper tiny)")

    print(f"  {Colors.GREEN}✓{Colors.ENDC} 환경 설정 완료\n")

class ServerProcess:
    """서버 프로세스 관리"""
    def __init__(self, name, module, port, host="0.0.0.0"):
        self.name = name
        self.module = module
        self.port = port
        self.host = host
        self.process = None
        self.thread = None

    def start(self):
        """서버 시작"""
        def run_server():
            import uvicorn
            uvicorn.run(
                self.module,
                host=self.host,
                port=self.port,
                log_level="warning",
                access_log=False
            )

        self.thread = threading.Thread(target=run_server, daemon=True)
        self.thread.start()

    def is_ready(self, timeout=30):
        """서버 준비 상태 확인"""
        import socket
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('127.0.0.1', self.port))
                sock.close()
                if result == 0:
                    return True
            except:
                pass
            time.sleep(0.5)
        return False

def start_servers():
    """모든 서버 시작"""
    print(f"{Colors.BLUE}[4/5] 서버 시작 중...{Colors.ENDC}")

    servers = []

    # 메인 API 서버
    print(f"  메인 API 서버 시작 중 (포트 8000)...", end="", flush=True)
    main_server = ServerProcess("Main API", "src.api:app", 8000)
    main_server.start()

    if main_server.is_ready(timeout=60):
        print(f" {Colors.GREEN}✓{Colors.ENDC}")
        servers.append(main_server)
    else:
        print(f" {Colors.FAIL}✗{Colors.ENDC}")
        return None

    # 음성 API 서버
    print(f"  음성 API 서버 시작 중 (포트 8001)...", end="", flush=True)
    voice_server = ServerProcess("Voice API", "src.voice_api:app", 8001)
    voice_server.start()

    if voice_server.is_ready(timeout=60):
        print(f" {Colors.GREEN}✓{Colors.ENDC}")
        servers.append(voice_server)
    else:
        print(f" {Colors.WARNING}⚠ (텍스트 채팅만 사용 가능){Colors.ENDC}")

    return servers

def print_status():
    """상태 정보 출력"""
    print(f"\n{Colors.BLUE}[5/5] 서버 실행 중{Colors.ENDC}")

    status = f"""
{Colors.GREEN}{Colors.BOLD}
╔═══════════════════════════════════════════════════════════════╗
║  서버가 성공적으로 시작되었습니다!                            ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  {Colors.CYAN}웹 인터페이스:{Colors.GREEN}                                            ║
║    http://localhost:8000                                      ║
║                                                               ║
║  {Colors.CYAN}API 엔드포인트:{Colors.GREEN}                                           ║
║    메인 API:  http://localhost:8000/api/v1                    ║
║    음성 API:  http://localhost:8001                           ║
║    WebSocket: ws://localhost:8001/ws/voice/{{session_id}}       ║
║                                                               ║
║  {Colors.CYAN}API 문서:{Colors.GREEN}                                                 ║
║    http://localhost:8000/docs                                 ║
║                                                               ║
║  {Colors.WARNING}종료: Ctrl+C{Colors.GREEN}                                              ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
{Colors.ENDC}
"""
    print(status)

def main():
    """메인 실행 함수"""
    print_banner()

    # 1. 요구사항 확인
    if not check_requirements():
        print(f"\n{Colors.FAIL}필수 요구사항을 충족하지 못했습니다.{Colors.ENDC}")
        print("설치 가이드: python -m pip install -r requirements.txt")
        sys.exit(1)

    # 2. GPU 확인
    gpu_mode = check_gpu_memory()

    # 3. 환경 설정
    setup_environment(gpu_mode)

    # 4. 서버 시작
    servers = start_servers()

    if not servers:
        print(f"\n{Colors.FAIL}서버 시작 실패{Colors.ENDC}")
        sys.exit(1)

    # 5. 상태 출력
    print_status()

    # 종료 시그널 처리
    def signal_handler(sig, frame):
        print(f"\n\n{Colors.WARNING}서버를 종료합니다...{Colors.ENDC}")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 메인 루프
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}서버를 종료합니다...{Colors.ENDC}")

if __name__ == "__main__":
    main()
