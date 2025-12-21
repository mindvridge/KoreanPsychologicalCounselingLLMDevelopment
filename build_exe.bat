@echo off
chcp 65001 >nul
echo ========================================
echo 마음챗 Windows 실행파일 빌드
echo ========================================
echo.

REM Python이 설치되어 있는지 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo [오류] Python이 설치되어 있지 않습니다.
    echo Python 3.10 이상을 설치해주세요.
    pause
    exit /b 1
)

echo Python 버전 확인 중...
python --version

echo.
echo PyInstaller 설치 확인 중...
python -m pip install --upgrade pip
python -m pip install pyinstaller

echo.
echo 빌드 스크립트 실행 중...
python build_exe.py

if errorlevel 1 (
    echo.
    echo [오류] 빌드에 실패했습니다.
    pause
    exit /b 1
)

echo.
echo ========================================
echo 빌드 완료!
echo ========================================
echo.
echo 실행파일 위치: dist\마음챗.exe
echo.
pause

