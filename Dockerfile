# ==============================================================================
# Dockerfile for Hugging Face Spaces & Cloud Deployment
# Production-ready Multi-Tenant Advanced RAG Knowledge Assistant
# ==============================================================================

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PORT=7860 \
    BACKEND_PORT=7860 \
    BACKEND_HOST=0.0.0.0 \
    HOME=/home/user \
    HF_HOME=/home/user/.cache/huggingface \
    TRANSFORMERS_CACHE=/home/user/.cache/huggingface/hub \
    TORCH_HOME=/home/user/.cache/torch \
    DATABASE_URL=sqlite:////app/rag_knowledge_db.sqlite3 \
    UPLOAD_DIR=/app/uploads

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user (UID 1000) as required by Hugging Face Spaces
RUN useradd -m -u 1000 user

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copy application files
COPY . /app

# Setup directories and permissions for UID 1000
RUN mkdir -p /app/uploads /home/user/.cache && \
    chown -R user:user /app /home/user

# Switch to non-root user
USER user

# Hugging Face Spaces default port
EXPOSE 7860

# Start FastAPI application
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "7860"]
