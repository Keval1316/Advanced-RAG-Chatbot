FROM python:3.12-slim

WORKDIR /app

# Copy requirements and install
COPY frontend/requirements.txt /app/frontend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/frontend/requirements.txt

# Copy frontend source code
COPY frontend/ /app/frontend/
COPY .env* /app/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8501

CMD ["streamlit", "run", "frontend/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
