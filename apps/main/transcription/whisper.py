import whisper

from apps.main.models import YoutubeVideo


def transcribe_video_whisper(video: YoutubeVideo):
    model = whisper.load_model('medium')
    result = model.transcribe(video.audio_file.path)

    video.transcription_language = result['language']
    video.transcription = result['text']
    video.save()
