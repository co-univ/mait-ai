# 공통 유틸 함수(로깅 설정, 예외 헬퍼 등)를 이곳에 작성하세요.
import httpx
from pathlib import Path
from app.services.file_parser import parse_pdf

async def download_file_from_url(url: str) -> bytes:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()  # 응답 상태 코드가 200이 아니면 예외 발생
        return response.content

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
