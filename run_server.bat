@echo off
REM 원클릭 서버 실행 스크립트 (Windows)
REM One-Click Server Launch Script

setlocal enabledelayedexpansion

echo ======================================================================
echo 한국어 심리 상담 AI - 원클릭 서버 실행
echo Korean Psychological Counseling AI - One-Click Launch
echo ======================================================================
echo.

REM 프로젝트 루트 확인
if not exist "src" (
    echo [ERROR] 프로젝트 루트 디렉토리에서 실행해주세요
    pause
    exit /b 1
)

if not exist "requirements.txt" (
    echo [ERROR] requirements.txt 파일이 없습니다
    pause
    exit /b 1
)

REM 1. Python 버전 확인
echo ======================================================================
echo 1. Python 버전 확인
echo ======================================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python이 설치되지 않았습니다
    echo Python 3.8 이상을 설치해주세요: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% 확인됨
echo.

REM 2. 가상 환경 설정
echo ======================================================================
echo 2. 가상 환경 설정
echo ======================================================================
echo.

if not exist "venv" (
    echo 가상 환경을 생성합니다...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] 가상 환경 생성 실패
        pause
        exit /b 1
    )
    echo [OK] 가상 환경 생성 완료
) else (
    echo [OK] 가상 환경이 이미 존재합니다
)
echo.

REM 가상 환경 활성화
call venv\Scripts\activate.bat
echo [OK] 가상 환경 활성화 완료
echo.

REM 3. 의존성 설치
echo ======================================================================
echo 3. 의존성 설치
echo ======================================================================
echo.

echo pip를 업그레이드합니다...
python -m pip install --upgrade pip -q

echo 의존성을 설치합니다... (시간이 걸릴 수 있습니다)
pip install -r requirements.txt -q
if errorlevel 1 (
    echo [WARNING] 일부 의존성 설치 실패 (계속 진행)
)
echo [OK] 의존성 설치 완료
echo.

REM 4. 디렉토리 생성
echo ======================================================================
echo 4. 디렉토리 생성
echo ======================================================================
echo.

for %%d in (data logs mental_health_vectors) do (
    if not exist "%%d" (
        mkdir "%%d"
        echo [OK] %%d\ 디렉토리 생성
    ) else (
        echo [OK] %%d\ 디렉토리 존재 확인
    )
)
echo.

REM 5. 환경 설정 파일 생성
echo ======================================================================
echo 5. 환경 설정 파일 생성
echo ======================================================================
echo.

if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo [OK] .env 파일 생성 완료

        REM 암호화 키 생성
        if exist "scripts\generate_encryption_key.py" (
            echo 암호화 키를 생성합니다...
            python scripts\generate_encryption_key.py --save --no-backup 2>nul
            if errorlevel 1 (
                echo [WARNING] 암호화 키 생성 건너뜀
            ) else (
                echo [OK] 암호화 키 생성 완료
            )
        )
    ) else (
        echo [ERROR] .env.example 파일이 없습니다
        pause
        exit /b 1
    )
) else (
    echo [OK] .env 파일이 이미 존재합니다
)
echo.

REM 6. 데이터베이스 초기화
echo ======================================================================
echo 6. 데이터베이스 초기화
echo ======================================================================
echo.

if not exist "data\mental_health.db" (
    if exist "scripts\init_database.py" (
        echo 데이터베이스를 초기화합니다...
        python scripts\init_database.py 2>nul
        if errorlevel 1 (
            echo [WARNING] 데이터베이스 초기화 실패 (서버 시작 시 자동 생성)
        ) else (
            echo [OK] 데이터베이스 초기화 완료
        )
    ) else (
        echo [WARNING] 데이터베이스 초기화 스크립트가 없습니다
    )
) else (
    echo [OK] 데이터베이스가 이미 존재합니다
)
echo.

REM 7. 지식 베이스 확인
echo ======================================================================
echo 7. RAG 지식 베이스 확인
echo ======================================================================
echo.

if exist "knowledge_base" (
    dir /b /s "knowledge_base\*" 2>nul | find /c /v "" >temp_count.txt
    set /p KB_FILES=<temp_count.txt
    del temp_count.txt
    echo [OK] 지식 베이스 파일 !KB_FILES!개 발견
) else (
    echo [WARNING] knowledge_base 디렉토리가 비어있습니다
    echo [WARNING] RAG 시스템을 사용하려면 지식 베이스 문서를 추가하세요
)
echo.

REM 8. 서버 시작
echo ======================================================================
echo 8. 서버 시작
echo ======================================================================
echo.

echo ======================================================================
echo 서버를 시작합니다...
echo ======================================================================
echo.

echo 접속 주소:
echo   - 메인 페이지: http://localhost:8000
echo   - API 문서: http://localhost:8000/docs
echo   - Health Check: http://localhost:8000/api/v1/health
echo.
echo 서버를 중지하려면 Ctrl+C를 누르세요.
echo.

REM uvicorn이 설치되어 있는지 확인
pip show uvicorn >nul 2>&1
if errorlevel 1 (
    REM 직접 실행
    python src\api.py
) else (
    REM uvicorn으로 시작 (권장)
    python -m uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
)

echo.
echo 서버를 종료합니다...
echo [OK] 서버가 정상적으로 종료되었습니다
pause
