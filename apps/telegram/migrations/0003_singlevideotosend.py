# Generated by Django 5.0.2 on 2024-02-13 03:28

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_alter_youtubevideo_channel'),
        ('telegram', '0002_telegramuser_updated_at_telegramvideo_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='SingleVideoToSend',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_sent', models.BooleanField(default=False)),
                ('send_to', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='telegram.telegramuser')),
                ('video', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.youtubevideo')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]