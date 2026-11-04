from django.core.management.base import BaseCommand

from mock.models import Question, SpeakingTask, Test, Word


class Command(BaseCommand):
    help = "Create a small demo dataset (original sample content)."

    def handle(self, *args, **options):
        reading, _ = Test.objects.get_or_create(
            title="Sample Reading 1", section="reading",
            defaults=dict(
                duration_minutes=25, passage_title="The Quiet Return of the Urban Fox",
                passage_text=(
                    "Foxes first appeared in British suburbs in large numbers during the 1930s, when new housing "
                    "estates offered gardens, quiet lanes and a steady supply of food. Within a generation they had "
                    "become a familiar sight after dark.\n\n"
                    "Researchers who tracked individual animals found that most urban foxes rarely travel more than "
                    "a kilometre from their den. Their diet is far more varied than many residents assume, including "
                    "insects, fruit and discarded takeaway food."),
            ))
        if not reading.questions.exists():
            tf = "Do the following statements agree with the information in the passage? Choose TRUE, FALSE or NOT GIVEN."
            gap = "Complete the sentences. Write NO MORE THAN TWO WORDS for each answer."
            Question.objects.bulk_create([
                Question(test=reading, number=1, kind="tfng", instruction=tf, answer="TRUE",
                         text="Foxes became common in suburbs before the 1940s."),
                Question(test=reading, number=2, kind="tfng", answer="FALSE",
                         text="Urban foxes usually travel long distances from their dens."),
                Question(test=reading, number=3, kind="tfng", answer="NOT GIVEN",
                         text="Foxes are more common in cities than in the countryside."),
                Question(test=reading, number=4, kind="gap", instruction=gap, answer="food",
                         text="Foxes were attracted to new estates by gardens and a supply of ______."),
                Question(test=reading, number=5, kind="gap", answer="takeaway food|takeaway|discarded takeaway food",
                         text="Besides insects and fruit, foxes eat ______."),
            ])

        # Inactive until real audio is uploaded in the admin.
        Test.objects.get_or_create(
            title="Sample Listening 1", section="listening",
            defaults=dict(duration_minutes=30, is_active=False))

        for part, prompt, bullets, closing, secs in [
            (1, "Let's talk about your hometown. What do you like most about it?", "", "", 60),
            (2, "Describe a place you visited that you would like to go back to.",
             "where it is\nwhen you went there\nwhat you did there", "and explain why you would like to go back.", 120),
            (3, "How has tourism changed the way people travel in your country?", "", "", 90),
        ]:
            SpeakingTask.objects.get_or_create(part=part, prompt=prompt, defaults=dict(
                bullets=bullets, closing=closing, speak_seconds=secs))

        for w in [
            dict(word="mitigate", phonetic="/ˈmɪtɪɡeɪt/", part_of_speech="verb", band_level=7,
                 definition="to make something less severe, harmful or painful",
                 example="Governments can mitigate the effects of climate change by investing in public transport.",
                 wrong_options=["to explain something in detail", "to cancel something completely",
                                "to measure something carefully"]),
            dict(word="substantial", phonetic="/səbˈstænʃl/", part_of_speech="adjective", band_level=6,
                 definition="large in amount, size or importance",
                 example="The new policy led to a substantial fall in pollution.",
                 wrong_options=["very small and easy to miss", "happening very suddenly",
                                "similar to something else"]),
            dict(word="advocate", phonetic="/ˈædvəkeɪt/", part_of_speech="verb", band_level=7,
                 definition="to publicly support an idea or plan",
                 example="Many teachers advocate shorter school days.",
                 wrong_options=["to strongly oppose a decision", "to carefully inspect something",
                                "to change something slightly"]),
        ]:
            Word.objects.get_or_create(word=w["word"], defaults=w)
        self.stdout.write(self.style.SUCCESS("Demo data created."))
