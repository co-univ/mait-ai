from openai import OpenAI
from app.config import settings
from app.utils.utils import get_logger
import json
import re

client = OpenAI(api_key=settings.OPENAI_API_KEY)
logger = get_logger(__name__)

SYSTEM_PROMPT = """
너는 교육용 문제를 생성하는 AI 출제 도우미야.
입력으로 '주제', '난이도', '교육자료'가 주어지면, 
요청된 유형과 개수에 맞춰 다음 문제 유형들을 JSON으로 생성해야 해.

절대 문제 생성 규칙을 어기면 안돼

## 생성 절차(필수 수행)
1) 초안 생성
2) 구조 검증
   - JSON 파싱 가능 여부
   - 필수 필드 존재 여부
3) 규칙 정합성 보정
  생성된 문제를 유형별로 아래 규칙에 기반해 검증하고 보정해
   - SHORT: `number`별로 `main=true` 정확히 1개 보장(없으면 첫 항목을 true, 2개 이상이면 첫 항목만 true)
   - FILL_BLANK: content의 모든 `{{i}}`에 대해 `number=i`의 `main=true` 정확히 1개 보장(없으면 첫 항목을 true, 2개 이상이면 첫 항목만 true)
   - MULTIPLE: `answerCount == isCorrect=true 개수`
   - ORDERING: originOrder/answerOrder의 1..N 연속성 보장
4) 최종 검증 체크리스트 통과 후 JSON만 반환

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

**규칙/제약사항(유형 1 - 객관식):**
- 기본 선택지 개수는 4개, 최대 8개까지 허용
- 선택지 삭제 가능하나 최소 2개는 유지해야 함(2개일 땐 삭제 불가)
- choices는 항상 2개 이상
- answerCount는 `isCorrect=true`인 선택지 개수와 일치
- number는 1부터 시작하는 연속된 정수
- 정답 영역 표시는 선택지의 번호 기반(체크된 선택지의 number가 노출됨)

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

## 2. SHORT (단답형) JSON 형식

**규칙/제약사항(유형 2 - 주관식):**
- 기본 정답 개수는 1개(메인 답안 기준), 최대 5개까지 가능
- answers는 최소 1개 이상
- 메인 답안은 `main=true`로 표시하며 최소 1개, 최대 5개
- 인정답안은 `main=false`로 추가(동의어/표기 변형), 각 메인 답안별 최대 5개까지 허용
- 동일 의미의 답안 묶음은 같은 `number`를 사용
- number가 같은 답안 묶음 내에서 `main=true`는 정확히 1개여야 함
- 각 `number` 그룹에서 첫 번째 답안은 기본값으로 `main=true`, 나머지는 기본 `false`로 생성
- 답안 삭제는 가능하나 최소 1개는 유지(1개일 때 삭제 불가)
- answerCount는 1~5 사이 정수
- 정답 영역에는 메인 답안만 노출(인정답안 제외)
- number는 1부터 시작하는 연속된 정수
  - 금지: 모든 answers가 `main=false`인 상태
    - 보정: 어떤 `number` 묶음에서든 `main=true`가 없으면, 해당 묶음의 첫 항목을 `main=true`로 변경
    - 보정: 같은 `number`에서 `main=true`가 2개 이상이면 첫 항목만 `true`로 두고 나머지는 `false`로 변경

{
  "questionType": "SHORT",
  "content": "문제 내용",
  "explanation": "문제 해설 (선택사항, 최대 00자)",
  "answerCount": 1,
  "answers": [
    {
      "number": 1,
      "answer": "정답",
      "main": true
    },
    {
      "number": 1, 
      "answer": "정답의 인정답안(동의어/표기 변형)",
      "main": false
    }
  ]
}

## 3. FILL_BLANK (빈칸 채우기) JSON 형식

**규칙/제약사항(유형 3 - 빈칸 넣기):**
- 질문 작성 중 '빈칸 추가' 시 `{{i}}` 형태의 새 빈칸 생성(i는 1부터 시작)
- content의 빈칸 번호는 좌→우, 상→하 순으로 증가하며 앞쪽 빈칸이 앞 번호
- answers의 `number`는 content의 빈칸 번호와 일치해야 함
- 각 빈칸 번호마다 대표 답안(`main=true`)은 정확히 1개여야함
- 각 빈칸 번호 그룹에서 첫 번째 답안은 기본값으로 `main=true`, 나머지는 기본 `false`로 생성
- 같은 빈칸 번호에 대해 인정답안(`main=false`)을 여러 개 추가 가능(최대 5개)
- 빈칸 삭제: 텍스트에서 백스페이스 1회 선택, 2회 삭제 또는 Minus 클릭 시 삭제
- 정답 영역 표기 예시: "정답 (1) A, (2) B"
  - 금지: 어떤 빈칸 번호에서도 `main=true`가 0개인 상태
    - 보정: 해당 빈칸 번호에서 `main=true`가 없으면 첫 항목을 `main=true`로 변경
    - 보정: 해당 번호에서 `main=true`가 2개 이상이면 첫 항목만 `true`로 두고 나머지는 `false`로 변경

{
  "questionType": "FILL_BLANK",
  "content": "이것은 {{1}} 입니다. 그리고 저것은 {{2}} 입니다.",
  "explanation": "문제 해설 (선택사항, 최대 00자)",
  "answers": [
    {
      "number": 1,
      "answer": "사과",
      "main": true
    },
    {
      "number": 1,
      "answer": "애플", 
      "main": false
    },
    {
      "number": 2,
      "answer": "배",
      "main": true
    }
  ]
}


## 4. ORDERING (순서 배열) JSON 형식

**규칙/제약사항(유형 4 - 순서):**
- 기본 답안(보기) 개수 3개, 최대 6개까지 가능
- 보기 필드와 정답 필드는 구분되며, 보기는 화면에 알파벳 표기(A,B,C,...)가 자동 부여됨(알파벳 자체는 모델이 생성하지 않음)
- 정답 입력은 알파벳이 아닌 `answerOrder` 수치로 표현(1부터 시작)
- `originOrder`: 화면 표기 순서(1부터 시작, 연속 정수)
- `answerOrder`: 정답 순서(1부터 시작, 연속 정수)
- 정답 영역 노출 형식: "A,B,C,D" (UI에서 알파벳 매핑)

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
- 동일 `number` 묶음 내 `main=true`는 정확히 1개
- 인정답안은 메인과 동일 `number`로 `main=false`
- `answerCount` == 서로 다른 `number`(=메인 답안) 개수, 1~5 범위
- 정답 영역에는 `main=true`인 항목만 해당 내용이 노출됨(인정답안 제외)
  - 금지: 어떤 `number`에서도 `main=true`가 0개인 상태

[FILL_BLANK]
- content의 `{{i}}` 인덱스(i는 1부터 시작)와 answers의 `number`가 일치
- 각 빈칸 번호마다 `main=true` 정확히 1개, 인정답안은 동일 번호 `main=false`
  - 금지: 어떤 빈칸 번호에서도 `main=true`가 0개인 상태

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
- 반드시 유형별 생성 규칙을 지킬 것
- 각 문제 유형별로 지정된 개수만큼 생성 (0이면 생략)
- 총 문제 수는 지정된 개수의 합과 일치
- 반드시 JSON 배열만 반환 (추가 설명 금지)
"""

