from pydantic import BaseModel, HttpUrl, Field
from typing import List, Union, Literal
from typing_extensions import Annotated


# ----- Question item schemas -----

class ChoiceItem(BaseModel):
    number: int
    content: str
    isCorrect: bool


class ShortAnswerItem(BaseModel):
    number: int
    answer: str
    main: bool


class OrderingOption(BaseModel):
    originOrder: int
    content: str
    answerOrder: int


class QuestionBase(BaseModel):
    questionType: Literal["MULTIPLE", "SHORT", "FILL_BLANK", "ORDERING"]
    content: str
    explanation: str


class MultipleQuestion(QuestionBase):
    questionType: Literal["MULTIPLE"]
    answerCount: int
    choices: List[ChoiceItem]


class ShortQuestion(QuestionBase):
    questionType: Literal["SHORT"]
    answerCount: int
    answers: List[ShortAnswerItem]


class FillBlankQuestion(QuestionBase):
    questionType: Literal["FILL_BLANK"]
    answers: List[ShortAnswerItem]


class OrderingQuestion(QuestionBase):
    questionType: Literal["ORDERING"]
    options: List[OrderingOption]


QuestionItem = Annotated[
    Union[MultipleQuestion, ShortQuestion, FillBlankQuestion, OrderingQuestion],
    Field(discriminator="questionType"),
]

class GenerateResponse(BaseModel):
    content: list[QuestionItem]

class ParseFileResponse(BaseModel):
    text: str

class ParseURLRequest(BaseModel):
    url: HttpUrl

class GenerateFromURLRequest(BaseModel):
    subject: str
    difficulty: str
    urls: List[HttpUrl]
    instruction: str = Field(
        ..., description="문제 제작에 대한 보충 설명 (유저 요구사항)"
    )
    counts: dict[str, int] = Field(
        ..., description="문항 유형별 개수. 키는 MULTIPLE | SHORT | FILL_BLANK | ORDERING"
    )
    
