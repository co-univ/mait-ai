import io
import markdown as md
from pdfminer.high_level import extract_text

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