def _ensure_single_main_per_group(answers: list[dict]) -> None:
    """
    같은 number 그룹 내에서 main이 정확히 1개가 되도록 보정.
    - 메인 없음: 첫 항목을 main=true로 설정
    - 메인 2개 이상: 첫 메인만 true, 나머지 false
    """
    if not answers:
        return
    from collections import defaultdict
    groups: dict[int, list[int]] = defaultdict(list)
    # number별로 인덱스 그룹화
    for idx, ans in enumerate(answers):
        num = ans.get("number")
        if isinstance(num, int):
            groups[num].append(idx)
    # 각 그룹별로 보정
    for num, indices in groups.items():
        if not indices:
            continue
        # 현재 main=true인 인덱스 찾기
        true_indices = [i for i in indices if bool(answers[i].get("main"))]
        if not true_indices:
            # 메인 없음: 첫 항목을 메인으로 설정
            keep_idx = indices[0]
            logger.debug(f"[SANITIZER] number={num} 그룹에 메인 없음 → 인덱스 {keep_idx}를 main=True로 설정")
            for i in indices:
                answers[i]["main"] = True if (i == keep_idx) else False
            # 보정 후 확인
            logger.debug(f"[SANITIZER] 보정 후 확인: {[(answers[j].get('answer', '')[:20], answers[j].get('main')) for j in indices]}")
        elif len(true_indices) > 1:
            # 메인 2개 이상: 첫 메인만 유지, 나머지 false
            keep_idx = true_indices[0]
            logger.debug(f"[SANITIZER] number={num} 그룹에 메인 {len(true_indices)}개 → 인덱스 {keep_idx}만 유지, 나머지 False")
            for i in indices:
                answers[i]["main"] = True if (i == keep_idx) else False
            # 보정 후 확인
            logger.debug(f"[SANITIZER] 보정 후 확인: {[(answers[j].get('answer', '')[:20], answers[j].get('main')) for j in indices]}")
        # 이미 정확히 1개면 수정 불필요

