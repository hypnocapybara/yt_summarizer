from openai import OpenAI
from django.conf import settings


def summarize_chunk(text: str, system_prompt: str, user_prompt: str) -> str:
    client = OpenAI(api_key=settings.OPEN_AI_KEY)

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt.format(text=text)}
        ]
    )

    return str(completion.choices[0].message.content)
