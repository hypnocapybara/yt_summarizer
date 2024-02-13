import string
import whisper

from nltk import tokenize
from pydub import AudioSegment

from apps.synthesizer.models import Speaker, Transcription, Segment, Word
from apps.main.summary.openai import TOKENIZER_LANGUAGES


def _process_text_for_word(text: str) -> str:
    return text.strip().translate(str.maketrans('', '', string.punctuation)).lower()


def transcribe_audio(transcription: Transcription):
    model = whisper.load_model('medium')
    result = model.transcribe(
        transcription.audio_file.path,
        word_timestamps=True,
        language=transcription.speaker.language
    )
    transcription.text = result['text']
    transcription.save()

    transcription.segments.all().delete()

    for data_segment in result['segments']:
        segment = Segment.objects.create(
            transcription=transcription,
            text=data_segment['text'].strip(),
            start=data_segment['start'],
            end=data_segment['end']
        )

        Word.objects.bulk_create([
            Word(
                segment=segment,
                text=_process_text_for_word(data_word['word']),
                start=data_word['start'],
                end=data_word['end'],
            )
            for data_word in data_segment['words']
        ])


def generate_from_text(speaker: Speaker, text: str) -> AudioSegment:
    text_words = tokenize.word_tokenize(text, language=TOKENIZER_LANGUAGES[speaker.language])
    text_words = [w.lower() for w in text_words if w not in string.punctuation]

    result = AudioSegment.silent(200)
    for text_word in text_words:
        word = Word.objects.filter(
            segment__transcription__speaker=speaker,
            text=text_word
        ).first()
        if not word:
            continue

        audio_file = AudioSegment.from_file(word.segment.transcription.audio_file.path)
        section = audio_file[int(word.start * 1000): int(word.end * 1000)]
        result += section
        result += AudioSegment.silent(200)

    return result
