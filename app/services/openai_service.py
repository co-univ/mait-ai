import openai
from app.config import settings

openai.api_key = settings.OPENAI_API_KEY

async def generate_text(prompt: str) -> dict:
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 친절한 백엔드 개발자 어시스턴트입니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7,
        )
        return {"content": response.choices[0].message.content}
    except Exception as e:
        return {"error": str(e)}
