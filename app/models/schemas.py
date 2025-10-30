from pydantic import BaseModel, HttpUrl, Field

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
    instruction: str = Field(
        ..., description="문제 제작에 대한 보충 설명 (유저 요구사항)"
    )
    counts: dict[str, int] = Field(
        ..., description="문항 유형별 개수. 키는 MULTIPLE | SHORT | FILL_BLANK | ORDERING"
    )
    
