#!/bin/bash
# =============================================================================
# 서버 종료 스크립트
# =============================================================================

echo "서버 종료 중..."

# PID 파일에서 프로세스 종료
for pid_file in logs/*.pid; do
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo "  종료: $pid_file (PID: $pid)"
            kill $pid 2>/dev/null
        fi
        rm -f "$pid_file"
    fi
done

# uvicorn 프로세스 정리
pkill -f "uvicorn src.api:app" 2>/dev/null
pkill -f "uvicorn src.voice_api:app" 2>/dev/null
pkill -f "uvicorn src.batch_api:app" 2>/dev/null

echo "✓ 모든 서버 종료됨"
