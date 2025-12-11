@echo off
chcp 65001 > nul
title 마음챗 - 한국어 심리상담 AI

echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║   마음챗 - 한국어 심리상담 AI 시스템                         ║
echo ║   RTX 5060 Ti 최적화 버전                                    ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

REM 가상환경 활성화 (있는 경우)
if exist "venv\Scripts\activate.bat" (
    echo [1/3] 가상환경 활성화 중...
    call venv\Scripts\activate.bat
)

if exist ".venv\Scripts\activate.bat" (
    echo [1/3] 가상환경 활성화 중...
    call .venv\Scripts\activate.bat
)

REM 환경 변수 로드
if exist ".env" (
    echo [2/3] 환경 변수 로드 중...
    for /f "tokens=*" %%a in (.env) do (
        set %%a
    )
)

REM 서버 시작
echo [3/3] 서버 시작 중...
echo.
python start_all.py

pause
