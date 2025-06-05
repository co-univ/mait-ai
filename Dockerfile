FROM python:3.11-slim

WORKDIR /app

# 시스템 패키지 설치(pdfminer.six 빌드용)
RUN apt-get update && \
    apt-get install -y build-essential libpoppler-cpp-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app
COPY .env .env

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
