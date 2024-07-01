from openai import OpenAI

from django.conf import settings


def summarize_chunk(text: str, system_prompt: str, user_prompt: str) -> str:
    client = OpenAI(
        api_key=settings.RUNPOD_API_KEY,
        base_url=f'https://api.runpod.ai/v2/{settings.MY_LLAMA_ID}/openai/v1',
    )

    response = client.chat.completions.create(
        model="meta-llama/Meta-Llama-3-8B-Instruct",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt.format(text=text)},
        ],
    )

    result = response.choices[0].message.content

    return result
