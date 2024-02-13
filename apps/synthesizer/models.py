from django.db import models


# Create your models here.
class Speaker(models.Model):
    LANGUAGE_CHOICES = (
        ('en', 'English'),
        ('ru', 'Russian')
    )
    name = models.CharField(max_length=50)
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES)

    def __str__(self):
        return self.name


class Transcription(models.Model):
    speaker = models.ForeignKey(Speaker, on_delete=models.CASCADE, related_name='transcriptions')
    audio_file = models.FileField(upload_to='synthesizer/audio/')
    text = models.TextField(blank=True, null=True)

    def __str__(self):
        return str(self.speaker) + ' - ' + str(self.pk)


class Segment(models.Model):
    transcription = models.ForeignKey(Transcription, on_delete=models.CASCADE, related_name='segments')
    text = models.TextField()
    start = models.FloatField()
    end = models.FloatField()


class Word(models.Model):
    segment = models.ForeignKey(Segment, on_delete=models.CASCADE, related_name='words')
    text = models.CharField(max_length=32)
    start = models.FloatField()
    end = models.FloatField()

    def __str__(self):
        return self.text
