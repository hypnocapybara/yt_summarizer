from datetime import timedelta
from typing import Literal

from nltk import tokenize
from tiktoken import get_encoding

from apps.main.models import YoutubeVideo

from .anthropic import summarize_chunk as summarize_chunk_anthropic
from .llama import summarize_chunk as summarize_chunk_llama
from .openai import summarize_chunk as summarize_chunk_openai


INITIAL_PROMPTS = {
    'en': 'You are the smart summarizer for YouTube video transcriptions. You can highlighting the main key points and described events',
    'ru': 'Ты - умный суммаризатор транскрипций YouTube видео. Ты выделяешь ключевые моменты и описываемые события. Отвечай на русском языке.',
}

USER_INPUTS = {
    'en': """
You are tasked with summarizing a YouTube video transcript or a portion of it, highlighting the main key points or events described. Follow these instructions carefully:

1. You will be provided with a transcript of a YouTube video or its chapter in the following format:
<transcript>
{text}
</transcript>

2. Carefully read through the transcript to understand the content and context of the video.

3. As you read, identify the main key points or significant events discussed in the video. Pay attention to:
   - Central themes or topics
   - Important facts or statistics
   - Key arguments or opinions expressed
   - Major events or developments described
   - Crucial examples or case studies mentioned

4. Present your key points and events within <summary> tags, structured like this:

<summary>
- [First key point]
- [Second key point]
- [Third key point]
- [Continue as needed]
</summary>

Remember to focus only on the information provided in the transcript. Do not add any external information or make assumptions beyond what is explicitly stated in the video content.

""",
    'ru': """
Вам поручено суммаризировать транскрипт (стенограмму) YouTube видео или его часть, выделяя основные ключевые моменты или описанные события.
Внимательно следуйте этим инструкциям:

1. Вам будет предоставлен транскрипт видео YouTube или его главы в следующем формате:
<transcript>
{text}
</transcript>

2. Внимательно прочитайте транскрипт, чтобы понять содержание и контекст видео.

3. Во время чтения определите основные ключевые моменты или значимые события, обсуждаемые в видео. Обратите внимание на:
- Центральные темы или темы
- Важные факты или статистику
- Ключевые аргументы или высказанные мнения
- Описанные основные события или разработки
- Упомянутые важные примеры или тематические исследования

4. Представьте свои ключевые моменты и события в тегах <summary>, структурированных следующим образом:

<summary>
- [Первый ключевой момент]
- [Второй ключевой момент]
- [Третий ключевой момент]
- [Продолжите по мере необходимости]
</summary>

Помните, что нужно сосредоточиться только на информации, представленной в стенограмме.
Не добавляйте никакой внешней информации и не делайте предположений сверх того, что явно указано в транскрипте.
""",
}

TOKENIZER_LANGUAGES = {
    'en': 'english',
    'ru': 'russian',
}

SUMMARIZERS = {
    'anthropic': {
        'func': summarize_chunk_anthropic,
        'context_window': 200000,
    },
    'openai': {
        'func': summarize_chunk_openai,
        'context_window': 128000
    },
    'llama': {
        'func': summarize_chunk_llama,
        'context_window': 128000,
    }
}


def summarize_video_generic(video: YoutubeVideo, summarizer_key: Literal['anthropic', 'openai', 'llama'] = 'anthropic'):
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
            # chapter_timestamp = chapter_timestamp[3:] if chapter_timestamp.startswith('00:') else chapter_timestamp
            chapter_heading = f'[{chapter_timestamp}] {chapter_title}'

            print(f'Summarizing chapter content: {chapter_heading}')

            selected_segments = [
                s for s in video.transcription_segments
                if chapter_start <= s['start'] <= chapter_end or chapter_start <= s['end'] <= chapter_end
            ]
            segments_text = ''.join(s['text'] for s in selected_segments).strip()
            segment_summary = summarize_text(segments_text, language, summarizer_key)

            chapter_summaries.append(f'{chapter_heading}\n{segment_summary}\n')

        video.summary = '\n'.join(chapter_summaries)
    else:
        video.summary = summarize_text(video.transcription, language, summarizer_key)

    video.save()


def split_text_in_chunks(text: str, language: str, max_tokens_count_in_chunk: int) -> list[str]:
    encoder = get_encoding("cl100k_base")
    sentences = tokenize.sent_tokenize(text, language=TOKENIZER_LANGUAGES[language])

    chunks_buffer = []
    sentences_buffer = []
    current_tokens_count = 0

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

    return chunks_buffer


def summarize_text(
        text: str, language: str, summarizer_key: Literal['anthropic', 'openai', 'llama'] = 'anthropic'
) -> str:
    summarizer = SUMMARIZERS[summarizer_key]
    func = summarizer['func']
    context_window = summarizer['context_window']

    chunks = split_text_in_chunks(text, language, context_window)
    summaries = []

    print(f'Gonna summarize {len(chunks)} chunks')

    for chunk in chunks:
        result = func(chunk, INITIAL_PROMPTS[language], USER_INPUTS[language])

        if '<summary>' in result and '</summary>' in result:
            result = result.split('<summary>')[1].strip()
            result = result.split('</summary>')[0].strip()

        summaries.append(result)

    return '\n'.join(summaries)
