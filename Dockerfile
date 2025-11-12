# Multi-stage build for Korean Mental Health LLM
# Optimized for production deployment with GPU support

# ============================================================================
# Stage 1: Base image with CUDA and Python
# ============================================================================
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04 AS base

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash llmuser

WORKDIR /app

# ============================================================================
# Stage 2: Dependencies installation
# ============================================================================
FROM base AS dependencies

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Download and cache Korean embedding model
RUN python3 -c "from sentence_transformers import SentenceTransformer; \
    model = SentenceTransformer('jhgan/ko-sroberta-multitask'); \
    model.save('/models/ko-sroberta-multitask')"

# ============================================================================
# Stage 3: Application
# ============================================================================
FROM base AS application

# Copy installed packages from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages
COPY --from=dependencies /models /models

# Copy application code
COPY --chown=llmuser:llmuser . /app

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/backups /app/cache && \
    chown -R llmuser:llmuser /app

# Switch to non-root user
USER llmuser

# Set environment variables
ENV TRANSFORMERS_CACHE=/app/cache \
    HF_HOME=/app/cache \
    SENTENCE_TRANSFORMERS_HOME=/models \
    MODEL_CACHE_DIR=/models \
    LOG_DIR=/app/logs \
    DATA_DIR=/app/data \
    BACKUP_DIR=/app/backups

# Expose ports
EXPOSE 7860 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Default command
CMD ["python3", "src/api.py"]

# ============================================================================
# Stage 4: Production (final stage)
# ============================================================================
FROM application AS production

# Additional production optimizations
ENV CUDA_VISIBLE_DEVICES=0 \
    GRADIO_SERVER_NAME=0.0.0.0 \
    GRADIO_SERVER_PORT=7860

# Copy startup script
COPY --chown=llmuser:llmuser scripts/start.sh /app/scripts/start.sh
RUN chmod +x /app/scripts/start.sh

ENTRYPOINT ["/app/scripts/start.sh"]

# ============================================================================
# Development stage (optional)
# ============================================================================
FROM application AS development

USER root

# Install development tools
RUN apt-get update && apt-get install -y \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir \
    pytest \
    pytest-cov \
    pytest-asyncio \
    black \
    flake8 \
    mypy

USER llmuser

CMD ["python3", "app.py"]

# ============================================================================
# Build instructions:
#
# Production:
#   docker build --target production -t korean-mental-health-llm:latest .
#
# Development:
#   docker build --target development -t korean-mental-health-llm:dev .
#
# Run:
#   docker run --gpus all -p 7860:7860 -p 8000:8000 \
#     -v $(pwd)/models:/app/models \
#     -v $(pwd)/logs:/app/logs \
#     korean-mental-health-llm:latest
# ============================================================================
