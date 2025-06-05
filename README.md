# ai-server

## 프로젝트 개요
- FastAPI 기반 AI 서버
- OpenAI API 호출
- Markdown/PDF → 텍스트 변환
- Java Spring 백엔드가 REST API 형태로 호출

## 구조
\`\`\`
ai-server/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   └── router.py
│   ├── services/
│   │   ├── openai_service.py
│   │   └── file_parser.py
│   ├── models/
│   │   └── schemas.py
│   └── utils/
│       └── utils.py
├── tests/
├── Dockerfile
├── requirements.txt
├── .env
└── README.md
\`\`\`

## 빠른 시작
1. \`pip install -r requirements.txt\`  
2. \`.env\` 파일에 OpenAI API 키, ALLOWED_ORIGINS 등 설정  
3. \`uvicorn app.main:app --reload --host 0.0.0.0 --port 8000\`  
4. Java 백엔드에서 \`http://<서버주소>:8000/api/ai/... \` 형태로 호출
