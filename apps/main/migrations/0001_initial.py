# Generated by Django 5.0 on 2023-12-18 20:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='YoutubeChannel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField()),
                ('enabled', models.BooleanField(default=True)),
                ('title', models.CharField(blank=True, max_length=200, null=True)),
                ('last_parsed_at', models.DateTimeField(blank=True, null=True)),
                ('voice_file', models.FileField(blank=True, null=True, upload_to='channels/')),
            ],
            options={
                'verbose_name': 'Youtube Channel',
                'verbose_name_plural': 'Youtube Channels',
            },
        ),
        migrations.CreateModel(
            name='YoutubeVideo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('url', models.URLField()),
                ('youtube_id', models.CharField(blank=True, max_length=100, null=True)),
                ('title', models.CharField(blank=True, max_length=200, null=True)),
                ('audio_file', models.FileField(blank=True, null=True, upload_to='videos/audio/')),
                ('transcription', models.TextField(blank=True, null=True)),
                ('transcription_language', models.CharField(blank=True, max_length=10, null=True)),
                ('summary', models.TextField(blank=True, null=True)),
                ('voiced_summary', models.FileField(blank=True, null=True, upload_to='videos/voiced/')),
                ('channel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.youtubechannel')),
            ],
            options={
                'verbose_name': 'Youtube Video',
                'verbose_name_plural': 'Youtube Videos',
            },
        ),
    ]
