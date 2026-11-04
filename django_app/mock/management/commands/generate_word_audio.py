import asyncio
from pathlib import Path

import edge_tts
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from mock.models import Word


VOICE = "en-GB-SoniaNeural"


class Command(BaseCommand):
    help = "Generate soft English neural pronunciation clips for vocabulary words."

    def add_arguments(self, parser):
        parser.add_argument("--overwrite", action="store_true")

    def handle(self, *args, **options):
        words = list(Word.objects.order_by("word"))
        if not words:
            raise CommandError("No vocabulary words found. Run seed_words first.")

        output_dir = Path(settings.MEDIA_ROOT) / "pronunciation"
        output_dir.mkdir(parents=True, exist_ok=True)
        failures = []
        generated = 0
        skipped = 0

        async def generate_one(word, semaphore):
            nonlocal generated, skipped
            filename = slugify(word.word) or f"word-{word.pk}"
            output_path = output_dir / f"{filename}.mp3"
            if output_path.exists() and not options["overwrite"]:
                skipped += 1
                return
            async with semaphore:
                try:
                    speech = edge_tts.Communicate(
                        word.word,
                        VOICE,
                        rate="+10%",
                        pitch="-1Hz",
                        volume="-6%",
                    )
                    await speech.save(str(output_path))
                    generated += 1
                except Exception as error:
                    failures.append(f"{word.word}: {error}")

        async def generate_all():
            semaphore = asyncio.Semaphore(3)
            await asyncio.gather(*(generate_one(word, semaphore) for word in words))

        asyncio.run(generate_all())
        self.stdout.write(f"Generated: {generated}; already present: {skipped}; voice: {VOICE}")
        if failures:
            raise CommandError("Some pronunciation files failed:\n" + "\n".join(failures))
