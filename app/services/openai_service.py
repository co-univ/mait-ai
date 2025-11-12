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
  "explanation": "문제 해설 (선택사항, 최대 00자)",
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
    },
    {
      "number": 3,
      "content": "선택지 3 내용",
      "isCorrect": false
    },
    {
      "number": 4,
      "content": "선택지 4 내용",
      "isCorrect": false
    }
  ]
}

**규칙/제약사항(유형 1 - 객관식):**
- 기본 선택지 개수는 4개, 최대 8개까지 허용
- 선택지 삭제 가능하나 최소 2개는 유지해야 함(2개일 땐 삭제 불가)
- choices는 항상 2개 이상
- answerCount는 `isCorrect=true`인 선택지 개수와 일치
- number는 1부터 시작하는 연속된 정수
- 동일 의미의 답안 묶음은 같은 `number`를 사용
- 각 `number` 묶음마다 `isMain=true`는 정확히 1개, 나머지는 같은 `number`로 `isMain=false`
- `answerCount`는 서로 다른 `number`(=메인 답안) 개수와 정확히 일치
- 정답 영역 표시는 선택지의 번호 기반(체크된 선택지의 number가 노출됨)

## 2. SHORT (단답형) JSON 형식

{
  "questionType": "SHORT",
  "content": "문제 내용",
  "explanation": "문제 해설 (선택사항, 최대 00자)",
  "answerCount": 1,
  "answers": [
    {
      "number": 1,
      "answer": "정답",
      "isMain": true
    },
    {
      "number": 1, 
      "answer": "정답의 인정답안(동의어/표기 변형)",
      "isMain": false
    }
  ]
}

**규칙/제약사항(유형 2 - 주관식):**
- 기본 정답 개수는 1개(메인 답안 기준), 최대 5개까지 가능
- answers는 최소 1개 이상
- 메인 답안은 `isMain=true`로 표시하며 최소 1개, 최대 5개
- 인정답안은 `isMain=false`로 추가(동의어/표기 변형), 각 메인 답안별 최대 5개까지 허용
- number가 같은 답안 사이에 main=true는 무조건 1개여야함.
- 답안 삭제는 가능하나 최소 1개는 유지(1개일 때 삭제 불가)
- answerCount는 1~5 사이 정수
  - 토글 off(조절 불가)일 때: 기본값은 메인 답안 개수와 동일
  - 토글 on(조절 가능)일 때: 1~5 범위에서 조절 가능
- 정답 영역에는 메인 답안만 노출(인정답안 제외)
- number는 1부터 시작하는 연속된 정수

## 3. FILL_BLANK (빈칸 채우기) JSON 형식

{
  "questionType": "FILL_BLANK",
  "content": "이것은 {{0}} 입니다. 그리고 저것은 {{1}} 입니다.",
  "explanation": "문제 해설 (선택사항, 최대 00자)",
  "answers": [
    {
      "number": 1,
      "answer": "사과",
      "isMain": true
    },
    {
      "number": 1,
      "answer": "애플", 
      "isMain": false
    },
    {
      "number": 2,
      "answer": "배",
      "isMain": true
    }
  ]
}

**규칙/제약사항(유형 3 - 빈칸 넣기):**
- 질문 작성 중 '빈칸 추가' 시 `{{i}}` 형태의 새 빈칸 생성(i는 0부터 시작)
- content의 빈칸 번호는 좌→우, 상→하 순으로 증가하며 앞쪽 빈칸이 앞 번호
- answers의 `number`는 content의 빈칸 번호와 일치해야 함
- 각 빈칸 번호마다 메인 답안(`isMain=true`)은 정확히 1개
- 같은 빈칸 번호에 대해 인정답안(`isMain=false`)을 여러 개 추가 가능(최대 5개)
- 빈칸 삭제: 텍스트에서 백스페이스 1회 선택, 2회 삭제 또는 Minus 클릭 시 삭제
- 정답 영역 표기 예시: "정답 (1) A, (2) B"

## 4. ORDERING (순서 배열) JSON 형식

{
  "questionType": "ORDERING",
  "content": "다음 단계를 올바른 순서로 배열하세요",
  "explanation": "문제 해설 (선택사항, 최대 00자)",
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
    },
    {
      "originOrder": 3,
      "content": "면을 넣는다",
      "answerOrder": 3
    }
  ]
}

**규칙/제약사항(유형 4 - 순서):**
- 기본 답안(보기) 개수 3개, 최대 6개까지 가능
- 보기 필드와 정답 필드는 구분되며, 보기는 화면에 알파벳 표기(A,B,C,...)가 자동 부여됨(알파벳 자체는 모델이 생성하지 않음)
- 정답 입력은 알파벳이 아닌 `answerOrder` 수치로 표현(1부터 시작)
- `originOrder`: 화면 표기 순서(1부터 시작, 연속 정수)
- `answerOrder`: 정답 순서(1부터 시작, 연속 정수)
- 정답 영역 노출 형식: "A,B,C,D" (UI에서 알파벳 매핑)

# 공통 제약사항

1. content는 필수이며 TEXT 형식 (긴 텍스트 가능)
2. explanation은 선택사항이며 최대 00자
3. 모든 문자열은 비어있지 않아야 함
4. 숫자 필드는 0 이상의 정수
5. 각 유형의 기본/최대 개수 규칙을 따를 것(객관식 4 기본/최대 8, 주관식 메인 1 기본/최대 5, 빈칸은 content의 {{i}} 수에 따름, 순서 3 기본/최대 6)

출력은 문제 객체들의 JSON 배열로 구성되어야 함. 각 객체는 위에서 정의한 형식을 따르며, 반드시 `questionType`을 포함해야 함. 개수가 0으로 지정된 유형은 포함하지 않음.

# 최종 검증 체크리스트(반드시 자체 점검 후 JSON만 반환)
- 전체 응답은 유효한 JSON 배열이어야 함(파싱 가능)
- 모든 객체는 `questionType` ∈ {MULTIPLE, SHORT, FILL_BLANK, ORDERING}
- 모든 문자열 필드는 비어있지 않음, 설명은 최대 00자 이하

[MULTIPLE]
- choices 길이: 2~8
- `answerCount` == `isCorrect=true` 개수
- `number`는 1부터 시작하는 연속 정수, 중복 없음

[SHORT]
- answers 길이 ≥ 1
- `number`는 1부터 시작하는 연속 정수
- 동일 `number` 묶음 내 `isMain=true`는 정확히 1개
- 인정답안은 메인과 동일 `number`로 `isMain=false`
- `answerCount` == 서로 다른 `number`(=메인 답안) 개수, 1~5 범위
- 정답 영역에는 `isMain=true`인 항목만 해당 내용이 노출됨(인정답안 제외)

[FILL_BLANK]
- content의 `{{i}}` 인덱스와 answers의 `number`가 일치
- 각 빈칸 번호마다 `isMain=true` 정확히 1개, 인정답안은 동일 번호 `isMain=false`

[ORDERING]
- options 길이: 2 이상(권장 기본 3, 최대 6)
- `originOrder`는 1..N 연속, 중복 없음
- `answerOrder`는 1..N 연속, 중복 없음

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
