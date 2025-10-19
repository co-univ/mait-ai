from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.schemas import GenerateRequest, GenerateResponse, ParseFileResponse, ParseURLRequest
from app.services.openai_service import generate_text
from app.services.file_parser import parse_markdown, parse_pdf
from app.utils.utils import download_file_from_url

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

@router.post("/parse-url", response_model=ParseFileResponse)
async def parse_url_endpoint(req: ParseURLRequest):
    try:
        raw_content = await download_file_from_url(str(req.url))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"파일을 다운로드할 수 없습니다: {e}")

    url_path = req.url.path.lower()

    if url_path.endswith(".md"):
        text = await parse_markdown(raw_content)
    elif url_path.endswith(".pdf"):
        text = parse_pdf(raw_content)
    else:
        raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다. URL은 .md 또는 .pdf로 끝나야 합니다.")
    
    return ParseFileResponse(text=text)
