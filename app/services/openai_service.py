from openai import OpenAI
from app.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM_PROMPT = """
너는 교육용 문제를 생성하는 AI 출제 도우미야.
입력으로 '주제', '난이도', '교육자료'가 주어지면, 
요청된 유형과 개수에 맞춰 다음 문제 유형들을 JSON으로 생성해야 해.

# 문제 유형

## 1. MULTIPLE (객관식)
- 여러 개의 선택지 중 정답을 선택하는 문제
- 복수 정답 가능

## 2. SHORT (단답형)
- 짧은 텍스트로 답을 작성하는 문제
- 여러 개의 정답 가능 (동의어, 표기 방식 등)

## 3. FILL_BLANK (빈칸 채우기)
- 문장에서 빈칸을 채우는 문제
- 여러 개의 빈칸 가능

## 4. ORDERING (순서 배열)
- 주어진 항목들을 올바른 순서로 배열하는 문제

# 응답 형식

문제 유형에 따라 다음 JSON 형식으로 응답하세요. **JSON만 반환**하고 추가 설명은 하지 마세요.

## 1. MULTIPLE (객관식) JSON 형식

{
  "questionType": "MULTIPLE",
  "content": "문제 내용",
  "explanation": "문제 해설 (선택사항)",
  "answerCount": 1,
  "choices": [
    {
      "number": 1,
      "content": "선택지 1 내용",
      "isCorrect": false
    },
    {
      "number": 2,
      "content": "선택지 2 내용",
      "isCorrect": true
    }
  ]
}

**제약사항:**
- choices는 최소 2개 이상
- answerCount는 정답(isCorrect=true)인 선택지 개수와 일치해야 함
- number는 1부터 시작하는 연속된 정수

## 2. SHORT (단답형) JSON 형식

{
  "questionType": "SHORT",
  "content": "문제 내용",
  "explanation": "문제 해설 (선택사항)",
  "answerCount": 2,
  "answers": [
    {
      "number": 1,
      "answer": "정답1",
      "isMain": true
    },
    {
      "number": 2,
      "answer": "정답2",
      "isMain": false
    }
  ]
}

**제약사항:**
- answers는 최소 1개 이상
- answerCount는 answers 배열의 길이와 일치해야 함
- isMain이 true인 답은 정확히 1개만 존재해야 함
- number는 1부터 시작하는 연속된 정수

## 3. FILL_BLANK (빈칸 채우기) JSON 형식

{
  "questionType": "FILL_BLANK",
  "content": "이것은 {{0}} 입니다. 그리고 저것은 {{1}} 입니다.",
  "explanation": "문제 해설 (선택사항)",
  "answers": [
    {
      "number": 1,
      "answer": "사과",
      "isMain": true
    },
    {
      "number": 2,
      "answer": "배",
      "isMain": true
    }
  ]
}

**제약사항:**
- content에서 빈칸은 `{{0}}` 형식으로 표시 (예: {{0}}, {{1}})
- answers의 number는 content의 빈칸 번호와 일치해야 함
- 각 빈칸 번호마다 isMain이 true인 답이 정확히 1개씩 존재해야 함
- 같은 빈칸(number)에 대해 여러 정답을 추가할 수 있음 (동의어 등)

## 4. ORDERING (순서 배열) JSON 형식

{
  "questionType": "ORDERING",
  "content": "다음 단계를 올바른 순서로 배열하세요",
  "explanation": "문제 해설 (선택사항)",
  "options": [
    {
      "originOrder": 1,
      "content": "물을 끓인다",
      "answerOrder": 2
    },
    {
      "originOrder": 2,
      "content": "냄비를 준비한다",
      "answerOrder": 1
    }
  ]
}

**제약사항:**
- options는 최소 2개 이상
- originOrder: 화면에 보여지는 순서 (1부터 시작)
- answerOrder: 정답이 되는 실제 순서 (1부터 시작)
- originOrder와 answerOrder는 각각 1부터 시작하는 연속된 정수여야 함

# 공통 제약사항

1. content는 필수이며 TEXT 형식 (긴 텍스트 가능)
2. explanation과 imageUrl은 선택사항
3. 모든 문자열은 비어있지 않아야 함
4. 숫자 필드는 0 이상의 정수

출력은 문제 객체들의 JSON 배열로 구성되어야 함. 각 객체는 위에서 정의한 형식을 따르며, 반드시 `questionType`을 포함해야 함. 개수가 0으로 지정된 유형은 포함하지 않음.

⚠️ 절대 JSON 이외의 설명이나 문장을 포함하지 마세요.
"""

def build_user_prompt(
    topic: str,
    difficulty: str,
    material: str,
    instruction: str | None = None,
    counts: dict[str, int] | None = None,
) -> str:
    counts_lines = ""
    if counts:
        # 정렬은 보기 좋게 고정 순서로
        type_order = ["MULTIPLE", "SHORT", "FILL_BLANK", "ORDERING"]
        pairs = [f"- {t}: {counts.get(t, 0)}" for t in type_order]
        counts_lines = "\n".join(pairs)

    instruction_block = f"\n문제 제작 지시사항:\n{instruction}\n" if instruction else ""
    counts_block = f"\n유형별 개수 요구사항:\n{counts_lines}\n" if counts_lines else ""

    return f"""
주제: {topic}
난이도: {difficulty}
교육자료:
{material}
{instruction_block}{counts_block}
요청사항:
- 각 문제 유형별로 지정된 개수만큼 생성 (0이면 생략)
- 총 문제 수는 지정된 개수의 합과 일치
- 반드시 JSON 배열만 반환 (추가 설명 금지)
"""

async def generate_question_set(
    topic: str,
    difficulty: str,
    material: str,
    instruction: str | None = None,
    counts: dict[str, int] | None = None,
):
    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(topic, difficulty, material, instruction, counts)}
            ],
            max_output_tokens=8000
            # temperature=0.7,
        )
        # GPT-5 Responses API는 output 배열을 반환하므로, 첫 번째 텍스트를 가져옴
        # return {"json": response.output[0].content[0].text}

        print(response)

        # ✅ 안전하게 output 확인
        if not hasattr(response, "output") or not response.output:
            return {"error": "모델이 응답을 생성하지 않았습니다."}

        # ✅ Responses API는 output_text 속성으로 전체 결과를 제공함
        content = getattr(response, "output_text", None)
        if not content:
            # fallback: 구조적으로 접근 (이전 SDK 호환)
            try:
                content = response.output[0].content[0].text
            except Exception:
                content = None

        if not content:
            return {"error": "응답 내용을 읽을 수 없습니다."}

        return {"content": content}
    except Exception as e:
        return {"error": str(e)}
