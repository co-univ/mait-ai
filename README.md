# 🤖 MAIT AI Server

FastAPI 기반 AI 서버로 OpenAI API 호출, S3 PDF 파싱, 텍스트 변환 기능을 제공합니다.

## ✨ 주요 기능

- 🔥 **FastAPI** 기반 고성능 REST API
- 🧠 **OpenAI API** 통합
- 📄 **PDF 파싱**: 로컬 파일, URL, AWS S3 지원
- 📝 **Markdown → HTML** 변환
- 🐳 **Docker & Docker Compose** 지원
- 🚀 **GitHub Actions CI/CD** 자동 배포
- ☁️ **AWS ECS** 배포 준비 완료

## 📁 프로젝트 구조

```
mait-ai/
├── app/
│   ├── main.py              # FastAPI 애플리케이션
│   ├── config.py            # 환경 설정
│   ├── api/
│   │   └── router.py        # API 라우터
│   ├── services/
│   │   ├── openai_service.py   # OpenAI 통합
│   │   └── file_parser.py      # PDF/Markdown 파서
│   ├── models/
│   │   └── schemas.py       # Pydantic 스키마
│   └── utils/
│       └── utils.py         # 유틸리티 함수
├── .github/workflows/       # GitHub Actions
├── tests/                   # 테스트
├── Dockerfile              # Docker 이미지 빌드
├── docker-compose.yml      # 로컬 개발 환경
├── requirements.txt        # Python 의존성
├── env.example            # 환경변수 예제
├── DEPLOYMENT_GUIDE.md    # 배포 가이드
└── S3_SETUP.md           # S3 설정 가이드
```

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 저장소 클론
git clone <repository-url>
cd mait-ai

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp env.example .env
# .env 파일을 열어 실제 값을 입력하세요
```

### 2. .env 파일 설정

```bash
# AWS S3 접근
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=ap-northeast-2

# OpenAI API
OPENAI_API_KEY=sk-proj-...

# CORS 설정
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

### 3. 서버 실행

#### 방법 1: 직접 실행
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 방법 2: Docker Compose (권장)
```bash
docker-compose up -d
```

### 4. API 테스트

```bash
# 헬스 체크
curl http://localhost:8000/health

# S3 PDF 읽기 (Python 스크립트)
python example_s3_pdf_with_auth.py
```

API 문서: http://localhost:8000/docs

## 📚 사용 예제

### S3에서 PDF 읽기

```python
from app.utils.utils import read_pdf_from_s3

# S3 URL에서 PDF 텍스트 추출
s3_url = "https://mait-ai.s3.ap-northeast-2.amazonaws.com/document.pdf"
text = read_pdf_from_s3(s3_url)
print(text)
```

### URL에서 PDF 읽기 (비동기)

```python
import asyncio
from app.utils.utils import read_pdf_from_url

async def main():
    url = "https://example.com/document.pdf"
    text = await read_pdf_from_url(url)
    print(text)

asyncio.run(main())
```

### 로컬 PDF 파일 읽기

```python
from app.utils.utils import read_pdf_file

text = read_pdf_file("path/to/document.pdf")
print(text)
```

## 🐳 Docker 사용

### 로컬 개발

```bash
# 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 서비스 중지
docker-compose down
```

### 프로덕션 빌드

```bash
# 이미지 빌드
docker build -t mait-ai:latest .

# 컨테이너 실행
docker run -d \
  -p 8000:8000 \
  -e AWS_ACCESS_KEY_ID="your_key" \
  -e AWS_SECRET_ACCESS_KEY="your_secret" \
  -e OPENAI_API_KEY="your_openai_key" \
  --name mait-ai \
  mait-ai:latest
```

## 🚢 배포

### GitHub Actions 자동 배포

`develop` 브랜치에 푸시하면 자동으로 배포됩니다.

#### 1. GitHub Secrets 설정

Repository Settings → Secrets → Actions에서 다음 시크릿을 등록:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `OPENAI_API_KEY`
- `ALLOWED_ORIGINS`

#### 2. 배포 워크플로우

- **AWS ECS 배포**: `.github/workflows/deploy-develop.yml`
- **Docker Hub 배포**: `.github/workflows/deploy-docker-hub.yml.example`

자세한 내용은 [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)를 참고하세요.

## 📖 문서

- [배포 가이드](DEPLOYMENT_GUIDE.md) - CI/CD 설정 및 배포 방법
- [S3 설정 가이드](S3_SETUP.md) - AWS S3 접근 설정

## 🛠 개발

### 테스트 실행

```bash
pytest tests/
```

### 코드 포맷팅

```bash
black app/
isort app/
```

### 타입 체크

```bash
mypy app/
```

## 📋 API 엔드포인트

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | `/health` | 헬스 체크 |
| POST | `/api/ai/...` | AI 관련 API |
| ... | ... | ... |

자세한 API 문서는 `/docs` 엔드포인트에서 확인하세요.

## 🤝 기여

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

## 📧 문의

프로젝트 관련 문의사항은 이슈를 등록해주세요.
