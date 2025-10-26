from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.schemas import GenerateRequest, GenerateResponse, ParseFileResponse, ParseURLRequest, GenerateFromURLRequest
from app.services.openai_service import generate_question_set
from app.services.file_parser import parse_markdown, parse_pdf
from app.utils.utils import download_file_from_url, parse_text_from_url

router = APIRouter()

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
        text = await parse_text_from_url(str(req.url))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"파일을 다운로드할 수 없습니다: {e}")
    return ParseFileResponse(text=text)

@router.post("/generate", response_model=GenerateResponse)
async def generate_from_url_endpoint(req: GenerateFromURLRequest):
    try:
        text = await parse_text_from_url(str(req.url))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"파일을 다운로드할 수 없습니다: {e}")

    result = await generate_question_set(req.title, req.difficulty, text)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return GenerateResponse(content=result["content"])
