from pydantic import BaseModel, HttpUrl

class GenerateRequest(BaseModel):
    title: str
    difficulty: str
    material: str

class GenerateResponse(BaseModel):
    content: str

class ParseFileResponse(BaseModel):
    text: str

class ParseURLRequest(BaseModel):
    url: HttpUrl

class GenerateFromURLRequest(BaseModel):
    title: str
    difficulty: str
    url: HttpUrl
