from fastapi import APIRouter, UploadFile, File, HTTPException, Request
import json
import time
from app.models.schemas import GenerateResponse, ParseFileResponse, ParseURLRequest, GenerateFromURLRequest
from app.services.openai_service import generate_question_set
from app.services.file_parser import parse_markdown, parse_pdf
from app.utils.utils import download_file_from_url, parse_text_from_url, get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.post("/parse-file", response_model=ParseFileResponse)
async def parse_file_endpoint(file: UploadFile = File(...)):
    logger.info(f"[PARSE_FILE_START] filename={file.filename}")
    try:
        filename = file.filename.lower()
        raw = await file.read()

        if filename.endswith(".md"):
            text = await parse_markdown(raw)
            logger.info(f"[PARSE_FILE_SUCCESS] filename={file.filename} | type=markdown | text_length={len(text)}")
        elif filename.endswith(".pdf"):
            text = parse_pdf(raw)
            logger.info(f"[PARSE_FILE_SUCCESS] filename={file.filename} | type=pdf | text_length={len(text)}")
        else:
            logger.error(f"[PARSE_FILE_ERROR] filename={file.filename} | error=지원하지 않는 파일 형식")
            raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다. (.md 또는 .pdf)")
        return ParseFileResponse(text=text)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PARSE_FILE_ERROR] filename={file.filename} | error={str(e)}")
        raise HTTPException(status_code=500, detail=f"파일 파싱 중 오류가 발생했습니다: {str(e)}")

@router.post("/parse-url", response_model=ParseFileResponse)
async def parse_url_endpoint(req: ParseURLRequest):
    logger.info(f"[PARSE_URL_START] url={req.url}")
    try:
        text = await parse_text_from_url(str(req.url))
        logger.info(f"[PARSE_URL_SUCCESS] url={req.url} | text_length={len(text)}")
        return ParseFileResponse(text=text)
    except ValueError as e:
        logger.error(f"[PARSE_URL_ERROR] url={req.url} | error={str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[PARSE_URL_ERROR] url={req.url} | error={str(e)}")
        raise HTTPException(status_code=400, detail=f"파일을 다운로드할 수 없습니다: {e}")

@router.post("/generate", response_model=GenerateResponse)
async def generate_from_url_endpoint(req: GenerateFromURLRequest, request: Request) -> GenerateResponse:
    start_time = time.time()
    # request_id는 이제 로그에 자동으로 포함되므로 별도로 지정할 필요 없음
    # 하지만 필요시 request.state에서 가져올 수 있음
    request_id = getattr(request.state, "request_id", "unknown")
    
    # request_id는 자동으로 로그에 포함되므로 메시지에서 제거 가능
    logger.info(
        f"[REQUEST_START] title={req.title} | difficulty={req.difficulty} | "
        f"urls_count={len(req.urls)} | counts={req.counts} | "
        f"client_ip={request.client.host if request.client else 'unknown'}"
    )
    
    try:
        texts = []
        for u in req.urls:
            try:
                text_part = await parse_text_from_url(str(u))
                logger.debug(f"[URL_PARSED] url={u} | text_length={len(text_part)}")
            except Exception as e:
                logger.error(f"[URL_ERROR] url={u} | error={str(e)}")
                # URL 처리 실패 시에도 에러를 내지 않고 진행 (빈 텍스트로 처리되거나 다른 URL 내용만 사용)
                continue
            texts.append(text_part)
        text = "\n\n".join(texts)
        logger.info(f"[TEXT_PREPARED] total_text_length={len(text)}")
    except Exception as e:
        logger.error(f"[PREPARE_ERROR] error={str(e)}")
        # 텍스트 준비 중 에러가 나도, 빈 텍스트로 AI 생성 시도
        text = ""

    logger.info(f"[AI_GENERATION_START]")
    ai_start_time = time.time()
    
    result = await generate_question_set(
        req.title,
        req.difficulty,
        text,
        req.instruction,
        req.counts,
    )
    
    ai_duration = time.time() - ai_start_time
    logger.info(f"[AI_GENERATION_COMPLETE] duration={ai_duration:.2f}s")
    
    if "error" in result:
        logger.error(f"[AI_ERROR] error={result['error']}")
        raise HTTPException(status_code=500, detail=result["error"])
    
    content = result.get("content")
    if isinstance(content, str):
        try:
            content = json.loads(content)
            question_count = len(content) if isinstance(content, list) else 1
            logger.info(f"[RESPONSE_READY] question_count={question_count}")
        except json.JSONDecodeError:
            logger.error(f"[JSON_ERROR] content_preview={content[:100] if content else 'None'}")
            raise HTTPException(status_code=500, detail="생성된 콘텐츠가 올바른 JSON이 아닙니다.")
    
    total_duration = time.time() - start_time
    logger.info(
        f"[REQUEST_COMPLETE] total_duration={total_duration:.2f}s | ai_duration={ai_duration:.2f}s | success=True"
    )
    
    return GenerateResponse(content=content)
