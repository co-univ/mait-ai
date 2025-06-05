from pydantic import BaseModel

class GenerateRequest(BaseModel):
    prompt: str

class GenerateResponse(BaseModel):
    content: str

class ParseFileResponse(BaseModel):
    text: str
