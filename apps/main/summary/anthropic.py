import anthropic

from django.conf import settings

MODEL_ID = "claude-3-5-sonnet-20240620"


def summarize_chunk(text: str, system_prompt: str, user_prompt: str) -> str:
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_KEY)

    message = client.messages.create(
        model=MODEL_ID,
        max_tokens=4096,
        temperature=0,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_prompt.format(text=text)
                    }
                ]
            }
        ]
    )

    result = '\n'.join([block.text for block in message.content])
    result = result.replace('\n\n', '\n')

    return result

    if '<summary>' not in result or '</summary>' not in result:
        return result

    a = text.split('<summary>')[1].strip()
    b = a.split('</summary>')[0].strip()
    c = b.replace('\n\n', '\n')

