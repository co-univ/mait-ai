# ==========================
#  1️⃣ 빌드 단계 (Builder)
# ==========================
FROM python:3.11-slim AS builder

WORKDIR /app

# 빌드 시 필요한 패키지만 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpoppler-cpp-dev && \
    rm -rf /var/lib/apt/lists/*

# pip 업그레이드 및 requirements 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt


# ==========================
#  2️⃣ 런타임 단계 (Runner)
# ==========================
FROM python:3.11-slim

WORKDIR /app

# 런타임에 필요한 최소 패키지 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpoppler-cpp-dev \
        libmagic1 && \
    rm -rf /var/lib/apt/lists/*

# Builder 단계에서 설치된 Python 패키지만 복사
COPY --from=builder /install /usr/local

# 앱 복사
COPY app ./app

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Seoul

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
