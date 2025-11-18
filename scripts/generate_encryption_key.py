#!/usr/bin/env python3
"""
암호화 키 생성 스크립트
Encryption Key Generation Script

PIPA (개인정보보호법) 준수를 위한 암호화 키 생성 도구입니다.
"""

import os
import secrets
import argparse
from pathlib import Path
from cryptography.fernet import Fernet


def generate_fernet_key() -> str:
    """
    Fernet 암호화 키 생성 (대칭키 암호화)

    Returns:
        str: Base64 인코딩된 Fernet 키
    """
    return Fernet.generate_key().decode()


def generate_session_key(length: int = 32) -> str:
    """
    세션 암호화 키 생성

    Args:
        length: 키 길이 (바이트)

    Returns:
        str: URL-safe base64 인코딩된 키
    """
    return secrets.token_urlsafe(length)


def generate_api_key(length: int = 32) -> str:
    """
    API 인증 키 생성

    Args:
        length: 키 길이 (바이트)

    Returns:
        str: URL-safe base64 인코딩된 API 키
    """
    return secrets.token_urlsafe(length)


def generate_hex_key(length: int = 32) -> str:
    """
    16진수 암호화 키 생성

    Args:
        length: 키 길이 (바이트)

    Returns:
        str: 16진수 문자열
    """
    return secrets.token_hex(length)


