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
import socket
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

def check_and_upgrade_pytorch():
    """PyTorch 버전 확인 및 자동 업그레이드"""
    print(f"{Colors.BLUE}[0/6] PyTorch 버전 확인 중...{Colors.ENDC}")
    
    try:
        import torch
        current_version = torch.__version__
        print(f"  현재 PyTorch 버전: {current_version}")
        
        # 버전 파싱 (예: "2.5.1+cu121" -> (2, 5, 1))
        version_parts = current_version.split('+')[0].split('.')
        major = int(version_parts[0])
        minor = int(version_parts[1]) if len(version_parts) > 1 else 0
        patch = int(version_parts[2]) if len(version_parts) > 2 else 0
        
        # CUDA 버전 확인
        cuda_version = None
        if '+' in current_version:
            cuda_part = current_version.split('+')[1]
            if 'cu' in cuda_part:
                cuda_version = cuda_part.split('cu')[1]
        
        # PyTorch 2.6.0 이상 필요
        needs_upgrade = (major < 2) or (major == 2 and minor < 6)
        
        if needs_upgrade:
            print(f"  {Colors.WARNING}⚠{Colors.ENDC} PyTorch 업그레이드 필요 (현재: {current_version}, 필요: 2.6.0+)")
            print(f"  {Colors.BLUE}PyTorch 업그레이드 중...{Colors.ENDC}")
            
            # CUDA 버전에 맞는 업그레이드 명령어 생성
            if cuda_version:
                # CUDA 버전이 있으면 해당 버전으로 설치
                index_url = f"https://download.pytorch.org/whl/cu{cuda_version}"
                upgrade_cmd = [
                    sys.executable, "-m", "pip", "install", 
                    "--upgrade", "torch>=2.6.0",
                    "--index-url", index_url
                ]
            else:
                # CUDA 버전이 없으면 기본 설치
                upgrade_cmd = [
                    sys.executable, "-m", "pip", "install",
                    "--upgrade", "torch>=2.6.0"
                ]
            
            try:
                result = subprocess.run(
                    upgrade_cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=300  # 5분 타임아웃
                )
                print(f"  {Colors.GREEN}✓{Colors.ENDC} PyTorch 업그레이드 완료")
                
                # 업그레이드 후 버전 재확인
                import importlib
                importlib.reload(torch)
                new_version = torch.__version__
                print(f"  새로운 PyTorch 버전: {new_version}")
                
            except subprocess.TimeoutExpired:
                print(f"  {Colors.WARNING}⚠{Colors.ENDC} 업그레이드 타임아웃 (계속 진행)")
            except subprocess.CalledProcessError as e:
                print(f"  {Colors.WARNING}⚠{Colors.ENDC} 업그레이드 실패: {e}")
                print(f"  {Colors.WARNING}수동 업그레이드: pip install --upgrade torch>=2.6.0{Colors.ENDC}")
        else:
            print(f"  {Colors.GREEN}✓{Colors.ENDC} PyTorch 버전 확인 완료 ({current_version})")
            
    except ImportError:
        print(f"  {Colors.WARNING}⚠{Colors.ENDC} PyTorch가 설치되지 않음")
        print(f"  {Colors.BLUE}PyTorch 설치 중...{Colors.ENDC}")
        try:
            # CUDA 버전 확인 시도 (nvidia-smi 사용)
            cuda_version = None
            try:
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    # CUDA 버전 추정 (일반적으로 cu121 또는 cu124)
                    # 실제로는 PyTorch 설치 후 자동으로 맞는 버전을 선택하도록 함
                    cuda_version = "121"  # 기본값으로 cu121 사용
            except:
                pass
            
            if cuda_version:
                index_url = f"https://download.pytorch.org/whl/cu{cuda_version}"
                install_cmd = [
                    sys.executable, "-m", "pip", "install",
                    "torch>=2.6.0",
                    "--index-url", index_url
                ]
            else:
                install_cmd = [
                    sys.executable, "-m", "pip", "install",
                    "torch>=2.6.0"
                ]
            
            subprocess.run(install_cmd, check=True, timeout=300)
            print(f"  {Colors.GREEN}✓{Colors.ENDC} PyTorch 설치 완료")
        except Exception as e:
            print(f"  {Colors.WARNING}⚠{Colors.ENDC} PyTorch 설치 실패: {e}")
    except Exception as e:
        print(f"  {Colors.WARNING}⚠{Colors.ENDC} PyTorch 버전 확인 실패: {e}")
    
    print()  # 빈 줄

