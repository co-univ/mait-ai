from pydantic import BaseModel, HttpUrl

class GenerateRequest(BaseModel):
    prompt: str

class GenerateResponse(BaseModel):
    content: str

class ParseFileResponse(BaseModel):
    text: str

class ParseURLRequest(BaseModel):
    url: HttpUrl
