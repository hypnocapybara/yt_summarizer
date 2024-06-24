from datetime import timedelta
from openai import OpenAI
from nltk import tokenize
from tiktoken import get_encoding

from django.conf import settings

from apps.main.models import YoutubeVideo


INITIAL_PROMPTS = {
    'en': 'You are the smart summarizer for YouTube video transcriptions. You can generate key moments based on video fragments',
    'ru': 'Ты - умный суммаризатор транскрипций YouTube видео. Ты выделяешь ключевые моменты из кусков транскрипций',
}

USER_INPUTS = {
    'en': """
The following text in triple quotes is a transcript part
```
{text}
```
Based on it, generate key moments, using the author's direct words whenever possible.
Use hyphens for a key moments list. For example:
- key moment 1
- key moment 2
""",
    'ru': """
Следующий текст в тройных кавчках - это часть транскрипта
```
{text}
```
Основываясь на нем, выдели основные ключевые моменты, по возможости используя прямые слова автора.
Используй дефисы для списка ключевых моментов. Пример:
- ключевой момент 1
- ключевой момент 2
""",
}

TOKENIZER_LANGUAGES = {
    'en': 'english',
    'ru': 'russian',
}


def summarize_video_openai(video: YoutubeVideo):
    language = video.transcription_language
    is_bad_language = language not in INITIAL_PROMPTS or language not in USER_INPUTS
    if is_bad_language or not video.transcription:
        return

    if video.chapters and video.transcription_segments:
        chapter_summaries = []

        for chapter in video.chapters:
            chapter_start = chapter['start']
            chapter_end = chapter['start'] + chapter['duration']
            chapter_title = chapter['title']
            chapter_timestamp = str(timedelta(seconds=chapter_start))
            chapter_timestamp = chapter_timestamp[3:] if chapter_timestamp.startswith('00:') else chapter_timestamp
            chapter_heading = f'[{chapter_timestamp}] {chapter_title}'

            print(f'Summarizing chapter content: {chapter_heading}')

            selected_segments = [
                s for s in video.transcription_segments
                if chapter_start <= s['start'] <= chapter_end or chapter_start <= s['end'] <= chapter_end
            ]
            segments_text = ''.join(s['text'] for s in selected_segments).strip()
            segment_summary = summarize_text(segments_text, language)

            chapter_summaries.append(f'{chapter_heading}\n{segment_summary}\n')

        video.summary = '\n'.join(chapter_summaries)
    else:
        video.summary = summarize_text(video.transcription, language)

    video.save()


def summarize_text(text: str, language: str) -> str:
    client = OpenAI(api_key=settings.OPEN_AI_KEY)

    encoder = get_encoding("cl100k_base")
    sentences = tokenize.sent_tokenize(text, language=TOKENIZER_LANGUAGES[language])

    chunks_buffer = []
    sentences_buffer = []
    current_tokens_count = 0
    max_tokens_count_in_chunk = 128000

    for sentence in sentences:
        tokens_count = len(encoder.encode(sentence))
        if current_tokens_count + tokens_count < max_tokens_count_in_chunk:
            sentences_buffer.append(sentence)
            current_tokens_count += tokens_count
        elif len(sentences_buffer) > 2:
            chunk = ' '.join(sentences_buffer)
            chunks_buffer.append(chunk)
            sentences_buffer = [
                sentences_buffer[-2],
                sentences_buffer[-1],
                sentence
            ]
            current_tokens_count = len(encoder.encode(' '.join(sentences_buffer)))

    chunks_buffer.append(' '.join(sentences_buffer))

    summaries = []

    print(f'Gonna summarize {len(chunks_buffer)} chunks')

    for chunk in chunks_buffer:
        completion = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": INITIAL_PROMPTS[language]},
                {"role": "user", "content": USER_INPUTS[language].format(text=chunk)}
            ]
        )

        result = str(completion.choices[0].message.content)
        summaries.append(result)

    return '\n'.join(summaries)