def check_requirements():
    """필수 요구사항 확인"""
    print(f"{Colors.BLUE}[1/6] 필수 요구사항 확인 중...{Colors.ENDC}")

    errors = []
    warnings = []

    # Python 버전 확인
    if sys.version_info < (3, 9):
        errors.append(f"Python 3.9+ 필요 (현재: {sys.version})")
    else:
        print(f"  {Colors.GREEN}✓{Colors.ENDC} Python {sys.version_info.major}.{sys.version_info.minor}")

    # OpenAI API 키 확인 (선택사항 - Mock 모드 사용 가능)
    if os.getenv('OPENAI_API_KEY'):
        print(f"  {Colors.GREEN}✓{Colors.ENDC} OpenAI API 키 설정됨")
    else:
        # Mock 모드 사용 가능 여부 확인
        try:
            import yaml
            config_path = PROJECT_ROOT / "configs" / "config.yaml"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    provider = config.get('model', {}).get('provider', 'openai')
                    if provider == 'mock':
                        print(f"  {Colors.WARNING}⚠{Colors.ENDC} OpenAI API 키 없음 (Mock 모드로 실행)")
                    else:
                        warnings.append("OPENAI_API_KEY 환경변수가 설정되지 않음 (Mock 모드 권장)")
            else:
                warnings.append("OPENAI_API_KEY 환경변수가 설정되지 않음")
        except:
            warnings.append("OPENAI_API_KEY 환경변수가 설정되지 않음 (Mock 모드 권장)")

    # 설정 파일 확인
    config_path = PROJECT_ROOT / "configs" / "config.yaml"
    if config_path.exists():
        print(f"  {Colors.GREEN}✓{Colors.ENDC} 설정 파일 존재")
    else:
        errors.append(f"설정 파일 없음: {config_path}")

    # GPU 확인 (새로운 gpu_check 모듈 사용)
    # 주의: 여기서는 경고만 표시하고, 실제 검증은 check_gpu_memory()에서 수행
    try:
        from src.gpu_check import check_gpu_availability
        gpu_info = check_gpu_availability(raise_on_failure=False)
        if gpu_info["available"]:
            gpu_name = gpu_info["device_name"]
            gpu_memory = gpu_info.get("total_memory", 0)
            print(f"  {Colors.GREEN}✓{Colors.ENDC} GPU: {gpu_name} ({gpu_memory:.1f}GB)")
        else:
            # GPU가 없으면 경고 표시 (check_gpu_memory()에서 에러 발생)
            print(f"  {Colors.WARNING}⚠{Colors.ENDC} CUDA GPU를 찾을 수 없음 (GPU가 필요합니다)")
            warnings.append("CUDA GPU를 찾을 수 없음 - GPU가 필요합니다")
    except ImportError:
        print(f"  {Colors.WARNING}⚠{Colors.ENDC} PyTorch가 설치되지 않음")
        warnings.append("PyTorch가 설치되지 않음")
    except Exception as e:
        print(f"  {Colors.WARNING}⚠{Colors.ENDC} GPU 확인 실패: {e}")
        warnings.append(f"GPU 확인 실패: {e}")

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
    """GPU 메모리 상태 확인 및 검증"""
    print(f"{Colors.BLUE}[2/6] GPU 메모리 확인 중...{Colors.ENDC}")

    try:
        from src.gpu_check import check_gpu_availability, require_gpu
        
        # GPU 필수 - 감지 실패 시 상세 에러 로그와 함께 예외 발생
        gpu_info = check_gpu_availability(raise_on_failure=True)
        
        if gpu_info["available"]:
            gpu_memory_total = gpu_info.get("total_memory", 0)
            gpu_memory_reserved = 0  # 실제 사용량은 런타임에 확인
            
            # 현재 GPU 메모리 사용량 확인 시도
            try:
                import torch
                if torch.cuda.is_available():
                    gpu_memory_reserved = torch.cuda.memory_reserved(0) / (1024**3)
            except Exception:
                pass
            
            gpu_memory_free = gpu_memory_total - gpu_memory_reserved

            print(f"  총 VRAM: {gpu_memory_total:.1f}GB")
            if gpu_memory_reserved > 0:
                print(f"  사용 가능: {gpu_memory_free:.1f}GB")

            # RTX 4070 Ti (12GB) 최적화 설정
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
            # 이 코드는 실행되지 않아야 함 (raise_on_failure=True이므로)
            print(f"  {Colors.FAIL}✗{Colors.ENDC} GPU 감지 실패")
            raise RuntimeError("GPU가 필요하지만 감지되지 않았습니다.")
    except RuntimeError:
        # GPU 감지 실패 - 이미 상세 로그가 출력되었으므로 재발생
        raise
    except Exception as e:
        print(f"  {Colors.FAIL}✗{Colors.ENDC} GPU 확인 중 오류: {e}")
        raise RuntimeError(f"GPU 확인 중 오류 발생: {e}")