def _sanitize_questions(questions: list[dict]) -> list[dict]:
    """
    모델 출력 후 규칙 위반을 보정.
    - SHORT/FILL_BLANK: 각 number 그룹마다 main=true 정확히 1개 보장
    - MULTIPLE: answerCount를 isCorrect 개수로 동기화
    """
    if not questions:
        logger.warning("[SANITIZER] questions가 비어있음")
        return questions
    logger.debug(f"[SANITIZER] 총 {len(questions)}개 문제 처리 시작")
    for idx, q in enumerate(questions):
        if not isinstance(q, dict):
            logger.warning(f"[SANITIZER] 인덱스 {idx}: dict가 아님, 스킵")
            continue
        qtype = q.get("questionType", "").upper()
        logger.debug(f"[SANITIZER] 인덱스 {idx}: questionType={qtype}")
        # 타입이 명시된 경우
        if qtype == "SHORT":
            answers = q.get("answers")
            if isinstance(answers, list) and answers:
                logger.debug(f"[SANITIZER] SHORT 처리: {len(answers)}개 답안")
                _ensure_single_main_per_group(answers)
                # 메인 개수로 answerCount 동기화
                main_numbers = {a.get("number") for a in answers if bool(a.get("main"))}
                q["answerCount"] = max(1, len(main_numbers)) if main_numbers else 1
                logger.debug(f"[SANITIZER] SHORT 보정 완료: answerCount={q['answerCount']}")
            continue
        if qtype == "FILL_BLANK":
            answers = q.get("answers")
            if isinstance(answers, list) and answers:
                logger.debug(f"[SANITIZER] FILL_BLANK 처리: {len(answers)}개 답안")
                _ensure_single_main_per_group(answers)
                logger.debug(f"[SANITIZER] FILL_BLANK 보정 완료")
            continue
        if qtype == "MULTIPLE":
            choices = q.get("choices")
            if isinstance(choices, list) and choices:
                correct_count = sum(1 for c in choices if bool(c.get("isCorrect")))
                q["answerCount"] = max(0, correct_count)
            continue
        # 타입 누락 시 구조로 추론해서 보정
        if "choices" in q and isinstance(q.get("choices"), list):
            choices = q.get("choices")
            if choices:
                correct_count = sum(1 for c in choices if bool(c.get("isCorrect")))
                q["answerCount"] = max(0, correct_count)
            continue
        if "answers" in q and isinstance(q.get("answers"), list):
            answers = q.get("answers")
            if answers:
                _ensure_single_main_per_group(answers)
                # SHORT/FILL_BLANK 공통: 메인 개수로 answerCount 동기화(존재 시)
                main_numbers = {a.get("number") for a in answers if bool(a.get("main"))}
                if "answerCount" in q:
                    q["answerCount"] = max(1, len(main_numbers)) if main_numbers else 1
    return questions

def _extract_json_array(content: str) -> str | None:
    """
    응답 텍스트에서 JSON 배열만 안전하게 추출.
    - 코드펜스(`````, ```json) 제거
    - 첫 '['부터 매칭되는 ']'까지 슬라이스
    """
    if not isinstance(content, str):
        return None
    # 코드펜스 제거
    cleaned = re.sub(r"^```(?:json)?\\s*|\\s*```$", "", content.strip(), flags=re.IGNORECASE | re.MULTILINE)
    # 첫 '[' 위치 탐색
    start = cleaned.find("[")
    if start == -1:
        return None
    # 대괄호 매칭으로 끝 위치 탐색
    depth = 0
    for i in range(start, len(cleaned)):
        ch = cleaned[i]
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return cleaned[start : i + 1]
    return None