def save_keys_to_env_file(
    env_path: str = ".env",
    data_encryption_key: str = None,
    log_encryption_key: str = None,
    session_secret_key: str = None,
    api_key: str = None,
    backup: bool = True
) -> None:
    """
    생성된 키를 .env 파일에 저장

    Args:
        env_path: .env 파일 경로
        data_encryption_key: 데이터 암호화 키
        log_encryption_key: 로그 암호화 키
        session_secret_key: 세션 암호화 키
        api_key: API 인증 키
        backup: 기존 .env 파일 백업 여부
    """
    env_file = Path(env_path)

    # 기존 .env 파일 백업
    if env_file.exists() and backup:
        backup_path = env_file.with_suffix('.env.backup')
        env_file.rename(backup_path)
        print(f"✓ 기존 .env 파일을 {backup_path}로 백업했습니다.")

    # .env.example 파일 복사하여 시작
    example_file = env_file.parent / ".env.example"

    if example_file.exists():
        with open(example_file, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = ""

    # 키 교체
    if data_encryption_key:
        content = content.replace("DATA_ENCRYPTION_KEY=", f"DATA_ENCRYPTION_KEY={data_encryption_key}")
        print(f"✓ DATA_ENCRYPTION_KEY 설정됨")

    if log_encryption_key:
        content = content.replace("LOG_ENCRYPTION_KEY=", f"LOG_ENCRYPTION_KEY={log_encryption_key}")
        print(f"✓ LOG_ENCRYPTION_KEY 설정됨")

    if session_secret_key:
        content = content.replace("SESSION_SECRET_KEY=", f"SESSION_SECRET_KEY={session_secret_key}")
        print(f"✓ SESSION_SECRET_KEY 설정됨")

    if api_key:
        # API_KEY= 부분만 교체 (주석 제외)
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip() == "API_KEY=":
                lines[i] = f"API_KEY={api_key}"
                break
        content = '\n'.join(lines)
        print(f"✓ API_KEY 설정됨")

    # .env 파일 저장
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\n✓ .env 파일이 생성되었습니다: {env_file.absolute()}")


def print_keys_to_console(
    data_encryption_key: str,
    log_encryption_key: str,
    session_secret_key: str,
    api_key: str
) -> None:
    """
    생성된 키를 콘솔에 출력

    Args:
        data_encryption_key: 데이터 암호화 키
        log_encryption_key: 로그 암호화 키
        session_secret_key: 세션 암호화 키
        api_key: API 인증 키
    """
    print("\n" + "="*70)
    print("생성된 암호화 키 (Encryption Keys Generated)")
    print("="*70)
    print("\n⚠️  경고: 이 키들을 안전한 곳에 보관하세요!")
    print("⚠️  Warning: Keep these keys in a secure location!\n")

    print("# .env 파일에 추가할 내용:")
    print("-"*70)
    print(f"DATA_ENCRYPTION_KEY={data_encryption_key}")
    print(f"LOG_ENCRYPTION_KEY={log_encryption_key}")
    print(f"SESSION_SECRET_KEY={session_secret_key}")
    print(f"API_KEY={api_key}")
    print("-"*70)

    print("\n📋 키 설명:")
    print(f"  • DATA_ENCRYPTION_KEY: 사용자 데이터 암호화용 (Fernet)")
    print(f"  • LOG_ENCRYPTION_KEY: 로그 파일 암호화용 (Fernet)")
    print(f"  • SESSION_SECRET_KEY: 세션 쿠키 암호화용")
    print(f"  • API_KEY: API 인증용")

    print("\n🔒 보안 권장사항:")
    print("  1. 이 키들을 절대 Git에 커밋하지 마세요")
    print("  2. .env 파일은 .gitignore에 포함되어야 합니다")
    print("  3. 프로덕션 환경에서는 환경 변수로 관리하세요")
    print("  4. 정기적으로 키를 순환(rotate)하세요")
    print("  5. 키가 유출되면 즉시 재생성하세요")
    print("="*70 + "\n")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="암호화 키 생성 도구 (PIPA 준수)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 모든 키 생성 및 출력
  python scripts/generate_encryption_key.py

  # .env 파일에 자동 저장
  python scripts/generate_encryption_key.py --save

  # 특정 키만 생성
  python scripts/generate_encryption_key.py --data-key
  python scripts/generate_encryption_key.py --api-key

  # 백업 없이 .env 파일 덮어쓰기
  python scripts/generate_encryption_key.py --save --no-backup
        """
    )

    parser.add_argument(
        "--save",
        action="store_true",
        help=".env 파일에 키 저장"
    )

    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="기존 .env 파일 백업 안함"
    )

    parser.add_argument(
        "--env-path",
        default=".env",
        help=".env 파일 경로 (기본값: .env)"
    )

    parser.add_argument(
        "--data-key",
        action="store_true",
        help="데이터 암호화 키만 생성"
    )

    parser.add_argument(
        "--log-key",
        action="store_true",
        help="로그 암호화 키만 생성"
    )

    parser.add_argument(
        "--session-key",
        action="store_true",
        help="세션 암호화 키만 생성"
    )

    parser.add_argument(
        "--api-key",
        action="store_true",
        help="API 인증 키만 생성"
    )

    args = parser.parse_args()

    # 특정 키만 생성하도록 지정되었는지 확인
    specific_key_requested = any([
        args.data_key,
        args.log_key,
        args.session_key,
        args.api_key
    ])

    # 키 생성
    data_encryption_key = None
    log_encryption_key = None
    session_secret_key = None
    api_key = None

    if args.data_key or not specific_key_requested:
        data_encryption_key = generate_fernet_key()
        print("✓ 데이터 암호화 키 생성됨")

    if args.log_key or not specific_key_requested:
        log_encryption_key = generate_fernet_key()
        print("✓ 로그 암호화 키 생성됨")

    if args.session_key or not specific_key_requested:
        session_secret_key = generate_session_key()
        print("✓ 세션 암호화 키 생성됨")

    if args.api_key or not specific_key_requested:
        api_key = generate_api_key()
        print("✓ API 인증 키 생성됨")

    # .env 파일에 저장
    if args.save:
        save_keys_to_env_file(
            env_path=args.env_path,
            data_encryption_key=data_encryption_key,
            log_encryption_key=log_encryption_key,
            session_secret_key=session_secret_key,
            api_key=api_key,
            backup=not args.no_backup
        )
    else:
        # 콘솔에 출력
        if not specific_key_requested:
            print_keys_to_console(
                data_encryption_key=data_encryption_key,
                log_encryption_key=log_encryption_key,
                session_secret_key=session_secret_key,
                api_key=api_key
            )
        else:
            print("\n생성된 키:")
            if data_encryption_key:
                print(f"DATA_ENCRYPTION_KEY={data_encryption_key}")
            if log_encryption_key:
                print(f"LOG_ENCRYPTION_KEY={log_encryption_key}")
            if session_secret_key:
                print(f"SESSION_SECRET_KEY={session_secret_key}")
            if api_key:
                print(f"API_KEY={api_key}")
            print()


if __name__ == "__main__":
    main()
