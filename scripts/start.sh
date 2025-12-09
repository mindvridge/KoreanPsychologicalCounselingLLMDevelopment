#!/bin/bash

# ============================================================================
# Startup script for Korean Mental Health LLM
# ============================================================================

set -e

echo "========================================="
echo "Korean Mental Health LLM Starting..."
echo "========================================="

# Load environment variables
if [ -f .env ]; then
    echo "Loading environment variables from .env"
    export $(cat .env | grep -v "^#" | xargs)
fi

# Check CUDA availability
echo "Checking CUDA availability..."
python3 -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA device count: {torch.cuda.device_count()}')" || true

# Run database migrations if needed
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Running database migrations..."
    python3 scripts/migrate_db.py
fi

# Start application based on mode
if [ "$APP_MODE" = "api" ]; then
    echo "Starting in API mode..."
    exec python3 -m uvicorn src.api:app --host 0.0.0.0 --port 8000
elif [ "$APP_MODE" = "gradio" ]; then
    echo "Starting in Gradio mode..."
    exec python3 app.py
else
    echo "Starting in hybrid mode (Gradio + API)..."
    # Start both services using supervisord or similar
    exec python3 src/api.py
fi
