# 공통 유틸 함수(로깅 설정, 예외 헬퍼 등)를 이곳에 작성하세요.
import httpx
import boto3
import logging
import sys
from contextvars import ContextVar
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, unquote
from app.services.file_parser import parse_pdf, parse_raw_by_extension

# MDC처럼 동작하는 context variable (Spring의 MDC와 유사)
request_id_context: ContextVar[str] = ContextVar("request_id", default="")


class RequestIDFormatter(logging.Formatter):
    """
    로그 포맷에 request_id를 자동으로 포함시키는 Formatter
    Spring의 MDC처럼 동작
    """
    
    def format(self, record: logging.LogRecord) -> str:
        # context에서 request_id 가져오기
        request_id = request_id_context.get("")
        
        # request_id가 있으면 로그 메시지에 포함
        if request_id:
            record.request_id = request_id
        else:
            record.request_id = "-"
        
        return super().format(record)


def setup_logging(log_level: str = "INFO", log_format: str = None):
    """
    애플리케이션 전역 로깅 설정
    
    Args:
        log_level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: 로그 포맷 문자열 (None이면 기본 포맷 사용)
    """
    if log_format is None:
        # request_id를 포함한 포맷
        log_format = "%(asctime)s - %(name)s - %(levelname)s - [request_id=%(request_id)s] - %(message)s"
    
    # Custom Formatter 사용
    formatter = RequestIDFormatter(log_format)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        handlers=[handler]
    )
    
    # uvicorn과 FastAPI의 로그 레벨도 조정
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)


def set_request_id(request_id: str):
    """
    현재 context에 request_id 설정 (MDC.put과 유사)
    
    Args:
        request_id: 설정할 request_id
    """
    request_id_context.set(request_id)


def get_request_id() -> str:
    """
    현재 context에서 request_id 가져오기 (MDC.get과 유사)
    
    Returns:
        현재 context의 request_id, 없으면 빈 문자열
    """
    return request_id_context.get("")

def get_logger(name: str) -> logging.Logger:
    """
    모듈별 logger 인스턴스 반환
    
    Args:
        name: 보통 __name__ 사용
        
    Returns:
        Logger 인스턴스
    """
    return logging.getLogger(name)

async def download_file_from_url(url: str) -> bytes:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()  # 응답 상태 코드가 200이 아니면 예외 발생
        return response.content
    
async def parse_text_from_url(url: str) -> str:
    """
    URL 확장자(.md/.pdf)에 따라 다운로드 후 텍스트 파싱
    """
    content = await download_file_from_url(url)
    from urllib.parse import urlparse
    ext = Path(urlparse(url).path).suffix.lower()
    if ext not in [".md", ".pdf"]:
        raise ValueError("지원하지 않는 파일 형식입니다. (.md 또는 .pdf)")
    return await parse_raw_by_extension(content, ext) 

async def read_pdf_from_url(url: str) -> str:
    """
    URL(예: S3)에서 PDF 파일을 다운로드하여 텍스트 내용을 추출합니다.
    
    Args:
        url: PDF 파일의 URL (예: S3 URL, HTTP/HTTPS URL 등)
    
    Returns:
        추출된 텍스트 내용
    
    Raises:
        httpx.HTTPError: 다운로드 중 HTTP 오류 발생 시
        Exception: PDF 파싱 중 오류 발생 시
    
    Example:
        >>> text = await read_pdf_from_url("https://example.com/sample.pdf")
        >>> print(text)
    """
    # URL에서 PDF 다운로드
    pdf_bytes = await download_file_from_url(url)
    
    # PDF에서 텍스트 추출
    text = parse_pdf(pdf_bytes)
    
    return text

def read_pdf_from_s3(s3_url: str, aws_access_key_id: Optional[str] = None, 
                     aws_secret_access_key: Optional[str] = None,
                     region_name: str = 'ap-northeast-2') -> str:
    """
    AWS S3에서 PDF 파일을 다운로드하여 텍스트 내용을 추출합니다.
    
    Args:
        s3_url: S3 URL (예: https://bucket-name.s3.region.amazonaws.com/path/to/file.pdf 
                또는 s3://bucket-name/path/to/file.pdf)
        aws_access_key_id: AWS Access Key ID (None이면 환경변수나 AWS config 사용)
        aws_secret_access_key: AWS Secret Access Key (None이면 환경변수나 AWS config 사용)
        region_name: AWS 리전 (기본값: ap-northeast-2)
    
    Returns:
        추출된 텍스트 내용
    
    Raises:
        Exception: S3 다운로드 또는 PDF 파싱 중 오류 발생 시
    
    Example:
        >>> text = read_pdf_from_s3("https://my-bucket.s3.ap-northeast-2.amazonaws.com/document.pdf")
        >>> print(text)
    """
    # S3 URL 파싱
    parsed = urlparse(s3_url)
    
    if parsed.scheme == 's3':
        # s3://bucket-name/path/to/file.pdf 형식
        bucket_name = parsed.netloc
        object_key = parsed.path.lstrip('/')
    else:
        # https://bucket-name.s3.region.amazonaws.com/path/to/file.pdf 형식
        # 또는 https://s3.region.amazonaws.com/bucket-name/path/to/file.pdf 형식
        if '.s3.' in parsed.netloc or '.s3-' in parsed.netloc:
            # bucket-name.s3.region.amazonaws.com 형식
            bucket_name = parsed.netloc.split('.s3')[0]
            object_key = parsed.path.lstrip('/')
        else:
            raise ValueError(f"지원하지 않는 S3 URL 형식입니다: {s3_url}")
    
    # URL 디코딩 (한글 파일명 등 처리)
    object_key = unquote(object_key)
    
    # S3 클라이언트 생성
    if aws_access_key_id and aws_secret_access_key:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
    else:
        # 환경변수나 AWS config에서 자동으로 인증 정보 가져오기
        s3_client = boto3.client('s3', region_name=region_name)
    
    # S3에서 파일 다운로드
    response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
    pdf_bytes = response['Body'].read()
    
    # PDF에서 텍스트 추출
    text = parse_pdf(pdf_bytes)
    
    return text

def read_pdf_file(file_path: str) -> str:
    """
    로컬 PDF 파일을 읽어서 텍스트 내용을 추출합니다.
    
    Args:
        file_path: PDF 파일 경로 (상대 경로 또는 절대 경로)
    
    Returns:
        추출된 텍스트 내용
    
    Raises:
        FileNotFoundError: 파일이 존재하지 않는 경우
        Exception: PDF 파싱 중 오류 발생 시
    
    Example:
        >>> text = read_pdf_file("documents/sample.pdf")
        >>> print(text)
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
    
    if not path.suffix.lower() == '.pdf':
        raise ValueError(f"PDF 파일이 아닙니다: {file_path}")
    
    with open(path, 'rb') as f:
        raw_bytes = f.read()
    
    return parse_pdf(raw_bytes)
