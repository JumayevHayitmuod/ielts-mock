from django.core.management.base import BaseCommand

from mock.models import Question, Section, Test


QUESTIONS = [
    ("The new policy had a ___ effect on traffic, reducing delays by half.", ["significant", "distant", "casual", "narrow"], "significant"),
    ("The scientist conducted an ___ study over five years.", ["extensive", "ordinary", "brief", "uncertain"], "extensive"),
    ("Please ___ your claim with reliable evidence.", ["support", "avoid", "ignore", "divide"], "support"),
    ("The city plans to ___ its public transport network.", ["expand", "refuse", "prevent", "reduce"], "expand"),
    ("The company must ___ to changing customer needs.", ["adapt", "belong", "insist", "appear"], "adapt"),
    ("Regular exercise can ___ the risk of heart disease.", ["reduce", "create", "measure", "allow"], "reduce"),
    ("The museum attracts a ___ number of visitors each year.", ["considerable", "temporary", "nervous", "distant"], "considerable"),
    ("We need to ___ the problem before proposing a solution.", ["identify", "celebrate", "deliver", "persuade"], "identify"),
    ("The report provides a ___ analysis of the issue.", ["detailed", "rare", "minor", "silent"], "detailed"),
    ("Many residents ___ the construction of the new park.", ["support", "prevent", "compare", "divide"], "support"),
    ("The project was delayed because of a lack of ___.", ["funding", "custom", "comfort", "permission"], "funding"),
    ("Water is an increasingly ___ resource in dry regions.", ["scarce", "polite", "equal", "smooth"], "scarce"),
    ("The new law aims to ___ air pollution.", ["reduce", "reveal", "replace", "require"], "reduce"),
    ("She is ___ in both English and Spanish.", ["fluent", "narrow", "distant", "ordinary"], "fluent"),
    ("The evidence strongly ___ the researchers' theory.", ["supports", "borrows", "compares", "prepares"], "supports"),
    ("The company introduced measures to ___ waste.", ["minimize", "announce", "purchase", "translate"], "minimize"),
    ("His explanation was ___, so everyone understood the process.", ["clear", "remote", "complex", "weak"], "clear"),
    ("Online courses offer greater ___ for adult learners.", ["flexibility", "accuracy", "quantity", "permission"], "flexibility"),
    ("The government should ___ investment in renewable energy.", ["encourage", "damage", "suspect", "divide"], "encourage"),
    ("The device is designed to ___ energy consumption.", ["reduce", "gather", "pretend", "compare"], "reduce"),
    ("There is a ___ difference between the two proposals.", ["substantial", "comfortable", "immediate", "ordinary"], "substantial"),
    ("The team worked together to ___ the challenge.", ["overcome", "observe", "contain", "replace"], "overcome"),
    ("The program gives students the ___ to study abroad.", ["opportunity", "evidence", "attitude", "influence"], "opportunity"),
    ("The town is ___ near the coast.", ["situated", "achieved", "suggested", "provided"], "situated"),
    ("The new system is more ___ than the old one.", ["efficient", "generous", "anxious", "similar"], "efficient"),
    ("The teacher asked students to ___ their opinions.", ["express", "restrict", "predict", "replace"], "express"),
    ("The results were ___ with previous studies.", ["consistent", "distant", "available", "separate"], "consistent"),
    ("The hospital provides ___ care for local residents.", ["essential", "average", "private", "similar"], "essential"),
    ("The organization aims to ___ awareness of mental health.", ["raise", "avoid", "assume", "repair"], "raise"),
    ("Many species are ___ by habitat loss.", ["threatened", "delighted", "prepared", "involved"], "threatened"),
]


class Command(BaseCommand):
    help = "Create or refresh a 30-question randomized vocabulary quiz."

    def handle(self, *args, **options):
        quiz, _ = Test.objects.get_or_create(
            title="Vocabulary Quiz 1",
            section=Section.QUIZ,
            defaults={"duration_minutes": 25, "is_active": True},
        )
        if quiz.duration_minutes != 25:
            quiz.duration_minutes = 25
            quiz.save(update_fields=["duration_minutes"])
        for number, (text, choices, answer) in enumerate(QUESTIONS, start=1):
            Question.objects.update_or_create(
                test=quiz,
                number=number,
                defaults={
                    "kind": Question.Kind.MCQ,
                    "instruction": "Choose the word that best completes the sentence.",
                    "text": text,
                    "options": choices,
                    "answer": answer,
                },
            )
        self.stdout.write(self.style.SUCCESS(f"{quiz.title}: {len(QUESTIONS)} questions ready."))
