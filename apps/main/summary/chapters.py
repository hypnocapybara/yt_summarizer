import re
from typing import Literal

import anthropic

from datetime import timedelta

from django.conf import settings
from openai import OpenAI

from apps.main.models import YoutubeVideo

MODEL_ID = "claude-3-5-sonnet-20240620"
SYSTEM_PROMPT_RU = "Ты - умный анализатор транскрипций (стенограмм) YouTube видео. Ты умеешь выделять главы (части) на основе транскрипта"
SYSTEM_PROMPT_EN = "You are smart YouTube video transcript analyzer. You can generate chapters based on the transcription"


CHAPTERS_PROMPT_RU = """
Вам поручено создать список глав YouTube видео на основе транскрипта с временными метками. Это поможет зрителям легче ориентироваться в видеоконтенте. Вот транскрипт, с которым вы будете работать:

<transcript>
{text}
</transcript>

Чтобы создать эффективные главы видео, выполните следующие действия:

1. Проанализируйте транскрипт:
 - Ищите основные изменения тем или сдвиги в разговоре.
 - Обращайте внимание на фразы, которые могут указывать на новый раздел, например «перейдем к», «далее» или «давайте поговорим о».
 - Рассмотрите естественные перерывы в контенте, например паузы или переходы между говорящими.

2. Создавайте названия глав:
 - Делайте заголовки короткими и описательными, в идеале 2–6 слов.
 - Используйте слова действия или ключевые фразы, которые резюмируют основную мысль раздела.
 - Убедитесь, что заголовки понятны и информативны для тех, кто не смотрел видео.

3. Отформатируйте главы:
 - Начните с временной метки в формате ЧЧ:ММ:СС.
 - После временной метки поставьте пробел, а затем название главы.
 - Перечислите главы в хронологическом порядке.

Вот примеры хороших и плохих названий глав:

Хорошие:
[0:00:00] Введение
[0:03:45] Объяснение основных функций
[0:12:30] Демонстрация в реальном времени

Плохие:
[0:00:00] Видео начинается здесь
[0:03:45] Обсуждаем некоторые вещи
[0:12:30] Демонстрация того, как это работает

Обработайте эти пограничные случаи:
- Если расшифровка начинается с середины предложения, используйте контекст, чтобы определить подходящую начальную главу.
- Для очень коротких видео (менее 5 минут) вам может понадобиться всего 2-3 главы.
- Если есть длинные разделы без четкой смены тем, рассмотрите возможность создания глав на основе временных интервалов (например, каждые 5-10 минут).

Теперь проанализируйте предоставленную расшифровку и сгенерируйте список глав видео YouTube. Нацельтесь на 5-10 глав, в зависимости от длины и сложности контента. Представьте свой окончательный результат в следующем формате:

<chapters>
[Перечислите здесь сгенерированные главы, по одной в строке]
</chapters>

Не забудьте тщательно продумать содержание и структуру видео, чтобы создать наиболее полезные главы для зрителей.
"""

CHAPTERS_PROMPT_EN = """
You are tasked with generating a list of YouTube video chapters based on a transcript with timestamps. This will help viewers navigate through the video content more easily. Here's the transcript you'll be working with:

<transcript>
{text}
</transcript>

To create effective video chapters, follow these steps:

1. Analyze the transcript:
   - Look for major topic changes or shifts in the conversation.
   - Pay attention to phrases that might indicate a new section, such as "moving on to," "next," or "let's talk about."
   - Consider natural breaks in the content, such as pauses or transitions between speakers.

2. Create chapter titles:
   - Keep titles short and descriptive, ideally 2-8 words.
   - Use action words or key phrases that summarize the main point of the section.
   - Ensure titles are clear and informative to someone who hasn't watched the video.

3. Format the chapters:
   - Start with the timestamp in HH:MM:SS format.
   - Follow the timestamp with a space and then the chapter title.
   - List chapters in chronological order.

Here are examples of good and bad chapter titles:

Good:
[0:00:00] Introduction
[0:03:45] Key Features Explained
[0:12:30] Live Demo

Bad:
[0:00:00] The video starts here
[0:03:45] Talking about some stuff
[0:12:30] Showing how it works

Handle these edge cases:
- If the transcript starts mid-sentence, use context to determine an appropriate starting chapter.
- For very short videos (under 5 minutes), you may only need 2-3 chapters.
- If there are long sections without clear topic changes, consider creating chapters based on time intervals (e.g., every 5-10 minutes).

Now, analyze the provided transcript and generate a list of YouTube video chapters. Aim for 5-10 chapters, depending on the length and complexity of the content. Present your final output in the following format:

<chapters>
[List your generated chapters here, one per line]
</chapters>

Remember to think carefully about the content and structure of the video to create the most useful chapters for viewers.
"""


def fill_video_chapters(video: YoutubeVideo, model: Literal['anthropic', 'openai'] = 'anthropic'):
    lines = []

    if not video.transcription_segments:
        return

    if video.transcription_language == 'en':
        system_prompt = SYSTEM_PROMPT_EN
        user_prompt = CHAPTERS_PROMPT_EN
    elif video.transcription_language == 'ru':
        system_prompt = SYSTEM_PROMPT_RU
        user_prompt = CHAPTERS_PROMPT_RU
    else:
        return

    for segment in video.transcription_segments:
        timestamp = str(timedelta(seconds=int(segment['start'])))
        text = segment['text']
        line = f'[{timestamp}] {text}'
        lines.append(line)

    transcript_text = '\n'.join(lines)

    if model == 'anthropic':
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
                            "text": user_prompt.format(text=transcript_text)
                        }
                    ]
                }
            ]
        )
        result = '\n'.join([block.text for block in message.content])
    elif model == 'openai':
        client = OpenAI(api_key=settings.OPEN_AI_KEY)

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt.format(text=transcript_text)}
            ]
        )
        result = str(completion.choices[0].message.content)
    else:
        return

    result = result.replace('\n\n', '\n')
    result = result.split('<chapters>')[1].strip()
    result = result.split('</chapters>')[0].strip()

    chapters = []
    chapter_lines = result.split('\n')
    print(f'Successfully fetched {len(chapter_lines)} chapters')

    last_segment_end = int(video.transcription_segments[-1]["end"])

    for i, line in enumerate(chapter_lines):
        time_parts = re.findall('\[(\d+):(\d+):(\d+)\]', line)[0]

        hour, minute, second = time_parts
        time_delta = timedelta(hours=int(hour), minutes=int(minute), seconds=int(second))
        start = time_delta.seconds

        title = line.split(']')[1].strip()

        if i < len(chapter_lines) - 1:
            next_line = chapter_lines[i+1]
            next_time_parts = re.findall('\[(\d+):(\d+):(\d+)\]', next_line)[0]
            hour, minute, second = next_time_parts
            time_delta = timedelta(hours=int(hour), minutes=int(minute), seconds=int(second))
            next_start = time_delta.seconds
            duration = next_start - start
        else:
            duration = last_segment_end - start

        chapters.append({
            "start": int(start),
            "title": title,
            "duration": int(duration),
        })

    video.chapters = chapters
    video.save()
