@echo off
cd /d C:\KoreanPsychologicalCounselingLLMDevelopment
echo ========================================
echo 서버 시작 중...
echo ========================================
python -m uvicorn src.api:app --host 127.0.0.1 --port 8000
pause