def setup_environment(gpu_mode):
    """환경 설정"""
    print(f"\n{Colors.BLUE}[3/6] 환경 설정 중...{Colors.ENDC}")

    # 환경 변수 설정
    os.environ['CONFIG_PATH'] = str(PROJECT_ROOT / "configs" / "config.yaml")
    os.environ['PYTHONPATH'] = str(PROJECT_ROOT)

    # GPU 모드별 설정 (gpu_mode는 항상 "high", "standard", "light" 중 하나여야 함)
    # CPU 모드는 허용하지 않음 - GPU가 없으면 check_gpu_memory()에서 이미 예외 발생
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
        # 예상치 못한 gpu_mode 값 - 에러 발생
        raise ValueError(f"잘못된 GPU 모드: {gpu_mode}. GPU가 감지되지 않았습니다.")

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
            try:
                import uvicorn
                uvicorn.run(
                    self.module,
                    host=self.host,
                    port=self.port,
                    log_level="warning",
                    access_log=False
                )
            except Exception as e:
                print(f"\n{Colors.FAIL}✗ {self.name} 서버 시작 실패: {e}{Colors.ENDC}")
                import traceback
                traceback.print_exc()

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

def stop_existing_servers():
    """기존 서버 종료"""
    print(f"{Colors.BLUE}[0/6] 기존 서버 종료 중...{Colors.ENDC}")
    
    ports_to_check = [8000, 8001]
    processes_killed = 0
    
    # 포트를 사용 중인 프로세스 찾기 및 종료
    if sys.platform == 'win32':
        # Windows
        try:
            import psutil
            for port in ports_to_check:
                for proc in psutil.process_iter(['pid', 'name', 'connections']):
                    try:
                        for conn in proc.info['connections'] or []:
                            if conn.laddr.port == port:
                                print(f"  포트 {port} 사용 중인 프로세스 종료 중 (PID: {proc.info['pid']})...", end="", flush=True)
                                proc.kill()
                                processes_killed += 1
                                print(f" {Colors.GREEN}✓{Colors.ENDC}")
                                break
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
        except ImportError:
            # psutil이 없으면 netstat 사용
            try:
                result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True, timeout=5)
                lines = result.stdout.split('\n')
                pids_to_kill = set()
                
                for line in lines:
                    for port in ports_to_check:
                        if f':{port}' in line and 'LISTENING' in line:
                            parts = line.split()
                            if len(parts) > 4:
                                pid = parts[-1]
                                if pid.isdigit():
                                    pids_to_kill.add(int(pid))
                
                for pid in pids_to_kill:
                    try:
                        print(f"  프로세스 종료 중 (PID: {pid})...", end="", flush=True)
                        subprocess.run(['taskkill', '/F', '/PID', str(pid)], 
                                     capture_output=True, timeout=5)
                        processes_killed += 1
                        print(f" {Colors.GREEN}✓{Colors.ENDC}")
                    except:
                        pass
            except:
                pass
        
        # Python 프로세스도 확인 (포트 기반으로 찾지 못한 경우)
        try:
            result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                                  capture_output=True, text=True, timeout=5)
            if 'python.exe' in result.stdout:
                print(f"  Python 프로세스 확인 중...", end="", flush=True)
                # 포트를 사용 중인 Python 프로세스만 종료 (전체 종료는 위험)
                print(f" {Colors.WARNING}⚠ (포트 기반 종료 완료){Colors.ENDC}")
        except:
            pass
    else:
        # Linux/Mac
        try:
            import psutil
            for port in ports_to_check:
                for proc in psutil.process_iter(['pid', 'name', 'connections']):
                    try:
                        for conn in proc.info['connections'] or []:
                            if conn.laddr.port == port:
                                print(f"  포트 {port} 사용 중인 프로세스 종료 중 (PID: {proc.info['pid']})...", end="", flush=True)
                                proc.terminate()
                                processes_killed += 1
                                print(f" {Colors.GREEN}✓{Colors.ENDC}")
                                break
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
        except ImportError:
            # lsof 사용
            try:
                for port in ports_to_check:
                    result = subprocess.run(['lsof', '-ti', f':{port}'], 
                                           capture_output=True, text=True, timeout=5)
                    if result.stdout.strip():
                        pids = result.stdout.strip().split('\n')
                        for pid in pids:
                            if pid.isdigit():
                                print(f"  포트 {port} 사용 중인 프로세스 종료 중 (PID: {pid})...", end="", flush=True)
                                subprocess.run(['kill', '-9', pid], timeout=5)
                                processes_killed += 1
                                print(f" {Colors.GREEN}✓{Colors.ENDC}")
            except:
                pass
    
    if processes_killed > 0:
        print(f"  {Colors.GREEN}✓{Colors.ENDC} {processes_killed}개 프로세스 종료됨")
        time.sleep(2)  # 포트 해제 대기
    else:
        print(f"  {Colors.GREEN}✓{Colors.ENDC} 실행 중인 서버 없음")
    
    # 포트가 해제되었는지 확인
    for port in ports_to_check:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        if result == 0:
            print(f"  {Colors.WARNING}⚠ 포트 {port}가 아직 사용 중입니다. 수동으로 종료해주세요.{Colors.ENDC}")
        else:
            print(f"  {Colors.GREEN}✓{Colors.ENDC} 포트 {port} 사용 가능")

