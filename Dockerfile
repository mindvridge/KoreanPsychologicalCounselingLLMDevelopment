# 한국형 심리상담 LLM Dockerfile
# RTX A100 (80GB) GPU 환경 최적화

# NVIDIA CUDA 기반 이미지 사용
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# 메타데이터
LABEL maintainer="Korean Mental Health LLM Team"
LABEL description="Korean Mental Health Counseling LLM with SOLAR-Ko-10.7B"

# 환경 변수 설정
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=0

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필수 도구 설치
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3-dev \
    git \
    wget \
    curl \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Python 심볼릭 링크 생성
RUN ln -s /usr/bin/python3.10 /usr/bin/python

# pip 업그레이드
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# requirements.txt 복사 및 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트 파일 복사
COPY . .

# 모델 캐시 디렉토리 생성
RUN mkdir -p /app/models /app/logs /app/data

# 권한 설정
RUN chmod -R 755 /app

# 포트 노출
# Gradio: 7860
# API (FastAPI): 8000
EXPOSE 7860 8000

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7860/ || exit 1

# 환경 변수 파일 로드를 위한 엔트리포인트 스크립트 생성
RUN echo '#!/bin/bash\n\
if [ -f .env ]; then\n\
    export $(cat .env | grep -v "^#" | xargs)\n\
fi\n\
exec "$@"' > /entrypoint.sh && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

# 기본 실행 명령 (Gradio 웹 인터페이스)
# 다른 실행 방법:
# - API 서버: docker run -p 8000:8000 image_name python -m uvicorn api:app --host 0.0.0.0 --port 8000
# - CLI: docker run -it image_name python -m src.main
CMD ["python", "-m", "gradio", "app.py"]

# Docker 빌드 명령:
# docker build -t korean-mental-health-llm:latest .

# Docker 실행 명령 (GPU 사용):
# docker run --gpus all -p 7860:7860 -v $(pwd)/models:/app/models korean-mental-health-llm:latest

# Docker Compose 사용 권장 (별도 docker-compose.yml 파일 참조)
