import asyncio

from django.core.management import BaseCommand
from django.conf import settings

from apps.telegram.bot import run_bot


class Command(BaseCommand):
    def handle(self, *args, **options):
        asyncio.run(run_bot(settings.TELEGRAM_BOT_TOKEN))
