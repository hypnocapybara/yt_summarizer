import re
import anthropic

from datetime import timedelta

from django.conf import settings

from apps.main.models import YoutubeVideo

MODEL_ID = "claude-3-5-sonnet-20240620"
SYSTEM_PROMPT = "Ты - умный анализатор транскрипций (стенограмм) YouTube видео. Ты умеешь выделять главы (части) на основе транскрипта"
CHAPTERS_PROMPT = """
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
- Для очень коротких видео (менее 2 минут) вам может понадобиться всего 2-3 главы.
- Если есть длинные разделы без четкой смены тем, рассмотрите возможность создания глав на основе временных интервалов (например, каждые 5-10 минут).

Теперь проанализируйте предоставленную расшифровку и сгенерируйте список глав видео YouTube. Нацельтесь на 5-10 глав, в зависимости от длины и сложности контента. Представьте свой окончательный результат в следующем формате:

<chapters>
[Перечислите здесь сгенерированные главы, по одной в строке]
</chapters>

Не забудьте тщательно продумать содержание и структуру видео, чтобы создать наиболее полезные главы для зрителей.
"""


def fill_video_chapters(video: YoutubeVideo):
    lines = []

    if not video.transcription_segments:
        return

    for segment in video.transcription_segments:
        timestamp = str(timedelta(seconds=int(segment['start'])))
        text = segment['text']
        line = f'[{timestamp}] {text}'
        lines.append(line)

    transcript_text = '\n'.join(lines)

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_KEY)
    message = client.messages.create(
        model=MODEL_ID,
        max_tokens=4096,
        temperature=0,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": CHAPTERS_PROMPT.format(text=transcript_text)
                    }
                ]
            }
        ]
    )

    result = '\n'.join([block.text for block in message.content])
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
