#!/usr/bin/env python3
"""
원클릭 서버 실행 스크립트
One-Click Server Launch Script

이 스크립트는 모든 것을 자동으로 설정하고 서버를 시작합니다.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


class Colors:
    """터미널 색상"""
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


def print_step(message):
    """단계 출력"""
    print(f"\n{Colors.BLUE}{'='*70}{Colors.NC}")
    print(f"{Colors.BLUE}{message}{Colors.NC}")
    print(f"{Colors.BLUE}{'='*70}{Colors.NC}\n")


def print_success(message):
    """성공 메시지"""
    print(f"{Colors.GREEN}✓{Colors.NC} {message}")


def print_warning(message):
    """경고 메시지"""
    print(f"{Colors.YELLOW}⚠{Colors.NC} {message}")


def print_error(message):
    """오류 메시지"""
    print(f"{Colors.RED}✗{Colors.NC} {message}")


def run_command(cmd, description, check=True, capture_output=False):
    """명령 실행"""
    try:
        if capture_output:
            result = subprocess.run(
                cmd,
                shell=True,
                check=check,
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        else:
            subprocess.run(cmd, shell=True, check=check)
            return True
    except subprocess.CalledProcessError as e:
        if check:
            print_error(f"{description} 실패")
            return False
        return False


def check_python_version():
    """Python 버전 확인"""
    print_step("1. Python 버전 확인")

    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error(f"Python 3.8 이상이 필요합니다. 현재 버전: {version.major}.{version.minor}")
        sys.exit(1)

    print_success(f"Python {version.major}.{version.minor}.{version.micro} 확인됨")
    return True


def setup_virtual_environment():
    """가상 환경 설정"""
    print_step("2. 가상 환경 설정")

    venv_path = Path("venv")

    if venv_path.exists():
        print_success("가상 환경이 이미 존재합니다")
        return True

    print("가상 환경을 생성합니다...")
    if not run_command(f"{sys.executable} -m venv venv", "가상 환경 생성"):
        print_error("가상 환경 생성 실패")
        return False

    print_success("가상 환경 생성 완료")
    return True


def get_pip_command():
    """pip 명령어 가져오기"""
    if platform.system() == "Windows":
        return os.path.join("venv", "Scripts", "pip")
    else:
        return os.path.join("venv", "bin", "pip")


def get_python_command():
    """python 명령어 가져오기"""
    if platform.system() == "Windows":
        return os.path.join("venv", "Scripts", "python")
    else:
        return os.path.join("venv", "bin", "python")


def install_dependencies():
    """의존성 설치"""
    print_step("3. 의존성 설치")

    pip_cmd = get_pip_command()

    # pip 업그레이드
    print("pip를 업그레이드합니다...")
    run_command(f"{pip_cmd} install --upgrade pip", "pip 업그레이드", check=False)

    # requirements.txt 확인
    if not Path("requirements.txt").exists():
        print_error("requirements.txt 파일이 없습니다")
        return False

    print("의존성을 설치합니다... (시간이 걸릴 수 있습니다)")
    if not run_command(f"{pip_cmd} install -r requirements.txt", "의존성 설치", check=False):
        print_warning("일부 의존성 설치 실패 (계속 진행)")
    else:
        print_success("의존성 설치 완료")

    return True


def create_directories():
    """필요한 디렉토리 생성"""
    print_step("4. 디렉토리 생성")

    directories = ["data", "logs", "mental_health_vectors"]

    for dir_name in directories:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print_success(f"{dir_name}/ 디렉토리 생성")
        else:
            print_success(f"{dir_name}/ 디렉토리 존재 확인")

    return True


def setup_env_file():
    """환경 설정 파일 생성"""
    print_step("5. 환경 설정 파일 생성")

    env_path = Path(".env")
    env_example_path = Path(".env.example")

    if env_path.exists():
        print_success(".env 파일이 이미 존재합니다")
        return True

    if not env_example_path.exists():
        print_error(".env.example 파일이 없습니다")
        return False

    # .env.example을 .env로 복사
    import shutil
    shutil.copy(env_example_path, env_path)
    print_success(".env 파일 생성 완료")

    # 암호화 키 생성
    print("\n암호화 키를 생성합니다...")
    python_cmd = get_python_command()

    if Path("scripts/generate_encryption_key.py").exists():
        result = run_command(
            f"{python_cmd} scripts/generate_encryption_key.py --save --no-backup",
            "암호화 키 생성",
            check=False
        )
        if result:
            print_success("암호화 키 생성 완료")
        else:
            print_warning("암호화 키 생성 건너뜀 (나중에 수동으로 생성 가능)")
    else:
        print_warning("암호화 키 생성 스크립트가 없습니다")

    return True


def initialize_database():
    """데이터베이스 초기화"""
    print_step("6. 데이터베이스 초기화")

    db_path = Path("data/mental_health.db")

    if db_path.exists():
        print_success("데이터베이스가 이미 존재합니다")
        return True

    print("데이터베이스를 초기화합니다...")
    python_cmd = get_python_command()

    if Path("scripts/init_database.py").exists():
        result = run_command(
            f"{python_cmd} scripts/init_database.py",
            "데이터베이스 초기화",
            check=False
        )
        if result:
            print_success("데이터베이스 초기화 완료")
        else:
            print_warning("데이터베이스 초기화 실패 (서버 시작 시 자동 생성)")
    else:
        print_warning("데이터베이스 초기화 스크립트가 없습니다 (서버 시작 시 자동 생성)")

    return True


def check_knowledge_base():
    """지식 베이스 확인"""
    print_step("7. RAG 지식 베이스 확인")

    kb_path = Path("knowledge_base")

    if not kb_path.exists() or not any(kb_path.iterdir()):
        print_warning("knowledge_base 디렉토리가 비어있습니다")
        print_warning("RAG 시스템을 사용하려면 지식 베이스 문서를 추가하세요")
        return True

    # 파일 개수 세기
    file_count = sum(1 for _ in kb_path.rglob("*") if _.is_file())
    print_success(f"지식 베이스 파일 {file_count}개 발견")

    return True


def start_server():
    """서버 시작"""
    print_step("8. 서버 시작")

    python_cmd = get_python_command()

    # API 파일 확인
    if not Path("src/api.py").exists():
        print_error("src/api.py 파일이 없습니다")
        return False

    print(f"\n{Colors.GREEN}{'='*70}{Colors.NC}")
    print(f"{Colors.GREEN}서버를 시작합니다...{Colors.NC}")
    print(f"{Colors.GREEN}{'='*70}{Colors.NC}\n")

    print("접속 주소:")
    print(f"  - 메인 페이지: {Colors.BLUE}http://localhost:8000{Colors.NC}")
    print(f"  - API 문서: {Colors.BLUE}http://localhost:8000/docs{Colors.NC}")
    print(f"  - Health Check: {Colors.BLUE}http://localhost:8000/api/v1/health{Colors.NC}")
    print(f"\n서버를 중지하려면 Ctrl+C를 누르세요.\n")

    # uvicorn 확인
    try:
        subprocess.run(
            f"{pip_cmd} show uvicorn",
            shell=True,
            check=True,
            capture_output=True
        )
        use_uvicorn = True
    except:
        use_uvicorn = False

    # 서버 시작
    try:
        if use_uvicorn:
            # uvicorn으로 시작 (권장)
            uvicorn_cmd = get_python_command().replace("python", "uvicorn") if platform.system() != "Windows" else os.path.join("venv", "Scripts", "uvicorn")

            subprocess.run(
                f"{python_cmd} -m uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload",
                shell=True
            )
        else:
            # 직접 실행
            subprocess.run(
                f"{python_cmd} src/api.py",
                shell=True
            )
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}서버를 종료합니다...{Colors.NC}")
        print_success("서버가 정상적으로 종료되었습니다")

    return True


def main():
    """메인 함수"""
    print(f"\n{Colors.GREEN}{'='*70}{Colors.NC}")
    print(f"{Colors.GREEN}한국어 심리 상담 AI - 원클릭 서버 실행{Colors.NC}")
    print(f"{Colors.GREEN}Korean Psychological Counseling AI - One-Click Launch{Colors.NC}")
    print(f"{Colors.GREEN}{'='*70}{Colors.NC}\n")

    # 현재 디렉토리가 프로젝트 루트인지 확인
    if not Path("src").exists() or not Path("requirements.txt").exists():
        print_error("프로젝트 루트 디렉토리에서 실행해주세요")
        sys.exit(1)

    # 각 단계 실행
    steps = [
        check_python_version,
        setup_virtual_environment,
        install_dependencies,
        create_directories,
        setup_env_file,
        initialize_database,
        check_knowledge_base,
        start_server
    ]

    for step in steps:
        if not step():
            print_error("\n설정 중 오류가 발생했습니다")
            sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}사용자가 중단했습니다{Colors.NC}")
        sys.exit(0)
    except Exception as e:
        print_error(f"\n예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