async def generate_question_set(
    topic: str,
    difficulty: str,
    material: str,
    instruction: str | None = None,
    counts: dict[str, int] | None = None,
):
    try:
        logger.info(f"[OPENAI_API_CALL] model=gpt-4.1-mini | topic={topic} | difficulty={difficulty} | material_length={len(material)}")
        
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(topic, difficulty, material, instruction, counts)}
            ],
            max_output_tokens=20000
            # temperature=0.7,
        )
        # return {"json": response.output[0].content[0].text}

        logger.debug(f"[OPENAI_RESPONSE] response_type={type(response).__name__}")

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
        # 생성 결과 파싱 및 규칙 보정
        try:
            parsed = json.loads(content)
        except Exception:
            # 코드펜스/텍스트 섞임 대비: JSON 배열만 추출하여 재시도
            extracted = _extract_json_array(content)
            if not extracted:
                return {"error": "모델 응답을 JSON으로 파싱할 수 없습니다."}
            try:
                parsed = json.loads(extracted)
            except Exception:
                return {"error": "모델 응답(JSON 추출본) 파싱에 실패했습니다."}
        if not isinstance(parsed, list):
            return {"error": "최상위 응답은 JSON 배열이어야 합니다."}
        # 디버깅: 보정 전 상태 (깊은 복사로 보존)
        import copy
        parsed_copy = copy.deepcopy(parsed)
        logger.debug(f"[DEBUG] 보정 전 SHORT/FILL_BLANK main 상태:")
        for q in parsed_copy:
            qtype = q.get("questionType", "")
            if qtype in ("SHORT", "FILL_BLANK"):
                answers = q.get("answers", [])
                for a in answers:
                    logger.debug(f"  {qtype}: number={a.get('number')}, main={a.get('main')}, answer={a.get('answer', '')[:30]}")
        # 규칙 위반 보정 (in-place 수정)
        sanitized = _sanitize_questions(parsed)
        logger.debug(f"[DEBUG] 보정 후 SHORT/FILL_BLANK main 상태:")
        for q in sanitized:
            qtype = q.get("questionType", "")
            if qtype in ("SHORT", "FILL_BLANK"):
                answers = q.get("answers", [])
                for a in answers:
                    logger.debug(f"  {qtype}: number={a.get('number')}, main={a.get('main')}, answer={a.get('answer', '')[:30]}")
        # JSON 문자열로 직렬화하여 반환
        json_str = json.dumps(sanitized, ensure_ascii=False)
        # 직렬화 후 값 확인 (디버깅)
        try:
            verify = json.loads(json_str)
            logger.debug(f"[DEBUG] JSON 직렬화 후 검증:")
            for q in verify:
                qtype = q.get("questionType", "")
                if qtype in ("SHORT", "FILL_BLANK"):
                    answers = q.get("answers", [])
                    for a in answers:
                        is_main = a.get("main")
                        logger.debug(f"  {qtype}: number={a.get('number')}, main={is_main} (type: {type(is_main).__name__}), answer={a.get('answer', '')[:30]}")
            # JSON 문자열에서 SHORT/FILL_BLANK의 main 값 직접 확인
            import re
            # SHORT/FILL_BLANK 문제의 main 값 추출
            for q in verify:
                qtype = q.get("questionType", "")
                if qtype in ("SHORT", "FILL_BLANK"):
                    # JSON 문자열에서 해당 문제 부분 찾기
                    q_content = q.get("content", "")[:30]
                    pattern = rf'"questionType":\s*"{qtype}"[^]]*?"answers":\s*\[(.*?)\]'
                    match = re.search(pattern, json_str, re.DOTALL)
                    if match:
                        answers_json = match.group(1)
                        is_main_values = re.findall(r'"main":\s*(true|false)', answers_json)
                        logger.debug(f"  {qtype} ({q_content}): JSON 문자열의 main 값들 = {is_main_values}")
        except Exception as e:
            logger.debug(f"[DEBUG] JSON 검증 실패: {e}")
        logger.info(f"[GENERATION_SUCCESS] question_count={len(sanitized)}")
        return {"content": json_str}
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        logger.error(f"[ERROR] generate_question_set 실패: {error_detail}")
        return {"error": f"문제 생성 중 오류가 발생했습니다: {str(e)}"}
