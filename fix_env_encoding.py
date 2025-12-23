#!/usr/bin/env python3
"""
.env 파일의 인코딩을 UTF-8로 변환하는 스크립트
"""

from pathlib import Path
import sys

def fix_env_encoding():
    """.env 파일을 UTF-8로 변환"""
    env_path = Path(".env")
    
    if not env_path.exists():
        print(".env 파일이 없습니다.")
        return False
    
    # 원본 파일 백업
    backup_path = env_path.with_suffix('.env.backup')
    try:
        import shutil
        shutil.copy(env_path, backup_path)
        print(f"원본 파일을 {backup_path}에 백업했습니다.")
    except Exception:
        pass
    
    try:
        # 바이너리로 읽기
        data = env_path.read_bytes()
        
        # 여러 인코딩 시도
        encodings = ['utf-8', 'utf-8-sig', 'cp949', 'euc-kr', 'latin1', 'iso-8859-1', 'windows-1252']
        content = None
        used_encoding = None
        
        for enc in encodings:
            try:
                content = data.decode(enc)
                used_encoding = enc
                print(f"성공적으로 {enc} 인코딩으로 읽었습니다.")
                break
            except (UnicodeDecodeError, LookupError):
                continue
        
        if content is None:
            # 모든 인코딩 실패 시 errors='replace'로 읽기 (더 안전함)
            print("모든 인코딩 시도 실패. errors='replace'로 읽습니다...")
            try:
                content = data.decode('utf-8', errors='replace')
                used_encoding = 'utf-8 (with errors replaced)'
            except Exception:
                # 최후의 수단: errors='ignore'
                content = data.decode('utf-8', errors='ignore')
                used_encoding = 'utf-8 (with errors ignored)'
        
        # UTF-8로 저장 (BOM 없이)
        env_path.write_text(content, encoding='utf-8', newline='\n')
        print(f".env 파일을 UTF-8로 변환했습니다. (원본 인코딩: {used_encoding})")
        
        # 변환 후 검증
        try:
            env_path.read_text(encoding='utf-8')
            print("검증 완료: .env 파일이 UTF-8로 인코딩되었습니다.")
        except UnicodeDecodeError:
            print("경고: UTF-8 인코딩 검증 실패")
        
        return True
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
        # 백업 복원 시도
        if backup_path.exists():
            try:
                import shutil
                shutil.copy(backup_path, env_path)
                print("백업에서 복원했습니다.")
            except Exception:
                pass
        return False

if __name__ == "__main__":
    success = fix_env_encoding()
    sys.exit(0 if success else 1)

