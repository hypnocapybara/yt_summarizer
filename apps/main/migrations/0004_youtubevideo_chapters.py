# Generated by Django 5.0.2 on 2024-03-15 23:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_youtubevideo_transcription_segments'),
    ]

    operations = [
        migrations.AddField(
            model_name='youtubevideo',
            name='chapters',
            field=models.JSONField(default=list),
        ),
    ]
