from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.schemas import GenerateRequest, GenerateResponse, ParseFileResponse
from app.services.openai_service import generate_text
from app.services.file_parser import parse_markdown, parse_pdf

router = APIRouter()

@router.post("/generate", response_model=GenerateResponse)
async def generate_endpoint(req: GenerateRequest):
    result = await generate_text(req.prompt)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return GenerateResponse(content=result["content"])

@router.post("/parse-file", response_model=ParseFileResponse)
async def parse_file_endpoint(file: UploadFile = File(...)):
    filename = file.filename.lower()
    raw = await file.read()

    if filename.endswith(".md"):
        text = await parse_markdown(raw)
    elif filename.endswith(".pdf"):
        text = parse_pdf(raw)
    else:
        raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다. (.md 또는 .pdf)")
    return ParseFileResponse(text=text)
