import io
import markdown as md
from pdfminer.high_level import extract_text
from typing import Literal

async def parse_markdown(raw_bytes: bytes) -> str:
    text_md = raw_bytes.decode("utf-8")
    html = md.markdown(text_md)
    import re
    plain = re.sub("<[^>]+>", "", html)
    return plain

def parse_pdf(raw_bytes: bytes) -> str:
    with io.BytesIO(raw_bytes) as fp:
        text = extract_text(fp)
    return text or ""

async def parse_raw_by_extension(raw_bytes: bytes, ext: Literal[".md", ".pdf"]) -> str:
    if ext == ".md":
        return await parse_markdown(raw_bytes)
    if ext == ".pdf":
        return parse_pdf(raw_bytes)
    raise ValueError("지원하지 않는 파일 형식입니다. (.md 또는 .pdf)")