def start_servers():
    """모든 서버 시작"""
    print(f"{Colors.BLUE}[4/6] 서버 시작 중...{Colors.ENDC}")

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
    print(f"\n{Colors.BLUE}[5/6] 서버 실행 중{Colors.ENDC}")

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
    
    # 0. 기존 서버 종료
    stop_existing_servers()
    print()  # 빈 줄 추가

    # 0.5. PyTorch 버전 확인 및 업그레이드
    check_and_upgrade_pytorch()

    # 1. 요구사항 확인
    if not check_requirements():
        print(f"\n{Colors.FAIL}필수 요구사항을 충족하지 못했습니다.{Colors.ENDC}")
        print("설치 가이드: python -m pip install -r requirements.txt")
        sys.exit(1)

    # 2. GPU 확인 (필수 - 실패 시 프로그램 종료)
    try:
        gpu_mode = check_gpu_memory()
    except RuntimeError as e:
        print(f"\n{Colors.FAIL}{Colors.BOLD}❌ GPU 검증 실패{Colors.ENDC}")
        print(f"{Colors.FAIL}프로그램을 종료합니다.{Colors.ENDC}\n")
        sys.exit(1)

    # 3. 환경 설정
    setup_environment(gpu_mode)

    # 4. 서버 시작
    servers = start_servers()

    if not servers:
        print(f"\n{Colors.FAIL}서버 시작 실패{Colors.ENDC}")
        sys.exit(1)

    # 5. 상태 출력
    print_status()

    # 6. 브라우저 자동 열기
    print(f"\n{Colors.BLUE}[6/6] 브라우저 열기...{Colors.ENDC}")
    try:
        import webbrowser
        # 서버가 준비될 때까지 잠시 대기
        time.sleep(2)
        webbrowser.open('http://localhost:8000')
        print(f"  {Colors.GREEN}✓{Colors.ENDC} 브라우저가 열렸습니다: http://localhost:8000")
    except Exception as e:
        print(f"  {Colors.WARNING}⚠{Colors.ENDC} 브라우저를 자동으로 열 수 없습니다: {e}")
        print(f"  수동으로 접속: http://localhost:8000")

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
