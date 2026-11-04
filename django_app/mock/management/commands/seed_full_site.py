from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from mock.models import Question, Section, SpeakingTask, Test, WritingTask


LISTENING_SCRIPT = (
    "Hello everyone. This is an announcement from the Riverside Community Centre. "
    "Our community garden welcomes new volunteers every Saturday from nine in the morning until noon. "
    "On your first visit, please meet Lina at the main gate for a short safety briefing. "
    "We provide gloves and small gardening tools, but please bring your own water bottle. "
    "This week, the group will plant herbs beside the east fence. "
    "In June, we will hold a small market on the second Saturday of the month. "
    "Visitors can buy plants and homemade food. All money raised will be used to build two raised garden beds for older residents. "
    "If you would like to join, write your name on the noticeboard inside the entrance before Friday afternoon. "
    "You do not need gardening experience, and children over twelve may come with an adult."
)

LISTENING_QUESTIONS = [
    ("When do volunteers meet at the garden?", ["Saturday morning", "Monday evening", "Friday afternoon", "Sunday noon"], "Saturday morning"),
    ("Where should a new volunteer meet Lina?", ["At the main gate", "Beside the east fence", "Inside the market", "At the bus stop"], "At the main gate"),
    ("What should volunteers bring?", ["A water bottle", "Gardening gloves", "A small spade", "A notebook"], "A water bottle"),
    ("What will the group plant this week?", ["Herbs", "Fruit trees", "Flowers", "Vegetables"], "Herbs"),
    ("When will the small market take place?", ["The second Saturday in June", "The first Friday in May", "Every Saturday morning", "The last Sunday in June"], "The second Saturday in June"),
    ("What will the money raised at the market pay for?", ["Two raised garden beds", "A new community hall", "More gardening tools", "A safety course"], "Two raised garden beds"),
    ("Where should people write their names to join?", ["On the noticeboard inside the entrance", "At the east fence", "On the garden gate", "At the market stall"], "On the noticeboard inside the entrance"),
    ("Which children may attend?", ["Children over twelve with an adult", "Children of any age alone", "Children under twelve with a friend", "Only children with gardening experience"], "Children over twelve with an adult"),
]

SPEAKING_TASKS = [
    {
        "part": 1,
        "prompt": "Let's talk about daily routines. What is the busiest part of your day? Do you prefer planning your day or deciding as you go?",
        "bullets": "",
        "closing": "",
        "speak_seconds": 60,
    },
    {
        "part": 2,
        "prompt": "Describe a public place in your town that you enjoy visiting.",
        "bullets": "where it is\nwhen you go there\nwhat people do there",
        "closing": "and explain why you enjoy visiting this place.",
        "speak_seconds": 120,
    },
    {
        "part": 3,
        "prompt": "How can public spaces improve people's quality of life? Should local communities have more influence on how these spaces are designed?",
        "bullets": "",
        "closing": "",
        "speak_seconds": 90,
    },
]

WRITING_TASKS = [
    {
        "part": 1,
        "title": "Library visits during the working week",
        "prompt": "The table below shows the number of visitors, in hundreds, to two public libraries from Monday to Friday. Summarise the information by selecting and reporting the main features, and make comparisons where relevant.",
        "data_table": {
            "headers": ["Day", "North library", "South library"],
            "rows": [
                ["Monday", 120, 90],
                ["Tuesday", 150, 110],
                ["Wednesday", 135, 125],
                ["Thursday", 170, 140],
                ["Friday", 190, 160],
            ],
        },
        "duration_minutes": 20,
        "minimum_words": 150,
    },
    {
        "part": 2,
        "title": "Public libraries in the digital age",
        "prompt": "Some people believe public libraries are no longer necessary because information is available online. To what extent do you agree or disagree? Give reasons for your answer and include examples from your own knowledge or experience.",
        "data_table": {},
        "duration_minutes": 40,
        "minimum_words": 250,
    },
]


class Command(BaseCommand):
    help = "Seed original Listening, Speaking, and Writing practice content."

    def handle(self, *args, **options):
        audio_path = Path(settings.MEDIA_ROOT) / "audio" / "community_garden.wav"
        if not audio_path.exists():
            raise CommandError(f"Listening audio not found: {audio_path}")

        listening, _ = Test.objects.update_or_create(
            title="Listening Practice Test 1",
            section=Section.LISTENING,
            defaults={
                "duration_minutes": 25,
                "audio": "audio/community_garden.wav",
                "is_active": True,
            },
        )
        for number, (text, choices, answer) in enumerate(LISTENING_QUESTIONS, start=1):
            Question.objects.update_or_create(
                test=listening,
                number=number,
                defaults={
                    "kind": Question.Kind.MCQ,
                    "instruction": "Listen to the community-centre announcement and choose the best answer.",
                    "text": text,
                    "options": choices,
                    "answer": answer,
                },
            )

        for task_data in SPEAKING_TASKS:
            SpeakingTask.objects.get_or_create(
                part=task_data["part"],
                prompt=task_data["prompt"],
                defaults={key: value for key, value in task_data.items() if key not in ("part", "prompt")},
            )

        for task_data in WRITING_TASKS:
            WritingTask.objects.update_or_create(
                title=task_data["title"],
                defaults=task_data,
            )

        self.stdout.write(self.style.SUCCESS(
            f"Added {listening.questions.count()} Listening questions, "
            f"{SpeakingTask.objects.count()} Speaking prompts, and "
            f"{WritingTask.objects.count()} Writing tasks."
        ))
